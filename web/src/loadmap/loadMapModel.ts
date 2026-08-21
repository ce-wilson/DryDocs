// Derivation for /load-map (O57). PURE and DOM-free, same construction as
// software/softwareModel.ts: every partition and status decision the page makes
// lives here, so the vocabulary that must not silently change is readable in
// one place instead of spread through JSX.
//
// THE GAP THIS FILE CLOSES: N4 generated load-map.json for web/ and N5 then
// rendered docs/plan/load-map.html — a page, not a console route — so the
// JSON's console consumer was never scoped. /software (O56) is the only web/
// code that imports it at all, and it deliberately keeps the 8 `doc-registry`
// rows. Everything else in the file — the 30 registry sources, the systems,
// the retired ids, the load sequence, and BOTH defect lists — had no reader.
//
// READS THE COMMITTED JSON ONLY. It never re-derives from config/, which is
// what makes it structurally incapable of disagreeing with
// docs/plan/load-map.html: both render the same generated artifact. That page
// keeps its own audience (N5's print/PDF surface for the SME loop); this one
// is the interactive lens, and neither replaces the other.

import loadMapData from '../generated/load-map.json'

/** A source's home registry. `doc-registry` rows are /software's; the rest are ours. */
export const DOC_REGISTRY = 'doc-registry'

export interface LedgerRef {
  state: string
  path: string | null
}

export interface OntologyMappingRef {
  id: string
  status: string
  label: string
}

export interface LoaderRef {
  name: string
  class?: string
  cli_name?: string
  source_label?: string
  commands?: string[]
}

export interface LoadMapSource {
  id: string
  home: string
  system: string | null
  origin: string | null
  kind: string
  authority: string | null
  derived: boolean
  urn: string | null
  replaces: string | null
  classification: string | null
  confirmed: boolean
  ledger: LedgerRef | string | null
  taxonomy_captures: unknown[]
  ontology_mappings: OntologyMappingRef[]
  loaders: LoaderRef[]
}

export interface LoadMapSystem {
  id: string
  name: string
  layer: string | null
  classification: string | null
  taxonomy_captures: unknown[]
}

export interface RetiredId {
  id: string
  replaced_by: string[]
  reason: string
}

export interface SequenceStep {
  command: string
  mode: string
  profiles: string[]
  note: string | null
  loaders: LoaderRef[]
}

/** A loader with no registry source — a DEFECT the JSON already carries. */
export interface SourcelessLoader {
  name: string
  class: string
  reason: string
  commands: string[]
}

/** A map entry whose source is unregistered — the second declared defect. */
export interface MapEntryWithoutSource {
  id: string
  status: string
  label: string
  source: string
  exemption: string
}

const data = loadMapData as unknown as {
  note: string
  sequence: SequenceStep[]
  ad_hoc_commands: string[]
  systems: LoadMapSystem[]
  sources: LoadMapSource[]
  retired: RetiredId[]
  sourceless_loaders: SourcelessLoader[]
  map_entries_without_registry_source: MapEntryWithoutSource[]
}

export const GENERATOR_NOTE = data.note

/** Every source, both registries — the denominator the page reports against. */
export const ALL_SOURCES: LoadMapSource[] = data.sources

/**
 * The rows this page owns: everything NOT in the doc registry.
 *
 * The split is by `home`, not by kind, and that is deliberate — /software
 * filters on exactly the same key in the opposite direction, so the two pages
 * partition the file with no overlap and no gap. Changing this predicate
 * without changing softwareModel.CORPORA would make rows vanish from both.
 */
export const SOURCES: LoadMapSource[] = ALL_SOURCES.filter((s) => s.home !== DOC_REGISTRY)

/** The doc-corpus rows, counted but not tabled here — /software renders them. */
export const DOC_CORPUS_COUNT = ALL_SOURCES.length - SOURCES.length

export const SYSTEMS: LoadMapSystem[] = data.systems
export const RETIRED: RetiredId[] = data.retired
export const SEQUENCE: SequenceStep[] = data.sequence
export const AD_HOC_COMMANDS: string[] = data.ad_hoc_commands
export const SOURCELESS_LOADERS: SourcelessLoader[] = data.sourceless_loaders
export const MAP_ENTRIES_WITHOUT_SOURCE: MapEntryWithoutSource[] = data.map_entries_without_registry_source

/** Both declared defect lists, totalled for the page's defect count. */
export const DEFECT_COUNT = SOURCELESS_LOADERS.length + MAP_ENTRIES_WITHOUT_SOURCE.length

/** Source kinds present, in descending frequency — drives the kind filter. */
export const KINDS: string[] = Array.from(
  SOURCES.reduce((acc, s) => acc.set(s.kind, (acc.get(s.kind) ?? 0) + 1), new Map<string, number>()),
)
  .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  .map(([kind]) => kind)

/** Distinct systems referenced by the source rows (not the systems table). */
export const SYSTEM_IDS: string[] = Array.from(new Set(SOURCES.map((s) => s.system).filter(Boolean) as string[])).sort()

/** Ledger state as a display string — the shape varies (object or bare string). */
export function ledgerState(ledger: LoadMapSource['ledger']): string {
  if (!ledger) return '—'
  return typeof ledger === 'string' ? ledger : ledger.state
}

/** Ledger path, when the entry carries one. */
export function ledgerPath(ledger: LoadMapSource['ledger']): string | null {
  return !ledger || typeof ledger === 'string' ? null : ledger.path
}

/**
 * How far a source has been taken through the pipeline.
 *
 * NOT a health score. Each stage is a declared fact from the registries, and a
 * source that legitimately stops early (a reference table nothing loads) is
 * not broken — which is why this returns the stages reached rather than a
 * pass/fail, and why the page labels the column "pipeline reach".
 */
export interface PipelineReach {
  captured: boolean
  mapped: boolean
  loaded: boolean
  label: string
}

export function pipelineReach(s: LoadMapSource): PipelineReach {
  const captured = s.taxonomy_captures.length > 0
  const mapped = s.ontology_mappings.length > 0
  const loaded = s.loaders.length > 0
  const reached = [captured && 'taxonomy', mapped && 'ontology', loaded && 'load'].filter(Boolean) as string[]
  return { captured, mapped, loaded, label: reached.length ? reached.join(' → ') : 'registered only' }
}

/** Every loader named anywhere in the sequence, de-duplicated by cli name. */
export function sequenceLoaderCount(): number {
  const names = new Set<string>()
  for (const step of SEQUENCE) for (const l of step.loaders) names.add(l.cli_name ?? l.name)
  return names.size
}
