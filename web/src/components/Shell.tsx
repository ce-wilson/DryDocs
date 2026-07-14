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

// Signed-in layout: mock banner, role-filtered nav (plain hash links — the App
// hashchange listener does the routing), admin-only env toggle, user chip,
// sign out. The full sidebar shell from the UI spec is O1 design-pass scope.
export default function Shell({
  session, persona, activeView, env, onEnvChange, onSignOut, children,
}: ShellProps) {
  return (
    <div className="shell">
      <div className="mock-banner">
        ◉ MOCK AUTH · SYNTHESIZED — persona {persona.id} ({session.role}) · no real
        access control · access path pending the O1 ADR
      </div>
      <header className="shell-head">
        <span className="brand">DryDocs</span>
        <nav className="shell-nav">
          {VIEWS.filter((v) => canSee(v.id, session.role)).map((v) => (
            <a key={v.id} href={hashFor(v.id)} className={v.id === activeView ? 'active' : undefined}>
              {v.label}
            </a>
          ))}
        </nav>
        <span className="spacer" />
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
      </header>
      {children}
    </div>
  )
}
