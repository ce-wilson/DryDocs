// Unit tests for the QuerySpec -> NVL mappers (O81).
//
// WHAT THESE GUARD IS A TRUTH CLAIM, not a rendering detail. A mapper turns rows
// back into the graph they were flattened from, and the one way it can be wrong
// that matters is drawing an edge or a node the reviewed spec never returned —
// a picture is far more convincing than a table, so an invented hop here is
// worse than an invented cell there. Each test below names the pattern its
// spec's Cypher walked and holds the mapper to exactly that.
import { describe, expect, it } from 'vitest'

import {
  CANVAS_SURFACES,
  GRAPH_KIND_TOKEN,
  NODE_CEILING,
  mapAppNeighbourhood,
  mapSeries,
  type SpecRow,
} from './nvl-mapping'

describe('mapSeries — runbooks.series.v1', () => {
  const rows: SpecRow[] = [
    { trigger_job: 'JOB_A', process: 'proc-1', kind: 'glue', lands: ['s3://raw/a', 's3://raw/b'] },
    { trigger_job: 'JOB_B', process: 'proc-1', kind: 'glue', lands: ['s3://raw/a'] },
  ]

  it('rebuilds both hops the spec walked, and only those', () => {
    const g = mapSeries(rows)
    expect(g.nodes.map((n) => n.kind).sort()).toEqual([
      'ControlMJob',
      'ControlMJob',
      'DataAsset',
      'DataAsset',
      'ETLProcess',
    ])
    expect(g.relationships.map((r) => r.caption).sort()).toEqual([
      'INVOKES',
      'INVOKES',
      'WRITES_TO',
      'WRITES_TO',
    ])
  })

  // G89 resolved this spec off :TRIGGERS — a PLANNED edge no loader may write —
  // and onto :INVOKES. The picture follows the spec, so the caption must too.
  it('captions the job hop INVOKES, never TRIGGERS', () => {
    const captions = mapSeries(rows).relationships.map((r) => r.caption)
    expect(captions).toContain('INVOKES')
    expect(captions).not.toContain('TRIGGERS')
  })

  it('merges repeated nodes across rows instead of duplicating them', () => {
    const g = mapSeries(rows)
    expect(g.nodes.filter((n) => n.kind === 'ETLProcess')).toHaveLength(1)
    expect(g.nodes.filter((n) => n.caption === 's3://raw/a')).toHaveLength(1)
    expect(g.rowCount).toBe(2)
  })

  it('draws nothing for a row that landed no assets', () => {
    const g = mapSeries([{ trigger_job: 'J', process: 'p', kind: 'k', lands: [] }])
    expect(g.nodes.map((n) => n.kind)).toEqual(['ControlMJob', 'ETLProcess'])
    expect(g.relationships).toHaveLength(1)
  })

  it('survives a collect() that yielded nulls', () => {
    const g = mapSeries([{ trigger_job: 'J', process: 'p', kind: 'k', lands: [null, ''] }])
    expect(g.nodes.filter((n) => n.kind === 'DataAsset')).toHaveLength(0)
  })

  // Zero rows is the honest state until the curated lineage load runs, so it
  // must be an empty graph rather than a crash or a fabricated placeholder.
  it('returns an empty graph for zero rows', () => {
    expect(mapSeries([])).toEqual({
      nodes: [],
      relationships: [],
      rowCount: 0,
      nodeCount: 0,
      truncated: false,
    })
  })
})

