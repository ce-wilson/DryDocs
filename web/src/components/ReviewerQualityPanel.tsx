// O51 — the admin-only reviewer panel: the four signals for one person, and the
// block that only a person can place.
//
// THE ORDER OF THE SURFACE IS THE ORDER OF THE ARGUMENT. Numbers first, with
// the window they were measured over; then the flags, each naming its limit;
// then the block, last, behind a required reason. A block button above the
// numbers would invite the decision before the reading.
//
// AUTO-ACCEPT RENDERS ITS REASON, NOT A DASH ALONE. The metric has no source
// until O48 builds the candidate-binding set, and a bare em-dash would read as
// a display bug. The server sends the sentence; this prints it.
//
// NO AUTO-BLOCK ANYWHERE IN THIS FILE. The block is one call, from one button,
// which is disabled until an admin has typed a reason. Nothing watches a
// threshold and nothing calls the API on a render.

import { useState } from 'react'

import StatTiles from './StatTiles'
import Meter from './ui/Meter'
import StatusChip from './ui/StatusChip'
import type { PersonaBlock, PersonaQuality } from '../lib/reviewQuality'
import { METRIC_LABELS, durationLabel, meterValue, ratePercent } from '../lib/reviewQuality'

export default function ReviewerQualityPanel({
  persona,
  windowDays,
  minDecisionsForFlag,
  block,
  onBlock,
  onUnblock,
  busy = false,
  error,
}: {
  persona: PersonaQuality
  windowDays: number
  minDecisionsForFlag: number
  block?: PersonaBlock | null
  onBlock?: (personaId: string, reason: string) => void
  onUnblock?: (personaId: string, note: string) => void
  busy?: boolean
  error?: string | null
}) {
  const [reason, setReason] = useState('')
  const [note, setNote] = useState('')

  const belowFloor = persona.submissions < minDecisionsForFlag

  return (
    <section
      className="flex flex-col gap-4"
      aria-label={`Reviewer quality — ${persona.persona_id}`}
    >
      <header className="flex flex-wrap items-center gap-2">
        <h3 className="font-mono text-sm font-semibold text-text">{persona.persona_id}</h3>
        {persona.blocked && (
          <StatusChip count={1} label="blocked from submitting" token="--status-fail-soft" />
        )}
        <span className="text-[11px] text-muted">last {windowDays} days</span>
      </header>

      <StatTiles
        tiles={[
          { label: 'Submissions', value: String(persona.submissions) },
          {
            label: 'Auto-accept',
            value: ratePercent(persona.auto_accept_rate),
          },
          { label: 'Too fast', value: ratePercent(persona.too_fast_rate) },
          { label: 'Returned', value: ratePercent(persona.admin_return_rate) },
          {
            label: 'Median review',
            value: durationLabel(persona.median_review_seconds),
          },
        ]}
      />

      <p className="text-[11px] text-muted">
        <span className="font-semibold">Auto-accept is not measured yet.</span>{' '}
        {persona.auto_accept_unavailable_because}
      </p>

      {belowFloor && (
        <p className="text-[11px]" style={{ color: 'var(--yellow)' }}>
          Fewer than {minDecisionsForFlag} decisions in this window, so nothing here is flagged:
          rates over a handful of submissions describe the handful, not the reviewer. The numbers
          are still shown — suppressing a flag is not the same as hiding the data.
        </p>
      )}

      {persona.flags.length > 0 && (
        <ul className="flex flex-col gap-2" aria-label="Limits crossed">
          {persona.flags.map((flag) => (
            <li key={flag.metric} className="flex flex-wrap items-center gap-2">
              <StatusChip
                count={Math.round(flag.value * 100)}
                label={`% ${METRIC_LABELS[flag.metric] ?? flag.metric}`}
                token="--yellow"
              />
              <Meter
                value={meterValue(flag.value, flag.limit)}
                threshold={101}
                label={`${flag.metric} against its limit`}
              />
              <span className="text-[11px] text-muted">
                limit {ratePercent(flag.limit)} — {flag.detail}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="rounded border border-edge-soft p-3">
        <p className="mb-2 text-[11px] text-muted">
          A limit flags; it never acts. Blocking stops this reviewer SUBMITTING — their drafts and
          uploads are unaffected — and the record keeps who, when and why.
        </p>

        {persona.blocked ? (
          <div className="flex flex-col gap-2">
            {block && (
              <p className="text-[11px] text-muted">
                Blocked {block.blocked_at} by {block.blocked_by}: {block.reason}
              </p>
            )}
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Note (required to lift)
              <input
                className="rounded border border-edge-soft bg-transparent px-2 py-1 text-xs text-text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="what changed"
              />
            </label>
            <button
              type="button"
              className="self-start rounded border border-edge-soft px-3 py-1 text-xs disabled:opacity-50"
              disabled={busy || note.trim().length === 0}
              onClick={() => onUnblock?.(persona.persona_id, note.trim())}
            >
              Lift the block
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <label className="flex flex-col gap-1 text-[11px] text-muted">
              Reason (required)
              <input
                className="rounded border border-edge-soft bg-transparent px-2 py-1 text-xs text-text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="what the reviewer is told"
              />
            </label>
            <button
              type="button"
              className="self-start rounded border border-edge-soft px-3 py-1 text-xs disabled:opacity-50"
              disabled={busy || reason.trim().length === 0}
              onClick={() => onBlock?.(persona.persona_id, reason.trim())}
            >
              Block from submitting
            </button>
          </div>
        )}

        {error && (
          <p className="mt-2 text-[11px]" style={{ color: 'var(--status-fail-soft)' }}>
            {error}
          </p>
        )}
      </div>
    </section>
  )
}
