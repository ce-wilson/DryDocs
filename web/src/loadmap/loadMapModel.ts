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
// the retired ids, the load sequence, and ALL FOUR defect lists (two at O57,
// two more at G80) — had no reader.
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

/** A `type` and not an `interface`, deliberately: an interface has no implicit
 *  index signature, so `LoadMapSource` did not satisfy `Record<string, unknown>`
 *  and the page's four table-view calls each carried a double cast to get past
 *  that. The alias satisfies it, and the casts are gone (WEB6). */
export type LoadMapSource = {
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
  class_facts: ClassFacts
}

export interface LoadMapSystem {
  id: string
  name: string
  layer: string | null
  classification: string | null
  /** N26: the business-application axis — the id and its STATE
   *  (`placeholder` on every committed row today, D1). */
  application_id: string | null
  application_id_state: 'absent' | 'placeholder' | 'declared'
  dataset_count: number
  taxonomy_captures: unknown[]
}

/** N26 — what the registry DERIVES about a dataset (drydocs_core.registry_view),
 *  never a stored field: the system's BDAT layer, the category, the acquisition
 *  block flattened, the replica predicate with its corroboration, and the ruled
 *  ontology class or UNCLASSIFIED. */
export interface OntologyClass {
  relationships: string[]
  state: 'classified' | 'UNCLASSIFIED'
  classes: string[]
  pending: number
  reason: string | null
}

export interface ReplicaState {
  state: 'replica' | 'replica-uncorroborated' | 'ads-without-distinct-origin' | 'original'
  origin: string | null
  carrier: string | null
  corroboration: string | null
}

export interface ClassFacts {
  layer: string | null
  taxonomy_category: string | null
  acquisition: {
    mode: string
    via: string | null
    format: string | null
    drop_dir: string | null
    drop_dir_base: string | null
  }
  replica: ReplicaState
  ontology_class: OntologyClass
}

/** N26 — the class-organized view: layer → system (application) → ontology class → datasets. */
export interface ClassViewDataset {
  id: string
  taxonomy_category: string | null
  acquisition_mode: string
  authority: string | null
  replica: ReplicaState['state']
  confirmed: boolean
  loader_count: number
  ontology_class: OntologyClass
}

export interface ClassViewSystem {
  system: string | null
  name: string | null
  application_id: string | null
  application_id_state: 'absent' | 'placeholder' | 'declared'
  dataset_count: number
  classes: { ontology_class: string; datasets: ClassViewDataset[] }[]
}

export interface ClassView {
  /** `asset_type` measured across the rows — a constant is not a classification. */
  asset_type: { field: string; constant: boolean; value: string | null; rows: number; of: number }
  layers: { layer: string; systems: ClassViewSystem[] }[]
}

/** N26 — BDAT layer x taxonomy_category; `displaced` is the derivable odd row. */
export interface LayerCategoryMatrix {
  layers: string[]
  categories: string[]
  cells: Record<string, Record<string, string[]>>
  singletons: { layer: string; category: string; dataset: string }[]
  displaced: { layer: string; category: string; dataset: string; home_layer: string; home_rows: number }[]
}

