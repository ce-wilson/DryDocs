import type { RunRow } from './demoLoads'
import StatusChip from '../components/ui/StatusChip'

// The /loads canvas (O16, site-plan §3 row 8): loader → :JobRun provenance as
// a run TIMELINE — dot-and-rail vertical list, newest first, status colored
// through theme tokens. Click selects the run (shared selection: crumb +
// frame linking, the Explorer contract).

function statusToken(status: RunRow['status']): string {
  // FAILED = --status-fail-soft (text-safe in both themes), not --red — red is
  // brand-only per DL-2 (internal/datalens-reference/continuity.md).
  return status === 'COMPLETED' ? '--green' : status === 'FAILED' ? '--status-fail-soft' : '--yellow'
}

export default function LoadsTimeline({
  runs,
  live,
  selectedRunId,
  onSelect,
}: {
  runs: readonly RunRow[]
  live: boolean
  selectedRunId: string | null
  onSelect: (runId: string | null) => void
}) {
  // DL-3 summary chips: the run population at a glance, before scanning the rail.
  const completed = runs.filter((r) => r.status === 'COMPLETED').length
  const failed = runs.filter((r) => r.status === 'FAILED').length
  const other = runs.length - completed - failed
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-edge-soft px-3 py-2">
        <span className="text-xs font-medium text-muted">Run timeline · newest first</span>
        <StatusChip count={completed} label="completed" token="--green" glyph="✔" />
        <StatusChip count={failed} label="failed" token="--status-fail-soft" glyph="✗" />
        {other > 0 && <StatusChip count={other} label="running" token="--yellow" glyph="~" />}
        <span
          className={
            'ml-auto rounded border px-2 py-0.5 font-mono text-[10px] ' +
            (live ? 'border-edge text-muted' : 'border-yellow/50 bg-yellow/10 text-yellow')
          }
        >
          {live ? 'LIVE — :JobRun envelope' : 'EXAMPLE DATA · ILLUSTRATIVE — no runs in the target DB'}
        </span>
      </div>
      <ol className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {runs.map((r) => {
          const token = statusToken(r.status)
          const selected = r.run_id === selectedRunId
          return (
            <li key={r.run_id} className="relative pb-4 pl-6 last:pb-0">
              {/* rail + dot */}
              <span className="absolute left-[5px] top-4 h-full w-px bg-edge-soft" aria-hidden="true" />
              <span
                className="absolute left-0 top-1.5 h-3 w-3 rounded-full border-2 bg-panel"
                style={{ borderColor: `var(${token})` }}
                aria-hidden="true"
              />
              <button
                type="button"
                onClick={() => onSelect(selected ? null : r.run_id)}
                aria-pressed={selected}
                className={
                  'w-full rounded-md border px-3 py-2 text-left transition-colors ' +
                  (selected ? 'border-blue-bright bg-panel-2' : 'border-edge bg-panel hover:border-faint')
                }
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-text">{r.loader}</span>
                  <span className="font-mono text-[10px] text-faint">{r.source}</span>
                  <span className="ml-auto rounded border px-1.5 py-0.5 font-mono text-[10px]" style={{ borderColor: `var(${token})`, color: `var(${token})` }}>
                    {r.status}
                  </span>
                </div>
                <div className="mt-1 font-mono text-[10px] text-muted">
                  {r.started_at}
                  {r.completed_at ? ` → ${r.completed_at}` : ' → (never completed)'}
                </div>
                <div className="mt-1 flex flex-wrap gap-2 font-mono text-[10px] text-muted">
                  <span>rows {r.rows_processed}</span>
                  <span>changed {r.rows_changed}</span>
                  {r.rows_rejected > 0 && <span className="text-yellow">rejected {r.rows_rejected}</span>}
                  {r.nodes_marked_removed > 0 && <span className="text-status-fail-soft">marked-removed {r.nodes_marked_removed}</span>}
                  {r.nodes_reactivated > 0 && <span>reactivated {r.nodes_reactivated}</span>}
                </div>
                <div className="mt-0.5 break-all font-mono text-[9px] text-faint">{r.run_id}</div>
              </button>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
