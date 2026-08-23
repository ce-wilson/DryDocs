# World Atlas (Natural Earth) — Source Manifest

**Purpose:** country outline geometry for the Z5 reusable location-map console module.
**Classification:** `External` — publishable. Public-domain source data under a
permissive redistribution licence; see `config/classification.yaml` and
`PUBLISH-BOUNDARY.md`.
**Added:** 2026-08-22 (backlog Z5).

---

## What is here

| File | What it is |
|---|---|
| `countries-110m.json` | Natural Earth 4.1.0 **Admin 0 — Countries**, 1:110m small scale, as quantized TopoJSON. 177 geometries, ~105 KB. Spherical coordinates, decimal degrees, **not** projected. |
| `LICENSE` | The world-atlas redistribution licence (ISC, Michael Bostock 2013–2019). |

**Source URL:** https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json
(npm package `world-atlas@2.0.2`, https://github.com/topojson/world-atlas)
**Captured:** 2026-08-22, via `npm pack world-atlas@2.0.2` — the tarball's
`package/countries-110m.json` and `package/LICENSE`, copied unmodified.

## Licensing — why this is safe to commit on a sometimes-published repo

Two layers, both permissive:

- **Natural Earth** (the underlying data) is explicitly **public domain**: "no permission
  is needed to use Natural Earth. Crediting the authors is unnecessary." It is the standard
  public-domain basemap.
- **world-atlas** (the TopoJSON conversion and redistribution) is **ISC**, which permits
  use, copying, modification and distribution provided the copyright notice travels with it.
  `LICENSE` beside this file is that notice.

This is why the JSON is **committed** rather than gitignored, unlike the vendor PDFs under
`external/orchestration/**` — those are copyrighted binaries we may not redistribute, and
the contrast is the point. A publishable repo can carry this one.

## How it is consumed — never at runtime

`scripts/render_world_map.py` decodes and projects this file into
`web/src/generated/world-map.ts` (committed SVG path data), guarded for drift by
`tests/unit/test_world_map_generated.py`. **The browser never reads this file, and the
console has no map dependency at runtime** — which is what lets the console work offline
(Z5: "no external tile or font fetch", the standing rule for every committed render
surface).

That is also why there is no `d3-geo` / `topojson-client` / `world-atlas` entry in
`web/package.json`: the geometry is decided here, reviewed as a committed artifact, and
regenerated deterministically — the `gates.json` / `load-map.json` / `benchmarkData.ts`
idiom applied to a map.

## Trust

**VERBATIM** as captured — the file is byte-identical to the published package. Everything
derived from it (projection, simplification, centroids, the Antarctica drop) happens in the
generator, is described in that script's header, and is **GROUNDED** to this source.

## Caveats worth knowing before trusting the output

- **1:110m is coarse by design.** Small island states are a few vertices; some are a single
  point-like ring. Correct for a "where are our sites" world view, wrong for anything
  measuring area, distance or borders.
- **Three geometries carry no ISO 3166-1 numeric code** — N. Cyprus, Somaliland and Kosovo,
  which are disputed or only partially recognized. The generator draws them (omitting them
  would punch holes in the map) under `x-` ids that no ISO code can equal, so the gazetteer
  can never resolve a country onto one. DryDocs takes no position on the underlying
  disputes; the data does not assign a code, and that absence is recorded rather than
  papered over.
- **Antarctica is dropped from the render**, not from this source. On an equirectangular
  canvas it occupies the entire bottom band and no located node will ever sit there.
- **Natural Earth's country names are its own** ("United States of America", "N. Cyprus").
  They are display labels, never join keys — the ISO numeric id is the key, and mapping a
  source's country spelling onto it is the gazetteer's job
  (`config/taxonomy/location-gazetteer.yaml`), deliberately, because spelling variance is a
  data problem and not a map problem.

## Refresh

Manual, and rarely: this is a fixed edition of a slow-moving dataset. To move editions,
re-run `npm pack world-atlas@<version>`, replace both files, update the version and capture
date above, regenerate, and let the drift guard show exactly what moved.
