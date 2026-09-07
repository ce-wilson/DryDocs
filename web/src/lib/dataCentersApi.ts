// The data-center spelling registry, read by the console (Z6).
//
// SEPARATE FROM graphApi.ts for corpusStatus.ts's exact reason: that module is
// the QuerySpec/named-query client and everything it fetches is a
// registry-reviewed graph read. This is CONFIG — a declared pairing in
// config/taxonomy/data-centers.yaml, no graph and no Cypher — and putting it
// behind the same client would blur the distinction ADR 0005 asks the console to
// keep visible.
//
// WHY THE CONSOLE NEEDS IT AT ALL. A folder's ControlMServer name is the SHORT
// Control-M code (`P32`); the `E####` default-time segment lives on the LONG
// form (`T032-E0700-DMA`), and short -> long is NOT derivable — BMC defines no
// format for a data-center name, so the pairing is a declared fact (LOAD2 (c)).
// Without this read the default-time seed has no route, and Z6's fallback clause
// would be unmeetable rather than merely unlabelled.

import { sessionId, sessionRejected, sessionToken } from './auth'
import type { Schemas } from './apiClient'
import { createAuthedApi, unwrap } from './apiClient'

export type DataCenterRow = Schemas['DataCenterOut']
export type DataCentersPayload = Schemas['DataCentersOut']

export async function fetchDataCenters(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<DataCentersPayload> {
  const api = createAuthedApi(baseUrl, { token: sessionToken, sessionId, rejected: sessionRejected })
  const result = await api.GET('/data-centers', { signal })
  if (result.response.status === 401) throw new Error('the server refused this session')
  return unwrap(result, 'data-centers')
}

/** Short Control-M code -> the long-form name that may carry an `E####`.
 *
 *  A Map rather than a lookup function so a caller can see the WHOLE pairing;
 *  the registry is small (a handful of rows) and a component that only ever
 *  asked one question at a time could not tell "no pairing declared" from "no
 *  registry loaded". */
export function longNameByCode(rows: readonly DataCenterRow[]): Map<string, string> {
  return new Map(rows.map((d) => [d.code, d.name]))
}

/** The registry's own declared default, where it declared one.
 *
 *  Preferred over re-parsing the long name: the file may record a default for a
 *  name whose segment we would not parse, and a declaration beats a derivation
 *  every time. The parse (`defaultTimeOf`) stays as the fallback for a row that
 *  carries the name and no explicit `default_time`. */
export function declaredDefaultByCode(rows: readonly DataCenterRow[]): Map<string, string> {
  return new Map(rows.filter((d) => d.default_time).map((d) => [d.code, d.default_time]))
}
