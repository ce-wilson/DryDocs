import {
  LEVEL_LABEL,
  LEVEL_TOKEN,
  statusSource,
  worstLevel,
  type StatusItem,
  type StatusLevel,
} from '../../lib/status'

// O28 — the two renderers for the node-status envelope. Both take the SAME
// StatusItem[] the contract defines, which is the point: the inspector's
// status section and the hub's spoke health glyph are two views of one shape,
// so a new producer lights up both without touching either.
//
// Nothing here switches on a known `type`. The namespace is shown verbatim and
// the level drives colour, so an unrecognised producer renders correctly.

/**
 * Spoke/row health glyph. `items` empty means healthy; pass `unknown` when
 * nothing has ever reported, which the contract keeps distinct from healthy —
 * a dashboard that shows those the same is green because nothing is watching.
 */
export function HealthGlyph({
  items,
  unknown = false,
  className = '',
}: {
  items: readonly StatusItem[]
  unknown?: boolean
  className?: string
}) {
  const level = worstLevel(items)

  if (unknown) {
    return (
      <span
        className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full border border-faint ${className}`}
        title="No producer has reported on this yet"
        aria-label="Status unknown"
      />
    )
  }

  if (level === null) {
    return (
      <span
        className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-teal ${className}`}
        title="Healthy — a producer ran and found nothing to report"
        aria-label="Healthy"
      />
    )
  }

  const counts = items.filter((i) => i.level === level).length
  return (
    <span
      className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${className}`}
      style={{ background: `var(${LEVEL_TOKEN[level]})` }}
      title={`${counts} ${LEVEL_LABEL[level].toLowerCase()}${counts === 1 ? '' : 's'}`}
      aria-label={`${LEVEL_LABEL[level]}: ${counts}`}
    />
  )
}

/** The inspector sidebar's status section. Renders nothing when there is
 *  nothing to say — an empty "Status: OK" block is noise in a 256px rail. */
export default function StatusItems({
  items,
  emptyNote,
}: {
  items: readonly StatusItem[]
  emptyNote?: string
}) {
  if (items.length === 0 && !emptyNote) return null

  return (
    <div>
      <h4 className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-faint">
        Status
        <HealthGlyph items={items} />
      </h4>
      {items.length === 0 ? (
        <p className="text-[11px] text-faint">{emptyNote}</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {items.map((item, i) => (
            <li
              key={`${item.type}-${i}`}
              className="rounded border border-edge-soft bg-bg-2/50 px-2 py-1"
              style={{ borderLeftColor: `var(${LEVEL_TOKEN[item.level as StatusLevel]})`, borderLeftWidth: 2 }}
            >
              <div className="flex items-center gap-1.5">
                <span
                  className="font-mono text-[10px] uppercase"
                  style={{ color: `var(${LEVEL_TOKEN[item.level as StatusLevel]})` }}
                >
                  {item.level}
                </span>
                {/* the namespace, not the whole type — the slug is in the message */}
                <span className="truncate font-mono text-[10px] text-faint">{statusSource(item)}</span>
              </div>
              <p className="mt-0.5 text-[11px] leading-snug text-text">{item.message}</p>
              {item.error && (
                <p className="mt-0.5 truncate font-mono text-[10px] text-muted" title={item.error}>
                  {item.error}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
