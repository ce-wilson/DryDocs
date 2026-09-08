import generated from '../generated/ui-concepts.json'

// WEB18 — the console half of R22's provenance fix.
//
// THE DEFECT. `ModuleTemplate` renders every module header as "tagline · backs
// onto <backend>". For Explorer that reads "Tower / app drill-down graph · backs
// onto drydocs". `backsOnto: 'drydocs'` is CORRECT — the tabs do read the graph
// — but the word Tower beside it invites exactly the inference R22 exists to
// prevent: on 2026-08-20 "how many towers" fell through to text2cypher and the
// model proxied a console term onto the real label :TOMRole, crossing from UI
// taxonomy into the TOM ontology without saying so. R22 fixed /ask. The header
// never got the fix, and a header is where a person forms the assumption the
// agent later has to correct.
//
// THE SENTENCE IS COMPOSED HERE AND DECLARED IN config/taxonomy/ui-concepts.yaml.
// Every fact below comes from the generated artifact; none is typed into this
// file. That split is the point rather than tidiness — a hand-written "Tower is
// a console concept, there are four" is a SECOND definition, and a second
// definition drifting from the guarded one is the whole class of defect WEB18
// closes. What is composed here is only the WORDING.
//
// THE LINE IT DOES NOT CROSS (clause b). It may say where a term comes from and
// that the graph does not back it. It may NOT say what the term maps to. There
// is no branch below that renders a binding: `graph_binding` gates whether the
// not-from-the-graph clause appears at all, and any value other than `none`
// makes this surface say LESS, not more — because a confirmed binding is a HITL
// gate ruling and the sentence for it belongs to whoever writes that ruling.

export interface UiConcept {
  term: string
  aliases: string[]
  source: string
  source_kind: string
  cardinality: number
  members: string[]
  graph_binding: string
}

export const UI_CONCEPTS: UiConcept[] = generated.concepts

/** The concept a header term names, by term or alias, case-insensitively.
 *  `null` for a word nothing declares — which is most words, and the reason
 *  the caller renders plain text rather than an empty tooltip. */
export function conceptFor(term: string): UiConcept | null {
  const wanted = term.trim().toLowerCase()
  if (!wanted) return null
  return (
    UI_CONCEPTS.find(
      (c) => c.term.toLowerCase() === wanted || c.aliases.some((a) => a.toLowerCase() === wanted),
    ) ?? null
  )
}

/** The provenance note, composed from the declaration.
 *
 *  Reads as one sentence about SOURCE and one about SCOPE, then the aliases —
 *  the cheap win clause (d) asks for, and the thing that actually helps someone
 *  who typed "CTO towers" and got nothing. A real acronym link waits on the
 *  term ledger; this is the part that needs no new surface. */
export function provenanceNote(concept: UiConcept): string {
  const parts = [`${concept.term} is defined in the console (${concept.source})`]
  // Only `none` licenses the not-from-the-graph clause. Anything else is a gate
  // ruling this surface has not read, so it says nothing rather than guessing.
  if (concept.graph_binding === 'none') {
    parts.push('not read from the graph')
  }
  parts.push(`${concept.cardinality} of them: ${concept.members.join(', ')}`)
  if (concept.aliases.length) {
    parts.push(`also written ${concept.aliases.join(', ')}`)
  }
  return parts.join(' · ')
}

/** The first declared concept named anywhere in a header tagline, or null.
 *  Word-boundary matched so "Towering" never matches "Tower" — a header is
 *  read at a glance and a wrong provenance note is worse than none. */
export function conceptInText(text: string): UiConcept | null {
  for (const concept of UI_CONCEPTS) {
    for (const name of [concept.term, ...concept.aliases]) {
      const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      if (new RegExp(`\\b${escaped}\\b`, 'i').test(text)) return concept
    }
  }
  return null
}
