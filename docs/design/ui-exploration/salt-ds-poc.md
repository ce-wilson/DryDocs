# Salt DS proof of concept (Idea-192)

- **Reviewed at:** commit `2883fc61` on `wip/idea-192-desktop` (plus the layout fix committed with this document), port base `port-base-20260910b`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Status:** research for Idea-192. Not a groom and not a stack decision; the locked single-track stack (`site-plan.md` section 1) is unchanged on `main`. Idea-192 records Salt as preferred company-side, not mandated (user ruling 2026-08-27), so this is an option being costed.
- **Salt source:** https://github.com/jpmorganchase/salt-ds.git (Apache-2.0), read at a local checkout of upstream commit `deb1ee156`. Packages were installed from registry.npmjs.org.
- **Code:** branch `wip/idea-192-desktop`, files listed in section 6.

## 1. What the PoC is

`/lab/salt-poc` renders the `/load-map` page three ways over the same committed `web/src/generated/load-map.json`.

| Skin (`?skin=`) | What renders |
|---|---|
| `current` | The real `LoadMapRoute`, unchanged. |
| `salt` | The same page with its leaf components replaced by `@salt-ds/core`, on Salt's own theme (`SaltProviderNext`: Open Sans and PT Mono, sharp corners, uppercase actions). |
| `salt-branded` | The `salt` page with Salt's leaf tokens pointed at `styles/tokens.css`: IBM Plex, DryDocs colors, sentence-case actions, rounded corners. |

`?density=high|medium|low|touch` sets Salt's density (default `high`). Light and dark follow the console's theme toggle. The route is a `GATED_SURFACE` at `sme`, the same access as `/load-map`, and it loads lazily, so the Salt chunk reaches no one who cannot open `/load-map`.

Why `/load-map`: it is the one page built on the shared table idiom (`tableControls`: `TableControlBar`, `SortableTh`, `useTableView`); it also carries tabs, status chips, stat tiles, a banner and an empty state; and it renders from a committed artifact, so it needs no graph.

## 2. The comparison set

Counts across `web/src` (`.tsx` and `.ts`, tests and generated files excluded), measured 2026-09-11:

| Control | Count |
|---|---|
| raw `<button>` | 81 |
| raw `<table>` | 45 |
| raw `<input>` | 34 |
| raw `<select>` | 19 |
| `EmptyState` (most-imported first-party primitive) | 19 importers |
| `StatusChip`, `IdChip`, `CompletenessNotice` | 3 importers each |
| `tableControls` | 2 importers |
| `Tabs` | 1 importer, but that importer is `ModuleTemplate`, which every module page instantiates |

Raw HTML controls outnumber the twelve first-party primitives by a wide margin. A Salt track is mostly a rewrite of raw controls, not a swap of primitives.

## 3. Component crosswalk (Idea-192 item a)

| Current | Salt 1.67 in the PoC | Result |
|---|---|---|
| `<table>` with class strings | `TableContainer`, `Table zebra`, `THead sticky`, `TBody`, `TR`, `TH`, `TD` | Works. Salt's own Table guidance sends "complex data" to the AG Grid data grid (`@salt-ds/ag-grid-theme`), not to `Table`. |
| `SortableTh` | `TH` holding a transparent `Button` and `ArrowUpIcon` or `ArrowDownIcon` | Hand-built; core has no sortable header. The three-state cycle and `aria-sort` carry over (verified). On Salt's theme, sortable headers render uppercase and plain headers do not. |
| `TableControlBar` | `Input` with a search adornment, `ToggleButton`, bordered `Button`, `Text` | Clean fit. |
| Kind filter chips (`aria-pressed` buttons) | `ToggleButtonGroup` | Fits. Single-select cannot toggle back to none, so the `all` button carries that. |
| `Tabs` | `Tabs`, `TabBar`, `TabList`, `Tab`, `TabTrigger`, `TabPanel` | Works; every panel stays mounted (F8). |
| Wiring pill (the `StatusChip` idiom) | `StatusIndicator` plus `Text color={status}` | Four Salt statuses only (F6). |
| `StatTiles` | `Card` with `Text styleAs="display3"` and `"label"` | Clean fit. |
| Banner paragraph | `Banner status="info"` | Clean fit. |
| `EmptyState` | None; `StackLayout` plus `Text` | No Salt equivalent. Stays first-party. |
| `ModuleToolbar`, `ResizableSplit`, the shell zones | Kept | Shared by all three skins. |
| `IdChip`, `Meter`, `EpistemicBadge`, `TruncationBadge`, `CompletenessNotice`, `TaglineWithProvenance` | Not exercised | Not tested; this page does not render them. |

