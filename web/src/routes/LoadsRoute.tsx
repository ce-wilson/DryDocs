import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import EmptyState from '../components/ui/EmptyState'
import LoadsTimeline from '../loads/LoadsTimeline'
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
          <LoadsTimeline runs={runs} live={live} selectedRunId={selectedRunId} onSelect={setSelectedRunId} />
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
