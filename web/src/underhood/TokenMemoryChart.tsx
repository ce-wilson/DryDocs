import { QUESTIONS, TOTALS, type StrategyId } from './benchmarkData'

// Hand-rolled SVG area/line chart (no chart library, per the console's
// existing idiom — GraphSvg/GraphExplorer draw their own SVG too): cumulative
// characters riding along in a continuous 12-question incident conversation,
// one line per strategy, log-scaled y-axis because the gap (16.4k vs 449.5k)
// would flatten two of the three lines on a linear axis.
//
// The per-question `chars` in benchmarkData.ts are verbatim quotes from the
// verdict tables. Summed in question order they land close to — but not
// exactly on — the verdict's own headline "Total context ingested" row
// (manifest's two partial/rule-only answers are recorded as 0 chars, but the
// real reads that produced "the rule" were not free; the verdict's total
// folds in overhead the per-question table doesn't itemize). Rather than
// invent per-question numbers to close that gap, each series here is scaled
// by one constant factor (rawSum → documented total) so the per-question
// SHAPE stays exactly proportional to the quoted numbers while the series
// lands on the one number the task explicitly calls the source of truth.

const ORDER: readonly StrategyId[] = ['manifest', 'fulltext', 'traversal']
const COLOR: Record<StrategyId, string> = { manifest: '--yellow', fulltext: '--blue-br', traversal: '--green' }
const LABEL: Record<StrategyId, string> = { manifest: 'Manifest', fulltext: 'Full-text', traversal: 'Traversal' }

function cumulative(values: readonly number[]): number[] {
  const out: number[] = []
  let running = 0
  for (const v of values) {
    running += v
    out.push(running)
  }
  return out
}

const W = 760
const H = 320
const PAD_L = 46
const PAD_R = 16
const PAD_T = 16
const PAD_B = 38
const PLOT_W = W - PAD_L - PAD_R
const PLOT_H = H - PAD_T - PAD_B

const LOG_MIN = 0 // 10^0 = 1
const LOG_MAX = Math.log10(500_000)

function yFor(chars: number): number {
  const v = Math.max(1, chars)
  const t = (Math.log10(v) - LOG_MIN) / (LOG_MAX - LOG_MIN)
  return PAD_T + (1 - t) * PLOT_H
}

function xFor(i: number): number {
  return PAD_L + (i / (QUESTIONS.length - 1)) * PLOT_W
}

const GRIDLINES = [1, 10, 100, 1_000, 10_000, 100_000] as const
const GRID_LABELS: Record<number, string> = { 1: '1', 10: '10', 100: '100', 1000: '1k', 10000: '10k', 100000: '100k' }

export default function TokenMemoryChart() {
  const series = ORDER.map((id) => {
    const raw = cumulative(QUESTIONS.map((q) => q[id].chars))
    const rawFinal = raw[raw.length - 1] || 1
    const target = TOTALS[id].chars
    const scale = target / rawFinal
    const scaled = raw.map((v) => v * scale)
    return { id, scaled, final: target }
  })

  return (
    <div className="rounded-lg border border-edge bg-panel p-4">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-sm font-semibold text-text">Token-memory tracker</h3>
        <span className="ml-auto flex flex-wrap gap-3">
          {series.map((s) => (
            <span key={s.id} className="flex items-center gap-1.5 font-mono text-[10.5px] text-muted">
              <span className="h-2 w-2 rounded-full" style={{ background: `var(${COLOR[s.id]})` }} aria-hidden="true" />
              {LABEL[s.id]} · {TOTALS[s.id].chars.toLocaleString()}ch ({TOTALS[s.id].tokens} tok)
            </span>
          ))}
        </span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 w-full" role="img" aria-label="Cumulative characters retrieved across the 12-question benchmark conversation, per strategy, log scale">
        {/* gridlines + y labels (log scale) */}
        {GRIDLINES.map((g) => {
          const y = yFor(g)
          return (
            <g key={g}>
              <line x1={PAD_L} y1={y} x2={W - PAD_R} y2={y} stroke="var(--edge-soft)" strokeWidth="1" />
              <text x={PAD_L - 6} y={y + 3} textAnchor="end" fill="var(--faint)" fontSize="9" fontFamily="var(--mono)">
                {GRID_LABELS[g]}
              </text>
            </g>
          )
        })}

        {/* x-axis question ticks */}
        {QUESTIONS.map((q, i) => (
          <text
            key={q.id}
            x={xFor(i)}
            y={H - PAD_B + 14}
            textAnchor="middle"
            fill="var(--faint)"
            fontSize="8.5"
            fontFamily="var(--mono)"
          >
            {q.id}
          </text>
        ))}

        {/* series: manifest first (largest, drawn behind), traversal last (smallest, drawn on top) */}
        {series.map((s) => {
          const points = s.scaled.map((v, i) => `${xFor(i)},${yFor(v)}`).join(' ')
          const areaPoints = `${PAD_L},${PAD_T + PLOT_H} ${points} ${W - PAD_R},${PAD_T + PLOT_H}`
          return (
            <g key={s.id}>
              <polygon points={areaPoints} fill={`var(${COLOR[s.id]})`} opacity="0.08" />
              <polyline points={points} fill="none" stroke={`var(${COLOR[s.id]})`} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
              {s.scaled.map((v, i) => (
                <circle key={i} cx={xFor(i)} cy={yFor(v)} r="2.4" fill={`var(${COLOR[s.id]})`} />
              ))}
            </g>
          )
        })}
      </svg>

      <p className="mt-1 text-[11px] leading-relaxed text-faint">
        What rides along in the agent&rsquo;s context window in a continuous incident conversation —{' '}
        <span className="font-mono">{TOTALS.manifest.tokens} tok</span> of documentation vs{' '}
        <span className="font-mono">{TOTALS.traversal.tokens} tok</span>. Y-axis is log-scaled (characters); per-question
        step sizes are the benchmark&rsquo;s quoted chars, scaled per series to land on the verdict&rsquo;s documented totals.
      </p>
    </div>
  )
}
