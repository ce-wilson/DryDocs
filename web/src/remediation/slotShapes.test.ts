import { describe, expect, it } from 'vitest'

import { checkSlot } from './slotShapes'
import { PROFILE } from './profileData'

describe('FTS_ID', () => {
  it('accepts the bare id', () => {
    expect(checkSlot('FTS_ID', 'FTS2').verdict).toBe('ok')
    expect(checkSlot('FTS_ID', 'FTSCAT1').verdict).toBe('ok')
  })

  // The rule text names this exact mistake: `ST 6.0 - FTS2` is FTS2.
  it('rejects a version fragment', () => {
    const res = checkSlot('FTS_ID', 'ST 6.0 - FTS2')
    expect(res.verdict).toBe('bad')
    expect(res.note).toContain('FTS2')
  })
})

describe('DEVX_KEY', () => {
  it('accepts UPPER_SNAKE', () => {
    expect(checkSlot('DEVX_KEY', 'SYNTH_INTAKE').verdict).toBe('ok')
  })

  it('names the hyphen specifically, since that is the rule’s own example', () => {
    const res = checkSlot('DEVX_KEY', 'DevX-project')
    expect(res.verdict).toBe('bad')
    expect(res.note).toContain('hyphen')
  })

  it('rejects lower case', () => {
    expect(checkSlot('DEVX_KEY', 'synth_intake').verdict).toBe('bad')
  })
})

describe('DELIVERY_MECHANISM', () => {
  it('accepts a member of the closed vocabulary', () => {
    expect(checkSlot('DELIVERY_MECHANISM', 'MFTS_AGENT').verdict).toBe('ok')
  })

  it('rejects anything else and lists the alternatives', () => {
    const res = checkSlot('DELIVERY_MECHANISM', 'MFTS')
    expect(res.verdict).toBe('bad')
    expect(res.note).toContain('SFTP_DIRECT')
  })
})

describe('EMAIL_DL_*', () => {
  it('accepts one address', () => {
    expect(checkSlot('EMAIL_DL_L3', 'l3_support@example.invalid').verdict).toBe('ok')
  })

  it('rejects a list, because the slot holds ONE distribution list', () => {
    expect(checkSlot('EMAIL_DL_PDN', 'a@example.invalid, b@example.invalid').verdict).toBe('bad')
  })
})

// The honesty clause, and the reason this module exists as its own file: a
// green tick against an invented pattern tells the SME a value was validated
// when nothing checked it.
describe('slots with no declared shape', () => {
  it('returns unchecked rather than ok', () => {
    for (const name of ['USER', 'REC_ID', 'SOURCE_CONTACT']) {
      const res = checkSlot(name, 'anything at all')
      expect(res.verdict).toBe('unchecked')
      expect(res.note).toContain('not validated')
    }
  })

  it('says unchecked for a slot name it has never seen', () => {
    expect(checkSlot('A_FUTURE_SLOT', 'x').verdict).toBe('unchecked')
  })
})

describe('an empty input is its own verdict', () => {
  it('is empty, not bad — the SME has simply not answered yet', () => {
    expect(checkSlot('FTS_ID', '').verdict).toBe('empty')
    expect(checkSlot('FTS_ID', '   ').verdict).toBe('empty')
  })
})

// Every slot the real profile carries must reach a verdict this module can
// render. Without this, adding a slot to G68's list would silently produce a
// row the form cannot describe.
describe('every slot in the committed profile is answerable', () => {
  it('reaches a verdict for each slot name', () => {
    for (const slot of PROFILE.substitution_slots) {
      expect(['ok', 'bad', 'unchecked']).toContain(checkSlot(slot.name, 'PLACEHOLDER_1').verdict)
    }
  })
})
