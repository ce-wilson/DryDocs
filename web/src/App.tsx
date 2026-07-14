import { useEffect, useState } from 'react'
import { currentSession, personaFor, signOut, type Session } from './lib/auth'
import { hashFor, defaultViewFor, viewFromHash, type ViewId } from './lib/views'
import SignIn from './components/SignIn'
import Shell, { type EnvName } from './components/Shell'
import MyApps from './components/MyApps'
import CypherConsole from './components/CypherConsole'
import Governance from './components/Governance'
import './App.css'

// Orchestrator: mock session (lib/auth.ts) + hash-based view switching gated by
// the role registry (lib/views.ts). No router by design — revisit post-O1 if the
// design pass grows past a handful of views.
export default function App() {
  const [session, setSession] = useState<Session | null>(() => currentSession())
  const [view, setView] = useState<ViewId>(() =>
    session ? viewFromHash(window.location.hash, session.role) : 'my-apps',
  )
  const [env, setEnv] = useState<EnvName>('Dev')

  useEffect(() => {
    if (!session) return
    const sync = () => {
      const v = viewFromHash(window.location.hash, session.role)
      // normalize unauthorized/unknown deep links to the role's default view
      if (window.location.hash !== hashFor(v)) {
        window.history.replaceState(null, '', hashFor(v))
      }
      setView(v)
    }
    sync()
    window.addEventListener('hashchange', sync)
    return () => window.removeEventListener('hashchange', sync)
  }, [session])

  function handleSignIn(s: Session) {
    setSession(s)
    window.location.hash = hashFor(defaultViewFor(s.role))
  }

  function handleSignOut() {
    signOut()
    setSession(null)
    window.history.replaceState(null, '', window.location.pathname)
  }

  if (!session) return <SignIn onSignIn={handleSignIn} />

  const persona = personaFor(session)
  return (
    <Shell
      session={session}
      persona={persona}
      activeView={view}
      env={env}
      onEnvChange={setEnv}
      onSignOut={handleSignOut}
    >
      {view === 'my-apps' && <MyApps persona={persona} />}
      {view === 'console' && <CypherConsole personaId={session.personaId} />}
      {view === 'governance' && <Governance />}
    </Shell>
  )
}
