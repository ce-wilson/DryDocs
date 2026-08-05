"""plan_ideas.py — render docs/restructure/IDEAS.md to docs/plan/ideas.html.

THE GAP THIS CLOSES (user directive 2026-08-05): the backlog has a rendered
surface (``docs/plan/board.html``) and the gate prompts have one
(``web/src/generated/gates.json`` -> the console ``/gates`` page). The INBOX had
none — it is the one artifact in the CLAUDE.md §0 triple (inbox -> backlog ->
board) that could only be read as raw markdown in an editor. Ideas that nobody
reviews are ideas that get re-discovered, and this session produced four inbox
entries that each correct something committed, so "reviewable" is not cosmetic.

WHAT THIS IS NOT: an authoring surface. IDEAS.md stays the system of record, hand
-edited, zero-schema by design (that is the whole point of a low-friction inbox).
This page is a deterministic READ view — the same contract the board holds, and
the reason both are safe to commit: byte-identical output for identical input, so
the stale-render check in the session ritual works on it (`git diff --quiet
docs/plan/ideas.html` after a re-render).

MARKDOWN: reuses ``drydocs.design_doc.render_body`` rather than adding a second
markdown implementation — the Epic L renderer already covers the subset IDEAS.md
uses (headings, nested lists, bold/code inline, tables, blockquotes, fences), and
a second renderer would drift from it. classification: Internal-Public (mechanism;
the CONTENT is whatever the inbox holds, which is why the page carries the same
INTERNAL banner the board does).
"""

from __future__ import annotations

from pathlib import Path

from drydocs.design_doc import render_body

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IDEAS_PATH = _REPO_ROOT / "docs" / "restructure" / "IDEAS.md"
DEFAULT_IDEAS_OUT_PATH = _REPO_ROOT / "docs" / "plan" / "ideas.html"

# SELF-CONTAINED stylesheet, deliberately not the board's. The first draft
# imported ``plan_board._CSS`` "so the two pages read as one surface", and the
# component-boundary guard rejected it in both directions — components never
# import each other. That guard was right on the design too: the board is a
# filterable grid, the inbox is prose, and they need different rules. What they
# share is a visual VOCABULARY (the same neutral palette and the same blue for
# actions), which is 20 lines of duplication rather than a coupling.
_CSS = """
:root{color-scheme:light}
body{font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1a1a1a;
  margin:2rem auto;padding:0 1.5rem;max-width:62rem;background:#fff}
h1{font-size:1.5rem;margin:0 0 .3rem}
.subtitle{color:#666;font-size:.85rem;margin:.2rem 0}
.backlink{display:inline-block;margin:0 0 1.2rem;padding:.35rem .8rem;border:1px solid #2563eb;
  border-radius:4px;background:#fff;color:#2563eb;text-decoration:none;font-size:.85rem}
.backlink:hover{background:#eff6ff}
.ideas-body h2{margin-top:2rem;padding-top:.6rem;border-top:2px solid #e2e2e2;font-size:1.15rem}
.ideas-body h3{margin-top:1.4rem;font-size:1rem}
.ideas-body li{margin:.45rem 0}
.ideas-body li>ul{margin-top:.35rem}
.ideas-body code{background:#f4f4f5;padding:.05rem .3rem;border-radius:3px;font-size:.88em}
.ideas-body blockquote{margin:.6rem 0;padding:.3rem 0 .3rem .9rem;border-left:3px solid #cbd5e1;
  color:#444}
.ideas-body table{border-collapse:collapse;margin:.7rem 0}
.ideas-body td,.ideas-body th{border:1px solid #e2e2e2;padding:.3rem .55rem;font-size:.9rem}
.ideas-body th{background:#f8f8f8;text-align:left}
""".strip()


def render_ideas(markdown: str) -> str:
    """Render IDEAS.md text to a standalone HTML page. Pure — no I/O, no clock.

    Deterministic by construction: no timestamp, no host path, no counter derived
    from anything but the input text. The board's self-locating-URL trick is the
    precedent — anything machine-specific is filled client-side or not at all, so
    the committed file stays byte-identical across the producer and company trees.
    """
    body = render_body(markdown)
    return (
        '<!doctype html>\n<html><head><meta charset="utf-8">\n'
        "<title>DryDocs — idea inbox</title>\n"
        f"<style>{_CSS}</style>\n</head><body>\n"
        '<a class="backlink" href="board.html">&larr; Project board</a>\n'
        "<h1>DryDocs — idea inbox</h1>\n"
        '<p class="subtitle">Rendered from <code>docs/restructure/IDEAS.md</code> &middot; '
        "a READ view. The markdown file is the system of record — capture and edit there, "
        "then re-render. Nothing here is committed to until it is groomed into "
        "<code>backlog.yaml</code> with an id, acceptance test, and owner agent.</p>\n"
        '<p class="subtitle"><strong>INTERNAL</strong> — the inbox carries unreviewed notes '
        "(PUBLISH-BOUNDARY.md).</p>\n"
        f'<div class="ideas-body">\n{body}\n</div>\n'
        "</body></html>\n"
    )


def write_ideas(
    ideas_path: str | Path = DEFAULT_IDEAS_PATH,
    out_path: str | Path = DEFAULT_IDEAS_OUT_PATH,
) -> Path:
    """Load ``ideas_path``, render it, write the HTML to ``out_path``. Returns the path."""
    markdown = Path(ideas_path).read_text(encoding="utf-8")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ideas(markdown), encoding="utf-8")
    return out_path
