import { useMemo, useState } from 'react'
import { listApps, runAgent, createSession, type AdkEvent } from '../lib/adk'
import { MODULES } from '../modules/registry'
import ModuleToolbar from '../layout/ModuleToolbar'

// /admin/agent-test (FB-2026-07-29-04): the ADMIN real-time twin of the Under
// the Hood view. UTH replays the committed benchmark fixture; this page runs a
// LIVE request through an agent and shows the same anatomy per run:
// interpretation → Cypher → return path → answer → metrics. Deliberately light
// chrome — an admin test harness, not a product surface. Read-only throughout
// (O20 stands: the UI writes nothing to the graph). The module dropdown lists
// only the registry's non-deterministic modules (retrieval: 'agent'); the
// deterministic QuerySpec modules have nothing to interpret and stay out.
// ADK unreachable → a SYNTHESIZED demo trace renders with the standard
// EXAMPLE DATA banner (the honesty convention), so the harness is inspectable
// before the R2 backend lands.

const AGENT_MODULES = MODULES.filter((m) => m.retrieval === 'agent')

interface Trace {
  live: boolean
  interpretation: string
  cypher: string
  path: string
  answer: string
  metrics: { label: string; value: string }[]
  raw?: AdkEvent[]
}

const DEMO_TRACE: Record<string, Omit<Trace, 'live'>> = {
  explorer: {
    interpretation:
      'Routed as GRAPH-NAV / fan-in question. Entities: job name → :ControlMJob anchor; "depends on" → WAS_INFORMED_BY traversal, direction=upstream, depth≤3. (SYNTHESIZED — the R2 router is not wired yet.)',
    cypher:
      "MATCH (j:ControlMJob {name: $name})<-[:WAS_INFORMED_BY*1..3]-(up)\nRETURN up.name AS dependent, labels(up) AS kind\nORDER BY dependent",
    path: 'router → text2cypher → read-only executor → 12 rows (:ControlMJob ×9, :EtlJob ×3) → summarizer',
    answer:
      '12 upstream dependents found within 3 hops; 9 Control-M jobs and 3 ETL jobs. Deepest chain length 3. (SYNTHESIZED example answer.)',
    metrics: [
      { label: 'chars in', value: '54' },
      { label: 'chars out', value: '208' },
      { label: 'model calls', value: '2' },
      { label: 'rows', value: '12' },
      { label: 'latency', value: '~180ms' },
    ],
  },
  docs: {
    interpretation:
      'Routed as DOCS / exact-lookup. Term detected → full-text index probe first, graph traversal fallback. (SYNTHESIZED — docmeta-qa demo shape from the P0 benchmark.)',
    cypher:
      "CALL db.index.fulltext.queryNodes('chunk_text', $term)\nYIELD node, score\nMATCH (node)<-[:CONTAINS]-(d:Document)\nRETURN d.title, node.heading, score LIMIT 3",
    path: 'router → fulltext top-3 → chunk fetch (~1.3k chars) → answer with citation',
    answer:
      'Definition returned from the vendor corpus with document + heading citation. (SYNTHESIZED example answer; live equivalent averaged ~52ms in the P0 benchmark.)',
    metrics: [
      { label: 'chars in', value: '31' },
      { label: 'chars out', value: '1,312' },
      { label: 'model calls', value: '1' },
      { label: 'chunks', value: '3' },
      { label: 'latency', value: '~52ms' },
    ],
  },
}

function extractCypher(text: string): string | null {
  const m = /```(?:cypher)?\s*([\s\S]*?)```/.exec(text)
  if (m) return m[1].trim()
  if (/\b(MATCH|CALL|RETURN)\b/.test(text)) return null // prose mentioning cypher ≠ a block
  return null
}

