import { useEffect, useMemo, useState } from 'react'
import type { createApiAccess } from '../lib/graphApi'
import type { AppCodeEntry, MappingGrid, MappingsApi } from '../lib/mappingsApi'
import type { SpecResult } from '../lib/graph'
import {
  DEMO_APP_ORCHESTRATORS,
  DEMO_CASCADE,
  DEMO_ORCHESTRATORS,
  DEMO_UNMAPPED_FOLDERS,
  type AppOrchestratorRow,
  type CascadeRow,
  type OrchestratorRow,
  type UnmappedFolderRow,
} from '../data/mappingsDemo'
import EmptyState from '../components/ui/EmptyState'

// K11 — the steward mapping cascade (gate seal-app-ref-edge-reshape §G,
// SIGNED OFF 2026-08-03). The act is ORCHESTRATOR-FIRST (§G1): Product Line
// -> Product -> Business Application (a LIST, never a single app — §G6) ->
// orchestrator (prefilled from the SEAL declaration, §G2 — the CONFIRMED
// mapping is what authors the USES_SOFTWARE edge) -> available folders
// (UNMAPPED ONLY, naming-pattern optional and layered on top — §G7; sortable
// by run_as_user, the SME addition) -> SME check/approval with notes.
//
// THE ONE RULE: this screen drafts STORE ROWS only (§E3/§G7) — the artifact
// is the complete updated config/overrides/app-code-mappings.csv; the K8
// loader is the only graph writer. The mandatory rationale + lifecycle chips
// (draft -> submitted -> gated -> loaded) ARE the confirmed edge's
// provenance and satisfy K10's port confirmation stamp — one mechanism.

const CASCADE_SPEC = 'mappings.catalog-cascade.v1'
const ORCHESTRATORS_SPEC = 'mappings.orchestrators.v1'
const APP_ORCH_SPEC = 'mappings.app-orchestrators.v1'
const UNMAPPED_SPEC = 'mappings.unmapped-folders.v1'
const APP_SPEC = 'explorer.applications.v1'

// The Control-M registry ref (platforms.yaml, C12-confirmed) — the one
// orchestrator with an onboarded entity source producer-side. Any other pick
// renders the honest "no entity source onboarded" state instead of a list.
const CONTROLM_PRODUCT_ID = 'controlm'

type Lifecycle = 'draft' | 'submitted' | 'gated' | 'loaded'
type FolderSort = 'folder' | 'run_as_users' | 'jobs' | 'app_code'

interface TrayEntry {
  key: string // `${app_code}|${folder_id ?? ''}` — the store's duplicate key sans origin
  label: string
  app_code: string
  folder_id: string | null
  tier: AppCodeEntry['tier']
  app_id: string
  origin: 'defined' | 'override'
  declared_end_state: string | null
  rationale: string
  authoredAt: string
  lifecycle: Exclude<Lifecycle, 'loaded'> // 'loaded' is DERIVED, never stored
}

interface AppOption {
  app_id: string
  name: string
}

function trayKey(personaId: string): string {
  return `drydocs.mappings.appcode.tray.v1.${personaId}`
}

