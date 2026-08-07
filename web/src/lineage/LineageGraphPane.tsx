import { useMemo, type CSSProperties } from 'react'
import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import TrustLegend from '../components/TrustLegend'
import {
  LINEAGE_EDGES,
  LINEAGE_KIND_TOKEN,
  LINEAGE_NODES,
  type LineageSelection,
} from './demoLineage'

// Lineage's graph pane (O10): the source→target DAG on React Flow — the mock
// subpage-2 pattern. Node/edge colors route through theme tokens (both
// schemes); node click writes the SHARED selection lifted in LineageRoute
// (same linking contract as Explorer).

type LineageNodeData = { label: string; kind: string; token: string; selected: boolean }
type LineageRFNode = Node<LineageNodeData, 'lineage'>

function LineageNode({ data }: NodeProps<LineageRFNode>) {
  return (
    <div
      className="rf-node rounded-md border-2 bg-panel px-2.5 py-1.5 text-center shadow-sm"
      style={
        {
          borderColor: `var(${data.token})`,
          '--rf-glow': `var(${data.token})`,
          boxShadow: data.selected
            ? `0 0 0 3px color-mix(in srgb, var(${data.token}) 35%, transparent)`
            : undefined,
        } as CSSProperties
      }
    >
      <Handle type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="text-xs font-semibold text-text">{data.label}</div>
      <div className="font-mono text-[10px]" style={{ color: `var(${data.token})` }}>
        {data.kind}
      </div>
      <Handle type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { lineage: LineageNode }

export default function LineageGraphPane({
  selection,
  onSelect,
}: {
  selection: LineageSelection | null
  onSelect: (sel: LineageSelection | null) => void
}) {
  const nodes: LineageRFNode[] = useMemo(
    () =>
      LINEAGE_NODES.map((n) => ({
        id: n.id,
        type: 'lineage' as const,
        position: { x: n.x, y: n.y },
        data: {
          label: n.label,
          kind: n.kind,
          token: LINEAGE_KIND_TOKEN[n.kind],
          selected: selection?.id === n.id,
        },
      })),
    [selection],
  )

  const edges: Edge[] = useMemo(
    () =>
      LINEAGE_EDGES.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.rel,
        style: { stroke: 'var(--faint)', strokeWidth: 1.4 },
        labelStyle: { fill: 'var(--muted)', fontSize: 10, fontFamily: 'var(--mono)' },
        labelBgStyle: { fill: 'var(--panel)', fillOpacity: 0.85 },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--faint)', width: 16, height: 16 },
      })),
    [],
  )

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-edge-soft px-3 py-2">
        <span className="text-xs font-medium text-muted">Data-series chain · source → target</span>
        <span className="ml-auto rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
          EXAMPLE DATA · ILLUSTRATIVE — curated rows land after the lineage live-load gate
        </span>
      </div>
      <div className="min-h-0 flex-1 bg-bg-2">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => {
            const dn = LINEAGE_NODES.find((n) => n.id === node.id)
            if (dn) onSelect({ id: dn.id, label: dn.label, kind: dn.kind })
          }}
          onPaneClick={() => onSelect(null)}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          proOptions={{ hideAttribution: false }}
          nodesDraggable={false}
          nodesConnectable={false}
          edgesFocusable={false}
          minZoom={0.4}
          maxZoom={2}
        >
          <Background color="var(--edge)" gap={22} />
          <Controls showInteractive={false} />
          <TrustLegend />
        </ReactFlow>
      </div>
    </div>
  )
}
