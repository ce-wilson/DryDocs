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
  | 'software'
  | 'gates'
  | 'loads'
  | 'loadmap'
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
    // Locations (Z5, 2026-08-22): the reusable map module's first consumer.
    // It sits beside Servers deliberately — same estate, one tab answering
    // "what do we have" and the next answering "where is it".
    // 'App neighbourhood' added at O81: the NVL canvas over the same
    // explorer.folder-applications.v1 the Folders tab tables, drawn as folder →
    // application and folder → data centre. It sits directly after Folders so
    // the table and its picture are neighbours.
    tabs: [
      'Applications',
      'Folders',
      'App neighbourhood',
      'App codes',
      'Jobs',
      'Conditions',
      'Servers',
      'Locations',
    ],
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
    // Was 'ddlineage' — written by nothing, retired 2026-08-04 (ADR 0002 X1).
    backsOnto: 'drydocs',
    // O60 added 'Swimlanes': job -> pipeline -> asset across lanes, with the
    // lane BASIS as a parameter (?lanes=source-kind | ?lanes=layer) rather than
    // a constant, so a further basis is an argument and not a re-layout.
    tabs: ['Hops', 'Data assets', 'Schema definition', 'Row-level preview', 'Swimlanes'],
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
    // O61 added 'Product roll-up': which area a job or folder supports, with
    // the two join rules (framework vs app-tied) side by side.
    tabs: ['Teams', 'Attributions', 'Escalation routing', 'Product roll-up'],
    phase: 2,
  },
  {
    id: 'runbooks',
    label: 'Runbooks',
    path: '/runbooks',
    tagline: 'Data-series provisioning chain',
    backsOnto: 'runbook-automation',
    // 'Series graph' added at O81: the NVL canvas over runbooks.series.v1 —
    // the SAME reviewed spec the Series tab tables, drawn as the graph its rows
    // were flattened from. It sits beside its table rather than replacing it.
    tabs: ['Series', 'Series graph', 'Generated runbooks', 'Metadata completeness'],
    phase: 2,
  },
  {
    id: 'remediation',
    label: 'Remediation',
    path: '/remediation',
    tagline: 'Finding → fix-batch flow',
    backsOnto: 'drydocs_remediation',
    // O59 added the first three: the SME INTAKE path — read the folder-set
    // profile, read the standards findings over it, supply the substitutions
    // the XML cannot carry. They sit ahead of the O17 flow tabs because that
    // is the order the work happens in.
    tabs: [
      'Profile',
      'Standards findings',
      'Substitutions',
      'Findings',
      'Fix batches',
      'Jira handoffs',
    ],
    phase: 2,
    // FB-03, and the same argument /gates and /software carry: every number on
    // this page is a DELTA against a standard — "7/9 slots not supplied", "21
    // findings" — and an end user reading those without the standard in mind
    // reads them as breakage. The substitutions frame goes further and asks for
    // input only an SME can supply. Opening this later is a one-line change;
    // the reverse is a retraction.
    access: 'sme',
  },
  {
    id: 'docs',
    label: 'Docs',
    path: '/docs',
    tagline: 'Document → Chunk corpus map',
    backsOnto: 'docmeta',
    // O58 added 'Corpus status': the docs-verify reconciliation — which
    // declared corpus is actually loaded, and in which database. It sits with
    // /docs because that is the module that backs onto docmeta, and the answer
    // is about the corpora this page already lists.
    tabs: ['Documents', 'Chunks', 'Trust/provenance audit', 'Corpus status'],
    phase: 3,
    retrieval: 'agent', // docmeta corpus Q&A — free-input, agent-interpreted (Epic R target)
    agent: 'docmeta-qa (ADK)',

  },
  {
    id: 'software',
    label: 'Software',
    path: '/software',
    tagline: 'Vendor to product to documentation, declared vs loaded',
    backsOnto: 'software-registry.json + doc corpora (generated) · DESCRIBES in drydocs',
    tabs: ['Products', 'Vendors', 'Documentation coverage', 'Corpora', 'Acronyms'],
    phase: 3,
    // FB-03: every column worth rendering here is a DELTA — gate state,
    // declared-vs-loaded, an edge withheld pending G32. An end user reading
    // "1016 pages staged, 0 loaded" without that context reads it as breakage.
    // Same audience as /gates. Opening this later is a one-line change; the
    // reverse is a retraction.
    access: 'sme',
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
    // O57: the console consumer load-map.json never had. N4 generated the file
    // for web/ and N5 rendered docs/plan/load-map.html — a page, not a route —
    // so everything except the doc-corpus rows /software keeps went unread.
    //
    // A NEW MODULE, NOT A TAB UNDER /loads, and the reason is the backsOnto
    // column: /loads backs onto :JobRun — records of executions that happened.
    // This backs onto a generated declaration artifact and can say nothing
    // about any run. Folding it in would make one of the two backsOnto claims
    // false, and "did it load?" vs "what is registered to load?" are different
    // questions asked by people in different situations.
    id: 'loadmap',
    label: 'Load map',
    path: '/load-map',
    tagline: 'Registered sources, load order, retired ids — declared, not run',
    backsOnto: 'load-map.json (generated) · config/source-registry + the doc-ledger union',
    tabs: ['Sources', 'Systems', 'Load sequence', 'Retired ids', 'Defects'],
    phase: 3,
    // FB-03, same argument as /software: every column is governance state —
    // confirmed-or-not, ledger tier, pipeline reach, and two lists of declared
    // defects with written exemptions. An end user reading "registered only"
    // or a defect row without that context reads breakage where there is a
    // ruling. Opening this later is one line; the reverse is a retraction.
    access: 'sme',
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
