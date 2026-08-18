"""Deterministic renderer: ``relationship_vocabulary.yaml`` → ``schema_graph.cypher``.

``drydocs_core/schema/schema_graph.cypher`` is a DERIVED VIEW of
``drydocs_core/ontology/relationship_vocabulary.yaml`` (the confirmed source of truth
for edge meaning — CLAUDE.md §6): one exemplar node per participating node label
(real label + ``:SchemaMeta`` marker) and one exemplar relationship per vocabulary
entry (real relationship type), so ``CALL db.schema.visualization()`` renders the
full declared schema in Neo4j Browser.

TARGET DATABASE: ``ddschema``, not ``drydocs`` — applied by
``drydocs bootstrap-schema-graph`` (SME direction 2026-08-02: "the schema graph is
for the project labels and relationships with different constraints and the DryDocs
project has different code and constraints, 2 different graphs"). It was
manual-only until then, and the reason is structural rather than habit: every
exemplar carries the REAL label beside the ``:SchemaMeta`` marker, so
``MERGE (n:SchemaMeta:ControlMJob {name: 'ControlMJob'})`` run against ``drydocs``
VIOLATES ``controlmjob_key`` (NODE KEY on ``folder_id``/``job_id`` — a NODE KEY
enforces existence, and the exemplar carries only ``name``). Proven live
2026-08-02 on a throwaway label: ``Node with label ZZProbe must have the
properties (folder_id, job_id)``. Dropping the real label would satisfy the
constraint but is exactly what ``db.schema.visualization()`` reads, so the answer
is a separate database whose constraints describe LABELS, not job rows.

House pattern: the same deterministic committed-render-matches-source idiom as the
plan board (``drydocs.plan_board`` + ``scripts/render_board.py``). Thin CLI:
``scripts/render_schema_graph.py``. Drift guard: ``tests/unit/test_schema_graph.py``
re-renders the vocabulary in-memory and fails when the committed file drifts.
Rendering is deterministic — same vocabulary in, byte-identical Cypher out; no
timestamps, no randomness.

Inclusion rule (the deterministic vocabulary→Cypher mapping, backlog C8)
------------------------------------------------------------------------
* ``local_relationships`` with ``status`` in :data:`RENDERED_STATUSES`
  (``active``/``planned``) are rendered, with the status carried on each edge as
  ``r.status``. ``deprecated`` and ``removed`` entries are EXCLUDED: planned
  entries are declared-but-inert vocabulary (loader not yet written) and belong
  in the schema picture; deprecated/removed entries are withdrawn meaning and do
  not. (This matches the hand-written file's original stance — "Deprecated
  entries ... are excluded" — now enforced mechanically.)
* Pipe-union endpoints (``from_node: "ETLProcess | ControlMJob"``) render one
  edge per alternative, in listed order.
* The wildcard ``from_node: "*"`` (``prov_was_generated_by`` — BaseLoader writes
  it for every node label) renders as representative edges from the fixed
  :data:`WILDCARD_EXEMPLARS` so the visualization stays readable; in the real
  graph the edge exists on all nodes.
* Self-referencing entries (``m3_was_informed_by``) render as a self-loop on a
  single bound node.
* Nodes: one exemplar per label referenced by a rendered relationship, in
  ``node_classifications`` order; ``class`` / ``dual_class`` / ``prov_type``
  come from the classification entry. Referenced-but-unclassified labels (infra
  labels like ``OntologyTerm``) follow, name-only, in first-reference order.
  Labels never referenced by a rendered edge (e.g. the retired
  ``DataSource``/``DataTarget``, or ``SchedulerKind`` since its C12
  deprecation) are omitted.
* Edge properties: ``vocab_id``, ``role`` (when set), ``prov_maps_to``
  (explicit ``null`` when unmapped), ``sosa_maps_to`` (when set), ``domain``,
  ``status``. Entry prose (``note``) stays in the vocabulary — the render
  carries structure only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from drydocs_core import yaml_fragments

#: PACKAGE-INTERNAL, both of them — reviewed in the Idea-109 sweep and left alone.
#: The vocabulary fragments and the generated ``.cypher`` live INSIDE
#: ``drydocs_core/`` and travel with the package, so ``__file__`` is the anchor
#: that is right rather than the one that is merely old. That is the other half of
#: the Idea-109 rule: only repo CONTENT follows the caller's checkout.
DEFAULT_VOCAB_PATH = Path(__file__).resolve().parent / "relationship_vocabulary"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "schema" / "schema_graph.cypher"

#: Vocabulary statuses rendered into the meta-graph (carried as ``r.status``).
RENDERED_STATUSES: tuple[str, ...] = ("active", "planned")

#: Representative from-labels for wildcard (``from_node: "*"``) entries — one
#: exemplar per major domain keeps ``db.schema.visualization()`` readable.
WILDCARD_EXEMPLARS: tuple[str, ...] = ("ControlMJob", "BusinessApplication", "CatalogLOB")

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_RULE_WIDTH = 79


class SchemaGraphError(RuntimeError):
    """The vocabulary file is missing, malformed, or not renderable."""


def _lit(value: Any) -> str:
    """Render a value as a Cypher literal (single-quoted string, or ``null``)."""
    if value is None:
        return "null"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def _rule(title: str) -> str:
    prefix = f"// ── {title} "
    return prefix + "─" * max(_RULE_WIDTH - len(prefix), 3)


def _endpoint_labels(rel: dict[str, Any], key: str) -> tuple[list[str], bool]:
    """Endpoint labels for one side of an entry: ``(labels, is_wildcard)``."""
    rel_id = rel.get("id", "<no id>")
    raw = rel.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise SchemaGraphError(f"[{rel_id}] {key} must be a non-empty string")
    raw = raw.strip()
    if raw == "*":
        if key != "from_node":
            raise SchemaGraphError(f"[{rel_id}] wildcard '*' is only supported for from_node")
        return list(WILDCARD_EXEMPLARS), True
    labels = [part.strip() for part in raw.split("|")]
    for label in labels:
        if not _IDENTIFIER.match(label):
            raise SchemaGraphError(f"[{rel_id}] {key} label {label!r} is not a valid identifier")
    return labels, False


def _node_statement(label: str, cls: dict[str, Any] | None) -> list[str]:
    merge = f"MERGE (n:SchemaMeta:{label} {{name: {_lit(label)}}})"
    if cls is None:
        return ["// (no node_classifications entry)", merge + ";"]
    sets = [f"n.class = {_lit(cls.get('class'))}"]
    if cls.get("dual_class") is not None:
        sets.append(f"n.dual_class = {_lit(cls.get('dual_class'))}")
    sets.append(f"n.prov_type = {_lit(cls.get('prov_type'))}")
    return [merge, "  SET " + ", ".join(sets) + ";"]


def _edge_statement(rel: dict[str, Any], from_label: str, to_label: str) -> list[str]:
    sets = [f"r.vocab_id = {_lit(rel.get('id'))}"]
    if rel.get("role") is not None:
        sets.append(f"r.role = {_lit(rel.get('role'))}")
    sets.append(f"r.prov_maps_to = {_lit(rel.get('prov_maps_to'))}")
    if rel.get("sosa_maps_to") is not None:
        sets.append(f"r.sosa_maps_to = {_lit(rel.get('sosa_maps_to'))}")
    sets.append(f"r.domain = {_lit(rel.get('domain'))}")
    sets.append(f"r.status = {_lit(rel.get('status'))}")

    label = rel["neo4j_label"]
    if from_label == to_label:
        lines = [
            f"MATCH (a:SchemaMeta {{name: {_lit(from_label)}}})",
            f"MERGE (a)-[r:{label}]->(a)",
        ]
    else:
        lines = [
            f"MATCH (a:SchemaMeta {{name: {_lit(from_label)}}}), "
            f"(b:SchemaMeta {{name: {_lit(to_label)}}})",
            f"MERGE (a)-[r:{label}]->(b)",
        ]
    lines.append("  SET " + ", ".join(sets) + ";")
    return lines


def _header() -> list[str]:
    statuses = " or ".join(f"'{s}'" for s in RENDERED_STATUSES)
    exemplars = ", ".join(WILDCARD_EXEMPLARS)
    return [
        "// " + "=" * 77,
        "// schema_graph.cypher  —  DryDocs schema meta-graph  (GENERATED — DO NOT EDIT)",
        "//",
        "// GENERATED deterministically from drydocs_core/ontology/relationship_vocabulary.yaml",
        "// (the confirmed source of truth for edge meaning) by:",
        "//     poetry run python scripts/render_schema_graph.py",
        "// Drift guard: tests/unit/test_schema_graph.py re-renders the vocabulary",
        "// in-memory and fails if this committed file does not match. To change the",
        "// schema picture, edit the vocabulary (via the HITL gate where meaning",
        "// changes), then regenerate. No timestamps — the render is deterministic.",
        "//",
        "// One exemplar node per participating node label (real label + :SchemaMeta",
        "// marker) and one exemplar relationship per vocabulary entry (real",
        "// relationship type), so the full declared schema renders in Neo4j Browser:",
        "//     CALL db.schema.visualization();",
        "// or browse the meta-graph directly:",
        "//     MATCH p = (:SchemaMeta)-[]->(:SchemaMeta) RETURN p;",
        "//",
        "// TARGET DATABASE: ddschema — NOT drydocs.  Apply with:",
        "//     drydocs bootstrap-schema-graph",
        "// TWO DIFFERENT GRAPHS (SME direction): this one describes LABELS and",
        "// RELATIONSHIP TYPES, the drydocs graph holds code and operational rows, and",
        "// their constraints are not the same constraints. Concretely — every exemplar",
        "// below carries the REAL label beside :SchemaMeta, so running this file",
        "// against drydocs violates controlmjob_key (NODE KEY on folder_id/job_id;",
        "// a NODE KEY enforces EXISTENCE and the exemplar carries only `name`).",
        "// To remove the meta-graph:  MATCH (n:SchemaMeta) DETACH DELETE n;",
        "//",
        "// Inclusion rule (drydocs_core/ontology/schema_graph.py):",
        f"//   * entries with status {statuses} render (status is carried on",
        "//     each edge as r.status); 'deprecated' and 'removed' entries are excluded.",
        '//   * pipe-union endpoints ("A | B") render one edge per alternative.',
        '//   * wildcard from_node "*" renders representative edges from fixed',
        f"//     exemplars ({exemplars}) — in the real",
        "//     graph BaseLoader writes that edge for every node label.",
        "//   * nodes: only labels referenced by a rendered relationship; class /",
        "//     dual_class / prov_type come from node_classifications (labels without",
        "//     a classification entry render name-only).",
        "//   * entry notes/prose stay in the vocabulary — this file carries structure.",
        "//",
        "// Node properties:  name, class (CURIE per namespaces.py), dual_class, prov_type",
        "// Edge properties:  vocab_id, role, prov_maps_to, sosa_maps_to, domain, status",
        "// " + "=" * 77,
    ]


def render_schema_graph(vocab_path: str | Path = DEFAULT_VOCAB_PATH) -> str:
    """Render the vocabulary to the schema meta-graph Cypher text. Pure/offline."""
    vocab_path = Path(vocab_path)
    if not vocab_path.exists():
        raise SchemaGraphError(f"vocabulary source not found: {vocab_path}")
    vocab = yaml_fragments.load_yaml_source(vocab_path) or {}
    classifications: list[dict[str, Any]] = vocab.get("node_classifications") or []
    relationships: list[dict[str, Any]] = vocab.get("local_relationships") or []

    rendered = [r for r in relationships if r.get("status") in RENDERED_STATUSES]
    if not rendered:
        raise SchemaGraphError(
            f"no {'/'.join(RENDERED_STATUSES)} local_relationships found in {vocab_path}"
        )

    # Expand entries into concrete (from, to) pairs; collect referenced labels in
    # first-reference order; refuse ambiguous duplicate (from, label, to) triples
    # (two entries would MERGE into ONE edge and silently overwrite vocab_id).
    expanded: list[tuple[dict[str, Any], list[tuple[str, str]], bool]] = []
    referenced: dict[str, None] = {}
    seen_triples: dict[tuple[str, str, str], str] = {}
    for rel in rendered:
        rel_id = rel.get("id")
        if not rel_id:
            raise SchemaGraphError(f"local_relationship without an id: {rel!r}")
        label = rel.get("neo4j_label")
        if not isinstance(label, str) or not _IDENTIFIER.match(label):
            raise SchemaGraphError(f"[{rel_id}] neo4j_label {label!r} is not a valid identifier")
        froms, wildcard = _endpoint_labels(rel, "from_node")
        tos, _ = _endpoint_labels(rel, "to_node")
        pairs = [(f, t) for f in froms for t in tos]
        for from_label, to_label in pairs:
            referenced.setdefault(from_label)
            referenced.setdefault(to_label)
            triple = (from_label, label, to_label)
            prior = seen_triples.get(triple)
            if prior is not None and prior != rel_id:
                raise SchemaGraphError(
                    f"duplicate edge triple {triple}: entries '{prior}' and '{rel_id}' "
                    "would MERGE into one edge"
                )
            seen_triples[triple] = rel_id
        expanded.append((rel, pairs, wildcard))

    by_label: dict[str, dict[str, Any]] = {}
    for entry in classifications:
        lbl = entry.get("label")
        if isinstance(lbl, str) and lbl not in by_label:
            by_label[lbl] = entry
    classified_order = [
        lbl
        for lbl in dict.fromkeys(e.get("label") for e in classifications)
        if isinstance(lbl, str) and lbl in referenced
    ]
    unclassified_order = [lbl for lbl in referenced if lbl not in by_label]

    lines: list[str] = []
    lines.extend(_header())
    lines.append("")
    lines.append(_rule("Constraint (ddschema's own — describes LABELS, not rows)"))
    lines.append("")
    lines.append("// The only constraint this graph needs: one exemplar per label. It is")
    lines.append("// deliberately NOT in drydocs_core/schema/constraints.cypher — that file")
    lines.append("// constrains the operational graph, and the two databases do not share a")
    lines.append("// constraint set. tests/unit/test_schema.py's EXPECTED_CONSTRAINTS")
    lines.append("// therefore does not move.")
    lines.append(
        "CREATE CONSTRAINT schemameta_name IF NOT EXISTS "
        "FOR (n:SchemaMeta) REQUIRE n.name IS UNIQUE;"
    )
    lines.append("")
    lines.append(_rule("Node labels"))
    lines.append("")
    for lbl in classified_order:
        lines.extend(_node_statement(lbl, by_label[lbl]))
    for lbl in unclassified_order:
        lines.extend(_node_statement(lbl, None))
    lines.append("")
    lines.append(_rule("Relationships (one exemplar edge per vocabulary entry)"))

    current_domain: object = object()  # sentinel that never equals a real domain
    for rel, pairs, wildcard in expanded:
        domain = rel.get("domain")
        if domain != current_domain:
            lines.append("")
            lines.append(_rule(f"domain: {domain}"))
            current_domain = domain
        if wildcard:
            lines.append("")
            lines.append(f"// {rel.get('id')}: from_node \"*\" — representative exemplar edges;")
            lines.append("// in the real graph this edge exists on every node label.")
        for from_label, to_label in pairs:
            lines.append("")
            lines.extend(_edge_statement(rel, from_label, to_label))

    return "\n".join(lines) + "\n"


def write_schema_graph(
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    out_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Render ``vocab_path`` and write the Cypher to ``out_path``. Returns the path."""
    text = render_schema_graph(vocab_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" — schema_graph.cypher is a COMMITTED, drift-checked render, so
    # it is the Idea-121 class (Idea-129 for the snapshot half). Missed by both
    # earlier sweeps and caught by its own `git add` CRLF warning while committing
    # the G98 consequences.
    out_path.write_text(text, encoding="utf-8", newline="\n")
    return out_path
