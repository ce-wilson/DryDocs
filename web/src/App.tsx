import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { currentSession, personaFor, signOut, type Session } from './lib/auth'
import SignIn from './components/SignIn'
import Shell, { type EnvName } from './layout/Shell'
import OverviewRoute from './routes/OverviewRoute'
import ExplorerRoute from './routes/explorer/ExplorerRoute'
import ExplorerLiveRoute from './routes/explorer/ExplorerLiveRoute'
import ExplorerTowerRoute from './routes/explorer/ExplorerTowerRoute'
import OwnershipRoute from './routes/OwnershipRoute'
import SkeletonModuleRoute from './routes/SkeletonModuleRoute'
import ConsoleRoute from './routes/ConsoleRoute'
import './App.css'

// O8 rebuild: real react-router routes (deep-linkable, back-button safe —
// design-review's 🔴 #1 finding against the old `#/...` hash router) replace
// the O2 hash-based App. Mock auth (lib/auth.ts) is unchanged: it still gates
// everything behind a persona picker, pending the O1 access-path ADR; only
// what happens AFTER sign-in is new.
export default function App() {
  const [session, setSession] = useState<Session | null>(() => currentSession())
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

        <Route path="lineage" element={<SkeletonModuleRoute id="lineage" />} />
        <Route path="ownership" element={<OwnershipRoute persona={persona} />} />
        <Route path="runbooks" element={<SkeletonModuleRoute id="runbooks" />} />
        <Route path="remediation" element={<SkeletonModuleRoute id="remediation" />} />
        <Route path="docs" element={<SkeletonModuleRoute id="docs" />} />
        <Route path="gates" element={<SkeletonModuleRoute id="gates" />} />
        <Route path="loads" element={<SkeletonModuleRoute id="loads" />} />

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
