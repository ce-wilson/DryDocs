"""render_remediation_profile.py — the /remediation INTAKE surface's input (O59).

Emits ``web/src/generated/remediation-profile.json``: one G68 ``FolderSetProfile``
computed by the REAL ``profile()`` over a SYNTHETIC folder-set export. The console
renders the four censuses, the findings and the substitution slots from this file
and computes nothing of its own — the SME reads what the export actually says.

WHY A GENERATED ARTIFACT AND NOT AN UPLOAD. O59 deliberately left the transport
open, saying it "follows G68's transport choice and must not be pre-empted here --
an upload widget built against a transport that turns out to be a CLI artifact is
thrown away". G68 then NAMED its transport: a CLI verb (``drydocs profile-folder-set
<export-dir> -o <json>``) writing a JSON artifact. So this is that choice honoured,
not a new one: the console consumes the verb's output shape, and the same
render/drift-guard pattern the fix-diff frame already uses (O17 → 2026-08-12) makes
the committed copy provably the mechanism's own output rather than a hand-written
mock. Cost against ADR 0005 is NIL for the same reason G68 recorded: remediation
reads no graph and writes none, so QuerySpecs are out by construction.

WHAT THE COMMITTED COPY IS AND IS NOT. It is SYNTHETIC — invented FIDs, SEALs from
the reserved 70001-70099 block, ``example.invalid`` addresses, invented paths. Real
folder sets carry real identity values and are Internal (J23). What it demonstrates
is the MECHANISM and the two failure classes, which is what the frame has to teach.

THE FIXTURE IS BUILT TO CARRY BOTH FAILURE CLASSES, because the whole point of the
findings frame is that it must not flatten them:
  * ``%%ds_ver`` (lower case) is the SILENCE class — R2 name drift. The registry
    lookup is exact, so the name produces NO fact row: the lineage is missing.
  * ``%%DS_VER = "v3"`` is the CONFIDENTLY WRONG class — R34 value contract. The
    name resolves, so a row IS written, carrying a false value.
It also carries the 2026-08-19 SME evidence shape (FileWatcher on the Control-M
platform account beside payload jobs on the application account), one shared
wrapper with fan-out 2 and one solo wrapper with fan-out 1, an orphan declaration,
a legacy mail destination and the DOMAIL block that would have consumed it (so all
three contact kinds appear, and R40 fires on the block whose deletion is exactly
why every contact row is documentation-only), and a folder that
supplies two of the nine substitution slots and no more.

Consumed by ``web/src/remediation/profileData.ts``. Drift guard:
``tests/unit/test_remediation_profile_json.py``. Registered in ``render_board.py``'s
default-paths run — an unregistered artifact silently drifts (the J20 incident).

Determinism: no timestamps, no randomness, and ``source`` is passed EXPLICITLY
rather than derived from the staging directory, because the extractor's contract is
a directory and a temp path would differ per machine and per run — which is a drift
guard that fails for a reason having nothing to do with drift.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from drydocs_lineage.extractors import ControlMXmlDefsExtractor  # noqa: E402
from drydocs_remediation.profile import profile  # noqa: E402
from drydocs_remediation.xml_bridge import to_definition_set  # noqa: E402

OUT = REPO / "web" / "src" / "generated" / "remediation-profile.json"

#: A stable stand-in for the staged export directory. The real verb records the
#: files it read; here the path is a temp dir, so naming it would make the
#: artifact differ per machine.
SOURCE = "SYNTHETIC demo export — export.xml (1 file staged)"

DEMO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="T032-E0700-DMA" FOLDER_NAME="PRSYNQ-INTAKE-DLY"
                DESCRIPTION="synthetic intake series - demo profile">
    <VARIABLE NAME="%%FID" VALUE="fid.synth.intake"/>
    <VARIABLE NAME="%%SEAL" VALUE="70004"/>
    <VARIABLE NAME="%%EMAIL_DL_L2" VALUE="l2_support@example.invalid"/>
    <VARIABLE NAME="%%EMAIL_DL_PDN" VALUE="downstream_owners@example.invalid"/>
    <VARIABLE NAME="%%NOTIFY" VALUE="legacy_mail@example.invalid"/>
    <VARIABLE NAME="%%WRAPPER" VALUE="/apps/synth/bin/generic_wrapper.ksh"/>
    <VARIABLE NAME="%%ORPHAN_ONE" VALUE="declared and never referenced"/>
    <SUB_FOLDER FOLDER_NAME="SAMPLE_DATASET">
      <VARIABLE NAME="%%DS_NAME" VALUE="sample_dataset"/>
      <JOB JOBNAME="JOB0010_SAMPLE_DAT_ONPM_FW" TASKTYPE="FileWatcher"
           APPLICATION="SYNTHAPP" RUN_AS="ctm.platform.acct"
           FILE_PATH="/data/synth/in/sample.dat"
           POSTCMD="cat /data/synth/in/sample.dat"/>
      <JOB JOBNAME="JOB0020_SAMPLE_PLCT" TASKTYPE="Command"
           APPLICATION="SYNTHAPP" RUN_AS="svc.synth.app"
           CMDLINE="%%WRAPPER -m %%MAPPING -e %%ENVCODE -v %%DS_VER">
        <VARIABLE NAME="%%MAPPING" VALUE="m_place_sample"/>
        <VARIABLE NAME="%%ENVCODE" VALUE="prod"/>
        <VARIABLE NAME="%%DS_VER" VALUE="v3"/>
      </JOB>
      <JOB JOBNAME="JOB0030_SAMPLE_TRUST" TASKTYPE="Command"
           APPLICATION="SYNTHAPP" RUN_AS="svc.synth.app"
           CMDLINE="%%WRAPPER -m %%MAPPING -e %%ENVCODE -v %%ds_ver">
        <VARIABLE NAME="%%MAPPING" VALUE="m_trust_sample"/>
        <VARIABLE NAME="%%ENVCODE" VALUE="prod"/>
        <VARIABLE NAME="%%ds_ver" VALUE="3.1"/>
      </JOB>
      <JOB JOBNAME="JOB0040_SAMPLE_SOLO" TASKTYPE="Command"
           APPLICATION="SYNTHOTHER" RUN_AS="svc.synth.app"
           CMDLINE="/apps/synth/bin/solo_only.ksh -d %%DS_NAME">
        <ON STMT="*" CODE="NOTOK">
          <DOMAIL DEST="legacy_ops_dl@example.invalid" SUBJECT="solo job failed"/>
        </ON>
      </JOB>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""


def build_remediation_profile() -> dict:
    """The whole frame, computed by the real G68 ``profile()``.

    Not pure — the extractor's contract is a DIRECTORY, so the demo export is
    staged into a temporary one. Nothing outside that directory is touched, and
    ``source`` is overridden so the temp path never reaches the artifact.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The newline pin matters even on a throwaway fixture: the extractor
        # reads what is written, so an unpinned write makes the census differ
        # between a machine that translates line endings and one that does not.
        (root / "export.xml").write_text(DEMO_XML, encoding="utf-8", newline="\n")
        staged = ControlMXmlDefsExtractor().extract(root)
        prof = profile(to_definition_set(staged, source=SOURCE))

    data = prof.as_dict()
    data["note"] = (
        "GENERATED by scripts/render_remediation_profile.py — never hand-edit; "
        "regenerate with a default-paths render_board.py run"
    )
    data["provenance"] = (
        "SYNTHETIC folder-set export through the REAL G68 profile() — the same "
        "census the `drydocs profile-folder-set` verb writes. Real exports carry "
        "real FIDs, SEALs and DLs and are Internal; drydocs_remediation writes no "
        "graph, so there is no QuerySpec by design."
    )
    data["summary"] = prof.summary()
    return data


def main() -> None:
    data = build_remediation_profile()
    OUT.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {OUT} ({data['summary']})")


if __name__ == "__main__":
    main()
