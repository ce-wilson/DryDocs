import ModuleToolbar from '../../layout/ModuleToolbar'
import GraphExplorer from '../../components/GraphExplorer'

// The O6 live dependency view, kept exactly as built — reads the graph
// through the GraphAccess seam's api adapter (lib/graphApi.ts), never
// neo4j-driver directly. Only a ModuleToolbar wrapper is new here, for
// breadcrumb consistency with the rest of the shell; GraphExplorer's own
// content is untouched apart from a data-view-heading attribute on its h1
// (O8's focus-management acceptance point).
export default function ExplorerLiveRoute({ personaId }: { personaId: string }) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Explorer', to: '/explorer' }, { label: 'Live dependency graph' }]} />
      <div className="min-h-0 flex-1 overflow-auto">
        <GraphExplorer personaId={personaId} />
      </div>
    </div>
  )
}
