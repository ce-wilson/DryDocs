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
    <Routes>
      <Route
        element={<Shell session={session} persona={persona} env={env} onEnvChange={setEnv} onSignOut={handleSignOut} />}
      >
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
        <Route path="remediation" element={<RemediationRoute />} />
        <Route path="docs" element={<DocsRoute persona={persona} />} />
        <Route path="docs/document/:docId" element={<DocsRoute persona={persona} />} />
        {/* FB-03: SME designation (steward+admin) from the module registry */}
        <Route
          path="software"
          element={
            persona.role === 'steward' || persona.role === 'admin' ? (
              <SoftwareRoute persona={persona} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="gates"
          element={persona.role === 'steward' || persona.role === 'admin' ? <GatesRoute /> : <Navigate to="/" replace />}
        />
        <Route path="loads" element={<LoadsRoute persona={persona} />} />
        <Route path="loads/run/:runId" element={<LoadsRoute persona={persona} />} />
        {/* O57: SME designation from the module registry — same gate as
            /software and /gates, for the same reason (governance state). */}
        <Route
          path="load-map"
          element={
            persona.role === 'steward' || persona.role === 'admin' ? <LoadMapRoute /> : <Navigate to="/" replace />
          }
        />
        <Route
          path="under-the-hood"
          element={persona.role === 'steward' || persona.role === 'admin' ? <UnderTheHoodRoute /> : <Navigate to="/" replace />}
        />

        {/* O47: the intake persona (?as=neo) plus steward/admin — the intake
            page's gate lives in auth.ts (canAccessIntake), because "SME" is a
            persona, not a fourth role tier. */}
        <Route
          path="intake"
          element={canAccessIntake(persona) ? <IntakeRoute persona={persona} /> : <Navigate to="/" replace />}
        />

        {/* O13: steward + admin only — the server enforces the same boundary
            on /mappings/*; steward still has NO /console (Cypher sandbox). */}
        <Route
          path="mappings"
          element={
            persona.role === 'steward' || persona.role === 'admin' ? (
              <MappingsRoute persona={persona} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* O12: admin persona only (O2 gating) — the traceability lens. */}
        <Route
          path="admin/config"
          element={persona.role === 'admin' ? <AdminConfigRoute /> : <Navigate to="/" replace />}
        />

        <Route
          path="console"
          element={
            persona.role === 'admin' ? (
              <ConsoleRoute personaId={session.personaId} role={session.role} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
