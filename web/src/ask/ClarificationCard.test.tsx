// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { FREE_TEXT_CHOICE, PROCEED_CHOICE, type AskClarification } from '../lib/askApi'
import ClarificationCard from './ClarificationCard'

// R19 (b): the card renders the agent's clarification request as an actionable
// question and composes the next turn's clarifications from what the person
// picked. What it must NOT do is decide for them: no default choice, Continue
// disabled until every term has an answer, and Cancel sends nothing.

afterEach(cleanup)

const PROMPT = "Before querying the graph: 'PDN' does not resolve to a registered QuerySpec."

const REQUEST: AskClarification = {
  prompt: PROMPT,
  terms: [
    {
      term: 'PDN',
      kind: 'acronym',
      candidates: [{ id: 'glossary:pdn:1', label: 'Production Delay Notification', source: 'glossary' }],
      choices: [
        { id: 'glossary:pdn:1', label: 'Production Delay Notification', source: 'glossary' },
        { id: FREE_TEXT_CHOICE, label: 'Something else — say what it means', source: 'you' },
        { id: PROCEED_CHOICE, label: 'Answer anyway', source: 'you' },
      ],
    },
  ],
}

function mount(overrides: Partial<Parameters<typeof ClarificationCard>[0]> = {}) {
  const onSubmit = vi.fn()
  const onDismiss = vi.fn()
  render(
    <ClarificationCard
      clarification={REQUEST}
      disabled={false}
      onSubmit={onSubmit}
      onDismiss={onDismiss}
      {...overrides}
    />,
  )
  return { onSubmit, onDismiss }
}

describe('ClarificationCard', () => {
  it('renders the prompt, the term and every choice as given', () => {
    mount()
    expect(screen.getByText(PROMPT)).toBeTruthy()
    expect(screen.getByText('PDN')).toBeTruthy()
    expect(screen.getByRole('button', { name: /Production Delay Notification/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: /Something else/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Answer anyway' })).toBeTruthy()
  })

  it('Continue is disabled until the person has chosen — the card picks nothing for them', () => {
    const { onSubmit } = mount()
    const cont = screen.getByRole('button', { name: 'Continue' }) as HTMLButtonElement
    expect(cont.disabled).toBe(true)
    fireEvent.click(cont)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('a candidate click submits its label as the resolution', () => {
    const { onSubmit } = mount()
    fireEvent.click(screen.getByRole('button', { name: /Production Delay Notification/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(onSubmit).toHaveBeenCalledWith([
      { term: 'PDN', resolution: 'Production Delay Notification', declined: false },
    ])
  })

  it('free text submits the words typed, and not before something is typed', () => {
    const { onSubmit } = mount()
    fireEvent.click(screen.getByRole('button', { name: /Something else/ }))
    const cont = screen.getByRole('button', { name: 'Continue' }) as HTMLButtonElement
    expect(cont.disabled).toBe(true)
    fireEvent.change(screen.getByLabelText('What PDN means'), { target: { value: '  Product Data Network ' } })
    expect(cont.disabled).toBe(false)
    fireEvent.click(cont)
    expect(onSubmit).toHaveBeenCalledWith([{ term: 'PDN', resolution: 'Product Data Network', declined: false }])
  })

  it('Answer anyway submits a declined clarification with no resolution', () => {
    const { onSubmit } = mount()
    fireEvent.click(screen.getByRole('button', { name: 'Answer anyway' }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(onSubmit).toHaveBeenCalledWith([{ term: 'PDN', resolution: null, declined: true }])
  })

  it('Cancel dismisses and sends nothing', () => {
    const { onSubmit, onDismiss } = mount()
    fireEvent.click(screen.getByRole('button', { name: /Production Delay Notification/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onDismiss).toHaveBeenCalledTimes(1)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('every term needs an answer before Continue enables', () => {
    const two: AskClarification = {
      prompt: PROMPT,
      terms: [
        REQUEST.terms[0],
        {
          term: 'ControlJob',
          kind: 'label',
          candidates: [{ id: 'label:ControlMJob', label: 'ControlMJob', source: 'label' }],
          choices: [
            { id: 'label:ControlMJob', label: 'ControlMJob', source: 'label' },
            { id: PROCEED_CHOICE, label: 'Answer anyway', source: 'you' },
          ],
        },
      ],
    }
    const { onSubmit } = mount({ clarification: two })
    fireEvent.click(screen.getByRole('button', { name: /Production Delay Notification/ }))
    const cont = screen.getByRole('button', { name: 'Continue' }) as HTMLButtonElement
    expect(cont.disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: /^ControlMJob/ }))
    expect(cont.disabled).toBe(false)
    fireEvent.click(cont)
    expect(onSubmit).toHaveBeenCalledWith([
      { term: 'PDN', resolution: 'Production Delay Notification', declined: false },
      { term: 'ControlJob', resolution: 'ControlMJob', declined: false },
    ])
  })

  it('disabled while a turn is in flight: nothing submits, nothing dismisses', () => {
    const { onSubmit, onDismiss } = mount({ disabled: true })
    fireEvent.click(screen.getByRole('button', { name: /Production Delay Notification/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onSubmit).not.toHaveBeenCalled()
    expect(onDismiss).not.toHaveBeenCalled()
  })
})
