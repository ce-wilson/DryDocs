// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import RbcCalendarSpike from './RbcCalendarSpike'
import type { RuleBasedCalendarDef } from './rbcCalendar'

afterEach(cleanup)

describe('RbcCalendarSpike — the year-boundary behavior the acceptance names', () => {
  const calendar: RuleBasedCalendarDef = {
    name: 'WORKDAYS',
    years: [2026],
    rule: { type: 'weekdays', weekdays: ['FRI'], occurrence: 'last' },
  }

  it('an undeclared year renders the boundary state, not a blank grid', () => {
    const { container } = render(<RbcCalendarSpike calendar={calendar} year={2028} month={1} />)
    expect(container.querySelector('[data-rbc-status="out-of-coverage"]')).toBeTruthy()
    expect(container.querySelector('[data-rbc-status="resolved"]')).toBeNull()
    // The grid never rendered at all -- no day cells exist to be silently empty.
    expect(container.querySelectorAll('[data-rbc-date]')).toHaveLength(0)
    expect(screen.getByText(/does not cover 2028/)).toBeTruthy()
    expect(screen.getByText(/Declared years: 2026/)).toBeTruthy()
  })

  it('a declared year renders a full month grid with the matched days flagged', () => {
    const { container } = render(<RbcCalendarSpike calendar={calendar} year={2026} month={1} />)
    expect(container.querySelector('[data-rbc-status="resolved"]')).toBeTruthy()
    // January 2026 has 31 days -- every one is a cell, matched or not.
    expect(container.querySelectorAll('[data-rbc-date]')).toHaveLength(31)
    const matches = container.querySelectorAll('[data-rbc-match="true"]')
    expect(matches).toHaveLength(1) // one last-Friday per month
    expect(matches[0].getAttribute('data-rbc-date')).toBe('2026-01-30') // last Friday of Jan 2026
  })

  it('a month with no matching date still renders every cell as a non-match, never omitted', () => {
    const noMatch: RuleBasedCalendarDef = { name: 'NONE', years: [2026], rule: { type: 'specific-dates', dates: [] } }
    const { container } = render(<RbcCalendarSpike calendar={noMatch} year={2026} month={2} />)
    expect(container.querySelectorAll('[data-rbc-date]')).toHaveLength(28) // Feb 2026, not a leap year
    expect(container.querySelectorAll('[data-rbc-match="true"]')).toHaveLength(0)
  })
})
