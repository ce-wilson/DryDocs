// Support-user asset search (2026-07-21, from chat): "why hasn't this table
// loaded" / "who supports this file or table". The search is deliberately
// NARROWED — Product → Application dropdowns scope the inventory BEFORE the
// partial-name match, so a support user is never string-searching all assets.
// SYNTHESIZED demo inventory (the SpecGrid demo-first idiom); the live twin is
// a future inventory QuerySpec + the runbooks.app-path.v1 path spec
// (UI-WIP/wf-runbook-path-01.md).

export interface AssetProduct {
  id: string
  label: string
}

export interface AssetApp {
  id: string // seal-style demo id
  label: string
  productId: string
}

export interface InventoryAsset {
  id: string
  name: string
  kind: 'file' | 'table'
  appId: string
  /** which node in the demo path graph this asset IS (highlight + anchor) */
  nodeId: string
  support: { team: string; queue: string; hours: string }
  load: { state: 'LATE' | 'OK' | 'RUNNING'; expectedBy: string; lastLoaded: string; blocking: string }
}

export const PRODUCTS: readonly AssetProduct[] = [
  { id: 'prod-hl', label: 'Home Lending' },
  { id: 'prod-auto', label: 'Auto' },
  { id: 'prod-cards', label: 'Credit Cards' },
]

export const APPS: readonly AssetApp[] = [
  { id: 'ccb-hl-app-01', label: 'HL-1 · Origination Workbench', productId: 'prod-hl' },
  { id: 'ccb-hl-app-02', label: 'HL-2 · Servicing Core', productId: 'prod-hl' },
  { id: 'ccb-hl-app-03', label: 'HL-3 · Portfolio Analytics', productId: 'prod-hl' },
  { id: 'ccb-au-app-01', label: 'AU-1 · Auto Inventory', productId: 'prod-auto' },
  { id: 'ccb-cc-app-01', label: 'CC-1 · Card Transactions', productId: 'prod-cards' },
]

const HL_SUPPORT = { team: 'HL Batch Support (demo)', queue: 'DEMO-HL-BATCH', hours: '24×5 + Sat AM' }
const SVC_SUPPORT = { team: 'Servicing Platform (demo)', queue: 'DEMO-SVC-CORE', hours: 'business hours' }

export const ASSETS: readonly InventoryAsset[] = [
  {
    id: 'a-pricing-dat',
    name: 'pricing_approval_$BUSINESS_DATE.dat',
    kind: 'file',
    appId: 'ccb-hl-app-01',
    nodeId: 'file',
    support: HL_SUPPORT,
    load: { state: 'LATE', expectedBy: '06:00 EST', lastLoaded: 'yesterday 05:52', blocking: 'cond HL-EXTRACT-OK not posted' },
  },
  {
    id: 'a-intake-dat',
    name: 'hl_app_intake_$BUSINESS_DATE.dat',
    kind: 'file',
    appId: 'ccb-hl-app-01',
    nodeId: 'file',
    support: HL_SUPPORT,
    load: { state: 'OK', expectedBy: '05:00 EST', lastLoaded: 'today 04:41', blocking: '—' },
  },
  {
    id: 'a-app-pipeline',
    name: 'STG_MORTGAGE.APP_PIPELINE',
    kind: 'table',
    appId: 'ccb-hl-app-01',
    nodeId: 'ds',
    support: HL_SUPPORT,
    load: { state: 'LATE', expectedBy: '06:30 EST', lastLoaded: 'yesterday 06:18', blocking: 'upstream hl_daily_extract not ended OK' },
  },
  {
    id: 'a-svc-vw',
    name: 'SERVICING_CORE_VW',
    kind: 'table',
    appId: 'ccb-hl-app-02',
    nodeId: 'vw',
    support: SVC_SUPPORT,
    load: { state: 'LATE', expectedBy: '07:00 EST', lastLoaded: 'yesterday 06:44', blocking: 'FEEDS from app_pipeline stale' },
  },
  {
    id: 'a-payments',
    name: 'SVC_CORE.PAYMENTS_DAILY',
    kind: 'table',
    appId: 'ccb-hl-app-02',
    nodeId: 'vw',
    support: SVC_SUPPORT,
    load: { state: 'OK', expectedBy: '06:00 EST', lastLoaded: 'today 05:37', blocking: '—' },
  },
  {
    id: 'a-boarding-dat',
    name: 'svc_boarding_$BUSINESS_DATE.dat',
    kind: 'file',
    appId: 'ccb-hl-app-02',
    nodeId: 'file',
    support: SVC_SUPPORT,
    load: { state: 'RUNNING', expectedBy: '09:00 EST', lastLoaded: 'in flight', blocking: '—' },
  },
  {
    id: 'a-risk-mart',
    name: 'PORT_ANALYTICS.RISK_MART',
    kind: 'table',
    appId: 'ccb-hl-app-03',
    nodeId: 'vw',
    support: SVC_SUPPORT,
    load: { state: 'OK', expectedBy: '08:00 EST', lastLoaded: 'today 07:12', blocking: '—' },
  },
  {
    id: 'a-inv-feed',
    name: 'auto_inventory_feed.dat',
    kind: 'file',
    appId: 'ccb-au-app-01',
    nodeId: 'file',
    support: HL_SUPPORT,
    load: { state: 'OK', expectedBy: '05:30 EST', lastLoaded: 'today 05:02', blocking: '—' },
  },
  {
    id: 'a-txn-daily',
    name: 'CARDS.TXN_DAILY',
    kind: 'table',
    appId: 'ccb-cc-app-01',
    nodeId: 'ds',
    support: HL_SUPPORT,
    load: { state: 'OK', expectedBy: '04:30 EST', lastLoaded: 'today 04:07', blocking: '—' },
  },
]

