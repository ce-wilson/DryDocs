import { useState } from 'react'
import { boltAllowed, type GraphResult } from '../lib/graph'
import { createBoltAccess } from '../lib/neo4j'
import { listApps, createSession, runAgent, type AdkEvent } from '../lib/adk'
import type { Role } from '../lib/auth'

const env = import.meta.env

const PRESETS: Record<string, string> = {
  'C4 components (depgraph)':
    'MATCH (a:CodeFile)-[:DEPENDS_ON]->(b:CodeFile) RETURN a.relPath AS source, b.relPath AS target LIMIT 25',
  'Label counts': 'MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC',
}

function ResultTable({ result }: { result: GraphResult }) {
  if (result.rows.length === 0) return <p>0 rows.</p>
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>{result.keys.map((k) => <th key={k}>{k}</th>)}</tr>
        </thead>
        <tbody>
          {result.rows.map((row, i) => (
            <tr key={i}>
              {result.keys.map((k) => <td key={k}>{JSON.stringify(row[k])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function CypherConsole({ personaId, role }: { personaId: string; role: Role }) {
  // --- dev-mode flow: browser -> bolt adapter -> Neo4j (GraphAccess seam) -----
  // Password is form-entered ONLY — never seeded from VITE_* env, which Vite
  // inlines into the built bundle (ADR 0005 decision 4).
  const [uri, setUri] = useState(env.VITE_NEO4J_URI ?? 'bolt://localhost:7687')
  const [user, setUser] = useState(env.VITE_NEO4J_USER ?? 'neo4j')
  const [password, setPassword] = useState('')
  const [database, setDatabase] = useState(env.VITE_NEO4J_DATABASE ?? 'neo4j')
  const [query, setQuery] = useState(PRESETS['C4 components (depgraph)'])
  const [result, setResult] = useState<GraphResult | null>(null)
  const [cypherStatus, setCypherStatus] = useState('')

  async function onRunCypher() {
    setCypherStatus('running…')
    setResult(null)
    try {
      const access = createBoltAccess({ uri, user, password, database })
      const res = await access.runRead(query)
      setResult(res)
      setCypherStatus(`${res.rows.length} rows`)
    } catch (e) {
      setCypherStatus(String(e))
    }
  }

  // --- agent flows: browser -> adk api_server -> Neo4j ------------------------
  const [adkUrl, setAdkUrl] = useState(env.VITE_ADK_URL ?? 'http://localhost:8000')
  const [apps, setApps] = useState<string[]>([])
  const [app, setApp] = useState('graph_query')
  const [sessionId, setSessionId] = useState('')
  const [message, setMessage] = useState('')
  const [events, setEvents] = useState<AdkEvent[] | null>(null)
  const [agentStatus, setAgentStatus] = useState('')

  // ADK sessions are scoped to the signed-in mock persona (was hardcoded 'local-dev')
  const userId = personaId

  async function onListApps() {
    setAgentStatus('listing…')
    try {
      const names = await listApps(adkUrl)
      setApps(names)
      if (names.length && !names.includes(app)) setApp(names[0])
      setAgentStatus(`${names.length} apps`)
    } catch (e) {
      setAgentStatus(String(e))
    }
  }

  async function onRunAgent() {
    setAgentStatus('running…')
    setEvents(null)
    try {
      let sid = sessionId
      if (!sid) {
        sid = `s_${Date.now()}`
        await createSession(adkUrl, app, userId, sid)
        setSessionId(sid)
      }
      const evts = await runAgent(adkUrl, app, userId, sid, message)
      setEvents(evts)
      setAgentStatus(`${evts.length} events`)
    } catch (e) {
      setAgentStatus(String(e))
    }
  }

  return (
    <main>
      <h1 tabIndex={-1} data-view-heading className="outline-none">Console — admin sandbox</h1>
      <p className="note">
        Direct bolt + ADK test surface (pre-dates the O1 access decision). Flow 1 talks
        straight to the local Docker Neo4j over bolt/WebSocket; flow 2 goes through the
        Google ADK api_server as persona <code>{personaId}</code>.
      </p>

      {!boltAllowed(role) && (
        <section>
          <h2>1 · Direct bolt — dev-mode only</h2>
          <p className="note">
            The raw-Cypher panel is a development tool: it renders only in dev builds, to
            admins (ADR 0005 — bolt-from-browser is not the deployment path). Deployment
            reads go through the drydocs-api adapter.
          </p>
        </section>
      )}
      {boltAllowed(role) && (
      <section>
        <h2>1 · Basic flow — Cypher → Neo4j → C4-ish rows</h2>
        <div className="row">
          <input value={uri} onChange={(e) => setUri(e.target.value)} title="bolt URI" />
          <input value={user} onChange={(e) => setUser(e.target.value)} title="user" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
          />
          <input value={database} onChange={(e) => setDatabase(e.target.value)} title="database" />
        </div>
        <div className="row">
          {Object.entries(PRESETS).map(([name, q]) => (
            <button key={name} onClick={() => setQuery(q)}>{name}</button>
          ))}
        </div>
        <textarea rows={4} value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="row">
          <button className="primary" onClick={onRunCypher}>Run Cypher</button>
          <span className="status">{cypherStatus}</span>
        </div>
        {result && <ResultTable result={result} />}
      </section>
      )}

      <section>
        <h2>2 · Agent flows — ADK api_server</h2>
        <div className="row">
          <input value={adkUrl} onChange={(e) => setAdkUrl(e.target.value)} title="ADK server URL" />
          <button onClick={onListApps}>List apps</button>
          <select value={app} onChange={(e) => { setApp(e.target.value); setSessionId('') }}>
            {(apps.length ? apps : ['graph_query', 'core_ingest', 'controlm_fix']).map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <textarea
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={
            app === 'graph_query'
              ? 'Optional: a Cypher read query (empty = default C4 component query). No LLM key needed.'
              : 'Message for the agent (needs GOOGLE_API_KEY in agents/.env).'
          }
        />
        <div className="row">
          <button className="primary" onClick={onRunAgent}>Run agent</button>
          <span className="status">{agentStatus} {sessionId && `· session ${sessionId}`}</span>
        </div>
        {events && (
          <pre className="scroll">
            {events
              .map((e) => e.content?.parts?.map((p) => p.text).filter(Boolean).join('\n') ?? JSON.stringify(e))
              .join('\n---\n')}
          </pre>
        )}
      </section>
    </main>
  )
}
