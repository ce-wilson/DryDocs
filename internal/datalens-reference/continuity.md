# Runtime-monitor continuity — HL DataLens ↔ DryDocs console (groom candidates)

> 2026-07-28. Context: **HL DataLens** is the SRE-built *runtime view* over the same batch
> estate DryDocs models (products → data flows → Control-M folders/jobs → Snowflake).
> Users will hop between the two tools: DryDocs answers *what is this, who owns it, what
> depends on it*; DataLens answers *how did it run last night*. Goal of this doc: remove
> the "harsh transition" in either direction, and feed the normal groom — each DL-item
> below carries proposed backlog fields; the groom assigns real O-series ids (per the
> O29–O32 precedent groomed from `two-track-ui-plan.md`).
>
> Source: four DataLens screenshots (this folder, `HL-Datalens-ui-*.png`) reviewed against
> `web/src/styles/tokens.css`, `web/src/index.css`, `UI-WIP/design-review.md`,
> `UI-WIP/site-plan.md`, `UI-WIP/two-track-ui-plan.md`. Per the two-track back-flow rule
> (company → producer is **mechanism-only reproduction**), this doc records patterns to
> reproduce generically — no files, assets, or styles copied. See DL-9 for the
> classification question this raises.

## Where the two tools already converge (no work needed)

- **Canvas colors are near-identical in light mode:** DryDocs `--bg #f4f6f9` /
  `--panel2 #eef2f7` vs DataLens ~`#F4F6FA` background / `#EEF2F7` tinted table headers.
- **Same primary-blue family:** `--blue #2e6bc4` vs their ~`#2563EB`.
- **Same table anatomy:** white cards on gray-blue, tinted (not bordered) header rows,
  green/red semantic status coloring.
- **Typography is a soft difference, not a clash:** IBM Plex Sans vs Inter — both neutral
  grotesques with similar x-height. **Keep Plex** (brand identity, and self-hosted per
  design-review's locked-down-intranet note — their Google-Fonts Inter has exactly the
  problem our review already flagged and fixed).

The real friction is concentrated in three places: **theme polarity** (their light-first
vs our dark-canonical → DL-7/O32), **shape language** (their 12–16px pills vs our 6px
flat borders → DL-3/DL-5), and **red** (our brand core vs their failure red → DL-2).

## Candidate items

| # | Item | Type | Size | Quick win? |
|---|------|------|------|------------|
| DL-1 | `tabular-nums` on numeric/timestamp columns | chore | XS | **YES** |
| DL-2 | Split brand red from status red (`--status-fail` token) | task | S | **YES** |
| DL-3 | Tinted status-count pill chips (`15 Completed` / `2 Not Completed`) | task | S | **YES** |
| DL-4 | Threshold-colored progress meter component | task | S–M | **YES** |
| DL-5 | Radius token + soften pass (~6px → ~10px on cards/panels) | task | M | no — repo-wide visual change, needs eyes |
| DL-6 | Entity-rendering convention: mono chips for job/folder/product identifiers | task | M | no — convention + sweep |
| DL-7 | *Merge, not new item:* tune O32's light pass toward the runtime monitor's values | groom-merge | — | free at O32 time |
| DL-8 | Cross-tool deep-link seam (producer ships the slot; company binds URLs) | requirement | M | no — Track-2 dependent |
| DL-9 | Classify + re-home the DataLens screenshots per the publish boundary | chore | XS | **YES** |

### DL-1 — Tabular numerals on numeric and timestamp columns  ·  QUICK WIN

DataLens renders `Start Time` / `End Time` / job counts in proportional figures and the
digit columns wobble; we should not inherit that. One utility class
(`font-variant-numeric: tabular-nums`, or Plex Mono where the cell is an identifier —
see DL-6) applied to numeric table columns, stat tiles, and the loads timeline.

- type: chore · module: drydocs-web · phase: 12 · agent: main · model: haiku · priority: p3
- depends_on: `[]` · inputs: `web/src/index.css`, `web/src/components/StatTiles.tsx`, `web/src/loads/`
- acceptance sketch: a `tabular-nums` utility exists in the token/base layer and is applied
  to every numeric column in StatTiles, LoadsTimeline, and any table rendering counts or
  timestamps; digits align vertically (before/after screenshot); build + lint green.

### DL-2 — Split brand red from status red  ·  QUICK WIN

`design-review.md` already flagged `--red #C8202E` doing double duty as Kept Orbit brand
core *and* danger. DataLens uses red aggressively for failed jobs and below-threshold
progress (~`#E11D48` rose family). If we adopt threshold meters (DL-4) the collision gets
worse. Resolve it now, in the token sheet, while the console is small:

