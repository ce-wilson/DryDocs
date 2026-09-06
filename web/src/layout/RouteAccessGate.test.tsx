// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'

import { GATED_SURFACES, MODULES } from '../modules/registry'
import RouteAccessGate from './RouteAccessGate'

// WEB3, the wiring half. routeAccess.test.ts proves canAccessPath answers
// correctly; this proves the GATE IS ACTUALLY IN THE PATH — that a refused
// pathname renders the redirect target instead of the guarded element. Both are
// needed: the O59 bug was a correct predicate that no route consulted, so a
// suite that only tested the predicate would have passed all the way through it.

afterEach(cleanup)

function renderAt(pathname: string, role: 'user' | 'steward' | 'admin') {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <Routes>
        <Route element={<RouteAccessGate role={role} />}>
          <Route path="/" element={<p>home</p>} />
          <Route path="*" element={<p>guarded</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

const GATED_MODULE_PATHS = MODULES.filter((m) => m.access && m.access !== 'all').map((m) => m.path)
const SME_ONLY = [...GATED_MODULE_PATHS, ...GATED_SURFACES.filter((s) => s.access === 'sme').map((s) => s.path)]
const ADMIN_ONLY = GATED_SURFACES.filter((s) => s.access === 'admin').map((s) => s.path)

describe('RouteAccessGate redirects rather than renders', () => {
  it.each(SME_ONLY)('%s is refused for a user', (path) => {
    renderAt(path, 'user')
    expect(screen.getByText('home')).toBeTruthy()
    expect(screen.queryByText('guarded')).toBeNull()
  })

  it.each(SME_ONLY)('%s renders for a steward', (path) => {
    renderAt(path, 'steward')
    expect(screen.getByText('guarded')).toBeTruthy()
  })

  it.each(ADMIN_ONLY)('%s is refused for a steward and rendered for an admin', (path) => {
    renderAt(path, 'steward')
    expect(screen.getByText('home')).toBeTruthy()
    cleanup()
    renderAt(path, 'admin')
    expect(screen.getByText('guarded')).toBeTruthy()
  })

  it('an ungated route renders for every role', () => {
    for (const role of ['user', 'steward', 'admin'] as const) {
      renderAt('/explorer', role)
      expect(screen.getByText('guarded')).toBeTruthy()
      cleanup()
    }
  })

  it('a deep link under a gated module is refused too', () => {
    renderAt('/remediation/finding/17', 'user')
    expect(screen.getByText('home')).toBeTruthy()
  })
})
