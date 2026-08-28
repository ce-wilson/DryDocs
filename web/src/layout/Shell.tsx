import { useRef, useState } from 'react'
import { Outlet } from 'react-router-dom'
import type { Persona, Session } from '../lib/auth'
import { ASIDE_COLLAPSE_STORAGE_KEY, initialAsideCollapsed, shellCssVars } from './shellConfig'
import { RightSidebarProvider, useRightSidebar } from './rightSidebarContext'
import { useRouteA11y } from './useRouteA11y'
import Header, { type EnvName } from './Header'
import Aside from './Aside'
import RightSidebarSlot from './RightSidebarSlot'

export type { EnvName }

interface ShellProps {
  session: Session
  persona: Persona
  env: EnvName
  onEnvChange: (env: EnvName) => void
  onSignOut: () => void
}

// The zone shell (O8 acceptance): aside / header / page-owned toolbar /
// content / right-sidebar slot, ALL driven by the one typed config in
// shellConfig.ts. The mock-auth banner from the old Shell (O2) is kept —
// mock auth itself is unchanged by this item, only the chrome around it.
export default function Shell(props: ShellProps) {
  return (
    <RightSidebarProvider>
      <ShellGrid {...props} />
    </RightSidebarProvider>
  )
}

function ShellGrid({ session, persona, env, onEnvChange, onSignOut }: ShellProps) {
  const [collapsed, setCollapsed] = useState(initialAsideCollapsed)
  const { isOpen } = useRightSidebar()
  const contentRef = useRef<HTMLDivElement>(null)
  useRouteA11y(contentRef)

  function toggleCollapsed(next: boolean) {
    setCollapsed(next)
    try {
      localStorage.setItem(ASIDE_COLLAPSE_STORAGE_KEY, next ? '1' : '0')
    } catch {
      /* ignore */
    }
  }

  const vars = shellCssVars(collapsed, isOpen)

  return (
    <div
      className="grid h-dvh w-full"
      style={{
        ...vars,
        gridTemplateColumns: 'var(--shell-aside-w) 1fr var(--shell-sidebar-w)',
        gridTemplateRows: 'auto var(--shell-header-h) 1fr',
        gridTemplateAreas: '"banner banner banner" "header header header" "aside main sidebar"',
      }}
    >
      {/* O69 re-decided this banner rather than leaving it standing. It read
          "MOCK AUTH ... no real access control ... access path pending the O1
          ADR", and by 2026-08-28 all three claims were false: the access path
          was ruled in ADR 0005, sign-in proves a secret, and the session
          expires server-side. What remains true is narrower and is what the
          band now says — the identities are synthetic, and their secrets are
          machine-local rather than issued by any directory. Muted, not yellow:
          a warning colour for a condition that is no longer a defect trains
          people to ignore the banner that matters. */}
      <div
        style={{ gridArea: 'banner' }}
        className="border-b border-edge bg-bg-2 px-3 py-1.5 text-center font-mono text-[11px] text-muted"
      >
        SYNTHETIC ACCOUNT · {persona.id} ({session.role}) · session authenticated by drydocs-api ·
        credentials are machine-local, not a directory
      </div>
      <div style={{ gridArea: 'header', height: 'var(--shell-header-h)' }} className="min-w-0">
        <Header session={session} persona={persona} env={env} onEnvChange={onEnvChange} onSignOut={onSignOut} />
      </div>
      <div style={{ gridArea: 'aside' }} className="min-h-0">
        <Aside persona={persona} collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
      </div>
      <div style={{ gridArea: 'sidebar' }} className="min-h-0 min-w-0 overflow-hidden">
        <RightSidebarSlot />
      </div>
      <main ref={contentRef} style={{ gridArea: 'main' }} className="min-h-0 min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
