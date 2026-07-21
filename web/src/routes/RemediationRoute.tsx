import { useState } from 'react'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import MiniDag from '../components/MiniDag'
import LinkedDemoFrame from '../components/LinkedDemoFrame'
import {
  BATCHES_FRAME,
  FINDINGS_FRAME,
  JIRA_FRAME,
  REMEDIATION_EDGES,
  REMEDIATION_NODES,
} from '../remediation/demoRemediation'

// /remediation (O17): the shared template — graph pane = the finding ->
// fix-batch flow. ALL frames are mechanism-only SYNTHESIZED fixtures, by
// design: drydocs_remediation writes ZERO graph (its no-graph-write
// invariant) and its outputs are file artifacts, so there is no graph shape
// for QuerySpecs to read — and inventing :Finding/:FixBatch labels in a spec
// would smuggle an ontology decision past the HITL gate. Live specs bind
// if/when a remediation graph shape is gate-confirmed (remediation TDD
// section 6/7 tracks that).
const remediationModule = MODULES.find((m) => m.id === 'remediation')!

const NOTICE =
  'SYNTHESIZED · ILLUSTRATIVE — remediation outputs are file artifacts (no graph shape; specs bind after a gate confirms one)'

export default function RemediationRoute() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selectedLabel = REMEDIATION_NODES.find((n) => n.id === selectedId)?.label
  const frameProps = { selectedId, onSelect: setSelectedId }

  return (
    <ModuleTemplate
      module={remediationModule}
      selection={selectedLabel}
      graphPane={
        <MiniDag
          nodes={REMEDIATION_NODES}
          edges={REMEDIATION_EDGES}
          title="Finding → fix-batch → package → Jira handoff (SoD: we analyze, dev implements)"
          badge="EXAMPLE DATA · ILLUSTRATIVE"
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      }
      tabContent={{
        Findings: <LinkedDemoFrame frame={FINDINGS_FRAME} notice={NOTICE} {...frameProps} />,
        'Fix batches': <LinkedDemoFrame frame={BATCHES_FRAME} notice={NOTICE} {...frameProps} />,
        'Jira handoffs': <LinkedDemoFrame frame={JIRA_FRAME} notice={NOTICE} {...frameProps} />,
      }}
    />
  )
}
