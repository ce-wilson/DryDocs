// SYNTHESIZED /remediation demo (O17): the finding -> fix-batch flow.
// Mechanism-only: drydocs_remediation writes ZERO graph (its no-graph-write
// invariant) and its outputs are file artifacts, so these frames are
// illustrative fixtures — live QuerySpecs bind only if/when a remediation
// graph shape is gate-confirmed (TDD section 6/7). Every value synthetic.

import type { DagEdgeDef, DagNodeDef } from '../components/MiniDag'

export const REMEDIATION_NODES: readonly DagNodeDef[] = [
  { id: 'finding', label: 'R1: folder name violates PRAOCG', sub: 'Finding (detector R1)', token: '--red', x: 0, y: 80 },
  { id: 'finding2', label: 'FW-really-API name/type disagreement', sub: 'Finding (principle 8)', token: '--red', x: 0, y: 190 },
  { id: 'batch', label: 'fix-batch 2026-07-XX (tier 1)', sub: 'FixBatch (transform engine)', token: '--yellow', x: 280, y: 130 },
  { id: 'package', label: 'xml before/after + change doc + mermaid', sub: 'Fix package', token: '--blue', x: 560, y: 130 },
  { id: 'jira', label: 'SYN-1234 (support → dev handoff)', sub: 'Jira handoff (SoD)', token: '--teal', x: 840, y: 130 },
]

export const REMEDIATION_EDGES: readonly DagEdgeDef[] = [
  { id: 'e1', source: 'finding', target: 'batch', label: 'batched' },
  { id: 'e2', source: 'finding2', target: 'batch', label: 'batched' },
  { id: 'e3', source: 'batch', target: 'package', label: 'transforms' },
  { id: 'e4', source: 'package', target: 'jira', label: 'handoff' },
]

export interface DemoFrame {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  nodeIds: readonly string[]
}

export const FINDINGS_FRAME: DemoFrame = {
  cols: ['Rule', 'Target', 'Severity', 'Status'],
  rows: [
    ['R1 naming (PRAOCG)', 'PRXBAD-FOLDER', 'medium', 'open'],
    ['principle 8 (FW-really-API)', 'FW_SERIESX_WATCH', 'high', 'batched'],
    ['description metadata missing', 'JOB_A_EXTRACT', 'low', 'open'],
  ],
  nodeIds: ['finding', 'finding2', 'finding'],
}

export const BATCHES_FRAME: DemoFrame = {
  cols: ['Batch', 'Tier', 'Findings', 'Status'],
  rows: [
    ['fix-batch 2026-07-XX', 'tier 1 (deterministic transform)', '2', 'package built'],
    ['fix-batch 2026-07-YY', 'tier 2 (agentic — gated on OQ-2/OQ-4)', '—', 'blocked'],
  ],
  nodeIds: ['batch', 'batch'],
}

export const JIRA_FRAME: DemoFrame = {
  cols: ['Ticket', 'Package', 'SoD', 'Status'],
  rows: [
    ['SYN-1234', 'xml before/after + change doc + mermaid + runbook', 'we analyze, dev implements', 'handed off'],
  ],
  nodeIds: ['jira'],
}
