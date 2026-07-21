import { useEffect, useMemo, useState } from 'react'
import type { Persona } from '../../lib/auth'
import { createApiAccess } from '../../lib/graphApi'
import { MODULES } from '../../modules/registry'
import { useRightSidebar } from '../../layout/rightSidebarContext'
import ModuleTemplate from '../ModuleTemplate'
import ExplorerGraphPane from '../../explorer/ExplorerGraphPane'
import DataFrame from '../../explorer/DataFrame'
import SpecGrid from '../../explorer/SpecGrid'
import NodeInspector from '../../explorer/NodeInspector'
import {
  APPLICATIONS_FRAME,
  CONDITIONS_FRAME,
  JOBS_FRAME,
  SERVERS_FRAME,
  type Selection,
} from '../../explorer/demoGraph'
import type { TowerKey } from '../../data/towers'

// Explorer (`/explorer`, O9): the first full instantiation of the shared
// module template — React Flow tower graph over the four data-frame tabs, with
// ONE lifted selection store linking graph, grids, and the right node
// inspector (node click filters rows; row select highlights the node). Demo
// content is the SYNTHESIZED tower set; the live O6 dependency view stays at
// /explorer/live, tower drill-downs at /explorer/tower/:key.
const explorerModule = MODULES.find((m) => m.id === 'explorer')!

export default function ExplorerRoute({ persona }: { persona: Persona }) {
  const [tower, setTower] = useState<TowerKey>('home')
  const [selection, setSelection] = useState<Selection | null>(null)
  const sidebar = useRightSidebar()
  // O11: each tab binds to its versioned QuerySpec via the GraphAccess api
  // adapter; the O9 demo frames survive as the visible fallback when
  // drydocs-api (or the graph) is unavailable.
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  // selection → inspector (the template's right sidebar slot)
  useEffect(() => {
    if (selection) {
      sidebar.set(<NodeInspector selection={selection} persona={persona} onSelect={setSelection} />)
    } else {
      sidebar.clear()
    }
    // clearing on unmount keeps the inspector from leaking into other routes
    return () => sidebar.clear()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection, persona])

  // selecting a node in another tower (via a frame row) re-frames the graph
  useEffect(() => {
    if (selection && selection.tower !== tower) setTower(selection.tower)
  }, [selection, tower])

  const frameProps = { selection, onSelect: setSelection }

  return (
    <ModuleTemplate
      module={explorerModule}
      selection={selection?.label}
      graphPane={
        <ExplorerGraphPane
          persona={persona}
          tower={tower}
          onTowerChange={setTower}
          selection={selection}
          onSelect={setSelection}
        />
      }
      tabContent={{
        Applications: (
          <SpecGrid
            access={access}
            specId="explorer.applications.v1"
            fallback={<DataFrame cols={APPLICATIONS_FRAME.cols} rows={APPLICATIONS_FRAME.rows} {...frameProps} />}
          />
        ),
        Jobs: (
          <SpecGrid
            access={access}
            specId="explorer.jobs.v1"
            fallback={<DataFrame cols={JOBS_FRAME.cols} rows={JOBS_FRAME.rows} {...frameProps} />}
          />
        ),
        Conditions: (
          <SpecGrid
            access={access}
            specId="explorer.conditions.v1"
            fallback={<DataFrame cols={CONDITIONS_FRAME.cols} rows={CONDITIONS_FRAME.rows} {...frameProps} />}
          />
        ),
        Servers: (
          <SpecGrid
            access={access}
            specId="explorer.servers.v1"
            fallback={<DataFrame cols={SERVERS_FRAME.cols} rows={SERVERS_FRAME.rows} {...frameProps} />}
          />
        ),
      }}
    />
  )
}
