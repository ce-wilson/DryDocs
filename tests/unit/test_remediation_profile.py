"""G68 — the folder-set PROFILE (census + substitution slots).

The fixture is built to exercise every census at once, and it carries the
2026-08-19 SME evidence shape deliberately: the FileWatcher runs as the
Control-M PLATFORM account while the payload jobs run as the APPLICATION
account. That pairing is the DESIGNED pattern, and a flat run_as census would
blur it into "this folder uses two accounts" — which is why census (b) reports
run_as by job type.

SYNTHETIC throughout — ``example.invalid`` addresses, invented FIDs, SEALs,
paths and DLs. Real values are Internal (J23), and the SEALID lesson is that
values hide inside name strings, so nothing here is copied from an estate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs_lineage.extractors import ControlMXmlDefsExtractor
from drydocs_remediation.profile import NOT_SUPPLIED, profile
from drydocs_remediation.xml_bridge import to_definition_set

DC = "T032-E0700-DMA"

#: one generic wrapper shared by two jobs (the Informatica shape the SME
#: described: the same few .ksh wrappers for ALL business applications) and one
#: wrapper invoked by exactly one job (the fan-out-1 control).
_PROFILE_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="{DC}" FOLDER_NAME="PRSYNG-PROFILE-DLY">
    <VARIABLE NAME="%%FID" VALUE="fid.synth.app"/>
    <VARIABLE NAME="%%SEAL" VALUE="70001"/>
    <VARIABLE NAME="%%EMAIL_DL_L2" VALUE="l2_support@example.invalid"/>
    <VARIABLE NAME="%%EMAIL_DL_PDN" VALUE="downstream_owners@example.invalid"/>
    <VARIABLE NAME="%%NOTIFY" VALUE="legacy_mail@example.invalid"/>
    <VARIABLE NAME="%%WRAPPER" VALUE="/apps/synth/bin/generic_wrapper.ksh"/>
    <VARIABLE NAME="%%ORPHAN_ONE" VALUE="unused"/>
    <SUB_FOLDER FOLDER_NAME="SAMPLE_DATASET">
      <VARIABLE NAME="%%DS_NAME" VALUE="sample_dataset"/>
      <JOB JOBNAME="JOB0010_SAMPLE_DAT_ONPM_FW" TASKTYPE="FileWatcher"
           APPLICATION="SYNTHAPP" RUN_AS="ctm.platform.acct"
           FILE_PATH="/data/synth/in/sample.dat"
           POSTCMD="cat /data/synth/in/sample.dat"/>
      <JOB JOBNAME="JOB0020_SAMPLE_PLCT" TASKTYPE="Command"
           APPLICATION="SYNTHAPP" RUN_AS="svc.synth.app"
           CMDLINE="%%WRAPPER -m %%MAPPING -e %%ENVCODE">
        <VARIABLE NAME="%%MAPPING" VALUE="m_place_sample"/>
        <VARIABLE NAME="%%ENVCODE" VALUE="prod"/>
      </JOB>
      <JOB JOBNAME="JOB0030_SAMPLE_TRUST" TASKTYPE="Command"
           APPLICATION="SYNTHAPP" RUN_AS="svc.synth.app"
           CMDLINE="%%WRAPPER -m %%MAPPING -e %%ENVCODE">
        <VARIABLE NAME="%%MAPPING" VALUE="m_trust_sample"/>
        <VARIABLE NAME="%%ENVCODE" VALUE="prod"/>
      </JOB>
      <JOB JOBNAME="JOB0040_SAMPLE_SOLO" TASKTYPE="Command"
           APPLICATION="SYNTHOTHER" RUN_AS="svc.synth.app"
           CMDLINE="/apps/synth/bin/solo_only.ksh -d %%DS_NAME"/>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""


@pytest.fixture()
def prof(tmp_path: Path):
    root = tmp_path / "profile"
    root.mkdir()
    (root / "export.xml").write_text(_PROFILE_XML, encoding="utf-8")
    return profile(to_definition_set(ControlMXmlDefsExtractor().extract(root)))


# == the contract ============================================================


def test_the_profile_is_one_json_serializable_object(prof) -> None:
    """The acceptance's shape: ONE FolderSetProfile, and the transport is a
    JSON artifact — so anything unserializable is a defect, not a detail."""
    blob = json.dumps(prof.as_dict())
    assert json.loads(blob)["shape"]["jobs"] == 4
    assert "slots:" in prof.summary()


def test_it_asserts_nothing_about_meaning_findings_ride_alongside(prof) -> None:
    """The module's standing invariant. The profile is a CENSUS: the defect
    list stays detect_all()'s output and is carried, never restated or ranked
    here, and nothing is ratified."""
    assert prof.findings, "the fixture should raise findings to carry"
    assert all(f["ratified"] is False for f in prof.findings)


# == (a) shape ===============================================================


def test_shape_counts_containers_and_job_types(prof) -> None:
    assert prof.shape.data_centers == [DC]
    assert prof.shape.folders == ["PRSYNG-PROFILE-DLY"]
    assert prof.shape.subfolders == ["PRSYNG-PROFILE-DLY/SAMPLE_DATASET"]
    assert prof.shape.jobs_by_type == {"file-watcher": 1, "other": 1, "placement": 1, "trust": 1}
    # dataset identity lives on the sub-folder ladder, so the leaf is the READING
    assert prof.shape.datasets_inferred == ["SAMPLE_DATASET"]


# == (b) identity ============================================================


def test_identity_reports_run_as_by_job_type_not_as_a_flat_list(prof) -> None:
    """THE 2026-08-19 SME EVIDENCE RIDER. A FileWatcher on the Control-M
    platform account beside payload jobs on the application account is the
    DESIGNED pattern — reported flat it reads as "two accounts", which loses
    the finding. The job-type split is what makes the pairing visible."""
    run_as = {r.value: r for r in prof.identity if r.fact == "RUN_AS"}
    assert set(run_as) == {"ctm.platform.acct", "svc.synth.app"}
    assert run_as["ctm.platform.acct"].job_types == ["file-watcher"]
    assert sorted(run_as["svc.synth.app"].job_types) == ["other", "placement", "trust"]


def test_identity_carries_where_used_not_bare_distinct_values(prof) -> None:
    """The SME's next question is always WHICH JOBS, so every row carries them."""
    fid = next(r for r in prof.identity if r.fact == "FID")
    assert fid.value == "fid.synth.app"
    assert len(fid.jobs) == 4  # inherited from folder scope by every job
    apps = {r.value: r.jobs for r in prof.identity if r.fact == "APPLICATION"}
    assert apps["SYNTHOTHER"] == ["JOB0040_SAMPLE_SOLO"]
    seal = next(r for r in prof.identity if r.fact == "SEAL")
    assert seal.value == "70001"  # reserved synthetic block


