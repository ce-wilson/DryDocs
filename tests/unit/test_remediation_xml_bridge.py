"""G67 — staged Control-M XML adapted into the remediation definition shape.

The bridge exists because reading definition XML was solved at G47 while
``XmlDefinitionFormat.load`` still refuses on vendor-schema grounds. It adapts
rather than parses, and it imports NO other component: it declares the shape it
needs as protocols, so the extractor satisfies them without remediation
depending on lineage (``test_module_boundary.py``). These cases pin the two
things that could silently go wrong in an adapter — the scope chain arriving
intact, and ``dump`` staying blocked.

SYNTHETIC throughout; ``example.invalid`` addresses and invented ids.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_lineage.extractors import ControlMXmlDefsExtractor
from drydocs_remediation.formats import XmlDefinitionFormat
from drydocs_remediation.xml_bridge import to_definition_set

DC = "P032-E0700-DMA"

_EXPORT = f"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="{DC}" FOLDER_NAME="FOLDER-SYNTH-UPD"
                DESCRIPTION="datasetSeriesName: SAMPLE |SeriesSLA: 17:00 EST">
    <VARIABLE NAME="%%ENV" VALUE="prod"/>
    <VARIABLE NAME="%%DROPBOX_DIR" VALUE="/data/synth/dropbox/UPD/"/>
    <SHOUT DEST="EM" MESSAGE="synthetic"/>
    <SUB_FOLDER SUB_FOLDER_NAME="SAMPLE_LKP">
      <VARIABLE NAME="%%DATAFLOW" VALUE="SAMPLE_LKP"/>
      <VARIABLE NAME="%%FILE_PREFIX" VALUE="SAMPLE_LKP_"/>
      <JOB JOBNAME="JOB0010_SAMPLE_LKP_TOK_ONPM_FW" TASKTYPE="FileWatcher"
           FILE_PATH="%%DROPBOX_DIR.%%FILE_PREFIX.%%$ODATE..tok"
           POSTCMD="cat %%DROPBOX_DIR.%%FILE_PREFIX.%%$ODATE..tok"
           DESCRIPTION="DELIVERY_MECHANISM: MFTS_AGENT | FTS_ID: FTS2">
        <VARIABLE NAME="%%FILE_EXTENSION" VALUE=".tok"/>
        <ON STMT="*" CODE="NOTOK">
          <DOMAIL DEST="%%NOTIFY"/>
        </ON>
      </JOB>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""


@pytest.fixture()
def definitions(tmp_path: Path):
    root = tmp_path / "controlm-xml"
    root.mkdir()
    (root / "export.xml").write_text(_EXPORT, encoding="utf-8")
    return to_definition_set(ControlMXmlDefsExtractor().extract(root))


def test_folders_and_subfolders_arrive_as_distinct_scopes(definitions) -> None:
    """A sub-folder has no record of its own in the extract — it is a variable
    container — so the bridge reconstructs it. It must NOT be folded into the
    folder layer, because it resolves between folder and job."""
    by_scope = {f.scope: f for f in definitions.folders}
    assert set(by_scope) == {"FOLDER", "SUBFOLDER"}
    assert by_scope["FOLDER"].name == "FOLDER-SYNTH-UPD"
    assert by_scope["SUBFOLDER"].name == "FOLDER-SYNTH-UPD/SAMPLE_LKP"
    assert [n for n, _ in by_scope["SUBFOLDER"].variables] == ["%%DATAFLOW", "%%FILE_PREFIX"]
    # folder_variables() is the FOLDER layer alone
    assert [n for n, _ in definitions.folder_variables()] == ["%%ENV", "%%DROPBOX_DIR"]


def test_scope_chain_survives_the_bridge_widest_first(definitions) -> None:
    """The chain comes FROM the extractor rather than being recomputed — two
    implementations of Control-M scope resolution would be the same mistake as
    two resolvers."""
    (job,) = definitions.jobs
    chain = definitions.resolution_chain(job)
    assert [scope for scope, _c, _d in chain] == ["FOLDER", "SUBFOLDER", "JOB"]
    assert [n for n, _ in chain[0][2]] == ["%%ENV", "%%DROPBOX_DIR"]
    assert [n for n, _ in chain[1][2]] == ["%%DATAFLOW", "%%FILE_PREFIX"]
    assert [n for n, _ in chain[2][2]] == ["%%FILE_EXTENSION"]


def test_job_fields_the_conformance_pass_needs_are_carried(definitions) -> None:
    (job,) = definitions.jobs
    assert job.job_type == "FileWatcher"
    assert job.subfolder_path == "SAMPLE_LKP"
    assert job.watch_template == "%%DROPBOX_DIR.%%FILE_PREFIX.%%$ODATE..tok"
    assert job.post_command == "cat %%DROPBOX_DIR.%%FILE_PREFIX.%%$ODATE..tok"
    assert job.description.startswith("DELIVERY_MECHANISM: MFTS_AGENT")


def test_notification_tags_are_recorded_per_container_not_inherited(definitions) -> None:
    """REQ-2 asks WHICH notification kinds a container emits, so the extractor
    records names rather than only counting. A folder must not report its
    jobs' notifications as its own, or every folder looks non-conformant."""
    by_scope = {f.scope: f for f in definitions.folders}
    assert by_scope["FOLDER"].notification_tags == ("SHOUT",)
    (job,) = definitions.jobs
    assert job.notification_tags == ("DOMAIL",)  # nested under ON, found by descent


def test_provenance_points_at_the_export(definitions) -> None:
    assert definitions.source.endswith("export.xml")


def test_dump_stays_blocked_reading_was_never_the_blocked_half() -> None:
    """The bridge retires the READ half of the XML blocker. Emitting XML that
    Control-M will import still needs the vendor schema, and inventing it is
    exactly what the blocked message refuses."""
    with pytest.raises(NotImplementedError, match="schema acquisition pending"):
        XmlDefinitionFormat().dump(None, Path("unused.xml"))
