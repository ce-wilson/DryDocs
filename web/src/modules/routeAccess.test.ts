import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { codeOnly, filesMatching, SRC, tsSources } from '../test/sourceScan'

import {
  accessForPath,
  canAccessModule,
  canAccessPath,
  GATED_SURFACES,
  MODULES,
  PERSONA_SCOPED_PATHS,
} from './registry'

// WEB3 — route authorization derives from the module registry.
//
// The bug this guards against already shipped once. O59 set /remediation's
// registry access to 'sme'; the nav entry disappeared and the ROUTE stayed
// reachable by typing the URL, because the nav read canAccessModule and the
// route restated `role === 'steward' || role === 'admin'` inline. The fix taken
// then was to duplicate the predicate at the route — which left the next module
// with access 'sme' free to reproduce it exactly.
//
// Both directions are asserted, per clause (b): every non-'all' module has a
// gated route, AND every declared gate corresponds to a route that exists.

const APP = join(SRC, 'App.tsx')

const ROLES = ['user', 'steward', 'admin'] as const

/** Route paths declared in App.tsx, normalised to leading-slash absolutes.
 *
 * A source read rather than an import: App.tsx's route table is JSX over every
 * route component in the console, so importing it to enumerate paths would drag
 * the whole app into a unit test. This reads the declaration, not a render
 * (J37's distinction) — what is being enumerated is the source text that IS the
 * route table. */
function declaredRoutePaths(): string[] {
  const src = readFileSync(APP, 'utf8')
  return [...src.matchAll(/<Route\s+path="([^"]+)"/g)]
    .map((m) => m[1])
    .filter((p) => p !== '*')
    .map((p) => (p.startsWith('/') ? p : `/${p}`))
}

describe('every non-all module is gated (clause b, forward)', () => {
  const gatedModules = MODULES.filter((m) => m.access && m.access !== 'all')

  it('there are gated modules to check', () => {
    expect(gatedModules.length).toBeGreaterThan(0)
  })

  it.each(gatedModules.map((m) => [m.id, m.path, m.access] as const))(
    '%s (%s) refuses a user and admits what its access declares',
    (_id, path, access) => {
      expect(accessForPath(path)).toBe(access)
      for (const role of ROLES) {
        expect(canAccessPath(path, role)).toBe(canAccessModule(access, role))
      }
      expect(canAccessPath(path, 'user')).toBe(false)
    },
  )

  it.each(gatedModules.map((m) => [m.id, m.path] as const))(
    '%s has a route in App.tsx, so the gate has something to gate',
    (_id, path) => {
      expect(declaredRoutePaths()).toContain(path)
    },
  )

  it('a deep link inherits its parent module gate', () => {
    // The O59 shape at one remove: /remediation gated, /remediation/anything not.
    for (const m of gatedModules) {
      expect(canAccessPath(`${m.path}/deep/link`, 'user')).toBe(false)
    }
  })
})

