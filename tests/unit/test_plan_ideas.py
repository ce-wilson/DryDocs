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

from drydocs.docgen.plan_ideas import (
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


#: The inbox id grammar: `[<EDITION>-]Idea-<n>[a-z]` - the optional edition segment
#: (rider idea-series-grammar B1, 2026-09-05; 2-5 uppercase letters, declared in
#: config/taxonomy/editions.yaml), the number, the optional SPLIT suffix. The base
#: inbox is unprefixed, so every existing header matches unchanged. Same segment the
#: allocator's _IDEA_RE carries; test_backlog.py holds the two grammars to one list.
_IDEA_ID = r"(?:[A-Z]{2,5}-)?Idea-\d+[a-z]?"

_HEADER = re.compile(
    rf"^- \*\*`({_IDEA_ID})`\*\* · \d{{4}}-\d{{2}}-\d{{2}} · `\[[a-z]+\]` · "
    r"\*\*(open|parked|groomed|merged|closed)\b.*?\*\* · prio\?? "
    r"\*\*(High|Med|Low|Deferred)\*\* —"
)


def _inbox_entries() -> list[str]:
    lines = DEFAULT_IDEAS_PATH.read_text(encoding="utf-8").split("\n")
    start = lines.index("## Inbox")
    end = next(i for i, line in enumerate(lines) if line.startswith("## ") and i > start)
    return [line for line in lines[start:end] if line.startswith("- ")]


def _all_idea_ids() -> list[str]:
    """Every `Idea-<n>` header in the file — inbox AND audit trail."""
    return re.findall(
        rf"^- \*\*`({_IDEA_ID})`\*\* ·", DEFAULT_IDEAS_PATH.read_text(encoding="utf-8"), re.M
    )


def test_every_inbox_entry_carries_the_header() -> None:
    """The Idea-<n> / status / prio scheme (user direction 2026-08-05) is only useful if
    it is COMPLETE. One unheadered entry and "scan the inbox by priority" stops working
    silently — the entry simply does not appear in the scan, which reads as "nothing to
    review here" rather than as a formatting slip."""
    bad = [line[:110] for line in _inbox_entries() if not _HEADER.match(line)]
    assert not bad, f"inbox entries missing or malforming the header: {bad}"


def test_idea_ids_are_unique() -> None:
    """Ids are stable references — the backlog notes and the audit trail cite them by
    number, so reusing one silently re-points every citation of it.

    Scans the WHOLE file, not just the inbox. A groomed entry moves to the audit trail
    and keeps its id, so an inbox-only check stops seeing half the namespace the moment
    a filing pass runs — and this file is `union-append` at port time, which is exactly
    when a second entry carrying an existing number arrives.
    """
    ids = _all_idea_ids()
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate Idea ids: {dupes}"


# ---- allocator bands (2026-08-18) -------------------------------------------
# Three allocators mint from one counter with no lock (producer-desktop,
# producer-laptop, company). Git serializes the first two only AFTER both have
# pushed, and never serializes the third. Bands remove the collision by making
# allocation need no coordination: producer 1-9999, company 10000+ — readable by
# LENGTH (five digits or more is company), so there is no boundary to remember.

#: Producer allocates at or below this. Company allocates above it.
PRODUCER_BAND_CEILING = 9999

#: Company ids that have legitimately arrived here through a `union-append` port.
#: EMPTY today and deliberately a hand-maintained list rather than a rule: a ported
#: company entry landing in the producer inbox is a thing a human should look at
#: once, and an exemption that must be typed is what forces that look.
PORTED_COMPANY_IDS: frozenset[int] = frozenset()


def test_producer_allocates_below_the_company_band() -> None:
    """Nothing minted here may take a company number.

    Forward-only by construction: historical ids are all far below the ceiling and
    are never renumbered (ids are join keys — the G87 ruling), so a low number means
    "allocated before the partition", not "producer". The rule governs the NEXT id.
    """
    stray = sorted(
        n
        for n in (
            int(i.split("Idea-", 1)[1].rstrip("abcdefghijklmnopqrstuvwxyz"))
            for i in _all_idea_ids()
            if "-Idea-" not in i  # an edition's own inbox counts from 1; only the base is banded
        )
        if n > PRODUCER_BAND_CEILING and n not in PORTED_COMPANY_IDS
    )
    assert not stray, (
        f"Idea ids in the COMPANY band (>{PRODUCER_BAND_CEILING}): {stray}. Producer "
        "allocates 1-9999. If these arrived through a port, add them to "
        "PORTED_COMPANY_IDS — the exemption is hand-maintained on purpose, so a "
        "company entry landing in this inbox gets looked at once."
    )


def test_the_bands_are_documented_where_a_capturer_will_read_them() -> None:
    """A convention nobody can find is re-broken by the next person to add an entry,
    and this one is only load-bearing at PORT time — months after the capture that
    breaks it. So the numbers live in the file that people actually open."""
    text = DEFAULT_IDEAS_PATH.read_text(encoding="utf-8")
    for token in ("9999", "10000+", "union-append"):
        assert token in text, (
            f"IDEAS.md no longer states {token!r} — the allocator-band rule has to be "
            "readable next to the capture format it constrains, not only in a test."
        )


def test_no_markdown_escape_leaks_into_the_render() -> None:
    """The Epic L renderer does not process backslash escapes, so a `\\*` written to mean
    "literal asterisk" reaches the published page as backslash-asterisk. Caught this way
    once already, on the first draft of the prio marker."""
    assert "\\*" not in DEFAULT_IDEAS_OUT_PATH.read_text(encoding="utf-8")


def test_a_pending_file_never_carries_a_real_idea_id() -> None:
    """PLAN4 (d): docs/restructure/ideas/pending-<branch>.md holds CANDIDATES (`Idea-?`),
    minted into IDEAS.md at landing in one allocator pass. A real header in one is an id
    that exists in a branch and nowhere the allocator's union can see it yet - the exact
    collision the pending file exists to remove. The README beside them is exempt."""
    pending_dir = DEFAULT_IDEAS_PATH.parent / "ideas"
    offenders = []
    for path in sorted(pending_dir.glob("pending-*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"`(?:[A-Z]{2,5}-)?Idea-\d+[a-z]?`", line):
                offenders.append(f"{path.name}:{n}")
    assert not offenders, (
        f"pending files carrying a real Idea id: {offenders}. Candidates use `Idea-?`; "
        "mint at landing with validate.py --mint-pending <file>."
    )
