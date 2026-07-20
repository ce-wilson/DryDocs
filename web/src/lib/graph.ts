// The GraphAccess seam (ADR 0005): the ONLY way console code reads the graph.
// Two adapters implement it — `bolt` (lib/neo4j.ts, a DEV-MODE tool only) and
// `api` (lib/graphApi.ts, the deployment path — real once drydocs-api lands,
// backlog O5). View components import THIS interface, never neo4j-driver;
// tsc enforces adapter conformance (`satisfies GraphAccess` in each adapter).

import type { Role } from './auth'

export interface GraphResult {
  keys: string[]
  rows: Record<string, unknown>[]
}

/** A named-view result also names the database the server routed it to —
 *  the trust boundary made visible (ADR 0002: drydocs vs drydocs_all is a
 *  SERVER routing decision; the client only ever learns it after the fact). */
export interface NamedResult extends GraphResult {
  database: string
}

export interface GraphAccess {
  readonly kind: 'bolt' | 'api'
  /** Read-only query execution. Raw Cypher is a dev/admin affordance only. */
  runRead(query: string): Promise<GraphResult>
  /** Named view query (ADR 0005 decision 2): payload shaping lives server-side
   *  in drydocs-api's query registry — never duplicated in the browser. The
   *  api adapter POSTs /query/{id}; bolt has no registry and fails loud. */
  runNamed(queryId: string, params?: Record<string, unknown>): Promise<NamedResult>
}

// The explicit dev flag + role gate for the bolt adapter (ADR 0005 decision 4):
// import.meta.env.DEV is baked in at build time, so production bundles have the
// bolt path unreachable BY CONSTRUCTION — no runtime toggle can re-enable it.
export function boltAllowed(role: Role): boolean {
  return import.meta.env.DEV && role === 'admin'
}
