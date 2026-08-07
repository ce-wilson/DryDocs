import { Panel } from '@xyflow/react'

// O29: the trust-tier / edge-provenance legend, live ON the graph canvases —
// the adopt of context-graph's declared/observed legend pattern
// (internal/context-graph-analysis/ui-architecture-analysis.md: "surface that
// in the live UI too, not only in the export manifest"). The tier palette
// REUSES the tokens the /under-the-hood corpus census already binds
// (underhood/benchmarkData.ts) — no new colors, and everything routes through
// theme CSS variables so both schemes render correctly.

export const TRUST_TIER_TOKEN = {
  VERBATIM: '--green',
  GROUNDED: '--blue-br',
  SYNTHESIZED: '--yellow',
} as const

type TrustTier = keyof typeof TRUST_TIER_TOKEN

const TIER_HINT: Record<TrustTier, string> = {
  VERBATIM: 'source of record',
  GROUNDED: 'derived / joined',
  SYNTHESIZED: 'inferred / demo',
}

const TIERS = Object.keys(TRUST_TIER_TOKEN) as TrustTier[]

/** Render inside a ReactFlow canvas (both graph panes wrap one). */
export default function TrustLegend() {
  // !ml-12 clears the ReactFlow zoom controls, which share bottom-left
  return (
    <Panel position="bottom-left" className="!m-2 !ml-12">
      <div className="rounded-md border border-edge-soft bg-panel/90 px-2.5 py-1.5 shadow-sm backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-faint">Trust tier</span>
          {TIERS.map((tier) => (
            <span key={tier} className="flex items-center gap-1">
              <span
                className="inline-block h-2 w-2 rounded-sm"
                style={{ background: `var(${TRUST_TIER_TOKEN[tier]})` }}
              />
              <span className="font-mono text-[10px] text-text">{tier}</span>
              <span className="text-[9px] text-muted">{TIER_HINT[tier]}</span>
            </span>
          ))}
        </div>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5">
          <span className="font-mono text-[9px] uppercase tracking-wider text-faint">Edge provenance</span>
          <span className="flex items-center gap-1">
            <svg width="18" height="6" aria-hidden="true">
              <line x1="0" y1="3" x2="18" y2="3" stroke="var(--faint)" strokeWidth="1.6" />
            </svg>
            <span className="text-[10px] text-muted">declared</span>
          </span>
          <span className="flex items-center gap-1">
            <svg width="18" height="6" aria-hidden="true">
              <line x1="0" y1="3" x2="18" y2="3" stroke="var(--faint)" strokeWidth="1.6" strokeDasharray="3 3" />
            </svg>
            <span className="text-[10px] text-muted">observed</span>
          </span>
        </div>
      </div>
    </Panel>
  )
}
