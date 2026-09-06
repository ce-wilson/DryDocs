import { useEffect, useRef } from 'react'

import type { SpecResult } from '../lib/graph'
import { useGraphQuery, type GraphQueryOptions, type QueryFailure } from './graphAccess'

// WEB1 — provenance of rendered data is a typed union.
//
// THE DEFECT (review 2026-09-05, finding A5, ranked second overall and first by
// the architecture pass): five routes implemented try-live-else-synthetic and
// each expressed it differently. SpecGrid and LoadsRoute swallowed the failure
// and substituted demo rows behind a badge; SpecGraphPane and CorpusStatus
// refused to render; OverviewRoute caught and discarded the error deliberately;
// MappingsRoute kept a separate apiDown string. Empty-result and request-failed
// were the same condition in some and different in others.
//
// WHY THAT MATTERS MORE HERE THAN IT WOULD ELSEWHERE. The product thesis is
// provenance. The console carries a TrustLegend, SYNTHESIZED watermarks and
// classification banners — and the single most important trust signal, whether
// the numbers on screen came from the graph or from a constant in the bundle,
// was decided ad hoc in five places with five presentations. A module that
// degrades to demo data without saying so clearly is the exact failure the rest
// of the provenance machinery exists to prevent.
//
// So there is ONE way now, and a source scan (provenance.test.ts) makes it the
// only way — the same enforcement shape the parent repo uses for render parsing
// (J37) and code-not-prose reads (J66): the seam is the only path because a
// test says so, not because a comment asks.

/** Why the rendered rows are demo rows. Kept distinct because they are
 *  different facts about the system, and a reader deserves to know which:
 *  `empty` means the graph answered and had nothing; `error` means it did not
 *  answer at all. Collapsing them is what the old fallbacks did. */
export type DemoReason = 'empty' | 'error'

/** Where the rows on screen came from.
 *
 * `empty` is a SUCCESS: the graph answered, and the answer was no rows. It
 * carries the result, because an empty frame still has a classification, a
 * cypher and a params echo to show. `error` never carries rows. */
export type Provenance<T> =
  | { status: 'loading' }
  | { status: 'live'; data: SpecResult; rows: T[] }
  | { status: 'empty'; data: SpecResult }
  | { status: 'demo'; rows: T[]; because: DemoReason; message: string | null }
  | { status: 'error'; message: string; reason: QueryFailure }

// ── the fallback counter (clause e) ─────────────────────────────────────────
//
// S8: when the API is unavailable, routes substitute synthetic demo data behind
// a badge and keep rendering. The application does not crash, does not error and
// does not stop — it quietly serves fabricated numbers, and there was no signal
// anywhere that would tell an operator this is happening. The fallback is
// designed so the page still looks healthy, which is exactly why it needs a
// count that is not on the page it is fabricating.

export interface FallbackCount {
  /** total activations this session */
  total: number
  /** per spec id, so an operator sees WHICH surface is fabricating */
  bySpec: Record<string, number>
  /** the most recent activation's reason and message, for the strip's detail */
  last: { specId: string; because: DemoReason; message: string | null } | null
}

let counts: FallbackCount = { total: 0, bySpec: {}, last: null }
const listeners = new Set<(c: FallbackCount) => void>()

export function fallbackCount(): FallbackCount {
  return counts
}

export function onFallback(fn: (c: FallbackCount) => void): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function recordFallback(specId: string, because: DemoReason, message: string | null): void {
  counts = {
    total: counts.total + 1,
    bySpec: { ...counts.bySpec, [specId]: (counts.bySpec[specId] ?? 0) + 1 },
    last: { specId, because, message },
  }
  for (const fn of listeners) fn(counts)
}

/** Test seam — a count is session-scoped state and must not leak between tests. */
export function __resetFallbackCount(): void {
  counts = { total: 0, bySpec: {}, last: null }
  for (const fn of listeners) fn(counts)
}

// ── the seam ────────────────────────────────────────────────────────────────

export interface LiveOrDemoOptions extends GraphQueryOptions {
  /** Render the demo rows when the graph answers with NO rows, not only when it
   *  fails. Default true: an unloaded database is the common case in this phase
   *  and a demo frame with a notice is more useful than an empty one. A surface
   *  where an empty answer is meaningful (a "nothing is broken" list) passes
   *  false and gets `empty`. */
  demoOnEmpty?: boolean
}

/** The ONE path from a QuerySpec to rendered rows, demo included.
 *
 * `demo` is the synthetic frame this surface falls back to, or null for a
 * surface that has none — in which case a failure stays an `error` and an empty
 * answer stays `empty`, and nothing is fabricated. Every activation of the demo
 * path is counted before it is returned.
 */
export function useLiveOrDemo<T>(
  specId: string,
  demo: readonly T[] | null,
  opts: LiveOrDemoOptions = {},
): Provenance<T> {
  const { demoOnEmpty = true, ...queryOpts } = opts
  const query = useGraphQuery(specId, {}, queryOpts)

  // The count is a side effect and belongs in an effect, keyed on the state that
  // caused it — counting during render would double-count under StrictMode and
  // re-count on every unrelated re-render.
  const because: DemoReason | null =
    demo === null
      ? null
      : query.status === 'error'
        ? 'error'
        : query.status === 'empty' && demoOnEmpty
          ? 'empty'
          : null
  const message = query.status === 'error' ? query.message : null
  const counted = useRef<string | null>(null)
  useEffect(() => {
    if (!because) {
      counted.current = null
      return
    }
    const key = `${specId}:${because}:${message ?? ''}`
    if (counted.current === key) return
    counted.current = key
    recordFallback(specId, because, message)
  }, [specId, because, message])

  if (query.status === 'loading') return { status: 'loading' }
  if (query.status === 'data') {
    return { status: 'live', data: query.data, rows: query.data.rows as unknown as T[] }
  }
  if (query.status === 'empty') {
    if (because === 'empty') return { status: 'demo', rows: [...demo!], because, message: null }
    return { status: 'empty', data: query.data }
  }
  if (because === 'error') return { status: 'demo', rows: [...demo!], because, message }
  return { status: 'error', message: query.message, reason: query.reason }
}

/** The rows to render, whatever their provenance — for the many call sites that
 *  draw the same table either way and let the badge carry the difference. */
export function rowsOf<T>(state: Provenance<T>): T[] {
  if (state.status === 'live' || state.status === 'demo') return state.rows
  return []
}