Shared by every skin with no edits: `useTableControls`, `useTableView`, `toCsv` and `download` from `tableControls.tsx`, and all of `loadMapModel`. The table logic ported unchanged and only presentation moved. That is the seam the 2026-07-17 assessment asked the shell to keep (section 7), and it holds.

## 4. Findings

**F1. The newest Salt releases do not install from public npm.** `@salt-ds/core` 1.67.1 through 1.70.0 depend on `@salt-ds/icons` ^1.18.1 or ^1.18.2. Those icon versions exist in the Salt repository (`packages/icons/CHANGELOG.md`), but npm's latest is 1.18.0, published 2026-03-31. The newest clean install is core 1.67.0 (2026-07-08); the PoC pairs it with theme 1.43.0 and icons 1.18.0, all pinned exactly. An internal registry that mirrors npm inherits the gap. For item (d): an offline install works (no external requests at runtime; fonts are self-hosted through `@fontsource`), but the version policy has to be "pin exact, and confirm the icons dependency resolves before bumping core."

**F2. A root provider re-themes the whole console.** A `SaltProvider` with no parent defaults to `applyClassesTo="root"`, which writes the `.salt-theme` classes and `data-mode` onto `<html>`, and Salt allows one root provider per window. The PoC passes `applyClassesTo="scope"`. Measured: `<html>` never received a Salt class or `data-mode` in any skin, and after a client-side navigation to `/load-map` no `.salt-theme` element remained. So a per-page adoption must use scoped providers, and a whole-console track would use one root provider and end `tokens.css`'s role as the single palette.

**F3. Salt CSS wins every property it shares with Tailwind.** None of Salt's component stylesheets uses `@layer`; they are injected unlayered at runtime, while Tailwind v4 utilities are layered. Salt's `FlexLayout` (under `StackLayout` and `FlowLayout`) sets `padding` and `margin` from its own variables, and `Card` sets `padding`. Measured: Tailwind `px-4` and `p-3` on a `FlowLayout` or `StackLayout` computed to zero; moved onto a plain wrapper `div`, they applied (heading inset 15px, equal to the current page). The same rule protects Salt from the console: the `@layer base` input styles in `index.css` did not reach Salt's `Input` (computed padding 0, no border). For item (b), the answer is: **Tailwind can stay for layout on plain elements; on any element that becomes a Salt component, spacing moves to Salt props.** The codebase has 1,757 `className=` occurrences in 100 of 111 `.tsx` files (2026-09-11, tests and generated files excluded; Idea-192's 1,167 across 65 was measured 2026-08-27 by a method it did not record). The cost term is the subset on elements that would become Salt components, not the total. The PoC page's own 53 are all on plain elements.

**F4. Salt injects its CSS at runtime.** Component styles arrive as `<style>` elements and stay in `<head>` after the Salt page unmounts. Every selector is scoped, so they are inert elsewhere (measured after navigation). The console sends no Content-Security-Policy today, so this works. A strict `style-src` without `'unsafe-inline'` would require `enableStyleInjection={false}` and bundling Salt's CSS.

**F5. Type follows density, and actions are uppercase.** Measured `h2`: 14px at `high` and 18px at `medium`, against the console's 22.5px. Table cells: 11px and 12px against 13.1px. First row height: 39px and 53px against 50px. Salt uppercases action text (buttons, toggle buttons) in both of its themes through one variable, `--salt-text-action-textTransform`; the branded skin sets it to `none` and the buttons render in sentence case (verified). Salt's default fonts are Open Sans and PT Mono. The J.P. Morgan theme variant that Salt's docs recommend also needs the Amplitude font, which is not public and was not tested.

**F6. The status vocabulary does not map one to one.** Salt has four statuses: `success`, `warning`, `error`, `info`. `ui-conventions.md` section 1 has five tokens: `--green`, `--yellow` (pending), `--teal` (running), `--status-fail`, `--muted` (inert). `--teal` and `--muted` have no Salt status, and pending lands on `warning`, which reads as caution. On this page `planned` renders as a warning and `registered` gets no indicator. The pill shape of `StatusChip` is also lost. This needs an SME ruling, because the section 1 table is the one mapping every surface follows.

**F7. Token mapping works through leaf tokens only.** Salt resolves its alias chain on the `.salt-theme` element, so re-pointing a foundation token on a descendant does not reach components. The branded skin overrides the leaf tokens components read (about 75 declarations, `var()` only, no hex). With those, IBM Plex and the DryDocs neutral, accent and status colors carry into Salt components in both modes (item c). Shape stays Salt's: corner radius, bordered cards, table rhythm. Whether that suits Kept Orbit is a design call, and the page lets a reviewer make it side by side.

