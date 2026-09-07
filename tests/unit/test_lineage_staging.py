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
    DEFAULT_KEEP,
    DIRTY_SUFFIX,
    HOPS,
    REQUIRED,
    StagingError,
    artifact_name,
    code_commit,
    is_dirty_commit,
    newest_artifact,
    prune_staged,
    read_artifact,
    stage_chain,
    staged_artifacts,
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


def test_the_sources_block_follows_the_declared_hop_order(tmp_path: Path) -> None:
    """HOPS is the declaration the artifact's sources block is checked against - not
    a literal asserted back at itself (the LIN1 review's nit)."""
    staged = stage_chain(jobs=_dpl_jobs(tmp_path))
    assert [s.hop for s in staged.sources] == [h for h, _ in HOPS]
    assert REQUIRED == {"controlm"}
    assert {s.hop for s in staged.sources if s.required} == REQUIRED


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


def test_a_variables_csv_discovered_beside_the_jobs_source_is_recorded_as_read(
    tmp_path: Path,
) -> None:
    """The LIN1 review's defect 1: with no --variables the extractor discovers a
    variables CSV beside a jobs DIRECTORY (its documented behavior) and the header used
    to say absent while the graph carried file-op edges built from it. Now the header
    names the file the extractor actually read."""
    jobs = _dpl_jobs(tmp_path)
    (jobs.parent / "variables.csv").write_text(
        "TABLE_NAME,JOB_ID,JOB_NAME,APPL_TYPE,NAME,VALUE\n"
        '10,1,JOB_AWS,OS,%%PRECMD,"mv /data/in/accounts.dat /work/accounts.dat"\n',
        encoding="utf-8",
        newline="\n",
    )
    staged = stage_chain(jobs=jobs.parent)  # the directory, the company route
    vars_state = next(s for s in staged.sources if s.hop == "controlm_variables")
    assert vars_state.present is True
    assert vars_state.path == str(jobs.parent / "variables.csv")
    assert "discovered" in vars_state.note
    assert staged.coverage["controlm"]["prepost_rows_read"] == 1
    assert {t for _, t, _ in staged.graph.rels} >= {"READS_FROM", "WRITES_TO"}


def test_an_explicit_variables_path_that_is_absent_reads_nothing_and_says_so(
    tmp_path: Path,
) -> None:
    """The same defect's second entry: an explicit path that does not exist must NOT
    fall back to discovery. The sibling variables CSV is present and must stay unread."""
    jobs = _dpl_jobs(tmp_path)
    (jobs.parent / "variables.csv").write_text(
        "TABLE_NAME,JOB_ID,JOB_NAME,APPL_TYPE,NAME,VALUE\n" '10,1,JOB_AWS,OS,%%PRECMD,"mv /a /b"\n',
        encoding="utf-8",
        newline="\n",
    )
    staged = stage_chain(jobs=jobs.parent, variables=jobs.parent / "nope.csv")
    vars_state = next(s for s in staged.sources if s.hop == "controlm_variables")
    assert vars_state.present is False and vars_state.note == "not found"
    assert staged.coverage["controlm"]["prepost_rows_read"] == 0
    assert staged.coverage["controlm"]["variables_path"] == ""


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


def test_the_artifact_round_trips_exactly_with_every_hop_present(tmp_path: Path) -> None:
    """to_dict -> file -> from_dict -> to_dict is exact: kinds, properties (hop 3's whole
    payload), rels - not just the counts (the LIN1 review's point 2b)."""
    staged = stage_chain(
        jobs=_dpl_jobs(tmp_path),
        mac_root=_mac_root(tmp_path),
        registry_root=_registry_root(tmp_path),
        glue_inventory=_glue_sheet(tmp_path),
    )
    out = tmp_path / "staged"
    out.mkdir()
    when = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
    path = write_artifact(
        staged, out, run_id="run-1", acquisition={"jobs": "test"}, captured_at=when, commit="abc123"
    )
    graph, header = read_artifact(path)
    assert graph.to_dict() == staged.graph.to_dict()
    assert header["schema"] == ARTIFACT_SCHEMA
    assert header["run_id"] == "run-1"
    assert header["code_commit"] == "abc123"
    assert header["acquisition"] == {"jobs": "test"}
    assert [s["hop"] for s in header["sources"]] == [h for h, _ in HOPS]
    assert header["extractors"] == {
        "controlm": "controlm-inventory",
        "dpl_mac": "dpl-mac",
        "dpl_registry": "dpl-registry",
        "glue": "glue-tables",
    }
    assert set(header["coverage"]) == {
        "controlm",
        "dpl_mac",
        "dpl_registry",
        "dpl_registry_crosscheck",
        "glue",
    }


