// The docs-verify read path (O58).
//
// SEPARATE FROM graphApi.ts ON PURPOSE. That module is the QuerySpec/named-query
// client — everything it fetches is a registry-reviewed read. This one endpoint
// is not a spec and cannot be (the reconciliation sweeps more than one database,
// and it needs SHOW DATABASES), so putting it behind the same client would blur
// exactly the distinction ADR 0005 asks the console to keep visible. Its own
// file, its own function, and the reason written down.
//
// The token comes from the session the same way every other authed call gets it;
// the request carries NO parameters, because the server chooses every query.

import { sessionRejected, sessionToken } from './auth'
import { createAuthedApi, unwrapAs } from './apiClient'

export interface CorpusRow {
  corpus_id: string
  target_db: string
  status: string
  documents: number
  chunks: number
  detail: string
  ok: boolean
}

export interface CorpusStatusPayload {
  classification: string
  /** Every database the sweep intends to visit. */
  databases_swept: string[]
  /** Those the server actually has. The difference is what the page must render
   *  as "not queried" rather than as zero rows (the O56 honesty rule). */
  databases_queried: string[]
  /** The status vocabulary, from the server. Never hand-copied into the UI. */
  statuses: string[]
  rows: CorpusRow[]
}

export async function fetchCorpusStatus(baseUrl: string): Promise<CorpusStatusPayload> {
  // O70: the typed client owns the token, the 401 → session-ended rule and the
  // O85 network diagnosis; the path is checked against the schema. The
  // response type is still hand-declared — /docs-verify is a free object
  // server-side until drydocs_api.schemas models it.
  const api = createAuthedApi(baseUrl, { token: sessionToken, rejected: sessionRejected })
  const result = await api.GET('/docs-verify')

  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) {
    // Steward+admin, matching /gates and /software. Said plainly rather than as
    // a generic failure: this is a designation, not a fault.
    throw new Error('this reconciliation is an SME surface — steward or admin only')
  }
  return unwrapAs<CorpusStatusPayload>(result, 'docs-verify')
}
