// QuerySpec result rows -> NVL nodes and relationships (O81 step 2).
//
// THE READ BOUNDARY IS THE POINT OF THIS FILE. The canvas consumes ONLY
// drydocs-api spec results (ADR 0005): no browser-side driver, no endpoint that
// accepts Cypher, no new spec minted for a picture. That constraint is what
// makes a graph canvas safe to add at all — the server still decides every query
// that runs and which database answers it, exactly as it did for the grids.
//
// SO THE MAPPING IS A FLATTENING, RUN BACKWARDS. A spec returns ROWS, because
// that is what a registry-reviewed query returns; the graph it was drawn from is
// implied by the row shape rather than carried in it. Each mapper below states
// which pattern its spec's Cypher walked, and rebuilds exactly that — no more.
// Inventing an edge the spec did not walk would put a claim on screen that no
// reviewed query stands behind, which is the failure this file exists to avoid.
//
// NODE STYLING KEYS OFF THE EXISTING CONVENTION, not a parallel style table:
// `kind -> theme token`, the same shape (and, for the concepts they share, the
// same tokens) as demoGraph's KIND_TOKEN, demoLineage's LINEAGE_KIND_TOKEN and
// demoOwnership's OWNERSHIP_KIND_TOKEN. Components consume tokens, never raw hex
// (site-plan §2), so both themes render correctly.

// TYPE-ONLY, and deliberately so: the full-page route (O86) gates on the HOST
// module's access designation, so a surface has to name its host. A type import
// is erased at build time, which keeps this module free of a runtime edge to the
// registry — it stays a pure mapper, importable by anything.
import type { ModuleId } from '../modules/registry'

/** A row as it arrives from a spec result: column name -> value. */
export type SpecRow = Record<string, unknown>

/** Graph labels these mappers can produce. Live labels, not the demo kinds. */
export type GraphKind =
  | 'ControlMJob'
  | 'ETLProcess'
  | 'DataAsset'
  | 'BusinessApplication'
  | 'ControlMFolder'
  | 'ControlMServer'

/** kind -> theme token. Shared concepts keep the token they already had
 *  elsewhere in the console, so a job is the same blue on every surface. */
export const GRAPH_KIND_TOKEN: Record<GraphKind, string> = {
  ControlMJob: '--blue-br',
  ETLProcess: '--yellow',
  DataAsset: '--blue',
  BusinessApplication: '--green',
  ControlMFolder: '--teal',
  ControlMServer: '--red',
}

export interface CanvasNode {
  id: string
  caption: string
  kind: GraphKind
  /** Everything the row said about this node, for the detail panel. */
  properties: Record<string, string>
}

export interface CanvasRelationship {
  id: string
  from: string
  to: string
  caption: string
}

export interface CanvasGraph {
  nodes: CanvasNode[]
  relationships: CanvasRelationship[]
  /** Rows the spec returned, before any cap. */
  rowCount: number
  /** Nodes the rows described, before any cap — `nodes.length` after it. */
  nodeCount: number
  /** True when the cap dropped something. Drives the truncation notice. */
  truncated: boolean
}

/** THE CEILING IS DECLARED, not discovered when the browser stalls. NVL renders
 *  far more than this happily; the limit exists because a canvas that silently
 *  shows some of the answer is worse than one that shows less and says so. */
export const NODE_CEILING = 300

function str(value: unknown): string {
  return value === null || value === undefined ? '' : String(value)
}

/** Collect nodes/edges de-duplicated by id, then cap — dropping any edge whose
 *  endpoint the cap removed, so no relationship ever points at nothing. */
class GraphBuilder {
  private readonly nodes = new Map<string, CanvasNode>()
  private readonly rels = new Map<string, CanvasRelationship>()

  node(id: string, kind: GraphKind, caption: string, properties: Record<string, string> = {}): void {
    if (!id) return
    const existing = this.nodes.get(id)
    if (existing) {
      // Later rows may carry properties an earlier one lacked; keep the union
      // rather than the first sighting, and never overwrite a value with ''.
      for (const [k, v] of Object.entries(properties)) if (v) existing.properties[k] = v
      return
    }
    this.nodes.set(id, { id, kind, caption, properties })
  }

  rel(from: string, to: string, caption: string): void {
    if (!from || !to) return
    const id = `${from}|${caption}|${to}`
    if (!this.rels.has(id)) this.rels.set(id, { id, from, to, caption })
  }

  build(rowCount: number): CanvasGraph {
    const all = [...this.nodes.values()]
    const kept = all.slice(0, NODE_CEILING)
    const keptIds = new Set(kept.map((n) => n.id))
    return {
      nodes: kept,
      relationships: [...this.rels.values()].filter((r) => keptIds.has(r.from) && keptIds.has(r.to)),
      rowCount,
      nodeCount: all.length,
      truncated: all.length > kept.length,
    }
  }
}

/** `runbooks.series.v1` -> the data-series traversal.
 *
 *  The spec walks (j:ControlMJob)-[:INVOKES]->(e:ETLProcess), then OPTIONAL
 *  (e)-[:WRITES_TO]->(d:DataAsset) collected into `lands`. Both hops are
 *  rebuilt; nothing else is. Note INVOKES, not TRIGGERS — G89 resolved the spec
 *  onto the edge a loader may actually write, and the picture follows the spec.
 */