- reserve `#C8202E` (`--color-brand`) strictly for the brand mark / Kept Orbit surfaces;
- add `--status-fail` (light ≈ `#c81e46`-family rose, dark a brightened equivalent —
  derived per the site-plan §2 one-step-darker/brighter rule, WCAG-checked like the
  `--faint` fix) and route every danger/failure surface through it;
- result: "red = failed job" reads identically in both tools, and brand red stays clean.

- type: task · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p2
  (p2 because DL-3/DL-4 build on it)
- depends_on: `[]` · inputs: `web/src/styles/tokens.css`, `UI-WIP/design-review.md` (consistency table), `UI-WIP/site-plan.md` §2
- acceptance sketch: `--status-fail` exists in both token sheets with the Tailwind
  `@theme` alias; a repo grep shows no non-brand surface consuming `--red`/`--color-brand`
  for error/danger semantics; both themes contrast-checked (≥4.5:1 on `--panel` for text
  use, ≥3:1 for large/graphic use); build + lint green.

### DL-3 — Tinted status-count pill chips  ·  QUICK WIN

DataLens's best small pattern: pill chips like `✓ 15 Completed` / `✕ 2 Not Completed` and
count-badged filter tabs (`Failed 0 · On Wait 0 · In Progress 0 · Completed 15`). Direct
recognition carry-over for anyone hopping tools, and it maps cleanly onto our existing
status vocabulary (loads, job runs, gate states). Build one `StatusChip` component
(token-tinted background, count + label, optional glyph) — reproduced generically in our
idiom (our radii, our tokens, HubGlyphs-style glyphs, **no emoji**).

- type: task · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p3
- depends_on: DL-2 · inputs: `web/src/components/`, `web/src/loads/`, `web/src/underhood/ResultChip.tsx` (nearest existing idiom)
- acceptance sketch: a reusable `StatusChip` renders tinted count+label pills from theme
  tokens only (no hex); adopted in at least two live surfaces (e.g. LoadsTimeline
  summary row and the underhood scoreboard); both themes verified; build + lint green.

### DL-4 — Threshold-colored progress meter  ·  QUICK WIN

DataLens's signature element: a thin rounded meter whose fill color is a function of a
threshold (43% and 73% render fail-red, 87%+ render green), paired with a right-aligned
percentage label. This is the single strongest visual bridge for the graph → runtime
mental hop, and it slots straight into StatTiles, the loads timeline, and any future
layer-4 (context-graph) health surface — including O28's node-status envelope glyphs.

- type: task · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p3
- depends_on: DL-2 · inputs: `web/src/components/StatTiles.tsx`, `web/src/loads/`
- acceptance sketch: a `Meter` component (value, optional threshold(s)) fills green /
  `--status-fail` by threshold, from tokens only; percentage label uses DL-1's
  `tabular-nums`; adopted in at least one live surface; honors
  `prefers-reduced-motion` if animated; both themes verified; build + lint green.

### DL-5 — Radius token + soften pass

Shape language is where "harsh" comes from even with matched colors: DataLens is pills
and 12–16px cards; we are 6px and flat 1px `--edge` borders. Meet partway — introduce
`--radius-sm/--radius-md` tokens (≈6/10px), lift cards/panels to `--radius-md`, keep
inputs/small controls at `--radius-sm`. Explicitly **not** adopting their full pill
buttons or gradient headers (see "Do not adopt"). Repo-wide visual change → wants a
before/after screenshot review, not a blind sweep; pairs naturally with O30 (App.css
retirement) since both touch every surface's chrome.

- type: task · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p3
- depends_on: `[]` (coordinate with O30) · inputs: `web/src/styles/tokens.css`, `web/src/index.css`, `web/src/App.css`
- acceptance sketch: radius tokens exist and every hard-coded `border-radius` in
  `web/src` resolves through them; cards/panels visually softened to `--radius-md` with
  before/after screenshots in both themes attached to the review; build + lint green.

### DL-6 — Entity-rendering convention: identifiers as mono chips

The strongest continuity lever is not styling — it is **entity recognition**. The same
Control-M folders (`PRORGG-HLDM-…`), job names (`PORGD0070_MPX_…_RFND`), and product
codes (PRARA/PRORG/PRSRV…) appear in both tools. Convention: any Control-M/product
identifier renders in Plex Mono inside a subtle chip, colored by the shared status
vocabulary (DL-2/DL-3) everywhere in the console — inspector, lineage nodes, loads
rows, search results. Same object, different lens, instant recognition.

