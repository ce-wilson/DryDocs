import { describe, expect, it } from 'vitest'

import {
  NO_PROPOSED_BINDINGS,
  PARKED_STATUS,
  RETURN_TO,
  REVIEW_STATUS,
  WAITING_ON,
  WAITING_ON_SUMMARY,
  confirmedByTheSme,
  readByTheExtractor,
  returnNoteIsUsable,
  reviewQueue,
  reviewSides,
} from './intakeReview'
import type { IntakeRecord, IntakeRow } from './intakeApi'

// O50. The queue's rules live in a pure module for the same reason O63's ladder
// does: what has to be true here is about the SHAPE of the review, and a rule
// inside JSX can only be tested by rendering it and reading strings back.

function row(intake_id: string, status: string): IntakeRow {
  return {
    intake_id,
    created_at: '2026-09-06T10:00:00Z',
    created_by: 'neo',
    origin: 'console',
    classification: 'Internal',
    context_type: 'incident-context',
    note: '',
    status,
    review_payload: null,
    area: {},
    thread_of: [],
    thread_flagged: false,
    thread_decision: null,
    legal_transitions: {
      status,
      transitions: [],
      waiting_on_gate: status === PARKED_STATUS,
      terminal: false,
      thread_decision_required: false,
      thread_decisions: [],
    },
  }
}

function record(over: Partial<IntakeRecord> = {}): IntakeRecord {
  return { ...row('i1', REVIEW_STATUS), evidence: [], ...over }
}

describe('the queue rail', () => {
  it('holds the two groups that are the admin’s work, and nothing else', () => {
    const q = reviewQueue([
      row('a', 'draft'),
      row('b', REVIEW_STATUS),
      row('c', PARKED_STATUS),
      row('d', 'admin-returned'),
      row('e', 'no-new-value'),
      row('f', REVIEW_STATUS),
    ])
    expect(q.awaiting.map((r) => r.intake_id)).toEqual(['b', 'f'])
    expect(q.parked.map((r) => r.intake_id)).toEqual(['c'])
  })

  it('keeps accepted records visible instead of dropping them', () => {
    // A record that vanished on accept would read as loaded, which is the one
    // thing acceptance does NOT do (the load is Q10's, behind its gates).
    const q = reviewQueue([row('a', PARKED_STATUS)])
    expect(q.parked).toHaveLength(1)
  })
})

describe('the park', () => {
  it('names both gates, so the chip says what it waits on', () => {
    const text = WAITING_ON.map((w) => `${w.what} ${w.gate}`).join(' ')
    expect(text).toContain('Q10 ← G31 ← G32') // the corpus load
    expect(text).toContain("Q10's HITL gate") // the assignment edge
    expect(WAITING_ON).toHaveLength(2)
  })

  it('says acceptance wrote nothing to the graph', () => {
    // The load boundary is the whole point of the chip: "accepted" reads as
    // "loaded" on every other review queue a person has used.
    expect(WAITING_ON_SUMMARY).toMatch(/writes nothing to the graph/)
  })
})

describe('the two sides of the review', () => {
  it('reports what the SME answered, with an unset area level as unset', () => {
    const facts = confirmedByTheSme(
      record({
        context_type: 'runbook-context',
        note: '  from the bridge call  ',
        area: { product_line_id: 'PL1', product_id: null, area_product_id: null, seal_id: '70001' },
      }),
    )
    expect(facts).toContainEqual({ label: 'Context type', value: 'runbook-context' })
    expect(facts).toContainEqual({ label: 'Product line', value: 'PL1' })
    expect(facts).toContainEqual({ label: 'Product', value: null })
    expect(facts).toContainEqual({ label: 'SEAL id', value: '70001' })
    expect(facts).toContainEqual({ label: 'Note', value: 'from the bridge call' })
  })

  it('reports every area level even when the record carries none', () => {
    // A missing LEVEL and a level answered "unknown" are the same fact to the
    // admin — nobody said — and both have to be a row, not an absence.
    const labels = confirmedByTheSme(record({ area: {} })).map((f) => f.label)
    expect(labels).toEqual(['Context type', 'Product line', 'Product', 'Area product', 'SEAL id', 'Note'])
  })

  it('flattens the parser preview per evidence file and skips superseded ones', () => {
    const facts = readByTheExtractor(
      record({
        evidence: [
          {
            evidence_id: 'e1',
            intake_id: 'i1',
            filename: 'reply.msg',
            rel_key: 'k',
            sha256: 'x',
            size: 1,
            kind: 'msg',
            pair_key: 'p',
            preview: { subject: 'RE: batch abend', from: 'a@b', keys: ['x', 'y'], date: null },
            uploaded_at: '2026-09-06T10:00:00Z',
            superseded: false,
          },
          {
            evidence_id: 'e0',
            intake_id: 'i1',
            filename: 'old.msg',
            rel_key: 'k',
            sha256: 'y',
            size: 1,
            kind: 'msg',
            pair_key: 'p',
            preview: { subject: 'superseded' },
            uploaded_at: '2026-09-06T09:00:00Z',
            superseded: true,
          },
        ],
      }),
    )
    expect(facts).toContainEqual({ label: 'reply.msg · subject', value: 'RE: batch abend' })
    expect(facts).toContainEqual({ label: 'reply.msg · keys', value: 'x, y' })
    expect(facts).toContainEqual({ label: 'reply.msg · date', value: null })
    expect(facts.some((f) => f.label.startsWith('old.msg'))).toBe(false)
  })

  it('reports NO extractor proposal, and says why, rather than an empty list', () => {
    // The clause O50 has to meet is "what the SME confirmed vs what the
    // extractor proposed". The proposal side is section 4's candidate-binding
    // set, which O48 builds and the O46 store has no column for. `null` and
    // `[]` are different claims — "nobody has run this yet" vs "it ran and
    // found nothing" — and the second one would be false today.
    expect(reviewSides(record()).proposed).toBeNull()
    expect(NO_PROPOSED_BINDINGS).toMatch(/O48/)
  })

  it('carries the thread delta and the SME’s ruling — the one real machine-vs-human pair', () => {
    const sides = reviewSides(
      record({ review_payload: 'the new paragraph', thread_decision: 'adds-value' }),
    )
    expect(sides.threadDelta).toBe('the new paragraph')
    expect(sides.threadDecision).toBe('adds-value')
  })
})

describe('the send-back note', () => {
  it('refuses blank and whitespace, and accepts a real note', () => {
    expect(returnNoteIsUsable('')).toBe(false)
    expect(returnNoteIsUsable('   \n ')).toBe(false)
    expect(returnNoteIsUsable('bindings look wrong')).toBe(true)
  })

  it('is keyed to the transition target, not to a button position', () => {
    expect(RETURN_TO).toBe('admin-returned')
  })
})
