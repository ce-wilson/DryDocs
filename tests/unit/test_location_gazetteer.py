"""Guard the Z5 gazetteer — the layer that turns place NAMES into map positions.

Everything here protects one of two things: that a place resolves to where it really
is, or that a place which cannot be resolved stays VISIBLE. The second is the easier
one to lose, and the more damaging: a map with a missing dot reads as "nothing there",
which is a different claim from "we could not place this".
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config" / "taxonomy" / "location-gazetteer.yaml"
GENERATED = REPO / "web" / "src" / "generated" / "gazetteer.json"
WORLD_MAP = REPO / "web" / "src" / "generated" / "world-map.ts"


def _renderer():
    spec = importlib.util.spec_from_file_location(
        "render_gazetteer", REPO / "scripts" / "render_gazetteer.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_gazetteer"] = module
    spec.loader.exec_module(module)
    return module


def _yaml() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))


def _json() -> dict:
    return json.loads(GENERATED.read_text(encoding="utf-8"))


def test_committed_artifact_matches_regeneration() -> None:
    rendered = _renderer().build_gazetteer()
    assert _json() == rendered, (
        "web/src/generated/gazetteer.json is stale — regenerate via "
        "`poetry run python scripts/render_board.py` and commit the result"
    )


def test_it_is_declared_external_and_stays_publishable() -> None:
    """The classification, and the rule that keeps it true.

    A gazetteer row is a PLACE — public geography, true regardless of who occupies
    it. The moment a row named a tenant, a SEAL, a hostname or a street address it
    would be Internal data wearing a taxonomy file's clothes and would have to move
    to internal/ (PUBLISH-BOUNDARY.md). This asserts the file has not drifted across
    that line, which is cheaper than noticing it after a publish.
    """
    doc = _yaml()
    assert doc["classification"] == "External"
    assert doc["classification_only"] is True

    # Scan the DATA, never the file text — the header prose legitimately discusses
    # the very words this forbids ("no row may name ... a hostname"), and a guard
    # that reads its own rationale as a violation trains people to delete the
    # rationale.
    forbidden = ("seal", "hostname", "host_name", "street", "address", "tenant", "occupant")
    rows: list[dict] = list(doc["countries"]) + list(doc["cities"])
    synthetic = doc.get("synthetic") or {}
    rows += list(synthetic.get("countries") or []) + list(synthetic.get("cities") or [])
    for row in rows:
        for key in row:
            assert not any(f in str(key).lower() for f in forbidden), (
                f"gazetteer row {row.get('id')!r} carries field {key!r} — a place "
                "lookup must never hold occupancy or address detail; that is Internal "
                "data and belongs in internal/"
            )
    for city in _json()["cities"]:
        assert city["grain"] != "address", (
            "grain 'address' is deliberately not allowed here — a street address is "
            "Internal by PUBLISH-BOUNDARY.md"
        )


def test_ids_are_unique_and_coordinates_are_real() -> None:
    cities = _json()["cities"]
    ids = [c["id"] for c in cities]
    assert len(ids) == len(set(ids)), "city ids are join keys and must be unique"
    for city in cities:
        assert -90 <= city["lat"] <= 90, f"{city['id']}: latitude out of range"
        assert -180 <= city["lon"] <= 180, f"{city['id']}: longitude out of range"
        assert not (city["lat"] == 0 and city["lon"] == 0), (
            f"{city['id']} sits at 0,0 — Null Island is the signature of a missing "
            "coordinate, never a real one"
        )


def test_every_real_country_resolves_to_a_shape_on_the_map() -> None:
    """A country the map cannot draw is a country whose cities can never appear."""
    drawn = set(re.findall(r'\{ id: "([^"]+)"', WORLD_MAP.read_text(encoding="utf-8")))
    for country in _json()["countries"]:
        if country["synthetic"]:
            continue
        if country["id"] in drawn:
            assert not country["no_shape"], (
                f"{country['name']} declares no_shape_at_source_resolution but the map "
                "does draw it — remove the declaration"
            )
            continue
        # A country the source is too coarse to draw is a REAL limitation, not a
        # bug: Natural Earth at 1:110m omits city-states like Singapore. Its cities
        # still plot correctly (a point needs only its own coordinate); what is
        # missing is the outline to tint and drill into. That has to be DECLARED, so
        # the gap is reviewed once rather than rediscovered as "the map is broken".
        assert country["no_shape"], (
            f"country {country['id']} ({country['name']}) has no shape in world-map.ts "
            "and does not declare it — add `no_shape_at_source_resolution: true` with "
            "the reason, or remove the country"
        )


def test_no_synthetic_place_can_land_on_real_geography() -> None:
    """The fixture must never be mistakable for the estate.

    The synthetic country "SYN" is not an ISO code on purpose. If a fixture token
    ever resolved onto a real country, a test run would draw imaginary sites inside
    somebody's actual territory — the generator raises on that collision, and this
    pins the outcome.
    """
    view = _json()
    real_ids = {c["id"] for c in view["countries"] if not c["synthetic"]}
    for city in view["cities"]:
        if city["synthetic"]:
            assert (
                city["country_id"] not in real_ids
            ), f"synthetic city {city['id']} resolved onto real country {city['country_id']}"
        else:
            assert city["country_id"] in real_ids, f"{city['id']} lost its country"


def test_alias_collisions_stop_the_build() -> None:
    """An ambiguous token has no right answer, so it must fail loudly.

    Last-writer-wins would put located nodes on the wrong continent and nothing
    downstream could detect it.
    """
    module = _renderer()
    countries = [
        {"id": "840", "name": "United States", "aliases": ["US"]},
        {"id": "826", "name": "United Kingdom", "aliases": ["US"]},  # deliberate clash
    ]
    try:
        module._invert_aliases(countries)
    except ValueError as exc:
        assert "collision" in str(exc)
    else:  # pragma: no cover - the guard failing IS the finding
        raise AssertionError("an alias mapping to two countries must raise, not resolve")


def test_projection_matches_the_world_map() -> None:
    """The gazetteer's pre-projected x/y must use the map's own formula.

    Two generators, one projection. If they drift, points sit off the shapes they
    belong to and the picture still looks plausible — which is why this is asserted
    rather than assumed.
    """
    gaz = _renderer()
    spec = importlib.util.spec_from_file_location(
        "render_world_map", REPO / "scripts" / "render_world_map.py"
    )
    assert spec and spec.loader
    world = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(world)

    assert (gaz.MAP_WIDTH, gaz.MAP_HEIGHT) == (world.WIDTH, world.HEIGHT)
    for lon, lat in [(0.0, 0.0), (-74.006, 40.7128), (139.7, 35.7), (-0.1276, 51.5072)]:
        assert gaz.project(lon, lat) == world.project(lon, lat)

    for city in _json()["cities"]:
        x, y = gaz.project(city["lon"], city["lat"])
        assert abs(city["x"] - round(x, 2)) < 1e-9, f"{city['id']}: stale projected x"
        assert abs(city["y"] - round(y, 2)) < 1e-9, f"{city['id']}: stale projected y"


def test_a_known_city_lands_where_it_should() -> None:
    """One end-to-end sanity anchor, in canvas units.

    New York at (-74.006, 40.7128) on a 1000x500 equirectangular canvas is
    x = (105.994/360)*1000 = 294.4, y = (49.2872/180)*500 = 136.9. If this moves,
    either the canvas or the projection changed and every plotted point moved with it.
    """
    city = next(c for c in _json()["cities"] if c["id"] == "us-new-york")
    assert abs(city["x"] - 294.43) < 0.05, city["x"]
    assert abs(city["y"] - 136.91) < 0.05, city["y"]