- type: task · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p3
- depends_on: DL-3 · inputs: `web/src/` (inspector, lineage, loads, ownership surfaces), `docs/RELATIONSHIP_GUIDE.md` (naming), `knowledge/standards/`
- acceptance sketch: a documented convention (one short section in site-plan or a
  UI-WIP note) + an `IdChip` component; adopted on the node inspector and one graph/list
  surface; no per-surface bespoke identifier styling remains on the touched surfaces;
  both themes verified; build + lint green.

### DL-7 — Groom-merge into O32 (light-mode pass): tune toward the runtime monitor

Not a new item. O32 already owns the light-mode design pass ("light is derived, not
designed"). Merge one sentence into its notes/acceptance: *the light pass should land on
(or consciously near) the runtime monitor's observed values — bg ~#F4F6FA, tinted table
headers #EEF2F7, threshold green/fail semantics per DL-2 — so light mode is the bridge
surface between the two tools.* Theme polarity (their light-first vs our dark-canonical)
is the single harshest transition; this makes O32 the fix at zero extra scope.

### DL-8 — Cross-tool deep-link seam (producer slot, company binding)

A job chip in DryDocs should open that job's runtime row in DataLens; a DataLens job
should link back to its DryDocs node. Producer side ships the *mechanism only*: an
optional per-entity "runtime view" link slot (URL template from config/env, hidden when
unset) on the inspector + IdChips. Binding real DataLens URLs is company data/env →
Track-2 (DD-series allocates company-side, per the backlog id rule). Follows the
two-track seam rule: a page is "ported" when it renders company config with zero
component edits.

- type: requirement · module: drydocs-web · phase: 12 · agent: main · model: sonnet · priority: p3
- depends_on: DL-6 · inputs: `web/src/`, `UI-WIP/two-track-ui-plan.md` (Track-2 table)
- acceptance sketch: a config/env-driven URL-template slot renders an external-link
  affordance on entity surfaces when set and nothing when unset; template documented in
  `.env.example`; no company URL or hostname appears anywhere in the repo; build + lint
  green. Company-side binding tracked as a DD-series item in their tracker, not here.

### DL-9 — Classification: re-home the DataLens screenshots  ·  QUICK WIN

`HL-Datalens-ui-*.png` (4 files) currently sit at the **repo root**. They are screenshots
of an internal company tool — under the publish boundary (§3, `PUBLISH-BOUNDARY.md`)
that is **Internal at minimum**, and they carry real product codes and job names. They
should live under `internal/` (e.g. `internal/datalens-reference/`) with a
`SOURCE-MANIFEST` + classification entry, not at root where a public push would carry
them. Groom should also rule where THIS doc lives: it names the company tool and quotes
identifier shapes, so either sanitize it for `UI-WIP/` (ports company-ward) or move it
to `internal/` alongside the screenshots.

- type: chore · module: repo-hygiene (or nearest) · agent: main · model: haiku · priority: p2
  (publish-boundary correctness)
- acceptance sketch: screenshots moved under `internal/` with a manifest +
  `config/classification.yaml` entry; `tests/unit/test_classification.py` green; no
  `HL-Datalens*` file remains outside `internal/`; this doc's home ruled and recorded.
- **DONE 2026-07-28** (`feat/datalens-quickwins`): screenshots + this doc moved to
  `internal/datalens-reference/` with a classified README (classification: Internal —
  pat-evidence precedent; no registry entry needed, these are shape references, not an
  ingested source). Root `/*.png` gitignore rule had kept the PNGs untracked (never at
  publish risk via git); they are now tracked in their classified home.

## Do not adopt (ruled out, with reasons)

- **Emoji-as-icons** — we have HubGlyphs; emoji break the token/recolor discipline and
  render inconsistently across platforms.
- **Gradient hero banner / gradient CTA buttons** — collides with the Kept Orbit
  identity and the site-plan §2 restraint rules; our glass header + mark is stronger.
- **Stacked drill-down panels** (row → panel-under-panel → pipeline → job table on one
  scrolling page) — our hash-routed views are structurally better (linkable,
  back-button-safe — the exact gap design-review flagged as critical). DL-8's deep links
  deliver the same "drill into runtime" feel without inheriting the scroll pile.
- **Full pill buttons / 16px radii everywhere** — DL-5 meets partway at ~10px instead.

## Suggested groom order

1. **DL-9** (publish-boundary correctness — do first, it's a `git mv` + manifest)
2. **DL-2** (token split; unblocks DL-3/DL-4)
3. **DL-1, DL-3, DL-4** (the quick-win trio — small, parallelizable, sonnet/haiku)
4. **DL-7** (free — one merged sentence into O32)
5. **DL-5, DL-6** (visual-change items that want screenshot review)
6. **DL-8** (requirement; producer slot now or when Track-2 asks)
