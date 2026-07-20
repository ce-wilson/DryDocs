import type { Persona } from '../../lib/auth'
import { MODULES } from '../../modules/registry'
import ModuleTemplate from '../ModuleTemplate'
import TowerDemoGrid from './TowerDemoGrid'

// Explorer index (`/explorer`, site-plan §3 row 1): the shared template, graph
// pane filled with the O2 tower-demo cards until a real tower/app drill-down
// graph replaces them (that graph + the Applications/Jobs/Conditions/Servers
// QuerySpecs are O9). The live O6 dependency view and the tower drill-downs
// stay reachable at their own nested routes rather than being crammed into
// this skeleton's exact zones — see /explorer/live and /explorer/tower/:key.
const explorerModule = MODULES.find((m) => m.id === 'explorer')!

export default function ExplorerRoute({ persona }: { persona: Persona }) {
  return <ModuleTemplate module={explorerModule} graphPane={<TowerDemoGrid persona={persona} />} />
}
