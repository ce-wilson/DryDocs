import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { GATED_SURFACES, MODULES, PERSONA_SCOPED_PATHS } from './registry'
import { PERSONAS } from '../lib/auth'
import { SRC } from '../test/sourceScan'

// WEB15 (c) — web/README.md and the code do not drift again.
//
// The README was materially wrong in four places at once: it denied a `?as=`
// parameter that exists, said nine modules where the registry declares twelve,
// said every module is open to every signed-in persona while five carry
// `access: 'sme'`, and carried three SID-shaped persona names that auth.ts
// retired on 2026-08-28 for publish-boundary reasons.
//
// Point three is the one that makes this a guard rather than a proofread: a doc
// that UNDERSTATES the authorization surface is worse than no doc, and it is
// the doc a company-side reader reaches first.
//
// Every assertion below reads the IMPORTABLE OBJECT and looks for it in the
// prose (J37's direction of travel: the declaration is the source, the render
// is what must agree with it). Nothing here parses the README into a model.

const README = readFileSync(join(SRC, '..', 'README.md'), 'utf8')

describe('the README agrees with the module registry', () => {
  it('states the module count the registry declares', () => {
    expect(README).toContain(`${MODULES.length} module routes`)
    expect(README).toContain(`the ${MODULES.length} modules`)
  })

  it('names every module whose access is not "all", with its path and level', () => {
    // The four-way drift's worst branch: a module gated in code and described
    // as open in the doc.
    for (const m of MODULES.filter((x) => x.access && x.access !== 'all')) {
      expect(README, `${m.id} is gated and the README does not name its path`).toContain(m.path)
      const row = README.split('\n').find((ln) => ln.includes(`| \`${m.path}\` |`))
      expect(row, `${m.id} has no access row in the README`).toBeTruthy()
      expect(row).toContain(`\`${m.access}\``)
    }
  })

  it('claims no more gated modules than there are', () => {
    const gated = MODULES.filter((m) => m.access && m.access !== 'all').length
    expect(README).toContain(`${['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six'][gated]} of the twelve`)
  })

  it('names every gated non-module surface', () => {
    for (const s of GATED_SURFACES) expect(README).toContain(`\`${s.path}\``)
  })

  it('names the persona-scoped exception as an exception', () => {
    for (const p of PERSONA_SCOPED_PATHS) expect(README).toContain(`\`${p}\``)
    expect(README).toContain('canAccessIntake')
  })
})

describe('the README agrees with the persona table', () => {
  it('lists every persona by its current id and role', () => {
    for (const p of PERSONAS) {
      const row = README.split('\n').find((ln) => ln.startsWith(`| \`${p.id}\` |`))
      expect(row, `persona ${p.id} has no README row`).toBeTruthy()
      expect(row).toContain(`| ${p.role} |`)
    }
  })

  it('says how many personas there are, and it is right', () => {
    expect(README).toContain(`The ${['', 'one', 'two', 'three', 'four', 'five', 'six'][PERSONAS.length]} synthetic personas`)
  })

  it('carries no retired SID-shaped display name', () => {
    // auth.ts retired these on 2026-08-28 for publish-boundary reasons and the
    // README carried them forward for a week. The pattern, not the three
    // literals: an initial, a dot, a space, a capitalised surname inside a
    // table cell — so a fourth one cannot be added either.
    const retired = README.split('\n').filter((ln) => /^\|\s*`\w+`\s*\([A-Z]\.\s+[A-Z]\w+\)/.test(ln))
    expect(retired).toEqual([])
  })
})

describe('the README does not deny what the code does', () => {
  it('describes ?as= as existing and DEV-only, because it does', () => {
    expect(README).toContain('VITE_DEV_CONSOLE_SECRET')
    expect(README).not.toMatch(/there is no `\?as=`/)
  })

  it('does not claim every module is open', () => {
    expect(README).not.toMatch(/All \d+ site-plan modules are open to every signed-in persona/)
  })
})
