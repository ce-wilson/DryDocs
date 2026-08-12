"""G67 — the greenfield job standard conformance pass (R2 + R30-R40).

Two fixtures carry the whole argument. ``_DRIFTED`` reproduces the SHAPE of a
real four-job flow that grew by hand: variables re-declared per job, one of
them mistyped, a reference that resolves to nothing, two values swapped, and a
watch path edited without its post-command — the half-finished rename that the
derived-handle pattern exists to make impossible.
``_GREENFIELD`` is the same flow rebuilt to the standard — folder holds the
flow invariants, a sub-folder holds the dataset identity, jobs hold only what
is genuinely per-job, and the composed filename is DERIVED once and referenced
everywhere.

The pair is the point: the first must raise every rule, and the second must
raise NONE. A standard nobody can reach is a wish, not a standard.

SYNTHETIC throughout — ``example.invalid`` addresses, invented ids and paths.
Real values are Internal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_lineage.extractors import ControlMXmlDefsExtractor
from drydocs_remediation.detect import (
    CONFORMANCE_RULE_IDS,
    DOT_SMUGGLING_RULE_ID,
    detect_all,
    detect_conformance,
)
from drydocs_remediation.xml_bridge import to_definition_set

DC = "T032-E0700-DMA"
#: unmistakably fake — a real dataset GUID would be an Internal identifier and
#: this file is publishable
UUID = "00000000-0000-4000-8000-000000000001"

# --------------------------------------------------------------------------
# The hand-grown flow: every rule has something to say about it.
# --------------------------------------------------------------------------
_DRIFTED = f"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="{DC}" FOLDER_NAME="FOLDER-SYNTH-DRIFT">
    <VARIABLE NAME="%%DevX-project" VALUE="SYNTHKEY"/>
    <SHOUT DEST="EM" MESSAGE="synthetic"/>
    <JOB JOBNAME="JOB0010_SAMPLE_DAT_ONPM_FW" TASKTYPE="FileWatcher"
         FILE_PATH="%%FILE_PATH%%FILE_PREFIX.%%$ODATE.%%FILE_EXTENSION"
         POSTCMD="cat %%FILE_PATH%%FILE_PREFIX.%%$ODATE.%%FILE_EXTENSION">
      <VARIABLE NAME="%%FILE_PATH" VALUE="/data/synth/dropbox/UPD/"/>
      <VARIABLE NAME="%%FILE_PREFIX" VALUE="SAMPLE_LKP_"/>
      <VARIABLE NAME="%%FILE_EXTENSION" VALUE=".txt"/>
    </JOB>
    <JOB JOBNAME="JOB0011_SAMPLE_TOK_ONPM_FW" TASKTYPE="FileWatcher"
         FILE_PATH="%%FILE_PATH.%%FILE_NM_PREFIX.%%$ODATE.%%FILE_NM_SUFFIX.tok"
         POSTCMD="cat %%FILE_PATH.%%FILE_PREFIX.%%$ODATE..tok">
      <VARIABLE NAME="%%FILE_PATH" VALUE="/data/synth/dropbox/UPD/"/>
      <VARIABLE NAME="%%FILE_PREFIX" VALUE="SAMPLE_LKP_"/>
      <VARIABLE NAME="%%FILE_NM_SUFFIX" VALUE="."/>
      <VARIABLE NAME="%%FILE_EXTENSION" VALUE=".tok"/>
    </JOB>
    <JOB JOBNAME="JOB0020_SAMPLE_AWS_PLCT" TASKTYPE="Command"
         CMDLINE="%%LAUNCHER_SCRIPT_PATH -env %%ENV -pipeline {UUID} -dataset %%DS_ID
                  -timeout %%TIMEOUT -datFile %%DAT_FILE">
      <VARIABLE NAME="%%LAUNCHER_SCRIPT_PATH" VALUE="/apps/synth/dt-launcher.sh"/>
      <VARIABLE NAME="%%ENV" VALUE="prod"/>
      <VARIABLE NAME="%%DS_ID" VALUE="{UUID}"/>
      <VARIABLE NAME="%%DS_VER" VALUE="1.0.0"/>
      <VARIABLE NAME="%%PIPELINE_ID" VALUE="{UUID}"/>
      <VARIABLE NAME="%%DATA_FLOW" VALUE="SAMPLE_LKP"/>
      <VARIABLE NAME="%%DAT_FILE" VALUE="/data/synth/dropbox/UPD/SAMPLE_LKP_20260811.txt"/>
    </JOB>
    <JOB JOBNAME="JOB0021_SAMPLE_AWS_TRUST" TASKTYPE="Command"
         CMDLINE="%%LAUNCHER_SCRIPT_PATH -env %%ENV -pipeline {UUID} -img %%IMG_PATH">
      <VARIABLE NAME="%%LAUNCHER_SCRIPT_PATH" VALUE="/apps/synth/dt-launcher.sh"/>
      <VARIABLE NAME="%%ENV" VALUE="prod"/>
      <VARIABLE NAME="%%DS_ID" VALUE="1.0.0"/>
      <VARIABLE NAME="%%DS_VER" VALUE="{UUID}"/>
      <VARIABLE NAME="%%IMG_PATH" VALUE="synth-prod-img"/>
      <VARIABLE NAME="%%DAT_FILE_NM" VALUE="SAMPLE_LKP_20260811.txt"/>
      <ON STMT="*" CODE="NOTOK">
        <DOMAIL DEST="%%EMAIL_GRP" SUBJECT="synthetic"/>
      </ON>
    </JOB>
  </SMART_FOLDER>
</DEFTABLE>
"""

