// O63 — ONE probe, asked by two surfaces.
//
// THE FAILURE THIS EXISTS FOR, because the shape of the module follows from it:
// the console came up with Neo4j, the API and Vite all green, every other view
// live against the graph, and Ask returned "Failed to fetch" and nothing else.
// The cause was a FOURTH service nobody had started — the agent server, which
// only the Ask spoke talks to. Starting it moved the failure to
// "ANTHROPIC_API_KEY is not set (agents/.env)": a completely different problem
// with a completely different fix, reached only by reading source and grepping
// .env files. Both states printed the same red line.
//
// So the console asks four questions, in dependency order, and reports them
// separately:
//
//   api      — is drydocs-api answering behind /api on this origin?
//   graph    — is the graph the console READS actually reachable, and which
//              database? (/api/graph-status; the API answers /health perfectly
//              well with no graph behind it, which is the whole point)
//   agent    — is the agent server up AND serving graph_qa? (/agent/list-apps)
//   provider — can that agent reach a model? (/agent/drydocs-health)
//
// TWO SURFACES, ONE IMPLEMENTATION (clause f). Ask's ladder is the REACTIVE
// view — it runs because something already failed — and the admin strip is the
// STANDING one, answering "is anything missing?" before a question is asked.
// Building the probe twice is how the two would end up disagreeing about what
// green means, so `readiness.ts` (the shell banner, a third consumer) now takes
// its API check from here too rather than keeping a parallel one.
//
// NEVER INVENT A GREEN, AND NEVER INVENT A RED EITHER (rule 1, the O56 honesty
// rule applied to liveness). The states are four, not two. A check whose
// DEPENDENCY is down is `not-checked` — not `down` — because it was never run:
// reporting the provider as broken when the agent server is simply absent would
// manufacture exactly the second failure this item exists to distinguish from
// the first.
//
// NO PORT, NO HOST, EVER (ADR 0020). Services are labelled by NAME. The bundle
// carries no deployment coordinate — web/scripts/checkDistCoordinates.mjs fails
// the build on one — and a port in a label would be both a lie in production
// and a guard failure.

import { agentBaseUrl, apiBaseUrl, sessionId, sessionRejected, sessionToken } from './auth'
import { createAuthedApi, createPublicApi } from './apiClient'
import { diagnoseNetworkFailure, isUpstreamDown, upstreamDownMessage } from './reachability'

/** The app the Ask spoke needs. A server that is up but does not serve THIS
 *  agent is not a green for this page's purpose. */
export const REQUIRED_AGENT_APP = 'graph_qa'

/** The provider probe agents/serve.py adds to the ADK app (its
 *  PROVIDER_PROBE_PATH; tests/stub_adk.py serves the same one). */
export const PROVIDER_PROBE_PATH = '/drydocs-health'

export type Readiness =
  | { state: 'unchecked' }
  | { state: 'checking' }
  | { state: 'up' }
  | { state: 'down'; message: string }

export async function probeHealth(apiUrl: string, signal?: AbortSignal): Promise<Readiness> {
  try {
    const res = await createPublicApi(apiUrl).GET('/health', { signal })
    if (res.response.ok) return { state: 'up' }
    if (isUpstreamDown(res.response.status)) {
      return { state: 'down', message: upstreamDownMessage(res.response.status, apiUrl) }
    }
    return { state: 'down', message: `the API answered ${res.response.status} on /health` }
  } catch (err) {
    if (signal?.aborted) return { state: 'unchecked' }
    // The thrown message is already the diagnosis when the typed client's
    // diagnosing fetch produced it; the direct call is the belt-and-braces path
    // for a failure that arrived some other way.
    const message = err instanceof Error ? err.message : String(err)
    if (message.includes('nothing answered') || message.includes('not answering')) {
      return { state: 'down', message }
    }
    return { state: 'down', message: (await diagnoseNetworkFailure(apiUrl)).message }
  }
}


export type ProbeState = 'not-checked' | 'checking' | 'ok' | 'down'

export type ServiceId = 'api' | 'graph' | 'agent' | 'provider'

