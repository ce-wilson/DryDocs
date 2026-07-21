import { useEffect, useState } from 'react'
import type { Persona } from '../../lib/auth'
import { MODULES } from '../../modules/registry'
import { useRightSidebar } from '../../layout/rightSidebarContext'
import ModuleTemplate from '../ModuleTemplate'
import ExplorerGraphPane from '../../explorer/ExplorerGraphPane'
import DataFrame from '../../explorer/DataFrame'
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
        Applications: <DataFrame cols={APPLICATIONS_FRAME.cols} rows={APPLICATIONS_FRAME.rows} {...frameProps} />,
        Jobs: <DataFrame cols={JOBS_FRAME.cols} rows={JOBS_FRAME.rows} {...frameProps} />,
        Conditions: <DataFrame cols={CONDITIONS_FRAME.cols} rows={CONDITIONS_FRAME.rows} {...frameProps} />,
        Servers: <DataFrame cols={SERVERS_FRAME.cols} rows={SERVERS_FRAME.rows} {...frameProps} />,
      }}
    />
  )
}
