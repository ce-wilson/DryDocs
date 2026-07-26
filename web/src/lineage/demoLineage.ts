// SYNTHESIZED lineage demo — the O9/O11 fallback idiom: a source→target DAG
// shown with a visible ILLUSTRATIVE badge until the lineage live-load gate
// flips the m3_* vocabulary and curated rows exist. The shape is
// the mechanism-only data-series chain (file watcher → landing pair → zone
// hops → provisioned target); every name is synthetic (publish boundary).

export type LineageKind = 'ControlMJob' | 'EtlJob' | 'Dataset' | 'S3Stage' | 'Warehouse'

// Same token vocabulary as the Explorer demo (theme-token routed, both schemes).
export const LINEAGE_KIND_TOKEN: Record<LineageKind, string> = {
  ControlMJob: '--blue-br',
  EtlJob: '--yellow',
  Dataset: '--blue',
  S3Stage: '--green',
  Warehouse: '--teal',
}

export interface LineageSelection {
  id: string
  label: string
  kind: LineageKind
}

export interface LineageDemoNode {
  id: string
  label: string
  kind: LineageKind
  /** DataAsset-style id for deep links (/lineage/asset/:assetId); processes have none */
  assetId?: string
  x: number
  y: number
}

export interface LineageDemoEdge {
  id: string
  source: string
  target: string
  rel: 'TRIGGERS' | 'READS_FROM' | 'WRITES_TO' | 'INVOKES'
}

export const LINEAGE_NODES: readonly LineageDemoNode[] = [
  { id: 'fw', label: 'FW_LANDING_WATCH', kind: 'ControlMJob', x: 0, y: 120 },
  { id: 'landing', label: 'series_x.dat/.tok', kind: 'Dataset', assetId: 'file://landing/series_x.dat', x: 150, y: 40 },
  { id: 'ingest', label: 'ingest-launcher', kind: 'EtlJob', x: 300, y: 120 },
  { id: 'raw', label: 'RAW/series_x', kind: 'S3Stage', assetId: 's3://zone/raw/series_x', x: 450, y: 40 },
  { id: 'transform', label: 'dpl-transform', kind: 'EtlJob', x: 600, y: 120 },
  { id: 'refined', label: 'REFINED/series_x', kind: 'S3Stage', assetId: 's3://zone/refined/series_x', x: 750, y: 40 },
  { id: 'provision', label: 'dpl-provision', kind: 'EtlJob', x: 900, y: 120 },
  { id: 'mart', label: 'MART.SERIES_X', kind: 'Warehouse', assetId: 'db://mart/series_x', x: 1050, y: 40 },
]

export const LINEAGE_EDGES: readonly LineageDemoEdge[] = [
  { id: 'e1', source: 'fw', target: 'ingest', rel: 'TRIGGERS' },
  { id: 'e2', source: 'landing', target: 'ingest', rel: 'READS_FROM' },
  { id: 'e3', source: 'ingest', target: 'raw', rel: 'WRITES_TO' },
  { id: 'e4', source: 'raw', target: 'transform', rel: 'READS_FROM' },
  { id: 'e5', source: 'transform', target: 'refined', rel: 'WRITES_TO' },
  { id: 'e6', source: 'refined', target: 'provision', rel: 'READS_FROM' },
  { id: 'e7', source: 'provision', target: 'mart', rel: 'WRITES_TO' },
]

export interface DemoFrame {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  /** node id per row, for selection linking */
  nodeIds: readonly string[]
}

export const HOPS_FRAME: DemoFrame = {
  cols: ['Activity', 'Hop', 'Data asset'],
  rows: [
    ['ingest-launcher', 'READS_FROM', 'file://landing/series_x.dat'],
    ['ingest-launcher', 'WRITES_TO', 's3://zone/raw/series_x'],
    ['dpl-transform', 'READS_FROM', 's3://zone/raw/series_x'],
    ['dpl-transform', 'WRITES_TO', 's3://zone/refined/series_x'],
    ['dpl-provision', 'READS_FROM', 's3://zone/refined/series_x'],
    ['dpl-provision', 'WRITES_TO', 'db://mart/series_x'],
  ],
  nodeIds: ['ingest', 'ingest', 'transform', 'transform', 'provision', 'provision'],
}

export const ASSETS_FRAME: DemoFrame = {
  cols: ['Data asset', 'Kind', 'Writers', 'Readers'],
  rows: [
    ['file://landing/series_x.dat', 'local_file', '0', '1'],
    ['s3://zone/raw/series_x', 's3_prefix', '1', '1'],
    ['s3://zone/refined/series_x', 's3_prefix', '1', '1'],
    ['db://mart/series_x', 'db_table', '1', '0'],
  ],
  nodeIds: ['landing', 'raw', 'refined', 'mart'],
}

export const SCHEMA_FRAME: DemoFrame = {
  cols: ['Data asset', 'Kind', 'Schema level'],
  rows: [
    ['file://landing/series_x.dat', 'local_file', 'node-schema (column level lands with the MAC feed, G17)'],
    ['s3://zone/raw/series_x', 's3_prefix', 'node-schema (column level lands with the MAC feed, G17)'],
    ['s3://zone/refined/series_x', 's3_prefix', 'node-schema (column level lands with the MAC feed, G17)'],
    ['db://mart/series_x', 'db_table', 'node-schema (column level lands with the MAC feed, G17)'],
  ],
  nodeIds: ['landing', 'raw', 'refined', 'mart'],
}

export function nodeByAssetId(assetId: string): LineageDemoNode | undefined {
  return LINEAGE_NODES.find((n) => n.assetId === assetId)
}
