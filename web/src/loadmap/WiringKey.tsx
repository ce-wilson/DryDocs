import { WIRING_STATES, wiringCensus, type LoadMapSource } from './loadMapModel'

// O90 — the legend for the wiring key.
//
// Every cell carries a TEXT label, never colour alone: this page has a print
// surface (docs/plan/load-map.html, N5) and a captured-DOM one is planned (O88),
// so a key that reads only in colour is a key that stops working on paper.
//
// The legend states the two QUESTIONS being crossed rather than leaving the
// reader to infer them from four adjectives.

export default function WiringKey({ sources }: { sources: readonly LoadMapSource[] }) {
  const census = wiringCensus(sources)
  return (
    <div className="shrink-0 rounded-md border border-edge bg-bg-2 px-3 py-2.5">
      <p className="mb-2 text-[11px] text-muted">
        <span className="font-semibold text-text">Wiring key</span> — the cross of two things the registry records
        separately: <i>has a gate ruled this source&rsquo;s meaning</i>, and <i>is a loader built that writes it</i>.
        Four states, because the two middle ones are neither wired nor planned.
      </p>
      <ul className="flex flex-wrap gap-x-4 gap-y-1.5">
        {WIRING_STATES.map((s) => (
          <li key={s.id} className="flex items-baseline gap-1.5 text-[10.5px]">
            <span
              className="inline-flex items-center rounded-full border px-1.5 py-px font-mono font-semibold"
              style={{
                borderColor: `var(${s.token})`,
                color: `var(${s.token})`,
                background: `color-mix(in srgb, var(${s.token}) 10%, transparent)`,
              }}
            >
              {census[s.id]} {s.label}
            </span>
            <span className="text-faint">{s.meaning}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
