"""G21 — the rua code-operations pass (captured content → ontology candidates).

SYNTHETIC fixtures throughout (shape-faithful, value-fake — the test_lineage_rua
convention). Each case pins one acceptance clause:
(a) launcher/interpreter invocations inside scripts classify via
    LAUNCHER_REGISTRY and become INVOKES candidates — DPL keeps its
    pipeline-GUID identity (G15);
(b) variable assignments classify via the FACT_REGISTRY ETL_* canonicals with
    the G16 value contracts — values decide, WARN counters fire;
(c) file operations emit READS_FROM / WRITES_TO candidates from the script
    node (the 2026-07-15 gate EDIT endpoints) — no new relationship types;
(d) profiles yield PATH mutations + script-to-script DEPENDENCY CANDIDATES
    flagged needs_vocabulary, and stage NO rels;
(e) skipped/unparseable constructs are counted by reason, never dropped.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_lineage.extractors import (
    RuaCodeOpsExtractor,
    RuaInventoryExtractor,
)
from drydocs_lineage.model import LineageGraph, asset_id, process_id

USER = "svc_synth"
GUID = "12345678-abcd-4ef0-9876-0123456789ab"

_META = f"""schema=rua-inventory/v2
collected_at=2026-07-27T12:00:00Z
collected_by={USER}
user={USER}
uid=4242
groups=synthgrp
login_shell=/bin/ksh
hostname=vsi-synth-01
fqdn=vsi-synth-01.example.internal
os=Linux
kernel=5.14.0-synth
scan_roots=/home/{USER} /opt/app
"""

_SCRIPT_ETL = f"""#!/bin/ksh
# synthetic launcher wrapper (fixture)
export ETL_ARTIFACT_URI=s3://synth-bucket/app/conform.jar
JAR_PATH=dt-launcher.sh
FILE_SFX=.

cp /in/landing/file.dat /work/stage/file.dat
gzip /work/stage/file.dat
chmod 750 /work/stage

dt-launcher.sh -pipeline {GUID} -env prod \\
  -appName synth_app
