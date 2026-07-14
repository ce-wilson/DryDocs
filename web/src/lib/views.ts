// The single role-gating registry: nav rendering, the hash guard, and the role
// default all read this map — role conditionals never scatter into components.
// Gating is cosmetic (client-side mock, see lib/auth.ts) until the O1 ADR.

import type { Role } from './auth'

export type ViewId = 'my-apps' | 'console' | 'governance'

export interface ViewDef {
  id: ViewId
  label: string
  roles: readonly Role[]
}

export const VIEWS: readonly ViewDef[] = [
  { id: 'my-apps', label: 'My Apps', roles: ['user', 'admin'] },
  { id: 'console', label: 'Console', roles: ['admin'] },
  { id: 'governance', label: 'Posture & Governance', roles: ['admin'] },
]

export function canSee(view: ViewId, role: Role): boolean {
  return VIEWS.some((v) => v.id === view && v.roles.includes(role))
}

export function defaultViewFor(role: Role): ViewId {
  return role === 'admin' ? 'console' : 'my-apps'
}

export function hashFor(view: ViewId): string {
  return `#/${view}`
}

// Unknown hash, or a view the role may not see, falls back to the role default.
export function viewFromHash(hash: string, role: Role): ViewId {
  const id = hash.replace(/^#\/?/, '')
  const view = VIEWS.find((v) => v.id === id)
  if (!view || !canSee(view.id, role)) return defaultViewFor(role)
  return view.id
}
