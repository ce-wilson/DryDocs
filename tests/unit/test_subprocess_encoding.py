"""J76 — a subprocess call that captures TEXT decodes with an EXPLICIT encoding.

THE INCIDENT THIS GUARDS. 2026-09-01: a comparison script read ``git show``
through ``subprocess.run(..., text=True)``. ``text=True`` decodes with the
platform locale — cp1252 on the desktop that ran it — and every backlog item
file holds em dashes, so the decoder substituted its way through the output
and the script reported 18 of 25 "differences" that did not exist. The file on
disk was clean; the instrument was broken; the corrupted measurement said the
tree was wrong. The reference implementation that does it right is the
allocator in ``.claude/skills/groom-backlog/validate.py``, which passes
``encoding="utf-8"`` and carries the comment saying why; this guard proves that
file passes.

SCOPE, stated here because the item asks for it: repo ``scripts/``, ``tests/``,
``web/e2e/`` and the groom-backlog skill's scripts — the places a MEASUREMENT is
authored. Production packages are out of scope: their subprocess calls talk to
tools whose output encoding is that tool's business, and widening the scope is a
separate ruling.

THE RULE, mechanically: a call of ``run``/``check_output``/``Popen``/``call``/
``check_call`` that passes ``text=True`` or ``universal_newlines=True`` must also
pass ``encoding=``. ``getoutput``/``getstatusoutput`` always decode with the
locale and have no encoding parameter, so they are refused outright. Read from
the syntax tree through ``tests/source_scan.call_sites`` (J66: a guard reads code,
not the prose around it — several files in scope EXPLAIN this exact pattern in
comments, and a substring test would fail on the explanation).

EXEMPTION: a comment ``# J76: locale`` on any line of the call. The one thing a
guard may read a comment for is a marker the author placed on purpose, and the
marker must say why on the same line.

THE OTHER TWO INCIDENTS OF THE SAME DAY GET PROSE, NOT GUARDS — see
docs/style/review-provenance.md, "Check the instrument before the subject".
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.source_scan import MISSING, NOT_CONSTANT, call_sites, comment_lines, source_text

REPO = Path(__file__).resolve().parents[2]

#: the places a measurement is authored (see the module docstring)
SCOPE = (
    "scripts",
    "tests",
    "web/e2e",
    ".claude/skills/groom-backlog",
)
REFERENCE_IMPLEMENTATION = REPO / ".claude" / "skills" / "groom-backlog" / "validate.py"

TEXT_CAPTURE_CALLS = ("run", "check_output", "Popen", "call", "check_call")
LOCALE_ONLY_CALLS = ("getoutput", "getstatusoutput")
TEXT_FLAGS = ("text", "universal_newlines")
EXEMPTION = "J76: locale"


def locale_decoding_calls(source: str) -> list[tuple[int, str]]:
    """``(line, reason)`` for every call in ``source`` that would decode captured
    output with the platform locale. Pure over text, so it is testable on a
    synthetic snippet and runs the same over every file in scope."""
    comments = comment_lines(source)
    found: list[tuple[int, str]] = []

    def exempt(lineno: int, end: int) -> bool:
        return any(EXEMPTION in comments.get(line, "") for line in range(lineno, end + 1))

    for site in call_sites(source, (*TEXT_CAPTURE_CALLS, *LOCALE_ONLY_CALLS)):
        if exempt(site.lineno, site.end_lineno):
            continue
        if site.name in LOCALE_ONLY_CALLS:
            found.append((site.lineno, f"{site.name}() always decodes with the locale"))
            continue
        flagged = [
            f for f in TEXT_FLAGS if site.constant(f) is True or site.constant(f) is NOT_CONSTANT
        ]
        if flagged and site.constant("encoding") is MISSING:
            found.append((site.lineno, f"{site.name}({flagged[0]}=...) with no encoding="))
    return found


def _python_files_in_scope() -> list[Path]:
    files: list[Path] = []
    for rel in SCOPE:
        root = REPO / rel
        files.extend(
            p for p in root.rglob("*.py") if "__pycache__" not in p.parts and ".venv" not in p.parts
        )
    return sorted(files)


# ---- the guard over the tree -----------------------------------------------------------


def test_no_measurement_in_scope_decodes_captured_output_with_the_locale() -> None:
    offenders: list[str] = []
    for path in _python_files_in_scope():
        for lineno, reason in locale_decoding_calls(source_text(path)):
            offenders.append(f"{path.relative_to(REPO).as_posix()}:{lineno}: {reason}")
    assert not offenders, (
        "subprocess captures decoding with the platform locale (cp1252 on Windows mojibakes "
        "every em dash and reports it as a difference — J76). Pass encoding='utf-8' (the "
        "allocator's shape), or put `# J76: locale` on the call with the reason:\n  "
        + "\n  ".join(offenders)
    )


def test_the_reference_implementation_passes() -> None:
    """The allocator is the shape to copy; if this ever fails the rule moved, not the file."""
    assert REFERENCE_IMPLEMENTATION.is_file()
    assert locale_decoding_calls(source_text(REFERENCE_IMPLEMENTATION)) == []


# ---- the guard on synthetic sources: red where it must be, green where it must be ------


@pytest.mark.parametrize(
    "snippet, reason",
    [
        ("subprocess.run(['git', 'show'], capture_output=True, text=True)", "run(text=...)"),
        (
            "subprocess.check_output(['git'], universal_newlines=True)",
            "check_output(universal_newlines=...)",
        ),
        ("subprocess.Popen(['x'], stdout=subprocess.PIPE, text=flag)", "Popen(text=...)"),
        ("out = subprocess.getoutput('git status')", "getoutput() always decodes"),
        ("run(['x'], text=True)", "run(text=...)"),
    ],
)
def test_red_on_a_locale_decoding_capture(snippet: str, reason: str) -> None:
    (hit,) = locale_decoding_calls("import subprocess\n" + snippet + "\n")
    assert hit[0] == 2 and hit[1].startswith(reason.split("(")[0])


@pytest.mark.parametrize(
    "snippet",
    [
        "subprocess.run(['git'], capture_output=True, encoding='utf-8', errors='replace')",
        "subprocess.run(['git'], capture_output=True, text=True, encoding='utf-8')",
        "subprocess.run(['git'], capture_output=True)  # bytes: decoded explicitly by the caller",
        "subprocess.run(['git'], check=True)",
        "subprocess.run(['git'], text=True)  # J76: locale — this tool writes the console code page",
        "other.run(text=True, encoding='utf-8')",
    ],
)
def test_green_on_an_explicit_encoding_a_bytes_capture_or_a_marked_exemption(snippet: str) -> None:
    assert locale_decoding_calls("import subprocess\n" + snippet + "\n") == []


def test_the_marker_counts_anywhere_inside_a_multi_line_call() -> None:
    src = "import subprocess\nsubprocess.run(\n    ['x'],\n    text=True,  # J76: locale — legacy tool\n)\n"
    assert locale_decoding_calls(src) == []


def test_a_comment_describing_the_pattern_is_not_a_call() -> None:
    """J66: the explanation of the rule must never trip the rule."""
    src = "# never subprocess.run(cmd, text=True): the locale codec mojibakes em dashes\nimport subprocess\n"
    assert locale_decoding_calls(src) == []
