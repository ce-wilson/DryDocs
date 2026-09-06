import type { Provenance } from '../data/provenance'

// WEB1 (b) — ONE presentational component for the provenance state.
//
// It replaces five per-route presentations of the same fact. The wording is
// deliberately plain and the same everywhere, because the value of a trust
// signal is that a reader recognises it without reading it: the same words, in
// the same place, on every surface that can fall back.
//
// It renders NOTHING for `live` and `loading`. A badge that says "LIVE" on
// every healthy frame is a badge people stop seeing, and this notice exists to
// be seen. The LIVE/row-count line stays where it already is — in SpecGrid's
// own footer — and this carries only the cases that need explaining.

const BOX = 'shrink-0 rounded border px-2 py-1 text-[11px]'

export default function ProvenanceNotice<T>({
  state,
  specId,
}: {
  state: Provenance<T>
  specId: string
}) {
  if (state.status === 'live' || state.status === 'loading') return null

  if (state.status === 'empty') {
    return (
      <p className={`${BOX} border-edge bg-panel-2 text-muted`} data-provenance="empty">
        Live QuerySpec <code className="font-mono">{specId}</code> ran and returned no rows. This
        is the graph&rsquo;s answer, not a failure.
      </p>
    )
  }

  if (state.status === 'demo') {
    // The two reasons are different facts about the system and are said
    // differently. Both name the spec, because "which query" is the first thing
    // anyone asks when a frame says it is showing synthetic data.
    return (
      <p
        className={`${BOX} border-yellow/50 bg-yellow/10 text-yellow`}
        data-provenance="demo"
        data-demo-because={state.because}
      >
        SYNTHESIZED demo rows.{' '}
        {state.because === 'empty' ? (
          <>
            Live QuerySpec <code className="font-mono">{specId}</code> ran and returned no rows, so
            this frame is showing its demo data instead. Nothing here came from the graph.
          </>
        ) : (
          <>
            Live QuerySpec <code className="font-mono">{specId}</code> is unavailable
            {state.message ? ` (${state.message.split('—')[0].trim()})` : ''} — this frame is
            showing its demo data instead. Nothing here came from the graph.
          </>
        )}
      </p>
    )
  }

  if (state.status === 'shape') {
    // WEB6 clause (c): the message stands IN PLACE OF the panel. WEB5's error
    // boundary is the backstop for a throw, not the presentation for a fact the
    // seam already established — and this is a fact, phrased for whoever has to
    // act on it: the query ran, the service is up, and the columns moved.
    return (
      <p className={`${BOX} border-red/50 bg-red/10 text-red`} data-provenance="shape">
        <b>Column mismatch.</b> {state.message}
      </p>
    )
  }

  return (
    <p className={`${BOX} border-red/50 bg-red/10 text-red`} data-provenance="error">
      Live QuerySpec <code className="font-mono">{specId}</code>{' '}
      {state.reason === 'timeout' ? 'did not answer in time' : 'failed'} — {state.message}. Nothing
      is shown rather than something fabricated.
    </p>
  )
}
