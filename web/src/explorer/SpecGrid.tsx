import { useMemo, useState, type ReactNode } from 'react'
import { useGraphAccess } from '../data/graphAccess'
import { useLiveOrDemo } from '../data/provenance'
import ProvenanceNotice from '../components/ProvenanceNotice'
import EmptyState from '../components/ui/EmptyState'
import TruncationBadge from '../components/ui/TruncationBadge'

// A QuerySpec-bound data frame (O11, site-plan §4): renders ONLY registry
// results — the UI never invents Cypher. Ships both export paths:
//   (a) client-side CSV/JSON of the CURRENT grid state (visible rows after
//       filtering) + a client-built sidecar manifest, and
//   (b) the server export: drydocs-api re-runs the spec and streams the full
//       result; the provenance manifest sidecar downloads alongside it.
// Classification banner renders for internal tiers; ddcontext/ddall results
// arrive pre-watermarked (trust_watermark column). "Copy as Cypher" exposes
// the spec's exact query + params — what you see is provably reproducible.
//
// On load failure (api down, DB empty) the frame falls back to the SYNTHESIZED
// demo grid passed as `fallback` — with a visible notice, never silently.
//
// WEB2 — THE ROW CEILING IS NOW VISIBLE, AND THE EXPORT STOPS CLAIMING "full".
// Every spec carries `limit`, default 500. A 900-row answer arrived as 500 rows
// and rendered `500/500 · drydocs · LIVE`, indistinguishable from a complete
// one; then the button labelled "⬇ CSV (full)" replayed the echoed params —
// which contain that same limit — and filed a governance manifest with
// `row_count: 500` and nothing saying the extract was partial. The canvas next
// door had solved exactly this for its node ceiling since O81. So the badge is
// the canvas's badge (components/ui/TruncationBadge), the label states the
// ceiling instead of claiming completeness, and the ceiling is raisable where
// API1 made it raisable.
//
// COMPLETENESS IS READ, NEVER INFERRED. `result.truncated` comes from the
// server's limit+1 probe; `rows.length === limit` is a guess that is wrong in
// both directions — a result of exactly 500 rows is complete about as often as
// not, and a filtered view has a different length again.

interface SpecGridProps {
  specId: string
  fallback: ReactNode
}

// WEB12 dropped the `access` prop. Sixteen call sites passed a GraphAccess
// their route had built, which is how the per-route client became a per-route
// obligation; the frame reads the session's one client from context instead.

// This frame's demo data is a ReactNode prop, not rows, so the seam is handed a
// non-empty marker: it decides PROVENANCE, and the node itself is rendered here.
// (SpecGrid is the one consumer shaped this way; every other call site passes
// its real demo rows.)
const DEMO_PRESENT: readonly Record<string, unknown>[] = []

function download(filename: string, content: Blob | string, type = 'text/plain') {
  const blob = typeof content === 'string' ? new Blob([content], { type }) : content
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function toCsv(keys: string[], rows: Record<string, unknown>[]): string {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
  }
  return [keys.join(','), ...rows.map((r) => keys.map((k) => esc(r[k])).join(','))].join('\n') + '\n'
}

/** A manifest field, when the manifest really carries it as that type.
 *
 *  The export manifest stays a free object across the seam (SpecExport) because
 *  it is a ledger record, not a typed payload — so the status line narrows in
 *  place rather than the seam pretending to a shape the schema does not
 *  declare. A manifest without `truncated` is an OLDER manifest, and the status
 *  line then says only what that manifest actually says. */
function manifestNumber(m: Record<string, unknown>, key: string): number | null {
  const v = m[key]
  return typeof v === 'number' ? v : null
}

/** The hover text for the two server-export buttons. The old one said only
 *  "re-runs the spec, streams + manifest", which is true and was the problem:
 *  it described the mechanism while the label made a claim about the content. */
function serverExportTitle(truncated: boolean, ceiling: number | null): string {
  const base = 'Server export — re-runs the spec, streams + manifest'
  if (!truncated) return `${base}. The result fits under the ceiling, so this is every row.`
  return ceiling === null
    ? `${base}. The result is capped, so this is a PARTIAL extract and the manifest records that.`
    : `${base}. Capped at ${ceiling} rows — a PARTIAL extract, and the manifest records the cap.`
}

/** Clause (b)'s second half: after the export, say what was exported — and, if
 *  it was capped, say so with the ceiling. The manifest is the authority here
 *  rather than the run result, because the manifest is the artifact that gets
 *  filed alongside the data and it is the one the reader can re-check. */
function exportSummary(manifest: Record<string, unknown>): string {
  const rows = manifestNumber(manifest, 'row_count')
  const count = rows === null ? 'the' : `${rows}`
  const truncated = manifest.truncated
  if (typeof truncated !== 'boolean') return `exported ${count} rows`
  const limit = manifestNumber(manifest, 'limit')
  if (!truncated) return `exported ${count} rows — complete`
  return limit === null
    ? `exported ${count} rows — CAPPED; the result has more`
    : `exported ${count} rows — CAPPED at ${limit}; the result has more`
}

