import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import {
  createMappingsApi,
  type ChangesetArtifact,
  type MappingDomain,
  type MappingGrid,
  type MappingOptions,
} from '../lib/mappingsApi'
import type { SpecResult } from '../lib/graph'
import { DEMO_COVERAGE, type CoverageRow } from '../data/mappingsDemo'
import ModuleToolbar from '../layout/ModuleToolbar'
import EmptyState from '../components/ui/EmptyState'

// /mappings — the O13 manual-mapping stewardship screen (wf-mapping-01).
// Steward + admin only (server-enforced too — /mappings/* returns 403 below
// steward). THE ONE RULE THAT SHAPES EVERYTHING: the loader stays the ONLY
// graph writer. Assigning drafts entries into a per-user changeset tray;
// submit produces a config/manual-loads/ change ARTIFACT (CSV + manifest
// snippet download) that travels git → K2 gate → merge → next load run.
// Zero graph writes happen here.

const COVERAGE_SPEC = 'mappings.attribution-coverage.v1'
const APP_SPEC = 'explorer.applications.v1'

type Queue = 'all' | 'unresolved' | 'conflict'
type Lifecycle = 'draft' | 'submitted' | 'gated' | 'loaded'

interface TrayEntry {
  key: string // folder_id:job_id
  folder_id: string
  job_id: string
  jobLabel: string
  seal_id: string
  rationale: string
  createTarget: boolean
  authoredAt: string
  lifecycle: Exclude<Lifecycle, 'loaded'> // 'loaded' is DERIVED from the grid, never stored
}

// Fallback registry mirror (drydocs_api/mappings.py DOMAINS) so the strip
// renders with a visible notice when the api is down — never silently.
const FALLBACK_DOMAINS: MappingDomain[] = [
  { id: 'ontology-map', title: 'Taxonomy ↔ Ontology map (the loading quintuple)', kind: 'quintuple', source: 'config/taxonomy-ontology-map.yaml', tier: null, available: true },
  { id: 'job-application', title: 'Job → Application (tier-5 manual CSV)', kind: 'manual', source: 'config/manual-loads/', tier: 5, available: true },
  { id: 'fid-seal', title: 'FID → seal_id (tier 2)', kind: 'manual', source: '(K6/T2 — reconciler table not built yet)', tier: 2, available: false },
  { id: 'alias-seal', title: 'ALIAS → seal_id (tier 4)', kind: 'manual', source: '(T3 — reconciler table not built yet)', tier: 4, available: false },
]

function trayStorageKey(personaId: string): string {
  return `drydocs.mappings.tray.v1.${personaId}`
}

function loadTray(personaId: string): TrayEntry[] {
  try {
    const raw = localStorage.getItem(trayStorageKey(personaId))
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? (parsed as TrayEntry[]) : []
  } catch {
    return []
  }
}

