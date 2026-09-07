// WEB11 — one module owns every console key in localStorage.
//
// THE DEFECT (S4): `signOut()` removed ONE key of eight and revoked the token.
// Everything else the console had written stayed — including the two that
// matter. The Ask last-turn envelope holds an answer, the executed Cypher,
// per-step row counts and the task graph; the app-code tray holds the
// application codes a steward selected. Both are QUERY RESULTS, both are keyed
// by persona rather than by session, and both were readable after sign-out by
// whoever opened the browser next. On a shared support desktop that is a
// different person, under a console that renders an INTERNAL classification
// banner and a not-for-redistribution notice over the same data on screen.
//
// `sessionRejected()` had the same gap, and it is the path taken when a session
// expires while a tab is open — which is the more common of the two.
//
// THE RETENTION DECISION IS THE POINT, not the plumbing. Every key declares
// whether it survives sign-out, in one table, with the reason. Before this the
// answer was "whatever nobody remembered to remove", which is not a decision.

/** Every key the console writes, and whether it survives a sign-out.
 *
 * `survives: true` is an OPT-OUT from clearing and needs a reason. The default
 * is that a key goes: a console whose data outlives its session is the failure
 * this table exists to make visible. */
interface KeySpec {
  /** the key, or a prefix when the key is per-persona / per-surface */
  key: string
  /** true when the stored value is scoped by persona or by surface, so
   *  clearing must sweep every key that starts with it */
  prefixed?: boolean
  survives: boolean
  why: string
}

export const STORAGE_KEYS: readonly KeySpec[] = [
  {
    key: 'drydocs.session.v2',
    survives: false,
    why: 'the session token itself — signOut already removed this one.',
  },
  {
    key: 'drydocs.ask.last-turn.',
    prefixed: true,
    survives: false,
    why: 'O64: a completed Ask turn — the answer, the executed Cypher, per-step row counts. A query result, and the reason this item exists. O64s design (it survives NAVIGATION within a session) is untouched; it is sign-out that clears it.',
  },
  {
    key: 'drydocs.app-code-tray.',
    prefixed: true,
    survives: false,
    why: 'K11: the application codes a steward selected. Working state over INTERNAL data.',
  },
  {
    key: 'drydocs.onboarding.v1',
    survives: false,
    why: 'which hub spokes this person has visited — about the PERSON, not the browser, so it goes with them.',
  },
  {
    key: 'drydocs.feedback.console.',
    prefixed: true,
    survives: true,
    why: "O89: a reviewer's UNSENT feedback drafts on a console route. It survives on purpose and the clause says why — drafts are per-viewer and must not need a backend, so the only place they exist is this browser, and clearing them at sign-out would silently discard a review someone had not finished. It is also the one surviving key that holds authored PROSE rather than a preference: the notes are the reviewer's own words about a page, never rows read from the graph, which is what makes keeping them a different decision from keeping the Ask turn above.",
  },
  {
    key: 'drydocs.theme.v1',
    survives: true,
    why: 'a display preference of the DEVICE. Carrying it across sign-outs is the behaviour anyone expects, and it reveals nothing.',
  },
  {
    key: 'drydocs.aside-collapsed.v1',
    survives: true,
    why: 'nav chrome width — a device preference, same argument as the theme.',
  },
  {
    key: 'drydocs.split.',
    prefixed: true,
    survives: true,
    why: 'split-pane positions per module — layout, not content.',
  },
  {
    key: 'drydocs.grid-widths.',
    prefixed: true,
    survives: true,
    why: 'grid column widths per grid — layout, not content.',
  },
]

/** Every declared key is under this prefix, so `clearAll` can be exhaustive
 *  without depending on the table being complete. */
export const STORAGE_PREFIX = 'drydocs.'

function safe<T>(fn: () => T, fallback: T): T {
  // Storage throws outright in some contexts (a browser set to block site
  // data, a sandboxed frame). Every accessor is guarded, because a console
  // that will not render because it could not read a saved column width is
  // worse than one that forgets the width.
  try {
    return fn()
  } catch {
    return fallback
  }
}

export function read(key: string): string | null {
  return safe(() => localStorage.getItem(key), null)
}

export function write(key: string, value: string): void {
  safe(() => localStorage.setItem(key, value), undefined)
}

export function remove(key: string): void {
  safe(() => localStorage.removeItem(key), undefined)
}

export function readJson<T>(key: string, fallback: T): T {
  const raw = read(key)
  if (raw === null) return fallback
  return safe(() => JSON.parse(raw) as T, fallback)
}

export function writeJson(key: string, value: unknown): void {
  safe(() => localStorage.setItem(key, JSON.stringify(value)), undefined)
}

/** Does this key survive a sign-out? Unknown keys under the console's prefix
 *  do NOT — default-deny, so a key added without a table row is cleared rather
 *  than silently retained. That is the safe direction to be wrong in. */
export function survivesSignOut(key: string): boolean {
  const spec = STORAGE_KEYS.find((s) => (s.prefixed ? key.startsWith(s.key) : key === s.key))
  return spec?.survives ?? false
}

/** Drop everything this console stored that does not explicitly survive.
 *
 * It sweeps by PREFIX rather than by the table, so a key someone added and
 * forgot to declare is still cleared. The table decides what stays; the prefix
 * decides what is ours.
 */
export function clearAll(): void {
  safe(() => {
    const doomed: string[] = []
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key && key.startsWith(STORAGE_PREFIX) && !survivesSignOut(key)) doomed.push(key)
    }
    for (const key of doomed) localStorage.removeItem(key)
  }, undefined)
}
