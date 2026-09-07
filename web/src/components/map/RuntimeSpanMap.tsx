import { useEffect, useMemo, useState } from 'react'
import type { GraphAccess } from '../../lib/graph'
import { COUNTRY_SHAPES, MAP_HEIGHT, MAP_WIDTH } from '../../generated/world-map'
import { viewBox, WORLD_BOX } from './projection'
import { resolveRows, type LocationRow, type PlacedSite } from './resolve'
import { validateRows, type RowShape } from '../../data/rowShape'
import type { DataCenterRow } from '../../lib/dataCentersApi'
import { declaredDefaultByCode, longNameByCode } from '../../lib/dataCentersApi'
import {
  DAY_MINUTES,
  NOMINAL_BAND_CAVEAT,
  SOURCE_ZONE,
  SOURCE_ZONE_CLAIM,
  SPAN_SOURCE_LABEL,
  clockLabel,
  convertSpan,
  defaultTimeOf,
  isDefaultSeeded,
  nominalOffsetMinutes,
  offsetLabel,
  parseClock,
  segmentsOf,
  spanFor,
  viewerZone,
  type Span,
} from '../../lib/runtimeSpan'

// Z6 — the global time-zone runtime map.
//
// REUSES THE Z5 MAP CORE and adds one axis to it: the same world geometry, the
// same equirectangular projection, the same gazetteer resolve. What is new is
// that a span of CLOCK is drawn across it, which is the one thing a dot map
// cannot say — "this runs at 07:00 in New York" and "that is 21:00 in Sydney"
// are the same fact and a reader should not have to do the arithmetic.
//
// THE TWO DCs STAY APART, on the screen as well as on the wire. `scheduling_dc`
// (the Control-M server name, the T032-E0700-DMA grammar) is what SEEDS a
// default time; `data_center` / city / country is where the host physically is
// and is what places a pin. They are labelled differently, they come from
// different columns, and nothing here joins them — gate server-location-ontology
// B4, which the Z2 acceptance requires by name.
//
// THE BANDS ARE SOLAR, NOT POLITICAL, and the footer says so. See
// NOMINAL_BAND_CAVEAT: the gazetteer holds coordinates and no zone ids, so a
// political zone would be invented. The VIEWER's conversion is not an
// approximation — that one goes through Intl with the browser's real zone.

const SPEC_ID = 'map.runtime-spans.v1'

interface SpanRow extends LocationRow {
  folder: string | null
  scheduling_dc: string | null
  avg_start_time: string | null
  avg_run_time: string | null
  start_next_day: string | null
  window_start: string | null
  window_end: string | null
}

const SPAN_COLUMNS: RowShape<SpanRow> = [
  'origin',
  'origin_kind',
  'folder',
  'scheduling_dc',
  'avg_start_time',
  'avg_run_time',
  'start_next_day',
  'window_start',
  'window_end',
  'data_center',
  'city',
  'state',
  'country',
  'location_grain',
]

/** How long a default-seeded bar is drawn for, stated once.
 *
 *  There is NO observed duration behind a DC default — the name carries a start
 *  and nothing else — so the bar's length is an assumption and it is written
 *  here rather than buried in a call. One hour, because it is the shortest span
 *  that reads as a span; the label says the length means nothing. */
const DEFAULT_SEED_MINUTES = 60

/** The two grains the acceptance names. */
type Grain = 'job' | 'folder'

type Load =
  | { state: 'loading' }
  | { state: 'error'; message: string }
  | { state: 'ready'; rows: SpanRow[] }

/** The date the span is read against, in the SOURCE zone.
 *
 *  A date is REQUIRED and cannot be skipped: the gap between two zones is not a
 *  constant — the hemispheres change clocks in opposite months — so "convert
 *  07:00 New York to Sydney" has no answer without one. Today, in the viewer's
 *  own calendar, is the only date that needs no explaining. */
function todayParts(now: Date): { year: number; month: number; day: number } {
  return { year: now.getFullYear(), month: now.getMonth() + 1, day: now.getDate() }
}

/** A site's longitude, inverted from the projection it was placed with.
 *  Exact rather than approximate: `project` is two lines of arithmetic and this
 *  is its inverse, which is why the projection is equirectangular at all. */
