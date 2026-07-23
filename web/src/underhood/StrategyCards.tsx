import { STRATEGIES } from './benchmarkData'

// The three retrieval strategies, structured-vs-unstructured framing (docs/
// design/graph-retrieval-benchmark-explainer.md §2): one card per strategy,
// same shape as the console's other card grids (hover-lift, token-colored
// accent bar) so the page reads as DryDocs chrome, not a one-off deck slide.
export default function StrategyCards() {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {STRATEGIES.map((s) => (
        <div
          key={s.id}
          className="hover-lift overflow-hidden rounded-lg border border-edge bg-panel"
          style={{ borderTopColor: `var(${s.token})`, borderTopWidth: 3 }}
        >
          <div className="p-3.5">
            <h3 className="text-sm font-semibold text-text">{s.label}</h3>
            <p className="mt-0.5 font-mono text-[10.5px] text-faint">{s.kicker}</p>
            <p className="mt-2.5 text-xs leading-relaxed text-muted">{s.how}</p>
            <dl className="mt-3 grid grid-cols-3 gap-2 border-t border-edge-soft pt-2.5 text-center">
              <div>
                <dt className="text-[9.5px] uppercase tracking-wide text-faint">Recall</dt>
                <dd className="font-mono text-xs font-semibold text-text">{s.recall}</dd>
              </div>
              <div>
                <dt className="text-[9.5px] uppercase tracking-wide text-faint">Tokens</dt>
                <dd className="font-mono text-xs font-semibold text-text">{s.tokens}</dd>
              </div>
              <div>
                <dt className="text-[9.5px] uppercase tracking-wide text-faint">Latency</dt>
                <dd className="font-mono text-xs font-semibold text-text">{s.latency}</dd>
              </div>
            </dl>
            <p className="mt-2.5 text-[11px] leading-relaxed text-faint">
              <span className="font-semibold" style={{ color: `var(${s.token})` }}>
                Failure modes —{' '}
              </span>
              {s.failureModes}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
