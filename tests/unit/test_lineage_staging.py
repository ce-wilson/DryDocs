"""LIN1 - the lineage EXTRACT as one operation: ``drydocs_lineage.staging`` runs the
chain's extractors in hop order into one graph and stages one artifact.

SYNTHETIC fixtures throughout (shape-faithful, value-fake), on the same shapes the
per-extractor tests already use - a MAC set, a registry landing zone, a Glue GUID
sheet - plus the bundled Control-M samples for hop 1. The CLI verb is proven in
``test_cli_lineage_extract.py``; this file proves the module the verb is thin over.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from drydocs.cli_shared import DEFAULT_SAMPLES_DIR
from drydocs_lineage.staging import (
    ARTIFACT_SCHEMA,
    HOPS,
    StagingError,
    read_artifact,
    stage_chain,
    write_artifact,
)

SAMPLE_JOBS = DEFAULT_SAMPLES_DIR / "controlm_jobs__sample.csv"
SAMPLE_VARS = DEFAULT_SAMPLES_DIR / "controlm_variables__sample.csv"

GUID_PIPE = "11111111-aaaa-4bbb-8ccc-000000000001"
GUID_PIPE_UNREGISTERED = "99999999-aaaa-4bbb-8ccc-000000000009"
DS_IN = "aaaa0001-dddd-4eee-8fff-000000000010"
DS_OUT = "aaaa0002-dddd-4eee-8fff-000000000020"
SEAL = "88888"

_CSV_HEADER = "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"


def _jobs_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "exports" / "jobs.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_CSV_HEADER + "".join(rows), encoding="utf-8", newline="\n")
    return path


def _dpl_jobs(tmp_path: Path) -> Path:
    """Three DPL launch spellings keying ONE pipeline (the G15 identity rule), plus
    one Ab Initio wrapper, so a single hop-1 run carries BOTH ETLProcess kinds."""
    return _jobs_csv(
        tmp_path,
        f'1,10,JOB_AWS,F1,svc.x,h1,"/apps/t/dt-accelerators/dt-launcher.sh -env D '
        f'-pipeline {GUID_PIPE} -i -conf /cfg/c.json",Y\n',
        f'2,10,JOB_ONPM,F1,svc.x,h1,"/apps/dpl/dpl_processor/bin/dpl_spark_processor '
        f'--pipeline-id {GUID_PIPE} --aws --queue-name q1",Y\n',
        f'3,10,JOB_UNREG,F1,svc.x,h1,"sh /a/dt-launcher.sh -pipeline {GUID_PIPE_UNREGISTERED} -t",Y\n',
        '4,10,JOB_AB,F1,svc.x,h1,"/opt/scripts/hldm/load_accounts.pset",Y\n',
    )


def _mac_root(tmp_path: Path) -> Path:
    root = tmp_path / "dpl-mac"
    set_dir = root / f"conform_accounts#{GUID_PIPE}"
    set_dir.mkdir(parents=True, exist_ok=True)
    (set_dir / "pipeline.json").write_text(
        json.dumps(
            {
                "pipelineId": GUID_PIPE,
                "pipelineType": "batch",
                "subType": "transformation",
                "ownerSealId": SEAL,
                "name": "conform-accounts",
            }
        ),
        encoding="utf-8",
    )
    (set_dir / "dataset_flow.json").write_text(
        json.dumps(
            {
                "pipelineId": GUID_PIPE,
                "inputDatasets": [{"guid": DS_IN, "version": "3", "zone": "RAW"}],
                "outputDatasets": [{"guid": DS_OUT, "version": "1", "zone": "TRUSTED"}],
            }
        ),
        encoding="utf-8",
    )
    return root


def _registry_root(tmp_path: Path) -> Path:
    root = tmp_path / "dpl-registry" / SEAL
    root.mkdir(parents=True)
    (root / "pipeline_id.json").write_text(
        json.dumps(
            [{"pipelineId": GUID_PIPE, "version": "3", "active": True, "ownerSealId": SEAL}]
        ),
        encoding="utf-8",
    )
    (root / "dataset_id.json").write_text(
        json.dumps({"datasets": [{"datasetId": DS_IN, "version": "3", "active": "ACTIVE"}]}),
        encoding="utf-8",
    )
    return root.parent


def _glue_sheet(tmp_path: Path) -> Path:
    path = tmp_path / "glue-inventory" / "guid_inventory.csv"
    path.parent.mkdir(parents=True)
    header = (
        "PlatformId,databaseName,tableName,tableDatasetId,tableDatasetIdSource,databaseFullPath"
    )
    db = "RAW__CCB__SYNTH_AREA__EVENTS_DB"
    rows = [
        f"104999,{db},{SEAL}_300000099_ACCOUNTS_RAW,{DS_IN},datasetGuid,{db.lower()}.{SEAL}_300000099_accounts_raw",
    ]
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8", newline="\n")
    return path


# --- hop 1 -----------------------------------------------------------------------


def test_hop_order_is_declared_and_only_the_first_hop_is_required() -> None:
    assert [h for h, _ in HOPS] == ["controlm", "dpl_mac", "dpl_registry", "glue"]
    assert [req for _, req in HOPS] == [True, False, False, False]


def test_the_bundled_samples_stage_abinitio_etl_processes() -> None:
    """Hop 1 on the package samples: every job seeds a process node, the Ab Initio
    wrappers classify as :ETLProcess kind abinitio, and INVOKES is the edge."""
    # the variables sample is machine-local (untracked): pass it only where it exists,
    # and the assertions below hold either way - hop 1 is the jobs CSV
    staged = stage_chain(jobs=SAMPLE_JOBS, variables=SAMPLE_VARS if SAMPLE_VARS.exists() else None)
    kinds = {n.kind for n in staged.graph.processes.values()}
    assert {"controlm_job", "abinitio"} <= kinds
    assert {t for _, t, _ in staged.graph.rels} == {"INVOKES"}
    cov = staged.coverage["controlm"]
    assert cov["jobs_added"] == cov["rows_read"] > 0
    assert cov["invocations_etl_process"] > 0
    # the optional hops were asked and had nothing - said so, not silent
    by_hop = {s.hop: s for s in staged.sources}
    assert by_hop["controlm"].present
    assert by_hop["controlm_variables"].present is SAMPLE_VARS.exists()
    for hop in ("dpl_mac", "dpl_registry", "glue"):
        assert by_hop[hop].present is False
        assert by_hop[hop].note == "no path given"
    assert set(staged.extractors) == {"controlm"}


def test_both_dpl_spellings_and_the_pset_land_as_one_hop1_run(tmp_path: Path) -> None:
    staged = stage_chain(jobs=_dpl_jobs(tmp_path))
    procs = staged.graph.processes
    assert procs[f"proc#dpl:{GUID_PIPE}"].kind == "dpl"
    assert procs[f"proc#dpl:{GUID_PIPE_UNREGISTERED}"].kind == "dpl"
    into_pipe = [r for r in staged.graph.rels if r[2] == f"proc#dpl:{GUID_PIPE}"]
    assert len(into_pipe) == 2, "both flag spellings key the SAME pipeline node (G15)"
    ab = [n for n in procs.values() if n.kind == "abinitio"]
    assert len(ab) == 1 and ab[0].name.endswith(".pset")


def test_a_missing_required_source_raises_and_names_the_path(tmp_path: Path) -> None:
    with pytest.raises(StagingError, match="required"):
        stage_chain(jobs=tmp_path / "nowhere" / "jobs.csv")


def test_an_empty_optional_zone_reads_as_absent_with_the_reason(tmp_path: Path) -> None:
    empty = tmp_path / "dpl-mac"
    empty.mkdir()
    staged = stage_chain(jobs=_dpl_jobs(tmp_path), mac_root=empty)
    mac = next(s for s in staged.sources if s.hop == "dpl_mac")
    assert mac.present is False
    assert mac.note == "directory is empty"
    assert mac.path == str(empty)
    assert "dpl_mac" not in staged.extractors


# --- hops 2a and 3 ------------------------------------------------------------------


def test_hop2a_joins_the_mac_flow_and_the_registry_onto_hop1s_pipeline(tmp_path: Path) -> None:
    staged = stage_chain(
        jobs=_dpl_jobs(tmp_path),
        mac_root=_mac_root(tmp_path),
        registry_root=_registry_root(tmp_path),
    )
    g = staged.graph
    pipe = f"proc#dpl:{GUID_PIPE}"
    reads = {dst for src, t, dst in g.rels if src == pipe and t == "READS_FROM"}
    writes = {dst for src, t, dst in g.rels if src == pipe and t == "WRITES_TO"}
    assert reads == {f"data#dpl_dataset:{DS_IN}"}
    assert writes == {f"data#dpl_dataset:{DS_OUT}"}
    assert staged.coverage["dpl_mac"]["matched"] == 1
    xc = staged.coverage["dpl_registry_crosscheck"]
    assert xc["clone_checked"] is True
    assert xc["observed_not_registered"] == [GUID_PIPE_UNREGISTERED]
    assert set(staged.extractors) == {"controlm", "dpl_mac", "dpl_registry"}


def test_hop3_places_the_dataset_as_properties_and_adds_no_edge(tmp_path: Path) -> None:
    staged = stage_chain(
        jobs=_dpl_jobs(tmp_path), mac_root=_mac_root(tmp_path), glue_inventory=_glue_sheet(tmp_path)
    )
    asset = staged.graph.data_assets[f"data#dpl_dataset:{DS_IN}"]
    assert asset.properties["glue_database_raw"].startswith("RAW__")
    assert asset.properties["glue_table_raw"].endswith("_ACCOUNTS_RAW")
    rel_types = {t for _, t, _ in staged.graph.rels}
    assert rel_types == {
        "INVOKES",
        "READS_FROM",
        "WRITES_TO",
    }, "glue adds properties, never an edge"
    assert staged.coverage["glue"]["datasets_enriched"] == 1


# --- the artifact ------------------------------------------------------------------------


def test_the_artifact_round_trips_and_is_deterministic(tmp_path: Path) -> None:
    staged = stage_chain(jobs=_dpl_jobs(tmp_path), mac_root=_mac_root(tmp_path))
    out = tmp_path / "staged"
    out.mkdir()
    when = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
    p1 = write_artifact(staged, out, run_id="run-1", acquisition={"jobs": "test"}, captured_at=when)
    graph, header = read_artifact(p1)
    assert graph.stats() == staged.graph.stats()
    assert graph.rels == staged.graph.rels
    assert header["schema"] == ARTIFACT_SCHEMA
    assert header["run_id"] == "run-1"
    assert header["acquisition"] == {"jobs": "test"}
    assert {s["hop"] for s in header["sources"]} == {
        "controlm",
        "controlm_variables",
        "dpl_mac",
        "dpl_registry",
        "glue",
    }
    assert header["extractors"] == {"controlm": "controlm-inventory", "dpl_mac": "dpl-mac"}
    # same inputs, same clock -> same bytes (the render-determinism rule)
    again = stage_chain(jobs=_dpl_jobs(tmp_path), mac_root=_mac_root(tmp_path))
    p2 = write_artifact(again, out, run_id="run-1", acquisition={"jobs": "test"}, captured_at=when)
    assert p1.read_bytes() == p2.read_bytes()
    assert b"\r\n" not in p1.read_bytes()


def test_reading_something_else_as_an_artifact_is_refused(tmp_path: Path) -> None:
    other = tmp_path / "x.json"
    other.write_text(json.dumps({"schema": "drydocs.lineage-graph.v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a staged lineage artifact"):
        read_artifact(other)
