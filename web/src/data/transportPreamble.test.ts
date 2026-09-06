import { describe, expect, it } from 'vitest'

import { codeOnly, filesMatching, withoutComments } from '../test/sourceScan'

// WEB12 clause (b) — the forty transport preambles stay gone.
//
// The counts this closes against, re-measured on the tree at pull (2026-09-05,
// wip/WEB12-laptop off main at 6c51618e):
//
//   the VITE_API_URL literal with its localhost fallback   16 files
//   useMemo(() => createApiAccess(...))                    15 files
//   the hand-rolled `let cancelled = false` effect         12 files, 14 sites
//   AbortController                                         0 occurrences
//
// The review's own numbers were 12 / 16 / 14; the difference is what each grep
// counts (files carrying the literal anywhere, including the messages in
// reachability.ts, versus preambles). Both are recorded rather than reconciled,
// because the point is the direction and the direction is to zero.
//
// EVERY SCAN READS CODE, NOT PROSE (J66). These three patterns are quoted
// verbatim by the comments that explain why they are gone — in graphAccess.ts,
// in GraphAccessProvider.tsx, in this file — so a raw-source scan would fail on
// its own explanation. codeOnly strips comments and string literals first; the
// fixtures below prove it still does.

const ALLOWED: Record<string, Record<string, string>> = {
  // pattern -> file -> why this one occurrence is the definition, not a copy
  'localhost:8001': {
    'lib/auth.ts': 'apiBaseUrl() — THE definition. Twelve files used to inline its body beside it.',
  },
  'createApiAccess(': {
    'lib/graphApi.ts': 'the factory itself.',
    'data/GraphAccessProvider.tsx': 'the ONE call, for the session.',
  },
  'let cancelled = false': {},
}

// Each pattern names HOW its source must be stripped, because getting that
// wrong is silent. `localhost:8001` only ever appears inside quotes, so codeOnly
// — which neutralises string literals — matched nothing at all, including the
// twelve real offenders. It reads comment-stripped source instead; the other two
// are code shapes and read codeOnly.
const PATTERNS: Record<string, { re: RegExp; strip: (s: string) => string }> = {
  'localhost:8001': { re: /localhost:8001/, strip: withoutComments },
  'createApiAccess(': { re: /createApiAccess\(/, strip: codeOnly },
  'let cancelled = false': { re: /let\s+cancelled\s*=\s*false/, strip: codeOnly },
}

describe('the transport preamble is gone (clause b)', () => {
  it.each(Object.keys(PATTERNS))('%s appears only where it is defined', (name) => {
    const allowed = ALLOWED[name]
    const { re, strip } = PATTERNS[name]
    const offenders = filesMatching(re, strip).filter((f) => !(f in allowed))
    expect(offenders).toEqual([])
  })

  it('every allow-list entry is a real occurrence, so the list shrinks with the code', () => {
    for (const [name, allowed] of Object.entries(ALLOWED)) {
      const { re, strip } = PATTERNS[name]
      const found = new Set(filesMatching(re, strip))
      expect(Object.keys(allowed).filter((f) => !found.has(f))).toEqual([])
    }
  })

  it('the scanner does not see the comments that quote these patterns', () => {
    // Instrument check (J76). Without it, a stripper regression would empty
    // every scan above and they would all pass, saying nothing.
    const cancelled = PATTERNS['let cancelled = false']
    const url = PATTERNS['localhost:8001']
    expect(url.re.test(url.strip('// was localhost:8001 before WEB12'))).toBe(false)
    expect(url.re.test(url.strip("const u = 'http://localhost:8001'"))).toBe(true)
    expect(cancelled.re.test(cancelled.strip('/* let cancelled = false */'))).toBe(false)
    expect(cancelled.re.test(cancelled.strip('let cancelled = false'))).toBe(true)
    expect(
      PATTERNS['createApiAccess('].re.test(codeOnly("const s = 'createApiAccess('")),
    ).toBe(false)
  })

  it('the scan reaches the files it claims to', () => {
    // A glob that matched nothing would make every assertion above vacuous.
    expect(filesMatching(/useGraphAccess|useGraphQuery/).length).toBeGreaterThan(10)
  })
})

describe('requests can be cancelled at all (clause a)', () => {
  it('AbortController is now used, where it was used zero times', () => {
    const users = filesMatching(/new AbortController\(/)
    expect(users.length).toBeGreaterThan(4)
    expect(users).toContain('data/graphAccess.ts')
  })

  it('the seam carries a signal on every read method', () => {
    const seam = codeOnly(
      // read through the scanner so a commented-out signature cannot satisfy it
      filesMatching(/interface GraphAccess/).length ? readGraph() : '',
    )
    for (const method of ['runRead', 'runNamed', 'runSpec', 'exportSpec']) {
      expect(seam).toMatch(new RegExp(`${method}\\([^)]*opts`, 's'))
    }
  })
})

function readGraph(): string {
  // eslint-disable-next-line
  return require('node:fs').readFileSync(
    new URL('../lib/graph.ts', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'),
    'utf8',
  ) as string
}
