import { Navigate, useParams } from 'react-router-dom'
import type { Persona } from '../../lib/auth'
import { canDrill } from '../../lib/views'
import { isTowerKey, TOWERS } from '../../data/towers'
import ModuleToolbar from '../../layout/ModuleToolbar'
import TowerDrill from '../../components/TowerDrill'

// A real deep-linkable route (site-plan §3: "Deep links: /explorer/tower/:key,
// ..."), replacing the old `#/tower/<key>` hash route. Same mock-RBAC guard as
// before (canDrill) — an unknown key or a tower outside the persona's access
// redirects back to the Explorer index instead of rendering.
export default function ExplorerTowerRoute({ persona }: { persona: Persona }) {
  const { towerKey } = useParams<{ towerKey: string }>()
  if (!towerKey || !isTowerKey(towerKey) || !canDrill(towerKey, persona)) {
    return <Navigate to="/explorer" replace />
  }
  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Explorer', to: '/explorer' }, { label: TOWERS[towerKey].title }]}
      />
      <div className="min-h-0 flex-1 overflow-auto">
        <TowerDrill towerKey={towerKey} />
      </div>
    </div>
  )
}
