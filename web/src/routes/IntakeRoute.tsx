import { useEffect, useMemo, useRef, useState } from 'react'
import type { SpecResult } from '../lib/graph'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { createIntakeApi, type IntakeRecord } from '../lib/intakeApi'
import contextTypesData from '../generated/context-types.json'
import ModuleToolbar from '../layout/ModuleToolbar'
import IdChip from '../components/ui/IdChip'
import IntakeStepper from '../components/IntakeStepper'

// O47 — the Context Intake page, slice 3 of UI-WIP/sme-intake-page-plan.md.
// Sections 1–3 are live against O45 (context-type artifact) and O46 (intake
// store); sections 4–8 render as disabled placeholders naming their slice —
// never silently absent. The area selector is a HINT channel by design (Q10:
// unattributable email lands unassigned, never guessed).

const AREA_TREE_SPEC = 'intake.area-tree.v1'
const APP_SPEC = 'explorer.applications.v1'
const BACKFILL_SPEC = 'mappings.catalog-cascade.v1'

interface AreaRow {
  product_line_id: string | null
  product_line: string | null
  product_id: string | null
  product: string | null
  area_product_id: string | null
  area_product: string | null
}

interface AppRow {
  app_id: string
  name: string | null
}

interface BackfillRow {
  product_line_id: string | null
  product_id: string | null
  app_id: string | null
}

const UNKNOWN = '__unknown__'

function SectionHeader({ n, title }: { n: number; title: string }) {
  return (
    <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold">
      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-edge-soft text-xs text-muted">
        {n}
      </span>
      {title}
    </h2>
  )
}

function LevelSelect({
  label,
  value,
  onChange,
  options,
  emptyNote,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { id: string; name: string }[]
  emptyNote?: string
}) {
  return (
    <label className="flex min-w-48 flex-col gap-1 text-xs">
      <span className="text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
      >
        <option value="">— select —</option>
        <option value={UNKNOWN}>Unknown</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}
          </option>
        ))}
      </select>
      {options.length === 0 && emptyNote && <span className="text-faint">{emptyNote}</span>}
    </label>
  )
}

function PlaceholderSection({ n, title, slice }: { n: number; title: string; slice: string }) {
  return (
    <section aria-disabled className="rounded border border-dashed border-edge-soft p-4 opacity-60">
      <SectionHeader n={n} title={title} />
      <p className="text-xs text-faint">Not in this slice — lands with {slice}.</p>
    </section>
  )
}

/** The inline thread diff: the O46 delta payload, new content highlighted. */
function ThreadDiff({ delta }: { delta: string }) {
  return (
    <pre className="max-h-48 overflow-auto rounded border border-edge-soft bg-panel-2 p-2 text-xs">
      {delta.split('\n').map((line, i) => (
        <div key={i} style={{ background: 'color-mix(in srgb, var(--teal) 18%, transparent)' }}>
          {line || ' '}
        </div>
      ))}
    </pre>
  )
}

