import type { Role } from '../lib/auth'
import ModuleToolbar from '../layout/ModuleToolbar'
import CypherConsole from '../components/CypherConsole'

// Not one of the site-plan's 9 module spokes — this is the O2 admin dev bench
// (raw bolt Cypher + ADK agent flows), kept reachable at /console (admin-only,
// gated in App.tsx) rather than silently dropped. It sits alongside the
// persona-gated, not-yet-built /admin/config (O12) and /mappings (O13) routes
// named in site-plan §3 as "not module spokes."
export default function ConsoleRoute({ personaId, role }: { personaId: string; role: Role }) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Console (dev)' }]} />
      {/* CypherConsole's own <main> has no class (it used to rely on the old
          Shell's ".shell > main:not(.wrap)" App.css rule for padding/width,
          which no longer exists) — the padding/max-width now lives on this
          wrapper instead. */}
      <div className="mx-auto min-h-0 w-full max-w-4xl flex-1 overflow-auto px-6 py-4">
        <CypherConsole personaId={personaId} role={role} />
      </div>
    </div>
  )
}