/** N26 (g) — content identity of the render's inputs: git blob ids and one digest. */
export interface Provenance {
  inputs: { path: string; blob: string }[]
  digest: string
  how_to_resolve: string
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
  /** LOADER NAMES, not LoaderRefs — the two `loaders` keys in load-map.json
   *  carry different shapes and this is the string one. `render_load_map.py`
   *  writes `[cls.name for cls in COMMAND_LOADERS[step.command]]` here and full
   *  rows under `sources[].loaders`.
   *
   *  It was declared `LoaderRef[]` until WEB6, and the file-wide double cast is
   *  what let that through: the two readers of this field asked each string for
   *  `.cli_name ?? .name` and got undefined, so /load-map's sequence table
   *  rendered its loader column as bare commas while docs/plan/load-map.html —
   *  generated from the same JSON by the same script — rendered the names, and
   *  sequenceLoaderCount() answered 1 for 27 loaders. Measured, not inferred. */
  loaders: string[]
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

/**
 * A LOADER_REGISTRY loader no declared command runs — reachable only ad hoc
 * via `drydocs load <name>` (G80). `reason` null means the suite is failing:
 * unexcused silence is exactly what cli.unchained_loaders() turns red on.
 */
export interface UnchainedLoader {
  name: string
  class: string
  loader: string
  reason: string | null
}

/**
 * A chain step whose declared bundled input is not committed with the repo
 * (G80, G78's other half). An `exemption` is a per-machine build on record
 * (the generated SEAL fixtures); null means a real run would fail at preflight.
 */
export interface StepWithUncommittedInput {
  command: string
  step: string
  file: string
  searched: string
  exemption: string | null
}

const data = loadMapData as {
  note: string
  sequence: SequenceStep[]
  ad_hoc_commands: string[]
  systems: LoadMapSystem[]
  sources: LoadMapSource[]
  retired: RetiredId[]
  sourceless_loaders: SourcelessLoader[]
  map_entries_without_registry_source: MapEntryWithoutSource[]
  unchained_loaders: UnchainedLoader[]
  steps_with_uncommitted_inputs: StepWithUncommittedInput[]
  class_view: ClassView
  layer_category_matrix: LayerCategoryMatrix
  provenance: Provenance
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
export const UNCHAINED_LOADERS: UnchainedLoader[] = data.unchained_loaders
export const STEPS_WITH_UNCOMMITTED_INPUTS: StepWithUncommittedInput[] = data.steps_with_uncommitted_inputs
/** N26 — the class-organized view, the layer x category matrix, and the inputs stamp. */
export const CLASS_VIEW: ClassView = data.class_view
export const LAYER_CATEGORY_MATRIX: LayerCategoryMatrix = data.layer_category_matrix
export const PROVENANCE: Provenance = data.provenance

/** All four declared defect lists, totalled for the page's defect count. */
export const DEFECT_COUNT =
  SOURCELESS_LOADERS.length +
  MAP_ENTRIES_WITHOUT_SOURCE.length +
  UNCHAINED_LOADERS.length +
  STEPS_WITH_UNCOMMITTED_INPUTS.length

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

/** Every loader named anywhere in the sequence, de-duplicated by name. */
export function sequenceLoaderCount(): number {
  const names = new Set<string>()
  for (const step of SEQUENCE) for (const name of step.loaders) names.add(name)
  return names.size
}

// ---- O90: the wiring key ---------------------------------------------------
//
// TWO AXES THE REGISTRY ALREADY RECORDS SEPARATELY, CROSSED. `confirmed` says a
// gate has ruled the source's MEANING; a non-empty `loaders` says something is
// BUILT that writes it. They are independent, and the census proves it rather
// than assuming it: every one of the four cells is occupied, and the lone
// built-but-unconfirmed row is the subject of its own backlog item (Q24).
//
// THIS REPORTS; IT DOES NOT RULE. A registry FIELD asserting pipeline-wiring
// readiness as a first-class disposition is gate territory, and that gate is
// drafted and unsigned (N10, config/gate-prompts/registry-wiring-readiness.yaml)
// — its census found `confirmed: false` splits three ways with the distinction
// living only in YAML comments. Nothing here adds, derives or persists such a
// field: it crosses two booleans that are already in the committed artifact. If
// the gate later signs a real wiring field, this reads that instead — a better
// input, not a rewrite.
//
// FOUR CELLS, NOT TWO. "Wired or planned" is two words for four states, and
// flattening them is the exact conflation N10 exists to end, so each cell says
// what is true of it.

export type WiringStateId = 'wired' | 'planned' | 'awaiting-gate' | 'registered'

export interface WiringState {
  id: WiringStateId
  /** The cell's own claim — never a grade. */
  label: string
  /** Theme token; the chip paints text and border with it (DL-3). */
  token: '--green' | '--yellow' | '--blue-br' | '--muted'
  /** What is true of a source in this cell, in one sentence. */
  meaning: string
}

export const WIRING_STATES: readonly WiringState[] = [
  {
    id: 'wired',
    label: 'wired',
    token: '--green',
    meaning: 'a gate ruled its meaning and a loader is built',
  },
  {
    id: 'planned',
    label: 'planned',
    token: '--yellow',
    meaning: 'a gate ruled its meaning; nothing is built yet',
  },
  {
    id: 'awaiting-gate',
    label: 'built, awaiting gate',
    token: '--blue-br',
    meaning: 'a loader is built; no gate has ruled its meaning',
  },
  {
    id: 'registered',
    label: 'registered',
    token: '--muted',
    meaning: 'declared in the registry; neither ruled nor built',
  },
]

const BY_ID = new Map(WIRING_STATES.map((s) => [s.id, s]))

/** Cross `confirmed` with loader presence. Pure function of the committed row. */
export function wiringState(s: LoadMapSource): WiringState {
  const built = s.loaders.length > 0
  const id: WiringStateId = s.confirmed
    ? built
      ? 'wired'
      : 'planned'
    : built
      ? 'awaiting-gate'
      : 'registered'
  return BY_ID.get(id)!
}

/** The live census, counted from the data — never a number typed into a component. */
export function wiringCensus(sources: readonly LoadMapSource[] = ALL_SOURCES): Record<WiringStateId, number> {
  const out: Record<WiringStateId, number> = { wired: 0, planned: 0, 'awaiting-gate': 0, registered: 0 }
  for (const s of sources) out[wiringState(s).id] += 1
  return out
}
