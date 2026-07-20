"""design_doc.py — deterministic Markdown → HTML renderer for DryDocs design docs (Epic L / L3).

drydocs-docgen. The doc `.md` is the SINGLE SOURCE OF TRUTH; this renders it to ONE
self-contained HTML surface, ``<stem>.html``:

  * on screen — theme-aware read column (dark/light) + the L5 annotate/save layer;
  * under ``@media print`` — black-on-white Letter pages carrying the L6 print-margin
    anchor tags + the Rev/commit footer (the same sheet headless Chromium applies for
    the L4 ``.pdf`` step).

The former ``<stem>.print.html`` twin is retired (L13, 2026-07-18): it misrendered as a
browser surface, and everything it carried now lives in the single file's print rules —
so the hand-maintained parallel HTML stays retired and the file count is one. B2 by decision (2026-07-08): a stdlib
hand-rolled renderer over the doc SUBSET we author — headings, GFM tables, fenced code,
bold, inline code, links, blockquotes, ordered/unordered lists, and horizontal rules —
rather than a third-party markdown dependency. Zero runtime deps keeps determinism
INTRINSIC (no library version to drift) and matches the repo's existing hand-built-HTML
pattern (plan_board.py, gate_pages.py).

ANCHORS: an ``<!-- anchor: id -->`` comment immediately before a block attaches
``id="id"`` to that block's element. This is the stable id namespace the outline
(doc_outline.py) validates, the traceability matrix keys on, and HITL feedback re-attaches
to. The comment itself never renders.

Rendering is DETERMINISTIC: given the same ``.md`` it always produces byte-identical HTML
— no build timestamps, no randomness. The doc's own front matter carries Rev/date, so the
render carries no build time. classification: Internal-Public (generic renderer; the docs
it renders carry their own classification in their front matter).
"""
from __future__ import annotations

import html
import re
from pathlib import Path

