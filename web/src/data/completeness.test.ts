import { describe, expect, it } from 'vitest'

import { SRC, codeOnly, filesMatching, readFileSync, tsSources } from '../test/sourceScan'
import { completeOf, completenessOf, completenessTitle } from './completeness'
import type { SpecResult } from '../lib/graph'

// WEB19 — the instrument that makes the wrong version fail.
//
// The module sweep's first cycle ended on one conclusion: the right answer to
// the completeness contract existed six times, was written down zero times, and
// recurred seven times. The second pass then measured the propagation event
// itself — the contract landed 2026-09-05, a new consumer was built 2026-09-06,
// and it dropped the flag on its first day.
//
// A seventh convention would have been the eighth recurrence, so the convention
// is a test. It enumerates every DIRECT spec consumer in the console and fails
// one that renders rows without ever naming their completeness. What it cannot
// check is whether the badge is in a sensible place; what it can check is that
// the surface had to think about it, which is the step that was being skipped.

const specResult = (over: Partial<SpecResult> = {}): SpecResult => ({
  spec_id: 'test.spec.v1',
  database: 'drydocs',
  classification: 'Internal',
  columns: [{ name: 'a', type: 'string', label: 'A' }],
  keys: ['a'],
  rows: [{ a: '1' }, { a: '2' }],
  cypher: 'MATCH (n) RETURN n',
  params: {},
  watermarked: false,
  truncated: false,
  ephemeral: false,
  ...over,
})

describe('the completeness envelope', () => {
  it('reads the server flag rather than inferring it from the row count', () => {
    // The whole point of API1's probe at limit + 1: two rows under a ceiling of
    // two is NOT truncated unless the server says so, and two rows IS truncated
    // when it does. `rows.length === limit` answers both of those wrong.
    expect(completenessOf(specResult({ truncated: false, limit: 2 })).truncated).toBe(false)
    expect(completenessOf(specResult({ truncated: true, limit: 2 })).truncated).toBe(true)
  })

  it('defaults shown to the rows that arrived, and takes a surface own count when given', () => {
    expect(completenessOf(specResult()).shown).toBe(2)
    // A map places some rows and refuses others; what it drew is what it says.
    expect(completenessOf(specResult(), 1).shown).toBe(1)
  })

  it('carries a null ceiling for a spec that declares none, never a zero', () => {
    // Zero would render as "capped at 0 rows", which is a sentence about a
    // ceiling that does not exist.
    expect(completenessOf(specResult()).limit).toBeNull()
    expect(completenessOf(specResult({ limit: null })).limit).toBeNull()
    expect(completenessOf(specResult({ limit: 500 })).limit).toBe(500)
  })

  it('says a complete result is complete, and never invents the total of a capped one', () => {
    const complete = completenessTitle(completeOf(12), 'rows', 'row')
    expect(complete).toMatch(/on screen/)
    expect(complete).not.toMatch(/[Cc]apped/)

    const capped = completenessTitle({ truncated: true, shown: 500, limit: 500 }, 'rows', 'row')
    expect(capped).toMatch(/Capped at 500 rows/)
    expect(capped).toMatch(/what arrived, not of what exists/)

    // No ceiling declared: the server capped it and did not say where.
    const unstated = completenessTitle({ truncated: true, shown: 500, limit: null }, 'rows', 'row')
    expect(unstated).toMatch(/capped by the server/)
    expect(unstated).not.toMatch(/\bnull\b/)
  })
})

// ── the consumer guard ──────────────────────────────────────────────────────

/** A DIRECT spec consumer: it runs a spec itself, or reads one through the
 *  shared hooks, and therefore holds rows whose completeness only it can
 *  report. `useLiveOrDemo` is not in this pattern — it hands its caller the
 *  whole `SpecResult`, so the envelope leaves that seam intact. */
