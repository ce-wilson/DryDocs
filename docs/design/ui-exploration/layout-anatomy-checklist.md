# App-shell layout anatomy — checklist

> Extracted 2026-07-17 from Keenthemes "Start React Free" v1.0.0 (the free template's
> `MasterLayout.tsx` + `DefaultThemeConfig.ts`). **Structure only — copy none of the code**
> (React 17 / CRA 4 / Bootstrap 5.0.1, all end-of-life). Companion visual reference:
> `start-react-free-reference.fig` (the template's Figma source — use for spacing and
> component anatomy; the palette will be entirely different per
> `DryDocs_UI_Development_Specs.md`).

## The zone decomposition (their nesting order, worth keeping verbatim)

```
root (full-viewport flex column)
└── page (flex row)
    ├── ASIDE  — left nav rail + panel
    ├── wrapper (flex column, fills remaining width)
    │   ├── HEADER  — fixed top bar
    │   ├── (flex column, fills remaining height)
    │   │   ├── TOOLBAR — page-level context strip (breadcrumbs live here, NOT in the header)
    │   │   └── CONTENT — the scrollable page body
    │   └── FOOTER
    └── SIDEBAR — optional RIGHT panel (distinct from the aside)
    + overlays: scroll-to-top, one-time init, drawer/off-canvas layer
```

Two ideas in there earn their keep beyond the obvious shell:

1. **Toolbar ≠ Header.** The header is global chrome (search, environment toggle, profile);
   the toolbar is a second strip under it owned by the *current page* (breadcrumbs, page
   actions, tab strip). Keeping them separate components means pages can swap toolbar
   content without touching global chrome.
2. **Aside ≠ Sidebar.** Left "aside" = primary navigation; right "sidebar" = optional
   contextual panel with pluggable content variants. For DryDocs this maps to a future
   node-inspector panel (click a graph node → details slide in on the right) without
   redesigning the shell.

## Checklist for the DryDocs shell

Spec targets from `DryDocs_UI_Development_Specs.md`: 250px fixed sidebar, 64px header,
fluid scrollable content split ~55% graph / ~45% data frames, dark schematic theme.

### Aside (left, 250px fixed)
- [ ] Logo slot at top (fixed height, never scrolls)
- [ ] Nav region scrolls independently of logo/footer (their `hover-scroll-y` trick:
      nav gets `flex: 1` + `overflow-y: auto`; logo and footer are `flex: none`)
- [ ] Aside footer pinned at bottom: Settings, User Profile, Logout
- [ ] Optional: two-tier aside (their primary/secondary split) — a ~70px icon rail +
      a label panel; gives a "minimized" mode for free. Decide: single 250px panel
      (spec) vs rail+panel (template). Default to spec; keep the CSS split-friendly.
- [ ] Collapse/minimize toggle button straddling the aside edge (absolutely positioned,
      translate-middle on the boundary)
- [ ] Mobile: aside becomes an off-canvas drawer with overlay (their `data-kt-drawer`
      behavior — reimplement with any modern drawer primitive, e.g. shadcn Sheet)

### Header (top, 64px fixed)
- [ ] Fixed positioning toggleable per breakpoint (they configure desktop vs
      tablet/mobile separately)
- [ ] Left: breadcrumbs? NO — breadcrumbs go in the toolbar (see below); header keeps
      global search ("Search nodes, servers, jobs")
- [ ] Center/right: environment toggle [ Prod | UAT | Dev ]
- [ ] Right: topbar cluster (notifications, user avatar menu) — their `Topbar.tsx` slot
- [ ] Header renders ABOVE content scroll (content scrolls under it)

### Toolbar (under header, page-owned)
- [ ] Breadcrumb slot (their config has a per-app breadcrumb on/off flag)
- [ ] Page-title + page-actions slot, populated by the active route (they do this via a
      PageData context provider the page writes into — the pattern to reuse; a small
      React context beats prop-drilling here)
- [ ] For DryDocs pages: this is where the graph/data-frame view controls live
      (zoom-to-fit, layout picker, refresh)

### Content (fluid, scrollable)
- [ ] `flex: 1` column that is the ONLY vertical scroll container (aside/header/footer
      never scroll with it)
- [ ] Width mode switch: fixed (max-width container) vs fluid — config-driven in the
      template; DryDocs wants fluid for the graph pages but a fixed-width mode is nearly
      free if built as a container class
- [ ] DryDocs split: top 50–60% lineage graph pane, bottom 40–50% data-frame tabs;
      make the divider a resizable handle (shadcn/ReUI Resizable) rather than fixed %
- [ ] Empty/loading state slot (their page loader zone — a `loader` config with display
      + type; useful for slow Cypher queries)

### Right sidebar (optional, phase 2)
- [ ] Reserve the slot in the shell grid even if unbuilt: node-inspector panel on
      graph-node click
- [ ] Content variants keyed by what was clicked (their `content: general|user|shop`
      switch → ours: job | script | etl-process | data-asset)
- [ ] Own background token + optional footer button area (both config flags in the
      template)

### Shell-wide config object (the meta-lesson)
- [ ] One typed theme/layout config drives every zone's display/fixed/width flags
      (their `IThemeConfig` + provider). Reproduce as a small typed context —
      it is what made 10 demo layouts possible from one shell.
- [ ] Every zone independently hideable (`display` flag) — cheap now, painful to retrofit
- [ ] Scroll-to-top affordance as a shell overlay, not per-page

## Explicitly NOT carried over
- Bootstrap grid/utility classes, jQuery-style `data-kt-*` init attributes, KTSVG icon
  wrapper, Redux/saga wiring, CRA build — all replaced by the Vite + React + Tailwind +
  shadcn/ReUI stack decision (see WEBSITE-IDEAS.MD / UI stack notes)
- Their light palette and `bg-info` aside color — DryDocs is dark-schematic
  (`#0f172a` base, cyber-teal/green/amber/red accents)
- Footer content (keep the zone, decide content later)
