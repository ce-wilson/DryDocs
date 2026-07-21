// SYNTHESIZED demo rows for the /mappings coverage grid — the O9/O11 fallback
// idiom: shown with a visible notice when drydocs-api (or the graph) is
// unavailable or empty, never silently. Shapes mirror the
// mappings.attribution-coverage.v1 spec columns; every value is synthetic
// (publish boundary — the wf-mapping-01 wireframe's own examples).

export interface CoverageRow {
  folder: string
  job: string
  folder_id: string
  job_id: string
  seal_id: string | null
  application: string | null
  match_method: string | null
  status: 'resolved' | 'unresolved' | 'conflict'
}

export const DEMO_COVERAGE: readonly CoverageRow[] = [
  {
    folder: 'PRARAG-DAILY',
    job: 'JOB_A_EXTRACT',
    folder_id: '161015',
    job_id: '7',
    seal_id: null,
    application: null,
    match_method: null,
    status: 'unresolved',
  },
  {
    folder: 'PRBCDE-NIGHTLY',
    job: 'JOB_C_LOAD',
    folder_id: '161020',
    job_id: '3',
    seal_id: null,
    application: null,
    match_method: null,
    status: 'unresolved',
  },
  {
    folder: 'PRBCDE-NIGHTLY',
    job: 'JOB_D_PUBLISH',
    folder_id: '161020',
    job_id: '4',
    seal_id: 'APP-2222',
    application: 'Synthetic Ledger Feed',
    match_method: 'alias',
    status: 'conflict',
  },
  {
    folder: 'PRARAG-DAILY',
    job: 'JOB_B_TRANSFORM',
    folder_id: '161015',
    job_id: '8',
    seal_id: 'APP-1234',
    application: 'Synthetic Risk Mart',
    match_method: 'seal_var',
    status: 'resolved',
  },
  {
    folder: 'PRXYZQ-WEEKLY',
    job: 'JOB_E_ARCHIVE',
    folder_id: '160501',
    job_id: '12',
    seal_id: 'APP-1234',
    application: 'Synthetic Risk Mart',
    match_method: 'app_name',
    status: 'resolved',
  },
]
