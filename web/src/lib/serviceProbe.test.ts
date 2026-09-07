import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  PROVIDER_PROBE_PATH,
  REQUIRED_AGENT_APP,
  probeAgent,
  probeProvider,
  probeServices,
  unprobed,
  type ServiceVerdict,
} from './serviceProbe'

// O63 — the probe's HONESTY rules, which are the three the item says must not
// break. Everything here is about what the console is allowed to CLAIM, not
// about wording.

vi.mock('./auth', () => ({
  apiBaseUrl: () => '/api',
  agentBaseUrl: () => '/agent',
  sessionToken: () => 'a-token',
  sessionId: () => 'a-session',
  sessionRejected: () => {},
}))

function respond(handler: (url: string) => Response | Promise<Response>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: Request | string) => {
      const url = typeof input === 'string' ? input : input.url
      return handler(url)
    }),
  )
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

const find = (services: ServiceVerdict[], id: string) => services.find((s) => s.id === id)!

beforeEach(() => vi.unstubAllGlobals())
afterEach(() => vi.unstubAllGlobals())

describe('rule 1 — never invent a green (and never invent a red)', () => {
  it('reports every service as `not-checked` before the first run, with no timestamp', () => {
    const initial = unprobed()
    expect(initial.checkedAt).toBeNull()
    expect(initial.services.map((s) => s.state)).toEqual([
      'not-checked',
      'not-checked',
      'not-checked',
      'not-checked',
    ])
    // The strip renders THIS rather than an empty row, which is what stops a
    // page looking healthy before it has asked anything.
    expect(initial.services).toHaveLength(4)
  })

  it('leaves the provider NOT-CHECKED when the agent server never answered', async () => {
    // The distinction the whole item turns on: a provider reported "down"
    // because there was no server to ask would manufacture the second failure
    // out of the first, and send someone to edit agents/.env over an unstarted
    // service.
    const agentDown: ServiceVerdict = {
      id: 'agent',
      label: 'agent server',
      state: 'down',
      detail: 'nothing answered',
    }
    const provider = await probeProvider(agentDown)
    expect(provider.state).toBe('not-checked')
    expect(provider.detail).toMatch(/not checked/i)
  })

  it('leaves the graph NOT-CHECKED when drydocs-api itself is down', async () => {
    respond((url) => {
      if (url.includes('/api/health')) throw new TypeError('Failed to fetch')
      return json([REQUIRED_AGENT_APP])
    })
    const { services } = await probeServices()
    expect(find(services, 'api').state).toBe('down')
    expect(find(services, 'graph').state).toBe('not-checked')
  })

  it('treats an agent server without the probe route as not-checked, not broken', async () => {
    // An older server that predates the route has not FAILED a provider check;
    // it has no provider check. Those are different, and only one of them is
    // somebody's problem to fix.
    respond((url) => (url.endsWith(PROVIDER_PROBE_PATH) ? json({}, 404) : json([])))
    const agentOk: ServiceVerdict = {
      id: 'agent',
      label: 'agent server',
      state: 'ok',
      detail: null,
    }
    const provider = await probeProvider(agentOk)
    expect(provider.state).toBe('not-checked')
  })
})

describe('rule 2 — the two agent failures must not collapse into one', () => {
  it('a THROWN fetch is "nothing answered on this origin"', async () => {
    respond(() => {
      throw new TypeError('Failed to fetch')
    })
    const agent = await probeAgent()
    expect(agent.state).toBe('down')
    expect(agent.detail).toMatch(/nothing answered/i)
    // NOT the proxy's message: the page's own server is what did not answer.
    expect(agent.detail).not.toMatch(/is not answering \(the page/i)
  })

  it('a proxy 502 is "the service behind /agent is not answering"', async () => {
    respond(() => new Response('bad gateway', { status: 502 }))
    const agent = await probeAgent()
    expect(agent.state).toBe('down')
    expect(agent.detail).toMatch(/not answering/i)
    expect(agent.detail).toContain('/agent')
    // And crucially NOT the same text as the thrown case.
    expect(agent.detail).not.toMatch(/nothing answered at/i)
  })

  it('a server that is up but does not serve graph_qa is its own verdict', async () => {
    respond(() => json(['some_other_app']))
    const agent = await probeAgent()
    expect(agent.state).toBe('down')
    expect(agent.detail).toContain(REQUIRED_AGENT_APP)
    expect(agent.detail).toContain('some_other_app')
    // "Start the server" would be the wrong fix here, so the text must not
    // read like the transport-down case.
    expect(agent.detail).not.toMatch(/nothing answered/i)
  })

  it('is green only when graph_qa is actually in the list', async () => {
    respond(() => json([REQUIRED_AGENT_APP, 'another']))
    expect((await probeAgent()).state).toBe('ok')
  })
})

describe('rule 3 — the provider verdict carries the server text and no secret', () => {
  it('surfaces the ProviderConfigError message verbatim', async () => {
    const detail = 'ANTHROPIC_API_KEY is not set (agents/.env)'
    respond((url) =>
      url.endsWith(PROVIDER_PROBE_PATH) ? json({ configured: false, detail }) : json([]),
    )
    const agentOk: ServiceVerdict = {
      id: 'agent',
      label: 'agent server',
      state: 'ok',
      detail: null,
    }
    const provider = await probeProvider(agentOk)
    expect(provider.state).toBe('down')
    // Whole, not paraphrased: it names the key AND the file, and a reworded
    // version loses one or both.
    expect(provider.detail).toBe(detail)
  })

  it('renders green with no detail when the provider is configured', async () => {
    respond((url) =>
      url.endsWith(PROVIDER_PROBE_PATH) ? json({ configured: true, detail: null }) : json([]),
    )
    const agentOk: ServiceVerdict = {
      id: 'agent',
      label: 'agent server',
      state: 'ok',
      detail: null,
    }
    const provider = await probeProvider(agentOk)
    expect(provider).toMatchObject({ state: 'ok', detail: null })
  })
})

describe('ADR 0020 — the probe names no host and no port', () => {
  it('labels every service by name', () => {
    for (const service of unprobed().services) {
      expect(service.label).not.toMatch(/:\d{2,5}\b/)
      expect(service.label).not.toMatch(/localhost|https?:\/\//)
    }
  })

  it('stamps the run so a verdict is never undated', async () => {
    respond(() => json([REQUIRED_AGENT_APP]))
    const fixed = new Date('2026-09-06T09:30:00Z')
    const result = await probeServices(undefined, () => fixed)
    // A stale-but-dated verdict is honest; an undated one cannot be judged.
    expect(result.checkedAt).toEqual(fixed)
  })
})
