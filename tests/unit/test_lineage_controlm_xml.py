"""G47 — the Control-M XML definition-export ingestion seam.

SYNTHETIC fixtures throughout (shape-faithful, value-fake; the element and
attribute names ARE the assumed contract documented in ``controlm_xml.py`` —
the company's real 9.0.21.300 export validates or amends it; real exports
are Internal and live in the controlm-xml/ landing zone, never here). Each
case pins one acceptance clause: (a) taxonomy-first staging with provenance,
(b) DOCUMENT ORDER preserved on variables (the resolver's
sequential-assignment contract), (c) the scope_layers handoff — staging
feeds the ONE shared resolver, guardrail 1 proven end to end, (d) cmd_line
stays VERBATIM in staging, (e) every skip counted by reason, unknown
elements tolerated-and-counted, (f) older-format tag synonyms, (g) ZERO
graph writes — the API is graph-free.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from drydocs_core.controlm import resolve_command_line
from drydocs_lineage.extractors import ControlMXmlDefsExtractor

DC = "P032-E0700-DMA"

_EXPORT = f"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="{DC}" FOLDER_NAME="PRHLD1G">
    <VARIABLE NAME="%%SCRIPT_DIR" VALUE="/apps/etl"/>
    <VARIABLE NAME="%%ENV_SUFFIX" VALUE="prod"/>
    <JOB JOBNAME="PRHLD1G001" TASKTYPE="Command" NODEID="host-hldm-01"
         APPLICATION="HLDM" RUN_AS="svc.hldm"
         CMDLINE="%%SCRIPT_DIR/%%SCRIPT -e %%ENV_SUFFIX -d %%$ODATE">
      <VARIABLE NAME="%%SCRIPT" VALUE="run_conform.sh"/>
      <INCOND NAME="PRHLD1G000-OK" ODATE="ODAT"/>
    </JOB>
    <SUB_FOLDER SUB_FOLDER_NAME="NESTED">
      <VARIABLE NAME="%%SCRIPT_DIR" VALUE="/apps/etl/nested"/>
      <JOB JOBNAME="PRHLD1G101" TASKTYPE="Command"
           CMDLINE="%%SCRIPT_DIR/cleanup.sh">
      </JOB>
    </SUB_FOLDER>
    <JOB JOBNAME="PRHLD1G002" TASKTYPE="FileWatch">
    </JOB>
    <JOB TASKTYPE="Command" CMDLINE="ghost.sh"/>
    <JOB JOBNAME="PRHLD1G001" TASKTYPE="Command" CMDLINE="dupe.sh"/>
    <VARIABLE VALUE="nameless"/>
    <SHOUT DEST="EM" MESSAGE="synthetic"/>
  </SMART_FOLDER>
  <TABLE DATACENTER="{DC}" TABLE_NAME="LEGACY1G">
    <JOB JOBNAME="LEGACY1G001" TASKTYPE="Command" CMDLINE="legacy.sh"/>
  </TABLE>
</DEFTABLE>
"""


@pytest.fixture()
def xml_root(tmp_path: Path) -> Path:
    root = tmp_path / "controlm-xml"
    root.mkdir()
    (root / "export_p032.xml").write_text(_EXPORT, encoding="utf-8")
    (root / "not_a_deftable.xml").write_text(
        "<WORKFLOW><STEP/></WORKFLOW>", encoding="utf-8")
    (root / "broken.xml").write_text("<DEFTABLE><FOLDER", encoding="utf-8")
    return root


@pytest.fixture()
def run(xml_root: Path):
    return ControlMXmlDefsExtractor().extract(xml_root)


# -- (a) taxonomy-first staging with provenance ---------------------------------------

def test_folders_and_jobs_staged_with_provenance(run) -> None:
    folders = {f.folder_name: f for f in run.folders}
    assert folders["PRHLD1G"].kind == "smart_folder"
    assert folders["PRHLD1G"].data_center == DC
    jobs = {j.job_name: j for j in run.jobs}
    j1 = jobs["PRHLD1G001"]
    assert (j1.task_type, j1.node_id, j1.application, j1.run_as) == (
        "Command", "host-hldm-01", "HLDM", "svc.hldm")
    assert j1.subfolder_path == ""
    assert j1.source_file.endswith("export_p032.xml")   # provenance
    nested = jobs["PRHLD1G101"]
    assert nested.subfolder_path == "NESTED"
    assert run.coverage.folders == 2
    assert run.coverage.jobs == 4


