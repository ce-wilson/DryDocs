import { useMemo, useState } from 'react'

import { apiBaseUrl } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import type { SpecResult } from '../lib/graph'
import EmptyState from '../components/ui/EmptyState'

// The Ask file-name REPORT (O62): search a file, get the application, the
// process, and who to escalate to.
//
// WHY A SPEC AND NOT THE AGENT. The item's own 2026-08-21 observation is the
// argument: a live Ask session answered a file-name question by routing to
// `docs.documents.v1`, whose Cypher applies NO filter — it lists every
// :Document and the model picked the match out of 27 rows. Correct that day,
// and it degrades as the corpus grows. Sharper still, a full listing can never
// render "not found", so the honest-absence clause below would be meaningless
// on top of it. `ask.file-search.v1` filters IN THE SPEC, which is what makes
// an empty answer mean something.
//
// ABSENCE IS RENDERED, NEVER IMPLIED. A leg the graph cannot supply says "not
// found via ask.file-search.v1" and names the spec, so a reader can tell "the
// graph does not hold this" from "nothing exists". An empty section with a
// heading reads as the second, which is the failure this clause exists for.
//
// THE REPO LEG IS ABSENT BY CONSTRUCTION and says so differently from the
// others: no :CodeRepo label exists in the ontology at all, so this is not a
// gap in the data but a subject nobody has modelled. Reporting it as "not
// found" would suggest a load would fix it. Minting the label is an ontology
// decision for the RELATIONSHIP_GUIDE and the HITL gate.

interface ReportRow {
  asset: string
  asset_kind: string
  hop: string
  activity: string
  activity_type: string
  folder: string
  app_id: string
  application: string
  dev_team: string
}

const SPEC_ID = 'ask.file-search.v1'

/** Which source system asserted each column — the legend the captured example
 *  carries, so a reader can tell where a row came from rather than assuming one
 *  system knows all of it. */
const SOURCE_LEGEND: readonly { column: string; label: string; source: string }[] = [
  { column: 'File / asset', label: ':DataAsset', source: 'lineage load (curated, post-gate)' },
  { column: 'Process', label: ':ETLProcess / :ControlMJob / :Script', source: 'Control-M + MAC extract' },
  { column: 'Control-M folder', label: ':ControlMFolder', source: 'Control-M definitions' },
  { column: 'Business application', label: ':BusinessApplication', source: 'SEAL extract, via the seal_app_ref :Port' },
  { column: 'Dev team', label: ':DevTeam', source: 'PAT attribution (WAS_ATTRIBUTED_TO developed_by)' },
]

/** Legs the report shows and where each comes from. `modelled: false` means the
 *  ontology has no label for it — a different statement from "not loaded". */
const LEGS: readonly { key: keyof ReportRow | 'repo'; label: string; modelled: boolean }[] = [
  { key: 'application', label: 'Business application', modelled: true },
  { key: 'activity', label: 'Process', modelled: true },
  { key: 'folder', label: 'Control-M folder', modelled: true },
  { key: 'dev_team', label: 'Dev team (escalation)', modelled: true },
  { key: 'repo', label: 'Code repository', modelled: false },
]

const TH = 'border-b border-edge px-2.5 py-1.5 text-left font-semibold text-muted'
const TD = 'border-b border-edge-soft px-2.5 py-1.5 align-top text-text'