export interface ServiceVerdict {
  id: ServiceId
  /** By NAME, never by port — see the ADR 0020 note above. */
  label: string
  state: ProbeState
  /** What was OBSERVED, verbatim where a server said it. Null when there is
   *  nothing to add (a plain green) or nothing to say (never ran). */
  detail: string | null
}

export interface ProbeResult {
  services: ServiceVerdict[]
  /** When the probe ran. Null before its first run — which is what lets the
   *  strip render "not checked" rather than a verdict it does not have. */
  checkedAt: Date | null
}

export const SERVICE_LABELS: Record<ServiceId, string> = {
  api: 'drydocs-api',
  graph: 'graph',
  agent: 'agent server',
  provider: 'agent provider',
}

const NOT_CHECKED: (id: ServiceId, detail?: string | null) => ServiceVerdict = (
  id,
  detail = null,
) => ({ id, label: SERVICE_LABELS[id], state: 'not-checked', detail })

function verdict(id: ServiceId, state: ProbeState, detail: string | null): ServiceVerdict {
  return { id, label: SERVICE_LABELS[id], state, detail }
}

/** The graph behind drydocs-api. Authenticated (steward/admin server-side), so
 *  a signed-out or user-tier caller gets `not-checked` with the reason rather
 *  than a red that would read as "the graph is down". */
export async function probeGraph(signal?: AbortSignal): Promise<ServiceVerdict> {
  if (!sessionToken()) return NOT_CHECKED('graph', 'sign in to check the graph')
  const api = createAuthedApi(apiBaseUrl(), {
    token: sessionToken,
    sessionId,
    rejected: sessionRejected,
  })
  try {
    const result = await api.GET('/graph-status', { signal })
    if (result.response.status === 403) {
      return NOT_CHECKED('graph', 'steward or admin only — not checked for this role')
    }
    if (!result.response.ok || !result.data) {
      return verdict('graph', 'down', `the API answered ${result.response.status}`)
    }
    const { reachable, database, detail } = result.data
    return reachable
      ? verdict('graph', 'ok', `database ${database}`)
      : verdict('graph', 'down', `${database} did not answer (${detail ?? 'no detail'})`)
  } catch {
    if (signal?.aborted) return NOT_CHECKED('graph')
    // The API itself is unreachable — which the `api` check already reports.
    // Saying it twice as a graph failure would double-count one outage.
    return NOT_CHECKED('graph', 'drydocs-api did not answer, so the graph was not checked')
  }
}

/** The agent server: up, and serving graph_qa.
 *
 *  A RAW FETCH RATHER THAN adk.listApps(), on purpose. That helper throws on a
 *  non-2xx before its caller ever sees the status, and the STATUS is exactly
 *  what separates the two failures rule 2 forbids collapsing: a thrown fetch
 *  means nothing answered on this origin, while a proxy 502/503/504 means the
 *  page's own server is up and the agent behind it is not. A probe is the one
 *  place that distinction is the product rather than an implementation detail. */
export async function probeAgent(signal?: AbortSignal): Promise<ServiceVerdict> {
  const base = agentBaseUrl()
  let response: Response
  try {
    response = await fetch(`${base}/list-apps`, { signal })
  } catch {
    if (signal?.aborted) return NOT_CHECKED('agent')
    return verdict(
      'agent',
      'down',
      `nothing answered at ${base} on this page's own origin — the server that serves this page is not answering`,
    )
  }
  if (isUpstreamDown(response.status)) {
    return verdict('agent', 'down', upstreamDownMessage(response.status, base))
  }
  if (!response.ok) {
    return verdict('agent', 'down', `${base}/list-apps answered ${response.status}`)
  }
  let apps: unknown
  try {
    apps = await response.json()
  } catch {
    return verdict('agent', 'down', `${base}/list-apps did not return JSON`)
  }
  if (!Array.isArray(apps)) {
    return verdict('agent', 'down', `${base}/list-apps did not return a list`)
  }
  if (!apps.includes(REQUIRED_AGENT_APP)) {
    // Up, but not serving what Ask needs. A different fix from "start it".
    return verdict(
      'agent',
      'down',
      `the agent server is up but does not serve ${REQUIRED_AGENT_APP} (it lists: ${
        apps.length ? apps.join(', ') : 'nothing'
      })`,
    )
  }
  return verdict('agent', 'ok', null)
}

