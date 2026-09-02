"""Every fenced code block under docs/ must close.

Found 2026-08-09 in `docs/port/port-prompt.md`, where it had been live since `84ed7e3`
(2026-08-05) and through four ports. That file wraps the pasteable company prompt
in one long ```` ```text ```` fence and nests a ```` ```powershell ```` example
inside it. Both used THREE backticks, so the inner block's closing fence closed
the OUTER one — 872 lines of guardrails, relays, tracker and step ledger leaked
out of the payload and rendered as page markdown, and the file's final fence
opened a block that never closed.

Nothing errored. The document simply meant something different from what it said,
to every company session that read it for five days. That is why this is a guard
and not a style note.

The rule (CommonMark 4.5) is the whole fix: **an outer fence must be LONGER than
any fence nested inside it**, because a closing fence must be at least as long as
its opener — and a line carrying an info string can only ever open.

SCOPE (J44, 2026-08-21): EVERY tracked markdown file, with a named carve-out list.
`docs/**` is what this repo authors and is held strictly. `internal/` holds
captured transcripts and `.claude/skills/**` / `docs/history/genesis/` hold
vendored or extracted material — the same defect lives in five of those files,
and editing them to satisfy a guard would edit somebody else's capture. They are
CARVED OUT BY NAME with the reason (CAPTURED_PATHS, the FOREIGN_PATHS /
HISTORICAL_PATHS idiom of test_runbook_currency.py), and the list is shrink-only:
a carved-out file that becomes clean must leave it. Anything new anywhere in the
tree is guarded from its first commit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs"

_FENCE = re.compile(r"^ {0,3}(`{3,})\s*(\S*)\s*$")


def unclosed_fence(text: str) -> tuple[int, int] | None:
    """``(line_no, backtick_count)`` of an unclosed fence, or ``None``.

    Walks the document the way a CommonMark parser does: a block opened with N
    backticks is closed by the first later line of >= N backticks that carries NO
    info string. Anything else inside is literal content.
    """
    open_at: int | None = None
    open_len = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if not match:
            continue
        ticks, info = match.group(1), match.group(2)
        if open_at is None:
            open_at, open_len = lineno, len(ticks)
        elif len(ticks) >= open_len and not info:
            open_at, open_len = None, 0
    return (open_at, open_len) if open_at is not None else None


def _docs() -> list[Path]:
    return sorted(DOCS_ROOT.rglob("*.md"))


def test_the_scan_actually_reaches_the_documents() -> None:
    """Guard the guard: an empty sweep passes everything and proves nothing."""
    found = _docs()
    assert len(found) > 20, f"expected the docs tree, found {len(found)} files"
    assert (DOCS_ROOT / "port" / "port-prompt.md") in found


def test_every_fence_under_docs_closes() -> None:
    problems = []
    for path in _docs():
        result = unclosed_fence(path.read_text(encoding="utf-8"))
        if result:
            lineno, ticks = result
            problems.append(
                f"{path.relative_to(DOCS_ROOT.parent)}: fence of {ticks} backticks "
                f"opened at line {lineno} never closes. If it wraps a nested block, "
                f"the OUTER fence must be longer than the inner one."
            )
    assert not problems, "\n".join(problems)


#: J44 — tracked markdown the fence guard does NOT hold, each with its reason.
#: These are captures and vendored material: the unclosed fence is the SOURCE's
#: defect, faithfully transcribed, and correcting it here would edit someone
#: else's document. Shrink-only: an entry that becomes clean fails below.
CAPTURED_PATHS: dict[str, str] = {
    "internal/cdo-reference/CONFLUENCE-TRANSCRIPT.md": (
        "VERBATIM capture of the company Confluence space (cdo-frameworks corpus, trust "
        "VERBATIM): the unclosed fence at line 5140 is the page's own"
    ),
    "internal/cdo-reference/TRANSCRIPT-1-ONTOLOGY.md": (
        "VERBATIM capture, same corpus: the fence at line 419 is the source's"
    ),
    ".claude/skills/data-context-extractor/references/domain-template.md": (
        "vendored skill reference material — upstream's file, upstream's fence (line 142)"
    ),
    ".claude/skills/data-context-extractor/references/example-output.md": (
        "vendored skill reference material — upstream's file, upstream's fence (line 112)"
    ),
}


def _tracked_markdown() -> list[Path]:
    import subprocess

    root = DOCS_ROOT.parent
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [root / line for line in out.splitlines() if line.endswith(".md")]


def test_every_fence_in_every_tracked_markdown_closes_or_is_carved_out_by_name() -> None:
    """J44: the whole tree, default-deny, captures excused by name with a reason."""
    root = DOCS_ROOT.parent
    problems = []
    still_dirty: set[str] = set()
    found = _tracked_markdown()
    assert len(found) > 200, f"expected the tracked markdown tree, found {len(found)} files"
    for path in found:
        rel = path.relative_to(root).as_posix()
        result = unclosed_fence(path.read_text(encoding="utf-8", errors="replace"))
        if not result:
            continue
        if rel in CAPTURED_PATHS:
            still_dirty.add(rel)
            continue
        lineno, ticks = result
        problems.append(
            f"{rel}: fence of {ticks} backticks opened at line {lineno} never closes. "
            "Fix it if this repo authored the file; if it is a capture, carve it out BY NAME "
            "in CAPTURED_PATHS with the reason."
        )
    assert not problems, "\n".join(problems)
    # shrink-only: a carve-out that no longer needs excusing must leave the list
    stale = sorted(set(CAPTURED_PATHS) - still_dirty)
    assert not stale, f"CAPTURED_PATHS entries are clean now — remove them: {stale}"


def test_every_carve_out_carries_a_reason_and_exists() -> None:
    root = DOCS_ROOT.parent
    for rel, why in CAPTURED_PATHS.items():
        assert why.strip(), rel
        assert (root / rel).exists(), f"{rel} is carved out but no longer tracked"
        assert not rel.startswith("docs/"), "docs/** is authored here and is never carved out"


# ---- the parser itself, both directions --------------------------------------


def test_a_balanced_document_is_clean() -> None:
    assert unclosed_fence("intro\n```py\ncode\n```\noutro\n") is None


def test_an_unclosed_fence_is_reported_with_its_line() -> None:
    assert unclosed_fence("intro\n```py\ncode never closed\n") == (2, 3)


def test_a_same_length_inner_fence_closes_the_outer_one() -> None:
    """The exact port-prompt.md defect, reproduced.

    Both fences are three backticks, so the inner block's closer ends the outer
    block early and the outer block's closer opens a new one that never closes.
    """
    doc = "```text\npayload\n\n```powershell\nGet-Thing\n```\n\nmore payload\n```\n"
    assert unclosed_fence(doc) == (9, 3)


def test_a_longer_outer_fence_nests_correctly() -> None:
    """The fix. Same document, four backticks outside and three inside."""
    doc = "````text\npayload\n\n```powershell\nGet-Thing\n```\n\nmore payload\n````\n"
    assert unclosed_fence(doc) is None


def test_a_closing_candidate_carrying_an_info_string_cannot_close() -> None:
    """A line with an info string only ever OPENS — the rule that makes the bug."""
    assert unclosed_fence("```\ncode\n```python\n") == (1, 3)


@pytest.mark.parametrize("indent", ["", " ", "  ", "   "])
def test_fences_indented_up_to_three_spaces_still_count(indent: str) -> None:
    assert unclosed_fence(f"{indent}```py\ncode\n{indent}```\n") is None