export default function FileReport({ personaId }: { personaId: string }) {
  const [term, setTerm] = useState('')
  const [rows, setRows] = useState<ReportRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const access = useMemo(() => createApiAccess(apiBaseUrl(), personaId), [personaId])

  async function run(e: React.FormEvent) {
    e.preventDefault()
    const q = term.trim()
    if (!q) return
    setBusy(true)
    setError(null)
    setRows(null)
    try {
      const res: SpecResult = await access.runSpec(SPEC_ID, { term: q })
      setRows(res.rows as unknown as ReportRow[])
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <form onSubmit={run} className="flex shrink-0 items-center gap-2">
        <input
          type="text"
          value={term}
          onChange={(ev) => setTerm(ev.target.value)}
          placeholder="file or table name…"
          aria-label="File or table name"
          className="min-w-0 flex-1 font-mono text-xs"
        />
        <button
          type="submit"
          disabled={busy || !term.trim()}
          className="rounded border border-edge bg-panel px-2.5 py-1 font-mono text-[11px] text-text hover:border-[var(--blue-br)] disabled:opacity-50"
        >
          {busy ? 'searching…' : 'Report'}
        </button>
      </form>

      <p className="shrink-0 rounded border border-edge px-2.5 py-1 text-[10px] leading-snug text-muted">
        Bound to the reviewed spec <span className="font-mono text-text">{SPEC_ID}</span>, which
        filters on the term SERVER-SIDE. No Cypher is composed in the browser (ADR 0005), and an
        empty answer is a real &ldquo;not found&rdquo; rather than a slice of a full listing.
      </p>

      {error && (
        <EmptyState
          title="The search could not run"
          hint={`${error} — nothing is shown rather than showing a report the spec did not return.`}
        />
      )}

      {rows !== null && rows.length === 0 && (
        <EmptyState
          title={`No asset matches “${term.trim()}”`}
          hint={`not found via ${SPEC_ID}. The spec filtered on the term and the graph returned nothing — which is an answer, not an empty section.`}
        />
      )}

      {rows !== null && rows.length > 0 && (
        <div className="min-h-0 flex-1 space-y-1.5 overflow-auto pr-0.5">
          {rows.map((row, i) => (
            <section key={`${row.asset}:${row.activity}:${i}`} className="rounded-md border border-edge">
              <p className="border-b border-edge bg-panel-2 px-2.5 py-1.5 font-mono text-[11px] font-semibold text-text">
                {row.asset}
                <span className="ml-2 font-normal text-muted">{row.asset_kind || 'kind not stated'}</span>
                {row.hop && <span className="ml-2 font-normal text-muted">{row.hop}</span>}
              </p>
              <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 px-2.5 py-2 text-[11px]">
                {LEGS.map((leg) => {
                  const value = leg.key === 'repo' ? '' : (row[leg.key] ?? '')
                  return (
                    <div key={leg.label} className="col-span-2 grid grid-cols-subgrid">
                      <dt className="text-muted">{leg.label}</dt>
                      <dd className="font-mono text-text">
                        {value ? (
                          value
                        ) : leg.modelled ? (
                          // The graph could hold this and does not.
                          <span className="text-yellow">not found via {SPEC_ID}</span>
                        ) : (
                          // The ontology has no label for this at all — a
                          // different statement, said differently.
                          <span className="text-muted">
                            not modelled — no :CodeRepo label exists in the ontology, so no load
                            would supply this. Minting one is a gate decision.
                          </span>
                        )}
                      </dd>
                    </div>
                  )
                })}
              </dl>
            </section>
          ))}
        </div>
      )}

      {rows === null && !error && (
        <div className="min-h-0 flex-1 overflow-auto">
          <EmptyState
            title="Search a file or table name"
            hint="The report names the owning application, the process, the Control-M folder and the dev team to escalate to."
          />
        </div>
      )}

      <details className="shrink-0 rounded-md border border-edge px-2.5 py-1 text-[10px] text-muted">
        <summary className="cursor-pointer select-none">
          which source asserted each row ({SOURCE_LEGEND.length})
        </summary>
        <table className="mt-1 w-full border-collapse">
          <thead>
            <tr>
              <th className={TH}>Column</th>
              <th className={TH}>Node label</th>
              <th className={TH}>Asserted by</th>
            </tr>
          </thead>
          <tbody>
            {SOURCE_LEGEND.map((l) => (
              <tr key={l.column}>
                <td className={TD}>{l.column}</td>
                <td className={`${TD} font-mono text-[10px]`}>{l.label}</td>
                <td className={`${TD} text-[10px] text-muted`}>{l.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}
