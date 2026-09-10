import { describe, expect, it } from 'vitest'

import {
  BDAT_LANES,
  isLaneBasis,
  LANE_BASES,
  layerItems,
  resolveLanes,
  undeclaredLanes,
  type LaneItem,
  type LoadMapSystem,
} from './laneBasis'
import { SWIMLANE_ITEMS } from './demoSwimlane'
import loadMap from '../generated/load-map.json'

// WEB23: the registry systems are a PARAMETER now, fetched on demand by the
// view so the artifact leaves the entry chunk. A test is not bundled, so it
// reads the same generated file directly - the assertions below are still about
// real registry systems and not a fixture, which is what makes the "not a
// fixture" test worth having.
const SYSTEMS = (loadMap as { systems?: LoadMapSystem[] }).systems ?? []

// O60. The resolver is the item's architectural ask — "one function, one place"
// — so it is what gets tested. The view renders whatever it returns.

describe('the basis is a parameter', () => {
  it('returns different lanes for different bases over the same input', () => {
    const a = resolveLanes('source-kind', SWIMLANE_ITEMS)
    const b = resolveLanes('layer', SWIMLANE_ITEMS, SYSTEMS)
    expect(a.lanes.map((l) => l.id)).not.toEqual(b.lanes.map((l) => l.id))
  })

  it('offers every basis in the picker, and the guard admits exactly those', () => {
    for (const b of LANE_BASES) expect(isLaneBasis(b.id)).toBe(true)
    expect(isLaneBasis('not-a-basis')).toBe(false)
    expect(isLaneBasis(null)).toBe(false)
    expect(isLaneBasis(undefined)).toBe(false)
  })
})

describe('the source-kind basis', () => {
  it('lands every demo item in a declared lane', () => {
    const { lanes, items } = resolveLanes('source-kind', SWIMLANE_ITEMS)
    const ids = new Set(lanes.map((l) => l.id))
    for (const item of items) expect(ids.has(item.lane)).toBe(true)
  })

  it('carries a wireframe key on every item, so SME feedback re-attaches', () => {
    const { items } = resolveLanes('source-kind', SWIMLANE_ITEMS)
    for (const item of items) expect(item.wf).toMatch(/^WF-DFL-\d\d$/)
  })
})

describe('the BDAT basis', () => {
  // (a) The clause that matters most: an empty declared lane is the FINDING.
  it('declares the human lane even though nothing carries it', () => {
    const { lanes, items } = resolveLanes('layer', SWIMLANE_ITEMS, SYSTEMS)
    const human = lanes.find((l) => l.id === 'human')
    expect(human, 'the human lane must be declared, not omitted').toBeDefined()
    expect(items.filter((i) => i.lane === 'human')).toHaveLength(0)
    expect(human!.emptyNote).toBeTruthy()
  })

  it('renders real registry systems, not a fixture', () => {
    const { items } = resolveLanes('layer', SWIMLANE_ITEMS, SYSTEMS)
    expect(items.length).toBeGreaterThan(0)
    // The demo swimlane items are NOT in this basis — it reads the load map.
    expect(items.map((i) => i.id)).not.toContain('pipeline')
  })

  // (b) Three different axes in this repo are called a layer. The basis must say
  // which one it means, and must not merge them.
  it('states its axis and names what it is NOT', () => {
    const { axisNote } = resolveLanes('layer', SWIMLANE_ITEMS, SYSTEMS)
    expect(axisNote).toContain('SYSTEM rows')
    expect(axisNote).toContain('rdfs:domain')
    expect(axisNote.toLowerCase()).toContain('domain')
  })

  // (c) A layer lane groups by CARRIER while `layer` is a system field.
  it('says the grouping is by carrier, not subject', () => {
    const { caveat } = resolveLanes('layer', SWIMLANE_ITEMS, SYSTEMS)
    expect(caveat).toBeTruthy()
    expect(caveat!.toUpperCase()).toContain('CARRIER')
  })
})

describe('undeclaredLanes', () => {
  // A value nobody declared is exactly what a reader needs to see — dropping it
  // silently is the failure this prevents.
  it('surfaces a lane the data uses that the declared set does not name', () => {
    const items: LaneItem[] = [{ id: 'x', label: 'x', sub: '', lane: 'invented' }]
    const extra = undeclaredLanes(items, BDAT_LANES)
    expect(extra.map((l) => l.id)).toEqual(['invented'])
    expect(extra[0].emptyNote).toContain('not a declared')
  })

  it('returns nothing when every lane is declared', () => {
    const items: LaneItem[] = [{ id: 'x', label: 'x', sub: '', lane: 'data' }]
    expect(undeclaredLanes(items, BDAT_LANES)).toEqual([])
  })
})

describe('the BDAT basis without its systems (WEB23)', () => {
  // The view fetches the registry on demand, so "no systems yet" is a real state
  // this resolver can be called in. It must render as NOTHING and not as the
  // empty-lane finding - SwimlaneView holds a reading notice for exactly that
  // window, and this pins the resolver half of the arrangement.
  it('declares its lanes and places no item when no systems are given', () => {
    const { lanes, items } = resolveLanes('layer', SWIMLANE_ITEMS)
    expect(items).toEqual([])
    expect(lanes.map((l) => l.id)).toContain('human')
  })

  it('maps whatever systems it is handed, undeclared layers included', () => {
    const items = layerItems([
      { id: 's1', name: 'One', layer: 'data', classification: 'Internal' },
      { id: 's2', name: 'Two' },
      { id: 's3', name: 'Three', layer: 'invented' },
    ])
    expect(items.map((i) => i.lane)).toEqual(['data', 'undeclared', 'invented'])
    // A system with no declared layer is not silently dropped into one.
    expect(items[1].sub).toBe('system')
    expect(items[0].sub).toBe('system · Internal')
  })
})