function download(filename: string, content: string, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function MappingsRoute({ persona }: { persona: Persona }) {
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const mappings = useMemo(() => createMappingsApi(apiUrl, persona.id), [apiUrl, persona.id])
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  const [apiDown, setApiDown] = useState<string | null>(null)
  const [domains, setDomains] = useState<MappingDomain[]>(FALLBACK_DOMAINS)
  const [activeDomain, setActiveDomain] = useState('job-application')
  const [options, setOptions] = useState<MappingOptions | null>(null)

  // coverage grid (job-application domain)
  const [coverage, setCoverage] = useState<CoverageRow[] | null>(null)
  const [coverageLive, setCoverageLive] = useState(false)
  const [queue, setQueue] = useState<Queue>('all')
  const [filter, setFilter] = useState('')
  const [checked, setChecked] = useState<ReadonlySet<string>>(new Set())

  // domain entry grids (manual CSV rows / ontology map), fetched per domain
  const [domainGrid, setDomainGrid] = useState<MappingGrid | null>(null)

  // changeset tray — persisted per-user (wf-mapping-01 annotation 4)
  const [tray, setTray] = useState<TrayEntry[]>(() => loadTray(persona.id))
  useEffect(() => {
    localStorage.setItem(trayStorageKey(persona.id), JSON.stringify(tray))
  }, [tray, persona.id])

  const [assignOpen, setAssignOpen] = useState(false)
  const [status, setStatus] = useState('')
  const [artifact, setArtifact] = useState<ChangesetArtifact | null>(null)

  useEffect(() => {
    let cancelled = false
    mappings
      .domains()
      .then((d) => {
        if (cancelled) return
        setDomains(d)
        setApiDown(null)
      })
      .catch((e: Error) => {
        if (!cancelled) setApiDown(e.message)
      })
    mappings
      .options()
      .then((o) => {
        if (!cancelled) setOptions(o)
      })
      .catch(() => {
        /* options footer just stays empty — the apiDown notice already shows */
      })
    return () => {
      cancelled = true
    }
  }, [mappings])

  useEffect(() => {
    let cancelled = false
    setCoverage(null)
    setCoverageLive(false)
    access
      .runSpec(COVERAGE_SPEC)
      .then((r: SpecResult) => {
        if (cancelled) return
        if (r.rows.length > 0) {
          setCoverage(r.rows as unknown as CoverageRow[])
          setCoverageLive(true)
        } else {
          setCoverage([...DEMO_COVERAGE]) // empty graph → demo frame, with notice
        }
      })
      .catch(() => {
        if (!cancelled) setCoverage([...DEMO_COVERAGE])
      })
    return () => {
      cancelled = true
    }
  }, [access])

  useEffect(() => {
    let cancelled = false
    setDomainGrid(null)
    const available = domains.find((d) => d.id === activeDomain)?.available
    if (!available) return
    mappings
      .grid(activeDomain)
      .then((g) => {
        if (!cancelled) setDomainGrid(g)
      })
      .catch(() => {
        /* grid stays null → its section shows the api-down hint */
      })
    return () => {
      cancelled = true
    }
  }, [mappings, activeDomain, domains])

  const visible = useMemo(() => {
    if (!coverage) return []
    let rows = coverage
    if (queue !== 'all') rows = rows.filter((r) => r.status === queue)
    if (filter) {
      const needle = filter.toLowerCase()
      rows = rows.filter((r) =>
        [r.folder, r.job, r.seal_id, r.application, r.match_method, r.status].some((v) =>
          String(v ?? '').toLowerCase().includes(needle),
        ),
      )
    }
    return rows
  }, [coverage, queue, filter])

  const rowKey = (r: CoverageRow) => `${r.folder_id}:${r.job_id}`
  const checkedRows = useMemo(
    () => (coverage ?? []).filter((r) => checked.has(rowKey(r))),
    [coverage, checked],
  )

  const toggleChecked = useCallback((key: string) => {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  // 'loaded' self-verification (wf-mapping-01 annotation 6): a submitted entry
  // whose job now resolves at tier `manual` in the LIVE grid has been applied
  // by a load run — the screen verifies against the graph, not its own state.
  const derivedLifecycle = useCallback(
    (e: TrayEntry): Lifecycle => {
      if (e.lifecycle !== 'draft' && coverageLive) {
        const row = (coverage ?? []).find((r) => rowKey(r) === e.key)
        if (row?.match_method === 'manual' && row.seal_id === e.seal_id) return 'loaded'
      }
      return e.lifecycle
    },
    [coverage, coverageLive],
  )

  function addDrafts(sealId: string, rationale: string, createTarget: boolean) {
    const authoredAt = new Date().toISOString()
    setTray((prev) => {
      const next = [...prev]
      for (const r of checkedRows) {
        const key = rowKey(r)
        const entry: TrayEntry = {
          key,
          folder_id: r.folder_id,
          job_id: r.job_id,
          jobLabel: `${r.folder}/${r.job}`,
          seal_id: sealId,
          rationale,
          createTarget,
          authoredAt,
          lifecycle: 'draft',
        }
        const i = next.findIndex((e) => e.key === key && e.lifecycle === 'draft')
        if (i >= 0) next[i] = entry
        else next.push(entry)
      }
      return next
    })
    setChecked(new Set())
    setAssignOpen(false)
    setStatus(`${checkedRows.length} draft${checkedRows.length === 1 ? '' : 's'} added to the changeset tray`)
  }

  async function submitChangeset() {
    const drafts = tray.filter((e) => e.lifecycle === 'draft')
    if (drafts.length === 0) return
    setStatus('submitting…')
    try {
      const art = await mappings.draftChangeset(
        drafts.map((e) => ({
          folder_id: e.folder_id,
          job_id: e.job_id,
          seal_id: e.seal_id,
          rationale: e.rationale,
          create_target_if_missing: e.createTarget,
        })),
      )
      download(art.filename, art.csv, 'text/csv')
      download(`${art.filename}.manifest-snippet.yaml`, art.manifest_snippet, 'text/yaml')
      setArtifact(art)
      setTray((prev) => prev.map((e) => (e.lifecycle === 'draft' ? { ...e, lifecycle: 'submitted' } : e)))
      setStatus(`change artifact ${art.filename} downloaded (${art.entries} entries) — the server wrote NOTHING`)
    } catch (e) {
      setStatus(`submit failed: ${(e as Error).message}`)
    }
  }

  const activeDef = domains.find((d) => d.id === activeDomain)

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar
        crumbs={[
          { label: 'Home', to: '/' },
          { label: 'Mappings' },
          ...(activeDef ? [{ label: activeDef.title.split(' (')[0] }] : []),
        ]}
        actions={
          <span className="font-mono text-[10px] text-faint" title="wf-mapping-01's one rule">
            zero graph writes — artifact → git → K2 gate → loader
          </span>
        }
      />

      <div className="px-4 pt-3">
        <h2 tabIndex={-1} data-view-heading className="text-lg font-semibold text-text outline-none">
          Mappings
          <span className="ml-2 rounded border border-edge px-1.5 py-0.5 align-middle font-mono text-[10px] text-muted">
            {persona.role === 'steward' ? 'steward' : 'admin'}
          </span>
        </h2>
        <p className="mt-0.5 text-xs text-faint">
          Manual mapping stewardship · drafts travel the change-artifact path; the loader stays the only graph writer
        </p>
      </div>

      {apiDown && (
        <p className="mx-4 mt-2 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 text-[11px] text-yellow">
          drydocs-api unavailable ({apiDown.split('—')[0].trim()}) — domain registry and coverage are the SYNTHESIZED
          demo set; drafting still works, submit needs the api.
        </p>
      )}

      {/* Domain strip — registry-driven (wf-mapping-01 annotation 1) */}
      <div className="flex flex-wrap items-center gap-1.5 px-4 pt-3" role="tablist" aria-label="Mapping domains">
        {domains.map((d) => (
          <button
            key={d.id}
            type="button"
            role="tab"
            aria-selected={d.id === activeDomain}
            disabled={!d.available}
            onClick={() => setActiveDomain(d.id)}
            title={d.source}
            className={
              'rounded-md border px-2.5 py-1 text-xs font-medium ' +
              (d.id === activeDomain
                ? 'border-brand bg-panel-2 text-text'
                : d.available
                  ? 'border-edge bg-bg-2 text-muted hover:text-text'
                  : 'cursor-not-allowed border-edge-soft text-faint')
            }
          >
            {d.title.split(' (')[0]}
            {d.tier !== null && <span className="ml-1 font-mono text-[10px]">t{d.tier}</span>}
            {!d.available && <span className="ml-1 text-[10px]">(not built)</span>}
          </button>
        ))}
      </div>

      <div className="flex min-h-0 flex-1 gap-3 p-4">
        {/* main pane */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2 overflow-hidden rounded-lg border border-edge bg-panel p-3">
          {activeDomain === 'job-application' ? (
            <>
              <p className="shrink-0 rounded border border-red/60 bg-red/10 px-2 py-1 font-mono text-[10px] text-brand-soft">
                INTERNAL — attribution coverage (PUBLISH-BOUNDARY.md)
              </p>
              <div className="flex shrink-0 flex-wrap items-center gap-1.5">
                {(['all', 'unresolved', 'conflict'] as const).map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQueue(q)}
                    className={
                      'rounded-md border px-2 py-0.5 text-[11px] font-medium ' +
                      (queue === q ? 'border-brand bg-panel-2 text-text' : 'border-edge bg-bg-2 text-muted hover:text-text')
                    }
                  >
                    {q === 'all' ? 'all rows' : `${q} queue`}
                    {coverage && q !== 'all' && (
                      <span className="ml-1 font-mono text-[10px]">
                        {coverage.filter((r) => r.status === q).length}
                      </span>
                    )}
                  </button>
                ))}
                <input
                  type="search"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder="Filter jobs…"
                  aria-label="Filter jobs"
                  className="w-40 text-xs"
                />
                <span className="font-mono text-[10px] text-faint">
                  {visible.length}/{coverage?.length ?? 0} · {coverageLive ? 'LIVE' : 'SYNTHESIZED demo'}
                </span>
                <button
                  type="button"
                  disabled={checkedRows.length === 0}
                  onClick={() => setAssignOpen(true)}
                  className="ml-auto rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-medium text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
                >
                  Assign to application… ({checkedRows.length})
                </button>
              </div>

              {!coverage ? (
                <EmptyState title="Loading…" hint={`Running QuerySpec ${COVERAGE_SPEC} via drydocs-api.`} />
              ) : visible.length === 0 ? (
                <EmptyState title="No rows in this queue" hint="Nothing matches the current queue/filter." />
              ) : (
                <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
                  <table className="w-full border-collapse text-left text-xs">
                    <thead className="sticky top-0 bg-panel-2">
                      <tr>
                        <th className="border-b border-edge px-2 py-1.5" aria-label="select" />
                        {['Folder', 'Job', 'Current app', 'Tier/evidence', 'Status'].map((h) => (
                          <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((r, i) => {
                        const key = rowKey(r)
                        return (
                          <tr key={key} className={i % 2 ? 'bg-bg-2/40' : ''}>
                            <td className="border-b border-edge-soft px-2 py-1.5">
                              <input
                                type="checkbox"
                                checked={checked.has(key)}
                                onChange={() => toggleChecked(key)}
                                aria-label={`select ${r.folder}/${r.job}`}
                              />
                            </td>
                            <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{r.folder}</td>
                            <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{r.job}</td>
                            <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">
                              {r.seal_id ? `${r.seal_id}${r.application ? ` · ${r.application}` : ''}` : '—'}
                            </td>
                            <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-muted">
                              {r.match_method ?? '—'}
                            </td>
                            <td className="border-b border-edge-soft px-2.5 py-1.5">
                              <StatusChip status={r.status} />
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* current manual entries for this domain (mapping.db read) */}
              <details className="shrink-0">
                <summary className="cursor-pointer text-[11px] font-medium text-muted">
                  Current manual entries (config/manual-loads/ · mapping.db)
                </summary>
                <DomainGridTable grid={domainGrid} apiDown={apiDown} />
              </details>
            </>
          ) : (
            <>
              <p className="shrink-0 text-[11px] text-muted">
                {activeDef?.title} — read-only view of the committed source ({activeDef?.source}), served from the
                mapping-store materialization.
              </p>
              <DomainGridTable grid={domainGrid} apiDown={apiDown} />
            </>
          )}

          {options && (
            <p className="shrink-0 border-t border-edge-soft pt-1.5 font-mono text-[10px] text-faint">
              vocabulary status (mapping.db):{' '}
              {options.status_summary.map((s) => `${s.status} ${s.n}`).join(' · ')}
            </p>
          )}
        </div>

        {/* changeset tray */}
        <aside className="flex w-64 shrink-0 flex-col gap-2 overflow-hidden rounded-lg border border-edge bg-panel p-3">
          <h3 className="shrink-0 text-sm font-semibold text-text">Changeset tray</h3>
          <p className="shrink-0 text-[10px] text-faint">
            Per-user drafts · lifecycle draft → submitted → gated → loaded; “loaded” is self-verified by the coverage
            grid flipping the job's tier to manual.
          </p>
          {tray.length === 0 ? (
            <EmptyState title="No drafts" hint="Select unresolved rows and assign an application." />
          ) : (
            <ul className="min-h-0 flex-1 space-y-1.5 overflow-y-auto">
              {tray.map((e) => {
                const lc = derivedLifecycle(e)
                return (
                  <li key={`${e.key}:${e.authoredAt}`} className="rounded-md border border-edge-soft bg-bg-2/40 p-2 text-[11px]">
                    <div className="flex items-center justify-between gap-1">
                      <span className="truncate font-medium text-text" title={e.jobLabel}>
                        {e.jobLabel}
                      </span>
                      <LifecycleChip lifecycle={lc} />
                    </div>
                    <div className="mt-0.5 font-mono text-[10px] text-muted">→ {e.seal_id}</div>
                    <div className="mt-0.5 truncate text-[10px] text-faint" title={e.rationale}>
                      {e.rationale}
                    </div>
                    <div className="mt-1 flex gap-1">
                      {lc === 'draft' && (
                        <button
                          type="button"
                          onClick={() => setTray((prev) => prev.filter((x) => x !== e))}
                          className="rounded border border-edge px-1.5 py-0.5 text-[10px] text-muted hover:text-text"
                        >
                          remove
                        </button>
                      )}
                      {lc === 'submitted' && (
                        <button
                          type="button"
                          title="Bookkeeping: mark after the K2 gate reviews the PR"
                          onClick={() =>
                            setTray((prev) => prev.map((x) => (x === e ? { ...x, lifecycle: 'gated' } : x)))
                          }
                          className="rounded border border-edge px-1.5 py-0.5 text-[10px] text-muted hover:text-text"
                        >
                          mark gated
                        </button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
          <button
            type="button"
            disabled={tray.every((e) => e.lifecycle !== 'draft')}
            onClick={submitChangeset}
            title="Downloads the config/manual-loads/ CSV + manifest snippet — commit it, gate it, next load run applies it"
            className="shrink-0 rounded-md border border-brand bg-panel-2 px-2.5 py-1.5 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Submit changeset (download artifact)
          </button>
          {status && <p className="shrink-0 font-mono text-[10px] text-muted">{status}</p>}
          {artifact && (
            <p className="shrink-0 rounded border border-edge-soft bg-bg-2/40 p-1.5 text-[10px] text-faint">
              {artifact.note}
            </p>
          )}
        </aside>
      </div>

      {assignOpen && (
        <AssignDialog
          rows={checkedRows}
          access={access}
          onCancel={() => setAssignOpen(false)}
          onAssign={addDrafts}
        />
      )}
    </div>
  )
}

function StatusChip({ status }: { status: CoverageRow['status'] }) {
  const cls =
    status === 'resolved'
      ? 'border-edge text-muted'
      : status === 'conflict'
        ? 'border-yellow/60 text-yellow'
        : 'border-red/60 text-brand-soft'
  return <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${cls}`}>{status}</span>
}

function LifecycleChip({ lifecycle }: { lifecycle: Lifecycle }) {
  const cls =
    lifecycle === 'loaded'
      ? 'border-brand text-text'
      : lifecycle === 'draft'
        ? 'border-edge text-muted'
        : 'border-edge-soft text-faint'
  return <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${cls}`}>{lifecycle}</span>
}

function DomainGridTable({ grid, apiDown }: { grid: MappingGrid | null; apiDown: string | null }) {
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
  return (
    <div className="mt-1.5 max-h-48 overflow-auto rounded-md border border-edge">
      <table className="w-full border-collapse text-left text-[11px]">
        <thead className="sticky top-0 bg-panel-2">
          <tr>
            {grid.keys.map((k) => (
              <th key={k} className="border-b border-edge px-2 py-1 font-semibold text-muted">
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.rows.map((r, i) => (
            <tr key={i} className={i % 2 ? 'bg-bg-2/40' : ''}>
              {grid.keys.map((k) => (
                <td key={k} className="border-b border-edge-soft px-2 py-1 text-text">
                  {String(r[k] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface AppOption {
  seal_id: string
  name: string
}

function AssignDialog({
  rows,
  access,
  onCancel,
  onAssign,
}: {
  rows: CoverageRow[]
  access: ReturnType<typeof createApiAccess>
  onCancel: () => void
  onAssign: (sealId: string, rationale: string, createTarget: boolean) => void
}) {
  const [apps, setApps] = useState<AppOption[] | null>(null)
  const [search, setSearch] = useState('')
  const [sealId, setSealId] = useState('')
  const [rationale, setRationale] = useState('')
  const [createTarget, setCreateTarget] = useState(false)

  useEffect(() => {
    let cancelled = false
    access
      .runSpec(APP_SPEC)
      .then((r) => {
        if (!cancelled) setApps(r.rows as unknown as AppOption[])
      })
      .catch(() => {
        if (!cancelled) setApps([]) // picker degrades to free-text seal_id entry
      })
    return () => {
      cancelled = true
    }
  }, [access])

  const matches = useMemo(() => {
    if (!apps) return []
    const needle = search.toLowerCase()
    return apps
      .filter((a) => !needle || a.seal_id?.toLowerCase().includes(needle) || a.name?.toLowerCase().includes(needle))
      .slice(0, 8)
  }, [apps, search])

  // K2 precedence honesty (wf-mapping-01 open item 2, resolved conservatively):
  // manual is tier 5 — it never overrides SEAL evidence; say so up front.
  const alreadyResolved = rows.filter((r) => r.status === 'resolved')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Assign to application">
      <div className="w-[28rem] max-w-[90vw] rounded-lg border border-edge bg-panel p-4 shadow-xl">
        <h3 className="text-sm font-semibold text-text">
          Assign {rows.length} job{rows.length === 1 ? '' : 's'} to an application
        </h3>
        <p className="mt-1 rounded border border-edge-soft bg-bg-2/40 p-2 text-[11px] text-muted">
          Manual mappings are <strong>tier 5</strong> — the lowest precedence. A manual entry never overrides SEAL
          evidence (K2 match policy).
        </p>
        {alreadyResolved.length > 0 && (
          <p className="mt-1.5 rounded border border-yellow/50 bg-yellow/10 p-2 text-[11px] text-yellow">
            {alreadyResolved.length} selected job{alreadyResolved.length === 1 ? ' already resolves' : 's already resolve'} at a
            higher tier — a manual entry will NOT override {alreadyResolved.length === 1 ? 'it' : 'them'}.
          </p>
        )}

        <label className="mt-3 block text-xs font-medium text-muted">
          Target BusinessApplication (search seal_id / name)
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={apps && apps.length === 0 ? 'app list unavailable — enter seal_id below' : 'Search…'}
            className="mt-1 w-full text-xs"
          />
        </label>
        {matches.length > 0 && (
          <ul className="mt-1 max-h-32 overflow-y-auto rounded-md border border-edge">
            {matches.map((a) => (
              <li key={a.seal_id}>
                <button
                  type="button"
                  onClick={() => {
                    setSealId(a.seal_id)
                    setSearch(`${a.seal_id} · ${a.name}`)
                  }}
                  className={
                    'w-full px-2 py-1 text-left text-[11px] hover:bg-bg-2 ' +
                    (sealId === a.seal_id ? 'bg-panel-2 text-text' : 'text-muted')
                  }
                >
                  <span className="font-mono">{a.seal_id}</span> · {a.name}
                </button>
              </li>
            ))}
          </ul>
        )}
        <label className="mt-2 block text-xs font-medium text-muted">
          seal_id
          <input
            type="text"
            value={sealId}
            onChange={(e) => setSealId(e.target.value)}
            placeholder="APP-…"
            className="mt-1 w-full font-mono text-xs"
          />
        </label>

        <label className="mt-2 block text-xs font-medium text-muted">
          Rationale <span className="text-brand-soft">(required — becomes the CSV provenance column)</span>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>

        <label className="mt-2 flex items-center gap-1.5 text-[11px] text-muted">
          <input type="checkbox" checked={createTarget} onChange={(e) => setCreateTarget(e.target.checked)} />
          create target BusinessApplication if missing
        </label>

        <div className="mt-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!sealId.trim() || !rationale.trim()}
            onClick={() => onAssign(sealId.trim(), rationale.trim(), createTarget)}
            className="rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Draft {rows.length} entr{rows.length === 1 ? 'y' : 'ies'}
          </button>
        </div>
      </div>
    </div>
  )
}
