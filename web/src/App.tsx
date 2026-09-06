import { lazy, useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import {
  canAccessIntake,
  currentSession,
  personaFor,
  PERSONAS,
  SESSION_REJECTED_EVENT,
  signIn,
  signOut,
  type Session,
} from './lib/auth'
import SignIn from './components/SignIn'
import Shell, { type EnvName } from './layout/Shell'
import { GraphAccessProvider } from './data/GraphAccessProvider'
import RouteAccessGate from './layout/RouteAccessGate'
import RouteErrorBoundary from './layout/RouteErrorBoundary'
import OverviewRoute from './routes/OverviewRoute'
import ExplorerRoute from './routes/explorer/ExplorerRoute'
import ExplorerLiveRoute from './routes/explorer/ExplorerLiveRoute'
import ExplorerTowerRoute from './routes/explorer/ExplorerTowerRoute'
import AskRoute from './routes/AskRoute'
import OwnershipRoute from './routes/OwnershipRoute'
import AssetPathRoute from './routes/AssetPathRoute'
import IntakeRoute from './routes/IntakeRoute'
import LineageRoute from './routes/LineageRoute'
import LoadsRoute from './routes/LoadsRoute'
import RunbooksRoute from './routes/RunbooksRoute'
import GraphCanvasRoute from './routes/GraphCanvasRoute'
import DocsRoute from './routes/DocsRoute'
import './App.css'

// WEB7 — CODE SPLITTING FOLLOWS THE AUTHORIZATION BOUNDARY, not file size.
//
// A4: the route gate was a RENDER decision and not a DELIVERY one. Every route
// was a static import in one 3.7 MB chunk, so a user-tier persona downloaded
// the enforcement matrix (295 KB) and the gate record (44 KB) for pages it can
// never open — and could read both out of devtools. Hiding a page from someone
// who has already been sent it is not an authorization boundary.
//
// THE SET IS EXACTLY THE GATED SET. Every module registry.ts marks with an
// `access` level, plus the three GATED_SURFACES, and nothing else: a chunk is
// admissible to a role or it is not, and splitting anything else here would be
// a size decision wearing this item's clothes. modules/lazyRoutes.test.ts
// derives the set from the registry and fails when the two disagree, so a new
// gated module cannot arrive shipped-to-everyone.
//
// WHAT IS DELIBERATELY NOT SPLIT: load-map.json (56 KB) is imported by
// lineage/laneBasis.ts, and /lineage is open to every role. It is admissible to
// a user, so by this item's own rule it stays in the initial chunk.
const MappingsRoute = lazy(() => import('./routes/MappingsRoute'))
const AdminConfigRoute = lazy(() => import('./routes/AdminConfigRoute'))
const ConsoleRoute = lazy(() => import('./routes/ConsoleRoute'))
const RemediationRoute = lazy(() => import('./routes/RemediationRoute'))
const SoftwareRoute = lazy(() => import('./routes/SoftwareRoute'))
const GatesRoute = lazy(() => import('./routes/GatesRoute'))
const LoadMapRoute = lazy(() => import('./routes/LoadMapRoute'))
const UnderTheHoodRoute = lazy(() => import('./routes/UnderTheHoodRoute'))


// O8 rebuild: real react-router routes (deep-linkable, back-button safe —
// design-review's 🔴 #1 finding against the old `#/...` hash router) replace
// the O2 hash-based App. O69 replaced the mock: sign-in now proves a secret to
// drydocs-api (lib/auth.ts), and a session the server refuses drops the whole
// console back here rather than leaving a shell whose panels all 401.
export default function App() {
  const [session, setSession] = useState<Session | null>(() => currentSession())
  const [env, setEnv] = useState<EnvName>('Dev')

  // DEV-only headless-verification affordance (the verify skill drives pages
  // via `?as=<personaId>`), baked OUT of production bundles by the
  // import.meta.env.DEV constant, same construction as boltAllowed(). It is a
  // real sign-in now, so it needs a real secret: VITE_DEV_CONSOLE_SECRET, set
  // in the dev shell beside the one scripts/set_console_credential.py stored.
  // No default and no fallback — a baked-in dev password is the exact thing a
  // credential step exists to remove.
  useEffect(() => {
    if (!import.meta.env.DEV || session) return
    const as = new URLSearchParams(window.location.search).get('as')
    if (!as || !PERSONAS.some((p) => p.id === as)) return
    const secret = import.meta.env.VITE_DEV_CONSOLE_SECRET as string | undefined
    if (!secret) {
      console.warn(
        `?as=${as} needs VITE_DEV_CONSOLE_SECRET set to that account's console secret; ` +
          'showing the sign-in screen instead',
      )
      return
    }
    const ctl = new AbortController()
    void signIn(as, secret)
      .then((s) => {
        if (!ctl.signal.aborted) setSession(s)
      })
      .catch((err: unknown) => console.warn(`?as=${as} sign-in refused:`, err))
    return () => ctl.abort()
  }, [session])

  // One 401 anywhere ends the session everywhere. Without this the shell keeps
  // rendering while every request behind it fails, which reads as a broken
  // console rather than an expired one.
  useEffect(() => {
    const drop = () => setSession(null)
    window.addEventListener(SESSION_REJECTED_EVENT, drop)
    return () => window.removeEventListener(SESSION_REJECTED_EVENT, drop)
  }, [])

  function handleSignIn(s: Session) {
    setSession(s)
  }

  function handleSignOut() {
    signOut()
    setSession(null)
  }

  if (!session) return <SignIn onSignIn={handleSignIn} />

  const persona = personaFor(session)

  return (
    // WEB12: ONE GraphAccess for the session, above the routes. Sixteen routes
    // used to build their own with useMemo(() => createApiAccess(...)); one
    // client per session is also what lets the R4 ephemeral specs the Ask
    // agent registers resolve for this session's reads.
    <GraphAccessProvider personaId={session.personaId}>
    <Routes>
      <Route
        element={<Shell session={session} persona={persona} env={env} onEnvChange={setEnv} onSignOut={handleSignOut} />}
      >
        {/* WEB3: ONE gate for every route below, derived from the module
            registry (canAccessPath). It replaces six inline
            `role === 'steward' || role === 'admin'` predicates — the shape that
            already shipped the O59 bug, where a module was hidden from the nav
            and still reachable by URL because the two expressions of the same
            policy drifted. A pathless layout route so it runs on every
            navigation and a new module cannot arrive un-gated. */}
        {/* WEB5: INSIDE the access gate, so a refused route redirects rather
            than rendering a boundary, and OUTSIDE every page, so one render
            throw breaks one panel instead of blanking the console. */}
        <Route element={<RouteAccessGate role={persona.role} />}>
        <Route element={<RouteErrorBoundary />}>
          <Route index element={<OverviewRoute persona={persona} />} />

          <Route path="explorer" element={<ExplorerRoute persona={persona} />} />
          <Route path="explorer/live" element={<ExplorerLiveRoute />} />
          <Route path="explorer/tower/:towerKey" element={<ExplorerTowerRoute persona={persona} />} />

          {/* R5: the Ask spoke — every persona, including non-admin (the whole
              point: agentic Q&A without the admin-only raw-Cypher console). */}
          <Route path="ask" element={<AskRoute persona={persona} />} />

          <Route path="lineage" element={<LineageRoute />} />
          <Route path="lineage/asset/:assetId" element={<LineageRoute />} />
          <Route path="ownership" element={<OwnershipRoute persona={persona} />} />
          <Route path="ownership/asset/:assetId" element={<AssetPathRoute />} />
          <Route path="runbooks" element={<RunbooksRoute />} />
          {/* O59 set this module's registry access to 'sme'. That hid the nav
              entry but left the ROUTE open to anyone typing the URL. The gate is
              RouteAccessGate above now, derived from that same registry entry —
              there is no per-route predicate here to fall out of step with it. */}
          <Route path="remediation" element={<RemediationRoute />} />
          {/* O86: one canvas surface, full page. The spec id is whitelisted
              against CANVAS_ROUTES inside the route, and the route gates on the
              surface's HOST module — /graph/:specId is not itself a module path,
              so RouteAccessGate lets it through and the host check inside is the
              gate (canAccessModule, same function, same vocabulary). */}
          <Route path="graph/:specId" element={<GraphCanvasRoute persona={persona} />} />
          <Route path="docs" element={<DocsRoute />} />
          <Route path="docs/document/:docId" element={<DocsRoute />} />
          <Route path="software" element={<SoftwareRoute persona={persona} />} />
          <Route path="gates" element={<GatesRoute />} />
          <Route path="loads" element={<LoadsRoute />} />
          <Route path="loads/run/:runId" element={<LoadsRoute />} />
          <Route path="load-map" element={<LoadMapRoute />} />
          <Route path="under-the-hood" element={<UnderTheHoodRoute />} />

          {/* O47: the intake persona (?as=neo) plus steward/admin. This is the
              ONE route that keeps its own gate: `access` is a role vocabulary and
              this grant is persona-scoped, so canAccessIntake stays in auth.ts
              and registry.ts's PERSONA_SCOPED_PATHS declares the exception. The
              vitest asserts it is the only one. */}
          <Route
            path="intake"
            element={canAccessIntake(persona) ? <IntakeRoute persona={persona} /> : <Navigate to="/" replace />}
          />

          <Route path="mappings" element={<MappingsRoute persona={persona} />} />
          <Route path="admin/config" element={<AdminConfigRoute />} />
          <Route
            path="console"
            element={<ConsoleRoute personaId={session.personaId} role={session.role} />}
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        </Route>
      </Route>
    </Routes>
    </GraphAccessProvider>
  )
}
