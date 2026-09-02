import { useEffect, useMemo, useState } from 'react'
import { createApiAccess } from '../lib/graphApi'
import { forceLayout, trimEdge, type PlacedNode } from '../lib/forceLayout'
import { GNODE, GSUB } from './GraphSvg'

// The LIVE graph view (backlog O6, wf-console-01 V5): real WAS_INFORMED_BY
// dependency edges from the knowledge graph, through the GraphAccess seam with
// the api adapter as the default path (ADR 0005). Payload shaping is
// server-side (drydocs-api's c4-graph named query) — this component only lays
// out and renders what the server returns. Graph before Cypher (the wireframe
// D4/V3 finding): there is no Cypher affordance here at all; raw Cypher stays
// on the admin Console bench.
//
// Rendering: the shared deterministic d3-force placement engine
// (lib/forceLayout.ts — extracted at R6 when the Ask spoke's Tier-2 task graph
// became the second scene needing it) + the in-repo SVG idiom (GraphSvg's
// visual language, whose text classes it shares). NVL deferred — revisit when
// the V5 explorer grows the C4 zoom ladder or >200-node scenes (decision on O6).
// O30: styled inline via Tailwind/token classes (App.css retired).

const env = import.meta.env

interface DepEdge {
  source: string
  target: string
  via: string
}

const W = 940
const H = 540
const R = 27
const PAD = 56

function layout(edges: DepEdge[]): PlacedNode[] {
  return forceLayout(edges, { width: W, height: H, radius: R, pad: PAD })
}

const JOB_COLOR = '#9B6BD4' // ControlMJob's label-family color (towers.ts idiom)

const NOTE = 'mt-2 text-[13px] leading-[1.55] text-muted'
const PANEL = 'overflow-hidden rounded-md border border-edge bg-panel'
const P_HEAD =
  'flex items-center justify-between gap-2.5 border-b border-edge bg-panel-2 px-3.5 py-2.5 text-[14px] font-semibold'
const P_HEAD_M = 'font-mono text-[11px] font-normal text-muted'

// Middle truncation: batch job names share long prefixes (PARAD00xx_PEX_…), so
// head truncation would render every node identically — keep head AND tail.
// Full names stay on the <title> hover and in the inspector.
function label(id: string): string {
  // head keeps the job-number digits (PARAD0060…), tail the role suffix
  return id.length > 16 ? `${id.slice(0, 9)}…${id.slice(-6)}` : id
}

