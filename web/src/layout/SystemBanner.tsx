import { useEffect, useState } from 'react'

import { useGraphAccess } from '../data/graphAccess'
import { fallbackCount, onFallback, type FallbackCount } from '../data/provenance'
import { useReadiness } from '../data/readiness'
import { useRuntimeConfig } from '../lib/runtimeView'

// WEB1 (d) and (e) — the console's two system-wide honesty signals, in one
// strip above the header.
//
// (d) READINESS, ONCE. `/health` was public, documented in the client's own
// comment, and called by nothing; "is the API up" was rediscovered by each
// route at the moment it failed and answered locally by showing demo data. Now
// the shell asks once and says it once. It NEVER invents a green (O56): while
// the probe is in flight, and if it could not run, the strip says nothing
// rather than implying health.
//
// (e) THE FALLBACK COUNT. S8's point is sharper than "add telemetry": when the
// API is unavailable this console does not crash, does not error and does not
// stop — it quietly serves fabricated numbers behind a badge, and the fallback
// is designed so the page still looks healthy. A per-frame badge cannot fix
// that, because the person who needs to know is not reading that frame. The
// count belongs OUTSIDE the surfaces doing the fabricating, which is why it
// lives here and not in SpecGrid.
//
// Everyone sees both. An earlier draft put the count on the admin strip only,
// which would have hidden "these numbers are invented" from exactly the people
// most likely to act on them.

export default function SystemBanner() {
  const { apiUrl } = useGraphAccess()
  const readiness = useReadiness(apiUrl)
  // The other once-at-mount read (ADR 0020): the O39 deep-link template from
  // GET /config, the API's non-secret per-deployment values.
  useRuntimeConfig(apiUrl)
  const [fallbacks, setFallbacks] = useState<FallbackCount>(fallbackCount)

  useEffect(() => onFallback(setFallbacks), [])

  if (readiness.state === 'down') {
    return (
      <div
        data-system-banner="down"
        className="border-b border-red/50 bg-red/10 px-3 py-1.5 text-center font-mono text-[11px] text-red"
      >
        drydocs-api is not answering — {readiness.message} · every live frame below is showing its
        demo data or nothing at all
      </div>
    )
  }

  if (fallbacks.total > 0) {
    const specs = Object.keys(fallbacks.bySpec).length
    return (
      <div
        data-system-banner="fallback"
        data-fallback-total={fallbacks.total}
        className="border-b border-yellow/50 bg-yellow/10 px-3 py-1.5 text-center font-mono text-[11px] text-yellow"
      >
        {fallbacks.total} fallback{fallbacks.total === 1 ? '' : 's'} to SYNTHESIZED demo data this
        session, across {specs} spec{specs === 1 ? '' : 's'}
        {fallbacks.last ? ` · last: ${fallbacks.last.specId} (${fallbacks.last.because})` : ''}
      </div>
    )
  }

  return null
}
