// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GraphAccessContext, __resetInFlight } from './graphAccess'
import type { GraphAccess, RequestOptions, SpecResult } from '../lib/graph'
import { filesMatching, withoutComments } from '../test/sourceScan'
import {
  __resetFallbackCount,
  fallbackCount,
  rowsOf,
  useLiveOrDemo,
} from './provenance'
import type { RowShape } from './rowShape'

// WEB1 — the provenance seam and the guard that makes it the only path.

const DEMO = [{ id: 'demo-1' }, { id: 'demo-2' }] as const

function specResult(rows: Record<string, unknown>[]): SpecResult {
  return {
    spec_id: 's.v1',
    database: 'drydocs',
    classification: 'internal-public',
    columns: [],
    cypher: 'RETURN 1',
    params: {},
    watermarked: false,
    truncated: false,
    ephemeral: false,
    keys: ['id'],
    rows,
  }
}

class Access {
  readonly kind = 'api' as const
  private settle!: (r: SpecResult) => void
  private fail!: (e: unknown) => void
  runSpec(_id: string, _p: Record<string, unknown> = {}, _o: RequestOptions = {}) {
    return new Promise<SpecResult>((resolve, reject) => {
      this.settle = resolve
      this.fail = reject
    })
  }
  answer(rows: Record<string, unknown>[]) {
    this.settle(specResult(rows))
  }
  /** WEB6: answer with a result whose columns are the caller's problem. */
  answerWith(over: Partial<SpecResult>) {
    this.settle({ ...specResult([{ id: 'r' }]), ...over })
  }
  refuse(message: string) {
    this.fail(new Error(message))
  }
  runRead = () => Promise.reject(new Error('unused'))
  runNamed = () => Promise.reject(new Error('unused'))
  exportSpec = () => Promise.reject(new Error('unused'))
}

let access: Access

function wrapper({ children }: { children: ReactNode }) {
  return (
    <GraphAccessContext.Provider
      value={{
        access: access as unknown as GraphAccess,
        apiUrl: 'http://api.test',
        getToken: () => Promise.resolve('t'),
      }}
    >
      {children}
    </GraphAccessContext.Provider>
  )
}

beforeEach(() => {
  access = new Access()
  __resetInFlight()
  __resetFallbackCount()
})
afterEach(() => {
  cleanup()
  __resetInFlight()
  __resetFallbackCount()
})

describe('the union distinguishes what the five fallbacks conflated', () => {
  it('rows from the graph are live', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    expect(result.current.status).toBe('loading')
    await act(async () => access.answer([{ id: 'real' }]))
    expect(result.current.status).toBe('live')
    expect(rowsOf(result.current)).toEqual([{ id: 'real' }])
  })

  it('a FAILED request is demo-because-error, never demo-because-empty', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.refuse('502 bad gateway'))
    expect(result.current).toMatchObject({ status: 'demo', because: 'error' })
    if (result.current.status === 'demo') expect(result.current.message).toContain('502')
  })

  it('an EMPTY answer is demo-because-empty, and carries no error message', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.answer([]))
    expect(result.current).toMatchObject({ status: 'demo', because: 'empty', message: null })
  })

  it('a surface that wants the empty answer gets `empty`, not demo rows', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', DEMO, { demoOnEmpty: false }), {
      wrapper,
    })
    await act(async () => access.answer([]))
    expect(result.current.status).toBe('empty')
    expect(rowsOf(result.current)).toEqual([])
  })

  it('a surface with NO demo shows an error, and fabricates nothing', async () => {
    // The property that matters most: no demo means no demo. A seam that
    // invented rows for a surface that declared none would be worse than the
    // five fallbacks it replaces.
    const { result } = renderHook(() => useLiveOrDemo('s.v1', null), { wrapper })
    await act(async () => access.refuse('502'))
    expect(result.current).toMatchObject({ status: 'error', reason: 'failed' })
    expect(rowsOf(result.current)).toEqual([])
  })

  it('a surface with no demo renders an empty answer as empty', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', null), { wrapper })
    await act(async () => access.answer([]))
    expect(result.current.status).toBe('empty')
  })
})

