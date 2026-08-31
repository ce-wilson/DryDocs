// Which lane does a thing belong in? (O60)
//
// LANE BASIS IS A PARAMETER, NOT A CONSTANT — the item's amendment, and the
// reason this file exists at all. A swimlane view has two separable questions:
// how to LAY OUT lanes, and which lane each thing goes in. Fusing them is what
// makes a second basis a rewrite. Here the layout is the view's job and the
// assignment is ONE function per basis, so adding a basis is a new argument and
// never a re-layout.
//
// TWO BASES TODAY, and they answer different questions over different data:
//
//   'source-kind'  the WF-DFL wireframe's three lanes — Control-M | Data Layer |
//                  File Server / Database — over the job -> pipeline -> asset
//                  demo graph.
//   'layer'        the BDAT layer (business | data | technology | human) over
//                  REGISTRY entities, read from the generated load-map.
//
// THE WORD "LAYER" IS OVERLOADED IN THIS REPO AND THE VIEW MUST NOT MERGE THE
// SENSES. Three different axes use these words:
//   1. the BDAT layer on source-registry SYSTEM rows — what 'layer' below means;
//   2. the relationship vocabulary's `human` DOMAIN, which its own header rules
//      is "a file/loader PARTITION — not rdfs:domain and not the BDAT layer on
//      source-registry SYSTEM rows" (gate vocabulary-domains-and-id-policy §A3);
//   3. rdfs:domain, which from_node/to_node carry.
// Each basis therefore states its axis in `axisNote`, and the view renders it.
//
// A LAYER LANE GROUPS BY CARRIER, NOT BY SUBJECT, for as long as `layer` is a
// SYSTEM field — an extract inherits the layer of the database it was pulled
// through. That is why the two People & Org datasets land in different lanes.
// Idea-216 rules on moving or deriving it; this view does not wait on that,
// because making the skew VISIBLE is the point. Said on the surface, not only
// here.

import loadMap from '../generated/load-map.json'

export type LaneBasisId = 'source-kind' | 'layer'

export interface LaneDef {
  id: string
  label: string
  /** Rendered when the lane is declared but holds nothing. */
  emptyNote?: string
  /** Wireframe region key for the LANE ITSELF (the source-kind lanes are
   *  WF-DFL-02..04). The BDAT lanes have no wireframe — that basis postdates
   *  it — and carry none rather than borrowing one. */
  wf?: string
}

export interface LaneItem {
  id: string
  label: string
  sub: string
  lane: string
  /** Wireframe region key, so SME feedback re-attaches (FB-2026-08-13-01). */
  wf?: string
}

export interface LaneBasis {
  id: LaneBasisId
  label: string
  /** WHICH AXIS this basis means. Rendered on the surface — see the note above. */
  axisNote: string
  lanes: LaneDef[]
  items: LaneItem[]
  /** Rendered under the lanes when the basis has a caveat a reader must know. */
  caveat?: string
}

// --------------------------------------------------------------------------- //
// basis 1 — the WF-DFL source-kind lanes
// --------------------------------------------------------------------------- //

export const SOURCE_KIND_LANES: LaneDef[] = [
  { id: 'controlm', label: 'Control-M', wf: 'WF-DFL-02' },
  { id: 'data-layer', label: 'Data Layer', wf: 'WF-DFL-03' },
  { id: 'file-db', label: 'File Server / Database', wf: 'WF-DFL-04' },
]

// --------------------------------------------------------------------------- //
// basis 2 — the BDAT layer, over registry systems
// --------------------------------------------------------------------------- //

/** Declared BDAT lanes. `human` is DECLARED here even though nothing carries it:
 *  an empty declared lane is the FINDING, and a view that hides it destroys the
 *  only evidence a reader would get. */
export const BDAT_LANES: LaneDef[] = [
  { id: 'business', label: 'business' },
  { id: 'data', label: 'data' },
  { id: 'technology', label: 'technology' },
  {
    id: 'human',
    label: 'human',
    emptyNote:
      'declared and empty — no registry system carries this layer. The lane renders because the absence is the finding.',
  },
]

interface LoadMapSystem {
  id: string
  name: string
  layer?: string
  classification?: string
}

/** Registry systems, as the generated load-map carries them. */
function systems(): LoadMapSystem[] {
  return ((loadMap as { systems?: LoadMapSystem[] }).systems ?? []).slice()
}

function layerItems(): LaneItem[] {
  return systems().map((s) => ({
    id: s.id,
    label: s.name,
    sub: s.classification ? `system · ${s.classification}` : 'system',
    // A system with NO declared layer is not silently dropped into one — it
    // gets its own bucket, because "undeclared" and "technology" are different
    // statements and only one of them is in the data.
    lane: s.layer ?? 'undeclared',
  }))
}

/** Any lane the data uses that the declared set does not name. Rendered rather
 *  than dropped: a value nobody declared is exactly what a reader needs to see. */
export function undeclaredLanes(items: LaneItem[], declared: LaneDef[]): LaneDef[] {
  const known = new Set(declared.map((l) => l.id))
  const extra = [...new Set(items.map((i) => i.lane))].filter((l) => !known.has(l))
  return extra.map((id) => ({
    id,
    label: id,
    emptyNote: 'not a declared BDAT layer — present in the data and shown because of that',
  }))
}

// --------------------------------------------------------------------------- //
// the resolver — ONE place, per the item's clause
// --------------------------------------------------------------------------- //

/**
 * The lane assignment for a basis. The view calls this and lays out whatever it
 * gets back; it never branches on the basis id itself.
 */
export function resolveLanes(basis: LaneBasisId, sourceKindItems: LaneItem[]): LaneBasis {
  if (basis === 'layer') {
    const items = layerItems()
    return {
      id: 'layer',
      label: 'BDAT layer',
      axisNote:
        'AXIS: the BDAT layer on source-registry SYSTEM rows. NOT the relationship vocabulary’s `human` domain (that is a file/loader partition), and NOT rdfs:domain (from_node/to_node carry that).',
      lanes: [...BDAT_LANES, ...undeclaredLanes(items, BDAT_LANES)],
      items,
      caveat:
        'A layer lane groups by CARRIER, not by subject: `layer` is a SYSTEM field today, so an extract inherits the layer of the database it was pulled through. That is why the two People & Org datasets sit in different lanes. Idea-216 rules on moving or deriving it; this view makes the skew visible rather than waiting.',
    }
  }
  return {
    id: 'source-kind',
    label: 'Source kind',
    axisNote:
      'AXIS: where the thing runs or lives — the WF-DFL wireframe’s three lanes. Nothing to do with the BDAT layer.',
    lanes: SOURCE_KIND_LANES,
    items: sourceKindItems,
  }
}

/** Every basis the view offers, for the picker and the deep link. */
export const LANE_BASES: readonly { id: LaneBasisId; label: string }[] = [
  { id: 'source-kind', label: 'Source kind' },
  { id: 'layer', label: 'BDAT layer' },
]

/** Is this arbitrary string a basis? Guards the ?lanes= parameter. */
export function isLaneBasis(value: string | null | undefined): value is LaneBasisId {
  return value === 'source-kind' || value === 'layer'
}
