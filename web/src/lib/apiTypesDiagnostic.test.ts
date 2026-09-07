import { describe, expect, it } from 'vitest'

import { failureText, schemaProblem } from '../../scripts/writeApiTypes'

// UNDER src/lib/ RATHER THAN BESIDE api.test.ts, and the reason is the port
// manifest and not taste: `web/src/generated/**` carries the `derived`
// disposition — the company side REGENERATES that directory — so a hand-written
// test placed there would be a hand-written file inside a regenerated tree. It
// still has to live under src/ because vitest collects `src/**` only.
//
// WEB16 — the diagnostic, tested, because a diagnostic nobody exercises drifts
// into being wrong. The one this replaces was a JSON parse error standing in
// for three different causes: a missing file, an empty one (what a failed dump
// used to leave behind, before API3), and a document that is not OpenAPI.

describe('what api:types says when the schema is not usable', () => {
  it('names an EMPTY file as empty, not as a syntax error at position 0', () => {
    // The exact state a pre-API3 interrupted dump left in the working tree.
    const problem = schemaProblem('')
    expect(problem).toContain('EMPTY')
    expect(problem).toContain('a previous dump was interrupted')
    expect(schemaProblem('   \n')).toBe(problem)
  })

  it('distinguishes unreadable, unparseable, and not-an-OpenAPI-document', () => {
    expect(schemaProblem(null)).toContain('cannot read')
    expect(schemaProblem('{ not json')).toContain('not valid JSON')
    expect(schemaProblem('{"openapi": "3.1.0"}')).toContain('declares no `paths`')
  })

  it('passes a real document', () => {
    expect(schemaProblem('{"openapi": "3.1.0", "paths": {}}')).toBeNull()
  })
})

describe('the failure message', () => {
  const text = failureText('src/generated/openapi.json is EMPTY')

  it('names the variable, and names it as the WRITER’s requirement', () => {
    // Clause (b): the variable is named before any traceback. Clause (a) is met
    // by this message rather than by a check, because `api:types` genuinely
    // does not need DRYDOCS_DATA_ROOT — it reads a committed JSON file — and a
    // check here would refuse a run that would have succeeded.
    expect(text).toContain('DRYDOCS_DATA_ROOT')
    expect(text).toContain('required by THAT script, not by this one')
  })

  it('names the writer and the order to run the pair in', () => {
    expect(text).toContain('scripts/dump_openapi.py')
    expect(text).toContain('npm run api:types')
    expect(text.indexOf('dump_openapi.py')).toBeLessThan(text.indexOf('npm run api:types'))
  })

  it('leads with the problem, so the cause is the first line', () => {
    expect(text.split('\n')[0]).toBe('api:types FAILED: src/generated/openapi.json is EMPTY')
  })
})
