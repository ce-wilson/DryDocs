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

import { sessionId, sessionRejected, sessionToken } from './auth'
import type { Schemas } from './apiClient'
import { createAuthedApi, unwrap } from './apiClient'

// WEB8: these were hand-declared interfaces while /docs-verify answered with a
// free object. The server declares the shape now, so they are ALIASES of the
// generated schema — the names stay because the pages import them, but the
// definition has exactly one home. Why each field is on the wire (the O56
// honesty rule behind `databases_queried`, the server-sent `statuses`
// vocabulary) is recorded where the shape is now decided: CorpusStatusOut in
// drydocs_api/schemas.py.
export type CorpusRow = Schemas['CorpusRowOut']
export type CorpusStatusPayload = Schemas['CorpusStatusOut']

export async function fetchCorpusStatus(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<CorpusStatusPayload> {
  // O70: the typed client owns the token, the 401 → session-ended rule and the
  // O85 network diagnosis; the path is checked against the schema. WEB8: the
  // RESPONSE is now checked too — the server declares CorpusStatusOut, so this
  // is a plain `unwrap` and the payload type is the generated one.
  const api = createAuthedApi(baseUrl, { token: sessionToken, sessionId, rejected: sessionRejected })
  const result = await api.GET('/docs-verify', { signal })

  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) {
    // Steward+admin, matching /gates and /software. Said plainly rather than as
    // a generic failure: this is a designation, not a fault.
    throw new Error('this reconciliation is an SME surface — steward or admin only')
  }
  return unwrap(result, 'docs-verify')
}
