import type { IntakeRecord, IntakeRow } from './intakeApi'

// O50 — the admin review queue's pure half (plan §7). The component renders
// what this decides; the SERVER still owns the status machine (the action
// buttons come from `legal_transitions`, never from anything here).

/** The two gates that hold an accepted record, named (plan §7, "the load
 *  boundary is absolute and pre-ruled").
 *
 *  ONE HOME, and it is here rather than in the two components that print it:
 *  the stepper's chip and the queue's parked group say the same thing, and a
 *  second copy is how one of them ends up naming a gate that moved. The API
 *  says only `waiting_on_gate: true` — a boolean, because the server's job is
 *  the machine and not the prose — so the WHAT is the console's to carry, and
 *  it is carried as data so a test can read it. */
export const WAITING_ON = [
  { what: 'Corpus load (Document → Chunk)', gate: 'Q10 ← G31 ← G32' },
  { what: 'Assignment edge (email Document → ControlMFolder)', gate: "Q10's HITL gate" },
] as const

/** The one-line version, for the stepper. Says what acceptance did NOT do,
 *  because that is the half a reader gets wrong: "accepted" reads as "loaded"
 *  on every other queue they have used. */
export const WAITING_ON_SUMMARY =
  'Parked: the load is Q10’s, behind its gates. Acceptance here writes nothing to the graph.'

/** Records the admin has to look at… */
export const REVIEW_STATUS = 'sme-confirmed'
/** …and records they already accepted, which stay visible because the park IS
 *  the state worth seeing (a record that vanished on accept would look loaded). */
export const PARKED_STATUS = 'admin-accepted'

export interface ReviewQueue<T> {
  awaiting: T[]
  parked: T[]
}

/** Split the queue into the two groups above. Everything else — drafts, the
 *  SME's work in flight, closed threads — is not the admin's rail and is left
 *  out rather than greyed: this is a work queue, not a record browser. */
export function reviewQueue<T extends { status: string }>(rows: readonly T[]): ReviewQueue<T> {
  return {
    awaiting: rows.filter((r) => r.status === REVIEW_STATUS),
    parked: rows.filter((r) => r.status === PARKED_STATUS),
  }
}

export interface Fact {
  label: string
  value: string | null
}

/** The area levels, in the cascade's own order (IntakeRoute section 1). */
const AREA_LEVELS: { key: string; label: string }[] = [
  { key: 'product_line_id', label: 'Product line' },
  { key: 'product_id', label: 'Product' },
  { key: 'area_product_id', label: 'Area product' },
  { key: 'seal_id', label: 'SEAL id' },
]

/** What the SME answered: the record's own fields. */
export function confirmedByTheSme(record: IntakeRow): Fact[] {
  return [
    { label: 'Context type', value: record.context_type },
    ...AREA_LEVELS.map((l) => ({ label: l.label, value: record.area[l.key] ?? null })),
    { label: 'Note', value: record.note.trim() || null },
  ]
}

/** What the parser READ off the uploaded bytes — `_parse_preview`'s output per
 *  evidence file, flattened.
 *
 *  READ, not PROPOSED, and the distinction is the whole reason this function is
 *  separate from the one below. These are email header facts (subject, from,
 *  date) and json top-level keys. They are not answers to the questions the SME
 *  answered, so putting them beside the SME's picks as a two-column DIFF would
 *  manufacture agreement or disagreement out of two unrelated field sets. They
 *  are shown as the other side of the record, labelled as what they are. */
export function readByTheExtractor(record: IntakeRecord): Fact[] {
  const facts: Fact[] = []
  for (const e of record.evidence.filter((x) => !x.superseded)) {
    const preview = e.preview ?? {}
    for (const [k, v] of Object.entries(preview)) {
      facts.push({
        label: `${e.filename} · ${k}`,
        value: v === null || v === undefined ? null : Array.isArray(v) ? v.join(', ') : String(v),
      })
    }
  }
  return facts
}

/** Why the proposed-bindings column is empty, said out loud.
 *
 *  The acceptance asks for "what the SME confirmed vs what the extractor
 *  proposed". The proposal side is section 4's candidate-binding set — one row
 *  per recognized entity with `status: proposed` — and it has NO PRODUCER: O48
 *  builds the panel that makes it and the O46 store has no column to hold it.
 *  So the panel prints this instead of a blank pane, and instead of diffing the
 *  header facts above against the SME's picks to produce a delta that would
 *  mean nothing. An empty column with no explanation reads as "the extractor
 *  proposed nothing about this evidence", which is a different and false claim. */
export const NO_PROPOSED_BINDINGS =
  'No proposed bindings to compare: the candidate-binding set is section 4’s output and lands with O48. The intake store has no column for it yet, so there is nothing here to have proposed.'

export interface ReviewSides {
  confirmed: Fact[]
  extracted: Fact[]
  /** O48's candidate-binding set. `null` = the producer does not exist yet;
   *  a list (including an empty one) will mean the extractor ran and found
   *  what it found. The two are different facts and the type keeps them apart. */
  proposed: Fact[] | null
  /** The delta the server computed for a thread continuation, and the SME's
   *  ruling on it — the one machine-proposed / human-disposed pair that DOES
   *  exist in today's store. */
  threadDelta: string | null
  threadDecision: string | null
}

export function reviewSides(record: IntakeRecord): ReviewSides {
  return {
    confirmed: confirmedByTheSme(record),
    extracted: readByTheExtractor(record),
    proposed: null,
    threadDelta: record.review_payload,
    threadDecision: record.thread_decision,
  }
}

/** The Send-back note rule, client-side.
 *
 *  The SERVER is the rule (`transition()` raises IntakeValidationError → 422
 *  on a blank note). This is convenience only, so the admin learns before the
 *  round trip — and the queue still surfaces the server's message verbatim if
 *  one arrives, because a client check that silently diverged from the server's
 *  would be worse than none. */
export function returnNoteIsUsable(note: string): boolean {
  return note.trim().length > 0
}

/** The transition that carries the note requirement. Read off the server's map
 *  by `to`, never by button order. */
export const RETURN_TO = 'admin-returned'