export default function IntakeRoute({ persona }: { persona: Persona }) {
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])
  const intakeApi = useMemo(() => createIntakeApi(apiUrl, persona.id), [apiUrl, persona.id])

  // ── graph-backed pickers (degrade to empty-with-notice; never fabricate)
  const [areaRows, setAreaRows] = useState<AreaRow[] | null>(null)
  const [areaLive, setAreaLive] = useState(false)
  const [apps, setApps] = useState<AppRow[] | null>(null)
  const [backfill, setBackfill] = useState<BackfillRow[]>([])

  useEffect(() => {
    let cancelled = false
    const run = <T,>(spec: string, set: (rows: T[]) => void, setLive?: (v: boolean) => void) =>
      access
        .runSpec(spec)
        .then((r: SpecResult) => {
          if (cancelled) return
          set(r.rows as unknown as T[])
          setLive?.(r.rows.length > 0)
        })
        .catch(() => {
          if (!cancelled) set([])
        })
    run<AreaRow>(AREA_TREE_SPEC, setAreaRows, setAreaLive)
    run<AppRow>(APP_SPEC, setApps)
    run<BackfillRow>(BACKFILL_SPEC, setBackfill)
    return () => {
      cancelled = true
    }
  }, [access])

  // ── §1 area cascade state
  const [productLineId, setProductLineId] = useState('')
  const [productId, setProductId] = useState('')
  const [areaProductId, setAreaProductId] = useState('')
  const [sealId, setSealId] = useState('')
  const [sealSearch, setSealSearch] = useState('')
  const [sealConflict, setSealConflict] = useState<string | null>(null)

  const productLines = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of areaRows ?? [])
      if (r.product_line_id) seen.set(r.product_line_id, r.product_line ?? r.product_line_id)
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [areaRows])

  const products = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of areaRows ?? [])
      if (r.product_id && (!productLineId || productLineId === UNKNOWN || r.product_line_id === productLineId))
        seen.set(r.product_id, r.product ?? r.product_id)
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [areaRows, productLineId])

  const areaProducts = useMemo(() => {
    const seen = new Map<string, string>()
    for (const r of areaRows ?? [])
      if (r.area_product_id && (!productId || productId === UNKNOWN || r.product_id === productId))
        seen.set(r.area_product_id, r.area_product ?? r.area_product_id)
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [areaRows, productId])

  const sealOptions = useMemo(() => {
    const q = sealSearch.trim().toLowerCase()
    return (apps ?? [])
      .filter((a) => !q || a.app_id.toLowerCase().includes(q) || (a.name ?? '').toLowerCase().includes(q))
      .slice(0, 30)
  }, [apps, sealSearch])

  function pickSeal(id: string) {
    setSealId(id)
    setSealConflict(null)
    if (!id || id === UNKNOWN) return
    // Back-fill PAT levels where the mapping exists; FLAG (never block) a conflict.
    const m = backfill.find((b) => b.app_id === id)
    if (!m) return
    const conflicts: string[] = []
    if (m.product_line_id) {
      if (productLineId && productLineId !== UNKNOWN && productLineId !== m.product_line_id)
        conflicts.push('product line')
      else setProductLineId(m.product_line_id)
    }
    if (m.product_id) {
      if (productId && productId !== UNKNOWN && productId !== m.product_id) conflicts.push('product')
      else setProductId(m.product_id)
    }
    if (conflicts.length > 0)
      setSealConflict(
        `SEAL mapping disagrees with your ${conflicts.join(' + ')} pick — flagged, not blocked; both are recorded.`,
      )
  }

  // ── §2 context type
  const contextTypes = (contextTypesData as { context_types: { id: string; label: string }[] })
    .context_types
  const [contextType, setContextType] = useState('')
  const [otherText, setOtherText] = useState('')
  const [note, setNote] = useState('')

  // ── intake record state (create → upload → stepper)
  const [record, setRecord] = useState<IntakeRecord | null>(null)
  const [priorDecisions, setPriorDecisions] = useState<{ id: string; decision: string | null }[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  function refreshPriors(rec: IntakeRecord) {
    // A third bounce of the same thread shows BOTH prior decisions — fetch each
    // prior intake in the chain and surface its recorded call.
    Promise.all(
      rec.thread_of.map((id) =>
        intakeApi
          .get(id)
          .then((r) => ({ id, decision: r.thread_decision as string | null }))
          .catch(() => ({ id, decision: null })),
      ),
    ).then(setPriorDecisions)
  }

  async function guard<T>(work: () => Promise<T>): Promise<T | undefined> {
    setBusy(true)
    setError(null)
    try {
      return await work()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      return undefined
    } finally {
      setBusy(false)
    }
  }

  async function createIntake() {
    const rec = await guard(() =>
      intakeApi.create(
        contextType || 'other',
        {
          product_line_id: productLineId === UNKNOWN ? null : productLineId || null,
          product_id: productId === UNKNOWN ? null : productId || null,
          area_product_id: areaProductId === UNKNOWN ? null : areaProductId || null,
          seal_id: sealId === UNKNOWN ? null : sealId || null,
        },
        contextType === 'other' && otherText ? `${otherText}\n${note}`.trim() : note,
      ),
    )
    if (rec) setRecord(rec)
  }

  async function upload(files: FileList | File[] | null) {
    if (!record || !files || files.length === 0) return
    const rec = await guard(() => intakeApi.uploadEvidence(record.intake_id, [...files]))
    if (rec) {
      setRecord(rec)
      if (rec.thread_flagged) refreshPriors(rec)
    }
  }

  async function decideThread(decision: 'adds-value' | 'no-new-value') {
    if (!record) return
    const rec = await guard(() => intakeApi.threadDecision(record.intake_id, decision))
    if (rec) setRecord(rec)
  }

  async function transition(to: string) {
    if (!record) return
    const rec = await guard(() => intakeApi.transition(record.intake_id, to))
    if (rec) setRecord(rec)
  }

  // Evidence rows grouped by pair_key: the .msg/.json Copilot pair renders as
  // ONE row with two format chips; unpaired files are a group of one.
  const evidenceGroups = useMemo(() => {
    const groups = new Map<string, typeof activeEvidence>()
    const activeEvidence = (record?.evidence ?? []).filter((e) => !e.superseded)
    for (const e of activeEvidence) {
      const g = groups.get(e.pair_key) ?? []
      g.push(e)
      groups.set(e.pair_key, g)
    }
    return [...groups.entries()]
  }, [record])

  const threadPending = record?.legal_transitions.thread_decision_required === true

  return (
    <div>
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Context intake' }]} />
      <div className="flex flex-col gap-4 p-4">
        {!areaLive && areaRows !== null && (
          <p className="rounded border border-edge-soft bg-panel-2 p-2 text-xs text-faint">
            Area tree returned no rows — the catalog load has not run against this API, or the
            area-product extract has not landed. “Unknown” remains selectable at every level.
          </p>
        )}
        {error && (
          <p className="rounded border p-2 text-xs" style={{ borderColor: 'var(--status-fail-soft)', color: 'var(--status-fail-soft)' }}>
            {error}
          </p>
        )}

        <section className="rounded border border-edge-soft p-4">
          <SectionHeader n={1} title="Area (a hint, never a guess)" />
          <div className="flex flex-wrap gap-3">
            <LevelSelect label="Product line" value={productLineId} onChange={(v) => { setProductLineId(v); setProductId(''); setAreaProductId('') }} options={productLines} />
            <LevelSelect label="Product" value={productId} onChange={(v) => { setProductId(v); setAreaProductId('') }} options={products} />
            <LevelSelect
              label="Area product"
              value={areaProductId}
              onChange={setAreaProductId}
              options={areaProducts}
              emptyNote="No area products loaded yet (extract pending) — Unknown is the honest answer."
            />
            <label className="flex min-w-56 flex-col gap-1 text-xs">
              <span className="text-muted">SEAL (searchable)</span>
              <input
                value={sealSearch}
                onChange={(e) => setSealSearch(e.target.value)}
                placeholder="search id or name…"
                className="rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
              />
              <select
                value={sealId}
                onChange={(e) => pickSeal(e.target.value)}
                className="rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
              >
                <option value="">— select —</option>
                <option value={UNKNOWN}>Unknown</option>
                {sealOptions.map((a) => (
                  <option key={a.app_id} value={a.app_id}>
                    {a.app_id} {a.name ? `· ${a.name}` : ''}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {sealConflict && (
            <p className="mt-2 text-xs" style={{ color: 'var(--yellow)' }}>
              {sealConflict}
            </p>
          )}
          {sealId && sealId !== UNKNOWN && (
            <p className="mt-2 text-xs text-muted">
              Selected: <IdChip id={sealId} />
            </p>
          )}
        </section>

        <section className="rounded border border-edge-soft p-4">
          <SectionHeader n={2} title="Context type" />
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex min-w-48 flex-col gap-1 text-xs">
              <span className="text-muted">Type</span>
              <select
                value={contextType}
                onChange={(e) => setContextType(e.target.value)}
                className="rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
              >
                <option value="">— select —</option>
                {contextTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
                <option value="other">Other / not listed</option>
              </select>
            </label>
            {contextType === 'other' && (
              <input
                value={otherText}
                onChange={(e) => setOtherText(e.target.value)}
                placeholder="what kind of context is this?"
                className="min-w-64 rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
              />
            )}
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="note (optional)"
              className="min-w-64 flex-1 rounded border border-edge-soft bg-panel px-2 py-1.5 text-sm"
            />
            {!record && (
              <button
                type="button"
                disabled={busy || !contextType}
                onClick={createIntake}
                className="rounded border border-blue-bright px-3 py-1.5 text-sm hover:bg-panel-2 disabled:opacity-50"
              >
                Start intake
              </button>
            )}
          </div>
        </section>

        <section className="rounded border border-edge-soft p-4">
          <SectionHeader n={3} title="Evidence" />
          {!record ? (
            <p className="text-xs text-faint">Start the intake (section 2) to attach evidence.</p>
          ) : (
            <>
              <p className="mb-2 text-xs text-muted">
                Intake <IdChip id={record.intake_id} /> · status {record.status}
              </p>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  void upload(e.dataTransfer.files)
                }}
                onClick={() => fileInput.current?.click()}
                className="mb-3 cursor-pointer rounded border border-dashed border-edge-soft p-6 text-center text-xs text-muted hover:border-blue-bright"
              >
                Drag .msg / .json / .txt here, or click to browse. The Copilot .msg/.json pair
                links by basename and renders as one row.
                <input
                  ref={fileInput}
                  type="file"
                  multiple
                  accept=".msg,.json,.txt"
                  className="hidden"
                  onChange={(e) => void upload(e.target.files)}
                />
              </div>
              <ul className="flex flex-col gap-1">
                {evidenceGroups.map(([pairKey, rows]) => (
                  <li key={pairKey} className="flex items-center gap-2 rounded border border-edge-soft px-2 py-1 text-xs">
                    <span className="font-medium">{pairKey}</span>
                    {rows.map((e) => (
                      <span key={e.evidence_id} className="rounded-full border border-edge-soft px-1.5 text-faint" title={e.filename}>
                        {e.kind}
                      </span>
                    ))}
                    {rows.length === 2 && <span className="text-faint">paired</span>}
                  </li>
                ))}
                {evidenceGroups.length === 0 && <li className="text-xs text-faint">No evidence yet.</li>}
              </ul>

              {record.thread_flagged && (
                <div className="mt-3 rounded border border-edge-soft bg-panel-2 p-3">
                  <p className="text-xs">
                    Continues the thread of intake{' '}
                    {record.thread_of.map((id) => (
                      <IdChip key={id} id={id} />
                    ))}
                  </p>
                  {priorDecisions.length > 1 && (
                    <p className="mt-1 text-xs text-muted">
                      Prior decisions on this thread:{' '}
                      {priorDecisions.map((p) => `${p.id}: ${p.decision ?? '—'}`).join(' · ')}
                    </p>
                  )}
                  {record.review_payload && <div className="mt-2"><ThreadDiff delta={record.review_payload} /></div>}
                  {threadPending && (
                    <div className="mt-2 flex gap-2">
                      <button type="button" disabled={busy} onClick={() => void decideThread('adds-value')} className="rounded border border-blue-bright px-2 py-1 text-xs disabled:opacity-50">
                        Adds value — proceed with the delta
                      </button>
                      <button type="button" disabled={busy} onClick={() => void decideThread('no-new-value')} className="rounded border border-edge-soft px-2 py-1 text-xs disabled:opacity-50">
                        No new value — record and stop
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-4">
                <IntakeStepper status={record.status} legal={record.legal_transitions} busy={busy} onTransition={(to) => void transition(to)} />
              </div>
            </>
          )}
        </section>

        <PlaceholderSection n={4} title="Review for ontology (the FCDO-style pass)" slice="O48" />
        <PlaceholderSection n={5} title="Related nodes in the structured graph" slice="O49" />
        <PlaceholderSection n={6} title="Agent first-pass correlation" slice="O49" />
        <PlaceholderSection n={7} title="Confirm → admin review → (gated) load" slice="O50" />
        <PlaceholderSection n={8} title="Reviewer-quality signal + admin block" slice="O51" />
      </div>
    </div>
  )
}
