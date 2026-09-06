// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { sessionRejected, signOut } from './auth'
import { clearAll, STORAGE_KEYS, STORAGE_PREFIX, survivesSignOut } from './storage'
import { codeOnly, filesMatching } from '../test/sourceScan'

// WEB11 — signOut cleared one key of eight. These tests populate all eight and
// assert what is left, because "did it clear?" is only answerable against a
// FULL store: a test that clears an empty store passes and proves nothing.

/** Every key a real session leaves behind, at its real spelling. */
const POPULATED: Record<string, string> = {
  'drydocs.session.v2': '{"token":"t","personaId":"mouse"}',
  'drydocs.ask.last-turn.mouse': '{"question":"who owns PARAD0060","envelope":{}}',
  'drydocs.app-code-tray.mouse': '["PROD_HL_12"]',
  'drydocs.onboarding.v1': '["explorer"]',
  'drydocs.theme.v1': 'dark',
  'drydocs.aside-collapsed.v1': '1',
  'drydocs.split.explorer': '320',
  'drydocs.grid-widths.seal-contact-override': '{"app":120}',
}

const SURVIVORS = ['drydocs.theme.v1', 'drydocs.aside-collapsed.v1', 'drydocs.split.explorer', 'drydocs.grid-widths.seal-contact-override']

function populate() {
  for (const [k, v] of Object.entries(POPULATED)) localStorage.setItem(k, v)
}

function remaining(): string[] {
  return Object.keys(POPULATED).filter((k) => localStorage.getItem(k) !== null)
}

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

describe('the retention decision is declared, once', () => {
  it('every declared key sits under the console prefix', () => {
    for (const spec of STORAGE_KEYS) expect(spec.key.startsWith(STORAGE_PREFIX)).toBe(true)
  })

  it('every key that survives says why', () => {
    for (const spec of STORAGE_KEYS) expect(spec.why.length).toBeGreaterThan(20)
  })

  it('an UNDECLARED key does not survive — default-deny', () => {
    // The safe direction to be wrong in: a key someone adds and forgets to
    // declare is cleared, not silently retained across sign-outs.
    expect(survivesSignOut('drydocs.something-new.v1')).toBe(false)
  })

  it('the two that hold query results do NOT survive', () => {
    expect(survivesSignOut('drydocs.ask.last-turn.mouse')).toBe(false)
    expect(survivesSignOut('drydocs.app-code-tray.mouse')).toBe(false)
  })
})

describe('clearAll leaves only what opted out', () => {
  it('directly', () => {
    populate()
    expect(remaining()).toHaveLength(8)
    clearAll()
    expect(remaining().sort()).toEqual([...SURVIVORS].sort())
  })

  it('through signOut (clause d)', () => {
    populate()
    signOut()
    expect(remaining().sort()).toEqual([...SURVIVORS].sort())
    expect(localStorage.getItem('drydocs.ask.last-turn.mouse')).toBeNull()
  })

  it('through sessionRejected — the path an EXPIRY takes (clause d)', () => {
    // The gap that matters more: nobody decides to have their session expire,
    // so this is the path a shared desktop actually goes down.
    populate()
    sessionRejected()
    expect(remaining().sort()).toEqual([...SURVIVORS].sort())
  })

  it('sweeps a per-persona key it has never seen', () => {
    // The keys are prefixed by persona, so clearing cannot work from a fixed
    // list — it sweeps the prefix. A second persona's leftovers go too.
    localStorage.setItem('drydocs.ask.last-turn.neo', '{}')
    localStorage.setItem('drydocs.app-code-tray.trinity', '[]')
    clearAll()
    expect(localStorage.getItem('drydocs.ask.last-turn.neo')).toBeNull()
    expect(localStorage.getItem('drydocs.app-code-tray.trinity')).toBeNull()
  })

  it('leaves another applications keys alone', () => {
    localStorage.setItem('someone-else.thing', 'keep me')
    populate()
    clearAll()
    expect(localStorage.getItem('someone-else.thing')).toBe('keep me')
  })
})

describe('no localStorage call exists outside the module (clause a)', () => {
  it('is true', () => {
    const offenders = filesMatching(/localStorage\./).filter((f) => f !== 'lib/storage.ts')
    expect(offenders).toEqual([])
  })

  it('and the scan can see a real call (instrument check)', () => {
    // Twice this burst a scan was written against the wrong stripper and passed
    // vacuously. `localStorage.` is a CODE shape, so codeOnly is right here —
    // and this asserts it finds one.
    expect(/localStorage\./.test(codeOnly('localStorage.getItem(k)'))).toBe(true)
    expect(/localStorage\./.test(codeOnly('// localStorage.getItem was here'))).toBe(false)
    expect(filesMatching(/localStorage\./)).toContain('lib/storage.ts')
  })
})
