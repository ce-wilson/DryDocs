import { useMemo, useState } from 'react'
import { TOWERS } from '../data/towers'
import { nodeById, type FrameRow, type Selection } from './demoGraph'
import EmptyState from '../components/ui/EmptyState'

// A data-frame grid (O9) — the ReUI Data Grid stand-in, hand-authored like the
// other copied-in primitives (Tabs / ResizableSplit). Linked selection both
// ways: a graph selection filters rows to the selected tower (with an explicit
// clear chip — never a silent filter) and highlights the exact node's row; a
// row click selects its backing node in the shared store.

interface DataFrameProps {
  cols: readonly string[]
  rows: readonly FrameRow[]
  selection: Selection | null
  onSelect: (sel: Selection | null) => void
}

export default function DataFrame({ cols, rows, selection, onSelect }: DataFrameProps) {
  const [text, setText] = useState('')
  const [towerFilterCleared, setTowerFilterCleared] = useState(false)

  const towerFilter = selection && !towerFilterCleared ? selection.tower : null
  const visible = useMemo(
    () =>
      rows.filter((r) => {
        if (towerFilter && r.tower !== null && r.tower !== towerFilter) return false
        if (text && !r.cells.some((c) => c.toLowerCase().includes(text.toLowerCase()))) return false
        return true
      }),
    [rows, towerFilter, text],
  )

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="flex shrink-0 items-center gap-2">
        <input
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Filter rows…"
          aria-label="Filter rows"
          className="w-44 text-xs"
        />
        {towerFilter && (
          <button
            type="button"
            onClick={() => setTowerFilterCleared(true)}
            className="rounded-full border border-blue-bright/60 bg-blue/10 px-2 py-0.5 text-[11px] text-blue-bright"
            title="Rows are filtered to the selected node's tower — click to show all"
          >
            filtered: {TOWERS[towerFilter].title} ✕
          </button>
        )}
        <span className="ml-auto font-mono text-[10px] text-faint">
          {visible.length}/{rows.length} rows · SYNTHESIZED
        </span>
      </div>

      {visible.length === 0 ? (
        <EmptyState title="No rows match" hint="Clear the filter chip or the text filter." />
      ) : (
        <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="sticky top-0 bg-panel-2">
              <tr>
                {cols.map((c) => (
                  <th key={c} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((r, i) => {
                const isSelected = r.nodeId !== undefined && r.nodeId === selection?.id
                const clickable = r.nodeId !== undefined
                return (
                  <tr
                    key={i}
                    aria-selected={isSelected}
                    onClick={() => {
                      if (!r.nodeId) return
                      const n = nodeById(r.nodeId)
                      if (n) {
                        setTowerFilterCleared(false)
                        onSelect({ id: n.id, label: n.label, kind: n.kind, tower: n.tower })
                      }
                    }}
                    className={
                      (isSelected ? 'bg-blue/15 ' : i % 2 ? 'bg-bg-2/40 ' : '') +
                      (clickable ? 'cursor-pointer hover:bg-panel-2' : 'cursor-default')
                    }
                    title={clickable ? 'Select this node in the graph' : undefined}
                  >
                    {r.cells.map((c, j) => (
                      <td key={j} className="border-b border-edge-soft px-2.5 py-1.5 text-text">
                        {c}
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
