// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import FailureLadder from './FailureLadder'
import type { ProbeResult, ServiceId, ServiceVerdict } from '../lib/serviceProbe'

// O63 — the ladder ON SCREEN. The machine itself is tested as a pure function
// (lib/askLadder.test.ts); this asserts the two things only rendering can show:
// the originating error survives the round trip untouched, and the checking
// state actually reaches the DOM before any verdict does.

function verdict(id: ServiceId, state: ServiceVerdict['state'], detail: string | null = null) {
  return { id, label: id, state, detail } satisfies ServiceVerdict
}

function probeReturning(services: ServiceVerdict[]) {
  return vi.fn(
    async (): Promise<ProbeResult> => ({ services, checkedAt: new Date('2026-09-06T14:00:00Z') }),
  )
}

afterEach(cleanup)

describe('the Ask failure ladder on screen', () => {
  it('renders the browser text verbatim, before anything else', async () => {
    render(
      <FailureLadder error="Failed to fetch" probe={probeReturning([verdict('agent', 'ok')])} />,
    )
    const original = await screen.findByText('Failed to fetch')
    expect(original.getAttribute('data-stage')).toBe('original')
    // First child of the list: the reader sees what the browser said before the
    // console's interpretation of it.
    expect(original.parentElement?.firstElementChild).toBe(original)
  })

  it('shows the checking state while the probe is in flight, then the verdicts', async () => {
    let release: (r: ProbeResult) => void = () => {}
    const probe = vi.fn(
      () =>
        new Promise<ProbeResult>((resolve) => {
          release = resolve
        }),
    )
    const { container } = render(<FailureLadder error="Failed to fetch" probe={probe} />)

    // (b) distinct from both success and failure — and present BEFORE any
    // verdict, which is the whole point of the clause.
    expect(container.querySelector('[data-stage="checking"]')).toBeTruthy()
    expect(container.querySelector('[data-stage="service"]')).toBeNull()

    release({
      services: [verdict('agent', 'down', 'nothing answered')],
      checkedAt: new Date(),
    })
    await waitFor(() => expect(container.querySelector('[data-stage="service"]')).toBeTruthy())
    expect(container.querySelector('[data-stage="checking"]')).toBeNull()
  })

  it('carries the provider text as-is, naming the key and the file', async () => {
    const detail = 'ANTHROPIC_API_KEY is not set (agents/.env)'
    render(
      <FailureLadder
        error="agent error"
        probe={probeReturning([verdict('agent', 'ok'), verdict('provider', 'down', detail)])}
      />,
    )
    // Whole, not paraphrased: this is the string that tells the reader the exact
    // key AND the exact file, which is the entire value of surfacing it.
    expect(await screen.findByText(detail)).toBeTruthy()
  })

  it('tells the two agent failures apart on screen', async () => {
    const { container, rerender } = render(
      <FailureLadder
        error="Failed to fetch"
        probe={probeReturning([verdict('agent', 'down', 'nothing answered at /agent')])}
      />,
    )
    await waitFor(() =>
      expect(container.querySelector('[data-service="agent"][data-state="down"]')).toBeTruthy(),
    )
    expect(container.textContent).toContain('nothing answered at /agent')

    rerender(
      <FailureLadder
        error="Failed to fetch (2)"
        probe={probeReturning([
          verdict('agent', 'ok'),
          verdict('provider', 'down', 'ANTHROPIC_API_KEY is not set (agents/.env)'),
        ])}
      />,
    )
    await waitFor(() =>
      expect(container.querySelector('[data-service="provider"][data-state="down"]')).toBeTruthy(),
    )
    // The two states render differently — which is the item's whole reason for
    // existing, since both used to print "the Ask page is broken".
    expect(container.textContent).not.toContain('nothing answered at /agent')
  })

  it('re-probes for a NEW failure rather than reusing the old verdict', async () => {
    const probe = probeReturning([verdict('agent', 'ok')])
    const { rerender } = render(<FailureLadder error="first" probe={probe} />)
    await waitFor(() => expect(probe).toHaveBeenCalledTimes(1))
    rerender(<FailureLadder error="second" probe={probe} />)
    await waitFor(() => expect(probe).toHaveBeenCalledTimes(2))
    // A stale verdict presented as a fresh one is the failure this avoids.
  })

  it('offers the support hand-off only when every check came back ok', async () => {
    const { container } = render(
      <FailureLadder
        error="Failed to fetch"
        probe={probeReturning([verdict('agent', 'ok'), verdict('provider', 'ok')])}
      />,
    )
    await waitFor(() => expect(container.querySelector('[data-stage="handoff"]')).toBeTruthy())
    expect(container.textContent).toContain('contact DryDocs support')
  })
})
