import neo4j, { Driver } from 'neo4j-driver'
import type { GraphAccess, GraphResult } from './graph'

// THE BOLT ADAPTER — a dev-mode tool, not the deployment path (ADR 0005).
// Only createBoltAccess is exported: console code reaches this module solely
// through the GraphAccess seam, and callers must gate on graph.boltAllowed()
// (dev build + admin role). Credentials are form-entered at runtime; never
// seed them from VITE_* env (Vite inlines those into the built bundle).

// One driver per page — the driver owns a connection pool; recreating it per
// query leaks WebSocket connections (the classic browser-driver mistake and
// the first thing to check in a heap-snapshot diff).
let driver: Driver | null = null
let driverKey = ''

function getDriver(uri: string, user: string, password: string): Driver {
  const key = `${uri}|${user}|${password}`
  if (driver && driverKey === key) return driver
  if (driver) void driver.close() // settings changed: release the old pool
  driver = neo4j.driver(uri, neo4j.auth.basic(user, password))
  driverKey = key
  return driver
}

async function runCypher(
  uri: string,
  user: string,
  password: string,
  database: string,
  query: string,
): Promise<GraphResult> {
  const session = getDriver(uri, user, password).session({
    database,
    defaultAccessMode: neo4j.session.READ,
  })
  try {
    const result = await session.run(query)
    return {
      keys: result.records[0]?.keys.map(String) ?? [],
      rows: result.records.map((r) => {
        const obj = r.toObject()
        for (const k of Object.keys(obj)) {
          const v = obj[k]
          if (neo4j.isInt(v)) obj[k] = v.toNumber()
        }
        return obj
      }),
    }
  } finally {
    await session.close() // sessions are per-query; never cache them
  }
}

export interface BoltSettings {
  uri: string
  user: string
  password: string
  database: string
}

export function createBoltAccess(s: BoltSettings): GraphAccess {
  return {
    kind: 'bolt',
    runRead: (query) => runCypher(s.uri, s.user, s.password, s.database, query),
    // Named views are api-path only: their Cypher lives in drydocs-api's
    // registry (server-side payload shaping, ADR 0005). Falling back to a
    // browser-side copy here would fork the query definitions — fail loud.
    runNamed: async () => {
      throw new Error(
        'named view queries are api-path only (ADR 0005) — the bolt adapter is the ' +
          'raw-Cypher dev bench and has no server-side query registry',
      )
    },
  } satisfies GraphAccess
}
