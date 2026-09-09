"""Guards for the O90 wiring key — the cross of `confirmed` and loader presence.

THE FAILURE THIS EXISTS TO CATCH is not a wrong colour. It is the key drifting
into a RULING. The distinction that makes O90 buildable at all is narrow: a
registry FIELD asserting pipeline-wiring readiness is gate territory (N10 drafted
config/gate-prompts/registry-wiring-readiness.yaml and it is unsigned), while
CROSSING two fields the registry already records separately is reporting. If a
`wired:` key ever appears in the registry sources, this key stopped reporting and
started asserting, and that must fail loudly rather than ship quietly.

AMENDED 2026-09-09 (CFG13). The gate signed - registry-wiring-readiness 18/18, with
source-descriptor-axes 13/13 in the same sitting - and ruled the fact a SIXTH
DESCRIPTOR AXIS, `wired`, declared per side with a reason. So the load-map row for a
registry-home dataset now CARRIES that declaration and the cross reads it. What stays
forbidden is what was always forbidden: a wiring field on the REGISTRY row itself.

The second failure is divergence. The same cross renders on two surfaces — the
console (web/src/loadmap/loadMapModel.ts) and N5's paper surface
(docs/plan/load-map.html) — and a key that disagrees between screen and print is
worse than no key, because a marked-up printout would cite a state the screen
never showed.

Static by necessity, for the reason test_load_map_console.py records: the console
has no JS runner in this suite, so the TS side is asserted by reading its source.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from drydocs_core.source_descriptors import SourceDescriptors

REPO = Path(__file__).resolve().parents[2]
LOAD_MAP = REPO / "web" / "src" / "generated" / "load-map.json"
PRINT_HTML = REPO / "docs" / "plan" / "load-map.html"
MODEL_TS = REPO / "web" / "src" / "loadmap" / "loadMapModel.ts"
RENDERER = REPO / "scripts" / "render_load_map.py"
REGISTRY_YAML = REPO / "config" / "source-registry.yaml"

STATE_IDS = ("wired", "planned", "awaiting", "registered")


def _sources() -> list[dict]:
    return json.loads(LOAD_MAP.read_text(encoding="utf-8"))["sources"]


def _state(source: dict) -> str:
    # the declared fact where the row carries one (CFG13); loader presence where not
    built = source["wired"] if "wired" in source else bool(source["loaders"])
    if source["confirmed"]:
        return "wired" if built else "planned"
    return "awaiting" if built else "registered"


def _census() -> dict[str, int]:
    out = dict.fromkeys(STATE_IDS, 0)
    for s in _sources():
        out[_state(s)] += 1
    return out


def test_the_key_reports_and_never_rules() -> None:
    """The wiring fact lives on the descriptor axis, never on the registry row.

    AMENDED 2026-09-09 by the ruling (registry-wiring-readiness D3, SIGNED 18/18;
    source-descriptor-axes B1/B2): the sixth axis `wired` is DECLARED per side in
    config/source-descriptors.yaml, so a load-map row for a registry-home dataset
    CARRIES that declaration, verbatim, and the cross reads it. Three things are
    pinned. A REGISTRY row (config/source-registry.yaml datasets[]) still carries
    none of the four names - there it would overload `confirmed` again, which is
    the conflation the gate ended. Every registry-home load-map row carries the
    descriptor's value and reason, unchanged - the renderer copies, it does not
    decide. And a doc-ledger row, which no descriptor answers for, carries no
    `wired` key at all - the cross falls back to loader presence there, as O90
    built it, and a key that appeared on one would be a value nobody declared.
    """
    forbidden = {"wired", "wiring", "wiring_state", "ready"}
    registry = yaml.safe_load(REGISTRY_YAML.read_text(encoding="utf-8"))
    for row in registry["datasets"]:
        overlap = forbidden & set(row)
        assert not overlap, (
            f"registry row {row['id']} carries {sorted(overlap)} - the wiring fact's home is "
            "the descriptor's sixth axis (config/source-descriptors.yaml wired:), ruled "
            "2026-09-09; a field on the registry row overloads `confirmed` again."
        )
    descriptors = SourceDescriptors.from_yaml()
    for s in _sources():
        if s["home"] == "source-registry":
            declared, reason = descriptors.wired(s["id"])
            assert s.get("wired") == declared and s.get("wired_reason") == reason, (
                f"load-map row {s['id']} does not carry the descriptor's declaration "
                f"({declared!r}, {reason!r}) - re-run scripts/render_load_map.py"
            )
        else:
            assert (
                "wired" not in s and "wired_reason" not in s
            ), f"doc-ledger row {s['id']} carries a wiring value nobody declared"


def test_both_axes_are_really_independent() -> None:
    """Every one of the four cells is occupied.

    If a cell empties, the cross has collapsed into one of its inputs and the
    key is dressing up a boolean. That is a real possibility — three of the four
    cells were within a couple of rows of empty when this was built — so the
    assertion is on occupancy, not on counts, which move constantly.
    """
    census = _census()
    empty = [k for k, v in census.items() if v == 0]
    assert not empty, (
        f"wiring cells {empty} are empty, so `confirmed` and loader presence no "
        f"longer vary independently: {census}"
    )
    assert sum(census.values()) == len(_sources())


def test_the_print_surface_carries_the_key_and_agrees_with_the_data() -> None:
    """N5's paper surface renders the legend, and its counts come from the rows."""
    html = PRINT_HTML.read_text(encoding="utf-8")
    assert "Wiring key" in html, "docs/plan/load-map.html lost the O90 legend"

    census = _census()
    for state, count in census.items():
        label = {
            "wired": "wired",
            "planned": "planned",
            "awaiting": "built, awaiting gate",
            "registered": "registered",
        }[state]
        needle = f'wr-{state}">{label}</span>&thinsp;{count}'
        assert needle in html, (
            f"legend count for {state!r} is not {count} in the rendered page — "
            "re-run scripts/render_load_map.py; a hand-typed count is the defect."
        )

    # One chip per source row, plus the legend's own four.
    chips = re.findall(r"chip wr-([a-z]+)", html)
    assert len(chips) == len(_sources()) + len(STATE_IDS)


def test_screen_and_paper_use_the_same_labels() -> None:
    """The two renderers state the same four cells, in the same words.

    Divergence here is the quiet failure: a printout would cite a state the
    console never showed, and a reviewer's note could not re-attach.
    """
    ts = MODEL_TS.read_text(encoding="utf-8")
    py = RENDERER.read_text(encoding="utf-8")
    for label in ("wired", "planned", "built, awaiting gate", "registered"):
        assert f"'{label}'" in ts or f'"{label}"' in ts, f"console lost the {label!r} label"
        assert f'"{label}"' in py, f"print renderer lost the {label!r} label"
