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
import TrustLegend from './TrustLegend'

// The shared mini-DAG graph pane (extracted at O17 — the 4th copy of this
// React Flow boilerplate was the signal): theme-token node colors, labeled
// edges, optional red flag ribbon per node, shared-selection glow. Module
// panes pass data + a badge; everything else is identical by construction.

export interface DagNodeDef {
  id: string
  label: string
  /** small mono sub-line (kind / role) */
  sub: string
  /** css custom-property name, e.g. '--blue' */
  token: string
  /** optional red flag ribbon text (e.g. unmapped_role, artifact-not-in-SCM) */
  flag?: string
  x: number
  y: number
}

export interface DagEdgeDef {
  id: string
  source: string
  target: string
  label?: string
}

type MiniDagData = { def: DagNodeDef; selected: boolean }
type MiniDagRFNode = Node<MiniDagData, 'mini'>

function MiniDagNode({ data }: NodeProps<MiniDagRFNode>) {
  const { def, selected } = data
  return (
    <div
      className="rf-node max-w-56 rounded-md border-2 bg-panel px-2.5 py-1.5 text-center shadow-sm"
      style={
        {
          borderColor: def.flag ? 'var(--red)' : `var(${def.token})`,
          '--rf-glow': def.flag ? 'var(--red)' : `var(${def.token})`,
          boxShadow: selected ? `0 0 0 3px color-mix(in srgb, var(${def.token}) 35%, transparent)` : undefined,
        } as CSSProperties
      }
    >
      <Handle type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="break-all text-[11px] font-semibold text-text">{def.label}</div>
      <div className="font-mono text-[10px]" style={{ color: `var(${def.token})` }}>
        {def.sub}
      </div>
      {def.flag && (
        <div className="mt-0.5 rounded border border-red/60 bg-red/10 px-1 font-mono text-[9px] text-brand-soft">
          {def.flag}
        </div>
      )}
      <Handle type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { mini: MiniDagNode }

export default function MiniDag({
  nodes,
  edges,
  badge,
  title,
  selectedId,
  onSelect,
  legend = false,
}: {
  nodes: readonly DagNodeDef[]
  edges: readonly DagEdgeDef[]
  badge: string
  title: string
  selectedId: string | null
  onSelect: (id: string | null) => void
  /** O29: opt-in trust-tier/provenance legend (the /docs corpus canvas wants it; other consumers opt in as their content mixes trust) */
  legend?: boolean
}) {
  const rfNodes: MiniDagRFNode[] = useMemo(
    () =>
      nodes.map((n) => ({
        id: n.id,
        type: 'mini' as const,
        position: { x: n.x, y: n.y },
        data: { def: n, selected: selectedId === n.id },
      })),
    [nodes, selectedId],
  )
  const rfEdges: Edge[] = useMemo(
    () =>
      edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        style: { stroke: 'var(--faint)', strokeWidth: 1.4 },
        labelStyle: { fill: 'var(--muted)', fontSize: 10, fontFamily: 'var(--mono)' },
        labelBgStyle: { fill: 'var(--panel)', fillOpacity: 0.85 },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--faint)', width: 16, height: 16 },
      })),
    [edges],
  )

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-edge-soft px-3 py-2">
        <span className="text-xs font-medium text-muted">{title}</span>
        <span className="ml-auto rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
          {badge}
        </span>
      </div>
      <div className="min-h-0 flex-1 bg-bg-2">
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => onSelect(selectedId === node.id ? null : node.id)}
          onPaneClick={() => onSelect(null)}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          proOptions={{ hideAttribution: false }}
          nodesDraggable={false}
          nodesConnectable={false}
          edgesFocusable={false}
          minZoom={0.3}
          maxZoom={2}
        >
          <Background color="var(--edge)" gap={22} />
          <Controls showInteractive={false} />
          {legend && <TrustLegend />}
        </ReactFlow>
      </div>
    </div>
  )
}