# --------------------------------------------------------------------------
# The same flow, rebuilt to the standard.
# --------------------------------------------------------------------------
_GREENFIELD = f"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="{DC}" FOLDER_NAME="FOLDER-SYNTH-GREEN">
    <VARIABLE NAME="%%ENV" VALUE="prod"/>
    <VARIABLE NAME="%%FID" VALUE="S000001"/>
    <VARIABLE NAME="%%SEAL" VALUE="70002"/>
    <VARIABLE NAME="%%CONF_PATH" VALUE="/data/synth/cfg/conf.json"/>
    <VARIABLE NAME="%%LAUNCHER_SCRIPT_PATH" VALUE="/apps/synth/dt-launcher.sh"/>
    <VARIABLE NAME="%%ETL_PLATFORM" VALUE="java"/>
    <VARIABLE NAME="%%ETL_ARTIFACT_URI"
              VALUE="https://artifacts.example.invalid/maven/sample-1.0.0.jar"/>
    <VARIABLE NAME="%%ETL_ARTIFACT_KIND" VALUE="jar"/>
    <VARIABLE NAME="%%ETL_PLATFORM_FLAGS" VALUE="-i"/>
    <VARIABLE NAME="%%TIMEOUT" VALUE="24"/>
    <VARIABLE NAME="%%POLLING_INTERVAL" VALUE="1"/>
    <VARIABLE NAME="%%FILE_BKP_DIR" VALUE="/data/synth/dropbox/bkp/"/>
    <VARIABLE NAME="%%DEVX_KEY" VALUE="SYNTHKEY"/>
    <VARIABLE NAME="%%EMAIL_DL_L2" VALUE="l2@example.invalid"/>
    <VARIABLE NAME="%%EMAIL_DL_L3" VALUE="l3@example.invalid"/>
    <VARIABLE NAME="%%EMAIL_DL_PDN" VALUE="pdn@example.invalid"/>
    <SUB_FOLDER SUB_FOLDER_NAME="SAMPLE_LKP">
      <VARIABLE NAME="%%DATAFLOW" VALUE="SAMPLE_LKP"/>
      <VARIABLE NAME="%%DS_ID" VALUE="{UUID}"/>
      <VARIABLE NAME="%%DS_VER" VALUE="1.0.0"/>
      <VARIABLE NAME="%%FILE_DIR" VALUE="/data/synth/dropbox/UPD/"/>
      <VARIABLE NAME="%%FILE_PREFIX" VALUE="SAMPLE_LKP_"/>
      <VARIABLE NAME="%%FILE_BUSINESS_DATE" VALUE="%%$ODATE"/>
      <VARIABLE NAME="%%F_NM_DAT" VALUE="%%FILE_PREFIX.%%FILE_BUSINESS_DATE..txt"/>
      <VARIABLE NAME="%%F_NM_TOK" VALUE="%%FILE_PREFIX.%%FILE_BUSINESS_DATE..tok"/>
      <VARIABLE NAME="%%F_FQN_DAT" VALUE="%%FILE_DIR.%%F_NM_DAT"/>
      <VARIABLE NAME="%%F_FQN_TOK" VALUE="%%FILE_DIR.%%F_NM_TOK"/>
      <JOB JOBNAME="JOB0010_SAMPLE_DAT_ONPM_FW" TASKTYPE="FileWatcher"
           FILE_PATH="%%F_FQN_DAT"
           DESCRIPTION="DELIVERY_MECHANISM: MFTS_AGENT | FTS_ID: FTS2">
        <VARIABLE NAME="%%FILE_EXTENSION" VALUE=".txt"/>
      </JOB>
      <JOB JOBNAME="JOB0011_SAMPLE_TOK_ONPM_FW" TASKTYPE="FileWatcher"
           FILE_PATH="%%F_FQN_TOK" POSTCMD="cat %%F_FQN_TOK"
           DESCRIPTION="DELIVERY_MECHANISM: MFTS_AGENT | FTS_ID: FTS2">
        <VARIABLE NAME="%%FILE_EXTENSION" VALUE=".tok"/>
      </JOB>
      <JOB JOBNAME="JOB0020_SAMPLE_AWS_PLCT" TASKTYPE="Command"
           DESCRIPTION="JOB_ROLE: PLACEMENT"
           CMDLINE="%%LAUNCHER_SCRIPT_PATH -env %%ENV -pipeline {UUID}
                    -dataset %%DS_ID -version %%DS_VER -fid %%FID -conf %%CONF_PATH
                    -timeout %%TIMEOUT -sleep %%POLLING_INTERVAL"/>
      <JOB JOBNAME="JOB0021_SAMPLE_AWS_TRUST" TASKTYPE="Command"
           DESCRIPTION="JOB_ROLE: TRUST_INGEST"
           CMDLINE="%%LAUNCHER_SCRIPT_PATH -env %%ENV -pipeline {UUID}
                    -dataflow %%DATAFLOW -img %%ETL_ARTIFACT_URI -seal %%SEAL
                    -fid %%FID -timeout %%TIMEOUT -sleep %%POLLING_INTERVAL
                    -conf %%CONF_PATH %%ETL_PLATFORM_FLAGS"
           POSTCMD="mv %%FILE_DIR/%%F_NM_DAT %%FILE_BKP_DIR/%%F_NM_DAT"/>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""


