"""The shared source-reading helper, and the trap it exists to remove (J66).

THE POINT, restated because every guard that hit this wrote its own fix: a guard
that greps its own source tree for a forbidden pattern also matches the COMMENT
explaining why the pattern is forbidden. The duplication was never the expensive
part — the expensive part is that such a guard teaches people to stop writing
explanations, in a repo whose comments carry its rulings.

This file is itself the proof: it names ``os.environ`` and ``${VAR:-default}``
several times in prose, and nothing here fires on them.
"""

from __future__ import annotations

import ast
import inspect
import re
import tokenize
from pathlib import Path
from typing import Final

import pytest

from tests.source_scan import (
    ALL,
    ATTRIBUTE,
    KINDS,
    MISSING,
    NAME,
    NOT_CONSTANT,
    VacuousScanError,
    absent,
    call_sites,
    called_names,
    code_only,
    comment_lines,
    imported_modules,
    source_text,
    without_prose,
)

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests"


# ---------------------------------------------------------------------------
# code_only — the verb the G128 guards needed.
# ---------------------------------------------------------------------------
def test_a_comment_naming_the_forbidden_thing_is_removed() -> None:
    """The exact shape that broke G128: the explanation names what it forbids."""
    source = "# never read os.environ directly\nvalue = settings.data_root\n"
    assert "os.environ" in source
    assert "os.environ" not in code_only(source)
    assert "settings.data_root" in code_only(source).replace(" ", "")


def test_a_docstring_naming_the_forbidden_thing_is_removed() -> None:
    """A docstring IS a string literal, which is exactly why it goes.

    Every one of the three guards that hit this trap named the forbidden thing in
    its own docstring — that is not a coincidence, it is what a good docstring
    does.
    """
    source = '"""This function must never use ${VAR:-default} syntax."""\nx = 1\n'
    assert "${VAR:-default}" not in code_only(source)


def test_real_code_survives_including_operators_and_names() -> None:
    source = "import os\n\n\ndef f(a, b=2):\n    return os.path.join(a, str(b))\n"
    kept = code_only(source).replace(" ", "")
    for fragment in ("importos", "deff(a,b=2)", "os.path.join(a,str(b))"):
        assert fragment in kept


def test_a_string_literal_in_real_code_is_removed_too() -> None:
    """Deliberate, and worth stating: this strips VALUES as well as prose.

    A guard asking "is this string present as a literal" must NOT use this verb —
    it would see nothing. The verb answers "does the code DO this", which is a
    different question, and conflating the two is how a guard passes vacuously.
    """
    assert "secret" not in code_only('token = "secret"\n')


def test_the_output_is_for_matching_and_not_for_reparsing() -> None:
    """Tokens are joined by single spaces, so indentation is gone.

    The first version of this test used a one-line body and DID NOT RAISE --
    ``def f ( ) : return 1`` is valid Python. A two-statement body is the honest
    case: with the newlines flattened there is no way to end the first statement.
    Said out loud because a caller who re-parsed this output would get a syntax
    error and blame the wrong thing.
    """
    with pytest.raises(SyntaxError):
        ast.parse(code_only("def f():\n    x = 1\n    return x\n"))


def test_unparseable_source_raises_rather_than_returning_nothing() -> None:
    """A guard silently scanning an empty string is worse than one that fails."""
    import tokenize

    with pytest.raises((tokenize.TokenError, SyntaxError, IndentationError)):
        code_only("def f(:\n    'unclosed\n")


# ---------------------------------------------------------------------------
# imported_modules — the verb the G129 guard needed.
# ---------------------------------------------------------------------------
def test_a_module_named_only_in_prose_is_not_an_import() -> None:
    """The G129 failure, exactly: three modules NAMED the script in a docstring."""
    source = '"""Write it with scripts/set_env_var.py, never by hand."""\nimport json\n'
    assert imported_modules(source) == {"json"}


def test_both_import_forms_are_reported() -> None:
    source = "import a.b\nfrom c.d import e\nimport f as g\n"
    assert imported_modules(source) == {"a.b", "c.d", "f"}


