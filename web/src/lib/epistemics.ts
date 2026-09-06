// R15: the epistemic label's hover text, and the cause shape it reads.
//
// A `.ts` beside the other seam types, not inside EpistemicBadge.tsx: the
// component file exports only the component (fast refresh, `--max-warnings 0`),
// and the wording of the hover text is testable without rendering anything.
//
// The text names the causes AS THEY ARRIVED — cause class, concrete detail (a
// planned vocabulary entry id, a probe class), and the count when one was
// measured. It paraphrases nothing: "partial", "incomplete", "approximate"
// would each be a second vocabulary for one fact.

export interface EpistemicCause {
  cause: string
  detail: string
  count?: number | null
}

export function describeCauses(causes: EpistemicCause[] | null | undefined): string {
  if (!causes || causes.length === 0) return 'Every cause this walk declares measured zero.'
  return (
    'The rows are a floor, not the whole answer. Causes: ' +
    causes
      .map((c) => `${c.cause} (${c.detail}${c.count === null || c.count === undefined ? '' : `: ${c.count}`})`)
      .join('; ')
  )
}
