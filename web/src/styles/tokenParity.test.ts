import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { SRC } from '../test/sourceScan'

// WEB14 — the two shipped pages carry a hand-frozen copy of the token sheet,
// and nothing detected the day they stopped agreeing.
//
// THE PAGES ARE NOT THE DEBT (T4 is explicit about this, and it matters,
// because the obvious "fix" is to delete them): public/landing.html is an
// intentional drop-in swap slot under a no-CDN intranet rule, and
// public/agent-test.html was SME-re-ruled as an independent page on 2026-07-29.
// Both are self-contained ON PURPOSE and stay that way — this is a drift guard
// on the repo's generated-artifact habit, not a generator, and clause (c) says
// so.
//
// WHICH SHEET EACH PAGE FROZE — BOTH froze the DARK one. agent-test.html says
// so in its own header ("dark token sheet values, frozen (tokens.css .dark)");
// landing.html does not, and it was checked rather than assumed: its `--bg` is
// #0d1520, which is tokens.css's `:root.dark` value, not the #f4f6f9 of `:root`.
// The pairing is declared here rather than inferred, because comparing a page
// against the wrong sheet reports every colour as drifted and the guard reads
// as broken on the day it lands.
//
// COUNTS: this reads 22 declarations in :root, 20 in :root.dark, 16 in
// landing.html and 18 in agent-test.html. The review reports 48 and 39 for the
// two pages; the difference is what is counted — every `--x:` occurrence in the
// page, declarations and usages alike, versus declarations inside the :root
// block. Recorded rather than reconciled: the guard needs declarations.

const WEB = join(SRC, '..')

function read(rel: string): string {
  return readFileSync(join(WEB, rel), 'utf8')
}

/** Custom properties declared inside one selector block.
 *
 * Deliberately dumb — a `--name: value;` scan over the block's text. These are
 * three hand-maintained files with flat token blocks and no nesting, and a real
 * CSS parser would be a dependency bought to read 150 lines.
 */
function tokensIn(css: string, selector: string): Record<string, string> {
  const start = css.indexOf(selector)
  if (start === -1) return {}
  const open = css.indexOf('{', start)
  // Brace-MATCHED, not "to the next }". The first draft stopped at the first
  // closing brace and read 22 of these blocks as a handful — a parser that
  // silently under-reads makes a drift guard pass on a page it never looked at.
  let depth = 0
  let end = open
  while (end < css.length) {
    if (css[end] === '{') depth += 1
    else if (css[end] === '}') {
      depth -= 1
      if (depth === 0) break
    }
    end += 1
  }
  const block = css.slice(open + 1, end)
  const out: Record<string, string> = {}
  for (const [, name, value] of block.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    out[name] = value.trim().replace(/\s+/g, ' ')
  }
  return out
}

const tokens = read('src/styles/tokens.css')
const LIGHT = tokensIn(tokens, ':root {')
const DARK = tokensIn(tokens, ':root.dark {')

/** page -> the sheet it froze, and the properties it declares. */
const FROZEN = {
  'public/landing.html': { source: DARK, sourceName: 'tokens.css :root.dark' },
  'public/agent-test.html': { source: DARK, sourceName: 'tokens.css :root.dark' },
} as const

/** Shared keys that are deliberately DIFFERENT, with the reason (clause b).
 *
 * Empty today, and that is a finding rather than an oversight: the pages and
 * the sheet agree on every shared property right now, which is exactly why a
 * guard is worth installing at this moment — it starts from a true baseline
 * rather than from a list of exceptions nobody can audit.
 */
const DELIBERATE_DIVERGENCE: Record<string, Record<string, string>> = {
  'public/landing.html': {},
  'public/agent-test.html': {},
}

describe('the frozen token sheets still agree with tokens.css', () => {
  it('the source sheets parsed — a guard over nothing proves nothing', () => {
    // Instrument check (J76). Both blocks are read by a deliberately dumb
    // scanner; if tokens.css is restructured and the selectors move, every
    // comparison below becomes vacuous and passes.
    expect(Object.keys(LIGHT).length).toBeGreaterThan(20)
    expect(Object.keys(DARK).length).toBeGreaterThan(18)
    expect(LIGHT['--blue']).toBeTruthy()
    expect(DARK['--bg']).toBeTruthy()
    // and the two sheets are DIFFERENT, or pairing a page with either would pass
    expect(LIGHT['--bg']).not.toBe(DARK['--bg'])
  })

  it.each(Object.keys(FROZEN))('%s parsed its own block', (page) => {
    const frozen = tokensIn(read(page), ':root')
    expect(Object.keys(frozen).length).toBeGreaterThan(14)
  })

  it.each(Object.keys(FROZEN))('%s agrees with its source on every shared key', (page) => {
    const { source, sourceName } = FROZEN[page as keyof typeof FROZEN]
    const frozen = tokensIn(read(page), ':root')
    const waived = DELIBERATE_DIVERGENCE[page]

    const drifted: string[] = []
    for (const [name, value] of Object.entries(frozen)) {
      if (!(name in source)) continue // the page may declare tokens of its own
      if (name in waived) continue
      if (source[name] !== value) drifted.push(`${name}: page has ${value}, ${sourceName} has ${source[name]}`)
    }
    expect(
      drifted,
      `${page} has drifted from ${sourceName}. Update the page, or add the key to ` +
        'DELIBERATE_DIVERGENCE with the reason it must differ:\n  ' +
        drifted.join('\n  '),
    ).toEqual([])
  })

  it.each(Object.keys(FROZEN))('%s shares enough keys for the check to mean something', (page) => {
    // A page that shared two tokens would pass the comparison above while
    // having drifted on the other forty.
    const { source } = FROZEN[page as keyof typeof FROZEN]
    const frozen = tokensIn(read(page), ':root')
    const shared = Object.keys(frozen).filter((k) => k in source)
    expect(shared.length).toBeGreaterThan(12)
  })

  it('every waiver names a key that actually exists in both', () => {
    for (const [page, waived] of Object.entries(DELIBERATE_DIVERGENCE)) {
      const { source } = FROZEN[page as keyof typeof FROZEN]
      const frozen = tokensIn(read(page), ':root')
      for (const [name, why] of Object.entries(waived)) {
        expect(name in frozen && name in source, `${page}: ${name} is waived but not shared`).toBe(true)
        expect(why.length).toBeGreaterThan(20)
      }
    }
  })

  it('the pages stay self-contained (clause c)', () => {
    // The guard must not tempt anyone into "fixing" the duplication by linking
    // the sheet: landing.html is a drop-in swap slot on an intranet with a
    // no-CDN rule, and agent-test.html was ruled independent by the SME.
    for (const page of Object.keys(FROZEN)) {
      const html = read(page)
      expect(html).not.toMatch(/<link[^>]+tokens\.css/)
      expect(html).toContain('<style>')
    }
  })
})
