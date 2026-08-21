import type { ModuleId } from '../modules/registry'

// One small glyph per module — used by both the aside nav and the Overview
// hub spokes (same registry, same icon, per wf-landing-01 annotation 1).
// Deliberately simple geometric strokes (no icon-font dependency) so they
// theme for free via `currentColor`.
export default function ModuleIcon({ id, className }: { id: ModuleId; className?: string }) {
  const common = { className, fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  switch (id) {
    case 'explorer':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <circle cx="12" cy="6" r="2.4" /><circle cx="5.5" cy="18" r="2.4" /><circle cx="18.5" cy="18" r="2.4" />
          <path d="M12 8.4V13m0 0-5 3m5-3 5 3" />
        </svg>
      )
    case 'ask':
      // speech bubble with a graph node inside — Q&A over the graph
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 5.5h16v11H10l-4.5 4v-4H4Z" />
          <circle cx="12" cy="11" r="1.6" />
          <path d="M12 9.4V7.8M9.8 12.6l-1.5 1M14.2 12.6l1.5 1" />
        </svg>
      )
    case 'lineage':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 6h4a3 3 0 0 1 3 3v6a3 3 0 0 0 3 3h6M15 6h5M15 18h5" />
          <circle cx="4" cy="6" r="1.6" /><circle cx="20" cy="6" r="1.6" /><circle cx="20" cy="18" r="1.6" />
        </svg>
      )
    case 'ownership':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <rect x="4" y="4" width="16" height="6" rx="1.5" />
          <circle cx="8" cy="16" r="2.4" /><circle cx="16" cy="16" r="2.4" />
          <path d="M8 10v3.4M16 10v3.4" />
        </svg>
      )
    case 'runbooks':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 5h11a3 3 0 0 1 3 3v11" />
          <rect x="4" y="12" width="7" height="7" rx="1.2" />
          <path d="M15 8h5" />
        </svg>
      )
    case 'remediation':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M12 3 4 7v5c0 4.5 3.4 7.6 8 9 4.6-1.4 8-4.5 8-9V7Z" />
          <path d="M9.5 12.2 11 14l3.6-3.8" />
        </svg>
      )
    case 'docs':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M6 3h9l4 4v14H6Z" /><path d="M15 3v4h4" />
          <path d="M9 12h7M9 15.5h7M9 8.5h3" />
        </svg>
      )
    case 'software':
      // A package outline (the product) with a document mark (its docs) — the
      // join this page exists to render. NOTE: the `default` branch below is
      // an exhaustiveness guard (O67) — a ModuleId with no case here is a
      // compile error at this switch, not a silently vanished glyph.
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M3 8.5 12 4l9 4.5v7L12 20l-9-4.5Z" />
          <path d="M3 8.5 12 13l9-4.5M12 13v7" />
        </svg>
      )
    case 'gates':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 21V8l8-5 8 5v13" /><path d="M4 12h16" /><path d="M10 21v-6h4v6" />
        </svg>
      )
    case 'loads':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 18h16M6 18V9l3-3 3 3v9M12 18v-5l3-3 3 3v5" />
        </svg>
      )
    case 'loadmap':
      // A folded map — deliberately unlike `loads` (bar-chart run timeline)
      // and `lineage` (branching DAG): this page is the territory, not the
      // traffic. This case was originally MISSING (the Load map nav entry
      // rendered as bare text, no error anywhere — noticed at O57); the
      // `default` guard below is what now makes that omission a compile error.
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M3 6.5 9 4l6 2.5L21 4v13.5L15 20l-6-2.5L3 20Z" />
          <path d="M9 4v13.5M15 6.5V20" />
        </svg>
      )
    case 'underhood':
      // gauge/speedometer — the benchmark's efficiency framing (needle biased
      // toward the low-cost side, the traversal win)
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <path d="M4 16a8 8 0 1 1 16 0" />
          <path d="M12 16 8.5 11" />
          <path d="M4 16h1M19 16h1M12 5.5v1M6.5 7.5l.7.7M17.5 7.5l-.7.7" />
        </svg>
      )
    case 'admin-config':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5 5l2.1 2.1M16.9 16.9 19 19M19 5l-2.1 2.1M7.1 16.9 5 19" />
        </svg>
      )
    default: {
      // O67 exhaustiveness guard: assigning to `never` makes a ModuleId with
      // no case above a COMPILE error at this switch — the point of omission —
      // instead of an undefined return that silently drops the glyph from the
      // aside and the Overview hub. No placeholder glyph on purpose: a visible
      // fallback would reintroduce the silent-gap defect through the fix.
      const unhandled: never = id
      throw new Error(`ModuleIcon: no glyph case for module id ${String(unhandled)}`)
    }
  }
}
