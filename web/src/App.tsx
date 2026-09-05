import { useEffect, useState } from 'react'
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
import OverviewRoute from './routes/OverviewRoute'
import ExplorerRoute from './routes/explorer/ExplorerRoute'
import ExplorerLiveRoute from './routes/explorer/ExplorerLiveRoute'
import ExplorerTowerRoute from './routes/explorer/ExplorerTowerRoute'
import AskRoute from './routes/AskRoute'
import OwnershipRoute from './routes/OwnershipRoute'
import AssetPathRoute from './routes/AssetPathRoute'
import IntakeRoute from './routes/IntakeRoute'
import ConsoleRoute from './routes/ConsoleRoute'
import MappingsRoute from './routes/MappingsRoute'
import LineageRoute from './routes/LineageRoute'
import AdminConfigRoute from './routes/AdminConfigRoute'
import LoadsRoute from './routes/LoadsRoute'
import RunbooksRoute from './routes/RunbooksRoute'
import RemediationRoute from './routes/RemediationRoute'
import GraphCanvasRoute from './routes/GraphCanvasRoute'
import DocsRoute from './routes/DocsRoute'
import SoftwareRoute from './routes/SoftwareRoute'
import GatesRoute from './routes/GatesRoute'
import LoadMapRoute from './routes/LoadMapRoute'
import UnderTheHoodRoute from './routes/UnderTheHoodRoute'
import './App.css'

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
    let cancelled = false
    void signIn(as, secret)
      .then((s) => {
        if (!cancelled) setSession(s)
      })
      .catch((err: unknown) => console.warn(`?as=${as} sign-in refused:`, err))
    return () => {
      cancelled = true
    }
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
        <Route element={<RouteAccessGate role={persona.role} />}>
          <Route index element={<OverviewRoute persona={persona} />} />

          <Route path="explorer" element={<ExplorerRoute persona={persona} />} />
          <Route path="explorer/live" element={<ExplorerLiveRoute personaId={session.personaId} />} />
          <Route path="explorer/tower/:towerKey" element={<ExplorerTowerRoute persona={persona} />} />

          {/* R5: the Ask spoke — every persona, including non-admin (the whole
              point: agentic Q&A without the admin-only raw-Cypher console). */}
          <Route path="ask" element={<AskRoute persona={persona} />} />

          <Route path="lineage" element={<LineageRoute persona={persona} />} />
          <Route path="lineage/asset/:assetId" element={<LineageRoute persona={persona} />} />
          <Route path="ownership" element={<OwnershipRoute persona={persona} />} />
          <Route path="ownership/asset/:assetId" element={<AssetPathRoute />} />
          <Route path="runbooks" element={<RunbooksRoute persona={persona} />} />
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
          <Route path="docs" element={<DocsRoute persona={persona} />} />
          <Route path="docs/document/:docId" element={<DocsRoute persona={persona} />} />
          <Route path="software" element={<SoftwareRoute persona={persona} />} />
          <Route path="gates" element={<GatesRoute />} />
          <Route path="loads" element={<LoadsRoute persona={persona} />} />
          <Route path="loads/run/:runId" element={<LoadsRoute persona={persona} />} />
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
    </Routes>
    </GraphAccessProvider>
  )
}
