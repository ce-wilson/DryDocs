// SYNTHESIZED /runbooks demo (O17): the data-series provisioning chain
// (FileWatcher -> RAW -> ING -> LD, the controlm-runbook-automation series
// shape) plus fallback frames. Mechanism-only — live series data is
// company-side; every name synthetic.

import type { DagEdgeDef, DagNodeDef } from '../components/MiniDag'

export const RUNBOOK_NODES: readonly DagNodeDef[] = [
  { id: 'fw', label: 'FW_SERIESX_WATCH', sub: 'FileWatcher job', token: '--blue-br', x: 0, y: 80 },
  { id: 'raw', label: 'RAW_SERIESX_LOAD', sub: 'RAW landing job', token: '--yellow', x: 210, y: 80 },
  { id: 'raw-asset', label: 'stage.RAW_SERIES_X', sub: 'landing table', token: '--green', x: 420, y: 10 },
  { id: 'ing', label: 'ING_SERIESX_CONFORM', sub: 'ING conform job', token: '--yellow', x: 420, y: 150 },
  { id: 'ld', label: 'LD_SERIESX_PROVISION', sub: 'LD provisioning job', token: '--yellow', x: 640, y: 80 },
  { id: 'mart', label: 'MART.SERIES_X', sub: 'provisioned target', token: '--teal', x: 860, y: 80 },
]

export const RUNBOOK_EDGES: readonly DagEdgeDef[] = [
  { id: 'e1', source: 'fw', target: 'raw', label: 'condition' },
  { id: 'e2', source: 'raw', target: 'raw-asset', label: 'WRITES_TO' },
  { id: 'e3', source: 'raw', target: 'ing', label: 'condition' },
  { id: 'e4', source: 'ing', target: 'ld', label: 'condition' },
  { id: 'e5', source: 'ld', target: 'mart', label: 'WRITES_TO' },
]

export interface DemoFrame {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  nodeIds: readonly string[]
}

export const SERIES_FRAME: DemoFrame = {
  cols: ['Series', 'Trigger job', 'Chain', 'Provisioned target'],
  rows: [
    ['series_x', 'FW_SERIESX_WATCH', 'FW → RAW → ING → LD', 'MART.SERIES_X'],
    ['series_y', 'FW_SERIESY_WATCH', 'FW → RAW → ING → LD', 'MART.SERIES_Y'],
  ],
  nodeIds: ['fw', 'fw'],
}

// These rows reference REAL repo artifacts (mechanism, not company data) —
// the runbooks this repo has actually generated/authored.
export const GENERATED_FRAME: DemoFrame = {
  cols: ['Runbook', 'Source', 'Status'],
  rows: [
    ['drydocs-startup-refresh-runbook', 'docs/design/ (L8 outline, Rev 2 SME-signed)', 'published'],
    ['runbook-mapping-demo', 'docs/runbook-mapping-demo.md (free-form; L14 refit pending)', 'pre-outline'],
  ],
  nodeIds: ['ld', 'ld'],
}

export const COMPLETENESS_FRAME: DemoFrame = {
  cols: ['Folder', 'Job', 'Description metadata'],
  rows: [
    ['PRARAG-DAILY', 'JOB_A_EXTRACT', 'missing'],
    ['PRARAG-DAILY', 'JOB_B_TRANSFORM', 'present'],
    ['PRBCDE-NIGHTLY', 'JOB_C_LOAD', 'missing'],
  ],
  nodeIds: ['raw', 'ing', 'ld'],
}
