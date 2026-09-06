// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import RouteErrorBoundary from './RouteErrorBoundary'

// WEB5 (c). What is being proven is not "a boundary exists" but the three
// properties that make it worth having: the SHELL survives, the message is
// verbatim, and navigating away clears it.

const MESSAGE = 'Cannot read properties of null (reading "job_name")'

let throwsNow = true

function Boom(): React.JSX.Element {
  if (throwsNow) throw new Error(MESSAGE)
  return <p>recovered</p>
}

function Shell({ initial = '/boom' }: { initial?: string }) {
  return (
    <MemoryRouter initialEntries={[initial]}>
      <nav>
        the shell nav <Link to="/fine">go elsewhere</Link>
      </nav>
      <Routes>
        <Route element={<RouteErrorBoundary />}>
          <Route path="/boom" element={<Boom />} />
          <Route path="/fine" element={<p>a healthy page</p>} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  throwsNow = true
  // React logs the caught error itself; the boundary logs it again on purpose
  // (there is no telemetry). Silenced so a passing test is not a wall of red.
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
})
afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('a render throw breaks one panel', () => {
  it('the shell survives — this is the whole point', () => {
    render(<Shell />)
    expect(screen.getByText('the shell nav')).toBeTruthy()
    expect(screen.getByText('This panel could not be rendered')).toBeTruthy()
  })

  it('shows the message VERBATIM, because that string goes into a ticket', () => {
    render(<Shell />)
    expect(screen.getByText(MESSAGE)).toBeTruthy()
  })

  it('shows no stack trace and no data from the row that threw', () => {
    render(<Shell />)
    const panel = screen.getByText('This panel could not be rendered').closest('div')!
    expect(panel.textContent).not.toContain('at ')
    expect(panel.querySelector('pre')).toBeNull()
  })

  it('a healthy route renders normally, with no boundary in the way', () => {
    render(<Shell initial="/fine" />)
    expect(screen.getByText('a healthy page')).toBeTruthy()
    expect(screen.queryByText('This panel could not be rendered')).toBeNull()
  })

  it('navigating away clears it — the key is what makes moving away the recovery', () => {
    // Without the pathname key a latched boundary carries its fallback to the
    // NEXT route, and the console stays broken until a reload: the same outcome
    // this item exists to prevent, one layer down.
    render(<Shell />)
    expect(screen.getByText('This panel could not be rendered')).toBeTruthy()
    fireEvent.click(screen.getByText('go elsewhere'))
    expect(screen.getByText('a healthy page')).toBeTruthy()
    expect(screen.queryByText('This panel could not be rendered')).toBeNull()
  })

  it('the retry REMOUNTS, so a transient failure actually recovers', () => {
    // A retry that only cleared the boundary's state would re-render the same
    // components over the same failed data and throw again — a button that
    // looks like a retry and is not one.
    render(<Shell />)
    throwsNow = false
    fireEvent.click(screen.getByText('Try this page again'))
    expect(screen.getByText('recovered')).toBeTruthy()
    expect(screen.queryByText('This panel could not be rendered')).toBeNull()
  })
})