const CONSUMER = /\b(runSpec|useGraphQuery|useSpecRows)(<[^(]*>)?\s*\(/

/** Naming the envelope at all. Deliberately loose: the guard's job is to make
 *  the flag impossible to be unaware of, not to dictate how it is rendered. */
const ENVELOPE = /\b(completeness|truncated|CompletenessNotice)\b/

/** Consumers that legitimately name no envelope, each with the reason.
 *
 *  A reason, not a checkbox: an exemption list without them becomes the place
 *  offenders are filed. Every entry here is either transport (it moves a result
 *  it does not render) or a surface that renders no LIST, which is what the flag
 *  qualifies. A surface that renders rows to a reader does not belong here. */
const EXEMPT: Record<string, string> = {
  'lib/graphApi.ts':
    'the API adapter - it carries the whole SpecResult across the seam, envelope included, and renders nothing',
  'data/graphAccess.ts':
    'the transport hook - its QueryState is generic over the result and hands SpecResult on unopened',
  'data/provenance.ts':
    'the live-or-demo seam - its live and empty arms carry data: SpecResult, so the envelope reaches the caller intact',
  'routes/OverviewRoute.tsx':
    'consumes rows as a LOOKUP, not a list - status-item strings become fixed spokes, and no row is rendered as a row',
  'routes/SoftwareRoute.tsx':
    'consumes rows as a LOOKUP, not a list - a product-id to document-count map behind a declaration-only view',
}

describe('every spec consumer reads the completeness envelope (WEB19)', () => {
  const consumers = filesMatching(CONSUMER, codeOnly, tsSources())

  it('finds the consumers at all, so a broken scan cannot pass vacuously', () => {
    // The failure mode this guards against: a pattern that matches nothing
    // reports perfect compliance. Four surfaces were migrated at WEB19 and four
    // more read specs directly; a scan returning fewer than that is broken.
    expect(consumers.length).toBeGreaterThanOrEqual(8)
  })

  it('fails a consumer that renders rows without ever naming their completeness', () => {
    const silent = consumers
      .filter((f) => !(f in EXEMPT))
      .filter((f) => !ENVELOPE.test(codeOnly(readFileSync(`${SRC}/${f}`, 'utf8'))))
    expect(silent, silent.join(', ')).toEqual([])
  })

  it('holds every exemption to a real, live consumer with a stated reason', () => {
    // The allow-list shrinks with the code: an entry whose file stopped reading
    // specs, or was deleted, fails here rather than sitting as a permanent
    // licence. The same shape WEB12's transport-preamble list uses.
    for (const [path, reason] of Object.entries(EXEMPT)) {
      expect(consumers, `${path} is exempted but no longer reads a spec`).toContain(path)
      expect(reason.length, `${path} needs a reason, not a checkbox`).toBeGreaterThan(40)
    }
  })

  it('names the four surfaces WEB19 migrated, so a regression fails rather than passing quietly', () => {
    // The review counted these four dropping the flag they were handed. They are
    // asserted BY NAME because a future refactor that re-hand-rolled one of their
    // fetch effects would otherwise only have to stop matching CONSUMER to pass.
    for (const path of [
      'components/map/RuntimeSpanMap.tsx',
      'components/map/LocationMap.tsx',
      'ask/FileReport.tsx',
      'routes/IntakeRoute.tsx',
    ]) {
      expect(consumers, `${path} no longer reads a spec through the shared hook`).toContain(path)
      expect(ENVELOPE.test(codeOnly(readFileSync(`${SRC}/${path}`, 'utf8')))).toBe(true)
    }
  })

  it('leaves no hand-rolled spec fetch outside the shared seams', () => {
    // A bare `.runSpec(` in a component is the shape that dropped the envelope
    // four times: it returns a SpecResult and every caller re-invented what to
    // do with it. The seams below are the only places it may be called.
    const SEAMS = ['lib/graph.ts', 'lib/graphApi.ts', 'lib/neo4j.ts', 'data/graphAccess.ts']
    const callers = filesMatching(/\.runSpec\s*\(/, codeOnly, tsSources()).filter(
      (f) => !SEAMS.includes(f),
    )
    expect(callers, callers.join(', ')).toEqual([])
  })
})
