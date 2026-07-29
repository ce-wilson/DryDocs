import { NavLink } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { canAccessModule, MODULES } from '../modules/registry'
import ModuleIcon from '../components/ModuleIcon'

// The ASIDE zone: global module nav (site-plan §3's registry, one entry per
// module, spoke order). Distinct from the right sidebar (aside ≠ sidebar,
// wf-module-subpage-01). Collapsible, but the grid column it occupies is
// ALWAYS reserved (shellConfig.ts) — collapsing narrows it to an icon rail,
// it never disappears.
export default function Aside({
  persona,
  collapsed,
  onToggleCollapsed,
}: {
  persona: Persona
  collapsed: boolean
  onToggleCollapsed: (next: boolean) => void
}) {
  return (
    <nav
      aria-label="Modules"
      className="flex h-full flex-col overflow-y-auto border-r border-edge-soft bg-panel px-2 py-3"
    >
      <button
        type="button"
        onClick={() => onToggleCollapsed(!collapsed)}
        aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
        title={collapsed ? 'Expand' : 'Collapse'}
        className="mb-2 flex h-8 w-8 items-center justify-center self-end rounded-md text-muted hover:bg-bg-2 hover:text-text"
      >
        {collapsed ? '»' : '«'}
      </button>

      <NavLink
        to="/"
        end
        className={({ isActive }) =>
          navItemClass(isActive) + ' mb-1'
        }
      >
        <span className="flex h-5 w-5 shrink-0 items-center justify-center text-brand" aria-hidden="true">●</span>
        {!collapsed && <span>Overview</span>}
      </NavLink>

      <div className="my-1 border-t border-edge-soft" />

      <ul className="flex flex-1 flex-col gap-1">
        {/* FB-03: modules render only for personas their `access` designation admits */}
        {MODULES.filter((m) => canAccessModule(m.access, persona.role)).map((m) => (
          <li key={m.id}>
            <NavLink to={m.path} className={({ isActive }) => navItemClass(isActive)} title={collapsed ? m.label : undefined}>
              <ModuleIcon id={m.id} className="h-5 w-5 shrink-0" />
              {!collapsed && <span className="truncate">{m.label}</span>}
            </NavLink>
          </li>
        ))}
      </ul>

      {persona.role === 'admin' && (
        <NavLink to="/admin/agent-test" className={({ isActive }) => navItemClass(isActive)} title={collapsed ? 'Agent Test' : undefined}>
          <span className="flex h-5 w-5 shrink-0 items-center justify-center font-mono text-[13px]" aria-hidden="true">⚗</span>
          {!collapsed && <span>Agent Test</span>}
        </NavLink>
      )}
      {(persona.role === 'steward' || persona.role === 'admin') && (
        <NavLink to="/mappings" className={({ isActive }) => navItemClass(isActive)} title={collapsed ? 'Mappings' : undefined}>
          <span className="flex h-5 w-5 shrink-0 items-center justify-center" aria-hidden="true">⇄</span>
          {!collapsed && <span className="truncate">Mappings</span>}
          {!collapsed && persona.role === 'steward' && (
            <span className="ml-auto rounded border border-edge px-1 font-mono text-[9px] text-faint">stew</span>
          )}
        </NavLink>
      )}

      {persona.role === 'admin' && (
        <NavLink to="/admin/config" className={({ isActive }) => navItemClass(isActive)} title={collapsed ? 'Configuration' : undefined}>
          <ModuleIcon id="admin-config" className="h-5 w-5 shrink-0" />
          {!collapsed && <span className="truncate">Configuration</span>}
        </NavLink>
      )}

      {persona.role === 'admin' && (
        <NavLink to="/console" className={({ isActive }) => navItemClass(isActive)} title={collapsed ? 'Console (dev)' : undefined}>
          <span className="flex h-5 w-5 shrink-0 items-center justify-center font-mono text-xs" aria-hidden="true">{'>_'}</span>
          {!collapsed && <span>Console (dev)</span>}
        </NavLink>
      )}

      <div className="mt-2 flex flex-col gap-1 border-t border-edge-soft pt-2">
        <span
          aria-disabled="true"
          title="Not yet implemented"
          className="flex cursor-not-allowed items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-faint"
        >
          <span className="h-5 w-5 shrink-0" aria-hidden="true">⚙</span>
          {!collapsed && <span>Settings</span>}
        </span>
        <span
          aria-disabled="true"
          title="Not yet implemented"
          className="flex cursor-not-allowed items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-faint"
        >
          <span className="h-5 w-5 shrink-0" aria-hidden="true">◍</span>
          {!collapsed && <span>Profile</span>}
        </span>
      </div>
    </nav>
  )
}

// Active-state treatment adapted from the mock's nav-links (drydocs-landing-dark.html
// `.nav-links a.active { border-bottom: 2px solid var(--blue-br) }`): this IA
// runs its module nav down the aside, not across a top bar, so the underline
// becomes a left accent bar — same "active = blue-bright accent line" idea,
// same axis as the rail itself.
function navItemClass(isActive: boolean): string {
  return (
    'flex items-center gap-2.5 rounded-md border-l-2 px-2.5 py-2 text-sm font-medium no-underline transition-colors ' +
    (isActive ? 'border-blue-bright bg-panel-2 text-text' : 'border-transparent text-muted hover:bg-bg-2 hover:text-text')
  )
}
