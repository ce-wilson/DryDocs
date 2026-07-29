// Small reusable "at-a-glance" stat tile row — bordered tiles, big mono
// number + 11px uppercase label. First user: UnderTheHoodRoute's benchmark
// headline stats; generic enough for any module summary row.
//
// O40 (DL-10, the runtime monitor's KPI-card→filter idiom): tiles are
// OPTIONALLY interactive. Pass onSelect (+ give tiles ids) and each tile
// becomes a keyboard-operable filter control (button, aria-pressed) whose
// active state scopes the content below; selecting the active tile again
// clears the filter. Without onSelect the row renders exactly as before —
// static tiles, zero behavior change for existing callers.
export interface StatTile {
  value: string
  label: string
  /** required only when the row is interactive (onSelect present) */
  id?: string
}

export default function StatTiles({
  tiles,
  selectedId,
  onSelect,
}: {
  tiles: readonly StatTile[]
  selectedId?: string | null
  onSelect?: (id: string | null) => void
}) {
  const body = (t: StatTile) => (
    <>
      <div className="font-mono text-xl font-bold tabular-nums text-text sm:text-2xl">{t.value}</div>
      <div className="mt-1 text-[11px] uppercase tracking-wide text-faint">{t.label}</div>
    </>
  )
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {tiles.map((t, i) =>
        onSelect && t.id ? (
          <button
            key={t.id}
            type="button"
            aria-pressed={selectedId === t.id}
            onClick={() => onSelect(selectedId === t.id ? null : t.id!)}
            className={
              'hover-lift rounded-lg border bg-panel px-3 py-3 text-center transition-colors ' +
              (selectedId === t.id ? 'border-blue-bright bg-panel-2' : 'border-edge hover:border-faint')
            }
          >
            {body(t)}
          </button>
        ) : (
          <div key={t.id ?? i} className="hover-lift rounded-lg border border-edge bg-panel px-3 py-3 text-center">
            {body(t)}
          </div>
        ),
      )}
    </div>
  )
}
