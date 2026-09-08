// Reviewer-quality signals, client side (O51, intake plan §8).
//
// SEPARATE FROM graphApi.ts for the same reason dataCentersApi is: nothing here
// is a graph read. These are derived numbers about intake records, and the two
// POSTs are an admin decision about a person — putting either behind the
// QuerySpec client would blur the line ADR 0005 asks the console to keep visible.
//
// THE THRESHOLDS ARE NOT RESTATED HERE. Every limit arrives in the payload
// beside the metric it applies to, so this module never holds a copy of
// config/review-quality.yaml. A second copy is the thing that drifts, and a
// console that disagreed with the server about what "too fast" means would flag
// people the server did not.

import type { Schemas } from './apiClient'
import { createAuthedApi, unwrap } from './apiClient'
import { sessionId, sessionRejected, sessionToken } from './auth'

export type PersonaQuality = Schemas['PersonaQualityOut']
export type QualityFlag = Schemas['QualityFlagOut']
export type PersonaBlock = Schemas['PersonaBlockOut']
export type ReviewQuality = Schemas['ReviewQualityOut']

function authed(baseUrl: string) {
  return createAuthedApi(baseUrl, {
    token: sessionToken,
    sessionId,
    rejected: sessionRejected,
  })
}

export async function fetchReviewQuality(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<ReviewQuality> {
  const result = await authed(baseUrl).GET('/review-quality', { signal })
  if (result.response.status === 401) throw new Error('the server refused this session')
  if (result.response.status === 403) throw new Error('reviewer quality is admin-only')
  return unwrap(result, 'review-quality')
}

export async function blockPersona(
  baseUrl: string,
  personaId: string,
  reason: string,
): Promise<PersonaBlock> {
  return unwrap(
    await authed(baseUrl).POST('/review-quality/block', {
      body: { persona_id: personaId, reason },
    }),
    'review-quality block',
  )
}

export async function unblockPersona(
  baseUrl: string,
  personaId: string,
  note: string,
): Promise<PersonaBlock> {
  return unwrap(
    await authed(baseUrl).POST('/review-quality/unblock', {
      body: { persona_id: personaId, note },
    }),
    'review-quality unblock',
  )
}

/** A rate as a whole percentage, or the em-dash for a rate that has none.
 *
 *  `null` and `0` must never render the same way. The auto-accept rate is null
 *  everywhere today because its source does not exist yet (O48), and printing
 *  it as `0%` would read as a reviewer who modifies every candidate — the best
 *  possible score, invented out of no data. */
export function ratePercent(rate: number | null | undefined): string {
  return rate === null || rate === undefined ? '—' : `${Math.round(rate * 100)}%`
}

/** A duration in seconds as a short human string; the em-dash for no reading.
 *  A record whose hand-over moment predates the event log has no measurable
 *  review time, which is not the same as a fast one. */
export function durationLabel(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—'
  if (seconds < 90) return `${Math.round(seconds)}s`
  if (seconds < 5400) return `${Math.round(seconds / 60)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

/** True when the reviewer has enough decisions in the window for a rate to
 *  mean anything. The server already suppresses the FLAG below this floor; the
 *  console uses the same number to say why a flagged-looking rate carries no
 *  flag, rather than leaving the reader to wonder. */
export function hasEnoughDecisions(persona: PersonaQuality, floor: number): boolean {
  return persona.submissions >= floor
}

/** The reviewers a rail should show: flagged or blocked, by persona id.
 *
 *  ORDERED BY ID, never by worst-first. The plan's words are "coaching and
 *  triage, not a leaderboard", and a list sorted by the worst number is a
 *  leaderboard whatever the heading above it says. */
export function railRows(personas: readonly PersonaQuality[]): PersonaQuality[] {
  return personas
    .filter((p) => p.flags.length > 0 || p.blocked)
    .slice()
    .sort((a, b) => a.persona_id.localeCompare(b.persona_id))
}

/** How full a meter should read for a rate against its limit: 100% when the
 *  rate is AT the limit, so the fill is "how much of the allowance is used".
 *  Clamped, because a rate of twice the limit is still a full meter. */
export function meterValue(rate: number, limit: number): number {
  if (limit <= 0) return rate > 0 ? 100 : 0
  return Math.max(0, Math.min(100, (rate / limit) * 100))
}

/** The metric names the server can flag on, in the order a panel lists them.
 *  `auto_accept_rate` is deliberately absent: a metric with no source must not
 *  flag a person, and a console that left room for it here would be the first
 *  place someone added it back. */
export const FLAGGABLE_METRICS = ['too_fast_rate', 'admin_return_rate'] as const

export const METRIC_LABELS: Readonly<Record<string, string>> = {
  too_fast_rate: 'Too fast',
  admin_return_rate: 'Returned by admin',
  auto_accept_rate: 'Auto-accept',
}
