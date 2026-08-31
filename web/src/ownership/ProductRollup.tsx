import { useState } from 'react'

import MiniDag from '../components/MiniDag'
import {
  LEAF_ANNOTATIONS,
  ROLLUP_EDGES,
  ROLLUP_NODES,
} from './demoProductRollup'

// The product roll-up view (O61): which area a job or folder supports.
//
// SHAPE CHOICE, recorded because the item asked for it: MiniDag, not mermaid.
// Three reasons, in order of weight. (1) /ownership already renders React Flow
// in its graph pane, so a mermaid block would put two graph idioms on one
// module. (2) MiniDag's hand-authored positions are usually its limitation
// (Idea-228) and here they are an ASSET — this is a fixed taxonomy diagram with
// two deliberate columns, so a layout engine would only fight the meaning the
// columns carry. (3) The dashed-edge affordance the honest rendering needs was
// a six-line addition to a component five routes already share, rather than a
// new renderer.
//
// TWO COLUMNS BECAUSE THERE ARE TWO JOIN RULES. A framework application carries
// no SEAL and reaches its AreaProduct by NAMING the token; an app-tied
// application carries a SEAL and joins through the Control-M sub-application.
// One column would imply one rule, and a support engineer tracing ownership
// needs to know which thread they are pulling.
//
// THE DASHED EDGE IS THE POINT OF THE CAPTION. "aligns to platform" is real in
// the estate and has no confirmed graph relationship behind it. Solid would
// assert an edge nobody ruled; omitting it would hide something true. Dashed,
// labelled and captioned commits nothing and skips no gate — and the view says
// so in words rather than leaving the dash to be interpreted.

export default function ProductRollup() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const annotation = LEAF_ANNOTATIONS.find((a) => a.nodeId === selectedId)

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        SYNTHESIZED · ILLUSTRATIVE — the SHAPE of the roll-up, with invented names. The SME's
        rendered example carries real org taxonomy and is machine-local, never committed.
      </p>

      <div className="flex shrink-0 flex-wrap items-center gap-3 rounded border border-edge bg-panel-2 px-2.5 py-1.5 text-[11px]">
        <span className="text-muted">
          <span className="font-semibold text-text">Framework</span> — no SEAL; the AreaProduct
          token is the join
        </span>
        <span className="text-muted">
          <span className="font-semibold text-text">App-tied</span> — carries SEAL; the Control-M
          sub-application is the join
        </span>
        <span className="ml-auto flex items-center gap-1.5 text-muted">
          <svg width="34" height="8" aria-hidden="true">
            <line
              x1="0"
              y1="4"
              x2="34"
              y2="4"
              stroke="var(--faint)"
              strokeWidth="1.5"
              strokeDasharray="5 4"
            />
          </svg>
          no confirmed graph relationship
        </span>
      </div>

      <div className="min-h-0 flex-1">
        <MiniDag
          nodes={ROLLUP_NODES}
          edges={ROLLUP_EDGES}
          title="AreaProduct → Product → ProductLine → LOB, by application kind"
          badge="EXAMPLE DATA · ILLUSTRATIVE"
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </div>

      {/* The leaf annotation: folder-name grammar, with classification beneath
          it. Shown on selection rather than always, because two of these at
          once is what made the SME's original example hard to read. */}
      {annotation ? (
        <div className="shrink-0 rounded-md border border-edge px-2.5 py-2 text-[11px]">
          <p className="font-mono font-semibold text-text">{selectedId}</p>
          <dl className="mt-1 grid grid-cols-[max-content_1fr] gap-x-3 gap-y-0.5">
            <dt className="text-muted">grammar</dt>
            <dd className="font-mono text-[10px] text-text">{annotation.grammar}</dd>
            <dt className="text-muted">join</dt>
            <dd className="text-[10px] text-text">{annotation.join}</dd>
            <dt className="text-muted">classification</dt>
            <dd className="font-mono text-[10px] text-text">{annotation.classification}</dd>
          </dl>
        </div>
      ) : (
        <p className="shrink-0 rounded-md border border-edge px-2.5 py-1.5 text-[10px] text-muted">
          Select a folder node for its name grammar and classification. The dashed{' '}
          <span className="font-mono">aligns to platform</span> edge is drawn because the
          alignment is real in the estate — but NO confirmed graph relationship backs it, so it
          is not asserted as one. Rendering it commits nothing and skips no gate; if it is ever
          ruled, it becomes a solid edge through the relationship-vocabulary registry and the
          HITL gate, not through this view.
        </p>
      )}
    </div>
  )
}
