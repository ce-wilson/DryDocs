import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import LineageGraphPane from '../lineage/LineageGraphPane'
import {
  ASSETS_FRAME,
  HOPS_FRAME,
  LINEAGE_NODES,
  SCHEMA_FRAME,
  nodeByAssetId,
  type DemoFrame,
  type LineageSelection,
} from '../lineage/demoLineage'

// /lineage (O10): the shared module template instantiated with the React Flow
// source→target DAG and the three ddlineage QuerySpec frames. Deep links
// resolve at /lineage/asset/:assetId (the demo asset ids; live assetIds once
// the gate flips and curated rows exist). Selection links graph ↔ frames as
// in Explorer (one lifted selection store).
const lineageModule = MODULES.find((m) => m.id === 'lineage')!

export default function LineageRoute({ persona }: { persona: Persona }) {
  const { assetId } = useParams<{ assetId: string }>()
  const [selection, setSelection] = useState<LineageSelection | null>(() => {
    if (!assetId) return null
    const n = nodeByAssetId(decodeURIComponent(assetId))
    return n ? { id: n.id, label: n.label, kind: n.kind } : null
  })

  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  const frameProps = { selection, onSelect: setSelection }

  return (
    <ModuleTemplate
      module={lineageModule}
      selection={selection?.label}
      graphPane={<LineageGraphPane selection={selection} onSelect={setSelection} />}
      tabContent={{
        Hops: (
          <SpecGrid
            access={access}
            specId="lineage.hops.v1"
            fallback={<LineageDemoFrame frame={HOPS_FRAME} {...frameProps} />}
          />
        ),
        'Data assets': (
          <SpecGrid
            access={access}
            specId="lineage.data-assets.v1"
            fallback={<LineageDemoFrame frame={ASSETS_FRAME} {...frameProps} />}
          />
        ),
        'Schema definition': (
          <SpecGrid
            access={access}
            specId="lineage.schema-definition.v1"
            fallback={<LineageDemoFrame frame={SCHEMA_FRAME} {...frameProps} />}
          />
        ),
        /* 'Row-level preview' stays the template's honest empty state — its
           QuerySpec is deliberately unbuilt (data preview needs the source
           platforms, not ddlineage). */
      }}
    />
  )
}

// The SYNTHESIZED fallback frame with Explorer-style selection linking:
// clicking a row selects (and highlights) its graph node; a selected node
// highlights its rows.
function LineageDemoFrame({
  frame,
  selection,
  onSelect,
}: {
  frame: DemoFrame
  selection: LineageSelection | null
  onSelect: (sel: LineageSelection | null) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        SYNTHESIZED · ILLUSTRATIVE — ddlineage carries no curated rows until the lineage live-load gate flips m3_*
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
                    const n = LINEAGE_NODES.find((x) => x.id === nodeId)
                    if (n) onSelect(isSelected ? null : { id: n.id, label: n.label, kind: n.kind })
                  }}
                  className={
                    'cursor-pointer ' +
                    (isSelected ? 'bg-panel-2' : i % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                  }
                >
                  {row.map((cell, j) => (
                    <td key={j} className="border-b border-edge-soft px-2.5 py-1.5 text-text">
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
