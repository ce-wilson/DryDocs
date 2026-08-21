"""R20 — registered query specs stay grounded in the vocabulary they are built on.

Two guards, two failure classes:

* STATIC (always runs): every label, relationship type and property a spec
  names is DECLARED — labels in ``node_classifications`` (plus the four
  infrastructure labels the ontology does not register: SchemaMeta, Uncertain,
  JobRun, AgentRun), relationship types in ``local_relationships`` with a
  non-deprecated entry; a type that is PLANNED ONLY may be named solely when
  the spec lists it in ``planned_terms`` (a written-down degradation). This is
  the class the 2026-08-21 audit found: ``ownership.teams.v1`` asked a
  ``DEVELOPS`` edge that was never registered and answered 0 for every team.

* LIVE (skips, naming the venue, when no database is reachable — J18): against
  the connected graph, every term a spec names either exists in
  ``db.labels()`` / ``db.relationshipTypes()`` / ``db.propertyKeys()`` or is
  absent for a reason the test can name. DRIFT — and a failure — is a term
  absent live whose writing loader HAS run there (a :JobRun for the loader the
  vocabulary entry names) and which NO template in the repo writes any more:
  the graph was built by an older vocabulary. Absent-and-never-loaded, and
  absent-because-the-template-writes-it-conditionally (CONTAINS_FOLDER needs
  the Oracle header-row join the bundled sample lacks), are REPORTED, not
  failed — on a partially loaded desktop that is the normal state, and it is
  exactly what the 2026-08-20 empty answer was: a load gap presenting as 0.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict

import pytest

from drydocs_api.query_specs import QUERY_SPECS, QuerySpec
from drydocs_core.ontology.schema_graph import DEFAULT_VOCAB_PATH
from drydocs_core.yaml_fragments import load_yaml_source

#: labels that are infrastructure, not ontology: the meta-graph marker (C8), the
#: uncertain realm (ADR 0011), loader and agent telemetry. Registered here so a
#: spec may name them and the guard still refuses any OTHER undeclared label.
INFRASTRUCTURE_LABELS = frozenset({"SchemaMeta", "Uncertain", "JobRun", "AgentRun"})

_NODE = re.compile(r"\(\s*\w*\s*:\s*([A-Za-z_][\w:]*)")
_LABEL_TEST = re.compile(
    r"(?<=\s)[a-z]\w*:([A-Z][A-Za-z0-9_]*)"
)  # WHERE NOT f:SchemaMeta, never [r:TYPE
_REL = re.compile(r"\[\s*\w*\s*:\s*([A-Za-z_][\w|]*)")
_PROP = re.compile(r"\b([a-z]\w*)\.([a-z_][a-z0-9_]*)")


def spec_terms(spec: QuerySpec) -> tuple[set[str], set[str], set[str]]:
    cy = spec.cypher
    labels: set[str] = set()
    for m in _NODE.findall(cy):
        labels.update(m.split(":"))
    labels.update(_LABEL_TEST.findall(cy))
    rels: set[str] = set()
    for m in _REL.findall(cy):
        rels.update(m.split("|"))
    props = {p for _, p in _PROP.findall(cy)}
    return labels, rels, props


def _vocab():
    doc = load_yaml_source(DEFAULT_VOCAB_PATH)
    labels = {n["label"] for n in doc["node_classifications"]}
    rels: dict[str, list[dict]] = defaultdict(list)
    for r in doc["local_relationships"]:
        if r.get("status") != "deprecated":
            rels[r["neo4j_label"]].append(r)
    return labels, rels


def _live_statuses(entries: list[dict]) -> set[str]:
    return {e["status"] for e in entries}


REPO = DEFAULT_VOCAB_PATH.parents[2]
WRITER_GLOBS = (
    "drydocs/loaders/cypher/*.cypher",
    "drydocs/loaders/*.py",
    "drydocs_core/schema/*.cypher",
    "drydocs_lineage/*.py",
    "drydocs_lineage/**/*.py",
)


def _writer_text() -> str:
    """Every template that can write an edge, concatenated — the census of what
    the repo still KNOWS how to write. A term named by a spec and by the
    vocabulary but by no writer is a term the graph can only carry from an
    older build."""
    chunks = []
    for pattern in WRITER_GLOBS:
        for path in sorted(REPO.glob(pattern)):
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


# -- static -----------------------------------------------------------------------


def test_every_spec_names_only_declared_vocabulary() -> None:
    decl_labels, decl_rels = _vocab()
    problems: list[str] = []
    for sid, spec in QUERY_SPECS.items():
        labels, rels, _ = spec_terms(spec)
        for label in sorted(labels - decl_labels - INFRASTRUCTURE_LABELS):
            problems.append(f"{sid}: label :{label} is not in node_classifications")
        for rel in sorted(rels):
            entries = decl_rels.get(rel)
            if not entries:
                problems.append(f"{sid}: relationship {rel} has no non-deprecated vocabulary entry")
                continue
            statuses = _live_statuses(entries)
            if statuses <= {"planned"} and rel not in spec.planned_terms:
                problems.append(
                    f"{sid}: {rel} is PLANNED ONLY (no loader) and not written down in "
                    "planned_terms — a spec that asks it answers 0 while meaning 'not loadable yet'"
                )
        for rel in spec.planned_terms:
            entries = decl_rels.get(rel, [])
            if entries and not (_live_statuses(entries) <= {"planned"}):
                problems.append(
                    f"{sid}: planned_terms lists {rel}, which is no longer planned-only — remove it"
                )
            if rel not in rels:
                problems.append(f"{sid}: planned_terms lists {rel}, which the cypher does not name")
    assert not problems, "\n".join(problems)


def test_every_active_spec_term_still_has_a_writer() -> None:
    """A spec may only ask an ACTIVE relationship type that some template in the
    repo still writes. A type the vocabulary keeps active but no writer names is
    the other half of drift: the registry says it exists, the graph can only
    carry it from an older build, and a spec answers 0 for it forever."""
    _, decl_rels = _vocab()
    writers = _writer_text()
    problems = []
    for sid, spec in QUERY_SPECS.items():
        _, rels, _ = spec_terms(spec)
        for rel in sorted(rels):
            statuses = _live_statuses(decl_rels.get(rel, []))
            if statuses & {"active", "applied"} and f":{rel}" not in writers:
                problems.append(
                    f"{sid}: {rel} is active in the vocabulary but no writer template names it"
                )
    assert not problems, "\n".join(problems)


def test_the_develops_regression_is_pinned() -> None:
    """The audit's concrete finding: no spec may ask DEVELOPS; the developer
    attribution is WAS_ATTRIBUTED_TO {role: 'developed_by'} (arch_develops)."""
    teams = QUERY_SPECS["ownership.teams.v1"].cypher
    assert "DEVELOPS" not in teams
    assert "WAS_ATTRIBUTED_TO {role: 'developed_by'}" in teams
    assert not any("[:DEVELOPS]" in s.cypher for s in QUERY_SPECS.values())


def test_planned_leg_on_the_cascade_is_written_down() -> None:
    spec = QUERY_SPECS["mappings.catalog-cascade.v1"]
    assert spec.planned_terms == ("HAS_APPLICATION",)
    assert "OPTIONAL MATCH (p)-[:HAS_APPLICATION]" in spec.cypher


# -- live (J18: skip names the venue) ---------------------------------------------


_VENUE: dict[str, str] = {"name": "unresolved"}


def _venue() -> str:
    """The machine/container/database the live half ran on (J18) — from the
    resolved settings, so a .env-configured desktop is named, not 'unset'."""
    try:
        from drydocs_core.config import load_settings

        cfg, _, _ = load_settings()
        return f"{cfg.uri} / {cfg.database} (host {os.environ.get('COMPUTERNAME') or os.uname().nodename})"
    except Exception:
        return "settings unresolved"


@pytest.fixture(scope="module")
def live_client():
    try:
        from drydocs_core.config import load_settings
        from drydocs_core.neo4j_client import Neo4jClient

        cfg, _, _ = load_settings()
        pw = cfg.password.get_secret_value()
        if not pw:
            pytest.skip(f"no NEO4J_PASSWORD — live spec smoke skipped (venue {_venue()})")
        client = Neo4jClient(cfg.uri, cfg.user, pw, cfg.database).__enter__()
        client.run("RETURN 1 AS ok")
    except Exception as exc:  # — any failure to reach the graph is a skip, named
        pytest.skip(
            f"no reachable Neo4j at {_venue()}: {type(exc).__name__} — live spec smoke skipped"
        )
    yield client
    client.__exit__(None, None, None)


def _loader_stem(name: str) -> str:
    return re.sub(r"\.v\d+$", "", name).replace(".cypher", "")


def test_live_schema_still_carries_every_loaded_spec_term(live_client) -> None:
    cli = live_client
    live_labels = {r["l"] for r in cli.run("CALL db.labels() YIELD label AS l RETURN l")}
    live_rels = {
        r["t"] for r in cli.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t")
    }
    live_props = {r["p"] for r in cli.run("CALL db.propertyKeys() YIELD propertyKey AS p RETURN p")}
    ran = {
        _loader_stem(r["n"])
        for r in cli.run("MATCH (j:JobRun) RETURN DISTINCT j.loader AS n")
        if r["n"]
    }
    _, decl_rels = _vocab()

    def writer_ran(rel: str) -> bool | None:
        """True/False when the vocabulary names a loader for the type; None when it does not."""
        loaders = {_loader_stem(e["loader"]) for e in decl_rels.get(rel, []) if e.get("loader")}
        if not loaders:
            return None
        return any(stem in ran for stem in loaders)

    writers = _writer_text()
    drift: list[str] = []
    not_loaded: list[str] = []
    for sid, spec in QUERY_SPECS.items():
        labels, rels, props = spec_terms(spec)
        for rel in sorted(rels):
            if rel in live_rels:
                continue
            status = writer_ran(rel)
            if status is True and f":{rel}" not in writers:
                # the graph was built by a template that has since stopped
                # writing this type — the live half of "vocabulary moved past"
                drift.append(
                    f"{sid}: {rel} absent live, its loader has run, and no template writes it any more"
                )
            elif status is True:
                not_loaded.append(
                    f"{sid}: {rel} (loader ran; the template writes it conditionally and no row qualified)"
                )
            else:
                not_loaded.append(f"{sid}: {rel} (loader not run here)")
        for label in sorted(labels - live_labels - INFRASTRUCTURE_LABELS):
            not_loaded.append(f"{sid}: :{label} (not in db.labels())")
        for prop in sorted(props - live_props):
            not_loaded.append(f"{sid}: .{prop} (not in db.propertyKeys())")
    # never silent: the census is printed so a partial desktop can read what it lacks
    print(f"\n[R20 live smoke @ {_venue()}] drift={len(drift)} not-loaded-here={len(not_loaded)}")
    for line in not_loaded:
        print("  not loaded:", line)
    assert not drift, "\n".join(drift)
