#!/usr/bin/env python3
"""Deterministic wireframe renderer — DryDocs SME review set.

Stdlib only (json, html, pathlib): runs anywhere Python 3.9+ exists, no repo
deps, no network, no graph. Same spec in → byte-identical SVG out (the
governed-render idiom: SME feedback cites element KEYS, which re-attach to
label/data/React/Cypher through KEYS.md).

Usage:
    python render_wireframes.py [spec.json] [out_dir]
Defaults: wireframes.json next to this script; out_dir = ./out
Outputs: <view>.svg per view + KEYS.md (key → label source / data / react / graph).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

INK = "#111a26"
MUT = "#48566c"
EDGE = "#94a3b8"
BG = "#f4f6f9"
PANEL = "#ffffff"
KEYBG = "#2e6bc4"
ACCENT = "#bd1f43"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def el_svg(e: dict) -> list[str]:
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    kind = e.get("type", "box")
    dash = ' stroke-dasharray="6 4"' if kind in ("text", "chip", "meter") else ""
    rx = 18 if kind in ("chip", "meter") else 6
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.4"{dash}/>'
    ]
    # key tag
    out.append(
        f'<rect x="{x}" y="{y - 16}" width="{9 * len(e["key"]) + 10}" height="18" rx="4" fill="{KEYBG}"/>'
    )
    out.append(
        f'<text x="{x + 5}" y="{y - 3}" font-family="monospace" font-size="12" fill="#ffffff">{esc(e["key"])}</text>'
    )
    # label, wrapped
    ty = y + 20
    for line in wrap(e["label"], max(24, int(w / 7.5)))[:4]:
        out.append(
            f'<text x="{x + 12}" y="{ty}" font-family="sans-serif" font-size="13" fill="{INK}">{esc(line)}</text>'
        )
        ty += 17
    # list items
    for it in e.get("items", []):
        out.append(f'<circle cx="{x + 22}" cy="{ty - 4}" r="3" fill="{MUT}"/>')
        out.append(
            f'<text x="{x + 34}" y="{ty}" font-family="sans-serif" font-size="12.5" fill="{MUT}">{esc(it)}</text>'
        )
        ty += 21
    if kind == "meter":
        out.append(
            f'<rect x="{x + 12}" y="{y + h - 12}" width="{w - 90}" height="6" rx="3" fill="#e3e9f0"/>'
        )
        out.append(
            f'<rect x="{x + 12}" y="{y + h - 12}" width="{int((w - 90) * 0.75)}" height="6" rx="3" fill="{ACCENT}"/>'
        )
    return out


def render_view(v: dict, meta: dict) -> str:
    cw, ch = v.get("canvas", [1280, 800])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" font-family="sans-serif">',
        f'<rect width="{cw}" height="{ch}" fill="{BG}"/>',
        f'<text x="20" y="{ch - 34}" font-size="15" font-weight="bold" fill="{INK}">{esc(v["title"])}</text>',
        f'<text x="20" y="{ch - 14}" font-family="monospace" font-size="11" fill="{MUT}">'
        f'{esc(v["route"])} · wireframe spec v{esc(meta["spec_version"])} · {esc(meta["date"])} · {esc(meta["source_branch"])} · keys resolve in KEYS.md</text>',
    ]
    for e in v["elements"]:
        parts.extend(el_svg(e))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_keys(spec: dict) -> str:
    m = spec["meta"]
    out = [
        f"# Wireframe keys — {m['title']}",
        "",
        f"Spec v{m['spec_version']} · {m['date']} · branch `{m['source_branch']}`.",
        f"Convention: {m['key_convention']}",
        "",
        "## Feedback addressed",
        "",
    ]
    for fb in m.get("feedback_addressed", []):
        out.append(f"- **{fb['id']}** — \"{fb['text']}\" → {fb['disposition']}")
    for v in spec["views"]:
        out += [
            "",
            f"## {v['title']} (`{v['route']}`)",
            "",
            "| Key | Label / element | Data source | React component | Graph / Cypher |",
            "|---|---|---|---|---|",
        ]
        for e in v["elements"]:
            mt = e.get("meta", {})
            out.append(
                "| `{}` | {} | {} | `{}` | `{}` |".format(
                    e["key"],
                    e["label"].replace("|", "\\|"),
                    mt.get("data", ""),
                    mt.get("react", ""),
                    mt.get("graph", ""),
                )
            )
    return "\n".join(out) + "\n"


def main() -> None:
    here = Path(__file__).resolve().parent
    spec_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "wireframes.json"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for v in spec["views"]:
        p = out_dir / f"{v['id']}.svg"
        p.write_text(render_view(v, spec["meta"]), encoding="utf-8")
        print(f"wrote {p}")
    k = out_dir / "KEYS.md"
    k.write_text(render_keys(spec), encoding="utf-8")
    print(f"wrote {k}")


if __name__ == "__main__":
    main()
