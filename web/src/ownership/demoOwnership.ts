// SYNTHESIZED ownership rollup demo (O15) — the K4 qualified-attribution
// shape rendered illustratively until the graph carries live rows: the
// acceptance chain CatalogLOB → ProductLine → Product → AreaProduct /
// DevTeam / BusinessApplication, plus Attribution nodes (attribution_id key, TOMRole
// crosswalk) with one unmapped_role=true example VISIBLY flagged — never
// hidden (the K4 rule). All names synthetic (publish boundary).

export type OwnershipKind =
  | 'CatalogLOB'
  | 'ProductLine'
  | 'Product'
  | 'AreaProduct'
  | 'DevTeam'
  | 'BusinessApplication'
  | 'Attribution'
  | 'TOMRole'

export const OWNERSHIP_KIND_TOKEN: Record<OwnershipKind, string> = {
  CatalogLOB: '--red',
  ProductLine: '--yellow',
  Product: '--yellow',
  AreaProduct: '--teal',
  DevTeam: '--green',
  BusinessApplication: '--blue',
  Attribution: '--blue-br',
  TOMRole: '--faint',
}

export interface OwnershipSelection {
  id: string
  label: string
  kind: OwnershipKind
}

export interface OwnershipDemoNode {
  id: string
  label: string
  kind: OwnershipKind
  /** unmapped_role=true Attribution — rendered flagged, never hidden */
  unmapped?: boolean
  x: number
  y: number
}

export const OWNERSHIP_NODES: readonly OwnershipDemoNode[] = [
  { id: 'lob', label: 'LOB-R (synthetic)', kind: 'CatalogLOB', x: 0, y: 100 },
  { id: 'pline', label: 'Ledger Services (line)', kind: 'ProductLine', x: 185, y: 100 },
  { id: 'product', label: 'Ledger Analytics', kind: 'Product', x: 380, y: 100 },
  { id: 'area', label: 'Data Platforms (ToT)', kind: 'AreaProduct', x: 570, y: 100 },
  { id: 'team', label: 'Team Nightowl', kind: 'DevTeam', x: 760, y: 100 },
  { id: 'app', label: 'APP-1234 · Synthetic Risk Mart', kind: 'BusinessApplication', x: 960, y: 100 },
  { id: 'att1', label: 'APP-1234|SEAL|L2 Operate Manager|SID9001', kind: 'Attribution', x: 1180, y: 20 },
  { id: 'att2', label: 'APP-1234|SEAL|Chaos Wrangler|SID9002', kind: 'Attribution', unmapped: true, x: 1180, y: 130 },
  { id: 'tom', label: 'operate_manager (L2)', kind: 'TOMRole', x: 1400, y: 20 },
]

export interface OwnershipDemoEdge {
  id: string
  source: string
  target: string
  rel: string
  /** rendering hint: 'rtl' edges point AGAINST the left→right chain layout
   *  (real vocabulary direction, e.g. DevTeam -SUPPORTS-> AreaProduct) */
  dir?: 'rtl'
}

// Relationship types, directions, and statuses mirror
// drydocs_core/schema/schema_graph.cypher EXACTLY (2026-07-21 SME correction:
// mock data may invent VALUES, never relationship semantics — the earlier
// HAS_PRODUCT-from-LOB / ALIGNED / DEVELOPS edges were invented and are gone).
// Per-scenario ruling of the rollup shape = backlog O23 (HITL gate).
export const OWNERSHIP_EDGES: readonly OwnershipDemoEdge[] = [
  { id: 'e1', source: 'lob', target: 'pline', rel: 'HAS_PRODUCT_LINE' },
  { id: 'e2', source: 'pline', target: 'product', rel: 'HAS_PRODUCT' },
  { id: 'e3', source: 'product', target: 'area', rel: 'HAS_AREA_PRODUCT (planned)' },
  { id: 'e4', source: 'team', target: 'area', rel: 'SUPPORTS', dir: 'rtl' },
  { id: 'e5', source: 'app', target: 'team', rel: 'WAS_ATTRIBUTED_TO (developed_by)', dir: 'rtl' },
  { id: 'e6', source: 'app', target: 'att1', rel: 'QUALIFIED_ATTRIBUTION' },
  { id: 'e7', source: 'app', target: 'att2', rel: 'QUALIFIED_ATTRIBUTION' },
  { id: 'e8', source: 'att1', target: 'tom', rel: 'HAD_ROLE' },
]

export interface DemoFrame {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  nodeIds: readonly string[]
}

export const TEAMS_FRAME: DemoFrame = {
  cols: ['Team id', 'Team', 'Applications'],
  rows: [
    ['T-77', 'Team Nightowl', '2'],
    ['T-78', 'Team Daybreak', '1'],
    ['T-79', 'Team Lanternfish', '0'],
  ],
  nodeIds: ['team', 'team', 'team'],
}

export const ATTRIBUTIONS_FRAME: DemoFrame = {
  cols: ['SEAL id', 'Source role', 'TOM role', 'Level', 'Unmapped?', 'Holder SID'],
  rows: [
    ['APP-1234', 'Chaos Wrangler', '—', '—', 'TRUE — needs crosswalk', 'SID9002'],
    ['APP-1234', 'L2 Operate Manager', 'operate_manager', 'L2', 'false', 'SID9001'],
    ['APP-2222', 'Design Authority', 'design_authority', '—', 'false', 'SID9003'],
  ],
  nodeIds: ['att2', 'att1', 'app'],
}

export const ESCALATION_FRAME: DemoFrame = {
  cols: ['Group id', 'Group'],
  rows: [
    ['SNG-100', 'SYN-APP-SUPPORT-L2'],
    ['SNG-101', 'SYN-DATA-PLATFORM-OPS'],
  ],
  nodeIds: ['team', 'team'],
}