def test_a_relative_import_yields_its_module_or_empty() -> None:
    """Honest over invented: this function has no package context to resolve a
    relative import against, so it reports what is written rather than guessing."""
    assert imported_modules("from . import x\n") == {""}
    assert imported_modules("from .base import y\n") == {"base"}


# ---------------------------------------------------------------------------
# called_names — the verb the G130 and I6 guards needed.
# ---------------------------------------------------------------------------
def test_a_call_named_in_a_comment_is_not_a_call() -> None:
    """The G130 failure: the docstring said `session` and `run(`."""
    source = '"""Pure -- it opens no session and never calls run()."""\nreturn compare(a, b)\n'
    assert called_names(source) == {"compare"}


def test_the_two_kinds_are_distinguished() -> None:
    """Load-bearing rather than tidy.

    A guard asserting a module never calls ``client.run`` must not fire on a
    local helper that happens to be named ``run`` — so the kinds are separate and
    the caller says which one it means.
    """
    source = "run(1)\nclient.run(2)\nother.thing()\n"
    assert called_names(source, kind=NAME) == {"run"}
    assert called_names(source, kind=ATTRIBUTE) == {"run", "thing"}
    assert called_names(source, kind=ALL) == {"run", "thing"}


def test_an_attribute_call_reports_its_final_attribute() -> None:
    """The receiver is a local at every real call site (`cli`, `out`, `dest`),
    so keying on it would make a guard miss the site it exists to catch."""
    assert called_names("a.b.c.execute()\n", kind=ATTRIBUTE) == {"execute"}


def test_an_unknown_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="kind must be one of"):
        called_names("x()\n", kind="attributes")
    assert set(KINDS) == {NAME, ATTRIBUTE, ALL}


# ---------------------------------------------------------------------------
# source_text — the thin path convenience.
# ---------------------------------------------------------------------------
def test_source_text_reads_utf8_and_resolves_against_a_root(tmp_path) -> None:
    """UTF-8 pinned in ONE place. Spelled at each call site it drifts, and the
    locale codec is cp1252 on the machines this runs on — the same defect I6
    found in the allocator, where an em dash crashed a subprocess read."""
    (tmp_path / "x.py").write_text("# em dash — here\nx = 1\n", encoding="utf-8", newline="\n")
    assert "—" in source_text("x.py", tmp_path)
    assert "—" in source_text(tmp_path / "x.py")


# ---------------------------------------------------------------------------
# (a) The migration is complete: no call site keeps a private copy.
# ---------------------------------------------------------------------------
def test_no_test_module_defines_its_own_python_source_stripper() -> None:
    """A helper that exists while the local copies stay is the same duplication
    one directory deeper.

    The Cypher stripper in test_vocabulary_endpoints.py is EXEMPT and named here
    rather than pattern-matched away: it shares the old name and strips a
    different grammar with regular expressions, which Python's tokenizer cannot
    do. Folding two unrelated things together because their names match is the
    mistake J66 clause (c) fences.
    """
    exempt = {"test_vocabulary_endpoints.py", "test_source_scan.py"}
    offenders: list[str] = []
    for path in sorted((TESTS / "unit").glob("*.py"), key=lambda p: p.as_posix()):
        if path.name in exempt:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {"_code_only", "code_only"}:
                offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, (
        f"private source strippers still defined at {offenders}. Import from "
        "tests.source_scan instead — a shared helper beside four local copies is "
        "not a shared helper."
    )


def test_the_cypher_stripper_is_still_there_and_is_still_a_different_thing() -> None:
    """Pin the exemption so a later sweep cannot quietly absorb it.

    If this ever fails because the function moved or was folded in, that is a
    DECISION to re-take, not a test to delete: the Cypher grammar is not Python's
    and a tokenizer cannot read it.
    """
    source = (TESTS / "unit" / "test_vocabulary_endpoints.py").read_text(encoding="utf-8")
    assert "def _code_only(text: str) -> str:" in source
    assert "Cypher with comments and string literals removed" in source


