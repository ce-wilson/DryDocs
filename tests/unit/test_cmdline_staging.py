"""G39/G40 — the TEMPORARY cmd-line job-detail staging store + parse.

Synthetic fixtures only (house rule: real command lines are Internal and
never enter the repo). The fake client stands in for the graph read; the
SQLite round-trip is real.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from drydocs.cmdline_staging import (
    PSGMGR_PROJECTION_SQL,
    RETIREMENT_NOTE,
    SCHEMA_VERSION,
    CmdlineStagingError,
    export_job_detail,
    parse_job_detail,
)

_GUID = "12345678-1234-1234-1234-123456789abc"

#: synthetic graph rows (the export Cypher's RETURN shape)
ROWS = [
    {"folder_id": "70001", "job_id": "1", "job_name": "SYN_DPL_DLY",
     "data_center": "P032-E0700-DMA", "task_type": "Job", "active": True,
     "cmd_line": f"/apps/dpl/dt-launcher.sh -pipeline {_GUID} -env prod -seal 70002 -i"},
    {"folder_id": "70001", "job_id": "2", "job_name": "SYN_VAR_LAUNCH",
     "data_center": "P032-E0700-DMA", "task_type": "Job", "active": True,
     # launcher hidden in a folder variable — the GUID literal still decides
     # (G15 acceptance c / G16 values-decide)
     "cmd_line": f"%%PY_LAUNCH --pipeline-id {_GUID} --aws --queue-name synq"},
    {"folder_id": "70001", "job_id": "3", "job_name": "SYN_PY",
     "data_center": "P032-E0700-DMA", "task_type": "Job", "active": False,
     "cmd_line": "python /apps/syn/etl_step.py --conf /apps/syn/etl.json"},
    {"folder_id": "70003", "job_id": "1", "job_name": "SYN_WATCHER",
     "data_center": "P045-E0700-DMB", "task_type": "Watcher", "active": True,
     "cmd_line": None},
    {"folder_id": "70003", "job_id": "2", "job_name": "SYN_UNKNOWN_BIN",
     "data_center": "P045-E0700-DMB", "task_type": "Job", "active": True,
     "cmd_line": "/apps/bin/mystery_widget --frob 7"},
    {"folder_id": "70003", "job_id": "3", "job_name": "SYN_NOOP",
     "data_center": "P045-E0700-DMB", "task_type": "Job", "active": True,
     "cmd_line": "echo done"},
]


class FakeClient:
    """Stands in for Neo4jClient.run — the export's only graph touchpoint."""

    def __init__(self, rows=ROWS):
        self.rows = rows
        self.queries = []

    def run(self, cypher, params=None, **kwargs):
        self.queries.append(cypher)
        return [dict(r) for r in self.rows]


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "job_detail.db"
    export_job_detail(FakeClient(), path)
    return path


def _q(path, sql):
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# G39 — export
# ---------------------------------------------------------------------------

def test_export_one_row_per_job_verbatim(store):
    rows = _q(store, "SELECT folder_id, job_id, task_type, cmd_line FROM job_detail "
                     "ORDER BY folder_id, job_id")
    assert len(rows) == 6
    by_key = {(r[0], r[1]): r for r in rows}
    # verbatim cmd_line, task-type discriminator, NULL for the watcher
    assert by_key[("70003", "1")][2] == "Watcher"
    assert by_key[("70003", "1")][3] is None
    assert by_key[("70001", "1")][3].startswith("/apps/dpl/dt-launcher.sh -pipeline")


def test_export_report_counts(tmp_path):
    report = export_job_detail(FakeClient(), tmp_path / "s.db")
    assert report.jobs == 6
    assert report.with_cmd_line == 5
    assert report.active == 5
    assert report.by_task_type == {"Job": 5, "Watcher": 1}
    assert "task_type" in report.summary()


def test_export_is_deterministic_and_idempotent(tmp_path):
    path = tmp_path / "s.db"
    export_job_detail(FakeClient(), path)
    first = _q(path, "SELECT * FROM job_detail ORDER BY folder_id, job_id")
    export_job_detail(FakeClient(), path)
    second = _q(path, "SELECT * FROM job_detail ORDER BY folder_id, job_id")
    assert first == second  # same graph -> same rows; re-export replaces