export function assetById(id: string): InventoryAsset | undefined {
  return ASSETS.find((a) => a.id === id)
}

export function appById(id: string): AssetApp | undefined {
  return APPS.find((a) => a.id === id)
}

/** Narrowed search: scope first (product → app → kind), THEN partial-name. */
export function searchAssets(opts: {
  productId?: string
  appId?: string
  kind?: 'file' | 'table' | ''
  needle: string
}): InventoryAsset[] {
  const needle = opts.needle.trim().toLowerCase()
  return ASSETS.filter((a) => {
    if (opts.appId && a.appId !== opts.appId) return false
    if (!opts.appId && opts.productId && appById(a.appId)?.productId !== opts.productId) return false
    if (opts.kind && a.kind !== opts.kind) return false
    if (needle && !a.name.toLowerCase().includes(needle)) return false
    return true
  })
}

// ── The demo path graph the asset sub-page renders (wf-runbook-path-01 made
// real): two lanes, expandable hidden neighbors, removable non-anchor nodes.

export type PathLane = 'tech' | 'data'

export interface PathNode {
  id: string
  label: string
  sub: string
  lane: PathLane
  /** theme token for the border (kind color) */
  token: string
  x: number
  y: number
  /** hidden until a neighbor expands it (the neo4j-browser feel) */
  hidden?: boolean
  /** anchors (source/target apps) cannot be removed */
  anchor?: boolean
  runbook?: { action: string; verify: string }
}

export interface PathEdge {
  id: string
  source: string
  target: string
  label: string
}

