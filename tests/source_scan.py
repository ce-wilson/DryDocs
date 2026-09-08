"""Read CODE, not the prose around it — the shared source-reading helper (J66).

THE FAILURE THIS REPLACES. A guard that greps its own source tree for a
forbidden pattern also matches the COMMENT that explains why the pattern is
forbidden. It happened three times on 2026-08-30 alone, in three separate builds,
and each author invented a different fix:

* G128's declared-list guards matched ``os.environ`` and ``${VAR:-default}`` in
  their own docstrings — fixed with a local tokenize-based stripper;
* G129's no-import guard matched the literal text ``set_env_var`` in three
  modules that merely NAME the script in prose — fixed with an abstract-syntax
  import walk;
* G130's purity guard matched ``session`` and ``run(`` in its own docstring —
  fixed with an abstract-syntax call walk.

Every fix was correct. Every fix was written from scratch. **The cost that
matters is not the duplication — it is that a guard which fails on the
explanation teaches people to stop writing explanations**, and in a repo whose
comments carry its rulings that costs more than the guard is worth.

THE RULE. A guard that asks "does this code do X" reads the code through one of
the three verbs below. A bare substring test over raw source is the defect, not a
shortcut. This is J37's disease at the other end: J37 says read the importable
object rather than a render; this says read the code rather than the prose around
it.

WHY IT LIVES AT THE TESTS ROOT. ``tests/env_drift.py`` is the precedent — a
shared non-test module beside the suites, imported as ``from tests import
env_drift``. pytest's default ``python_files`` collects only ``test_*.py`` and
``*_test.py``, so a module named like this one is never collected as a test, and
both the unit and integration suites can import it. The unit directory would have
worked too and would have said the wrong thing: the helper is not one suite's.

WHAT IS DELIBERATELY NOT HERE. The Cypher stripper in
``tests/unit/test_vocabulary_endpoints.py`` shares this module's old name and is
NOT the same thing: it strips Cypher comments and literals with regular
expressions over a grammar Python's tokenizer cannot parse. It stays where it is.
Folding two unrelated things together because their names match is the mistake
this note exists to prevent.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

#: The whole surface. Pinned rather than inferred, and asserted by
#: tests/unit/test_source_scan.py: a helper module that grows a fourth verb
#: nobody calls is how a shared helper becomes a private one again. The fourth
#: verb, ``call_sites``, arrived with a caller (J76's subprocess-encoding guard)
#: and ``comment_lines`` with it, for the one thing a guard may read a comment
#: for: an exemption marker placed on purpose. ``without_prose`` and ``absent``
#: arrived together with CORE2 and are one idea, not two: the stripper a LITERAL
#: subject needs, and the call shape that proves the right stripper was chosen.
__all__ = [
    "code_only",
    "without_prose",
    "imported_modules",
    "called_names",
    "call_sites",
    "comment_lines",
    "source_text",
    "absent",
    "CallSite",
    "MISSING",
    "NOT_CONSTANT",
    "VacuousScanError",
]

#: Which calls :func:`called_names` reports. ``"name"`` is a bare ``foo()``,
#: ``"attribute"`` is ``obj.foo()``, ``"all"`` is both. The distinction is
#: load-bearing rather than a convenience: a guard asserting a module does not
#: call ``client.run`` should not fire on a local helper that happens to be
#: called ``run``.
NAME: Final = "name"
ATTRIBUTE: Final = "attribute"
ALL: Final = "all"
KINDS: Final = (NAME, ATTRIBUTE, ALL)


def source_text(path: Path | str, root: Path | None = None) -> str:
    """Read a source file as text. The thin path-taking convenience.

    The three verbs take TEXT so every one of them is testable without touching
    the filesystem; this exists because most call sites do have a path and
    spelling ``read_text(encoding="utf-8")`` at each of them is how encodings
    drift apart.
    """
    target = Path(path)
    if root is not None and not target.is_absolute():
        target = root / target
    return target.read_text(encoding="utf-8")


def code_only(source: str) -> str:
    """``source`` with comments and string literals removed.

    Returns the surviving tokens joined by single spaces, so this is for
    SUBSTRING and regular-expression matching, never for re-parsing: the spacing
    is not the original and was never meant to be.

    Docstrings go too, because a docstring is a string literal — which is the
    whole point. Every guard that hit this trap named the thing it forbids in its
    own docstring.

    Raises ``tokenize.TokenError`` on source that does not tokenize; that is
    surfaced rather than swallowed, because a guard silently scanning nothing is
    worse than one that fails loudly.
    """
    kept: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(tok.string)
    return " ".join(kept)


def without_prose(source: str) -> str:
    """``source`` with its PROSE removed and its data literals left alone.

    Prose in Python is two things, not one: ``#`` comments and DOCSTRINGS. Both
    go; every other string literal stays. This is the stripper for a subject
    that IS a literal — a file path, a route, a Cypher statement, an import
    specifier — where :func:`code_only` would remove the very text being looked
    for and the guard would pass on nothing (CORE2: six of six absence scans
    across two bursts failed exactly that way).

    Docstrings go WITH the comments because otherwise this stripper cannot be
    used at all by the guards that need it: a module whose docstring names every
    symbol it forbids — the house style, and the right style — would match its
    own explanation. That is J66's failure arriving from the other side, and the
    reason this verb is not called ``without_comments`` after the TypeScript
    twin in ``web/src/test/sourceScan.ts``: TypeScript has no docstring, so
    there the two names mean the same thing and here they do not.

    UNLIKE :func:`code_only`, THE LAYOUT IS THE ORIGINAL. Prose is blanked in
    place rather than re-joined from tokens, so ``os.environ``, ``a.b.c`` and
    every literal survive character-for-character. ``code_only`` joins tokens
    with single spaces, which is a second and quieter way for an absence scan to
    match nothing: ``"query_specs.py"`` cannot appear in its output even when
    the module does import it. Line and column numbers are preserved too, so a
    result can be read next to the file.

    Raises ``tokenize.TokenError`` or ``SyntaxError`` on source that does not
    parse — surfaced, never swallowed, for the reason :func:`code_only` gives.
    """
    lines = source.splitlines(keepends=True)
    spans: list[tuple[int, int, int, int]] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            spans.append((tok.start[0], tok.start[1], tok.end[0], tok.end[1]))
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, holders):
            continue
        body = getattr(node, "body", None)
        if not body or not isinstance(body[0], ast.Expr):
            continue
        first = body[0].value
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        spans.append(
            (
                first.lineno,
                first.col_offset,
                first.end_lineno or first.lineno,
                first.end_col_offset or 0,
            )
        )
    for start_row, start_col, end_row, end_col in spans:
        for row in range(start_row, end_row + 1):
            line = lines[row - 1]
            keep_right = line[len(line.rstrip("\r\n")) :]
            body_text = line[: len(line) - len(keep_right)]
            lo = start_col if row == start_row else 0
            hi = end_col if row == end_row else len(body_text)
            lo, hi = min(lo, len(body_text)), min(hi, len(body_text))
            lines[row - 1] = body_text[:lo] + " " * (hi - lo) + body_text[hi:] + keep_right
    return "".join(lines)


def imported_modules(source: str) -> set[str]:
    """Every module name ``source`` imports, from both import forms.

    ``import a.b`` yields ``a.b``; ``from a.b import c`` yields ``a.b``. A
    relative import yields its module or ``""`` when it names none, which keeps
    the return type honest rather than inventing a resolved name this function
    has no package context to compute.

    This is what a "does anything import X" guard needs: mentioning a module in
    prose is not importing it, and that distinction was the G129 failure exactly.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
    return found


