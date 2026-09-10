import { useEffect, useMemo, useState } from 'react'
import type { Persona } from '../lib/auth'
import {
  createMappingsApi,
  type MappingDomain,
  type MappingGrid,
  type MappingOptions,
  type MappingsApi,
  type OverrideEntry,
} from '../lib/mappingsApi'
import { DEMO_OVERRIDE_GRID, type OverrideGridRow } from '../data/mappingsDemo'
import ModuleToolbar from '../layout/ModuleToolbar'
import EmptyState from '../components/ui/EmptyState'
import AppCodeCascadePane from './AppCodeCascadePane'
import DomainGridTable from './DomainGridTable'
import { isResolved, useGraphAccess, useGraphQuery } from '../data/graphAccess'
import { validateRows, validateRowsOf, type RowShape } from '../data/rowShape'
import CompletenessNotice from '../components/ui/CompletenessNotice'
import { completeOf } from '../data/completeness'

// /mappings — the O13 manual-mapping stewardship screen (wf-mapping-01).
// Steward + admin only (server-enforced too — /mappings/* returns 403 below
// steward). THE ONE RULE THAT SHAPES EVERYTHING: the loader stays the ONLY
// graph writer. Assigning drafts entries into a per-user changeset tray;
// submit produces a change ARTIFACT (CSV + manifest snippet download) that
// travels git → gate → merge → next load run. Zero graph writes happen here.
//
// K15 (2026-08-05) — THE JOB-GRAIN PANE IS RETIRED, not re-bound. K7 §A1 ruled
// attribution FOLDER-grain ("jobs inherit through CONTAINS_JOB and no per-job
// application edge is authored going forward"), and K8 retired the job-grain
// edge outright. This pane's coverage grid read that edge, so post-K8 it
// reported every row as "unresolved" and its assign flow drafted a changeset
// the server refuses — a live misreporting surface.
//
// WHY RETIRE RATHER THAN RE-BIND (SME, 2026-08-05): a folder and its jobs carry
// the SAME app code, so a job-grain grid is N× rows carrying ONE folder-level
// fact. That is not a finer answer, it is the same answer repeated — and a grid
// that looks per-job invites being read as per-job truth, which is exactly the
// model K7 corrected. "Which application owns this job?" stays answerable as a
// one-hop traversal (job → CONTAINS_JOB → folder → BELONGS_TO_APPLICATION);
// it does not need a maintained grid. app-code-mapping (the K7 defined-mapping
// store, one authored row per app code) is now the default domain.

// Fallback registry mirror (drydocs_api/mappings.py DOMAINS) so the strip
// renders with a visible notice when the api is down — never silently.
const FALLBACK_DOMAINS: MappingDomain[] = [
  { id: 'ontology-map', title: 'Taxonomy ↔ Ontology map (the loading quintuple)', kind: 'quintuple', source: 'config/taxonomy-ontology-map.yaml', tier: null, available: true },
  { id: 'seal-contact-override', title: 'Application Contacts (operate-manager override list — L1/L2)', kind: 'override', source: 'config/overrides/seal-contact-overrides.csv', tier: null, available: true },
  { id: 'app-code-mapping', title: 'Application ← App code (the K7 defined-mapping store)', kind: 'defined', source: 'config/overrides/app-code-mappings.csv', tier: null, available: true },
  { id: 'fid-seal', title: 'FID → app_id (tier 2)', kind: 'manual', source: '(K6/T2 — reconciler table not built yet)', tier: 2, available: false },
  { id: 'alias-seal', title: 'ALIAS → app_id (tier 4)', kind: 'manual', source: '(T3 — reconciler table not built yet)', tier: 4, available: false },
]


