import { describe, expect, it } from 'vitest'

import {
  CANVAS_ROUTES,
  CANVAS_SURFACES,
  canvasRoutePath,
  isCanvasSpecId,
} from './nvl-mapping'
import { canAccessModule, MODULES } from '../modules/registry'

// O86. The route's whole safety story is the whitelist and the gate, and both
// are decidable without a browser — so they are tested here rather than left to
// a person clicking through.

describe('the whitelist', () => {
  it('admits every canvas surface', () => {
    for (const specId of Object.keys(CANVAS_SURFACES)) {
      expect(isCanvasSpecId(specId)).toBe(true)
    }
  })

  // The point of clause (b): an id outside the map renders a named refusal
  // rather than being passed through to drydocs-api. The API would refuse an
  // unregistered spec anyway — this is a refusal to invite the attempt.
  it('rejects anything else, including plausible near-misses', () => {
    for (const bad of [
      'runbooks.series.v2',
      'runbooks.series',
      '',
      '../admin',
      'constructor',
      'toString',
    ]) {
      expect(isCanvasSpecId(bad)).toBe(false)
    }
  })

  // `'toString' in obj` is true for every object literal. Object.hasOwn is why
  // the two prototype names above are refused, and this pins the reason.
  it('is not fooled by inherited properties', () => {
    expect(isCanvasSpecId('hasOwnProperty')).toBe(false)
    expect(isCanvasSpecId('__proto__')).toBe(false)
  })

  it('rejects undefined, which is what a missing route param gives it', () => {
    expect(isCanvasSpecId(undefined)).toBe(false)
  })
})

describe('every canvas surface has a route entry', () => {
  // The `satisfies Record<CanvasSpecId, CanvasRoute>` on CANVAS_ROUTES makes a
  // missing entry a COMPILE error. This asserts the same thing at runtime, so
  // the guarantee survives someone loosening the type.
  it('covers CANVAS_SURFACES exactly', () => {
    expect(Object.keys(CANVAS_ROUTES).sort()).toEqual(Object.keys(CANVAS_SURFACES).sort())
  })

  it('names a host module that exists in the registry', () => {
    for (const [specId, route] of Object.entries(CANVAS_ROUTES)) {
      const host = MODULES.find((m) => m.id === route.module)
      expect(host, `${specId} names a module the registry does not have`).toBeDefined()
    }
  })

  it('gives each surface a human title, since it becomes the page heading', () => {
    for (const route of Object.values(CANVAS_ROUTES)) {
      expect(route.title.trim().length).toBeGreaterThan(0)
    }
  })
})

describe('the route gates exactly like its host module', () => {
  // Clause (c). Not "is it gated" but "does it AGREE with the host" — a
  // full-page view stricter or looser than the tab it mirrors is the defect,
  // in either direction.
  //
  // The route reads the HOST's designation rather than carrying one of its own,
  // so the two cannot disagree: there is no second place to edit.
  it('carries no access designation of its own', () => {
    for (const route of Object.values(CANVAS_ROUTES)) {
      expect(route).not.toHaveProperty('access')
    }
  })

  // Stated rather than assumed, because it is the current fact and not a
  // permanent one: both hosts are open to every role today, so neither
  // full-page canvas is restricted. If a host is later designated 'sme', the
  // route follows WITHOUT a change here — which is the property being bought,
  // and this test is where a reader finds that out.
  it('inherits today: both hosts admit every role', () => {
    for (const route of Object.values(CANVAS_ROUTES)) {
      const host = MODULES.find((m) => m.id === route.module)!
      expect(canAccessModule(host.access, 'user')).toBe(true)
    }
  })

  // canAccessModule is the one function standing between a designation and a
  // rendered page, and O59 changed a designation with nothing testing it
  // (Idea-231). Covered here because this route depends on it being right.
  it('refuses a user for an sme designation, and admits steward and admin', () => {
    expect(canAccessModule('sme', 'user')).toBe(false)
    expect(canAccessModule('sme', 'steward')).toBe(true)
    expect(canAccessModule('sme', 'admin')).toBe(true)
    expect(canAccessModule(undefined, 'user')).toBe(true)
    expect(canAccessModule('all', 'user')).toBe(true)
    expect(canAccessModule('admin', 'steward')).toBe(false)
  })
})

describe('canvasRoutePath', () => {
  it('builds the path the router answers', () => {
    expect(canvasRoutePath('runbooks.series.v1')).toBe('/graph/runbooks.series.v1')
  })

  it('encodes the id, so a spec id can never break out of the segment', () => {
    // No current id needs it; the encoding is what keeps that true if one does.
    expect(canvasRoutePath('explorer.folder-applications.v1')).not.toContain(' ')
    expect(canvasRoutePath('explorer.folder-applications.v1').startsWith('/graph/')).toBe(true)
  })
})
