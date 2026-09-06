import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

import { parseAdkEvent, type AskEnvelope, type AskStep } from './askApi'
import { filesMatching, withoutComments } from '../test/sourceScan'

// R12 — the OTHER end of the stub-ADK fixture.
//
// tests/stub_adk.py serves the ADK contract with no LLM key, and
// tests/integration/test_stub_adk_ask_wiring.py drives it against a real
// drydocs-api. That proves the stub is faithful to the SERVER side of the
// handshake. It cannot prove the console can read what the stub emits, because
// the console's parser is TypeScript and that test is Python.
//
// So the stub's stream is committed as a fixture, the python test asserts byte
// for byte that the stub still produces it, and this parses it with the REAL
// parseAdkEvent — not a re-implementation. Two ends, one recorded artifact
// between them, and neither end can drift without the other going red.
//
// THE FRAME SPLITTING IS DELIBERATELY DUPLICATED from lib/adk.ts rather than
// extracted and shared. Sharing it would make this test agree with adk.ts by
// construction, which is the one thing it must not do: the question here is
// whether the wire format the stub writes is the wire format the console reads,
// and a shared splitter would answer that question with itself.

const SSE = readFileSync(
  resolve(process.cwd(), '..', 'tests', 'fixtures', 'adk', 'stub-run-sse.txt'),
  'utf8',
)

/** SSE frames, split the way lib/adk.ts's reader loop does. */
function frames(body: string): unknown[] {
  const out: unknown[] = []
  for (const frame of body.split('\n\n')) {
    for (const line of frame.split('\n')) {
      if (!line.startsWith('data:')) continue
      out.push(JSON.parse(line.slice(5).trim()))
    }
  }
  return out
}

describe('the console can read what the stub emits', () => {
  it('the fixture is a real recorded stream, not an empty file', () => {
    // The vacuous-pass guard: every assertion below is over `frames(SSE)`, and
    // a missing or empty fixture would make them all trivially true.
    expect(SSE.length).toBeGreaterThan(200)
    expect(SSE).toContain('data:')
    expect(frames(SSE)).toHaveLength(3)
  })

  it('parseAdkEvent classifies every frame — none is silently dropped', () => {
    const parsed = frames(SSE).map((f) => parseAdkEvent(f as never))
    expect(parsed.every((p) => p !== null)).toBe(true)
    expect(parsed.map((p) => p?.kind)).toEqual(['step', 'step', 'final'])
  })

  it('the steps carry what the Ask surface renders', () => {
    const steps = frames(SSE)
      .map((f) => parseAdkEvent(f as never))
      .filter((p): p is { kind: 'step'; step: AskStep } => p?.kind === 'step')
      .map((p) => p.step)
    expect(steps.map((s) => s.kind)).toEqual(['router', 'spec'])
    const spec = steps[1]
    expect(spec.database).toBe('drydocs')
    expect(spec.cypher).toContain('MATCH')
    // `explore_ref` is null in the recorded stream because the fixture is
    // generated with no registrar — the R4 round trip is the python test's job,
    // and recording a real ref would put a session-scoped id in the tree.
    expect(spec.explore_ref).toBeNull()
  })

  it('the last frame is the ENVELOPE, which is what ends a turn', () => {
    const parsed = frames(SSE).map((f) => parseAdkEvent(f as never))
    const last = parsed[parsed.length - 1]
    expect(last?.kind).toBe('final')
    const envelope = (last as { kind: 'final'; envelope: AskEnvelope }).envelope
    // askApi.ask throws "agent returned no envelope" if nothing final arrives,
    // and `status` is the only thing that makes a payload final.
    expect(envelope.status).toBe('ok')
    expect(envelope.answer).toBeTruthy()
    expect(envelope.metrics?.llm_calls).toBe(0)
    expect(envelope.model).toBeNull()
  })

  it('NOTHING SHIPPABLE reaches for the stub or its fixture', () => {
    // The acceptance's last line: "the stub never ships in web/dist". The stub
    // itself is Python under tests/ and could not, but the FIXTURE is a file in
    // the repo that a component could import — and once imported it is an entry
    // reachable from src/main.tsx and therefore in the bundle. filesMatching
    // excludes test files by construction, so a hit here is a real one.
    //
    // Asserted rather than argued, because "it obviously cannot happen" is how
    // a demo fixture ends up in production twice.
    expect(filesMatching(/stub-run-sse|stub_adk|stubStream/, withoutComments)).toEqual([])
  })

  it('a step frame and the envelope are told apart by shape, not by position', () => {
    // The parser's rule, exercised against the fixture's own payloads rather
    // than against invented ones: a payload with `kind: 'step'` is a step and a
    // payload with a string `status` is final. Reordering the stream must not
    // change the classification.
    const reversed = frames(SSE).reverse()
    expect(reversed.map((f) => parseAdkEvent(f as never)?.kind)).toEqual(['final', 'step', 'step'])
  })
})
