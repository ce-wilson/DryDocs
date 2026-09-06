import { useMemo, useState, type ReactNode } from 'react'
import { useGraphAccess } from '../data/graphAccess'
import { useLiveOrDemo } from '../data/provenance'
import ProvenanceNotice from '../components/ProvenanceNotice'
import EmptyState from '../components/ui/EmptyState'

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

export default function SpecGrid({ specId, fallback }: SpecGridProps) {
  const { access } = useGraphAccess()
  const [filter, setFilter] = useState('')
  const [status, setStatus] = useState('')

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

  async function serverExport(format: 'csv' | 'jsonl') {
    setStatus(`exporting ${format}…`)
    try {
      const { filename, blob, manifest } = await access.exportSpec(specId, result.params, format)
      download(filename, blob)
      download(`${filename}.manifest.json`, JSON.stringify(manifest, null, 2), 'application/json')
      setStatus(`exported ${manifest.row_count} rows`)
    } catch (e) {
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
        <span className="ml-auto flex items-center gap-1">
          <GridButton label="CSV" title="Client export — current grid state" onClick={() => clientExport('csv')} />
          <GridButton label="JSON" title="Client export — current grid state" onClick={() => clientExport('json')} />
          <GridButton label="⬇ CSV (full)" title="Server export — re-runs the spec, streams + manifest" onClick={() => serverExport('csv')} />
          <GridButton label="⬇ JSONL (full)" title="Server export — re-runs the spec, streams + manifest" onClick={() => serverExport('jsonl')} />
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
