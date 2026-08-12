"""Defect B′ regression: no evidence is never evidence.

The POC's exact failure, pinned: a command-only job pair used to compare
``None == None`` on the watch surface and report ``equivalent=True`` — which
is how "PASS 12/12" shipped while six CMDLINEs were broken. Now command lines
are resolved and diffed, and a job with nothing comparable is named in
``not_proven`` and blocks the claim.
"""

from __future__ import annotations

from drydocs_remediation.equivalence import prove_equivalence, resolved_command
from drydocs_remediation.formats import DefinitionSet, FolderDefinition, JobDefinition
from drydocs_remediation.transform import canonical_variable_rename, propose_greenfield


def _command_only_set(command: str) -> DefinitionSet:
    return DefinitionSet(
        folders=[FolderDefinition(name="F", variables=[("%%SCRIPT_PATH", "/opt/dpl")])],
        jobs=[
            JobDefinition(
                name="CMDJOB",
                variables=[("%%ENV", "prod")],
                command_line=command,
            )
        ],
    )


def test_broken_command_line_is_a_divergence_not_a_pass() -> None:
    """The POC scenario head-on: a greenfield whose CMDLINE dangles must FAIL.

    Before the fix this reported equivalent=True with zero divergences —
    the report this test's docstring exists to make impossible again.
    """
    legacy = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    broken = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    # simulate the pre-A′ partial rename: greenfield folder renamed the
    # variable but the command line still references the old name
    broken.folders[0].variables[0] = ("%%LAUNCHER_SCRIPT_PATH", "/opt/dpl")
    report = prove_equivalence(legacy, broken)
    assert report.equivalent is False
    assert report.proven_jobs == 0
    assert any("command" in d for d in report.divergences)


def test_equal_command_lines_prove_a_command_only_job() -> None:
    legacy = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    same = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    report = prove_equivalence(legacy, same)
    assert report.equivalent is True
    assert report.proven_jobs == 1
    assert report.not_proven == []


def test_cosmetic_rename_still_proves_equivalent_on_the_command_surface() -> None:
    """The point of resolving: a COMPLETE rename changes definitions but not
    resolved behavior, and must pass — that is what 'behavior-preserving' means."""
    legacy = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    rule = canonical_variable_rename(
        {"SCRIPT_PATH": "LAUNCHER_SCRIPT_PATH"}, rule_id="R-demo", ratified=True
    )
    greenfield = propose_greenfield(legacy, [rule]).greenfield
    assert resolved_command(greenfield.folder_variables(), greenfield.jobs[0]) == (
        resolved_command(legacy.folder_variables(), legacy.jobs[0])
    )
    report = prove_equivalence(legacy, greenfield)
    assert report.equivalent is True, report.divergences


def test_nothing_comparable_is_not_proven_never_a_pass() -> None:
    """A job with no watch template and no command line cannot be proven — it
    is NAMED, and equivalent=True is refused."""
    bare = DefinitionSet(jobs=[JobDefinition(name="GHOSTJOB")])
    report = prove_equivalence(bare, DefinitionSet(jobs=[JobDefinition(name="GHOSTJOB")]))
    assert report.equivalent is False
    assert report.proven_jobs == 0
    assert report.not_proven and "GHOSTJOB" in report.not_proven[0]
    assert report.divergences == []


def test_one_side_losing_its_command_line_is_a_divergence_not_a_skip() -> None:
    legacy = _command_only_set("%%SCRIPT_PATH/run.sh -env %%ENV")
    lost = _command_only_set("")
    report = prove_equivalence(legacy, lost)
    assert report.equivalent is False
    assert any("command" in d for d in report.divergences)


def test_empty_folders_compare_vacuously_but_honestly() -> None:
    """Zero jobs on both sides: nothing diverged, nothing unproven — and
    proven_jobs says 0, so nobody can read it as 12/12."""
    report = prove_equivalence(DefinitionSet(), DefinitionSet())
    assert report.equivalent is True
    assert report.compared_jobs == 0
    assert report.proven_jobs == 0
