import { describe, expect, it } from 'vitest'

import { controlPart } from './askApi'

// ADR 0019 (WEB9 clause b) - no credential rides in a message part. The R5
// control part names the console session by its PUBLIC handle so the agent can
// scope the specs it registers; the bearer token stays in the browser and the
// agent authenticates itself. Before the ruling this part carried the live
// token under `api_token`, which is how a credential reached the ADK session
// store (R23). This test is what keeps the field from coming back. ADR 0020
// (WEB10) then removed `api_url` too: which drydocs-api the agent calls is the
// agent's own deployment fact (DRYDOCS_API_URL), not something the page tells it.
describe('controlPart', () => {
  const token = 'bearer-token-that-must-not-cross'
  const part = controlPart('sess-handle-1')

  it('carries the session handle and nothing else', () => {
    const payload = JSON.parse(part.text) as { drydocs_control: Record<string, unknown> }
    expect(payload.drydocs_control).toEqual({ session_id: 'sess-handle-1' })
  })

  it('never carries a token field, by name or by value', () => {
    expect(part.text).not.toContain('api_token')
    expect(part.text).not.toContain('token')
    expect(part.text).not.toContain(token)
  })

  it('never carries an api url: the agent resolves its own (ADR 0020)', () => {
    expect(part.text).not.toContain('api_url')
    expect(part.text).not.toContain('http')
  })

  it('takes only a handle: the signature has no room for a token', () => {
    // one positional string - the handle. A second argument does not compile
    // (tsc) and would be ignored at runtime; this pins the runtime half.
    expect(controlPart.length).toBe(1)
  })
})
