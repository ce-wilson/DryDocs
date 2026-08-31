import { useState } from 'react'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import MiniDag from '../components/MiniDag'
import LinkedDemoFrame from '../components/LinkedDemoFrame'
import FixDiff from '../remediation/FixDiff'
import ProfileFrame from '../remediation/ProfileFrame'
import StandardsFindings from '../remediation/StandardsFindings'
import Substitutions from '../remediation/Substitutions'
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
        // O59 — THE INTAKE PATH, beside the O17 flow panes rather than instead
        // of them. The three frames below are file-backed: G68's real profile()
        // over a synthetic export, drift-guarded, arriving as a generated
        // artifact because G68 NAMED its transport as a CLI verb writing JSON.
        //
        // WHY 'Standards findings' AND 'Findings' BOTH EXIST, which looks like
        // a duplicate and is not. 'Findings' is a node in the finding ->
        // fix-batch -> Jira FLOW, wired to the graph pane's selection; it
        // illustrates what happens to a finding once it is batched. 'Standards
        // findings' is detect_all()'s output over one folder set, which is what
        // an SME reads BEFORE any of that. Merging them would have cost the
        // flow pane its linked frame and taught the reader that a census and a
        // work queue are the same list.
        Profile: <ProfileFrame />,
        'Standards findings': <StandardsFindings />,
        Substitutions: <Substitutions />,
        Findings: <LinkedDemoFrame frame={FINDINGS_FRAME} notice={NOTICE} {...frameProps} />,
        'Fix batches': <LinkedDemoFrame frame={BATCHES_FRAME} notice={NOTICE} {...frameProps} />,
        // The SME working-session diff (2026-08-12): generated-artifact-backed,
        // not a demo fixture — the frame is computed by the real xml_io
        // splice + self-check pipeline (over synthetic data) and drift-guarded.
        'Fix diff': <FixDiff />,
        'Jira handoffs': <LinkedDemoFrame frame={JIRA_FRAME} notice={NOTICE} {...frameProps} />,
      }}
    />
  )
}
