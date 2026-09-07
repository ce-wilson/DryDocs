// Z6 — the runtime map's arithmetic, kept out of the render.
//
// THREE THINGS THIS FILE REFUSES TO DO, each one a way the map would state a
// fact it does not have:
//
//  1. It never presents a DEFAULT as an OBSERVED runtime. The acceptance says
//     the DC-name default time "may seed the span ONLY if labeled as a default",
//     so provenance is a field on the span and not a footnote — a caller cannot
//     obtain a span without also obtaining what it came from.
//  2. It never truncates a span that crosses midnight. A run from 23:00 to 02:00
//     is ONE run, and a bar clipped at the right edge of the day reads as a
//     three-hour job that ends at midnight. Spans are returned as SEGMENTS on
//     the clock, so a wrap is two bars of one span rather than one wrong bar.
//  3. It never hardcodes the viewer's zone. The browser's own zone comes from
//     Intl; the SOURCE zone is a declared constant with its provenance attached.
//
// THE SOURCE ZONE IS AN SME ASSERTION WITH AN OPEN CONFIRMATION ITEM, and the
// console says so rather than treating it as a fact.
// knowledge/standards/technology/data-center-naming-convention.md — authority
// `internal-standards` (precedence tier 2), trust_tier `internal / SME-asserted
// / mutable` — states "all times normalize to EST", and its own open item 4 is
// "Confirm E is always Eastern (SME stated all times are EST)". So:
//
//   * the zone is read as the IANA zone America/New_York, NOT a fixed UTC-5
//     offset, because a Control-M start time is a WALL CLOCK time at the data
//     center and a wall clock reads 07:00 in July as well as in January. The two
//     readings differ by an hour for eight months of the year, and an hour is
//     the difference between a window that contains a change and one that does
//     not;
//   * that reading is a DECISION, recorded here, and the UI names it.

/** The declared source zone for Control-M times, and where the claim comes from. */
export const SOURCE_ZONE = 'America/New_York'
export const SOURCE_ZONE_CLAIM =
  'Control-M times are read as wall-clock in America/New_York — the internal standard’s ' +
  '“all times normalize to EST”, whose own open item is “confirm E is always Eastern”. ' +
  'Read as the IANA zone, not a fixed UTC−5: a start time is a wall clock, so the offset ' +
  'moves with daylight saving.'

/** Where a span's minutes came from. Ordered as patch_window.py reads them. */
export type SpanSource =
  /** job-level avg_start_time + avg_run_time — the P4 supplement properties. */
  | 'observed-job'
  /** the folder's window_start/window_end rollup — an extent, never a sum. */
  | 'folder-window'
  /** the E#### segment of the scheduling DC name. A DEFAULT, never observed. */
  | 'dc-default'
  /** nothing placeable. Reported, never guessed. */
  | 'none'

export const SPAN_SOURCE_LABEL: Record<SpanSource, string> = {
  'observed-job': 'Observed (job avg start + avg run)',
  'folder-window': 'Folder window (extent of its members)',
  'dc-default': 'DEFAULT from the DC name — not an observed runtime',
  none: 'No timing data',
}

/** True for the one source that is not a measurement. The UI keys its warning
 *  on this rather than on the string, so a new default-ish source cannot be
 *  added without deciding which side of this line it is on. */
export function isDefaultSeeded(source: SpanSource): boolean {
  return source === 'dc-default'
}

export interface Span {
  /** Minutes after midnight in SOURCE_ZONE, 0..1439. */
  startMinute: number
  /** Duration in minutes. May exceed 1440 for a run longer than a day. */
  durationMinutes: number
  source: SpanSource
  /** What the row actually said, so a refusal is diagnosable without the graph. */
  said: string
}

export const DAY_MINUTES = 24 * 60

/** Parse the time shapes the P4 supplement loader normalizes to (patch_window.py's
 *  "assumed time shapes"): ``HH:MM``, ``HH:MM:SS``, ``HHMM``, ``HHMMSS``.
 *  Anything else is `null` — never a guess, which is that loader's own rule. */
export function parseClock(raw: string | null | undefined): number | null {
  if (raw === null || raw === undefined) return null
  const text = String(raw).trim()
  if (!text) return null
  let hh: number
  let mm: number
  const colon = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(text)
  if (colon) {
    hh = Number(colon[1])
    mm = Number(colon[2])
  } else if (/^\d{4}$/.test(text) || /^\d{6}$/.test(text)) {
    hh = Number(text.slice(0, 2))
    mm = Number(text.slice(2, 4))
  } else {
    return null
  }
  if (hh > 23 || mm > 59) return null
  return hh * 60 + mm
}

