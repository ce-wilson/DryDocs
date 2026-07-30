// Ask-spoke client (R5): types for the graph_qa answer envelope (the ADR
// 0007 contract in agents/graph_qa/README.md), the control-part builder that
// forwards this session's drydocs-api token to the agent (the R4 owner-token
// handshake — control.py owns the shape server-side), and the event parser
// that splits the ADK stream into live step events + the final envelope.
//
// O20 stands here in full: everything this module touches is a READ — the
// agent's Cypher runs server-side in READ mode, and the only "state" the UI
// creates is TTL-bounded ephemeral specs owned by its own session.

import { createSession, runAgentParts, runAgentSse, type AdkEvent, type AdkPart } from '../lib/adk'

export interface AskStep {
  i: number
  kind: string // 'router' | 'spec' | 'text2cypher' | 'answer'
  ms: number
  spec_id?: string | null
  cypher?: string | null
  database?: string | null
  rows?: number | null
  truncated?: boolean
  fix_retries?: number
  error?: string | null
  explore_ref?: string | null // R4: eph.<hash> — runs/exports via /specs/{ref}
}

export interface AskSource {
  document: string // 'spec:<id>' | 'text2cypher:<db>'
  trust: string // 'CONFIRMED' | 'SYNTHESIZED'
  fetched_at?: string | null
  stale?: boolean | null
}

export interface AskMetrics {
  iterations: number
  llm_calls: number
  tokens: { prompt: number; completion: number; total: number }
  context: Record<string, number>
  memory: Record<string, number>
  cost_est_usd?: number | null
  response_ms: Record<string, number>
}

export interface AskEnvelope {
  status?: string
  error?: string
  run_id?: string
  tier?: string
  answer?: string
  model?: string | null
  steps?: AskStep[]
  sources?: AskSource[]
  metrics?: AskMetrics
}

export function controlPart(apiToken: string, apiUrl: string): AdkPart {
  return { text: JSON.stringify({ drydocs_control: { api_token: apiToken, api_url: apiUrl } }) }
}

type Parsed = { kind: 'step'; step: AskStep } | { kind: 'final'; envelope: AskEnvelope } | null

export function parseAdkEvent(event: AdkEvent): Parsed {
  const text = event.content?.parts?.[0]?.text
  if (!text) return null
  let payload: Record<string, unknown>
  try {
    payload = JSON.parse(text) as Record<string, unknown>
  } catch {
    return null
  }
  if (payload.kind === 'step' && typeof payload.step === 'object' && payload.step !== null) {
    return { kind: 'step', step: payload.step as AskStep }
  }
  if (typeof payload.status === 'string') {
    return { kind: 'final', envelope: payload as AskEnvelope }
  }
  return null
}

export interface AskOptions {
  adkUrl: string
  app: string
  userId: string
  sessionId: string
  question: string
  /** the R4 handshake — omit to ask without explore_refs (agent still answers) */
  control?: AdkPart
  onStep: (step: AskStep) => void
}

let sessionReady: string | null = null

export async function ensureSession(adkUrl: string, app: string, userId: string, sessionId: string): Promise<void> {
  const key = `${adkUrl}|${app}|${userId}|${sessionId}`
  if (sessionReady === key) return
  await createSession(adkUrl, app, userId, sessionId)
  sessionReady = key
}

/** Ask one question: streams step events into `onStep` as the agent works
 *  (SSE), falling back to the buffered /run when streaming isn't available —
 *  steps then arrive together with the answer, visibly but not live. */
export async function ask(opts: AskOptions): Promise<AskEnvelope> {
  const { adkUrl, app, userId, sessionId, question, control, onStep } = opts
  const parts: AdkPart[] = control ? [{ text: question }, control] : [{ text: question }]
  await ensureSession(adkUrl, app, userId, sessionId)

  let final: AskEnvelope | null = null
  const handle = (event: AdkEvent) => {
    const parsed = parseAdkEvent(event)
    if (!parsed) return
    if (parsed.kind === 'step') onStep(parsed.step)
    else final = parsed.envelope
  }

  try {
    await runAgentSse(adkUrl, app, userId, sessionId, parts, handle)
  } catch {
    const events = await runAgentParts(adkUrl, app, userId, sessionId, parts)
    events.forEach(handle)
  }
  if (!final) throw new Error('agent returned no envelope — is the graph_qa app selected?')
  return final
}
