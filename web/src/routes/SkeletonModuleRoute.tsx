import { MODULES, type ModuleId } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'

// The six modules with no bespoke O2/O6 content to fold in (Lineage, Runbooks,
// Remediation, Docs, Gates, Loads) all render the identical shared template —
// per wf-module-subpage-01 annotation 7, that's the point: nothing but the
// registry entry should differ between them at this stage.
export default function SkeletonModuleRoute({ id }: { id: ModuleId }) {
  const module = MODULES.find((m) => m.id === id)
  if (!module) throw new Error(`unknown module: ${id}`)
  return <ModuleTemplate module={module} />
}