function download(filename: string, content: string, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function MappingsRoute({ persona }: { persona: Persona }) {
  // The O13 mappings client is a different surface with its own API; it takes
  // the base URL from the session rather than re-deriving it.
  const { apiUrl } = useGraphAccess()
  const mappings = useMemo(() => createMappingsApi(apiUrl, persona.id), [apiUrl, persona.id])

  const [apiDown, setApiDown] = useState<string | null>(null)
  const [domains, setDomains] = useState<MappingDomain[]>(FALLBACK_DOMAINS)
  // ?domain= deep-links a specific strip tab (e.g. /mappings?domain=seal-contact-override).
  // Default is app-code-mapping (K15): the K7 defined-mapping store is the authoring
  // surface, one row per app code.
  const [activeDomain, setActiveDomain] = useState(() => {
    const wanted = new URLSearchParams(window.location.search).get('domain')
    return FALLBACK_DOMAINS.some((d) => d.id === wanted && d.available) ? wanted! : 'app-code-mapping'
  })
  const [options, setOptions] = useState<MappingOptions | null>(null)

  // domain entry grids (manual CSV rows / ontology map), fetched per domain
  const [domainGrid, setDomainGrid] = useState<MappingGrid | null>(null)

  useEffect(() => {
    const ctl = new AbortController()
    mappings
      .domains()
      .then((d) => {
        if (ctl.signal.aborted) return
        setDomains(d)
        setApiDown(null)
      })
      .catch((e: Error) => {
        if (!ctl.signal.aborted) setApiDown(e.message)
      })
    mappings
      .options()
      .then((o) => {
        if (!ctl.signal.aborted) setOptions(o)
      })
      .catch(() => {
        /* options footer just stays empty — the apiDown notice already shows */
      })
    return () => ctl.abort()
  }, [mappings])

  useEffect(() => {
    const ctl = new AbortController()
    setDomainGrid(null)
    const available = domains.find((d) => d.id === activeDomain)?.available
    if (!available) return
    mappings
      .grid(activeDomain)
      .then((g) => {
        if (!ctl.signal.aborted) setDomainGrid(g)
      })
      .catch(() => {
        /* grid stays null → its section shows the api-down hint */
      })
    return () => ctl.abort()
  }, [mappings, activeDomain, domains])

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
          drydocs-api unavailable ({apiDown.split('—')[0].trim()}) — the domain registry is the SYNTHESIZED demo set;
          drafting still works, submit needs the api.
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
          {activeDomain === 'seal-contact-override' ? (
            <SealOverridePane
              mappings={mappings}
              grid={domainGrid}
              apiDown={apiDown}
            />
          ) : activeDomain === 'app-code-mapping' ? (
            <AppCodeCascadePane
              mappings={mappings}
              grid={domainGrid}
              apiDown={apiDown}
              personaId={persona.id}
            />
          ) : (
            <>
              <p className="shrink-0 text-[11px] text-muted">
                {activeDef?.title} — read-only view of the committed source ({activeDef?.source}), served from the
                mapping-store materialization.
              </p>
              <DomainGridTable
                grid={domainGrid}
                apiDown={apiDown}
                domainId={activeDomain}
                source={activeDef?.source}
              />
            </>
          )}

          {options && (
            <p className="shrink-0 border-t border-edge-soft pt-1.5 font-mono text-[10px] text-faint">
              vocabulary status (mapping.db):{' '}
              {options.status_summary.map((s) => `${s.status} ${s.n}`).join(' · ')}
            </p>
          )}
        </div>

      </div>

    </div>
  )
}

// ── O24 SEAL-contact override pane (ui-write-surface gate SME-3, M2 tier) ──
// SEAL says one thing, the support team knows another, and only the
// application owner (AO privilege) can fix SEAL. Every row carries an ORIGIN
// flag; source and override render side by side, never merged. Drafting
// returns the COMPLETE updated committed file (commit-by-replace); the
// source-corrections report is the artifact that carries the fix request to
// the AOs. Zero graph writes, zero server writes.

const SEAL_ROLES_SPEC = 'mappings.seal-contact-roles.v1'

/** The nine columns the seal-contact-override grid returns. Verified against
 *  the server's own SELECT (drydocs_api/mappings.py, `seal-contact-override`),
 *  which aliases app_seal_id AS app_id and emits the other eight verbatim — so
 *  this is the full row, not a subset chosen to make the check pass. */
const OVERRIDE_GRID_COLUMNS: RowShape<OverrideGridRow> = [
  'app_id',
  'role_name',
  'origin',
  'holder_sid',
  'holder_name',
  'rationale',
  'authored_by',
  'authored_on',
  'status',
]

interface SealRoleRow {
  app_id: string
  application: string | null
  role_name: string
  level: string | null
  holder_sid: string | null
  holder_name: string | null
}

/** WEB6: the columns SealRoleRow requires, checked at runtime. Names only —
 *  their TYPES come from the result's own column declarations, so this is not a
 *  second copy of the server's contract. `keyof SealRoleRow` means a rename of a
 *  field here is a compile error, not a silently unchecked column. */
const SEAL_ROLE_COLUMNS: RowShape<SealRoleRow> = [
  'app_id',
  'application',
  'role_name',
  'level',
  'holder_sid',
  'holder_name',
]

