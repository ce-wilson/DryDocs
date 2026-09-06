// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { ANCHOR_ATTRIBUTE, anchorBlocks, injectMarginTags, routeSlug } from '../lib/paperForm'
import { clearAll, survivesSignOut } from '../lib/storage'
import {
  FEEDBACK_ROUTES,
  consoleDocId,
  exportYaml,
  feedbackEnabledFor,
  feedbackFileName,
  loadNotes,
  nonEmpty,
  orphanedAnchors,
  saveNotes,
  storageKey,
} from './consoleFeedback'
import { codeOnly, filesMatching, readFileSync, SRC, withoutComments } from '../test/sourceScan'

// O89 — the console half of the Epic L HITL loop.
//
// The clauses that can be checked without a browser are checked here; the one
// that cannot (does a reviewer's pen land where the tag is) is the paper half's
// and belongs to a person with a printout.

function page(): Document {
  const doc = document.implementation.createHTMLDocument('console')
  doc.body.innerHTML = [
    '<main>',
    '  <h1>Gates</h1>',
    '  <h2>Open gates</h2>',
    '  <table><thead><tr><th>id</th></tr></thead><tbody>',
    '    <tr><td>gate-a</td></tr><tr><td>gate-b</td></tr>',
    '  </tbody></table>',
    '</main>',
  ].join('\n')
  return doc
}

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

// ── clause (a): one format, the design doc's ────────────────────────────────

describe('the export is the design doc format', () => {
  it('emits doc:/notes: with per-note anchor and a block scalar', () => {
    const yaml = exportYaml('/gates', { 'gates.aaaaaaaa': 'the count is wrong' })
    expect(yaml).toContain('doc: console.gates')
    expect(yaml).toContain('notes:')
    expect(yaml).toContain('  - anchor: gates.aaaaaaaa')
    expect(yaml).toContain('    note: |')
    expect(yaml).toContain('      the count is wrong')
    expect(yaml.endsWith('\n')).toBe(true)
  })

  it('a multi-line note stays a block scalar, indented under its own key', () => {
    const yaml = exportYaml('/gates', { 'gates.aaaaaaaa': 'line one\nline two: with a colon' })
    expect(yaml).toContain('      line one\n      line two: with a colon')
  })

  it('an opened-but-empty textarea is not a note', () => {
    // A note nobody wrote would arrive in the file as an empty entry someone
    // else has to read and decide about.
    expect(nonEmpty({ a: '', b: '   ', c: 'real' })).toEqual([['c', 'real']])
    expect(exportYaml('/gates', { 'gates.a': '  ' })).not.toContain('anchor:')
  })

  it('`doc:` is a STEM the loader can key on, never a route path', () => {
    // drydocs/loaders/doc_traceability.py takes `doc:` as a free string and the
    // FILENAME carries the rev through ^(?P<doc_id>.+)-rev(\d+)\.ya?ml$. A path
    // would break the filename and read as a doc stem resolving to no .md.
    expect(consoleDocId('/gates')).toBe('console.gates')
    expect(consoleDocId('/load-map')).toBe('console.load-map')
    expect(consoleDocId('/')).toBe('console.overview')
    for (const route of FEEDBACK_ROUTES) {
      expect(consoleDocId(route)).not.toContain('/')
      expect(feedbackFileName(route)).toMatch(/^console\.[a-z0-9-]+-rev\d+\.yaml$/)
    }
  })
})

// ── clause (b)/(e): one anchor set, shared with the paper half ──────────────

