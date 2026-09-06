// @vitest-environment jsdom
import { act, cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import FeedbackLayer from './FeedbackLayer'
import { saveNotes } from './consoleFeedback'
import { anchorBlocks, routeSlug } from '../lib/paperForm'

// O89 clause (d), the half that needed a rendered component to check.
//
// THE NAVIGATION CASE IS HERE FOR A REASON: it was a real bug, not a
// precaution. The route effect schedules setNotes(loadNotes(newRoute)) and the
// DOM effect runs in the SAME commit, when the ref still holds the previous
// route's notes — so every textarea was seeded empty while the badge counted
// the drafts that existed. Nothing was lost, which is what made it bad: a
// reviewer arriving back at a page they had annotated saw "3 notes" and three
// blank boxes, and no way to tell which was true.

function page(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <main dangerouslySetInnerHTML={{ __html: '<h1>Gates</h1><h2>Open gates</h2>' }} />
      <Nav />
      <Routes>
        <Route path="*" element={<FeedbackLayer enabled />} />
      </Routes>
    </MemoryRouter>,
  )
}

/** A real in-router navigation. Re-rendering with different `initialEntries`
 *  would REMOUNT, and a remount cannot reproduce the defect this file exists
 *  for: on a fresh mount `useState(loadNotes(pathname))` is already right, and
 *  only a navigation puts the two effects in one commit with a stale ref. */
function Nav() {
  const navigate = useNavigate()
  return (
    <button type="button" onClick={() => navigate('/software')}>
      go to software
    </button>
  )
}

const MAIN = '<main><h1>Gates</h1><h2>Open gates</h2></main>'

/** The anchors the layer will offer, computed from a CLEAN copy of the markup.
 *
 *  Not from the rendered page: by the time a test could read it the layer has
 *  already inserted a ✎ and a note box into every block, which changes their
 *  text and therefore their hashes. That is the same compute-before-you-mutate
 *  trap injectMarginTags hit, arriving here in the test instead of the code —
 *  and it failed loudly, with an anchor that matched no label, rather than
 *  quietly agreeing with itself. */
function anchorsFor(route: string): string[] {
  const doc = document.implementation.createHTMLDocument('probe')
  doc.body.innerHTML = MAIN
  return anchorBlocks(doc.querySelector('main')!, routeSlug(route)).map((b) => b.anchor)
}

beforeEach(() => localStorage.clear())
afterEach(() => {
  cleanup()
  localStorage.clear()
})

describe('the annotate controls', () => {
  it('attach one ✎ per anchored block, and only inside main', () => {
    page('/gates')
    const buttons = screen.getAllByRole('button', { name: /^Annotate / })
    expect(buttons).toHaveLength(2) // the h1 and the h2
    for (const b of buttons) expect(b.closest('main')).not.toBeNull()
  })

  it('render nothing at all on a route the loop does not cover', () => {
    page('/explorer')
    expect(screen.queryAllByRole('button', { name: /^Annotate / })).toHaveLength(0)
    expect(screen.queryByText('Review mode')).toBeNull()
  })

  it('SEED A SAVED DRAFT INTO ITS TEXTAREA — the navigation bug', () => {
    // Save a draft for /gates, then mount there. Under the defect the textarea
    // came up empty because the DOM effect read a ref the route effect had not
    // updated yet.
    const [first] = anchorsFor('/gates')
    saveNotes('/gates', { [first]: 'the count is wrong' })
    page('/gates')
    const ta = screen.getByLabelText(`Note for ${first}`) as HTMLTextAreaElement
    expect(ta.value).toBe('the count is wrong')
    // and the block is marked, so a reviewer can see what they annotated
    expect(document.querySelector('.dd-annotated')).not.toBeNull()
  })

  it('the count and the textareas agree — they read the same place', () => {
    const anchors = anchorsFor('/gates')
    saveNotes('/gates', { [anchors[0]]: 'one', [anchors[1]]: 'two' })
    page('/gates')
    expect(screen.getByText('2 notes')).toBeTruthy()
    for (const a of anchors) {
      expect((screen.getByLabelText(`Note for ${a}`) as HTMLTextAreaElement).value).not.toBe('')
    }
  })

  it('typing persists to storage under the route’s own key', async () => {
    const [first] = anchorsFor('/gates')
    page('/gates')
    const ta = screen.getByLabelText(`Note for ${first}`) as HTMLTextAreaElement
    await act(async () => {
      ta.value = 'typed'
      ta.dispatchEvent(new Event('input', { bubbles: true }))
    })
    expect(localStorage.getItem('drydocs.feedback.console.gates')).toContain('typed')
  })

  it('SEEDS THE NEW ROUTE DRAFTS AFTER A NAVIGATION - the actual defect', async () => {
    // A fresh mount cannot show this: useState(loadNotes(pathname)) is already
    // right there. Only a NAVIGATION puts the route effect and the DOM effect
    // in one commit, with the ref still holding the previous page's notes - so
    // the badge counted /software's drafts while every textarea came up empty.
    const [softwareFirst] = anchorsFor('/software')
    saveNotes('/software', { [softwareFirst]: 'written on the software page' })

    page('/gates')
    expect(screen.getByText('0 notes')).toBeTruthy()

    await act(async () => {
      screen.getByRole('button', { name: 'go to software' }).click()
    })

    expect(screen.getByText('1 notes')).toBeTruthy()
    const ta = screen.getByLabelText(`Note for ${softwareFirst}`) as HTMLTextAreaElement
    expect(ta.value).toBe('written on the software page')
    expect(document.querySelector('.dd-annotated')).not.toBeNull()
  })

  it('leaves the DOM as it found it when the layer goes away', () => {
    // The layer decorates a tree it does not own, so its teardown has to be
    // complete: a stray ✎ or a leftover data-dd-anchor would end up in a paper
    // capture, which is the one place those attributes mean something.
    const probe = page('/gates')
    expect(document.querySelectorAll('.dd-note-btn').length).toBeGreaterThan(0)
    probe.unmount()
    expect(document.querySelectorAll('.dd-note-btn')).toHaveLength(0)
    expect(document.querySelectorAll('[data-dd-anchor]')).toHaveLength(0)
  })
})
