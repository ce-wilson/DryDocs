// The ONE typed layout config driving every zone of the shell (O8 acceptance).
// Shell.tsx turns these into CSS custom properties on the shell's grid root, so
// the grid template, the aside's collapsed width, and the right-sidebar's
// reserved column all read from this single source instead of being repeated
// (and drifting) across component files.
//
// Zone rules encoded here (docs/design/ui-exploration/wf-module-subpage-01.md, wf-landing-01.md):
// - aside ≠ sidebar: the aside is global nav (left); the right sidebar is a
//   per-page, per-node inspector. Never conflate the two.
// - the collapsed aside keeps its grid column (collapsedWidthPx, not 0/none) —
//   collapsing narrows it, it never disappears and reflows the content column.
// - the right sidebar's column is reserved even when the inspector is closed
//   (collapsedWidthPx here is 0, but the column stays in the grid template —
//   see Shell.tsx's grid-template-columns, which always has three tracks).
// - breadcrumbs live in the page-owned toolbar (site-plan §3's per-module
//   template), never in the header — the header has no toolbarHeightPx-shaped
//   slot for one.

export interface ShellLayoutConfig {
  header: { heightPx: number }
  aside: { widthPx: number; collapsedWidthPx: number }
  /** page-owned toolbar (breadcrumb + actions) — height is shared so every
   *  module's toolbar lines up, even though its *content* is per-route. */
  toolbar: { heightPx: number }
  rightSidebar: { widthPx: number; collapsedWidthPx: number }
}

export const SHELL_LAYOUT: ShellLayoutConfig = {
  header: { heightPx: 64 },
  aside: { widthPx: 240, collapsedWidthPx: 64 },
  toolbar: { heightPx: 56 },
  rightSidebar: { widthPx: 340, collapsedWidthPx: 0 },
}

/** CSS custom properties for the shell grid, derived from the config above —
 *  the single place that turns the typed config into what the DOM consumes. */
export function shellCssVars(asideCollapsed: boolean, sidebarOpen: boolean): Record<string, string> {
  const { header, aside, toolbar, rightSidebar } = SHELL_LAYOUT
  return {
    '--shell-header-h': `${header.heightPx}px`,
    '--shell-aside-w': `${asideCollapsed ? aside.collapsedWidthPx : aside.widthPx}px`,
    '--shell-toolbar-h': `${toolbar.heightPx}px`,
    '--shell-sidebar-w': `${sidebarOpen ? rightSidebar.widthPx : rightSidebar.collapsedWidthPx}px`,
  }
}

// Aside collapsed/expanded is persisted (the collapse toggle keeps the choice
// across reloads); lives here rather than in Aside.tsx so that component file
// stays component-only (keeps react-refresh happy).
export const ASIDE_COLLAPSE_STORAGE_KEY = 'drydocs.aside-collapsed.v1'

export function initialAsideCollapsed(): boolean {
  try {
    return localStorage.getItem(ASIDE_COLLAPSE_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}
