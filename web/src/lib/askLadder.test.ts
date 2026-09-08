import { describe, expect, it } from 'vitest'

import { SUPPORT_HANDOFF, ladderStages, type LadderStage } from './askLadder'
import type { ProbeResult, ServiceId, ServiceVerdict } from './serviceProbe'

// O63 — the ladder's STATE MACHINE, which is what the acceptance asks be
// tested, explicitly "rather than its copy".
//
// That distinction is the reason `ladderStages` is a pure function at all. A
// machine living inside JSX can only be tested by rendering it and reading
// strings back, which is a test of the wording — so a copy edit would go red
// and a broken transition would not. Everything below asserts SHAPE and ORDER;
// the one string it does check verbatim is the originating error, because
// leaving that untouched IS clause (a).

function verdict(id: ServiceId, state: ServiceVerdict['state'], detail: string | null = null) {
  return { id, label: id, state, detail } satisfies ServiceVerdict
}

function probe(...services: ServiceVerdict[]): ProbeResult {
  return { services, checkedAt: new Date('2026-09-06T12:00:00Z') }
}

const kinds = (stages: LadderStage[]) => stages.map((s) => s.kind)

describe('the Ask failure ladder', () => {
  it('(a) renders the originating error FIRST and verbatim', () => {
    const stages = ladderStages('Failed to fetch', null)
    expect(stages[0]).toEqual({ kind: 'original', text: 'Failed to fetch' })
  })

  it('(a) never re-words, prefixes or friendlies the browser text', () => {
    // The exact string is what a reader pastes into a search or a ticket, so
    // this asserts the ABSENCE of decoration rather than the presence of any.
    const raw = 'Failed to fetch'
    const [first] = ladderStages(raw, probe(verdict('agent', 'ok')))
    expect(first).toEqual({ kind: 'original', text: raw })
    expect((first as { text: string }).text).not.toMatch(/sorry|oops|problem|error:/i)
  })

  it('(b) shows `checking` while the probe is in flight, and no verdict yet', () => {
    const stages = ladderStages('Failed to fetch', null)
    expect(kinds(stages)).toEqual(['original', 'checking'])
    // A slow probe must never look like a verdict: nothing here is a service
    // row and nothing is a hand-off.
    expect(stages.some((s) => s.kind === 'service' || s.kind === 'handoff')).toBe(false)
  })

  it('(c) reports the agent transport once the probe lands', () => {
    const stages = ladderStages(
      'Failed to fetch',
      probe(verdict('api', 'ok'), verdict('agent', 'down', 'nothing answered')),
    )
    const agent = stages.find((s) => s.kind === 'service' && s.verdict.id === 'agent')
    expect(agent).toBeTruthy()
    expect(kinds(stages)).toEqual(['original', 'service'])
  })

  it('(d) carries the provider error VERBATIM when the transport is green', () => {
    // The worked example from the item. The string names the exact key AND the
    // exact file, and any paraphrase loses one or both — so it is asserted
    // whole, which is the one place this file does check copy on purpose.
    const detail = 'ANTHROPIC_API_KEY is not set (agents/.env)'
    const stages = ladderStages(
      'agent error',
      probe(verdict('agent', 'ok'), verdict('provider', 'down', detail)),
    )
    const provider = stages.find((s) => s.kind === 'service' && s.verdict.id === 'provider')
    expect(provider && 'verdict' in provider && provider.verdict.detail).toBe(detail)
  })

  it('(e) hands off to support only when nothing is left to fix', () => {
    const allGreen = ladderStages(
      'Failed to fetch',
      probe(verdict('api', 'ok'), verdict('agent', 'ok'), verdict('provider', 'ok')),
    )
    expect(kinds(allGreen).at(-1)).toBe('handoff')
    expect(allGreen.at(-1)).toEqual({ kind: 'handoff', text: SUPPORT_HANDOFF })
  })

  it('(e) does NOT hand off while a self-serviceable failure is on screen', () => {
    // A red row IS the reader's next action. Offering support beside it buries
    // the fixable thing under the unfixable one.
    const stages = ladderStages('Failed to fetch', probe(verdict('agent', 'down', 'nothing')))
    expect(kinds(stages)).not.toContain('handoff')
  })

  it('a `not-checked` never earns a hand-off — it was never asked', () => {
    // Rule 1 wearing a different hat: telling someone to contact support
    // because a probe was SKIPPED is an invented verdict. Here the provider was
    // not checked (no agent to ask), and the agent itself is down, so the
    // actionable row stands alone.
    const stages = ladderStages(
      'Failed to fetch',
      probe(verdict('agent', 'down', 'nothing answered'), verdict('provider', 'not-checked')),
    )
    expect(kinds(stages)).not.toContain('handoff')
  })

  it('the full ladder runs error -> checking -> verdict -> hand-off across two calls', () => {
    // The state machine end to end, as the acceptance describes it: the same
    // originating error, before and after the probe resolves.
    const before = ladderStages('Failed to fetch', null)
    const after = ladderStages(
      'Failed to fetch',
      probe(verdict('api', 'ok'), verdict('agent', 'ok'), verdict('provider', 'ok')),
    )
    expect(kinds(before)).toEqual(['original', 'checking'])
    expect(kinds(after)).toEqual(['original', 'service', 'service', 'handoff'])
    expect(before[0]).toEqual(after[0])
  })

  it('a green api and graph are not rendered as news, but a red one is', () => {
    const green = ladderStages(
      'Failed to fetch',
      probe(verdict('api', 'ok'), verdict('graph', 'ok'), verdict('agent', 'ok')),
    )
    const ids = green
      .filter((s): s is { kind: 'service'; verdict: ServiceVerdict } => s.kind === 'service')
      .map((s) => s.verdict.id)
    expect(ids).toEqual(['agent'])

    const redGraph = ladderStages(
      'Failed to fetch',
      probe(verdict('api', 'ok'), verdict('graph', 'down', 'refused'), verdict('agent', 'ok')),
    )
    const redIds = redGraph
      .filter((s): s is { kind: 'service'; verdict: ServiceVerdict } => s.kind === 'service')
      .map((s) => s.verdict.id)
    expect(redIds).toEqual(['graph', 'agent'])
  })
})
