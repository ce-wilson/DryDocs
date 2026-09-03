import { describe, expect, it } from 'vitest'

import { canAccessModule, MODULES, type ModuleDef, type ModuleId } from './registry'

// O92. canAccessModule is three lines and decides, for every persona, which
// console modules exist at all: the aside nav (layout/Aside.tsx), the Overview
// spokes (routes/OverviewRoute.tsx) and the full-page canvas
// (routes/GraphCanvasRoute.tsx) all filter MODULES through it with the same
// expression. O59 changed a module's designation with one word and nothing
// outside the diff would have noticed (Idea-231). This file is what notices.
//
// WHAT THIS IS NOT: an authorization test. The server re-resolves the real
// role from the bearer token on every request and the API is the enforcement
// point (ADR 0005 decision 3; lib/auth.ts says so at length), so a module
// wrongly shown here exposes no data — every call the page makes is still
// checked. This is about the console's AUDIENCE decisions staying deliberate,
// and the failure is silent in both directions: a module wrongly OPENED shows
// an end user numbers they will misread as breakage (the FB-03 argument); a
// module wrongly CLOSED simply vanishes for them, with no error anywhere.
// Both directions are asserted below, over the real registry.

type Role = Parameters<typeof canAccessModule>[1]
type Access = ModuleDef['access']

const ROLES: readonly Role[] = ['user', 'steward', 'admin']

// ---------------------------------------------------------------------------
// (b), (c) THE PIN: which module ids carry a non-default designation, and why.
//
// This is the larger half of the item. The list should change rarely and always
// on purpose, which is exactly when a pin is the right instrument — the same
// "state the number so it cannot drift quietly" pattern ui-tests.yaml's coverage
// pins use. Each entry carries the REASON as recorded where the designation was
// made, because a designation whose reason is unrecorded is the thing the pin
// exists to prevent. Change the registry, then change this table in the same
// commit and say why in the message.
//
// The test can check that a reason is PRESENT; whether it is still TRUE is a
// review question, and the item says so rather than pretending otherwise.
// ---------------------------------------------------------------------------
const DESIGNATED: Readonly<Record<string, { access: Exclude<Access, undefined | 'all'>; reason: string }>> = {
  remediation: {
    access: 'sme',
    reason:
      'O59 (2026-08-31): every number on the page is a DELTA against a standard ' +
      '("7/9 slots not supplied", "21 findings") and the substitutions frame asks ' +
      'for input only an SME can supply; an end user reads deltas as breakage.',
  },
  software: {
    access: 'sme',
    reason:
      'FB-03: every column is a delta — gate state, declared-vs-loaded, an edge ' +
      'withheld pending G32; "1016 pages staged, 0 loaded" reads as breakage ' +
      'without that context. Same audience as /gates.',
  },
  gates: {
    access: 'sme',
    reason: "FB-03: gate reviews are the SME's surface.",
  },
  loadmap: {
    access: 'sme',
    reason:
      'FB-03, the /software argument (O57): every column is governance state — ' +
      'confirmed-or-not, ledger tier, pipeline reach, declared defects with written ' +
      'exemptions — and "registered only" reads as breakage where there is a ruling.',
  },
  underhood: {
    access: 'sme',
    reason: 'FB-03: the retrieval benchmark showcase is an SME/admin audience, not end users.',
  },
}

/** The same filter expression the three call sites use, so the test reads the
 *  registry the way the pages do rather than re-deriving it. */
function visibleTo(role: Role): readonly ModuleDef[] {
  return MODULES.filter((m) => canAccessModule(m.access, role))
}

function isDesignated(m: ModuleDef): boolean {
  return m.access !== undefined && m.access !== 'all'
}

