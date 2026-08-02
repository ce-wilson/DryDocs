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
  app_id: string | null
  application: string | null
  // match_method KEEPS the source's own vocabulary — 'seal' | 'fid' | 'app_name' |
  // 'alias' | 'manual' (drydocs/loaders/seal_attribution.py MATCH_METHOD_BY_TIER).
  // Gate business-application-identity §B2(ii): identity takes a neutral name, but
  // evidence records what another system literally wrote. A sweep that renamed these
  // alongside seal_id would be a misapplication of the same rule.
  match_method: string | null
  status: 'resolved' | 'unresolved' | 'conflict'
}

// O24 seal-contact-override grid rows (mirror of v_seal_contact_grid: the
// SEAL source value and the user override arrive as ADJACENT origin-flagged
// rows, source first). Synthetic values only.
export interface OverrideGridRow {
  app_id: string
  role_name: string
  origin: 'source' | 'override'
  holder_sid: string | null
  holder_name: string | null
  rationale: string | null
  authored_by: string | null
  authored_on: string | null
  status: 'active' | 'corrected-in-seal'
}

export const DEMO_OVERRIDE_GRID: readonly OverrideGridRow[] = [
  { app_id: 'APP-1234', role_name: 'L2 Operate Manager', origin: 'source', holder_sid: 'U111111', holder_name: null, rationale: null, authored_by: null, authored_on: null, status: 'active' },
  { app_id: 'APP-1234', role_name: 'L2 Operate Manager', origin: 'override', holder_sid: 'U222222', holder_name: 'Sam Steward', rationale: 'person left the team', authored_by: 'kchen2190', authored_on: '2026-07-21', status: 'active' },
  { app_id: 'APP-2222', role_name: 'L1 Operate Manager', origin: 'override', holder_sid: 'U333333', holder_name: null, rationale: 'role unassigned in SEAL', authored_by: 'kchen2190', authored_on: '2026-07-21', status: 'active' },
]

export const DEMO_COVERAGE: readonly CoverageRow[] = [
  {
    folder: 'PRARAG-DAILY',
    job: 'JOB_A_EXTRACT',
    folder_id: '161015',
    job_id: '7',
    app_id: null,
    application: null,
    match_method: null,
    status: 'unresolved',
  },
  {
    folder: 'PRBCDE-NIGHTLY',
    job: 'JOB_C_LOAD',
    folder_id: '161020',
    job_id: '3',
    app_id: null,
    application: null,
    match_method: null,
    status: 'unresolved',
  },
  {
    folder: 'PRBCDE-NIGHTLY',
    job: 'JOB_D_PUBLISH',
    folder_id: '161020',
    job_id: '4',
    app_id: 'APP-2222',
    application: 'Synthetic Ledger Feed',
    match_method: 'alias',
    status: 'conflict',
  },
  {
    folder: 'PRARAG-DAILY',
    job: 'JOB_B_TRANSFORM',
    folder_id: '161015',
    job_id: '8',
    app_id: 'APP-1234',
    application: 'Synthetic Risk Mart',
    // 'seal_var' until 2026-08-01 (S3): this fixture invented a value the graph never
    // writes. The real tier vocabulary is seal | fid | app_name | alias | manual.
    match_method: 'seal',
    status: 'resolved',
  },
  {
    folder: 'PRXYZQ-WEEKLY',
    job: 'JOB_E_ARCHIVE',
    folder_id: '160501',
    job_id: '12',
    app_id: 'APP-1234',
    application: 'Synthetic Risk Mart',
    match_method: 'app_name',
    status: 'resolved',
  },
]
