// ONE VOCABULARY OF COMPLETENESS, for every surface that renders a capped
// result (WEB2, from review 2026-09-05 finding S1).
//
// The canvas got this right first: it declares NODE_CEILING, states that a
// silently-cropped picture is a lie, and renders a TRUNCATED n/N badge when the
// cap bites. The grid next door — reading the SAME spec results, through the
// same seam — showed `500/500 · drydocs · LIVE` on a 900-row answer and offered
// a button labelled "full". The wording, the placement and the colour now live
// here so the two surfaces cannot drift apart again by being edited separately.
//
// N IS OPTIONAL, AND THAT IS THE HONEST PART. The canvas knows the true total:
// it capped the nodes itself, after counting them. The grid never does — the
// server probes one row past the ceiling (API1) and answers "there was more",
// which is enough to say TRUNCATED and not enough to say how much more.
// Inventing an N for the grid would be a fabricated completeness claim, which
// is the exact defect this item exists to remove, so `total: null` renders
// `500+` instead. Anything that later learns the real count passes it.

export interface TruncationBadgeProps {
  /** How many are on screen. */
  shown: number
  /** How many there really are, or null when only "more than `shown`" is known. */
  total: number | null
  /** What is being counted, for the hover text: 'nodes', 'rows'. */
  unit: string
  /** The full sentence on hover — each surface names its own ceiling. */
  title: string
}

export default function TruncationBadge({ shown, total, unit, title }: TruncationBadgeProps) {
  return (
    <span
      className="rounded-xs border border-yellow px-1.5 py-0.5 font-mono text-[10px] text-yellow"
      title={title}
      data-truncated={unit}
    >
      TRUNCATED {shown}/{total === null ? `${shown}+` : total}
    </span>
  )
}