/** Seconds to whole minutes, at least one — patch_window.py's `_run_minutes`.
 *  A job that ran for 20 seconds still occupies clock, and rounding it to zero
 *  would make it disappear from a picture of what is running. */
export function runMinutes(seconds: string | number | null | undefined): number | null {
  if (seconds === null || seconds === undefined || seconds === '') return null
  const n = Number(seconds)
  if (!Number.isFinite(n) || n < 0) return null
  return Math.max(1, Math.round(n / 60))
}

/** The `E####` segment of a long-form DC name (`T032-E0700-DMA` -> 07:00).
 *  Returns null when the name carries no time segment, which is a legitimate
 *  registration and not a failure (the registry's own rule). */
export function defaultTimeOf(longName: string | null | undefined): number | null {
  if (!longName) return null
  const m = /(?:^|-)E(\d{4})(?:-|$)/.exec(longName)
  return m ? parseClock(m[1]) : null
}

export interface SpanInputs {
  avg_start_time?: string | null
  avg_run_time?: string | number | null
  window_start?: string | null
  window_end?: string | null
  /** The DC-name default, already resolved through the short -> long registry
   *  pairing (which is a declared fact and not derivable — LOAD2 (c)). */
  dcDefaultMinute?: number | null
  /** How long a default-seeded span is drawn for. Explicit because there is no
   *  observed duration behind it; the caller states the assumption. */
  dcDefaultDurationMinutes?: number
}

/** Pick the span, in the order patch_window.py already reads the sources.
 *
 * The ORDER is not this file's invention and must not drift from it: job-level
 * timing first, folder rollup second, and only then the DC default. Reversing
 * any pair would let a default silently outrank a measurement. */
export function spanFor(row: SpanInputs): Span {
  const start = parseClock(row.avg_start_time)
  const run = runMinutes(row.avg_run_time)
  if (start !== null && run !== null) {
    return {
      startMinute: start,
      durationMinutes: run,
      source: 'observed-job',
      said: `avg_start_time=${row.avg_start_time} avg_run_time=${row.avg_run_time}`,
    }
  }
  const wStart = parseClock(row.window_start)
  const wEnd = parseClock(row.window_end)
  if (wStart !== null && wEnd !== null) {
    // The folder window is an EXTENT (min member start .. max member end), so a
    // window that ends "before" it starts crossed midnight rather than being
    // wrong. Adding a day is the only reading that keeps it one window.
    const duration = wEnd >= wStart ? wEnd - wStart : DAY_MINUTES - wStart + wEnd
    return {
      startMinute: wStart,
      durationMinutes: Math.max(1, duration),
      source: 'folder-window',
      said: `window_start=${row.window_start} window_end=${row.window_end}`,
    }
  }
  if (row.dcDefaultMinute !== null && row.dcDefaultMinute !== undefined) {
    return {
      startMinute: row.dcDefaultMinute,
      durationMinutes: Math.max(1, row.dcDefaultDurationMinutes ?? 60),
      source: 'dc-default',
      said: 'no job or folder timing — seeded from the scheduling DC name',
    }
  }
  return {
    startMinute: 0,
    durationMinutes: 0,
    source: 'none',
    said: 'no avg_start_time/avg_run_time, no folder window, no DC default time',
  }
}

export interface Segment {
  /** Minutes after midnight on the clock this segment is drawn against. */
  from: number
  to: number
  /** 0 for the day the span starts on, 1 for the next, and so on. */
  dayOffset: number
}

/** Cut a span into per-day segments so a midnight crossing renders whole.
 *
 * A 23:00 + 180min run comes back as [23:00..24:00 on day 0, 00:00..02:00 on
 * day 1] — two bars, one span. Clipping it at 24:00 instead would draw a
 * one-hour job, which is the truncation the acceptance forbids by name. */
export function segmentsOf(startMinute: number, durationMinutes: number): Segment[] {
  if (durationMinutes <= 0) return []
  const out: Segment[] = []
  let cursor = startMinute
  let remaining = durationMinutes
  let day = 0
  while (remaining > 0) {
    const room = DAY_MINUTES - cursor
    const take = Math.min(room, remaining)
    out.push({ from: cursor, to: cursor + take, dayOffset: day })
    remaining -= take
    cursor = 0
    day += 1
  }
  return out
}

// ── zone conversion ─────────────────────────────────────────────────────────
//
// No date library: Intl already knows every zone the browser does, and adding a
// dependency to do arithmetic the platform does is the kind of thing the
// registry discipline makes non-free.

