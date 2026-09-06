// The console's paper form (O88): turn an EXECUTED console page into one
// self-contained printable document carrying the L6 margin gutter and a
// route/commit provenance footer.
//
// PURE ON PURPOSE. Everything here is a transformation over a `Document` —
// no fetch, no Node, no browser launch — so it runs identically under jsdom in
// the unit suite (paperForm.test.ts) and inside scripts/captureRoutes.mjs, which
// hands it the HTML Playwright pulled out of headless Edge. The capture is the
// executed DOM, never a re-render of the same data: a second renderer that
// reproduced console markup from JSON would drift from the screen silently,
// which is the whole failure a capture avoids.
//
// WHAT THE DESIGN-DOC RENDERER LENDS AND WHAT IT CANNOT. drydocs/docgen/
// design_doc.py prints a `.dd-margin-tag` span into the left gutter of every
// anchored block (`_inject_margin_anchors`) and a `.dd-print-footer` that
// repeats on every page (`doc_rev_footer`). The CLASSES and their print CSS are
// reused verbatim (src/styles/print.css; tests/unit/test_console_print_gutter.py
// pins the two sheets equal).
//
// THE ANCHOR SCHEME IS CONTENT-DERIVED AS OF O89, and this replaces what O88
// shipped two days earlier. O88 tagged blocks `<route-slug>.<n>` in DOM order,
// under its own stated constraint — a design doc tags by authored id and the
// console had none. O89 clause (b) is that an anchor keyed to an index does not
// survive an inserted panel and a content-derived one does, and clause (e) is
// that the paper gutter and the screen control must offer the SAME ids. Both
// halves now call `anchorFor` below, so they agree by construction rather than
// by two implementations being kept in step. Nothing was keyed to the ordinals
// yet — no console feedback file, no scan — so the change costs no re-attachment.
//
// WHY A HASH AND NOT A SLUG, which is where this departs from L11's doc rule.
// A design doc's anchorable text is a heading — a sentence, slugs beautifully.
// The console's anchorables include DATA-FRAME ROWS, whose "own text" is a job
// name or a folder name. Two consequences, and the second is the one that
// settles it: identical first cells are ordinary in a 500-row grid, so slugs
// collide exactly where the granularity matters most; and a slug would write
// production identifiers into `docs/design/feedback/`, which is a published
// path and precisely where SEALIDs have hidden inside folder-name strings
// before. A short hash of the block's text is content-derived, survives
// insertion, is unique per block, and carries no source text.
//
// A CAPTURE IS A MOMENT AND THE FOOTER SAYS SO. A design doc's footer is
// `Rev N · commit <hash>` because its rev is authored. A console page has no
// rev — it has a route, a commit, a wall-clock time, and an API it read — and
// all four (plus the persona that saw it) go on every printed page. Without
// them a marked-up printout is a note about a screen that existed once.

export const MARGIN_TAG_CLASS = 'dd-margin-tag'
export const PRINT_FOOTER_CLASS = 'dd-print-footer'
export const ANCHOR_ATTRIBUTE = 'data-dd-anchor'
export const CAPTURE_META_NAME = 'drydocs-capture'
export const PAPER_STYLE_ID = 'dd-paper-css'

/** The blocks a reviewer's pen lands beside, in the order the page renders them.
 *  A data-frame ROW is anchored through its first cell: a `<tr>` is not a reliable
 *  containing block for an absolutely positioned tag in Chromium, a `<td>` is, and
 *  the first cell's left edge is the table's — so the tag lands in the gutter. The
 *  first capture of /gates carried two anchors for a whole page, which is not a
 *  granularity anyone marks up a table at. */
export const ANCHOR_SELECTOR = 'h1, h2, h3, h4, table, tbody > tr > td:first-child, [role="tabpanel"]'

export interface CaptureProvenance {
  /** the console route, e.g. `/gates` */
  route: string
  /** the capture host's HEAD, with ` (dirty)` when the tree differed */
  commit: string
  /** ISO-8601 UTC */
  capturedAt: string
  /** the origin the page actually read — recorded from its own /login request */
  api: string
  /** the persona that was signed in */
  persona: string
  /** e.g. `msedge 140.0.x` — which headless browser executed the page */
  browser?: string
}

