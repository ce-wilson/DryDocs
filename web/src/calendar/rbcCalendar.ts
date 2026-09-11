// G86 spike: can a Rule-Based Calendar (RBC) be resolved into concrete dates,
// and drawn as an actual calendar, without silently projecting past what the
// calendar declares? external/orchestration/bmc-controlm/controlm-calendars.md
// names four RBC rule types (Specific Dates, Weekdays, Month Days, Advanced)
// and one hard constraint this module exists to prove out: "calendars are
// defined against EXPLICIT YEARS... a UI that silently projects past it is
// WRONG" (G86 acceptance, quoting the vendor doc's Authoritative Additions).
//
// This is a SPIKE, not the production resolver. When Phase A of
// knowledge/standards/technology/calendar-resolution-projection-plan.md lands
// (acquiring real RBC definitions into the graph), the production version of
// this logic belongs in drydocs_core per MODULE_MAP.md — pure resolve logic,
// no graph write, no run cadence. What is proved here: the four rule types
// are resolvable into a date set, and the year-boundary refusal is a real
// return value, not a comment.

export type Weekday = 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN'

const WEEKDAY_INDEX: Record<Weekday, number> = {
  SUN: 0,
  MON: 1,
  TUE: 2,
  WED: 3,
  THU: 4,
  FRI: 5,
  SAT: 6,
}

/** Which occurrence of the weekday within its month. `'any'` = every one. */
export type WeekdayOccurrence = 'any' | 1 | 2 | 3 | 4 | 'last'

export interface RbcSpecificDatesRule {
  type: 'specific-dates'
  /** `'MM-DD'`, independent of calendar year (vendor doc: "up to 12-month cycles"). */
  dates: string[]
}

export interface RbcWeekdaysRule {
  type: 'weekdays'
  weekdays: Weekday[]
  occurrence: WeekdayOccurrence
}

export interface RbcMonthDaysRule {
  type: 'month-days'
  /** 1-31. */
  days: number[]
  /** 1-12; omitted means every month. */
  months?: number[]
}

export interface RbcAdvancedRule {
  type: 'advanced'
  combine: 'AND' | 'OR'
  rules: RbcRule[]
}

export type RbcRule = RbcSpecificDatesRule | RbcWeekdaysRule | RbcMonthDaysRule | RbcAdvancedRule

export interface RuleBasedCalendarDef {
  name: string
  /** The calendar's declared coverage — "Apply on" years, vendor doc §Regular calendar. */
  years: number[]
  rule: RbcRule
}

export type CalendarResolution =
  | { status: 'resolved'; year: number; dates: string[] }
  | { status: 'out-of-coverage'; year: number; declaredYears: number[] }

function isLeap(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0
}

const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

function daysInMonth(year: number, month: number): number {
  return month === 2 && isLeap(year) ? 29 : DAYS_IN_MONTH[month - 1]
}

function iso(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

/** `0` (Sunday) .. `6` (Saturday), via the proleptic-Gregorian day count — no `Date` object,
 * so the calculation cannot silently pick up the runtime's local timezone. */
function weekdayIndex(year: number, month: number, day: number): number {
  const t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
  const y = month < 3 ? year - 1 : year
  return (y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) + t[month - 1] + day) % 7
}

function resolveWeekdaysRule(rule: RbcWeekdaysRule, year: number): Set<string> {
  const wanted = new Set(rule.weekdays.map((w) => WEEKDAY_INDEX[w]))
  const out = new Set<string>()
  for (let month = 1; month <= 12; month++) {
    const matches: number[] = []
    for (let day = 1; day <= daysInMonth(year, month); day++) {
      if (wanted.has(weekdayIndex(year, month, day))) matches.push(day)
    }
    if (rule.occurrence === 'any') {
      for (const day of matches) out.add(iso(year, month, day))
      continue
    }
    // Group by weekday so "3rd Wednesday" and "last Friday" are per-weekday
    // ordinals, not per-month ordinals across mixed weekdays.
    const byWeekday = new Map<number, number[]>()
    for (const day of matches) {
      const wd = weekdayIndex(year, month, day)
      const list = byWeekday.get(wd) ?? []
      list.push(day)
      byWeekday.set(wd, list)
    }
    for (const list of byWeekday.values()) {
      const day = rule.occurrence === 'last' ? list[list.length - 1] : list[rule.occurrence - 1]
      if (day !== undefined) out.add(iso(year, month, day))
    }
  }
  return out
}

function resolveMonthDaysRule(rule: RbcMonthDaysRule, year: number): Set<string> {
  const months = rule.months ?? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  const out = new Set<string>()
  for (const month of months) {
    const cap = daysInMonth(year, month)
    for (const day of rule.days) {
      // A day past the month's real length (e.g. day 30 in February) is a
      // rule that this month cannot satisfy — skipped, not clamped: clamping
      // would draw a date the rule never named.
      if (day >= 1 && day <= cap) out.add(iso(year, month, day))
    }
  }
  return out
}

function resolveSpecificDatesRule(rule: RbcSpecificDatesRule, year: number): Set<string> {
  const out = new Set<string>()
  for (const md of rule.dates) {
    const [month, day] = md.split('-').map(Number)
    if (month >= 1 && month <= 12 && day >= 1 && day <= daysInMonth(year, month)) {
      out.add(iso(year, month, day))
    }
  }
  return out
}

function resolveRule(rule: RbcRule, year: number): Set<string> {
  switch (rule.type) {
    case 'specific-dates':
      return resolveSpecificDatesRule(rule, year)
    case 'weekdays':
      return resolveWeekdaysRule(rule, year)
    case 'month-days':
      return resolveMonthDaysRule(rule, year)
    case 'advanced': {
      const sets = rule.rules.map((r) => resolveRule(r, year))
      if (sets.length === 0) return new Set()
      if (rule.combine === 'OR') return sets.reduce((acc, s) => new Set([...acc, ...s]))
      return sets.reduce((acc, s) => new Set([...acc].filter((d) => s.has(d))))
    }
  }
}

/**
 * Resolve one calendar year against its rule — but only if the calendar
 * DECLARES that year. This is the boundary the acceptance names: a calendar
 * defined through 2027 says nothing about 2028, and returning an empty
 * `resolved` set for 2028 would read as "the calendar is empty that year"
 * rather than "the calendar was never asked about that year". The two are
 * different facts and the caller (the renderer) must be able to tell them
 * apart.
 */
export function resolveRbcYear(calendar: RuleBasedCalendarDef, year: number): CalendarResolution {
  if (!calendar.years.includes(year)) {
    return { status: 'out-of-coverage', year, declaredYears: [...calendar.years].sort((a, b) => a - b) }
  }
  return { status: 'resolved', year, dates: [...resolveRule(calendar.rule, year)].sort() }
}
