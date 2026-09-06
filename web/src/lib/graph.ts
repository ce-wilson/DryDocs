// The GraphAccess seam (ADR 0005): the ONLY way console code reads the graph.
// Two adapters implement it — `bolt` (lib/neo4j.ts, a DEV-MODE tool only) and
// `api` (lib/graphApi.ts, the deployment path — real once drydocs-api lands,
// backlog O5). View components import THIS interface, never neo4j-driver;
// tsc enforces adapter conformance (`satisfies GraphAccess` in each adapter).

import type { Role } from './auth'

export interface GraphResult {
  keys: string[]
  rows: Record<string, unknown>[]
}

/** A named-view result also names the database the server routed it to —
 *  the trust boundary made visible (ADR 0002: drydocs vs drydocs_all is a
 *  SERVER routing decision; the client only ever learns it after the fact). */
export interface NamedResult extends GraphResult {
  database: string
}

/** A QuerySpec run result (O11, site-plan §4): the registry echoes back the
 *  spec's contract with the rows, so the UI can render the classification
 *  banner, the SYNTHESIZED watermark, and "Copy as Cypher" without ever
 *  holding its own query definitions. */
export interface SpecResult extends GraphResult {
  spec_id: string
  database: string
  classification: string
  columns: { name: string; type: string; label: string }[]
  cypher: string
  params: Record<string, unknown>
  watermarked: boolean
  /** WEB2/API1: did the row ceiling bite? The server probes at `limit + 1` and
   *  answers this directly, so no surface has to guess from `rows.length` —
   *  which is the guess that made a 500-row extract indistinguishable from a
   *  complete one (review 2026-09-05, S1). */
  truncated: boolean
  /** The ceiling that applied, or null/absent when the spec has none. Optional
   *  because the server declares it optional; a required field here would stop
   *  `SpecRunOutCoversSpecResult` compiling. */
  limit?: number | null
  /** R4: an ephemeral (agent-registered) spec replays params frozen at
   *  registration, so its ceiling CANNOT be raised. The seam carries the
   *  server's own answer rather than letting the console re-derive it from the
   *  `eph.` id prefix — a second source of truth for a server policy is exactly
   *  what this item exists to remove. */
  ephemeral: boolean
}

/** A completed server-side export: the streamed data plus its provenance
 *  manifest (fetched from the export ledger once the stream finished). */
export interface SpecExport {
  filename: string
  blob: Blob
  manifest: Record<string, unknown>
}

/** Per-call transport options (WEB12).
 *
 * One optional bag rather than a trailing `signal` argument on four methods:
 * a deadline, a cancel and anything later (a caller-raised export ceiling —
 * API1 clause (c) — is the obvious next one) all belong to the REQUEST, not to
 * the query, and adding them positionally would rewrite every call site again.
 *
 * `signal` is honoured by the `api` adapter and ignored by `bolt`, which fails
 * loud on every method that would need it. */
export interface RequestOptions {
  signal?: AbortSignal
}

/** Export-only options (WEB2, from API1 clause (c)).
 *
 * The ceiling rides in the options bag rather than as a fifth positional
 * argument — the direction `RequestOptions` above already names. It does NOT
 * ride in `RequestOptions` itself: three of the four seam methods have no
 * ceiling to raise, and a field they would silently ignore is a worse seam than
 * one extra type. Raising a GRID read's limit would change what is on screen;
 * raising an EXPORT's changes what lands in a file that carries a manifest, and
 * the server treats those as different permissions (ExportBody). */
export interface ExportOptions extends RequestOptions {
  /** Omitted (the default) keeps the display ceiling the run already applied.
   *  The server 422s a value it will not honour — over its own ceiling, or on
   *  an ephemeral spec — and the console surfaces that message rather than
   *  holding its own copy of the rule. */
  limit?: number | null
}

export interface GraphAccess {
  readonly kind: 'bolt' | 'api'
  /** Read-only query execution. Raw Cypher is a dev/admin affordance only. */
  runRead(query: string, opts?: RequestOptions): Promise<GraphResult>
  /** Named view query (ADR 0005 decision 2): payload shaping lives server-side
   *  in drydocs-api's query registry — never duplicated in the browser. The
   *  api adapter POSTs /query/{id}; bolt has no registry and fails loud. */
  runNamed(queryId: string, params?: Record<string, unknown>, opts?: RequestOptions): Promise<NamedResult>
  /** QuerySpec run (O11): the data-frame read path. Registry results only —
   *  api adapter POSTs /specs/{id}/run; bolt fails loud (no registry). */
  runSpec(specId: string, params?: Record<string, unknown>, opts?: RequestOptions): Promise<SpecResult>
  /** Server-side export (O11 path b): re-runs the spec server-side, streams
   *  csv/jsonl, then fetches the provenance manifest for the sidecar file. */
  exportSpec(
    specId: string,
    params: Record<string, unknown>,
    format: 'csv' | 'jsonl',
    opts?: ExportOptions,
  ): Promise<SpecExport>
}

// The explicit dev flag + role gate for the bolt adapter (ADR 0005 decision 4):
// import.meta.env.DEV is baked in at build time, so production bundles have the
// bolt path unreachable BY CONSTRUCTION — no runtime toggle can re-enable it.
export function boltAllowed(role: Role): boolean {
  return import.meta.env.DEV && role === 'admin'
}