/** `/load-map` → `load-map`; `/` → `overview`; `/explorer/tower/home` → `explorer-tower-home`. */
export function routeSlug(route: string): string {
  const slug = route
    .replace(/[?#].*$/, '')
    .split('/')
    .filter(Boolean)
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'overview'
}

/** The running footer, one line, every field present. */
export function footerText(p: CaptureProvenance): string {
  const parts = [
    `route ${p.route}`,
    `commit ${p.commit}`,
    `captured ${p.capturedAt}`,
    `api ${p.api}`,
    `persona ${p.persona}`,
  ]
  if (p.browser) parts.push(`browser ${p.browser}`)
  return parts.join(' · ')
}

/** FNV-1a over the block's text, 8 hex chars.
 *
 *  Not cryptographic and does not need to be: the job is a stable, short,
 *  content-derived id, and the input is text a reviewer can read on the page.
 *  Written out rather than pulled from a library because the same function has
 *  to run in the browser, under jsdom, and inside the capture driver, and a
 *  dependency in this file would break the "pure over a Document" property the
 *  header promises. */
export function textHash(text: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i)
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h.toString(16).padStart(8, '0')
}

/** The text an anchor is derived FROM: collapsed whitespace, case-folded.
 *
 *  Collapsed because a re-render may reflow the same words differently, and an
 *  anchor that moved because a line wrapped would be positional in disguise.
 *  Truncated because a whole table's text is not what identifies it — the first
 *  200 characters are, and a shorter input makes the hash no less stable. */
export function anchorText(el: { tagName?: string; textContent: string | null }): string {
  const text = (el.textContent ?? '').replace(/\s+/g, ' ').trim().toLowerCase().slice(0, 200)
  // THE TAG NAME IS PART OF THE IDENTITY, and leaving it out was a real
  // collision rather than a theoretical one: a `<div role="tabpanel">` whose
  // only content is an `<h3>` has exactly its child's text, so the panel and
  // the heading hashed identically and one of them took a `-2` suffix it had
  // not earned. A heading and the panel containing it are different blocks to
  // annotate; their element type says so without appealing to position.
  return `${(el.tagName ?? '').toLowerCase()}|${text}`
}

/** The anchor for one block: `<route-slug>.<hash>`, or `<route-slug>.<table>.<row>`
 *  for a data-frame row.
 *
 *  ROWS CARRY THEIR TABLE'S HASH AS A PREFIX, which is what makes a note on a
 *  vanished row degrade to the table it was in rather than being dropped —
 *  `feedback_anchor_valid`'s "fall back to the authored parent" rule (L11), in
 *  the shape the console needs. `consoleAnchorValid` below is the other half.
 *
 *  THE `.` SEPARATOR IS THE NAMESPACE. A design-doc anchor is `<authored>` or
 *  `<authored>--<slug>`; a console anchor always begins with a route slug and a
 *  dot. The two share a YAML format and must not share an id space (clause b),
 *  and the separators being disjoint is what lets a validator tell them apart
 *  without being told which kind it is looking at. */
export function anchorFor(el: HTMLElement, slug: string): string {
  const own = textHash(anchorText(el))
  const cell = el.tagName === 'TD' || el.tagName === 'TH'
  if (!cell) return `${slug}.${own}`
  const table = el.closest('table')
  return table ? `${slug}.${textHash(anchorText(table))}.${own}` : `${slug}.${own}`
}

/** Does a recorded anchor still re-attach to the anchors a page now offers?
 *
 *  Exact match, else — for a row anchor — its TABLE prefix, so a note on a row
 *  that has since gone re-attaches to the table rather than being silently
 *  lost. A feedback loop that drops notes quietly is worse than none, because
 *  the reviewer believes it worked (clause c).
 *
 *  Returns the anchor it re-attaches TO, or null when nothing takes it. */
export function consoleAnchorValid(anchor: string, known: readonly string[]): string | null {
  const set = new Set(known)
  if (set.has(anchor)) return anchor
  const parts = anchor.split('.')
  if (parts.length < 3) return null
  const base = parts.slice(0, -1).join('.')
  return set.has(base) ? base : null
}

/** Tag every anchorable block under `root` with its content-derived anchor;
 *  returns the anchors in document order.
 *
 *  A `<table>` cannot hold a span as a direct child (browsers foster-parent it
 *  out), so its tag rides in the caption, which is a legal child and positions
 *  relative to the table.
 *
 *  A COLLISION SUFFIX, because two blocks CAN carry the same text — an empty
 *  cell, a repeated "Total" row — and two blocks with one anchor would make a
 *  note ambiguous rather than merely imprecise. The suffix is ordinal within
 *  the collision only, so inserting an unrelated block never renumbers it. */
export interface AnchoredBlock {
  el: HTMLElement
  anchor: string
}

/** Every anchorable block under `root`, with its id — THE one function that
 *  decides what is annotatable and what it is called.
 *
 *  Both halves of the loop call it: the paper gutter (`injectMarginTags`, below)
 *  and the screen control (`feedback/consoleFeedback.ts`). That is clause (e)
 *  made structural rather than promised — a printout's gutter cannot name an id
 *  the screen does not offer, because there is nothing that could compute a
 *  different answer.
 *
 *  IT MUTATES NOTHING, and that is what makes the shared use safe: injecting a
 *  tag changes an element's textContent, and a table is reached before its own
 *  rows, so computing anchors WHILE tagging hashed each row's table with the
 *  table's tag already inside it — the row anchors stopped carrying the table as
 *  a prefix and the degradation rule silently stopped working. Compute first,
 *  then whoever called it can do what it likes to the DOM. */
export function anchorBlocks(root: ParentNode, slug: string): AnchoredBlock[] {
  const blocks = Array.from(root.querySelectorAll<HTMLElement>(ANCHOR_SELECTOR)).filter(
    (el) => !el.closest(`.${PRINT_FOOTER_CLASS}`),
  )
  const seen = new Map<string, number>()
  return blocks.map((el) => {
    const base = anchorFor(el, slug)
    const dup = seen.get(base) ?? 0
    seen.set(base, dup + 1)
    return { el, anchor: dup === 0 ? base : `${base}-${dup + 1}` }
  })
}

export function injectMarginTags(root: ParentNode, slug: string, doc: Document): string[] {
  const blocks = anchorBlocks(root, slug)
  const anchors = blocks.map((b) => b.anchor)

  for (const { el, anchor } of blocks) {
    const tag = doc.createElement('span')
    tag.className = MARGIN_TAG_CLASS
    tag.setAttribute('aria-hidden', 'true')
    tag.textContent = anchor
    el.setAttribute(ANCHOR_ATTRIBUTE, anchor)
    if (el.tagName === 'TABLE') {
      const table = el as HTMLTableElement
      const caption = table.caption ?? table.createCaption()
      caption.prepend(tag)
    } else {
      el.prepend(tag)
    }
  }
  return anchors
}

/** Everything the page could still fetch on open: `src`/`srcset`/`poster`
 *  attributes and CSS `url(...)` values that are not data:/blob:/#. The caller
 *  decides whether a hit is a defect (the capture driver refuses to call a
 *  file self-contained while this is non-empty). */
export function externalReferences(html: string): string[] {
  const hits = new Set<string>()
  const attr = /\b(?:src|srcset|poster)\s*=\s*["']([^"']+)["']/gi
  const url = /url\(\s*["']?([^"')]+)["']?\s*\)/gi
  for (const re of [attr, url]) {
    for (const m of html.matchAll(re)) {
      const value = m[1].trim()
      if (!value || value.startsWith('data:') || value.startsWith('#')) continue
      hits.add(value.length > 80 ? `${value.slice(0, 77)}...` : value)
    }
  }
  return Array.from(hits).sort()
}

export interface AssembleOptions {
  /** every rule of every stylesheet the page had loaded, as cssText — the
   *  print sheet rides in with it because index.css imports it */
  css: string
  provenance: CaptureProvenance
}

/** Make `doc` self-contained and printable, in place. Returns the ANCHORS it
 *  tagged, in document order.
 *
 *  O89 changed this from a count to the ids themselves, because the count was
 *  only ever a sanity number and the ids are what the loop needs: the capture
 *  manifest records them, and the Python guard that reports an orphaned note
 *  (clause c) checks a feedback file's anchors against exactly this list. A
 *  count cannot answer "does this note still re-attach".
 *
 *  Removes what would run or fetch: scripts, stylesheet/preload/icon links,
 *  the dev server's injected `<style>` elements (their rules come back as the
 *  one inlined sheet), iframes. Adds the inlined sheet, the margin tags, the
 *  running footer, a `<meta>` carrying the provenance as JSON, and a title
 *  that says what this is. */
export function assemblePaperDocument(doc: Document, opts: AssembleOptions): string[] {
  const { css, provenance } = opts
  for (const el of Array.from(
    doc.querySelectorAll(
      'script, link[rel="stylesheet"], link[rel="modulepreload"], link[rel="preload"], ' +
        'link[rel="icon"], link[rel="manifest"], style, iframe',
    ),
  )) {
    el.remove()
  }

  const style = doc.createElement('style')
  style.id = PAPER_STYLE_ID
  style.textContent = css
  doc.head.appendChild(style)

  const meta = doc.createElement('meta')
  meta.setAttribute('name', CAPTURE_META_NAME)
  meta.setAttribute('content', JSON.stringify(provenance))
  doc.head.appendChild(meta)

  const title = doc.querySelector('title') ?? doc.head.appendChild(doc.createElement('title'))
  title.textContent = `DryDocs paper form — ${provenance.route} @ ${provenance.commit}`

  const root: ParentNode = doc.querySelector('main') ?? doc.body
  const anchors = injectMarginTags(root, routeSlug(provenance.route), doc)

  const footer = doc.createElement('div')
  footer.className = PRINT_FOOTER_CLASS
  footer.textContent = footerText(provenance)
  doc.body.appendChild(footer)
  return anchors
}
