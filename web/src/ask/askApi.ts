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
  // R15: the label the spec's walk earned on this run, as the API graded it —
  // 'exact' | 'lower-bound' | null (ungraded). Rendered as given.
  epistemic?: string | null
  causes?: { cause: string; detail: string; count?: number | null }[]
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
  // R6 Tier-2 caps and whether they bit. Optional because an envelope from a
  // pre-R6 agent build has neither.
  budget?: { tokens_limit: number; tokens_used: number; exhausted: boolean }
  tier2?: { engaged: boolean; votes: string[]; forced_solve: boolean }
}

/** R6: one cumulative frame of the Tier-2 task graph. Edges are exactly the
 *  record lib/forceLayout.ts lays out, so no adapter sits between them. */
export interface TaskGraphSnapshot {
  iteration: number
  phase: 'start' | 'iteration' | 'final'
  nodes: { id: string; kind: string; label: string; iteration: number; rows: number | null }[]
  edges: { source: string; target: string; via: string }[]
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
  task_graph?: TaskGraphSnapshot[]
}

/** The R5 control part: the session's PUBLIC handle, and nothing else.
 *  ADR 0019 D1 — no credential rides in a message part; ADR 0020 — no api url
 *  either, because which drydocs-api the agent calls is the agent's own
 *  deployment fact (DRYDOCS_API_URL), not the page's to say. The agent
 *  authenticates itself; the handle only names the session its registrations
 *  belong to. askApi.test.ts pins both absences. */
export function controlPart(sessionId: string): AdkPart {
  return { text: JSON.stringify({ drydocs_control: { session_id: sessionId } }) }
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
  /** WEB12 (c): abort the turn. A stopped turn throws AskStopped, never an
   *  answer — the one thing a stop control must never produce is a result. */
  signal?: AbortSignal
}

/** The turn was stopped by the person asking. Distinct from an agent error and
 *  from a transport failure, because it renders differently and is nobody's
 *  fault: a stopped turn is a stopped turn, not a failed one. */
export class AskStopped extends Error {
  constructor() {
    super('stopped')
    this.name = 'AskStopped'
  }
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
  const { adkUrl, app, userId, sessionId, question, control, onStep, signal } = opts
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
    await runAgentSse(adkUrl, app, userId, sessionId, parts, handle, signal)
  } catch (err) {
    // A STOP is not a transport failure. Falling back to the non-streaming
    // endpoint here would restart the very turn the person just stopped, which
    // is worse than not offering the control at all.
    if (signal?.aborted) throw new AskStopped()
    void err
    const events = await runAgentParts(adkUrl, app, userId, sessionId, parts)
    events.forEach(handle)
  }
  if (signal?.aborted) throw new AskStopped()
  if (!final) throw new Error('agent returned no envelope — is the graph_qa app selected?')
  return final
}
