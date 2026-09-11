// G86 spike: can a RULE_BASED_CALENDAR draw as an actual calendar in the
// console? This is the answer, scoped to RBC only per the acceptance ("render
// a calendar is really three renderers -- scope a spike to RBC only first").
//
// NOT wired into a route or the module registry: the graph carries no RBC
// definitions today (see the G86 ruling doc,
// docs/reviews/g86-calendar-validation-and-rendering-ruling-2026-09-11.md) --
// only the folder-level RULE_BASED_CALENDARS reference attribute survives
// import, as unmodeled residue (drydocs_remediation/xml_io.py), never the
// calendar's own rule content. So this component takes a calendar DEFINITION
// as a prop rather than fetching one; it exists to prove the rendering
// approach and the year-boundary behavior, not to ship a page with nothing
// behind it.
//
// The one behavior the acceptance calls out by name: a year the calendar does
// not declare must read as a BOUNDARY, not as an empty month. Silently
// projecting past explicit year coverage is the one thing this component is
// not allowed to do, so the out-of-coverage branch is not a fallback -- it is
// the other half of the component.

import EmptyState from '../components/ui/EmptyState'
import { resolveRbcYear, type RuleBasedCalendarDef } from './rbcCalendar'

const WEEKDAY_HEADERS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function daysInGregorianMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate()
}

function firstWeekdayOfMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month - 1, 1)).getUTCDay()
}

export default function RbcCalendarSpike({
  calendar,
  year,
  month,
}: {
  calendar: RuleBasedCalendarDef
  year: number
  month: number
}) {
  const resolution = resolveRbcYear(calendar, year)

  if (resolution.status === 'out-of-coverage') {
    return (
      <div className="rounded-lg border border-edge bg-panel p-4" data-rbc-status="out-of-coverage">
        <p className="mb-2 font-mono text-xs uppercase tracking-wide text-faint">{calendar.name}</p>
        <EmptyState
          title={`${calendar.name} does not cover ${year}`}
          hint={`Declared years: ${resolution.declaredYears.join(', ')}. Control-M calendars are defined against explicit years -- this is not an empty result, it is a question the calendar was never asked.`}
        />
      </div>
    )
  }

  const matched = new Set(resolution.dates.filter((d) => d.startsWith(`${year}-${String(month).padStart(2, '0')}`)))
  const leading = firstWeekdayOfMonth(year, month)
  const cap = daysInGregorianMonth(year, month)
  const cells: (number | null)[] = [...Array(leading).fill(null), ...Array.from({ length: cap }, (_, i) => i + 1)]
  const monthName = new Date(Date.UTC(year, month - 1, 1)).toLocaleString('en-US', { month: 'long', timeZone: 'UTC' })

  return (
    <div className="rounded-lg border border-edge bg-panel p-4" data-rbc-status="resolved">
      <p className="mb-2 font-mono text-xs uppercase tracking-wide text-faint">{calendar.name}</p>
      <p className="mb-3 text-sm font-medium text-text">
        {monthName} {year}
      </p>
      <div className="grid grid-cols-7 gap-1 text-center">
        {WEEKDAY_HEADERS.map((label) => (
          <div key={label} className="text-[11px] uppercase tracking-wide text-faint">
            {label}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day === null) return <div key={`blank-${i}`} />
          const iso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
          const isMatch = matched.has(iso)
          return (
            <div
              key={iso}
              data-rbc-date={iso}
              data-rbc-match={isMatch}
              aria-label={isMatch ? `${iso}, matches ${calendar.name}` : iso}
              className={
                'flex h-8 items-center justify-center rounded-sm border font-mono text-xs tabular-nums ' +
                (isMatch ? 'border-blue-bright bg-panel-2 text-text' : 'border-transparent text-faint')
              }
            >
              {day}
            </div>
          )
        })}
      </div>
    </div>
  )
}