def test_two_runs_over_the_same_inputs_write_identical_bytes(tmp_path: Path) -> None:
    """Determinism, measured for real: two DIFFERENT output directories (the review's
    point 2a - one directory and one run id was the same file read twice)."""
    when = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
    out_a, out_b = tmp_path / "a", tmp_path / "b"
    out_a.mkdir()
    out_b.mkdir()
    first = stage_chain(jobs=_dpl_jobs(tmp_path), mac_root=_mac_root(tmp_path))
    p1 = write_artifact(first, out_a, run_id="run-1", captured_at=when, commit="abc123")
    second = stage_chain(jobs=_dpl_jobs(tmp_path), mac_root=_mac_root(tmp_path))
    p2 = write_artifact(second, out_b, run_id="run-1", captured_at=when, commit="abc123")
    assert p1 != p2 and p1.read_bytes() == p2.read_bytes()
    assert b"\r\n" not in p1.read_bytes()


def test_the_artifact_name_sorts_by_capture_time() -> None:
    """A UTC stamp leads the run id, so a listing sorts chronologically and the newest
    is derivable without opening a file (the review's point 4)."""
    early = artifact_name("zzzz", datetime(2026, 9, 3, 12, 0, tzinfo=UTC))
    late = artifact_name("aaaa", datetime(2026, 9, 3, 12, 0, 1, tzinfo=UTC))
    assert early == "lineage-20260903T120000Z-zzzz.json"
    assert sorted([late, early]) == [early, late]


def test_reading_something_else_as_an_artifact_is_refused(tmp_path: Path) -> None:
    other = tmp_path / "x.json"
    other.write_text(json.dumps({"schema": "drydocs.lineage-graph.v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a staged lineage artifact"):
        read_artifact(other)


# --- LIN2 (c): the two LIN1 follow-ups that bite at load time, and retention ---------


def _git_repo(tmp_path: Path) -> Path:
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    import os

    env = {**os.environ, **env}
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "one"], cwd=repo, check=True, env=env)
    return repo


def test_code_commit_marks_a_dirty_tree(tmp_path: Path) -> None:
    """The 93f4d832 verify pass: HEAD alone claims a commit the artifact was not built
    from when the tree carries uncommitted edits. Clean -> bare sha; a modified tracked
    file OR an untracked file -> ``<sha>-dirty`` (git describe's convention)."""
    repo = _git_repo(tmp_path)
    clean = code_commit(repo)
    assert len(clean) == 40 and not is_dirty_commit(clean)
    (repo / "a.txt").write_text("changed\n", encoding="utf-8")
    dirty = code_commit(repo)
    assert dirty == clean + DIRTY_SUFFIX and is_dirty_commit(dirty)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    (repo / "stray.txt").write_text("x\n", encoding="utf-8")
    assert is_dirty_commit(code_commit(repo)), "an untracked file is a dirty tree too"


def test_code_commit_outside_a_checkout_is_unknown_not_a_guess(tmp_path: Path) -> None:
    bare = tmp_path / "not-a-repo"
    bare.mkdir()
    assert code_commit(bare) == "unknown"


def _touch_artifacts(staged: Path, stamps: list[str]) -> list[Path]:
    staged.mkdir(parents=True, exist_ok=True)
    out = []
    for i, stamp in enumerate(stamps):
        p = staged / f"lineage-{stamp}-run{i}.json"
        p.write_text("{}", encoding="utf-8")
        out.append(p)
    (staged / "notes.txt").write_text("not an artifact", encoding="utf-8")
    return out


def test_newest_artifact_is_derived_from_the_name_alone(tmp_path: Path) -> None:
    """The stamp leads, so the newest is the last by name - no file is opened, and a
    stray non-artifact file in the zone is ignored."""
    staged = tmp_path / "lineage" / "staged"
    assert newest_artifact(staged) is None  # the zone does not exist yet
    files = _touch_artifacts(staged, ["20260904T120000Z", "20260903T235959Z", "20260904T120001Z"])
    assert newest_artifact(staged) == files[2]
    assert staged_artifacts(staged) == [files[1], files[0], files[2]]


def test_prune_keeps_the_newest_n_and_the_load_side_never_deletes(tmp_path: Path) -> None:
    """Retention, as decided in LIN2: the EXTRACT prunes to the newest ``keep`` after a
    successful write; ``keep <= 0`` keeps everything. DEFAULT_KEEP is the verb's default
    and is pinned so a change to it is a decision, not a drift."""
    assert DEFAULT_KEEP == 10
    staged = tmp_path / "lineage" / "staged"
    files = _touch_artifacts(staged, [f"2026090{d}T000000Z" for d in range(1, 6)])
    assert prune_staged(staged, keep=0) == []
    assert prune_staged(staged, keep=10) == []
    removed = prune_staged(staged, keep=2)
    assert removed == files[:3]
    assert staged_artifacts(staged) == files[3:]
    assert (staged / "notes.txt").exists(), "only artifacts are ever pruned"
