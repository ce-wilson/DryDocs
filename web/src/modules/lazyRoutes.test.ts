import { describe, expect, it } from 'vitest'

import { GATED_SURFACES, MODULES } from './registry'
import { codeOnly, readFileSync, SRC, withoutComments } from '../test/sourceScan'

// WEB7 — the split follows the AUTHORIZATION boundary, and a test says so.
//
// The set of lazy routes and the set of gated routes are the same set. That is
// the item's whole claim, and it is the kind of claim that decays silently: a
// new gated module arrives, someone adds a static import beside the others, and
// the page is hidden from the nav while its chunk still ships to everyone —
// which is O59's defect one layer down, in delivery rather than in rendering.
//
// So this derives the expected set from registry.ts (the same declaration
// RouteAccessGate reads) and checks App.tsx against it, in BOTH directions.

const APP = readFileSync(`${SRC}/App.tsx`, 'utf8')

/** The route element names App.tsx declares lazily, e.g. `AdminConfigRoute`.
 *  Read from CODE — `const X = lazy(` is a code shape, and App.tsx's header
 *  comment names the pattern while explaining it (J66). */
function lazyNames(source: string): string[] {
  return [...codeOnly(source).matchAll(/const\s+(\w+)\s*=\s*lazy\(/g)].map((m) => m[1])
}

/** Every path the registry gates: a module with an `access` level, plus the
 *  three surfaces that are gated without being modules. */
function gatedPaths(): string[] {
  const fromModules = MODULES.filter((m) => m.access).map((m) => m.path)
  const fromSurfaces = GATED_SURFACES.map((s) => s.path)
  return [...new Set([...fromModules, ...fromSurfaces])].sort()
}

/** The element name App.tsx routes a path to — `<Route path="gates"
 *  element={<GatesRoute ...` — read from the route table. */
function elementForPath(path: string): string | null {
  const bare = path.replace(/^\//, '')
  // withoutComments, NOT codeOnly: what is being matched IS a string literal
  // (`path="gates"`), and codeOnly neutralises literals — so every lookup
  // returned null, and the two set comparisons below compared two empty sets
  // successfully. The vacuity test is what surfaced that, which is the whole
  // argument for having one.
  const re = new RegExp(`path="${bare}"[\\s\\S]{0,120}?element=\\{<(\\w+)`)
  return re.exec(withoutComments(APP))?.[1] ?? null
}

describe('the lazy set is the gated set', () => {
  it('every gated path routes to a component App.tsx loads lazily', () => {
    const lazy = new Set(lazyNames(APP))
    const missing = gatedPaths().filter((p) => {
      const el = elementForPath(p)
      return el !== null && !lazy.has(el)
    })
    expect(
      missing,
      `gated paths whose route component still ships to every persona: ${missing.join(', ')}`,
    ).toEqual([])
  })

  it('and every path IS found in the route table — the scan is not passing vacuously', () => {
    // Without this, a change to the route-table syntax would make every path
    // resolve to null, `missing` would be empty, and the test above would
    // report success while checking nothing.
    const unresolved = gatedPaths().filter((p) => elementForPath(p) === null)
    expect(unresolved, `paths not found in App.tsx's route table: ${unresolved.join(', ')}`).toEqual(
      [],
    )
  })

  it('nothing UNGATED was split — that would be a size decision, not this one', () => {
    // The item is explicit: "a chunk is admissible to a role or it is not".
    // Splitting an open route to shave bytes is a different decision and would
    // need its own reason; this catches one arriving under this item's cover.
    const gatedElements = new Set(
      gatedPaths()
        .map(elementForPath)
        .filter((e): e is string => e !== null),
    )
    const extra = lazyNames(APP).filter((n) => !gatedElements.has(n))
    expect(extra, `lazy in App.tsx but not gated: ${extra.join(', ')}`).toEqual([])
  })

  it('the registry really does gate something (instrument check)', () => {
    expect(gatedPaths().length).toBeGreaterThan(5)
    expect(lazyNames(APP).length).toBeGreaterThan(5)
  })
})

describe('the split has somewhere to land', () => {
  it('one Suspense boundary wraps the route tree, inside the error boundary', () => {
    // A lazy route with no Suspense ancestor throws at render. The boundary
    // being OUTSIDE it is deliberate: a chunk that fails to download rejects
    // during render, so the error boundary catches a network failure and offers
    // its retry, rather than the console going blank.
    const boundary = codeOnly(readFileSync(`${SRC}/layout/RouteErrorBoundary.tsx`, 'utf8'))
    expect(boundary).toContain('<Suspense')
    expect(boundary.indexOf('<Boundary')).toBeLessThan(boundary.indexOf('<Suspense'))
    expect(boundary.indexOf('<Suspense')).toBeLessThan(boundary.indexOf('<Outlet'))
  })

  it('the Locations tab carries its OWN Suspense, so a tab load does not blank the page', () => {
    const explorer = codeOnly(readFileSync(`${SRC}/routes/explorer/ExplorerRoute.tsx`, 'utf8'))
    expect(explorer).toContain('lazy(')
    expect(explorer).toContain('<Suspense')
  })
})

describe('the ceiling is real and is wired to CI', () => {
  it('the check script names its ceiling, its date and the ratchet rule', () => {
    const raw = readFileSync(`${SRC}/../scripts/checkBundleSize.mjs`, 'utf8')
    // Deliberately reading raw here, not codeOnly: the subject IS the recorded
    // note, and the note lives in a comment. Stated because the default in this
    // repo is the other way (J66's exception clause).
    expect(raw).toMatch(/const CEILING_BYTES = [\d_]+/)
    expect(raw).toMatch(/2026-09-05/)
    expect(withoutComments(raw)).toContain('process.exit(1)')
  })

  it('the CI job runs it', () => {
    const ci = readFileSync(`${SRC}/../../.github/workflows/ci.yml`, 'utf8')
    expect(ci).toContain('npm run bundle:check')
  })
})
