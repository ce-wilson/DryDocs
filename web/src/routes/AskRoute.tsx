import { useEffect, useMemo, useRef, useState } from 'react'
import ModuleToolbar from '../layout/ModuleToolbar'
import EmptyState from '../components/ui/EmptyState'
import SpecGrid from '../explorer/SpecGrid'
import { createApiAccess, createApiClient } from '../lib/graphApi'
import { ask, controlPart, type AskEnvelope, type AskSource, type AskStep } from '../ask/askApi'
import TaskGraphPane from '../ask/TaskGraphPane'
import type { Persona } from '../lib/auth'

// The Ask spoke (R5 / ADR 0007): free-text Q&A over the knowledge graph for
// EVERY persona — the agent tier does the reasoning, the server does the
// governance. Zero graph writes from this path (O20): the agent's Cypher runs
// in READ mode server-side, and the only state this page causes is the
// TTL-bounded ephemeral specs (R4) owned by its own drydocs-api session —
// which is exactly what makes Open-in-Explorer/Export possible WITHOUT the
// browser ever submitting raw Cypher. The admin console bench (/console)
// stays as-is for dev use; this page is the end-user surface.

interface Turn {
  id: number
  question: string
  steps: AskStep[]
  envelope: AskEnvelope | null
  error: string | null
  running: boolean
}

// O64: ONE completed turn per persona survives navigation, in browser-local
// storage for this phase. Completed turns only — the write site below runs
// solely on a success envelope, and the read here refuses anything else — so
// neither an in-flight spinner nor a stale error can be re-presented as
// current. Explore-refs inside a restored turn keep their existing TTL
// behavior: SpecGrid's fallback shows the expired-ref empty state, the turn
// itself still renders.
const LAST_TURN_PREFIX = 'drydocs.ask.last-turn.v1.'

function lastTurnKey(personaId: string): string {
  return `${LAST_TURN_PREFIX}${personaId}`
}

function loadLastTurn(personaId: string): Turn[] {
  try {
    const raw = localStorage.getItem(lastTurnKey(personaId))
    if (!raw) return []
    const turn = JSON.parse(raw) as Turn
    if (!turn || typeof turn.question !== 'string' || !turn.envelope) return []
    // id 0 keeps the restored turn clear of the session counter (fresh asks
    // start at id 1; a colliding id would make patch() update both turns and
    // React see duplicate keys); error/running cleared — a persisted turn is
    // completed by construction.
    return [{ ...turn, id: 0, steps: Array.isArray(turn.steps) ? turn.steps : [], error: null, running: false }]
  } catch {
    return []
  }
}

const STEP_LABEL: Record<string, string> = {
  router: 'Routing onto a registered QuerySpec',
  spec: 'Running registered QuerySpec',
  text2cypher: 'Schema-grounded text2cypher',
  answer: 'Composing the answer',
}

