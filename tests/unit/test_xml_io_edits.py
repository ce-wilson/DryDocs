"""xml_io test classes C-E, G-J: edits are minimal-diff, the self-check is
adversarial, re-runs are idempotent, refusals are loud, deps are stdlib-only.

The self-check tests (class E) are each verified to FAIL without the guard —
an injected extra edit and a suppressed intended effect must both abort, or
rule 4 is decoration.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from drydocs_remediation.xml_io import (
    EditScript,
    Effect,
    Locator,
    LocatorNotFoundError,
    NoTemplateSiblingError,
    SelfCheckFailedError,
    XmlIoError,
    load_document,
    locate,
    render,
    self_check,
    structural_diff,
    write,
)
from tests.unit.fixtures_controlm_xml import (
    F2_STYLE,
    F3_RESIDUE,
    F5_PROLOG,
    ROUND_TRIP_FIXTURES,
)


def _lines_changed(before: bytes, after: bytes) -> list[tuple[bytes, bytes]]:
    """(before_line, after_line) pairs that differ, for style assertions."""
    b, a = before.split(b"\n"), after.split(b"\n")
    assert len(b) == len(a), "line count changed"
    return [(x, y) for x, y in zip(b, a, strict=True) if x != y]


# --------------------------------------------------------------------------- #
# C. Per-edit-kind minimal diff
# --------------------------------------------------------------------------- #


def test_set_attribute_touches_exactly_one_line() -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "%%SCRIPT_PATH/run.sh -env %%ENV -v", change_id="chg-1")
    out = render(doc, script.compile())
    changed = _lines_changed(F3_RESIDUE, out)
    assert len(changed) == 1
    assert changed[0][1].strip() == b'CMDLINE="%%SCRIPT_PATH/run.sh -env %%ENV -v"'


def test_set_attribute_on_wrapped_tag_preserves_wrapping() -> None:
    """The load-bearing style case: editing one attribute of a multi-line tag
    must leave every other line of that tag byte-identical."""
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B001"))
    script = EditScript(doc)
    script.set_attribute(job, "NODEID", "host-xyz-99", change_id="chg-1")
    out = render(doc, script.compile())
    changed = _lines_changed(F2_STYLE, out)
    assert len(changed) == 1
    assert b"host-xyz-99" in changed[0][1]
    # the wrapped RUN_AS line with its tab indent and single quotes survives
    assert b"\t RUN_AS='svc.xyz'" in out


def test_add_attribute_clones_the_separator_style() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B002"))
    script = EditScript(doc)
    script.add_attribute(job, "APPLICATION", "XYZ", change_id="chg-1")
    out = render(doc, script.compile())
    assert (
        b'<JOB JOBNAME="PRXYZ2B002" TASKTYPE="Command" CMDLINE="a.sh" APPLICATION="XYZ" />' in out
    )


def test_remove_attribute_takes_its_separator_with_it() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B002"))
    script = EditScript(doc)
    script.remove_attribute(job, "CMDLINE", change_id="chg-1")
    out = render(doc, script.compile())
    assert b'<JOB JOBNAME="PRXYZ2B002" TASKTYPE="Command" />' in out


def test_insert_element_clones_sibling_style() -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    sibling = locate(
        doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001", element="VARIABLE", name="%%ENV")
    )
    script = EditScript(doc)
    script.insert_element(
        job,
        "VARIABLE",
        [("NAME", "%%REGION"), ("VALUE", "us-east")],
        after=sibling,
        change_id="chg-1",
    )
    out = render(doc, script.compile())
    expected_line = (
        b'      <VARIABLE NAME="%%ENV" VALUE="prod"/>\n'
        b'      <VARIABLE NAME="%%REGION" VALUE="us-east"/>'
    )
    assert expected_line in out, "inserted line must match its sibling's indent and empty-tag form"


def test_delete_element_leaves_no_blank_line() -> None:
    doc = load_document(F3_RESIDUE)
    var = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001", element="VARIABLE", name="%%ENV"))
    script = EditScript(doc)
    script.delete_element(var, change_id="chg-1")
    out = render(doc, script.compile())
    assert b'%%ENV" VALUE="prod"' not in out
    assert b"\n\n" not in out.replace(b"\r\n", b"\n"), "deletion left a blank line"


def test_residue_untouched_by_edits_elsewhere() -> None:
    """An edit in one job leaves every unmodeled element byte-identical."""
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "changed.sh", change_id="chg-1")
    out = render(doc, script.compile())
    for chunk in (
        b'<INCOND NAME="PRXYZ3C000-OK" ODATE="ODAT" AND_OR="AND"/>',
        b'<RULE_BASED_CALENDARS NAME="WORKDAYS" DAYS="ALL" DAYS_AND_OR="OR"/>',
        b'<DOMAIL DEST="ops-dl" SUBJECT="failed under %%SCRIPT_PATH"/>',
    ):
        assert chunk in out


# --------------------------------------------------------------------------- #
# D. Escaping
# --------------------------------------------------------------------------- #


def test_escaping_is_minimal_and_quote_aware() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", 'run.sh --sql="a < b & c > d"', change_id="chg-1")
    out = render(doc, script.compile())
    assert (
        b'CMDLINE="run.sh --sql=&quot;a &lt; b &amp; c > d&quot;"' in out
    ), "must escape & < and the delimiter quote; must NOT escape >"


def test_single_quoted_attribute_stays_single_quoted() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B001"))
    script = EditScript(doc)
    script.set_attribute(job, "RUN_AS", "svc.other", change_id="chg-1")
    out = render(doc, script.compile())
    assert b"RUN_AS='svc.other'" in out


def test_newline_in_value_becomes_numeric_ref() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B002"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "a\nb\tc", change_id="chg-1")
    out = render(doc, script.compile())
    assert b'CMDLINE="a&#10;b&#9;c"' in out


# --------------------------------------------------------------------------- #
# E. Self-check — each case fails without the guard
# --------------------------------------------------------------------------- #


def test_self_check_passes_on_an_honest_edit(tmp_path: Path) -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "new.sh", change_id="chg-1")
    target = tmp_path / "updated.xml"
    report = write(doc, script, target)
    assert report.ok
    assert len(report.changed_line_numbers) == 1
    assert target.read_bytes() == render(doc, script.compile())


def test_self_check_catches_an_unexpected_edit() -> None:
    """An edit that produced effects the intended list does not carry -> abort."""
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "new.sh", change_id="chg-1")
    script.intended_effects  # noqa: B018 - documents that the list is a copy
    script._intended.clear()  # suppress the intent: the edit is now smuggled
    emitted = render(doc, script.compile())
    report = self_check(doc, script, emitted)
    assert not report.ok
    assert [e.kind for e in report.unexpected] == ["attr-set"]


def test_self_check_catches_a_missing_intended_effect() -> None:
    """An intended effect whose edit never landed -> abort, named."""
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script._intended.append(Effect("attr-set", job.path, "CMDLINE", old="x", new="y"))
    report = self_check(doc, script, render(doc, script.compile()))
    assert not report.ok
    assert [e.detail for e in report.missing] == ["CMDLINE"]


def test_write_aborts_and_leaves_no_file(tmp_path: Path) -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "new.sh", change_id="chg-1")
    script._intended.clear()
    target = tmp_path / "updated.xml"
    with pytest.raises(SelfCheckFailedError):
        write(doc, script, target)
    assert not target.exists(), "a failed self-check must write nothing"
    assert not target.with_suffix(".xml.selfcheck-tmp").exists()


def test_tag_corruption_cannot_pass_the_self_check() -> None:
    """A renamed tag aborts by one of two routes, both closed: an aligned pair
    (the root) raises tag-rename immediately; a child-level rename reads as
    delete+insert, which no intended list carries -> unexpected effects."""
    src = ROUND_TRIP_FIXTURES["F1_minimal"]
    before = load_document(src)

    # route 1: root rename -> hard error from the aligned-pair check
    with pytest.raises(SelfCheckFailedError, match="tag-rename"):
        structural_diff(before, load_document(src.replace(b"DEFTABLE>", b"DEFTABLES>")))

    # route 2: child rename -> delete+insert that self_check rejects as unexpected
    after_bytes = src.replace(b"<VARIABLE ", b"<WARIABLE ")
    report = self_check(before, EditScript(before), after_bytes)
    assert not report.ok
    assert {e.kind for e in report.unexpected} == {"element-delete", "element-insert"}


# --------------------------------------------------------------------------- #
# G. Idempotence
# --------------------------------------------------------------------------- #


def test_reapplying_an_applied_change_set_is_satisfied_not_missing(tmp_path: Path) -> None:
    """Run an approved change twice: second run produces zero edits, zero
    missing effects, and byte-identical output — the already-at-target trap."""
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "new.sh", change_id="chg-1")
    first = render(doc, script.compile())

    doc2 = load_document(first)
    job2 = locate(doc2, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script2 = EditScript(doc2)
    effect = script2.set_attribute(job2, "CMDLINE", "new.sh", change_id="chg-1")
    assert script2.satisfied == [effect]
    assert script2.compile() == []
    second = render(doc2, script2.compile())
    assert second == first
    report = self_check(doc2, script2, second)
    assert report.ok and not report.missing


# --------------------------------------------------------------------------- #
# H. Refusals
# --------------------------------------------------------------------------- #


def test_overlapping_edits_refused() -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "a.sh", change_id="chg-1")
    script.set_attribute(job, "CMDLINE", "b.sh", change_id="chg-2")
    with pytest.raises(XmlIoError, match="overlapping"):
        script.compile()


def test_change_id_is_required_by_signature() -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    with pytest.raises(TypeError):
        EditScript(doc).set_attribute(job, "CMDLINE", "x.sh")  # type: ignore[call-arg]


def test_insert_with_no_template_is_refused() -> None:
    doc = load_document(ROUND_TRIP_FIXTURES["F1_minimal"])
    job = locate(doc, Locator(folder="PRXYZ1A", job="PRXYZ1A001"))
    with pytest.raises(XmlIoError, match="self-closed|clone style"):
        EditScript(doc).insert_element(job, "INCOND", [("NAME", "X-OK")], change_id="chg-1")


def test_set_on_a_missing_attribute_is_a_loud_miss() -> None:
    doc = load_document(F3_RESIDUE)
    job = locate(doc, Locator(folder="PRXYZ3C", job="PRXYZ3C001"))
    with pytest.raises(LocatorNotFoundError, match="add_attribute"):
        EditScript(doc).set_attribute(job, "GHOST", "x", change_id="chg-1")


def test_no_template_sibling_error_type_exists_for_paired_parents() -> None:
    doc = load_document(F2_STYLE)
    job = locate(doc, Locator(folder="PRXYZ2B", job="PRXYZ2B003"))  # paired <JOB></JOB>
    with pytest.raises(NoTemplateSiblingError):
        EditScript(doc).insert_element(job, "INCOND", [("NAME", "X-OK")], change_id="chg-1")


# --------------------------------------------------------------------------- #
# I. Portability
# --------------------------------------------------------------------------- #


def test_crlf_document_edits_stay_crlf(tmp_path: Path) -> None:
    doc = load_document(F5_PROLOG)
    job = locate(doc, Locator(folder="PRXYZ5E", job="PRXYZ5E001"))
    script = EditScript(doc)
    script.set_attribute(job, "CMDLINE", "changed.sh", change_id="chg-1")
    target = tmp_path / "crlf.xml"
    report = write(doc, script, target)
    assert report.ok
    out = target.read_bytes()
    assert out.startswith(b"\xef\xbb\xbf"), "BOM survives"
    assert b"changed.sh" in out
    assert out.count(b"\r\n") == F5_PROLOG.count(b"\r\n"), "newline style untouched"


# --------------------------------------------------------------------------- #
# J. Dependency guard — the splicer stays stdlib + core + formats
# --------------------------------------------------------------------------- #


def test_xml_io_imports_are_stdlib_core_and_formats_only() -> None:
    """lxml is the VALIDATOR's dependency, never the emitter's; lineage is a
    forbidden component import. Guarded here so 'simplifying' the splicer into
    a serializer cannot land quietly."""
    module_path = Path(__file__).resolve().parents[2] / "drydocs_remediation" / "xml_io.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    allowed_third_party = {"drydocs_core"}
    stdlib = set(sys.stdlib_module_names)
    offenders = {r for r in roots if r not in stdlib and r not in allowed_third_party}
    assert not offenders, f"xml_io imports outside stdlib+core: {sorted(offenders)}"
    assert "lxml" not in roots and "drydocs_lineage" not in roots
