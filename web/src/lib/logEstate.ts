import { sessionRejected, sessionToken } from './auth'
import { createAuthedApi, unwrapAs } from './apiClient'

// O68 — the client for /admin/log-estate.
//
// Beside the other API wrappers rather than inside the panel, for the reason
// WEB12 gave: a route that builds its own client is a route with its own auth
// policy. This one goes through `createAuthedApi`, so it inherits the token, the
// 401-ends-the-session rule and the O85 network diagnosis, and its path is
// checked against the generated schema.
//
// NOT THROUGH THE QuerySpec SEAM, deliberately. That seam reads the GRAPH, and
// its provenance vocabulary — live / empty / demo — is about what the graph
// answered. This reads the HOST'S DISK. Routing it through useGraphQuery would
// attach a claim ("live from the graph") that is simply false, on a page whose
// entire subject is where things actually are.
//
// THE RESPONSE TYPE IS HAND-DECLARED, and says so: /admin/log-estate returns a
// free `dict` server-side until drydocs_api.schemas models it, which is WEB8's
// list and not this item's. `unwrapAs` is the marker for exactly that — every
// call site of it is a route the schema has not modelled yet.

export interface LogKindRow {
  id: string
  level: string
  retention_days: number
  rotation: string
  format: string
  status: string
  dir: string | null
  path: string
  exists: boolean
  file_count: number
  total_bytes: number
  /** Age of the oldest file on disk, or null when there are none. The half of
   *  the retention question the declaration cannot answer. */
  oldest_days: number | null
  over_retention: boolean
}

export interface DataZoneRow {
  id: string
  path: string
  mode: string | null
  exists: boolean
  file_count: number
  total_bytes: number
  empty: boolean
}

export interface LogEstatePayload {
  kinds: LogKindRow[]
  zones: DataZoneRow[]
}

export async function fetchLogEstate(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<LogEstatePayload> {
  const api = createAuthedApi(baseUrl, { token: sessionToken, rejected: sessionRejected })
  const result = await api.GET('/admin/log-estate', { signal })

  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) {
    // Said plainly rather than as a generic failure: this is a designation, not
    // a fault. The estate names real paths on the host's disk, which is
    // operational detail an admin is asking for and a user-tier persona is not.
    throw new Error('the log estate is an admin surface')
  }
  return unwrapAs<LogEstatePayload>(result, 'admin/log-estate')
}

/** Bytes as a person reads them. Base 1024, one decimal — the panel is about
 *  orders of magnitude ("is this 4 MB or 4 GB"), not exact accounting. */
export function humanBytes(n: number): string {
  if (n < 1024) return `${n} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let value = n / 1024
  let i = 0
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024
    i += 1
  }
  return `${value.toFixed(1)} ${units[i]}`
}
