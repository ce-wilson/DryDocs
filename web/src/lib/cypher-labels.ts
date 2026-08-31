// Which labels and relationship types does a query NAME? (O84)
//
// WHY THIS IS NOT A CYPHER PARSER, and must not become one. It answers one
// question for one purpose: a FIRST-PARTY preset came back with zero rows, and
// the console needs to tell "the graph holds no matching data" apart from "this
// query names a label the database does not have". The second is the defect O84
// exists for — two first-party call sites drifted from a signed gate ruling, the
// unit suite stayed green, and the surface reported SUCCESS with an empty result.
//
// SCOPE FENCE, from O84 clause (d): first-party presets and agent defaults only.
// This is deliberately never run over user-typed Cypher — the bolt panel is a
// raw-Cypher bench and turning it into a validator nobody asked for would be a
// different product decision. The caller enforces that by only consulting this
// for a query it recognises as one of its own presets.
//
// A pattern match is the right shape precisely BECAUSE it is approximate: it
// over-reports nothing that matters (a name it fails to spot is simply not
// diagnosed) and it cannot reject a query, only annotate an already-empty
// result.

/** `(a:Label)`, `(:Label)`, and the `(a:A:B)` multi-label form. */
const LABEL = /\(\s*\w*\s*:\s*([A-Za-z_][\w]*(?:\s*:\s*[A-Za-z_][\w]*)*)\s*[){]/g

/** `[:REL]`, `[r:REL]`, and the `[:A|B]` alternation form. */
const REL = /\[\s*\w*\s*:\s*([A-Z_][A-Z0-9_]*(?:\s*\|\s*[A-Z_][A-Z0-9_]*)*)\s*[*\]]/g

function collect(query: string, pattern: RegExp, split: RegExp): string[] {
  const found = new Set<string>()
  // A fresh lastIndex per call: the module-level regexes carry /g state.
  pattern.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = pattern.exec(query)) !== null) {
    for (const part of m[1].split(split)) {
      const name = part.trim()
      if (name) found.add(name)
    }
  }
  return [...found]
}

/** Node labels the query names, in no particular order. */
export function labelsNamedIn(query: string): string[] {
  return collect(query, LABEL, /:/)
}

/** Relationship types the query names, in no particular order. */
export function relTypesNamedIn(query: string): string[] {
  return collect(query, REL, /\|/)
}