# == (c) variables ===========================================================


def test_variable_census_carries_its_defect_state_inline(prof) -> None:
    """Census and defect list are ONE table here, not two the reader joins by
    hand: R31 (orphan) and R30 (unresolved) are answered on the row that names
    the variable."""
    rows = {(r.name, r.scope): r for r in prof.variables}
    orphan = rows[("ORPHAN_ONE", "FOLDER")]
    assert orphan.distinct_values == 1 and orphan.reference_count == 0

    mapping = rows[("MAPPING", "JOB")]
    assert mapping.distinct_values == 2  # m_place_sample / m_trust_sample
    assert mapping.reference_count == 2
    assert mapping.unreferenced is False

    wrapper = rows[("WRAPPER", "FOLDER")]
    assert wrapper.reference_count == 2  # the two jobs sharing it


# == (d) contacts ============================================================


def test_contacts_split_by_kind_and_are_documentation_only(prof) -> None:
    """The shared EMAIL_DL_ prefix hides two audiences (guidelines §7.3): L2/L3
    are internal support tiers, PDN is downstream business users. The page says
    MUST NOT collapse them. And every row is documentation-only, because R40
    deletes the block that would have used a mail destination."""
    kinds = {c.name: c.kind for c in prof.contacts}
    assert kinds["EMAIL_DL_L2"] == "support-tier"
    assert kinds["EMAIL_DL_PDN"] == "delay-notification-consumer"
    assert kinds["NOTIFY"] == "domail-destination"
    assert all(c.documentation_only for c in prof.contacts)
    assert all(c.containers == ["PRSYNG-PROFILE-DLY"] for c in prof.contacts)