export default function AskRoute({ persona }: { persona: Persona }) {
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const adkUrl = (import.meta.env.VITE_ADK_URL as string | undefined) ?? 'http://localhost:8000'

  // ONE shared client: the token handed to the agent (the R4 owner token) and
  // the runSpec/exportSpec calls must belong to the SAME api session, or the
  // agent-registered explore_refs would 404 for this page.
  const client = useMemo(() => createApiClient(apiUrl, persona.id), [apiUrl, persona.id])
  const access = useMemo(() => createApiAccess(apiUrl, persona.id, client), [apiUrl, persona.id, client])

  // spec id -> classification, for citation chips ('spec:<id>' sources).
  const [specClass, setSpecClass] = useState<Record<string, string>>({})
  useEffect(() => {
    let cancelled = false
    fetch(`${apiUrl}/specs`)
      .then((r) => (r.ok ? r.json() : []))
      .then((specs: { id: string; classification: string }[]) => {
        if (!cancelled) setSpecClass(Object.fromEntries(specs.map((s) => [s.id, s.classification])))
      })
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [apiUrl])

  const sessionId = useMemo(
    () => `ask-${persona.id}-${Math.random().toString(36).slice(2, 10)}`,
    [persona.id],
  )

  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>(() => loadLastTurn(persona.id))
  const nextId = useRef(1)
  // O64: a `?as=` persona swap re-renders this same mounted route (sign-out
  // remounts, the dev bypass does not), so a persona change re-derives the
  // list from THAT persona's storage — the other persona's turn must never
  // linger on screen. Render-time reset is the React "state from props"
  // adjustment pattern; an in-flight ask from the old persona patches by id
  // into a list that no longer holds it (a no-op) and still SAVES under the
  // persona that asked, which onAsk captured at call time.
  const shownPersona = useRef(persona.id)
  if (shownPersona.current !== persona.id) {
    shownPersona.current = persona.id
    setTurns(loadLastTurn(persona.id))
  }
  const running = turns.some((t) => t.running)

  async function onAsk() {
    const q = question.trim()
    if (!q || running) return
    setQuestion('')
    const id = nextId.current++
    setTurns((prev) => [...prev, { id, question: q, steps: [], envelope: null, error: null, running: true }])
    const patch = (fn: (t: Turn) => Turn) =>
      setTurns((prev) => prev.map((t) => (t.id === id ? fn(t) : t)))

    // R4 handshake: forward this session's api token so the agent can register
    // ephemeral specs WE own. If drydocs-api is down the question still runs —
    // steps simply carry no explore_ref (honest degradation, matching the agent).
    let control: ReturnType<typeof controlPart> | undefined
    try {
      control = controlPart(await client.getToken(), apiUrl)
    } catch {
      control = undefined
    }

    try {
      const envelope = await ask({
        adkUrl,
        app: 'graph_qa',
        userId: persona.id,
        sessionId,
        question: q,
        control,
        onStep: (step) => patch((t) => ({ ...t, steps: [...t.steps.filter((s) => s.i !== step.i), step] })),
      })
      if (envelope.status === 'error') {
        patch((t) => ({ ...t, error: envelope.error ?? 'agent error', running: false }))
      } else {
        // the final envelope's steps are authoritative (streamed ones were live previews)
        const completed: Turn = {
          id,
          question: q,
          envelope,
          steps: envelope.steps ?? [],
          error: null,
          running: false,
        }
        // O64: the ONLY persistence write — success envelopes, nothing else
        try {
          localStorage.setItem(lastTurnKey(persona.id), JSON.stringify(completed))
        } catch {}
        patch((t) => ({ ...t, envelope, steps: envelope.steps ?? t.steps, running: false }))
      }
    } catch (e) {
      patch((t) => ({ ...t, error: (e as Error).message, running: false }))
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Ask' }]} />
      <div className="min-h-0 flex-1 overflow-auto p-4">
        <div className="mx-auto flex max-w-4xl flex-col gap-4">
          <header>
            <h1 data-view-heading tabIndex={-1} className="text-lg font-semibold text-text">
              Ask the knowledge graph
            </h1>
            <p className="text-xs text-muted">
              Free-text questions answered by the tiered graph_qa agent (ADR 0007): registered
              QuerySpecs first, schema-grounded text2cypher when none fits. Every executed Cypher is
              inspectable and re-runnable below — nothing here writes the graph.
            </p>
          </header>

          {turns.length === 0 && (
            <EmptyState
              title="Ask a question"
              hint='Try "how many applications are there?" or "which folders feed the most jobs?" — the agent shows its work.'
            />
          )}

          {turns.map((turn) => (
            <TurnCard key={turn.id} turn={turn} access={access} specClass={specClass} />
          ))}

          <form
            className="flex shrink-0 gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              void onAsk()
            }}
          >
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={running ? 'Waiting for the agent…' : 'Ask about jobs, folders, applications, ownership…'}
              aria-label="Question"
              disabled={running}
              className="min-w-0 flex-1 text-sm"
            />
            <button
              type="submit"
              disabled={running || !question.trim()}
              className="rounded-md border border-edge bg-bg-2 px-3 py-1 text-sm font-medium text-text disabled:opacity-50"
            >
              Ask
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

function TurnCard({
  turn,
  access,
  specClass,
}: {
  turn: Turn
  access: ReturnType<typeof createApiAccess>
  specClass: Record<string, string>
}) {
  const envelope = turn.envelope
  const watermarked = (envelope?.sources ?? []).some((s) => s.trust === 'SYNTHESIZED')
  return (
    <section className="rounded-lg border border-edge bg-panel-2/40 p-3">
      <p className="text-sm font-medium text-text">“{turn.question}”</p>

      {/* streamed agent steps — live while running, then the envelope's record */}
      <ol className="mt-2 flex flex-col gap-1" aria-label="Agent steps">
        {turn.steps.map((step) => (
          <StepLine key={step.i} step={step} />
        ))}
        {turn.running && (
          <li className="flex items-center gap-2 text-xs text-muted">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-bright" aria-hidden="true" />
            {turn.steps.length === 0 ? 'agent is thinking…' : 'working…'}
          </li>
        )}
      </ol>

      {turn.error && (
        <p className="mt-2 rounded border border-red/60 bg-red/10 px-2 py-1 text-xs text-brand-soft">
          {turn.error}
        </p>
      )}

      {envelope && (
        <div className="mt-3 flex flex-col gap-2">
          {watermarked && (
            <p className="rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
              SYNTHESIZED — parts of this answer derive from watermarked (unverified) data
            </p>
          )}
          <p className="whitespace-pre-wrap text-sm text-text">{envelope.answer}</p>

          {(envelope.sources?.length ?? 0) > 0 && (
            <div className="flex flex-wrap items-center gap-1.5" aria-label="Sources">
              <span className="text-[10px] uppercase tracking-wide text-faint">Sources</span>
              {envelope.sources!.map((s, i) => (
                <SourceChip key={i} source={s} specClass={specClass} />
              ))}
            </div>
          )}

          <MetricsChip envelope={envelope} />

          {/* R6: the Tier-2 task graph, one frame per iteration. Present only
              on runs that actually escalated — most never do. */}
          {(envelope.task_graph?.length ?? 0) > 0 && (
            <TaskGraphPane snapshots={envelope.task_graph!} />
          )}

          <details className="rounded border border-edge-soft bg-bg-2/40 px-2 py-1">
            <summary className="cursor-pointer text-xs font-medium text-muted">
              How I got this — {envelope.steps?.length ?? 0} steps, every Cypher inspectable
            </summary>
            <div className="mt-2 flex flex-col gap-2">
              {(envelope.steps ?? []).map((step) => (
                <StepDetail key={step.i} step={step} access={access} />
              ))}
            </div>
          </details>
        </div>
      )}
    </section>
  )
}

function StepLine({ step }: { step: AskStep }) {
  const label = STEP_LABEL[step.kind] ?? step.kind
  const detail =
    step.kind === 'spec' && step.spec_id
      ? step.spec_id
      : step.kind === 'router'
        ? step.spec_id
          ? `→ ${step.spec_id}`
          : '→ no spec fits, escalating'
        : step.kind === 'text2cypher' && (step.fix_retries ?? 0) > 0
          ? `repair attempt ${step.fix_retries}`
          : null
  return (
    <li className="flex flex-wrap items-center gap-2 text-xs">
      <span className={step.error ? 'text-yellow' : 'text-muted'}>
        {step.error ? '△' : '✓'} {label}
      </span>
      {detail && <code className="font-mono text-[10px] text-faint">{detail}</code>}
      {step.rows !== null && step.rows !== undefined && (
        <span className="font-mono text-[10px] text-faint">
          {step.rows} rows · {step.database} · {step.ms} ms
        </span>
      )}
    </li>
  )
}

function SourceChip({ source, specClass }: { source: AskSource; specClass: Record<string, string> }) {
  const [kind, id] = source.document.split(':', 2)
  // spec sources carry the registry row's classification; agent-generated
  // Cypher carries the ephemeral ceiling — the same stamp its export manifest
  // will carry (R4). Mirrors EPHEMERAL_CLASSIFICATION in
  // drydocs_api/ephemeral_specs.py; if that ceiling is ever re-pointed, this
  // moves with it.
  const classification = kind === 'spec' ? (specClass[id] ?? 'internal') : 'internal'
  const confirmed = source.trust === 'CONFIRMED'
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border border-edge bg-bg-2 px-2 py-0.5 font-mono text-[10px]"
      title={`${source.document} · trust ${source.trust} · ${classification}`}
    >
      <span className={confirmed ? 'text-green' : 'text-yellow'}>{source.trust}</span>
      <span className="text-text">{source.document}</span>
      <span className="text-faint">{classification}</span>
    </span>
  )
}

function MetricsChip({ envelope }: { envelope: AskEnvelope }) {
  const m = envelope.metrics
  if (!m) return null
  const cost = m.cost_est_usd
  return (
    <p className="flex flex-wrap items-center gap-2 font-mono text-[10px] text-faint" aria-label="Run metrics">
      <span className="rounded-full border border-edge bg-bg-2 px-2 py-0.5">
        {m.response_ms?.total ?? 0} ms · {m.tokens?.total ?? 0} tok · {m.llm_calls} LLM calls ·{' '}
        {m.iterations} iteration{m.iterations === 1 ? '' : 's'}
        {typeof cost === 'number' ? ` · ~$${cost.toFixed(4)}` : ''}
      </span>
      <span>
        tier {envelope.tier} · {envelope.model ?? 'model n/a'} · run {envelope.run_id}
      </span>
      {/* R6: a cap is only tunable if you can see it act. Shown when Tier 2
          engaged, and always when the budget was spent — never silently. */}
      {m.tier2?.engaged && (
        <span
          className="rounded-full border border-edge bg-bg-2 px-2 py-0.5"
          title={`next-step votes: ${(m.tier2.votes ?? []).join(', ') || 'none'}`}
        >
          tier-2 · {(m.tier2.votes ?? []).filter((v) => v === 'enhance').length}/
          {(m.tier2.votes ?? []).length} enhance votes
          {m.tier2.forced_solve ? ' · forced solve' : ''}
        </span>
      )}
      {m.budget?.exhausted && (
        <span className="rounded-full border border-yellow/50 bg-yellow/10 px-2 py-0.5 text-yellow">
          token budget spent ({m.budget.tokens_used}/{m.budget.tokens_limit}) — exploration stopped
        </span>
      )}
    </p>
  )
}

function StepDetail({ step, access }: { step: AskStep; access: ReturnType<typeof createApiAccess> }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded border border-edge-soft p-2">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-medium text-text">
          {step.i}. {STEP_LABEL[step.kind] ?? step.kind}
        </span>
        {step.database && <code className="font-mono text-[10px] text-faint">db {step.database}</code>}
        {step.rows !== null && step.rows !== undefined && (
          <code className="font-mono text-[10px] text-faint">{step.rows} rows</code>
        )}
        <code className="font-mono text-[10px] text-faint">{step.ms} ms</code>
        {(step.fix_retries ?? 0) > 0 && (
          <code className="font-mono text-[10px] text-yellow">fix #{step.fix_retries}</code>
        )}
        {step.explore_ref && (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="ml-auto rounded-md border border-edge bg-bg-2 px-2 py-0.5 text-[11px] font-medium text-muted hover:border-faint hover:text-text"
            title={`Re-run this exact Cypher via its ephemeral spec ${step.explore_ref} — export ships the provenance manifest`}
          >
            {open ? 'Close explorer' : 'Open in Explorer / Export'}
          </button>
        )}
      </div>
      {step.error && (
        <p className="mt-1 font-mono text-[10px] text-yellow">
          {step.error}
          {step.kind === 'text2cypher' ? ' — repaired below in the fix history' : ''}
        </p>
      )}
      {step.cypher && (
        <pre className="mt-1 overflow-x-auto rounded bg-bg-2/60 p-2 font-mono text-[10px] text-muted">
          {step.cypher}
        </pre>
      )}
      {open && step.explore_ref && (
        <div className="mt-2 h-72">
          {/* the R4 payoff: the SAME SpecGrid the Explorer uses, pointed at the
              ephemeral ref — run + both export paths + manifest, zero raw Cypher
              leaving the browser. */}
          <SpecGrid
            access={access}
            specId={step.explore_ref}
            fallback={
              <EmptyState
                title="Ephemeral spec unavailable"
                hint="Refs are session-scoped and TTL-bounded (30 min) — re-ask the question to mint a fresh one."
              />
            }
          />
        </div>
      )}
    </div>
  )
}
