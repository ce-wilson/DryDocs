import { afterEach, describe, expect, it, vi } from 'vitest'

import { createAuthedApi, createPublicApi, detailOf, requireToken, type SessionHooks, unwrap, unwrapAs } from './apiClient'

vi.mock('./reachability', () => ({
  diagnoseNetworkFailure: async (baseUrl: string) => ({ message: `diagnosed: nothing answered at ${baseUrl}` }),
}))

// O70. The transport policies the hand-written wrappers used to carry one copy
// each — bearer from the session, 401 ends the session, a network failure is
// diagnosed rather than asserted — now live in one client. These pin them
// against a fake fetch, so the middleware is tested as code rather than by a
// person signing in and watching.

const BASE = 'http://api.test.invalid'

function fakeFetch(status: number, body: unknown, headers: Record<string, string> = {}) {
  const calls: Request[] = []
  const impl = vi.fn(async (request: Request) => {
    calls.push(request)
    const text = typeof body === 'string' ? body : JSON.stringify(body)
    return new Response(text, {
      status,
      headers: { 'content-type': typeof body === 'string' ? 'text/plain' : 'application/json', ...headers },
    })
  })
  vi.stubGlobal('fetch', impl)
  return calls
}

function hooks(token: string | null): SessionHooks & { rejections: number } {
  const h = {
    rejections: 0,
    token: () => token,
    rejected() {
      h.rejections += 1
    },
  }
  return h
}

afterEach(() => vi.unstubAllGlobals())

describe('the authed client', () => {
  it('sends the session token as a bearer on every request', async () => {
    const calls = fakeFetch(200, { status: 'ok' })
    const session = hooks('tok-1')
    const { data } = await createAuthedApi(BASE, session, 'trinity').GET('/health')
    expect(data).toEqual({ status: 'ok' })
    expect(calls[0]?.headers.get('authorization')).toBe('Bearer tok-1')
    expect(calls[0]?.url).toBe(`${BASE}/health`)
    expect(session.rejections).toBe(0)
  })

  it('refuses to send without a token, ends the session, and names the persona', async () => {
    const calls = fakeFetch(200, { status: 'ok' })
    const session = hooks(null)
    await expect(createAuthedApi(BASE, session, 'trinity').GET('/health')).rejects.toThrow(
      'not signed in as trinity — the console session has ended',
    )
    expect(calls).toHaveLength(0)
    expect(session.rejections).toBe(1)
  })

  it('treats a 401 as the end of the session and does not retry', async () => {
    const calls = fakeFetch(401, { detail: 'invalid session' })
    const session = hooks('stale')
    const result = await createAuthedApi(BASE, session).GET('/health')
    expect(result.response.status).toBe(401)
    expect(calls).toHaveLength(1)
    expect(session.rejections).toBe(1)
  })

  it('substitutes the reachability diagnosis for a bare network failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    await expect(createAuthedApi(BASE, hooks('tok')).GET('/health')).rejects.toThrow(
      `diagnosed: nothing answered at ${BASE}`,
    )
  })

  it('serializes path and query parameters from the declared shapes', async () => {
    const calls = fakeFetch(200, { drafts: [] })
    await createAuthedApi(BASE, hooks('tok')).GET('/mappings/drafts', { params: { query: { domain: 'a b' } } })
    await createAuthedApi(BASE, hooks('tok')).GET('/mappings/grid/{domain_id}', {
      params: { path: { domain_id: 'x/y' } },
    })
    expect(calls[0]?.url).toBe(`${BASE}/mappings/drafts?domain=a%20b`)
    expect(calls[1]?.url).toBe(`${BASE}/mappings/grid/x%2Fy`)
  })
})

describe('the public client', () => {
  it('sends no bearer and touches no session', async () => {
    const calls = fakeFetch(200, [])
    const { data } = await createPublicApi(BASE).GET('/specs')
    expect(data).toEqual([])
    expect(calls[0]?.headers.get('authorization')).toBeNull()
  })
})

describe('requireToken', () => {
  it('returns the token, or ends the session and throws', () => {
    expect(requireToken(hooks('t'))).toBe('t')
    const session = hooks(null)
    expect(() => requireToken(session)).toThrow('not signed in — the console session has ended')
    expect(session.rejections).toBe(1)
  })
})

describe('unwrap', () => {
  const res = (status: number, statusText = '') => new Response(null, { status, statusText })

  it('returns the data of a successful call', () => {
    expect(unwrap({ data: { a: 1 }, response: res(200) }, 'x')).toEqual({ a: 1 })
  })

  it("names the call and quotes FastAPI's detail on a refusal", () => {
    expect(() => unwrap({ error: { detail: 'unknown spec' }, response: res(404) }, 'spec s1')).toThrow(
      'spec s1 failed (404): unknown spec',
    )
  })

  it('quotes a 422 whole, since its detail is a list', () => {
    const error = { detail: [{ loc: ['body', 'params'], msg: 'x' }] }
    expect(() => unwrap({ error, response: res(422) }, 'q')).toThrow(`q failed (422): ${JSON.stringify(error)}`)
  })

  it('falls back to a text body, then to the status text', () => {
    expect(detailOf('plain refusal', res(500))).toBe('plain refusal')
    expect(detailOf(undefined, res(502, 'Bad Gateway'))).toBe('Bad Gateway')
    expect(() => unwrap({ response: res(500, 'Server Error') }, 'z')).toThrow('z failed (500): Server Error')
  })

  it('unwrapAs is the same check with a claimed type', () => {
    expect(unwrapAs<{ n: number }>({ data: { n: 2 }, response: res(200) }, 'x').n).toBe(2)
    expect(() => unwrapAs<{ n: number }>({ error: 'no', response: res(403) }, 'x')).toThrow('x failed (403): no')
  })
})
