// SYNTHESIZED /loads demo runs — the fallback timeline when loads.runs.v1
// returns nothing (fresh DB) or the api is down. Shapes mirror the BaseLoader
// :JobRun envelope; every value synthetic.

export interface RunRow {
  run_id: string
  loader: string
  source: string
  started_at: string
  completed_at: string | null
  status: 'COMPLETED' | 'FAILED' | 'STARTED'
  rows_processed: number
  rows_changed: number
  rows_rejected: number
  nodes_marked_removed: number
  nodes_reactivated: number
}

export const DEMO_RUNS: readonly RunRow[] = [
  {
    run_id: 'demo-run-0004',
    loader: 'seal_attribution',
    source: 'controlm-variable-normalization',
    started_at: '2026-07-21T02:40:00',
    completed_at: '2026-07-21T02:41:12',
    status: 'COMPLETED',
    rows_processed: 17,
    rows_changed: 3,
    rows_rejected: 0,
    nodes_marked_removed: 1,
    nodes_reactivated: 0,
  },
  {
    run_id: 'demo-run-0003',
    loader: 'controlm_jobs',
    source: 'controlm-psgmgr',
    started_at: '2026-07-21T02:35:00',
    completed_at: '2026-07-21T02:37:02',
    status: 'COMPLETED',
    rows_processed: 17,
    rows_changed: 17,
    rows_rejected: 2,
    nodes_marked_removed: 0,
    nodes_reactivated: 1,
  },
  {
    run_id: 'demo-run-0002',
    loader: 'controlm_folders',
    source: 'controlm-psgmgr',
    started_at: '2026-07-21T02:30:00',
    completed_at: null,
    status: 'FAILED',
    rows_processed: 4,
    rows_changed: 0,
    rows_rejected: 4,
    nodes_marked_removed: 0,
    nodes_reactivated: 0,
  },
  {
    run_id: 'demo-run-0001',
    loader: 'bmc_docs',
    source: 'bmc-docs-corpus',
    started_at: '2026-07-21T02:20:00',
    completed_at: '2026-07-21T02:26:44',
    status: 'COMPLETED',
    rows_processed: 412,
    rows_changed: 412,
    rows_rejected: 0,
    nodes_marked_removed: 0,
    nodes_reactivated: 0,
  },
]
