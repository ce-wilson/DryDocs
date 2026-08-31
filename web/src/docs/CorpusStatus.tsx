import { useEffect, useMemo, useState } from 'react'

import { apiBaseUrl } from '../lib/auth'
import { fetchCorpusStatus, type CorpusStatusPayload } from '../lib/corpusStatus'
import EmptyState from '../components/ui/EmptyState'
import StatusChip from '../components/ui/StatusChip'

// The docs-verify surface (O58): which declared corpus is actually loaded, and
// in which database.
//
// NOT A QUERYSPEC FRAME, and that is the item's whole content rather than an
// omission. The reconciliation is inherently MULTI-database — it sweeps more
// than one precisely so a corpus sitting where it did not declare becomes
// visible — while a spec carries exactly one `database:` and SPEC_DATABASES has
// been {"drydocs"} since the G102 fold. It also needs SHOW DATABASES, a
// server-level query no spec expresses, which is the only source of `db-absent`.
// So this reads a named server-side endpoint whose queries are all chosen by
// drydocs_core.docs_verify; the browser sends no parameters and cannot influence
// which Cypher runs. The cost and the ADR 0005 position are recorded in
// drydocs_api/corpus_status.py.
//
// THE STATUS VOCABULARY COMES FROM THE SERVER, never from a list typed here.
// O58's own acceptance says "six states"; there have been SEVEN since G102 added
// wrong-realm. A page built to that wording would have had no cell for the
// status that replaced the wrong-db subject — so the payload carries the set and
// this component renders whatever it is sent.
//
// WRONG-DB IS THE ALARM, because it is the one status that sets a non-zero exit
// on the CLI: a corpus in a database it did not declare is the G30 failure class
// at corpus granularity. It is coloured as a failure and counted separately, not
// listed alphabetically among the rest.

/** Token per status. Anything the server sends that is not listed here still
 *  renders — in the neutral token — because an unknown status must appear, not
 *  vanish. The two FAILING statuses are the alarm and are coloured as such. */
const STATUS_TOKEN: Record<string, '--green' | '--yellow' | '--status-fail-soft' | '--muted'> = {
  loaded: '--green',
  missing: '--yellow',
  stale: '--yellow',
  'wrong-db': '--status-fail-soft',
  'wrong-realm': '--status-fail-soft',
  unshaped: '--muted',
  'db-absent': '--muted',
}

const FAILING = new Set(['wrong-db', 'wrong-realm'])

const TH = 'border-b border-edge px-2.5 py-1.5 text-left font-semibold text-muted'
const TD = 'border-b border-edge-soft px-2.5 py-1.5 align-top text-text'

function tokenFor(status: string) {
  return STATUS_TOKEN[status] ?? '--muted'
}

export default function CorpusStatus() {
  const [data, setData] = useState<CorpusStatusPayload | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchCorpusStatus(apiBaseUrl())
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const counts = useMemo(() => {
    if (!data) return []
    // Every status the SERVER declares gets a chip, including the zeroes: a
    // status that disappears when nothing is in it reads as "this page does not
    // check for that", and "0 wrong-db" is the reassurance worth showing.
    return data.statuses.map((s) => ({
      status: s,
      n: data.rows.filter((r) => r.status === s).length,
    }))
  }, [data])

  if (error) {
    return (
      <EmptyState
        title="The corpus reconciliation could not be read"
        hint={`${error}. Nothing is shown rather than showing a reconciliation that did not run.`}
      />
    )
  }
  if (!data) return <EmptyState title="Reconciling declared corpora against the graph…" />

  const notQueried = data.databases_swept.filter((db) => !data.databases_queried.includes(db))

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 rounded border border-edge bg-panel-2 px-2.5 py-1.5">
        {counts.map(({ status, n }) => (
          <StatusChip key={status} count={n} label={status} token={tokenFor(status)} />
        ))}
        <span className="ml-auto font-mono text-[10px] text-muted">
          swept: {data.databases_queried.join(', ') || 'none'}
        </span>
      </div>

      {notQueried.length > 0 && (
        // The O56 honesty rule, made visible: a database that was not queried
        // renders as NOT QUERIED, never as zero rows. Absence of a database is
        // not absence of data in it.
        <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
          not queried: {notQueried.join(', ')} — the server does not have{' '}
          {notQueried.length === 1 ? 'it' : 'them'}. Corpora declaring{' '}
          {notQueried.length === 1 ? 'it' : 'them'} report db-absent; nothing here is a count of
          zero.
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              <th className={TH}>Corpus</th>
              <th className={TH}>Declared db</th>
              <th className={TH}>Status</th>
              <th className={TH}>Documents</th>
              <th className={TH}>Chunks</th>
              <th className={TH}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr
                key={r.corpus_id}
                className={FAILING.has(r.status) ? 'bg-[var(--status-fail-soft)]/10' : undefined}
              >
                <td className={`${TD} font-mono text-[11px]`}>{r.corpus_id}</td>
                <td className={`${TD} font-mono text-[10px] text-muted`}>{r.target_db}</td>
                <td className={TD}>
                  <span
                    className="rounded-full border px-1.5 py-0.5 font-mono text-[10px] font-semibold"
                    style={{
                      borderColor: `var(${tokenFor(r.status)})`,
                      color: `var(${tokenFor(r.status)})`,
                      background: `color-mix(in srgb, var(${tokenFor(r.status)}) 10%, transparent)`,
                    }}
                  >
                    {r.status}
                  </span>
                </td>
                {/* A corpus that is not loaded has no count to show. An em dash
                    rather than 0: zero documents and "we did not find it" are
                    different statements. */}
                <td className={`${TD} tabular-nums`}>{r.documents || '—'}</td>
                <td className={`${TD} tabular-nums`}>{r.chunks || '—'}</td>
                <td className={`${TD} text-[11px] leading-snug text-muted`}>{r.detail || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="shrink-0 rounded border border-edge px-2.5 py-1 text-[10px] leading-snug text-muted">
        <span className="font-mono text-[var(--status-fail-soft)]">wrong-db</span> and{' '}
        <span className="font-mono text-[var(--status-fail-soft)]">wrong-realm</span> are the
        alarm — they are the statuses that make <span className="font-mono">drydocs docs-verify</span>{' '}
        exit non-zero. A corpus in a database it did not declare is invisible to any single-database
        query, which is why this page reads a multi-database sweep rather than a QuerySpec.
      </p>
    </div>
  )
}