function longitudeOf(site: PlacedSite): number {
  return (site.point.x / MAP_WIDTH) * 360 - 180
}

function spanOf(row: SpanRow, dcDefault: number | null): Span {
  return spanFor({
    avg_start_time: row.avg_start_time,
    avg_run_time: row.avg_run_time,
    window_start: row.window_start,
    window_end: row.window_end,
    dcDefaultMinute: dcDefault,
    dcDefaultDurationMinutes: DEFAULT_SEED_MINUTES,
  })
}

export interface RuntimeSpanMapProps {
  access: GraphAccess
  /** The spelling registry, already fetched. Passed in rather than fetched here
   *  so the component is testable without a server and so the page can say
   *  which venue the rows came from (J18) beside its own heading. */
  dataCenters: readonly DataCenterRow[]
  /** Injectable clock — a map whose picture changed with the wall time would be
   *  untestable, and "today" is a real input to the conversion. */
  now?: Date
  /** Injectable viewer zone, defaulting to the browser's own.
   *
   *  A PROP because the default is `Intl`'s answer, which is the MACHINE's zone:
   *  a test that asserted on it would pass on the laptop that wrote it and fail
   *  in CI, and the failure would look like a bug in the conversion rather than
   *  in the test. The production path never passes it. */
  viewerTimeZone?: string
  className?: string
}

