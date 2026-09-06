// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'

import {
  ANCHOR_ATTRIBUTE,
  assemblePaperDocument,
  CAPTURE_META_NAME,
  type CaptureProvenance,
  externalReferences,
  footerText,
  consoleAnchorValid,
  injectMarginTags,
  MARGIN_TAG_CLASS,
  PAPER_STYLE_ID,
  PRINT_FOOTER_CLASS,
  routeSlug,
} from './paperForm'

// O88. The transformation is pure over a Document, so the properties the item
// asks for — self-contained, the L6 gutter on every marked block, a footer that
// names the moment — are asserted here under jsdom rather than left to a
// person printing a page and looking.

const PROV: CaptureProvenance = {
  route: '/gates',
  commit: 'abc123def456 (dirty)',
  capturedAt: '2026-09-03T08:00:00Z',
  api: 'http://localhost:8001',
  persona: 'mouse',
  browser: 'msedge 140.0',
}

function page(): Document {
  const doc = document.implementation.createHTMLDocument('DryDocs Console')
  doc.head.innerHTML = [
    '<link rel="stylesheet" href="/src/index.css">',
    '<link rel="modulepreload" href="/src/main.tsx">',
    '<link rel="icon" href="/favicon.svg">',
    '<style>.hmr{color:red}</style>',
    '<script type="module" src="/src/main.tsx"></script>',
  ].join('')
  doc.body.innerHTML = [
    '<aside><nav><h2>Modules</h2></nav></aside>',
    '<main>',
    '  <h1>Gates</h1>',
    '  <p>3 gates in the record</p>',
    '  <h2>Open gates</h2>',
    '  <table><thead><tr><th>id</th></tr></thead><tbody><tr><td>x</td></tr></tbody></table>',
    '  <div role="tabpanel"><h3>Signed off</h3><img src="/vendor-icons/neo4j.svg"></div>',
    '  <script>console.log("inline")</script>',
    '</main>',
  ].join('\n')
  return doc
}

describe('routeSlug', () => {
  it('flattens a route to a filename-safe slug and names the landing page', () => {
    expect(routeSlug('/gates')).toBe('gates')
    expect(routeSlug('/load-map')).toBe('load-map')
    expect(routeSlug('/explorer/tower/home?x=1#frag')).toBe('explorer-tower-home')
    expect(routeSlug('/')).toBe('overview')
  })
})

describe('footerText', () => {
  it('carries the route, commit, time, api and persona, in that order', () => {
    const text = footerText(PROV)
    expect(text).toBe(
      'route /gates · commit abc123def456 (dirty) · captured 2026-09-03T08:00:00Z · ' +
        'api http://localhost:8001 · persona mouse · browser msedge 140.0',
    )
    const { browser: _browser, ...noBrowser } = PROV
    expect(footerText(noBrowser)).not.toContain('browser')
  })
})

