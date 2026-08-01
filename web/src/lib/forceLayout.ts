import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force'

// The shared d3-force placement engine (extracted from GraphExplorer at R6).
//
// Two panes now lay out node/edge scenes — the live job dependency graph and
// the Ask spoke's Tier-2 task graph — and they need the SAME engine, not the
// same LOOK: a task graph is not a job graph and should not be dressed as one.
// So this module owns placement only (the d3 dependency, the tick count, the
// rescale) and each pane keeps its own visual language.
//
// Deterministic by design: d3-force's default random source is a fixed-seed
// LCG and the simulation runs to convergence synchronously with no animation,
// so positions are stable and the views stay screenshot- and CDP-assertable.

/** The edge record every caller passes. Shaped to match what the agent
 *  envelope's task-graph snapshots emit verbatim, so no adapter is needed. */
export interface LayoutEdge {
  source: string
  target: string
  via?: string
}

export interface PlacedNode {
  id: string
  x: number
  y: number
}

export interface LayoutOptions {
  width: number
  height: number
  /** node radius — drives collision spacing and the edge-endpoint trim */
  radius: number
  pad: number
  linkDistance?: number
  charge?: number
}

interface LayoutNode extends SimulationNodeDatum {
  id: string
}

/**
 * Place every node named by `edges` (plus any `extraIds` with no edges yet)
 * inside the given box.
 *
 * `extraIds` matters for the task graph specifically: its first snapshot is a
 * single question node with NO edges, and a layout that only knows about edge
 * endpoints would render that opening frame empty.
 */
export function forceLayout(
  edges: readonly LayoutEdge[],
  opts: LayoutOptions,
  extraIds: readonly string[] = [],
): PlacedNode[] {
  const { width: W, height: H, radius: R, pad: PAD } = opts
  const ids = [...new Set([...edges.flatMap((e) => [e.source, e.target]), ...extraIds])]
  if (ids.length === 0) return []

  const nodes: LayoutNode[] = ids.map((id) => ({ id }))
  const links: SimulationLinkDatum<LayoutNode>[] = edges.map((e) => ({
    source: e.source,
    target: e.target,
  }))
  const sim = forceSimulation(nodes)
    .force(
      'link',
      forceLink<LayoutNode, SimulationLinkDatum<LayoutNode>>(links)
        .id((d) => d.id)
        .distance(opts.linkDistance ?? 110),
    )
    .force('charge', forceManyBody().strength(opts.charge ?? -380))
    .force('center', forceCenter(W / 2, H / 2))
    .force('collide', forceCollide(R + 14))
    // Weak pull to center keeps DISCONNECTED chains from repelling each other
    // to the bbox extremes (which would crush each cluster in the rescale).
    .force('x', forceX(W / 2).strength(0.08))
    .force('y', forceY(H / 2).strength(0.1))
    .stop()
  sim.tick(300)

  const xs = nodes.map((n) => n.x ?? 0)
  const ys = nodes.map((n) => n.y ?? 0)
  const [minX, maxX] = [Math.min(...xs), Math.max(...xs)]
  const [minY, maxY] = [Math.min(...ys), Math.max(...ys)]
  const sx = (W - 2 * PAD) / Math.max(1, maxX - minX)
  const sy = (H - 2 * PAD) / Math.max(1, maxY - minY)
  const s = Math.min(sx, sy, 1.4)
  return nodes.map((n) => ({
    id: n.id,
    x: PAD + ((n.x ?? 0) - minX) * s + (W - 2 * PAD - (maxX - minX) * s) / 2,
    y: PAD + ((n.y ?? 0) - minY) * s + (H - 2 * PAD - (maxY - minY) * s) / 2,
  }))
}

/** Trim an edge to the node circles at both ends, so arrowheads land on the
 *  rim rather than under the target. Shared because getting it wrong looks
 *  like a rendering bug in whichever pane forgets it. */
export function trimEdge(
  a: PlacedNode,
  b: PlacedNode,
  radius: number,
  headroom = 4,
): { x1: number; y1: number; x2: number; y2: number } {
  const dx = b.x - a.x
  const dy = b.y - a.y
  const len = Math.hypot(dx, dy) || 1
  return {
    x1: a.x + (dx / len) * radius,
    y1: a.y + (dy / len) * radius,
    x2: b.x - (dx / len) * (radius + headroom),
    y2: b.y - (dy / len) * (radius + headroom),
  }
}
