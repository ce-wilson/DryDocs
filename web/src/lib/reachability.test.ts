// reachability.ts after ADR 0020 (WEB10): the blocked-origin verdict is gone
// because the boundary it diagnosed is gone. What remains is two verdicts told
// apart by the RESPONSE - a thrown fetch is the page's own server, a proxy
// 502/503/504 is the service behind a path - and neither needs a probe. No
// fetch is injected here because nothing is fetched.
import { describe, expect, it } from 'vitest'

import {
  diagnoseNetworkFailure,
  isUpstreamDown,
  upstreamDownMessage,
} from './reachability'

describe('diagnoseNetworkFailure (the fetch threw)', () => {
  it('reads a thrown fetch as the server that serves the page not answering, and names the base path', async () => {
    const d = await diagnoseNetworkFailure('/api')
    expect(d.verdict).toBe('unreachable')
    expect(d.message).toContain('nothing answered')
    expect(d.message).toContain('/api')
  })

  it('never names the retired allowlist - there is no cross-origin branch left to explain', async () => {
    const d = await diagnoseNetworkFailure('/api')
    expect(d.message).not.toContain('DRYDOCS_CORS_ORIGINS')
    expect(d.message).not.toContain('allowlist')
  })
})

describe('isUpstreamDown (the proxy answered)', () => {
  it('recognizes the three gateway statuses a reverse proxy writes for an absent upstream', () => {
    for (const s of [502, 503, 504]) expect(isUpstreamDown(s)).toBe(true)
  })

  it('leaves every other status to the caller - 500 is the service answering, not absent', () => {
    for (const s of [200, 401, 404, 500]) expect(isUpstreamDown(s)).toBe(false)
  })
})

describe('upstreamDownMessage', () => {
  it('names the path, the status and that it is not this page', () => {
    const m = upstreamDownMessage(502, '/api')
    expect(m).toContain('/api')
    expect(m).toContain('502')
    expect(m).toContain('not this page')
  })

  it('carries the start command only in DEV (vitest runs with import.meta.env.DEV true)', () => {
    expect(import.meta.env.DEV).toBe(true)
    expect(upstreamDownMessage(502, '/api')).toContain('uvicorn drydocs_api.app:create_app')
  })
})
