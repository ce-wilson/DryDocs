import { sessionId, sessionRejected, sessionToken } from './auth'
import type { Schemas } from './apiClient'
import { createAuthedApi, unwrap } from './apiClient'

// R18 (d) — the client for /admin/qa-trace, the Ask decision trace.
//
// Beside the other API wrappers rather than inside the Ask route, for the reason
// WEB12 gave and logEstate.ts repeats: a route that builds its own client is a
// route with its own auth policy. This goes through `createAuthedApi`, so it
// inherits the token, the 401-ends-the-session rule and the O85 network
// diagnosis, and its path is checked against the generated schema.
//
// THE TRACE IS FETCHED, NEVER LINKED TO. A plain <a href> would reach the API
// with no bearer token and 401, so "the Ask UI links the visible run id to the
// trace" is implemented as a control that fetches and hands the person a file —
// the same shape every other authenticated read on this console has.
//
// WHY THE PAYLOAD IS THE GENERATED TYPE AND `records` STILL IS NOT: the server
// declares QaTraceOut (so the O70 every-JSON-route-declares-a-model guard is
// satisfied and this is not a hand-declared contract), but `records` is the
// writer's own JSONL replayed, and drydocs_api/schemas.py says why it stays
// untyped there: a declared record shape here would be a second contract free to
// disagree with the file the agent actually wrote.

export type QaTracePayload = Schemas['QaTraceOut']

export async function fetchQaTrace(
  baseUrl: string,
  query: { runId?: string; sessionId?: string },
  signal?: AbortSignal,
): Promise<QaTracePayload> {
  const api = createAuthedApi(baseUrl, { token: sessionToken, sessionId, rejected: sessionRejected })
  const result = await api.GET('/admin/qa-trace', {
    params: { query: { run_id: query.runId, session_id: query.sessionId } },
    signal,
  })

  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) {
    // A designation, not a fault — the same wording logEstate.ts uses, and for
    // the same reason: the trace carries prompt text and host-side detail an
    // admin is asking for and a user-tier persona is not.
    throw new Error('the Ask trace is an admin surface')
  }
  if (result.response.status === 422) {
    // The route refuses a call with no correlation key. Reachable only from a
    // caller that lost the run id, so it is said plainly rather than mapped
    // onto "not found" — the two have different fixes.
    throw new Error('a trace is looked up by run id — none was given')
  }
  return unwrap(result, 'admin/qa-trace')
}

/** The trace as a file the person keeps: pretty JSON, named by what it is of.
 *  Download rather than a rendered panel — acceptance (d) says "retrieve or
 *  download", and a run's trace is tens to hundreds of records whose value is
 *  in reading them beside the code, not in a viewport. */
export function traceFilename(payload: QaTracePayload): string {
  const key = payload.run_id || payload.session_id || 'unknown'
  return `qa-trace-${key.replace(/[^A-Za-z0-9._-]/g, '_')}.json`
}
