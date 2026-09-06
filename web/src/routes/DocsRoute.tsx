import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import MiniDag from '../components/MiniDag'
import LinkedDemoFrame from '../components/LinkedDemoFrame'
import CorpusStatus from '../docs/CorpusStatus'
import {
  CHUNKS_FRAME,
  DOCS_EDGES,
  DOCS_NODES,
  DOCUMENTS_FRAME,
  TRUST_FRAME,
} from '../docsmod/demoDocs'

// /docs (O18): the shared template over the lexical corpus — Document ->
// Chunk map in the graph pane; frames bind the docs.* QuerySpecs with the
// trust tier (VERBATIM / GROUNDED / SYNTHESIZED) as a visible column, never
// hidden. /docs/document/:docId deep links resolve to a selection.
const docsModule = MODULES.find((m) => m.id === 'docs')!

const NOTICE = 'SYNTHESIZED · ILLUSTRATIVE — the live corpus renders once bmc-docs is loaded in the target DB'

export default function DocsRoute() {
  const { docId } = useParams<{ docId: string }>()
  const [selectedId, setSelectedId] = useState<string | null>(docId ? 'doc' : null)

  const selectedLabel = docId ?? DOCS_NODES.find((n) => n.id === selectedId)?.label
  const frameProps = { selectedId, onSelect: setSelectedId }

  return (
    <ModuleTemplate
      module={docsModule}
      selection={selectedLabel}
      graphPane={
        <MiniDag
          nodes={DOCS_NODES}
          edges={DOCS_EDGES}
          title="Document → Chunk corpus map (llm-graph-builder pattern)"
          badge="EXAMPLE SHAPE · ILLUSTRATIVE — frames below are LIVE when the corpus is loaded"
          selectedId={selectedId}
          onSelect={setSelectedId}
          legend
        />
      }
      tabContent={{
        // O58: NOT a SpecGrid — this one reads a named server-side sweep, not a
        // QuerySpec, because the reconciliation is multi-database by design.
        // The component owns its own fetch and its own error state.
        'Corpus status': <CorpusStatus />,
        Documents: (
          <SpecGrid specId="docs.documents.v1"
            fallback={<LinkedDemoFrame frame={DOCUMENTS_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
        Chunks: (
          <SpecGrid specId="docs.chunks.v1"
            fallback={<LinkedDemoFrame frame={CHUNKS_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
        'Trust/provenance audit': (
          <SpecGrid specId="docs.trust-provenance.v1"
            fallback={<LinkedDemoFrame frame={TRUST_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
      }}
    />
  )
}
