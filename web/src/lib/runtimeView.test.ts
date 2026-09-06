// O39's template now arrives from GET /config (ADR 0020, WEB10) instead of the
// build. These pin the load: nothing before it, the served value after it, and
// a failed load changing nothing.
import { afterEach, describe, expect, it, vi } from 'vitest'

import { loadRuntimeConfig, resetRuntimeConfigForTests, runtimeViewTemplate, runtimeViewUrl } from './runtimeView'

// An absolute base: Node's Request rejects a bare path, where the browser resolves it.
const BASE = 'http://api.test.invalid'

function serve(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
  resetRuntimeConfigForTests()
})

describe('the runtime-view template from GET /config', () => {
  it('is null before any load, so a chip renders no link rather than a wrong one', () => {
    expect(runtimeViewTemplate()).toBeNull()
    expect(runtimeViewUrl('job', 'J70001')).toBeNull()
  })

  it('takes the served value and binds kind and URI-encoded id into it', async () => {
    serve(200, { runtime_view_url_template: 'https://runtime.example.internal/{kind}/{id}' })
    await loadRuntimeConfig(BASE)
    expect(runtimeViewUrl('job', 'J 70001')).toBe('https://runtime.example.internal/job/J%2070001')
  })

  it('stays null when the deployment configures none', async () => {
    serve(200, { runtime_view_url_template: null })
    await loadRuntimeConfig(BASE)
    expect(runtimeViewTemplate()).toBeNull()
  })

  it('leaves the template alone when the load fails - the readiness banner owns that message', async () => {
    serve(200, { runtime_view_url_template: 'https://runtime.example.internal/{kind}/{id}' })
    await loadRuntimeConfig(BASE)
    serve(502, 'upstream not answering')
    await loadRuntimeConfig(BASE)
    expect(runtimeViewTemplate()).toBe('https://runtime.example.internal/{kind}/{id}')
  })
})
