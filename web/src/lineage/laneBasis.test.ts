import { describe, expect, it } from 'vitest'

import {
  BDAT_LANES,
  isLaneBasis,
  LANE_BASES,
  resolveLanes,
  undeclaredLanes,
  type LaneItem,
} from './laneBasis'
import { SWIMLANE_ITEMS } from './demoSwimlane'

// O60. The resolver is the item's architectural ask — "one function, one place"
// — so it is what gets tested. The view renders whatever it returns.

describe('the basis is a parameter', () => {
  it('returns different lanes for different bases over the same input', () => {
    const a = resolveLanes('source-kind', SWIMLANE_ITEMS)
    const b = resolveLanes('layer', SWIMLANE_ITEMS)
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
    const { lanes, items } = resolveLanes('layer', SWIMLANE_ITEMS)
    const human = lanes.find((l) => l.id === 'human')
    expect(human, 'the human lane must be declared, not omitted').toBeDefined()
    expect(items.filter((i) => i.lane === 'human')).toHaveLength(0)
    expect(human!.emptyNote).toBeTruthy()
  })

  it('renders real registry systems, not a fixture', () => {
    const { items } = resolveLanes('layer', SWIMLANE_ITEMS)
    expect(items.length).toBeGreaterThan(0)
    // The demo swimlane items are NOT in this basis — it reads the load map.
    expect(items.map((i) => i.id)).not.toContain('pipeline')
  })

  // (b) Three different axes in this repo are called a layer. The basis must say
  // which one it means, and must not merge them.
  it('states its axis and names what it is NOT', () => {
    const { axisNote } = resolveLanes('layer', SWIMLANE_ITEMS)
    expect(axisNote).toContain('SYSTEM rows')
    expect(axisNote).toContain('rdfs:domain')
    expect(axisNote.toLowerCase()).toContain('domain')
  })

  // (c) A layer lane groups by CARRIER while `layer` is a system field.
  it('says the grouping is by carrier, not subject', () => {
    const { caveat } = resolveLanes('layer', SWIMLANE_ITEMS)
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
