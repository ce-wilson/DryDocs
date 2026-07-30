// Thin client for the ADK api_server REST surface (default http://localhost:8000).
// Endpoints per https://adk.dev/runtime/api-server/

export interface AdkEvent {
  author?: string
  content?: { role?: string; parts?: { text?: string }[] }
  [k: string]: unknown
}

async function asJson(res: Response) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  return res.json()
}

export function listApps(baseUrl: string): Promise<string[]> {
  return fetch(`${baseUrl}/list-apps`).then(asJson)
}

export function createSession(
  baseUrl: string,
  app: string,
  userId: string,
  sessionId: string,
): Promise<unknown> {
  return fetch(`${baseUrl}/apps/${app}/users/${userId}/sessions/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  }).then(asJson)
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

export interface AdkPart {
  text: string
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
  }).then(asJson)
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
): Promise<void> {
  const res = await fetch(`${baseUrl}/run_sse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: runBody(app, userId, sessionId, parts),
  })
  if (!res.ok || !res.body) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
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
          onEvent(JSON.parse(line.slice(5).trim()) as AdkEvent)
        } catch {
          // partial/noise frame — skip; the final envelope re-carries everything
        }
      }
      boundary = buffer.indexOf('\n\n')
    }
  }
}