# == (e) invocations =========================================================


def test_shared_wrapper_reports_fan_out_and_what_varies_under_it(prof) -> None:
    """The identity-grade census. On a generic-wrapper platform the script path
    distinguishes nothing, so what the lineage gate needs to know is WHICH
    parameter varies per job. This measures it; the ruling stays the gate's."""
    shared = next(i for i in prof.invocations if i.fan_out > 1)
    assert shared.fan_out == 2
    assert sorted(shared.jobs) == ["JOB0020_SAMPLE_PLCT", "JOB0030_SAMPLE_TRUST"]
    # MAPPING differs per job -> an identity-grade candidate; ENVCODE does not
    assert shared.varying_variables == ["MAPPING"]
    assert "ENVCODE" in shared.constant_variables


def test_a_fan_out_of_one_is_reported_too(prof) -> None:
    """Explicitly required: a one-to-one wrapper is the EVIDENCE that path
    identity IS sufficient for that kind, which is as decision-relevant as the
    converse. Dropping it would bias the census toward the shared case."""
    solo = [i for i in prof.invocations if i.fan_out == 1]
    assert solo, "fan-out-1 wrappers must appear"
    assert any(i.jobs == ["JOB0040_SAMPLE_SOLO"] for i in solo)


# == substitution slots ======================================================


def test_a_slot_with_no_value_is_not_supplied_and_never_a_default(prof) -> None:
    """The clause the SME will check. An absent slot must be structurally
    unfakeable: status says not-supplied AND value is None — never "", never a
    placeholder. Inventing one is how a proposal becomes a wrong fact nobody
    re-checks."""
    slots = {s.name: s for s in prof.substitution_slots}
    absent = slots["DEVX_KEY"]
    assert absent.status == NOT_SUPPLIED
    assert absent.value is None
    assert absent.value != ""


def test_a_slot_present_in_the_export_reports_its_current_value(prof) -> None:
    slots = {s.name: s for s in prof.substitution_slots}
    assert slots["EMAIL_DL_L2"].status == "present"
    assert slots["EMAIL_DL_L2"].value == "l2_support@example.invalid"


def test_every_slot_names_its_rule_and_the_jobs_it_applies_to(prof) -> None:
    """Each slot carries the vocabulary or shape rule from the guidelines page
    — quoted, not invented — and the jobs it would apply to."""
    slots = {s.name: s for s in prof.substitution_slots}
    assert "^FTS[A-Z]*[0-9]+$" in slots["FTS_ID"].rule  # the page's own shape
    assert "MFTS_AGENT" in slots["DELIVERY_MECHANISM"].rule
    assert all(s.rule for s in prof.substitution_slots)
    # watcher-description slots apply to the watchers, folder slots to all jobs
    assert slots["FTS_ID"].applies_to == ["JOB0010_SAMPLE_DAT_ONPM_FW"]
    assert len(slots["DEVX_KEY"].applies_to) == 4


def test_the_slot_list_is_closed_and_matches_the_acceptance(prof) -> None:
    """Named in the item, so pinned here: drift in this list is a scope change,
    not a refactor."""
    assert [s.name for s in prof.substitution_slots] == [
        "DEVX_KEY",
        "DELIVERY_MECHANISM",
        "USER",
        "FTS_ID",
        "REC_ID",
        "SOURCE_CONTACT",
        "EMAIL_DL_L2",
        "EMAIL_DL_L3",
        "EMAIL_DL_PDN",
    ]
