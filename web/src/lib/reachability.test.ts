import { describe, expect, it, vi } from 'vitest'

import { diagnoseNetworkFailure } from './reachability'

// The two branches are the whole point, and neither is observable in a unit
// test without injecting fetch: in a real browser the difference is made by
// the network stack, which is exactly why the console could not tell them
// apart in the first place.

// An OPAQUE response is what a no-cors probe actually resolves with, and it
// cannot be built through `new Response(...)` — the constructor rejects status
// 0. The probe only cares that the promise RESOLVES, so the stand-in models
// that and nothing else, which is also the honest shape: reading an opaque
// response is exactly what the browser forbids.
const reachable = () => vi.fn().mockResolvedValue({ type: 'opaque', status: 0 } as unknown as Response)
const dead = () => vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))

describe('a server that answers the probe', () => {
  it('is diagnosed as a blocked origin, not as a dead server', async () => {
    const d = await diagnoseNetworkFailure('http://localhost:8001', reachable())
    expect(d.verdict).toBe('blocked-origin')
    expect(d.message).toContain('answered')
  })

  it('names the environment variable that fixes it', async () => {
    const d = await diagnoseNetworkFailure('http://localhost:8001', reachable())
    expect(d.message).toContain('DRYDOCS_CORS_ORIGINS')
  })

  // The message it replaces asserted a cause. This one reports what it saw and
  // says "almost always" about the inference — a reachable server plus a failed
  // request is strong evidence of a blocked origin, not proof of one.
  it('does not assert a diagnosis it cannot prove', async () => {
    const d = await diagnoseNetworkFailure('http://localhost:8001', reachable())
    expect(d.message).toContain('almost always')
  })

  it('probes with no-cors, or it would be blocked the same way the real request was', async () => {
    const probe = reachable()
    await diagnoseNetworkFailure('http://localhost:8001', probe)
    expect(probe).toHaveBeenCalledWith(
      'http://localhost:8001/docs',
      expect.objectContaining({ mode: 'no-cors' })
    )
  })
})

describe('a server that does not answer the probe', () => {
  it('is diagnosed as unreachable and names the start command', async () => {
    const d = await diagnoseNetworkFailure('http://localhost:8001', dead())
    expect(d.verdict).toBe('unreachable')
    expect(d.message).toContain('nothing answered')
    expect(d.message).toContain('uvicorn drydocs_api.app:create_app')
  })

  it('does not mention the allowlist, which is not the problem here', async () => {
    const d = await diagnoseNetworkFailure('http://localhost:8001', dead())
    expect(d.message).not.toContain('DRYDOCS_CORS_ORIGINS')
  })
})

describe('the baseUrl reaches the reader either way', () => {
  it('is quoted in both messages, since the console can be pointed anywhere', async () => {
    const up = await diagnoseNetworkFailure('http://localhost:9999', reachable())
    const down = await diagnoseNetworkFailure('http://localhost:9999', dead())
    expect(up.message).toContain('http://localhost:9999')
    expect(down.message).toContain('http://localhost:9999')
  })
})
