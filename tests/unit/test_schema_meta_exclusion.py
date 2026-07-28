"""O33 — the :SchemaMeta exemplar audit (read side + the residual write path).

``schema_graph.cypher`` MERGEs a ``:SchemaMeta:<RealLabel>`` exemplar per
participating node label, KEYLESS by design, and exemplar EDGES between them —
including property-qualified ones (``{role: 'seal_app_ref'}``). Whenever the
meta-graph is applied (manually, by design), an unguarded QuerySpec returns
the exemplars as phantom null-keyed rows, and a name-keyed loader MATCH can
even attach a real edge to an exemplar. These tests audit ALL specs against
ALL stamped labels, parsed from the committed meta-graph itself so a future
regeneration re-audits automatically.

Root-fix considered and NOT taken (the O33 notes option): giving exemplars
fake key properties would make them satisfy the key-based loader guards —
the exact failure family Q8/L17 closed — so keyless-plus-label-predicate is
strictly safer. The label predicate is the belt everywhere.

The live proof (meta-graph applied to a real database → every spec returns
zero rows, no guard satisfied) is tests/integration/test_meta_graph_exclusion.py.
"""
from __future__ import annotations

import re
from pathlib import Path

from drydocs_api.query_specs import QUERY_SPECS

REPO = Path(__file__).resolve().parents[2]
SCHEMA_GRAPH = REPO / "drydocs_core" / "schema" / "schema_graph.cypher"
RUNS_ON_CYPHER = REPO / "drydocs" / "loaders" / "cypher" / "runs_on_resolution.cypher"

_EXEMPLAR_RE = re.compile(r"MERGE \(n:SchemaMeta:(\w+)")
#: node-pattern label bindings — "(alias:Label" — never relationship types
_BOUND_LABEL_RE = re.compile(r"\(\s*\w*\s*:\s*([A-Za-z]\w*)")
_EXCLUSION_RE = re.compile(r"NOT\s+\w+:SchemaMeta")


def stamped_labels() -> frozenset[str]:
    return frozenset(_EXEMPLAR_RE.findall(SCHEMA_GRAPH.read_text(encoding="utf-8")))


def test_meta_graph_parses_and_covers_the_known_contaminators() -> None:
    labels = stamped_labels()
    assert len(labels) >= 40, f"exemplar parse regressed: {len(labels)} labels"
    assert {
        "BusinessApplication", "ControlMJob", "ControlMServer", "DataAsset",
        "JobRun", "Document", "Chunk", "Attribution", "DocSection", "Employee",
    } <= labels


def test_every_spec_excludes_the_exemplars() -> None:
    """The audit itself: EVERY spec must carry the rename-proof
    ``NOT <alias>:SchemaMeta`` predicate — not merely those binding a label
    this repo's meta-graph stamps today.

    Tightened 2026-07-28 (back-flow #3). The old rule exempted "unstamped"
    labels and named ServiceNowGroup as the example, which made the invariant
    depend on THIS repo's vocabulary size: the consumer's larger vocab does
    stamp :ServiceNowGroup, so its schema_graph contaminated
    ownership.escalation-routing.v1 while the producer sweep saw nothing to fix
    (PORT-REPORT-94132c80). A vocabulary is a moving target — growing it must
    not silently widen query exposure. The predicate is a no-op on a label that
    is never stamped, so requiring it everywhere costs nothing and cannot go
    stale; 22 of 23 specs already satisfied it when this was tightened.
    """
    missing = [s.id for s in QUERY_SPECS.values() if not _EXCLUSION_RE.search(s.cypher)]
    assert missing == [], (
        f"specs with no :SchemaMeta exclusion: {missing} — the predicate is required "
        "regardless of whether this repo's vocab currently stamps the bound label"
    )


def test_property_qualified_exemplar_edges_are_not_a_defense() -> None:
    """The subtle case: the meta-graph's WAS_ASSOCIATED_WITH exemplar edge
    CARRIES role='seal_app_ref', so the role predicate alone would have
    matched the exemplar chain — the two specs riding that edge must carry
    the label predicate explicitly."""
    for spec_id in ("explorer.folder-applications.v1", "mappings.attribution-coverage.v1"):
        assert _EXCLUSION_RE.search(QUERY_SPECS[spec_id].cypher), spec_id


def test_runs_on_resolution_never_touches_exemplars() -> None:
    """The one WRITE path a name-keyed exemplar could reach: the exemplar
    :ControlMHostGroup has name='ControlMHostGroup', so a job whose node_id
    equals the label string would have edged to the schema exemplar. Both
    the resolution cypher and the coverage census exclude exemplars."""
    from drydocs.loaders.runs_on_resolution import _COVERAGE_QUERY, _MULTI_DC_QUERY

    cypher = RUNS_ON_CYPHER.read_text(encoding="utf-8")
    assert "NOT g:SchemaMeta" in cypher and "NOT h:SchemaMeta" in cypher
    assert "NOT j:SchemaMeta" in cypher
    assert "NOT j:SchemaMeta" in _COVERAGE_QUERY
    assert "NOT g:SchemaMeta" in _COVERAGE_QUERY and "NOT h:SchemaMeta" in _COVERAGE_QUERY
    assert "NOT g:SchemaMeta" in _MULTI_DC_QUERY


def test_loader_guard_probes_exclude_exemplars() -> None:
    """The write-side clause: every whole-registry prereq guard (the Q8 /
    batch_port / L17 family) pairs the label predicate with a key-not-null
    clause, so a keyless exemplar can never wave an empty registry through."""
    import inspect

    from drydocs.loaders import batch_port_orchestrator, bmc_docs, doc_traceability

    for module in (batch_port_orchestrator, bmc_docs, doc_traceability):
        source = inspect.getsource(module)
        assert ":SchemaMeta" in source, module.__name__
        assert "IS NOT NULL" in source, module.__name__