def _load(tmp_path: Path, xml: str, name: str):
    root = tmp_path / name
    root.mkdir()
    (root / "export.xml").write_text(xml, encoding="utf-8")
    return to_definition_set(ControlMXmlDefsExtractor().extract(root))


@pytest.fixture()
def drifted(tmp_path: Path):
    return _load(tmp_path, _DRIFTED, "drift")


@pytest.fixture()
def greenfield(tmp_path: Path):
    return _load(tmp_path, _GREENFIELD, "green")


def _by_rule(findings) -> dict[str, list]:
    out: dict[str, list] = {}
    for finding in findings:
        out.setdefault(finding.rule_id, []).append(finding)
    return out


# == the pair ================================================================


def test_every_rule_fires_on_the_hand_grown_flow(drifted) -> None:
    """If a rule cannot fire on a fixture built to violate it, the rule is
    decoration. This is the guard against that."""
    fired = set(_by_rule(detect_conformance(drifted)))
    missing = [rule for rule in CONFORMANCE_RULE_IDS if rule not in fired]
    assert not missing, f"rules that never fired: {missing}"


def test_the_greenfield_shape_is_clean(greenfield) -> None:
    """The standard has to be REACHABLE. Same four jobs, same dataset, same
    files — rebuilt to the ladder, it raises nothing."""
    findings = detect_conformance(greenfield)
    assert findings == [], "\n".join(f"{f.rule_id} {f.target}: {f.message}" for f in findings)


