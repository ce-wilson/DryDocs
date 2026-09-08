import { describe, expect, it } from 'vitest'

import type { PersonaQuality } from './reviewQuality'
import {
  FLAGGABLE_METRICS,
  durationLabel,
  hasEnoughDecisions,
  meterValue,
  railRows,
  ratePercent,
} from './reviewQuality'

// O51 — the pure half. The rules worth a test here are the ones a reader would
// otherwise have to infer from a rendered percentage.

function persona(over: Partial<PersonaQuality> = {}): PersonaQuality {
  return {
    persona_id: 'sme1',
    submissions: 8,
    auto_accept_rate: null,
    auto_accept_unavailable_because: 'lands with O48',
    too_fast_rate: 0.1,
    admin_return_rate: 0.1,
    median_review_seconds: 300,
    flags: [],
    blocked: false,
    ...over,
  }
}

describe('a rate with no reading never renders as a zero', () => {
  it('separates null from 0, which is the whole O56 point here', () => {
    expect(ratePercent(null)).toBe('—')
    expect(ratePercent(undefined)).toBe('—')
    expect(ratePercent(0)).toBe('0%')
    expect(ratePercent(0.755)).toBe('76%')
  })

  it('does the same for a duration, for the same reason', () => {
    // No hand-over moment means no measurable review time. Printing 0s would
    // say "instant", which is the strongest accusation the panel can make.
    expect(durationLabel(null)).toBe('—')
    expect(durationLabel(0)).toBe('0s')
    expect(durationLabel(45)).toBe('45s')
    expect(durationLabel(600)).toBe('10m')
    expect(durationLabel(7200)).toBe('2.0h')
  })
})

describe('the rail', () => {
  it('lists only flagged or blocked reviewers', () => {
    const rows = railRows([
      persona({ persona_id: 'clean' }),
      persona({ persona_id: 'blocked', blocked: true }),
      persona({
        persona_id: 'flagged',
        flags: [{ metric: 'too_fast_rate', value: 0.5, limit: 0.3, detail: '4 of 8' }],
      }),
    ])
    expect(rows.map((r) => r.persona_id)).toEqual(['blocked', 'flagged'])
  })

  it('orders by persona id and never by the worst number', () => {
    // "Coaching and triage, not a leaderboard" (plan §8). A list sorted by the
    // worst rate IS a leaderboard whatever the heading above it says.
    const rows = railRows([
      persona({
        persona_id: 'zeta',
        flags: [{ metric: 'too_fast_rate', value: 0.9, limit: 0.3, detail: 'worst' }],
      }),
      persona({
        persona_id: 'alpha',
        flags: [{ metric: 'too_fast_rate', value: 0.31, limit: 0.3, detail: 'barely' }],
      }),
    ])
    expect(rows.map((r) => r.persona_id)).toEqual(['alpha', 'zeta'])
  })
})

describe('the meter reads the allowance, not the rate', () => {
  it('is full AT the limit and stays full past it', () => {
    expect(meterValue(0.15, 0.3)).toBe(50)
    expect(meterValue(0.3, 0.3)).toBe(100)
    expect(meterValue(0.9, 0.3)).toBe(100)
    expect(meterValue(0, 0.3)).toBe(0)
  })

  it('does not divide by a zero limit', () => {
    expect(meterValue(0.4, 0)).toBe(100)
    expect(meterValue(0, 0)).toBe(0)
  })
})

describe('the decision floor', () => {
  it('is the server number, used to explain a rate rather than to compute one', () => {
    expect(hasEnoughDecisions(persona({ submissions: 4 }), 5)).toBe(false)
    expect(hasEnoughDecisions(persona({ submissions: 5 }), 5)).toBe(true)
  })
})

describe('the flaggable metrics', () => {
  it('does not include auto-accept', () => {
    // A metric with no source must not flag a person, and this list is where
    // someone would first put it back.
    expect([...FLAGGABLE_METRICS]).toEqual(['too_fast_rate', 'admin_return_rate'])
    expect(FLAGGABLE_METRICS).not.toContain('auto_accept_rate')
  })
})
