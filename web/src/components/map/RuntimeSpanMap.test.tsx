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

async function pick(
  rows: Record<string, unknown>[],
  name: string,
  grain: 'job' | 'folder' = 'job',
) {
  render(
    <RuntimeSpanMap
      access={access(rows)}
      dataCenters={REGISTRY}
      now={JAN_15}
      viewerTimeZone="UTC"
    />,
  )
  const grainSelect = await screen.findByLabelText('Grain')
  if (grain !== 'job') fireEvent.change(grainSelect, { target: { value: grain } })
  const entity = screen.getByLabelText(grain === 'job' ? 'Job' : 'Folder')
  fireEvent.change(entity, { target: { value: name } })
  return entity
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
    fireEvent.change(await screen.findByLabelText('Job'), { target: { value: 'JOB_A' } })
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
  it('names BOTH, each under a label that says which kind it is', async () => {
    // POSITIVE assertions on purpose. An earlier draft of this test asserted
    // that the two names never appeared adjacent, which passed for the wrong
    // reason — neither name was rendered at all. Naming only one of them is the
    // conflation by omission: a reader who sees "DEFAULT from the DC name" and
    // one data center concludes that is the data center the name came from.
    await pick([row()], 'JOB_A')
    const scheduling = screen.getByText('Scheduling DC (Control-M)').parentElement!
    const physical = screen.getByText('Physical data center').parentElement!
    expect(scheduling.textContent).toContain('P32')
    expect(scheduling.textContent).toContain('T032-E0700-DMA')
    expect(physical.textContent).toContain('DC-EAST')
    expect(physical.textContent).toContain('New York, NY')
    // and neither name appears under the other's label
    expect(scheduling.textContent).not.toContain('DC-EAST')
    expect(physical.textContent).not.toContain('T032-E0700-DMA')
    // the pin still carries the physical place and its nominal band
    const titles = [...document.querySelectorAll('title')].map((t) => t.textContent ?? '')
    expect(titles.some((t) => t.includes('New York') && t.includes('nominal'))).toBe(true)
  })

  it('says "host never resolved" rather than borrowing the scheduling name', async () => {
    await pick([row({ data_center: null, city: null, state: null, country: null })], 'JOB_A')
    const physical = screen.getByText('Physical data center').parentElement!
    expect(physical.textContent).toContain('host never resolved')
    expect(physical.textContent).not.toContain('P32')
  })
})

describe('the folder grain', () => {
  it('reads the folder window, not one member job’s runtime', async () => {
    // The acceptance names BOTH grains. A folder's span is the P4 window rollup
    // — an EXTENT — and a member's avg_start_time standing in for it would
    // answer a different question under this label.
    const rows = [
      row({ origin: 'JOB_A', avg_start_time: '03:00', avg_run_time: '600', window_start: '01:00', window_end: '05:00' }),
      row({ origin: 'JOB_B', avg_start_time: '04:00', avg_run_time: '600', window_start: '01:00', window_end: '05:00' }),
    ]
    await pick(rows, 'FOLDER_A', 'folder')
    const text = document.body.textContent ?? ''
    expect(text).toContain('01:00 – 05:00') // the folder's own extent
    expect(text).toMatch(/Folder window \(extent of its members\)/)
    expect(text).not.toMatch(/Observed \(job avg start/)
  })

  it('lists each folder once, however many jobs it holds', async () => {
    const rows = [row({ origin: 'JOB_A' }), row({ origin: 'JOB_B' }), row({ origin: 'JOB_C', folder: 'FOLDER_B' })]
    render(
      <RuntimeSpanMap access={access(rows)} dataCenters={REGISTRY} now={JAN_15} viewerTimeZone="UTC" />,
    )
    fireEvent.change(await screen.findByLabelText('Grain'), { target: { value: 'folder' } })
    const options = [...screen.getByLabelText('Folder').querySelectorAll('option')].map(
      (o) => o.textContent,
    )
    expect(options).toEqual(['— select a folder —', 'FOLDER_A', 'FOLDER_B'])
  })
})

describe('honesty about the bands and the zone', () => {
  it('says the bands are solar and the source zone is an assertion', async () => {
    render(
      <RuntimeSpanMap access={access([row()])} dataCenters={REGISTRY} now={JAN_15} viewerTimeZone="UTC" />,
    )
    await screen.findByLabelText('Job')
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
    await screen.findByLabelText('Job')
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