def called_names(source: str, *, kind: str = ALL) -> set[str]:
    """The names ``source`` CALLS — bare, attribute, or both.

    Attribute calls report the final attribute only (``cli.run(...)`` yields
    ``run``), because the receiver is a local at every real call site and keying
    on it would make a guard miss the very site it exists to catch.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and kind in (NAME, ALL):
            found.add(func.id)
        elif isinstance(func, ast.Attribute) and kind in (ATTRIBUTE, ALL):
            found.add(func.attr)
    return found


@dataclass(frozen=True)
class CallSite:
    """One call of a watched name: where it is and which keywords it passes.

    ``keywords`` maps each keyword argument's name to its literal value when the
    argument is a constant (``True``, ``"utf-8"``), else to :data:`NOT_CONSTANT`
    — a guard can then say "``text=True`` with no ``encoding``" without guessing
    at expressions it cannot evaluate. ``lineno``/``end_lineno`` bracket the whole
    call, so a per-line exemption marker anywhere inside it can be honoured.
    """

    name: str
    lineno: int
    end_lineno: int
    keywords: dict[str, object] = field(default_factory=dict)

    def constant(self, keyword: str) -> object:
        return self.keywords.get(keyword, MISSING)


MISSING: Final = object()
NOT_CONSTANT: Final = object()


def call_sites(source: str, names: Collection[str]) -> list[CallSite]:
    """Every call of one of ``names`` (bare or final-attribute, as
    :func:`called_names` matches), with its keyword arguments — the fourth verb
    (J76). :func:`called_names` answers "is X called at all"; a guard about HOW
    something is called (``subprocess.run(..., text=True)`` with no encoding)
    needs the arguments, and reading them from the tree rather than the text is
    what keeps such a guard off the comments that explain the very pattern it
    forbids."""
    wanted = set(names)
    found: list[CallSite] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            continue
        if name not in wanted:
            continue
        keywords: dict[str, object] = {}
        for kw in node.keywords:
            if kw.arg is None:  # **mapping — its keys are unknowable here
                continue
            keywords[kw.arg] = (
                kw.value.value if isinstance(kw.value, ast.Constant) else NOT_CONSTANT
            )
        found.append(
            CallSite(
                name=name,
                lineno=node.lineno,
                end_lineno=node.end_lineno or node.lineno,
                keywords=keywords,
            )
        )
    return found


def comment_lines(source: str) -> dict[int, str]:
    """Line number -> the comment on that line, for every line that carries one.

    The one legitimate reason a guard reads a comment: an EXEMPTION MARKER the
    author put there on purpose (the ``noqa`` idiom). A guard that honours a
    marker reads exactly the marker's line, never the prose around the code —
    the J66 rule with its one stated exception made explicit.
    """
    found: dict[int, str] = {}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            found[tok.start[0]] = tok.string
    return found


class VacuousScanError(AssertionError):
    """An absence scan that could not have found its subject in the first place.

    Raised by :func:`absent` when the pattern no longer matches its own positive
    control after stripping — the guard was measuring nothing. It subclasses
    ``AssertionError`` so pytest reports it as the test failure it is, and is a
    distinct type so the test that PROVES the refusal can name what it caught
    rather than accepting any failure as the right one.
    """


def _apply(
    text: str, stripper: Callable[[str], str], normalize: Callable[[str], str] | None
) -> str:
    """The one pipeline. Control and tree go through THIS, never through two."""
    scanned = stripper(text)
    return normalize(scanned) if normalize is not None else scanned


def _matches(pattern: str | re.Pattern[str], text: str) -> bool:
    return bool(pattern.search(text)) if isinstance(pattern, re.Pattern) else pattern in text


def absent(
    pattern: str | re.Pattern[str],
    sources: Mapping[str, str] | Iterable[Path | str],
    *,
    positive_control: str,
    stripper: Callable[[str], str] = code_only,
    normalize: Callable[[str], str] | None = None,
    root: Path | None = None,
    because: str = "",
) -> None:
    """Assert ``pattern`` appears in none of ``sources`` — with a MUTATION PROBE.

    THE PROBLEM THIS EXISTS FOR. An absence scan is the one assertion shape that
    passes when it is broken. ``assert X not in code_only(source)`` is green when
    the code is clean, green when the pattern is misspelled, and green when the
    stripper removed the subject before the scan ran — and the last one is not
    hypothetical: six of six absence scans written across two Lane B bursts were
    vacuous on first write, always the same way, because ``code_only`` strips
    string literals and the subject WAS a literal. Two of the six were caught
    only by deliberately breaking the thing the guard claimed to catch.

    THE FIX IS TO MAKE THE PROBE MANDATORY AND AUTOMATIC. ``positive_control`` is
    a snippet that DOES contain the subject, shaped like the real violation. It
    goes through the same stripper and the same ``normalize`` as the tree — the
    same pipeline, not an equivalent one — and the pattern must still match it.
    When it does not, this raises :class:`VacuousScanError` naming the stripper,
    the subject and the control's scanned text, and the guard fails on ITSELF
    rather than passing on the tree.

    WHAT IT STILL CANNOT DO, said here because a guard that oversells itself is
    the failure it is meant to prevent: it cannot tell whether the control looks
    like the REAL violation. ``absent("useGraphAccess", ..., positive_control="x
    = useGraphAccess()")`` clears the probe and is still the wrong guard if the
    violation in the wild is ``path='/admin'``. What this buys is that a control
    now EXISTS, in the call, where a reviewer reads it — the wrong control is
    visible, and a stripper/subject mismatch is impossible.

    ``sources`` is either a mapping of label to source text, or an iterable of
    paths read through :func:`source_text` (``root`` resolves relative ones). An
    EMPTY source set is refused, not passed: scanning nothing is the other way
    an absence guard reports green while checking nothing.

    ``pattern`` is a substring when it is a ``str`` and a search when it is a
    compiled regular expression. Matching happens after ``normalize``, so write
    the pattern in normalized form — and note that the control proves you did,
    which is why no separate rule about it is needed.
    """
    if isinstance(sources, Mapping):
        texts = dict(sources)
    else:
        texts = {str(p): source_text(p, root) for p in sources}
    if not texts:
        raise VacuousScanError(
            f"absent({pattern!r}) was given no sources to scan. A scan over zero "
            "files passes for the same reason a scan over a stripped-away subject "
            "does: it never looked."
        )

    scanned_control = _apply(positive_control, stripper, normalize)
    if not _matches(pattern, scanned_control):
        raise VacuousScanError(
            f"POSITIVE CONTROL FAILED: {pattern!r} does not match its own control "
            f"after {stripper.__name__}"
            + (f" + {getattr(normalize, '__name__', 'normalize')}" if normalize else "")
            + ".\n"
            f"  control  : {positive_control!r}\n"
            f"  scanned  : {scanned_control!r}\n"
            "The stripper removed the subject (or reshaped it) before the scan ran, "
            "so this guard would pass on ANY tree. A subject that is a string "
            "literal needs without_prose; code_only is for a subject that is code. "
            "Note also that code_only joins tokens with single spaces, so a dotted "
            "name never survives it intact (J66, CORE2)."
        )

    hits = {
        label: text
        for label, text in texts.items()
        if _matches(pattern, _apply(text, stripper, normalize))
    }
    if hits:
        raise AssertionError(
            f"{pattern!r} is present in {sorted(hits)}" + (f": {because}" if because else "")
        )