describe('every fallback activation is counted (clause e)', () => {
  it('counts an error fallback, with the spec that caused it', async () => {
    renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    expect(fallbackCount().total).toBe(0)
    await act(async () => access.refuse('502'))
    const c = fallbackCount()
    expect(c.total).toBe(1)
    expect(c.bySpec['s.v1']).toBe(1)
    expect(c.last).toMatchObject({ specId: 's.v1', because: 'error' })
  })

  it('counts an empty fallback too — fabricated rows are fabricated either way', async () => {
    renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.answer([]))
    expect(fallbackCount()).toMatchObject({ total: 1, last: { because: 'empty' } })
  })

  it('a LIVE answer counts nothing', async () => {
    renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.answer([{ id: 'real' }]))
    expect(fallbackCount().total).toBe(0)
  })

  it('one fallback counts ONCE, not once per re-render', async () => {
    // The count is an operator signal; a number that inflates with re-renders
    // is a number nobody can act on.
    const { rerender } = renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.refuse('502'))
    rerender()
    rerender()
    expect(fallbackCount().total).toBe(1)
  })
})

// ── clause (c): the seam is the only path ───────────────────────────────────

/** The eleven synthetic-data modules the item enumerates. */
const DEMO_MODULES = [
  'demoGraph',
  'demoLineage',
  'demoLoads',
  'demoOwnership',
  'demoProductRollup',
  'demoRemediation',
  'demoRunbooks',
  'demoDocs',
  'demoSwimlane',
  'demoStatus',
  'mappingsDemo',
]

/** Files that import a demo module for a reason that is NOT a live fallback.
 *
 * Default-deny with a reason each, the shape test_module_boundary.py uses. The
 * distinction being drawn is real and worth stating: a pane whose CONTENT is
 * the demo graph — a surface with no live source yet — is not degrading from
 * live data, and routing it through a seam that reports `demo` would say
 * something false about a frame that never claimed to be live. What clause (c)
 * forbids is the try-live-else-synthetic path, and that is what this list holds
 * the line on: any file that both reads a spec AND imports a demo module has to
 * argue for itself here.
 *
 * Three demo modules NAME another demo module only in a comment (demoSwimlane,
 * demoProductRollup, and nvl-mapping.ts's token note). They are not listed,
 * because withoutComments correctly does not see them — and listing a file the
 * scan cannot find would make the dead-entry test below fail, which is how the
 * first draft of this list was corrected. */
const NOT_A_FALLBACK: Record<string, string> = {
  'explorer/DataFrame.tsx': 'renders a demo frame BY DESIGN — it has no live source.',
  'explorer/ExplorerGraphPane.tsx': 'the demo graph IS its content; no spec behind it.',
  'explorer/NodeInspector.tsx': 'inspector fixtures for a demo node.',
  'lineage/LineageGraphPane.tsx': 'the demo DAG IS its content.',
  'lineage/SwimlaneView.tsx': 'draws the demo swimlanes; no spec behind it.',
  'ownership/OwnershipGraphPane.tsx': 'the demo rollup IS its content.',
  'ownership/ProductRollup.tsx': 'renders the demo rollup; no spec behind it.',
  'loads/LoadsTimeline.tsx': 'draws whatever rows it is given; the seam decides provenance.',
  'routes/RemediationRoute.tsx': 'the remediation surfaces are demo-only in this phase.',
  'routes/DocsRoute.tsx': 'passes its demo frames to SpecGrid, which owns the seam.',
  'routes/LineageRoute.tsx': 'passes its demo frames to SpecGrid, which owns the seam.',
  'routes/RunbooksRoute.tsx': 'passes its demo frames to SpecGrid, which owns the seam.',
  'routes/OwnershipRoute.tsx': 'passes its demo frames to SpecGrid, which owns the seam.',
  'routes/explorer/ExplorerRoute.tsx': 'passes its demo frames to SpecGrid, which owns the seam.',
  'routes/MappingsRoute.tsx': 'the O13 mappings surface has its own API, not a QuerySpec.',
  'routes/AppCodeCascadePane.tsx': 'ON the seam: four demo frames pass THROUGH useLiveOrDemo.',
  'routes/LoadsRoute.tsx': 'ON the seam: DEMO_RUNS is passed TO useLiveOrDemo.',
}

