import { createContext, useContext, useEffect, useRef, useState } from 'react'

import type { GraphAccess, SpecResult } from '../lib/graph'

// WEB12 — the console's data layer. One provider, one hook, and the forty
// transport preambles the review counted (A6, T6) delete themselves.
//
// WHAT WAS THERE: every route re-derived the API base URL from
// import.meta.env.VITE_API_URL with a localhost fallback (12 files, beside
// apiBaseUrl() which already did exactly that), re-built a GraphAccess with
// useMemo(() => createApiAccess(...)) (16), and hand-rolled a
// `let cancelled = false` effect (14). None of those requests had a deadline,
// none could be cancelled, and two panes needing the same spec ran it twice.
// Loading and hung were the same screen, because loading was modelled as
// "data is still null".
//
// WHY IT LIVES IN src/data/: the review's structural note is that there is no
// data layer at all. This is it. lib/ is documented as PURE modules (the vitest
// config says so) and a hook is not pure; components/ is presentational. The
// directory holding the console's data gains the module that fetches it.

/** How long a spec read may take before it is abandoned. 20s is chosen against
 *  the surface, not the network: the slowest reviewed specs are multi-hop
 *  traversals over the whole estate, which run in low single-digit seconds on a
 *  warm database, so 20 leaves generous headroom while still being far below a
 *  person's patience for a page that will never answer. A caller with a known
 *  slower read overrides it; the Ask stream has no deadline at all, on purpose
 *  (see runAgentSse — unbounded latency is that surface's whole nature). */
export const DEFAULT_DEADLINE_MS = 20_000

// ── the provider ────────────────────────────────────────────────────────────

export interface GraphAccessValue {
  access: GraphAccess
  /** The session's public handle (ADR 0019), from the SAME client the access
   *  uses. R5 hands it to the graph_qa agent as the owner of the ephemeral
   *  specs it registers; sharing one client is what makes them resolvable here. */
  getSessionId(): Promise<string>
  /** The one place the console's API base URL is known, for the diagnostics
   *  that need to name it. Reads apiBaseUrl(); no route re-derives it. */
  apiUrl: string
}

/** The session's one GraphAccess. Exported for GraphAccessProvider.tsx, which
 *  is the only place that should write it. */
export const GraphAccessContext = createContext<GraphAccessValue | null>(null)

/** The shared GraphAccess. Throws by name outside a provider rather than
 *  quietly building a second client — one client per session is what lets the
 *  R4 ephemeral specs an agent registers resolve for this session's reads. */
export function useGraphAccess(): GraphAccessValue {
  const value = useContext(GraphAccessContext)
  if (!value) {
    throw new Error('useGraphAccess() outside <GraphAccessProvider> — mount it above the routes')
  }
  return value
}

// ── the state union ─────────────────────────────────────────────────────────

export type QueryFailure = 'timeout' | 'aborted' | 'failed'

/** Loading, loaded-empty, hung and failed are four states, not one screen.
 *
 * `empty` carries its result: a frame that rendered zero rows still has a
 * classification, a cypher and a params echo to show, and collapsing it into
 * "no data" is how a successful empty answer gets rendered as a failure. */
export type QueryState<T> =
  | { status: 'loading' }
  | { status: 'data'; data: T }
  | { status: 'empty'; data: T }
  | { status: 'error'; reason: QueryFailure; message: string }

/** Did this state come back from the server at all? */
export function isResolved<T>(state: QueryState<T>): state is { status: 'data' | 'empty'; data: T } {
  return state.status === 'data' || state.status === 'empty'
}

/** The result if there is one, else undefined — for the many call sites that
 *  treat empty and non-empty alike. */
export function resultOf<T>(state: QueryState<T>): T | undefined {
  return isResolved(state) ? state.data : undefined
}

// ── in-flight dedupe ────────────────────────────────────────────────────────

interface Flight {
  promise: Promise<SpecResult>
  controller: AbortController
  timer: ReturnType<typeof setTimeout>
  timedOut: boolean
  subscribers: number
}

const inFlight = new Map<string, Flight>()

/** Stable key: two call sites building the same params in a different order are
 *  the same request, and JSON.stringify alone would say otherwise. */
export function requestKey(specId: string, params: Record<string, unknown>): string {
  const sorted = Object.keys(params)
    .sort()
    .map((k) => `${k}=${JSON.stringify(params[k])}`)
    .join('&')
  return `${specId}?${sorted}`
}

function release(key: string, flight: Flight): void {
  flight.subscribers -= 1
  if (flight.subscribers > 0) return
  // Delete BEFORE aborting. React StrictMode double-mounts in dev: mount 1
  // starts the request, unmount aborts it, mount 2 runs immediately after — and
  // if the aborted entry were still in the map, mount 2 would join it and await
  // an AbortError forever. This ordering is why that does not happen.
  inFlight.delete(key)
  clearTimeout(flight.timer)
  flight.controller.abort()
}

