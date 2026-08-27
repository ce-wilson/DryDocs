// Derivation for /software. PURE and DOM-free on purpose: every status decision
// the page makes lives here, so the vocabulary that must not silently change is
// in one readable place rather than spread through JSX.
//
// THE DOMAIN FACT THIS FILE EXISTS TO GET RIGHT: the only software<->docs edge is
// (:Document)-[:DESCRIBES]->(:SoftwareProduct). It is ACTIVE and loaded for
// exactly one product. A corpus declaring a database the console cannot read is
// absent BY TOPOLOGY, not by defect — so this file never lets a "0" stand for a
// database that was never queried.
//
// `drydocs docs-coverage` (drydocs/docs_coverage.py) is the authoritative
// multi-database version of the same join; a QuerySpec is single-database by
// construction, so the page is a lens and the CLI is the reconciliation.

import softwareData from '../generated/software-registry.json'
import loadMapData from '../generated/load-map.json'

// Databases a QuerySpec can read (drydocs_api.query_specs.SPEC_DATABASES).
// `dddocs` is deliberately absent: schema/provisioning never creates it, which
// is the open topology question G32 exists to rule on.
export const QUERYABLE_DATABASES = new Set(['drydocs']) // G102 (2026-08-18): the fold — ddcontext/ddall retired; the uncertain realm is the :Uncertain label
export const REGISTRY_DB = 'drydocs'

export interface VendorIconDef {
  id: string
  label: string
  kind: string | null
  category: string | null
  hex: string | null
  verified: boolean
  asset: string
  source: string
  // OPTIONAL on-dark variant — present only for marks that ship an official
  // pair (React today). Null means the single `asset` reads on both grounds.
  asset_dark?: string | null
  source_dark?: string | null
}

export interface Vendor {
  id: string
  name: string
  publisher_url: string | null
  icon: VendorIconDef | null
}

export interface DocumentationBlock {
  corpus: string
  docs_version?: string
  current_for?: string[]
  available_versions?: { version: string; path?: string; access?: string; enumerable?: boolean }[]
}

export interface Product {
  id: string
  vendor: string
  name: string
  category: string | null
  role: string | null
  type: string | null
  versions: string[]
  used_by_drydocs: boolean
  documentation: DocumentationBlock | null
  stack: string[]
}

export interface Corpus {
  id: string
  classification: string | null
  confirmed: boolean
  ledger: { state: string; path: string | null } | string
  tier: string | null
  curation: string | null
  connector: string | null
  target_db: string | null
  trust_default: string | null
  graph_locator: { match?: string; value?: string } | null
  taxonomy_path: string | null
  loaders: { cli_name?: string; name?: string }[]
  ontology_mappings: unknown[]
}

export const VENDORS = softwareData.vendors as Vendor[]
export const PRODUCTS = softwareData.products as Product[]
export const VENDORS_WITHOUT_ICONS = (softwareData.vendors_without_icons ?? []) as string[]
/** One glossary entry. Provenance is STRUCTURED (O68 clause d) — `source` and
 *  `added` are required in config/taxonomy/software-registry.yaml and guarded
 *  Python-side, so no row can render without saying where it came from. */
export interface Acronym {
  term: string
  expansion: string
  source: string
  added: string
  note: string | null
}

/** Term-sorted by the renderer — the file's order is the contract, not ours. */
export const ACRONYMS = (softwareData.acronyms ?? []) as Acronym[]
export const DRYDOCS_APPLICATION_ID = softwareData.drydocs_application_id as string | undefined

export const CORPORA = (loadMapData.sources as unknown as (Corpus & { home?: string })[]).filter(
  (s) => s.home === 'doc-registry',
)

const CORPUS_BY_ID = new Map(CORPORA.map((c) => [c.id, c]))

/** Vendor id -> vendor, for the product table's icon cell. */
export const VENDOR_BY_ID = new Map(VENDORS.map((v) => [v.id, v]))

/**
 * What kind of relationship DryDocs has to a product.
 *
 * `used_by_drydocs` is true for BOTH neo4j (we are built on it) and controlm
 * (we ingest FROM it). Rendering that one boolean conflates them, so the page
 * renders this instead.
 */