describe('injectMarginTags', () => {
  it('tags headings, tables, rows and tab panels, and nothing else', () => {
    const doc = page()
    const main = doc.querySelector('main')!
    const anchors = injectMarginTags(main, 'gates', doc)
    const tags = Array.from(main.querySelectorAll(`.${MARGIN_TAG_CLASS}`)).map((t) => t.textContent)
    expect(anchors).toHaveLength(6)
    expect(tags).toEqual(anchors)
    // every anchor is namespaced to the route and content-derived (O89) — the
    // shape, not the literal ids, because pinning six hashes would make this a
    // test of the hash function rather than of the scheme.
    for (const a of anchors) expect(a).toMatch(/^gates\.[0-9a-f]{8}(\.[0-9a-f]{8})?$/)
    expect(new Set(anchors).size).toBe(anchors.length)
    // a row is anchored through its first cell, never its header cell
    expect(main.querySelector('tbody td')?.hasAttribute(ANCHOR_ATTRIBUTE)).toBe(true)
    expect(main.querySelector('thead th')?.hasAttribute(ANCHOR_ATTRIBUTE)).toBe(false)
    expect(main.querySelector('p')?.hasAttribute(ANCHOR_ATTRIBUTE)).toBe(false)
    // the visible tag and the machine-readable anchor agree
    for (const el of Array.from(main.querySelectorAll(`[${ANCHOR_ATTRIBUTE}]`))) {
      expect(el.querySelector(`.${MARGIN_TAG_CLASS}`)?.textContent).toBe(el.getAttribute(ANCHOR_ATTRIBUTE))
    }
  })

  it("puts a table's tag in its caption, where a span is a legal child", () => {
    const doc = page()
    injectMarginTags(doc.querySelector('main')!, 'gates', doc)
    const table = doc.querySelector('table')!
    expect(table.caption?.querySelector(`.${MARGIN_TAG_CLASS}`)?.textContent).toBe(
      table.getAttribute(ANCHOR_ATTRIBUTE),
    )
    expect(table.firstElementChild?.tagName).toBe('CAPTION')
  })

  // ── O89: the properties the ordinal scheme did not have ───────────────────

  it('AN INSERTED BLOCK DOES NOT MOVE THE ANCHORS AROUND IT', () => {
    // This is the whole reason the scheme changed. Under `<slug>.<n>` inserting
    // a heading renumbered everything after it, so every prior note re-attached
    // to the wrong block — silently, because the ids still resolved.
    const before = page()
    const beforeAnchors = injectMarginTags(before.querySelector('main')!, 'gates', before)

    const after = page()
    const main = after.querySelector('main')!
    main.insertBefore(after.createElement('h2'), main.querySelector('table'))
    main.querySelector('h2:empty')!.textContent = 'Inserted section'
    const afterAnchors = injectMarginTags(main, 'gates', after)

    expect(afterAnchors).toHaveLength(beforeAnchors.length + 1)
    for (const a of beforeAnchors) expect(afterAnchors).toContain(a)
  })

  it('a ROW anchor carries its table as a prefix, so a lost row degrades to the table', () => {
    const doc = page()
    const anchors = injectMarginTags(doc.querySelector('main')!, 'gates', doc)
    const table = doc.querySelector('table')!.getAttribute(ANCHOR_ATTRIBUTE)!
    const row = doc.querySelector('tbody td')!.getAttribute(ANCHOR_ATTRIBUTE)!
    expect(row.startsWith(`${table}.`)).toBe(true)
    expect(consoleAnchorValid(row, anchors)).toBe(row)
    // the row is gone; the note lands on the table rather than being dropped
    expect(consoleAnchorValid(row, anchors.filter((a) => a !== row))).toBe(table)
    // and when the table is gone too, nothing takes it — REPORTED, not invented
    expect(consoleAnchorValid(row, anchors.filter((a) => a !== row && a !== table))).toBeNull()
  })

  it('two blocks with identical text get distinct anchors', () => {
    const doc = page()
    const main = doc.querySelector('main')!
    const twin = doc.createElement('h2')
    twin.textContent = 'Open gates' // the same text as the existing h2
    main.appendChild(twin)
    const anchors = injectMarginTags(main, 'gates', doc)
    expect(new Set(anchors).size).toBe(anchors.length)
    expect(anchors.filter((a) => a.endsWith('-2'))).toHaveLength(1)
  })

  it('a console anchor cannot be mistaken for a design-doc one', () => {
    // The two share a YAML format and must not share an id space (clause b).
    // Doc anchors are authored words, optionally `--`-derived; console anchors
    // always begin with a route slug and a dot.
    const doc = page()
    const anchors = injectMarginTags(doc.querySelector('main')!, 'gates', doc)
    for (const a of anchors) {
      expect(a).toContain('.')
      expect(a).not.toContain('--')
    }
    expect(consoleAnchorValid('traceability-matrix', anchors)).toBeNull()
    expect(consoleAnchorValid('detailed-design--stage-2', anchors)).toBeNull()
  })

  it('is stable: the same DOM tags the same anchors twice over', () => {
    const a = page()
    const b = page()
    injectMarginTags(a.querySelector('main')!, 'gates', a)
    injectMarginTags(b.querySelector('main')!, 'gates', b)
    expect(a.querySelector('main')!.innerHTML).toBe(b.querySelector('main')!.innerHTML)
  })
})

describe('assemblePaperDocument', () => {
  it('removes everything that would run or fetch, and inlines the one sheet', () => {
    const doc = page()
    assemblePaperDocument(doc, { css: '.x{color:blue} @media print{.dd-margin-tag{display:block}}', provenance: PROV })
    expect(doc.querySelectorAll('script, link, iframe')).toHaveLength(0)
    const styles = doc.querySelectorAll('style')
    expect(styles).toHaveLength(1)
    expect(styles[0].id).toBe(PAPER_STYLE_ID)
    expect(styles[0].textContent).toContain('@media print')
  })

  it('names the moment: a footer on the page and the provenance in a meta tag', () => {
    const doc = page()
    assemblePaperDocument(doc, { css: '', provenance: PROV })
    expect(doc.querySelector(`.${PRINT_FOOTER_CLASS}`)?.textContent).toBe(footerText(PROV))
    const meta = doc.querySelector(`meta[name="${CAPTURE_META_NAME}"]`)
    expect(JSON.parse(meta!.getAttribute('content')!)).toEqual(PROV)
    expect(doc.title).toContain('/gates')
  })

  it('tags inside main only, never the shell chrome', () => {
    const doc = page()
    assemblePaperDocument(doc, { css: '', provenance: PROV })
    expect(doc.querySelector('aside')!.querySelectorAll(`.${MARGIN_TAG_CLASS}`)).toHaveLength(0)
    expect(doc.querySelector('main')!.querySelectorAll(`.${MARGIN_TAG_CLASS}`)).toHaveLength(6)
  })
})

describe('externalReferences', () => {
  it('finds what a page could still fetch, and ignores data URIs and fragments', () => {
    const html =
      '<img src="/vendor-icons/neo4j.svg"><img src="data:image/svg+xml;base64,AAAA">' +
      '<style>.a{background:url(https://fonts.example/x.woff2)} .b{background:url("data:image/png;base64,BB")}</style>' +
      '<a href="/gates">nav links are not requests</a><use href="#icon"/>'
    expect(externalReferences(html)).toEqual(['/vendor-icons/neo4j.svg', 'https://fonts.example/x.woff2'])
  })

  it('is empty for a document the capture driver may call self-contained', () => {
    const doc = page()
    doc.querySelector('img')!.setAttribute('src', 'data:image/svg+xml;base64,AAAA')
    assemblePaperDocument(doc, { css: '.x{background:url(data:image/png;base64,BB)}', provenance: PROV })
    expect(externalReferences(doc.documentElement.outerHTML)).toEqual([])
  })
})
