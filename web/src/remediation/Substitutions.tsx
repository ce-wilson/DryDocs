import { useMemo, useState } from 'react'

import { PROFILE, PROFILE_NOTICE } from './profileData'
import { checkSlot, type ShapeVerdict } from './slotShapes'

// The SUBSTITUTIONS frame (O59): the half the census cannot produce.
//
// THE DIVISION THIS SURFACE EXISTS FOR — the machine reports what IS, the SME
// supplies what is NOT THERE. G68's slot list is the closed nine facts the
// Control-M export cannot carry, each arriving with its current value or the
// fact that it has none, the shape rule it must satisfy, and the jobs it
// would apply to.
//
// THE OUTPUT IS A PROPOSAL AND ONLY A PROPOSAL. Nothing on this page writes
// XML, a graph, or anything else: the export is a file the SME carries into
// the gate, and the equivalence proof is what consumes it downstream. The
// component holds the typed values in local state and hands them back — it
// has no writer to call, deliberately, because there is no ratified path from
// an SME's typing to an estate change and inventing one here would route
// around the gate.
//
// "NOT SUPPLIED" IS NEVER A DEFAULT. G68 makes an absent slot structurally
// unfakeable (`status: not-supplied` AND `value: null`, never "") and this
// frame renders that state as itself. A pre-filled guess is how a proposal
// becomes a wrong fact nobody re-checks — the exact failure the whole module
// exists to remove.
//
// THE SHAPE CHECK IS A TYPO CATCHER, NOT AN AUTHORITY. Four of the nine slots
// have no shape rule on the guidelines page, and those report `unchecked`
// rather than a green tick: see slotShapes.ts, which holds the reasoning and
// the patterns.

const VERDICT_TOKEN: Record<ShapeVerdict, string> = {
  ok: '--green',
  bad: '--status-fail-soft',
  unchecked: '--yellow',
  empty: '--muted',
}

function download(filename: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function Substitutions() {
  const slots = PROFILE.substitution_slots
  const [proposed, setProposed] = useState<Record<string, string>>({})

  const checks = useMemo(
    () => Object.fromEntries(slots.map((s) => [s.name, checkSlot(s.name, proposed[s.name] ?? '')])),
    [slots, proposed]
  )

  const answered = slots.filter((s) => (proposed[s.name] ?? '').trim()).length
  const bad = slots.filter((s) => checks[s.name].verdict === 'bad').length
  const open = slots.filter((s) => s.status === 'not-supplied').length

  const proposal = () => ({
    kind: 'substitution-proposal',
    status: 'PROPOSAL — not applied. Nothing wrote XML or a graph.',
    source: PROFILE.source,
    provenance: PROFILE.provenance,
    slots: slots.map((slot) => {
      const value = (proposed[slot.name] ?? '').trim()
      return {
        name: slot.name,
        home: slot.home,
        rule: slot.rule,
        current: slot.value,
        current_status: slot.status,
        // Absent stays absent in the export too: null, never "".
        proposed: value || null,
        shape_check: checks[slot.name].verdict,
        applies_to_jobs: slot.applies_to.length,
      }
    }),
  })

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        {PROFILE_NOTICE}
      </p>

      <div className="flex shrink-0 flex-wrap items-center gap-2 rounded border border-edge bg-panel-2 px-2.5 py-1.5 text-[11px]">
        <span className="text-muted">
          <span className="font-mono font-semibold tabular-nums text-text">
            {open}/{slots.length}
          </span>{' '}
          slots not supplied by the export ·{' '}
          <span className="font-mono font-semibold tabular-nums text-text">{answered}</span>{' '}
          answered here{' '}
          {bad > 0 && (
            <span className="ml-1 font-mono text-[var(--status-fail-soft)]">
              · {bad} fail their shape rule
            </span>
          )}
        </span>
        <button
          type="button"
          className="ml-auto rounded border border-edge bg-panel px-2 py-0.5 font-mono text-[11px] text-text hover:border-[var(--blue-br)]"
          onClick={() => download('substitution-proposal.json', JSON.stringify(proposal(), null, 2))}
        >
          Export proposal (.json)
        </button>
      </div>

      <p className="shrink-0 rounded border border-edge px-2.5 py-1 text-[10px] leading-snug text-muted">
        The export is a PROPOSAL the SME carries into the gate — never an applied change.
        Nothing on this page writes XML or a graph, by the module&rsquo;s standing invariant.
      </p>

      <div className="min-h-0 flex-1 space-y-1.5 overflow-auto pr-0.5">
        {slots.map((slot) => {
          const check = checks[slot.name]
          return (
            <div key={slot.name} className="rounded-md border border-edge">
              <div className="flex flex-wrap items-baseline gap-2 border-b border-edge bg-panel-2 px-2.5 py-1.5">
                <span className="font-mono text-[11px] font-semibold text-text">{slot.name}</span>
                <span className="font-mono text-[10px] text-muted">lives on the {slot.home}</span>
                <span className="ml-auto font-mono text-[10px] tabular-nums text-muted">
                  applies to {slot.applies_to.length} job
                  {slot.applies_to.length === 1 ? '' : 's'}
                </span>
              </div>

              <div className="grid gap-2 px-2.5 py-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <p className="text-[10px] font-semibold text-muted">In the export</p>
                  {slot.status === 'not-supplied' ? (
                    // Never a default and never a guess: the absence is the fact.
                    <p className="mt-0.5 font-mono text-[11px] text-yellow">not supplied</p>
                  ) : (
                    <p className="mt-0.5 font-mono text-[11px] text-text">{slot.value}</p>
                  )}
                  <p className="mt-1 text-[10px] leading-snug text-muted">{slot.rule}</p>
                </div>

                <div>
                  <label className="text-[10px] font-semibold text-muted" htmlFor={`slot-${slot.name}`}>
                    Proposed value
                  </label>
                  <input
                    id={`slot-${slot.name}`}
                    type="text"
                    className="mt-0.5 w-full font-mono text-xs"
                    placeholder={slot.status === 'not-supplied' ? 'not supplied' : 'leave blank to keep'}
                    value={proposed[slot.name] ?? ''}
                    onChange={(e) =>
                      setProposed((prev) => ({ ...prev, [slot.name]: e.target.value }))
                    }
                  />
                  {check.verdict !== 'empty' && (
                    <p
                      className="mt-0.5 font-mono text-[10px] leading-snug"
                      style={{ color: `var(${VERDICT_TOKEN[check.verdict]})` }}
                    >
                      {check.verdict === 'ok' ? 'matches its shape rule' : check.note}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