# ---------------------------------------------------------------------------
# (d) The location, confirmed at build time rather than asserted in prose.
# ---------------------------------------------------------------------------
def test_pytest_does_not_collect_the_helper_as_a_test() -> None:
    """Default ``python_files`` is ``test_*.py`` / ``*_test.py``; the module is
    named so it matches neither, the same shape as tests/env_drift.py."""
    name = "source_scan.py"
    assert not name.startswith("test_") and not name.endswith("_test.py")
    assert (TESTS / name).exists()


def test_both_suites_can_import_it() -> None:
    """The reason it sits at the tests ROOT and not under unit/.

    tests/env_drift.py is the precedent and conftest.py imports it as
    ``from tests import env_drift``; the same import works from either suite,
    which is what makes this the shared module rather than the unit suite's.
    """
    import importlib

    module = importlib.import_module("tests.source_scan")
    assert module.__file__ and module.__file__.endswith("source_scan.py")
    for verb in (code_only, without_prose, imported_modules, called_names, source_text, absent):
        assert inspect.getmodule(verb) is module


def test_the_helper_holds_the_verbs_it_has_callers_for() -> None:
    """Clause (b): nothing else goes in.

    A helper module that grows a verb nobody calls is how a shared helper becomes
    a private one again, so the surface is pinned rather than trusted. CORE2 added
    two entries and one exception type, and they are one idea rather than three:
    the stripper a LITERAL subject needs, the call shape that proves the right
    stripper was chosen, and the failure that shape raises.
    """
    import tests.source_scan as module

    # Against __all__, not against vars(): a module's namespace also holds what it
    # IMPORTS (Path, Final), so the first version of this test failed on its own
    # imports rather than on any new verb.
    assert set(module.__all__) == {
        "code_only",
        "without_prose",
        "imported_modules",
        "called_names",
        "call_sites",
        "comment_lines",
        "source_text",
        "absent",
        "return_annotation",
        "CallSite",
        "MISSING",
        "NOT_CONSTANT",
        "VacuousScanError",
    }
    sentinels = {"MISSING", "NOT_CONSTANT", "CallSite", "VacuousScanError"}
    for name in module.__all__:
        if name not in sentinels:
            assert callable(getattr(module, name))


# ---- call_sites: the fourth verb (J76) ------------------------------------------------


def test_call_sites_reports_keywords_with_constant_values_and_marks_the_rest() -> None:
    src = (
        "import subprocess\n"
        "flag = True\n"
        "subprocess.run(['git'], capture_output=True, text=True)\n"
        "run(['x'], text=flag, encoding='utf-8')\n"
        "other(text=True)\n"
    )
    sites = call_sites(src, ["run"])
    assert [s.lineno for s in sites] == [3, 4]
    assert sites[0].keywords == {"capture_output": True, "text": True}
    assert sites[0].constant("encoding") is MISSING
    assert sites[1].keywords["text"] is NOT_CONSTANT
    assert sites[1].constant("encoding") == "utf-8"


def test_a_call_named_only_in_a_comment_or_string_has_no_call_site() -> None:
    src = "# subprocess.run(text=True) is the pattern this forbids\nx = 'run(text=True)'\n"
    assert call_sites(src, ["run"]) == []


def test_call_sites_span_the_whole_call_so_a_marker_inside_it_is_findable() -> None:
    src = "run(\n    ['git'],\n    text=True,\n)\n"
    (site,) = call_sites(src, ["run"])
    assert (site.lineno, site.end_lineno) == (1, 4)


def test_comment_lines_reads_exactly_the_comments_by_line() -> None:
    src = "x = 1  # first\ny = 'not # a comment'\n# whole line\n"
    assert comment_lines(src) == {1: "# first", 3: "# whole line"}


