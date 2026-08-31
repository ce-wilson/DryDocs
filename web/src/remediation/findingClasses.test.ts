import { describe, expect, it } from 'vitest'

import { CLASSES, failureClassOf, groupFindings } from './findingClasses'
import { PROFILE, type Finding } from './profileData'

const f = (rule_id: string, severity = 'should-fix'): Finding => ({
  rule_id,
  severity,
  ratified: false,
  target: 'JOB:VAR',
  message: 'synthetic',
})

describe('failureClassOf', () => {
  it('classes the two rules detect.py names as classes', () => {
    expect(failureClassOf('R34')).toBe('confidently-wrong')
    expect(failureClassOf('R2')).toBe('silence')
  })

  // `conformance` is a real third answer, not a fallback: the rest of the
  // greenfield standard neither silences a row nor falsifies one.
  it('leaves every other rule in conformance', () => {
    expect(failureClassOf('R32')).toBe('conformance')
    expect(failureClassOf('R99-does-not-exist')).toBe('conformance')
  })
})

describe('groupFindings', () => {
  it('ranks confidently-wrong ahead of silence', () => {
    const ids = groupFindings([f('R2'), f('R34', 'must-fix')]).map((g) => g.id)
    expect(ids.indexOf('confidently-wrong')).toBeLessThan(ids.indexOf('silence'))
  })

  // A section that vanishes when empty reads as "this page does not check for
  // that" — and the page's whole claim is that both classes are looked for.
  it('returns every class even when a class is empty', () => {
    const groups = groupFindings([f('R32')])
    expect(groups).toHaveLength(CLASSES.length)
    expect(groups.find((g) => g.id === 'silence')?.count).toBe(0)
  })

  it('groups by rule id inside a class and counts the findings', () => {
    const groups = groupFindings([f('R32'), f('R32'), f('R35')])
    const conformance = groups.find((g) => g.id === 'conformance')!
    expect(conformance.count).toBe(3)
    expect(conformance.rules.map((r) => r.ruleId)).toEqual(['R32', 'R35'])
    expect(conformance.rules[0].findings).toHaveLength(2)
  })

  it('reports the WORST severity on a rule group, not the first', () => {
    const [worstFirst] = groupFindings([f('R32', 'advisory'), f('R32', 'must-fix')])
      .filter((g) => g.id === 'conformance')
      .flatMap((g) => g.rules)
    expect(worstFirst.severity).toBe('must-fix')
  })

  it('loses nothing: every finding lands in exactly one class', () => {
    const total = groupFindings(PROFILE.findings).reduce((n, g) => n + g.count, 0)
    expect(total).toBe(PROFILE.findings.length)
  })
})

// The committed artifact must actually exercise the split, or the frame
// demonstrates its headline claim with an empty section. Pinned on the Python
// side too (test_remediation_profile_json) — this is the console's own check
// that what it renders is what it promises.
describe('the committed profile demonstrates both classes', () => {
  it('has at least one finding in each of the two named classes', () => {
    const groups = groupFindings(PROFILE.findings)
    expect(groups.find((g) => g.id === 'confidently-wrong')!.count).toBeGreaterThan(0)
    expect(groups.find((g) => g.id === 'silence')!.count).toBeGreaterThan(0)
  })
})
