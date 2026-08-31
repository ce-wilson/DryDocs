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
import { diagnoseNetworkFailure } from './reachability'

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
  const token = sessionToken()
  if (!token) {
    sessionRejected()
    throw new Error('not signed in — the console session has ended')
  }

  let res: Response
  try {
    res = await fetch(`${baseUrl}/docs-verify`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new Error((await diagnoseNetworkFailure(baseUrl)).message)
  }

  if (res.status === 401) {
    sessionRejected()
    throw new Error('the server refused this session')
  }
  if (res.status === 403) {
    // Steward+admin, matching /gates and /software. Said plainly rather than as
    // a generic failure: this is a designation, not a fault.
    throw new Error('this reconciliation is an SME surface — steward or admin only')
  }
  if (!res.ok) throw new Error(`docs-verify failed (${res.status})`)

  return (await res.json()) as CorpusStatusPayload
}
