import { describe, expect, it } from 'vitest'

import type { SpecResult } from '../lib/graph'
import { codeOnly, filesMatching, readFileSync, withoutComments } from '../test/sourceScan'
import { DECLARED_TYPE_EXCEPTIONS, TYPE_CHECK_ROWS, validateRows, validateRowsOf } from './rowShape'
import type { RowShape } from './rowShape'

// WEB6 — the seam check, and the guard that keeps the seam from re-growing.

interface JobRow {
  job_name: string
  folder: string
  data_center: string | null
  job_id: string
}
const JOB_COLUMNS: RowShape<JobRow> = ['job_name', 'folder', 'data_center', 'job_id']

interface AppRow {
  app_id: string
  name: string
  applications: number
}
const APP_COLUMNS: RowShape<AppRow> = ['app_id', 'name', 'applications']

function result(over: Partial<SpecResult> = {}): SpecResult {
  return {
    spec_id: 'explorer.jobs.v2',
    database: 'drydocs',
    classification: 'internal',
    columns: [
      { name: 'job_name', type: 'string', label: 'Job' },
      { name: 'folder', type: 'string', label: 'Folder' },
      { name: 'data_center', type: 'string', label: 'Data center' },
      { name: 'job_id', type: 'string', label: 'Job id' },
    ],
    cypher: 'MATCH (n) RETURN n LIMIT $limit',
    params: { limit: 500 },
    watermarked: false,
    truncated: false,
    limit: 500,
    ephemeral: false,
    keys: ['job_name', 'folder', 'data_center', 'job_id'],
    rows: [{ job_name: 'J1', folder: 'F1', data_center: 'DC1', job_id: 'j-1' }],
    ...over,
  }
}

function appResult(over: Partial<SpecResult> = {}): SpecResult {
  return result({
    spec_id: 'explorer.controlm-app-codes.v1',
    columns: [
      { name: 'app_id', type: 'string', label: 'Application ID' },
      { name: 'name', type: 'string', label: 'Application' },
      { name: 'applications', type: 'int', label: 'Apps' },
    ],
    keys: ['app_id', 'name', 'applications'],
    rows: [{ app_id: 'a-1', name: 'Alpha', applications: 3 }],
    ...over,
  })
}

// ── clause (d): conforming, missing, mistyped — for two specs ────────────────

describe('a conforming result passes, for both specs', () => {
  it('the string spec', () => {
    const out = validateRows<JobRow>(result(), JOB_COLUMNS)
    expect(out.ok).toBe(true)
    if (out.ok) expect(out.rows[0].job_name).toBe('J1')
  })

  it('the spec with an int column', () => {
    const out = validateRows<AppRow>(appResult(), APP_COLUMNS)
    expect(out.ok).toBe(true)
    if (out.ok) expect(out.rows[0].applications).toBe(3)
  })
})

describe('a MISSING column is named, not rendered as blanks', () => {
  it('names the spec, the column and what did arrive', () => {
    const out = validateRows<JobRow>(
      result({
        columns: result().columns.filter((c) => c.name !== 'data_center'),
        keys: ['job_name', 'folder', 'job_id'],
      }),
      JOB_COLUMNS,
    )
    expect(out.ok).toBe(false)
    if (!out.ok) {
      expect(out.message).toContain('explorer.jobs.v2')
      expect(out.message).toContain("'data_center'")
      expect(out.message).toContain('job_name, folder, job_id')
    }
  })

  it('lists every missing column, not just the first', () => {
    const out = validateRows<AppRow>(
      appResult({ columns: [{ name: 'app_id', type: 'string', label: 'A' }], keys: ['app_id'] }),
      APP_COLUMNS,
    )
    expect(out.ok).toBe(false)
    if (!out.ok) expect(out.message).toContain("'name', 'applications'")
  })
})

describe('a MISTYPED column is named, with the row index', () => {
  it('a string where the server declared int', () => {
    const out = validateRows<AppRow>(
      appResult({
        rows: [
          { app_id: 'a-1', name: 'Alpha', applications: 3 },
          { app_id: 'a-2', name: 'Beta', applications: '7' },
        ],
      }),
      APP_COLUMNS,
    )
    expect(out.ok).toBe(false)
    if (!out.ok) {
      expect(out.message).toContain("column 'applications' is declared int")
      expect(out.message).toContain('row 1 carries string')
    }
  })

  it('a number where the server declared string', () => {
    const out = validateRows<JobRow>(result({ rows: [{ ...result().rows[0], folder: 7 }] }), JOB_COLUMNS)
    expect(out.ok).toBe(false)
    if (!out.ok) expect(out.message).toContain('row 0 carries number')
  })

  it('an ARRAY is named as an array, not as "object"', () => {
    const out = validateRows<JobRow>(
      result({ rows: [{ ...result().rows[0], folder: ['a', 'b'] }] }),
      JOB_COLUMNS,
    )
    expect(out.ok).toBe(false)
    if (!out.ok) expect(out.message).toContain('carries array')
  })
})

// ── the three things that would fail on real data if assumed away ───────────

