// Thin client for the ADK api_server REST surface, reached as `/agent` on the
// page's own origin (agentBaseUrl(); the proxy forwards to the ADK server - ADR 0020).
// Endpoints per https://adk.dev/runtime/api-server/
//
// WEB8 (b): THE CONTRACT IS HAND-DECLARED, AND HERE IS WHY IT IS NOT GENERATED.
// The acceptance offered two shapes — a schema the agent server publishes with a
// generated client on the drydocs-api pattern, or a hand-declared contract in one
// module with a drift test against a recorded fixture. The second, on three
// grounds, none of them taste:
//
//   1. THE SERVER IS NOT OURS. agents/serve.py hands its work to Google's
//      `get_fast_api_app`. Generating a client from that schema would commit a
//      VENDOR's API surface as a repo artifact and re-churn it on every ADK
//      upgrade, and the only thing we would be guarding is whether we copied
//      Google's file correctly.
//   2. NO JOB HERE CAN REGENERATE IT. `google-adk` lives in agents/.venv, not the
//      repo interpreter — tests/unit/test_session_redaction.py skips for exactly
//      this reason — so a committed dump could not be drift-checked in CI. That
//      is the determinism argument drydocs_api/corpus_status.py already used to
//      reject a generated artifact, applied to the same facts.
//   3. THE RECORDING ALREADY EXISTS AND IS BETTER EVIDENCE. tests/stub_adk.py
//      reproduces this contract, tests/fixtures/adk/stub-run-sse.txt is its
//      recorded stream asserted byte-for-byte on the python side, and
//      ask/stubStream.test.ts parses that recording with the REAL parser. What
//      was missing was never a schema — it was that the declarations below could
//      not fail: `AdkEvent` carried an index signature, so every shape satisfied
//      it, and `asJson` returned `any`, so every claim about a body was a cast.
//      Both are gone, and `isAdkEvent` ties the types to the recording.
//
// The types are what the CONSOLE reads, not everything ADK sends. Every field is
// optional because the vendor may add or omit any of them; the guard below is a
// MINIMUM, and says so.

/** One part of a message. The console only ever reads `text`. */
export interface AdkPart {
  text: string
}

/** An event's content. `parts` is where askApi.parseAdkEvent finds its payload. */
export interface AdkContent {
  role?: string
  parts?: { text?: string }[]
}

/** An agent event as the console reads it. NOT the vendor's whole event — the
 *  fields below are the ones anything here touches, which is why there is no
 *  index signature: one made every object an AdkEvent and the type a decoration. */
export interface AdkEvent {
  author?: string
  content?: AdkContent
}

/** A MINIMUM shape check, not a validation of the vendor's event.
 *
 *  It answers the only question the console asks of a frame: is this an object
 *  whose `content.parts` — if present at all — is something parseAdkEvent can
 *  walk without throwing? Everything is optional, so a bare `{}` passes, and
 *  that is correct: an event with no text is one parseAdkEvent returns null for,
 *  which is a handled case and not a malformed frame. What this rejects is the
 *  shape that would throw: a non-object, or `parts` that is not an array. */
export function isAdkEvent(value: unknown): value is AdkEvent {
  if (typeof value !== 'object' || value === null) return false
  const { content } = value as { content?: unknown }
  if (content === undefined) return true
  if (typeof content !== 'object' || content === null) return false
  const { parts } = content as { parts?: unknown }
  if (parts === undefined) return true
  return Array.isArray(parts) && parts.every((p) => typeof p === 'object' && p !== null)
}

/** The body of a 2xx, UNTYPED — every caller narrows it. It returned `any`
 *  before, which is how three functions came to claim a type they never checked. */
async function asJson(res: Response): Promise<unknown> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  return res.json()
}

function adkEvents(body: unknown, what: string): AdkEvent[] {
  if (!Array.isArray(body) || !body.every(isAdkEvent)) {
    throw new Error(`${what}: the agent server did not return a list of events`)
  }
  return body
}

export async function listApps(baseUrl: string): Promise<string[]> {
  const body = await asJson(await fetch(`${baseUrl}/list-apps`))
  if (!Array.isArray(body) || !body.every((n) => typeof n === 'string')) {
    throw new Error('list-apps: the agent server did not return a list of app names')
  }
  return body
}

/** Create the session a run will attach to. Returns nothing on purpose: the
 *  server answers with a session object and NEITHER caller reads it — declaring
 *  a shape the console discards would be a claim with no consumer to keep it
 *  honest, and this surface has no recording behind it (the fixture covers
 *  /run_sse only). */
export async function createSession(
  baseUrl: string,
  app: string,
  userId: string,
  sessionId: string,
): Promise<void> {
  await asJson(
    await fetch(`${baseUrl}/apps/${app}/users/${userId}/sessions/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }),
  )
}

export function runAgent(
  baseUrl: string,
  app: string,
  userId: string,
  sessionId: string,
  text: string,
): Promise<AdkEvent[]> {
  return runAgentParts(baseUrl, app, userId, sessionId, [{ text }])
}

function runBody(app: string, userId: string, sessionId: string, parts: AdkPart[]) {
  return JSON.stringify({
    appName: app,
    userId,
    sessionId,
    newMessage: { role: 'user', parts },
    streaming: false,
  })
}

/** Multi-part run — the Ask spoke sends [question, control] parts (R5); the
 *  control part carries the drydocs-api session token the agent needs to
 *  register ephemeral specs owned by THIS session (R4 wiring). */
export function runAgentParts(
  baseUrl: string,
  app: string,
  userId: string,
  sessionId: string,
  parts: AdkPart[],
): Promise<AdkEvent[]> {
  return fetch(`${baseUrl}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: runBody(app, userId, sessionId, parts),
  })
    .then(asJson)
    .then((body) => adkEvents(body, 'run'))
}

/** Streamed run over the api_server's SSE endpoint: each yielded agent event
 *  arrives as a `data: {...}` frame and is handed to `onEvent` as it lands —
 *  the Ask spoke renders step events live this way. The caller falls back to
 *  runAgentParts when this rejects (older ADK, proxy without SSE). */
export async function runAgentSse(
  baseUrl: string,
  app: string,
  userId: string,
  sessionId: string,
  parts: AdkPart[],
  onEvent: (event: AdkEvent) => void,
  // WEB12 (c): the ONE surface with genuinely unbounded latency is the one that
  // must be stoppable. No deadline here on purpose — an agent may legitimately
  // take minutes — but a person must be able to end the turn, and the fetch and
  // the reader BOTH have to hear about it or the stream keeps arriving.
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${baseUrl}/run_sse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: runBody(app, userId, sessionId, parts),
    signal,
  })
  if (!res.ok || !res.body) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const stop = () => void reader.cancel()
  signal?.addEventListener('abort', stop)
  for (;;) {
    if (signal?.aborted) break
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // SSE frames are separated by a blank line; each carries `data: <json>`.
    let boundary = buffer.indexOf('\n\n')
    while (boundary >= 0) {
      const frame = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      for (const line of frame.split('\n')) {
        if (!line.startsWith('data:')) continue
        try {
          // WEB8: narrowed, not cast. A frame that is not event-shaped is
          // skipped exactly like an unparseable one — both are the same
          // "partial/noise" case, and the envelope re-carries everything.
          const frameEvent: unknown = JSON.parse(line.slice(5).trim())
          if (isAdkEvent(frameEvent)) onEvent(frameEvent)
        } catch {
          // partial/noise frame — skip; the final envelope re-carries everything
        }
      }
      boundary = buffer.indexOf('\n\n')
    }
  }
}
