import { useMemo, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'

import type { Persona } from '../lib/auth'
import { apiBaseUrl } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import { CANVAS_ROUTES, isCanvasSpecId, type CanvasNode } from '../lib/nvl-mapping'
import { canAccessModule, MODULES } from '../modules/registry'
import ModuleToolbar from '../layout/ModuleToolbar'
import SpecGraphPane from '../components/SpecGraphPane'
import EmptyState from '../components/ui/EmptyState'

// `/graph/:specId` — one canvas surface, full page (O86).
//
// WHY A ROUTE AND NOT A MAXIMIZE TOGGLE. O81 shipped the canvas inside the
// data-frame strip, which is about 215px at the default split: the whole graph
// fits, and its captions are small. A CSS maximize (~20 lines) or the
// Fullscreen API (~10) would both solve the height and neither produces a link
// anybody can send, or a view the back button understands. Site-plan §1 locked
// the console into real routes for exactly that, and `lineage/asset/:assetId`
// and `explorer/tower/:towerKey` are the same shape already in the router.
//
// THE SPEC ID IS WHITELISTED, NEVER PASSED THROUGH. CANVAS_ROUTES is a closed
// map, so an id outside it renders a named refusal here rather than reaching
// drydocs-api. That is not a data-exposure fix — the API refuses anything
// unregistered anyway — it is a refusal to INVITE the attempt, and it keeps
// ADR 0005's rule that the console never chooses a query the registry did not
// review.
//
// IT GATES LIKE ITS SIBLINGS. The surface's HOST module supplies the rule, so
// this page applies whatever /runbooks or /explorer applies. A deep link is
// reachable by anyone holding it and the server re-resolves the real role from
// the token on every call, so the data is safe either way; the point is that a
// full-page view must not become the one page that does not check.
//
// NO SESSION IN THE URL, and none is needed: the token lives in localStorage
// under drydocs.session.v2, so a same-origin tab boots the app and finds it. A
// token in a query string would land in history, in logs, and in any link
// somebody shares.

export default function GraphCanvasRoute({ persona }: { persona: Persona }) {
  const { specId } = useParams<{ specId: string }>()
  const [selected, setSelected] = useState<CanvasNode | null>(null)
  const access = useMemo(() => createApiAccess(apiBaseUrl(), persona.id), [persona.id])

  if (!isCanvasSpecId(specId)) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Graph canvas' }]} />
        <EmptyState
          title="Not a canvas surface"
          hint={
            `"${specId ?? ''}" is not one of the reviewed specs this console can draw. ` +
            `The canvas surfaces are: ${Object.keys(CANVAS_ROUTES).join(', ')}.`
          }
        />
      </div>
    )
  }

  const surface = CANVAS_ROUTES[specId]
  const host = MODULES.find((m) => m.id === surface.module)
  // The host module is the gate. A surface whose module has been removed from
  // the registry is a build-time impossibility (CANVAS_ROUTES is typed against
  // ModuleId), so this is belt-and-braces rather than an expected branch — but
  // it fails CLOSED, because the alternative is a page that renders when its
  // rule cannot be found.
  if (!host || !canAccessModule(host.access, persona.role)) {
    return <Navigate to="/" replace />
  }

  return (
    // `h-full min-h-0 flex-col` is load-bearing, not cosmetic: the shell's
    // <main> is a grid area, so a route that does not claim the height gives
    // its flex children none. The canvas then mounts into a ZERO-HEIGHT
    // element, NVL reports its node count in the header and draws nothing —
    // which looks like a data bug and is a layout one. Same root every other
    // full-height route uses (ModuleTemplate).
    <div className="flex h-full min-h-0 flex-col">
      {/* The crumb back to the host module is the way OUT of the full page,
          and it is the shape every other parameterised route already uses. */}
      <ModuleToolbar
        crumbs={[
          { label: 'Home', to: '/' },
          { label: host.label, to: host.path },
          { label: surface.title },
        ]}
      />
      <div className="flex min-h-0 flex-1 flex-col gap-2 p-4">
        <h2 tabIndex={-1} data-view-heading className="text-lg font-semibold text-text outline-none">
          {surface.title}
          <span className="ml-2 font-mono text-[11px] font-normal text-muted">{specId}</span>
        </h2>
        <div className="min-h-0 flex-1">
        <SpecGraphPane
          access={access}
          specId={specId}
          title={surface.title}
          selected={selected}
          onSelect={setSelected}
          fullPage
        />
        </div>
      </div>
    </div>
  )
}
