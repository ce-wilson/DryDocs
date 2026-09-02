import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import {
  isLaneBasis,
  LANE_BASES,
  resolveLanes,
  type LaneBasisId,
  type LaneItem,
} from './laneBasis'
import { EDGE_BACKING, SWIMLANE_EDGES, SWIMLANE_ITEMS } from './demoSwimlane'

// The /lineage swimlane (O60). Filename recorded at build: SwimlaneView.tsx, as
// the item proposed.
//
// THE LAYOUT NEVER BRANCHES ON THE BASIS. It asks resolveLanes() for lanes and
// items and renders whatever comes back, so a third basis is a new resolver case
// and not a re-layout here. That separation is the item's amendment, and it is
// the difference between "a second basis" and "a second view".
//
// DEEP LINK: ?lanes=source-kind | ?lanes=layer — parameter name recorded at
// build, matching the existing ?domain= idiom. An unrecognised value falls back
// to the default basis rather than rendering nothing, because a bad link should
// still show the page.
//
// WHAT THIS SURFACE SAYS OUT LOUD, rather than only in code:
//   * which AXIS a lane basis means (three different things in this repo are
//     called a layer, and merging them silently would be the defect);
//   * that a layer lane groups by CARRIER, not subject, while `layer` is a
//     system field;
//   * that an empty declared lane is a FINDING, not a rendering gap;
//   * what backs the READS/WRITES edges, with the vocabulary entry ids quoted.

const DEFAULT_BASIS: LaneBasisId = 'source-kind'

export default function SwimlaneView() {
  const [params, setParams] = useSearchParams()
  const raw = params.get('lanes')
  const basisId: LaneBasisId = isLaneBasis(raw) ? raw : DEFAULT_BASIS

  const basis = useMemo(() => resolveLanes(basisId, SWIMLANE_ITEMS), [basisId])

  const byLane = useMemo(() => {
    const map = new Map<string, LaneItem[]>()
    for (const lane of basis.lanes) map.set(lane.id, [])
    for (const item of basis.items) {
      const bucket = map.get(item.lane)
      if (bucket) bucket.push(item)
    }
    return map
  }, [basis])

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        {/* WF-DFL-17 — the mode tag the wireframe reserves. */}
        EXAMPLE DATA · ILLUSTRATIVE (WF-DFL-17) — synthesized series; the BDAT basis renders
        REAL registry entities from the generated load-map.
      </p>

      <div className="flex shrink-0 flex-wrap items-center gap-2 rounded border border-edge bg-panel-2 px-2.5 py-1.5 text-[11px]">
        {/* WF-DFL-01 — the toolbar row the wireframe reserves for the picker. */}
        <span className="text-muted">Lane basis</span>
        <span className="font-mono text-[10px] text-faint">WF-DFL-01</span>
        {LANE_BASES.map((b) => (
          <button
            key={b.id}
            type="button"
            onClick={() => {
              const next = new URLSearchParams(params)
              next.set('lanes', b.id)
              setParams(next, { replace: false })
            }}
            className={
              'rounded px-2 py-0.5 font-mono text-[11px] ' +
              (b.id === basisId
                ? 'border border-[var(--blue-br)] text-text'
                : 'border border-edge text-muted hover:text-text')
            }
          >
            {b.label}
          </button>
        ))}
        <span className="ml-auto font-mono text-[10px] text-faint">?lanes={basisId}</span>
      </div>

      {/* The axis, always. Three different things here are called a layer. */}
      <p className="shrink-0 rounded border border-edge px-2.5 py-1 text-[10px] leading-snug text-muted">
        {basis.axisNote}
      </p>

      <div className="min-h-0 flex-1 overflow-auto">
        <div className="flex min-h-full gap-1.5">
          {basis.lanes.map((lane) => {
            const items = byLane.get(lane.id) ?? []
            return (
              <section
                key={lane.id}
                className="flex min-w-[210px] flex-1 flex-col rounded-md border border-edge"
              >
                <p className="border-b border-edge bg-panel-2 px-2.5 py-1.5 font-mono text-[11px] font-semibold text-muted">
                  {lane.label}
                  <span className="ml-2 tabular-nums font-normal">{items.length}</span>
                  {lane.wf && <span className="ml-2 font-normal text-faint">{lane.wf}</span>}
                </p>
                <div className="flex flex-1 flex-col gap-1.5 p-2">
                  {items.map((item) => (
                    <div key={item.id} className="rounded border border-edge bg-panel px-2 py-1.5">
                      <p className="font-mono text-[11px] text-text">{item.label}</p>
                      <p className="text-[10px] text-muted">{item.sub}</p>
                      {item.wf && (
                        // The wireframe key, so SME feedback re-attaches to a
                        // component that exists.
                        <p className="mt-0.5 font-mono text-[10px] text-faint">{item.wf}</p>
                      )}
                    </div>
                  ))}
                  {items.length === 0 && (
                    // An empty DECLARED lane is the finding. Never hidden.
                    <p className="rounded border border-yellow/40 bg-yellow/5 px-2 py-1.5 text-[10px] leading-snug text-yellow">
                      {lane.emptyNote ?? 'declared, and empty'}
                    </p>
                  )}
                </div>
              </section>
            )
          })}
        </div>
      </div>

      {basis.caveat && (
        <p className="shrink-0 rounded border border-yellow/40 bg-yellow/5 px-2.5 py-1 text-[10px] leading-snug text-yellow">
          {basis.caveat}
        </p>
      )}

      {basisId === 'source-kind' && (
        <div className="shrink-0 rounded-md border border-edge px-2.5 py-1.5 text-[10px] leading-snug text-muted">
          <p className="font-mono text-[10px] text-text">
            edges: {SWIMLANE_EDGES.map((e) => `${e.label} (${e.wf})`).join(' · ')}
          </p>
          <p className="mt-1">
            READS_FROM and WRITES_TO render SOLID, and the wireframe's own WF-DFL-14/15 labels
            reading &ldquo;(planned)&rdquo; are STALE. Both are backed by ACTIVE relationship
            vocabulary entries —{' '}
            {EDGE_BACKING.map((b) => `${b.entry} (${b.status})`).join(', ')} — which superseded the
            deprecated m3_reads_from / m3_writes_to. Drawing them dashed would understate a
            confirmed ruling; the item made its instruction conditional on the vocabulary, so the
            data decided.
          </p>
        </div>
      )}
    </div>
  )
}
