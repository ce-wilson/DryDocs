import { useMemo, useState } from 'react'

// Shared table controls — the DomainGridTable idiom, extracted so a third
// surface can use it instead of copying it a third time.
//
// WHY EXTRACT NOW. `toCsv` already existed twice (explorer/SpecGrid.tsx and
// routes/DomainGridTable.tsx) with the same RFC 4180 rule written out both
// times. /load-map wanting the same controls is the third copy, and three is
// where a convention becomes a thing that drifts. The behaviours here are the
// ones DomainGridTable settled on; its reasoning is carried over rather than
// re-derived, because the reason is the rule.
//
// SORT IS A THREE-STATE CYCLE (none -> asc -> desc -> none), not the usual two.
// The natural row order is meaningful on every surface that uses this: the
// mapping grid comes back ORDER BY seq (the authored loading quintuple), and
// the load map's rows arrive in registry order. A two-state toggle makes that
// original order unreachable the moment a reader clicks any header.
//
// EVERY CONTROL OPERATES ON THE CURRENT VIEW. Nothing here re-queries, writes,
// or reaches a server: these render over a committed artifact or an already-
// returned row set. A control that changed what data exists would belong to the
// surface, not to a presentation helper.

export type SortState = { key: string; dir: 'asc' | 'desc' } | null

/** RFC 4180 escaping — the rule SpecGrid and DomainGridTable each wrote out. */
export function toCsv(keys: readonly string[], rows: readonly Record<string, unknown>[]): string {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s
  }
  return [keys.join(','), ...rows.map((r) => keys.map((k) => esc(r[k])).join(','))].join('\n') + '\n'
}

export function download(filename: string, content: string, type = 'text/csv') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Compare two cells for sorting.
 *
 * BLANKS SORT LAST IN BOTH DIRECTIONS — an empty cell is missing data, not a
 * value smaller than every other value. Sorting them to the top under `asc`
 * would bury the rows a reader sorted in order to find.
 */
export function compareCells(a: unknown, b: unknown): number {
  const emptyA = a === null || a === undefined || a === ''
  const emptyB = b === null || b === undefined || b === ''
  if (emptyA && emptyB) return 0
  if (emptyA) return 1
  if (emptyB) return -1
  if (typeof a === 'number' && typeof b === 'number') return a - b
  if (typeof a === 'boolean' && typeof b === 'boolean') return Number(a) - Number(b)
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' })
}

/** The three-state cycle, as a pure transition so it can be tested directly. */
export function nextSort(current: SortState, key: string): SortState {
  if (!current || current.key !== key) return { key, dir: 'asc' }
  if (current.dir === 'asc') return { key, dir: 'desc' }
  return null
}

/** One rendered group: its key value, a display label, and its rows. */
export interface RowGroup<T> {
  key: string
  label: string
  rows: T[]
}

/**
 * Filter, sort and optionally group a row set for display.
 *
 * GROUPING IS ORTHOGONAL TO SORTING, and applying it in that order is what
 * keeps it honest: rows are sorted FIRST, then partitioned, so the order
 * inside a group is the same order a reader would see ungrouped. Grouping that
 * re-ordered rows on its own would make the sort control lie.
 *
 * Groups are ordered by label, blank group last — the same reason blank cells
 * sort last.
 */
export function useTableView<T extends Record<string, unknown>>(
  rows: readonly T[],
  opts: {
    filter: string
    searchKeys: readonly string[]
    sort: SortState
    /** null = no grouping. */
    groupKey: string | null
  },
): { rows: T[]; groups: RowGroup<T>[] | null } {
  const { filter, searchKeys, sort, groupKey } = opts
  return useMemo(() => {
    const term = filter.trim().toLowerCase()
    let out = term
      ? rows.filter((r) => searchKeys.some((k) => String(r[k] ?? '').toLowerCase().includes(term)))
      : [...rows]

    if (sort) {
      const dir = sort.dir === 'asc' ? 1 : -1
      // Copy before sorting: the incoming order is the natural one, and the
      // caller may still be holding it.
      out = [...out].sort((a, b) => compareCells(a[sort.key], b[sort.key]) * dir)
    }

    if (!groupKey) return { rows: out, groups: null }

    const byKey = new Map<string, T[]>()
    for (const r of out) {
      const k = String(r[groupKey] ?? '')
      const bucket = byKey.get(k)
      if (bucket) bucket.push(r)
      else byKey.set(k, [r])
    }
    const groups: RowGroup<T>[] = [...byKey.entries()]
      .map(([key, groupRows]) => ({ key, label: key || '(none)', rows: groupRows }))
      .sort((a, b) => (a.key === '' ? 1 : b.key === '' ? -1 : a.label.localeCompare(b.label)))
    return { rows: out, groups }
  }, [rows, filter, searchKeys, sort, groupKey])
}

/** The control bar: filter box, optional group-by toggle, CSV export, count. */
export function TableControlBar({
  filter,
  onFilter,
  count,
  total,
  groupLabel,
  grouped,
  onToggleGroup,
  onExport,
}: {
  filter: string
  onFilter: (v: string) => void
  count: number
  total: number
  /** Omit to hide the toggle — a table with nothing meaningful to group by. */
  groupLabel?: string
  grouped?: boolean
  onToggleGroup?: () => void
  onExport?: () => void
}) {
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-2">
      <input
        type="search"
        value={filter}
        onChange={(e) => onFilter(e.target.value)}
        placeholder="filter rows"
        aria-label="Filter rows"
        className="w-44 rounded border border-edge bg-bg-2 px-2 py-0.5 text-[11px] text-text placeholder:text-faint"
      />
      {groupLabel && onToggleGroup && (
        <button
          type="button"
          onClick={onToggleGroup}
          aria-pressed={!!grouped}
          className={
            'rounded border px-2 py-0.5 text-[10px] ' +
            (grouped ? 'border-blue-bright bg-panel-2 text-text' : 'border-edge text-muted hover:text-text')
          }
        >
          group by {groupLabel}
        </button>
      )}
      {onExport && (
        <button
          type="button"
          onClick={onExport}
          className="rounded border border-edge px-2 py-0.5 text-[10px] text-muted hover:text-text"
        >
          export CSV
        </button>
      )}
      <span className="text-[10px] text-faint">
        {count === total ? `${total} rows` : `${count} of ${total} rows`}
      </span>
    </div>
  )
}

/** A sortable `<th>`: click cycles none -> asc -> desc -> none. */
export function SortableTh({
  label,
  sortKey,
  sort,
  onSort,
  className,
}: {
  label: string
  /** null = not sortable (a composite or rendered cell with no single value). */
  sortKey: string | null
  sort: SortState
  onSort: (k: string) => void
  className?: string
}) {
  if (!sortKey) return <th className={className}>{label}</th>
  const active = sort?.key === sortKey
  const glyph = !active ? '' : sort.dir === 'asc' ? ' ▲' : ' ▼'
  return (
    <th
      className={className}
      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button type="button" onClick={() => onSort(sortKey)} className="w-full text-left hover:text-text" title={`Sort by ${label}`}>
        {label}
        <span className="text-blue-bright">{glyph}</span>
      </button>
    </th>
  )
}

/** Local state for one table's controls. */
export function useTableControls(initialSort: SortState = null) {
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState<SortState>(initialSort)
  const [grouped, setGrouped] = useState(false)
  return {
    filter,
    setFilter,
    sort,
    grouped,
    toggleGroup: () => setGrouped((g) => !g),
    cycleSort: (k: string) => setSort((cur) => nextSort(cur, k)),
  }
}
