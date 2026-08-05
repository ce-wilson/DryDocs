"""Guards for the idea-inbox read view (docs/plan/ideas.html).

Same contract as the board render: deterministic, self-contained, and COMMITTED
in sync with its source. The committed-file check is the one that earns its keep
— the board links to this page, so a groom that edits IDEAS.md without
re-rendering leaves a published page describing a stale inbox, which is the J20
drift class (a gate-prompt commit regenerated gates.json but not the matrix).
"""

from __future__ import annotations

from pathlib import Path

from drydocs.plan_ideas import (
    DEFAULT_IDEAS_OUT_PATH,
    DEFAULT_IDEAS_PATH,
    render_ideas,
    write_ideas,
)

_SAMPLE = """# IDEAS — the idea board (inbox)

## Inbox

- **`GROOMED 2026-01-01 → Z9`** *(partially — the rest stays open)* — [idea] a thing.
- [bug] another thing with `code` and **bold**.

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
    assert "GROOMED 2026-01-01" in html, "promotion markers must survive the render"
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
