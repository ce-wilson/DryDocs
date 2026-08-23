"""render_world_map.py — Z5: turn the vendored Natural Earth TopoJSON into committed SVG paths.

WHY A GENERATED ARTIFACT RATHER THAN A RUNTIME DEPENDENCY. The console must work
offline (Z5 acceptance: "no external tile or font fetch", the same rule every
committed render surface follows), so the geometry has to be embedded either way.
Given that, decoding TopoJSON in the browser buys nothing and costs three runtime
dependencies (``d3-geo``, ``topojson-client``, ``world-atlas``). Projecting here
instead makes the map a reviewable committed artifact guarded by a drift test —
the same idiom as ``gates.json``, ``load-map.json`` and ``benchmarkData.ts``.

WHY EQUIRECTANGULAR, WHICH IS NOT THE PRETTIEST CHOICE. The component has to place
gazetteer points on the SAME surface as these country outlines, and a point plotted
under a different projection than the shapes lands in the wrong place. Equirectangular
is the one projection whose forward transform is two lines of arithmetic, so the
browser reproduces it exactly (``web/src/components/map/projection.ts``) without
importing a projection library or trusting it to agree with this script. Natural Earth
or Robinson would look better and would require shipping the polynomial to both sides
and keeping them in step forever. The distortion at high latitudes is real and
accepted: this is a "where are our sites" console map, not a navigational one.

DRILL-DOWN COMES FREE. Every country carries its bbox in projected space, so the
country view is the SAME path data under a different SVG viewBox. There is no second
asset to generate, and no way for the world map and the country map to disagree.

Source: external/geo/world-atlas/countries-110m.json (Natural Earth 4.1.0 admin-0
at 1:110m, redistributed by world-atlas 2.0.2, ISC — see that directory's
SOURCE-MANIFEST.md). Regenerate with:

    poetry run python scripts/render_world_map.py

Guarded by tests/unit/test_world_map_generated.py (regenerate, assert no drift).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from drydocs_core.repo_paths import repo_root

REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
SOURCE = REPO_ROOT / "external" / "geo" / "world-atlas" / "countries-110m.json"
TARGET = REPO_ROOT / "web" / "src" / "generated" / "world-map.ts"

#: Projected-space canvas. Equirectangular over the full sphere is exactly 2:1;
#: 1000x500 keeps one unit ≈ 0.36° of longitude, finer than the 1:110m source.
WIDTH = 1000.0
HEIGHT = 500.0

#: Coordinate rounding in projected units. At this canvas 0.1 unit is ~4km at the
#: equator — well below the source's own resolution, so it discards no real detail
#: while cutting the emitted file roughly in half.
PRECISION = 1

#: Natural Earth carries Antarctica as a country. It spans the whole bottom of an
#: equirectangular canvas, dominates the frame, and no located node will ever sit
#: there. Dropped from the drawn world, and the drop is recorded rather than silent.
DROPPED_IDS = {"010"}


def _decode_arcs(topology: dict[str, Any]) -> list[list[tuple[float, float]]]:
    """Dequantize TopoJSON's delta-encoded integer arcs back to lon/lat degrees.

    TopoJSON stores each arc as a first absolute position followed by deltas, all
    in quantized integer space; ``transform`` carries the scale/translate back to
    spherical coordinates. Decoding it here is ~15 lines, which is the whole reason
    this script needs no topojson dependency.
    """
    scale_x, scale_y = topology["transform"]["scale"]
    translate_x, translate_y = topology["transform"]["translate"]
    arcs: list[list[tuple[float, float]]] = []
    for arc in topology["arcs"]:
        x = y = 0
        points: list[tuple[float, float]] = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * scale_x + translate_x, y * scale_y + translate_y))
        arcs.append(points)
    return arcs


def project(lon: float, lat: float) -> tuple[float, float]:
    """Equirectangular lon/lat -> canvas x/y. The browser mirrors this exactly.

    Kept as a named function rather than inlined precisely so the TypeScript twin
    in ``web/src/components/map/projection.ts`` has one formula to match, and the
    guard has one thing to compare against.
    """
    return ((lon + 180.0) / 360.0 * WIDTH, (90.0 - lat) / 180.0 * HEIGHT)


def _ring_to_points(
    ring: list[int], arcs: list[list[tuple[float, float]]]
) -> list[tuple[float, float]]:
    """Stitch a TopoJSON ring's arc indices into one coordinate run.

    A negative index means "this arc, reversed", encoded as ~i, and the shared
    endpoint between consecutive arcs is dropped so the ring has no duplicate
    vertices.
    """
    points: list[tuple[float, float]] = []
    for index in ring:
        arc = arcs[~index][::-1] if index < 0 else arcs[index]
        points.extend(arc[1:] if points else arc)
    return points


def _split_at_antimeridian(
    points: list[tuple[float, float]],
) -> list[list[tuple[float, float]]]:
    """Cut a lon/lat ring wherever it crosses ±180°, before projecting.

    FOUND BY LOOKING AT THE PICTURE, not by a test. Russia and Fiji both straddle
    the antimeridian, and an equirectangular canvas has no way to express that: a
    vertex at +179° followed by one at -179° is a 2° step on the globe and a
    998-unit leap across the canvas, so the renderer drew a horizontal streak the
    full width of the map through both of them. It also made their bboxes the
    ENTIRE WORLD, which would have made "drill into Russia" a no-op that silently
    showed everything.

    The cut is detected in DEGREES (a longitude step > 180° is impossible for real
    adjacent vertices at this resolution, so it can only be a wrap) and each
    contiguous run becomes its own subpath. The cost is a hairline gap exactly at
    the dateline where the polygon no longer closes across it — invisible at 1:110m,
    and a far better trade than a streak across the Pacific.
    """
    runs: list[list[tuple[float, float]]] = [[]]
    previous_lon: float | None = None
    for lon, lat in points:
        if previous_lon is not None and abs(lon - previous_lon) > 180.0:
            runs.append([])
        runs[-1].append((lon, lat))
        previous_lon = lon
    return [run for run in runs if len(run) >= 3]


def _rings(
    polygons: list[list[list[int]]], arcs: list[list[tuple[float, float]]]
) -> list[list[tuple[float, float]]]:
    """Every drawable ring of a country, in PROJECTED units, antimeridian-safe."""
    out: list[list[tuple[float, float]]] = []
    for rings in polygons:
        for ring in rings:
            for run in _split_at_antimeridian(_ring_to_points(ring, arcs)):
                out.append([project(lon, lat) for lon, lat in run])
    return out


def _path_d(polygons: list[list[list[int]]], arcs: list[list[tuple[float, float]]]) -> str:
    """SVG path data for one country: every ring of every polygon, closed."""
    parts: list[str] = []
    for points in _rings(polygons, arcs):
        coords = " L".join(f"{x:.{PRECISION}f} {y:.{PRECISION}f}" for x, y in points)
        parts.append(f"M{coords}Z")
    return "".join(parts)


def _bbox_and_centroid(
    polygons: list[list[list[int]]], arcs: list[list[tuple[float, float]]]
) -> tuple[list[float], list[float]]:
    """Frame and anchor for one country, both taken from its LARGEST landmass.

    Measured, not assumed: an area-WEIGHTED centroid over every ring — the obvious
    first implementation — puts France in the Bay of Biscay (-2.9, 42.5) and the
    United States in Montana (-112.6, 45.7), because French Guiana and Alaska drag
    the mean off the mainland. Averaging across parts separated by an ocean has no
    meaningful answer, so this takes the single biggest ring instead and reports
    that ring's box and centroid. France then anchors in France.

    The same reasoning applies to the frame: a bbox spanning every territory zooms
    the France drill-down out to the Atlantic. The consumer widens this frame to
    include any point it actually plots (see LocationMap's `frameFor`), so an
    outlying site is never cropped — the narrow default just stops the common case
    from being useless.
    """
    best_area = -1.0
    best: tuple[list[float], list[float]] | None = None
    for points in _rings(polygons, arcs):
        area = cx = cy = 0.0
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for i in range(len(points)):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % len(points)]
            cross = x0 * y1 - x1 * y0
            area += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
            min_x, max_x = min(min_x, x0), max(max_x, x0)
            min_y, max_y = min(min_y, y0), max(max_y, y0)
        if abs(area) <= best_area:
            continue
        best_area = abs(area)
        centroid = (
            [cx / (3.0 * area), cy / (3.0 * area)]
            if area != 0
            else [(min_x + max_x) / 2, (min_y + max_y) / 2]
        )
        best = ([min_x, min_y, max_x - min_x, max_y - min_y], centroid)
    assert best is not None, "every country has at least one drawable ring"
    bbox, centroid = best
    return (
        [round(v, PRECISION) for v in bbox],
        [round(v, PRECISION) for v in centroid],
    )


def build() -> str:
    topology = json.loads(SOURCE.read_text(encoding="utf-8"))
    arcs = _decode_arcs(topology)
    rows: list[dict[str, Any]] = []
    dropped: list[str] = []
    unjoinable: list[str] = []
    for geometry in topology["objects"]["countries"]["geometries"]:
        name = geometry["properties"]["name"]
        if "id" in geometry:
            # Natural Earth's id IS the ISO 3166-1 numeric code; zero-padded here so
            # it stays a stable string key rather than an integer that loses its
            # leading zero.
            iso_numeric = f"{int(geometry['id']):03d}"
        else:
            # Three geometries carry no ISO numeric code because none is assigned:
            # N. Cyprus, Somaliland and Kosovo are disputed or only partially
            # recognized. They are still DRAWN — leaving them out would punch holes
            # in the map — but they are given an `x-` id that no ISO code can ever
            # equal, so the gazetteer cannot accidentally resolve a country onto
            # one. This is a fact about the world, recorded rather than smoothed
            # over; DryDocs takes no position on the underlying disputes.
            iso_numeric = "x-" + name.lower().replace(".", "").replace(" ", "-")
            unjoinable.append(f"{iso_numeric} ({name})")
        if iso_numeric in DROPPED_IDS:
            dropped.append(f"{iso_numeric} {name}")
            continue
        polygons = geometry["arcs"] if geometry["type"] == "MultiPolygon" else [geometry["arcs"]]
        bbox, centroid = _bbox_and_centroid(polygons, arcs)
        rows.append(
            {
                "id": iso_numeric,
                "name": name,
                "d": _path_d(polygons, arcs),
                "bbox": bbox,
                "centroid": centroid,
            }
        )
    rows.sort(key=lambda r: r["id"])

    entries = ",\n".join(
        "  { "
        f'id: "{r["id"]}", name: {json.dumps(r["name"])}, '
        f"bbox: {r['bbox']}, centroid: {r['centroid']}, "
        f'd: "{r["d"]}" '
        "}"
        for r in rows
    )
    dropped_note = ", ".join(dropped) if dropped else "none"
    unjoinable_note = ", ".join(unjoinable) if unjoinable else "none"
    return f"""// GENERATED by scripts/render_world_map.py — DO NOT EDIT BY HAND.
// Regenerate: poetry run python scripts/render_world_map.py
// Drift-guarded by tests/unit/test_world_map_generated.py.
//
// Source: Natural Earth 4.1.0 admin-0 countries at 1:110m, redistributed as
// TopoJSON by world-atlas 2.0.2 (ISC). Vendored at
// external/geo/world-atlas/countries-110m.json — see its SOURCE-MANIFEST.md.
//
// Projection: equirectangular onto a {WIDTH:.0f}x{HEIGHT:.0f} canvas. The TypeScript twin of
// the projection lives in ./projection.ts and MUST agree with the Python one, or
// plotted points drift off the shapes they belong to.
//
// `bbox` is [x, y, width, height] in projected units — the country drill-down is
// the same path data under this viewBox, which is why there is no second asset.
// `centroid` is area-weighted, so multi-part countries centre on their mainland.
//
// Countries in the source but deliberately not drawn: {dropped_note}.
// Drawn but NOT joinable (no ISO 3166-1 numeric code is assigned to them — they are
// disputed or only partially recognized, so no gazetteer entry can resolve onto
// them): {unjoinable_note}.

export interface CountryShape {{
  /** ISO 3166-1 numeric, zero-padded — the join key the gazetteer resolves to. */
  id: string
  name: string
  bbox: readonly [number, number, number, number]
  centroid: readonly [number, number]
  d: string
}}

export const MAP_WIDTH = {WIDTH:.0f}
export const MAP_HEIGHT = {HEIGHT:.0f}

export const COUNTRY_SHAPES: readonly CountryShape[] = [
{entries},
] as const

export const COUNTRY_BY_ID: ReadonlyMap<string, CountryShape> = new Map(
  COUNTRY_SHAPES.map((c) => [c.id, c]),
)
"""


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    text = build()
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    count = text.count('{ id: "')
    print(f"wrote {TARGET} ({count} countries, {len(text) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
