import { useMemo, useState } from 'react'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import OwnershipGraphPane from '../ownership/OwnershipGraphPane'
import {
  ATTRIBUTIONS_FRAME,
  ESCALATION_FRAME,
  OWNERSHIP_NODES,
  TEAMS_FRAME,
  type DemoFrame,
  type OwnershipSelection,
} from '../ownership/demoOwnership'

// /ownership (O15): the kept MyApps view EVOLVED into the shared template —
// graph pane renders the SEAL→PAT rollup in the K4 qualified-attribution
// shape (MyApps survives as the pane's toggled alternate view); the three
// data-frame tabs bind to QuerySpecs with honest empty states when a source
// (e.g. escalation routing — company-side) isn't loaded in the target DB.
const ownershipModule = MODULES.find((m) => m.id === 'ownership')!

export default function OwnershipRoute({ persona }: { persona: Persona }) {
  const [selection, setSelection] = useState<OwnershipSelection | null>(null)
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  const frameProps = { selection, onSelect: setSelection }

  return (
    <ModuleTemplate
      module={ownershipModule}
      selection={selection?.label}
      graphPane={<OwnershipGraphPane persona={persona} selection={selection} onSelect={setSelection} />}
      tabContent={{
        Teams: (
          <SpecGrid
            access={access}
            specId="ownership.teams.v1"
            fallback={<OwnershipDemoFrame frame={TEAMS_FRAME} {...frameProps} />}
          />
        ),
        Attributions: (
          <SpecGrid
            access={access}
            specId="ownership.attributions.v1"
            fallback={<OwnershipDemoFrame frame={ATTRIBUTIONS_FRAME} {...frameProps} />}
          />
        ),
        'Escalation routing': (
          <SpecGrid
            access={access}
            specId="ownership.escalation-routing.v1"
            fallback={<OwnershipDemoFrame frame={ESCALATION_FRAME} {...frameProps} />}
          />
        ),
      }}
    />
  )
}

function OwnershipDemoFrame({
  frame,
  selection,
  onSelect,
}: {
  frame: DemoFrame
  selection: OwnershipSelection | null
  onSelect: (sel: OwnershipSelection | null) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        SYNTHESIZED · ILLUSTRATIVE — live rows appear once the SEAL/PAT sources are loaded in the target DB
      </p>
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {frame.cols.map((c) => (
                <th key={c} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {frame.rows.map((row, i) => {
              const nodeId = frame.nodeIds[i]
              const isSelected = selection?.id === nodeId
              return (
                <tr
                  key={i}
                  onClick={() => {
                    const n = OWNERSHIP_NODES.find((x) => x.id === nodeId)
                    if (n) onSelect(isSelected ? null : { id: n.id, label: n.label, kind: n.kind })
                  }}
                  className={
                    'cursor-pointer ' +
                    (isSelected ? 'bg-panel-2' : i % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                  }
                >
                  {row.map((cell, j) => (
                    <td
                      key={j}
                      className={
                        'border-b border-edge-soft px-2.5 py-1.5 ' +
                        (String(cell).startsWith('TRUE') ? 'font-mono text-[11px] text-brand-soft' : 'text-text')
                      }
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
