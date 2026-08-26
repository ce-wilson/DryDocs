import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { MappingGrid } from '../lib/mappingsApi'

// The read-only mapping.db grid for the registry-driven domains (ontology-map
// and, when their reconciler tables land, fid-seal / alias-seal). Extracted
// from MappingsRoute at the point it grew controls — the same move
// AppCodeCascadePane made out of the same route, and it rides UNBOUND in
// config/taxonomy/ui-components.yaml for the same reason: 'mappings' is not a
// registry module, so binding it would invent one.
//
// FOUR CONTROLS, all operating on the CURRENT VIEW and none of them touching
// the server: filter, sort, column widths, CSV export. The grid is a read-only
// materialization of a committed source, so every control here is presentation
// — nothing re-queries, nothing writes, and the row set stays whatever
// /mappings/grid/<domain> returned.
//
// Sort is a THREE-state cycle (none -> asc -> desc -> none) rather than the
// usual two, because the server's natural order is meaningful: ontology_mapping
// comes back ORDER BY seq, the authored sequence of the loading quintuple. A
// two-state toggle would make that order unreachable once a reader clicked any
// header.

const MIN_COL_PX = 60
const WIDTHS_KEY = 'drydocs.mappings.colwidths.v1'

type SortState = { key: string; dir: 'asc' | 'desc' } | null

/** CSV escaping — the same rule as explorer/SpecGrid.tsx's toCsv (RFC 4180). */
function toCsv(keys: string[], rows: Record<string, unknown>[]): string {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
  }
  return [keys.join(','), ...rows.map((r) => keys.map((k) => esc(r[k])).join(','))].join('\n') + '\n'
}