# == what each rule actually says ============================================


def test_r30_names_the_reference_that_resolves_to_ctmerr(drifted) -> None:
    targets = {f.target for f in _by_rule(detect_conformance(drifted))["R30"]}
    assert "JOB0011_SAMPLE_TOK_ONPM_FW:watch_template" in targets
    assert "JOB0020_SAMPLE_AWS_PLCT:command_line" in targets  # %%TIMEOUT undeclared


def test_r31_spares_facts_and_metadata_declared_for_the_record(drifted) -> None:
    """FILE_EXTENSION is referenced by nothing and is REQUIRED anyway — the SQL
    parse reads it. Flagging it would fight the standard. PIPELINE_ID is
    neither a registered fact nor a metadata field, so it stays an orphan."""
    orphans = {f.target for f in _by_rule(detect_conformance(drifted))["R31"]}
    assert "JOB0020_SAMPLE_AWS_PLCT:PIPELINE_ID" in orphans
    assert not [t for t in orphans if t.endswith(":FILE_EXTENSION")]
    assert not [t for t in orphans if t.endswith(":DS_VER")]  # a fact, not an orphan


def test_r32_requires_the_uniform_cmd_set_at_some_scope(drifted) -> None:
    missing = {f.target for f in _by_rule(detect_conformance(drifted))["R32"]}
    assert "JOB0020_SAMPLE_AWS_PLCT:ETL_PLATFORM" in missing
    assert "JOB0010_SAMPLE_DAT_ONPM_FW:FILE_DIR" in missing


def test_r33_rules_the_literal_the_carrier_not_the_variable(drifted) -> None:
    (finding,) = _by_rule(detect_conformance(drifted))["R33"]
    assert finding.target == "JOB0020_SAMPLE_AWS_PLCT:PIPELINE_ID"
    assert "remove the variable" in finding.message


def test_r34_reports_a_swap_as_a_wrong_row_not_a_missing_one(drifted) -> None:
    """The swapped pair is the worst class in the set: both names resolve, so
    the graph gains two facts and one of them is false."""
    findings = _by_rule(detect_conformance(drifted))["R34"]
    targets = {f.target for f in findings}
    assert "JOB0021_SAMPLE_AWS_TRUST:DS_ID" in targets
    assert "JOB0021_SAMPLE_AWS_TRUST:DS_VER" in targets
    assert all(f.severity == "must-fix" for f in findings)
    assert all("wrong row, not a missing one" in f.message for f in findings)


def test_r2_reports_drift_as_silence_and_distinguishes_an_alias(drifted) -> None:
    by_target = {f.target: f for f in _by_rule(detect_conformance(drifted))["R2"]}
    drift = by_target["JOB0020_SAMPLE_AWS_PLCT:DATA_FLOW"]
    assert drift.severity == "should-fix"
    assert "NO fact row at all" in drift.message  # the SILENCE class
    alias = by_target["JOB0021_SAMPLE_AWS_TRUST:IMG_PATH"]
    assert alias.severity == "advisory"  # materializes, just with a WARN
    assert "ETL_ARTIFACT_URI" in alias.message


def test_r35_finds_the_copy_paste_that_causes_the_drift(drifted) -> None:
    hoistable = {f.target.split(":")[1] for f in _by_rule(detect_conformance(drifted))["R35"]}
    assert {"ENV", "LAUNCHER_SCRIPT_PATH", "FILE_PREFIX"} <= hoistable