# ---------------------------------------------------------------------------
# without_prose: the stripper a LITERAL subject needs (CORE2)
# ---------------------------------------------------------------------------
_WITH_PROSE = '''"""Module doc naming query_specs.py."""
import os


def f(items):
    """Doc naming DROP CONSTRAINT."""
    # comment naming query_specs.py
    path = "drydocs_api/query_specs.py"
    value = os.environ.get("X")
    return path, value, items[:-1]
'''


def test_a_literal_survives_the_stripper_that_a_literal_subject_needs() -> None:
    """The whole reason the verb exists. `code_only` removes this and the guard
    that was looking for it passes on nothing."""
    scanned = without_prose(_WITH_PROSE)
    assert 'path = "drydocs_api/query_specs.py"' in scanned
    assert "query_specs.py" not in code_only(_WITH_PROSE), (
        "if this ever stops being true, code_only changed and CORE2's premise "
        "with it -- re-derive the split rather than relaxing the test"
    )


def test_a_docstring_goes_with_the_comments_because_both_are_prose() -> None:
    """Docstrings are not data. A module whose docstring names every symbol it
    forbids is the house style, and a stripper that kept docstrings could not be
    used by the guards that need it."""
    scanned = without_prose(_WITH_PROSE)
    assert "Module doc" not in scanned
    assert "DROP CONSTRAINT" not in scanned
    assert "comment naming" not in scanned


def test_the_layout_is_the_original_so_a_dotted_name_survives_intact() -> None:
    """The second, quieter vacuity: `code_only` joins tokens with single spaces,
    so `os.environ` arrives as `os . environ` and a substring scan for the dotted
    form matches nothing at all. Prose is blanked IN PLACE here instead."""
    scanned = without_prose(_WITH_PROSE)
    assert "os.environ" in scanned
    assert "os . environ" in code_only(_WITH_PROSE)
    assert len(scanned.splitlines()) == len(
        _WITH_PROSE.splitlines()
    ), "line numbers are preserved on purpose: a result can be read next to the file"


def test_unparseable_source_raises_here_too() -> None:
    with pytest.raises((tokenize.TokenError, SyntaxError, IndentationError)):
        without_prose("def f(:\n")


# ---------------------------------------------------------------------------
# absent: the positive control is the point (CORE2 clauses (a) and (b))
# ---------------------------------------------------------------------------
def test_clause_b_a_literal_subject_with_code_only_fails_on_the_control() -> None:
    """THE CLAUSE, and the shape of all six real failures.

    The tree here DOES contain the subject, so without the control this call
    would report green while checking nothing -- which is exactly what the six
    vacuous guards did. The failure must be about the CONTROL, not about the
    tree: that is the difference between "your guard is broken" and "your code
    is broken", and only the first one is true.
    """
    tree = {"m.py": 'p = "drydocs_api/query_specs.py"\n'}
    with pytest.raises(VacuousScanError) as info:
        absent("query_specs.py", tree, positive_control='p = Path("query_specs.py")')
    message = str(info.value)
    assert "POSITIVE CONTROL FAILED" in message
    assert "code_only" in message, "the message names the stripper that ate the subject"
    assert "query_specs.py" in message, "and the subject itself"
    assert "without_prose" in message, "and what to reach for instead"

    # ... and the same call with the right stripper reports the REAL hit.
    with pytest.raises(AssertionError) as real:
        absent(
            "query_specs.py",
            tree,
            positive_control='p = Path("query_specs.py")',
            stripper=without_prose,
        )
    assert "POSITIVE CONTROL" not in str(real.value)
    assert "m.py" in str(real.value)


def test_a_control_and_a_tree_go_through_one_pipeline_not_two() -> None:
    """`normalize` applies to both or the probe measures nothing: a control that
    skipped the caller's post-processing would prove the pattern matches text no
    scan ever produces."""
    absent(
        "os.environ",
        {"m.py": "value = 1\n"},
        positive_control="v = os.environ.get('X')",
        normalize=lambda text: text.replace(" ", ""),
    )
    with pytest.raises(VacuousScanError):
        # The same control, without the normalization: code_only spaces the dots.
        absent("os.environ", {"m.py": "value = 1\n"}, positive_control="v = os.environ.get('X')")