export function relationship(p: Product): string {
  if (!p.used_by_drydocs) return 'registered — not used'
  if (p.stack.includes('source')) return 'ingested from'
  if (p.stack.length) return `built on (${p.stack.join(', ')})`
  return 'used'
}

/** Whether the console is ENTITLED to report a document count for a corpus. */
export function isQueryable(targetDb: string | null | undefined): boolean {
  return !!targetDb && QUERYABLE_DATABASES.has(targetDb)
}

export type EdgeState =
  | 'withheld-cross-db'
  | 'no-corpus'
  | 'unregistered-corpus'
  | 'possible'

/**
 * Whether a DESCRIBES edge is even POSSIBLE for this product — which is a
 * DECLARATION question, decided without touching the graph, exactly as
 * `drydocs docs-coverage`'s layer 1 decides it.
 *
 * Kept SEPARATE from gate state on purpose: a corpus can be both gate-blocked
 * AND permanently edge-less, and a single chip would imply that signing the
 * gate produces coverage. It will not — `vendor_docs.cypher` writes no
 * DESCRIBES edge at all, deliberately.
 */
export function edgeState(p: Product): EdgeState {
  const corpusId = p.documentation?.corpus
  if (!corpusId) return 'no-corpus'
  const corpus = CORPUS_BY_ID.get(corpusId)
  if (!corpus) return 'unregistered-corpus'
  if (corpus.target_db && corpus.target_db !== REGISTRY_DB) return 'withheld-cross-db'
  return 'possible'
}

export function gateState(p: Product): 'confirmed' | 'awaiting gate' | 'n/a' {
  const corpus = p.documentation?.corpus ? CORPUS_BY_ID.get(p.documentation.corpus) : undefined
  if (!corpus) return 'n/a'
  return corpus.confirmed ? 'confirmed' : 'awaiting gate'
}

/** Q16 currency. `current_for` is a HUMAN assertion — never derived here. */
export function currency(p: Product): { label: string; drifted: boolean } {
  const doc = p.documentation
  if (!doc) return { label: 'no docs', drifted: false }
  if (!doc.docs_version) return { label: 'unverified', drifted: false }
  const confirmed = doc.current_for ?? []
  if (!confirmed.length) {
    return { label: `${doc.docs_version} docs · current_for: [] (unverified)`, drifted: false }
  }
  const missing = p.versions.filter((v) => !confirmed.includes(v))
  if (!missing.length) return { label: `${doc.docs_version} docs · current`, drifted: false }
  return { label: `${doc.docs_version} docs · not confirmed for ${missing.join(', ')}`, drifted: true }
}

export function corpusOf(p: Product): Corpus | undefined {
  return p.documentation?.corpus ? CORPUS_BY_ID.get(p.documentation.corpus) : undefined
}

/**
 * The in-graph cell. Returns a STRING when the console is not entitled to a
 * number — never 0, which would be a false claim of absence.
 */
export function inGraphLabel(
  p: Product,
  live: Map<string, number> | null,
): { text: string; numeric: boolean } {
  const corpus = corpusOf(p)
  if (corpus && !isQueryable(corpus.target_db)) {
    // Post-G102 this branch should be UNREACHABLE: the fold put every corpus in
    // the one spec-readable database. It is kept as a belt for a row that misses
    // a future re-target — with honest wording, not the retired G32 label.
    return { text: `not queried — ${corpus.target_db} is not spec-readable`, numeric: false }
  }
  if (!live) return { text: 'not queried', numeric: false }
  return { text: String(live.get(p.id) ?? 0), numeric: true }
}

/** Corpora that no product's `documentation.corpus` names. */
export function unclaimedCorpora(): Corpus[] {
  const declared = new Set(
    PRODUCTS.map((p) => p.documentation?.corpus).filter((c): c is string => !!c),
  )
  return CORPORA.filter((c) => !declared.has(c.id))
}

export const COVERAGE_STATS = {
  products: PRODUCTS.length,
  vendors: VENDORS.length,
  vendorsWithIcons: VENDORS.filter((v) => v.icon).length,
  corpora: CORPORA.length,
  corporaAwaitingGate: CORPORA.filter((c) => !c.confirmed).length,
  productsWithDocs: PRODUCTS.filter((p) => p.documentation).length,
}
