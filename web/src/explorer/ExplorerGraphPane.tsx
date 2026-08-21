import { useMemo, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Node,
  type NodeProps,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { relEdgeTypes, type RelFlowEdge } from '../components/RelEdge'
import type { Persona } from '../lib/auth'
import { canDrill } from '../lib/views'
import { TOWERS, TOWER_KEYS, type TowerKey } from '../data/towers'
import { KIND_TOKEN, towerEdges, towerNodes, type NodeKind, type Selection } from './demoGraph'

// Explorer's graph pane (O9): the tower/app drill-down graph on React Flow.
// Tower chips switch the rendered pipeline; node click writes the SHARED
// selection (lifted in ExplorerRoute) that also drives the data frames and the
// right node inspector. All node/edge colors route through theme tokens.

type DemoNodeData = { label: string; kind: NodeKind; selected: boolean }
type DemoRFNode = Node<DemoNodeData, 'demo'>

function DemoNode({ data }: NodeProps<DemoRFNode>) {
  const token = KIND_TOKEN[data.kind]
  return (
    <div
      className="rf-node rounded-md border-2 bg-panel px-2.5 py-1.5 text-center shadow-sm"
      style={
        {
          borderColor: `var(${token})`,
          '--rf-glow': `var(${token})`,
          boxShadow: data.selected ? `0 0 0 3px color-mix(in srgb, var(${token}) 35%, transparent)` : undefined,
        } as CSSProperties
      }
    >
      <Handle type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="text-xs font-semibold text-text">{data.label}</div>
      <div className="font-mono text-[10px]" style={{ color: `var(${token})` }}>
        {data.kind}
      </div>
      <Handle type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { demo: DemoNode }

interface ExplorerGraphPaneProps {
  persona: Persona
  tower: TowerKey
  onTowerChange: (t: TowerKey) => void
  selection: Selection | null
  onSelect: (sel: Selection | null) => void
}

export default function ExplorerGraphPane({ persona, tower, onTowerChange, selection, onSelect }: ExplorerGraphPaneProps) {
  const nodes: DemoRFNode[] = useMemo(
    () =>
      towerNodes(tower).map((n, i) => {
        const raw = TOWERS[tower].graph.nodes[i]
        return {
          id: n.id,
          type: 'demo' as const,
          position: { x: raw.x * 1.35, y: raw.y * 1.15 },
          data: { label: n.label, kind: n.kind, selected: selection?.id === n.id },
        }
      }),
    [tower, selection],
  )

  const edges: RelFlowEdge[] = useMemo(
    () =>
      towerEdges(tower).map((e) => ({
        id: e.id,
        type: 'rel' as const,
        source: e.source,
        target: e.target,
        // O66: name + stroke render via the shared RelEdge overlay chip
        data: { rel: e.rel },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--faint)', width: 16, height: 16 },
      })),
    [tower],
  )

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-edge-soft px-3 py-2">
        {TOWER_KEYS.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => {
              onTowerChange(k)
              onSelect(null)
            }}
            aria-pressed={k === tower}
            className={
              'rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ' +
              (k === tower
                ? 'border-blue-bright bg-blue/15 text-blue-bright'
                : 'border-edge text-muted hover:border-faint hover:text-text')
            }
          >
            {TOWERS[k].title}
          </button>
        ))}
        <span className="ml-auto rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
          EXAMPLE DATA · ILLUSTRATIVE
        </span>
        {canDrill(tower, persona) && (
          <Link to={`/explorer/tower/${tower}`} className="text-xs text-blue-bright">
            Open drill-down →
          </Link>
        )}
        <Link to="/explorer/live" className="text-xs text-muted hover:text-blue-bright" title="Real WAS_INFORMED_BY edges (O6)">
          live graph
        </Link>
      </div>
      <div className="min-h-0 flex-1 bg-bg-2">
        {/* key= remounts per tower so fitView re-frames the new pipeline */}
        <ReactFlow
          key={tower}
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={relEdgeTypes}
          onNodeClick={(_, node) => {
            const dn = towerNodes(tower).find((n) => n.id === node.id)
            if (dn) onSelect({ id: dn.id, label: dn.label, kind: dn.kind, tower })
          }}
          onPaneClick={() => onSelect(null)}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          proOptions={{ hideAttribution: false }}
          nodesDraggable={false}
          nodesConnectable={false}
          edgesFocusable={false}
          minZoom={0.4}
          maxZoom={2}
        >
          <Background color="var(--edge)" gap={22} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  )
}
