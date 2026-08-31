import { sessionRejected, sessionToken } from './auth'
import { diagnoseNetworkFailure } from './reachability'
import type { GraphAccess, GraphResult, NamedResult, SpecExport, SpecResult } from './graph'

// The deployment adapter (ADR 0005): HTTP to the drydocs-api thin API.
// Sessions are server-side; this adapter READS the token the sign-in flow
// obtained and never obtains one itself. It must NEVER fall back to bolt
// silently, or the seam would leak the dev path into deployment behavior —
// every failure here is loud.
//
// O69 CHANGED THE 401 BEHAVIOUR, and the change is the point rather than a
// side effect. This client used to hold a persona id and silently log in
// again on any 401, which was only possible because logging in took no
// secret; a client that can re-authenticate itself out of a rejection is a
// client for which the rejection means nothing. Now a 401 is terminal: the
// local session is dropped, the app is told, and the user lands on the
// sign-in screen. Expiry and revocation therefore actually take effect.

interface ApiEnvelope {
  keys: string[]
  rows: Record<string, unknown>[]
  database: string
}

export async function readDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown }
    return typeof body.detail === 'string' ? body.detail : JSON.stringify(body)
  } catch {
    return res.statusText
  }
}

/** The shared HTTP client behind every drydocs-api surface (GraphAccess here;
 *  the O13 mappings client in mappingsApi.ts). One auth policy — read the
 *  session's token, treat a 401 as the end of that session — so no surface can
 *  drift its own behaviour on rejection. */
export interface ApiClient {
  authedPost(path: string, body: unknown): Promise<Response>
  authedGet(path: string): Promise<Response>
  /** The session's own bearer token. R5 hands it to the graph_qa agent as the
   *  R4 owner token, so ephemeral specs the agent registers resolve for THIS
   *  session's runSpec/exportSpec calls — which is why the Ask spoke must
   *  share ONE client between token and GraphAccess. Rejects when there is no
   *  session; it cannot create one. */
  getToken(): Promise<string>
}

// personaId is kept in the signature for the ~15 call sites that pass it and
// for the error text; it is no longer a credential, because it never was one.
export function createApiClient(baseUrl: string, personaId: string): ApiClient {
  async function post(path: string, body: unknown, bearer?: string): Promise<Response> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (bearer) headers.Authorization = `Bearer ${bearer}`
    try {
      return await fetch(`${baseUrl}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })
    } catch {
      // O85: same probe as the sign-in path. A blocked origin and a dead
      // server are indistinguishable to this catch, and asserting the second
      // sends the reader to start a server that is already running.
      throw new Error((await diagnoseNetworkFailure(baseUrl)).message)
    }
  }

  /** The held token, or a loud failure. There is deliberately no path from
   *  here to a new session: obtaining one needs a secret, which lives only in
   *  the sign-in form and is never stored. */
  function requireToken(): string {
    const token = sessionToken()
    if (!token) {
      sessionRejected()
      throw new Error(`not signed in as ${personaId} — the console session has ended`)
    }
    return token
  }

  /** A 401 means the server refused the token we hold. Retrying with the same
   *  token would just fail again, so drop the session and surface it. */
  function rejectIfUnauthorized(res: Response): Response {
    if (res.status === 401) sessionRejected()
    return res
  }

  return {
    async authedPost(path: string, body: unknown): Promise<Response> {
      return rejectIfUnauthorized(await post(path, body, requireToken()))
    },
    async authedGet(path: string): Promise<Response> {
      const res = await fetch(`${baseUrl}${path}`, {
        headers: { Authorization: `Bearer ${requireToken()}` },
      })
      return rejectIfUnauthorized(res)
    },
    async getToken(): Promise<string> {
      return requireToken()
    },
  }
}

export function createApiAccess(
  baseUrl: string,
  personaId: string,
  client: ApiClient = createApiClient(baseUrl, personaId),
): GraphAccess {
  const { authedPost, authedGet } = client

  async function envelope(path: string, body: unknown): Promise<ApiEnvelope> {
    const res = await authedPost(path, body)
    if (!res.ok) throw new Error(`api ${path} failed (${res.status}): ${await readDetail(res)}`)
    return (await res.json()) as ApiEnvelope
  }

  return {
    kind: 'api',
    async runRead(query: string): Promise<GraphResult> {
      const { keys, rows } = await envelope('/raw-cypher', { cypher: query })
      return { keys, rows }
    },
    async runNamed(queryId: string, params = {}): Promise<NamedResult> {
      const { keys, rows, database } = await envelope(`/query/${queryId}`, { params })
      return { keys, rows, database }
    },
    async runSpec(specId: string, params = {}): Promise<SpecResult> {
      const res = await authedPost(`/specs/${specId}/run`, { params })
      if (!res.ok) throw new Error(`spec ${specId} failed (${res.status}): ${await readDetail(res)}`)
      return (await res.json()) as SpecResult
    },
    async exportSpec(specId, params, format): Promise<SpecExport> {
      const res = await authedPost(`/specs/${specId}/export?format=${format}`, { params })
      if (!res.ok) throw new Error(`export ${specId} failed (${res.status}): ${await readDetail(res)}`)
      const blob = await res.blob() // stream fully consumed → manifest registered
      const manifestPath = res.headers.get('X-DryDocs-Manifest-Path')
      const disposition = res.headers.get('Content-Disposition') ?? ''
      const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `${specId}.${format}`
      if (!manifestPath) throw new Error('export missing manifest path header')
      const manifestRes = await authedGet(manifestPath)
      if (!manifestRes.ok) {
        throw new Error(`manifest fetch failed (${manifestRes.status}): ${await readDetail(manifestRes)}`)
      }
      const manifest = (await manifestRes.json()) as Record<string, unknown>
      return { filename, blob, manifest }
    },
  } satisfies GraphAccess
}
