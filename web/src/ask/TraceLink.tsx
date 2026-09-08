import { useState } from 'react'
import { download } from '../components/ui/tableControls'
import { fetchQaTrace, traceFilename } from '../lib/qaTrace'

// R18 (d) — the console half: the run id the metrics chip already shows becomes
// the way to the decision trace behind it.
//
// THREE CONDITIONS, ALL REQUIRED, and each one is a different question.
// `enabled` is whether the SERVER recorded anything (the envelope's
// `debug_trace`, which the agent sets from the qa-debug declaration); `canRead`
// is whether THIS PERSON may read it (admin — the route refuses anyone else
// anyway, so this picks whether the control is drawn, not whether the data is
// safe); and a run id is what the lookup is BY. Missing any of them, the chip
// renders the plain run id it has always rendered — the control appears when it
// would work, and never as a button that explains why it cannot.
//
// A FETCH, NOT AN <a href>. The API takes a bearer token, so a plain link would
// 401; and the trace is a file to read beside the code rather than a panel to
// scroll, which is why acceptance (d)'s "retrieve or download" is answered with
// a download.
//
// A FAILURE IS SAID, NOT SWALLOWED. This sits under an answer that already
// succeeded, so a trace that will not load must never look like a problem with
// the answer: the message names the trace.

export function TraceLink({
  runId,
  enabled,
  canRead,
  apiBase,
}: {
  runId?: string
  enabled?: boolean
  canRead: boolean
  apiBase: string
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!runId) return null
  if (!enabled || !canRead) return <span>run {runId}</span>

  const get = async () => {
    setBusy(true)
    setError(null)
    try {
      const payload = await fetchQaTrace(apiBase, { runId })
      download(traceFilename(payload), JSON.stringify(payload, null, 2), 'application/json')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'the trace could not be read')
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className="inline-flex items-center gap-1">
      <span>run</span>
      <button
        type="button"
        onClick={get}
        disabled={busy}
        title={`download the decision trace for ${runId}`}
        aria-label={`download the decision trace for run ${runId}`}
        className="rounded-full border border-edge bg-bg-2 px-2 py-0.5 font-mono text-[10px] text-text underline decoration-dotted underline-offset-2 hover:border-text disabled:opacity-60"
      >
        {busy ? 'fetching trace…' : runId}
      </button>
      {error && <span className="text-yellow">trace: {error}</span>}
    </span>
  )
}
