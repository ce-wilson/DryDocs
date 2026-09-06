// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { codeOnly, filesMatching, withoutComments } from '../../test/sourceScan'
import { describeCauses } from '../../lib/epistemics'
import EpistemicBadge from './EpistemicBadge'

// R15 clause (d): consumers render the label AS GIVEN. The badge is the one
// place the label becomes text, so this is where "as given" is asserted: the
// string in equals the string out, nothing for null, and the hover text names
// the causes machine-readably rather than paraphrasing them.

afterEach(cleanup)

describe('EpistemicBadge renders the server label as given', () => {
  it('lower-bound, with its causes in the hover text', () => {
    render(
      <EpistemicBadge
        epistemic="lower-bound"
        causes={[
          { cause: 'unparsed-cmd-line', detail: 'unparsed-cmd-line', count: 7 },
          { cause: 'gate-pending-edge', detail: 'scheduler_invokes_utility', count: null },
        ]}
      />,
    )
    const badge = screen.getByText('lower-bound')
    expect(badge.getAttribute('data-epistemic')).toBe('lower-bound')
    const title = badge.getAttribute('title') ?? ''
    expect(title).toContain('unparsed-cmd-line (unparsed-cmd-line: 7)')
    expect(title).toContain('gate-pending-edge (scheduler_invokes_utility)')
    expect(title).toContain('floor')
  })

  it('exact, with no causes, says every cause measured zero', () => {
    render(<EpistemicBadge epistemic="exact" causes={[]} />)
    const badge = screen.getByText('exact')
    expect(badge.getAttribute('data-epistemic')).toBe('exact')
    expect(badge.getAttribute('title')).toBe('Every cause this walk declares measured zero.')
  })

  it('null renders NOTHING — ungraded is not exact', () => {
    const { container } = render(<EpistemicBadge epistemic={null} />)
    expect(container.innerHTML).toBe('')
    expect(screen.queryByText('exact')).toBeNull()
  })

  it('undefined (an older server without the field) also renders nothing', () => {
    const { container } = render(<EpistemicBadge epistemic={undefined} />)
    expect(container.innerHTML).toBe('')
  })

  it('an unfamiliar label still passes through verbatim — the badge invents no vocabulary', () => {
    // A future server value must reach the screen as itself, not be mapped to
    // the nearest word this component knows.
    render(<EpistemicBadge epistemic="some-future-label" />)
    expect(screen.getByText('some-future-label')).toBeTruthy()
  })

  it('describeCauses omits a count that was not measured', () => {
    expect(describeCauses([{ cause: 'gate-pending-edge', detail: 'scheduler_depends_on_file' }])).toBe(
      'The rows are a floor, not the whole answer. Causes: gate-pending-edge (scheduler_depends_on_file)',
    )
  })
})

describe('one vocabulary of epistemic status', () => {
  it('exactly one source renders data-epistemic', () => {
    // Same shape as the TRUNCATED guard: a second place that turns the label
    // into a DOM node is the drift, caught here rather than by two badges that
    // no longer match.
    expect(filesMatching(/data-epistemic=/, codeOnly)).toEqual(['components/ui/EpistemicBadge.tsx'])
  })

  it('no source outside the badge hard-codes the label words into the UI', () => {
    // The consumers pass the server's string through; none of them may write
    // "lower-bound" as a literal of its own. The badge itself needs the literal
    // once, to pick a colour; the type files name the values only in comments,
    // which this scan strips, so they are not exempted here — they simply do
    // not carry the word as code.
    const offenders = filesMatching(/'lower-bound'/, withoutComments).filter(
      (f) => f !== 'components/ui/EpistemicBadge.tsx',
    )
    expect(offenders).toEqual([])
  })
})