describe('the demo modules are reached through the seam (clause c)', () => {
  const pattern = new RegExp(`\\b(${DEMO_MODULES.join('|')})\\b`)

  // withoutComments, NOT codeOnly, and this is the second time in one item that
  // the choice decided whether the guard worked at all. A demo module is
  // reached through an import PATH — '../loads/demoLoads' — which is a string
  // literal, and codeOnly neutralises string literals. Written that way the
  // scan matched nothing, every offender list was empty, and the assertions
  // passed while proving nothing. The dead-entry test below is what caught it:
  // a scan that finds nothing makes every allow-list entry look dead, which is
  // exactly why that test is worth having.
  const scan = () => filesMatching(pattern, withoutComments)

  it('every importer of a demo module is accounted for', () => {
    const offenders = scan()
      .filter((f) => !DEMO_MODULES.some((m) => f.endsWith(`${m}.ts`)))
      .filter((f) => !(f in NOT_A_FALLBACK))
      .filter((f) => f !== 'data/provenance.ts')
    expect(offenders).toEqual([])
  })

  it('the list has no dead entries, so it shrinks as routes move onto the seam', () => {
    const importers = new Set(scan())
    const dead = Object.keys(NOT_A_FALLBACK).filter((f) => !importers.has(f))
    expect(dead, `dead allow-list entries: ${dead.join(', ')}`).toEqual([])
  })

  it('the scan sees an import and not a comment (instrument check)', () => {
    // Both directions, because getting either wrong is silent: a scan that
    // cannot see an import proves nothing, and one that fires on the comment
    // explaining the rule teaches people to delete the explanation (J66).
    expect(pattern.test(withoutComments('// demoLoads used to be imported here'))).toBe(false)
    expect(
      pattern.test(withoutComments("import { DEMO_RUNS } from '../loads/demoLoads'")),
    ).toBe(true)
  })

  it('SpecGrid reaches its fallback through the seam and not around it', () => {
    const onSeam = filesMatching(/useLiveOrDemo/)
    for (const f of [
      'explorer/SpecGrid.tsx',
      'components/SpecGraphPane.tsx',
      'routes/LoadsRoute.tsx',
      'routes/AppCodeCascadePane.tsx',
    ]) {
      expect(onSeam).toContain(f)
    }
  })
})

// ── WEB6: the shape state ───────────────────────────────────────────────────

describe('a result whose columns do not match is its own state', () => {
  interface ShapedRow {
    id: string
    label: string
  }
  const SHAPE: RowShape<ShapedRow> = ['id', 'label']
  // The demo has to describe the SAME row type the shape does — the compiler
  // says so, which is a small win on its own: a demo that drifted from the
  // shape it stands in for used to be representable.
  const SHAPED_DEMO: readonly ShapedRow[] = [{ id: 'demo-1', label: 'Demo one' }]

  it('reports `shape`, not `live`, when a required column is absent', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', SHAPED_DEMO, { shape: SHAPE }), { wrapper })
    await act(async () => access.answer([{ id: 'real' }]))
    expect(result.current.status).toBe('shape')
    if (result.current.status === 'shape') expect(result.current.message).toContain("'label'")
  })

  it('DOES NOT fall back to demo, even though this surface has one', async () => {
    // The whole value of catching a contract change is that someone sees it.
    // Substituting fabricated rows behind a badge would hide exactly the drift
    // the check exists to expose — so this is asserted, not assumed.
    const { result } = renderHook(() => useLiveOrDemo('s.v1', SHAPED_DEMO, { shape: SHAPE }), { wrapper })
    await act(async () => access.answer([{ id: 'real' }]))
    expect(result.current.status).not.toBe('demo')
    expect(rowsOf(result.current)).toEqual([])
  })

  it('is COUNTED where an operator already looks, under its own reason', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', SHAPED_DEMO, { shape: SHAPE }), { wrapper })
    await act(async () => access.answer([{ id: 'real' }]))
    expect(result.current.status).toBe('shape')
    expect(fallbackCount().total).toBe(1)
    expect(fallbackCount().last?.because).toBe('shape')
    expect(fallbackCount().bySpec['s.v1']).toBe(1)
  })

  it('a matching result stays live, and the rows come back typed', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', SHAPED_DEMO, { shape: SHAPE }), { wrapper })
    await act(async () =>
      access.answerWith({
        keys: ['id', 'label'],
        columns: [
          { name: 'id', type: 'string', label: 'Id' },
          { name: 'label', type: 'string', label: 'Label' },
        ],
        rows: [{ id: 'r1', label: 'One' }],
      }),
    )
    expect(result.current.status).toBe('live')
    expect(rowsOf(result.current)).toEqual([{ id: 'r1', label: 'One' }])
    expect(fallbackCount().total).toBe(0)
  })

  it('a caller that declares NO shape is unaffected — the old behaviour, kept', async () => {
    const { result } = renderHook(() => useLiveOrDemo('s.v1', DEMO), { wrapper })
    await act(async () => access.answer([{ id: 'real' }]))
    expect(result.current.status).toBe('live')
  })
})