def test_a_regular_expression_is_searched_and_a_string_is_a_substring() -> None:
    pattern = re.compile(r"\$\{[^}]*:-")
    absent(
        pattern,
        {"m.py": "tail = items[:-1]\n"},
        positive_control='REF = "${DRYDOCS_LOGDIR:-/tmp}"',
        stripper=without_prose,
    )
    with pytest.raises(AssertionError):
        absent(
            pattern,
            {"m.py": 'REF = "${X:-y}"\n'},
            positive_control='REF = "${DRYDOCS_LOGDIR:-/tmp}"',
            stripper=without_prose,
        )


def test_scanning_no_files_is_refused_rather_than_passed() -> None:
    """The other way an absence guard reports green while checking nothing: a
    glob that matched nothing, a list that emptied out under a refactor."""
    with pytest.raises(VacuousScanError) as info:
        absent("anything", {}, positive_control="anything")
    assert "no sources" in str(info.value)


def test_paths_are_read_through_source_text_and_the_label_is_the_path(tmp_path) -> None:
    (tmp_path / "a.py").write_text('x = "forbidden"\n', encoding="utf-8")
    with pytest.raises(AssertionError) as info:
        absent(
            "forbidden",
            ["a.py"],
            root=tmp_path,
            positive_control='x = "forbidden"',
            stripper=without_prose,
            because="the reason reaches the reader",
        )
    assert "a.py" in str(info.value)
    assert "the reason reaches the reader" in str(info.value)


# ---------------------------------------------------------------------------
# Clause (d): the guard over the guards
# ---------------------------------------------------------------------------
#: Files whose absence scans over a stripper are NOT guards over the tree and so
#: cannot go through `absent`. One entry, with its reason, because a list that
#: grows quietly is how a swept tree un-sweeps itself.
_NOT_GUARDS: Final = {
    "test_source_scan.py": (
        "the strippers' own unit tests -- they assert what code_only and "
        "without_prose REMOVE, which is the one place an absence scan over a "
        "stripper is the subject rather than the instrument"
    ),
}

_STRIPPER_NAMES: Final = ("code_only", "without_prose")
#: String methods that pass their receiver's origin through. A guard writing
#: `code_only(s).upper()` is still scanning stripper output.
_PASSTHROUGH: Final = ("replace", "upper", "lower", "casefold", "strip")


def _derives_from_stripper(node: ast.AST, bound: set[str]) -> bool:
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in _STRIPPER_NAMES:
            return True
        if isinstance(func, ast.Attribute) and func.attr in _PASSTHROUGH:
            return _derives_from_stripper(func.value, bound)
        return False
    if isinstance(node, ast.Name):
        return node.id in bound
    if isinstance(node, ast.Attribute) and node.attr in _PASSTHROUGH:
        return _derives_from_stripper(node.value, bound)
    return False


def _absence_scans_outside_the_helper(source: str) -> list[int]:
    """Line numbers of `<pattern> not in <stripper output>` in ``source``.

    READS THE CODE, never the text (J66) -- which is not a formality here: this
    guard's own explanation names both strippers, and a substring version of it
    would fail on this docstring. That is the exact failure J66 exists for, met
    inside the guard written to enforce it.
    """
    tree = ast.parse(source)
    bound: set[str] = set()
    for _ in range(2):  # a second pass so `code = other` after `other = code_only(x)` binds
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _derives_from_stripper(node.value, bound):
                bound.update(t.id for t in node.targets if isinstance(t, ast.Name))
    found: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, ast.NotIn) for op in node.ops):
            continue
        if any(_derives_from_stripper(c, bound) for c in node.comparators):
            found.append(node.lineno)
    return sorted(set(found))


