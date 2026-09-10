import { useMemo } from 'react'

import type { Completeness } from './completeness'
import { isResolved, useGraphQuery, type GraphQueryOptions, type QueryFailure } from './graphAccess'
import { validateRows, type RowShape } from './rowShape'

// WEB19 — the shared read: typed rows and their completeness, or a reason there
// are none. One hook, four migrations, and a `ready` state that cannot be
// constructed without the envelope.
//
// WHAT IT REPLACES, and why the replacement is the fix rather than a tidy-up.
// Four surfaces each carried the same twenty lines: a `useEffect`, a
// `let live = true` guard, a `.then` that ran `validateRows` and a `Load` union
// whose ready arm was `{ state: 'ready'; rows }`. That union is where the
// envelope died — it had nowhere to put the flag, so the flag was dropped at the
// line that built it, one line after the server sent it. Fixing the four call
// sites without fixing the union would have left the fifth surface to make the
// same mistake, which is what happened on 2026-09-06, one day after the contract
// landed (review 2026-09-09, L1-1(b)).
//
// THREE THINGS IT INHERITS from useGraphQuery rather than re-implementing, each
// of which the hand-rolled effects did NOT have: a deadline, a real abort on
// unmount, and in-flight dedupe so two panes reading one spec run it once.
//
// A SHAPE FAILURE IS AN ERROR HERE, not an empty result. The graph answered and
// the contract moved; rendering zero rows would report that as "nothing is
// there", which is the one thing WEB6 exists to stop. Surfaces that want to
// degrade rather than shout (the intake pickers) read the reason and choose.

export type SpecRowsFailure = QueryFailure | 'shape'

/** The read, as three states. `ready` carries the rows AND their completeness,
 *  and there is no arm that carries rows without it. An empty answer is `ready`
 *  with zero rows: the graph answered, and the answer was none — a success, and
 *  a complete one. */
export type SpecRows<T> =
  | { state: 'loading' }
  | { state: 'error'; reason: SpecRowsFailure; message: string }
  | { state: 'ready'; rows: T[]; completeness: Completeness }

/** Run a QuerySpec, check its columns, and get back rows with their envelope.
 *
 * The shape travels with the type parameter (WEB6), so the hook cannot be called
 * for a row type nobody declared columns for.
 */
export function useSpecRows<T>(
  specId: string,
  shape: RowShape<T>,
  params: Record<string, unknown> = {},
  opts: GraphQueryOptions = {},
): SpecRows<T> {
  const query = useGraphQuery(specId, params, opts)
  // Memoised on the result identity: useGraphQuery returns a stable object per
  // fetch, so the column check runs once per answer rather than once per
  // keystroke in a filter box above it.
  return useMemo<SpecRows<T>>(() => {
    if (!isResolved(query)) {
      return query.status === 'loading'
        ? { state: 'loading' }
        : { state: 'error', reason: query.reason, message: query.message }
    }
    const checked = validateRows<T>(query.data, shape)
    if (!checked.ok) return { state: 'error', reason: 'shape', message: checked.message }
    return { state: 'ready', rows: checked.rows, completeness: checked.completeness }
  }, [query, shape])
}

/** The rows if there are any, else none — for the surfaces that derive from an
 *  empty list either way and let the error channel carry the difference. */
export function rowsOfSpec<T>(state: SpecRows<T>): T[] {
  return state.state === 'ready' ? state.rows : []
}
