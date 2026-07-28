import type { ResultKind } from './benchmarkData'

// Shared per-strategy result glyph — the scoreboard, the question detail
// panel, and the hallucination spotlight all render the same five outcomes
// the same way, so the meaning of "pass"/"fail"/etc. never drifts between
// panels on this one page.
const META: Record<ResultKind, { glyph: string; label: string; token: string }> = {
  // fail/hallucination use --status-fail-soft, not --red: red = brand only (DL-2),
  // and the soft variant is the text-safe one in both themes (tokens.css).
  pass: { glyph: '✔', label: 'pass', token: '--green' },
  fail: { glyph: '✗', label: 'fail', token: '--status-fail-soft' },
  partial: { glyph: '~', label: 'partial', token: '--yellow' },
  abstain: { glyph: 'Ⓐ', label: 'abstain', token: '--teal' },
  hallucination: { glyph: '⚠', label: 'hallucination', token: '--status-fail-soft' },
}

export default function ResultChip({ kind, compact }: { kind: ResultKind; compact?: boolean }) {
  const m = META[kind]
  return (
    <span
      className={
        'inline-flex items-center gap-1 rounded border px-1.5 py-0.5 font-mono font-semibold ' +
        (compact ? 'text-[11px]' : 'text-xs')
      }
      style={{ borderColor: `var(${m.token})`, color: `var(${m.token})`, background: `color-mix(in srgb, var(${m.token}) 10%, transparent)` }}
      title={m.label}
    >
      <span aria-hidden="true">{m.glyph}</span>
      {!compact && <span className="capitalize">{m.label}</span>}
    </span>
  )
}
