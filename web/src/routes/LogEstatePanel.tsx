import { useEffect, useState } from 'react'

import EmptyState from '../components/ui/EmptyState'
import { useGraphAccess } from '../data/graphAccess'
import { fetchLogEstate, humanBytes, type LogEstatePayload } from '../lib/logEstate'

// O68 — the log estate, as a PANEL on the admin page (clause a: the SME placed
// it there rather than in a new epic).
//
// WHY A PANEL AND NOT JUST THE CLI (clause e, in the panel's own copy below as
// the clause asks): `drydocs landing-zones` exists so "my extracts are gone" is
// a one-command answer, and the person most likely to ask is on a machine where
// the CLI is not the habitual surface. Post-retention it answers the same
// question for logs — days declared against days actually on disk.
//
// THE DEBUG TIER IS REPORTED, NEVER RENDERED (clause c). ADR 0014 clause 6
// splits the lean API log from a verbose short-retention debug log carrying
// Cypher text and request detail; capturing that is ruled, surfacing it is not,
// and they are different risks — a short-lived file on an operator's disk versus
// a page anyone with the console can read. So `api-debug` appears here with its
// size, retention and age exactly like every other kind, and there is nothing
// to click that would show its contents. That is STRUCTURAL, not a promise: the
// endpoint takes no parameter naming a file, the payload carries no contents
// field, and this component makes one request with no arguments.

type Load =
  | { state: 'loading' }
  | { state: 'ready'; data: LogEstatePayload }
  | { state: 'error'; message: string }

export default function LogEstatePanel() {
  const { apiUrl } = useGraphAccess()
  const [load, setLoad] = useState<Load>({ state: 'loading' })

  useEffect(() => {
    const ctl = new AbortController()
    fetchLogEstate(apiUrl, ctl.signal)
      .then((data) => {
        if (!ctl.signal.aborted) setLoad({ state: 'ready', data })
      })
      .catch((err: unknown) => {
        if (ctl.signal.aborted) return
        // Loud, never a silent empty table: an empty estate and an unreachable
        // API look identical to a reader, and only one of them means "nothing
        // is there" — the same rule LocationMap keeps for the same reason.
        setLoad({ state: 'error', message: err instanceof Error ? err.message : String(err) })
      })
    return () => ctl.abort()
  }, [apiUrl])

  if (load.state === 'loading') {
    return <EmptyState title="Reading the log estate…" hint="drydocs-api /admin/log-estate" />
  }
  if (load.state === 'error') {
    return (
      <EmptyState
        title="The log estate could not be read"
        hint={`${load.message}. Nothing is shown rather than a directory listing that might be stale.`}
      />
    )
  }

  const { kinds, zones } = load.data

  return (
    <div className="flex h-full min-h-0 flex-col gap-2 overflow-auto">
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
        <b>Declared against actual.</b> Each kind&rsquo;s retention is what{' '}
        <code className="mx-0.5">config/log-kinds.yaml</code> says it keeps; the <b>oldest</b> column
        is what is on disk now, and a row is flagged when the two disagree. The command{' '}
        <code className="mx-0.5">drydocs landing-zones</code> answers the same question for extracts
        — this panel exists because the person asking &ldquo;where did my logs go&rdquo; is usually
        not at a terminal. <b>Contents are never shown, for any kind.</b>
      </p>

      <EstateTable
        caption={`Log kinds (${kinds.length})`}
        columns={['kind', 'level', 'directory', 'files', 'size', 'oldest', 'retention', 'rotation']}
        rows={kinds.map((k) => ({
          cells: [
            k.id,
            k.level,
            k.path,
            k.exists ? String(k.file_count) : '—',
            k.exists ? humanBytes(k.total_bytes) : '—',
            k.oldest_days === null ? '—' : `${k.oldest_days}d`,
            `${k.retention_days}d`,
            k.rotation,
          ],
          // Two different facts, said differently. "over retention" is a
          // disagreement between the declaration and the disk and is the thing
          // this panel exists to surface; "no directory" is a kind that has not
          // written yet, which for a `planned` kind is correct and for an
          // `active` one is worth a look.
          flag: k.over_retention
            ? `older than ${k.retention_days}d`
            : k.exists
              ? ''
              : k.status === 'planned'
                ? 'planned — no writer yet'
                : 'no directory',
          pathColumn: 2,
        }))}
      />

      <EstateTable
        caption={`Data zones (${zones.length})`}
        columns={['zone', 'path', 'files', 'size']}
        rows={zones.map((z) => ({
          cells: [
            z.id,
            z.path,
            z.exists ? String(z.file_count) : '—',
            z.exists ? humanBytes(z.total_bytes) : '—',
          ],
          flag: z.exists ? (z.empty ? 'empty' : '') : 'absent',
          pathColumn: 1,
        }))}
      />
    </div>
  )
}

interface EstateRow {
  cells: string[]
  flag: string
  /** Which cell holds a filesystem path, so it renders monospaced. */
  pathColumn: number
}

function EstateTable({
  caption,
  columns,
  rows,
}: {
  caption: string
  columns: string[]
  rows: EstateRow[]
}) {
  return (
    <div className="shrink-0 overflow-auto rounded-md border border-edge">
      <table className="w-full border-collapse text-left text-xs">
        <caption className="border-b border-edge bg-panel-2 px-2.5 py-1 text-left text-[11px] font-semibold text-muted">
          {caption}
        </caption>
        <thead className="bg-panel-2">
          <tr>
            {[...columns, ''].map((h, i) => (
              <th key={i} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? 'bg-bg-2/40' : ''}>
              {row.cells.map((cell, j) => (
                <td
                  key={j}
                  className={
                    'border-b border-edge-soft px-2.5 py-1.5 ' +
                    (j === row.pathColumn ? 'font-mono text-[10px] text-faint' : 'text-text')
                  }
                >
                  {cell}
                </td>
              ))}
              <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-yellow">
                {row.flag}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
