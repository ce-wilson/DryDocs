"""xml_io test class F + the transform-side defect A′ regression.

The POC's finding, as a permanent guard: a ratified rename that rewrites only
the fields the shipped ``canonical_variable_rename`` touched (job variables +
watch template) MUST be rejected by the post-conditions, with every surviving
site named — and the reference sweep must pass the same conditions with the
diff touching exactly the expected lines.
"""

from __future__ import annotations

import pytest

from drydocs_remediation.formats import DefinitionSet, FolderDefinition, JobDefinition
from drydocs_remediation.transform import canonical_variable_rename, propose_greenfield
from drydocs_remediation.xml_io import (
    EditScript,
    Locator,
    SelfCheckFailedError,
    load_document,
    locate,
    render,
    self_check,
    write,
)
from tests.unit.fixtures_controlm_xml import F3_RESIDUE

RENAME = ("SCRIPT_PATH", "LAUNCHER_SCRIPT_PATH")


# --------------------------------------------------------------------------- #
# F1: the OLD executor's shape is rejected (this is the red-first regression)
# --------------------------------------------------------------------------- #


def test_field_list_rename_is_rejected_with_every_surviving_site_named(tmp_path) -> None:
    """Rewrite ONLY what the pre-fix rename rewrote — the job-level VARIABLE
    definition — and declare the rename. The post-conditions must refuse, and
    the refusal must enumerate the CMDLINE, POSTCMD, DESCRIPTION, folder-scope,
    sub-folder-scope and residue (QUANTITATIVE/CONTROL/DOACTION/DOMAIL/CAPTURE)
    survivors the old code silently left dangling."""
    doc = load_document(F3_RESIDUE)
    script = EditScript(doc)
    script.declare_rename(*RENAME)
    folder_var = locate(doc, Locator(folder="PRXYZ3C", element="VARIABLE", name="%%SCRIPT_PATH"))
    # the old executor renamed the JOB-level declaration; F3 declares
    # %%SCRIPT_PATH at FOLDER scope, which the old executor never touched —
    # rewrite the folder one here to make the partial rewrite as generous as
    # possible: even WITH the definition site fixed, references still dangle.
    script.set_attribute(folder_var, "NAME", "%%LAUNCHER_SCRIPT_PATH", change_id="chg-old-style")

    emitted = render(doc, script.compile())
    report = self_check(doc, script, emitted)
    assert not report.ok
    dangling = [v for v in report.violations if v.startswith("no-dangling-reference")]
    # one per surviving %%SCRIPT_PATH token: DESCRIPTION, CMDLINE, POSTCMD,
    # QUANTITATIVE NAME, DOACTION WHAT, DOMAIL SUBJECT, sub-folder VARIABLE
    # value, sub-folder JOB CMDLINE
    assert len(dangling) >= 7, f"expected the survivors enumerated, got: {dangling}"
    conservation = [v for v in report.violations if v.startswith("reference-conservation")]
    assert conservation, "under-rewriting must also fail the conservation law"

    target = tmp_path / "updated.xml"
    with pytest.raises(SelfCheckFailedError):
        write(doc, script, target)
    assert not target.exists()


# --------------------------------------------------------------------------- #
# F2: the reference sweep passes, touching exactly the expected lines
# --------------------------------------------------------------------------- #


def test_reference_sweep_rewrites_every_surface_and_passes(tmp_path) -> None:
    doc = load_document(F3_RESIDUE)
    folder = locate(doc, Locator(folder="PRXYZ3C"))
    script = EditScript(doc)
    effects = script.replace_reference_tokens(folder, *RENAME, change_id="chg-1")

    # every surface enumerated for the change doc: folder VARIABLE definition,
    # job DESCRIPTION/CMDLINE/POSTCMD, QUANTITATIVE, CONTROL? (no - CTL-%%ENV),
    # DOACTION WHAT, DOMAIL SUBJECT, sub-folder VARIABLE value, nested CMDLINE
    touched = {(e.path.rsplit("/", 1)[-1], e.detail) for e in effects}
    assert len(effects) >= 9, f"sweep must enumerate every site: {sorted(touched)}"

    target = tmp_path / "updated.xml"
    report = write(doc, script, target)
    assert report.ok
    out = target.read_bytes()
    assert b"%%SCRIPT_PATH" not in out.replace(
        b"%%LAUNCHER_SCRIPT_PATH", b""
    ), "no dangling %%SCRIPT_PATH anywhere, residue included"
    # conservation: every original token became the new name
    assert out.count(b"%%LAUNCHER_SCRIPT_PATH") == F3_RESIDUE.count(b"%%SCRIPT_PATH")
    # the diff touches only lines that carried the token
    for lineno in report.changed_line_numbers:
        line = F3_RESIDUE.split(b"\n")[lineno - 1]
        assert b"%%SCRIPT_PATH" in line, f"line {lineno} changed without carrying the token"


