import { readFileSync, readdirSync } from 'node:fs'
import { join, relative } from 'node:path'

// The console's source-scan helpers, shared by every guard that asserts a
// pattern is absent from web/src (WEB3's role predicates, WEB12's transport
// preambles, and WEB1's demo-module imports).
//
// EXTRACTED AT WEB12, and the reason is the review's own headline finding: "a
// governing abstraction exists, is correct, and the call sites route around
// it", counted eight times. Three guards each carrying their own copy of a
// comment stripper would have been the ninth.
//
// It is a `.ts` deliberately: config/taxonomy/ui-components.yaml scans `.tsx`,
// so a test helper here does not enter the component ledger.

/** The repo's `web/src` directory, resolved from this module. */
export const SRC = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')

// One left-to-right alternation, matched ONCE per token. An earlier draft
// stripped comments first and strings second, which ate `//localhost:8001'` out
// of a string literal and left a dangling quote that mis-parsed the rest of the
// line — a stripper that corrupts the code it is about to scan produces silent
// false negatives, which is the worst failure mode a guard can have.
const TOKENS = /\/\*[\s\S]*?\*\/|\/\/[^\n]*|`(?:[^`\\]|\\.)*`|'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*"/g

/** Source with comments and string/template literals neutralised.
 *
 * J66, and not a formality: these guards forbid patterns whose EXPLANATIONS
 * quote them verbatim. A scan over raw source fails on its own comment and
 * teaches the next person to delete the comment — which, in a codebase whose
 * comments carry its rulings, costs more than the guard is worth. Literals go
 * too, because a URL or a message that contains the pattern is not a use of it.
 *
 * Quotes are preserved (a literal becomes two quote characters, not nothing) so
 * a pattern that ends at the OPENING quote of a literal still matches real code.
 *
 * KNOWN LIMITATION, stated rather than discovered: it does not understand regex
 * literals, so a regex containing a quote or a backtick — like TOKENS above —
 * is mis-tokenised. That is survivable because it affects exactly one file in
 * web/src (this one) and no guard's pattern occurs in it. A guard that needed
 * to scan regex-heavy source would need a real tokenizer, not a bigger regex.
 */
export function codeOnly(source: string): string {
  return source.replace(TOKENS, (tok) => {
    if (tok.startsWith('/*') || tok.startsWith('//')) return ' '
    return tok[0] + tok[0]
  })
}

/** Every hand-written TypeScript source under `dir`, tests excluded.
 *
 * Tests are excluded because a guard's own fixtures name the pattern it
 * forbids; including them would make every guard fail on itself. Generated
 * sources are excluded for the opposite reason — nobody edits them, so holding
 * them to a hand-written convention only produces noise. */
export function tsSources(dir: string = SRC, out: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name !== 'generated') tsSources(full, out)
    } else if (/\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name)) {
      out.push(full)
    }
  }
  return out
}

/** Repo-relative, forward-slashed paths of the sources whose CODE matches. */
export function filesMatching(pattern: RegExp, files: string[] = tsSources()): string[] {
  return files
    .filter((f) => pattern.test(codeOnly(readFileSync(f, 'utf8'))))
    .map((f) => relative(SRC, f).replace(/\\/g, '/'))
}

export { readFileSync, relative }
