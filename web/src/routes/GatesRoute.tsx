import { useMemo, useState } from 'react'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import MiniDag, { type DagEdgeDef, type DagNodeDef } from '../components/MiniDag'
import EmptyState from '../components/ui/EmptyState'
import gatesData from '../generated/gates.json'

// /gates (O19): READ-ONLY render of the gate record — a GENERATED gates.json
// (scripts/render_gates.py; test_gates_json.py is the drift guard). ZERO
// action controls: no sign-off, no edits — each gate links to its repo
// artifacts as text. Write-shaped gate actions are exactly what the O20 gate
// decides; until it signs off, this page only reads.

interface GateRow {
  kind: 'log-entry' | 'prompt-only'
  date: string | null
  title: string
  status: 'open' | 'deferred' | 'pending' | 'signed-off' | 'recorded'
  prompt_files: string[]
  log_ref: string | null
  unblocks: string[]
}

const GATES = gatesData.gates as GateRow[]
const gatesModule = MODULES.find((m) => m.id === 'gates')!

const OPEN_STATUSES = new Set(['open', 'deferred', 'pending'])

function statusToken(status: GateRow['status']): string {
  if (status === 'signed-off') return '--green'
  if (status === 'recorded') return '--teal'
  if (status === 'deferred') return '--yellow'
  return '--red'
}

export default function GatesRoute() {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const selected = selectedIdx === null ? null : GATES[selectedIdx]

  const { nodes, edges } = useMemo(() => {
    if (!selected) return { nodes: [] as DagNodeDef[], edges: [] as DagEdgeDef[] }
    const nodes: DagNodeDef[] = [
      {
        id: 'gate',
        label: selected.title.length > 70 ? selected.title.slice(0, 70) + '…' : selected.title,
        sub: `gate · ${selected.status}`,
        token: statusToken(selected.status),
        x: 0,
        y: Math.max(0, (selected.unblocks.length - 1) * 45),
      },
      ...selected.unblocks.map((id, i) => ({
        id: `item-${id}`,
        label: id,
        sub: 'backlog item',
        token: '--blue',
        x: 320,
        y: i * 90,
      })),
    ]
    const edges: DagEdgeDef[] = selected.unblocks.map((id) => ({
      id: `e-${id}`,
      source: 'gate',
      target: `item-${id}`,
      label: 'references',
    }))
    return { nodes, edges }
  }, [selected])

  const openGates = GATES.filter((g) => OPEN_STATUSES.has(g.status))
  const signedGates = GATES.filter((g) => !OPEN_STATUSES.has(g.status))

  const table = (rows: GateRow[]) => (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
        READ-ONLY — the gate record renders; acting on gates from the UI is the O20 gate's decision. Rows link to
        repo artifacts.
      </p>
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['Date', 'Gate', 'Status', 'Artifacts', 'Referenced by'].map((h) => (
                <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((g) => {
              const idx = GATES.indexOf(g)
              const isSelected = idx === selectedIdx
              return (
                <tr
                  key={idx}
                  onClick={() => setSelectedIdx(isSelected ? null : idx)}
                  className={
                    'cursor-pointer ' +
                    (isSelected ? 'bg-panel-2' : idx % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                  }
                >
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {g.date ?? '—'}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{g.title}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5">
                    <span
                      className="rounded border px-1.5 py-0.5 font-mono text-[10px]"
                      style={{ borderColor: `var(${statusToken(g.status)})`, color: `var(${statusToken(g.status)})` }}
                    >
                      {g.status}
                    </span>
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {[...g.prompt_files, ...(g.log_ref ? [g.log_ref] : [])].join(', ') || '—'}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {g.unblocks.join(', ') || '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )

  return (
    <ModuleTemplate
      module={gatesModule}
      selection={selected?.title.split('—')[0].trim()}
      toolbarActions={
        <span className="font-mono text-[10px] text-faint" title="O19: zero action controls by design">
          read-only record — sign-offs happen in the HITL flow, never here
        </span>
      }
      graphPane={
        selected ? (
          <MiniDag
            nodes={nodes}
            edges={edges}
            title={`Gate dependency graph — ${selected.status}`}
            badge="GENERATED from gates.json — references derived from backlog mentions"
            selectedId={null}
            onSelect={() => {}}
          />
        ) : (
          <EmptyState
            title="Select a gate row"
            hint={`${GATES.length} gates in the record (${openGates.length} open/deferred/pending). Click a row to see what it references.`}
          />
        )
      }
      tabContent={{
        'Open gates': openGates.length ? (
          table(openGates)
        ) : (
          <EmptyState title="No open gates" hint="Every rendered gate page has a recorded session." />
        ),
        'Signed off': table(signedGates),
        'Gate log': (
          <div className="flex h-full min-h-0 flex-col gap-1.5">
            <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
              The full log lives at config/gate-log.md (also rendered verbatim on /admin/config → Gate log). This
              frame is the entry index.
            </p>
            <div className="min-h-0 flex-1">{table(GATES)}</div>
          </div>
        ),
      }}
    />
  )
}
