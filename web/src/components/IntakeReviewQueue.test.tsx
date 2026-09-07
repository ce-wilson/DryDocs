// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import IntakeReviewQueue from './IntakeReviewQueue'
import type { IntakeApi, IntakeRecord, IntakeRow } from '../lib/intakeApi'
import { PARKED_STATUS, REVIEW_STATUS } from '../lib/intakeReview'

// O50. What these assert is that the SERVER owns the machine: the buttons are
// the server's legal-transitions map rendered, and the note rule's authority is
// the server's 422, which arrives verbatim. Nothing here re-encodes a hop.

afterEach(cleanup)

function row(intake_id: string, status: string, over: Partial<IntakeRow> = {}): IntakeRow {
  return {
    intake_id,
    created_at: '2026-09-06T10:00:00Z',
    created_by: 'neo',
    origin: 'console',
    classification: 'Internal',
    context_type: 'incident-context',
    note: 'the abend on the nightly',
    status,
    review_payload: null,
    area: { product_line_id: 'PL1', product_id: null, area_product_id: null, seal_id: null },
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
    ...over,
  }
}

/** The map an ADMIN gets back at sme-confirmed (drydocs_api/intake.py
 *  TRANSITIONS) — copied as data, because it is what the wire carries. */
const ADMIN_ACTIONS = [
  { to: 'admin-accepted', action: 'Accept' },
  { to: 'admin-returned', action: 'Send back' },
]

function adminRecord(over: Partial<IntakeRecord> = {}): IntakeRecord {
  const base = row('i1', REVIEW_STATUS)
  return {
    ...base,
    evidence: [],
    legal_transitions: { ...base.legal_transitions, transitions: ADMIN_ACTIONS },
    ...over,
  }
}

function stubApi(over: Partial<IntakeApi> = {}): IntakeApi {
  return {
    list: vi.fn(async () => [row('i1', REVIEW_STATUS), row('i2', PARKED_STATUS), row('i3', 'draft')]),
    get: vi.fn(async () => adminRecord()),
    create: vi.fn(),
    uploadEvidence: vi.fn(),
    transition: vi.fn(async () => adminRecord()),
    threadDecision: vi.fn(),
    ...over,
  } as unknown as IntakeApi
}

async function openTheRecord(api: IntakeApi) {
  render(<IntakeReviewQueue api={api} />)
  const rowButton = await screen.findByText('i1')
  fireEvent.click(rowButton)
  await screen.findByText('What the SME confirmed')
}

describe('the rail', () => {
  it('lists only the two groups that are the admin’s work', async () => {
    render(<IntakeReviewQueue api={stubApi()} />)
    await screen.findByText('i1')
    expect(screen.getByText('i2')).toBeTruthy() // parked, still visible
    expect(screen.queryByText('i3')).toBeNull() // a draft is the SME's, not the queue's
  })

  it('names both gates the parked group waits on', async () => {
    render(<IntakeReviewQueue api={stubApi()} />)
    await screen.findByText('i1')
    const text = document.body.textContent ?? ''
    expect(text).toContain('Q10 ← G31 ← G32')
    expect(text).toContain("Q10's HITL gate")
  })

  it('says the rail is empty rather than rendering nothing', async () => {
    render(<IntakeReviewQueue api={stubApi({ list: vi.fn(async () => []) })} />)
    expect(await screen.findByText(/Nothing confirmed is waiting/)).toBeTruthy()
    expect(screen.getByText('None parked.')).toBeTruthy()
  })
})