describe('the screen and the gutter cannot offer different ids', () => {
  it('the screen anchors are exactly what the print pass tags', () => {
    // Not "they agree today" — they call the same function, and this asserts it
    // over a real DOM so a future second implementation is caught.
    const screen = page()
    const paper = page()
    const fromScreen = anchorBlocks(screen.querySelector('main')!, routeSlug('/gates')).map(
      (b) => b.anchor,
    )
    const fromPaper = injectMarginTags(paper.querySelector('main')!, routeSlug('/gates'), paper)
    expect(fromScreen).toEqual(fromPaper)
    expect(fromScreen.length).toBeGreaterThan(3)
  })

  it('one route list serves both halves', () => {
    // The driver imports FEEDBACK_ROUTES; a second list would drift into a
    // printout whose gutter names ids no screen offers (clause e).
    const driver = readFileSync(`${SRC}/../scripts/captureRoutes.mjs`, 'utf8')
    expect(codeOnly(driver)).toContain('FEEDBACK_ROUTES')
    // AND it does not restate them. The first version of this assertion checked
    // only that the import survived, so replacing `[...FEEDBACK_ROUTES]` with a
    // literal array still passed — the import line kept the name alive. A route
    // literal anywhere in the driver's CODE is the drift itself, so that is what
    // is forbidden.
    //
    // withoutComments AND NOT codeOnly, which this got wrong before the probe
    // caught it: a route is a STRING LITERAL and codeOnly neutralises literals,
    // so the scan matched nothing and reported no offender while the literal
    // array sat there. Comments are still stripped, because the usage banner
    // names the routes in prose on purpose and a guard that failed on its own
    // documentation would teach people to delete the documentation (J66).
    // Choose the stripper deliberately: codeOnly for a code shape, this for a
    // literal.
    for (const route of FEEDBACK_ROUTES) {
      expect(withoutComments(driver)).not.toContain(route)
    }
    expect(FEEDBACK_ROUTES).toEqual(['/gates', '/software', '/load-map'])
    expect(feedbackEnabledFor('/gates')).toBe(true)
    expect(feedbackEnabledFor('/explorer')).toBe(false)
  })

  it('nothing else in web/src computes a console anchor of its own', () => {
    // The whole clause-(e) guarantee is that ONE function answers. A second
    // caller of textHash outside paperForm would be a second answer.
    expect(filesMatching(/textHash\s*\(/, codeOnly)).toEqual(['lib/paperForm.ts'])
  })
})

// ── clause (c): an orphaned note is reported, never dropped ─────────────────

describe('a note whose block is gone', () => {
  it('is reported, and the row case degrades to its table first', () => {
    const doc = page()
    const anchors = injectMarginTags(doc.querySelector('main')!, 'gates', doc)
    const table = doc.querySelector('table')!.getAttribute(ANCHOR_ATTRIBUTE)!
    const row = doc.querySelector('tbody td')!.getAttribute(ANCHOR_ATTRIBUTE)!

    // the row is gone but its table remains: NOT an orphan, it re-attaches up
    expect(orphanedAnchors({ [row]: 'note' }, anchors.filter((a) => a !== row))).toEqual([])
    // the table is gone too: nothing takes it, and it is reported
    expect(
      orphanedAnchors({ [row]: 'note' }, anchors.filter((a) => a !== row && a !== table)),
    ).toEqual([row])
  })

  it('is still EXPORTED — reported is not the same as dropped', () => {
    // The failure this clause exists to prevent is the quiet one: a reviewer
    // believes the loop worked. Losing the note would be that failure with a
    // warning attached.
    const yaml = exportYaml('/gates', { 'gates.deadbeef': 'a note on a vanished block' })
    expect(yaml).toContain('gates.deadbeef')
    expect(yaml).toContain('a note on a vanished block')
  })
})

// ── clause (d): drafts are per-viewer and survive a sign-out ────────────────

describe('unsent drafts', () => {
  it('round-trip through the console-prefixed key', () => {
    saveNotes('/gates', { 'gates.aaaaaaaa': 'kept' })
    expect(loadNotes('/gates')).toEqual({ 'gates.aaaaaaaa': 'kept' })
    expect(storageKey('/gates')).toBe('drydocs.feedback.console.gates')
  })

  it('SURVIVE a sign-out, unlike every other content key', () => {
    // Clause (d): drafts must not need a backend, so this browser is the only
    // place they exist and clearing them would discard an unfinished review.
    saveNotes('/gates', { 'gates.aaaaaaaa': 'half-written' })
    expect(survivesSignOut(storageKey('/gates'))).toBe(true)
    clearAll()
    expect(loadNotes('/gates')).toEqual({ 'gates.aaaaaaaa': 'half-written' })
  })

  it('are per ROUTE — one page’s notes never appear on another', () => {
    saveNotes('/gates', { 'gates.a': 'g' })
    saveNotes('/software', { 'software.a': 's' })
    expect(loadNotes('/gates')).toEqual({ 'gates.a': 'g' })
    expect(loadNotes('/software')).toEqual({ 'software.a': 's' })
  })
})
