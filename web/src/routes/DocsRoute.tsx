import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import SpecGrid from '../explorer/SpecGrid'
import MiniDag from '../components/MiniDag'
import LinkedDemoFrame from '../components/LinkedDemoFrame'
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

export default function DocsRoute({ persona }: { persona: Persona }) {
  const { docId } = useParams<{ docId: string }>()
  const [selectedId, setSelectedId] = useState<string | null>(docId ? 'doc' : null)
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

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
        />
      }
      tabContent={{
        Documents: (
          <SpecGrid
            access={access}
            specId="docs.documents.v1"
            fallback={<LinkedDemoFrame frame={DOCUMENTS_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
        Chunks: (
          <SpecGrid
            access={access}
            specId="docs.chunks.v1"
            fallback={<LinkedDemoFrame frame={CHUNKS_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
        'Trust/provenance audit': (
          <SpecGrid
            access={access}
            specId="docs.trust-provenance.v1"
            fallback={<LinkedDemoFrame frame={TRUST_FRAME} notice={NOTICE} {...frameProps} />}
          />
        ),
      }}
    />
  )
}