def test_every_absence_scan_over_a_stripper_goes_through_the_helper() -> None:
    """Clause (d): the sweep cannot silently un-sweep.

    An absence scan is the one assertion shape that passes when it is broken, so
    a tree that was swept once and then grew a hand-written one is back where it
    started. The listing is the point: this names file and line rather than
    saying a count is wrong.
    """
    offenders: dict[str, list[int]] = {}
    # The whole tests tree, not tests/unit alone: no integration suite reaches a
    # stripper today, and a guard that watched only the directory where the six
    # failures happened would be the next hole rather than the fix.
    for path in sorted(TESTS.rglob("test_*.py")):
        if path.name in _NOT_GUARDS:
            continue
        lines = _absence_scans_outside_the_helper(path.read_text(encoding="utf-8"))
        if lines:
            offenders[path.name] = lines
    assert not offenders, (
        f"absence scans over a stripper that do not go through absent(): {offenders}. "
        "Each one passes when the stripper removed its subject -- six of six did, "
        "across two bursts. Move it onto absent(pattern, sources, "
        "positive_control=...), which runs the same stripper over a control first "
        "and refuses when the pattern stops matching it (CORE2)."
    )


def test_the_guard_over_the_guards_can_see_the_shape_it_looks_for() -> None:
    """The clause-(d) guard is itself an absence assertion, so it gets the same
    treatment it enforces: a positive control, here as a test rather than as a
    parameter, because its subject is a code SHAPE and not a pattern."""
    assert _absence_scans_outside_the_helper('x = "a" not in code_only(s)\n') == [1]
    assert _absence_scans_outside_the_helper("code = code_only(s)\nassert 'a' not in code\n") == [2]
    assert _absence_scans_outside_the_helper(
        "code = without_prose(s).upper()\nassert 'A' not in code\n"
    ) == [2]
    assert (
        _absence_scans_outside_the_helper("assert 'a' not in raw_source\n") == []
    ), "a raw-source scan is a different rule (J66 itself), not this guard's subject"
    assert _absence_scans_outside_the_helper("assert 'a' in code_only(s)\n") == [], (
        "a PRESENCE scan over a stripper cannot be vacuous the same way: if the "
        "stripper ate the subject the assertion fails, loudly, on the first run"
    )


def test_the_exemption_list_says_why_and_stays_short() -> None:
    """A file-level exemption is a real hole -- a genuine guard added to an
    exempt file is not checked -- so it is one file, named, with its reason."""
    assert set(_NOT_GUARDS) == {"test_source_scan.py"}
    for reason in _NOT_GUARDS.values():
        assert len(reason) > 40, "an exemption without a reason is an exemption nobody can review"


# ---- return_annotation: the probe registry's verb (CORE10, ADR 0021 D3) -----------


_PROBE_SOURCE = """
from drydocs_core.check_outcome import CheckOutcome

# a comment that mentions def probe_named_only_here() -> bool
def annotated_probe(x) -> CheckOutcome:
    ...

def bare_probe(x) -> bool:
    ...

def unannotated_probe(x):
    ...

class Holder:
    def method(self) -> "CheckOutcome":
        ...
"""


def test_return_annotation_reads_the_def_as_written() -> None:
    from tests.source_scan import return_annotation

    assert return_annotation(_PROBE_SOURCE, "annotated_probe") == "CheckOutcome"
    assert return_annotation(_PROBE_SOURCE, "bare_probe") == "bool"
    assert return_annotation(_PROBE_SOURCE, "Holder.method") == "'CheckOutcome'"


def test_an_unannotated_function_is_none_and_a_missing_one_raises() -> None:
    """Two different answers on purpose: a guard must not read "no such function"
    as "unannotated" (it would fail for the wrong reason) or as "annotated" (it
    would pass on nothing)."""
    from tests.source_scan import return_annotation

    assert return_annotation(_PROBE_SOURCE, "unannotated_probe") is None
    with pytest.raises(LookupError):
        return_annotation(_PROBE_SOURCE, "probe_named_only_here")  # a comment is not a def
    with pytest.raises(LookupError):
        return_annotation(_PROBE_SOURCE, "Holder")  # a class is not a function
