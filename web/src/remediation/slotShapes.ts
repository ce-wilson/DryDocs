// Client-side shape checks for the substitution form (O59).
//
// WHAT THIS IS FOR, and its ceiling. The form asks an SME for facts the export
// does not carry, and a typo in one of them becomes a proposal nobody
// re-checks. So the shape rule is shown beside the input and checked as it is
// typed. It is a TYPO CATCHER, not an authority: the rules come from the
// guidelines page via G68's slot list, the profile carries each slot's rule
// text verbatim, and nothing here ratifies a value.
//
// A SLOT WITH NO DECLARED SHAPE RETURNS `unchecked`, NOT `ok`. Four of the
// nine slots (USER, REC_ID, SOURCE_CONTACT, and any slot a future guidelines
// revision adds) have no shape rule on the page — SOURCE_CONTACT's own rule
// text says whether it must be a DL is an OPEN question. Inventing a pattern
// for them would be exactly the guessing that produced the drift C30
// documents, and a green tick against an invented rule is worse than no tick:
// it tells the SME a value was validated when nothing checked it.
//
// FTS_ID and DEVX_KEY carry the two rules the guidelines state as shapes, and
// EMAIL_DL_* is checked as an address only — an address, never a specific
// domain, because which domains are legal is an estate fact this repo does not
// hold.

export type ShapeVerdict = 'ok' | 'bad' | 'unchecked' | 'empty'

export interface ShapeResult {
  verdict: ShapeVerdict
  /** Shown beside the input when the verdict is `bad` or `unchecked`. */
  note: string
}

/** `^FTS[A-Z]*[0-9]+$` — the BARE id; `ST 6.0 - FTS2` is FTS2. */
const FTS_ID = /^FTS[A-Z]*[0-9]+$/
/** UPPER_SNAKE and hyphen-free: a hyphen is illegal in a Control-M name. */
const UPPER_SNAKE = /^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$/
/** An address, nothing stronger: local@domain.tld with no whitespace. */
const ADDRESS = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/
/** The closed vocabulary the guidelines state for the transfer mechanism. */
const DELIVERY_MECHANISMS = ['MFTS_AGENT', 'SFTP_DIRECT', 'API_GENERATED']

export function checkSlot(name: string, raw: string): ShapeResult {
  const value = raw.trim()
  if (!value) return { verdict: 'empty', note: '' }

  if (name === 'FTS_ID') {
    return FTS_ID.test(value)
      ? { verdict: 'ok', note: '' }
      : {
          verdict: 'bad',
          note: 'expected the BARE id, shape FTS[letters][digits] — drop version fragments (`ST 6.0 - FTS2` is FTS2)',
        }
  }

  if (name === 'DEVX_KEY') {
    if (value.includes('-')) {
      return {
        verdict: 'bad',
        note: 'a hyphen is illegal in a Control-M name — `DevX-project` becomes DEVX_PROJECT',
      }
    }
    return UPPER_SNAKE.test(value)
      ? { verdict: 'ok', note: '' }
      : { verdict: 'bad', note: 'expected UPPER_SNAKE (letters, digits and single underscores)' }
  }

  if (name === 'DELIVERY_MECHANISM') {
    return DELIVERY_MECHANISMS.includes(value)
      ? { verdict: 'ok', note: '' }
      : { verdict: 'bad', note: `expected one of ${DELIVERY_MECHANISMS.join(' | ')}` }
  }

  if (name.startsWith('EMAIL_DL_')) {
    return ADDRESS.test(value)
      ? { verdict: 'ok', note: '' }
      : { verdict: 'bad', note: 'expected a single address — one distribution list, not a list of them' }
  }

  return {
    verdict: 'unchecked',
    note: 'no shape rule on the guidelines page — recorded as typed, and not validated',
  }
}
