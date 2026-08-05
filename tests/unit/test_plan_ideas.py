"""Guards for the idea-inbox read view (docs/plan/ideas.html).

Same contract as the board render: deterministic, self-contained, and COMMITTED
in sync with its source. The committed-file check is the one that earns its keep
— the board links to this page, so a groom that edits IDEAS.md without
re-rendering leaves a published page describing a stale inbox, which is the J20
drift class (a gate-prompt commit regenerated gates.json but not the matrix).
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs.plan_ideas import (
    DEFAULT_IDEAS_OUT_PATH,
    DEFAULT_IDEAS_PATH,
    render_ideas,
    write_ideas,
)

_SAMPLE = """# IDEAS — the idea board (inbox)

## Inbox

- **`Idea-2`** · 2026-01-01 · `[idea]` · **groomed → Z9** · prio? **High** — a thing.
- **`Idea-1`** · 2026-01-01 · `[bug]` · **open** · prio? **Low** — another with `code` and **bold**.

## Recently groomed (audit trail)

- 2026-01-01 — [chore] something → **Z8**.
"""


def test_render_is_deterministic() -> None:
    """No clock, no host path, no counter — the committed file must be
    byte-identical across the producer and company trees (the board's
    self-locating-URL precedent)."""
    assert render_ideas(_SAMPLE) == render_ideas(_SAMPLE)


def test_render_is_self_contained() -> None:
    """No external CSS/JS/font fetch: the page has to open from a file:// path
    on a machine with no network, which is how it actually gets read."""
    html = render_ideas(_SAMPLE)
    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    for remote in ("http://", "https://", "<script src=", "@import"):
        assert remote not in html, remote


def test_content_and_backlink_render() -> None:
    html = render_ideas(_SAMPLE)
    assert "idea inbox" in html
    assert 'href="board.html"' in html, "the page must link back to the board"
    assert "Idea-2" in html, "entry ids must survive the render"
    assert "groomed → Z9" in html, "status must survive the render"
    assert "<code>code</code>" in html and "<strong>bold</strong>" in html


def test_page_declares_it_is_not_the_source_of_record() -> None:
    """The inbox is hand-edited markdown BY DESIGN (zero schema, low friction).
    A rendered page that did not say so invites someone to treat it as an
    authoring surface and lose a capture."""
    html = render_ideas(_SAMPLE)
    assert "system of record" in html
    assert "IDEAS.md" in html


def test_write_ideas_writes_file(tmp_path: Path) -> None:
    src = tmp_path / "IDEAS.md"
    src.write_text(_SAMPLE, encoding="utf-8")
    out = tmp_path / "out" / "ideas.html"

    written = write_ideas(src, out)

    assert written == out
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_committed_ideas_page_matches_its_source() -> None:
    """The stale-render check from the CLAUDE.md session ritual, as a test:
    re-render the real IDEAS.md and compare to what is committed."""
    expected = render_ideas(DEFAULT_IDEAS_PATH.read_text(encoding="utf-8"))
    committed = DEFAULT_IDEAS_OUT_PATH.read_text(encoding="utf-8")
    assert committed == expected, (
        "docs/plan/ideas.html is stale — re-run `python scripts/render_board.py` "
        "(it renders the inbox too) and commit the refresh"
    )


_HEADER = re.compile(
    r"^- \*\*`(Idea-\d+[a-z]?)`\*\* · \d{4}-\d{2}-\d{2} · `\[[a-z]+\]` · "
    r"\*\*(open|parked|groomed|merged|closed)\b.*?\*\* · prio\?? "
    r"\*\*(High|Med|Low|Deferred)\*\* —"
)


def _inbox_entries() -> list[str]:
    lines = DEFAULT_IDEAS_PATH.read_text(encoding="utf-8").split("\n")
    start = lines.index("## Inbox")
    end = next(i for i, line in enumerate(lines) if line.startswith("## ") and i > start)
    return [line for line in lines[start:end] if line.startswith("- ")]


def test_every_inbox_entry_carries_the_header() -> None:
    """The Idea-<n> / status / prio scheme (user direction 2026-08-05) is only useful if
    it is COMPLETE. One unheadered entry and "scan the inbox by priority" stops working
    silently — the entry simply does not appear in the scan, which reads as "nothing to
    review here" rather than as a formatting slip."""
    bad = [line[:110] for line in _inbox_entries() if not _HEADER.match(line)]
    assert not bad, f"inbox entries missing or malforming the header: {bad}"


def test_idea_ids_are_unique() -> None:
    """Ids are stable references — the backlog notes and the audit trail cite them by
    number, so reusing one silently re-points every citation of it."""
    ids = [_HEADER.match(line).group(1) for line in _inbox_entries()]  # type: ignore[union-attr]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate Idea ids: {dupes}"


def test_no_markdown_escape_leaks_into_the_render() -> None:
    """The Epic L renderer does not process backslash escapes, so a `\\*` written to mean
    "literal asterisk" reaches the published page as backslash-asterisk. Caught this way
    once already, on the first draft of the prio marker."""
    assert "\\*" not in DEFAULT_IDEAS_OUT_PATH.read_text(encoding="utf-8")
