import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getStraightPath,
  type Edge,
  type EdgeProps,
} from '@xyflow/react'

// O66: the ONE relationship-label treatment for every ReactFlow canvas —
// ownership, explorer, and lineage all render their edge names through this
// component, so a future label change fixes all three at once. The label is
// an HTML chip in the EdgeLabelRenderer portal, NOT the built-in SVG `label`
// prop: the SVG label paints in the edge layer, which stacks BELOW nodes, so
// on layouts where an edge is short relative to its name (ownership's
// left-to-right K4 chain) the name clips behind the node boxes and the page's
// subject becomes unreadable. The chip carries an explicit zIndex because the
// edgelabel-renderer portal has none of its own — without it the chip resolves
// to DOM order and STILL paints under the nodes (the exact defect, observed
// in-browser 2026-08-21 against the first EdgeLabelRenderer attempt).
// Everything themes through tokens; nothing here decides what an edge MEANS
// (K4's attribution shape is gate-confirmed and out of scope for rendering).

export type RelEdgeData = { rel: string; path?: 'straight' | 'bezier' }
export type RelFlowEdge = Edge<RelEdgeData, 'rel'>

export default function RelEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}: EdgeProps<RelFlowEdge>) {
  // straight for chain layouts (ownership); bezier default matches the curve
  // the explorer/lineage canvases rendered before adopting this component
  const [path, labelX, labelY] =
    data?.path === 'straight'
      ? getStraightPath({ sourceX, sourceY, targetX, targetY })
      : getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition })
  return (
    <>
      <BaseEdge path={path} markerEnd={markerEnd} style={{ stroke: 'var(--faint)', strokeWidth: 1.4 }} />
      <EdgeLabelRenderer>
        <div
          className="pointer-events-none absolute whitespace-nowrap rounded border border-edge bg-panel px-1.5 py-0.5 font-mono text-[10px] text-muted shadow-sm"
          style={{ transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`, zIndex: 10 }}
        >
          {data?.rel}
        </div>
      </EdgeLabelRenderer>
    </>
  )
}

/** Pass as `edgeTypes` (module-level const, so ReactFlow never sees a new object per render). */
export const relEdgeTypes = { rel: RelEdge }
