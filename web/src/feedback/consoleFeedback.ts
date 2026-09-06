import { anchorBlocks, consoleAnchorValid, routeSlug, type AnchoredBlock } from '../lib/paperForm'
import { readJson, STORAGE_PREFIX, writeJson } from '../lib/storage'

// O89 — the console's half of the Epic L HITL loop, in the design doc's format.
//
// ONE FORMAT, NOT A SECOND ONE (clause a). What this exports is the existing
// `drydocs.docgen.design_doc.feedback_yaml` shape — `doc:` / `notes:` with a
// per-note `anchor:` and `note:` — so one parser, one graph loader
// (`load-doc-traceability`, gate doc-traceability-feedback) and one
// `transcribe-doc-markup` skill serve both surfaces. A console-shaped variant
// would fork the HITL loop at its narrowest point, which is the point where a
// reviewer's notes turn into rows.
//
// `doc:` IS A STEM, NEVER A ROUTE PATH, and this is the question O89's note
// deferred to whoever built it with the loader in front of them. The loader
// (drydocs/loaders/doc_traceability.py) takes `doc:` as a free string and keys
// `:DocSection` on `(origin, doc_id, anchor)`; the FILENAME is what carries the
// rev, through `^(?P<doc_id>.+)-rev(\d+)\.ya?ml$`. A path would break the
// filename (slashes) and read as a doc stem that resolves to no `.md`. So a
// console file is `console.<route-slug>` — a stem, dotted, unmistakable next to
// `controlm-ingestion-tdd`, and it lands in the SAME directory because the
// prefix already distinguishes it.
//
// THE IDIOM IS THE DESIGN DOC'S, ported rather than redesigned (clause d).
// design_doc.py's `_FEEDBACK_JS` keeps `{anchor: note}` in localStorage under
// one key per document, shows a `✎` per anchored block, marks an annotated
// block, and offers one Copy control that puts the paste-ready block on the
// clipboard. Reviewers move between the two surfaces; a second interaction to
// learn is a cost with no benefit.

/** The routes BOTH halves of the loop cover (clause e).
 *
 *  Declared here and imported by scripts/captureRoutes.mjs, so the screen
 *  control and the paper capture cannot disagree about which pages are
 *  reviewable — two lists would drift and the symptom would be a printout whose
 *  gutter names ids no screen offers, which is the failure clause (e) names.
 *
 *  The three SME-designated governed surfaces, which O88 chose for a reason that
 *  still holds: they render from COMMITTED GENERATED ARTIFACTS, so they are
 *  capturable and reviewable on any machine with no graph behind them. A
 *  graph-backed route is opt-in for the capture (`--routes`) and is only as good
 *  as the graph at that moment; extending the SCREEN half to one is a decision
 *  about what a note means, not a line in a list.
 */
export const FEEDBACK_ROUTES: readonly string[] = ['/gates', '/software', '/load-map']

/** Is this route one the loop covers? */
export function feedbackEnabledFor(pathname: string): boolean {
  return FEEDBACK_ROUTES.includes(pathname)
}

/** The state a reviewer accumulates on one route: anchor → note text. */
export type FeedbackNotes = Record<string, string>

/** `console.gates` — the `doc:` value and the storage key's suffix. */
export function consoleDocId(route: string): string {
  return `console.${routeSlug(route)}`
}

/** `console.gates-rev1.yaml` — the file name the loader's regex expects.
 *
 *  A console page has no authored rev the way a design doc does, so the rev is
 *  the reviewer's: rev1 is the first pass over this route. The capture footer,
 *  not the rev, is what says WHICH moment of the page was reviewed. */
export function feedbackFileName(route: string, rev = 1): string {
  return `${consoleDocId(route)}-rev${rev}.yaml`
}

/** Storage key for one route's unsent drafts.
 *
 *  The FULL key including the console's prefix — lib/storage.ts's helpers do not
 *  add it, and `clearAll` sweeps by that prefix, so a key without it would be
 *  invisible to the retention table and to the sweep alike. `drydocs.feedback.
 *  console.` is the row declared there (survives: true — clause d's per-viewer
 *  drafts must not need a backend, and sign-out must not discard an unfinished
 *  review). */
export function storageKey(route: string): string {
  return `${STORAGE_PREFIX}feedback.${consoleDocId(route)}`
}

export function loadNotes(route: string): FeedbackNotes {
  return readJson<FeedbackNotes>(storageKey(route), {})
}

export function saveNotes(route: string, notes: FeedbackNotes): void {
  writeJson(storageKey(route), notes)
}

/** Notes that actually say something. A textarea a reviewer opened and closed
 *  is not a note, and exporting it would put empty entries in a file someone
 *  else has to read. */
export function nonEmpty(notes: FeedbackNotes): [string, string][] {
  return Object.entries(notes)
    .filter(([, note]) => note.trim())
    .sort(([a], [b]) => a.localeCompare(b))
}

/** The paste-ready block, byte-identical in shape to the design doc's export.
 *
 *  Block scalars (`note: |`) for the same reason the doc export uses them: a
 *  reviewer's note is prose and may contain colons, quotes and newlines, and
 *  anything that needed escaping would be a format a person cannot hand-edit. */
export function exportYaml(route: string, notes: FeedbackNotes, rev = 1): string {
  const doc = consoleDocId(route)
  const lines = [
    `# console feedback — paste into docs/design/feedback/${feedbackFileName(route, rev)}`,
    `# route ${route} — anchors are content-derived (O89); the capture footer names the moment`,
    `doc: ${doc}`,
    'notes:',
  ]
  for (const [anchor, note] of nonEmpty(notes)) {
    lines.push(`  - anchor: ${anchor}`)
    lines.push('    note: |')
    for (const line of note.replace(/\r/g, '').split('\n')) lines.push(`      ${line}`)
  }
  return `${lines.join('\n')}\n`
}

/** The blocks on the live page a reviewer can annotate.
 *
 *  The SAME `anchorBlocks` the paper gutter uses, so the two halves cannot
 *  offer different ids (clause e). `main` and not `body`: the shell chrome goes
 *  on paper for context but is not what anyone reviews, and O88's capture
 *  anchors from `main` too. */
export function annotatableBlocks(route: string, root: ParentNode | null): AnchoredBlock[] {
  if (!root) return []
  return anchorBlocks(root, routeSlug(route))
}

/** Which recorded notes no longer re-attach to what the page now offers.
 *
 *  Clause (c): a note whose anchor has gone is REPORTED, never dropped. This is
 *  the browser-side half — the reviewer sees the count while they still
 *  remember what they meant — and tests/unit/test_console_feedback.py is the
 *  repo-side half, over committed files. */
export function orphanedAnchors(notes: FeedbackNotes, available: readonly string[]): string[] {
  // consoleAnchorValid, not a second copy of its rule. A first draft restated
  // the exact-then-table-prefix logic here, which is the shape every item in
  // this burst has been removing: two expressions of one policy drift, and the
  // one that drifts is the one nobody is looking at.
  return nonEmpty(notes)
    .map(([anchor]) => anchor)
    .filter((anchor) => consoleAnchorValid(anchor, available) === null)
}
