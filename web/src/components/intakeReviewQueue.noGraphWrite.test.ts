import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { codeOnly, SRC, withoutComments } from '../test/sourceScan'

// O50's absolute clause, asserted instead of claimed: "acceptance here never
// triggers a load, and no code path from this surface writes the graph."
//
// A COMMENT SAYING SO IS NOT A GUARD. The queue's header says it, and a header
// stays true only until the day someone adds a "load it now" button because the
// record is sitting right there and the graph client is one import away. The
// load waits on Q10 behind G31/G32 — a ruling about database topology that has
// not been made — so a write from here would not be a premature feature, it
// would be a decision taken by a UI.
//
// J66: the scan runs over `codeOnly`, because the paragraph above quotes every
// name it forbids. A raw substring scan would fail on its own explanation.

const QUEUE = join(SRC, 'components', 'IntakeReviewQueue.tsx')
const LIB = join(SRC, 'lib', 'intakeReview.ts')

/** Every seam that reaches the graph, or a write of any kind, from web/src.
 *  Names, not shapes: these are the imports and call sites that exist today,
 *  and a new one arriving without a row here is what O42's resolver is for. */
const GRAPH_SEAMS = [
  'useGraphAccess', // the console's graph client
  'runSpec', // a QuerySpec read
  'runCypher', // the ADR 0005 sandbox path
  'createGraphApi',
  'boltAllowed',
  'lib/graph',
  'data/graphAccess',
]

describe('the review queue writes no graph', () => {
  it('imports no graph seam, and calls none', () => {
    for (const file of [QUEUE, LIB]) {
      const code = codeOnly(readFileSync(file, 'utf8'))
      for (const seam of GRAPH_SEAMS) {
        expect(code.includes(seam), `${file} reaches the graph through ${seam}`).toBe(false)
      }
    }
  })

  it('reaches the server through the intake client only', () => {
    // The positive half. Absence proves nothing on its own — a file that
    // imported a graph client under a new name would pass the scan above — so
    // this pins what the queue DOES talk to: one API surface, whose write
    // routes are the four /intake/* handlers and no others.
    //
    // `withoutComments`, not `codeOnly`: the subject here IS an import path,
    // which is a string literal, and codeOnly neutralises those by design. The
    // cost is that a literal containing one of these words would match — worth
    // it, because the alternative is asserting nothing about what it DOES talk
    // to.
    const code = withoutComments(readFileSync(QUEUE, 'utf8'))
    expect(code).toContain("from '../lib/intakeApi'")
    expect(code).not.toContain('fetch(')
    expect(code).not.toContain('XMLHttpRequest')
  })

  it('the scanner strips the prose that quotes the seams', () => {
    // Instrument check (J76): this file's own header names every forbidden
    // seam. If codeOnly regressed, the first test would fail on the comment
    // rather than on the code, and the fix would be to delete the comment.
    expect(codeOnly('// useGraphAccess is forbidden here')).not.toContain('useGraphAccess')
    expect(codeOnly("const s = 'runSpec'")).not.toContain('runSpec')
    expect(codeOnly('const x = useGraphAccess()')).toContain('useGraphAccess')
  })
})