/** A zone's UTC offset in minutes at an instant. */
export function offsetMinutesAt(utcMs: number, timeZone: string): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(new Date(utcMs))
  const at = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? '0')
  // `hour: '2-digit'` with hour12:false yields 24 for midnight in some engines.
  const hour = at('hour') % 24
  const asUtc = Date.UTC(at('year'), at('month') - 1, at('day'), hour, at('minute'), at('second'))
  return (asUtc - utcMs) / 60000
}

/** The instant at which a wall-clock time in `timeZone` occurs, on `date`.
 *
 * Two passes, which is the standard correction and not a superstition: the first
 * offset is looked up at the WRONG instant (the guess), so a wall time within an
 * hour of a DST boundary would resolve with the offset from the other side of
 * it. */
export function wallClockToUtc(
  year: number,
  month: number,
  day: number,
  minuteOfDay: number,
  timeZone: string,
): number {
  const guess = Date.UTC(year, month - 1, day, 0, minuteOfDay)
  const first = guess - offsetMinutesAt(guess, timeZone) * 60000
  return guess - offsetMinutesAt(first, timeZone) * 60000
}

/** The viewer's own zone. Read from the browser, never hardcoded — and named
 *  rather than assumed present, because a locked-down engine can report a bare
 *  UTC and the page should say what it used. */
export function viewerZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
}

export interface ConvertedSpan {
  /** Minutes after midnight in the VIEWER's zone. */
  startMinute: number
  durationMinutes: number
  /** Whole days the viewer's clock is ahead (+) or behind (-) the source's for
   *  this instant — the "yesterday/tomorrow" a reader needs to not misread a
   *  bar that starts at 21:00 their time for the same calendar day. */
  dayShift: number
  /** The offset difference in minutes, for the label. */
  offsetDeltaMinutes: number
}

/** Convert a source-zone wall-clock span to the viewer's zone on a given date.
 *
 * `on` is the calendar date the span is read against, in the SOURCE zone. It has
 * to be a real date because the offset between two zones is not a constant: the
 * northern and southern hemispheres change clocks in opposite months, so the gap
 * between New York and Sydney is 14 hours or 16 depending on the day. */
export function convertSpan(
  span: Span,
  on: { year: number; month: number; day: number },
  sourceZone: string = SOURCE_ZONE,
  targetZone: string = viewerZone(),
): ConvertedSpan {
  const utc = wallClockToUtc(on.year, on.month, on.day, span.startMinute, sourceZone)
  const targetOffset = offsetMinutesAt(utc, targetZone)
  const sourceOffset = offsetMinutesAt(utc, sourceZone)
  const rawMinute = span.startMinute + (targetOffset - sourceOffset)
  const dayShift = Math.floor(rawMinute / DAY_MINUTES)
  return {
    startMinute: ((rawMinute % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES,
    durationMinutes: span.durationMinutes,
    dayShift,
    offsetDeltaMinutes: targetOffset - sourceOffset,
  }
}

/** `07:30` from minutes after midnight. */
export function clockLabel(minuteOfDay: number): string {
  const m = ((minuteOfDay % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
}

/** `+5:30` / `−4:00` / `+0:00` — an offset a reader can check against a clock. */
export function offsetLabel(minutes: number): string {
  const sign = minutes < 0 ? '−' : '+'
  const abs = Math.abs(minutes)
  return `${sign}${Math.floor(abs / 60)}:${String(abs % 60).padStart(2, '0')}`
}

// ── the map's hour bands ────────────────────────────────────────────────────

/** A site's NOMINAL offset, from its longitude.
 *
 * SOLAR, NOT POLITICAL, and the UI says so. Real zones follow borders: mainland
 * China is one zone across sixty degrees, India runs on a half-hour, and Spain
 * keeps Berlin's clock. The gazetteer behind the Z5 map holds city coordinates
 * and no zone id, so a lookup would need a dataset we do not have — and a
 * plausible-looking political zone we invented would be worse than an
 * approximation that announces itself. */
export function nominalOffsetMinutes(longitudeDegrees: number): number {
  const minutes = Math.round(longitudeDegrees / 15) * 60
  // A longitude just west of Greenwich rounds to -0, which is a real value in
  // JS and compares unequal to 0 under Object.is. Nothing downstream should
  // have to know that.
  return minutes === 0 ? 0 : minutes
}

export const NOMINAL_BAND_CAVEAT =
  'Hour bands are nominal solar meridians (15° per hour), not political time zones — ' +
  'the gazetteer carries coordinates, not zone ids. Use them to read “roughly what ' +
  'time is it there”, never as an authority on a country’s clock.'