export default function GraphExplorer({ personaId }: { personaId: string }) {
  const apiUrl = env.VITE_API_URL ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, personaId), [apiUrl, personaId])

  const [edges, setEdges] = useState<DepEdge[] | null>(null)
  const [database, setDatabase] = useState('')
  const [error, setError] = useState('')
  const [selected, setSelected] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setError('')
    setEdges(null)
    access
      .runNamed('c4-graph')
      .then((res) => {
        if (cancelled) return
        setDatabase(res.database)
        setEdges(
          res.rows.map((r) => ({
            source: String(r.source),
            target: String(r.target),
            via: r.via_condition == null ? '' : String(r.via_condition),
          })),
        )
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
    return () => {
      cancelled = true
    }
  }, [access, attempt])

  const placed = useMemo(() => (edges && edges.length ? layout(edges) : []), [edges])
  const byId = useMemo(() => new Map(placed.map((n) => [n.id, n])), [placed])

  const upstream = edges?.filter((e) => e.source === selected) ?? [] // selected was informed by …
  const downstream = edges?.filter((e) => e.target === selected) ?? [] // … inform selected's successors

  return (
    <main className="mx-auto max-w-[1180px] px-[30px]">
      <div className="flex flex-wrap items-center gap-3 pb-1 pt-6">
        <h1 tabIndex={-1} data-view-heading className="text-[21px] font-bold outline-none">Graph — live dependency view</h1>
        <span className="whitespace-nowrap rounded-xs border border-green/50 bg-green/8 px-[9px] py-1 font-mono text-[11px] font-medium text-green">
          LIVE · knowledge graph · db {database || '—'} · api adapter (ADR 0005)
        </span>
      </div>
      <p className={NOTE}>
        Real <code>WAS_INFORMED_BY</code> dependency edges from the local EE database, shaped
        server-side by drydocs-api&#39;s <code>c4-graph</code> named query. An arrow A → B reads
        &#34;A was informed by B&#34;: A runs after B, connected by the hover-labeled condition.
        The tower drill-downs remain the synthesized no-backend demo.
      </p>

      {error && (
        <section className={`${PANEL} px-3.5 pb-3`}>
          <div className={`${P_HEAD} -mx-3.5 mb-2`}>Graph unavailable</div>
          <p className={NOTE}>{error}</p>
          <p className={NOTE}>
            The live view needs the thin API and the Neo4j EE container running; the
            synthesized tower pages under Overview work without either.
          </p>
          <div className="my-2 flex flex-wrap items-center gap-2">
            <button
              className="rounded-sm border border-blue-bright bg-blue px-[0.9rem] py-[0.35rem] font-semibold text-white hover:bg-blue-bright"
              onClick={() => setAttempt((n) => n + 1)}
            >
              Retry
            </button>
          </div>
        </section>
      )}
      {!error && edges === null && <p className={NOTE}>Connecting to drydocs-api…</p>}
      {edges !== null && edges.length === 0 && (
        <p className={NOTE}>0 dependency edges in {database} — load the graph first (README quick start).</p>
      )}

      {edges !== null && edges.length > 0 && (
        <div className="my-4 grid grid-cols-1 gap-4 min-[901px]:grid-cols-[1.7fr_1fr]">
          <div className={PANEL}>
            <div className={P_HEAD}>
              Job dependency graph · WAS_INFORMED_BY
              <span className={P_HEAD_M}>
                {placed.length} jobs · {edges.length} edges · server cap 200
              </span>
            </div>
            <div className="p-2.5">
              <svg
                viewBox={`0 0 ${W} ${H}`}
                width="100%"
                xmlns="http://www.w3.org/2000/svg"
                role="img"
                aria-label={`Live job dependency graph: ${placed.length} jobs, ${edges.length} WAS_INFORMED_BY edges from database ${database}`}
              >
                <defs>
                  <marker id="gx-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M0,0 L10,5 L0,10 z" fill="#8A97A8" />
                  </marker>
                </defs>
                {edges.map((e, i) => {
                  const a = byId.get(e.source)
                  const b = byId.get(e.target)
                  if (!a || !b) return null
                  const { x1, y1, x2, y2 } = trimEdge(a, b, R)
                  const dim = selected && e.source !== selected && e.target !== selected
                  return (
                    <g key={i} opacity={dim ? 0.25 : 1}>
                      <title>{`${e.source} → ${e.target}${e.via ? ` · via ${e.via}` : ''}`}</title>
                      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3C4E66" strokeWidth="1.6" markerEnd="url(#gx-arr)" />
                    </g>
                  )
                })}
                {placed.map((n) => {
                  const dim =
                    selected &&
                    n.id !== selected &&
                    !upstream.some((e) => e.target === n.id) &&
                    !downstream.some((e) => e.source === n.id)
                  return (
                    <g
                      key={n.id}
                      className="cursor-pointer [&:focus-visible_circle]:stroke-blue-bright [&:focus-visible_circle]:[stroke-width:3]"
                      opacity={dim ? 0.3 : 1}
                      role="button"
                      tabIndex={0}
                      aria-label={`Job ${n.id}`}
                      onClick={() => setSelected(selected === n.id ? '' : n.id)}
                      onKeyDown={(ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                          ev.preventDefault()
                          setSelected(selected === n.id ? '' : n.id)
                        }
                      }}
                    >
                      <title>{n.id}</title>
                      <circle
                        cx={n.x}
                        cy={n.y}
                        r={R}
                        fill={JOB_COLOR}
                        opacity=".16"
                        stroke={n.id === selected ? '#e8edf3' : JOB_COLOR}
                        strokeWidth="2"
                      />
                      <text x={n.x} y={n.y + 1} textAnchor="middle" className={GNODE}>
                        {label(n.id)}
                      </text>
                      <text x={n.x} y={n.y + 15} textAnchor="middle" className={GSUB}>
                        :ControlMJob
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>
          </div>

          <div className={PANEL}>
            <div className={P_HEAD}>
              Node inspector
              <span className={P_HEAD_M}>{selected ? ':ControlMJob' : 'select a node'}</span>
            </div>
            {!selected && (
              <p className={`${NOTE} px-3.5 py-3`}>
                Click a job to see its neighborhood: what it waits on (upstream) and what waits
                on it (downstream), with the via-condition per edge.
              </p>
            )}
            {selected && (
              <div className="px-3.5 py-3 text-[13px]">
                <div className="mb-2.5 break-all font-mono text-sm font-semibold text-blue-bright">{selected}</div>
                <h3 className="mb-1 mt-2.5 text-xs font-semibold uppercase tracking-[0.04em] text-[#c8d2de]">
                  Upstream · was informed by ({upstream.length})
                </h3>
                {upstream.length === 0 && <p className={NOTE}>No predecessors — chain entry point.</p>}
                <ul className="list-none">
                  {upstream.map((e, i) => (
                    <li key={i} className="border-b border-edge-soft py-[3px] last:border-b-0">
                      <code className="text-xs text-text">{e.target}</code>
                      {e.via && <span className="font-mono text-[11px] text-muted"> via {e.via}</span>}
                    </li>
                  ))}
                </ul>
                <h3 className="mb-1 mt-2.5 text-xs font-semibold uppercase tracking-[0.04em] text-[#c8d2de]">
                  Downstream · informs ({downstream.length})
                </h3>
                {downstream.length === 0 && <p className={NOTE}>No successors — chain terminal.</p>}
                <ul className="list-none">
                  {downstream.map((e, i) => (
                    <li key={i} className="border-b border-edge-soft py-[3px] last:border-b-0">
                      <code className="text-xs text-text">{e.source}</code>
                      {e.via && <span className="font-mono text-[11px] text-muted"> via {e.via}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="pb-[46px] pt-5 text-center font-mono text-[11px] text-faint">
        Data: LIVE from the local Neo4j EE knowledge graph · GraphAccess seam, api adapter
        (drydocs-api, ADR 0005) · payload shaped server-side (c4-graph named query) · layout
        d3-force, deterministic
      </div>
    </main>
  )
}