describe('the review panel', () => {
  it('reads the record whole, because the queue row carries no evidence (WEB8)', async () => {
    const api = stubApi()
    await openTheRecord(api)
    expect(api.get).toHaveBeenCalledWith('i1')
  })

  it('shows the SME’s answers and says why there is no extractor proposal', async () => {
    await openTheRecord(stubApi())
    // Scoped to the confirmed pane: the context type also names the rail row,
    // and asserting on the page as a whole would pass on the wrong one.
    const confirmed = within(screen.getByText('What the SME confirmed').closest('section')!)
    expect(confirmed.getByText('incident-context')).toBeTruthy()
    expect(confirmed.getByText('the abend on the nightly')).toBeTruthy()
    expect(confirmed.getByText('PL1')).toBeTruthy()
    expect(confirmed.getAllByText('not supplied')).toHaveLength(3) // the levels nobody answered
    expect(screen.getByText(/lands with O48/)).toBeTruthy()
  })

  it('renders the thread delta with the SME’s ruling when the record carries one', async () => {
    const api = stubApi({
      get: vi.fn(async () =>
        adminRecord({ review_payload: 'the new paragraph', thread_decision: 'adds-value' }),
      ),
    })
    await openTheRecord(api)
    expect(screen.getByText(/machine proposed, SME disposed/)).toBeTruthy()
    expect(screen.getByText('SME ruling: adds-value')).toBeTruthy()
    expect(screen.getByText('the new paragraph')).toBeTruthy()
  })
})

describe('the decision', () => {
  it('renders exactly the actions the server’s map carries — no more', async () => {
    await openTheRecord(stubApi())
    expect(screen.getByRole('button', { name: 'Accept' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Send back' })).toBeTruthy()
    // 'Reject' is in the plan's prose and NOT in TRANSITIONS. A button the
    // server would refuse is the failure this rule exists to prevent.
    expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull()
  })

  it('renders the full status machine in the panel, gates and all', async () => {
    // The acceptance asks for the machine in the ui-conventions vocabulary.
    // The panel reuses IntakeStepper rather than drawing a second one, so what
    // is asserted here is that it is REACHED — the stepper's own stage tokens
    // are its tests' business, not this file's.
    const parked = adminRecord({ status: PARKED_STATUS })
    parked.legal_transitions = { ...parked.legal_transitions, transitions: [], waiting_on_gate: true }
    render(<IntakeReviewQueue api={stubApi({ get: vi.fn(async () => parked) })} />)
    fireEvent.click(await screen.findByText('i2'))
    expect(await screen.findByText('Admin accepted')).toBeTruthy()
    expect(screen.getByText('Loaded')).toBeTruthy()
    // Twice on the page: the rail's standing note and the selected record's
    // own park. Both come from WAITING_ON, which is why they cannot disagree.
    expect(screen.getAllByText(/Q10 ← G31 ← G32/)).toHaveLength(2)
  })

  it('offers nothing at a status whose map is empty, and says so', async () => {
    const parked = adminRecord({ status: PARKED_STATUS })
    parked.legal_transitions = { ...parked.legal_transitions, transitions: [], waiting_on_gate: true }
    render(<IntakeReviewQueue api={stubApi({ get: vi.fn(async () => parked) })} />)
    fireEvent.click(await screen.findByText('i2'))
    expect(await screen.findByText(/No actions at/)).toBeTruthy()
  })

  it('holds Send back until a note is typed, and lets Accept through with none', async () => {
    await openTheRecord(stubApi())
    const sendBack = screen.getByRole('button', { name: 'Send back' }) as HTMLButtonElement
    expect(sendBack.disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Accept' }) as HTMLButtonElement).disabled).toBe(false)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'bindings look wrong' } })
    expect(sendBack.disabled).toBe(false)
  })

  it('sends the note with the return and nothing with the accept', async () => {
    const api = stubApi()
    await openTheRecord(api)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'wrong product line' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send back' }))
    await waitFor(() =>
      expect(api.transition).toHaveBeenCalledWith('i1', 'admin-returned', 'wrong product line'),
    )
  })

  it('surfaces the server’s refusal verbatim', async () => {
    // The client check is convenience; `transition()` is the rule. If the two
    // ever diverge the person must read the SERVER's sentence, not ours.
    const wire = 'intake i1 transition failed (422): a return goes back with a note — the SME needs the why'
    const api = stubApi({
      transition: vi.fn(async () => {
        throw new Error(wire)
      }),
    })
    await openTheRecord(api)
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))
    expect(await screen.findByText(wire)).toBeTruthy()
  })

  it('re-reads the queue after a decision instead of guessing the new state', async () => {
    const api = stubApi()
    await openTheRecord(api)
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))
    await waitFor(() => expect(api.list).toHaveBeenCalledTimes(2))
  })
})
