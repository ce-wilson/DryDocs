// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import RuntimeSpanMap from './RuntimeSpanMap'
import type { GraphAccess, RequestOptions, SpecResult } from '../../lib/graph'
import type { DataCenterRow } from '../../lib/dataCentersApi'

// Z6. The arithmetic is pinned in lib/runtimeSpan.test.ts; what is asserted here
// is what the SURFACE says — that a default is labelled as a default, that a job
// with no timing is reported rather than drawn, that the two DCs stay apart, and
// that a midnight crossing arrives as two bars of one span.
//
// The date AND the viewer zone are fixed (2026-01-15, standard time in New York;
// the viewer on UTC) so the picture does not change with the machine. Both are
// props for exactly that reason: `viewerZone()` reads Intl, which answers with
// whatever zone the runner is set to — this laptop is America/Chicago and CI is
// not, and a test that asserted on that would fail somewhere else and look like
// a bug in the conversion.

afterEach(cleanup)

const JAN_15 = new Date(2026, 0, 15, 9, 0, 0)

const COLUMNS = [
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
].map((name) => ({ name, type: 'string', label: name }))

function row(over: Partial<Record<string, unknown>> = {}): Record<string, unknown> {
  return {
    origin: 'JOB_A',
    origin_kind: 'job',
    folder: 'FOLDER_A',
    scheduling_dc: 'P32',
    avg_start_time: null,
    avg_run_time: null,
    start_next_day: null,
    window_start: null,
    window_end: null,
    data_center: 'DC-EAST',
    city: 'New York',
    state: 'NY',
    country: 'United States',
    location_grain: 'city',
    ...over,
  }
}

function result(rows: Record<string, unknown>[]): SpecResult {
  return {
    spec_id: 'map.runtime-spans.v1',
    database: 'drydocs',
    classification: 'internal',
    columns: COLUMNS,
    cypher: 'MATCH ...',
    params: {},
    watermarked: false,
    truncated: false,
    ephemeral: false,
    keys: COLUMNS.map((c) => c.name),
    rows,
  }
}

function access(rows: Record<string, unknown>[], fail?: string): GraphAccess {
  return {
    kind: 'api',
    runSpec: (_id: string, _p?: Record<string, unknown>, _o?: RequestOptions) =>
      fail ? Promise.reject(new Error(fail)) : Promise.resolve(result(rows)),
    runRead: () => Promise.reject(new Error('unused')),
    runNamed: () => Promise.reject(new Error('unused')),
    exportSpec: () => Promise.reject(new Error('unused')),
  } as unknown as GraphAccess
}

/** The registry sample's shape: a short code paired to a long name that carries
 *  an E#### segment, plus one that carries none. */
const REGISTRY: DataCenterRow[] = [
  {
    code: 'P32',
    name: 'T032-E0700-DMA',
    default_time: '07:00',
    suffix: 'DMA',
    sample: true,
    note: '',
  },
  { code: 'P99', name: 'T099-PLAIN', default_time: '', suffix: '', sample: true, note: '' },
]

async function pick(rows: Record<string, unknown>[], origin: string) {
  render(
    <RuntimeSpanMap
      access={access(rows)}
      dataCenters={REGISTRY}
      now={JAN_15}
      viewerTimeZone="UTC"
    />,
  )
  const select = await screen.findByRole('combobox')
  fireEvent.change(select, { target: { value: origin } })
  return select
}

describe('the observed case', () => {
  it('shows the source-zone span and the viewer’s, and calls it observed', async () => {
    await pick([row({ avg_start_time: '07:00', avg_run_time: '3600' })], 'JOB_A')
    const text = document.body.textContent ?? ''
    expect(text).toContain('07:00 – 08:00')
    // 07:00 New York on a January date is 12:00 UTC — the viewer's zone, pinned.
    expect(text).toContain('12:00 – 13:00')
    expect(text).toMatch(/Observed \(job avg start \+ avg run\)/)
    expect(text).not.toMatch(/DEFAULT from the DC name/)
  })
})

