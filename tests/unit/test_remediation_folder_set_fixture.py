"""REM2 — the bundled folder-set export, and the verb that reads it.

WHY THE FIXTURE EXISTS. `drydocs profile-folder-set` is the remediation module's
only CLI verb and the runbook's step 2, and until now nothing in the tree fed it:
its only demonstrations were against real exports on one machine, so a runbook
reader took the output shape on faith. That is the J18 preference — sample
reproducible over machine pinned — failing on the one document written for the
support audience.

WHERE IT LIVES, AND WHY NOT BESIDE THE CSV SAMPLES. The item's inputs named
`drydocs/data/samples/`, and that directory is exactly wrong for this fixture:
`drydocs/data/**` is `never-port`, so a file there is in every clone of THIS repo
and in no consumer clone. A runbook written for the support audience would then
name a path that audience does not have, and the test below would need a skip
guard that makes it vacuous on the side that matters — which is the ruling Lane A
made on 2026-09-09 (`97e2d5d3`) when three CORE9 skip removals failed
`test_never_port_citations` for that same reason. `tests/**` is `evaluate`, it
crosses, and the module's other synthetic fixtures already live here. The runbook
cites this directory beside the transcript fixture it already cited.

SYNTHETIC, AND SWEPT FOR IT. `tests/fixtures/` sits OUTSIDE the publish-boundary
guard's scan A, so a real application id pasted into the XML would ride a green
suite to a public push. The sweep below is this file's job, on the J15 lesson:
sweep for the VALUE, not the field, because the ids in this fixture live inside
folder-name strings.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs_lineage.extractors import ControlMXmlDefsExtractor
from drydocs_remediation.detect import CONFORMANCE_RULE_IDS, DOT_SMUGGLING_RULE_ID, detect_all
from drydocs_remediation.profile import profile
from drydocs_remediation.xml_bridge import to_definition_set

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "remediation" / "synthetic-folder-set-export"
EXPORT = FIXTURE_DIR / "demo-folder-set.xml"
RUNBOOK = REPO / "docs" / "design" / "drydocs-remediation-runbook.md"

SYNTHETIC_BLOCK = range(70001, 70100)

#: Any run of five or six digits in the fixture. Five-digit runs are the shape a
#: real application id takes, and they hide inside folder names here on purpose,
#: which is the only reason a value sweep beats a field check.
_ID_SHAPED = re.compile(r"\b\d{5,6}\b")


def _profile():
    return profile(to_definition_set(ControlMXmlDefsExtractor().extract(FIXTURE_DIR)))


# -- (b) the value sweep -------------------------------------------------------


def test_every_id_shaped_value_is_in_the_reserved_synthetic_block() -> None:
    text = EXPORT.read_text(encoding="utf-8")
    outside = sorted(
        {value for value in _ID_SHAPED.findall(text) if int(value) not in SYNTHETIC_BLOCK}
    )
    assert not outside, (
        f"id-shaped values outside the reserved synthetic block 70001-70099: {outside} — "
        "tests/fixtures/ is outside the publish-boundary guard's scan A, so this test IS "
        "the sweep for this file, and the values sit inside folder-name strings"
    )


# -- (e) the report's TOP-LEVEL shape, not its prose ---------------------------


def test_the_artifact_has_the_two_halves_the_runbook_describes() -> None:
    """Five censuses, then the substitution slots — the division is the point,
    so the keys are the contract and the wording of any row is not."""
    blob = _profile().as_dict()
    assert list(blob) == [
        "source",
        "shape",
        "identity",
        "variables",
        "contacts",
        "invocations",
        "substitution_slots",
        "findings",
    ]
    assert json.loads(json.dumps(blob)), "the transport is a JSON artifact"


def test_the_shape_census_counts_what_the_fixture_declares() -> None:
    """The counts the runbook's success line quotes. Pinned so an edit to the
    fixture that changes them has to change the runbook in the same commit."""
    shape = _profile().shape
    assert shape.folders == [
        "PRSYNG-REM2-70004-DEMO-DLY",
        "PRSYNG-REM2-70004-DEMO-WKLY",
        "PRSYNG_REM2_70005_LEGACY",
    ]
    assert len(shape.subfolders) == 2
    assert shape.jobs == 12


def test_the_substitution_slots_report_not_supplied_rather_than_a_default() -> None:
    """The half of the artifact that exists to REFUSE. A slot the export cannot
    answer carries a null, never an invented value — inventing one is how a
    proposal becomes a wrong fact nobody re-checks."""
    slots = _profile().substitution_slots
    open_slots = [s for s in slots if s.status == "not-supplied"]
    assert open_slots, "a synthetic export must still leave the human-supplied facts open"
    assert all(s.value is None for s in open_slots)


# -- (a) one instance of each defect the detectors handle ----------------------


def test_the_fixture_carries_a_case_for_every_rule_the_detectors_implement() -> None:
    """Read from the registry, not from the fixture's own header (J37): adding a
    rule to CONFORMANCE_RULE_IDS without adding a case here fails HERE, which is
    the only moment anyone would think to extend the fixture.
    """
    raised = {
        f.rule_id
        for f in detect_all(to_definition_set(ControlMXmlDefsExtractor().extract(FIXTURE_DIR)))
    }
    expected = set(CONFORMANCE_RULE_IDS) | {DOT_SMUGGLING_RULE_ID}
    assert expected <= raised, (
        f"the bundled folder set raises no case for {sorted(expected - raised)} — "
        "add a job to demo-folder-set.xml that produces it, and name it in the "
        "header comment's per-job list"
    )


def test_the_header_comment_names_every_rule_the_fixture_raises() -> None:
    """(c) A reader must be able to tell which finding each job is there to
    produce. The header is prose, so this checks only that no rule the detectors
    raise is missing from it — the direction that goes stale."""
    header = EXPORT.read_text(encoding="utf-8").split("-->", 1)[0]
    raised = {
        f.rule_id
        for f in detect_all(to_definition_set(ControlMXmlDefsExtractor().extract(FIXTURE_DIR)))
    }
    unnamed = sorted(rule for rule in raised if rule not in header)
    assert not unnamed, (
        f"the fixture raises {unnamed} and its header comment does not name them — "
        "the header is how a reader joins a finding to the job that causes it"
    )


def test_one_job_is_compliant_so_the_fixture_is_not_all_defects() -> None:
    """A set where every job is broken teaches nothing about what right looks
    like. JOB0130 is the CTL watcher that cats the file it watched, correctly."""
    findings = detect_all(to_definition_set(ControlMXmlDefsExtractor().extract(FIXTURE_DIR)))
    assert not [f for f in findings if f.target.startswith("JOB0130_DEMO_FEED_CTL")]


# -- (d) the runbook's command line, and the verb it names ---------------------


def test_the_runbook_invokes_the_verb_on_this_fixture() -> None:
    """The runbook promises the census runs in any clone. The path it prints has
    to be the path that exists, which is what makes the promise checkable."""
    runbook = RUNBOOK.read_text(encoding="utf-8")
    cited = "drydocs profile-folder-set tests/fixtures/remediation/synthetic-folder-set-export"
    assert cited in runbook, "the runbook no longer runs the verb on the bundled folder set"
    assert FIXTURE_DIR.is_dir() and EXPORT.exists()


def test_profile_folder_set_is_still_the_modules_only_registered_verb() -> None:
    """The runbook says so twice, and the sentence is only safe while it is true.
    Read from the registered commands (J37), never from `drydocs --help`."""
    names = {c.name or c.callback.__name__ for c in cli_mod.app.registered_commands}
    assert "profile-folder-set" in names
    remediation_verbs = {n for n in names if "folder-set" in n or "remediat" in n}
    assert remediation_verbs == {"profile-folder-set"}, (
        f"the remediation module registers {sorted(remediation_verbs)} — the runbook's "
        "'this is the module's only CLI verb' is no longer true and must be rewritten"
    )


def test_the_verb_exits_zero_and_writes_the_artifact(tmp_path: Path) -> None:
    """The CLI's contract is its exit code and the file it leaves behind, so
    asserting on those is the exception J37 allows — the summary PROSE is a
    render and nothing here reads it."""
    out = tmp_path / "folder-set-profile.json"
    result = CliRunner().invoke(
        cli_mod.app, ["profile-folder-set", str(FIXTURE_DIR), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text(encoding="utf-8"))["shape"]["jobs"] == 12
