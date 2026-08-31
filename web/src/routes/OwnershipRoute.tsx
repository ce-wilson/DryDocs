import { useMemo, useState } from 'react'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import OwnershipGraphPane from '../ownership/OwnershipGraphPane'
import AssetSearchPanel from '../ownership/AssetSearchPanel'
import ProductRollup from '../ownership/ProductRollup'
import {
  ATTRIBUTIONS_FRAME,
  CAPTURE_GAPS_FRAME,
  ESCALATION_FRAME,
  OWNERSHIP_NODES,
  REQUIRED_CONTACT_GAPS_FRAME,
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
      graphPane={
        // support-user search strip (2026-07-21 chat) rides ABOVE the O15
        // rollup pane: narrow (Product → Application → file/table) then
        // partial-name; a result deep-links /ownership/asset/:assetId.
        <div className="flex h-full min-h-0 flex-col">
          <AssetSearchPanel />
          <div className="min-h-0 flex-1">
            <OwnershipGraphPane persona={persona} selection={selection} onSelect={setSelection} />
          </div>
        </div>
      }
      tabContent={{
        // O61: SYNTHESIZED, and no spec — the two roll-up SHAPES are the
        // content, and one of its edges is deliberately unbacked by any graph
        // relationship, so there is nothing here for a QuerySpec to return.
        'Product roll-up': <ProductRollup />,
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
        // G71 (SS-C5): the completeness pair JOINS this page rather than opening a
        // new one — the Attributions tab beside it floats unmapped rows first, so
        // one page answers "what is wrong with this application's contacts".
        // SS-C6 keeps the two findings apart: roster gaps on covered apps here,
        // capture gaps (no feed mentioned the app) on their own tab.
        'Required-contact gaps': (
          <div className="flex h-full min-h-0 flex-col">
            <p className="shrink-0 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
              Caveats from the sign-off: Operate Manager assignments are mid-correction at
              source (findings there are being fixed elsewhere), and this check counts to
              one and stops — it cannot see geography / coverage-window gaps.
            </p>
            <div className="min-h-0 flex-1">
              <SpecGrid
                access={access}
                specId="ownership.required-contact-gaps.v1"
                fallback={<OwnershipDemoFrame frame={REQUIRED_CONTACT_GAPS_FRAME} {...frameProps} />}
              />
            </div>
          </div>
        ),
        'Capture gaps': (
          <div className="flex h-full min-h-0 flex-col">
            <p className="shrink-0 px-3 py-2 text-xs text-slate-500 dark:text-slate-400">
              Applications no feed mentioned. A capture gap is not a roster gap — the
              response is a capture fix, not a contact chase.
            </p>
            <div className="min-h-0 flex-1">
              <SpecGrid
                access={access}
                specId="ownership.capture-gaps.v1"
                fallback={<OwnershipDemoFrame frame={CAPTURE_GAPS_FRAME} {...frameProps} />}
              />
            </div>
          </div>
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
