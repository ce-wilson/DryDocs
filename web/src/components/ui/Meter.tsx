// Threshold-colored progress meter — the runtime monitor's signature element
// (DL-4, internal/datalens-reference/continuity.md) reproduced generically:
// thin rounded track, fill green at/above the threshold, --status-fail below,
// right-aligned tabular percentage. Fill uses the STRONG token variants (the
// ≥3:1 graphics rule); the label stays --muted so text contrast never rides
// on the fill hue. No animation — nothing here needs motion.

export default function Meter({
  value,
  threshold = 100,
  label,
  className,
}: {
  value: number // 0–100
  threshold?: number // fill turns green at/above this (default: only 100 is green)
  label?: string // accessible name
  className?: string
}) {
  const v = Math.max(0, Math.min(100, value))
  const token = v >= threshold ? '--green' : '--status-fail'
  return (
    <span className={'inline-flex items-center gap-2 ' + (className ?? '')}>
      <span
        className="h-1.5 w-24 overflow-hidden rounded-full bg-edge-soft"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={v}
        aria-label={label ?? 'progress'}
      >
        <span
          className="block h-full rounded-full"
          style={{ width: `${v}%`, background: `var(${token})` }}
        />
      </span>
      <span className="font-mono text-[11px] tabular-nums text-muted">{Math.round(v)}%</span>
    </span>
  )
}
