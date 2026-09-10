import { describe, expect, it } from 'vitest'

import { SRC, filesMatching, readFileSync, tsSources, withoutComments } from '../test/sourceScan'

// WEB23 — the entry chunk's one generated artifact, kept out of it by a test.
//
// THE MECHANISM THIS PROTECTS. `web/src/generated/load-map.json` is 139 KB on
// disk and 79 KB in the bundle. While ANY module reachable from a statically
// imported route imported it statically, it sat in the entry chunk — the bytes
// every persona downloads before anything renders — and the measured entry chunk
// was 2,506,022 bytes against a 2,505,000 ceiling, over it. Moving the one
// remaining static importer (`lineage/laneBasis.ts`, reachable from /lineage,
// which is open to every role) to an on-demand `import()` took it to 2,426,767.
//
// WHY A TEST AND NOT A COMMENT. The import that costs 79 KB looks exactly like
// the import that costs nothing: one line, at the top, resolving fine, with no
// error at any point between writing it and the CI bundle check going red for
// whoever pushes next. The bundle check catches the SIZE; it cannot say what
// arrived or where to put it. This says both, at the file that would do it.
//
// WHAT IS ALLOWED. `import()` — the dynamic form — anywhere, and a static import
// inside a route that is already lazy (`loadmap/loadMapModel.ts`,
// `software/softwareModel.ts`), because those chunks are fetched when their
// route opens and the artifact rides along with them rather than ahead of them.

// READ WITH `withoutComments`, NEVER `codeOnly`: the pattern's subject IS a
// string literal - the artifact's path - and codeOnly neutralises literals, so
// every assertion here would pass vacuously against it. That is not
// hypothetical; this guard was written with codeOnly first and matched nothing,
// including the two real importers. Comments still go, so the note in
// laneBasis.ts that QUOTES the forbidden import is not read as one (J66).

/** A STATIC import of the generated load map. The dynamic form is
 *  `import(...)` — a call, with a parenthesis where this pattern needs a quote —
 *  so it does not match, which is the whole distinction being drawn. */
const STATIC_LOAD_MAP = /import\s[^()]*?['"][^'"]*generated\/load-map\.json['"]/

/** Modules that may hold a static import because they are only ever reached
 *  through a lazily loaded route, with the route named. `lazyRoutes.test.ts`
 *  is what keeps those routes lazy; this list depends on that and says so. */
const LAZY_ONLY: Record<string, string> = {
  'loadmap/loadMapModel.ts': 'reached only from /load-map (LoadMapRoute, lazy in App.tsx)',
  'software/softwareModel.ts': 'reached only from /software (SoftwareRoute, lazy in App.tsx)',
}

describe('the generated load map stays out of the entry chunk (WEB23)', () => {
  const importers = filesMatching(STATIC_LOAD_MAP, withoutComments, tsSources())

  it('is imported statically only from modules behind a lazy route boundary', () => {
    const unexpected = importers.filter((f) => !(f in LAZY_ONLY))
    expect(
      unexpected,
      `${unexpected.join(', ')} imports web/src/generated/load-map.json statically. ` +
        'That puts 79 KB into the chunk every persona downloads before anything renders. ' +
        'Use the on-demand form (see lineage/layerSystems.ts), or say here why the module is ' +
        'only reachable behind a lazy route.',
    ).toEqual([])
  })

  it('holds every allowance to a real importer with a stated reason', () => {
    // The list shrinks with the code: an entry whose file stopped importing the
    // artifact fails here rather than sitting as a permanent licence.
    for (const [path, reason] of Object.entries(LAZY_ONLY)) {
      expect(importers, `${path} is allowed a static import but no longer has one`).toContain(path)
      expect(reason.length, `${path} needs a reason naming its route`).toBeGreaterThan(30)
    }
  })

  it('keeps laneBasis on the on-demand path, which is where the 79 KB was won', () => {
    const laneBasis = withoutComments(readFileSync(`${SRC}/lineage/laneBasis.ts`, 'utf8'))
    expect(STATIC_LOAD_MAP.test(laneBasis)).toBe(false)
    // And the module that replaced it still fetches dynamically.
    const layerSystems = withoutComments(readFileSync(`${SRC}/lineage/layerSystems.ts`, 'utf8'))
    expect(layerSystems).toMatch(/import\(/)
  })

  it('finds the importers at all, so a broken pattern cannot pass vacuously', () => {
    // Two lazy-only modules read it today. A scan returning none means the
    // pattern stopped matching, not that the artifact stopped being used.
    expect(importers.length).toBeGreaterThanOrEqual(2)
  })
})
