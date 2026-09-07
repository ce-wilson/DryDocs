import { sessionId, sessionRejected, sessionToken } from './auth'
import type { Schemas } from './apiClient'
import { createAuthedApi, unwrap } from './apiClient'

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
// WEB8 CLOSED THIS ONE. The note that stood here said the response type was
// hand-declared because /admin/log-estate returned a free `dict` server-side
// "until drydocs_api.schemas models it, which is WEB8's list". It does now, so
// these are aliases of the generated schema and the `unwrapAs` marker is gone
// with the last of its call sites.
//
// Worth keeping from that note: this route was added by O68, AFTER O70 drew up
// the follow-up list, so it opened the same hole a second time and no test
// noticed. The schema guard now runs the other way round — every JSON route
// must declare a model — so the next route added this way fails rather than
// joins a list.

export type LogKindRow = Schemas['LogKindOut']
export type DataZoneRow = Schemas['LogZoneOut']
export type LogEstatePayload = Schemas['LogEstateOut']

export async function fetchLogEstate(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<LogEstatePayload> {
  const api = createAuthedApi(baseUrl, { token: sessionToken, sessionId, rejected: sessionRejected })
  const result = await api.GET('/admin/log-estate', { signal })

  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) {
    // Said plainly rather than as a generic failure: this is a designation, not
    // a fault. The estate names real paths on the host's disk, which is
    // operational detail an admin is asking for and a user-tier persona is not.
    throw new Error('the log estate is an admin surface')
  }
  return unwrap(result, 'admin/log-estate')
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
