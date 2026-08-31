// SYNTHESIZED product roll-up demo (O61) — the two roll-up shapes, side by side.
//
// WHAT THIS DRAWS, and why two columns rather than one. A folder's PAT
// AreaProduct token is the leaf; it rolls up AreaProduct -> Product ->
// ProductLine -> LOB. But HOW a folder reaches its AreaProduct differs by
// application kind, and the difference is the whole point of the view:
//
//   * FRAMEWORK applications carry no direct SEAL. The AreaProduct token IS the
//     join — the folder names it, and that name is the only thread back to the
//     product taxonomy.
//   * APP-TIED applications carry a SEAL. The Control-M sub-application is the
//     join, and the SEAL is what identifies the owning application.
//
// Rendering them in one column would suggest one join rule. They are two, and a
// support engineer tracing ownership needs to know which one they are following.
//
// THE DASHED EDGE IS THE HONEST PART. "aligns to platform" is a cross-branch
// relationship the estate genuinely has and the ONTOLOGY has not ruled on —
// there is no confirmed graph relationship behind it. Drawing it solid would
// assert an edge nobody confirmed; omitting it would hide something real. So it
// is dashed, labelled, and captioned on the view. Rendering it commits nothing
// and skips no gate.
//
// EVERY VALUE IS SYNTHETIC. The SME supplied a rendered example whose values are
// real org taxonomy; that transcription is machine-local and never committed.
// What is committed here is a twin of its SHAPE (the demoOwnership idiom).

import type { DagEdgeDef, DagNodeDef } from '../components/MiniDag'

/** Left column x, right column x — hand-authored, like every MiniDag. */
const FRAMEWORK_X = 0
const APP_TIED_X = 460

export const ROLLUP_NODES: readonly DagNodeDef[] = [
  // --- shared crown: the taxonomy both shapes roll up into --------------------
  { id: 'lob', label: 'Synthetic Banking LOB', sub: 'CatalogLOB', token: '--red', x: 230, y: 0 },

  // --- framework branch (no SEAL; the AreaProduct token is the join) ----------
  {
    id: 'fw-line',
    label: 'Data Platform Services',
    sub: 'ProductLine',
    token: '--yellow',
    x: FRAMEWORK_X,
    y: 110,
  },
  {
    id: 'fw-product',
    label: 'Ingestion Framework',
    sub: 'Product',
    token: '--yellow',
    x: FRAMEWORK_X,
    y: 220,
  },
  {
    id: 'fw-area',
    label: 'SYNTH_INGEST',
    sub: 'AreaProduct — the join',
    token: '--teal',
    x: FRAMEWORK_X,
    y: 330,
  },
  {
    id: 'fw-folder',
    label: 'PRSYNQ-INTAKE-DLY',
    sub: 'folder · P R AOC G · no SEAL',
    token: '--blue',
    x: FRAMEWORK_X,
    y: 440,
  },

  // --- app-tied branch (SEAL; the Control-M sub-application is the join) ------
  {
    id: 'at-line',
    label: 'Retail Reporting',
    sub: 'ProductLine',
    token: '--yellow',
    x: APP_TIED_X,
    y: 110,
  },
  {
    id: 'at-product',
    label: 'Statement Delivery',
    sub: 'Product',
    token: '--yellow',
    x: APP_TIED_X,
    y: 220,
  },
  {
    id: 'at-area',
    label: 'SYNTH_STMT',
    sub: 'AreaProduct',
    token: '--teal',
    x: APP_TIED_X,
    y: 330,
  },
  {
    id: 'at-app',
    label: 'SYNTHAPP (SEAL 70004)',
    sub: 'BusinessApplication — the join',
    token: '--green',
    x: APP_TIED_X,
    y: 440,
  },
  {
    id: 'at-folder',
    label: 'PRSYNS-STMT-DLY',
    sub: 'folder · P R AOC G · sub-application',
    token: '--blue',
    x: APP_TIED_X,
    y: 550,
  },
]

export const ROLLUP_EDGES: readonly DagEdgeDef[] = [
  { id: 'r1', source: 'fw-line', target: 'lob', label: 'rolls up' },
  { id: 'r2', source: 'fw-product', target: 'fw-line', label: 'rolls up' },
  { id: 'r3', source: 'fw-area', target: 'fw-product', label: 'rolls up' },
  { id: 'r4', source: 'fw-folder', target: 'fw-area', label: 'names token' },

  { id: 'r5', source: 'at-line', target: 'lob', label: 'rolls up' },
  { id: 'r6', source: 'at-product', target: 'at-line', label: 'rolls up' },
  { id: 'r7', source: 'at-area', target: 'at-product', label: 'rolls up' },
  { id: 'r8', source: 'at-app', target: 'at-area', label: 'supports' },
  { id: 'r9', source: 'at-folder', target: 'at-app', label: 'sub-application' },

  // The one edge no confirmed graph relationship backs. Dashed and labelled.
  {
    id: 'align',
    source: 'at-folder',
    target: 'fw-area',
    label: 'aligns to platform (no confirmed edge)',
    unbacked: true,
  },
]

/** Leaf annotations: the folder-name grammar, and the classification beneath it. */
export interface LeafAnnotation {
  nodeId: string
  grammar: string
  classification: string
  join: string
}

export const LEAF_ANNOTATIONS: readonly LeafAnnotation[] = [
  {
    nodeId: 'fw-folder',
    grammar: 'PRSYNQ = P·R·SYN·Q — pos 1 environment, pos 2 region, pos 3-5 platform code, pos 6 grouping',
    classification: 'Internal-Public (synthetic demo values)',
    join: 'AreaProduct token — the folder names SYNTH_INGEST and that name is the only thread back',
  },
  {
    nodeId: 'at-folder',
    grammar: 'PRSYNS = P·R·SYN·S — same six-character positional code, different grouping character',
    classification: 'Internal-Public (synthetic demo values)',
    join: 'Control-M sub-application — the SEAL identifies the owning application',
  },
]