def test_export_meta_carries_retirement_and_psgmgr_projection(store):
    meta = dict(_q(store, "SELECT key, value FROM meta"))
    assert meta["schema_version"] == SCHEMA_VERSION
    assert meta["retirement"] == RETIREMENT_NOTE
    assert "CM_DEF_VJOB_DETAIL" in RETIREMENT_NOTE
    assert meta["psgmgr_projection"] == PSGMGR_PROJECTION_SQL
    assert "psgmgr.CM_DEF_VJOB" in meta["psgmgr_projection"]
    # variables explicitly out of scope, by design not omission
    assert "OUT OF SCOPE" in meta["variables"]


def test_export_no_timestamp_in_store(store):
    """Determinism: no wall-clock values anywhere (mapping-store contract)."""
    meta = dict(_q(store, "SELECT key, value FROM meta"))
    assert not any("20" in k and "date" in k.lower() for k in meta)
    cols = [r[1] for r in _q(store, "PRAGMA table_info(job_detail)")]
    assert "exported_at" not in cols


# ---------------------------------------------------------------------------
# G40 — parse
# ---------------------------------------------------------------------------

def test_parse_refuses_missing_or_foreign_store(tmp_path):
    with pytest.raises(CmdlineStagingError, match="not found"):
        parse_job_detail(tmp_path / "nope.db")
    foreign = tmp_path / "foreign.db"
    conn = sqlite3.connect(str(foreign))
    conn.executescript(
        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
        "CREATE TABLE job_detail (folder_id TEXT, job_id TEXT, cmd_line TEXT);"
    )
    conn.commit(); conn.close()
    with pytest.raises(CmdlineStagingError, match="schema_version"):
        parse_job_detail(foreign)


def test_parse_coverage_accounts_for_every_row(store):
    coverage = parse_job_detail(store)
    assert coverage.total == 6  # never-silent: every job lands in a bucket
    assert coverage.no_cmd_line == 1        # the watcher
    assert coverage.partial == 1            # mystery_widget -> UNKNOWN
    assert coverage.unparsed == 1           # echo done -> no-op, nothing extracted
    assert coverage.parsed == 3
    assert "parsed=3" in coverage.summary()
    verdicts = dict(
        ((r[0], r[1]), r[2])
        for r in _q(store, "SELECT folder_id, job_id, verdict FROM parse_quality")
    )
    assert len(verdicts) == 6
    assert verdicts[("70003", "1")] == "no_cmd_line"
    assert verdicts[("70003", "2")] == "partial"
    assert verdicts[("70003", "3")] == "unparsed"


def test_parse_dpl_detail_columns(store):
    parse_job_detail(store)
    row = _q(store,
             "SELECT invocation_type, launcher, launch_mode, pipeline_guid, "
             "props_json FROM job_detail_parsed "
             "WHERE folder_id='70001' AND job_id='1'")[0]
    itype, launcher, mode, guid, props_json = row
    assert itype == "DPL"
    assert launcher == "/apps/dpl/dt-launcher.sh"
    assert mode == "-i"                      # G15: property, never identity
    assert guid == _GUID
    props = json.loads(props_json)
    assert props["env"] == "prod"
    assert props["seal"] == "70002"          # direct SEAL-attribution source
    assert "launch_mode" not in props        # popped into its own column


def test_parse_var_launcher_guid_fallback(store):
    """%%VAR launcher + --pipeline-id GUID literal still classifies DPL
    (G15 acceptance c — values decide, never the variable name)."""
    parse_job_detail(store)
    row = _q(store,
             "SELECT invocation_type, classifier_rule, pipeline_guid, props_json "
             "FROM job_detail_parsed WHERE folder_id='70001' AND job_id='2'")[0]
    assert row[0] == "DPL"
    assert row[1] == "dpl.pipeline_guid_literal"
    assert row[2] == _GUID
    props = json.loads(row[3])
    assert props["aws"] == "true"
    assert props["queue_name"] == "synq"


def test_parse_python_payload_and_artifact_kind(store):
    parse_job_detail(store)
    row = _q(store,
             "SELECT invocation_type, script_path, config_path, artifact_kind "
             "FROM job_detail_parsed WHERE folder_id='70001' AND job_id='3'")[0]
    assert row[0] == "PYTHON"
    assert row[1] == "/apps/syn/etl_step.py"
    assert row[2] == "/apps/syn/etl.json"
    assert row[3] == "python-script"


