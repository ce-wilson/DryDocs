// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GraphAccessContext, __resetInFlight } from '../data/graphAccess'
import { __resetFallbackCount } from '../data/provenance'
import type { ExportOptions, GraphAccess, SpecExport, SpecResult } from '../lib/graph'
import { codeOnly, filesMatching } from '../test/sourceScan'
import SpecGrid from './SpecGrid'

// WEB2 — the row ceiling, on the surface where the output leaves the browser.
//
// THE CENTRAL ASSERTION IS A NEGATIVE ONE: the badge must be driven by the
// server's `truncated` field and NOT by `rows.length === limit`, which is the
// heuristic the item forbids and the one any reimplementation would reach for.
// So every fixture below breaks the correlation on purpose — the capped case
// has three rows and the uncapped case has five hundred. A guard whose fixtures
// let the two agree would pass against the defect it exists to catch.

const LIMIT = 500

function rowsOfLength(n: number): Record<string, unknown>[] {
  return Array.from({ length: n }, (_, i) => ({ a: `row-${i}` }))
}

function specResult(over: Partial<SpecResult> = {}): SpecResult {
  return {
    spec_id: 'test.spec.v1',
    database: 'drydocs',
    classification: 'internal-public',
    columns: [{ name: 'a', type: 'string', label: 'A' }],
    cypher: 'MATCH (n) RETURN n LIMIT $limit',
    params: { limit: LIMIT },
    watermarked: false,
    truncated: false,
    limit: LIMIT,
    ephemeral: false,
    keys: ['a'],
    rows: rowsOfLength(3),
    ...over,
  }
}

/** A seam stub that answers runSpec at once and RECORDS what exportSpec was
 *  asked for — the raised ceiling has to reach the seam, not merely change a
 *  label, so the options bag is captured rather than the button text alone. */
class Access {
  readonly kind = 'api' as const
  exports: { specId: string; format: string; opts: ExportOptions }[] = []
  manifest: Record<string, unknown> = { row_count: 3, truncated: false, limit: LIMIT }
  exportFails: string | null = null

  // A plain field, not a constructor parameter property: `erasableSyntaxOnly`
  // is on, so the shorthand does not compile here.
  readonly result: SpecResult
  constructor(result: SpecResult) {
    this.result = result
  }

  runSpec = () => Promise.resolve(this.result)
  exportSpec = (
    specId: string,
    _params: Record<string, unknown>,
    format: 'csv' | 'jsonl',
    opts: ExportOptions = {},
  ): Promise<SpecExport> => {
    this.exports.push({ specId, format, opts })
    if (this.exportFails) return Promise.reject(new Error(this.exportFails))
    return Promise.resolve({
      filename: `${specId}.${format}`,
      blob: new Blob(['x']),
      manifest: this.manifest,
    })
  }
  runRead = () => Promise.reject(new Error('unused'))
  runNamed = () => Promise.reject(new Error('unused'))
}

let access: Access

function wrapper({ children }: { children: ReactNode }) {
  return (
    <GraphAccessContext.Provider
      value={{
        access: access as unknown as GraphAccess,
        apiUrl: 'http://api.test',
        getSessionId: () => Promise.resolve('t'),
      }}
    >
      {children}
    </GraphAccessContext.Provider>
  )
}

/** Render the grid over one result and wait for the live state. */
async function grid(over: Partial<SpecResult> = {}) {
  access = new Access(specResult(over))
  render(<SpecGrid specId="test.spec.v1" fallback={<div>demo</div>} />, { wrapper })
  await screen.findByRole('table')
  return access
}

// jsdom implements neither of these; the download path calls both on every
// export, and an unstubbed `click()` on a blob href logs a navigation error
// that has nothing to do with what is under test.
const realCreate = URL.createObjectURL
const realRevoke = URL.revokeObjectURL
const realClick = HTMLAnchorElement.prototype.click

beforeEach(() => {
  __resetInFlight()
  __resetFallbackCount()
  URL.createObjectURL = () => 'blob:test'
  URL.revokeObjectURL = () => {}
  HTMLAnchorElement.prototype.click = () => {}
})
afterEach(() => {
  cleanup()
  __resetInFlight()
  __resetFallbackCount()
  URL.createObjectURL = realCreate
  URL.revokeObjectURL = realRevoke
  HTMLAnchorElement.prototype.click = realClick
})

// ── clause (a): the badge ───────────────────────────────────────────────────

