// Mock RBAC predicate for the tower demo deep links. Everything else that used
// to live here (ViewId/VIEWS/canSee/hashFor*/parseRoute/defaultViewFor) was the
// hash-based router the O2 console shipped with; O8 replaces that with real
// react-router routes (see src/App.tsx), so those hash-only helpers are
// retired along with it — nothing in this module cares about `#/...` anymore.

import type { Persona } from './auth'

// Tower drill-down access: admin drills any tower; a user only their own
// (persona.towerKey — the tower their ServiceNow-derived apps roll up to).
export function canDrill(towerKey: string, persona: Persona): boolean {
  return persona.role === 'admin' || persona.towerKey === towerKey
}
