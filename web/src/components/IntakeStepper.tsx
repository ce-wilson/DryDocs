import type { LegalTransitions } from '../lib/intakeApi'

// The O47 intake status machine, rendered — adapted from LoadsTimeline's
// dot-and-rail (ordered stage array, one status dot per stage, ui-conventions
// §1 tokens). Action buttons render from the API's legal-transitions map, so
// the client carries NO workflow knowledge of its own (decided 2026-08-06:
// no client-side workflow library — the server's map IS the workflow).

/** The ordered happy path (drydocs_api/intake.py STATUSES). `admin-returned`
 *  is a bounce, not a stage: it renders as a fail-soft marker on the draft
 *  stage the record returns to. `no-new-value` is the terminal alternative. */
const STAGES = [
  { id: 'draft', label: 'Draft' },
  { id: 'ontology-reviewed', label: 'Ontology reviewed' },
  { id: 'correlated', label: 'Correlated' },
  { id: 'sme-confirmed', label: 'SME confirmed' },
  { id: 'admin-accepted', label: 'Admin accepted' },
  { id: 'loaded', label: 'Loaded' },
] as const

function stageToken(stageIdx: number, currentIdx: number, status: string): string {
  // ui-conventions §1: done → green, active → teal, pending → muted;
  // a returned or dead-ended record marks its active stage fail-soft
  // (never brand --red, DL-2).
  if (status === 'admin-returned' && stageIdx === 0) return '--status-fail-soft'
  if (status === 'no-new-value' && stageIdx === currentIdx) return '--status-fail-soft'
  if (stageIdx < currentIdx) return '--green'
  if (stageIdx === currentIdx) return '--teal'
  return '--muted'
}

export default function IntakeStepper({
  status,
  legal,
  busy,
  onTransition,
}: {
  status: string
  legal: LegalTransitions
  busy: boolean
  onTransition: (to: string) => void
}) {
  // admin-returned re-queues to the front; no-new-value dead-ends where it was.
  const currentIdx =
    status === 'admin-returned' ? 0 : Math.max(0, STAGES.findIndex((s) => s.id === status))

  return (
    <div>
      <ol className="flex flex-wrap items-center gap-1">
        {STAGES.map((s, i) => {
          const token = stageToken(i, currentIdx, status)
          return (
            <li key={s.id} className="flex items-center gap-1">
              {i > 0 && <span aria-hidden className="h-px w-4 bg-edge-soft" />}
              <span
                className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs"
                style={{ borderColor: `var(${token})`, color: `var(${token})` }}
                aria-current={i === currentIdx ? 'step' : undefined}
              >
                <span
                  aria-hidden
                  className="h-2 w-2 rounded-full"
                  style={{ background: `var(${token})` }}
                />
                {s.label}
              </span>
            </li>
          )
        })}
      </ol>
      {status === 'admin-returned' && (
        <p className="mt-1 text-xs" style={{ color: 'var(--status-fail-soft)' }}>
          Returned by admin — back at draft for rework.
        </p>
      )}
      {status === 'no-new-value' && (
        <p className="mt-1 text-xs text-faint">
          Closed: no new value over the prior thread. Nothing was proposed.
        </p>
      )}
      {legal.waiting_on_gate && (
        <p className="mt-1 text-xs text-faint">Waiting on the gated load (O50 slice — parked).</p>
      )}
      <div className="mt-2 flex flex-wrap gap-2">
        {legal.transitions.map((t) => (
          <button
            key={t.to}
            type="button"
            disabled={busy}
            onClick={() => onTransition(t.to)}
            className="rounded border border-edge-soft bg-panel px-2 py-1 text-xs hover:border-blue-bright disabled:opacity-50"
            title={`→ ${t.to}`}
          >
            {t.action}
          </button>
        ))}
        {legal.transitions.length === 0 && !legal.terminal && !legal.thread_decision_required && (
          <span className="text-xs text-faint">No actions for your role at this stage.</span>
        )}
      </div>
    </div>
  )
}
