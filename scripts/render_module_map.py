"""Render MODULE_MAP.md's component-map section from ``drydocs_core.component_map`` (ADR 0018 D1).

The section between ``<!-- component-map:begin -->`` and ``<!-- component-map:end -->`` is a
RENDER (J43: derived, never carried): one row per component - group, backlog module, id series,
the dotted prefixes the boundary test classifies by - and one row per owned non-Python surface.
``tests/unit/test_module_map_render.py`` fails when the committed section differs from a fresh
render, the same drift guard every other committed render has. The prose around the markers,
and the per-row history tables below it, stay hand-written: this renders the DECLARATION, the
tables carry the STORY.

Stdlib + ``drydocs_core.component_map`` + PyYAML (for ``modules.yaml`` ``series:``).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from drydocs_core.component_map import (  # noqa: E402
    COMPONENT_GROUPS,
    COMPONENT_MODULE,
    CORE_MODULE,
    CORE_PREFIXES,
    NON_PYTHON_MODULES,
    SURFACE_OWNERS,
)

MODULE_MAP = REPO_ROOT / "MODULE_MAP.md"
MODULES_YAML = REPO_ROOT / "docs" / "restructure" / "backlog" / "modules.yaml"
BEGIN = "<!-- component-map:begin -->"
END = "<!-- component-map:end -->"


def _series() -> dict[str, str]:
    import yaml

    doc = yaml.safe_load(MODULES_YAML.read_text(encoding="utf-8")) or {}
    return dict(doc.get("series") or {})


def render_section() -> str:
    series = _series()
    lines = [
        BEGIN,
        "_Rendered from `drydocs_core/component_map.py` by `scripts/render_module_map.py`;"
        " do not edit by hand (ADR 0018 D1). The tables further down carry each row's history._",
        "",
        "| Component | Backlog module | Series | Dotted prefixes (the boundary test classifies by these) |",
        "|---|---|---|---|",
        f"| core | `{CORE_MODULE}` | `{series.get(CORE_MODULE, '?')}` | "
        + ", ".join(f"`{p}`" for p in CORE_PREFIXES)
        + " |",
    ]
    for group, prefixes in COMPONENT_GROUPS.items():
        module = COMPONENT_MODULE[group]
        lines.append(
            f"| {group} | `{module}` | `{series.get(module, '?')}` | "
            + ", ".join(f"`{p}`" for p in prefixes)
            + " |"
        )
    lines += [
        "",
        "| Owned surface (no Python package root) | Owning module |",
        "|---|---|",
    ]
    for directory, module in sorted(SURFACE_OWNERS.items()):
        lines.append(f"| `{directory}/` | `{module}` |")
    lines += [
        "",
        "Work-area and non-Python modules (own no package): "
        + ", ".join(f"`{m}`" for m in sorted(NON_PYTHON_MODULES))
        + ".",
        END,
    ]
    return "\n".join(lines)


def splice(text: str, section: str) -> str:
    i = text.index(BEGIN)
    j = text.index(END) + len(END)
    return text[:i] + section + text[j:]


def main() -> int:
    text = MODULE_MAP.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{MODULE_MAP.name}: markers {BEGIN} / {END} not found")
    out = splice(text, render_section())
    if out != text:
        MODULE_MAP.write_text(out, encoding="utf-8", newline="\n")
        print(f"wrote {MODULE_MAP}")
    else:
        print(f"{MODULE_MAP.name}: component-map section already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
