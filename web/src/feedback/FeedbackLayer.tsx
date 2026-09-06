import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'

import { ANCHOR_ATTRIBUTE } from '../lib/paperForm'
import {
  annotatableBlocks,
  exportYaml,
  feedbackEnabledFor,
  feedbackFileName,
  loadNotes,
  nonEmpty,
  orphanedAnchors,
  saveNotes,
  type FeedbackNotes,
} from './consoleFeedback'

// O89 clause (d) — the screen half of the L5 loop, mirroring the design doc's
// control rather than inventing a console one. Reviewers move between the two
// surfaces; a second interaction to learn is a cost with no benefit.
//
// IT WORKS OVER THE RENDERED DOM, not over the React tree, and that is the only
// way it could. The anchor for a block is a hash of the text a reviewer can
// SEE, and only the DOM knows that — a component does not know what its
// children rendered to. So this walks `main` after each render the way
// design_doc.py's `_FEEDBACK_JS` walks the document, using the SAME
// `anchorBlocks` the paper gutter uses (clause e: the gutter cannot name an id
// the screen does not offer, because one function answers for both).
//
// OFF BY DEFAULT, behind a toggle in the bar. The console is a working surface
// most of the time and a review surface some of the time; a ✎ beside every
// heading and every table row all day would be the kind of chrome people learn
// to stop seeing, which is the same argument ProvenanceNotice makes for
// rendering nothing when a frame is healthy.
//
// NOTHING IS SENT ANYWHERE. Drafts live in this browser (lib/storage.ts,
// `survives: true`) and leave it only when a person presses Copy and pastes the
// block into a file — clause (d)'s "must not need a backend", and the same
// trust posture as the doc loop, where the reviewer is the transport.

const BTN_CLASS = 'dd-note-btn'
const BOX_CLASS = 'dd-note-box'
const ANNOTATED_CLASS = 'dd-annotated'

export default function FeedbackLayer({ enabled = false }: { enabled?: boolean }) {
  const { pathname } = useLocation()
  const [on, setOn] = useState(enabled)
  const [notes, setNotes] = useState<FeedbackNotes>(() => loadNotes(pathname))
  const [available, setAvailable] = useState<string[]>([])
  const [status, setStatus] = useState('')
  // The live notes, for the DOM listeners: they are attached once per pass and
  // would otherwise close over the state as it was at attach time.
  const notesRef = useRef(notes)
  notesRef.current = notes

  // A route change is a different document: load ITS drafts, drop the old ones.
  useEffect(() => {
    setNotes(loadNotes(pathname))
    setStatus('')
  }, [pathname])

  const persist = useCallback(
    (next: FeedbackNotes) => {
      setNotes(next)
      saveNotes(pathname, next)
    },
    [pathname],
  )

  useEffect(() => {
    const main = document.querySelector('main')
    // The route check belongs HERE as well as at the render below: `on` is state
    // and survives a navigation, so a reviewer who switched review mode on and
    // then walked to an uncovered page would get a component that renders
    // nothing while still decorating every heading on it.
    const main2 = feedbackEnabledFor(pathname) ? main : null
    if (!on || !main2) {
      setAvailable([])
      return
    }
    const blocks = annotatableBlocks(pathname, main2)
    setAvailable(blocks.map((b) => b.anchor))
    const added: HTMLElement[] = []

    for (const { el, anchor } of blocks) {
      el.setAttribute(ANCHOR_ATTRIBUTE, anchor)
      const btn = document.createElement('button')
      btn.type = 'button'
      btn.className = BTN_CLASS
      btn.textContent = '✎'
      btn.title = `Annotate ${anchor}`
      btn.setAttribute('aria-label', `Annotate ${anchor}`)

      const box = document.createElement('div')
      box.className = BOX_CLASS
      const ta = document.createElement('textarea')
      ta.value = notesRef.current[anchor] ?? ''
      ta.setAttribute('aria-label', `Note for ${anchor}`)
      ta.placeholder = `note for ${anchor} …`
      box.hidden = !ta.value.trim()
      if (ta.value.trim()) el.classList.add(ANNOTATED_CLASS)
      ta.addEventListener('input', () => {
        persist({ ...notesRef.current, [anchor]: ta.value })
        el.classList.toggle(ANNOTATED_CLASS, !!ta.value.trim())
      })
      btn.addEventListener('click', () => {
        box.hidden = !box.hidden
        if (!box.hidden) ta.focus()
      })
      box.appendChild(ta)
      // A table's controls ride OUTSIDE it: a <button> is not a legal child of
      // <table>, and browsers foster-parent it out of the table entirely, which
      // is the same constraint that puts the print tag in the caption.
      const host = el.tagName === 'TABLE' ? el.parentElement : el
      if (host && el.tagName === 'TABLE') {
        host.insertBefore(btn, el)
        host.insertBefore(box, el)
      } else {
        el.prepend(btn)
        el.appendChild(box)
      }
      added.push(btn, box)
    }

    return () => {
      for (const el of added) el.remove()
      for (const { el } of blocks) {
        el.removeAttribute(ANCHOR_ATTRIBUTE)
        el.classList.remove(ANNOTATED_CLASS)
      }
    }
    // `notes` is deliberately NOT a dependency: it changes on every keystroke,
    // and re-running this would tear down the textarea the reviewer is typing
    // in. The listeners read notesRef, which is current.
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [on, pathname, persist])

  const count = nonEmpty(notes).length
  const orphans = orphanedAnchors(notes, available)

  // Clause (e): the loop covers the routes O88 captures, and nowhere else. A bar
  // on a page whose paper form nobody takes would offer a reviewer ids that
  // never reach a printout — half a loop, which is worse than none because it
  // looks like the whole one.
  if (!feedbackEnabledFor(pathname)) return null

  async function copy() {
    const text = exportYaml(pathname, notes)
    try {
      await navigator.clipboard.writeText(text)
      setStatus(`copied — paste into docs/design/feedback/${feedbackFileName(pathname)}`)
    } catch {
      // O56: say what happened. A "copied" that did not copy is worse than a
      // failure, because the reviewer closes the tab.
      setStatus('clipboard unavailable — the browser refused it')
    }
  }

  return (
    <div className="dd-fb-bar fixed bottom-4 right-4 z-50 flex flex-col gap-1.5 rounded-lg border border-edge bg-panel px-3 py-2 text-xs shadow-lg print:hidden">
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1.5 text-muted">
          <input type="checkbox" checked={on} onChange={(e) => setOn(e.target.checked)} />
          Review mode
        </label>
        <span className="font-mono text-[10px] text-faint">{count} notes</span>
        {on && (
          <button
            type="button"
            onClick={copy}
            disabled={count === 0}
            className="rounded-md border border-edge bg-bg-2 px-2 py-0.5 text-[11px] font-medium text-muted enabled:hover:border-faint enabled:hover:text-text disabled:opacity-40"
          >
            Copy feedback
          </button>
        )}
      </div>
      {on && orphans.length > 0 && (
        // Clause (c): a note whose anchor is gone is REPORTED. It is still in
        // storage and still in the export — dropping it is what this must never
        // do — but the reviewer is told, while they can still remember what it
        // meant. The table-prefix fallback has already been tried by then.
        <p className="max-w-xs text-[10px] text-yellow">
          {orphans.length} note{orphans.length === 1 ? '' : 's'} no longer match a block on this
          page ({orphans.join(', ')}). They are kept and still export; the page changed under them.
        </p>
      )}
      {status && <p className="max-w-xs font-mono text-[10px] text-muted">{status}</p>}
    </div>
  )
}
