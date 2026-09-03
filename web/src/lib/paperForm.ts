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
// pins the two sheets equal). The ANCHOR SCHEME cannot transfer: a design doc
// tags blocks by their authored `id`, and the console has almost none, so tags
// here are `<route-slug>.<n>` in DOM order over the blocks a reviewer marks —
// headings, tables, tab panels. That ordinal is the key a scanned markup gets
// re-attached by, which is why it is stable for a given DOM and written into a
// `data-dd-anchor` attribute as well as the visible tag.
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

/** Tag every anchorable block under `root` with `<slug>.<n>`; returns the count.
 *  A `<table>` cannot hold a span as a direct child (browsers foster-parent it
 *  out), so its tag rides in the caption, which is a legal child and positions
 *  relative to the table. */
export function injectMarginTags(root: ParentNode, slug: string, doc: Document): number {
  let n = 0
  for (const el of Array.from(root.querySelectorAll<HTMLElement>(ANCHOR_SELECTOR))) {
    if (el.closest(`.${PRINT_FOOTER_CLASS}`)) continue
    n += 1
    const anchor = `${slug}.${n}`
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
  return n
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

/** Make `doc` self-contained and printable, in place. Returns the tag count.
 *
 *  Removes what would run or fetch: scripts, stylesheet/preload/icon links,
 *  the dev server's injected `<style>` elements (their rules come back as the
 *  one inlined sheet), iframes. Adds the inlined sheet, the margin tags, the
 *  running footer, a `<meta>` carrying the provenance as JSON, and a title
 *  that says what this is. */
export function assemblePaperDocument(doc: Document, opts: AssembleOptions): number {
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
  const count = injectMarginTags(root, routeSlug(provenance.route), doc)

  const footer = doc.createElement('div')
  footer.className = PRINT_FOOTER_CLASS
  footer.textContent = footerText(provenance)
  doc.body.appendChild(footer)
  return count
}
