import { useEffect, useMemo, useState } from 'react'
import type { Persona } from '../../lib/auth'
import { createApiAccess } from '../../lib/graphApi'
import { MODULES } from '../../modules/registry'
import { useRightSidebar } from '../../layout/rightSidebarContext'
import ModuleTemplate from '../ModuleTemplate'
import ExplorerGraphPane from '../../explorer/ExplorerGraphPane'
import DataFrame from '../../explorer/DataFrame'
import SpecGrid from '../../explorer/SpecGrid'
import SpecGraphPane from '../../components/SpecGraphPane'
import type { CanvasNode } from '../../lib/nvl-mapping'
import LocationMap, { type MapDimension } from '../../components/map/LocationMap'
import NodeInspector from '../../explorer/NodeInspector'
import {
  APP_CODES_FRAME,
  APPLICATIONS_FRAME,
  CONDITIONS_FRAME,
  FOLDERS_FRAME,
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

// Z5: the relationship dimensions the Locations tab offers. This list is the
// dropdown — LocationMap knows nothing about servers, jobs or teams, so adding
// the next located label is one QuerySpec plus one entry here, with no change to
// the component. Each `note` states what the dimension actually CLAIMS, because
// "jobs at a location" and "a team's work reaches a location" are different
// assertions and a map flattens that distinction unless the page says otherwise.
const LOCATION_DIMENSIONS: readonly MapDimension[] = [
  {
    specId: 'map.server-locations.v1',
    label: 'Servers',
    kind: 'server',
    note: 'Inventory servers at the data center they are placed in (the direct LOCATED_IN edge).',
  },
  {
    specId: 'map.job-locations.v1',
    label: 'Jobs',
    kind: 'job',
    note:
      'Jobs at the location of the host they run on. There is no job\u2192server edge by design ' +
      '(gate SS C3) \u2014 this is the traversal, so a job whose host never resolved is counted as ' +
      'unplaceable rather than shown somewhere convenient.',
  },
  {
    specId: 'map.team-locations.v1',
    label: 'Teams',
    kind: 'team',
    note:
      'Where a team\u2019s applications RUN \u2014 a reach claim, never a residence claim. DryDocs ' +
      'holds no person-location data.',
  },
]

export default function ExplorerRoute({ persona }: { persona: Persona }) {
  const [tower, setTower] = useState<TowerKey>('home')
  const [selection, setSelection] = useState<Selection | null>(null)
  // O81: spec-derived node ids are a different namespace from the demo graph's
  // Selection, so the canvas holds its own rather than sharing this one.
  const [canvasNode, setCanvasNode] = useState<CanvasNode | null>(null)
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
        Folders: (
          <SpecGrid
            access={access}
            specId="explorer.folder-applications.v1"
            fallback={<DataFrame cols={FOLDERS_FRAME.cols} rows={FOLDERS_FRAME.rows} {...frameProps} />}
          />
        ),
        // O81 surface 2: the application neighbourhood, drawn from the same
        // reviewed spec the Folders tab tables — folder → application, folder →
        // data centre. The :Port hop the spec traverses is deliberately NOT
        // drawn: the rows carry no port identity, so a port node would be one
        // the console invented (see nvl-mapping.ts).
        'App neighbourhood': (
          <SpecGraphPane
            access={access}
            specId="explorer.folder-applications.v1"
            title="Application neighbourhood · folder → application · folder → data centre"
            selected={canvasNode}
            onSelect={setCanvasNode}
          />
        ),
        'App codes': (
          <SpecGrid
            access={access}
            specId="explorer.controlm-app-codes.v1"
            fallback={<DataFrame cols={APP_CODES_FRAME.cols} rows={APP_CODES_FRAME.rows} {...frameProps} />}
          />
        ),
        Jobs: (
          <SpecGrid
            access={access}
            specId="explorer.jobs.v2"
            fallback={<DataFrame cols={JOBS_FRAME.cols} rows={JOBS_FRAME.rows} {...frameProps} />}
          />
        ),
        Conditions: (
          <SpecGrid
            access={access}
            specId="explorer.conditions.v2"
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
        Locations: (
          <LocationMap access={access} dimensions={LOCATION_DIMENSIONS} placeNoun="data centers" />
        ),
      }}
    />
  )
}
