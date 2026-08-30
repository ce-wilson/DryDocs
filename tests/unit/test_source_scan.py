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
from pathlib import Path

import pytest

from tests.source_scan import (
    ALL,
    ATTRIBUTE,
    KINDS,
    NAME,
    called_names,
    code_only,
    imported_modules,
    source_text,
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
    for verb in (code_only, imported_modules, called_names, source_text):
        assert inspect.getmodule(verb) is module


def test_the_helper_holds_three_verbs_and_one_convenience() -> None:
    """Clause (b): nothing else goes in.

    A helper module that grows a fourth verb nobody calls is how a shared helper
    becomes a private one again, so the surface is pinned rather than trusted.
    """
    import tests.source_scan as module

    # Against __all__, not against vars(): a module's namespace also holds what it
    # IMPORTS (Path, Final), so the first version of this test failed on its own
    # imports rather than on any new verb.
    assert set(module.__all__) == {"code_only", "imported_modules", "called_names", "source_text"}
    for name in module.__all__:
        assert callable(getattr(module, name))
