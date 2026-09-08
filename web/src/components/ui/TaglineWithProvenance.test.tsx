// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { TaglineWithProvenance } from './TaglineWithProvenance'
import { conceptFor, conceptInText, provenanceNote, UI_CONCEPTS } from '../../lib/uiConcepts'

// WEB18 (a),(b),(d). The header must say where a console-defined term comes
// from — and must NOT say what it maps to in the graph, which is a HITL gate
// decision. Both halves are asserted, because on this surface the second one is
// the load-bearing half: the defect being fixed is a term crossing from UI
// taxonomy into the ontology without anybody deciding it should.

afterEach(cleanup)

const TOWER = UI_CONCEPTS.find((c) => c.term === 'Tower')!

describe('TaglineWithProvenance', () => {
  it('annotates a declared term in the tagline', () => {
    render(<TaglineWithProvenance tagline="Tower / app drill-down graph" />)
    const marked = screen.getByText('Tower')
    expect(marked.tagName.toLowerCase()).toBe('abbr')
    expect(marked.getAttribute('data-ui-concept')).toBe('Tower')
  })

  it('says where the term is defined and that the graph does not back it', () => {
    render(<TaglineWithProvenance tagline="Tower / app drill-down graph" />)
    const note = screen.getByText('Tower').getAttribute('title') ?? ''
    expect(note).toContain('defined in the console')
    expect(note).toContain(TOWER.source)
    expect(note).toContain('not read from the graph')
  })

  it('carries the count and the members from the declaration', () => {
    render(<TaglineWithProvenance tagline="Tower / app drill-down graph" />)
    const note = screen.getByText('Tower').getAttribute('title') ?? ''
    expect(note).toContain(String(TOWER.cardinality))
    for (const member of TOWER.members) expect(note).toContain(member)
  })

  it('surfaces the aliases — clause (d), the cheap win', () => {
    // The person who typed "CTO towers" and got nothing is who this is for.
    const note = provenanceNote(TOWER)
    for (const alias of TOWER.aliases) expect(note).toContain(alias)
  })

  it('asserts NO ontology binding — clause (b), the hard boundary', () => {
    render(<TaglineWithProvenance tagline="Tower / app drill-down graph" />)
    const note = screen.getByText('Tower').getAttribute('title') ?? ''
    // :TOMRole is the label a model actually proxied Tower onto on 2026-08-20.
    // The header may say a term is not from the graph; saying what it IS
    // instead is the gate's ruling, and a hover that pre-empted it would
    // reproduce the crossing R22 exists to prevent.
    expect(note).not.toContain('TOMRole')
    expect(note).not.toContain('label')
    expect(note).not.toMatch(/maps to|same as|equivalent/i)
  })

  it('leaves a tagline that names no declared term exactly as it was', () => {
    const { container } = render(<TaglineWithProvenance tagline="Load runs and rejects" />)
    expect(container.querySelector('abbr')).toBeNull()
    expect(container.textContent).toBe('Load runs and rejects')
  })

  it('keeps the tagline text around the annotated word', () => {
    const { container } = render(<TaglineWithProvenance tagline="Tower / app drill-down graph" />)
    expect(container.textContent).toBe('Tower / app drill-down graph')
  })
})

describe('conceptInText', () => {
  it('matches on a word boundary, never inside a longer word', () => {
    // A wrong provenance note on a header read at a glance is worse than none.
    expect(conceptInText('Towering inferno')).toBeNull()
    expect(conceptInText('Tower / app drill-down graph')?.term).toBe('Tower')
  })

  it('matches an alias, case-insensitively', () => {
    expect(conceptInText('CTO towers overview')?.term).toBe('Tower')
    expect(conceptFor('cto tower')?.term).toBe('Tower')
    expect(conceptFor('')).toBeNull()
    expect(conceptFor('nothing declared')).toBeNull()
  })
})
