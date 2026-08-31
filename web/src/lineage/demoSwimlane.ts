// SYNTHESIZED swimlane demo (O60) — job -> pipeline -> asset for one data series.
//
// Every region carries its WF-DFL wireframe key, so SME feedback written against
// the wireframe (the FB-2026-08-13-01 convention) re-attaches to a component
// that now exists rather than to a picture that does not.
//
// ALL VALUES INVENTED — no real folder, job or host names (the demoLineage
// idiom, and the publish boundary).

import type { LaneItem } from './laneBasis'

export interface SwimlaneEdge {
  id: string
  source: string
  target: string
  label: string
  wf: string
  /** Dashed + captioned when the vocabulary does not back the edge. */
  unbacked?: boolean
}

export const SWIMLANE_ITEMS: LaneItem[] = [
  {
    id: 'fw',
    label: 'JOB0010_SAMPLE_DAT_FW',
    sub: 'FileWatcher — detects arrival',
    lane: 'controlm',
    wf: 'WF-DFL-05',
  },
  {
    id: 'launcher',
    label: 'JOB0020_SAMPLE_PLCT',
    sub: 'ETL launcher — CMDLINE carries the token',
    lane: 'controlm',
    wf: 'WF-DFL-06',
  },
  {
    id: 'downstream',
    label: 'JOB0030_SAMPLE_TRUST',
    sub: 'waits on pipeline-complete',
    lane: 'controlm',
    wf: 'WF-DFL-07',
  },
  {
    id: 'pipeline',
    label: 'p_place_sample',
    sub: 'ETLProcess — RAW → TRUSTED → REFINED',
    lane: 'data-layer',
    wf: 'WF-DFL-08',
  },
  {
    id: 'srcfile',
    label: '/data/synth/in/sample.dat (+ .tok)',
    sub: 'source file on the file server',
    lane: 'file-db',
    wf: 'WF-DFL-09',
  },
  {
    id: 'target',
    label: 'synth@[db].sample.trusted_sample',
    sub: 'target dataset — registry URN',
    lane: 'file-db',
    wf: 'WF-DFL-10',
  },
]

// THE READS/WRITES EDGES ARE SOLID, and that is a correction the build made
// rather than a preference.
//
// O60's acceptance says they render dashed and marked planned "for as long as
// m3_reads_from / m3_writes_to carry status: planned in the relationship
// vocabulary". They do NOT: both are `deprecated`, superseded by
// `scheduler_reads_from` and `scheduler_writes_to`, and BOTH SUCCESSORS ARE
// ACTIVE. The condition the acceptance made its instruction depend on is false,
// so the edges are backed and drawing them dashed would understate a confirmed
// ruling. The wireframe's own WF-DFL-14/15 labels still read "(planned)" and are
// stale for the same reason; the view says so on the surface.
//
// Worth noting the item did this RIGHT: it wrote the rule as a CONDITION on the
// vocabulary rather than as a flat instruction, which is what let the build
// resolve it from the data instead of following stale wording. Guarded by
// tests/unit/test_lineage_edge_backing.py so the two cannot drift apart again.
export const SWIMLANE_EDGES: SwimlaneEdge[] = [
  { id: 'e1', source: 'srcfile', target: 'fw', label: 'detected by', wf: 'WF-DFL-11' },
  { id: 'e2', source: 'fw', target: 'launcher', label: 'condition', wf: 'WF-DFL-12' },
  { id: 'e3', source: 'launcher', target: 'pipeline', label: 'launches', wf: 'WF-DFL-13' },
  { id: 'e4', source: 'pipeline', target: 'srcfile', label: 'READS_FROM', wf: 'WF-DFL-14' },
  { id: 'e5', source: 'pipeline', target: 'target', label: 'WRITES_TO', wf: 'WF-DFL-15' },
  {
    id: 'e6',
    source: 'pipeline',
    target: 'downstream',
    label: 'pipeline-complete condition',
    wf: 'WF-DFL-16',
  },
]

/** The vocabulary entries the two data edges rest on, quoted on the surface so
 *  a reader can check the claim rather than take it. */
export const EDGE_BACKING = [
  { label: 'READS_FROM', entry: 'scheduler_reads_from', status: 'active' },
  { label: 'WRITES_TO', entry: 'scheduler_writes_to', status: 'active' },
] as const
