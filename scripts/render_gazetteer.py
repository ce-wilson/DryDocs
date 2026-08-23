"""Generate the location-gazetteer artifact for the Z5 map module.

Reads ``config/taxonomy/location-gazetteer.yaml`` and emits
``web/src/generated/gazetteer.json`` — the map component reads the artifact,
never the yaml, and never hardcodes a place. Same rule as the O45 context-type
dropdown next door.

Two things happen here rather than in the browser, both on purpose:

* **Alias flattening.** The yaml keeps aliases as an author-friendly list per
  country; the artifact ships the inverted, lower-cased lookup the consumer
  actually needs. Inverting it here means the collision check is a build-time
  failure (see :func:`_invert_aliases`) instead of a last-writer-wins surprise
  at runtime.
* **Projection to canvas units.** Every city is pre-projected with the SAME
  equirectangular formula the country shapes were baked with
  (``scripts/render_world_map.py``), so a point and the shape it sits on cannot
  disagree — the failure mode this whole design is arranged to prevent.

Rides the default ``render_board.py`` run (the J17/J20/N4 one-entry-point idiom);
``tests/unit/test_location_gazetteer.py`` is the drift guard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "config" / "taxonomy" / "location-gazetteer.yaml"
OUT = REPO / "web" / "src" / "generated" / "gazetteer.json"

#: Must match scripts/render_world_map.py. Guarded by
#: tests/unit/test_location_gazetteer.py::test_projection_matches_the_world_map.
MAP_WIDTH = 1000.0
MAP_HEIGHT = 500.0


def project(lon: float, lat: float) -> tuple[float, float]:
    """Equirectangular lon/lat -> canvas x/y — the world map's formula, verbatim."""
    return ((lon + 180.0) / 360.0 * MAP_WIDTH, (90.0 - lat) / 180.0 * MAP_HEIGHT)


def _norm(token: str) -> str:
    """The matching normal form: trimmed, case-folded, inner whitespace collapsed.

    Deliberately does NOT strip punctuation — "U.S." and "US" are listed as separate
    aliases instead. Stripping punctuation silently merges tokens the source may
    have meant to distinguish, and an alias list that has to be written out is an
    alias list somebody reviewed.
    """
    return " ".join(token.split()).casefold()


def _invert_aliases(countries: list[dict[str, Any]]) -> dict[str, str]:
    """name/alias -> country id, with collisions raised rather than resolved.

    A token that maps to two countries has no right answer, so the build stops and
    names both. Silently keeping the last one would put located nodes on the wrong
    continent and nothing downstream could detect it.
    """
    lookup: dict[str, str] = {}
    for country in countries:
        tokens = [country["name"], *(country.get("aliases") or [])]
        for token in tokens:
            key = _norm(str(token))
            existing = lookup.get(key)
            if existing is not None and existing != country["id"]:
                raise ValueError(
                    f"gazetteer alias collision: {token!r} maps to both country "
                    f"{existing} and {country['id']} — an ambiguous token cannot be "
                    "resolved, remove or qualify one of them"
                )
            lookup[key] = country["id"]
    return lookup


def _city_rows(
    cities: list[dict[str, Any]], *, synthetic: bool, alias_to_id: dict[str, str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for city in cities:
        # Real cities key on an ISO country id; synthetic ones deliberately do not
        # have one (their "SYN" is not an ISO code and must never land on a real
        # country's shape), so they carry the raw alias for display only.
        country_id = city.get("country_id")
        if country_id is None and not synthetic:
            alias = _norm(str(city.get("country_alias", "")))
            country_id = alias_to_id.get(alias)
        x, y = project(float(city["lon"]), float(city["lat"]))
        rows.append(
            {
                "id": city["id"],
                "name": city["name"],
                "state": city.get("state") or None,
                "country_id": country_id,
                "country_alias": city.get("country_alias"),
                "lat": float(city["lat"]),
                "lon": float(city["lon"]),
                "x": round(x, 2),
                "y": round(y, 2),
                "grain": city.get("grain", "city"),
                "synthetic": synthetic,
            }
        )
    return rows


def build_gazetteer() -> dict[str, Any]:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    synthetic = data.get("synthetic") or {}

    countries = data["countries"]
    alias_to_id = _invert_aliases(countries)
    # Synthetic country tokens resolve to their own id space so a surface can label
    # them, but they are NOT merged into alias_to_id — nothing synthetic may ever
    # resolve onto a real ISO country.
    synthetic_aliases = {
        _norm(str(token)): country["id"]
        for country in (synthetic.get("countries") or [])
        for token in [country["name"], *(country.get("aliases") or [])]
    }
    overlap = sorted(set(alias_to_id) & set(synthetic_aliases))
    if overlap:
        raise ValueError(
            f"synthetic country token(s) {overlap} collide with real countries — "
            "a fixture must never resolve onto real geography"
        )

    cities = _city_rows(data["cities"], synthetic=False, alias_to_id=alias_to_id)
    cities += _city_rows(synthetic.get("cities") or [], synthetic=True, alias_to_id=alias_to_id)

    return {
        "taxonomy": data["taxonomy"],
        "classification": data["classification"],
        "captured": str(data["captured"]),
        "map": {"width": MAP_WIDTH, "height": MAP_HEIGHT, "projection": "equirectangular"},
        "countries": [
            {
                "id": c["id"],
                "name": c["name"],
                "synthetic": False,
                # Carried through so the console can say WHY a country never
                # highlights, instead of leaving it looking like missing data.
                "no_shape": bool(c.get("no_shape_at_source_resolution", False)),
            }
            for c in countries
        ]
        + [
            {"id": c["id"], "name": c["name"], "synthetic": True, "no_shape": True}
            for c in (synthetic.get("countries") or [])
        ],
        "country_lookup": dict(sorted({**alias_to_id, **synthetic_aliases}.items())),
        "cities": sorted(cities, key=lambda c: c["id"]),
    }


def main() -> None:
    view = build_gazetteer()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8", newline="\n")
    real = sum(1 for c in view["cities"] if not c["synthetic"])
    print(
        f"wrote {OUT} ({len(view['countries'])} countries, {real} cities "
        f"+ {len(view['cities']) - real} synthetic)"
    )


if __name__ == "__main__":
    main()