describe('the TRUNCATED badge, mirroring the canvas', () => {
  it('renders on a capped result — with THREE rows, so nothing about the count could have produced it', async () => {
    await grid({ truncated: true, rows: rowsOfLength(3) })
    const badge = screen.getByText(/^TRUNCATED/)
    expect(badge.textContent).toBe('TRUNCATED 3/3+')
  })

  it('does NOT render on an uncapped result of exactly the ceiling — the heuristic the item forbids', async () => {
    await grid({ truncated: false, rows: rowsOfLength(LIMIT) })
    expect(screen.queryByText(/^TRUNCATED/)).toBeNull()
    // and the row count line still says 500/500, which is the display the old
    // code offered as its only signal.
    expect(screen.getByText(/500\/500/)).toBeTruthy()
  })

  it('names the ceiling in the hover text, from the typed field', async () => {
    await grid({ truncated: true, limit: 250, rows: rowsOfLength(3) })
    expect(screen.getByText(/^TRUNCATED/).getAttribute('title')).toContain('Capped at 250 rows')
  })

  it('says only what it knows when the spec declares no ceiling', async () => {
    await grid({ truncated: true, limit: null, rows: rowsOfLength(3) })
    const title = screen.getByText(/^TRUNCATED/).getAttribute('title') ?? ''
    expect(title).toContain('capped by the server')
    expect(title).not.toMatch(/\d/)
  })
})

// ── clause (b): the export labels and the post-export status ────────────────

describe('no button says "full" unless the result is complete', () => {
  it('says (full) on an uncapped result', async () => {
    await grid({ truncated: false, rows: rowsOfLength(LIMIT) })
    expect(screen.getByRole('button', { name: '⬇ CSV (full)' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '⬇ JSONL (full)' })).toBeTruthy()
  })

  it('states the ceiling instead, on a capped result — and the word "full" is nowhere on the surface', async () => {
    await grid({ truncated: true, rows: rowsOfLength(3) })
    expect(screen.getByRole('button', { name: '⬇ CSV (first 500 rows)' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '⬇ JSONL (first 500 rows)' })).toBeTruthy()
    for (const b of screen.getAllByRole('button')) expect(b.textContent).not.toMatch(/full/i)
  })

  it('the status line after a CAPPED export names the cap', async () => {
    const a = await grid({ truncated: true, rows: rowsOfLength(3) })
    a.manifest = { row_count: 500, truncated: true, limit: LIMIT }
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (first 500 rows)' }))
    await waitFor(() =>
      expect(screen.getByText('exported 500 rows — CAPPED at 500; the result has more')).toBeTruthy(),
    )
  })

  it('the status line after a COMPLETE export says complete', async () => {
    const a = await grid({ truncated: false, rows: rowsOfLength(12) })
    a.manifest = { row_count: 12, truncated: false, limit: LIMIT }
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (full)' }))
    await waitFor(() => expect(screen.getByText('exported 12 rows — complete')).toBeTruthy())
  })

  it('an OLDER manifest with no truncated field claims neither', async () => {
    const a = await grid({ truncated: false, rows: rowsOfLength(12) })
    a.manifest = { row_count: 12 }
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (full)' }))
    await waitFor(() => expect(screen.getByText('exported 12 rows')).toBeTruthy())
  })
})

// ── clause (c): raise it where API1 made it raisable, say so where it did not ─

