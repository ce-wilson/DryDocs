// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { GraphAccess, RequestOptions, SpecResult } from '../lib/graph'
import { __resetInFlight, GraphAccessContext, requestKey, useGraphAccess, useGraphQuery } from './graphAccess'

// WEB12 — the data layer's own tests. What is asserted here is the behaviour
// the forty hand-rolled preambles never had: a deadline, a cancel path, and one
// request where two panes used to make two.

function specResult(rows: Record<string, unknown>[]): SpecResult {
  return {
    spec_id: 'test.spec.v1',
    database: 'drydocs',
    classification: 'internal-public',
    columns: [],
    cypher: 'RETURN 1',
    params: {},
    watermarked: false,
    keys: ['a'],
    rows,
  }
}

/** A GraphAccess that records what it was asked and when it answers. */
class RecordingAccess {
  readonly kind = 'api' as const
  calls: { specId: string; params: Record<string, unknown>; signal?: AbortSignal }[] = []
  private resolvers: ((r: SpecResult) => void)[] = []
  private rejecters: ((e: unknown) => void)[] = []

  runSpec(specId: string, params: Record<string, unknown> = {}, opts: RequestOptions = {}) {
    this.calls.push({ specId, params, signal: opts.signal })
    return new Promise<SpecResult>((resolve, reject) => {
      this.resolvers.push(resolve)
      this.rejecters.push(reject)
      opts.signal?.addEventListener('abort', () => {
        const err = new Error('aborted')
        err.name = 'AbortError'
        reject(err)
      })
    })
  }

  settle(rows: Record<string, unknown>[] = [{ a: 1 }]) {
    for (const resolve of this.resolvers.splice(0)) resolve(specResult(rows))
    this.rejecters.length = 0
  }

  fail(message: string) {
    for (const reject of this.rejecters.splice(0)) reject(new Error(message))
    this.resolvers.length = 0
  }

  // the rest of the seam is unused here and fails loud if a test reaches it
  runRead = () => Promise.reject(new Error('not used'))
  runNamed = () => Promise.reject(new Error('not used'))
  exportSpec = () => Promise.reject(new Error('not used'))
}

let access: RecordingAccess

/** The real context, given the recording access — so the hook under test is
 *  the real hook reading the real context, with only the transport faked. */
function wrapper({ children }: { children: ReactNode }) {
  return (
    <GraphAccessContext.Provider
      value={{
        access: access as unknown as GraphAccess,
        apiUrl: 'http://api.test',
        getToken: () => Promise.resolve('test-token'),
      }}
    >
      {children}
    </GraphAccessContext.Provider>
  )
}

beforeEach(() => {
  access = new RecordingAccess()
  __resetInFlight()
})

afterEach(() => {
  cleanup()
  __resetInFlight()
  vi.useRealTimers()
})

describe('the state union', () => {
  it('starts loading, then reports data', async () => {
    const { result } = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    expect(result.current.status).toBe('loading')
    await act(async () => {
      access.settle([{ a: 1 }])
    })
    expect(result.current).toMatchObject({ status: 'data' })
  })

  it('a successful zero-row read is empty, NOT an error', async () => {
    // The distinction the review found five routes getting wrong: a request
    // that failed must never render as a result that was empty, and vice versa.
    const { result } = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    await act(async () => {
      access.settle([])
    })
    expect(result.current.status).toBe('empty')
    if (result.current.status === 'empty') {
      expect(result.current.data.classification).toBe('internal-public')
    }
  })

  it('a failed read reports the server message and reason failed', async () => {
    const { result } = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    await act(async () => {
      access.fail('spec test.spec.v1 failed (502): bad gateway')
    })
    expect(result.current).toMatchObject({ status: 'error', reason: 'failed' })
    if (result.current.status === 'error') expect(result.current.message).toContain('502')
  })

  it('does NOT retry — a transient failure surfaces once', async () => {
    // Clause (d): the read console's stated choice. One call, one failure.
    const { result } = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    await act(async () => {
      access.fail('502')
    })
    expect(result.current.status).toBe('error')
    expect(access.calls).toHaveLength(1)
  })
})

