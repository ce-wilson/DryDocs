// O28 — the node-status envelope, UI side.
//
// ONE shape for every producer: {type, level, message, error?}. The contract
// and its two rules live in knowledge/standards/node-status-envelope.md:
// items are always DERIVED by a producing system (never hand-authored), and a
// new source adds a NAMESPACED TYPE rather than a new field.
//
// That second rule is what this module leans on: nothing here switches on a
// known set of `type` values, so a producer that ships tomorrow renders
// correctly today. Level and namespace carry all the presentation.

export type StatusLevel = 'info' | 'warning' | 'error'

export interface StatusItem {
  /** `<source>/<slug>`, e.g. `drydocs.loader/rows-rejected` */
  type: string
  level: StatusLevel
  message: string
  /** optional detail slot */
  error?: string
}

const LEVELS: readonly StatusLevel[] = ['info', 'warning', 'error']

/** Severity order — index doubles as the rank for worstLevel(). */
export const LEVEL_RANK: Record<StatusLevel, number> = { info: 0, warning: 1, error: 2 }

/** The source namespace — the part before the `/`. */
export function statusSource(item: StatusItem): string {
  return item.type.split('/')[0] ?? item.type
}

/**
 * Parse one `status_item` cell from `loads.status-items.v1`.
 *
 * The wire format is a JSON string because Neo4j cannot hold a map inside a
 * list property. Returns null rather than throwing: one malformed item must
 * not blank a whole status section, and a producer bug should degrade to
 * "fewer signals", never to "no page".
 */
export function parseStatusItem(raw: unknown): StatusItem | null {
  if (raw == null) return null
  let value: unknown = raw
  if (typeof raw === 'string') {
    try {
      value = JSON.parse(raw)
    } catch {
      return null
    }
  }
  if (typeof value !== 'object' || value === null) return null
  const o = value as Record<string, unknown>
  if (typeof o.type !== 'string' || typeof o.message !== 'string') return null
  if (typeof o.level !== 'string' || !LEVELS.includes(o.level as StatusLevel)) return null
  const item: StatusItem = { type: o.type, level: o.level as StatusLevel, message: o.message }
  if (typeof o.error === 'string' && o.error) item.error = o.error
  return item
}

export function parseStatusItems(rows: readonly unknown[]): StatusItem[] {
  return rows.map(parseStatusItem).filter((i): i is StatusItem => i !== null)
}

/**
 * The glyph severity for a node: the worst level present, or null when there
 * is nothing to report.
 *
 * `null` deliberately covers BOTH "healthy" and "unknown" for the caller to
 * distinguish — the contract keeps them apart in the graph (a :JobRun with an
 * empty list is healthy; no :JobRun at all is unknown), and a caller that
 * cannot tell should render neither a green tick nor an alarm.
 */
export function worstLevel(items: readonly StatusItem[]): StatusLevel | null {
  if (items.length === 0) return null
  return items.reduce<StatusLevel>(
    (worst, i) => (LEVEL_RANK[i.level] > LEVEL_RANK[worst] ? i.level : worst),
    'info',
  )
}

/** Token colour per level — O8 token sheet, never hard-coded hex. */
export const LEVEL_TOKEN: Record<StatusLevel, string> = {
  info: '--blue-bright',
  warning: '--yellow',
  error: '--red',
}

export const LEVEL_LABEL: Record<StatusLevel, string> = {
  info: 'Info',
  warning: 'Warning',
  error: 'Error',
}
