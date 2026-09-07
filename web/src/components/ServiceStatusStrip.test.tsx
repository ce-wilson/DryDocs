// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ServiceStatusStrip from './ServiceStatusStrip'
import { checkedAtLabel, type ProbeResult, type ServiceId, type ServiceVerdict } from '../lib/serviceProbe'

// O63 (f) — the strip's two promises: it never shows a verdict it does not
// have, and it never implies it is watching.

function verdict(id: ServiceId, state: ServiceVerdict['state'], detail: string | null = null) {
  return { id, label: id, state, detail } satisfies ServiceVerdict
}

const AT = new Date('2026-09-06T14:05:00Z')

afterEach(cleanup)

function probeReturning(services: ServiceVerdict[], at: Date = AT) {
  return vi.fn(async (): Promise<ProbeResult> => ({ services, checkedAt: at }))
}

/** A probe that never settles — the in-flight state. */
function probeHanging() {
  return vi.fn(() => new Promise<ProbeResult>(() => {}))
}

describe('the service-status strip', () => {
  it('renders "not checked" rather than a verdict before its first run', async () => {
    // The acceptance names this case specifically, and it is rule 1 at the
    // moment it matters most: an empty or green strip on first paint is a claim
    // the page has not earned.
    render(<ServiceStatusStrip probe={probeHanging()} now={() => AT} />)
    const strip = screen.getByLabelText('service status')
    expect(strip).toBeTruthy()
    expect(screen.getByTestId('checked-at').textContent).toMatch(/checking|not checked yet/)
    // Nothing may read as ok while nothing has answered.
    expect(strip.textContent).not.toMatch(/\bok\b/)
  })

  it('carries a timestamp beside the verdict once it has run', async () => {
    render(
      <ServiceStatusStrip
        probe={probeReturning([verdict('api', 'ok'), verdict('agent', 'ok')])}
        now={() => AT}
      />,
    )
    await waitFor(() =>
      expect(screen.getByTestId('checked-at').textContent).toBe(checkedAtLabel(AT)),
    )
    // A stale-but-DATED verdict is honest; an undated one cannot be judged.
    expect(screen.getByTestId('checked-at').textContent).toMatch(/^checked /)
  })

  it('re-checks on demand, and only on demand', async () => {
    const probe = probeReturning([verdict('api', 'ok')])
    render(<ServiceStatusStrip probe={probe} now={() => AT} />)
    await waitFor(() => expect(probe).toHaveBeenCalledTimes(1))

    // NO TIMER. The strip must not imply a real-time system it is not; if it
    // polled, this wait would show a second call with nobody asking.
    await new Promise((r) => setTimeout(r, 60))
    expect(probe).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: /re-check/i }))
    await waitFor(() => expect(probe).toHaveBeenCalledTimes(2))
  })

  it('shows a down service and carries the server text verbatim', async () => {
    const detail = 'ANTHROPIC_API_KEY is not set (agents/.env)'
    render(
      <ServiceStatusStrip
        probe={probeReturning([verdict('provider', 'down', detail)])}
        now={() => AT}
      />,
    )
    await waitFor(() => expect(screen.getByText(detail)).toBeTruthy())
  })

  it('labels services by name, never by port (ADR 0020)', async () => {
    render(
      <ServiceStatusStrip
        probe={probeReturning([verdict('api', 'ok'), verdict('agent', 'ok')])}
        now={() => AT}
      />,
    )
    await waitFor(() => expect(screen.getByTestId('checked-at').textContent).toMatch(/^checked/))
    const text = screen.getByLabelText('service status').textContent ?? ''
    expect(text).not.toMatch(/:\d{4,5}\b/)
    expect(text).not.toMatch(/localhost|https?:\/\//)
  })

  it('checkedAtLabel says "not checked yet" for a null instant', () => {
    expect(checkedAtLabel(null)).toBe('not checked yet')
    expect(checkedAtLabel(AT)).toMatch(/^checked \d/)
  })
})
