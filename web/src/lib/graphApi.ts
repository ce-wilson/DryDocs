import type { GraphAccess, GraphResult, NamedResult } from './graph'

// The deployment adapter (ADR 0005): HTTP to the drydocs-api thin API.
// Sessions are server-side — the adapter exchanges the signed-in persona id
// for an opaque bearer token (the O5 auth stub; enterprise OIDC replaces the
// exchange company-side) and retries ONCE on 401 (server restart drops the
// in-memory session store). It must NEVER fall back to bolt silently, or the
// seam would leak the dev path into deployment behavior — every failure here
// is loud.

interface ApiEnvelope {
  keys: string[]
  rows: Record<string, unknown>[]
  database: string
}

async function readDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown }
    return typeof body.detail === 'string' ? body.detail : JSON.stringify(body)
  } catch {
    return res.statusText
  }
}

export function createApiAccess(baseUrl: string, personaId: string): GraphAccess {
  let token: string | null = null

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
      throw new Error(
        `drydocs-api unreachable at ${baseUrl} — start it with: ` +
          'poetry run uvicorn drydocs_api.app:create_app --factory --port 8001',
      )
    }
  }

  async function login(): Promise<string> {
    const res = await post('/login', { persona_id: personaId })
    if (!res.ok) throw new Error(`api login failed (${res.status}): ${await readDetail(res)}`)
    const session = (await res.json()) as { token: string }
    token = session.token
    return token
  }

  async function authedPost(path: string, body: unknown): Promise<Response> {
    let res = await post(path, body, token ?? (await login()))
    if (res.status === 401) res = await post(path, body, await login()) // stale session: one retry
    return res
  }

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
  } satisfies GraphAccess
}
