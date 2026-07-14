// The single role-gating registry: nav rendering, the hash guard, and the role
// default all read this map — role conditionals never scatter into components.
// Gating is cosmetic (client-side mock, see lib/auth.ts) until the O1 ADR.

import type { Persona, Role } from './auth'

export type ViewId = 'landing' | 'my-apps' | 'console' | 'governance'

export interface ViewDef {
  id: ViewId
  label: string
  roles: readonly Role[]
}

export const VIEWS: readonly ViewDef[] = [
  { id: 'landing', label: 'Overview', roles: ['user', 'admin'] },
  { id: 'my-apps', label: 'My Apps', roles: ['user', 'admin'] },
  { id: 'console', label: 'Console', roles: ['admin'] },
  { id: 'governance', label: 'Posture & Governance', roles: ['admin'] },
]

export function canSee(view: ViewId, role: Role): boolean {
  return VIEWS.some((v) => v.id === view && v.roles.includes(role))
}

export function defaultViewFor(role: Role): ViewId {
  return role === 'admin' ? 'landing' : 'my-apps'
}

// Tower drill-down access: admin drills any tower; a user only their own
// (persona.towerKey — the tower their ServiceNow-derived apps roll up to).
export function canDrill(towerKey: string, persona: Persona): boolean {
  return persona.role === 'admin' || persona.towerKey === towerKey
}

export interface Route {
  view: ViewId
  tower?: string
}

export function hashFor(view: ViewId): string {
  return `#/${view}`
}

export function hashForTower(towerKey: string): string {
  return `#/tower/${towerKey}`
}

export function hashForRoute(route: Route): string {
  return route.tower ? hashForTower(route.tower) : hashFor(route.view)
}

// Unknown hash, a view the role may not see, or a tower the persona may not
// drill, all fall back safely. `isTower` is injected so this module stays free
// of data imports (App passes the TOWERS membership test).
export function parseRoute(hash: string, persona: Persona, isTower: (key: string) => boolean): Route {
  const path = hash.replace(/^#\/?/, '')
  if (path.startsWith('tower/')) {
    const key = path.slice('tower/'.length)
    if (isTower(key) && canDrill(key, persona)) return { view: 'landing', tower: key }
    return { view: 'landing' }
  }
  const view = VIEWS.find((v) => v.id === path)
  if (!view || !canSee(view.id, persona.role)) return { view: defaultViewFor(persona.role) }
  return { view: view.id }
}
