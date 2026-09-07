import { useEffect, useState } from 'react'

import { probeHealth, type Readiness } from '../lib/serviceProbe'

export { probeHealth }
export type { Readiness }

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

// O63: `Readiness` and `probeHealth` MOVED to lib/serviceProbe.ts and are
// re-exported above so this module's callers did not have to move. The reason is
// the "one implementation, two surfaces" clause taken seriously: the service
// probe needs exactly this API check, and a second copy of it is how the banner
// and the strip would come to disagree about whether drydocs-api is up. It went
// DOWN a layer rather than the probe reaching up one - data/ already depends on
// lib/, and lib/ importing back out of data/ would invert that.

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
