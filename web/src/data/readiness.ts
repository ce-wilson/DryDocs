import { useEffect, useState } from 'react'

import { createPublicApi } from '../lib/apiClient'
import { diagnoseNetworkFailure, isUpstreamDown, upstreamDownMessage } from '../lib/reachability'

// WEB1 (d) — ONE readiness probe, at shell mount.
//
// `/health` exists in the API, is named in the client's own comment as a public
// route, and NOTHING in web/src called it. So "is the system up" was
// rediscovered independently by each route at the moment it failed, and
// answered locally by falling back to demo data — eleven modules each deciding
// what to show. One probe lets the whole console say it once.
//
// IT NEVER INVENTS A GREEN (O56). The states are three, not two: `up`, `down`,
// and `unchecked`. A probe that could not run reports `unchecked` — a probe
// that reported healthy because it never ran is the failure the rule is about.
//
// It reuses the client's diagnosis rather than forking one (ADR 0020): a
// thrown fetch is the page's own server, a proxy 502/503/504 is drydocs-api
// absent behind it, so the message says what was OBSERVED instead of
// asserting a cause.

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

/** The shell's probe. One call at mount; re-probes when the base URL changes. */
export function useReadiness(apiUrl: string): Readiness {
  const [readiness, setReadiness] = useState<Readiness>({ state: 'unchecked' })

  useEffect(() => {
    const ctl = new AbortController()
    setReadiness({ state: 'checking' })
    void probeHealth(apiUrl, ctl.signal).then((r) => {
      if (!ctl.signal.aborted) setReadiness(r)
    })
    return () => ctl.abort()
  }, [apiUrl])

  return readiness
}
