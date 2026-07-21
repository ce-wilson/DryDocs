// Explorer demo model (O9) — a typed view over the SYNTHESIZED tower dataset
// (data/towers.ts, EXAMPLE DATA · ILLUSTRATIVE). Node identity is stable
// (`<towerKey>:<index>`) so the graph pane, the data frames, and the node
// inspector can share ONE selection store (acceptance: node click filters rows,
// row select highlights the node). Colors are NOT the stored demo hex — every
// kind maps to a theme token so both themes render correctly.

import { TOWERS, TOWER_KEYS, MY_APPS_ROLLUP, type TowerKey } from '../data/towers'

export type NodeKind =
  | 'Tower'
  | 'EtlJob'
  | 'ControlMJob'
  | 'Dataset'
  | 'S3Stage'
  | 'Warehouse'
  | 'Platform'
  | 'Application'

/** kind → theme token (site-plan §2: components consume tokens, never raw hex) */
export const KIND_TOKEN: Record<NodeKind, string> = {
  Tower: '--red',
  EtlJob: '--yellow',
  ControlMJob: '--blue-br',
  Dataset: '--blue',
  S3Stage: '--green',
  Warehouse: '--teal',
  Platform: '--yellow',
  Application: '--green',
}

export interface DemoNode {
  id: string
  tower: TowerKey
  label: string
  kind: NodeKind
}

export interface DemoEdge {
  id: string
  source: string
  target: string
  rel: string
}

export interface Selection {
  id: string
  label: string
  kind: NodeKind
  tower: TowerKey
}

export function towerNodes(tower: TowerKey): DemoNode[] {
  return TOWERS[tower].graph.nodes.map((n, i) => ({
    id: `${tower}:${i}`,
    tower,
    label: n.label,
    kind: n.sub as NodeKind,
  }))
}

export function towerEdges(tower: TowerKey): DemoEdge[] {
  return TOWERS[tower].graph.edges.map(([s, t, rel], i) => ({
    id: `${tower}:e${i}`,
    source: `${tower}:${s}`,
    target: `${tower}:${t}`,
    rel,
  }))
}

export function nodeById(id: string): DemoNode | undefined {
  const [tower] = id.split(':')
  if (!(tower in TOWERS)) return undefined
  return towerNodes(tower as TowerKey).find((n) => n.id === id)
}

export interface Connection {
  rel: string
  dir: 'out' | 'in'
  other: DemoNode
}

/** in/out connections of a node, for the inspector's connections list */
export function connectionsOf(sel: Selection): Connection[] {
  const nodes = towerNodes(sel.tower)
  return towerEdges(sel.tower).flatMap((e): Connection[] => {
    if (e.source === sel.id) {
      const other = nodes.find((n) => n.id === e.target)
      return other ? [{ rel: e.rel, dir: 'out', other }] : []
    }
    if (e.target === sel.id) {
      const other = nodes.find((n) => n.id === e.source)
      return other ? [{ rel: e.rel, dir: 'in', other }] : []
    }
    return []
  })
}

// ── Data-frame rows (Explorer tabs: Applications · Jobs · Conditions · Servers)
// Every row carries the tower it belongs to (selection filters by tower) and,
// where the row IS a graph node, that node's id (row select → node highlight).

export interface FrameRow {
  cells: string[]
  tower: TowerKey | null
  nodeId?: string
}

const ETL_ENGINE: Record<TowerKey, string> = {
  home: 'Informatica',
  auto: 'PySpark',
  cards: 'Ab Initio',
  shared: '—',
}

export const APPLICATIONS_FRAME = {
  cols: ['Name', 'Kind', 'Products', 'Teams'],
  rows: [
    ...TOWER_KEYS.map((k): FrameRow => {
      const t = TOWERS[k]
      return {
        cells: [t.title, 'Tower', t.stats[0]?.[0] ?? '—', t.stats[1]?.[0] ?? '—'],
        tower: k,
        nodeId: `${k}:0`,
      }
    }),
    ...MY_APPS_ROLLUP.nodes.slice(1).map(
      (n): FrameRow => ({
        cells: [n.label, 'Application', '—', '—'],
        tower: 'home', // the rollup demo hangs off Home Lending Technology
      }),
    ),
  ],
}

