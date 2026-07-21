// SYNTHESIZED /docs demo (O18): the Document -> Chunk corpus map shape
// (llm-graph-builder pattern the bmc-docs loader writes) + fallback frames.
// The live corpus usually exists (bmc-docs load, gate-accepted 2026-07-08) —
// these fixtures appear only on an empty DB or with the api down.

import type { DagEdgeDef, DagNodeDef } from '../components/MiniDag'

export const DOCS_NODES: readonly DagNodeDef[] = [
  { id: 'doc', label: 'controlm-job-basics (VERBATIM)', sub: ':Document', token: '--blue', x: 0, y: 80 },
  { id: 'c0', label: '#0 preamble', sub: ':Chunk (FIRST_CHUNK)', token: '--green', x: 260, y: 0 },
  { id: 'c1', label: '#1 What is a job?', sub: ':Chunk', token: '--green', x: 260, y: 90 },
  { id: 'c2', label: '#2 Conditions', sub: ':Chunk', token: '--green', x: 260, y: 180 },
  { id: 'product', label: 'BMC Control-M', sub: ':SoftwareProduct (DESCRIBES)', token: '--teal', x: 520, y: 80 },
]

export const DOCS_EDGES: readonly DagEdgeDef[] = [
  { id: 'e1', source: 'doc', target: 'c0', label: 'FIRST_CHUNK' },
  { id: 'e2', source: 'c0', target: 'c1', label: 'NEXT_CHUNK' },
  { id: 'e3', source: 'c1', target: 'c2', label: 'NEXT_CHUNK' },
  { id: 'e4', source: 'doc', target: 'product', label: 'DESCRIBES' },
]

export interface DemoFrame {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  nodeIds: readonly string[]
}

export const DOCUMENTS_FRAME: DemoFrame = {
  cols: ['Document', 'Title', 'Trust tier', 'Chunks'],
  rows: [
    ['controlm-job-basics', 'Job basics', 'VERBATIM', '3'],
    ['controlm-conditions-notes', 'Conditions (notes)', 'GROUNDED', '2'],
    ['workbench-summary', 'Workbench summary', 'SYNTHESIZED', '1'],
  ],
  nodeIds: ['doc', 'doc', 'doc'],
}

export const CHUNKS_FRAME: DemoFrame = {
  cols: ['Chunk', 'Document', 'Seq', 'Trust tier'],
  rows: [
    ['controlm-job-basics#0', 'controlm-job-basics', '0', 'VERBATIM'],
    ['controlm-job-basics#1', 'controlm-job-basics', '1', 'VERBATIM'],
    ['workbench-summary#0', 'workbench-summary', '0', 'SYNTHESIZED'],
  ],
  nodeIds: ['c0', 'c1', 'c2'],
}

export const TRUST_FRAME: DemoFrame = {
  cols: ['Trust tier', 'Chunks', 'Documents'],
  rows: [
    ['VERBATIM', '3', '1'],
    ['GROUNDED', '2', '1'],
    ['SYNTHESIZED', '1', '1'],
  ],
  nodeIds: ['doc', 'doc', 'doc'],
}