export default function SpecGrid({ specId, fallback }: SpecGridProps) {
  const { access } = useGraphAccess()
  const [filter, setFilter] = useState('')
  const [status, setStatus] = useState('')
  // API1 clause (c)'s raisable ceiling, as typed. Held as the raw string so the
  // field can be empty (= "use the display ceiling") and so a half-typed number
  // is never sent; parsed at the call.
  const [raiseTo, setRaiseTo] = useState('')

  // WEB1: the ONE provenance seam. `fallback` is this frame's synthetic demo
  // node, so the seam is told there IS a demo and reports `demo` rather than
  // `empty`/`error` — the same policy this frame already had, now stated once
  // and counted where an operator can see it.
  const provenance = useLiveOrDemo<Record<string, unknown>>(specId, DEMO_PRESENT)
  // Nullable only for the filter memo, which runs before the guards below (a
  // hook cannot be called conditionally). Past the guards the result is live.
  const loaded = provenance.status === 'live' ? provenance.data : null

  const visible = useMemo(() => {
    if (!loaded) return []
    if (!filter) return loaded.rows
    const needle = filter.toLowerCase()
    return loaded.rows.filter((r) =>
      loaded.keys.some((k) => String(r[k] ?? '').toLowerCase().includes(needle)),
    )
  }, [loaded, filter])

  if (provenance.status === 'loading') {
    return <EmptyState title="Loading…" hint={`Running QuerySpec ${specId} via drydocs-api.`} />
  }
  if (provenance.status !== 'live') {
    return (
      <div className="flex h-full min-h-0 flex-col gap-2">
        <ProvenanceNotice state={provenance} specId={specId} />
        {provenance.status === 'demo' && <div className="min-h-0 flex-1">{fallback}</div>}
      </div>
    )
  }

  const result = provenance.data

  // `internal` is the most restrictive level in the vocabulary — J23 collapsed
  // the former fourth tier into it (2026-07-31).
  const isInternal = result.classification === 'internal'

  // The ceiling that governed the rows on screen. Null only for a spec with no
  // limit at all, which is also a spec that cannot be truncated.
  const displayLimit = result.limit ?? null
  // R4: an ephemeral spec replays params frozen at registration, so the server
  // refuses to re-ceiling it. The seam carries the server's own answer; the
  // console does not re-derive the rule from the id.
  const canRaise = result.truncated && !result.ephemeral
  const raised = canRaise && /^\d+$/.test(raiseTo) && Number(raiseTo) > 0 ? Number(raiseTo) : null
  // What the next export will be capped at, as far as the console can know.
  const exportCeiling = raised ?? displayLimit

  /** Clause (b): the button never says "full" unless the result on screen says
   *  it is complete. Where it is not, the label states the ceiling — a number
   *  the reader can check against the file they get — rather than a promise. */
  function exportLabel(format: 'CSV' | 'JSONL'): string {
    if (!result.truncated) return `⬇ ${format} (full)`
    return exportCeiling === null
      ? `⬇ ${format} (capped)`
      : `⬇ ${format} (first ${exportCeiling} rows)`
  }

  async function serverExport(format: 'csv' | 'jsonl') {
    setStatus(`exporting ${format}…`)
    try {
      // `raised` and not `exportCeiling`: omitting the field asks for the
      // server's default, which IS the display ceiling. Sending it back
      // explicitly would turn every export into a raise request, and the server
      // rejects a raise on an ephemeral spec — so the untouched case would
      // start failing on the surface it never applied to.
      const { filename, blob, manifest } = await access.exportSpec(specId, result.params, format, {
        limit: raised,
      })
      download(filename, blob)
      download(`${filename}.manifest.json`, JSON.stringify(manifest, null, 2), 'application/json')
      setStatus(exportSummary(manifest))
    } catch (e) {
      // The server's refusal verbatim — it names its own ceiling and its own
      // R4 rule, and a second copy of either in the browser would be a second
      // source of truth for a server decision.
      setStatus(`export failed: ${(e as Error).message}`)
    }
  }

  function clientExport(format: 'csv' | 'json') {
    const r = result!
    // same filename-prefix rule as the server path (exports.py filename_for)
    const prefix = isInternal ? `${r.classification.toUpperCase()}__` : ''
    const name = `${prefix}${r.spec_id}.view.${format}`
    const data = format === 'csv' ? toCsv(r.keys, visible) : JSON.stringify(visible, null, 2) + '\n'
    download(name, data, format === 'csv' ? 'text/csv' : 'application/json')
    // client-side sidecar: same spec provenance, view-scoped row count
    download(
      `${name}.manifest.json`,
      JSON.stringify(
        {
          query_spec: r.spec_id,
          params: r.params,
          database: r.database,
          classification: r.classification,
          row_count: visible.length,
          scope: 'client-view (current grid state — filtered rows only)',
          // The client sidecar is a governance artifact too, and it was the
          // one place the cap could hide completely: a filtered view of a
          // capped result is twice removed from the answer, and its row_count
          // says nothing about either. These name the RESULT the view was cut
          // from, which is why they are not called row_count.
          truncated: r.truncated,
          limit: r.limit ?? null,
          trust_tiers_present: r.watermarked ? ['SYNTHESIZED'] : [],
          exported_at: new Date().toISOString(),
        },
        null,
        2,
      ),
      'application/json',
    )
  }

  function copyAsCypher() {
    const text = `// QuerySpec ${result!.spec_id} · database ${result!.database}\n// params: ${JSON.stringify(result.params)}\n${result!.cypher}\n`
    navigator.clipboard.writeText(text).then(
      () => setStatus('Cypher copied'),
      () => setStatus('clipboard unavailable'),
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      {isInternal && (
        <p className="shrink-0 rounded border border-red/60 bg-red/10 px-2 py-1 font-mono text-[10px] text-brand-soft">
          {result.classification.toUpperCase()} — not for redistribution (PUBLISH-BOUNDARY.md); exports carry the
          filename prefix + manifest
        </p>
      )}
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
          {visible.length}/{result.rows.length} · {result.database} · LIVE
        </span>
        {/* Clause (a): the canvas's badge, beside the canvas's count line, in
            the canvas's words. `total` is null because the grid genuinely does
            not know N — the server probed one row past the ceiling, which
            answers "there is more" and not "how much more". */}
        {result.truncated && (
          <TruncationBadge
            shown={result.rows.length}
            total={null}
            unit="rows"
            title={
              displayLimit === null
                ? 'This result was capped by the server; there are more rows than are on screen.'
                : `Capped at ${displayLimit} rows; there are more. The count above is of what arrived, not of what exists.`
            }
          />
        )}
        {canRaise && (
          // Clause (c): where API1 made the ceiling raisable, offer it — and
          // let the SERVER refuse a value it will not honour. The console holds
          // no copy of EXPORT_LIMIT_CEILING, so the two cannot drift.
          <label className="flex items-center gap-1 font-mono text-[10px] text-muted">
            export up to
            <input
              type="number"
              min={1}
              step={1}
              value={raiseTo}
              onChange={(e) => setRaiseTo(e.target.value)}
              placeholder={displayLimit === null ? '' : String(displayLimit)}
              aria-label="Export row ceiling"
              title="Raise the ceiling for the server export only — the rows on screen are unaffected. The server refuses a value above its own limit and says what that limit is."
              className="w-24 text-xs"
            />
          </label>
        )}
        {result.truncated && result.ephemeral && (
          // Clause (c)'s other half: say WHY it cannot be raised rather than
          // offering a control that will 422.
          <span
            className="font-mono text-[10px] text-yellow"
            title="R4: an ephemeral spec is registered by the agent with its params frozen, which is what makes the answer replayable. Rewriting its ceiling would change the query the transcript cites."
          >
            ceiling frozen at registration (R4)
          </span>
        )}
        <span className="ml-auto flex items-center gap-1">
          <GridButton label="CSV" title="Client export — current grid state" onClick={() => clientExport('csv')} />
          <GridButton label="JSON" title="Client export — current grid state" onClick={() => clientExport('json')} />
          <GridButton
            label={exportLabel('CSV')}
            title={serverExportTitle(result.truncated, exportCeiling)}
            onClick={() => serverExport('csv')}
          />
          <GridButton
            label={exportLabel('JSONL')}
            title={serverExportTitle(result.truncated, exportCeiling)}
            onClick={() => serverExport('jsonl')}
          />
          <GridButton label="Copy as Cypher" title="The spec's exact query + params" onClick={copyAsCypher} />
        </span>
      </div>
      {status && <p className="shrink-0 font-mono text-[10px] text-muted">{status}</p>}

      {visible.length === 0 ? (
        <EmptyState title="No rows" hint="The database returned nothing for this spec (or the filter excludes everything)." />
      ) : (
        <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="sticky top-0 bg-panel-2">
              <tr>
                {result.keys.map((k) => (
                  <th key={k} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                    {result.columns.find((c) => c.name === k)?.label ?? k}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((r, i) => (
                <tr key={i} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  {result.keys.map((k) => (
                    <td
                      key={k}
                      className={
                        'border-b border-edge-soft px-2.5 py-1.5 ' +
                        (k === 'trust_watermark' ? 'font-mono text-[10px] text-yellow' : 'text-text')
                      }
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
