import { describe, expect, it } from 'vitest'

import {
  DAY_MINUTES,
  SOURCE_ZONE,
  clockLabel,
  convertSpan,
  defaultTimeOf,
  isDefaultSeeded,
  nominalOffsetMinutes,
  offsetLabel,
  offsetMinutesAt,
  parseClock,
  runMinutes,
  segmentsOf,
  spanFor,
  wallClockToUtc,
} from './runtimeSpan'

// Z6. Everything the map claims about a clock is decided here, so this is where
// the claims are checked. Dates are chosen on purpose: 2026-01-15 is standard
// time in New York, 2026-07-15 is daylight time, and the two must not behave
// the same.

describe('parsing the shapes the loader normalizes to', () => {
  it('reads HH:MM, HH:MM:SS, HHMM and HHMMSS', () => {
    expect(parseClock('07:00')).toBe(420)
    expect(parseClock('23:59:30')).toBe(23 * 60 + 59)
    expect(parseClock('0700')).toBe(420)
    expect(parseClock('070015')).toBe(420)
    expect(parseClock('7:05')).toBe(425)
  })

  it('refuses anything else rather than guessing', () => {
    // patch_window.py's own rule: an unrecognised shape is a finding, never a
    // value. A parser that reached for a plausible reading here would put a
    // fabricated start time on a map.
    for (const bad of ['', '  ', '7', '25:00', '07:60', 'morning', '7pm', null, undefined]) {
      expect(parseClock(bad), `parsed ${String(bad)}`).toBeNull()
    }
  })

  it('rounds run seconds to whole minutes, never to zero', () => {
    expect(runMinutes(3600)).toBe(60)
    expect(runMinutes(20)).toBe(1) // a 20-second job still occupies clock
    expect(runMinutes(0)).toBe(1)
    expect(runMinutes(null)).toBeNull()
    expect(runMinutes('')).toBeNull()
    expect(runMinutes('not a number')).toBeNull()
    expect(runMinutes(-5)).toBeNull()
  })

  it('reads the E#### segment of a DC name, and tolerates its absence', () => {
    expect(defaultTimeOf('T032-E0700-DMA')).toBe(420)
    expect(defaultTimeOf('T021-E0800-ANY')).toBe(480)
    // A name with no time segment is a legitimate registration, not a failure:
    // the E#### reading is an internal convention the registry marks optional.
    expect(defaultTimeOf('P12')).toBeNull()
    expect(defaultTimeOf(null)).toBeNull()
  })
})

describe('which source a span comes from', () => {
  it('prefers the job-level observation over everything', () => {
    const s = spanFor({
      avg_start_time: '02:30',
      avg_run_time: 5400,
      window_start: '00:00',
      window_end: '23:00',
      dcDefaultMinute: 420,
    })
    expect(s.source).toBe('observed-job')
    expect(s.startMinute).toBe(150)
    expect(s.durationMinutes).toBe(90)
  })

  it('falls to the folder window, and reads a backwards one as a midnight crossing', () => {
    // The folder window is an EXTENT (min member start .. max member end), so
    // end < start means it wrapped. Treating it as an error would drop a real
    // overnight window; treating it as a negative duration would draw nothing.
    const s = spanFor({ window_start: '22:00', window_end: '01:30' })
    expect(s.source).toBe('folder-window')
    expect(s.startMinute).toBe(22 * 60)
    expect(s.durationMinutes).toBe(210)
  })

  it('falls to the DC default LAST, and labels it as a default', () => {
    const s = spanFor({ dcDefaultMinute: 420 })
    expect(s.source).toBe('dc-default')
    expect(isDefaultSeeded(s.source)).toBe(true)
    expect(s.said).toMatch(/seeded from the scheduling DC name/)
  })

  it('never lets a default outrank a measurement', () => {
    // The ordering is patch_window.py's and this is the assertion that stops it
    // drifting: a default that outranked an observation would put an invented
    // 07:00 on a job whose real start is in the graph.
    expect(spanFor({ avg_start_time: '03:00', avg_run_time: 60, dcDefaultMinute: 420 }).source).toBe(
      'observed-job',
    )
    expect(spanFor({ window_start: '03:00', window_end: '04:00', dcDefaultMinute: 420 }).source).toBe(
      'folder-window',
    )
  })

  it('reports nothing rather than inventing something', () => {
    const s = spanFor({})
    expect(s.source).toBe('none')
    expect(s.durationMinutes).toBe(0)
    expect(isDefaultSeeded(s.source)).toBe(false)
  })
})