export function mapSeries(rows: readonly SpecRow[]): CanvasGraph {
  const b = new GraphBuilder()
  for (const row of rows) {
    const job = str(row.trigger_job)
    const process = str(row.process)
    const kind = str(row.kind)
    const jobId = `job:${job}`
    const processId = `etl:${process}`

    if (job) b.node(jobId, 'ControlMJob', job, { 'Job name': job })
    if (process) b.node(processId, 'ETLProcess', process, { Token: process, Kind: kind })
    if (job && process) b.rel(jobId, processId, 'INVOKES')

    // `lands` is a collect(); a spec that landed nothing yields [] or [null].
    const lands = Array.isArray(row.lands) ? row.lands : []
    for (const raw of lands) {
      const asset = str(raw)
      if (!asset) continue
      const assetId = `asset:${asset}`
      b.node(assetId, 'DataAsset', asset, { 'Asset id': asset })
      if (process) b.rel(processId, assetId, 'WRITES_TO')
    }
  }
  return b.build(rows.length)
}

/** `explorer.folder-applications.v1` -> the application neighbourhood.
 *
 *  The spec walks (f:ControlMFolder)-[:BELONGS_TO_APPLICATION {role:
 *  'seal_app_ref'}]->(:Port)<-[:HAS_PORT]-(a:BusinessApplication), with OPTIONAL
 *  (f)-[:SCHEDULED_ON]->(s:ControlMServer) and a job COUNT.
 *
 *  THE PORT HOP IS DELIBERATELY NOT DRAWN. The spec returns no port identity —
 *  only the application either side of it — so a :Port node here would be one
 *  this console invented, and the K7/K8 reshape put that hop under a signed
 *  gate. The folder-to-application edge is captioned for what it is, and the
 *  port's active_state rides as a property of the edge's folder end, where the
 *  row actually put it. Jobs are a COUNT, not identities, so they are a property
 *  too: drawing N job nodes from a number would be inventing them.
 */
export function mapAppNeighbourhood(rows: readonly SpecRow[]): CanvasGraph {
  const b = new GraphBuilder()
  for (const row of rows) {
    const appId = str(row.app_id)
    const app = str(row.application) || appId
    const folder = str(row.folder)
    const dc = str(row.data_center)
    const appNodeId = `app:${appId}`
    const folderId = `folder:${folder}`

    if (appId) b.node(appNodeId, 'BusinessApplication', app, { 'Application id': appId, Name: app })
    if (folder) {
      b.node(folderId, 'ControlMFolder', folder, {
        Folder: folder,
        Jobs: str(row.jobs),
        'Port state': str(row.port_state),
        Origin: str(row.origin),
      })
    }
    if (appId && folder) b.rel(folderId, appNodeId, 'BELONGS_TO_APPLICATION')
    if (dc) {
      const dcId = `server:${dc}`
      b.node(dcId, 'ControlMServer', dc, { 'Data centre': dc })
      if (folder) b.rel(folderId, dcId, 'SCHEDULED_ON')
    }
  }
  return b.build(rows.length)
}

/** The two surfaces this item ships, by spec id. A surface is a spec plus the
 *  mapper that knows which pattern that spec walked — pairing them anywhere else
 *  would let a spec be drawn by a mapper built for a different row shape. */
export const CANVAS_SURFACES = {
  'runbooks.series.v1': mapSeries,
  'explorer.folder-applications.v1': mapAppNeighbourhood,
} as const satisfies Record<string, (rows: readonly SpecRow[]) => CanvasGraph>

export type CanvasSpecId = keyof typeof CANVAS_SURFACES

/** What the full-page route needs to know about a canvas surface (O86).
 *
 *  `module` is the surface's HOST — the module whose tab renders it inline —
 *  and it is what the route gates on, so `/graph/:specId` applies whatever rule
 *  its host applies and cannot become the one page that does not check. */
export interface CanvasRoute {
  module: ModuleId
  title: string
}

/** Every canvas surface, keyed for the full-page route.
 *
 *  `satisfies Record<CanvasSpecId, ...>` is doing real work: adding a surface to
 *  CANVAS_SURFACES without a route entry here is a COMPILE ERROR, so a new canvas
 *  cannot quietly ship with no page and no gate. The whitelist the route checks
 *  is this object — an id that is not a key renders a named refusal rather than
 *  being passed through to the API (O86 clause b). */
export const CANVAS_ROUTES = {
  'runbooks.series.v1': { module: 'runbooks', title: 'Data-series provisioning graph' },
  'explorer.folder-applications.v1': {
    module: 'explorer',
    title: 'Application neighbourhood',
  },
} as const satisfies Record<CanvasSpecId, CanvasRoute>

/** Is this arbitrary string a canvas surface the route may render? */
export function isCanvasSpecId(value: string | undefined): value is CanvasSpecId {
  return value !== undefined && Object.hasOwn(CANVAS_ROUTES, value)
}

/** The path `/graph/:specId` for a surface — one place, so the anchor in a
 *  canvas header and the route that answers it cannot disagree. */
export function canvasRoutePath(specId: CanvasSpecId): string {
  return `/graph/${encodeURIComponent(specId)}`
}