export const PATH_NODES: readonly PathNode[] = [
  { id: 'hl1', label: 'HL-1', sub: 'BusinessApplication', lane: 'tech', token: '--red', x: 0, y: 90, anchor: true },
  { id: 'f1', label: 'DEMO-HL-EXTRACT', sub: 'ControlMFolder', lane: 'tech', token: '--blue-br', x: 190, y: 90 },
  {
    id: 'j1', label: 'hl_daily_extract', sub: 'ControlMJob', lane: 'tech', token: '--yellow', x: 400, y: 90,
    runbook: { action: 'Check status; rerun from DEMO-HL-EXTRACT if failed', verify: 'ended OK' },
  },
  {
    id: 'cond', label: 'HL-EXTRACT-OK', sub: 'Condition', lane: 'tech', token: '--yellow', x: 610, y: 0, hidden: true,
    runbook: { action: 'Confirm the out-condition posted (job→job handoff)', verify: 'condition present' },
  },
  {
    id: 'j2', label: 'hl_core_load', sub: 'ControlMJob', lane: 'tech', token: '--yellow', x: 620, y: 90,
    runbook: { action: 'Check downstream load in DEMO-HL-CORE', verify: 'ended OK' },
  },
  { id: 'f2', label: 'DEMO-HL-CORE', sub: 'ControlMFolder', lane: 'tech', token: '--blue-br', x: 830, y: 90 },
  { id: 'hl2', label: 'HL-2', sub: 'BusinessApplication', lane: 'tech', token: '--red', x: 1040, y: 90, anchor: true },
  { id: 'repo', label: 'hl-extract-etl', sub: 'GitRepo · DEMO-HL', lane: 'tech', token: '--teal', x: 400, y: -30, hidden: true },
  { id: 'route', label: 'NEP-DEMO-rt', sub: 'TransferRoute', lane: 'data', token: '--teal', x: 160, y: 310, hidden: true },
  {
    id: 'file', label: 'pricing_approval_$DATE.dat', sub: 'File · provenance 0.2', lane: 'data', token: '--green', x: 400, y: 310,
    runbook: { action: 'Confirm arrival in the managed-transfer drop', verify: 'file watcher OK' },
  },
  { id: 'stg', label: 'stg_mortgage', sub: 'S3Stage', lane: 'data', token: '--green', x: 400, y: 430, hidden: true },
  { id: 'ds', label: 'app_pipeline', sub: 'Dataset', lane: 'data', token: '--blue', x: 660, y: 310 },
  {
    id: 'vw', label: 'SERVICING_CORE_VW', sub: 'View', lane: 'data', token: '--teal', x: 880, y: 310,
    runbook: { action: 'Freshness check before HL-2 business hours', verify: 'refreshed today' },
  },
]

export const PATH_EDGES: readonly PathEdge[] = [
  { id: 'e1', source: 'hl1', target: 'f1', label: 'OWNS' },
  { id: 'e2', source: 'f1', target: 'j1', label: 'CONTAINS_JOB' },
  { id: 'e3', source: 'j1', target: 'j2', label: 'cond HL-EXTRACT-OK' },
  { id: 'e3a', source: 'j1', target: 'cond', label: 'POSTS' },
  { id: 'e3b', source: 'cond', target: 'j2', label: 'RELEASES' },
  { id: 'e4', source: 'f2', target: 'j2', label: 'CONTAINS_JOB' },
  { id: 'e5', source: 'hl2', target: 'f2', label: 'OWNS' },
  { id: 'e6', source: 'repo', target: 'j1', label: 'CODE_SOURCED' },
  { id: 'e7', source: 'j1', target: 'file', label: 'WRITES' },
  { id: 'e8', source: 'route', target: 'file', label: 'ROUTES' },
  { id: 'e9', source: 'file', target: 'stg', label: 'LANDS_IN' },
  { id: 'e10', source: 'stg', target: 'ds', label: 'LOADS' },
  { id: 'e11', source: 'file', target: 'ds', label: 'LOADS (via stage)' },
  { id: 'e12', source: 'ds', target: 'vw', label: 'FEEDS' },
  { id: 'e13', source: 'vw', target: 'hl2', label: 'READ_BY' },
]

/** ids visible on first render (the SHORTEST-path spine; hidden = expandable context) */
export function initialVisible(): Set<string> {
  return new Set(PATH_NODES.filter((n) => !n.hidden).map((n) => n.id))
}

/** hidden neighbors of `id` that an Expand reveals */
export function expandable(id: string, visible: Set<string>): string[] {
  return PATH_EDGES.filter((e) => e.source === id || e.target === id)
    .map((e) => (e.source === id ? e.target : e.source))
    .filter((n) => !visible.has(n))
}

/** the assumed path-spec cypher, needle-bound like SpecGrid's Copy-as-Cypher */
export function pathCypher(needle: string): string {
  return (
    `// QuerySpec runbooks.app-path.v1 (assumed contract — read-only)\n` +
    `MATCH p = SHORTEST 1 (a:BusinessApplication {seal_id: $source})\n` +
    `  -[]-+(fn) WHERE fn.file_name CONTAINS $needle OR fn.table_name CONTAINS $needle\n` +
    `RETURN p\n` +
    `// $needle = '${needle}'  · classic fallback: shortestPath((a)-[*..12]-(b))`
  )
}
