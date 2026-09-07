// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import QualityRail from './QualityRail'
import ReviewerQualityPanel from './ReviewerQualityPanel'
import type { PersonaQuality } from '../lib/reviewQuality'

// O51. What these assert is the posture, not the layout: a metric with no
// source says so instead of showing a number, a rate below the decision floor
// carries its explanation, and the block is a deliberate act with a reason.

afterEach(cleanup)

function persona(over: Partial<PersonaQuality> = {}): PersonaQuality {
  return {
    persona_id: 'sme1',
    submissions: 8,
    auto_accept_rate: null,
    auto_accept_unavailable_because: 'Not computable yet: … lands with O48.',
    too_fast_rate: 0.5,
    admin_return_rate: 0.1,
    median_review_seconds: 42,
    flags: [{ metric: 'too_fast_rate', value: 0.5, limit: 0.3, detail: '4 of 8 confirms' }],
    blocked: false,
    ...over,
  }
}

describe('the auto-accept metric', () => {
  it('prints its reason rather than a number or a bare dash', () => {
    render(
      <ReviewerQualityPanel persona={persona()} windowDays={30} minDecisionsForFlag={5} />,
    )
    expect(screen.getByText(/Auto-accept is not measured yet/)).toBeTruthy()
    expect(screen.getByText(/lands with O48/)).toBeTruthy()
    // and NOT a zero: 0% reads as a reviewer who modifies every candidate
    expect(screen.queryByText('0%')).toBeNull()
  })
})

describe('a flag', () => {
  it('names the limit it was compared against', () => {
    render(
      <ReviewerQualityPanel persona={persona()} windowDays={30} minDecisionsForFlag={5} />,
    )
    expect(screen.getByText(/limit 30%/)).toBeTruthy()
    expect(screen.getByText(/4 of 8 confirms/)).toBeTruthy()
  })

  it('is absent below the decision floor, and the panel says why', () => {
    render(
      <ReviewerQualityPanel
        persona={persona({ submissions: 2, flags: [] })}
        windowDays={30}
        minDecisionsForFlag={5}
      />,
    )
    expect(screen.getByText(/Fewer than 5 decisions/)).toBeTruthy()
    // the numbers are still shown — suppressing a flag is not hiding the data
    expect(screen.getByText('2')).toBeTruthy()
  })
})

describe('the block', () => {
  it('cannot be placed without a reason', () => {
    const onBlock = vi.fn()
    render(
      <ReviewerQualityPanel
        persona={persona()}
        windowDays={30}
        minDecisionsForFlag={5}
        onBlock={onBlock}
      />,
    )
    const button = screen.getByRole('button', { name: 'Block from submitting' })
    expect(button.hasAttribute('disabled')).toBe(true)
    fireEvent.click(button)
    expect(onBlock).not.toHaveBeenCalled()

    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'rubber-stamping' } })
    expect(button.hasAttribute('disabled')).toBe(false)
    fireEvent.click(button)
    expect(onBlock).toHaveBeenCalledWith('sme1', 'rubber-stamping')
  })

  it('shows who placed it and needs a note to lift', () => {
    const onUnblock = vi.fn()
    render(
      <ReviewerQualityPanel
        persona={persona({ blocked: true })}
        windowDays={30}
        minDecisionsForFlag={5}
        block={{
          block_id: 'b1',
          persona_id: 'sme1',
          blocked_at: '2026-09-07T10:00:00+00:00',
          blocked_by: 'morpheus',
          reason: 'rubber-stamping',
        }}
        onUnblock={onUnblock}
      />,
    )
    expect(screen.getByText(/by morpheus: rubber-stamping/)).toBeTruthy()
    const button = screen.getByRole('button', { name: 'Lift the block' })
    expect(button.hasAttribute('disabled')).toBe(true)
    fireEvent.change(screen.getByLabelText(/Note/), { target: { value: 'coached' } })
    fireEvent.click(button)
    expect(onUnblock).toHaveBeenCalledWith('sme1', 'coached')
  })

  it('surfaces the server refusal verbatim', () => {
    render(
      <ReviewerQualityPanel
        persona={persona()}
        windowDays={30}
        minDecisionsForFlag={5}
        error="blocking a reviewer is an admin decision"
      />,
    )
    expect(screen.getByText('blocking a reviewer is an admin decision')).toBeTruthy()
  })
})

describe('the rail', () => {
  it('says an empty rail is the ordinary state, not a failed read', () => {
    render(<QualityRail personas={[persona({ flags: [], blocked: false })]} />)
    expect(screen.getByText(/an empty rail is the ordinary state/)).toBeTruthy()
  })

  it('carries the metric that tripped, and selects a reviewer without blocking one', () => {
    const onSelect = vi.fn()
    render(<QualityRail personas={[persona()]} onSelect={onSelect} />)
    const row = screen.getByRole('button', { name: /sme1/ })
    expect(within(row).getByText(/4 of 8 confirms/)).toBeTruthy()
    fireEvent.click(row)
    expect(onSelect).toHaveBeenCalledWith('sme1')
    // no block control on the rail: the decision lives behind a reason field
    expect(screen.queryByRole('button', { name: /Block/ })).toBeNull()
  })
})
