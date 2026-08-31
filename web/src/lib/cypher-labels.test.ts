import { describe, expect, it } from 'vitest'

import { labelsNamedIn, relTypesNamedIn } from './cypher-labels'

// The cases that matter are the ones the console actually runs plus the shapes
// that would make a pattern match lie: a label-free query must report NOTHING,
// because the caller treats "no labels named" as "cannot diagnose" rather than
// as "everything is missing".
describe('labelsNamedIn', () => {
  it('finds both ends of the depgraph preset', () => {
    const q =
      'MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) RETURN a.rel_path AS source, b.rel_path AS target LIMIT 25'
    expect(labelsNamedIn(q).sort()).toEqual(['CodeModule'])
  })

  it('reports nothing for a query that names no label', () => {
    expect(labelsNamedIn('MATCH (n) RETURN labels(n) AS labels, count(*) AS count')).toEqual([])
  })

  it('splits a multi-label pattern', () => {
    expect(labelsNamedIn('MATCH (n:Job:Uncertain) RETURN n').sort()).toEqual(['Job', 'Uncertain'])
  })

  it('finds an anonymous label', () => {
    expect(labelsNamedIn('MATCH (:DataAsset)<-[:WRITES_TO]-(x) RETURN x')).toEqual(['DataAsset'])
  })

  it('reads a label followed by a property map', () => {
    expect(labelsNamedIn("MATCH (f:ControlMFolder {name: 'x'}) RETURN f")).toEqual([
      'ControlMFolder',
    ])
  })

  it('de-duplicates repeats', () => {
    expect(labelsNamedIn('MATCH (a:X)--(b:X) RETURN a')).toEqual(['X'])
  })
})

describe('relTypesNamedIn', () => {
  it('finds the depgraph edge', () => {
    expect(relTypesNamedIn('MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) RETURN a')).toEqual([
      'IMPORTS',
    ])
  })

  it('splits an alternation', () => {
    expect(relTypesNamedIn('MATCH ()-[:READS_FROM|WRITES_TO]->() RETURN 1').sort()).toEqual([
      'READS_FROM',
      'WRITES_TO',
    ])
  })

  it('reads a variable-length hop', () => {
    expect(relTypesNamedIn('MATCH ()-[:INVOKES*1..3]->() RETURN 1')).toEqual(['INVOKES'])
  })

  it('reports nothing for an untyped relationship', () => {
    expect(relTypesNamedIn('MATCH (a)-[r]->(b) RETURN r')).toEqual([])
  })
})

describe('the regexes do not leak state between calls', () => {
  // /g regexes carry lastIndex; a shared module-level pattern that is not reset
  // returns different answers on the second call for the same input, which is
  // the kind of defect that only shows up once a second preset exists.
  it('gives the same answer twice', () => {
    const q = 'MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) RETURN a'
    expect(labelsNamedIn(q)).toEqual(labelsNamedIn(q))
    expect(relTypesNamedIn(q)).toEqual(relTypesNamedIn(q))
  })
})