function SealOverridePane({
  mappings,
  grid,
  apiDown,
}: {
  mappings: MappingsApi
  grid: MappingGrid | null
  apiDown: string | null
}) {
  const [drafts, setDrafts] = useState<OverrideEntry[]>([])
  const [dialogSeed, setDialogSeed] = useState<Partial<OverrideEntry> | null>(null)
  const [status, setStatus] = useState('')

  // live SEAL attributions from the graph (the origin='source' rows the
  // committed list may not have captured yet)
  const sealRoles = useGraphQuery(SEAL_ROLES_SPEC)
  // Memoised on the query STATE, whose identity changes only when the read
  // does: the rows feed a useMemo below, and a fresh array every render would
  // rebuild the whole override grid on every keystroke.
  // WEB6: the columns this pane needs, checked against the server's own
  // declarations. A spec that renamed `holder_sid` used to render a column of
  // blanks; it now names the column. ONE call, memoised on the query state —
  // the rows and the problem are two faces of one check, and computing them
  // separately would let them disagree.
  // WEB19: the completeness envelope rides in the same memo as the rows and the
  // problem, for the reason the comment above already gives — they are faces of
  // one check, and computing them apart lets them disagree. A capped live read
  // silently withholds SEAL attributions the committed grid below then appears
  // to contradict.
  const live = useMemo(() => {
    if (!isResolved(sealRoles)) return { rows: null, problem: null, completeness: completeOf(0) }
    const checked = validateRows<SealRoleRow>(sealRoles.data, SEAL_ROLE_COLUMNS)
    return checked.ok
      ? { rows: checked.rows, problem: null, completeness: checked.completeness }
      : { rows: [] as SealRoleRow[], problem: checked.message, completeness: completeOf(0) }
  }, [sealRoles])
  // A shape failure reads as "no live rows" HERE rather than blanking the pane:
  // the committed grid below is a real answer that does not depend on this read,
  // so hiding it would cost the operator more than the mismatch does. The
  // message rides on the pane's own status line instead.
  const liveSource: SealRoleRow[] | null = useMemo(
    () => (sealRoles.status === 'error' ? [] : live.rows),
    [sealRoles.status, live],
  )

  // one origin-flagged row list: committed grid rows (store) + live graph
  // attributions not already captured as a source row for that (app, role)
  // WEB6: the O13 mappings grid declares KEYS and rows and no column types, so
  // the same check runs presence-only over it — which is the half that catches a
  // renamed column, and the half this cast was hiding.
  const gridChecked = useMemo(
    () =>
      validateRowsOf<OverrideGridRow>(
        { source: `mappings grid '${grid?.domain ?? 'override'}'`, keys: grid?.keys ?? [], rows: grid?.rows ?? [] },
        OVERRIDE_GRID_COLUMNS,
      ),
    [grid],
  )
  // Part of the memo above rather than derived after it: a fresh `[]` on every
  // render is a new identity, and the row memo below takes it as a dependency.
  const gridRows: OverrideGridRow[] = useMemo(
    () => (gridChecked.ok ? gridChecked.rows : []),
    [gridChecked],
  )

  const rows: OverrideGridRow[] = useMemo(() => {
    const isDemo = apiDown !== null && grid === null
    const stored: OverrideGridRow[] = isDemo
      ? [...DEMO_OVERRIDE_GRID]
      : gridRows
    const covered = new Set(
      stored.filter((r) => r.origin === 'source').map((r) => `${r.app_id}|${r.role_name}`),
    )
    const live: OverrideGridRow[] = (liveSource ?? [])
      .filter((s) => !covered.has(`${s.app_id}|${s.role_name}`))
      .map((s) => ({
        app_id: s.app_id,
        role_name: s.role_name,
        origin: 'source' as const,
        holder_sid: s.holder_sid,
        holder_name: s.holder_name,
        rationale: null,
        authored_by: null,
        authored_on: null,
        status: 'active' as const,
      }))
    return [...stored, ...live].sort(
      (a, b) =>
        a.app_id.localeCompare(b.app_id) ||
        a.role_name.localeCompare(b.role_name) ||
        (a.origin === b.origin ? 0 : a.origin === 'source' ? -1 : 1),
    )
  }, [grid, apiDown, liveSource, gridRows])

  const demo = apiDown !== null && grid === null

  async function downloadUpdatedList() {
    if (drafts.length === 0) return
    setStatus('drafting…')
    try {
      const art = await mappings.draftOverride(drafts)
      // S4: the draft is now DURABLE in var/mapping.db before anything is
      // downloaded, so an interrupted session no longer loses the edit and a
      // second steward's draft cannot be overwritten by this one.
      const patch = await mappings.promoteDraft(art.draft_id)
      download(patch.filename, patch.diff, 'text/x-patch')
      setDrafts([])
      setStatus(
        `diff downloaded (${art.entries} new row(s) over ${art.committed_rows} committed) — apply it on a branch with \`git apply\` against ${patch.path} and commit; the server wrote NO committed file`,
      )
    } catch (e) {
      setStatus(`draft failed: ${(e as Error).message}`)
    }
  }

  async function downloadReport() {
    setStatus('generating report…')
    try {
      const rep = await mappings.correctionsReport()
      download(rep.filename, rep.markdown, 'text/markdown')
      setStatus(`source-corrections report downloaded (${rep.count} outstanding) — for the application owners (AO privilege fixes SEAL)`)
    } catch (e) {
      setStatus(`report failed: ${(e as Error).message}`)
    }
  }

  return (
    <>
      <p className="shrink-0 rounded border border-red/60 bg-red/10 px-2 py-1 font-mono text-[10px] text-brand-soft">
        INTERNAL — contact attributions (PUBLISH-BOUNDARY.md)
      </p>
      <div className="flex shrink-0 flex-wrap items-center gap-1.5">
        <span className="font-mono text-[10px] text-faint">
          {rows.length} rows · {demo ? 'SYNTHESIZED demo' : 'mapping.db + live graph'}
        </span>
        <span className="text-[10px] text-faint">
          origin-flagged: SEAL source and user override side by side — an override never replaces the SEAL value
        </span>
        <button
          type="button"
          onClick={() => setDialogSeed({})}
          className="ml-auto rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-medium text-text"
        >
          New override…
        </button>
        <button
          type="button"
          onClick={downloadReport}
          disabled={demo}
          title="Markdown artifact for the application owners — only the AO privilege can fix SEAL itself"
          className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text disabled:cursor-not-allowed disabled:text-faint"
        >
          Source-corrections report
        </button>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title="No attributions or overrides yet"
          hint="Live SEAL operate-manager attributions and committed overrides both appear here, origin-flagged."
        />
      ) : (
        <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="sticky top-0 bg-panel-2">
              <tr>
                {['Application', 'Role', 'Origin', 'Holder', 'Rationale', 'Authored', 'Status', ''].map((h, i) => (
                  <th key={i} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-text">{r.app_id}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{r.role_name}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5">
                    <OriginChip origin={r.origin} />
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[11px] text-text">
                    {r.holder_sid ?? '—'}
                    {r.holder_name ? ` · ${r.holder_name}` : ''}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-[11px] text-muted">{r.rationale ?? ''}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-faint">
                    {[r.authored_by, r.authored_on].filter(Boolean).join(' ')}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-faint">
                    {r.origin === 'override' ? r.status : ''}
                  </td>
                  <td className="border-b border-edge-soft px-2 py-1.5">
                    {r.origin === 'source' && (
                      <button
                        type="button"
                        title="Draft a correction for this SEAL value"
                        onClick={() =>
                          setDialogSeed({
                            app_id: r.app_id,
                            role_name: r.role_name,
                            seal_holder_sid: r.holder_sid ?? '',
                          })
                        }
                        className="rounded border border-edge px-1.5 py-0.5 text-[10px] text-muted hover:text-text"
                      >
                        override…
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {drafts.length > 0 && (
        <div className="flex shrink-0 items-center gap-2 rounded-md border border-edge-soft bg-bg-2/40 p-2">
          <span className="text-[11px] text-muted">
            {drafts.length} draft override{drafts.length === 1 ? '' : 's'}:{' '}
            <span className="font-mono text-[10px]">
              {drafts.map((d) => `${d.app_id}/${d.role_name}→${d.override_holder_sid}`).join(', ')}
            </span>
          </span>
          <button
            type="button"
            onClick={downloadUpdatedList}
            disabled={demo}
            title="Downloads the COMPLETE updated override list — replace the committed file and commit"
            className="ml-auto rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Download updated override list
          </button>
          <button
            type="button"
            onClick={() => setDrafts([])}
            className="rounded border border-edge px-1.5 py-0.5 text-[10px] text-muted hover:text-text"
          >
            clear
          </button>
        </div>
      )}
      {live.problem && (
        // WEB6 clause (c): said in place of the rows it would have rendered,
        // and never mixed into the transient action status above it.
        <p className="shrink-0 rounded border border-red/50 bg-red/10 px-2 py-1 text-[11px] text-red">
          <b>Column mismatch.</b> {live.problem} Live SEAL attributions are not shown; the committed
          grid below is unaffected.
        </p>
      )}
      {live.completeness.truncated && (
        // WEB19: the live read hit the server's ceiling, so the attributions
        // shown are the first of them. Said here rather than left to the reader
        // to infer from a row count, because the committed grid beside it looks
        // like the disagreement.
        <p className="flex shrink-0 items-center gap-2 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 text-[11px] text-yellow">
          <span>
            <b>Partial live read.</b> Live SEAL attributions were capped by the server; more exist
            than are merged into the grid below.
          </span>
          <CompletenessNotice completeness={live.completeness} unit="rows" noun="attribution" />
        </p>
      )}
      {status && <p className="shrink-0 font-mono text-[10px] text-muted">{status}</p>}

      {dialogSeed && (
        <OverrideDialog
          seed={dialogSeed}
          onCancel={() => setDialogSeed(null)}
          onDraft={(entry) => {
            setDrafts((prev) => [...prev, entry])
            setDialogSeed(null)
            setStatus(`override drafted for ${entry.app_id} / ${entry.role_name}`)
          }}
        />
      )}
    </>
  )
}

function OriginChip({ origin }: { origin: OverrideGridRow['origin'] }) {
  return origin === 'source' ? (
    <span className="rounded border border-edge px-1.5 py-0.5 font-mono text-[10px] text-muted">source (SEAL)</span>
  ) : (
    <span className="rounded border border-brand px-1.5 py-0.5 font-mono text-[10px] text-text">user override</span>
  )
}

function OverrideDialog({
  seed,
  onCancel,
  onDraft,
}: {
  seed: Partial<OverrideEntry>
  onCancel: () => void
  onDraft: (entry: OverrideEntry) => void
}) {
  const [app, setApp] = useState(seed.app_id ?? '')
  const [role, setRole] = useState(seed.role_name ?? 'L2 Operate Manager')
  const [sealSid, setSealSid] = useState(seed.seal_holder_sid ?? '')
  const [sid, setSid] = useState('')
  const [name, setName] = useState('')
  const [rationale, setRationale] = useState('')

  const notACorrection = sealSid.trim() !== '' && sealSid.trim() === sid.trim()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Draft SEAL-contact override">
      <div className="w-[28rem] max-w-[90vw] rounded-lg border border-edge bg-panel p-4 shadow-xl">
        <h3 className="text-sm font-semibold text-text">Draft a SEAL-contact override</h3>
        <p className="mt-1 rounded border border-edge-soft bg-bg-2/40 p-2 text-[11px] text-muted">
          The override is kept <strong>side by side</strong> with the SEAL value — it never replaces it and never
          writes the graph. Only the application owner (<strong>AO privilege</strong>) can fix SEAL; the
          source-corrections report carries this request to them.
        </p>

        <label className="mt-3 block text-xs font-medium text-muted">
          Application ID
          <input type="text" value={app} onChange={(e) => setApp(e.target.value)} placeholder="APP-…" className="mt-1 w-full font-mono text-xs" />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Role
          <select value={role} onChange={(e) => setRole(e.target.value)} className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text">
            <option>L1 Operate Manager</option>
            <option>L2 Operate Manager</option>
          </select>
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          SEAL currently shows (holder SID — leave empty if nobody is assigned)
          <input type="text" value={sealSid} onChange={(e) => setSealSid(e.target.value)} className="mt-1 w-full font-mono text-xs" />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Correct holder SID
          <input type="text" value={sid} onChange={(e) => setSid(e.target.value)} className="mt-1 w-full font-mono text-xs" />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Correct holder name (optional)
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-full text-xs" />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Rationale <span className="text-brand-soft">(required — becomes the report's justification column)</span>
          <textarea value={rationale} onChange={(e) => setRationale(e.target.value)} rows={2} className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text" />
        </label>
        {notACorrection && (
          <p className="mt-1.5 rounded border border-yellow/50 bg-yellow/10 p-2 text-[11px] text-yellow">
            The override equals the SEAL value — that is not a correction.
          </p>
        )}

        <div className="mt-3 flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text">
            Cancel
          </button>
          <button
            type="button"
            disabled={!app.trim() || !sid.trim() || !rationale.trim() || notACorrection}
            onClick={() =>
              onDraft({
                app_id: app.trim(),
                role_name: role,
                seal_holder_sid: sealSid.trim() || undefined,
                override_holder_sid: sid.trim(),
                override_holder_name: name.trim() || undefined,
                rationale: rationale.trim(),
              })
            }
            className="rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Draft override
          </button>
        </div>
      </div>
    </div>
  )
}