def test_r36_catches_the_same_file_written_twice(drifted) -> None:
    (finding,) = _by_rule(detect_conformance(drifted))["R36"]
    assert finding.target == "JOB0020_SAMPLE_AWS_PLCT:DAT_FILE"
    assert "DAT_FILE_NM" in finding.message


def test_r37_flags_adjacent_references_as_ambiguous(drifted) -> None:
    targets = {f.target for f in _by_rule(detect_conformance(drifted))["R37"]}
    assert "JOB0010_SAMPLE_DAT_ONPM_FW:watch_template" in targets


def test_r38_enforces_the_vendor_charset(drifted) -> None:
    (finding,) = _by_rule(detect_conformance(drifted))["R38"]
    assert finding.target.endswith(":DevX-project")
    assert finding.severity == "must-fix"


def test_r39_requires_the_cat_on_tok_and_forbids_it_on_dat(drifted) -> None:
    """The TOK job's cat no longer mirrors its watch path — the path was
    edited and the post-command was not. Reusing the SAME expression is the
    whole point of the rule: the file detected must be the file echoed."""
    by_rule = _by_rule(detect_conformance(drifted))
    (tok,) = by_rule["R39a"]
    assert tok.target == "JOB0011_SAMPLE_TOK_ONPM_FW:post_command"
    (dat,) = by_rule["R39b"]
    assert dat.target == "JOB0010_SAMPLE_DAT_ONPM_FW:post_command"
    assert dat.severity == "must-fix"  # multi-GB into sysout is not a nit
    assert "multi-GB" in dat.message


def test_r40_removes_every_generated_notification_including_domail(drifted) -> None:
    """REQ-2 removed the shouts and left DOMAIL out of scope; the SME ruling of
    2026-08-11 extends it to mail. Both kinds are reported, and the container
    that emits one is named — a folder shout and a job's On-Do mail are two
    different edits."""
    by_target = {f.target: f for f in _by_rule(detect_conformance(drifted))["R40"]}
    assert "SHOUT" in by_target["FOLDER-SYNTH-DRIFT:notifications"].message
    job = by_target["JOB0021_SAMPLE_AWS_TRUST:notifications"]
    assert "DOMAIL" in job.message
    # the fix is deletion; declaring %%EMAIL_GRP would re-wire what is removed
    assert "do not declare its destination" in job.message


def test_nothing_binds_notify_to_a_distribution_list(drifted) -> None:
    """Email is being removed as a mechanism: the incident is the call to
    action. An unset %%NOTIFY is reported as an ordinary unresolvable
    reference and NEVER as 'point this at a support DL'."""
    messages = " ".join(f.message for f in detect_conformance(drifted))
    assert "EMAIL_DL" not in messages
    assert "NOTIFY" not in messages or "CTMERR" in messages


# == the pass is additive, never a replacement ===============================


def test_conformance_is_separate_from_the_m0_detector(drifted) -> None:
    """M0 pins detect_findings(modern) == []; a conformance pass legitimately
    has plenty to say about a minimal transcript. Keeping them apart preserves
    that contract, and detect_all composes them."""
    combined = detect_all(drifted)
    rules = {f.rule_id for f in combined}
    assert DOT_SMUGGLING_RULE_ID in rules
    assert len(combined) == len(detect_conformance(drifted)) + len(
        [f for f in combined if f.rule_id == DOT_SMUGGLING_RULE_ID]
    )


def test_every_finding_is_unratified(drifted) -> None:
    """Rule ratification is gate territory until the registry is machine
    readable; hardcoding those judgments here would leak gate decisions."""
    assert all(f.ratified is False for f in detect_all(drifted))


def test_findings_carry_the_registry_severity_vocabulary(drifted) -> None:
    allowed = {"must-fix", "should-fix", "advisory"}
    assert {f.severity for f in detect_all(drifted)} <= allowed
