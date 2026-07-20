import type { Persona } from '../lib/auth'
import ModuleToolbar from '../layout/ModuleToolbar'
import MyApps from '../components/MyApps'

// Ownership (`/ownership`, site-plan §3 row 3: "SEAL→PAT→team rollup graph
// (My Apps SVG pattern)"). The O2 My Apps view is exactly that content, so it
// is folded in here wholesale rather than rebuilt against the shared
// ModuleTemplate zones (that retrofit — Teams/Memberships/Escalation routing
// as real data-frame tabs — is later module-view work, same as Explorer's
// live view). The standalone `/my-apps` route is retired; see the O8 commit
// message.
export default function OwnershipRoute({ persona }: { persona: Persona }) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Ownership' }]} />
      <div className="min-h-0 flex-1 overflow-auto">
        <MyApps persona={persona} />
      </div>
    </div>
  )
}
