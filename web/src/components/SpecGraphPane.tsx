import { useEffect, useMemo, useState } from 'react'

import type { GraphAccess, SpecResult } from '../lib/graph'
import { CANVAS_SURFACES, type CanvasNode, type CanvasSpecId } from '../lib/nvl-mapping'
import GraphCanvas from './GraphCanvas'
import EmptyState from './ui/EmptyState'
import { IdChip } from './ui/IdChip'

// A QuerySpec-bound GRAPH frame (O81 step 4) — the canvas's sibling to SpecGrid.
// SpecGrid renders a reviewed spec's rows as a table; this renders the SAME
// reviewed spec's rows as the graph they were flattened from. One fetch path,
// one registry, one server-side decision about which database answers.
//
// THE PAIRING IS BY SPEC ID, from CANVAS_SURFACES. A mapper knows which Cypher
// pattern its spec walked, so pairing a spec with a mapper written for a
// different row shape is the one mistake that would put an invented edge on
// screen — the type here makes that unrepresentable rather than merely
// discouraged.
//
// FAILURE IS LOUD, and does NOT fall back to a demo graph. SpecGrid drops to a
// synthesized grid when the API is down, with a visible notice; a canvas has no
// equivalent, because a picture of fabricated topology is far more convincing
// than a table of it and there is no honest way to caption that difference at a
// glance. So this frame reports the error and draws nothing.

export interface SpecGraphPaneProps {
  access: GraphAccess
  specId: CanvasSpecId
  title: string
  badge?: string
  /** Lifted so the canvas and the route's other frames share one selection. */
  selected: CanvasNode | null
  onSelect: (node: CanvasNode | null) => void
}

export default function SpecGraphPane({
  access,
  specId,
  title,
  badge,
  selected,
  onSelect,
}: SpecGraphPaneProps) {
  const [result, setResult] = useState<SpecResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setResult(null)
    setError(null)
    access
      .runSpec(specId)
      .then((r) => {
        if (!cancelled) setResult(r)
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message)
      })
    return () => {
      cancelled = true
    }
  }, [access, specId])

  const graph = useMemo(() => {
    if (!result) return null
    return CANVAS_SURFACES[specId](result.rows)
  }, [result, specId])

  if (error) {
    return (
      <EmptyState
        title="The graph could not be loaded"
        hint={`${specId} — ${error}. Nothing is drawn rather than drawing something that is not the graph.`}
      />
    )
  }
  if (!graph) return <EmptyState title="Loading the graph…" hint={specId} />

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1">
        <GraphCanvas
          graph={graph}
          selectedId={selected?.id ?? null}
          onSelect={onSelect}
          title={title}
          badge={badge ?? result?.classification?.toUpperCase()}
        />
      </div>
      {selected && <SelectedNodeDetail node={selected} onClose={() => onSelect(null)} />}
    </div>
  )
}

/** The detail strip for a selected node.
 *
 *  Built from the EXISTING primitives (IdChip and the shared tokens) rather than
 *  a new detail renderer — O81 step 3 forbids duplicate detail rendering, and
 *  NodeInspector cannot be reused directly because it is typed to the demo
 *  graph's Selection/NodeKind, not to spec-derived nodes. The properties shown
 *  are exactly the ones the ROW carried; this panel never fetches, so it can
 *  never show a fact the reviewed spec did not return. */
function SelectedNodeDetail({ node, onClose }: { node: CanvasNode; onClose: () => void }) {
  const entries = Object.entries(node.properties).filter(([, v]) => v)
  return (
    <div className="border-t border-edge bg-panel-2/40 px-3 py-2">
      <div className="flex items-center gap-2">
        <IdChip id={node.caption} />
        <span className="font-mono text-[10px] text-muted">{node.kind}</span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Clear selection"
          className="ml-auto rounded px-1.5 text-muted hover:bg-panel-2 hover:text-text"
        >
          ✕
        </button>
      </div>
      {entries.length > 0 && (
        <dl className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
          {entries.map(([k, v]) => (
            <div key={k} className="col-span-2 grid grid-cols-subgrid">
              <dt className="text-faint">{k}</dt>
              <dd className="truncate font-mono text-text">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  )
}