// ---------------------------------------------------------------------------
// (a) the function itself: three roles against every designation value
// ---------------------------------------------------------------------------
describe('canAccessModule', () => {
  // The full matrix, written out rather than derived, so a reader can see each
  // cell and a change to any one of them fails by name. 'admin' is in the matrix
  // even though no module carries it today (the pin below says so): the branch
  // exists in the function, and the day a module uses it is not the day to find
  // out what it does.
  const MATRIX: ReadonlyArray<[Access, Role, boolean]> = [
    [undefined, 'user', true],
    [undefined, 'steward', true],
    [undefined, 'admin', true],
    ['all', 'user', true],
    ['all', 'steward', true],
    ['all', 'admin', true],
    ['sme', 'user', false],
    ['sme', 'steward', true],
    ['sme', 'admin', true],
    ['admin', 'user', false],
    ['admin', 'steward', false],
    ['admin', 'admin', true],
  ]

  it.each(MATRIX)('access=%s role=%s -> %s', (access, role, expected) => {
    expect(canAccessModule(access, role)).toBe(expected)
  })

  it('covers every designation value for every role, so the matrix cannot go stale by omission', () => {
    const accesses: Access[] = [undefined, 'all', 'sme', 'admin']
    const cells = new Set(MATRIX.map(([a, r]) => `${String(a)}|${r}`))
    for (const a of accesses) for (const r of ROLES) expect(cells.has(`${String(a)}|${r}`)).toBe(true)
    expect(MATRIX.length).toBe(accesses.length * ROLES.length)
  })

  it('treats a missing designation and an explicit all identically', () => {
    for (const role of ROLES) expect(canAccessModule(undefined, role)).toBe(canAccessModule('all', role))
  })

  it('is monotone in the role: whatever a user may see, a steward may; whatever a steward may, an admin may', () => {
    const accesses: Access[] = [undefined, 'all', 'sme', 'admin']
    for (const a of accesses) {
      if (canAccessModule(a, 'user')) expect(canAccessModule(a, 'steward')).toBe(true)
      if (canAccessModule(a, 'steward')) expect(canAccessModule(a, 'admin')).toBe(true)
    }
  })
})

// ---------------------------------------------------------------------------
// (b), (c) the pin against the real registry
// ---------------------------------------------------------------------------
describe('the designated modules are pinned, with a reason each', () => {
  // toEqual on the WHOLE map, not a subset check: adding a designation, removing
  // one, or changing sme -> admin all fail here. A subset check would miss the
  // removal, which is the wrongly-OPENED direction.
  it('exactly these module ids carry a non-default access value', () => {
    const actual = Object.fromEntries(MODULES.filter(isDesignated).map((m) => [m.id, m.access]))
    const pinned = Object.fromEntries(Object.entries(DESIGNATED).map(([id, d]) => [id, d.access]))
    expect(actual).toEqual(pinned)
  })

  it('every pinned id is a module the registry has', () => {
    const ids = new Set<ModuleId>(MODULES.map((m) => m.id))
    for (const id of Object.keys(DESIGNATED)) expect(ids.has(id as ModuleId), `${id} is not in MODULES`).toBe(true)
  })

  it('every entry records a reason (whether the reason still holds is a review question)', () => {
    for (const [id, d] of Object.entries(DESIGNATED)) {
      expect(d.reason.trim().length, `${id} has no recorded reason`).toBeGreaterThan(20)
    }
  })

  // Stated as the current fact rather than assumed: the 'admin' designation is
  // unused. If a module adopts it, this test is where the reader learns the
  // registry crossed that line, and the pin above names the module.
  it('no module is designated admin today', () => {
    expect(MODULES.filter((m) => m.access === 'admin').map((m) => m.id)).toEqual([])
  })
})

// ---------------------------------------------------------------------------
// (e) both silent directions, over the real registry, through the call sites'
// own filter expression
// ---------------------------------------------------------------------------
describe('what each role sees, through the filter the pages use', () => {
  // Wrongly OPENED: an end user must never be handed a designated module. This
  // is the direction FB-03 argues — numbers that are deltas read as breakage.
  it('the user role sees no designated module', () => {
    expect(visibleTo('user').filter(isDesignated).map((m) => m.id)).toEqual([])
  })

  // Wrongly CLOSED: a default module must not vanish for anyone, and an sme
  // module must not vanish for the roles it is FOR. Nothing renders an error
  // when a module disappears — the only symptom is its absence.
  it('the user role sees every default module', () => {
    const defaults = MODULES.filter((m) => !isDesignated(m)).map((m) => m.id)
    expect(visibleTo('user').map((m) => m.id)).toEqual(defaults)
  })

  it('steward and admin see every sme module, in registry order', () => {
    const sme = MODULES.filter((m) => m.access === 'sme').map((m) => m.id)
    for (const role of ['steward', 'admin'] as const) {
      const seen = visibleTo(role).map((m) => m.id)
      expect(sme.filter((id) => !seen.includes(id)), `${role} lost an sme module`).toEqual([])
    }
  })

  it('admin sees the whole registry', () => {
    expect(visibleTo('admin').map((m) => m.id)).toEqual(MODULES.map((m) => m.id))
  })

  // The filter preserves registry order for every role, which the Overview
  // spokes depend on (clockwise from 12 o'clock is the registry order with the
  // hidden entries removed, not re-sorted).
  it('filtering never reorders: each role sees a subsequence of the registry', () => {
    const order = MODULES.map((m) => m.id)
    for (const role of ROLES) {
      const seen = visibleTo(role).map((m) => m.id)
      expect(seen).toEqual(order.filter((id) => seen.includes(id)))
    }
  })
})
