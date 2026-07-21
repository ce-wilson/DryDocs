"""O11 QuerySpec registry + export tests — pure handlers over a duck-typed
runner (the drydocs-api offline idiom): no server, no driver, no FastAPI."""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from drydocs_api.exports import (
    ExportLedger,
    UnknownExportError,
    WATERMARK_COLUMN,
    banner_text,
    export_manifest,
    export_spec,
    filename_for,
    list_specs,
    run_spec,
)
from drydocs_api.queries import ParamValidationError
from drydocs_api.query_specs import (
    CLASSIFICATIONS,
    QUERY_SPECS,
    SPEC_DATABASES,
    UnknownSpecError,
    query_spec,
)
from drydocs_api.guard import is_write_cypher
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


def test_explorer_frames_have_specs():
    """The Explorer tabs bind to versioned specs (O11 acceptance; jobs/
    conditions bumped v2 at the 2026-07-21 SME correction — folder resolved
    through :ControlMFolder, data_center via SCHEDULED_ON)."""
    for spec_id in (
        "explorer.applications.v1",
        "explorer.folder-applications.v1",
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
    """Folder -> BusinessApplication rides the gated attribution edges only."""
    spec = QUERY_SPECS["explorer.folder-applications.v1"]
    assert "WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}" in spec.cypher
    assert "CONTAINS_JOB" in spec.cypher
    assert ":BusinessApplication" in spec.cypher


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
    assert len(lines) == 1  # internal-public â†’ no banner object
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
