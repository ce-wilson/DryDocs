// The two failure classes, kept apart (O59).
//
// WHY THIS IS NOT A SORT. detect.py's own module docstring draws the line:
//
//   "Name drift produces SILENCE: the variable misses the fact registry, no
//    STG_APP_FACT row is written, and lineage is simply absent. A value
//    contract breach produces a CONFIDENTLY WRONG row: the name hits, so the
//    graph gains a fact whose value is false. The second is worse ... filing
//    it as a lint warning next to a rename suggestion would bury it."
//
// A page that ranks the two together teaches the reader the wrong triage
// order, which is why O59 required them reported apart rather than merely
// sorted by severity. Severity ALSO happens to rank them correctly today
// (R34 is must-fix, R2 is should-fix) — that is the point at which a sort
// looks sufficient and is not: severity is a per-rule judgement that can be
// re-ruled at the registry, and the class is a property of what the defect
// DOES to the downstream row. They are allowed to disagree.
//
// THE MAP IS DELIBERATELY TINY AND EXPLICIT. Only the two rules detect.py
// names as classes are classed; every other rule is `conformance`, which is a
// real third answer and not a fallback bucket — the greenfield standard's
// other rules are conformance checks that neither silence a row nor falsify
// one. A new rule therefore lands in `conformance` rather than being
// mis-filed into a class nobody assigned it to.

import type { Finding } from './profileData'

export type FailureClass = 'confidently-wrong' | 'silence' | 'conformance'

/** R2 — name drift. R34 — value contract. Both spellings are detect.py's. */
const CLASS_BY_RULE: Record<string, FailureClass> = {
  R2: 'silence',
  R34: 'confidently-wrong',
}

export function failureClassOf(ruleId: string): FailureClass {
  return CLASS_BY_RULE[ruleId] ?? 'conformance'
}

export interface ClassDef {
  id: FailureClass
  title: string
  /** What the defect does to the downstream row — the reason for the split. */
  effect: string
  token: '--status-fail-soft' | '--yellow' | '--muted'
}

/** Ordered worst-first. The order IS the triage lesson. */
export const CLASSES: readonly ClassDef[] = [
  {
    id: 'confidently-wrong',
    title: 'Confidently wrong',
    effect:
      'the name resolves, so a fact row IS written — carrying a false value. Worse than a missing row, because nothing downstream looks broken.',
    token: '--status-fail-soft',
  },
  {
    id: 'silence',
    title: 'Silence',
    effect:
      'the drifted name misses the fact registry, so NO row is written at all. The lineage is missing, not wrong — and an absence reports nothing.',
    token: '--yellow',
  },
  {
    id: 'conformance',
    title: 'Other conformance',
    effect:
      'neither silences a row nor falsifies one — the rest of the greenfield job standard.',
    token: '--muted',
  },
]

export interface RuleGroup {
  ruleId: string
  /** The worst severity on the group, by detect.py's vocabulary. */
  severity: string
  findings: Finding[]
}

export interface ClassGroup extends ClassDef {
  rules: RuleGroup[]
  count: number
}

const SEVERITY_ORDER = ['must-fix', 'should-fix', 'advisory']

function worst(findings: Finding[]): string {
  const ranks = findings.map((f) => {
    const i = SEVERITY_ORDER.indexOf(f.severity)
    return i === -1 ? SEVERITY_ORDER.length : i
  })
  return SEVERITY_ORDER[Math.min(...ranks)] ?? findings[0].severity
}

/**
 * Group findings by class, then by rule id within a class.
 *
 * Every class is returned even when empty: a section that disappears when it
 * has nothing in it reads as "this page does not check for that", and the
 * whole claim here is that both classes are being looked for.
 */
export function groupFindings(findings: readonly Finding[]): ClassGroup[] {
  return CLASSES.map((def) => {
    const mine = findings.filter((f) => failureClassOf(f.rule_id) === def.id)
    const byRule = new Map<string, Finding[]>()
    for (const f of mine) {
      const list = byRule.get(f.rule_id)
      if (list) list.push(f)
      else byRule.set(f.rule_id, [f])
    }
    const rules = [...byRule.entries()]
      .map(([ruleId, list]) => ({ ruleId, severity: worst(list), findings: list }))
      .sort(
        (a, b) =>
          SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity) ||
          b.findings.length - a.findings.length ||
          a.ruleId.localeCompare(b.ruleId)
      )
    return { ...def, rules, count: mine.length }
  })
}
