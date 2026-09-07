import { useCallback, useEffect, useMemo, useState } from 'react'
import type { IntakeApi, IntakeRecord, IntakeRow } from '../lib/intakeApi'
import {
  NO_PROPOSED_BINDINGS,
  RETURN_TO,
  WAITING_ON,
  reviewQueue,
  reviewSides,
  returnNoteIsUsable,
  type Fact,
} from '../lib/intakeReview'
import IdChip from './ui/IdChip'
import StatusChip from './ui/StatusChip'
import IntakeStepper from './IntakeStepper'
import ThreadDiff from './ThreadDiff'

// O50 — section 7 of docs/design/ui-exploration/sme-intake-page-plan.md: the
// admin review queue.
//
// THE SERVER OWNS THE MACHINE. Every action button below comes from the
// selected record's `legal_transitions.transitions`; this file contains no list
// of legal hops and no role check of its own. That is the 2026-08-06 ruling the
// stepper already follows, and the reason the note requirement is enforced HERE
// only as convenience — the rule is `transition()`'s 422.
//
// NOTHING ON THIS SURFACE WRITES THE GRAPH. Accept moves a SQLite row to
// `admin-accepted` and stops; the load is Q10's, behind G31/G32. The parked
// group exists so that boundary is visible rather than implied.