describe('the deadline', () => {
  it('abandons a hung request and says so', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useGraphQuery('test.spec.v1', {}, { deadlineMs: 5_000 }), {
      wrapper,
    })
    expect(result.current.status).toBe('loading')
    await act(async () => {
      vi.advanceTimersByTime(5_001)
    })
    expect(result.current).toMatchObject({ status: 'error', reason: 'timeout' })
    if (result.current.status === 'error') expect(result.current.message).toContain('5s')
    expect(access.calls[0].signal?.aborted).toBe(true)
  })

  it('a timeout is distinguishable from a failure — loading and hung are not one screen', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useGraphQuery('test.spec.v1', {}, { deadlineMs: 1_000 }), {
      wrapper,
    })
    await act(async () => {
      vi.advanceTimersByTime(1_001)
    })
    expect(result.current.status === 'error' && result.current.reason).toBe('timeout')
  })
})

describe('cancellation', () => {
  it('aborts the request on unmount, not merely the setState', async () => {
    // The hand-rolled `let cancelled = false` prevented a setState after
    // unmount; it did not stop the work. This asserts the signal.
    const { unmount } = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    expect(access.calls[0].signal?.aborted).toBe(false)
    unmount()
    await waitFor(() => expect(access.calls[0].signal?.aborted).toBe(true))
  })
})

describe('in-flight dedupe', () => {
  it('two panes needing the same spec make ONE request', async () => {
    renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    expect(access.calls).toHaveLength(1)
  })

  it('and both panes get the answer', async () => {
    const a = renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    const b = renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    await act(async () => {
      access.settle([{ a: 1 }])
    })
    expect(a.result.current.status).toBe('data')
    expect(b.result.current.status).toBe('data')
  })

  it('different params are different requests', () => {
    renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    renderHook(() => useGraphQuery('test.spec.v1', { limit: 20 }), { wrapper })
    expect(access.calls).toHaveLength(2)
  })

  it('one subscriber leaving does not abort the other', async () => {
    const a = renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    renderHook(() => useGraphQuery('test.spec.v1', { limit: 10 }), { wrapper })
    a.unmount()
    expect(access.calls[0].signal?.aborted).toBe(false)
  })

  it('a remount after the last subscriber leaves starts a FRESH request', async () => {
    // React StrictMode double-mounts in dev: mount, unmount, mount again,
    // immediately. If the aborted flight were still in the map the second mount
    // would join it and await an AbortError forever — a blank panel in dev only.
    const first = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    first.unmount()
    const second = renderHook(() => useGraphQuery('test.spec.v1'), { wrapper })
    expect(access.calls).toHaveLength(2)
    await act(async () => {
      access.settle([{ a: 1 }])
    })
    expect(second.result.current.status).toBe('data')
  })
})

describe('the request key', () => {
  it('is stable across param ordering', () => {
    expect(requestKey('s', { b: 2, a: 1 })).toBe(requestKey('s', { a: 1, b: 2 }))
  })

  it('separates specs and values', () => {
    expect(requestKey('s', { a: 1 })).not.toBe(requestKey('t', { a: 1 }))
    expect(requestKey('s', { a: 1 })).not.toBe(requestKey('s', { a: 2 }))
  })
})

describe('the provider', () => {
  it('refuses to work outside itself, by name', () => {
    // A hook that quietly built its own client would recreate the per-route
    // client this item deletes, and break the shared-token property R4 needs.
    expect(() => renderHook(() => useGraphAccess())).toThrow(/GraphAccessProvider/)
  })

  it('exposes one apiUrl for the whole session', () => {
    const { result } = renderHook(() => useGraphAccess(), { wrapper })
    expect(result.current.apiUrl).toBe('http://api.test')
  })
})