def test_parse_warn_stream_counts(store, caplog):
    with caplog.at_level("WARNING", logger="drydocs.cmdline_staging"):
        parse_job_detail(store)
    warned = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warned) == 2  # one partial + one unparsed, each COUNTED and logged


def test_parse_prefers_resolved_cmd_line(store):
    """The internal resolution query's output wins when present (the core
    parser is designed for resolved values); parsed_from records which text
    was parsed, per job."""
    conn = sqlite3.connect(str(store))
    conn.execute(
        "UPDATE job_detail SET cmd_line_resolved = ? "
        "WHERE folder_id='70003' AND job_id='3'",
        ("python /apps/syn/resolved_step.py",),
    )
    conn.commit(); conn.close()
    coverage = parse_job_detail(store)
    # raw 'echo done' was unparsed; the resolved text parses instead
    assert coverage.from_resolved == 1
    assert coverage.unparsed == 0
    assert coverage.parsed == 4
    assert "1 from resolved" in coverage.summary()
    row = _q(store, "SELECT verdict, parsed_from FROM parse_quality "
                    "WHERE folder_id='70003' AND job_id='3'")[0]
    assert row == ("parsed", "resolved")
    others = _q(store, "SELECT DISTINCT parsed_from FROM parse_quality "
                       "WHERE verdict != 'no_cmd_line' "
                       "AND NOT (folder_id='70003' AND job_id='3')")
    assert others == [("raw",)]


def test_reexport_clears_resolution_column(store):
    """Documented loudly: the store is temporary plumbing — re-export rebuilds
    everything, and the internal resolution query re-runs afterward."""
    conn = sqlite3.connect(str(store))
    conn.execute("UPDATE job_detail SET cmd_line_resolved = 'x'")
    conn.commit(); conn.close()
    export_job_detail(FakeClient(), store)
    assert _q(store, "SELECT count(*) FROM job_detail "
                     "WHERE cmd_line_resolved IS NOT NULL")[0][0] == 0


def test_export_rebuilds_stale_v1_store_in_place(tmp_path):
    """A v1-era file (no cmd_line_resolved column) is rebuilt by export, not
    tripped over — the store is derived, DROP+recreate is the contract."""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(str(path))
    conn.executescript(
        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
        "CREATE TABLE job_detail (folder_id TEXT NOT NULL, job_id TEXT NOT NULL,"
        " job_name TEXT, data_center TEXT, task_type TEXT, active INTEGER,"
        " cmd_line TEXT, PRIMARY KEY (folder_id, job_id));"
        "INSERT INTO meta VALUES ('schema_version', 'drydocs.cmdline-staging.v1');"
    )
    conn.commit(); conn.close()
    report = export_job_detail(FakeClient(), path)
    assert report.jobs == 6
    meta = dict(_q(path, "SELECT key, value FROM meta"))
    assert meta["schema_version"] == SCHEMA_VERSION
    cols = [r[1] for r in _q(path, "PRAGMA table_info(job_detail)")]
    assert "cmd_line_resolved" in cols


def test_reexport_clears_parsed_tables(store):
    parse_job_detail(store)
    assert _q(store, "SELECT count(*) FROM job_detail_parsed")[0][0] > 0
    export_job_detail(FakeClient(), store)  # re-export replaces the base rows
    assert _q(store, "SELECT count(*) FROM job_detail_parsed")[0][0] == 0
    assert _q(store, "SELECT count(*) FROM parse_quality")[0][0] == 0


def test_module_never_writes_the_graph():
    """G22 is the terminus gate: the parse step takes only a db_path (no
    client), and the export's single graph call is the read-only MATCH."""
    import inspect

    from drydocs import cmdline_staging

    assert "client" not in inspect.signature(parse_job_detail).parameters
    fake = FakeClient()
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        export_job_detail(fake, Path(td) / "s.db")
    assert len(fake.queries) == 1
    q = fake.queries[0].upper()
    assert q.lstrip().startswith("MATCH")
    for verb in ("MERGE", "CREATE", "DELETE", "SET "):
        assert verb not in q
    source = inspect.getsource(cmdline_staging)
    assert "Neo4jClient" not in source  # duck-typed read seam only
