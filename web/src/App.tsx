import { useEffect, useState } from 'react'
import { currentSession, personaFor, signOut, type Session } from './lib/auth'
import { defaultViewFor, hashFor, hashForRoute, parseRoute, type Route } from './lib/views'
import { isTowerKey } from './data/towers'
import SignIn from './components/SignIn'
import Shell, { type EnvName } from './components/Shell'
import Landing from './components/Landing'
import MyApps from './components/MyApps'
import CypherConsole from './components/CypherConsole'
import Governance from './components/Governance'
import './App.css'

// Orchestrator: mock session (lib/auth.ts) + hash-based routing gated by the
// role registry (lib/views.ts). No router by design — revisit post-O1 if the
// design pass grows past a handful of views.
export default function App() {
  const [session, setSession] = useState<Session | null>(() => currentSession())
  const [route, setRoute] = useState<Route>(() =>
    session ? parseRoute(window.location.hash, personaFor(session), isTowerKey) : { view: 'my-apps' },
  )
  const [env, setEnv] = useState<EnvName>('Dev')

  useEffect(() => {
    if (!session) return
    const persona = personaFor(session)
    const sync = () => {
      const r = parseRoute(window.location.hash, persona, isTowerKey)
      // normalize unauthorized/unknown deep links to what the persona may see
      if (window.location.hash !== hashForRoute(r)) {
        window.history.replaceState(null, '', hashForRoute(r))
      }
      setRoute(r)
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
      activeView={route.view}
      env={env}
      onEnvChange={setEnv}
      onSignOut={handleSignOut}
    >
      {route.view === 'landing' && <Landing tower={route.tower} persona={persona} />}
      {route.view === 'my-apps' && <MyApps persona={persona} />}
      {route.view === 'console' && <CypherConsole personaId={session.personaId} role={session.role} />}
      {route.view === 'governance' && <Governance />}
    </Shell>
  )
}
