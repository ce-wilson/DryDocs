import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import EmptyState from '../components/ui/EmptyState'
import LoadsTimeline from '../loads/LoadsTimeline'
import StatTiles from '../components/StatTiles'
import { DEMO_RUNS, type RunRow } from '../loads/demoLoads'

// /loads (O16): the shared template with the run TIMELINE as this module's
// canvas — loader → :JobRun provenance, newest first. Frames (Runs / Rejects
// / Drift-coverage) bind to QuerySpecs over the BaseLoader :JobRun envelope;
// /loads/run/:runId deep links resolve to a selection. Empty states honest on
// databases with no runs (the demo timeline shows with a visible badge).
const loadsModule = MODULES.find((m) => m.id === 'loads')!

export default function LoadsRoute({ persona }: { persona: Persona }) {
  const { runId } = useParams<{ runId: string }>()
  const [selectedRunId, setSelectedRunId] = useState<string | null>(runId ?? null)
  const [runs, setRuns] = useState<readonly RunRow[] | null>(null)
  const [live, setLive] = useState(false)
  // O40 (DL-10): status stat-tiles ARE the filter controls for the timeline below.
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  useEffect(() => {
    let cancelled = false
    access
      .runSpec('loads.runs.v1')
      .then((r) => {
        if (cancelled) return
        if (r.rows.length > 0) {
          setRuns(r.rows as unknown as RunRow[])
          setLive(true)
        } else {
          setRuns(DEMO_RUNS)
        }
      })
      .catch(() => {
        if (!cancelled) setRuns(DEMO_RUNS)
      })
    return () => {
      cancelled = true
    }
  }, [access])

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
        Runs: <SpecGrid access={access} specId="loads.runs.v1" fallback={fallbackNote} />,
        Rejects: <SpecGrid access={access} specId="loads.rejects.v1" fallback={fallbackNote} />,
        'Drift/coverage': <SpecGrid access={access} specId="loads.drift-coverage.v1" fallback={fallbackNote} />,
      }}
    />
  )
}
