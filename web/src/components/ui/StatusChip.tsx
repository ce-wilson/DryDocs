// Token-tinted count+label pill — the runtime monitor's "15 Completed /
// 2 Not Completed" summary-chip pattern reproduced generically in the DryDocs
// idiom (DL-3, internal/datalens-reference/continuity.md): theme tokens only
// (no hex), glyph characters in the ResultChip tradition (no emoji), pill
// radius on chips only (DL-5 keeps cards/panels at the house radius).
// Use *text-safe* tokens (--green / --yellow / --teal / --status-fail-soft /
// --blue-br) — the chip paints text with the same token as its border.

export default function StatusChip({
  count,
  label,
  token,
  glyph,
  title,
}: {
  count: number
  label: string
  token: '--green' | '--yellow' | '--teal' | '--blue-br' | '--status-fail-soft' | '--muted'
  glyph?: string
  title?: string
}) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[11px] font-semibold tabular-nums"
      style={{
        borderColor: `var(${token})`,
        color: `var(${token})`,
        background: `color-mix(in srgb, var(${token}) 10%, transparent)`,
      }}
      title={title ?? `${count} ${label}`}
    >
      {glyph && <span aria-hidden="true">{glyph}</span>}
      <span>{count}</span>
      <span className="font-sans font-medium">{label}</span>
    </span>
  )
}