# ── inline formatting ────────────────────────────────────────────────────────
_CODE_SPAN = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
# italic: single asterisks hugging non-space content (won't match `a * b` or a lone `*`)
_ITALIC = re.compile(r"\*(\S(?:[^*\n]*\S)?)\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_PLACEHOLDER = re.compile(r"\x00(\d+)\x00")


def _inline(text: str) -> str:
    """Render inline markdown in a run of text (code spans, bold, links) — escaped."""
    codes: list[str] = []

    def _protect(m: re.Match[str]) -> str:
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    text = _CODE_SPAN.sub(_protect, text)          # 1. pull code spans out
    text = html.escape(text)                       # 2. escape everything else
    text = _BOLD.sub(r"<strong>\1</strong>", text)  # 3. bold
    text = _ITALIC.sub(r"<em>\1</em>", text)        # 3b. italic
    text = _LINK.sub(                              # 4. links
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', text
    )
    text = _PLACEHOLDER.sub(lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)  # 5. restore
    return text


# ── block helpers ──────────────────────────────────────────────────────────────
_ANCHOR = re.compile(r"^<!--\s*anchor:\s*([a-z0-9][a-z0-9-]*)\s*-->$", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
_LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
_TABLE_SEP = re.compile(r"^\|?[\s:|-]+\|?$")


def _with_id(block_html: str, block_id: str | None) -> str:
    """Inject ``id="..."`` into the first opening tag of ``block_html``."""
    if not block_id:
        return block_html
    return re.sub(
        r"^(<[a-zA-Z][a-zA-Z0-9]*)",
        rf'\1 id="{html.escape(block_id, quote=True)}"',
        block_html,
        count=1,
    )


def _is_table_sep(line: str) -> bool:
    s = line.strip()
    return bool(_TABLE_SEP.match(s)) and "-" in s and "|" in s


def _parse_fence(lines: list[str], start: int) -> tuple[str, int]:
    lang = lines[start].strip()[3:].strip()
    body: list[str] = []
    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        body.append(lines[i])
        i += 1
    i += 1  # consume the closing ```
    code = html.escape("\n".join(body))
    cls = f' class="{html.escape(lang, quote=True)}"' if lang else ""
    return f"<pre{cls}><code>{code}</code></pre>", i


def _parse_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
        i += 1
    header, data = rows[0], rows[2:]  # rows[1] is the |---| separator
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out.append("</tr></thead>")
    if data:
        out.append("<tbody>")
        for r in data:
            out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
        out.append("</tbody>")
    out.append("</table>")
    return "".join(out), i


def _build_nested(items: list[tuple[int, bool, str]]) -> str:
    """Flat (indent, ordered, text) items -> nested <ul>/<ol> HTML."""
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent, tag)
    for indent, ordered, text in items:
        tag = "ol" if ordered else "ul"
        if stack and indent > stack[-1][0]:
            out.append(f"<{tag}>")
            stack.append((indent, tag))
            out.append(f"<li>{_inline(text)}")
        else:
            while stack and stack[-1][0] > indent:
                _, t = stack.pop()
                out.append(f"</li></{t}>")
            if stack and stack[-1][0] == indent:
                out.append(f"</li><li>{_inline(text)}")
            else:
                out.append(f"<{tag}>")
                stack.append((indent, tag))
                out.append(f"<li>{_inline(text)}")
    while stack:
        _, t = stack.pop()
        out.append(f"</li></{t}>")
    return "".join(out)


def _parse_list(lines: list[str], start: int) -> tuple[str, int]:
    items: list[tuple[int, bool, str]] = []
    i = start
    while i < len(lines):
        m = _LIST_ITEM.match(lines[i])
        if m:
            items.append((len(m.group(1)), m.group(2).endswith("."), m.group(3)))
            i += 1
        elif lines[i].strip() and items and (len(lines[i]) - len(lines[i].lstrip())) > items[-1][0]:
            # indented continuation of the current item
            items[-1] = (items[-1][0], items[-1][1], items[-1][2] + " " + lines[i].strip())
            i += 1
        else:
            break
    return _build_nested(items), i


def _parse_blockquote(lines: list[str], start: int) -> tuple[str, int]:
    inner: list[str] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        stripped = lines[i].lstrip()[1:]
        inner.append(stripped[1:] if stripped.startswith(" ") else stripped)
        i += 1
    return f"<blockquote>{render_body(chr(10).join(inner))}</blockquote>", i


# ── the block renderer ───────────────────────────────────────────────────────
def render_body(md: str) -> str:
    """Render the markdown subset to an HTML fragment (no <html>/<head> wrapper)."""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    pending_id: str | None = None
    i, n = 0, len(lines)

    def flush_para() -> None:
        nonlocal para, pending_id
        if para:
            out.append(_with_id(f"<p>{_inline(' '.join(para))}</p>", pending_id))
            pending_id = None
            para = []

    while i < n:
        line = lines[i]
        s = line.strip()

        am = _ANCHOR.match(s)
        if am:
            flush_para()
            pending_id = am.group(1).lower()
            i += 1
            continue
        if s.startswith("<!--") and s.endswith("-->"):  # non-anchor comment: drop
            flush_para()
            i += 1
            continue
        if s == "":
            flush_para()
            i += 1
            continue
        if s.startswith("```"):
            flush_para()
            block, i = _parse_fence(lines, i)
            out.append(_with_id(block, pending_id))
            pending_id = None
            continue
        hm = _HEADING.match(s)
        if hm:
            flush_para()
            level = len(hm.group(1))
            out.append(_with_id(f"<h{level}>{_inline(hm.group(2))}</h{level}>", pending_id))
            pending_id = None
            i += 1
            continue
        if _HR.match(s):
            flush_para()
            out.append(_with_id("<hr>", pending_id))
            pending_id = None
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and _is_table_sep(lines[i + 1]):
            flush_para()
            block, i = _parse_table(lines, i)
            out.append(_with_id(block, pending_id))
            pending_id = None
            continue
        if s.startswith(">"):
            flush_para()
            block, i = _parse_blockquote(lines, i)
            out.append(_with_id(block, pending_id))
            pending_id = None
            continue
        if _LIST_ITEM.match(line):
            flush_para()
            block, i = _parse_list(lines, i)
            out.append(_with_id(block, pending_id))
            pending_id = None
            continue
        para.append(s)
        i += 1

    flush_para()
    return "\n".join(out)


# ── document wrappers ────────────────────────────────────────────────────────
def doc_title(md: str) -> str:
    """The first H1's text, stripped of inline markdown; fallback 'Design document'."""
    for line in md.splitlines():
        m = _HEADING.match(line.strip())
        if m and len(m.group(1)) == 1:
            return re.sub(r"[`*]", "", m.group(2)).strip()
    return "Design document"


_SCREEN_CSS = """\
:root { color-scheme: light dark; --ink:#1a1a1a; --mid:#555; --line:#d0d0d0; --faint:#f6f6f6; --bg:#fff; --link:#0a58ca; }
@media (prefers-color-scheme: dark) { :root { --ink:#e6e6e6; --mid:#a0a0a0; --line:#3a3a3a; --faint:#1c1c1c; --bg:#141414; --link:#6ea8fe; } }
:root[data-theme="dark"] { --ink:#e6e6e6; --mid:#a0a0a0; --line:#3a3a3a; --faint:#1c1c1c; --bg:#141414; --link:#6ea8fe; }
:root[data-theme="light"] { --ink:#1a1a1a; --mid:#555; --line:#d0d0d0; --faint:#f6f6f6; --bg:#fff; --link:#0a58ca; }
* { box-sizing: border-box; }
body { font: 15px/1.6 "Segoe UI", system-ui, Arial, sans-serif; color: var(--ink); background: var(--bg); margin: 0; }
main { max-width: 900px; margin: 0 auto; padding: 32px 24px 80px; }
h1 { font-size: 28px; margin: 0 0 6px; letter-spacing:-0.3px; }
h2 { font-size: 20px; margin: 34px 0 10px; padding-bottom:5px; border-bottom: 2px solid var(--ink); }
h3 { font-size: 16px; margin: 22px 0 8px; }
h4,h5,h6 { font-size: 14px; margin: 16px 0 6px; }
p { margin: 10px 0; } strong { font-weight: 700; }
a { color: var(--link); } a:hover { text-decoration: underline; }
code { font-family: "Cascadia Mono","Consolas",monospace; font-size: 0.88em; background: var(--faint); padding: 1px 4px; border-radius: 3px; }
pre { font-family: "Cascadia Mono","Consolas",monospace; font-size: 12.5px; line-height:1.45; border:1px solid var(--line); background: var(--faint); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 14px 0; font-size: 13.5px; display:block; overflow-x:auto; }
th,td { border:1px solid var(--line); padding: 6px 9px; text-align:left; vertical-align: top; }
th { background: var(--faint); font-weight:700; }
blockquote { margin: 14px 0; padding: 2px 16px; border-left: 4px solid var(--line); color: var(--mid); }
ul,ol { margin: 10px 0; padding-left: 26px; } li { margin: 4px 0; }
hr { border:none; border-top:1px solid var(--line); margin: 26px 0; }
:target { scroll-margin-top: 12px; } :target > :first-child, h2:target, h3:target { outline: 2px solid var(--link); outline-offset: 4px; }
.dd-margin-tag, .dd-print-footer { display: none; }
"""

# The print sheet (L13: an @media print block in the ONE html, not a second file). It
# reuses the crafted look from the prior hand-authored print.html, extended to cover the
# elements the generic renderer emits (lists / blockquote / links / h4-h6 / hr). Placed
# LAST in the merged stylesheet so its rules win over the screen rules at equal
# specificity; the variable block lists every theme selector the screen sheet uses so the
# light print palette beats both the OS dark scheme and the data-theme toggle.
_PRINT_MEDIA_CSS = """\
@page { size: Letter; margin: 0.6in 0.62in 0.55in 0.62in; }
@media print {
:root, :root[data-theme="dark"], :root[data-theme="light"] { color-scheme: light; --ink:#1a1a1a; --mid:#555; --line:#bdbdbd; --fill:#eee; --faint:#f6f6f6; --bg:#fff; --link:#0a58ca; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5px/1.45 "Segoe UI", system-ui, Arial, sans-serif; }
main { max-width: 7.2in; margin: 0 auto; padding: 0 0 0 0.62in; position: relative; }
h1 { font-size: 21px; margin: 0 0 2px; letter-spacing:-0.2px; }
h2 { font-size: 14px; margin: 16px 0 8px; padding-bottom:4px; border-bottom: 2px solid var(--ink); text-transform: uppercase; letter-spacing: 0.6px; }
h3 { font-size: 11.5px; margin: 13px 0 5px; padding-bottom:2px; border-bottom:1px solid var(--line); }
h4,h5,h6 { font-size: 10.5px; margin: 9px 0 4px; }
p { margin: 6px 0; }
a { color: inherit; text-decoration: underline; }
code { font-size: 9.2px; padding: 0 2px; border-radius: 2px; }
table { display: table; width:100%; margin: 7px 0; font-size: 9.1px; overflow-x: visible; }
th, td { padding: 3px 5px; }
th { background: var(--fill); }
td code, th code { background: transparent; padding: 0; }
pre { font-size: 8.4px; line-height: 1.35; padding: 7px 9px; margin: 7px 0; white-space: pre; overflow: hidden; border-radius: 3px; }
pre.sql { background:#fbfbfb; }
blockquote { margin: 7px 0; padding: 2px 10px; border-left: 3px solid var(--line); break-inside: avoid; }
ul,ol { margin: 6px 0 6px 16px; padding: 0; } li { margin: 3px 0; }
hr { margin: 10px 0; }
h2, h3, table, pre { break-inside: avoid; }

/* L6 paper HITL: each anchored block sits in the left gutter (main's own padding-left,
   reserved above) so a printed page carries the anchor id beside its section — no @page
   margin-box support required, so headless Chromium print-to-pdf renders it reliably. */
h1, h2, h3, h4, h5, h6, p, table, pre, ul, ol, blockquote { position: relative; }
.dd-margin-tag {
  display: block; position: absolute; left: -0.6in; top: 0.1em; width: 0.54in;
  font: 6.2px/1.15 "Cascadia Mono","Consolas",monospace; text-align: right;
  color: var(--mid); letter-spacing: 0.1px; word-break: break-word;
}
/* Rev/commit footer: `position: fixed` repeats on every printed page in Chromium's
   headless print-to-pdf (the standard running-footer technique) without needing CSS
   Paged-Media margin-box content(), which Chromium supports only partially. */
.dd-print-footer {
  display: block; position: fixed; left: 0.62in; right: 0.62in; bottom: 0.12in;
  font-size: 8px; color: var(--mid); text-align: center;
  border-top: 1px solid var(--line); padding-top: 3px;
}
}
"""


# ── L6: print-margin anchors + Rev/commit footer ────────────────────────────
# The paper HITL loop (Epic L / L6): the printed .html gets annotated by pen, scanned,
# and the transcribe-doc-markup skill re-attaches each pen note to a section anchor. That
# only works if the anchor id is VISIBLE on the printed page next to its section — so each
# anchored block carries a small tag for the page's left gutter, hidden on screen and
# shown only under @media print (L13: one file, two surfaces).
# `<hr>` is a void element (can't hold a child span) and is deliberately excluded; no anchor
# in the real TDD ever attaches to one (front-matter/headings/paragraphs only).
_MARGIN_TAG_OPEN = re.compile(
    r'(<(?:h[1-6]|p|table|pre|ul|ol|blockquote)\s+id="([a-zA-Z][\w-]*)"[^>]*>)'
)


def _inject_margin_anchors(body_html: str) -> str:
    """Tag each anchored block with its stable anchor id for the left print gutter
    (``.dd-margin-tag``: display:none on screen, positioned by ``_PRINT_MEDIA_CSS`` in
    print). Runs BEFORE ``_inject_subsection_anchors`` so only AUTHORED anchors get a
    printed gutter tag — the L11 derived ids stay screen-annotation-only. Pure string
    substitution on the already-rendered body — deterministic."""
    def _tag(m: re.Match[str]) -> str:
        opening, anchor = m.group(1), m.group(2)
        return f'{opening}<span class="dd-margin-tag" aria-hidden="true">{html.escape(anchor)}</span>'
    return _MARGIN_TAG_OPEN.sub(_tag, body_html)


_REV_RE = re.compile(r"\bRev\s+(\d+)\b")
_COMMIT_RE = re.compile(r"\bcommit\s+`([0-9a-fA-F]{6,40})`")
_REV_PLACEHOLDER = "Rev —"     # em dash: a doc that declares no Rev still gets a footer
_COMMIT_PLACEHOLDER = "—"


def doc_rev_footer(md: str) -> str:
    """The deterministic 'Rev N · commit <hash>' footer string. Derived STRICTLY from
    the doc's own declared front matter (the ``Rev N`` / `` `commit abc123` `` text an
    author writes in — see controlm-ingestion-tdd.md's front-matter anchor) — never from
    git state or a render-time timestamp, so the render stays byte-deterministic. A doc
    that declares neither gets the fixed placeholder, not an empty/blank footer."""
    rev_m = _REV_RE.search(md)
    commit_m = _COMMIT_RE.search(md)
    rev = f"Rev {rev_m.group(1)}" if rev_m else _REV_PLACEHOLDER
    commit = commit_m.group(1) if commit_m else _COMMIT_PLACEHOLDER
    return f"{rev} · commit {commit}"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "doc"


def feedback_yaml(doc_id: str, notes: dict[str, str]) -> str:
    """The CANONICAL anchor-keyed feedback format. The screen save-button's clipboard
    export (``_FEEDBACK_JS``) mirrors this byte-for-byte — keep the two in sync. Empty
    notes are skipped; multi-line notes use a YAML block scalar."""
    out = [
        f"# design-doc feedback — paste into docs/design/feedback/{doc_id}-rev<N>.yaml",
        f"doc: {doc_id}",
        "notes:",
    ]
    for anchor, note in notes.items():
        text = (note or "").replace("\r", "")
        if not text.strip():
            continue
        out.append(f"  - anchor: {anchor}")
        out.append("    note: |")
        out.extend(f"      {line}" for line in text.split("\n"))
    return "\n".join(out) + "\n"


# ── L11: derived subsection anchors (screen only) ────────────────────────────
# When an anchored section has MORE THAN TWO subsections (sub-headings one level down,
# or a numbered step list with 3+ top-level items), each subsection gets its own annotate
# control so feedback keys to the exact subsection. The derived id is
# ``<parent-anchor>--<slug-of-subsection-text>`` — CONTENT-derived, never positional, so a
# note on "1.b" survives someone inserting a new "1.a". Derived ids exist in the one html
# but never grow a printed gutter tag (margin tags are injected first, from authored
# anchors only) — the paper namespace and the doc_outline authored namespace stay intact.
# Consequence for authors: don't use ``--`` inside an authored anchor id — the double
# hyphen is reserved as the derived-anchor separator (see doc_outline.DERIVED_ANCHOR_SEP).
_SUB_SEP = "--"
_H_BLOCK = re.compile(r'^<h([1-6])(?:\s+id="([^"]+)")?>(.*)</h\1>$')
_OL_OPEN = re.compile(r'^<ol(?:\s+id="([^"]+)")?>')
_LIST_TOKEN = re.compile(r"<(/?)(ol|ul|li)(?:\s[^>]*)?>")
_ANY_TAG = re.compile(r"<[^>]+>")


def _strip_tags(fragment: str) -> str:
    return html.unescape(_ANY_TAG.sub("", fragment))


def _derived_id(parent: str, text: str, used: set[str]) -> str:
    """``parent--slug`` from the subsection's leading text; deduped deterministically."""
    words = _strip_tags(text).split()
    base = _slug(" ".join(words[:6]))[:40].strip("-") or "item"
    cand, n = base, 1
    while f"{parent}{_SUB_SEP}{cand}" in used:
        n += 1
        cand = f"{base}-{n}"
    full = f"{parent}{_SUB_SEP}{cand}"
    used.add(full)
    return full


def _li_lead_text(rest: str) -> str:
    """The item's own leading content: up to its first nested list or its close tag."""
    cut = len(rest)
    for stop in ("<ol", "<ul", "</li"):
        pos = rest.find(stop)
        if pos >= 0:
            cut = min(cut, pos)
    return rest[:cut]


def _inject_li_ids(ol_html: str, parent: str, used: set[str]) -> str:
    """Give each TOP-LEVEL <li> of a numbered list a derived id — only when the list has
    more than two top-level items (the L11 threshold)."""
    depth = 0
    positions: list[int] = []
    for m in _LIST_TOKEN.finditer(ol_html):
        closing, tag = m.group(1) == "/", m.group(2)
        if tag in ("ol", "ul"):
            depth += -1 if closing else 1
        elif tag == "li" and not closing and depth == 1:
            positions.append(m.start())
    if len(positions) <= 2:
        return ol_html
    out: list[str] = []
    last = 0
    for pos in positions:
        out.append(ol_html[last:pos])
        tag_end = ol_html.index(">", pos) + 1
        did = _derived_id(parent, _li_lead_text(ol_html[tag_end:]), used)
        out.append(f'<li id="{did}">')
        last = tag_end
    out.append(ol_html[last:])
    return "".join(out)


def _inject_subsection_anchors(body_html: str) -> str:
    """SCREEN-ONLY post-pass over the rendered body: derived ids for subsections of
    anchored sections (see the L11 block comment above). Pure string work on whole block
    lines — safe because the renderer emits each heading/list block as a single line and
    escapes markup inside code fences, so nothing inside a <pre> can false-match."""
    lines = body_html.split("\n")
    stack: list[tuple[str, int]] = []  # nearest anchored ancestors: (anchor, heading level)
    # (parent, level) -> {"total": all subheadings seen, "unanchored": their line indexes}
    heading_groups: dict[tuple[str, int], dict] = {}
    ol_candidates: list[tuple[int, str]] = []  # (line index, parent anchor)

    for idx, line in enumerate(lines):
        hm = _H_BLOCK.match(line)
        if hm:
            level, hid = int(hm.group(1)), hm.group(2)
            while stack and stack[-1][1] >= level:
                stack.pop()
            if stack:
                group = heading_groups.setdefault((stack[-1][0], level), {"total": 0, "unanchored": []})
                group["total"] += 1  # anchored subheadings count toward the >2 threshold
                if not hid:
                    group["unanchored"].append(idx)
            if hid:
                stack.append((hid, level))
            continue
        om = _OL_OPEN.match(line)
        if om:
            parent = om.group(1) or (stack[-1][0] if stack else None)
            if parent:
                ol_candidates.append((idx, parent))

    used: set[str] = set()
    for (parent, _level), group in heading_groups.items():
        if group["total"] > 2:
            for idx in group["unanchored"]:
                hm = _H_BLOCK.match(lines[idx])
                did = _derived_id(parent, hm.group(3), used)
                lines[idx] = f"<h{hm.group(1)} id=\"{did}\">{hm.group(3)}</h{hm.group(1)}>"
    for idx, parent in ol_candidates:
        lines[idx] = _inject_li_ids(lines[idx], parent, used)
    return "\n".join(lines)


# ── L10: the appendix "SME - Feedback" instruction panel (screen only) ───────
def sme_feedback_filename(doc_id: str, md: str) -> str:
    """The exact per-doc feedback filename, with the doc's declared Rev baked in
    (``controlm-ingestion-tdd-rev3.yaml``). Falls back to the ``rev<N>`` placeholder for a
    doc that declares no Rev — same front-matter source as ``doc_rev_footer``, so the
    render stays deterministic (no git/timestamp reads)."""
    m = _REV_RE.search(md)
    rev = m.group(1) if m else "<N>"
    return f"{doc_id}-rev{rev}.yaml"


def _sme_feedback_panel(doc_id: str, md: str) -> str:
    """Static HOW-TO block appended below the last section: walks the SME through
    annotate → copy → create-file → paste. Deliberately carries NO element ids, so the
    annotate layer never attaches controls to its own instructions."""
    fname = html.escape(sme_feedback_filename(doc_id, md))
    return (
        '<hr class="dd-sme-divider">\n'
        '<section class="dd-sme-feedback" aria-label="SME - Feedback">\n'
        "<h2>SME - Feedback</h2>\n"
        "<p>How to return your notes on this document:</p>\n"
        "<ol>\n"
        "<li>Click the <strong>✎</strong> button beside any section (or numbered step) and type "
        "your note — notes save in your browser as you type.</li>\n"
        "<li>When finished, click <strong>Copy feedback</strong> in the bottom-right toolbar. "
        "Your notes are copied as anchor-keyed YAML.</li>\n"
        "<li>Create the feedback file (it is YAML, <em>not</em> markdown) — "
        f"<strong>Copy To:</strong> <code>docs/design/feedback/</code> · "
        f"<strong>File Name:</strong> <code>{fname}</code></li>\n"
        "<li>Paste the copied block into that file, save, and commit (or send the file back "
        "to the team).</li>\n"
        "</ol>\n"
        "</section>"
    )


# HITL layer for the SCREEN surface only (@media print hides it). Static → deterministic.
_FEEDBACK_CSS = """
.dd-note-btn { border:1px solid var(--line); background:var(--bg); color:var(--mid); cursor:pointer; font-size:12px; line-height:1; padding:2px 6px; border-radius:5px; margin-right:6px; }
.dd-note-btn:hover { color:var(--link); border-color:var(--link); }
.dd-note-box { margin:6px 0 10px; }
.dd-note-box textarea { width:100%; min-height:56px; font:13px/1.4 "Segoe UI",system-ui,sans-serif; color:var(--ink); background:var(--faint); border:1px solid var(--line); border-radius:6px; padding:8px; resize:vertical; }
.dd-annotated { box-shadow:-3px 0 0 var(--link); padding-left:8px; }
.dd-fb-bar { position:fixed; right:16px; bottom:16px; display:flex; gap:8px; align-items:center; background:var(--bg); border:1px solid var(--line); border-radius:10px; padding:8px 12px; box-shadow:0 2px 10px rgba(0,0,0,.15); font-size:13px; z-index:50; }
.dd-fb-bar button { cursor:pointer; border:1px solid var(--link); background:var(--link); color:#fff; border-radius:6px; padding:5px 10px; font-size:13px; }
.dd-fb-bar .dd-badge { font-weight:700; }
.dd-toast { position:fixed; right:16px; bottom:64px; background:var(--ink); color:var(--bg); padding:8px 12px; border-radius:8px; font-size:13px; z-index:60; opacity:0; transition:opacity .2s; }
.dd-toast.show { opacity:1; }
.dd-sme-feedback ol li { margin: 6px 0; }
@media print { .dd-note-btn, .dd-note-box, .dd-fb-bar, .dd-toast, .dd-sme-feedback, .dd-sme-divider { display:none !important; } }
"""

_FEEDBACK_JS = r"""
(function(){
  var DOC="__DOCID__", KEY="drydocs-doc-feedback:"+DOC;
  function load(){ try{return JSON.parse(localStorage.getItem(KEY)||"{}");}catch(e){return {};} }
  function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }
  var state=load(), badge;
  function count(){ return Object.keys(state).filter(function(k){return (state[k]||"").trim();}).length; }
  function refresh(){ if(badge) badge.textContent=count(); }
  function toast(msg){ var t=document.createElement("div"); t.className="dd-toast"; t.textContent=msg; document.body.appendChild(t); requestAnimationFrame(function(){t.classList.add("show");}); setTimeout(function(){t.classList.remove("show"); setTimeout(function(){t.remove();},250);},1600); }
  function exportYaml(){
    var lines=["# design-doc feedback — paste into docs/design/feedback/"+DOC+"-rev<N>.yaml","doc: "+DOC,"notes:"];
    Object.keys(state).forEach(function(a){
      var note=(state[a]||"").replace(/\r/g,""); if(!note.trim()) return;
      lines.push("  - anchor: "+a); lines.push("    note: |");
      note.split("\n").forEach(function(l){ lines.push("      "+l); });
    });
    return lines.join("\n")+"\n";
  }
  function attach(el){
    var id=el.id;
    var btn=document.createElement("button"); btn.className="dd-note-btn"; btn.type="button"; btn.textContent="✎"; btn.title="Annotate #"+id;
    var box=document.createElement("div"); box.className="dd-note-box"; box.style.display=(state[id]||"").trim()?"block":"none";
    var ta=document.createElement("textarea"); ta.value=state[id]||""; ta.setAttribute("placeholder","note for #"+id+" …");
    ta.addEventListener("input",function(){ state[id]=ta.value; save(); refresh(); el.classList.toggle("dd-annotated", !!ta.value.trim()); });
    if((state[id]||"").trim()) el.classList.add("dd-annotated");
    box.appendChild(ta);
    btn.addEventListener("click",function(){ box.style.display=box.style.display==="none"?"block":"none"; if(box.style.display==="block") ta.focus(); });
    if(el.tagName==="LI"){ el.insertAdjacentElement("afterbegin", btn); el.appendChild(box); }
    else { el.insertAdjacentElement("afterend", box); el.insertAdjacentElement("beforebegin", btn); }
  }
  document.addEventListener("DOMContentLoaded",function(){
    document.querySelectorAll("main [id]").forEach(attach);
    var bar=document.createElement("div"); bar.className="dd-fb-bar";
    var lbl=document.createElement("span"); lbl.innerHTML='notes <span class="dd-badge">0</span>'; badge=lbl.querySelector(".dd-badge");
    var ex=document.createElement("button"); ex.type="button"; ex.textContent="Copy feedback";
    ex.addEventListener("click",function(){ var y=exportYaml();
      var done=function(){toast("feedback copied — paste into docs/design/feedback/");};
      if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(y).then(done,function(){fallback(y);}); } else { fallback(y); }
    });
    function fallback(y){ var t=document.createElement("textarea"); t.value=y; document.body.appendChild(t); t.select(); try{document.execCommand("copy"); toast("feedback copied");}catch(e){toast("copy failed — select the box");} t.remove(); }
    bar.appendChild(lbl); bar.appendChild(ex); document.body.appendChild(bar); refresh();
  });
})();
"""


def _feedback_html(doc_id: str) -> str:
    return f"<script>\n{_FEEDBACK_JS.replace('__DOCID__', doc_id)}\n</script>"


def render_doc(md: str, doc_id: str | None = None) -> str:
    """Render the full self-contained HTML document — ONE surface for both uses (L13).
    On screen: theme-aware, with the HITL annotate/save layer (per-anchor localStorage
    note + a clipboard export in the ``feedback_yaml`` format). Under ``@media print``:
    the black-on-white Letter layout with the L6 margin anchor tags and the Rev/commit
    footer; the annotate layer and SME panel are print-hidden by CSS."""
    css = _SCREEN_CSS + _FEEDBACK_CSS + _PRINT_MEDIA_CSS
    title = html.escape(doc_title(md))
    doc_id = doc_id or _slug(doc_title(md))
    body = render_body(md)
    # Order matters: L6 margin tags FIRST (authored anchors only — a derived id must
    # never reach the printed gutter), THEN the L11 derived subsection anchors, THEN the
    # L10 panel — whose own numbered steps must never grow annotate controls.
    body = _inject_margin_anchors(body)
    body = _inject_subsection_anchors(body)
    body = f"{body}\n{_sme_feedback_panel(doc_id, md)}"
    footer = f'<footer class="dd-print-footer">{html.escape(doc_rev_footer(md))}</footer>\n'
    did = html.escape(doc_id, quote=True)
    feedback = _feedback_html(did)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n<style>\n{css}</style>\n</head>\n<body>\n"
        f"<main>\n{body}\n</main>\n{footer}{feedback}\n</body>\n</html>\n"
    )


def write_doc(md_path: str | Path, out_dir: str | Path | None = None) -> Path:
    """Render ``md_path`` to its single ``<stem>.html`` surface; return the path."""
    md_path = Path(md_path)
    md = md_path.read_text(encoding="utf-8")
    out_dir = Path(out_dir) if out_dir else md_path.parent
    html_path = out_dir / f"{md_path.stem}.html"
    html_path.write_text(render_doc(md, doc_id=md_path.stem), encoding="utf-8")
    return html_path