function FactList({ facts, empty }: { facts: Fact[]; empty: string }) {
  if (facts.length === 0) return <p className="text-xs text-faint">{empty}</p>
  return (
    <dl className="flex flex-col gap-1 text-xs">
      {facts.map((f) => (
        <div key={f.label} className="flex gap-2">
          <dt className="min-w-32 shrink-0 text-muted">{f.label}</dt>
          <dd className="break-all">
            {f.value === null ? (
              // Never a blank cell and never a guess: the SME may leave a level
              // unknown on purpose (Q10 — unattributable context lands
              // unassigned rather than attributed to somewhere plausible).
              <span className="text-faint">not supplied</span>
            ) : (
              f.value
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function QueueRow({
  row,
  selected,
  onSelect,
}: {
  row: IntakeRow
  selected: boolean
  onSelect: () => void
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-current={selected ? 'true' : undefined}
        className={`w-full rounded border px-2 py-1.5 text-left text-xs hover:border-blue-bright ${
          selected ? 'border-blue-bright bg-panel-2' : 'border-edge-soft bg-panel'
        }`}
      >
        <span className="flex items-center gap-2">
          <IdChip id={row.intake_id} />
          <span className="text-muted">{row.context_type}</span>
        </span>
        <span className="mt-0.5 block text-faint">
          {row.created_by} · {row.created_at}
        </span>
      </button>
    </li>
  )
}

export default function IntakeReviewQueue({ api }: { api: IntakeApi }) {
  const [rows, setRows] = useState<IntakeRow[] | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [record, setRecord] = useState<IntakeRecord | null>(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // the api identity changes with the persona, which is when the queue's
  // contents change too (list_intakes is role-scoped server-side)
  const load = useCallback(async () => {
    try {
      setRows(await api.list())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setRows([])
    }
  }, [api])

  useEffect(() => {
    void load()
  }, [load])

  const queue = useMemo(() => reviewQueue(rows ?? []), [rows])

  async function select(intakeId: string) {
    setSelectedId(intakeId)
    setNote('')
    setError(null)
    setRecord(null)
    try {
      // WEB8: the queue rows carry NO evidence — `list_intakes` never touches
      // the evidence table — so the review panel reads the record whole. The
      // types say so now, which is what stops this being a runtime surprise.
      setRecord(await api.get(intakeId))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function act(to: string) {
    if (!record) return
    setBusy(true)
    setError(null)
    try {
      await api.transition(record.intake_id, to, to === RETURN_TO ? note : '')
      setSelectedId(null)
      setRecord(null)
      setNote('')
      await load()
    } catch (e) {
      // VERBATIM. The server's 422 text ("a return goes back with a note — the
      // SME needs the why") is the rule speaking; paraphrasing it here would
      // put a second, drifting copy of the rule on the screen.
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const sides = record ? reviewSides(record) : null
  const actions = record?.legal_transitions.transitions ?? []
  const returnAction = actions.find((t) => t.to === RETURN_TO)

  return (
    <div className="flex flex-col gap-3 md:flex-row">
      <div className="md:w-64 md:shrink-0">
        <div className="mb-2 flex flex-wrap gap-1">
          <StatusChip count={queue.awaiting.length} label="to review" token="--teal" />
          <StatusChip count={queue.parked.length} label="parked" token="--yellow" />
        </div>
        {rows === null && <p className="text-xs text-faint">Loading the queue…</p>}
        {rows !== null && (
          <>
            <h3 className="mb-1 text-xs font-semibold text-muted">Awaiting review</h3>
            {queue.awaiting.length === 0 ? (
              <p className="text-xs text-faint">
                Nothing confirmed is waiting. Records reach this rail at{' '}
                <code>sme-confirmed</code>.
              </p>
            ) : (
              <ul className="flex flex-col gap-1">
                {queue.awaiting.map((r) => (
                  <QueueRow
                    key={r.intake_id}
                    row={r}
                    selected={r.intake_id === selectedId}
                    onSelect={() => void select(r.intake_id)}
                  />
                ))}
              </ul>
            )}
            <h3 className="mb-1 mt-3 text-xs font-semibold text-muted">
              Accepted — waiting on gate
            </h3>
            {queue.parked.length === 0 ? (
              <p className="text-xs text-faint">None parked.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {queue.parked.map((r) => (
                  <QueueRow
                    key={r.intake_id}
                    row={r}
                    selected={r.intake_id === selectedId}
                    onSelect={() => void select(r.intake_id)}
                  />
                ))}
              </ul>
            )}
            <ul className="mt-1 flex flex-col gap-0.5 text-xs" style={{ color: 'var(--yellow)' }}>
              {WAITING_ON.map((w) => (
                <li key={w.gate}>
                  {w.what} — {w.gate}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="min-w-0 flex-1">
        {error && (
          <p className="mb-2 text-xs" style={{ color: 'var(--status-fail-soft)' }}>
            {error}
          </p>
        )}
        {!record && <p className="text-xs text-faint">Select a record to review it.</p>}
        {record && sides && (
          <div className="flex flex-col gap-3">
            {/* The full machine, rendered for CONTEXT — the acceptance asks for
                it in the ui-conventions StatusChip vocabulary, and the stepper
                is where that vocabulary already lives. Its action row is off:
                the Decision section below owns the buttons, because Send-back
                carries the note rule. Both read the same server map. */}
            <IntakeStepper
              status={record.status}
              legal={record.legal_transitions}
              busy={busy}
              showActions={false}
            />
            <div className="grid gap-3 md:grid-cols-2">
              <section className="rounded border border-edge-soft p-2">
                <h3 className="mb-1 text-xs font-semibold">What the SME confirmed</h3>
                <FactList facts={sides.confirmed} empty="Nothing recorded." />
              </section>
              <section className="rounded border border-edge-soft p-2">
                <h3 className="mb-1 text-xs font-semibold">What the extractor proposed</h3>
                {/* The honest empty state, not a blank pane — see
                    NO_PROPOSED_BINDINGS for why it is a sentence and not a
                    manufactured delta. */}
                {sides.proposed === null ? (
                  <p className="text-xs text-faint">{NO_PROPOSED_BINDINGS}</p>
                ) : (
                  <FactList facts={sides.proposed} empty="The extractor proposed nothing." />
                )}
                <h4 className="mb-1 mt-2 text-xs font-semibold text-muted">
                  What the parser read off the evidence
                </h4>
                <FactList
                  facts={sides.extracted}
                  empty="No evidence uploaded, or nothing parsable in it."
                />
              </section>
            </div>

            {sides.threadDelta && (
              <section className="rounded border border-edge-soft p-2">
                <h3 className="mb-1 text-xs font-semibold">
                  Thread delta — machine proposed, SME disposed
                </h3>
                <p className="mb-1 text-xs text-muted">
                  SME ruling: {sides.threadDecision ?? 'not yet decided'}
                </p>
                <ThreadDiff delta={sides.threadDelta} />
              </section>
            )}

            <section className="rounded border border-edge-soft p-2">
              <h3 className="mb-1 text-xs font-semibold">Decision</h3>
              {returnAction && (
                <label className="mb-2 flex flex-col gap-1 text-xs">
                  <span className="text-muted">
                    Note (required to {returnAction.action.toLowerCase()})
                  </span>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    rows={2}
                    className="rounded border border-edge-soft bg-panel px-2 py-1 text-sm"
                  />
                </label>
              )}
              <div className="flex flex-wrap gap-2">
                {actions.map((t) => (
                  <button
                    key={t.to}
                    type="button"
                    disabled={busy || (t.to === RETURN_TO && !returnNoteIsUsable(note))}
                    onClick={() => void act(t.to)}
                    className="rounded border border-edge-soft bg-panel px-2 py-1 text-xs hover:border-blue-bright disabled:opacity-50"
                    title={`→ ${t.to}`}
                  >
                    {t.action}
                  </button>
                ))}
                {actions.length === 0 && (
                  <span className="text-xs text-faint">
                    No actions at <code>{record.status}</code> for your role.
                  </span>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
