import { useCallback, useEffect, useRef, useState } from 'react'

import {
  checkedAtLabel,
  probeServices,
  unprobed,
  type ProbeResult,
  type ServiceVerdict,
} from '../lib/serviceProbe'

// O63 clause (f) — the standing view of the same probe Ask's ladder runs.
//
// ON DEMAND AND TIMESTAMPED, NOT A LIVE MONITOR, and that is a property of the
// project rather than a preference: DryDocs is deliberately not a real-time
// system, so a surface that implied otherwise would be lying about what it can
// know. It checks when the page loads and when Re-check is pressed, shows the
// time it checked beside the verdict, and NEVER polls on a timer. A
// stale-but-dated verdict is honest; a green dot that silently stopped updating
// is the failure this repo keeps refusing elsewhere — and it is the same reason
// the console renders committed artifacts instead of live-deriving them.
//
// The question this answers is "is anything missing right now?", asked before
// anyone types a question. Ask's ladder answers the same thing afterwards,
// which is why both read one probe: built twice, the two would eventually
// disagree about what green means.

const DOT: Record<ServiceVerdict['state'], string> = {
  ok: 'bg-green',
  down: 'bg-status-fail',
  checking: 'bg-yellow animate-pulse',
  'not-checked': 'bg-faint',
}

/** The word beside the dot. `not checked` is a first-class verdict here, never
 *  a blank or a hopeful green — a probe that could not run has not found the
 *  service healthy, it has found nothing (rule 1). */
const WORD: Record<ServiceVerdict['state'], string> = {
  ok: 'ok',
  down: 'down',
  checking: 'checking…',
  'not-checked': 'not checked',
}

function ServiceRow({ verdict }: { verdict: ServiceVerdict }) {
  return (
    <li className="flex items-baseline gap-1.5" data-service={verdict.id}>
      <span
        aria-hidden
        className={`inline-block h-1.5 w-1.5 shrink-0 translate-y-[-1px] rounded-full ${DOT[verdict.state]}`}
      />
      <span className="font-mono text-[10px] text-muted">{verdict.label}</span>
      <span
        className={`font-mono text-[10px] ${verdict.state === 'down' ? 'text-status-fail' : 'text-faint'}`}
      >
        {WORD[verdict.state]}
      </span>
      {verdict.detail && (
        // VERBATIM. Where a server said something — the provider's
        // "ANTHROPIC_API_KEY is not set (agents/.env)", the proxy's own
        // wording — it is carried through unaltered: the string names the file
        // to edit, and a paraphrase loses it.
        <span className="truncate text-[10px] text-faint" title={verdict.detail}>
          {verdict.detail}
        </span>
      )}
    </li>
  )
}

export default function ServiceStatusStrip({
  /** Injectable for tests; production reads the real clock. */
  now = () => new Date(),
  /** Injectable for tests; production runs the real probe. */
  probe = probeServices,
}: {
  now?: () => Date
  probe?: typeof probeServices
} = {}) {
  const [result, setResult] = useState<ProbeResult>(unprobed())
  const [running, setRunning] = useState(false)
  const live = useRef(true)

  const run = useCallback(
    async (signal?: AbortSignal) => {
      setRunning(true)
      try {
        const next = await probe(signal, now)
        if (live.current && !signal?.aborted) setResult(next)
      } finally {
        if (live.current) setRunning(false)
      }
    },
    [probe, now],
  )

  useEffect(() => {
    live.current = true
    const ctl = new AbortController()
    void run(ctl.signal)
    // NO INTERVAL HERE, and none is coming: see the module note. The cleanup
    // aborts the in-flight probe rather than cancelling a timer, because there
    // is no timer to cancel.
    return () => {
      live.current = false
      ctl.abort()
    }
  }, [run])

  return (
    <section
      aria-label="service status"
      className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-b border-edge-soft px-3 py-1.5"
    >
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {result.services.map((verdict) => (
          <ServiceRow
            key={verdict.id}
            verdict={running ? { ...verdict, state: 'checking', detail: null } : verdict}
          />
        ))}
      </ul>
      <span className="ml-auto flex items-center gap-2">
        <span className="font-mono text-[10px] text-faint" data-testid="checked-at">
          {running ? 'checking…' : checkedAtLabel(result.checkedAt)}
        </span>
        <button
          type="button"
          className="rounded border border-edge-soft px-1.5 py-0.5 font-mono text-[10px] text-muted hover:text-text disabled:opacity-50"
          onClick={() => void run()}
          disabled={running}
        >
          Re-check
        </button>
      </span>
    </section>
  )
}