**F8. Tabs keep every panel mounted.** Salt's `TabPanel` renders all panels and hides the inactive ones. The Salt skins carry 101 table rows in the DOM against 30 on the current page, which renders only the active tab. Harmless here; it matters for heavy tabs such as graph panes.

**F9. Bundle.** The Salt stack lands entirely in the PoC's lazy chunk: 231,740 bytes of JS (57.9 KB gzip) and 282,810 bytes of CSS (44.1 KB gzip, carrying both `theme.css` and `theme-next.css`). The entry chunk is unchanged at 2,424,600 bytes against the 2,500,000 ceiling. `@fontsource` emits 64 font files covering every subset; a browser fetches only the subsets a page uses.

## 5. Proposed narrow scope for the groom

For the backlog item or items Idea-192 grooms into:

1. **Starting artifact:** this PoC and its branch. The first item extends it rather than restarting.
2. **Settled by the PoC:** the seam holds (shell, table hooks and models unchanged); a scoped provider works and tears down cleanly (F2); an offline install works with exact pins (F1); the Tailwind-for-layout rule (F3).
3. **Rulings for the HITL gate before any build:**
   - R1. Per-page scoped Salt, or one root provider for the whole console (F2).
   - R2. Status vocabulary: how running, inert and pending map into Salt's four statuses (F6).
   - R3. Grids: Salt `Table` with our `tableControls`, or the AG Grid data grid with `@salt-ds/ag-grid-theme`. The second is a new dependency and a larger decision than the skin; not tested.
   - R4. Brand: density default, uppercase actions, type scale and corner shape against Kept Orbit (F5, F7).
   - R5. Version policy, given the icons publishing gap (F1).
4. **Next measurable unit:** re-skin `ModuleTemplate`, the component every module page instantiates, behind the same `?skin=` switch. That puts every module page up for review at once and yields F3's real cost term: the count of `className=` sites on elements that become Salt components.
5. **Out of scope for the first item:** graph canvases (React Flow and NVL are untouched either way), the `By class` tab, `IdChip`, `Meter` and the badges, and any change to the locked-stack pin in `tests/unit/test_software_registry.py`.

## 6. Verification record

Venue: the desktop, worktree `ui-workstream` on `wip/idea-192-desktop`. Vite dev server on port 5174; drydocs-api on port 8011 against a throwaway credential store written by `web/e2e/bootstrap_credential.py` (the machine's real store was not touched); headless Edge through Playwright 1.62.1. No graph was needed.

| Check | Result |
|---|---|
| `npm run build` | Passes. |
| `npm run bundle:check` | 2,424,600 of 2,500,000 bytes. |
| `npm run lint` (oxlint) | Clean. |
| `npx vitest run` | 51 files, 535 tests pass, including the lazy-route, route-access and README guards. |
| pytest: `test_ui_components`, `test_software_registry`, `test_console_delivery`, `test_ui_tests_ledger` and the J57 family | 132 passed. |
| Browser: three skins in light and dark render with no console errors | Pass. |
| Browser: `<html>` never carries a Salt class; clean teardown after navigation | Pass. |
| Browser: sort cycle with `aria-sort`, filter (10 of 30 rows), group by system, tab switch | Pass. |
| Browser: a `user`-tier persona is redirected to `/` and the Salt chunk is never requested | Pass. |

Files on the branch: `web/src/routes/SaltPocRoute.tsx`, `web/src/routes/SaltPocRoute.css`, `web/src/App.tsx` (lazy route), `web/src/modules/registry.ts` (`GATED_SURFACES` entry), `web/README.md` (gated-surface list), `web/package.json` and its lock (five exact pins), `config/taxonomy/ui-components.yaml` and `tests/unit/test_ui_components.py` (ledger row; pin 111 to 112).

To run it: start the console from this branch per the `run-drydocs-console` skill, sign in as a steward or admin persona, and open `/lab/salt-poc`.

## 7. The 2026-07-17 assessment, lifted from git history

Idea-192 asked for this to be back on disk before any costing. It was compressed to one line at groom `ea1a4554` and survives in full only at commit `f9d0b2d0`. As it stood that day, with what the PoC now confirms:

- `@salt-ds/core`, Apache-2.0, active (1.67.0 in July 2026; consistent with F1).
- Built for dense data: density modes (confirmed, F5), an AG Grid pairing (confirmed in Salt's docs, R3), WCAG 2.1 (not re-checked).
- A versioned npm dependency with churn in its lab package, not Tailwind (confirmed and sharpened, F3), and aesthetically opposite the dark-schematic spec (the branded skin tests how far tokens close that gap, F7).
- Mitigation: keep the shell library-agnostic so a port swaps components, not structure (confirmed, section 3).
- A community Salt MCP server was noted (glama.ai, `@feesch/salt-mcp`); not evaluated.
