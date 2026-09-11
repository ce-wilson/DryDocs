import { describe, expect, it } from 'vitest'

import { resolveRbcYear, type RuleBasedCalendarDef } from './rbcCalendar'

// Independent oracle for weekday assertions: the JS engine's own UTC date
// arithmetic, a different code path than rbcCalendar's hand-rolled
// weekdayIndex (which deliberately avoids Date to keep the calculation clear
// of the runtime's local timezone). Using Date only here, never in the
// module under test, is what makes this a real cross-check and not a mirror.
function utcWeekday(year: number, month: number, day: number): number {
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay()
}

describe('resolveRbcYear — the year-boundary refusal (G86 acceptance)', () => {
  const calendar: RuleBasedCalendarDef = {
    name: 'WORKDAYS',
    years: [2025, 2026],
    rule: { type: 'specific-dates', dates: ['12-25'] },
  }

  it('a declared year resolves', () => {
    const result = resolveRbcYear(calendar, 2026)
    expect(result).toEqual({ status: 'resolved', year: 2026, dates: ['2026-12-25'] })
  })

  it('an undeclared year refuses rather than silently projecting', () => {
    // The calendar says nothing about 2028; the vendor doc's own words are
    // "a projection may only extend as far as the calendar's year coverage".
    const result = resolveRbcYear(calendar, 2028)
    expect(result).toEqual({ status: 'out-of-coverage', year: 2028, declaredYears: [2025, 2026] })
  })

  it('out-of-coverage is not the same shape as "resolved with zero dates" — a caller can tell them apart', () => {
    const empty: RuleBasedCalendarDef = { name: 'EMPTY', years: [2026], rule: { type: 'specific-dates', dates: [] } }
    expect(resolveRbcYear(empty, 2026)).toEqual({ status: 'resolved', year: 2026, dates: [] })
    expect(resolveRbcYear(empty, 2027).status).toBe('out-of-coverage')
  })
})

describe('specific-dates rule', () => {
  it('recurs at the same month-day independent of the calendar year', () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'HOLIDAYS',
      years: [2025, 2026],
      rule: { type: 'specific-dates', dates: ['01-01', '07-04'] },
    }
    expect(resolveRbcYear(calendar, 2025)).toEqual({
      status: 'resolved',
      year: 2025,
      dates: ['2025-01-01', '2025-07-04'],
    })
  })

  it('drops a date the target year cannot have (Feb 30 — malformed input, not silently clamped)', () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'BAD',
      years: [2026],
      rule: { type: 'specific-dates', dates: ['02-30'] },
    }
    expect(resolveRbcYear(calendar, 2026)).toEqual({ status: 'resolved', year: 2026, dates: [] })
  })
})

describe('month-days rule', () => {
  it('applies to every month by default', () => {
    const calendar: RuleBasedCalendarDef = { name: 'M15', years: [2026], rule: { type: 'month-days', days: [15] } }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status === 'resolved') expect(result.dates).toHaveLength(12)
  })

  it('restricts to declared months', () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'Q1-15',
      years: [2026],
      rule: { type: 'month-days', days: [15], months: [1, 2, 3] },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result).toEqual({
      status: 'resolved',
      year: 2026,
      dates: ['2026-01-15', '2026-02-15', '2026-03-15'],
    })
  })

  it('skips a day-of-month a given month does not have, rather than clamping it', () => {
    // Day 30 exists in every month except February. 2026 is not a leap year.
    const calendar: RuleBasedCalendarDef = { name: 'D30', years: [2026], rule: { type: 'month-days', days: [30] } }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status === 'resolved') {
      expect(result.dates).toHaveLength(11)
      expect(result.dates).not.toContain('2026-02-30')
    }
  })
})

describe('weekdays rule, checked against an independent Date-based oracle', () => {
  it("'any' occurrence matches every Monday in the year", () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'MONDAYS',
      years: [2026],
      rule: { type: 'weekdays', weekdays: ['MON'], occurrence: 'any' },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status !== 'resolved') return
    for (const iso of result.dates) {
      const [y, m, d] = iso.split('-').map(Number)
      expect(utcWeekday(y, m, d)).toBe(1) // Monday
    }
    expect(result.dates).toHaveLength(52) // 2026 has 52 Mondays
  })

  it("'last' occurrence picks the last matching weekday of each month", () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'LAST-FRI',
      years: [2026],
      rule: { type: 'weekdays', weekdays: ['FRI'], occurrence: 'last' },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status !== 'resolved') return
    expect(result.dates).toHaveLength(12)
    for (const iso of result.dates) {
      const [y, m, d] = iso.split('-').map(Number)
      expect(utcWeekday(y, m, d)).toBe(5) // Friday
      // No later day in the same month is also a Friday.
      const cap = new Date(Date.UTC(y, m, 0)).getUTCDate()
      for (let day = d + 1; day <= cap; day++) expect(utcWeekday(y, m, day)).not.toBe(5)
    }
  })

  it('a numbered occurrence (3rd Wednesday) matches the oracle exactly', () => {
    const calendar: RuleBasedCalendarDef = {
      name: '3RD-WED',
      years: [2026],
      rule: { type: 'weekdays', weekdays: ['WED'], occurrence: 3 },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status !== 'resolved') return
    for (let month = 1; month <= 12; month++) {
      const wednesdays: number[] = []
      const cap = new Date(Date.UTC(2026, month, 0)).getUTCDate()
      for (let day = 1; day <= cap; day++) if (utcWeekday(2026, month, day) === 3) wednesdays.push(day)
      const expected = wednesdays[2]
      const iso = `2026-${String(month).padStart(2, '0')}-${String(expected).padStart(2, '0')}`
      expect(result.dates).toContain(iso)
    }
  })
})

describe('advanced rule — AND/OR combination', () => {
  const specificJuly4: RuleBasedCalendarDef['rule'] = { type: 'specific-dates', dates: ['07-04'] }
  const mondays: RuleBasedCalendarDef['rule'] = { type: 'weekdays', weekdays: ['MON'], occurrence: 'any' }

  it('OR unions the sub-rules', () => {
    const calendar: RuleBasedCalendarDef = {
      name: 'OR',
      years: [2026],
      rule: { type: 'advanced', combine: 'OR', rules: [specificJuly4, { type: 'month-days', days: [1] } as const] },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status !== 'resolved') return
    expect(result.dates).toContain('2026-07-04')
    expect(result.dates).toContain('2026-01-01')
    expect(result.dates).toHaveLength(13) // 12 month-starts + July 4th (not a month-start)
  })

  it('AND intersects the sub-rules', () => {
    // Every day-of-month-4 that also falls on a Monday, 2026.
    const calendar: RuleBasedCalendarDef = {
      name: 'AND',
      years: [2026],
      rule: { type: 'advanced', combine: 'AND', rules: [mondays, { type: 'month-days', days: [4] } as const] },
    }
    const result = resolveRbcYear(calendar, 2026)
    expect(result.status).toBe('resolved')
    if (result.status !== 'resolved') return
    for (const iso of result.dates) {
      const [y, m, d] = iso.split('-').map(Number)
      expect(d).toBe(4)
      expect(utcWeekday(y, m, d)).toBe(1)
    }
    expect(result.dates.length).toBeGreaterThan(0)
  })
})
