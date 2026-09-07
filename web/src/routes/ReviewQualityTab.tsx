import { useCallback, useEffect, useMemo, useState } from 'react'

import QualityRail from '../components/QualityRail'
import ReviewerQualityPanel from '../components/ReviewerQualityPanel'
import EmptyState from '../components/ui/EmptyState'
import { useGraphAccess } from '../data/graphAccess'
import type { PersonaQuality, ReviewQuality } from '../lib/reviewQuality'
import { blockPersona, fetchReviewQuality, unblockPersona } from '../lib/reviewQuality'

// O51 — the reviewer-quality tab on the admin page: the rail, and the panel for
// whoever is selected on it.
//
// WHY A TAB HERE rather than a page of its own: it reads named people's numbers
// and holds the block action, so it belongs behind the admin gate this page
// already is. The same placement argument the log estate made (O68).
//
// A FAILED READ IS LOUD. An empty rail and an unreachable API look identical to
// a reader, and only one of them means "nobody is flagged" — the rule
// LogEstatePanel and LocationMap both keep, for the same reason.
//
// THE BLOCK IS ONE CLICK BY ONE PERSON, and this component is where that is
// visible: the two calls below happen only in a handler, never in an effect, so
// no render can place or lift a block.

type Load =
  | { state: 'loading' }
  | { state: 'ready'; data: ReviewQuality }
  | { state: 'error'; message: string }

export default function ReviewQualityTab() {
  const { apiUrl } = useGraphAccess()
  const [load, setLoad] = useState<Load>({ state: 'loading' })
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const read = useCallback(
    (signal?: AbortSignal) =>
      fetchReviewQuality(apiUrl, signal)
        .then((data) => {
          if (!signal?.aborted) setLoad({ state: 'ready', data })
        })
        .catch((err: unknown) => {
          if (signal?.aborted) return
          setLoad({
            state: 'error',
            message: err instanceof Error ? err.message : String(err),
          })
        }),
    [apiUrl],
  )

  useEffect(() => {
    const ctl = new AbortController()
    void read(ctl.signal)
    return () => ctl.abort()
  }, [read])

  const personas: readonly PersonaQuality[] = useMemo(
    () => (load.state === 'ready' ? load.data.personas : []),
    [load],
  )
  const selected = personas.find((p) => p.persona_id === selectedId) ?? personas[0] ?? null
  const openBlock =
    load.state === 'ready' && selected
      ? (load.data.blocks.find((b) => b.persona_id === selected.persona_id) ?? null)
      : null

  const act = async (run: () => Promise<unknown>) => {
    setBusy(true)
    setActionError(null)
    try {
      await run()
      await read()
    } catch (err: unknown) {
      // Verbatim: the server's refusal is the reason, and a rewritten one would
      // be the console's opinion about someone else's decision.
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  if (load.state === 'loading') return <p className="text-xs text-muted">Reading review quality…</p>
  if (load.state === 'error') {
    return (
      <EmptyState
        title="Reviewer quality could not be read"
        hint={`${load.message}. Nothing is shown rather than an empty rail, which would read as "nobody is flagged".`}
      />
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3 overflow-auto">
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
        Signals derived from intake records over the last {load.data.window_days} days — no new data
        entry. Limits live in config/review-quality.yaml and FLAG only; the block below is an admin
        decision, and no code path places one automatically.
      </p>

      <QualityRail
        personas={personas}
        selectedId={selected?.persona_id ?? null}
        onSelect={setSelectedId}
      />

      {selected ? (
        <ReviewerQualityPanel
          persona={selected}
          windowDays={load.data.window_days}
          minDecisionsForFlag={load.data.min_decisions_for_flag}
          block={openBlock}
          busy={busy}
          error={actionError}
          onBlock={(personaId, reason) => void act(() => blockPersona(apiUrl, personaId, reason))}
          onUnblock={(personaId, note) => void act(() => unblockPersona(apiUrl, personaId, note))}
        />
      ) : (
        <EmptyState
          title="No submissions in this window"
          hint="Nobody has confirmed an intake record in the last window, so there is nothing to measure. That is an empty window, not an empty result."
        />
      )}
    </div>
  )
}
