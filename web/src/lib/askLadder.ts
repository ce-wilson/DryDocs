// O63 — the Ask failure ladder, as a pure function.
//
// WHY A REDUCER AND NOT A COMPONENT. The acceptance asks for a test over the
// ladder's STATE MACHINE rather than its copy, and a state machine tangled into
// JSX can only be tested by rendering it and reading strings back — which is a
// test of the copy, exactly what was ruled against. So the machine is
// `ladderStages(originalError, probe)`, a pure function of two inputs, and the
// component renders whatever it returns.
//
// THE STAGE ORDER HAS A TRAP THE CLAUSES DO NOT SPELL OUT. Clause (d) says "if
// the transport is green, the NEXT stage's error is surfaced as-is" — which
// reads like a sequence of fresh requests. It is not. The originating error has
// ALREADY arrived (it is the failed turn's own error), so the ladder never
// re-runs the question: it renders that error verbatim, probes the services
// once, and REINTERPRETS the failure against what the probe found. One probe,
// no retry, and the person's question is not silently asked again.

import type { ProbeResult, ServiceVerdict } from './serviceProbe'

/** The hand-off text (clause e).
 *
 *  RULED AT BUILD TIME, as the item asked. It stays a PLAIN STRING with no
 *  link: this is the producer console, where "support" is the person reading
 *  the screen, and inventing a destination would be inventing a fact. If it
 *  should ever resolve somewhere it becomes config on the
 *  VITE_RUNTIME_VIEW_URL_TEMPLATE precedent — unset means no affordance renders
 *  — and a company hostname is never committed here. */
export const SUPPORT_HANDOFF = 'contact DryDocs support'

export type LadderStage =
  /** (a) The browser's own words, never re-worded. */
  | { kind: 'original'; text: string }
  /** (b) A probe is in flight. Visibly distinct from any verdict. */
  | { kind: 'checking' }
  /** (c)/(d) One service's verdict, its detail carried verbatim. */
  | { kind: 'service'; verdict: ServiceVerdict }
  /** (e) The checks stopped being self-serviceable. */
  | { kind: 'handoff'; text: string }

/**
 * The ladder for a failed turn.
 *
 * `probe` is null while the probe has not finished — which is the `checking`
 * state, and the reason it is a separate input rather than a flag on the
 * result: a slow probe must never look like a verdict (clause b).
 *
 * Only services that say something USEFUL are rendered. A green api and a green
 * graph are not news on a page whose Ask call just failed — they are the
 * services every other page already proved working — so the ladder shows the
 * two that are specific to Ask (agent, provider) plus anything actually down.
 * The alternative, four rows of mostly green, buries the one row that matters.
 */
export function ladderStages(originalError: string, probe: ProbeResult | null): LadderStage[] {
  // (a) FIRST and VERBATIM. Not re-worded, not prefixed, not "friendlied":
  // "Failed to fetch" is what the reader will paste into a search or a ticket,
  // and the browser's own wording is the honest report of what the browser saw.
  const stages: LadderStage[] = [{ kind: 'original', text: originalError }]

  if (probe === null) {
    stages.push({ kind: 'checking' })
    return stages
  }

  const shown = probe.services.filter(
    (s) => s.state === 'down' || s.id === 'agent' || s.id === 'provider',
  )
  for (const verdict of shown) stages.push({ kind: 'service', verdict })

  // (e) Nothing the reader can act on: every check that ran came back ok, so
  // the ladder has run out of self-serviceable answers. A `not-checked` does
  // NOT earn a hand-off — it means the question was never asked, and telling
  // someone to contact support because a probe was skipped is the invented
  // verdict rule 1 forbids, wearing a different hat.
  if (!probe.services.some((s) => s.state === 'down')) {
    stages.push({ kind: 'handoff', text: SUPPORT_HANDOFF })
  }
  return stages
}
