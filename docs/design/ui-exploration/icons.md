# DryDocs Icon Set

Derived from the landing-page hub visual (`Gemini_Generated_Image_oob4hpoob4hpoob4.png`) and
the dark-schematic visual language in `DryDocs_UI_Development_Specs.md`. Replicated as inline
SVG (not raster) so the set is reusable, recolorable, and crisp at any size.

Live reference: https://claude.ai/code/artifact/a05cff17-317a-439a-ac1c-a7f99dc7fc64

## Palette tokens

| Token | Hex | Use |
|---|---|---|
| `--red-0` / `--red-1` | `#e23a54` / `#8c1230` | Brand sphere gradient |
| `--teal` | `#38d6c4` | Healthy / left-column connectors |
| `--amber` | `#eeab4d` | Warning / right-column connectors |
| `--bg-0` | `#070d18` | App background |
| `--panel-border` | `rgba(148,177,209,0.14)` | Glass panel edges |

Conventions: 120×120 viewBox, ~2.2px stroke, `feGaussianBlur` glow filter on the accent layer only.

## Glyphs (7)

1. **Brand Mark** — red sphere + revolving translucent rectangles (per spec: "Red sphere with
   revolving rectangular shapes"). Header lockup / favicon.
2. **Tower Auto** — isometric city block + car badge. Auto Finance tower node.
3. **Infrastructure** — server rack (3 rows, status LEDs) + orchestration gear + Linux host badge.
   Reused for both "Core Infrastructure" nodes in the hub.
4. **Home Lending** — isometric house, roof + door + window. Mortgage tower node.
5. **Data Lineage** — two data frames joined by directional elbow connectors. Pipeline node.
6. **Credit Cards** — three fanned rounded-rect cards, each a different accent stripe. Cards
   tower node.

## Status

- [x] Icon set drawn and matched to hub composition
- [x] Export as standalone components — DONE 2026-07-21 (O22) as
      `web/src/components/icons/HubGlyphs.tsx`: inline-SVG React components
      (recolorable beats static `.svg` files — everything routes through the O8
      token sheet, no hard-coded hex; palette mapping in the file header).
      `TowerIcon`/`BrandMark` now consume them; glow = `.glyph-accent`
      drop-shadow, dark mode only (light = solid outline per site-plan §2).
      Both themes verified via computed styles (accents resolve to their theme's
      token values; light filter: none).
- [ ] ~~Swap in real Inter / Fira Code webfonts~~ SUPERSEDED: the locked stack
      self-hosts IBM Plex Sans/Mono (site-plan §1, shipped in O8) — this line
      predated the font decision.
- [x] Brand mark UPGRADED 2026-07-21 to the **Kept Orbit** geometry
      (`kept-orbit-philosophy.md`, `drydocs-mark*.svg` — logo-5/logo-8 rebuilt
      as exact ellipse-arc staves): console `BrandMarkGlyph` + `favicon.svg` +
      the alt landing all share it. The original glyph-1 description ("red
      sphere + revolving rectangles") is superseded by the stave construction.