# -- (b) document order preserved (the sequential-assignment contract) ----------------

def test_variable_order_scope_and_container(run) -> None:
    folder_vars = [v for v in run.variables if v.scope == "FOLDER"]
    assert [(v.ordinal, v.name) for v in folder_vars] == [
        (1, "%%SCRIPT_DIR"), (2, "%%ENV_SUFFIX")]
    job_vars = [v for v in run.variables if v.scope == "JOB"]
    assert [(v.container, v.name) for v in job_vars] == [
        ("PRHLD1G001", "%%SCRIPT")]
    sub_vars = [v for v in run.variables if v.scope == "SUBFOLDER"]
    assert [(v.container, v.value) for v in sub_vars] == [
        ("NESTED", "/apps/etl/nested")]


# -- (c) the scope_layers handoff — guardrail 1 proven end to end ---------------------

def test_scope_layers_feed_the_one_shared_resolver(run) -> None:
    """Staging hands ordered defs to drydocs_core.controlm — the extractor
    itself never substitutes anything."""
    job = next(j for j in run.jobs if j.job_name == "PRHLD1G001")
    rcl = resolve_command_line(run.scope_layers(job), job.cmd_line)
    assert rcl.resolved == "/apps/etl/run_conform.sh -e prod -d {ODATE}"
    assert rcl.is_fully_resolved
    assert ("SCRIPT", "JOB") in rcl.substituted
    assert ("SCRIPT_DIR", "FOLDER") in rcl.substituted


def test_subfolder_layer_overrides_the_folder_binding(run) -> None:
    job = next(j for j in run.jobs if j.job_name == "PRHLD1G101")
    layers = run.scope_layers(job)
    assert [scope for scope, _ in layers] == ["FOLDER", "SUBFOLDER", "JOB"]
    rcl = resolve_command_line(layers, job.cmd_line)
    assert rcl.resolved == "/apps/etl/nested/cleanup.sh"   # job > subfolder > folder
    assert rcl.substituted == (("SCRIPT_DIR", "SUBFOLDER"),)


# -- (d) cmd_line stays VERBATIM in staging -------------------------------------------

def test_cmd_line_staged_verbatim_never_resolved(run) -> None:
    job = next(j for j in run.jobs if j.job_name == "PRHLD1G001")
    assert job.cmd_line == "%%SCRIPT_DIR/%%SCRIPT -e %%ENV_SUFFIX -d %%$ODATE"


# -- (e) every skip counted by reason --------------------------------------------------

def test_skips_and_tolerated_elements_counted(run) -> None:
    cov = run.coverage
    assert cov.files_read == 1
    assert cov.files_invalid == 2        # not-a-DEFTABLE root + broken XML
    assert cov.jobs_no_name == 1         # the ghost JOB
    assert cov.duplicate_jobs == 1       # PRHLD1G001 again — first wins
    assert cov.jobs_no_cmd_line == 1     # the FileWatch job, staged anyway
    assert cov.variables_no_name == 1    # the nameless VARIABLE
    assert cov.elements_ignored == 2     # INCOND + SHOUT — tolerated, counted
    dupe_kept = next(j for j in run.jobs if j.job_name == "PRHLD1G001")
    assert dupe_kept.cmd_line != "dupe.sh"
    watcher = next(j for j in run.jobs if j.job_name == "PRHLD1G002")
    assert watcher.cmd_line == "" and watcher.task_type == "FileWatch"
    assert "invalid_files=2" in cov.summary()


# -- (f) older-format tag synonyms ------------------------------------------------------

def test_legacy_table_tags_accepted(run) -> None:
    legacy = next(f for f in run.folders if f.folder_name == "LEGACY1G")
    assert legacy.kind == "folder"
    assert any(j.job_name == "LEGACY1G001" for j in run.jobs)


# -- (g) ZERO graph writes: the API is graph-free ---------------------------------------

def test_staging_is_graph_free(run) -> None:
    """No LineageGraph parameter exists anywhere in the extractor API —
    staging cannot write what it never receives; activation waits on the
    psgmgr-vs-XML precedence ruling (guardrail 3)."""
    params = inspect.signature(ControlMXmlDefsExtractor.extract).parameters
    assert set(params) == {"self", "source"}
    assert run.folders and run.jobs and run.variables   # flat records only
