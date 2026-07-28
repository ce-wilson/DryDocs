// Small reusable "at-a-glance" stat tile row — bordered tiles, big mono
// number + 11px uppercase label. First user: UnderTheHoodRoute's benchmark
// headline stats; generic enough for any module summary row.
export interface StatTile {
  value: string
  label: string
}

export default function StatTiles({ tiles }: { tiles: readonly StatTile[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {tiles.map((t, i) => (
        <div key={i} className="hover-lift rounded-lg border border-edge bg-panel px-3 py-3 text-center">
          <div className="font-mono text-xl font-bold tabular-nums text-text sm:text-2xl">{t.value}</div>
          <div className="mt-1 text-[11px] uppercase tracking-wide text-faint">{t.label}</div>
        </div>
      ))}
    </div>
  )
}
