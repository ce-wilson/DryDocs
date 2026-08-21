# Design Critique: drydocs-landing-dark.html

Branch: `feature/ui-dark-landing-myapps` · Reviewed: 2026-07-06 · Stage: exploration mockup
Views covered: Landing, Tower drill-down, My Apps (user view).

## Overall Impression

A confident, coherent dark UI — the IBM Plex pairing, disciplined token palette, and mono-labeled graph diagrams read as a credible internal engineering tool. The biggest opportunity: the hero spends its largest type on the product name (already in the nav) instead of the value proposition, and the three-view SPA has no routing, so none of the states are linkable or back-button safe.

## Usability

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| No URL/hash routing — drill-down and My Apps are `display` toggles. Browser back exits the site instead of the view; states can't be deep-linked or shared. | 🔴 Critical (for the real build) | Use `location.hash` (`#/tower/home`, `#/my-apps`) + `hashchange` listener. Cheap in the mockup, essential in prod. |
| "Explore the Graph" (primary CTA) silently opens the **Home Lending** drill-down specifically. Label promises a generic explorer. | 🟡 Moderate | Either scroll to "Explore by Tower" or relabel ("See an example"). |
| "My Apps" button only exists inside the Home Lending drill-down (`display:none` elsewhere). The feature this branch is named for is 2 clicks deep and undiscoverable. | 🟡 Moderate | Surface a signed-in entry point in the nav (or next to Sign In) once authenticated. |
| Nav links (Graph Explorer, Lineage, Pipelines, Teams, About) and "Watch Demo" are dead `#` links. | 🟢 Minor (expected in mockup) | Track as backlog items; stub pages before user testing. |
| View switch doesn't move focus — screen-reader/keyboard users stay on a now-hidden button. | 🟡 Moderate | On view change, focus the view's `h2` (`tabindex="-1"` + `.focus()`). |
| `TOWERS[*].spark` sparkline data is defined but never rendered — dead data implies a missing UI element. | 🟢 Minor | Render sparklines on tower cards or delete the data. |

## Visual Hierarchy

- **What draws the eye first:** the red-core hero illustration, then the 74px "DryDocs" h1. The illustration earns it; the h1 duplicates the nav logo. Swap emphasis: make "A Don't-Repeat-Yourself Knowledge Graph" (or a sharper benefit line) the h1-weight element.
- **Reading flow:** hero → feature strip → tower cards is clean and conventional. The 4-item feature strip with border-separated columns scans well.
- **Drill-down:** Cypher panel (left) before graph result (right) puts code before payoff; consider graph-first for non-engineer SMEs.
- **My Apps rollup SVG** is the strongest artifact in the file — clear card anatomy (app id, SNOW badge, team, PAT badge). The `ROLLS_UP_TO` edge labels floating mid-path are slightly orphaned; anchor them closer to the arrows.

## Consistency

| Element | Issue | Recommendation |
|---------|-------|----------------|
| Dependency matrix table | Columns "Shared Buckets" vs "Shared S3 Buckets" are near-duplicates; Snowflake column is entirely "—"; "Credit Cards" appears as two rows; cells read as prose sentences, not matrix values. | Redesign as tower × resource grid with ✓/dep markers, or a from→to edge list. This is the weakest panel content-wise. |
| Button heights | `.signin` (~35px), `.btn-myapps`/`.back` (~34px), primary buttons (~43px) all differ. | One button scale (e.g. 36/44px sm/md tokens). |
| Focus styles | Only `.tower` has `:focus-visible`; nav links and buttons rely on default (suppressed by borders/colors in places). | Global `:focus-visible` rule using `--blue-br`. |
| Red `--red` | Used for brand core *and* danger ("SNOW · Admin" badge). | Keep red = alert; use brand accent elsewhere, or accept and document the dual role. |
| Fonts via Google Fonts CDN | Won't load on a locked-down intranet (the likely deployment target). | Self-host IBM Plex woff2. |
| Inline `onclick` handlers | Fine for a mockup; blocked by strict CSP in prod. | Move to `addEventListener` when porting. |

## Accessibility

- **Color contrast** (computed, WCAG AA = 4.5:1 normal / 3:1 large):
  - Body text `#E8EDF3` on `#0D1520` — 15.6:1 ✅
  - Muted `#8A97A8` on bg/panels — 5.7–6.2:1 ✅
  - Buttons, tags, table text — 4.5–9.8:1 ✅
  - **`--faint #5C6B7E` on bg — 3.37:1 ❌** (footer, SVG captions at 10–11px). Lighten to ≈`#71809A` or reserve for decorative-only.
- **Tiny SVG text:** 9px edge labels and 10px sub-labels in fixed-viewBox SVGs (1000-wide) shrink below legibility on narrow screens. Provide a text alternative (the `aria-label`s are good) and consider larger base sizes.
- **Touch targets:** tower cards and primary buttons fine; nav links and ~34px buttons are below the 44px guideline for touch use — acceptable for a desktop-first internal tool, note it.
- **Positives:** `role="img"` + meaningful `aria-label` on every diagram SVG; tower cards are keyboard-operable with `role="button"`, `tabIndex`, Enter/Space handling; `lang="en"`; semantic `nav`/`main`/`section`.
- **Responsive gap:** single 900px breakpoint stacks grids, but `.nav-links` never collapses — nav overflows below ~760px. Needs a collapse/hamburger plan.

## What Works Well

- Design tokens are disciplined — everything routes through `:root` variables, which makes the planned light/dark theming and print variants nearly free.
- The synthesized-data honesty ("EXAMPLE DATA · ILLUSTRATIVE / ANONYMIZED" tags, footer provenance lines) is exactly right for a demo that will be shown around a bank.
- The My Apps view tells a real story: ServiceNow access → app cards → PAT teams → CTO tower, plus Control-M folder/job lineage with median start times. It maps 1:1 to the DryDocs graph model (taxonomy → ontology edges like `ROLLS_UP_TO`, `CONTAINS`, `TRIGGERS`).
- Cypher panels with syntax highlighting double as documentation of the ontology — good SME-communication device.

## Priority Recommendations

1. **Add hash routing + focus management** — makes all three views testable, linkable, and accessible; smallest change with the biggest structural payoff before more views are added.
2. **Rework the hero headline hierarchy** — lead with the value proposition, not the logo repeated at 74px; keeps the strong illustration as the anchor.
3. **Redesign the Inter-Tower Dependency Matrix** — current columns/rows are internally inconsistent; as the panel most tied to DryDocs' core promise (cross-tower dependencies), it deserves the clearest treatment.
4. **Fix `--faint` contrast and set a nav-collapse plan** — the only hard WCAG failure plus the only broken responsive state.
