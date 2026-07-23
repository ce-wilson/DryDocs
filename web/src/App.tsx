import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { currentSession, personaFor, PERSONAS, signIn, signOut, type Session } from './lib/auth'
import SignIn from './components/SignIn'
import Shell, { type EnvName } from './layout/Shell'
import OverviewRoute from './routes/OverviewRoute'
import ExplorerRoute from './routes/explorer/ExplorerRoute'
import ExplorerLiveRoute from './routes/explorer/ExplorerLiveRoute'
import ExplorerTowerRoute from './routes/explorer/ExplorerTowerRoute'
import OwnershipRoute from './routes/OwnershipRoute'
import AssetPathRoute from './routes/AssetPathRoute'
import ConsoleRoute from './routes/ConsoleRoute'
import MappingsRoute from './routes/MappingsRoute'
import LineageRoute from './routes/LineageRoute'
import AdminConfigRoute from './routes/AdminConfigRoute'
import LoadsRoute from './routes/LoadsRoute'
import RunbooksRoute from './routes/RunbooksRoute'
import RemediationRoute from './routes/RemediationRoute'
import DocsRoute from './routes/DocsRoute'
import GatesRoute from './routes/GatesRoute'
import UnderTheHoodRoute from './routes/UnderTheHoodRoute'
import './App.css'

// O8 rebuild: real react-router routes (deep-linkable, back-button safe —
// design-review's 🔴 #1 finding against the old `#/...` hash router) replace
// the O2 hash-based App. Mock auth (lib/auth.ts) is unchanged: it still gates
// everything behind a persona picker, pending the O1 access-path ADR; only
// what happens AFTER sign-in is new.
export default function App() {
  const [session, setSession] = useState<Session | null>(() => {
    // DEV-only headless-verification affordance (the verify skill drives
    // pages via `?as=<personaId>`): baked OUT of production bundles by the
    // import.meta.env.DEV constant, same construction as boltAllowed().
    if (import.meta.env.DEV) {
      const as = new URLSearchParams(window.location.search).get('as')
      if (as && PERSONAS.some((p) => p.id === as)) return signIn(as)
    }
    return currentSession()
  })
  const [env, setEnv] = useState<EnvName>('Dev')

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

        <Route path="lineage" element={<LineageRoute persona={persona} />} />
        <Route path="lineage/asset/:assetId" element={<LineageRoute persona={persona} />} />
        <Route path="ownership" element={<OwnershipRoute persona={persona} />} />
        <Route path="ownership/asset/:assetId" element={<AssetPathRoute />} />
        <Route path="runbooks" element={<RunbooksRoute persona={persona} />} />
        <Route path="remediation" element={<RemediationRoute />} />
        <Route path="docs" element={<DocsRoute persona={persona} />} />
        <Route path="docs/document/:docId" element={<DocsRoute persona={persona} />} />
        <Route path="gates" element={<GatesRoute />} />
        <Route path="loads" element={<LoadsRoute persona={persona} />} />
        <Route path="loads/run/:runId" element={<LoadsRoute persona={persona} />} />
        <Route path="under-the-hood" element={<UnderTheHoodRoute />} />

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
