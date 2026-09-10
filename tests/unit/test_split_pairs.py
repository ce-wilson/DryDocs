"""PORT12 — a commit split across two dispositions ports as a broken half.

The defect, in the instance that produced this module: G130 (`01761011`) added
``constraints_detail`` to ``drydocs_core/neo4j_client.py`` and a call to it in
``drydocs/cli_schema.py`` in one commit. The caller's path is canonical-producer and
crosses wholesale; the method's path falls to the manifest default, which is
evaluate-on-collision for a file both sides authored, so it waited on a hand-merge.
The consumer got the caller, the sixteen lines did not arrive, and ``drydocs
bootstrap`` raised ``AttributeError`` ten days later — an uncalled missing method
raises nothing until it is called.

WHAT IS PINNED HERE, in the order it matters.

THE POSITIVE CONTROL FIRST, because a detector for a defect shape that cannot find
the instance the shape was drawn from has not been shown to work. It is not the last
test in the file for the same reason.

Then the two arms of the manifest DEFAULT, which is where the precision lives: a file
the range CREATED reaches a consumer that lacks it as a clean-add and carries every
definition in it; only a file that already existed can take the evaluate arm.
Conflating them is what a first pass does, and it reported 404 pairs.

Then attribution: a name defined in two places cannot be attributed to either, and a
name the using file defines itself resolves locally. Both are about whether the
detector's CLAIM — "this use needs THAT definition" — is honest.

And the three outcomes, because a range that could not be compared is not a range
with no findings (ADR 0021).
"""

from __future__ import annotations

import subprocess

import pytest

from drydocs.port.split_pairs import (
    CROSSES_UNATTENDED,
    NEEDS_A_HAND,
    NEITHER,
    check_range,
    defined_names,
    referenced_names,
    split_pairs,
    tree_definitions,
)

#: The commit the whole module exists for.
G130 = "01761011"


def _git_has(rev: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", f"{rev}^{{commit}}"], capture_output=True
        ).returncode
        == 0
    )


# --- the positive control -----------------------------------------------------


@pytest.mark.skipif(not _git_has(G130), reason=f"{G130} not in this clone (shallow or fresh)")
def test_the_detector_finds_g130_the_case_it_was_drawn_from() -> None:
    """PORT12 acceptance (d). The item is not done without this.

    Run over the single commit, the check must name ``constraints_detail`` as defined
    in the client and used from ``cli_schema.py``. Everything else in this file tests
    the detector's judgment; this tests that it has any.
    """
    outcome = check_range(f"{G130}^", G130)
    assert not outcome.is_not_checked, outcome.render()
    assert not outcome.is_clean, "the detector reports the G130 range as clean"

    hits = {
        (f.name, f.defined_in, f.used_in)
        for f in outcome.findings
        if f.name == "constraints_detail"
    }
    assert (
        "constraints_detail",
        "drydocs_core/neo4j_client.py",
        "drydocs/cli_schema.py",
    ) in hits, (
        "the detector does not find the split pair it was built from: "
        f"{sorted(f.render() for f in outcome.findings)}"
    )


# --- the classes come from the manifest, not from a second reading ------------


def test_the_three_classes_are_disjoint_and_name_the_dispositions() -> None:
    assert not (CROSSES_UNATTENDED & NEEDS_A_HAND)
    assert not (CROSSES_UNATTENDED & NEITHER)
    assert not (NEEDS_A_HAND & NEITHER)
    # derived is regenerated on the consumer's own sources (J43), so nothing defined
    # in one travels as text; never-port does not cross at all.
    assert NEITHER == {"derived", "never-port"}
    assert "canonical-producer" in CROSSES_UNATTENDED
    assert {"evaluate", "per-entry", "canonical-company"} <= NEEDS_A_HAND


# --- what counts as a definition ---------------------------------------------


def test_a_definition_is_module_or_class_scope_never_a_local() -> None:
    """The first pass used ast.walk and reported three test locals as definitions.

    A local cannot be half of a split pair: no other module can reach it by name,
    so a hand-merge that dropped it breaks nothing anywhere else.
    """
    source = (
        "TOP = 1\n"
        "class C:\n"
        "    FIELD: int = 2\n"
        "    def method(self):\n"
        "        local_name = 3\n"
        "        def nested():\n"
        "            pass\n"
        "        return local_name\n"
        "def fn():\n"
        "    another_local = 4\n"
        "    return another_local\n"
    )
    found = defined_names(source)
    assert {"TOP", "C", "FIELD", "method", "fn"} <= found
    assert "local_name" not in found
    assert "another_local" not in found
    assert "nested" not in found, "a function inside a method is reachable from nowhere"


