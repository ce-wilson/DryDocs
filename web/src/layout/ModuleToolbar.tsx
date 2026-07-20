import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface Crumb {
  label: string
  to?: string
}

// The PAGE-OWNED toolbar zone. Every route renders its own instance — this is
// deliberate: breadcrumbs and page actions belong to the page, never the
// global header (wf-landing-01 annotation 6, wf-module-subpage-01 zone rule).
// `crumbs` is route-derived (site-plan §3: "Home > <Module> > <selection>");
// `actions` is a slot for page-specific buttons (layout picker, zoom-to-fit,
// refresh, export — wired up module-by-module in later backlog items).
export default function ModuleToolbar({ crumbs, actions }: { crumbs: readonly Crumb[]; actions?: ReactNode }) {
  return (
    <div
      style={{ minHeight: 'var(--shell-toolbar-h)' }}
      className="flex flex-wrap items-center gap-3 border-b border-edge-soft px-4 py-2"
    >
      <nav aria-label="Breadcrumb" className="min-w-0 flex-1">
        <ol className="flex flex-wrap items-center gap-1.5 text-sm text-muted">
          {crumbs.map((c, i) => (
            <li key={i} className="flex items-center gap-1.5">
              {i > 0 && <span aria-hidden="true">/</span>}
              {c.to ? (
                <Link to={c.to} className="text-muted no-underline hover:text-text">
                  {c.label}
                </Link>
              ) : (
                <span className="text-text" aria-current="page">
                  {c.label}
                </span>
              )}
            </li>
          ))}
        </ol>
      </nav>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