describe('the raisable ceiling', () => {
  it('offers no control when nothing was capped', async () => {
    await grid({ truncated: false, rows: rowsOfLength(LIMIT) })
    expect(screen.queryByLabelText('Export row ceiling')).toBeNull()
  })

  it('offers the control on a capped registry spec, and the raised value reaches the seam', async () => {
    const a = await grid({ truncated: true, rows: rowsOfLength(3) })
    fireEvent.change(screen.getByLabelText('Export row ceiling'), { target: { value: '2000' } })
    expect(screen.getByRole('button', { name: '⬇ CSV (first 2000 rows)' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (first 2000 rows)' }))
    await waitFor(() => expect(a.exports).toHaveLength(1))
    expect(a.exports[0].opts.limit).toBe(2000)
  })

  it('sends NO limit when the control is untouched — the default IS the display ceiling', async () => {
    const a = await grid({ truncated: true, rows: rowsOfLength(3) })
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (first 500 rows)' }))
    await waitFor(() => expect(a.exports).toHaveLength(1))
    expect(a.exports[0].opts.limit).toBeNull()
  })

  it('ignores a half-typed value rather than sending it', async () => {
    const a = await grid({ truncated: true, rows: rowsOfLength(3) })
    fireEvent.change(screen.getByLabelText('Export row ceiling'), { target: { value: '-' } })
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (first 500 rows)' }))
    await waitFor(() => expect(a.exports).toHaveLength(1))
    expect(a.exports[0].opts.limit).toBeNull()
  })

  it('an EPHEMERAL spec gets the reason, not a control that would 422 (R4)', async () => {
    await grid({ truncated: true, ephemeral: true, spec_id: 'eph.abc', rows: rowsOfLength(3) })
    expect(screen.queryByLabelText('Export row ceiling')).toBeNull()
    expect(screen.getByText(/ceiling frozen at registration/)).toBeTruthy()
  })

  it("surfaces the server's refusal verbatim rather than holding a copy of the rule", async () => {
    const a = await grid({ truncated: true, rows: rowsOfLength(3) })
    a.exportFails = 'export 422: export limit 200000 exceeds the server ceiling 50000'
    fireEvent.click(screen.getByRole('button', { name: '⬇ CSV (first 500 rows)' }))
    await waitFor(() =>
      expect(screen.getByText(/exceeds the server ceiling 50000/)).toBeTruthy(),
    )
  })
})

// ── one vocabulary, enforced ────────────────────────────────────────────────

describe('the two surfaces share one badge', () => {
  it('exactly one source declares the word TRUNCATED', () => {
    // The point of the item is that the grid and the canvas cannot drift apart
    // by being edited separately. They can only stay together if there is one
    // place to edit — so a second declaration is the drift, caught here rather
    // than by someone noticing two badges that no longer match.
    const declaring = filesMatching(/\bTRUNCATED\b/, codeOnly)
    expect(declaring).toEqual(['components/ui/TruncationBadge.tsx'])
  })

  it('and the scan is looking at real sources, not an empty list', () => {
    // J76 / the 2026-09-05 vacuous-scan lesson: a scan that matches nothing
    // reports "no offenders" just as loudly as a scan that finds nothing wrong.
    // This asserts the corpus is populated and that the stripper leaves JSX
    // text alone, which is the property the assertion above depends on.
    expect(filesMatching(/\bexport default function\b/, codeOnly).length).toBeGreaterThan(20)
  })
})

// ── R15 clause (d): the epistemic label, rendered as given ──────────────────

describe('the EPISTEMIC badge on the grid', () => {
  it('renders lower-bound as the server wrote it, with the causes on hover', async () => {
    await grid({
      epistemic: 'lower-bound',
      causes: [{ cause: 'unparsed-cmd-line', detail: 'unparsed-cmd-line', count: 4 }],
      rows: rowsOfLength(3),
    })
    const badge = screen.getByText('lower-bound')
    expect(badge.getAttribute('data-epistemic')).toBe('lower-bound')
    expect(badge.getAttribute('title')).toContain('unparsed-cmd-line (unparsed-cmd-line: 4)')
  })

  it('renders exact as exact', async () => {
    await grid({ epistemic: 'exact', causes: [], rows: rowsOfLength(3) })
    expect(screen.getByText('exact').getAttribute('data-epistemic')).toBe('exact')
  })

  it('renders nothing for an ungraded spec — null is never shown as exact', async () => {
    await grid({ epistemic: null, causes: [], rows: rowsOfLength(3) })
    expect(screen.queryByText('exact')).toBeNull()
    expect(screen.queryByText('lower-bound')).toBeNull()
    expect(document.querySelector('[data-epistemic]')).toBeNull()
  })

  it('zero rows with lower-bound still shows the badge — the empty frame says WHY it is empty', async () => {
    // Not through grid(): with zero rows there is no table to wait for. This
    // frame declares a demo, so an empty live answer becomes the demo-on-empty
    // notice — and THAT notice must carry the label, or the one case clause
    // (b) exists for (zero rows, lower-bound) is the one case that loses it.
    access = new Access(
      specResult({
        epistemic: 'lower-bound',
        causes: [{ cause: 'gate-pending-edge', detail: 'scheduler_depends_on_file' }],
        rows: [],
      }),
    )
    render(<SpecGrid specId="test.spec.v1" fallback={<div>demo</div>} />, { wrapper })
    const badge = await screen.findByText('lower-bound')
    expect(badge.getAttribute('title')).toContain('scheduler_depends_on_file')
    const notice = document.querySelector('[data-provenance="demo"]')
    expect(notice?.getAttribute('data-demo-because')).toBe('empty')
    expect(notice?.contains(badge)).toBe(true)
  })

  it('zero rows with exact says exact', async () => {
    access = new Access(specResult({ epistemic: 'exact', causes: [], rows: [] }))
    render(<SpecGrid specId="test.spec.v1" fallback={<div>demo</div>} />, { wrapper })
    expect((await screen.findByText('exact')).getAttribute('data-epistemic')).toBe('exact')
  })

  it('zero rows ungraded says nothing about epistemics', async () => {
    access = new Access(specResult({ epistemic: null, causes: [], rows: [] }))
    render(<SpecGrid specId="test.spec.v1" fallback={<div>demo</div>} />, { wrapper })
    await screen.findByText(/returned no rows/)
    expect(document.querySelector('[data-epistemic]')).toBeNull()
  })
})