def test_a_module_level_conditional_still_binds_at_module_scope() -> None:
    source = "import typing\nif typing.TYPE_CHECKING:\n    Alias = int\ntry:\n    X = 1\nexcept ImportError:\n    X = 2\n"
    assert {"Alias", "X"} <= defined_names(source)


def test_a_reference_includes_attribute_access_not_only_imports() -> None:
    """``cli.constraints_detail()`` is an attribute, not an import.

    An import-only reading would have missed the case this module exists for, so the
    breadth is deliberate — and it is what makes the attribution filters necessary.
    """
    refs = referenced_names("def f(cli):\n    return cli.constraints_detail()\n")
    assert "constraints_detail" in refs
    assert "cli" in refs


def test_neither_side_reads_prose() -> None:
    """J66. A name in a comment defines nothing and references nothing."""
    commented = "# def constraints_detail(self): ...\n# x.constraints_detail()\nY = 1\n"
    assert "constraints_detail" not in defined_names(commented)
    assert "constraints_detail" not in referenced_names(commented)


def test_unparseable_source_yields_nothing_rather_than_raising() -> None:
    assert defined_names("def (:\n") == set()
    assert referenced_names("def (:\n") == set()


# --- the two arms of the manifest DEFAULT ------------------------------------


BEFORE_EXISTING = {
    "core/thing.py": "def old():\n    pass\n",
    "cli/run.py": "def main():\n    old()\n",
}
AFTER_EXISTING = {
    "core/thing.py": "def old():\n    pass\n\n\ndef brand_new():\n    pass\n",
    "cli/run.py": "def main():\n    old()\n    brand_new()\n",
}
DISPOSITIONS = {"core/thing.py": "default_ok", "cli/run.py": "canonical-producer"}


def test_a_preexisting_default_file_takes_the_evaluate_arm_and_is_reported() -> None:
    """The G130 shape in miniature: the file was already on both sides."""
    pairs, ambiguous, clean_added = split_pairs(BEFORE_EXISTING, AFTER_EXISTING, DISPOSITIONS)
    assert [p.name for p in pairs] == ["brand_new"]
    assert pairs[0].defined_in == "core/thing.py"
    assert pairs[0].used_in == "cli/run.py"
    assert not ambiguous and not clean_added


def test_a_file_the_range_created_crosses_whole_and_is_not_a_pair() -> None:
    """The other arm, and the one that cut a 133-finding sweep down to its real cases.

    A path that falls to the manifest default is clean-add when the consumer lacks it.
    A file this range created almost certainly lands there, arriving whole with every
    definition in it — a new file crossing normally, not a split. It is COUNTED rather
    than dropped, because a silent drop is how a detector starts under-reporting.
    """
    before = {"cli/run.py": "def main():\n    pass\n"}  # core/thing.py absent at base
    pairs, _ambiguous, clean_added = split_pairs(before, AFTER_EXISTING, DISPOSITIONS)
    assert pairs == []
    assert clean_added == ["core/thing.py"]


def test_an_explicit_hand_merge_row_needs_a_hand_however_new_the_file() -> None:
    """A per-entry row is a RULING, not an inference from the consumer's tree.

    The file is absent at the base here, so under the DEFAULT it would have been a
    clean-add and reported nothing. Under an explicit per-entry row every name in it
    is a definition someone must carry entry by entry — `old` as much as `brand_new`,
    because to this consumer both are new — and both are reported.
    """
    before = {"cli/run.py": "def main():\n    pass\n"}
    dispositions = {"core/thing.py": "per-entry", "cli/run.py": "canonical-producer"}
    pairs, _ambiguous, clean_added = split_pairs(before, AFTER_EXISTING, dispositions)
    assert sorted(p.name for p in pairs) == ["brand_new", "old"]
    assert all(p.defined_in == "core/thing.py" for p in pairs)
    assert clean_added == [], "an explicit row is never reclassified as a clean-add"


