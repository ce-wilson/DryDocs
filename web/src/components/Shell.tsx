import type { ReactNode } from 'react'
import type { Persona, Session } from '../lib/auth'
import { VIEWS, canSee, hashFor, type ViewId } from '../lib/views'

export type EnvName = 'Prod' | 'UAT' | 'Dev'
const ENVS: readonly EnvName[] = ['Prod', 'UAT', 'Dev']

interface ShellProps {
  session: Session
  persona: Persona
  activeView: ViewId
  env: EnvName
  onEnvChange: (env: EnvName) => void
  onSignOut: () => void
  children: ReactNode
}

// Signed-in layout in the mockup's shell language: mock banner, sticky nav with
// the brand mark, role-filtered links (plain hash links — the App hashchange
// listener does the routing), admin-only env toggle, user chip, sign out.
export default function Shell({
  session, persona, activeView, env, onEnvChange, onSignOut, children,
}: ShellProps) {
  return (
    <div className="shell">
      <div className="mock-banner">
        ◉ MOCK AUTH · SYNTHESIZED — persona {persona.id} ({session.role}) · no real
        access control · access path pending the O1 ADR
      </div>
      <nav>
        <div className="nav-in">
          <div className="logo"><BrandMark /> DryDocs</div>
          <div className="nav-links">
            {VIEWS.filter((v) => canSee(v.id, session.role)).map((v) => (
              <a key={v.id} href={hashFor(v.id)} className={v.id === activeView ? 'active' : undefined}>
                {v.label}
              </a>
            ))}
          </div>
          {session.role === 'admin' && (
            <div className="env-toggle" title="Environment (cosmetic — mock)">
              {ENVS.map((name) => (
                <button
                  key={name}
                  className={name === env ? 'active' : undefined}
                  onClick={() => onEnvChange(name)}
                >
                  {name}
                </button>
              ))}
            </div>
          )}
          <span className="userchip">◉ {persona.id} · {persona.chip}</span>
          <button className="signout" onClick={onSignOut}>Sign out</button>
        </div>
      </nav>
      {children}
    </div>
  )
}

// The mockup's brand mark: two dashed orbit rings around a red core.
function BrandMark() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
      <circle cx="13" cy="13" r="10" fill="none" stroke="#2E6BC4" strokeWidth="2.4" strokeDasharray="18 8" />
      <circle cx="13" cy="13" r="10" fill="none" stroke="#D9B831" strokeWidth="2.4" strokeDasharray="10 38" strokeDashoffset="-20" />
      <circle cx="13" cy="13" r="4" fill="#C8202E" />
    </svg>
  )
}