/** Can the agent reach a model? Only meaningful once the agent server answers,
 *  so the caller passes that verdict in: a provider check with no server to ask
 *  is `not-checked`, never `down`. */
export async function probeProvider(
  agent: ServiceVerdict,
  signal?: AbortSignal,
): Promise<ServiceVerdict> {
  if (agent.state !== 'ok') {
    return NOT_CHECKED('provider', 'the agent server did not answer, so this was not checked')
  }
  const base = agentBaseUrl()
  try {
    const response = await fetch(`${base}${PROVIDER_PROBE_PATH}`, { signal })
    if (response.status === 404) {
      // An older agent server without the probe route. Not a provider failure —
      // the check simply is not available here.
      return NOT_CHECKED('provider', 'this agent server does not serve the provider check')
    }
    if (!response.ok) {
      return NOT_CHECKED('provider', `the provider check answered ${response.status}`)
    }
    const body: unknown = await response.json()
    if (typeof body !== 'object' || body === null || !('configured' in body)) {
      return NOT_CHECKED('provider', 'the provider check did not answer in the expected shape')
    }
    const { configured, detail } = body as { configured: unknown; detail?: unknown }
    if (configured === true) return verdict('provider', 'ok', null)
    // VERBATIM (clause d): the server's own text names the exact key AND the
    // exact file, and any paraphrase loses one or both. It never carries a
    // value — that is asserted server-side in tests/unit/test_service_probe.py.
    return verdict(
      'provider',
      'down',
      typeof detail === 'string' && detail ? detail : 'the agent provider is not configured',
    )
  } catch {
    if (signal?.aborted) return NOT_CHECKED('provider')
    return NOT_CHECKED('provider', 'the provider check could not be reached')
  }
}

/** All four, in dependency order. The graph is asked only of a live API and the
 *  provider only of a live agent, so an outage is reported once, at its cause,
 *  and everything downstream says it was not checked. */
export async function probeServices(
  signal?: AbortSignal,
  now: () => Date = () => new Date(),
): Promise<ProbeResult> {
  const readiness = await probeHealth(apiBaseUrl(), signal)
  const api: ServiceVerdict =
    readiness.state === 'up'
      ? verdict('api', 'ok', null)
      : readiness.state === 'down'
        ? verdict('api', 'down', readiness.message)
        : NOT_CHECKED('api')

  const graph =
    api.state === 'ok'
      ? await probeGraph(signal)
      : NOT_CHECKED('graph', 'drydocs-api did not answer, so the graph was not checked')

  const agent = await probeAgent(signal)
  const provider = await probeProvider(agent, signal)

  return { services: [api, graph, agent, provider], checkedAt: now() }
}

/** The strip's timestamp, formatted for a reader.
 *
 *  Lives here rather than beside the component for two reasons: it formats a
 *  ProbeResult field, so this is where it belongs; and exporting a non-component
 *  from a component file breaks fast refresh (oxlint's react/only-export-components,
 *  which the console gates at --max-warnings 0).
 *
 *  Locale-formatted rather than sliced out of an ISO string — it is read by a
 *  person, in their own clock — and the caller injects the instant, so a test
 *  never has to assert a format against a moving target. */
export function checkedAtLabel(at: Date | null): string {
  if (at === null) return 'not checked yet'
  return `checked ${at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

/** The strip's pre-run state: every service present and unchecked, no
 *  timestamp. Rendering this rather than an empty strip is what stops a page
 *  from looking healthy before it has asked anything. */
export function unprobed(): ProbeResult {
  return {
    services: (['api', 'graph', 'agent', 'provider'] as ServiceId[]).map((id) => NOT_CHECKED(id)),
    checkedAt: null,
  }
}