function start(access: GraphAccess, specId: string, params: Record<string, unknown>, deadlineMs: number): [string, Flight] {
  const key = requestKey(specId, params)
  const existing = inFlight.get(key)
  if (existing) {
    existing.subscribers += 1
    return [key, existing]
  }
  // The timer and the promise both close over the flight, and the flight holds
  // both — so one of the three has to be named before it exists. It used to be
  // the promise, seeded with a cast placeholder; naming the two locals first
  // and building the record once removes the only field in this module that was
  // ever briefly a lie (WEB6). Neither closure can run before the assignment:
  // setTimeout does not fire synchronously and neither does `finally`.
  const controller = new AbortController()
  const timer = setTimeout(() => {
    flight.timedOut = true
    controller.abort()
  }, deadlineMs)
  const promise = access.runSpec(specId, params, { signal: controller.signal }).finally(() => {
    clearTimeout(timer)
    // A settled request is no longer in flight; leaving it in the map would
    // make this a cache, and a cache with classification-aware invalidation is
    // its own decision (clause e), not a side effect of deduping.
    if (inFlight.get(key) === flight) inFlight.delete(key)
  })
  const flight: Flight = { controller, timedOut: false, subscribers: 1, timer, promise }
  inFlight.set(key, flight)
  return [key, flight]
}

/** Test seam: no test should depend on another test's leftover flight. */
export function __resetInFlight(): void {
  for (const [key, flight] of inFlight) {
    clearTimeout(flight.timer)
    inFlight.delete(key)
  }
}

// ── the hook ────────────────────────────────────────────────────────────────

export interface GraphQueryOptions {
  /** Milliseconds before the request is abandoned. Defaults to DEFAULT_DEADLINE_MS. */
  deadlineMs?: number
  /** Skip the read entirely (a tab that is not open, a param not chosen yet).
   *  The state stays `loading`, which is honest: nothing has been asked. */
  enabled?: boolean
  /** The seam to read through, when it is not the session's own (WEB19).
   *
   *  DEFAULTS TO THE PROVIDER and every route leaves it alone. It exists for the
   *  components that take `access` as a PROP — RuntimeSpanMap and LocationMap
   *  are both drawn in tests against a hand-built fake with no provider above
   *  them — because the alternative was those two keeping their own hand-rolled
   *  fetch effects, which is exactly where the completeness envelope was being
   *  dropped. A hook nothing can reach is a hook nothing migrates onto. */
  access?: GraphAccess
}

/** Run a QuerySpec and get back a state, not a nullable.
 *
 * NO RETRY, AND THAT IS A DECISION, not an omission — the review's point that a
 * defensible choice should be a stated one. A read console that retries turns a
 * transient 502 from a restarting API into a slow success, which hides exactly
 * the condition an operator needs to see; and every read here is idempotent but
 * not free, so a retry storm against a saturated API makes the outage worse.
 * The failure surfaces, once, with what the server said. A caller who wants
 * another attempt has a Retry control to offer the person reading the screen.
 */
export function useGraphQuery(
  specId: string,
  params: Record<string, unknown> = {},
  opts: GraphQueryOptions = {},
): QueryState<SpecResult> {
  const { deadlineMs = DEFAULT_DEADLINE_MS, enabled = true, access: given } = opts
  // The context is read unconditionally — a hook cannot be skipped — and used
  // only when no seam was handed in. Missing BOTH is the same error
  // useGraphAccess() raises, and it is raised by name for the same reason.
  const ctx = useContext(GraphAccessContext)
  const access = given ?? ctx?.access
  if (!access) {
    throw new Error(
      'useGraphQuery() outside <GraphAccessProvider> and with no access option — mount the provider above the routes, or pass { access }',
    )
  }
  const key = requestKey(specId, params)
  const [state, setState] = useState<QueryState<SpecResult>>({ status: 'loading' })
  // The params object is rebuilt every render at most call sites; the KEY is
  // what identifies the request, so the effect depends on the key and reads the
  // current object through a ref. Without this every render restarts the read.
  const paramsRef = useRef(params)
  paramsRef.current = params

  useEffect(() => {
    if (!enabled) return
    let alive = true // this subscriber's own liveness, never the controller's
    setState({ status: 'loading' })
    const [flightKey, flight] = start(access, specId, paramsRef.current, deadlineMs)
    flight.promise.then(
      (result) => {
        if (!alive) return
        setState(result.rows.length === 0 ? { status: 'empty', data: result } : { status: 'data', data: result })
      },
      (err: unknown) => {
        if (!alive) return
        const aborted = err instanceof Error && (err.name === 'AbortError' || /abort/i.test(err.message))
        const reason: QueryFailure = flight.timedOut ? 'timeout' : aborted ? 'aborted' : 'failed'
        setState({
          status: 'error',
          reason,
          message: flight.timedOut
            ? `no answer from the API within ${Math.round(deadlineMs / 1000)}s`
            : err instanceof Error
              ? err.message
              : String(err),
        })
      },
    )
    return () => {
      alive = false
      release(flightKey, flight)
    }
  }, [access, specId, key, deadlineMs, enabled])

  return enabled ? state : { status: 'loading' }
}