describe('what real results actually look like', () => {
  it('NULL satisfies a declared type — OPTIONAL MATCH is normal, not a defect', () => {
    // explorer.jobs.v2 fills data_center from an OPTIONAL MATCH and declares it
    // string. Rejecting null would fail on every job with no server.
    const out = validateRows<JobRow>(
      result({ rows: [{ job_name: 'J1', folder: 'F1', data_center: null, job_id: 'j-1' }] }),
      JOB_COLUMNS,
    )
    expect(out.ok).toBe(true)
  })

  it('an EPHEMERAL spec is checked for presence only (R4 types are placeholders)', () => {
    // R4 registers every ephemeral column as type "string" whatever it holds,
    // so type-checking one would reject an agent's perfectly good count.
    const eph = appResult({
      spec_id: 'eph.abc123',
      ephemeral: true,
      columns: [
        { name: 'app_id', type: 'string', label: 'app_id' },
        { name: 'name', type: 'string', label: 'name' },
        { name: 'applications', type: 'string', label: 'applications' },
      ],
    })
    expect(validateRows<AppRow>(eph, APP_COLUMNS).ok).toBe(true)
    // ...but a missing column still fails, which is the check that matters there
    const short = { ...eph, keys: ['app_id'], columns: eph.columns.slice(0, 1) }
    expect(validateRows<AppRow>(short, APP_COLUMNS).ok).toBe(false)
  })

  it('the two known-wrong SERVER declarations are exempt from the type check only', () => {
    const series: SpecResult = result({
      spec_id: 'runbooks.series.v1',
      columns: [
        { name: 'trigger_job', type: 'string', label: 'Trigger job' },
        { name: 'lands', type: 'string', label: 'Lands' },
      ],
      keys: ['trigger_job', 'lands'],
      rows: [{ trigger_job: 'J1', lands: ['asset-1', 'asset-2'] }],
    })
    interface SeriesRow {
      trigger_job: string
      lands: unknown[]
    }
    const shape: RowShape<SeriesRow> = ['trigger_job', 'lands']
    expect(validateRows<SeriesRow>(series, shape).ok).toBe(true)
    // the PRESENCE check still applies to an exempt column
    const missing = { ...series, keys: ['trigger_job'], columns: series.columns.slice(0, 1) }
    expect(validateRows<SeriesRow>(missing, shape).ok).toBe(false)
  })

  it('every exception names a spec and at least one column', () => {
    // A dead entry here is an exemption nobody can audit. The live check that
    // the server declaration is STILL wrong is a python guard
    // (tests/unit/test_row_shape_exceptions.py) — only that side can import the
    // registry, which is J37's rule, not a convenience.
    const entries = Object.entries(DECLARED_TYPE_EXCEPTIONS)
    expect(entries.length).toBeGreaterThan(0)
    for (const [specId, columns] of entries) {
      expect(specId).toMatch(/^[a-z0-9-]+(\.[a-z0-9-]+)+\.v\d+$/)
      expect(columns.length).toBeGreaterThan(0)
    }
  })
})

describe('the core check over a source that declares no types', () => {
  it('checks presence and nothing else — the O13 mappings grid shape', () => {
    const ok = validateRowsOf<{ a: string; b: string }>(
      { source: "mappings grid 'x'", keys: ['a', 'b'], rows: [{ a: '1', b: 2 }] },
      ['a', 'b'],
    )
    // `b` is a number under no declaration: presence passed, and there was
    // nothing to type-check it against. That is the honest outcome, not a miss.
    expect(ok.ok).toBe(true)
    const bad = validateRowsOf<{ a: string; b: string }>(
      { source: "mappings grid 'x'", keys: ['a'], rows: [{ a: '1' }] },
      ['a', 'b'],
    )
    expect(bad.ok).toBe(false)
    if (!bad.ok) expect(bad.message).toContain("mappings grid 'x'")
  })

  it('stops after the declared row budget rather than walking a full grid', () => {
    const rows = Array.from({ length: TYPE_CHECK_ROWS + 5 }, (_, i) => ({
      app_id: `a-${i}`,
      name: 'x',
      // the mistype is PAST the budget, so it is deliberately not caught
      applications: i === TYPE_CHECK_ROWS + 2 ? 'seven' : i,
    }))
    expect(validateRows<AppRow>(appResult({ rows }), APP_COLUMNS).ok).toBe(true)
    rows[0].applications = 'seven'
    expect(validateRows<AppRow>(appResult({ rows }), APP_COLUMNS).ok).toBe(false)
  })
})

// ── clause (b): the seam cannot re-grow ─────────────────────────────────────

describe('the double cast is gone and stays gone', () => {
  it('no hand-written source under web/src contains `as unknown as`', () => {
    expect(filesMatching(/as unknown as/, codeOnly)).toEqual([])
  })

  it('and the scan is reading real code — its own explanation does not trip it', () => {
    // J66, demonstrated rather than asserted: rowShape.ts's header quotes the
    // forbidden pattern verbatim while explaining it. A raw substring scan would
    // fail on that comment and teach the next person to delete the explanation.
    const raw = readFileSync(`${process.cwd()}/src/data/rowShape.ts`, 'utf8')
    expect(raw).toContain('as unknown as')
    expect(codeOnly(raw)).not.toContain('as unknown as')
    // and the corpus is populated — a scan over nothing reports "no offenders"
    // just as loudly (the 2026-09-05 vacuous-scan lesson).
    expect(filesMatching(/\bexport\b/, withoutComments).length).toBeGreaterThan(40)
  })
})
