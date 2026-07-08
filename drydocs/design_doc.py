"""design_doc.py — deterministic Markdown → HTML renderer for DryDocs design docs (Epic L / L3).

drydocs-docgen. The doc `.md` is the SINGLE SOURCE OF TRUTH; this renders it to two
self-contained HTML surfaces:

  * ``<stem>.html``        — screen read surface (theme-aware, max-width column)
  * ``<stem>.print.html``  — print/PDF surface (Letter @page, page-friendly type)

so the hand-maintained parallel HTML is retired. B2 by decision (2026-07-08): a stdlib
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
"""

# Print CSS reuses the crafted look from the prior hand-authored print.html, extended to
# cover the elements the generic renderer emits (lists / blockquote / links / h4-h6 / hr).
_PRINT_CSS = """\
:root { --ink:#1a1a1a; --mid:#555; --line:#bdbdbd; --fill:#eee; --faint:#f6f6f6; }
@page { size: Letter; margin: 0.6in 0.62in 0.55in 0.62in; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5px/1.45 "Segoe UI", system-ui, Arial, sans-serif; color: var(--ink); margin: 0; }
main { max-width: 7.2in; margin: 0 auto; }
h1 { font-size: 21px; margin: 0 0 2px; letter-spacing:-0.2px; }
h2 { font-size: 14px; margin: 16px 0 8px; padding-bottom:4px; border-bottom: 2px solid var(--ink); text-transform: uppercase; letter-spacing: 0.6px; }
h3 { font-size: 11.5px; margin: 13px 0 5px; padding-bottom:2px; border-bottom:1px solid var(--line); }
h4,h5,h6 { font-size: 10.5px; margin: 9px 0 4px; }
p { margin: 6px 0; } strong { font-weight: 700; }
a { color: inherit; text-decoration: underline; }
code { font-family: "Cascadia Mono","Consolas",monospace; font-size: 9.2px; background: var(--faint); padding: 0 2px; border-radius: 2px; }
table { width:100%; border-collapse: collapse; margin: 7px 0; font-size: 9.1px; }
th, td { border: 1px solid var(--line); padding: 3px 5px; text-align: left; vertical-align: top; }
th { background: var(--fill); font-weight: 700; }
td code, th code { background: transparent; padding: 0; }
pre { font-family: "Cascadia Mono","Consolas",monospace; font-size: 8.4px; line-height: 1.35; border: 1px solid var(--line); background: var(--faint); padding: 7px 9px; margin: 7px 0; white-space: pre; overflow: hidden; border-radius: 3px; }
pre.sql { background:#fbfbfb; } pre code { background:none; padding:0; }
blockquote { margin: 7px 0; padding: 2px 10px; border-left: 3px solid var(--line); color: var(--mid); break-inside: avoid; }
ul,ol { margin: 6px 0 6px 16px; padding: 0; } li { margin: 3px 0; }
hr { border:none; border-top:1px solid var(--line); margin: 10px 0; }
h2, h3, table, pre { break-inside: avoid; }
"""


def render_doc(md: str, mode: str = "screen") -> str:
    """Render a full self-contained HTML document. ``mode`` is 'screen' or 'print'."""
    css = _PRINT_CSS if mode == "print" else _SCREEN_CSS
    title = html.escape(doc_title(md))
    body = render_body(md)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n<style>\n{css}</style>\n</head>\n<body>\n"
        f"<main>\n{body}\n</main>\n</body>\n</html>\n"
    )


def write_doc(md_path: str | Path, out_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Render ``md_path`` to ``<stem>.html`` + ``<stem>.print.html``; return their paths."""
    md_path = Path(md_path)
    md = md_path.read_text(encoding="utf-8")
    out_dir = Path(out_dir) if out_dir else md_path.parent
    html_path = out_dir / f"{md_path.stem}.html"
    print_path = out_dir / f"{md_path.stem}.print.html"
    html_path.write_text(render_doc(md, "screen"), encoding="utf-8")
    print_path.write_text(render_doc(md, "print"), encoding="utf-8")
    return html_path, print_path