export const JOBS_FRAME = {
  cols: ['Job', 'Type', 'Engine', 'Tower'],
  rows: TOWER_KEYS.flatMap((k) =>
    towerNodes(k)
      .filter((n) => n.kind === 'EtlJob' || n.kind === 'ControlMJob')
      .map(
        (n): FrameRow => ({
          cells: [n.label, n.kind, n.kind === 'EtlJob' ? ETL_ENGINE[k] : 'Control-M', TOWERS[k].title],
          tower: k,
          nodeId: n.id,
        }),
      ),
  ),
}

// Synthesized Control-M-style conditions referencing the demo jobs (no real
// condition names — mechanism only).
export const CONDITIONS_FRAME = {
  cols: ['Condition', 'Direction', 'Job', 'Tower'],
  rows: [
    { cells: ['HL-APP-EXTRACT-OK', 'out', 'm_app_approval', 'Home Lending'], tower: 'home' as TowerKey, nodeId: 'home:1' },
    { cells: ['HL-APP-EXTRACT-OK', 'in', 'HL_DLY_LOAD', 'Home Lending'], tower: 'home' as TowerKey, nodeId: 'home:5' },
    { cells: ['AUTO-INV-READY', 'out', 'prod_inventory', 'Auto'], tower: 'auto' as TowerKey, nodeId: 'auto:1' },
    { cells: ['CARDS-TXN-OK', 'out', 'Txn_ETL', 'Credit Cards'], tower: 'cards' as TowerKey, nodeId: 'cards:1' },
    { cells: ['CARDS-TXN-OK', 'in', 'prod_inventory', 'Auto'], tower: 'auto' as TowerKey, nodeId: 'auto:1' },
    { cells: ['SHR-CATALOG-SYNC', 'out', 'HL_DLY_LOAD', 'Shared Services'], tower: 'shared' as TowerKey, nodeId: 'shared:5' },
  ] as FrameRow[],
}

// Fictional folder -> application crosswalk rows (mechanism only): the demo
// twin of explorer.folder-applications.v1 (ControlMFolder -> CONTAINS_JOB ->
// WAS_ASSOCIATED_WITH {seal_app_ref} -> BusinessApplication, with the
// SCHEDULED_ON data center).
export const FOLDERS_FRAME = {
  cols: ['Folder', 'Data center', 'SEAL id', 'Application', 'Jobs'],
  rows: [
    { cells: ['DEMO-HL-DAILY', 'CTM-DEMO-EAST', 'ccb-hl-app-02', 'Servicing Core', '2'], tower: 'home' as TowerKey, nodeId: 'home:5' },
    { cells: ['DEMO-AUTO-INV', 'CTM-DEMO-WEST', 'ccb-hl-app-03', 'Portfolio Analytics', '1'], tower: 'auto' as TowerKey, nodeId: 'auto:1' },
    { cells: ['DEMO-CARDS-TXN', 'CTM-DEMO-WEST', 'ccb-hl-app-01', 'Origination Workbench', '1'], tower: 'cards' as TowerKey, nodeId: 'cards:1' },
    { cells: ['DEMO-SHR-CATALOG', 'CTM-DEMO-EAST', '—', '(unattributed — work queue)', '1'], tower: 'shared' as TowerKey, nodeId: 'shared:1' },
  ] as FrameRow[],
}

// Fictional scheduler hosts (mechanism only — no real server names).
export const SERVERS_FRAME = {
  cols: ['Server', 'Data center', 'Serves', 'Jobs'],
  rows: [
    { cells: ['CTM-DEMO-EAST', 'DC East (demo)', 'Home Lending · Shared Services', '2'], tower: 'home' as TowerKey, nodeId: 'home:5' },
    { cells: ['CTM-DEMO-WEST', 'DC West (demo)', 'Auto · Credit Cards', '2'], tower: 'auto' as TowerKey },
    { cells: ['CTM-DEMO-DR', 'DR site (demo)', 'standby', '0'], tower: null },
  ] as FrameRow[],
}
