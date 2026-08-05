"""O11 QuerySpec registry + export tests — pure handlers over a duck-typed
runner (the drydocs-api offline idiom): no server, no driver, no FastAPI."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

import pytest

from drydocs_api.exports import (
    WATERMARK_COLUMN,
    ExportLedger,
    UnknownExportError,
    banner_text,
    export_manifest,
    export_spec,
    filename_for,
    list_specs,
    run_spec,
)
from drydocs_api.guard import ElementIdRejected, ensure_no_element_ids, is_write_cypher
from drydocs_api.queries import ParamValidationError
from drydocs_api.query_specs import (
    CLASSIFICATIONS,
    QUERY_SPECS,
    SPEC_DATABASES,
    UnknownSpecError,
    query_spec,
)
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError


class FakeRunner:
    def __init__(self, keys=None, rows=None):
        self.calls: list[tuple[str, dict, str]] = []
        self._keys = keys or ["name"]
        self._rows = rows if rows is not None else [{"name": "demo"}]

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        return self._keys, self._rows


class FakeStreamingRunner(FakeRunner):
    """Streams rows lazily and records that the stream (not run) was used."""

    def __init__(self, keys=None, rows=None):
        super().__init__(keys, rows)
        self.streamed = False

    def stream(self, cypher, params, database):
        self.streamed = True
        self.calls.append((cypher, dict(params), database))
        return self._keys, iter(self._rows)


def _token(store: InMemorySessionStore) -> str:
    return store.issue("jdoe4821").token


# ── registry invariants ──────────────────────────────────────────────────────


def test_every_spec_is_versioned_read_only_and_classified():
    assert QUERY_SPECS, "registry is empty"
    for spec in QUERY_SPECS.values():
        assert re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+\.v\d+$", spec.id)
        assert spec.database in SPEC_DATABASES
        assert spec.classification in CLASSIFICATIONS
        assert spec.columns
        assert is_write_cypher(spec.cypher) is None


def test_mappings_coverage_spec_registered():
    """O13: the stewardship coverage grid binds to its versioned spec — status
    (resolved/unresolved/conflict) and match_method (the K2 tier evidence) are
    grid-visible columns, keyed folder_id/job_id for the assign dialog."""
    spec = query_spec("mappings.attribution-coverage.v1")
    assert spec.database == "drydocs"
    names = {c.name for c in spec.columns}
    assert {"status", "match_method", "folder_id", "job_id", "app_id"} <= names


def test_lineage_frames_have_specs():
    """O10: the Lineage tabs bind to specs on `drydocs` — where the curated
    lineage writer lands (G30 ruling 2026-07-26; ADR 0002 "Residency
    clarification"). They were pointed at `ddlineage`, which was written by
    nothing (retired at X1, 2026-08-04). They still return zero rows until the
    lineage live-load gate flips the m3_* entries — that gate, not the
    database, is why."""
    for spec_id in ("lineage.hops.v1", "lineage.data-assets.v1", "lineage.schema-definition.v1"):
        assert query_spec(spec_id).database == "drydocs"


def test_explorer_frames_have_specs():
    """The Explorer tabs bind to versioned specs (O11 acceptance; jobs/
    conditions bumped v2 at the 2026-07-21 SME correction — folder resolved
    through :ControlMFolder, data_center via SCHEDULED_ON)."""
    for spec_id in (
        "explorer.applications.v1",
        "explorer.folder-applications.v1",
        "explorer.controlm-app-codes.v1",
        "explorer.jobs.v2",
        "explorer.conditions.v2",
        "explorer.servers.v1",
    ):
        assert spec_id in QUERY_SPECS


def test_jobs_spec_resolves_folder_node_and_data_center():
    """The SME correction itself: the Jobs frame reads the :ControlMFolder
    node's real name and the DATA_CENTER server via SCHEDULED_ON — not the
    job's denormalized folder_id."""
    spec = QUERY_SPECS["explorer.jobs.v2"]
    assert ":ControlMFolder" in spec.cypher and "CONTAINS_JOB" in spec.cypher
    assert "SCHEDULED_ON" in spec.cypher and ":ControlMServer" in spec.cypher
    assert "data_center" in [c.name for c in spec.columns]


def test_folder_applications_spec_uses_gated_edges():
    """Folder -> BusinessApplication rides the RULED folder-grain edge only
    (K7/K8, re-bound per gate §A2), with the §B3 origin disclosed."""
    spec = QUERY_SPECS["explorer.folder-applications.v1"]
    assert "BELONGS_TO_APPLICATION {role: 'seal_app_ref'}" in spec.cypher
    assert "WAS_ASSOCIATED_WITH" not in spec.cypher, "the job-grain derivation is retired (§A1)"
    assert "HAS_PORT" in spec.cypher and "BatchProcessing" in spec.cypher
    assert ":BusinessApplication" in spec.cypher
    assert "origin" in [c.name for c in spec.columns]


def test_app_codes_spec_classifies_both_mapping_patterns():
    """The SME two-pattern model (2026-07-21), re-bound to the ruled
    folder-grain edges at K8: dedicated codes map direct, shared platform
    codes fan out to many applications. The authoritative mapping is the K9
    defined-mapping store; this spec stays the observed cross-check."""
    spec = QUERY_SPECS["explorer.controlm-app-codes.v1"]
    assert ":ControlMApplication" in spec.cypher and "CONTAINS_FOLDER" in spec.cypher
    assert "BELONGS_TO_APPLICATION {role: 'seal_app_ref'}" in spec.cypher
    assert "WAS_ASSOCIATED_WITH" not in spec.cypher, "the job-grain derivation is retired (§A1)"
    assert "direct (dedicated code)" in spec.cypher
    assert "shared platform code" in spec.cypher
    assert "unmapped" in spec.cypher
    assert "mapping_pattern" in [c.name for c in spec.columns]


# ── O27 authoring conventions (drydocs_api/AUTHORING.md) ────────────────────

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_AUTHORING_DOC = _REPO_ROOT / "drydocs_api" / "AUTHORING.md"
_CONSTRAINTS = _REPO_ROOT / "drydocs_core" / "schema" / "constraints.cypher"


def test_no_spec_returns_a_graph_internal_element_id():
    """O27 rule 3. Element ids are Neo4j-internal pointers that change on
    restore and re-load, so one in a deep link or export manifest later
    resolves to a DIFFERENT node — a silent wrong answer, not an error."""
    for spec in QUERY_SPECS.values():
        ensure_no_element_ids(spec.cypher, f"spec '{spec.id}'")


def test_element_id_guard_catches_both_spellings_and_spares_source_ids():
    """Assert the RULE, not just today's registry — the registry is currently
    clean, so a scan of it alone would pass even if the detector were broken.
    Cypher function names are case-insensitive, hence the spelling cases."""
    for bad in (
        "MATCH (n) RETURN elementId(n) AS x",
        "MATCH (n) RETURN ElementId(n) AS x",
        "MATCH (n) RETURN id(n) AS x",
        "MATCH (n) RETURN ID(n) AS x",
        "MATCH (n) RETURN id (n) AS x",
    ):
        with pytest.raises(ElementIdRejected):
            ensure_no_element_ids(bad, "probe")

    # Source-system ids are declared in constraints.cypher and are CORRECT to
    # return. A guard that flagged these would push authors toward element ids.
    for good in (
        "MATCH (j:ControlMJob) RETURN j.job_id AS job_id, j.folder_id AS folder_id",
        "MATCH (a:BusinessApplication) RETURN a.app_id AS app_id",
        "MATCH (r:JobRun) RETURN r.run_id AS run_id, toString(r.started_at) AS started_at",
    ):
        ensure_no_element_ids(good, "probe")


def _declared_keys() -> dict[str, list[set[str]]]:
    """label -> every declared key property-set (NODE KEY or UNIQUE)."""
    text = _CONSTRAINTS.read_text(encoding="utf-8")
    keys: dict[str, list[set[str]]] = {}
    for label, expr in re.findall(
        r"FOR\s+\(\w+:(\w+)\)\s+REQUIRE\s+(.+?)\s+IS\s+(?:NODE KEY|UNIQUE)", text
    ):
        keys.setdefault(label, []).append(set(re.findall(r"\.(\w+)", expr)))
    return keys


def _documented_namespace_table() -> list[tuple[str, set[str], str]]:
    """(label, key properties, namespace) rows from AUTHORING.md rule 2."""
    rows = []
    for label, key_expr, namespace in re.findall(
        r"^\|\s*`(\w+)`\s*\|\s*`([^`]+)`[^|]*\|\s*(.+?)\s*\|\s*$",
        _AUTHORING_DOC.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        rows.append((label, set(re.findall(r"\w+", key_expr)), namespace.strip("* ")))
    return rows


def test_authoring_doc_namespace_table_matches_declared_keys():
    """O27 rule 2 ties the external-ref namespace to the DECLARED uniqueness
    scope, so the doc's table is only trustworthy if it still agrees with
    constraints.cypher. Without this the table is a record checkable only
    against itself — it would go stale the first time a key changes.

    This also pins the correction O27 needed: the item was groomed as
    "namespace = data center", which holds for exactly ONE node kind
    (ControlMHostGroup). Jobs and conditions are folder-scoped.
    """
    declared = _declared_keys()
    rows = _documented_namespace_table()
    assert len(rows) >= 6, "rule 2's namespace table did not parse — did its shape change?"

    for label, doc_props, namespace in rows:
        assert label in declared, f"AUTHORING.md documents {label}, constraints.cypher has no key"
        assert doc_props in declared[label], (
            f"AUTHORING.md says {label}'s key is {sorted(doc_props)}, "
            f"constraints.cypher declares {[sorted(k) for k in declared[label]]}"
        )
        # The load-bearing invariant: a namespace is needed EXACTLY when the
        # name alone is not unique, i.e. when the declared key is composite.
        if namespace == "none":
            assert len(doc_props) == 1, f"{label}: no namespace, but a composite key"
        else:
            assert len(doc_props) > 1, f"{label}: namespace '{namespace}' but a single-prop key"
            normalized = namespace.replace(" ", "_")
            assert any(
                normalized in p for p in doc_props
            ), f"{label}: namespace '{namespace}' names no part of its key {sorted(doc_props)}"


def test_authoring_conventions_are_discoverable_from_the_registry():
    """The acceptance is 'discoverable from query_specs.py' — a conventions doc
    nobody can find from the file it governs is not a convention."""
    import drydocs_api.query_specs as qs

    assert _AUTHORING_DOC.exists()
    assert "AUTHORING.md" in (qs.__doc__ or "")


def test_unknown_spec_fails_closed():
    with pytest.raises(UnknownSpecError):
        query_spec("explorer.nonsense.v9")


def test_list_specs_exposes_cypher_and_classification():
    listed = {s["id"]: s for s in list_specs()}
    spec = QUERY_SPECS["explorer.jobs.v2"]
    assert listed[spec.id]["cypher"] == spec.cypher  # "Copy as Cypher" source
    assert listed[spec.id]["classification"] == spec.classification
    assert listed["context.label-census.v1"]["watermarked"] is True


# ── run path ─────────────────────────────────────────────────────────────────


def test_run_spec_routes_to_spec_database_and_requires_auth():
    store = InMemorySessionStore()
    runner = FakeRunner()
    out = run_spec("explorer.jobs.v2", {}, _token(store), store, runner)
    assert runner.calls[0][2] == "drydocs"
    assert runner.calls[0][1] == {"limit": 500}  # default applied
    assert out["classification"] == "internal"
    assert out["watermarked"] is False
    with pytest.raises(InvalidTokenError):
        run_spec("explorer.jobs.v2", {}, "bogus", store, runner)


def test_run_spec_rejects_unknown_params():
    store = InMemorySessionStore()
    with pytest.raises(ParamValidationError):
        run_spec("explorer.jobs.v2", {"evil": 1}, _token(store), store, FakeRunner())


def test_ddcontext_results_carry_grid_visible_watermark():
    store = InMemorySessionStore()
    runner = FakeRunner(keys=["labels", "count"], rows=[{"labels": ["X"], "count": 2}])
    out = run_spec("context.label-census.v1", {}, _token(store), store, runner)
    assert out["watermarked"] is True
    assert WATERMARK_COLUMN in out["keys"]
    assert all(r[WATERMARK_COLUMN].startswith("SYNTHESIZED") for r in out["rows"])


# ── classification rules ─────────────────────────────────────────────────────


def test_filename_prefix_rule():
    internal = QUERY_SPECS["explorer.jobs.v2"]
    assert filename_for(internal, "csv") == "INTERNAL__explorer.jobs.v2.csv"
    public = QUERY_SPECS["context.label-census.v1"]
    assert filename_for(public, "jsonl") == "context.label-census.v1.jsonl"


def test_banner_only_for_internal_tiers():
    assert banner_text(QUERY_SPECS["explorer.jobs.v2"]) is not None
    assert banner_text(QUERY_SPECS["context.label-census.v1"]) is None


# ── export path ──────────────────────────────────────────────────────────────


def test_csv_export_streams_banner_header_rows_and_registers_manifest():
    store = InMemorySessionStore()
    ledger = ExportLedger()
    runner = FakeStreamingRunner(
        keys=["job_name", "folder", "data_center", "job_id"],
        rows=[
            {"job_name": "J1", "folder": "DEMO-HL-DAILY", "data_center": "DC-E", "job_id": "1"},
            {"job_name": "J2", "folder": "DEMO-HL-DAILY", "data_center": "DC-E", "job_id": "2"},
        ],
    )
    token = _token(store)
    job = export_spec("explorer.jobs.v2", {}, "csv", token, store, runner, ledger)

    # manifest must NOT exist until the stream completes
    with pytest.raises(UnknownExportError):
        ledger.manifest(job.export_id)

    lines = "".join(job.chunks).splitlines()
    assert runner.streamed, "export must use the streaming runner path"
    assert lines[0].startswith("# CLASSIFICATION: INTERNAL")  # banner row
    assert lines[1] == "job_name,folder,data_center,job_id"  # header
    assert lines[2].startswith("J1,") and len(lines) == 4

    manifest = export_manifest(job.export_id, token, store, ledger)
    spec = QUERY_SPECS["explorer.jobs.v2"]
    assert manifest["query_spec"] == spec.id
    assert manifest["cypher_sha256"] == hashlib.sha256(spec.cypher.encode()).hexdigest()
    assert manifest["params"] == {"limit": 500}
    assert manifest["database"] == "drydocs"
    assert manifest["row_count"] == 2
    assert manifest["classification"] == "internal"
    assert manifest["exported_by"] == "jdoe4821"
    assert manifest["executed_at"]


def test_jsonl_export_watermarks_ddcontext_and_reports_trust_tier():
    store = InMemorySessionStore()
    ledger = ExportLedger()
    runner = FakeRunner(keys=["labels", "count"], rows=[{"labels": ["X"], "count": 2}])
    token = _token(store)
    job = export_spec("context.label-census.v1", {}, "jsonl", token, store, runner, ledger)
    lines = "".join(job.chunks).splitlines()
    assert len(lines) == 1  # internal-public -> no banner object
    row = json.loads(lines[0])
    assert row[WATERMARK_COLUMN].startswith("SYNTHESIZED")

    manifest = export_manifest(job.export_id, token, store, ledger)
    assert "SYNTHESIZED" in manifest["trust_tiers_present"]
    assert job.filename == "context.label-census.v1.jsonl"


def test_export_rejects_unknown_format_and_requires_auth():
    store = InMemorySessionStore()
    ledger = ExportLedger()
    with pytest.raises(ValueError):
        export_spec("explorer.jobs.v2", {}, "parquet", _token(store), store, FakeRunner(), ledger)
    with pytest.raises(InvalidTokenError):
        export_spec("explorer.jobs.v2", {}, "csv", "bogus", store, FakeRunner(), ledger)


def test_ledger_is_bounded():
    ledger = ExportLedger(capacity=2)
    for i in range(3):
        ledger.complete(f"e{i}", {"i": i})
    with pytest.raises(UnknownExportError):
        ledger.manifest("e0")
    assert ledger.manifest("e2") == {"i": 2}
