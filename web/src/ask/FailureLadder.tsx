import { useEffect, useState } from 'react'

import { ladderStages } from '../lib/askLadder'
import { probeServices, type ProbeResult } from '../lib/serviceProbe'

// O63 (a)-(e) — what the Ask surface shows instead of one red line.
//
// THE FAILURE IT REPLACES: the console came up green everywhere, Ask returned
// "Failed to fetch", and the cause was a fourth service nobody had started.
// Starting it moved the failure to "ANTHROPIC_API_KEY is not set (agents/.env)"
// — a different problem with a different fix, and both printed the same red
// line. This renders the browser's own words, then asks the services, then says
// which of those two states it is actually in.
//
// RULED HERE, because the item left it to the builder: the probe runs ONCE PER
// FAILURE, with no re-check control. A repeat button on this surface would be a
// second, worse copy of the admin strip's Re-check — and the reader whose turn
// just failed wants the answer, not an instrument. A new failure runs a new
// probe, which is when the answer could actually have changed.
//
// IT NEVER RE-ASKS THE QUESTION. The originating error has already arrived; the
// ladder probes the SERVICES and reinterprets that error against what it finds.
// Silently re-running a person's question because it failed would spend their
// tokens to tell them something a HEAD request already knows.

const STATE_WORD = {
  ok: 'ok',
  down: 'down',
  checking: 'checking…',
  'not-checked': 'not checked',
} as const

export default function FailureLadder({
  error,
  /** Injectable for tests; production runs the real probe. */
  probe = probeServices,
}: {
  error: string
  probe?: typeof probeServices
}) {
  const [result, setResult] = useState<ProbeResult | null>(null)

  useEffect(() => {
    const ctl = new AbortController()
    // Reset first: a NEW failure must not be read against the OLD probe, which
    // would be a stale verdict presented as a fresh one.
    setResult(null)
    void probe(ctl.signal).then((r) => {
      if (!ctl.signal.aborted) setResult(r)
    })
    return () => ctl.abort()
  }, [error, probe])

  const stages = ladderStages(error, result)

  return (
    <div
      className="mt-2 rounded border border-red/60 bg-red/10 px-2 py-1.5 text-xs"
      data-testid="failure-ladder"
    >
      <ol className="flex flex-col gap-1">
        {stages.map((stage, i) => {
          if (stage.kind === 'original') {
            return (
              // VERBATIM (clause a). Not re-worded, not prefixed, not wrapped in
              // an apology: this exact string is what the reader pastes into a
              // search or a support ticket.
              <li key="original" className="text-brand-soft" data-stage="original">
                {stage.text}
              </li>
            )
          }
          if (stage.kind === 'checking') {
            return (
              // (b) Visibly distinct from both success and failure, so a slow
              // probe never reads as a verdict.
              <li
                key="checking"
                className="flex items-center gap-2 text-muted"
                data-stage="checking"
              >
                <span
                  aria-hidden
                  className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-yellow"
                />
                checking the services this page depends on…
              </li>
            )
          }
          if (stage.kind === 'service') {
            const { verdict } = stage
            return (
              <li
                key={`${verdict.id}-${i}`}
                className="flex flex-wrap items-baseline gap-1.5"
                data-stage="service"
                data-service={verdict.id}
                data-state={verdict.state}
              >
                <span
                  aria-hidden
                  className={`inline-block h-1.5 w-1.5 shrink-0 translate-y-[-1px] rounded-full ${
                    verdict.state === 'ok'
                      ? 'bg-green'
                      : verdict.state === 'down'
                        ? 'bg-status-fail'
                        : 'bg-faint'
                  }`}
                />
                <span className="font-mono text-[10px] text-muted">{verdict.label}</span>
                <span className="font-mono text-[10px] text-faint">
                  {STATE_WORD[verdict.state]}
                </span>
                {verdict.detail && (
                  // (d) AS-IS. The provider's text names the exact key and the
                  // exact file; a paraphrase loses one or both.
                  <span className="text-muted">{verdict.detail}</span>
                )}
              </li>
            )
          }
          return (
            <li key="handoff" className="text-muted" data-stage="handoff">
              {stage.text}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
