import TruncationBadge from './TruncationBadge'
import { completenessTitle, type Completeness } from '../../data/completeness'

// WEB19 — the one render of a completeness envelope, for the surfaces that are
// not the grid.
//
// TruncationBadge (WEB2) already fixed the WORDING and the colour of a capped
// result. What it did not fix is the four-line conditional around it: shown,
// total, unit and a hand-written title sentence, re-decided at each call site.
// Three surfaces that predate the contract are being retrofitted at WEB20 and
// two more are migrating at WEB19, so that conditional was about to be written
// five more times. This is it, written once.
//
// IT RENDERS NOTHING WHEN THE RESULT IS COMPLETE, on purpose. A permanent
// "complete" chip would train a reader to stop looking at the place the warning
// appears, which is the one place it has to be noticed.
//
// `total` stays null: the server probes one row past the ceiling and answers
// "there was more", which is enough to say TRUNCATED and not enough to say how
// much more. See TruncationBadge's own note.

export interface CompletenessNoticeProps {
  completeness: Completeness
  /** What is being counted, for the badge and the sentence: 'rows', 'jobs'. */
  unit: string
  /** What the SURFACE calls its subject, singular: 'job', 'site', 'file'. */
  noun: string
}

export default function CompletenessNotice({ completeness, unit, noun }: CompletenessNoticeProps) {
  if (!completeness.truncated) return null
  return (
    <TruncationBadge
      shown={completeness.shown}
      total={null}
      unit={unit}
      title={completenessTitle(completeness, unit, noun)}
    />
  )
}