describe('every declared gate is real (clause b, reverse)', () => {
  it.each(GATED_SURFACES.map((s) => [s.path, s.access] as const))(
    '%s is a route that exists and is gated at %s',
    (path, access) => {
      expect(declaredRoutePaths()).toContain(path)
      expect(accessForPath(path)).toBe(access)
      expect(canAccessPath(path, 'user')).toBe(false)
    },
  )

  it('every gated surface carries the reason it is gated', () => {
    for (const s of GATED_SURFACES) expect(s.why.length).toBeGreaterThan(20)
  })

  it('the persona-scoped exceptions are declared, and are the only ones', () => {
    // /intake admits the SME persona as well as two roles, which the `access`
    // role vocabulary cannot express — the ADR this item nominates. It is
    // listed so the exception is a declaration, and asserted so a second one
    // cannot be added silently.
    expect([...PERSONA_SCOPED_PATHS]).toEqual(['/intake'])
    expect(accessForPath('/intake')).toBeUndefined()
  })

  it('App.tsx actually mounts the gate, ahead of every gated route', () => {
    // Without this, deleting the one <Route element={<RouteAccessGate .../>}>
    // line would open every gated route and every OTHER test here would still
    // pass — canAccessPath would keep answering correctly to nobody. That is
    // precisely the O59 failure: a correct predicate no route consulted.
    const src = readFileSync(APP, 'utf8')
    const gateAt = src.indexOf('<RouteAccessGate')
    expect(gateAt).toBeGreaterThan(-1)
    for (const path of [
      ...MODULES.filter((m) => m.access && m.access !== 'all').map((m) => m.path),
      ...GATED_SURFACES.map((s) => s.path),
    ]) {
      // `path="x"` and not `<Route path="x"` — several routes wrap onto their
      // own line, and a prefix that only matches the one-line spelling would
      // pass by finding nothing.
      const routeAt = src.indexOf(`path="${path.slice(1)}"`)
      expect(routeAt, `no route declares ${path}`).toBeGreaterThan(gateAt)
    }
  })

  it('an ungated path is ungated for everyone', () => {
    for (const role of ROLES) {
      expect(canAccessPath('/explorer', role)).toBe(true)
      expect(canAccessPath('/ask', role)).toBe(true)
    }
  })
})

// ── clause (c): the registry stays the single check ─────────────────────────

/** Files allowed to compare a role or a persona id, each with its reason.
 *
 * Default-deny, the shape test_module_boundary.py uses: a file not listed here
 * fails, so a new inline predicate has to argue for itself in this table rather
 * than arrive unnoticed. These are the sites as WEB3 left them — every one of
 * them is a DISPLAY or CAPABILITY decision, not route authorization. */
const ALLOWED: Record<string, string> = {
  'modules/registry.ts': 'canAccessModule — the one check. This IS the definition.',
  'lib/auth.ts':
    'canAccessIntake — the persona-scoped grant the access vocabulary cannot express (PERSONA_SCOPED_PATHS).',
  'lib/graph.ts':
    'boltAllowed — a DEV-only capability gate on the bolt adapter (ADR 0005), not a route.',
  'lib/views.ts': 'tower visibility: admin sees every tower, others their own. A view filter.',
  'layout/Aside.tsx': 'the "stew" badge beside the Mappings link — which label to draw.',
  'layout/Header.tsx': 'an admin-only header affordance — a display decision.',
  'routes/MappingsRoute.tsx': 'renders the word "steward" or "admin" as text.',
}

describe('no route authorization outside the registry (clause c)', () => {
  const PREDICATE = /\.?\brole\s*[!=]==?\s*['"]|\bpersona\.id\s*[!=]==?\s*['"]/

  it('the scanner strips the prose that quotes the pattern', () => {
    // Instrument check: this fixture is exactly the shape of the comments in
    // App.tsx and registry.ts. If codeOnly regressed, the scan below would fail
    // on explanations and the allow-list would grow for the wrong reason.
    expect(PREDICATE.test(codeOnly("// was role === 'admin' before WEB3"))).toBe(false)
    expect(PREDICATE.test(codeOnly("/* role === 'steward' */"))).toBe(false)
    expect(PREDICATE.test(codeOnly("const s = 'role === admin'"))).toBe(false)
    expect(PREDICATE.test(codeOnly("if (persona.role === 'admin') return"))).toBe(true)
  })

  it('finds the sources it means to scan', () => {
    expect(tsSources().length).toBeGreaterThan(100)
  })

  it('every role or persona comparison is in a file that declares why', () => {
    const offenders = filesMatching(PREDICATE).filter((rel) => !(rel in ALLOWED))
    expect(offenders).toEqual([])
  })

  it('App.tsx itself carries no role predicate at all', () => {
    expect(PREDICATE.test(codeOnly(readFileSync(APP, 'utf8')))).toBe(false)
  })

  it('the allow-list has no dead entries', () => {
    const withPredicate = new Set(filesMatching(PREDICATE))
    expect(Object.keys(ALLOWED).filter((f) => !withPredicate.has(f))).toEqual([])
  })
})
