import { useEffect, useMemo, useRef, useState } from 'react'
import type NVL from '@neo4j-nvl/base'
import type { Node as NvlNode, Relationship as NvlRelationship } from '@neo4j-nvl/base'
import { InteractiveNvlWrapper } from '@neo4j-nvl/react'

import type { CanvasGraph, CanvasNode } from '../lib/nvl-mapping'
import { GRAPH_KIND_TOKEN, NODE_CEILING } from '../lib/nvl-mapping'
import EmptyState from './ui/EmptyState'

// The NVL graph canvas (O81 step 3): pan / zoom / select over a graph the
// MAPPER built from QuerySpec rows. This component knows nothing about specs,
// Cypher or the API — it takes a CanvasGraph and draws it, which is what keeps
// the ADR 0005 read boundary a property of the data path rather than a promise
// this file has to keep.
//
// TOKENS RESOLVED AT RENDER, because NVL takes concrete colours. The console's
// rule is that components consume theme tokens and never raw hex (site-plan §2),
// and NVL cannot read a CSS custom property — so the token is resolved against
// the live computed style and re-resolved when the theme changes. Hard-coding
// the hex here would have made the canvas the one surface that does not follow
// the theme, which is exactly the class of defect TC-SHELL-04 exists for.
//
// TRUNCATION IS SAID OUT LOUD. A capped render announces that it is capped: the
// absent-is-never-empty discipline the loaders and the location map already
// follow applies to pixels too. A canvas quietly showing 300 of 900 nodes makes
// a claim about the graph that is simply false.

/** Read a theme token's current value. Returns '' when it cannot be resolved,
 *  which the caller treats as "let NVL pick", never as a colour. */
function resolveToken(token: string): string {
  if (typeof window === 'undefined') return ''
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim()
}

/** Re-resolve whenever the theme class flips on <html> (lib/theme.ts stamps it). */
function useThemeEpoch(): number {
  const [epoch, setEpoch] = useState(0)
  useEffect(() => {
    const root = document.documentElement
    const observer = new MutationObserver(() => setEpoch((n) => n + 1))
    observer.observe(root, { attributes: true, attributeFilter: ['class'] })
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onMedia = () => setEpoch((n) => n + 1)
    media.addEventListener('change', onMedia)
    return () => {
      observer.disconnect()
      media.removeEventListener('change', onMedia)
    }
  }, [])
  return epoch
}

export interface GraphCanvasProps {
  graph: CanvasGraph
  /** Node id, or null. Owned by the route so the canvas and its data frames
   *  share ONE selection — the same contract the demo panes already keep. */
  selectedId: string | null
  onSelect: (node: CanvasNode | null) => void
  title: string
  /** Provenance/trust line rendered beside the title, as the other panes do. */
  badge?: string
}

