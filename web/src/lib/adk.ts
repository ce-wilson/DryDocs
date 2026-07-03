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
  return fetch(`${baseUrl}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      appName: app,
      userId,
      sessionId,
      newMessage: { role: 'user', parts: [{ text }] },
      streaming: false,
    }),
  }).then(asJson)
}
