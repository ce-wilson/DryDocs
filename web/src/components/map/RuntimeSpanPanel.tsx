import { useEffect, useState } from 'react'
import RuntimeSpanMap from './RuntimeSpanMap'
import { useGraphAccess } from '../../data/graphAccess'
import { fetchDataCenters, type DataCentersPayload } from '../../lib/dataCentersApi'

// Z6 — the one thing RuntimeSpanMap deliberately does not do: fetch.
//
// The map takes its registry as a PROP so it can be rendered against fixtures
// with no server; this panel is where the real read happens, and where the
// VENUE gets said out loud (J18). `source` is the difference between "these are
// the four production data centers" and "these are the publishable synthetic
// rows", and a default time shown without it would make a producer-side demo
// read as a statement about production.

const VENUE_LABEL: Record<string, string> = {
  'internal-twin': 'internal twin (the real inventory, machine-local)',
  'publishable-sample': 'publishable sample (synthetic — NOT the real inventory)',
}

export default function RuntimeSpanPanel({ className }: { className?: string }) {
  const { access, apiUrl } = useGraphAccess()
  const [registry, setRegistry] = useState<DataCentersPayload | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ctl = new AbortController()
    fetchDataCenters(apiUrl, ctl.signal)
      .then(setRegistry)
      .catch((e: unknown) => {
        if (ctl.signal.aborted) return
        setError(e instanceof Error ? e.message : String(e))
      })
    return () => ctl.abort()
  }, [apiUrl])

  return (
    <section className={className}>
      <p className="mb-2 text-xs/[1.5]" style={{ color: 'var(--muted)' }}>
        {registry ? (
          <>
            Data-center registry: {registry.data_centers.length} row(s) from the{' '}
            <span style={{ color: registry.source === 'internal-twin' ? 'var(--text)' : 'var(--yellow)' }}>
              {VENUE_LABEL[registry.source] ?? registry.source}
            </span>
            {registry.updated ? ` · updated ${registry.updated}` : ''}
          </>
        ) : error ? (
          // Loud, and specific about what is lost: without the registry the
          // default-time fallback has no route, so a job with no explicit
          // timing reports "no runtime" rather than a seeded one. That is the
          // correct behaviour and the reader should know why it happened.
          <span style={{ color: 'var(--status-fail-soft)' }}>
            Data-center registry unavailable ({error}) — jobs with no explicit timing will report no
            runtime rather than a DC default.
          </span>
        ) : (
          'Reading the data-center registry…'
        )}
      </p>
      <RuntimeSpanMap access={access} dataCenters={registry?.data_centers ?? []} />
    </section>
  )
}
