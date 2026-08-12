// SYNTHESIZED demo rows for the /mappings panes — the O9/O11 fallback idiom:
// shown with a visible notice when drydocs-api (or the graph) is unavailable
// or empty, never silently. Every value is synthetic (publish boundary — the
// wf-mapping-01 wireframe's own examples).
//
// K15 (2026-08-05): CoverageRow + DEMO_COVERAGE removed with the job-grain
// pane. They mirrored mappings.attribution-coverage.v1, a spec that read the
// edge K8 retired — a demo fixture for a retired surface is a trap, because it
// renders convincingly and describes nothing that exists.


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

// K11 — the app-code cascade pane's demo frames (synthetic values only).
// Shapes mirror the mappings.catalog-cascade.v1 / mappings.orchestrators.v1 /
// mappings.app-orchestrators.v1 / mappings.unmapped-folders.v1 spec columns.
export interface CascadeRow {
  product_line_id: string
  product_line: string
  product_id: string | null
  product: string | null
  app_id: string | null
  application: string | null
}

export interface OrchestratorRow {
  product_id: string
  product: string
}

export interface AppOrchestratorRow {
  app_id: string
  product_id: string
  product: string
  source: string // 'batch-port' (declared prefill) | 'app-code-mapping' (confirmed)
  origin: 'declared' | 'confirmed' | null
  declared_raw: string | null
}

export interface UnmappedFolderRow {
  folder_id: string
  folder: string
  app_code: string | null
  data_center: string | null
  jobs: number
  run_as_users: string
}

export const DEMO_CASCADE: readonly CascadeRow[] = [
  { product_line_id: 'PL-100', product_line: 'Synthetic Risk', product_id: 'PRD-110', product: 'Risk Mart', app_id: 'APP-1234', application: 'Synthetic Risk Mart' },
  { product_line_id: 'PL-100', product_line: 'Synthetic Risk', product_id: 'PRD-110', product: 'Risk Mart', app_id: 'APP-1235', application: 'Synthetic Risk Mart UI' },
  { product_line_id: 'PL-200', product_line: 'Synthetic Ledger', product_id: 'PRD-210', product: 'Ledger Feed', app_id: 'APP-2222', application: 'Synthetic Ledger Feed' },
  { product_line_id: 'PL-200', product_line: 'Synthetic Ledger', product_id: 'PRD-220', product: 'Ledger Archive', app_id: null, application: null },
]

export const DEMO_ORCHESTRATORS: readonly OrchestratorRow[] = [
  { product_id: 'controlm', product: 'BMC Control-M' },
  { product_id: 'autosys', product: 'Broadcom Workload Automation' },
]

export const DEMO_APP_ORCHESTRATORS: readonly AppOrchestratorRow[] = [
  { app_id: 'APP-1234', product_id: 'controlm', product: 'BMC Control-M', source: 'batch-port', origin: 'declared', declared_raw: 'Control-M' },
  { app_id: 'APP-2222', product_id: 'controlm', product: 'BMC Control-M', source: 'app-code-mapping', origin: 'confirmed', declared_raw: null },
  // mid-migration is a NORMAL state (§G3) — two orchestrators, no drift flag
  { app_id: 'APP-2222', product_id: 'autosys', product: 'Broadcom Workload Automation', source: 'batch-port', origin: 'declared', declared_raw: 'Autosys' },
]

export const DEMO_UNMAPPED_FOLDERS: readonly UnmappedFolderRow[] = [
  { folder_id: '70001', folder: 'PRARAG-DAILY', app_code: 'ARA', data_center: 'T032-E0700-DMA', jobs: 14, run_as_users: 'svc_riskbatch' },
  { folder_id: '70002', folder: 'PRARAG-MONTHLY', app_code: 'ARA', data_center: 'T032-E0700-DMA', jobs: 3, run_as_users: 'svc_riskbatch' },
  { folder_id: '70003', folder: 'PRBCDE-NIGHTLY', app_code: 'BCD', data_center: 'T045-E0600-DMB', jobs: 22, run_as_users: 'svc_ledger, svc_archive' },
  { folder_id: '70004', folder: 'PRXYZQ-WEEKLY', app_code: 'XYZ', data_center: 'T045-E0600-DMB', jobs: 5, run_as_users: 'svc_platform' },
]