function loadTray(personaId: string): TrayEntry[] {
  try {
    const raw = localStorage.getItem(trayKey(personaId))
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

function LifecycleChip({ lifecycle }: { lifecycle: Lifecycle }) {
  const cls =
    lifecycle === 'loaded'
      ? 'border-brand text-text'
      : lifecycle === 'draft'
        ? 'border-edge text-muted'
        : 'border-edge-soft text-faint'
  return <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${cls}`}>{lifecycle}</span>
}

function StepLabel({ n, title }: { n: number; title: string }) {
  return (
    <p className="text-xs font-semibold text-text">
      <span className="mr-1.5 inline-block w-4 rounded bg-panel-2 text-center font-mono text-[10px] text-muted">
        {n}
      </span>
      {title}
    </p>
  )
}

export default function AppCodeCascadePane({
  mappings,
  access,
  grid,
  apiDown,
  personaId,
}: {
  mappings: MappingsApi
  access: ReturnType<typeof createApiAccess>
  grid: MappingGrid | null
  apiDown: string | null
  personaId: string
}) {
  // ── live data (each spec degrades to its SYNTHESIZED demo frame, with notice)
  const [cascade, setCascade] = useState<CascadeRow[] | null>(null)
  const [cascadeLive, setCascadeLive] = useState(false)
  const [orchestrators, setOrchestrators] = useState<OrchestratorRow[] | null>(null)
  const [appOrch, setAppOrch] = useState<AppOrchestratorRow[] | null>(null)
  const [folders, setFolders] = useState<UnmappedFolderRow[] | null>(null)
  const [foldersLive, setFoldersLive] = useState(false)
  const [allApps, setAllApps] = useState<AppOption[] | null>(null)

  useEffect(() => {
    let cancelled = false
    const run = <T,>(
      spec: string,
      demo: readonly T[],
      set: (rows: T[]) => void,
      setLive?: (live: boolean) => void,
    ) =>
      access
        .runSpec(spec)
        .then((r: SpecResult) => {
          if (cancelled) return
          if (r.rows.length > 0) {
            set(r.rows as unknown as T[])
            setLive?.(true)
          } else {
            set([...demo])
          }
        })
        .catch(() => {
          if (!cancelled) set([...demo])
        })
    run(CASCADE_SPEC, DEMO_CASCADE, setCascade, setCascadeLive)
    run(ORCHESTRATORS_SPEC, DEMO_ORCHESTRATORS, setOrchestrators)
    run(APP_ORCH_SPEC, DEMO_APP_ORCHESTRATORS, setAppOrch)
    run(UNMAPPED_SPEC, DEMO_UNMAPPED_FOLDERS, setFolders, setFoldersLive)
    access
      .runSpec(APP_SPEC)
      .then((r) => {
        if (!cancelled) setAllApps(r.rows as unknown as AppOption[])
      })
      .catch(() => {
        if (!cancelled) setAllApps([])
      })
    return () => {
      cancelled = true
    }
  }, [access])

  // ── cascade selection state
  const [productLineId, setProductLineId] = useState('')
  const [productId, setProductId] = useState('')
  const [appId, setAppId] = useState('')
  const [orchestratorId, setOrchestratorId] = useState('')
  const [appSearch, setAppSearch] = useState('')

  const productLines = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of cascade ?? []) seen.set(r.product_line_id, r.product_line)
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [cascade])

  const products = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of cascade ?? []) {
      if (r.product_line_id === productLineId && r.product_id) seen.set(r.product_id, r.product ?? r.product_id)
    }
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [cascade, productLineId])

  // §G6: HAS_APPLICATION is 1:many BY DESIGN — this is a LIST, never a single
  // application. Producer-side the edge is still planned (catalog_has_application;
  // loading waits on the C9 product-scoped-extract condition), so the list may be
  // empty; the search fallback keeps the cascade usable and the notice says why.
  const productApps = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of cascade ?? []) {
      if (r.product_id === productId && r.app_id) seen.set(r.app_id, r.application ?? r.app_id)
    }
    return [...seen.entries()].map(([id, name]) => ({ app_id: id, name }))
  }, [cascade, productId])

  const appMatches = useMemo(() => {
    if (!allApps || !appSearch) return []
    const needle = appSearch.toLowerCase()
    return allApps
      .filter((a) => a.app_id?.toLowerCase().includes(needle) || a.name?.toLowerCase().includes(needle))
      .slice(0, 6)
  }, [allApps, appSearch])

  // §G2: the SEAL-declared orchestrator PREFILLS the picker — the pick under a
  // confirmed mapping is what authors the edge (§G1). §G3: several edges are a
  // normal mid-migration state, shown, never flagged as drift.
  const selectedAppEdges = useMemo(
    () => (appOrch ?? []).filter((e) => e.app_id === appId),
    [appOrch, appId],
  )
  useEffect(() => {
    if (!appId || orchestratorId) return
    const declared = selectedAppEdges.find((e) => e.source === 'batch-port')
    if (declared) setOrchestratorId(declared.product_id)
  }, [appId, orchestratorId, selectedAppEdges])

  // ── folder filter (§G7: unmapped only is spec-enforced; the pattern filter
  // is OPTIONAL and layered on top — never primary)
  const [pattern, setPattern] = useState('')
  const [sortKey, setSortKey] = useState<FolderSort>('folder')
  const [checked, setChecked] = useState<ReadonlySet<string>>(new Set())

  const visibleFolders = useMemo(() => {
    if (orchestratorId !== CONTROLM_PRODUCT_ID) return []
    let rows = folders ?? []
    if (pattern) {
      const needle = pattern.toLowerCase()
      rows = rows.filter((f) =>
        [f.folder, f.app_code, f.run_as_users].some((v) => String(v ?? '').toLowerCase().includes(needle)),
      )
    }
    return [...rows].sort((a, b) => {
      if (sortKey === 'jobs') return b.jobs - a.jobs
      return String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''))
    })
  }, [folders, orchestratorId, pattern, sortKey])

  const checkedFolders = useMemo(
    () => (folders ?? []).filter((f) => checked.has(f.folder_id)),
    [folders, checked],
  )

  // ── tray (per-user, persisted; lifecycle chips ARE the provenance — §G7)
  const [tray, setTray] = useState<TrayEntry[]>(() => loadTray(personaId))
  useEffect(() => {
    localStorage.setItem(trayKey(personaId), JSON.stringify(tray))
  }, [tray, personaId])

  const [dialogOpen, setDialogOpen] = useState(false)
  const [status, setStatus] = useState('')
  const [artifactNote, setArtifactNote] = useState('')

  // 'loaded' self-verification: the committed grid (mapping.db) carries the
  // row AND the folder(s) left the LIVE unmapped queue — verified against the
  // store + graph, never against this screen's own state.
  const committedKeys = useMemo(() => {
    const keys = new Set<string>()
    for (const r of grid?.rows ?? []) {
      keys.add(`${String(r.app_code ?? '')}|${String(r.folder_id ?? '')}`)
    }
    return keys
  }, [grid])

  const derivedLifecycle = (e: TrayEntry): Lifecycle => {
    if (e.lifecycle !== 'draft' && committedKeys.has(e.key) && foldersLive) {
      const stillUnmapped = (folders ?? []).some((f) =>
        e.folder_id ? f.folder_id === e.folder_id : f.app_code === e.app_code,
      )
      if (!stillUnmapped) return 'loaded'
    }
    return e.lifecycle
  }

  function addDrafts(entry: {
    tier: AppCodeEntry['tier']
    origin: 'defined' | 'override'
    rationale: string
    declaredEndState: string
  }) {
    const authoredAt = new Date().toISOString()
    const perFolder = entry.tier === 'platform'
    const next: TrayEntry[] = []
    if (perFolder) {
      for (const f of checkedFolders) {
        if (!f.app_code) continue
        next.push({
          key: `${f.app_code}|${f.folder_id}`,
          label: `${f.app_code} · ${f.folder}`,
          app_code: f.app_code,
          folder_id: f.folder_id,
          tier: entry.tier,
          app_id: appId,
          origin: entry.origin,
          declared_end_state: null,
          rationale: entry.rationale,
          authoredAt,
          lifecycle: 'draft',
        })
      }
    } else {
      // seal-born / dual-coded are CODE-LEVEL rows (§B1 fan-out): one row per
      // distinct app code among the selected folders.
      const codes = [...new Set(checkedFolders.map((f) => f.app_code).filter(Boolean))] as string[]
      for (const code of codes) {
        next.push({
          key: `${code}|`,
          label: `${code} (code-level — fan-out covers every folder under it)`,
          app_code: code,
          folder_id: null,
          tier: entry.tier,
          app_id: appId,
          origin: entry.origin,
          declared_end_state: entry.tier === 'dual-coded' ? entry.declaredEndState : null,
          rationale: entry.rationale,
          authoredAt,
          lifecycle: 'draft',
        })
      }
    }
    setTray((prev) => {
      const merged = [...prev]
      for (const e of next) {
        const i = merged.findIndex((x) => x.key === e.key && x.lifecycle === 'draft')
        if (i >= 0) merged[i] = e
        else merged.push(e)
      }
      return merged
    })
    setChecked(new Set())
    setDialogOpen(false)
    setStatus(`${next.length} draft row${next.length === 1 ? '' : 's'} added to the tray`)
  }

  async function submitDrafts() {
    const drafts = tray.filter((e) => e.lifecycle === 'draft')
    if (drafts.length === 0) return
    setStatus('drafting…')
    try {
      const art = await mappings.draftAppCode(
        drafts.map((e) => ({
          app_code: e.app_code,
          tier: e.tier,
          app_id: e.app_id || undefined,
          folder_id: e.folder_id ?? undefined,
          declared_end_state: e.declared_end_state ?? undefined,
          origin: e.origin,
          rationale: e.rationale,
        })),
      )
      download(art.filename, art.csv, 'text/csv')
      setArtifactNote(art.note)
      setTray((prev) => prev.map((e) => (e.lifecycle === 'draft' ? { ...e, lifecycle: 'submitted' } : e)))
      setStatus(
        `updated defined-mapping list downloaded (${art.entries} new, ${art.total_rows} total) — the server wrote NOTHING`,
      )
    } catch (e) {
      setStatus(`draft failed: ${(e as Error).message}`)
    }
  }

  const selectedOrchestrator = (orchestrators ?? []).find((o) => o.product_id === orchestratorId)
  const codelessSelection = checkedFolders.some((f) => !f.app_code)

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-hidden">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        <p className="shrink-0 rounded border border-red/60 bg-red/10 px-2 py-1 font-mono text-[10px] text-brand-soft">
          INTERNAL — application attribution (PUBLISH-BOUNDARY.md)
        </p>
        <p className="shrink-0 text-[11px] text-muted">
          The defined mapping is authored per <strong>app code</strong> and fanned out to folders by the loader
          (§B1). Your approval + notes here <strong>are</strong> the confirmed edge's provenance — they become
          the edge's origin and the port's confirmation stamp (§G7/K10). One mechanism, not two.
        </p>

        {/* 1-2 — catalog spine */}
        <div className="grid shrink-0 grid-cols-2 gap-2">
          <div>
            <StepLabel n={1} title="Product line" />
            <select
              value={productLineId}
              onChange={(e) => {
                setProductLineId(e.target.value)
                setProductId('')
                setAppId('')
              }}
              aria-label="Product line"
              className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
            >
              <option value="">— pick —</option>
              {productLines.map((pl) => (
                <option key={pl.id} value={pl.id}>
                  {pl.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <StepLabel n={2} title="Product" />
            <select
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value)
                setAppId('')
              }}
              disabled={!productLineId}
              aria-label="Product"
              className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text disabled:text-faint"
            >
              <option value="">— pick —</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 3 — the application LIST (§G6: 1:many by design, never a single app) */}
        <div className="shrink-0">
          <StepLabel n={3} title="Business application (the product's list — §G6)" />
          {productId && productApps.length > 0 ? (
            <ul className="mt-1 max-h-28 overflow-y-auto rounded-md border border-edge">
              {productApps.map((a) => (
                <li key={a.app_id}>
                  <button
                    type="button"
                    onClick={() => {
                      setAppId(a.app_id)
                      setOrchestratorId('')
                    }}
                    className={
                      'w-full px-2 py-1 text-left text-[11px] hover:bg-bg-2 ' +
                      (appId === a.app_id ? 'bg-panel-2 text-text' : 'text-muted')
                    }
                  >
                    <span className="font-mono">{a.app_id}</span> · {a.name}
                  </button>
                </li>
              ))}
            </ul>
          ) : productId ? (
            <p className="mt-1 rounded border border-yellow/50 bg-yellow/10 p-1.5 text-[11px] text-yellow">
              No catalog application links loaded — producer-side{' '}
              <span className="font-mono">catalog_has_application</span> is planned with no loader (loading
              waits on the product-scoped extract). Search the full application list instead:
            </p>
          ) : (
            <p className="mt-1 text-[11px] text-faint">Pick a product first{cascadeLive ? '' : ' · SYNTHESIZED demo catalog'}.</p>
          )}
          {productId && productApps.length === 0 && (
            <div className="mt-1">
              <input
                type="search"
                value={appSearch}
                onChange={(e) => setAppSearch(e.target.value)}
                placeholder="Search Application ID / name…"
                aria-label="Search applications"
                className="w-full text-xs"
              />
              {appMatches.length > 0 && (
                <ul className="mt-1 max-h-28 overflow-y-auto rounded-md border border-edge">
                  {appMatches.map((a) => (
                    <li key={a.app_id}>
                      <button
                        type="button"
                        onClick={() => {
                          setAppId(a.app_id)
                          setOrchestratorId('')
                          setAppSearch(`${a.app_id} · ${a.name}`)
                        }}
                        className={
                          'w-full px-2 py-1 text-left text-[11px] hover:bg-bg-2 ' +
                          (appId === a.app_id ? 'bg-panel-2 text-text' : 'text-muted')
                        }
                      >
                        <span className="font-mono">{a.app_id}</span> · {a.name}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* 4 — orchestrator FIRST, before the folder filter (§G1) */}
        <div className="shrink-0">
          <StepLabel n={4} title="Orchestrator (picked BEFORE the folder filter — §G1)" />
          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            {(orchestrators ?? []).map((o) => (
              <button
                key={o.product_id}
                type="button"
                disabled={!appId}
                onClick={() => setOrchestratorId(o.product_id)}
                className={
                  'rounded-md border px-2.5 py-1 text-xs font-medium ' +
                  (orchestratorId === o.product_id
                    ? 'border-brand bg-panel-2 text-text'
                    : appId
                      ? 'border-edge bg-bg-2 text-muted hover:text-text'
                      : 'cursor-not-allowed border-edge-soft text-faint')
                }
              >
                {o.product}
              </button>
            ))}
          </div>
          {appId && selectedAppEdges.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {selectedAppEdges.map((e, i) => (
                <span
                  key={i}
                  className={
                    'rounded border px-1.5 py-0.5 font-mono text-[10px] ' +
                    (e.origin === 'confirmed' ? 'border-brand text-text' : 'border-edge text-muted')
                  }
                  title={
                    e.origin === 'confirmed'
                      ? 'authored by a confirmed mapping (§G1)'
                      : `SEAL declaration${e.declared_raw ? ` ("${e.declared_raw}")` : ''} — prefill only (§G2)`
                  }
                >
                  {e.product} · {e.origin ?? e.source}
                </span>
              ))}
              {selectedAppEdges.length > 1 && (
                <span className="text-[10px] text-faint">
                  several orchestrators = mid-migration, a normal state (§G3) — not drift
                </span>
              )}
            </div>
          )}
          {appId && orchestratorId && selectedAppEdges.some((e) => e.source === 'batch-port' && e.product_id === orchestratorId) && (
            <p className="mt-1 text-[10px] text-faint">
              Prefilled from the SEAL declaration (§G2). The declaration never authors the edge — the mapping
              you confirm here is what does (§G1).
            </p>
          )}
        </div>

        {/* 5 — available folders: UNMAPPED ONLY (§G7) */}
        <div className="flex min-h-0 flex-1 flex-col">
          <StepLabel n={5} title="Available folders (unmapped only — §G7)" />
          {!orchestratorId ? (
            <p className="mt-1 text-[11px] text-faint">Pick an orchestrator first.</p>
          ) : orchestratorId !== CONTROLM_PRODUCT_ID ? (
            <EmptyState
              title={`No ${selectedOrchestrator?.product ?? orchestratorId} entity source onboarded`}
              hint="Control-M is the baseline domain (§G: a sibling orchestrator drops in as its own domain without re-opening the grain ruling)."
            />
          ) : (
            <>
              <div className="mt-1 flex shrink-0 flex-wrap items-center gap-1.5">
                <input
                  type="search"
                  value={pattern}
                  onChange={(e) => setPattern(e.target.value)}
                  placeholder="Naming-pattern filter (optional)…"
                  aria-label="Naming-pattern filter (optional)"
                  title="OPTIONAL, layered on top of unmapped-only — never primary (§G7): a folder name does not reliably identify an application"
                  className="w-52 text-xs"
                />
                <label className="text-[10px] text-faint">
                  sort{' '}
                  <select
                    value={sortKey}
                    onChange={(e) => setSortKey(e.target.value as FolderSort)}
                    aria-label="Sort folders"
                    className="rounded-md border border-edge bg-bg-2 p-1 text-[11px] text-text"
                  >
                    <option value="folder">folder</option>
                    <option value="app_code">app code</option>
                    <option value="run_as_users">run-as user</option>
                    <option value="jobs">jobs</option>
                  </select>
                </label>
                <span className="font-mono text-[10px] text-faint">
                  {visibleFolders.length}/{folders?.length ?? 0} unmapped · {foldersLive ? 'LIVE' : 'SYNTHESIZED demo'}
                </span>
                <button
                  type="button"
                  disabled={checkedFolders.length === 0 || !appId}
                  onClick={() => setDialogOpen(true)}
                  className="ml-auto rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-medium text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
                >
                  Approve mapping… ({checkedFolders.length})
                </button>
              </div>
              <div className="mt-1 min-h-0 flex-1 overflow-auto rounded-md border border-edge">
                <table className="w-full border-collapse text-left text-xs">
                  <thead className="sticky top-0 bg-panel-2">
                    <tr>
                      <th className="border-b border-edge px-2 py-1.5" aria-label="select" />
                      {['Folder', 'App code', 'Data center', 'Jobs', 'Run-as users'].map((h) => (
                        <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visibleFolders.map((f, i) => (
                      <tr key={f.folder_id} className={i % 2 ? 'bg-bg-2/40' : ''}>
                        <td className="border-b border-edge-soft px-2 py-1.5">
                          <input
                            type="checkbox"
                            checked={checked.has(f.folder_id)}
                            onChange={() =>
                              setChecked((prev) => {
                                const next = new Set(prev)
                                if (next.has(f.folder_id)) next.delete(f.folder_id)
                                else next.add(f.folder_id)
                                return next
                              })
                            }
                            aria-label={`select ${f.folder}`}
                          />
                        </td>
                        <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{f.folder}</td>
                        <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-text">
                          {f.app_code ?? '—'}
                        </td>
                        <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{f.data_center ?? '—'}</td>
                        <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-muted">
                          {f.jobs}
                        </td>
                        <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-muted">
                          {f.run_as_users || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* committed rows (mapping.db read) */}
        <details className="shrink-0">
          <summary className="cursor-pointer text-[11px] font-medium text-muted">
            Committed defined-mapping rows (config/overrides/app-code-mappings.csv · mapping.db)
          </summary>
          {!grid ? (
            <p className="px-1 py-2 text-[11px] text-faint">
              {apiDown ? 'Needs drydocs-api (mapping.db read).' : 'Loading mapping.db grid…'}
            </p>
          ) : grid.rows.length === 0 ? (
            <p className="px-1 py-2 text-[11px] text-faint">No committed rows yet.</p>
          ) : (
            <div className="mt-1.5 max-h-40 overflow-auto rounded-md border border-edge">
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
          )}
        </details>
      </div>

      {/* 6 — the tray: lifecycle chips ARE the confirmation provenance (§G7) */}
      <aside className="flex w-64 shrink-0 flex-col gap-2 overflow-hidden rounded-lg border border-edge bg-panel p-3">
        <h3 className="shrink-0 text-sm font-semibold text-text">Mapping tray</h3>
        <p className="shrink-0 text-[10px] text-faint">
          draft → submitted → gated → loaded. The chips + your rationale are the confirmed edge's provenance
          (§G7) — “loaded” is verified against the committed store and the live unmapped queue, never this
          screen's own state.
        </p>
        {tray.length === 0 ? (
          <EmptyState title="No drafts" hint="Walk the cascade and approve a mapping." />
        ) : (
          <ul className="min-h-0 flex-1 space-y-1.5 overflow-y-auto">
            {tray.map((e) => {
              const lc = derivedLifecycle(e)
              return (
                <li key={`${e.key}:${e.authoredAt}`} className="rounded-md border border-edge-soft bg-bg-2/40 p-2 text-[11px]">
                  <div className="flex items-center justify-between gap-1">
                    <span className="truncate font-medium text-text" title={e.label}>
                      {e.label}
                    </span>
                    <LifecycleChip lifecycle={lc} />
                  </div>
                  <div className="mt-0.5 font-mono text-[10px] text-muted">
                    → {e.app_id} · {e.tier}
                    {e.origin === 'override' ? ' · override' : ''}
                  </div>
                  {e.declared_end_state && (
                    <div className="mt-0.5 truncate text-[10px] text-faint" title={e.declared_end_state}>
                      end state: {e.declared_end_state}
                    </div>
                  )}
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
                        title="Bookkeeping: mark after the PR is reviewed (git review is the review — §E1)"
                        onClick={() => setTray((prev) => prev.map((x) => (x === e ? { ...x, lifecycle: 'gated' } : x)))}
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
          disabled={tray.every((e) => e.lifecycle !== 'draft') || apiDown !== null}
          onClick={submitDrafts}
          title="Downloads the COMPLETE updated config/overrides/app-code-mappings.csv — replace the committed file, commit, and the next K8 load run applies it"
          className="shrink-0 rounded-md border border-brand bg-panel-2 px-2.5 py-1.5 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
        >
          Submit drafts (download artifact)
        </button>
        {status && <p className="shrink-0 font-mono text-[10px] text-muted">{status}</p>}
        {artifactNote && (
          <p className="shrink-0 rounded border border-edge-soft bg-bg-2/40 p-1.5 text-[10px] text-faint">{artifactNote}</p>
        )}
      </aside>

      {dialogOpen && (
        <ApproveMappingDialog
          appId={appId}
          folders={checkedFolders}
          codelessSelection={codelessSelection}
          onCancel={() => setDialogOpen(false)}
          onApprove={addDrafts}
        />
      )}
    </div>
  )
}

function ApproveMappingDialog({
  appId,
  folders,
  codelessSelection,
  onCancel,
  onApprove,
}: {
  appId: string
  folders: UnmappedFolderRow[]
  codelessSelection: boolean
  onCancel: () => void
  onApprove: (entry: {
    tier: AppCodeEntry['tier']
    origin: 'defined' | 'override'
    rationale: string
    declaredEndState: string
  }) => void
}) {
  const [tier, setTier] = useState<AppCodeEntry['tier']>('seal-born')
  const [origin, setOrigin] = useState<'defined' | 'override'>('defined')
  const [rationale, setRationale] = useState('')
  const [declaredEndState, setDeclaredEndState] = useState('')

  const codes = [...new Set(folders.map((f) => f.app_code).filter(Boolean))]
  const needsEndState = tier === 'dual-coded' && !declaredEndState.trim()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Approve app-code mapping">
      <div className="w-[30rem] max-w-[90vw] rounded-lg border border-edge bg-panel p-4 shadow-xl">
        <h3 className="text-sm font-semibold text-text">
          SME check — map {codes.length === 1 ? `app code ${codes[0]}` : `${codes.length} app codes`} → {appId}
        </h3>
        <p className="mt-1 rounded border border-edge-soft bg-bg-2/40 p-2 text-[11px] text-muted">
          This drafts <strong>store rows only</strong> — the K8 loader is the only graph writer (§E3). Your
          approval + rationale become the confirmed edge's provenance and the port's confirmation stamp
          (§G7/K10).
        </p>
        {codelessSelection && (
          <p className="mt-1.5 rounded border border-yellow/50 bg-yellow/10 p-2 text-[11px] text-yellow">
            Some selected folders carry no app code — the defined mapping is authored per code (§B1), so those
            folders are skipped here (route them through a manual tier-5 pin instead).
          </p>
        )}

        <label className="mt-3 block text-xs font-medium text-muted">
          Tier (§B2)
          <select
            value={tier}
            onChange={(e) => setTier(e.target.value as AppCodeEntry['tier'])}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          >
            <option value="seal-born">seal-born — code created FOR this application (1:1, code-level row)</option>
            <option value="platform">platform — shared code, resolves PER FOLDER (one row per selected folder)</option>
            <option value="dual-coded">dual-coded — migrating; code-level row with a declared end state</option>
          </select>
        </label>
        {tier !== 'platform' && (
          <p className="mt-1 text-[10px] text-faint">
            Code-level row: the loader fans out to <strong>every</strong> folder under the code (§B1) — new
            folders inherit the moment they appear, not just the ones selected.
          </p>
        )}
        {tier === 'dual-coded' && (
          <label className="mt-2 block text-xs font-medium text-muted">
            Declared end state <span className="text-brand-soft">(required — a stalled migration must stay visible, §B2)</span>
            <input
              type="text"
              value={declaredEndState}
              onChange={(e) => setDeclaredEndState(e.target.value)}
              placeholder="e.g. all workload under this code once the platform folders drain"
              className="mt-1 w-full text-xs"
            />
          </label>
        )}
        <label className="mt-2 block text-xs font-medium text-muted">
          Origin
          <select
            value={origin}
            onChange={(e) => setOrigin(e.target.value as 'defined' | 'override')}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          >
            <option value="defined">defined — the authoritative mapping</option>
            <option value="override">override — corrects a wrong derived value (may be PERMANENT, §E2)</option>
          </select>
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Approval notes / rationale{' '}
          <span className="text-brand-soft">(required — becomes the row's provenance and the gate reviewer's context)</span>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>

        <div className="mt-3 flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text">
            Cancel
          </button>
          <button
            type="button"
            disabled={!rationale.trim() || needsEndState || codes.length === 0}
            onClick={() => onApprove({ tier, origin, rationale: rationale.trim(), declaredEndState: declaredEndState.trim() })}
            className="rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Approve → draft
          </button>
        </div>
      </div>
    </div>
  )
}