describe('mapAppNeighbourhood — explorer.folder-applications.v1', () => {
  const rows: SpecRow[] = [
    {
      folder: 'F1',
      data_center: 'DC-EAST',
      app_id: 'APP1',
      application: 'Payments',
      origin: 'seal',
      port_state: 'active',
      jobs: 12,
    },
    {
      folder: 'F2',
      data_center: 'DC-EAST',
      app_id: 'APP1',
      application: 'Payments',
      origin: 'seal',
      port_state: 'active',
      jobs: 3,
    },
  ]

  it('draws folder -> application and folder -> data centre', () => {
    const g = mapAppNeighbourhood(rows)
    expect(g.relationships.map((r) => r.caption).sort()).toEqual([
      'BELONGS_TO_APPLICATION',
      'BELONGS_TO_APPLICATION',
      'SCHEDULED_ON',
      'SCHEDULED_ON',
    ])
    expect(g.nodes.filter((n) => n.kind === 'BusinessApplication')).toHaveLength(1)
    expect(g.nodes.filter((n) => n.kind === 'ControlMServer')).toHaveLength(1)
  })

  // THE PORT HOP IS THE POINT. The spec traverses (:Port) but returns no port
  // identity, and the K7/K8 reshape put that hop under a signed gate — so a
  // :Port node here would be one the console invented.
  it('does not invent a Port node from a hop the rows cannot identify', () => {
    const kinds = new Set(mapAppNeighbourhood(rows).nodes.map((n) => n.kind))
    expect([...kinds].some((k) => k.toLowerCase().includes('port'))).toBe(false)
  })

  // `jobs` is a count. Drawing N job nodes from a number would be inventing them.
  it('keeps the job COUNT as a property rather than drawing job nodes', () => {
    const g = mapAppNeighbourhood(rows)
    expect(g.nodes.filter((n) => n.kind === 'ControlMJob')).toHaveLength(0)
    const folder = g.nodes.find((n) => n.caption === 'F1')
    expect(folder?.properties.Jobs).toBe('12')
  })

  it('tolerates a row with no data centre', () => {
    const g = mapAppNeighbourhood([{ folder: 'F', app_id: 'A', application: 'App' }])
    expect(g.relationships.map((r) => r.caption)).toEqual(['BELONGS_TO_APPLICATION'])
  })
})

describe('the declared ceiling', () => {
  it('caps nodes and says it capped them', () => {
    const rows: SpecRow[] = Array.from({ length: NODE_CEILING + 40 }, (_, i) => ({
      trigger_job: `JOB_${i}`,
      process: `proc_${i}`,
      kind: 'k',
      lands: [],
    }))
    const g = mapSeries(rows)
    expect(g.nodes).toHaveLength(NODE_CEILING)
    expect(g.truncated).toBe(true)
    expect(g.nodeCount).toBe((NODE_CEILING + 40) * 2)
  })

  it('never leaves a relationship pointing at a node the cap removed', () => {
    const rows: SpecRow[] = Array.from({ length: NODE_CEILING + 40 }, (_, i) => ({
      trigger_job: `JOB_${i}`,
      process: `proc_${i}`,
      kind: 'k',
      lands: [],
    }))
    const g = mapSeries(rows)
    const ids = new Set(g.nodes.map((n) => n.id))
    for (const rel of g.relationships) {
      expect(ids.has(rel.from)).toBe(true)
      expect(ids.has(rel.to)).toBe(true)
    }
  })

  it('does not flag truncation when nothing was dropped', () => {
    expect(mapSeries([{ trigger_job: 'J', process: 'p', kind: 'k', lands: [] }]).truncated).toBe(
      false,
    )
  })
})

describe('styling and surface registration', () => {
  it('gives every kind a theme token, never a raw hex', () => {
    for (const [kind, token] of Object.entries(GRAPH_KIND_TOKEN)) {
      expect(token.startsWith('--'), `${kind} must map to a token`).toBe(true)
    }
  })

  it('every kind a mapper can emit has a token', () => {
    const emitted = new Set([
      ...mapSeries([{ trigger_job: 'j', process: 'p', kind: 'k', lands: ['a'] }]).nodes.map(
        (n) => n.kind,
      ),
      ...mapAppNeighbourhood([
        { folder: 'f', app_id: 'a', application: 'A', data_center: 'd' },
      ]).nodes.map((n) => n.kind),
    ])
    for (const kind of emitted) expect(GRAPH_KIND_TOKEN[kind]).toBeTruthy()
  })

  it('pairs each shipped surface with its own mapper', () => {
    expect(Object.keys(CANVAS_SURFACES).sort()).toEqual([
      'explorer.folder-applications.v1',
      'runbooks.series.v1',
    ])
  })
})
