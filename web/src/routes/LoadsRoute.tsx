import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import EmptyState from '../components/ui/EmptyState'
import LoadsTimeline from '../loads/LoadsTimeline'
import StatTiles from '../components/StatTiles'
import { DEMO_RUNS, type RunRow } from '../loads/demoLoads'
import { rowsOf, useLiveOrDemo } from '../data/provenance'
import ProvenanceNotice from '../components/ProvenanceNotice'

// /loads (O16): the shared template with the run TIMELINE as this module's
// canvas — loader → :JobRun provenance, newest first. Frames (Runs / Rejects
// / Drift-coverage) bind to QuerySpecs over the BaseLoader :JobRun envelope;
// /loads/run/:runId deep links resolve to a selection. Empty states honest on
// databases with no runs (the demo timeline shows with a visible badge).
const loadsModule = MODULES.find((m) => m.id === 'loads')!
const RUNS_SPEC = 'loads.runs.v1'

export default function LoadsRoute() {
  const { runId } = useParams<{ runId: string }>()
  const [selectedRunId, setSelectedRunId] = useState<string | null>(runId ?? null)
  // O40 (DL-10): status stat-tiles ARE the filter controls for the timeline below.
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  // WEB1: one seam, one typed state. `live` is no longer a boolean this route
  // maintains — it is the union's own status, and DEMO_RUNS is reached through
  // the seam rather than beside it.
  const provenance = useLiveOrDemo<RunRow>(RUNS_SPEC, DEMO_RUNS)
  const live = provenance.status === 'live'
  const runs: readonly RunRow[] | null =
    provenance.status === 'loading' ? null : rowsOf(provenance)

  const fallbackNote = (
    <EmptyState
      title="No rows in the target DB"
      hint="The :JobRun envelope carries rows once a load runs against this database."
    />
  )

  return (
    <ModuleTemplate
      module={loadsModule}
      selection={selectedRunId ?? undefined}
      graphPane={
        runs ? (
          <div className="flex h-full min-h-0 flex-col">
            <div className="shrink-0 px-3 pt-3">
              <ProvenanceNotice state={provenance} specId={RUNS_SPEC} />
            </div>
            <div className="shrink-0 px-3 pt-3">
              <StatTiles
                tiles={[
                  { id: 'all', value: String(runs.length), label: 'All runs' },
                  { id: 'COMPLETED', value: String(runs.filter((r) => r.status === 'COMPLETED').length), label: 'Completed' },
                  { id: 'FAILED', value: String(runs.filter((r) => r.status === 'FAILED').length), label: 'Failed' },
                  { id: 'STARTED', value: String(runs.filter((r) => r.status === 'STARTED').length), label: 'Running' },
                ]}
                selectedId={statusFilter ?? 'all'}
                onSelect={(id) => setStatusFilter(id === 'all' ? null : id)}
              />
            </div>
            <LoadsTimeline
              runs={statusFilter ? runs.filter((r) => r.status === statusFilter) : runs}
              live={live}
              selectedRunId={selectedRunId}
              onSelect={setSelectedRunId}
            />
          </div>
        ) : (
          <EmptyState title="Loading…" hint="Running QuerySpec loads.runs.v1 via drydocs-api." />
        )
      }
      tabContent={{
        Runs: <SpecGrid specId="loads.runs.v1" fallback={fallbackNote} />,
        Rejects: <SpecGrid specId="loads.rejects.v1" fallback={fallbackNote} />,
        'Drift/coverage': <SpecGrid specId="loads.drift-coverage.v1" fallback={fallbackNote} />,
        // O28: the node-status envelope, live end-to-end — BaseLoader derives
        // the items, they ride on the :JobRun, and this frame is the same spec
        // the inspector and hub glyphs consume.
        Status: <SpecGrid specId="loads.status-items.v1" fallback={fallbackNote} />,
      }}
    />
  )
}
