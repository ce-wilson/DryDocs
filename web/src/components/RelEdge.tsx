import { useLayoutEffect, useRef, useState } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getStraightPath,
  useStore,
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
//
// O77: THAT FIX TRADED ONE OCCLUSION FOR THE OTHER, and the reason is geometry,
// not paint order. A chip drawn at the path midpoint sits inside a neighbouring
// node's rect whenever the layout's column pitch is near the node width — which
// ownership's is (185-220px pitch, boxes up to max-w-56 = 224px). Winning the
// z-fight only chooses WHICH text is destroyed: pre-O66 the relationship name
// lost, post-O66 the node name did. So the chip now MOVES instead of stacking:
// it is measured, tested against the real node rects, and walked out along the
// edge's perpendicular to the first position that intersects nothing. When the
// midpoint is already clear — the common case on the bezier canvases — nothing
// moves at all, so explorer and lineage keep the placement they have today.

export type RelEdgeData = { rel: string; path?: 'straight' | 'bezier' }
export type RelFlowEdge = Edge<RelEdgeData, 'rel'>

/** Flow-coordinate rect. Chips and nodes are both measured pre-transform, so
 *  the two are directly comparable without dividing anything by the zoom. */
type Rect = { x: number; y: number; w: number; h: number }

/** Breathing room kept between a chip and any node box it dodges. */
const CLEARANCE = 6
/** Walk outward in small steps so the chip settles just clear of the box
 *  rather than at a fixed offset that would over-shoot short labels. */
const STEP = 6
/** Past this the layout is too dense for any placement to help; the chip stays
 *  at the midpoint on top, which is O66's behaviour and never worse than it. */
const MAX_OFFSET = 220

function hits(cx: number, cy: number, w: number, h: number, r: Rect): boolean {
  return (
    cx - w / 2 < r.x + r.w + CLEARANCE &&
    cx + w / 2 > r.x - CLEARANCE &&
    cy - h / 2 < r.y + r.h + CLEARANCE &&
    cy + h / 2 > r.y - CLEARANCE
  )
}

/** First point along the edge's perpendicular where the chip clears every node.
 *  Both directions are tried at each distance, so the chip takes the SHORTER
 *  detour and a chain of horizontal edges does not all pile up on one side. */
function placeClearOfNodes(
  labelX: number,
  labelY: number,
  chip: { w: number; h: number },
  nodes: readonly Rect[],
  dx: number,
  dy: number,
): { x: number; y: number } {
  const clear = (x: number, y: number) => !nodes.some((r) => hits(x, y, chip.w, chip.h, r))
  if (chip.w === 0 || clear(labelX, labelY)) return { x: labelX, y: labelY }
  const len = Math.hypot(dx, dy) || 1
  // perpendicular of the edge direction: vertical for the horizontal chain
  // layouts, which is where the collision actually happens
  const nx = -dy / len
  const ny = dx / len
  for (let d = STEP; d <= MAX_OFFSET; d += STEP) {
    for (const side of [1, -1]) {
      const x = labelX + nx * d * side
      const y = labelY + ny * d * side
      if (clear(x, y)) return { x, y }
    }
  }
  return { x: labelX, y: labelY }
}

export default function RelEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
  style,
}: EdgeProps<RelFlowEdge>) {
  // straight for chain layouts (ownership); bezier default matches the curve
  // the explorer/lineage canvases rendered before adopting this component
  const [path, labelX, labelY] =
    data?.path === 'straight'
      ? getStraightPath({ sourceX, sourceY, targetX, targetY })
      : getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition })

  // The node rects to dodge, read from the store rather than passed in: an edge
  // must clear EVERY node it happens to cross, not only its own endpoints (on
  // ownership the QUALIFIED_ATTRIBUTION chips cross a third box entirely).
  // nodeLookup is a stable Map that changes identity when nodes move or resize,
  // so this re-runs exactly when the geometry it depends on has changed.
  const nodeRects = useStore((s) => {
    const rects: Rect[] = []
    for (const node of s.nodeLookup.values()) {
      const w = node.measured?.width
      const h = node.measured?.height
      // Unmeasured on the first paint; the store updates once ReactFlow has
      // measured, which re-runs this selector with real numbers.
      if (!w || !h) continue
      const p = node.internals.positionAbsolute
      rects.push({ x: p.x, y: p.y, w, h })
    }
    return rects
  }, shallowRects)

  // Measured, not estimated: the chip is a themed HTML element whose width is
  // the label's own text metrics, and a character-count guess would be wrong in
  // exactly the dense layouts this code exists for.
  const chipRef = useRef<HTMLDivElement | null>(null)
  const [chip, setChip] = useState({ w: 0, h: 0 })
  useLayoutEffect(() => {
    const el = chipRef.current
    if (!el) return
    const w = el.offsetWidth
    const h = el.offsetHeight
    setChip((prev) => (prev.w === w && prev.h === h ? prev : { w, h }))
  }, [data?.rel])

  const at = placeClearOfNodes(labelX, labelY, chip, nodeRects, targetX - sourceX, targetY - sourceY)

  return (
    <>
      {/* The caller's `style` is MERGED, not ignored. This component used to
          hardcode the stroke and drop whatever the edge declared, which meant a
          caller could set `style` and watch nothing happen — found at O61, where
          a dashed "no confirmed relationship" edge rendered solid and therefore
          asserted exactly what it was drawn to deny. Colour and weight stay the
          defaults so the shared look holds unless a caller deliberately says
          otherwise. */}
      <BaseEdge
        path={path}
        markerEnd={markerEnd}
        style={{ stroke: 'var(--faint)', strokeWidth: 1.4, ...style }}
      />
      {/* O78: an UNNAMED edge draws no chip. The three canvases that adopted
          this component first always carry a name, so this never fired for
          them; MiniDag's edge label is optional, and rendering the chip
          unconditionally would have put an empty bordered box on every
          unlabelled edge across five routes. */}
      {data?.rel ? (
        <EdgeLabelRenderer>
          <div
            ref={chipRef}
            className="pointer-events-none absolute whitespace-nowrap rounded border border-edge bg-panel px-1.5 py-0.5 font-mono text-[10px] text-muted shadow-sm"
            style={{ transform: `translate(-50%, -50%) translate(${at.x}px,${at.y}px)`, zIndex: 10 }}
          >
            {data.rel}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  )
}

/** The selector builds a fresh array every run, so equality is by VALUE —
 *  without this every edge re-renders on every store tick. */
function shallowRects(a: readonly Rect[], b: readonly Rect[]): boolean {
  if (a.length !== b.length) return false
  return a.every((r, i) => r.x === b[i].x && r.y === b[i].y && r.w === b[i].w && r.h === b[i].h)
}

/** Pass as `edgeTypes` (module-level const, so ReactFlow never sees a new object per render). */
export const relEdgeTypes = { rel: RelEdge }