describe('a span that crosses midnight is not truncated', () => {
  it('splits into one segment per day, keeping the whole duration', () => {
    const segs = segmentsOf(23 * 60, 180)
    expect(segs).toEqual([
      { from: 1380, to: 1440, dayOffset: 0 },
      { from: 0, to: 120, dayOffset: 1 },
    ])
    const drawn = segs.reduce((n, s) => n + (s.to - s.from), 0)
    expect(drawn).toBe(180) // the acceptance's clause, as arithmetic
  })

  it('handles a run longer than a whole day', () => {
    // 12:00 plus two days and two hours: half a day, a whole day, then the
    // tail. Three bars, and the arithmetic still adds up to the whole run.
    const total = 2 * DAY_MINUTES + 120
    const segs = segmentsOf(12 * 60, total)
    expect(segs).toHaveLength(3)
    expect(segs.reduce((n, s) => n + (s.to - s.from), 0)).toBe(total)
    expect(segs[segs.length - 1].dayOffset).toBe(2)
  })

  it('draws nothing for a span with no duration', () => {
    expect(segmentsOf(0, 0)).toEqual([])
  })
})

describe('zone conversion', () => {
  it('knows New York changes offset between January and July', () => {
    // The reason the source zone is read as an IANA zone and not a fixed UTC−5:
    // if these were equal, every summer window would be drawn an hour wrong.
    const jan = offsetMinutesAt(Date.UTC(2026, 0, 15, 12), SOURCE_ZONE)
    const jul = offsetMinutesAt(Date.UTC(2026, 6, 15, 12), SOURCE_ZONE)
    expect(jan).toBe(-300)
    expect(jul).toBe(-240)
  })

  it('resolves a wall-clock time to the instant it actually happens', () => {
    // 07:00 in New York on 2026-01-15 is 12:00 UTC; on 2026-07-15 it is 11:00.
    expect(wallClockToUtc(2026, 1, 15, 420, SOURCE_ZONE)).toBe(Date.UTC(2026, 0, 15, 12, 0))
    expect(wallClockToUtc(2026, 7, 15, 420, SOURCE_ZONE)).toBe(Date.UTC(2026, 6, 15, 11, 0))
  })

  it('converts a source span into the viewer’s zone', () => {
    const span = spanFor({ avg_start_time: '07:00', avg_run_time: 3600 })
    const utcView = convertSpan(span, { year: 2026, month: 1, day: 15 }, SOURCE_ZONE, 'UTC')
    expect(clockLabel(utcView.startMinute)).toBe('12:00')
    expect(utcView.offsetDeltaMinutes).toBe(300)
    expect(utcView.durationMinutes).toBe(60)
  })

  it('reports the day shift, so a bar is not read against the wrong date', () => {
    // 22:00 in New York is the NEXT morning in Tokyo. Without the shift the bar
    // reads as "this evening" to a Tokyo viewer, which is a day out.
    const span = spanFor({ avg_start_time: '22:00', avg_run_time: 1800 })
    const tokyo = convertSpan(span, { year: 2026, month: 1, day: 15 }, SOURCE_ZONE, 'Asia/Tokyo')
    expect(tokyo.dayShift).toBe(1)
    expect(clockLabel(tokyo.startMinute)).toBe('12:00')
  })

  it('handles a zone whose offset is not a whole hour', () => {
    const span = spanFor({ avg_start_time: '07:00', avg_run_time: 600 })
    const kolkata = convertSpan(span, { year: 2026, month: 1, day: 15 }, SOURCE_ZONE, 'Asia/Kolkata')
    expect(clockLabel(kolkata.startMinute)).toBe('17:30')
    expect(offsetLabel(kolkata.offsetDeltaMinutes)).toBe('+10:30')
  })

  it('shows a negative shift when the viewer is behind the source', () => {
    const span = spanFor({ avg_start_time: '01:00', avg_run_time: 600 })
    const la = convertSpan(span, { year: 2026, month: 1, day: 15 }, SOURCE_ZONE, 'America/Los_Angeles')
    expect(la.dayShift).toBe(-1)
    expect(clockLabel(la.startMinute)).toBe('22:00')
  })
})

describe('the nominal hour bands', () => {
  it('are solar meridians, and the labels say the arithmetic', () => {
    expect(nominalOffsetMinutes(0)).toBe(0) // Greenwich
    expect(nominalOffsetMinutes(-74)).toBe(-300) // New York, 5 bands west
    expect(nominalOffsetMinutes(139.7)).toBe(540) // Tokyo, 9 bands east
    expect(offsetLabel(-300)).toBe('−5:00')
    expect(offsetLabel(0)).toBe('+0:00')
  })

  it('disagrees with the political zone where the political zone is the odd one', () => {
    // Stated as a TEST rather than only in prose, because it is the caveat the
    // UI carries: Spain keeps Berlin's clock while sitting on Greenwich's
    // meridian. A band that claimed to be a time zone would be wrong here.
    expect(nominalOffsetMinutes(-3.7)).toBe(0) // Madrid, solar
    expect(offsetMinutesAt(Date.UTC(2026, 0, 15, 12), 'Europe/Madrid')).toBe(60) // political
  })
})