describe('the default-seeded case', () => {
  it('labels it a DEFAULT and says the length means nothing', async () => {
    // The acceptance's clause, as a rendered string: a DC default "may seed the
    // span ONLY if labeled as a default, never presented as an observed
    // runtime". A yellow bar with no sentence would fail it.
    await pick([row()], 'JOB_A')
    const text = document.body.textContent ?? ''
    expect(text).toMatch(/DEFAULT from the DC name — not an observed runtime/)
    expect(text).toMatch(/means nothing/)
    expect(text).toContain('07:00 – 08:00') // the registry's declared default
  })

  it('takes the registry’s DECLARED default over re-parsing the name', async () => {
    // A declaration beats a derivation: the file may record a default for a name
    // whose segment we would not parse.
    const declared: DataCenterRow[] = [
      { code: 'P32', name: 'no-parsable-segment', default_time: '05:30', suffix: '', sample: true, note: '' },
    ]
    render(
      <RuntimeSpanMap
        access={access([row()])}
        dataCenters={declared}
        now={JAN_15}
        viewerTimeZone="UTC"
      />,
    )
    fireEvent.change(await screen.findByRole('combobox'), { target: { value: 'JOB_A' } })
    expect(document.body.textContent).toContain('05:30 – 06:30')
  })

  it('reports a job with no timing rather than drawing one', async () => {
    await pick([row({ scheduling_dc: 'P99' })], 'JOB_A')
    const text = document.body.textContent ?? ''
    expect(text).toMatch(/No runtime to draw/)
    expect(text).toMatch(/an invented span is a worse answer than none/)
    expect(document.querySelectorAll('[data-segment]')).toHaveLength(0)
  })
})

describe('a span that crosses midnight', () => {
  it('draws as two bars of one span, never clipped', async () => {
    // 17:00 New York + 6h is 22:00–04:00 UTC. The VIEWER's clock is the one the
    // bars are drawn against, so the wrap has to happen THERE — a source-zone
    // wrap that lands inside a single viewer day would draw one bar, correctly.
    await pick([row({ avg_start_time: '17:00', avg_run_time: '21600' })], 'JOB_A')
    const bars = document.querySelectorAll('[data-segment]')
    expect(bars).toHaveLength(2)
    const widths = [...bars].map((b) => Number(b.getAttribute('width')))
    expect(widths.reduce((a, b) => a + b, 0)).toBe(360) // the whole six hours
  })
})

describe('the two data centers stay apart', () => {
  it('names the scheduling DC as the seed and the physical place as the pin', async () => {
    await pick([row()], 'JOB_A')
    const text = document.body.textContent ?? ''
    // The seed came from the SCHEDULING dc; the pin's tooltip names the city.
    expect(text).toMatch(/DC name/)
    const titles = [...document.querySelectorAll('title')].map((t) => t.textContent ?? '')
    expect(titles.some((t) => t.includes('New York') && t.includes('nominal'))).toBe(true)
    // and nothing anywhere claims the two are the same object
    expect(text).not.toMatch(/T032-E0700-DMA.*DC-EAST|DC-EAST.*T032-E0700-DMA/)
  })
})

describe('honesty about the bands and the zone', () => {
  it('says the bands are solar and the source zone is an assertion', async () => {
    render(
      <RuntimeSpanMap access={access([row()])} dataCenters={REGISTRY} now={JAN_15} viewerTimeZone="UTC" />,
    )
    await screen.findByRole('combobox')
    const text = document.body.textContent ?? ''
    expect(text).toMatch(/nominal solar meridians/)
    expect(text).toMatch(/not political time zones/)
    expect(text).toMatch(/confirm E is always Eastern/i)
  })

  it('counts the jobs it cannot draw', async () => {
    render(
      <RuntimeSpanMap
        access={access([row(), row({ origin: 'JOB_B', scheduling_dc: 'P99' })])}
        dataCenters={REGISTRY}
        now={JAN_15}
        viewerTimeZone="UTC"
      />,
    )
    await screen.findByRole('combobox')
    expect(document.body.textContent).toMatch(/2 job\(s\) returned; 1 with no timing data at all/)
  })

  it('is loud when the query fails, never a silent empty map', async () => {
    render(
      <RuntimeSpanMap
        access={access([], 'neo4j went away')}
        dataCenters={REGISTRY}
        now={JAN_15}
        viewerTimeZone="UTC"
      />,
    )
    expect(await screen.findByText('neo4j went away')).toBeTruthy()
  })
})