# --- attribution --------------------------------------------------------------


def test_a_name_defined_in_two_modules_is_ambiguous_not_a_finding() -> None:
    """``row.description`` matched a ``description`` field defined elsewhere, and the
    first sweep returned 404 pairs on that alone. With two candidate definitions the
    claim "this use needs THAT definition" is a guess, so it is counted, not asserted.
    """
    in_tree = {"brand_new": {"core/thing.py", "core/other.py"}}
    pairs, ambiguous, _ = split_pairs(
        BEFORE_EXISTING, AFTER_EXISTING, DISPOSITIONS, definitions_in_tree=in_tree
    )
    assert pairs == []
    assert ambiguous == ["brand_new"]


def test_one_definition_in_the_tree_is_attributable() -> None:
    in_tree = {"brand_new": {"core/thing.py"}}
    pairs, ambiguous, _ = split_pairs(
        BEFORE_EXISTING, AFTER_EXISTING, DISPOSITIONS, definitions_in_tree=in_tree
    )
    assert [p.name for p in pairs] == ["brand_new"]
    assert ambiguous == []


def test_a_name_the_using_file_defines_itself_resolves_locally() -> None:
    after = {
        "core/thing.py": "def old():\n    pass\n\n\ndef brand_new():\n    pass\n",
        "cli/run.py": "def brand_new():\n    pass\n\n\ndef main():\n    brand_new()\n",
    }
    pairs, _ambiguous, _ = split_pairs(BEFORE_EXISTING, after, DISPOSITIONS)
    assert pairs == [], "the use resolves to the using file's own definition"


def test_a_definition_in_the_test_tree_is_not_a_definition_side() -> None:
    """No production module imports from ``tests/``, so a production reference can
    never resolve to a test-defined name. A fake client in a test defines
    ``constraints_detail`` too, and counting it duplicated a true finding."""
    before = {"tests/unit/test_x.py": "", "cli/run.py": "def main():\n    pass\n"}
    after = {
        "tests/unit/test_x.py": "class Fake:\n    def brand_new(self):\n        pass\n",
        "cli/run.py": "def main(o):\n    o.brand_new()\n",
    }
    pairs, _ambiguous, _ = split_pairs(
        before, after, {"tests/unit/test_x.py": "default_ok", "cli/run.py": "canonical-producer"}
    )
    assert pairs == []


def test_tree_definitions_is_the_attribution_denominator() -> None:
    files = {
        "core/a.py": "def shared():\n    pass\n",
        "core/b.py": "def shared():\n    pass\n",
        "core/c.py": "def only_here():\n    pass\n",
        "tests/unit/test_d.py": "def shared():\n    pass\n",
    }
    defs = tree_definitions(files)
    assert defs["shared"] == {"core/a.py", "core/b.py"}, "the test tree is excluded"
    assert defs["only_here"] == {"core/c.py"}


# --- three outcomes, and no silence ------------------------------------------


def test_an_unresolvable_revision_is_not_checked_never_clean() -> None:
    """ADR 0021. A range that could not be compared is not a range with no findings,
    and the reason names the revision so the reader knows what to fetch."""
    outcome = check_range("port-base-19990101", "HEAD")
    assert outcome.is_not_checked
    assert not outcome.is_clean
    assert "port-base-19990101" in (outcome.reason or "")
    assert outcome.render().startswith("NOT CHECKED")
    with pytest.raises(TypeError):
        bool(outcome)


def test_a_range_with_no_python_change_is_clean_over_a_named_subject() -> None:
    outcome = check_range("HEAD", "HEAD")
    assert outcome.is_clean
    assert outcome.size == 0
    assert "HEAD..HEAD" in (outcome.subject or "")


def test_it_reports_rather_than_gates() -> None:
    """PORT12 acceptance (c). A split commit is legitimate — the dispositions are
    right — so what it owes is a relay line, not a refusal. Nothing here raises on
    findings, and the type is what carries the three states to the caller."""
    pairs, _ambiguous, _ = split_pairs(BEFORE_EXISTING, AFTER_EXISTING, DISPOSITIONS)
    assert pairs and pairs[0].render()
    assert "defined in" in pairs[0].render() and "used from" in pairs[0].render()
