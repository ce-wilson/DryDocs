// ONE VOCABULARY OF EPISTEMIC STATUS, for every surface that renders a graded
// answer (R15). The label is the SERVER's: `exact` when every cause the spec's
// walk declares measured zero, `lower-bound` when one fired, and null when the
// spec declares no walk at all. This component renders the string it is given
// and never re-words it — "partial", "incomplete", "approximate" would each be
// a second vocabulary for one fact, which is the drift TruncationBadge exists
// to prevent for completeness.
//
// A null label renders NOTHING. Silence is the honest default for a spec that
// has not said what its walk can miss; a badge reading EXACT there would be a
// claim nobody made (the GitNexus failure — a partial graph presented whole).
//
// The hover text names the causes, machine-readably as they arrived: the cause
// class, the concrete detail (a planned vocabulary entry id, a probe class),
// and the count when one was measured. Zero rows under LOWER-BOUND therefore
// reads "nothing visible to this walk, because …" and never "none exist".

import { describeCauses, type EpistemicCause } from '../../lib/epistemics'

export interface EpistemicBadgeProps {
  /** 'exact' | 'lower-bound' | null (ungraded — renders nothing). */
  epistemic: string | null | undefined
  /** What limited the walk; empty for an exact answer. */
  causes?: EpistemicCause[] | null
}

export default function EpistemicBadge({ epistemic, causes }: EpistemicBadgeProps) {
  if (epistemic === null || epistemic === undefined) return null
  const bounded = epistemic === 'lower-bound'
  return (
    <span
      className={
        bounded
          ? 'rounded-xs border border-yellow px-1.5 py-0.5 font-mono text-[10px] text-yellow'
          : 'rounded-xs border border-faint px-1.5 py-0.5 font-mono text-[10px] text-faint'
      }
      title={describeCauses(causes)}
      data-epistemic={epistemic}
    >
      {epistemic}
    </span>
  )
}
