import { useMemo, useState, type CSSProperties } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import ModuleToolbar from '../layout/ModuleToolbar'
import EmptyState from '../components/ui/EmptyState'
import {
  appById,
  assetById,
  expandable,
  initialVisible,
  pathCypher,
  PATH_EDGES,
  PATH_NODES,
  type PathNode,
} from '../ownership/assetSearch'

// /ownership/asset/:assetId (2026-07-21 chat; wf-runbook-path-01 made real):
// the support answer page for ONE searched file/table. Two-lane path graph
// (technical + data) rendered neo4j-browser-style — the user doesn't know
// Cypher and the system doesn't know exactly what they meant, so the result
// is a GRAPH they steer: click a node → Expand neighbors / Remove from view.
// The cypher panel shows the assumed path spec (needle-bound); the proposed
// runbook below is a PROJECTION of the currently visible path nodes — remove
// a node and its step disappears, honestly.

type PathNodeData = { label: string; sub: string; token: string; selected: boolean; searched: boolean; expandableCount: number }
type PathRFNode = Node<PathNodeData, 'path'>

function PathNodeView({ data }: NodeProps<PathRFNode>) {
  return (
    <div
      className="rf-node rounded-md border-2 bg-panel px-2.5 py-1.5 text-center"
      style={
        {
          borderColor: `var(${data.token})`,
          '--rf-glow': `var(${data.token})`,
          boxShadow: data.selected
            ? `0 0 0 3px color-mix(in srgb, var(${data.token}) 40%, transparent)`
            : data.searched
              ? `0 0 0 3px color-mix(in srgb, var(--yellow) 45%, transparent)`
              : undefined,
        } as CSSProperties
      }
    >
      {/* handles on BOTH sides so rtl vocabulary edges (REQUIRES_IN_CONDITION,
          derived WAS_ASSOCIATED_WITH) attach cleanly instead of wrapping */}
      <Handle id="tl" type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <Handle id="tr" type="target" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="max-w-44 truncate font-mono text-[11px] font-semibold text-text">{data.label}</div>
      <div className="text-[10px]" style={{ color: `var(${data.token})` }}>
        {data.sub}
        {data.expandableCount > 0 && <span className="ml-1 text-faint">(+{data.expandableCount})</span>}
      </div>
      <Handle id="sr" type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <Handle id="sl" type="source" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { path: PathNodeView }

export default function AssetPathRoute() {
  const { assetId } = useParams()
  const asset = assetId ? assetById(assetId) : undefined
  const [visible, setVisible] = useState<Set<string>>(initialVisible)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selected: PathNode | undefined = PATH_NODES.find((n) => n.id === selectedId)
  const selectedExpandable = selectedId ? expandable(selectedId, visible) : []

  const nodes: PathRFNode[] = useMemo(
    () =>
      PATH_NODES.filter((n) => visible.has(n.id)).map((n) => ({
        id: n.id,
        type: 'path' as const,
        position: { x: n.x, y: n.y },
        data: {
          label: n.label,
          sub: n.sub,
          token: n.token,
          selected: n.id === selectedId,
          searched: n.id === asset?.nodeId,
          expandableCount: expandable(n.id, visible).length,
        },
      })),
    [visible, selectedId, asset],
  )

  const edges: Edge[] = useMemo(
    () =>
      PATH_EDGES.filter((e) => visible.has(e.source) && visible.has(e.target))
        // the summary condition edge hides once the Condition node is expanded
        .filter((e) => !(e.id === 'e3' && visible.has('cond')))
        .map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.dir === 'rtl' ? 'sl' : 'sr',
          targetHandle: e.dir === 'rtl' ? 'tr' : 'tl',
          label: e.label,
          style: { stroke: 'var(--faint)', strokeWidth: 1.3 },
          labelStyle: { fill: 'var(--muted)', fontSize: 9.5, fontFamily: 'var(--mono)' },
          labelBgStyle: { fill: 'var(--panel)', fillOpacity: 0.85 },
          markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--faint)', width: 15, height: 15 },
        })),
    [visible],
  )

  if (!asset) {
    return (
      <div className="p-6">
        <EmptyState title="Unknown asset" hint="Search again from the Ownership page." />
        <Link to="/ownership" className="mt-3 inline-block text-sm text-blue-bright">← back to Ownership</Link>
      </div>
    )
  }
  const app = appById(asset.appId)

  function expandSelected() {
    if (!selectedId) return
    setVisible((v) => new Set([...v, ...expandable(selectedId, v)]))
  }
  function removeSelected() {
    if (!selected || selected.anchor) return
    setVisible((v) => {
      const next = new Set(v)
      next.delete(selected.id)
      return next
    })
    setSelectedId(null)
  }

  const runbookRows = PATH_NODES.filter((n) => visible.has(n.id) && n.runbook)

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Ownership', to: '/ownership' }, { label: asset.name }]}
      />
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <h2 tabIndex={-1} data-view-heading className="text-lg font-semibold text-text outline-none">
          {asset.name}
        </h2>

        {/* the two support answers, up front */}
        <div className="mt-2 grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="rounded-lg border border-edge bg-panel p-3 text-xs">
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-faint">Who supports this</h3>
            <p className="text-text">{asset.support.team}</p>
            <p className="font-mono text-[11px] text-muted">queue {asset.support.queue} · {asset.support.hours}</p>
            <p className="mt-1 text-faint">{app?.label}</p>
          </div>
          <div className="rounded-lg border border-edge bg-panel p-3 text-xs">
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-faint">Load status</h3>
            <p className={'font-mono text-[11px] ' + (asset.load.state === 'LATE' ? 'text-brand-soft' : 'text-green')}>
              {asset.load.state} · expected by {asset.load.expectedBy}
            </p>
            <p className="text-muted">last loaded: {asset.load.lastLoaded}</p>
            <p className="text-text">{asset.load.blocking}</p>
          </div>
          <div className="rounded-lg border border-edge bg-panel p-3 text-xs">
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-faint">Selected node</h3>
            {selected ? (
              <>
                <p className="font-mono text-[11px] text-text">{selected.label}</p>
                <p className="text-faint">{selected.sub}</p>
                <span className="mt-1.5 flex gap-1.5">
                  <button
                    type="button"
                    onClick={expandSelected}
                    disabled={selectedExpandable.length === 0}
                    className="rounded-md border border-teal px-2 py-0.5 text-[11px] text-teal disabled:opacity-40"
                  >
                    Expand +{selectedExpandable.length}
                  </button>
                  <button
                    type="button"
                    onClick={removeSelected}
                    disabled={!!selected.anchor}
                    title={selected.anchor ? 'source/target anchors stay' : undefined}
                    className="rounded-md border border-edge px-2 py-0.5 text-[11px] text-muted disabled:opacity-40"
                  >
                    Remove from view
                  </button>
                </span>
              </>
            ) : (
              <p className="text-faint">Click a node — expand its neighbors or remove it from the view.</p>
            )}
          </div>
        </div>

        {/* the steerable path graph */}
        <div className="mt-3 overflow-hidden rounded-lg border border-edge bg-panel">
          <div className="flex flex-wrap items-center gap-2 border-b border-edge-soft px-3 py-1.5">
            <span className="font-mono text-[10px] text-faint">
              TECHNICAL lane (top) · DATA lane (bottom) · path 1 of 1 · {nodes.length} nodes shown
            </span>
            <button
              type="button"
              onClick={() => {
                setVisible(initialVisible())
                setSelectedId(null)
              }}
              className="rounded-md border border-edge px-2 py-0.5 text-[11px] text-muted hover:text-text"
            >
              Reset view
            </button>
            <span className="ml-auto rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
              EXAMPLE DATA · ILLUSTRATIVE
            </span>
          </div>
          <div className="h-105 bg-bg-2">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, node) => setSelectedId(node.id)}
              onPaneClick={() => setSelectedId(null)}
              fitView
              fitViewOptions={{ padding: 0.16 }}
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

        {/* the honest cypher + the runbook projection */}
        <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <div className="rounded-lg border border-edge bg-panel p-3">
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-faint">
              Path query (the assumed contract — shown even though you never have to write it)
            </h3>
            <pre className="overflow-x-auto rounded-md border border-edge-soft bg-bg p-2.5 font-mono text-[11px] leading-relaxed text-muted">
              {pathCypher(asset.name)}
            </pre>
          </div>
          <div className="rounded-lg border border-edge bg-panel p-3">
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-faint">
              Proposed runbook — a projection of the visible path
            </h3>
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['#', 'Lane', 'Node', 'Action', 'Verify'].map((h) => (
                    <th key={h} className="border-b border-edge py-1 pr-2 text-left text-[10px] font-semibold uppercase tracking-wide text-faint">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runbookRows.map((n, i) => (
                  <tr
                    key={n.id}
                    onClick={() => setSelectedId(n.id)}
                    className={'cursor-pointer hover:bg-bg-2 ' + (n.id === selectedId ? 'bg-panel-2' : '')}
                  >
                    <td className="border-b border-edge-soft py-1.5 pr-2 text-muted">{i + 1}</td>
                    <td className={'border-b border-edge-soft py-1.5 pr-2 ' + (n.lane === 'tech' ? 'text-blue-bright' : 'text-green')}>
                      {n.lane}
                    </td>
                    <td className="border-b border-edge-soft py-1.5 pr-2 font-mono text-[11px] text-text">{n.label}</td>
                    <td className="border-b border-edge-soft py-1.5 pr-2 text-text">{n.runbook!.action}</td>
                    <td className="border-b border-edge-soft py-1.5 font-mono text-[11px] text-muted">{n.runbook!.verify}</td>
                  </tr>
                ))}
                {runbookRows.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-2 text-faint">No runbook-bearing nodes visible — Reset view.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-3 font-mono text-[10px] text-faint">
          SYNTHESIZED demo path (wf-runbook-path-01 made real) — this is the OVERVIEW start of a runbook; detail
          fills in per node as the graph and its QuerySpecs mature. Live twin: runbooks.app-path.v1.
        </p>
      </div>
    </div>
  )
}
