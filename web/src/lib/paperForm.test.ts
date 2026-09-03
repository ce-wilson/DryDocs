// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'

import {
  ANCHOR_ATTRIBUTE,
  assemblePaperDocument,
  CAPTURE_META_NAME,
  type CaptureProvenance,
  externalReferences,
  footerText,
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
  it('tags headings, tables, rows and tab panels in DOM order with <slug>.<n>, and nothing else', () => {
    const doc = page()
    const main = doc.querySelector('main')!
    const count = injectMarginTags(main, 'gates', doc)
    const tags = Array.from(main.querySelectorAll(`.${MARGIN_TAG_CLASS}`)).map((t) => t.textContent)
    expect(count).toBe(6)
    expect(tags).toEqual(['gates.1', 'gates.2', 'gates.3', 'gates.4', 'gates.5', 'gates.6'])
    expect(main.querySelector('h1')?.getAttribute(ANCHOR_ATTRIBUTE)).toBe('gates.1')
    // a row is anchored through its first cell, never its header cell
    expect(main.querySelector('tbody td')?.getAttribute(ANCHOR_ATTRIBUTE)).toBe('gates.4')
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
    expect(table.caption?.querySelector(`.${MARGIN_TAG_CLASS}`)?.textContent).toBe('gates.3')
    expect(table.firstElementChild?.tagName).toBe('CAPTION')
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
