import { useEffect, useMemo, useState } from 'react'
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force'
import { createApiAccess } from '../lib/graphApi'

// The LIVE graph view (backlog O6, wf-console-01 V5): real WAS_INFORMED_BY
// dependency edges from the knowledge graph, through the GraphAccess seam with
// the api adapter as the default path (ADR 0005). Payload shaping is
// server-side (drydocs-api's c4-graph named query) — this component only lays
// out and renders what the server returns. Graph before Cypher (the wireframe
// D4/V3 finding): there is no Cypher affordance here at all; raw Cypher stays
// on the admin Console bench.
//
// Rendering: d3-force layout (ISC, layout-only; deterministic — d3-force's
// default random source is a fixed-seed LCG) + the in-repo SVG idiom
// (GraphSvg's visual language). NVL deferred — revisit when the V5 explorer
// grows the C4 zoom ladder or >200-node scenes (decision recorded on O6).

const env = import.meta.env

interface DepEdge {
  source: string
  target: string
  via: string
}

interface LayoutNode extends SimulationNodeDatum {
  id: string
}

interface PlacedNode {
  id: string
  x: number
  y: number
}

const W = 940
const H = 540
const R = 27
const PAD = 56

// Static, deterministic force layout: run the simulation to convergence
// synchronously, then rescale into the viewBox. No animation by design —
// stable positions make the view screenshot- and CDP-assertable.
function layout(edges: DepEdge[]): PlacedNode[] {
  const ids = [...new Set(edges.flatMap((e) => [e.source, e.target]))]
  const nodes: LayoutNode[] = ids.map((id) => ({ id }))
  const links: SimulationLinkDatum<LayoutNode>[] = edges.map((e) => ({
    source: e.source,
    target: e.target,
  }))
  const sim = forceSimulation(nodes)
    .force('link', forceLink<LayoutNode, SimulationLinkDatum<LayoutNode>>(links).id((d) => d.id).distance(110))
    .force('charge', forceManyBody().strength(-380))
    .force('center', forceCenter(W / 2, H / 2))
    .force('collide', forceCollide(R + 14))
    // Weak pull to center keeps DISCONNECTED chains from repelling each other
    // to the bbox extremes (which would crush each cluster in the rescale).
    .force('x', forceX(W / 2).strength(0.08))
    .force('y', forceY(H / 2).strength(0.1))
    .stop()
  sim.tick(300)

  const xs = nodes.map((n) => n.x ?? 0)
  const ys = nodes.map((n) => n.y ?? 0)
  const [minX, maxX] = [Math.min(...xs), Math.max(...xs)]
  const [minY, maxY] = [Math.min(...ys), Math.max(...ys)]
  const sx = (W - 2 * PAD) / Math.max(1, maxX - minX)
  const sy = (H - 2 * PAD) / Math.max(1, maxY - minY)
  const s = Math.min(sx, sy, 1.4)
  return nodes.map((n) => ({
    id: n.id,
    x: PAD + ((n.x ?? 0) - minX) * s + (W - 2 * PAD - (maxX - minX) * s) / 2,
    y: PAD + ((n.y ?? 0) - minY) * s + (H - 2 * PAD - (maxY - minY) * s) / 2,
  }))
}

const JOB_COLOR = '#9B6BD4' // ControlMJob's label-family color (towers.ts idiom)

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
    <main className="wrap">
      <div className="view-head">
        <h1>Graph — live dependency view</h1>
        <span className="tag tag-live">
          LIVE · knowledge graph · db {database || '—'} · api adapter (ADR 0005)
        </span>
      </div>
      <p className="note">
        Real <code>WAS_INFORMED_BY</code> dependency edges from the local EE database, shaped
        server-side by drydocs-api&#39;s <code>c4-graph</code> named query. An arrow A → B reads
        &#34;A was informed by B&#34;: A runs after B, connected by the hover-labeled condition.
        The tower drill-downs remain the synthesized no-backend demo.
      </p>

      {error && (
        <section className="panel gx-msg">
          <div className="p-head">Graph unavailable</div>
          <p className="note">{error}</p>
          <p className="note">
            The live view needs the thin API and the Neo4j EE container running; the
            synthesized tower pages under Overview work without either.
          </p>
          <div className="row">
            <button className="primary" onClick={() => setAttempt((n) => n + 1)}>Retry</button>
          </div>
        </section>
      )}
      {!error && edges === null && <p className="note">Connecting to drydocs-api…</p>}
      {edges !== null && edges.length === 0 && (
        <p className="note">0 dependency edges in {database} — load the graph first (README quick start).</p>
      )}

      {edges !== null && edges.length > 0 && (
        <div className="gx-grid">
          <div className="panel">
            <div className="p-head">
              Job dependency graph · WAS_INFORMED_BY
              <span className="m">
                {placed.length} jobs · {edges.length} edges · server cap 200
              </span>
            </div>
            <div className="graphbox">
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
                  const dx = b.x - a.x
                  const dy = b.y - a.y
                  const len = Math.hypot(dx, dy) || 1
                  const x1 = a.x + (dx / len) * R
                  const y1 = a.y + (dy / len) * R
                  const x2 = b.x - (dx / len) * (R + 4)
                  const y2 = b.y - (dy / len) * (R + 4)
                  const dim = selected && e.source !== selected && e.target !== selected
                  return (
                    <g key={i} className="gx-edge" opacity={dim ? 0.25 : 1}>
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
                      className="gx-node"
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
                      <text x={n.x} y={n.y + 1} textAnchor="middle" className="gnode">
                        {label(n.id)}
                      </text>
                      <text x={n.x} y={n.y + 15} textAnchor="middle" className="gsub">
                        :ControlMJob
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>
          </div>

          <div className="panel gx-inspector">
            <div className="p-head">
              Node inspector
              <span className="m">{selected ? ':ControlMJob' : 'select a node'}</span>
            </div>
            {!selected && (
              <p className="note">
                Click a job to see its neighborhood: what it waits on (upstream) and what waits
                on it (downstream), with the via-condition per edge.
              </p>
            )}
            {selected && (
              <div className="gx-inspect-body">
                <div className="gx-jobname">{selected}</div>
                <h3>Upstream · was informed by ({upstream.length})</h3>
                {upstream.length === 0 && <p className="note">No predecessors — chain entry point.</p>}
                <ul>
                  {upstream.map((e, i) => (
                    <li key={i}>
                      <code>{e.target}</code>
                      {e.via && <span className="gx-via"> via {e.via}</span>}
                    </li>
                  ))}
                </ul>
                <h3>Downstream · informs ({downstream.length})</h3>
                {downstream.length === 0 && <p className="note">No successors — chain terminal.</p>}
                <ul>
                  {downstream.map((e, i) => (
                    <li key={i}>
                      <code>{e.source}</code>
                      {e.via && <span className="gx-via"> via {e.via}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="foot">
        Data: LIVE from the local Neo4j EE knowledge graph · GraphAccess seam, api adapter
        (drydocs-api, ADR 0005) · payload shaped server-side (c4-graph named query) · layout
        d3-force, deterministic
      </div>
    </main>
  )
}
