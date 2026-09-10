import type { SpecResult } from '../lib/graph'

// WEB19 — the completeness envelope, as a value that travels WITH the rows.
//
// THE DEFECT (review 2026-09-09, L1-1(b)): `truncated` landed on the API
// response 2026-09-05 and a new consumer built 2026-09-06 dropped it on its
// first day. Not through carelessness — through the shape of the seam. The one
// helper every consumer already went through, `validateRows`, returned
// `{ ok: true, rows }`, so `checked.rows` was the natural thing to write and the
// envelope was gone by the time anyone could render it. A map that plots 500 of
// 3,000 hosts is not a map with a missing badge; it is a wrong picture of the
// estate, and a picture is the artifact a reader trusts without checking a row
// count.
//
// THE CORRECTION IS NOT A FOURTH IMPLEMENTATION of the badge. It is to make the
// envelope hard to drop: this type is REQUIRED on the success branch of the row
// check (rowShape.ts) and on the `ready` state of the shared read hook
// (useSpecRows.ts), so a surface that wants rows has already been handed the
// completeness of those rows and has to discard it deliberately.
//
// WHY A TYPE AND NOT A CONVENTION. Slot 10 of the module sweep counted six
// independent implementations of this contract and zero written conventions,
// with seven recurrences. A seventh convention would have been the eighth
// recurrence. A required field is checked by the compiler on every future
// consumer, including the ones nobody reviews.

/** How complete the rows are, as the SERVER answered it — never inferred.
 *
 *  `truncated` is the server's own probe at `limit + 1` (API1), not
 *  `rows.length === limit`, which is the guess that made a 500-row extract
 *  indistinguishable from a complete one. `limit` is the ceiling that applied,
 *  or null for a spec that declares none. `shown` is what the surface actually
 *  holds, which is not always `rows.length` on the wire: a map resolves rows
 *  against a gazetteer and can place fewer than it received. */
export interface Completeness {
  truncated: boolean
  shown: number
  limit: number | null
}

/** The envelope off a spec result. `shown` defaults to the rows that arrived;
 *  a surface that renders a subset of them passes its own count. */
export function completenessOf(result: SpecResult, shown: number = result.rows.length): Completeness {
  return { truncated: result.truncated, shown, limit: result.limit ?? null }
}

/** The same envelope for a source that HAS no ceiling — a fixed demo frame, a
 *  grid the server sends whole. Named rather than written inline as an object
 *  literal at each call site, because "this cannot be truncated" is a claim and
 *  a claim deserves one spelling that can be searched for. */
export function completeOf(shown: number): Completeness {
  return { truncated: false, shown, limit: null }
}

/** The hover sentence, in the vocabulary WEB2 fixed for TruncationBadge.
 *
 *  `unit` is what is being counted ('rows', 'jobs', 'sites'); `noun` is what the
 *  surface calls its own subject, so the sentence reads about the estate rather
 *  than about the query. The count on screen is described as what ARRIVED, never
 *  as what exists — the server answered "there is more" and not "how much more",
 *  and inventing the second is the fabricated completeness claim this whole
 *  mechanism exists to remove. */
export function completenessTitle(c: Completeness, unit: string, noun: string): string {
  if (!c.truncated) {
    return `Every ${noun} the query matched is on screen; the result fits under the server's ceiling.`
  }
  const cap =
    c.limit === null
      ? `This result was capped by the server`
      : `Capped at ${c.limit} ${unit}`
  return `${cap}; there are more ${unit} than are shown. The count is of what arrived, not of what exists.`
}
