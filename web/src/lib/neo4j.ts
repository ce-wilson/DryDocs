import neo4j, { Driver } from 'neo4j-driver'

// One driver per page — the driver owns a connection pool; recreating it per
// query leaks WebSocket connections (the classic browser-driver mistake and
// the first thing to check in a heap-snapshot diff).
let driver: Driver | null = null
let driverKey = ''

export function getDriver(uri: string, user: string, password: string): Driver {
  const key = `${uri}|${user}|${password}`
  if (driver && driverKey === key) return driver
  if (driver) void driver.close() // settings changed: release the old pool
  driver = neo4j.driver(uri, neo4j.auth.basic(user, password))
  driverKey = key
  return driver
}

export interface CypherResult {
  keys: string[]
  rows: Record<string, unknown>[]
}

export async function runCypher(
  uri: string,
  user: string,
  password: string,
  database: string,
  query: string,
): Promise<CypherResult> {
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
