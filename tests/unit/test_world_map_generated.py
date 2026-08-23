"""Guard the Z5 world-map asset: it is GENERATED, so it must never be hand-edited.

The drift half is the same idiom as gates.json / load-map.json / benchmarkData.ts —
regenerate from the vendored source and assert the committed file matches. The rest of
this module guards the things a byte-compare cannot see: that the projection means what
the consumer thinks it means, and that the two failures found while building this asset
stay fixed.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GENERATED = REPO / "web" / "src" / "generated" / "world-map.ts"
SOURCE = REPO / "external" / "geo" / "world-atlas" / "countries-110m.json"


def _renderer():
    """Import scripts/render_world_map.py by path — scripts/ is not a package."""
    spec = importlib.util.spec_from_file_location(
        "render_world_map", REPO / "scripts" / "render_world_map.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_world_map"] = module
    spec.loader.exec_module(module)
    return module


def test_the_vendored_source_is_present_and_is_the_pinned_edition() -> None:
    """A generated asset with no source is unregenerable — and unreviewable."""
    assert SOURCE.exists(), f"vendored map source missing: {SOURCE}"
    manifest = (SOURCE.parent / "SOURCE-MANIFEST.md").read_text(encoding="utf-8")
    assert "world-atlas@2.0.2" in manifest, "the manifest must pin the captured edition"
    assert (SOURCE.parent / "LICENSE").exists(), (
        "the ISC licence must travel with the redistribution — that is the condition "
        "under which this repo may carry it at all"
    )


def test_committed_map_matches_regeneration() -> None:
    """The drift guard: hand-edit the asset, or move the source, and this fails."""
    rendered = _renderer().build()
    committed = GENERATED.read_text(encoding="utf-8")
    assert committed == rendered, (
        "web/src/generated/world-map.ts is stale or hand-edited — regenerate with "
        "`poetry run python scripts/render_world_map.py` and commit the result"
    )


def test_the_asset_carries_the_whole_world_minus_the_documented_drop() -> None:
    text = GENERATED.read_text(encoding="utf-8")
    ids = re.findall(r'\{ id: "([^"]+)"', text)
    assert len(ids) == len(set(ids)), "country ids must be unique — they are the join key"
    # 177 geometries in the source, Antarctica deliberately not drawn.
    assert len(ids) == 176, f"expected 176 drawn countries, found {len(ids)}"
    assert "010" not in ids, "Antarctica is dropped from the render by design"
    assert "Antarctica" in text, "...and the drop must stay DOCUMENTED in the header"


def test_the_three_codeless_territories_are_drawn_but_cannot_be_joined() -> None:
    """N. Cyprus, Somaliland and Kosovo have no ISO 3166-1 numeric code assigned.

    They are drawn — omitting them would punch holes in the map — under `x-` ids
    that no ISO code can equal, so a gazetteer country can never resolve onto one.
    Pinned because "just give them an id" is the tempting fix and it would silently
    put located nodes inside a disputed territory.
    """
    ids = re.findall(r'\{ id: "([^"]+)"', GENERATED.read_text(encoding="utf-8"))
    codeless = sorted(i for i in ids if i.startswith("x-"))
    assert codeless == ["x-kosovo", "x-n-cyprus", "x-somaliland"], codeless
    for i in codeless:
        assert not i.isdigit(), "an x- id must never be mistakable for an ISO numeric code"


@pytest.mark.parametrize(
    ("iso", "name", "lon", "lat"),
    [
        ("840", "United States", -99.0, 39.5),
        ("826", "United Kingdom", -2.7, 53.9),
        ("250", "France", 2.3, 46.6),
        ("392", "Japan", 136.9, 36.0),
        ("036", "Australia", 134.4, -25.6),
    ],
)
def test_centroids_land_inside_their_own_country(
    iso: str, name: str, lon: float, lat: float
) -> None:
    """The regression that motivated the largest-ring rule.

    An area-WEIGHTED centroid over every ring — the obvious first implementation —
    put France in the Bay of Biscay (-2.9, 42.5) and the United States in Montana
    (-112.6, 45.7), because French Guiana and Alaska drag the mean off the mainland.
    These expectations are the mainland answers; they fail if anyone reinstates the
    weighted mean, and the numbers are loose enough (±2°) to survive a source edition
    bump that shifts a coastline.
    """
    module = _renderer()
    text = GENERATED.read_text(encoding="utf-8")
    match = re.search(
        rf'\{{ id: "{iso}", name: "[^"]*", bbox: \[[^]]*\], centroid: \[([^]]*)\]', text
    )
    assert match, f"{name} ({iso}) not found in the generated asset"
    x, y = (float(v) for v in match.group(1).split(","))
    # Invert the projection and compare in degrees, where the expectation is legible.
    got_lon = x / module.WIDTH * 360.0 - 180.0
    got_lat = 90.0 - y / module.HEIGHT * 180.0
    assert abs(got_lon - lon) < 2.0 and abs(got_lat - lat) < 2.0, (
        f"{name} centroid drifted to ({got_lon:.2f}, {got_lat:.2f}), expected "
        f"about ({lon}, {lat}) — a centroid outside its own country usually means "
        "the largest-ring rule was replaced by an area-weighted mean"
    )


def test_no_ring_streaks_across_the_map() -> None:
    """The antimeridian regression — found by LOOKING at the render, not by a test.

    Russia and Fiji both straddle 180°. Before the fix, a vertex at +179° followed
    by one at -179° (a 2° step on the globe) became a 998-unit leap across the
    canvas, so both countries drew a horizontal streak the full width of the world.
    Worse and quieter: it made their bboxes the ENTIRE WORLD, so "drill into Russia"
    would have silently shown everything and looked like a broken click.

    Nothing about the numbers looked wrong — only the picture did — which is exactly
    why it is pinned here now.
    """
    text = GENERATED.read_text(encoding="utf-8")
    blocks = re.findall(r'\{ id: "([^"]+)", name: "([^"]*)".*?d: "([^"]*)" \}', text)
    assert blocks, "no country path data parsed — the regex or the format changed"
    for iso, name, d in blocks:
        for ring in d.split("Z"):
            ring = ring.strip().lstrip("M")
            if not ring:
                continue
            xs = [float(pair.split(" ")[0]) for pair in ring.split("L") if pair.strip()]
            span = max(xs) - min(xs)
            assert span <= 500, (
                f"{name} ({iso}) has a ring spanning {span:.0f} canvas units — more than "
                "half the world. That is an antimeridian wrap drawing a streak across "
                "the map; _split_at_antimeridian is what prevents it"
            )


def test_antimeridian_countries_frame_their_own_landmass() -> None:
    """The quieter half of the same bug: a world-sized bbox breaks drill-down."""
    text = GENERATED.read_text(encoding="utf-8")
    for iso, name in [("643", "Russia"), ("242", "Fiji")]:
        match = re.search(rf'\{{ id: "{iso}", name: "[^"]*", bbox: \[([^\]]*)\]', text)
        assert match, f"{name} not found"
        _, _, w, _ = (float(v) for v in match.group(1).split(","))
        assert w < 500, (
            f"{name}'s drill-down frame is {w:.0f} units wide — a country whose bbox is "
            "most of the world cannot be drilled into"
        )


def test_the_split_only_fires_on_a_real_wrap() -> None:
    """It must cut antimeridian crossings and NOTHING else.

    A split that fired on ordinary vertices would quietly shred every coastline into
    disconnected fragments, and the map would still look broadly map-shaped.
    """
    module = _renderer()
    ordinary = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (0.0, 0.0)]
    assert module._split_at_antimeridian(ordinary) == [
        ordinary
    ], "a ring that never crosses 180° must come back whole"
    wrapping = [
        (179.0, 10.0),
        (179.5, 11.0),
        (180.0, 12.0),
        (-179.0, 12.0),
        (-178.0, 11.0),
        (-177.5, 10.0),
    ]
    runs = module._split_at_antimeridian(wrapping)
    assert len(runs) == 2, f"expected the wrap to split into two runs, got {len(runs)}"
    assert all(len(r) >= 3 for r in runs)


def test_the_typescript_projection_is_the_python_one() -> None:
    """The invariant the whole design rests on: one formula, two languages.

    A mismatch does not look broken — shapes still draw, points still appear, they
    are just in the wrong place. Nothing downstream can detect that, so it is pinned
    here by reading the constants out of the TS rather than trusting a comment.
    """
    module = _renderer()
    ts = (REPO / "web" / "src" / "components" / "map" / "projection.ts").read_text(encoding="utf-8")
    assert "((lon + 180) / 360) * MAP_WIDTH" in ts
    assert "((90 - lat) / 180) * MAP_HEIGHT" in ts
    generated = GENERATED.read_text(encoding="utf-8")
    assert f"export const MAP_WIDTH = {module.WIDTH:.0f}" in generated
    assert f"export const MAP_HEIGHT = {module.HEIGHT:.0f}" in generated


def test_the_asset_declares_itself_generated() -> None:
    head = GENERATED.read_text(encoding="utf-8")[:400]
    assert "GENERATED by scripts/render_world_map.py" in head
    assert "DO NOT EDIT BY HAND" in head
