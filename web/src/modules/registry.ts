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
    // 'App neighborhood' added at O81: the NVL canvas over the same
    // explorer.folder-applications.v1 the Folders tab tables, drawn as folder →
    // application and folder → data center. It sits directly after Folders so
    // the table and its picture are neighbours.
    tabs: [
      'Applications',
      'Folders',
      'App neighborhood',
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

// ── WEB3: route authorization derives from THIS file ────────────────────────
//
// Before WEB3 authorization had two expressions. canAccessModule() drove the
// nav (Aside), the Overview spokes and the canvas host gate, while App.tsx
// restated `persona.role === 'steward' || persona.role === 'admin'` inline six
// times. That divergence had already shipped one bug: O59 set /remediation's
// registry access to 'sme', which hid the nav entry and left the route
// reachable by typing the URL — a module was hidden and open at the same time.
// The fix chosen then was to duplicate the predicate at the route, which is why
// the next module added with access 'sme' would have reproduced it exactly.
//
// So the gate is now derived, and it is derived ONE level up from the routes:
// App.tsx wraps every route in a single pathless gate that asks this file what
// the current path requires. A new module cannot be added un-gated, because
// nobody has to remember to gate it — there is no per-route predicate left to
// forget.

/** A route-gated surface that is NOT a nav module or an Overview spoke.
 *
 * The `admin-config` ModuleId above already establishes the category (O12:
 * "admin surfaces reuse the shared template but are NOT nav modules"). These
 * carry the SAME `access` vocabulary and go through the SAME canAccessModule,
 * so being off the nav never means being off the check. */
export interface GatedSurface {
  path: string
  access: NonNullable<ModuleDef['access']>
  /** why this surface is gated — the sentence a future reader needs */
  why: string
}

export const GATED_SURFACES: readonly GatedSurface[] = [
  {
    path: '/mappings',
    access: 'sme',
    why: 'O13: the mapping WRITE surface — drafts, changeset promotion, corrections. The server enforces the same boundary on /mappings/*; steward still has no /console.',
  },
  {
    path: '/admin/config',
    access: 'admin',
    why: 'O12: the traceability lens — admin persona only.',
  },
  {
    path: '/console',
    access: 'admin',
    why: 'ADR 0005: the raw-Cypher sandbox. Admin only, and deliberately NOT opened to steward.',
  },
  {
    path: '/lab/salt-poc',
    access: 'sme',
    why: 'Idea-192 research PoC: /load-map re-skinned with Salt DS. Same access as the page it mirrors, and gated so its lazy chunk (the Salt stack) ships to no one who cannot open /load-map.',
  },
]

/** Paths whose gate is deliberately NOT expressible in the `access` vocabulary.
 *
 * `/intake` admits the SME PERSONA (`?as=neo`) as well as steward and admin, so
 * its check is `canAccessIntake(persona)` in lib/auth.ts and it keeps its own
 * route-level gate. `access` is a role vocabulary and this is a persona-scoped
 * grant; widening the vocabulary to hold both is the ADR the item nominates
 * ("route authorization derives from the module registry", whose ADR-sized part
 * is exactly how persona-scoped and role-scoped gates share one vocabulary).
 * Listed here rather than left silent so the exception is a declaration and not
 * an omission — and so the both-directions test below can assert it is the ONLY
 * one. */
export const PERSONA_SCOPED_PATHS: readonly string[] = ['/intake']

/** The access a path requires, or undefined when nothing gates it.
 *
 * Modules match by prefix (so `/lineage/asset/x` inherits `/lineage`), which is
 * `moduleByPath`'s rule and the reason a deep link cannot slip past a gate its
 * parent route carries. */
export function accessForPath(pathname: string): ModuleDef['access'] | undefined {
  const surface = GATED_SURFACES.find(
    (s) => pathname === s.path || pathname.startsWith(`${s.path}/`),
  )
  if (surface) return surface.access
  return moduleByPath(pathname)?.access
}

/** May this role open this path? The single question App.tsx asks. */
export function canAccessPath(pathname: string, role: 'user' | 'steward' | 'admin'): boolean {
  return canAccessModule(accessForPath(pathname), role)
}
