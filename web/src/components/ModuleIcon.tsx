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
  }
}