function download(filename: string, content: string, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Blanks sort LAST in both directions — an empty cell is missing data, not a
 * smallest value, and burying the populated rows under 30 nulls is the reverse
 * of what a reader asked for. Numeric when both sides parse, collation
 * otherwise. Returns a non-finite sentinel for the blank cases so the caller
 * can skip the direction multiplier.
 */
function compareCells(a: unknown, b: unknown): number {
  const av = a === null || a === undefined || a === '' ? null : a
  const bv = b === null || b === undefined || b === '' ? null : b
  if (av === null && bv === null) return 0
  if (av === null) return Number.POSITIVE_INFINITY
  if (bv === null) return Number.NEGATIVE_INFINITY
  const an = Number(av)
  const bn = Number(bv)
  if (!Number.isNaN(an) && !Number.isNaN(bn)) return an - bn
  return String(av).localeCompare(String(bv))
}

export default function DomainGridTable({
  grid,
  apiDown,
  domainId,
  source,
}: {
  grid: MappingGrid | null
  apiDown: string | null
  domainId: string
  source?: string
}) {
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState<SortState>(null)
  const [widths, setWidths] = useState<Record<string, number> | null>(null)
  const headRefs = useRef<Record<string, HTMLTableCellElement | null>>({})
  const drag = useRef<{ key: string; startX: number; startW: number } | null>(null)

  const keys = useMemo(() => grid?.keys ?? [], [grid])
  const storageKey = `${WIDTHS_KEY}.${domainId}`

  // Filter and sort reset when the domain changes — carrying one domain's
  // filter onto another's columns would silently hide rows.
  useEffect(() => {
    setFilter('')
    setSort(null)
    setWidths(null)
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) setWidths(JSON.parse(saved) as Record<string, number>)
    } catch {
      /* private mode / blocked storage — the measured defaults below still apply */
    }
  }, [storageKey])

  // Seed widths from the NATURAL (table-auto) layout the first time a grid
  // paints, then switch to table-fixed so dragging is meaningful. Measuring
  // beats guessing: the quintuple's matrix_row column is an order of magnitude
  // wider than its status column, and an equal-split default would look broken
  // before anyone touched it.
  useLayoutEffect(() => {
    if (widths || !grid || grid.rows.length === 0) return
    const measured: Record<string, number> = {}
    for (const k of keys) {
      const el = headRefs.current[k]
      if (el) measured[k] = Math.max(MIN_COL_PX, Math.round(el.getBoundingClientRect().width))
    }
    if (Object.keys(measured).length === keys.length) setWidths(measured)
  }, [widths, grid, keys])

  const onPointerMove = useCallback((e: PointerEvent) => {
    const d = drag.current
    if (!d) return
    const next = Math.max(MIN_COL_PX, d.startW + (e.clientX - d.startX))
    setWidths((w) => (w ? { ...w, [d.key]: next } : w))
  }, [])

  const onPointerUp = useCallback(() => {
    drag.current = null
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
    setWidths((w) => {
      try {
        if (w) localStorage.setItem(storageKey, JSON.stringify(w))
      } catch {
        /* not persisting is fine; the drag still applied for this session */
      }
      return w
    })
  }, [onPointerMove, storageKey])

  function startResize(e: React.PointerEvent, key: string) {
    e.preventDefault()
    e.stopPropagation() // a resize drag must never also register as a sort click
    const w = widths?.[key] ?? headRefs.current[key]?.getBoundingClientRect().width ?? MIN_COL_PX
    drag.current = { key, startX: e.clientX, startW: w }
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
  }

  useEffect(
    () => () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
    },
    [onPointerMove, onPointerUp],
  )

  const visible = useMemo(() => {
    if (!grid) return []
    const needle = filter.trim().toLowerCase()
    const rows = needle
      ? grid.rows.filter((r) => keys.some((k) => String(r[k] ?? '').toLowerCase().includes(needle)))
      : grid.rows
    if (!sort) return rows
    const dir = sort.dir === 'asc' ? 1 : -1
    // copy before sorting: the server's row order IS the natural order the
    // third click cycles back to, so it must survive
    return [...rows].sort((a, b) => {
      const c = compareCells(a[sort.key], b[sort.key])
      if (!Number.isFinite(c)) return c > 0 ? 1 : -1 // blanks last, both directions
      return c * dir
    })
  }, [grid, keys, filter, sort])

  if (!grid) {
    return (
      <p className="px-1 py-2 text-[11px] text-faint">
        {apiDown ? 'Needs drydocs-api (mapping.db read).' : 'Loading mapping.db grid…'}
      </p>
    )
  }
  if (grid.rows.length === 0) {
    return <p className="px-1 py-2 text-[11px] text-faint">No committed entries yet.</p>
  }

  const allRows = grid.rows

  function cycleSort(k: string) {
    setSort((s) =>
      !s || s.key !== k ? { key: k, dir: 'asc' } : s.dir === 'asc' ? { key: k, dir: 'desc' } : null,
    )
  }

  function resetColumns() {
    setWidths(null)
    try {
      localStorage.removeItem(storageKey)
    } catch {
      /* nothing to clear */
    }
  }

  function exportCsv() {
    // Mapping domains carry no `classification` in the registry, so no
    // INTERNAL__ filename prefix applies here. If one is ever added to DOMAINS,
    // adopt SpecGrid.clientExport's prefix rule rather than writing a second.
    const name = `${domainId}.view.csv`
    download(name, toCsv(keys, visible), 'text/csv')
    // Sidecar, matching the O11 client-export path: an export that cannot say
    // what it is a view OF is not evidence of anything.
    download(
      `${name}.manifest.json`,
      JSON.stringify(
        {
          mapping_domain: domainId,
          source: source ?? null,
          row_count: visible.length,
          total_rows: allRows.length,
          scope: 'client-view (current grid state — filter and sort applied)',
          filter: filter || null,
          sort: sort ? `${sort.key} ${sort.dir}` : 'natural (server order)',
          exported_at: new Date().toISOString(),
        },
        null,
        2,
      ),
      'application/json',
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-1.5">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5">
        <input
          type="search"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter rows…"
          aria-label="Filter rows"
          className="w-40 text-xs"
        />
        <span className="font-mono text-[10px] text-faint">
          {visible.length}/{allRows.length}
          {sort ? ` · ${sort.key} ${sort.dir}` : ''}
        </span>
        <span className="ml-auto flex items-center gap-1">
          {widths && (
            <GridButton
              label="Reset columns"
              title="Back to the measured default widths"
              onClick={resetColumns}
            />
          )}
          <GridButton
            label="CSV"
            title="Client export — current grid state (filter + sort), plus a manifest sidecar"
            onClick={exportCsv}
          />
        </span>
      </div>

      {visible.length === 0 ? (
        <p className="px-1 py-2 text-[11px] text-faint">No rows match that filter.</p>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
          <table
            className={'w-full border-collapse text-left text-[11px] ' + (widths ? 'table-fixed' : 'table-auto')}
          >
            {widths && (
              <colgroup>
                {keys.map((k) => (
                  <col key={k} style={{ width: `${widths[k]}px` }} />
                ))}
              </colgroup>
            )}
            <thead className="sticky top-0 z-10 bg-panel-2">
              <tr>
                {keys.map((k) => {
                  const active = sort?.key === k
                  return (
                    <th
                      key={k}
                      ref={(el) => {
                        headRefs.current[k] = el
                      }}
                      scope="col"
                      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
                      className="relative border-b border-edge p-0 font-semibold text-muted"
                    >
                      <button
                        type="button"
                        onClick={() => cycleSort(k)}
                        title={`Sort by ${k} — click again to reverse, a third time for the source order`}
                        className={
                          'flex w-full items-center gap-1 px-2 py-1 text-left hover:text-text ' +
                          (active ? 'text-text' : '')
                        }
                      >
                        <span className="truncate">{k}</span>
                        <span className="font-mono text-[9px] text-faint">
                          {active ? (sort.dir === 'asc' ? '▲' : '▼') : ''}
                        </span>
                      </button>
                      <span
                        role="separator"
                        aria-orientation="vertical"
                        aria-label={`Resize ${k} column`}
                        onPointerDown={(e) => startResize(e, k)}
                        className="absolute right-0 top-0 h-full w-1.5 cursor-col-resize select-none hover:bg-brand/60"
                      />
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {visible.map((r, i) => (
                <tr key={i} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  {keys.map((k) => (
                    <td
                      key={k}
                      title={String(r[k] ?? '')}
                      className="truncate border-b border-edge-soft px-2 py-1 text-text"
                    >
                      {String(r[k] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function GridButton({ label, title, onClick }: { label: string; title: string; onClick: () => void }) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className="rounded-md border border-edge bg-bg-2 px-2 py-0.5 text-[11px] font-medium text-muted hover:border-faint hover:text-text"
    >
      {label}
    </button>
  )
}
