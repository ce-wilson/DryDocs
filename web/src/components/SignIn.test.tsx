// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { PERSONAS, SME_PERSONA_ID } from '../lib/auth'
import SignIn from './SignIn'
import source from './SignIn.tsx?raw'

// O87. The SME seat is fully encoded in behaviour (SME_PERSONA_ID gates /intake)
// and used to be invisible on the picker. The marker must FOLLOW the constant —
// parameterized on it here, never on the literal id — so these tests still pass
// if the seat moves and fail if someone hardcodes the id back into SignIn.tsx.
// The first component test in this tree: React Testing Library under jsdom,
// which O80 provisioned for exactly the moment a pure-module test was not enough.

afterEach(cleanup)

function pickerButtons() {
  // Every persona row is a button carrying its display name; the Sign in submit
  // button only appears after a choice, so the initial render has exactly one
  // button per persona.
  return screen.getAllByRole('button')
}

describe('the SME seat marker', () => {
  it('attaches to whichever persona SME_PERSONA_ID names, and to no other', () => {
    render(<SignIn onSignIn={() => undefined} />)
    const buttons = pickerButtons()
    expect(buttons).toHaveLength(PERSONAS.length)
    for (const persona of PERSONAS) {
      const button = buttons.find((b) => within(b).queryByText(persona.displayName))!
      expect(button, `no picker row for ${persona.id}`).toBeDefined()
      const marker = button.querySelector('[data-sme-seat]')
      expect(marker !== null, `${persona.id}: marker present=${marker !== null}`).toBe(
        persona.id === SME_PERSONA_ID,
      )
    }
  })

  it('names the seat in text and in a title, so it is not colour-only', () => {
    render(<SignIn onSignIn={() => undefined} />)
    const marker = document.querySelector('[data-sme-seat]')!
    expect(marker.textContent).toContain('SME seat')
    expect(marker.getAttribute('title')).toMatch(/SME seat/)
    expect(marker.getAttribute('style')).toContain('var(--green)')
  })

  it("leaves the SME persona's role badge saying its real role", () => {
    render(<SignIn onSignIn={() => undefined} />)
    const sme = PERSONAS.find((p) => p.id === SME_PERSONA_ID)!
    const button = pickerButtons().find((b) => within(b).queryByText(sme.displayName))!
    expect(within(button).getByText(sme.role)).toBeDefined()
    // O47: SME is who the persona is, not a fourth role tier. The badge must keep
    // agreeing with canAccessModule, which knows nothing about the seat.
    expect(sme.role).toBe('user')
  })

  it('derives the seat from the constant: the id is not written into SignIn.tsx', () => {
    // Reads the component's source on purpose: the defect this item exists to
    // avoid is a hardcoded id, and only the source can show one. Code, not prose
    // — the pattern is a quoted literal, which a comment naming the seat's role
    // would not carry.
    expect(source).not.toMatch(new RegExp(`['"\`]${SME_PERSONA_ID}['"\`]`))
    expect(source).toContain('SME_PERSONA_ID')
  })
})
