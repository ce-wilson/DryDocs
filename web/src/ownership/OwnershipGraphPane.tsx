import { useMemo, useState, type CSSProperties } from 'react'
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
import type { Persona } from '../lib/auth'
import MyApps from '../components/MyApps'
import {
  OWNERSHIP_EDGES,
  OWNERSHIP_KIND_TOKEN,
  OWNERSHIP_NODES,
  type OwnershipSelection,
} from './demoOwnership'

// Ownership's graph pane (O15): the SEAL→PAT rollup rendered in the K4
// qualified-attribution shape — Attribution nodes with their TOMRole
// crosswalk, unmapped_role=true VISIBLY flagged (never hidden). The kept
// O2 MyApps view survives as a toggled alternate ("My apps"), so O15 is the
// template-instantiation upgrade the backlog names, not a teardown.

type OwnNodeData = { label: string; kind: string; token: string; unmapped: boolean; selected: boolean }
type OwnRFNode = Node<OwnNodeData, 'own'>

function OwnNode({ data }: NodeProps<OwnRFNode>) {
  return (
    <div
      className="rf-node max-w-56 rounded-md border-2 bg-panel px-2.5 py-1.5 text-center shadow-sm"
      style={
        {
          borderColor: data.unmapped ? 'var(--red)' : `var(${data.token})`,
          '--rf-glow': data.unmapped ? 'var(--red)' : `var(${data.token})`,
          boxShadow: data.selected
            ? `0 0 0 3px color-mix(in srgb, var(${data.token}) 35%, transparent)`
            : undefined,
        } as CSSProperties
      }
    >
      {/* handles on BOTH sides: vocabulary edges run in both directions along
          the chain layout (e.g. DevTeam -SUPPORTS-> AreaProduct), so rtl edges
          attach left-source → right-target instead of wrapping around */}
      <Handle id="tl" type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <Handle id="tr" type="target" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="break-all text-[11px] font-semibold text-text">{data.label}</div>
      <div className="font-mono text-[10px]" style={{ color: `var(${data.token})` }}>
        {data.kind}
      </div>
      {data.unmapped && (
        <div className="mt-0.5 rounded border border-red/60 bg-red/10 px-1 font-mono text-[9px] text-brand-soft">
          unmapped_role=true — needs crosswalk
        </div>
      )}
      <Handle id="sr" type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <Handle id="sl" type="source" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { own: OwnNode }

export default function OwnershipGraphPane({
  persona,
  selection,
  onSelect,
}: {
  persona: Persona
  selection: OwnershipSelection | null
  onSelect: (sel: OwnershipSelection | null) => void
}) {
  const [view, setView] = useState<'rollup' | 'myapps'>('rollup')

  const nodes: OwnRFNode[] = useMemo(
    () =>
      OWNERSHIP_NODES.map((n) => ({
        id: n.id,
        type: 'own' as const,
        position: { x: n.x, y: n.y },
        data: {
          label: n.label,
          kind: n.kind,
          token: OWNERSHIP_KIND_TOKEN[n.kind],
          unmapped: Boolean(n.unmapped),
          selected: selection?.id === n.id,
        },
      })),
    [selection],
  )

  const edges: Edge[] = useMemo(
    () =>
      OWNERSHIP_EDGES.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.dir === 'rtl' ? 'sl' : 'sr',
        targetHandle: e.dir === 'rtl' ? 'tr' : 'tl',
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
        {(
          [
            ['rollup', 'Rollup (K4 shape)'],
            ['myapps', 'My apps'],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setView(k)}
            aria-pressed={view === k}
            className={
              'rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ' +
              (view === k
                ? 'border-blue-bright bg-blue/15 text-blue-bright'
                : 'border-edge text-muted hover:border-faint hover:text-text')
            }
          >
            {label}
          </button>
        ))}
        {view === 'rollup' && (
          <span className="ml-auto rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
            EXAMPLE DATA · ILLUSTRATIVE — K4 qualified-attribution shape
          </span>
        )}
      </div>
      {view === 'myapps' ? (
        <div className="min-h-0 flex-1 overflow-auto">
          <MyApps persona={persona} />
        </div>
      ) : (
        <div className="min-h-0 flex-1 bg-bg-2">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodeClick={(_, node) => {
              const dn = OWNERSHIP_NODES.find((n) => n.id === node.id)
              if (dn) onSelect({ id: dn.id, label: dn.label, kind: dn.kind })
            }}
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
          </ReactFlow>
        </div>
      )}
    </div>
  )
}
