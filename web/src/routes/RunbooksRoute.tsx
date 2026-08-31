import { useMemo, useState } from 'react'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import SpecGraphPane from '../components/SpecGraphPane'
import type { CanvasNode } from '../lib/nvl-mapping'
import MiniDag from '../components/MiniDag'
import LinkedDemoFrame from '../components/LinkedDemoFrame'
import {
  COMPLETENESS_FRAME,
  GENERATED_FRAME,
  RUNBOOK_EDGES,
  RUNBOOK_NODES,
  SERIES_FRAME,
} from '../runbooks/demoRunbooks'

// /runbooks (O17): the shared template — graph pane = the data-series
// provisioning chain (FileWatcher -> RAW -> ING -> LD). Series binds
// runbooks.series.v1 (drydocs since the G30 ruling; zero rows honest pre-gate); Metadata
// completeness binds runbooks.metadata-completeness.v1 (drydocs — live where
// jobs are loaded); Generated runbooks lists the repo's real runbook
// artifacts (file artifacts, not graph rows — no spec by design).
const runbooksModule = MODULES.find((m) => m.id === 'runbooks')!

const NOTICE = 'SYNTHESIZED · ILLUSTRATIVE — live series data is company-side (mechanism-only fixtures)'

export default function RunbooksRoute({ persona }: { persona: Persona }) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  // O81: the canvas keeps its own selection rather than sharing selectedId —
  // that one is a DEMO node id (RUNBOOK_NODES), and a spec-derived node id is a
  // different namespace. Collapsing them would make a click on one surface
  // highlight an unrelated row on the other.
  const [canvasNode, setCanvasNode] = useState<CanvasNode | null>(null)
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  const selectedLabel = RUNBOOK_NODES.find((n) => n.id === selectedId)?.label
  const frameProps = { selectedId, onSelect: setSelectedId }

  return (
    <ModuleTemplate
      module={runbooksModule}
      selection={selectedLabel}
      graphPane={
        <MiniDag
          nodes={RUNBOOK_NODES}
          edges={RUNBOOK_EDGES}
          title="Data-series provisioning chain · FW → RAW → ING → LD"
          badge="EXAMPLE DATA · ILLUSTRATIVE"
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      }
      tabContent={{
        Series: (
          <SpecGrid
            access={access}
            specId="runbooks.series.v1"
            fallback={<LinkedDemoFrame frame={SERIES_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
        // O81 surface 1: the SAME reviewed spec the Series tab tables, drawn as
        // the graph its rows were flattened from (job -INVOKES-> process
        // -WRITES_TO-> asset). Zero rows until the curated lineage load runs,
        // and the canvas says so rather than showing an empty rectangle.
        'Series graph': (
          <SpecGraphPane
            access={access}
            specId="runbooks.series.v1"
            title="Data-series traversal · job → ETL process → asset"
            selected={canvasNode}
            onSelect={setCanvasNode}
          />
        ),
        'Generated runbooks': (
          <LinkedDemoFrame
            frame={GENERATED_FRAME}
            notice="Repo runbook artifacts (files, not graph rows — no QuerySpec by design)"
            {...frameProps}
          />
        ),
        'Metadata completeness': (
          <SpecGrid
            access={access}
            specId="runbooks.metadata-completeness.v1"
            fallback={<LinkedDemoFrame frame={COMPLETENESS_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
      }}
    />
  )
}
