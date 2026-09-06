import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { canAccessPath } from '../modules/registry'

/** WEB3 — ONE route gate for the whole console, driven by the module registry.
 *
 * It is a pathless layout route wrapping every route inside the Shell, so it
 * runs on every navigation and asks `canAccessPath` what the current pathname
 * requires. That placement is the point of the item: six inline
 * `role === 'steward' || role === 'admin'` predicates used to sit on six route
 * elements, and the bug they caused (O59 — /remediation hidden from the nav and
 * still reachable by URL) was a MISSING one, not a wrong one. A per-route check
 * can be forgotten; a check nobody writes per route cannot.
 *
 * A refused route redirects to `/`, which is what each of the six predicates did
 * — the behaviour is unchanged, only its single source is new.
 *
 * `/intake` is not gated here: it admits the SME persona as well as the two
 * roles, so `canAccessIntake` keeps its route-level check (registry.ts's
 * PERSONA_SCOPED_PATHS records that, and the vitest asserts it is the only
 * exception).
 */
export default function RouteAccessGate({ role }: { role: 'user' | 'steward' | 'admin' }) {
  const { pathname } = useLocation()
  return canAccessPath(pathname, role) ? <Outlet /> : <Navigate to="/" replace />
}