export default function AgentTestRoute() {
  const [moduleId, setModuleId] = useState<string>(AGENT_MODULES[0]?.id ?? '')
  const [input, setInput] = useState('')
  const [running, setRunning] = useState(false)
  const [trace, setTrace] = useState<Trace | null>(null)
  const [error, setError] = useState<string | null>(null)
  const mod = useMemo(() => AGENT_MODULES.find((m) => m.id === moduleId), [moduleId])
  const adkUrl = (import.meta.env.VITE_ADK_URL as string | undefined) ?? 'http://localhost:8000'

  async function run() {
    if (!input.trim() || !mod) return
    setRunning(true)
    setError(null)
    const t0 = performance.now()
    try {
      const apps = await listApps(adkUrl)
      const app = apps.find((a) => a.includes(mod.id)) ?? apps[0]
      if (!app) throw new Error('ADK reachable but no apps registered')
      const sessionId = `agent-test-${t0.toFixed(0)}`
      await createSession(adkUrl, app, 'admin-test', sessionId)
      const events = await runAgent(adkUrl, app, 'admin-test', sessionId, input.trim())
      const ms = performance.now() - t0
      const texts = events
        .map((e) => e.content?.parts?.map((p) => p.text ?? '').join('') ?? '')
        .filter(Boolean)
      const answer = texts[texts.length - 1] ?? '(no text in final event)'
      const cypher = texts.map(extractCypher).find(Boolean) ?? '(no cypher block surfaced in events)'
      setTrace({
        live: true,
        interpretation: texts[0] ?? '(no interpretation event)',
        cypher,
        path: events.map((e) => e.author ?? '?').join(' → ') || '(no events)',
        answer,
        metrics: [
          { label: 'chars in', value: String(input.trim().length) },
          { label: 'chars out', value: texts.join('').length.toLocaleString() },
          { label: 'events', value: String(events.length) },
          { label: 'latency', value: `${Math.round(ms)}ms` },
          { label: 'agent app', value: app },
        ],
        raw: events,
      })
    } catch (e) {
      // honest fallback: the SYNTHESIZED demo trace, clearly tagged
      setError(`ADK unreachable at ${adkUrl} (${e instanceof Error ? e.message : String(e)}) — showing the SYNTHESIZED demo trace instead.`)
      setTrace({ live: false, ...DEMO_TRACE[mod.id] })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Agent Test' }]} />
      <h2 tabIndex={-1} data-view-heading className="sr-only">
        Agent Test
      </h2>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto flex max-w-4xl flex-col gap-3">
          <div className="flex flex-wrap items-baseline gap-2">
            <h1 className="text-lg font-bold text-text">Agent Test</h1>
            <span className="rounded border border-edge px-2 py-0.5 font-mono text-[10px] text-muted">
              admin · real-time · read-only (O20)
            </span>
            <span className="font-mono text-[10px] text-faint">
              the live twin of Under the Hood — one run, same anatomy
            </span>
          </div>

          {/* module / agent / request */}
          <div className="flex flex-wrap items-end gap-2 rounded-md border border-edge bg-panel p-3">
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Module (non-deterministic only)
              <select value={moduleId} onChange={(e) => setModuleId(e.target.value)} className="min-w-40">
                {AGENT_MODULES.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex flex-col gap-1 text-[11px] text-muted">
              Agent
              <span className="rounded border border-edge-soft bg-bg-2 px-2 py-1.5 font-mono text-[11px] text-teal">
                {mod?.agent ?? '—'}
              </span>
            </div>
            <label className="flex min-w-64 flex-1 flex-col gap-1 text-[11px] text-muted">
              SME request
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && run()}
                placeholder="e.g. which jobs depend on the nightly folder load?"
                className="w-full"
              />
            </label>
            <button
              type="button"
              onClick={run}
              disabled={running || !input.trim()}
              className="rounded-md border border-blue-bright bg-blue px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {running ? 'Running…' : 'Run'}
            </button>
          </div>

          {error && (
            <p className="rounded border border-yellow/50 bg-yellow/10 px-3 py-2 font-mono text-[11px] text-yellow">{error}</p>
          )}

          {trace && (
            <div className="flex flex-col gap-2">
              <span
                className={
                  'self-start rounded border px-2 py-0.5 font-mono text-[10px] ' +
                  (trace.live ? 'border-green text-green' : 'border-yellow/50 bg-yellow/10 text-yellow')
                }
              >
                {trace.live ? 'LIVE — ADK run' : 'EXAMPLE DATA · SYNTHESIZED — ADK not reachable'}
              </span>

              <Section title="1 · How the input was interpreted">{trace.interpretation}</Section>
              <Section title="2 · Cypher" mono>
                {trace.cypher}
              </Section>
              <Section title="3 · Return path" mono>
                {trace.path}
              </Section>
              <Section title="4 · Answer">{trace.answer}</Section>

              <div className="rounded-md border border-edge bg-panel p-3">
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-faint">5 · Metrics</h3>
                <div className="flex flex-wrap gap-2">
                  {trace.metrics.map((m) => (
                    <span key={m.label} className="rounded border border-edge-soft bg-bg-2 px-2 py-1 font-mono text-[11px] tabular-nums text-text">
                      {m.value} <span className="text-faint">{m.label}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, mono, children }: { title: string; mono?: boolean; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-edge bg-panel p-3">
      <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-faint">{title}</h3>
      <pre className={'whitespace-pre-wrap break-words text-xs leading-relaxed ' + (mono ? 'font-mono text-teal' : 'font-sans text-text')}>
        {children}
      </pre>
    </div>
  )
}
