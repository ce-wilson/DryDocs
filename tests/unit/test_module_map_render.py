"""MODULE_MAP.md's component-map section is a RENDER of drydocs_core.component_map (ADR 0018 D1).

Two guards. (1) Drift: the committed section equals a fresh render - the same rule every
committed render carries (J43). (2) Completeness: every dotted prefix the map declares is
named somewhere in MODULE_MAP.md's hand-written tables, so the story cannot silently omit a
component the declaration knows about. The reverse - a hand row naming a module the map does
not classify - is the boundary test's default-deny, not this file's.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_MAP = REPO_ROOT / "MODULE_MAP.md"


def _renderer():
    spec = importlib.util.spec_from_file_location(
        "render_module_map", REPO_ROOT / "scripts" / "render_module_map.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_committed_component_map_section_matches_a_fresh_render() -> None:
    r = _renderer()
    text = MODULE_MAP.read_text(encoding="utf-8")
    assert r.BEGIN in text and r.END in text, "MODULE_MAP.md lost its component-map markers"
    committed = text[text.index(r.BEGIN) : text.index(r.END) + len(r.END)]
    assert committed == r.render_section(), (
        "MODULE_MAP.md's component-map section is stale - run "
        "`poetry run python scripts/render_module_map.py` and commit the result"
    )


def test_every_declared_prefix_is_told_in_the_hand_tables() -> None:
    """The render says WHAT; the hand tables say WHY. A prefix with no story is a gap."""
    from drydocs_core.component_map import COMPONENT_GROUPS, CORE_PREFIXES

    r = _renderer()
    text = MODULE_MAP.read_text(encoding="utf-8")
    story = text.replace(text[text.index(r.BEGIN) : text.index(r.END) + len(r.END)], "")
    missing = []
    for prefix in (*CORE_PREFIXES, *(p for ps in COMPONENT_GROUPS.values() for p in ps)):
        # a prefix is told by its dotted name, its path form (drydocs/review/, drydocs_core/),
        # or its file name (the cli_*.py row lists six basenames in one cell)
        as_path = prefix.replace(".", "/")
        basename = prefix.rsplit(".", 1)[-1]
        if (
            prefix in story
            or as_path in story
            or f"{basename}.py" in story
            or f"{basename}/" in story
        ):
            continue
        missing.append(prefix)
    assert not missing, (
        f"declared in drydocs_core/component_map.py but told nowhere in MODULE_MAP.md's "
        f"tables: {missing}. Add the row (what it is, which component, what it writes)."
    )


def test_the_renderer_is_deterministic() -> None:
    r = _renderer()
    assert r.render_section() == r.render_section()
    assert r.splice(f"head\n{r.BEGIN}\nold\n{r.END}\ntail", "NEW") == "head\nNEW\ntail"
