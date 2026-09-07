// O51 — the admin queue's quality rail: who tripped a limit, and which one.
//
// WHAT A RAIL IS FOR. Not a score, and not a ranking: a short list of the
// reviewers a person should look at next, each carrying the metric that put
// them there and the limit it was compared against. The plan's own words for
// the surface are "coaching and triage, not a leaderboard", so rows are ordered
// by persona id and no cell holds a rank.
//
// EVERY NUMBER COMES FROM THE SERVER, including the limits. The console holds
// no copy of config/review-quality.yaml — see lib/reviewQuality.ts for why.
//
// THE RAIL NEVER BLOCKS ANYONE. It renders the flag and, when the admin asks
// for one, selects the reviewer; the block lives on the panel, behind a reason
// field, and is an admin action in the API. A rail with a block button would
// put the decision one accidental click from a measurement.

import Meter from './ui/Meter'
import StatusChip from './ui/StatusChip'
import type { PersonaQuality } from '../lib/reviewQuality'
import { METRIC_LABELS, meterValue, railRows, ratePercent } from '../lib/reviewQuality'

export default function QualityRail({
  personas,
  selectedId,
  onSelect,
}: {
  personas: readonly PersonaQuality[]
  selectedId?: string | null
  onSelect?: (personaId: string) => void
}) {
  const rows = railRows(personas)

  if (rows.length === 0) {
    return (
      <p className="text-xs text-muted">
        No reviewer has crossed a limit in this window, and none is blocked. The rail lists only
        reviewers a limit has flagged — an empty rail is the ordinary state, not a missing read.
      </p>
    )
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Reviewers flagged in this window">
      {rows.map((persona) => {
        const selected = persona.persona_id === selectedId
        return (
          <li key={persona.persona_id}>
            <button
              type="button"
              onClick={() => onSelect?.(persona.persona_id)}
              aria-pressed={selected}
              className={
                'flex w-full flex-col gap-1 rounded border px-3 py-2 text-left ' +
                (selected ? 'border-teal' : 'border-edge-soft')
              }
            >
              <span className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-semibold text-text">
                  {persona.persona_id}
                </span>
                {persona.blocked && (
                  <StatusChip
                    count={1}
                    label="blocked"
                    token="--status-fail-soft"
                    title="An admin has blocked this reviewer from submitting. Their drafts are unaffected."
                  />
                )}
                <StatusChip
                  count={persona.submissions}
                  label="submissions"
                  token="--muted"
                  title="Submissions in the rolling window"
                />
              </span>

              {persona.flags.map((flag) => (
                <span key={flag.metric} className="flex flex-wrap items-center gap-2">
                  <StatusChip
                    count={Math.round(flag.value * 100)}
                    label={`% ${METRIC_LABELS[flag.metric] ?? flag.metric}`}
                    token="--yellow"
                    title={flag.detail}
                  />
                  <Meter
                    value={meterValue(flag.value, flag.limit)}
                    threshold={101}
                    label={`${flag.metric} against its limit`}
                  />
                  <span className="text-[11px] text-muted">
                    limit {ratePercent(flag.limit)} — {flag.detail}
                  </span>
                </span>
              ))}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