export default function RuntimeSpanMap({
  access,
  dataCenters,
  now = new Date(),
  viewerTimeZone,
  className,
}: RuntimeSpanMapProps) {
  const [load, setLoad] = useState<Load>({ state: 'loading' })
  const [selected, setSelected] = useState<string | null>(null)
  const [mode, setMode] = useState<Grain>('job')

  useEffect(() => {
    let live = true
    setLoad({ state: 'loading' })
    access
      .runSpec(SPEC_ID, {})
      .then((res) => {
        if (!live) return
        const checked = validateRows<SpanRow>(res, SPAN_COLUMNS)
        setLoad(
          checked.ok
            ? { state: 'ready', rows: checked.rows }
            : { state: 'error', message: checked.message },
        )
      })
      .catch((err: unknown) => {
        if (!live) return
        // Loud, never a silent empty map — Z5's rule, and the reason is the
        // same: an empty map and a failed query look identical to a reader.
        setLoad({ state: 'error', message: err instanceof Error ? err.message : String(err) })
      })
    return () => {
      live = false
    }
  }, [access])

  // Memoized because the fallback is a fresh literal: an unmemoized `[]` makes
  // every derived useMemo below re-run on every render, which the hook linter
  // catches and which would quietly re-resolve the whole gazetteer.
  const rows = useMemo(() => (load.state === 'ready' ? load.rows : []), [load])

  const longByCode = useMemo(() => longNameByCode(dataCenters), [dataCenters])
  const declaredByCode = useMemo(() => declaredDefaultByCode(dataCenters), [dataCenters])

  /** The DC default for a row's SCHEDULING data center, declaration first. */
  function dcDefaultFor(row: SpanRow): number | null {
    const code = row.scheduling_dc
    if (!code) return null
    const declared = declaredByCode.get(code)
    if (declared) return parseClock(declared)
    return defaultTimeOf(longByCode.get(code) ?? null)
  }

  // The acceptance names BOTH grains — "for a selected folder or job" — and they
  // are different questions rather than a filter of one another. A job's span is
  // its own average run; a FOLDER's is the window_start/window_end rollup, which
  // the P4 contract defines as min member start .. max member end. An EXTENT,
  // never a sum, and never one member's runtime standing in for the folder's.
  const folders = useMemo(
    () => [...new Set(rows.map((r) => r.folder).filter((f): f is string => Boolean(f)))].sort(),
    [rows],
  )
  const options = mode === 'job' ? rows.map((r) => r.origin) : folders

  const selectedRows = useMemo(
    () =>
      selected === null
        ? []
        : rows.filter((r) => (mode === 'job' ? r.origin === selected : r.folder === selected)),
    [rows, mode, selected],
  )
  const head = selectedRows[0] ?? null

  const span = head
    ? mode === 'job'
      ? spanOf(head, dcDefaultFor(head))
      : // Folder grain: deliberately WITHOUT the job columns. Passing a member's
        // avg_start_time here would answer "when does one job in this folder
        // run" under a label that says "when does this folder run".
        spanFor({
          window_start: head.window_start,
          window_end: head.window_end,
          dcDefaultMinute: dcDefaultFor(head),
          dcDefaultDurationMinutes: DEFAULT_SEED_MINUTES,
        })
    : null

  // Sites for the SELECTION only: this map answers "where does this run reach",
  // not "where is everything". A folder's sites are the union of its jobs'.
  const resolved = useMemo(() => resolveRows(selectedRows), [selectedRows])

  const viewer = viewerTimeZone ?? viewerZone()
  const on = todayParts(now)
  const converted = span && span.source !== 'none' ? convertSpan(span, on, SOURCE_ZONE, viewer) : null
  const segments = converted ? segmentsOf(converted.startMinute, converted.durationMinutes) : []

  // The 24 nominal bands, each labelled with the local clock at the span's start.
  const bands = useMemo(() => {
    const out: { offsetMinutes: number; x: number; width: number }[] = []
    for (let i = 0; i < 24; i += 1) {
      const lon = -180 + i * 15
      out.push({
        offsetMinutes: nominalOffsetMinutes(lon + 7.5),
        x: (i / 24) * MAP_WIDTH,
        width: MAP_WIDTH / 24,
      })
    }
    return out
  }, [])

  // A JOB-grain count, said as one: it is the number of rows the map could not
  // draw at job grain, and it does not become a folder count by switching the
  // dropdown.
  const timingless = rows.filter((r) => spanOf(r, dcDefaultFor(r)).source === 'none').length

  return (
    <section className={className} aria-label="Runtime span map">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-[13px]">
          <span style={{ color: 'var(--muted)' }}>Grain</span>
          <select
            className="rounded-md border px-2 py-1 text-[13px]"
            style={{ borderColor: 'var(--edge)', background: 'var(--panel)', color: 'var(--text)' }}
            value={mode}
            aria-label="Grain"
            onChange={(e) => {
              setMode(e.target.value as Grain)
              setSelected(null)
            }}
          >
            <option value="job">Job</option>
            <option value="folder">Folder</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-[13px]">
          <span style={{ color: 'var(--muted)' }}>{mode === 'job' ? 'Job' : 'Folder'}</span>
          <select
            className="max-w-80 rounded-md border px-2 py-1 text-[13px]"
            style={{ borderColor: 'var(--edge)', background: 'var(--panel)', color: 'var(--text)' }}
            value={selected ?? ''}
            aria-label={mode === 'job' ? 'Job' : 'Folder'}
            onChange={(e) => setSelected(e.target.value || null)}
          >
            <option value="">— select a {mode} —</option>
            {options.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <span className="text-[13px]" style={{ color: 'var(--muted)' }}>
          Your zone: <span style={{ color: 'var(--text)' }}>{viewer}</span>
        </span>
      </div>

      {load.state === 'loading' && (
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Loading runtime spans…
        </p>
      )}
      {load.state === 'error' && (
        <p className="text-xs" style={{ color: 'var(--status-fail-soft)' }}>
          {load.message}
        </p>
      )}

      {span && (
        <div
          className="mb-3 rounded-lg border p-2 text-[13px]"
          style={{ borderColor: 'var(--edge)', background: 'var(--panel)' }}
        >
          {span.source === 'none' ? (
            <p style={{ color: 'var(--yellow)' }}>
              No runtime to draw: {span.said}. Reported rather than seeded — an invented span is a
              worse answer than none.
            </p>
          ) : (
            <>
              <p>
                <span style={{ color: 'var(--muted)' }}>Source zone ({SOURCE_ZONE}):</span>{' '}
                {clockLabel(span.startMinute)} – {clockLabel(span.startMinute + span.durationMinutes)}{' '}
                ({span.durationMinutes} min)
              </p>
              <p>
                <span style={{ color: 'var(--muted)' }}>Your clock ({viewer}):</span>{' '}
                {clockLabel(converted!.startMinute)} –{' '}
                {clockLabel(converted!.startMinute + converted!.durationMinutes)}
                {converted!.dayShift !== 0 && (
                  <span style={{ color: 'var(--yellow)' }}>
                    {' '}
                    ({converted!.dayShift > 0 ? '+' : ''}
                    {converted!.dayShift} day)
                  </span>
                )}{' '}
                <span style={{ color: 'var(--muted)' }}>
                  offset {offsetLabel(converted!.offsetDeltaMinutes)}
                </span>
              </p>
              <p
                style={{
                  color: isDefaultSeeded(span.source) ? 'var(--yellow)' : 'var(--muted)',
                }}
              >
                {SPAN_SOURCE_LABEL[span.source]}
                {isDefaultSeeded(span.source) && (
                  <>
                    {' '}
                    — the DC name carries a start and no duration, so the {DEFAULT_SEED_MINUTES}-minute
                    length is drawn to make the start visible and means nothing.
                  </>
                )}
              </p>
              {mode === 'job' && head?.start_next_day && (
                <p style={{ color: 'var(--muted)' }}>
                  start_next_day = {head.start_next_day} (carried from the graph, not applied here —
                  the ordering rule it encodes is patch_window.py&rsquo;s)
                </p>
              )}
            </>
          )}
        </div>
      )}

      {/* ---- the two data centers, side by side and never joined ----
           On the screen as well as on the wire (gate server-location-ontology
           B4). Naming only one of them would be the conflation by omission:
           a reader who sees "DEFAULT from the DC name" and one data center
           reasonably concludes that is the data center the name came from. */}
      {head && (
        <div className="mb-3 grid gap-2 md:grid-cols-2">
          <div
            className="rounded-lg border p-2 text-[13px]"
            style={{ borderColor: 'var(--edge)', background: 'var(--panel)' }}
          >
            <p style={{ color: 'var(--muted)' }}>Scheduling DC (Control-M)</p>
            <p>
              {head.scheduling_dc ?? <span style={{ color: 'var(--muted)' }}>not recorded</span>}
              {head.scheduling_dc && longByCode.get(head.scheduling_dc) && (
                <span style={{ color: 'var(--muted)' }}>
                  {' '}
                  · {longByCode.get(head.scheduling_dc)}
                </span>
              )}
            </p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              Where the E#### default time comes from. A scheduling name, not a place.
            </p>
          </div>
          <div
            className="rounded-lg border p-2 text-[13px]"
            style={{ borderColor: 'var(--edge)', background: 'var(--panel)' }}
          >
            <p style={{ color: 'var(--muted)' }}>Physical data center</p>
            <p>
              {head.data_center ?? <span style={{ color: 'var(--muted)' }}>host never resolved</span>}
              {head.city && (
                <span style={{ color: 'var(--muted)' }}>
                  {' '}
                  · {head.city}
                  {head.state ? `, ${head.state}` : ''}
                </span>
              )}
            </p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              Where the host actually is. Never joined to the name above by name.
            </p>
          </div>
        </div>
      )}

      {/* ---- the clock rail: one row of 24 bands, the span drawn across it ---- */}
      {converted && (
        <div
          className="mb-3 overflow-hidden rounded-lg border"
          style={{ borderColor: 'var(--edge)', background: 'var(--bg2)' }}
        >
          <svg viewBox="0 0 1440 60" className="block h-auto w-full" role="img" aria-label="Runtime span on the viewer's clock">
            {Array.from({ length: 24 }, (_, h) => (
              <g key={h}>
                <rect
                  x={h * 60}
                  y={0}
                  width={60}
                  height={40}
                  fill={h < 6 || h >= 22 ? 'color-mix(in srgb, var(--muted) 18%, var(--panel))' : 'var(--panel)'}
                  stroke="var(--edge-soft)"
                  strokeWidth={0.5}
                />
                <text x={h * 60 + 30} y={54} textAnchor="middle" fontSize={10} fill="var(--muted)">
                  {String(h).padStart(2, '0')}
                </text>
              </g>
            ))}
            {segments.map((s, i) => (
              <rect
                key={`${s.dayOffset}-${s.from}`}
                x={s.from}
                y={8 + s.dayOffset * 10}
                width={Math.max(2, s.to - s.from)}
                height={8}
                rx={2}
                fill={
                  isDefaultSeeded(span!.source)
                    ? 'color-mix(in srgb, var(--yellow) 70%, transparent)'
                    : 'color-mix(in srgb, var(--teal) 70%, transparent)'
                }
                stroke={isDefaultSeeded(span!.source) ? 'var(--yellow)' : 'var(--teal)'}
                strokeWidth={0.8}
                data-segment={i}
              >
                <title>
                  {`${clockLabel(s.from)}–${clockLabel(s.to % DAY_MINUTES || DAY_MINUTES)}` +
                    (s.dayOffset ? ` (+${s.dayOffset} day)` : '')}
                </title>
              </rect>
            ))}
          </svg>
        </div>
      )}

      {/* ---- the world, with the nominal bands and the run's own sites ---- */}
      <div
        className="overflow-hidden rounded-lg border"
        style={{ borderColor: 'var(--edge)', background: 'var(--bg2)' }}
      >
        <svg
          viewBox={viewBox(WORLD_BOX)}
          className="block h-auto w-full"
          role="img"
          aria-label="World time-zone map"
          strokeLinejoin="round"
        >
          {bands.map((b) => (
            <rect
              key={b.offsetMinutes + b.x}
              x={b.x}
              y={0}
              width={b.width}
              height={MAP_HEIGHT}
              fill={
                Math.round(b.offsetMinutes / 60) % 2 === 0
                  ? 'color-mix(in srgb, var(--blue) 5%, transparent)'
                  : 'transparent'
              }
            />
          ))}
          {COUNTRY_SHAPES.map((c) => (
            <path key={c.id} d={c.d} fill="var(--panel)" stroke="var(--edge-soft)" strokeWidth={0.4}>
              <title>{c.name}</title>
            </path>
          ))}
          {resolved.sites.map((site) => {
            const bandOffset = nominalOffsetMinutes(longitudeOf(site))
            const local = converted
              ? clockLabel(span!.startMinute + (bandOffset - offsetOfSourceAt(span!, on)))
              : null
            return (
              <g key={site.key}>
                <circle
                  cx={site.point.x}
                  cy={site.point.y}
                  r={4}
                  fill="color-mix(in srgb, var(--teal) 70%, transparent)"
                  stroke="var(--teal)"
                  strokeWidth={1}
                />
                <title>
                  {`${site.cityName}${site.state ? `, ${site.state}` : ''} — nominal ${offsetLabel(bandOffset)}` +
                    (local ? ` · run starts ~${local} there` : '') +
                    (site.synthetic ? ' · synthetic fixture' : '')}
                </title>
              </g>
            )
          })}
        </svg>
      </div>

      <p className="mt-2 text-xs/[1.5]" style={{ color: 'var(--muted)' }}>
        {NOMINAL_BAND_CAVEAT}
      </p>
      <p className="mt-1 text-xs/[1.5]" style={{ color: 'var(--muted)' }}>
        {SOURCE_ZONE_CLAIM}
      </p>
      {load.state === 'ready' && (
        <p className="mt-1 text-xs/[1.5]" style={{ color: timingless ? 'var(--yellow)' : 'var(--muted)' }}>
          {rows.length} job(s) returned; {timingless} with no timing data at all. Shown as a count
          because a job the map cannot draw is a real gap, not an empty selection.
        </p>
      )}
    </section>
  )
}

/** The source zone's own offset on the read date — the reference the nominal
 *  band arithmetic is relative to. Kept as a function beside its one caller so
 *  the "nominal minus source" subtraction is not a bare number in the JSX. */
function offsetOfSourceAt(span: Span, on: { year: number; month: number; day: number }): number {
  const utcView = convertSpan(span, on, SOURCE_ZONE, 'UTC')
  // convertSpan to UTC gives (UTC - source); the nominal bands are also stated
  // against UTC, so subtracting this puts both on one axis.
  return -utcView.offsetDeltaMinutes
}
