"""Guards for the O90 wiring key — the cross of `confirmed` and loader presence.

THE FAILURE THIS EXISTS TO CATCH is not a wrong colour. It is the key drifting
into a RULING. The distinction that makes O90 buildable at all is narrow: a
registry FIELD asserting pipeline-wiring readiness is gate territory (N10 drafted
config/gate-prompts/registry-wiring-readiness.yaml and it is unsigned), while
CROSSING two fields the registry already records separately is reporting. If a
`wired:` key ever appears in the registry sources, this key stopped reporting and
started asserting, and that must fail loudly rather than ship quietly.

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

REPO = Path(__file__).resolve().parents[2]
LOAD_MAP = REPO / "web" / "src" / "generated" / "load-map.json"
PRINT_HTML = REPO / "docs" / "plan" / "load-map.html"
MODEL_TS = REPO / "web" / "src" / "loadmap" / "loadMapModel.ts"
RENDERER = REPO / "scripts" / "render_load_map.py"

STATE_IDS = ("wired", "planned", "awaiting", "registered")


def _sources() -> list[dict]:
    return json.loads(LOAD_MAP.read_text(encoding="utf-8"))["sources"]


def _state(source: dict) -> str:
    built = bool(source["loaders"])
    if source["confirmed"]:
        return "wired" if built else "planned"
    return "awaiting" if built else "registered"


def _census() -> dict[str, int]:
    out = dict.fromkeys(STATE_IDS, 0)
    for s in _sources():
        out[_state(s)] += 1
    return out


def test_the_key_reports_and_never_rules() -> None:
    """No source row carries a wiring field of its own.

    The moment one does, the cross is no longer derived from two independent
    dispositions and the unsigned N10 gate has been pre-empted by a renderer.
    """
    forbidden = {"wired", "wiring", "wiring_state", "ready"}
    for s in _sources():
        overlap = forbidden & set(s)
        assert not overlap, (
            f"source {s['id']} carries {sorted(overlap)} — a wiring disposition is "
            "gate territory (N10, registry-wiring-readiness, unsigned). The key "
            "crosses `confirmed` x `loaders`; it must not read or write a field."
        )


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
            "registered": "registered only",
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
    for label in ("wired", "planned", "built, awaiting gate", "registered only"):
        assert f"'{label}'" in ts or f'"{label}"' in ts, f"console lost the {label!r} label"
        assert f'"{label}"' in py, f"print renderer lost the {label!r} label"
