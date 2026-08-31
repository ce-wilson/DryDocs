import { useState } from 'react'
import { boltAllowed, type GraphResult } from '../lib/graph'
import { labelsNamedIn } from '../lib/cypher-labels'
import { createBoltAccess } from '../lib/neo4j'
import { listApps, createSession, runAgent, type AdkEvent } from '../lib/adk'
import type { Role } from '../lib/auth'

const env = import.meta.env

const PRESETS: Record<string, string> = {
  // Labels/edge/property per gate self-documentation-code-graph: §C1 ruled
  // :CodeModule (option (b) :CodeFile was rejected), §D1 ruled :IMPORTS, and the
  // loader writes snake_case `rel_path`. Kept in step with DEFAULT_QUERY in
  // agents/graph_query/agent.py, which is section 2's empty-message default.
  'C4 components (depgraph)':
    'MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) RETURN a.rel_path AS source, b.rel_path AS target LIMIT 25',
  'Label counts': 'MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC',
}

// O30: styled inline via Tailwind/token classes (App.css retired). The code-bg
// hardcode (#0a111b) is the mockup's dark language, kept for parity (O32 owns
// the light pass).
const NOTE = 'mt-2 text-[13px] leading-[1.55] text-muted'
const ROW = 'my-2 flex flex-wrap items-center gap-2'
const BTN = 'rounded-sm border border-edge bg-bg-2 px-[0.7rem] py-[0.35rem] hover:border-faint'
const BTN_PRIMARY =
  'rounded-sm border border-blue-bright bg-blue px-[0.9rem] py-[0.35rem] font-semibold text-white hover:bg-blue-bright'
const STATUS = 'break-all text-[0.85rem] text-muted'
const SECTION = 'my-4 rounded-md border border-edge bg-panel p-4'
const H2 = 'mb-1.5 text-[15px] font-semibold'

function ResultTable({ result }: { result: GraphResult }) {
  if (result.rows.length === 0) return <p>0 rows.</p>
  return (
    <div className="max-h-[420px] overflow-x-auto overflow-y-auto">
      <table className="w-full border-collapse text-[12.5px]">
        <thead>
          <tr>
            {result.keys.map((k) => (
              <th key={k} className="border-b border-edge bg-panel-2 px-3 py-2 text-left font-semibold text-[#c8d2de]">
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, i) => (
            <tr key={i}>
              {result.keys.map((k) => (
                <td key={k} className="border-b border-edge-soft px-3 py-2 font-mono text-[11.5px] text-[#b9c4d2]">
                  {JSON.stringify(row[k])}
                </td>
              ))}
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
      setCypherStatus(`${res.rows.length} rows${await emptyPresetDiagnosis(access, res)}`)
    } catch (e) {
      setCypherStatus(String(e))
    }
  }

  // O84 clause (c): ZERO ROWS FROM A PRESET IS NOT SELF-EXPLANATORY. A preset
  // whose labels drifted from the schema returns success with an empty result,
  // which reads exactly like an empty graph — that is how two first-party call
  // sites named a rejected label for weeks with a green suite behind them. So an
  // empty preset result asks the database which labels it actually has and says
  // which of the named ones are missing.
  //
  // PRESETS ONLY, per clause (d). The box below is a raw-Cypher bench and
  // user-typed queries are none of this function's business; widening it into a
  // general validator is a product decision nobody has made. Identity is by
  // exact match against PRESETS, so an edited preset is user Cypher again.
  async function emptyPresetDiagnosis(
    access: ReturnType<typeof createBoltAccess>,
    res: GraphResult,
  ): Promise<string> {
    if (res.rows.length > 0) return ''
    if (!Object.values(PRESETS).includes(query)) return ''
    const named = labelsNamedIn(query)
    if (named.length === 0) return ''
    try {
      const present = await access.runRead('CALL db.labels() YIELD label RETURN label')
      const have = new Set(present.rows.map((r) => String(r.label)))
      const missing = named.filter((l) => !have.has(l))
      if (missing.length === 0) return ''
      return ` — but database '${database}' has no ${missing.join(', ')} label, so this is a preset naming nothing real rather than an empty result`
    } catch {
      // The diagnosis is a courtesy; a database that will not answer
      // db.labels() must not turn a successful query into an error.
      return ''
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

  // ADK sessions are scoped to the signed-in persona (was hardcoded 'local-dev')
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
      <p className={NOTE}>
        Direct bolt + ADK test surface (pre-dates the O1 access decision). Flow 1 talks
        straight to the local Docker Neo4j over bolt/WebSocket; flow 2 goes through the
        Google ADK api_server as persona <code>{personaId}</code>.
      </p>

      {!boltAllowed(role) && (
        <section className={SECTION}>
          <h2 className={H2}>1 · Direct bolt — dev-mode only</h2>
          <p className={NOTE}>
            The raw-Cypher panel is a development tool: it renders only in dev builds, to
            admins (ADR 0005 — bolt-from-browser is not the deployment path). Deployment
            reads go through the drydocs-api adapter.
          </p>
        </section>
      )}
      {boltAllowed(role) && (
      <section className={SECTION}>
        <h2 className={H2}>1 · Basic flow — Cypher → Neo4j → C4-ish rows</h2>
        <div className={ROW}>
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
        <div className={ROW}>
          {Object.entries(PRESETS).map(([name, q]) => (
            <button key={name} className={BTN} onClick={() => setQuery(q)}>{name}</button>
          ))}
        </div>
        <textarea className="w-full font-mono" rows={4} value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className={ROW}>
          <button className={BTN_PRIMARY} onClick={onRunCypher}>Run Cypher</button>
          <span className={STATUS}>{cypherStatus}</span>
        </div>
        {result && <ResultTable result={result} />}
      </section>
      )}

      <section className={SECTION}>
        <h2 className={H2}>2 · Agent flows — ADK api_server</h2>
        <div className={ROW}>
          <input value={adkUrl} onChange={(e) => setAdkUrl(e.target.value)} title="ADK server URL" />
          <button className={BTN} onClick={onListApps}>List apps</button>
          <select value={app} onChange={(e) => { setApp(e.target.value); setSessionId('') }}>
            {(apps.length ? apps : ['graph_query', 'core_ingest', 'controlm_fix']).map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <textarea
          className="w-full font-mono"
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={
            app === 'graph_query'
              ? 'Optional: a Cypher read query (empty = default C4 component query). No LLM key needed.'
              : 'Message for the agent (needs GOOGLE_API_KEY in agents/.env).'
          }
        />
        <div className={ROW}>
          <button className={BTN_PRIMARY} onClick={onRunAgent}>Run agent</button>
          <span className={STATUS}>{agentStatus} {sessionId && `· session ${sessionId}`}</span>
        </div>
        {events && (
          <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-sm border border-edge-soft bg-[#0a111b] p-3 font-mono text-[0.8rem]">
            {events
              .map((e) => e.content?.parts?.map((p) => p.text).filter(Boolean).join('\n') ?? JSON.stringify(e))
              .join('\n---\n')}
          </pre>
        )}
      </section>
    </main>
  )
}
