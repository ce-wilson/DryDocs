import type { GraphSpec } from '../data/towers'

const R = 27

// SVG text styles, shared with GraphExplorer's live pane (formerly App.css
// .gnode/.gsub/.gedge — O30 moved them inline; the grays are the mockup's
// dark-language values, kept verbatim for parity until the O32 light pass).
export const GNODE = 'fill-[#e8edf3] text-[11px] font-semibold'
export const GSUB = 'fill-[#8a97a8] font-mono text-[9px]'
export const GEDGE = 'fill-[#8a97a8] font-mono text-[9px] font-medium'

// Pure SVG graph renderer — port of the mockup's renderGraph(): circle nodes
// with label + :sub, straight edges trimmed to the node radius, arrowheads.
export default function GraphSvg({ graph, viewBox = '0 0 620 300', ariaLabel }: {
  graph: GraphSpec
  viewBox?: string
  ariaLabel: string
}) {
  const markerId = `garr-${ariaLabel.replace(/\W+/g, '-').toLowerCase()}`
  return (
    <svg viewBox={viewBox} width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label={ariaLabel}>
      <defs>
        <marker id={markerId} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="#8A97A8" />
        </marker>
      </defs>
      {graph.edges.map(([a, b, rel], i) => {
        const n1 = graph.nodes[a]
        const n2 = graph.nodes[b]
        const dx = n2.x - n1.x
        const dy = n2.y - n1.y
        const len = Math.hypot(dx, dy)
        const x1 = n1.x + (dx / len) * R
        const y1 = n1.y + (dy / len) * R
        const x2 = n2.x - (dx / len) * (R + 4)
        const y2 = n2.y - (dy / len) * (R + 4)
        return (
          <g key={i}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3C4E66" strokeWidth="1.6" markerEnd={`url(#${markerId})`} />
            <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 6} textAnchor="middle" className={GEDGE}>{rel}</text>
          </g>
        )
      })}
      {graph.nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={R} fill={n.c} opacity=".16" stroke={n.c} strokeWidth="2" />
          <text x={n.x} y={n.y + 1} textAnchor="middle" className={GNODE}>{n.label}</text>
          <text x={n.x} y={n.y + 15} textAnchor="middle" className={GSUB}>:{n.sub}</text>
        </g>
      ))}
    </svg>
  )
}
