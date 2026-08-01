// The module registry — ONE array driving both the aside nav and the Overview
// radial-hub spokes (wf-landing-01 annotation 1: "spoke click and nav click are
// the same route... adding a module = one registry entry, zero layout edits").
// Order here is nav top-to-bottom (site-plan §3 table) and also the spoke order
// used by OverviewRoute (wf-landing-01 annotation 2: clockwise from 12 o'clock).

export type ModuleId =
  | 'explorer'
  | 'ask'
  | 'lineage'
  | 'ownership'
  | 'runbooks'
  | 'remediation'
  | 'docs'
  | 'gates'
  | 'loads'
  | 'underhood'
  // admin surfaces reuse the shared template (ModuleDef shape) but are NOT
  // nav modules/spokes — deliberately absent from MODULES below (O12).
  | 'admin-config'

export interface ModuleDef {
  id: ModuleId
  label: string
  path: string
  /** graph pane one-liner shown on the Overview spoke + the module template's empty state */
  tagline: string
  /** which database/system this module backs onto (site-plan §3 "Backs onto" column) */
  backsOnto: string
  /** data-frame tab labels, in order (site-plan §3 "Data frames" column) */
  tabs: readonly string[]
  /** P0/P1/P2/P3 build phase (site-plan §3 "Phase" column) */
  phase: 1 | 2 | 3
  /** Page designation (FB-2026-07-29-03): who the page is FOR.
      'all' (default) | 'sme' (steward + admin) | 'admin'. Display/nav gating
      only under mock auth — server enforcement arrives with the O1 ADR. */
  access?: 'all' | 'sme' | 'admin'
  /** Retrieval character: 'deterministic' (QuerySpec-backed; default) vs
      'agent' (free-input, agent-interpreted — the non-deterministic modules
      the /admin/agent-test harness exposes). */
  retrieval?: 'deterministic' | 'agent'
  /** Agent identity shown by the agent-test harness (only for retrieval:'agent'). */
  agent?: string
}

/** FB-03 access check, one place: 'sme' admits steward+admin; 'admin' admits admin. */
export function canAccessModule(access: ModuleDef['access'], role: 'user' | 'steward' | 'admin'): boolean {
  if (!access || access === 'all') return true
  if (access === 'sme') return role === 'steward' || role === 'admin'
  return role === 'admin'
}

export const MODULES: readonly ModuleDef[] = [
  {
    id: 'explorer',
    label: 'Explorer',
    path: '/explorer',
    tagline: 'Tower / app drill-down graph',
    backsOnto: 'drydocs',
    // Folders + App codes added 2026-07-21 (SME corrections): the
    // ControlMFolder -> BusinessApplication crosswalk and the Control-M
    // APPLICATION-code mapping-pattern view (dedicated code vs shared
    // platform code) — the SME mapping surface needed soonest. Site-plan §3
    // listed four tabs; these are the reviewed additions.
    tabs: ['Applications', 'Folders', 'App codes', 'Jobs', 'Conditions', 'Servers'],
    phase: 1,
    retrieval: 'agent', // graph-nav Q&A over the drydocs graph (Epic R router target)
    agent: 'graph-qa (ADK)',

  },
  {
    // R5 (ADR 0007): the Ask spoke — the agentic Q&A surface for every
    // persona. Free-input by definition, hence retrieval:'agent'; the page
    // itself never writes (O20) and never submits raw Cypher (R4 ephemeral
    // refs ride the /specs paths).
    id: 'ask',
    label: 'Ask',
    path: '/ask',
    tagline: 'Free-text Q&A with every Cypher inspectable',
    backsOnto: 'graph_qa (ADK) → drydocs',
    tabs: ['Ask'],
    phase: 3,
    retrieval: 'agent',
    agent: 'graph_qa (ADK)',
  },
  {
    id: 'lineage',
    label: 'Lineage',
    path: '/lineage',
    tagline: 'Source → target DAG',
    // G30 ruling 2026-07-26: curated lineage lands in `drydocs` (ADR 0002 D1/D2).
    // Was 'ddlineage' — provisioned, but written by nothing.
    backsOnto: 'drydocs',
    tabs: ['Hops', 'Data assets', 'Schema definition', 'Row-level preview'],
    phase: 1,
  },
  {
    id: 'ownership',
    label: 'Ownership',
    path: '/ownership',
    tagline: 'SEAL → PAT → team rollup',
    backsOnto: 'seal-attribution',
    // 'Memberships' -> 'Attributions' at O15: K4 replaced the membership
    // scheme with qualified Attribution nodes (the tab tracks the model).
    tabs: ['Teams', 'Attributions', 'Escalation routing'],
    phase: 2,
  },
  {
    id: 'runbooks',
    label: 'Runbooks',
    path: '/runbooks',
    tagline: 'Data-series provisioning chain',
    backsOnto: 'runbook-automation',
    tabs: ['Series', 'Generated runbooks', 'Metadata completeness'],
    phase: 2,
  },
  {
    id: 'remediation',
    label: 'Remediation',
    path: '/remediation',
    tagline: 'Finding → fix-batch flow',
    backsOnto: 'drydocs_remediation',
    tabs: ['Findings', 'Fix batches', 'Jira handoffs'],
    phase: 2,
  },
  {
    id: 'docs',
    label: 'Docs',
    path: '/docs',
    tagline: 'Document → Chunk corpus map',
    backsOnto: 'docmeta',
    tabs: ['Documents', 'Chunks', 'Trust/provenance audit'],
    phase: 3,
    retrieval: 'agent', // docmeta corpus Q&A — free-input, agent-interpreted (Epic R target)
    agent: 'docmeta-qa (ADK)',

  },
  {
    id: 'gates',
    label: 'Gates',
    path: '/gates',
    tagline: 'Gate dependency graph',
    backsOnto: 'HITL/review',
    tabs: ['Open gates', 'Signed off', 'Gate log'],
    phase: 3,
    access: 'sme', // FB-03: gate reviews are the SME's surface

  },
  {
    id: 'loads',
    label: 'Loads',
    path: '/loads',
    tagline: 'Loader → JobRun timeline',
    backsOnto: "BaseLoader :JobRuns",
    tabs: ['Runs', 'Rejects', 'Drift/coverage', 'Status'],
    phase: 2,
  },
  {
    id: 'underhood',
    label: 'Under the Hood',
    path: '/under-the-hood',
    tagline: '12/12 traversal vs manifest/full-text — the retrieval benchmark',
    backsOnto: 'docmeta P0 benchmark (fixture)',
    // bespoke page (UnderTheHoodRoute), not a ModuleTemplate instantiation —
    // tabs/backsOnto kept for ModuleDef shape consistency (Aside nav, spoke
    // registry) even though this route renders its own layout, per its own
    // ModuleToolbar breadcrumb (like AssetPathRoute).
    tabs: ['Scoreboard', 'Strategies', 'Token tracker'],
    phase: 1,
    access: 'sme', // FB-03: benchmark showcase — SME/admin audience, not end users

  },
]

export function moduleByPath(pathname: string): ModuleDef | undefined {
  return MODULES.find((m) => pathname === m.path || pathname.startsWith(`${m.path}/`))
}
