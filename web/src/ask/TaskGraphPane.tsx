import { useMemo, useState } from 'react'
import { forceLayout, trimEdge } from '../lib/forceLayout'
import type { TaskGraphSnapshot } from './askApi'

// R6 — the Tier-2 task graph, one frame per iteration.
//
// This renders the agent's WORKING MEMORY, not the knowledge graph, and the two
// must not be confusable at a glance: a viewer who mistakes a synthesized
// sub-question node for a real graph node has been actively misled. Hence the
// separate visual language (kind-keyed colours, the phase stepper, the explicit
// caption) even though the placement engine is shared with GraphExplorer.
//
// The snapshots are ephemeral by ruling, not by omission — R1 (2026-07-23) put
// the task graph in-process only, so these frames exist for the life of the
// answer on screen and nowhere else. There is deliberately no export.

const W = 620
const H = 300
const R = 22
const PAD = 34

const KIND_COLOR: Record<string, string> = {
  question: 'var(--blue-bright)',
  subquestion: 'var(--yellow)',
  evidence: 'var(--teal)',
  answer: 'var(--green, var(--teal))',
}

const PHASE_LABEL: Record<string, string> = {
  start: 'question',
  iteration: 'round',
  final: 'answer',
}

function short(text: string, max = 22): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

export default function TaskGraphPane({ snapshots }: { snapshots: TaskGraphSnapshot[] }) {
  const [frame, setFrame] = useState(snapshots.length - 1)
  const snap = snapshots[Math.min(frame, snapshots.length - 1)]

  const placed = useMemo(
    () =>
      snap
        ? forceLayout(
            snap.edges ?? [],
            { width: W, height: H, radius: R, pad: PAD, linkDistance: 90, charge: -300 },
            // the opening frame is one node with NO edges — without this it
            // would render empty
            (snap.nodes ?? []).map((n) => n.id),
          )
        : [],
    [snap],
  )
  const byId = useMemo(() => new Map(placed.map((n) => [n.id, n])), [placed])
  const nodeById = useMemo(
    () => new Map((snap?.nodes ?? []).map((n) => [n.id, n])),
    [snap],
  )

  if (!snap) return null

  return (
    <div>
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <h4 className="text-[11px] font-semibold uppercase tracking-wide text-faint">
          Tier-2 task graph
        </h4>
        <span className="font-mono text-[9px] text-faint">
          in-process working memory · not the knowledge graph
        </span>
        <div className="ml-auto flex gap-1" role="group" aria-label="Task graph iteration">
          {snapshots.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setFrame(i)}
              aria-pressed={i === frame}
              className={`rounded border px-1.5 py-0.5 font-mono text-[9px] ${
                i === frame
                  ? 'border-blue-bright text-blue-bright'
                  : 'border-edge-soft text-muted hover:border-faint'
              }`}
            >
              {PHASE_LABEL[s.phase] ?? s.phase}
              {s.phase === 'iteration' ? ` ${s.iteration}` : ''}
            </button>
          ))}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label={`Tier-2 task graph, ${PHASE_LABEL[snap.phase] ?? snap.phase}: ${
          (snap.nodes ?? []).length
        } nodes, ${(snap.edges ?? []).length} edges`}
        className="rounded border border-edge-soft bg-bg-2/40"
      >
        <defs>
          <marker
            id="tg-arr"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 z" fill="#8A97A8" />
          </marker>
        </defs>

        {(snap.edges ?? []).map((e, i) => {
          const a = byId.get(e.source)
          const b = byId.get(e.target)
          if (!a || !b) return null
          const { x1, y1, x2, y2 } = trimEdge(a, b, R)
          return (
            <g key={i}>
              <title>{`${e.source} → ${e.target} · ${e.via}`}</title>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#3C4E66"
                strokeWidth="1.4"
                markerEnd="url(#tg-arr)"
              />
            </g>
          )
        })}

        {placed.map((p) => {
          const node = nodeById.get(p.id)
          if (!node) return null
          const color = KIND_COLOR[node.kind] ?? 'var(--muted)'
          return (
            <g key={p.id}>
              <title>{`${node.kind}: ${node.label}${
                node.rows == null ? '' : ` (${node.rows} rows)`
              }`}</title>
              <circle
                cx={p.x}
                cy={p.y}
                r={R}
                fill={color}
                opacity=".16"
                stroke={color}
                strokeWidth="1.6"
              />
              <text
                x={p.x}
                y={p.y + 1}
                textAnchor="middle"
                className="fill-current text-[8px] text-text"
              >
                {short(node.kind === 'answer' ? 'answer' : node.label, 14)}
              </text>
              <text
                x={p.x}
                y={p.y + 12}
                textAnchor="middle"
                className="fill-current font-mono text-[7px] text-faint"
              >
                {node.rows == null ? node.kind : `${node.rows} rows`}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