def test_sweep_respects_the_name_boundary() -> None:
    """%%ENV must not rewrite inside %%ENV_SUFFIX-style longer names — the
    boundary rule proven in transform._rename_in_text, now at the byte layer."""
    src = F3_RESIDUE.replace(b'NAME="%%ENV" VALUE="prod"', b'NAME="%%ENV" VALUE="prod"')
    doc = load_document(src)
    folder = locate(doc, Locator(folder="PRXYZ3C"))
    script = EditScript(doc)
    script.replace_reference_tokens(folder, "ENV", "ENVIRONMENT", change_id="chg-1")
    out = render(doc, script.compile())
    assert b"%%ENVIRONMENT" in out
    # CAPTURE PATTERN="rows=%%ENV" carries the token; CTL-%%ENV too
    assert b"CTL-%%ENVIRONMENT" in out
    assert b"%%ENVIRONMENTIRONMENT" not in out


def test_sweep_is_scoped_to_the_subtree() -> None:
    """A rename scoped to one job leaves the same token elsewhere alone —
    scope is the approved change's blast radius, not the whole file."""
    doc = load_document(F3_RESIDUE)
    nested_job = locate(doc, Locator(folder="PRXYZ3C", subfolder_path="NESTED", job="PRXYZ3C101"))
    script = EditScript(doc)
    script.replace_reference_tokens(nested_job, *RENAME, change_id="chg-1")
    emitted = render(doc, script.compile())
    # the nested job's CMDLINE is rewritten...
    assert b'CMDLINE="%%LAUNCHER_SCRIPT_PATH/clean.sh"' in emitted
    # ...but the folder-level definition and the first job's surfaces are not
    # (and therefore the post-conditions REFUSE this partial state, correctly:
    # a scoped rename of a folder-scoped variable is not behavior-preserving)
    report = self_check(doc, script, emitted)
    assert not report.ok


# --------------------------------------------------------------------------- #
# The transform-side (model) rename is now surface-complete
# --------------------------------------------------------------------------- #


def _legacy_set() -> DefinitionSet:
    return DefinitionSet(
        folders=[
            FolderDefinition(
                name="F",
                variables=[("%%SCRIPT_PATH", "/opt/dpl")],
                description="folder uses %%SCRIPT_PATH",
            )
        ],
        jobs=[
            JobDefinition(
                name="CMDJOB",
                variables=[("%%ENV", "prod")],
                command_line="%%SCRIPT_PATH/run.sh -env %%ENV",
                post_command="cat %%SCRIPT_PATH/out.tok",
                description="uses %%SCRIPT_PATH",
                scope_chain=[
                    ("FOLDER", "F", [("%%SCRIPT_PATH", "/opt/dpl")]),
                    ("JOB", "CMDJOB", [("%%ENV", "prod")]),
                ],
            )
        ],
    )


def test_model_rename_covers_every_surface_and_scope() -> None:
    """The POC repro, inverted: every surface the 2026-08-12 session found
    stale must now carry the new name."""
    rule = canonical_variable_rename(
        {"SCRIPT_PATH": "LAUNCHER_SCRIPT_PATH"}, rule_id="R-demo", ratified=True
    )
    greenfield = propose_greenfield(_legacy_set(), [rule]).greenfield
    job = greenfield.jobs[0]
    folder = greenfield.folders[0]
    assert folder.variables == [("%%LAUNCHER_SCRIPT_PATH", "/opt/dpl")]
    assert folder.description == "folder uses %%LAUNCHER_SCRIPT_PATH"
    assert job.command_line == "%%LAUNCHER_SCRIPT_PATH/run.sh -env %%ENV"
    assert job.post_command == "cat %%LAUNCHER_SCRIPT_PATH/out.tok"
    assert job.description == "uses %%LAUNCHER_SCRIPT_PATH"
    assert job.scope_chain[0] == ("FOLDER", "F", [("%%LAUNCHER_SCRIPT_PATH", "/opt/dpl")])
    assert "%%SCRIPT_PATH" not in repr(greenfield), "no stale token anywhere in the model"


def test_model_rename_is_idempotent() -> None:
    rule = canonical_variable_rename(
        {"SCRIPT_PATH": "LAUNCHER_SCRIPT_PATH"}, rule_id="R-demo", ratified=True
    )
    once = propose_greenfield(_legacy_set(), [rule]).greenfield
    twice = propose_greenfield(once, [rule]).greenfield
    assert once == twice


def test_model_rename_conflict_in_folder_scope_raises() -> None:
    """The conflict guard now covers folder scope too — renaming onto a name
    already defined there is Tier-2 judgment."""
    definitions = DefinitionSet(
        folders=[
            FolderDefinition(
                name="F",
                variables=[("%%OLD", "a"), ("%%NEW", "b")],
            )
        ],
    )
    rule = canonical_variable_rename({"OLD": "NEW"}, rule_id="R-x", ratified=True)
    with pytest.raises(ValueError, match="folder 'F'"):
        propose_greenfield(definitions, [rule])