python3 /opt/app/post_check.py --mode audit
frobnicate --wat
"""

_SCRIPT_NO_OPS = """#!/bin/sh
# nothing but a comment and a blank line
"""

_PROFILE = """# synthetic .profile (fixture)
export PATH=$PATH:/opt/app/bin
. /opt/app/env/common_env.sh
sh /opt/app/bin/warmup.sh
"""


def _write_bundle(root: Path) -> Path:
    bundle = root / f"rua_vsi-synth-01_{USER}_20260727"
    scripts_dir = bundle / "scripts" / "opt" / "app"
    profiles_dir = bundle / "profiles"
    scripts_dir.mkdir(parents=True)
    profiles_dir.mkdir(parents=True)
    (bundle / "meta.txt").write_text(_META, encoding="utf-8")
    (bundle / "directories.tsv").write_text(
        "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
        f"/opt/app\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n",
        encoding="utf-8",
    )
    (bundle / "profiles.tsv").write_text(
        "name\tpath\texists\tsize\tmtime\tperms\towner\tsha256\n"
        f".profile\t/home/{USER}/.profile\tyes\t42\t2026-07-20 09:00\t644\t{USER}\t{'aa' * 32}\n",
        encoding="utf-8",
    )
    (profiles_dir / ".profile").write_text(_PROFILE, encoding="utf-8")
    (bundle / "scripts.tsv").write_text(
        "path\towner\tgroup\tperms\tsize\tmtime\tsha256\n"
        f"/opt/app/run_etl.ksh\t{USER}\tsynthgrp\t750\t400\t2026-07-20 09:00\t{'bb' * 32}\n"
        f"/opt/app/noop.sh\t{USER}\tsynthgrp\t750\t40\t2026-07-20 09:00\t{'cc' * 32}\n"
        f"/opt/app/lost.sh\t{USER}\tsynthgrp\t750\t40\t2026-07-20 09:00\t{'dd' * 32}\n",
        encoding="utf-8",
    )
    (scripts_dir / "run_etl.ksh").write_text(_SCRIPT_ETL, encoding="utf-8")
    (scripts_dir / "noop.sh").write_text(_SCRIPT_NO_OPS, encoding="utf-8")
    # lost.sh: listed, no copy carried back — counted, never implied
    return bundle


@pytest.fixture()
def staged(tmp_path):
    bundle = _write_bundle(tmp_path)
    graph = LineageGraph()
    RuaInventoryExtractor().extract(bundle, into=graph)
    result = RuaCodeOpsExtractor().extract(bundle, into=graph)
    return graph, result


SCRIPT_ID = process_id("rua_script", "/opt/app/run_etl.ksh")


def test_a_invocations_classify_and_link_invokes(staged) -> None:
    graph, result = staged
    cov = result.coverage
    # dt-launcher.sh (DPL, GUID identity), python3 script, frobnicate (UNKNOWN)
    dpl_id = process_id("dpl", GUID)
    assert dpl_id in graph.processes, "DPL invocation must key on the pipeline GUID (G15)"
    assert (SCRIPT_ID, "INVOKES", dpl_id) in graph.rels
    py_id = process_id("python", "/opt/app/post_check.py")
    assert (SCRIPT_ID, "INVOKES", py_id) in graph.rels
    assert cov.invocations_added >= 3
    assert cov.invocations_unresolved == 1  # frobnicate — UNKNOWN, kept AND counted
    # G15 definition-level properties ride the DPL node, never identity
    assert graph.processes[dpl_id].properties.get("env") == "prod"
    assert graph.processes[dpl_id].properties.get("app_name") == "synth_app"


def test_b_assignments_classify_with_value_contracts(staged) -> None:
    _, result = staged
    cov = result.coverage
    facts = {f["name"]: f for f in result.facts}
    # canonical spelling — clean fact
    assert facts["ETL_ARTIFACT_URI"]["fact_type"] == "ARTIFACT_URI"
    assert facts["ETL_ARTIFACT_URI"]["fact_alias_of"] is None
    # the JAR_PATH -> dt-launcher.sh gotcha: the VALUE decides (G16)
    assert facts["JAR_PATH"]["fact_type"] == "LAUNCHER_SCRIPT_PATH"
    assert facts["JAR_PATH"]["fact_name_mismatch"] is True
    assert cov.fact_name_mismatches >= 1
    assert cov.facts_classified == len(result.facts)
    # FILE_SFX='.' is an assignment but not a fact — still counted
    assert cov.assignments_classified > cov.facts_classified


def test_c_file_ops_emit_gate_edit_endpoints(staged) -> None:
    graph, result = staged
    cov = result.coverage
    src = asset_id("local_file", "/in/landing/file.dat")
    tgt = asset_id("local_file", "/work/stage/file.dat")
    gz = asset_id("local_file", "/work/stage/file.dat.gz")
    assert (SCRIPT_ID, "READS_FROM", src) in graph.rels
    assert (SCRIPT_ID, "WRITES_TO", tgt) in graph.rels
    assert (SCRIPT_ID, "WRITES_TO", gz) in graph.rels  # gzip twin (G14)
    assert cov.file_ops_added == 4  # cp src+tgt, gzip src+twin
    assert cov.file_ops_skipped_non_dataflow >= 1  # chmod — mechanics, counted
    # no new relationship types anywhere
    assert {r[1] for r in graph.rels} <= {"INVOKES", "READS_FROM", "WRITES_TO", "TRIGGERS"}


def test_d_profiles_stage_no_rels_only_candidates(staged) -> None:
    graph, result = staged
    profile_id = process_id("rua_profile", f"/home/{USER}/.profile")
    assert not [
        r for r in graph.rels if r[0] == profile_id
    ], "a profile's edge meaning is G22's — no rels from profile nodes"
    assert result.path_mutations and result.path_mutations[0]["value"].endswith("/opt/app/bin")
    deps = {(d["via"], d["target"]) for d in result.dependency_candidates}
    assert ("source", "/opt/app/env/common_env.sh") in deps
    assert ("invocation", "/opt/app/bin/warmup.sh") in deps
    assert all(d["needs_vocabulary"] for d in result.dependency_candidates)


def test_e_skips_counted_by_reason(staged) -> None:
    _, result = staged
    cov = result.coverage
    assert cov.scripts_seen == 3
    assert cov.scripts_parsed == 2
    assert cov.scripts_no_copy == 1  # lost.sh — listed, content absent
    assert cov.profiles_parsed == 1
    assert cov.lines_comment >= 3
    assert cov.lines_blank >= 2
    assert cov.lines_continuation_joined == 1  # the dt-launcher backslash line
    assert cov.statements_unparsed >= 1  # frobnicate
    summary = cov.summary()
    assert "unparsed=" in summary and "unresolved=" in summary
