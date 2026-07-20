import { Link } from 'react-router-dom'
import type { Persona, Session } from '../lib/auth'
import BrandMark from '../components/BrandMark'
import ThemeToggle from '../components/ThemeToggle'

export type EnvName = 'Prod' | 'UAT' | 'Dev'
const ENVS: readonly EnvName[] = ['Prod', 'UAT', 'Dev']

interface HeaderProps {
  session: Session
  persona: Persona
  env: EnvName
  onEnvChange: (env: EnvName) => void
  onSignOut: () => void
}

// The GLOBAL header zone (site-plan §3 / wf-landing-01): logo, search, env
// toggle, 3-state theme toggle, avatar. Fixed height from shellConfig.
// Breadcrumbs deliberately do NOT live here — that is the page-owned toolbar's
// job (wf-landing-01 annotation 6 / wf-module-subpage-01 zone rule).
export default function Header({ persona, env, onEnvChange, onSignOut }: HeaderProps) {
  return (
    <header className="flex h-full items-center gap-4 border-b border-edge-soft bg-panel/90 px-4 backdrop-blur">
      <Link to="/" className="flex shrink-0 items-center gap-2 text-lg font-bold tracking-tight text-text no-underline">
        <BrandMark />
        <span className="hidden sm:inline">DryDocs</span>
      </Link>

      <div className="mx-auto flex w-full max-w-md items-center">
        <label className="sr-only" htmlFor="global-search">Search nodes, servers, jobs</label>
        <input
          id="global-search"
          type="search"
          placeholder="Search nodes, servers, jobs…"
          className="w-full rounded-md border border-edge bg-bg-2 px-3 py-1.5 text-sm text-text placeholder:text-faint"
        />
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-3">
        {persona.role === 'admin' && (
          <div
            className="flex overflow-hidden rounded-md border border-edge text-xs font-semibold"
            title="Environment (cosmetic — mock, pending the O1 access-path ADR)"
          >
            {ENVS.map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => onEnvChange(name)}
                className={
                  'px-2.5 py-1.5 transition-colors ' +
                  (name === env ? 'bg-panel-2 text-text shadow-[inset_0_-2px_0_var(--teal)]' : 'text-muted hover:text-text')
                }
              >
                {name}
              </button>
            ))}
          </div>
        )}

        <ThemeToggle />

        <span
          className="hidden max-w-[180px] items-center truncate rounded-full border border-edge px-3 py-1 font-mono text-[11px] text-muted md:inline-flex"
          title={persona.chip}
        >
          ◉ {persona.id}
        </span>
        <button
          type="button"
          onClick={onSignOut}
          className="rounded-md border border-blue bg-blue/10 px-3 py-1.5 text-sm font-semibold text-blue-bright hover:bg-blue/20"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