export default function GraphCanvas({
  graph,
  selectedId,
  onSelect,
  title,
  badge,
}: GraphCanvasProps) {
  const epoch = useThemeEpoch()
  const byId = useRef(new Map<string, CanvasNode>())
  const nvl = useRef<NVL | null>(null)

  const { nodes, rels } = useMemo(() => {
    void epoch // re-resolve tokens on theme change
    const edgeColor = resolveToken('--edge') || undefined
    byId.current = new Map(graph.nodes.map((n) => [n.id, n]))
    const nvlNodes: NvlNode[] = graph.nodes.map((n) => {
      const color = resolveToken(GRAPH_KIND_TOKEN[n.kind])
      return {
        id: n.id,
        caption: n.caption,
        // Large enough for the caption to be legible once the view is fitted;
        // NVL's default leaves the label unreadable at any useful zoom.
        size: 26,
        ...(color ? { color } : {}),
        selected: n.id === selectedId,
      }
    })
    const nvlRels: NvlRelationship[] = graph.relationships.map((r) => ({
      id: r.id,
      from: r.from,
      to: r.to,
      caption: r.caption,
      ...(edgeColor ? { color: edgeColor } : {}),
    }))
    return { nodes: nvlNodes, rels: nvlRels }
  }, [graph, selectedId, epoch])

  // FIT AFTER LAYOUT, or the viewport shows whatever happens to be under it.
  // The force layout starts every node near the origin and pushes them outward
  // over several frames, so a fit on the same tick frames a graph that has not
  // spread yet — the first render showed ONE node of nine, with the header
  // truthfully reporting nine. The delay is why this is a timer rather than an
  // effect body: it waits for the layout to settle, then frames every node.
  useEffect(() => {
    if (graph.nodes.length === 0) return
    const ids = graph.nodes.map((n) => n.id)
    const timer = setTimeout(() => nvl.current?.fit(ids), 600)
    return () => clearTimeout(timer)
  }, [graph])

  // ZERO ROWS IS AN HONEST STATE, not a failure — the series spec returns none
  // until the curated lineage load runs, and the empty state says which spec
  // came back empty rather than showing a blank rectangle.
  if (graph.nodes.length === 0) {
    return (
      <div className="flex h-full flex-col">
        <CanvasHeader title={title} badge={badge} graph={graph} />
        <EmptyState
          title="No graph to draw"
          hint={
            graph.rowCount === 0
              ? 'The spec returned zero rows. That is the honest state until the load behind it runs — it is not an error and not an empty graph.'
              : 'The spec returned rows, but none of them described a node this view can draw.'
          }
        />
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <CanvasHeader title={title} badge={badge} graph={graph} />
      {/* Fills the frame it is given rather than forcing a height: a fixed
          minimum overflowed the data-frame strip and pushed the graph below the
          fold. The strip is about 215px, which fits the graph but renders its
          captions small — the shell's resizable divider is the way to more room,
          and the canvas re-fits whenever its graph changes. */}
      <div className="relative min-h-0 flex-1">
        <InteractiveNvlWrapper
          ref={nvl}
          nodes={nodes}
          rels={rels}
          // THE CANVAS RENDERER IS A CORRECTNESS CHOICE, not a performance one,
          // and NVL's own docs are explicit: the default WebGL renderer "does
          // not support captions and arrowheads". Every node and relationship
          // here carries a caption — the relationship name is half the point of
          // drawing the edge at all (the same concern O66 raised) — so WebGL
          // would have silently rendered an unlabelled blob graph. It also
          // cannot initialise in headless Chromium, which is how this surfaced:
          // the screenshot run closed the browser outright.
          // d3Force, NOT 'forceDirected' — and this was measured, not preferred.
          // With 'forceDirected' all nine nodes of the fixture graph rendered
          // stacked at the origin: the header truthfully said nine, the canvas
          // showed one circle, and nothing errored. d3Force spreads them and the
          // edges draw. A layout that silently collapses the graph is worse than
          // a slower one, so the working layout is the default here.
          nvlOptions={{ layout: 'd3Force', initialZoom: 1, renderer: 'canvas' }}
          mouseEventCallbacks={{
            onZoom: true,
            onPan: true,
            onDrag: true,
            onNodeClick: (node: NvlNode) => onSelect(byId.current.get(node.id) ?? null),
            onCanvasClick: () => onSelect(null),
          }}
          className="h-full w-full"
        />
      </div>
    </div>
  )
}

function CanvasHeader({
  title,
  badge,
  graph,
}: {
  title: string
  badge?: string
  graph: CanvasGraph
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-edge px-3 py-2">
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      {badge && (
        <span className="rounded-xs border border-edge px-1.5 py-0.5 font-mono text-[10px] text-muted">
          {badge}
        </span>
      )}
      <span className="ml-auto font-mono text-[10px] text-faint">
        {graph.nodes.length} nodes · {graph.relationships.length} rels · {graph.rowCount} rows
      </span>
      {graph.truncated && (
        // The capped render says so, with both numbers, so the reader knows
        // exactly how much of the answer is on screen.
        <span
          className="rounded-xs border border-yellow px-1.5 py-0.5 font-mono text-[10px] text-yellow"
          title={`Capped at ${NODE_CEILING} nodes; the rows described ${graph.nodeCount}.`}
        >
          TRUNCATED {graph.nodes.length}/{graph.nodeCount}
        </span>
      )}
    </div>
  )
}
