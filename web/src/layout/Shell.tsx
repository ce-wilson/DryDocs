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
      <div
        style={{ gridArea: 'banner' }}
        className="border-b border-yellow/45 bg-yellow/10 px-3 py-1.5 text-center font-mono text-[11px] text-yellow"
      >
        ◉ MOCK AUTH · SYNTHESIZED — persona {persona.id} ({session.role}) · no real access control · access
        path pending the O1 ADR
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
