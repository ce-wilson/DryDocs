import { useState } from 'react'

import {
  FREE_TEXT_CHOICE,
  PROCEED_CHOICE,
  type AskClarification,
  type AskClarificationTerm,
  type Clarification,
} from '../lib/askApi'

// R19 (b): the clarification request rendered as an actionable question. The
// agent found a term it could not resolve and refused to pick a near match for
// the person; this card is where the person picks — a listed candidate, their
// own words, or "answer anyway" (which is recorded as declined and stated on
// the answer). The card composes the NEXT turn's clarifications and hands them
// up; it never re-words the prompt, the candidates or the choices, which arrive
// from term_resolution.py as given.

interface Props {
  clarification: AskClarification
  /** true while any turn is in flight — the card waits, it never double-sends */
  disabled: boolean
  onSubmit: (clarifications: Clarification[]) => void
  onDismiss: () => void
}

type Draft = { choice: string | null; text: string }

function toClarification(term: AskClarificationTerm, draft: Draft): Clarification | null {
  if (draft.choice === PROCEED_CHOICE) return { term: term.term, resolution: null, declined: true }
  if (draft.choice === FREE_TEXT_CHOICE) {
    const text = draft.text.trim()
    return text ? { term: term.term, resolution: text, declined: false } : null
  }
  const picked = term.choices.find((c) => c.id === draft.choice)
  if (!picked) return null
  return { term: term.term, resolution: picked.label, declined: false }
}

export default function ClarificationCard({ clarification, disabled, onSubmit, onDismiss }: Props) {
  const [drafts, setDrafts] = useState<Record<string, Draft>>({})
  const draftFor = (term: string): Draft => drafts[term] ?? { choice: null, text: '' }
  const setDraft = (term: string, fn: (d: Draft) => Draft) =>
    setDrafts((prev) => ({ ...prev, [term]: fn(draftFor(term)) }))

  const composed = clarification.terms.map((t) => toClarification(t, draftFor(t.term)))
  const complete = composed.length > 0 && composed.every((c) => c !== null)

  return (
    <div
      role="group"
      aria-label="Clarification needed"
      className="mt-3 flex flex-col gap-3 rounded border border-yellow/50 bg-yellow/10 p-3"
    >
      <p className="whitespace-pre-wrap text-sm text-text">{clarification.prompt}</p>

      {clarification.terms.map((term) => {
        const draft = draftFor(term.term)
        return (
          <fieldset key={term.term} className="flex flex-col gap-1.5" disabled={disabled}>
            <legend className="text-xs font-medium text-text">
              <code className="font-mono">{term.term}</code>
              <span className="ml-1 text-faint">({term.kind})</span>
            </legend>
            <div className="flex flex-wrap gap-1.5">
              {term.choices.map((choice) => {
                const selected = draft.choice === choice.id
                return (
                  <button
                    key={choice.id}
                    type="button"
                    aria-pressed={selected}
                    title={choice.detail ?? undefined}
                    onClick={() => setDraft(term.term, (d) => ({ ...d, choice: choice.id }))}
                    className={
                      'rounded-md border px-2 py-0.5 text-xs ' +
                      (selected
                        ? 'border-blue-bright bg-bg-2 text-text'
                        : 'border-edge bg-bg-2 text-muted hover:border-faint hover:text-text')
                    }
                  >
                    {choice.label}
                    {choice.source && choice.source !== 'you' && (
                      <span className="ml-1 font-mono text-[10px] text-faint">{choice.source}</span>
                    )}
                  </button>
                )
              })}
            </div>
            {draft.choice === FREE_TEXT_CHOICE && (
              <input
                type="text"
                value={draft.text}
                onChange={(e) => setDraft(term.term, (d) => ({ ...d, text: e.target.value }))}
                aria-label={`What ${term.term} means`}
                placeholder={`What does ${term.term} mean here?`}
                className="min-w-0 text-sm"
              />
            )}
          </fieldset>
        )
      })}

      <div className="flex gap-2">
        <button
          type="button"
          disabled={disabled || !complete}
          onClick={() => onSubmit(composed.filter((c): c is Clarification => c !== null))}
          className="rounded-md border border-edge bg-bg-2 px-3 py-1 text-sm font-medium text-text disabled:opacity-50"
        >
          Continue
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={onDismiss}
          className="rounded-md border border-edge bg-bg-2 px-3 py-1 text-sm font-medium text-muted disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
