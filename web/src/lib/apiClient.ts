import createClient from 'openapi-fetch'

import type { components, paths } from '../generated/api'
import { diagnoseNetworkFailure } from './reachability'

// O70. The console's HTTP layer: openapi-fetch over the GENERATED `paths` type
// (src/generated/api.d.ts, from drydocs-api's own OpenAPI schema), so every
// request path, path/query parameter and JSON body is checked against the
// server's declaration at compile time, and a response is typed wherever the
// server declares one (drydocs_api.schemas). The hand-written fetch wrappers
// this replaces restated the API from memory with nothing guarding them — an
// API change was a runtime surprise; now it is a `tsc -b` error.
//
// Two flavours, one policy each:
//   public — no session: /login, /health, the /specs list the Ask page reads.
//   authed — reads the session's token on every request and treats a 401 as
//            the END of that session (O69: a client that can re-authenticate
//            itself out of a rejection is a client for which the rejection
//            means nothing). It must never fall back to bolt silently.
// Both route a network failure through the O85 probe, because a dead server and
// a blocked origin are the same TypeError to fetch and the message must say which.
//
// The session hooks are INJECTED rather than imported from lib/auth so that
// auth.ts can use the public client for /login without a module cycle.

export type Api = ReturnType<typeof createClient<paths>>
export type Schemas = components['schemas']
export type { paths }

/** What the authed client needs from the session layer (lib/auth.ts). */
export interface SessionHooks {
  /** the held bearer token, or null when signed out */
  token(): string | null
  /** the server (or the absence of a token) ended the session: drop it, tell the app */
  rejected(): void
}

function diagnosingFetch(baseUrl: string): (request: Request) => Promise<Response> {
  return async (request) => {
    try {
      return await globalThis.fetch(request)
    } catch {
      throw new Error((await diagnoseNetworkFailure(baseUrl)).message)
    }
  }
}

/** A client with no session: sign-in, health, and the public spec list. */
export function createPublicApi(baseUrl: string): Api {
  return createClient<paths>({ baseUrl, fetch: diagnosingFetch(baseUrl) })
}

/** The held token, or a loud failure. There is deliberately no path from here
 *  to a new session: obtaining one needs a secret, which lives only in the
 *  sign-in form and is never stored. */
export function requireToken(session: SessionHooks, personaId?: string): string {
  const token = session.token()
  if (!token) {
    session.rejected()
    const who = personaId ? ` as ${personaId}` : ''
    throw new Error(`not signed in${who} — the console session has ended`)
  }
  return token
}

/** A client that sends the session's bearer token and ends the session on 401. */
export function createAuthedApi(baseUrl: string, session: SessionHooks, personaId?: string): Api {
  const api = createPublicApi(baseUrl)
  api.use({
    onRequest({ request }) {
      request.headers.set('Authorization', `Bearer ${requireToken(session, personaId)}`)
      return request
    },
    onResponse({ response }) {
      // A 401 means the server refused the token we hold. Retrying with the same
      // token would just fail again, so drop the session and surface it.
      if (response.status === 401) session.rejected()
      return response
    },
  })
  return api
}

/** What a refused response said. FastAPI puts a string (or a 422's list) under
 *  `detail`; a non-JSON body arrives as text; anything else is quoted whole. */
export function detailOf(error: unknown, response: Response): string {
  if (typeof error === 'string' && error) return error
  if (error && typeof error === 'object') {
    const detail = (error as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
    return JSON.stringify(error)
  }
  return response.statusText
}

/** The typed body of a successful call, or a thrown Error naming the call and
 *  the server's refusal. openapi-fetch never throws on a non-2xx status — it
 *  returns `error` beside `response` — so this is the one place the wrappers'
 *  "<what> failed (<status>): <detail>" messages come from. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }, what: string): T {
  if (result.error !== undefined || !result.response.ok) {
    throw new Error(`${what} failed (${result.response.status}): ${detailOf(result.error, result.response)}`)
  }
  return result.data as T
}

/** `unwrap` for a route the server still declares as a FREE OBJECT. The type
 *  the caller names is a claim the console makes about the wire, not one the
 *  schema backs — which is why this is a separate function with a separate
 *  name: every call site of it is a route drydocs_api.schemas has not modelled
 *  yet, and the list of them is the follow-up O70 left. When the server
 *  declares the shape, the call becomes a plain `unwrap` and the hand type an
 *  alias of the schema. */
export function unwrapAs<T>(result: { data?: unknown; error?: unknown; response: Response }, what: string): T {
  return unwrap(result, what) as T
}
