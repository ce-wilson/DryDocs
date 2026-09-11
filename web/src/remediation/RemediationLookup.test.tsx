// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import lookupData from '../generated/remediation-lookup.json'
import RemediationLookup from './RemediationLookup'

afterEach(cleanup)

interface CitationRow {
  doc: string
  line: number
}

const lookups = lookupData.lookups as { answers: { citations: CitationRow[] }[] }[]
const citations = lookups.flatMap((l) => l.answers.flatMap((a) => a.citations))

describe('RemediationLookup walks vendor, then standards, then team (G85)', () => {
  it('renders every tier of every change, in the order the artifact walked them', () => {
    const { container } = render(<RemediationLookup />)
    for (const lookup of lookupData.lookups) {
      const section = container.querySelector(`[data-lookup="${lookup.approval_id}"]`)
      expect(section).toBeTruthy()
      const tiers = [...section!.querySelectorAll('[data-lookup-tier]')].map((n) => n.getAttribute('data-lookup-tier'))
      expect(tiers).toEqual(lookupData.tiers.map((t) => t.id))
    }
  })

  it('every citation shows where it came from and its trust tier', () => {
    const { container } = render(<RemediationLookup />)
    const rows = container.querySelectorAll('[data-lookup-trust]')
    expect(rows).toHaveLength(citations.length)
    for (const c of citations) {
      expect(screen.getAllByText(`${c.doc}:${c.line}`).length).toBeGreaterThan(0)
    }
    rows.forEach((row) => expect(row.getAttribute('data-lookup-trust')).toBeTruthy())
  })

  it('a tier with nothing citable renders its gap and the reason, never an empty box', () => {
    const { container } = render(<RemediationLookup />)
    const gapTiers = container.querySelectorAll('[data-lookup-status="gap"]')
    expect(gapTiers.length).toBeGreaterThan(0)
    gapTiers.forEach((tier) => {
      expect(tier.querySelectorAll('[data-lookup-trust]')).toHaveLength(0)
      expect(tier.querySelector('[data-lookup-gap]')).toBeTruthy()
    })
  })

  it('says plainly that no live agent answered', () => {
    render(<RemediationLookup />)
    expect(screen.getByText(lookupData.agent_seam)).toBeTruthy()
  })
})
