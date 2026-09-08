import { conceptInText, provenanceNote } from '../../lib/uiConcepts'

// WEB18 — a module tagline, with a provenance note on the one word that needs
// one.
//
// WHY IT IS ITS OWN COMPONENT rather than three lines inside ModuleTemplate:
// what it decides is not layout. It decides whether a term the console INVENTED
// is presented next to "backs onto drydocs" with nothing separating the two —
// the exact adjacency that led a model to answer a Tower question out of
// :TOMRole on 2026-08-20. That decision reads better with its own name and its
// own test than folded into a header's paragraph.
//
// IT SAYS NOTHING WHEN NOTHING IS DECLARED. A tagline naming no declared
// concept renders as plain text, identical to before — this is additive on one
// header today (Explorer), and a component that decorated every tagline would
// be teaching people to ignore the decoration.

export function TaglineWithProvenance({ tagline }: { tagline: string }) {
  const concept = conceptInText(tagline)
  if (!concept) return <>{tagline}</>

  const note = provenanceNote(concept)
  const index = tagline.toLowerCase().indexOf(concept.term.toLowerCase())
  // The term as the TAGLINE spells it, not as the declaration does: the header
  // is what a person is reading, and re-casing their word to match a yaml file
  // would be a second, quieter kind of drift.
  const [before, match, after] =
    index < 0
      ? ['', '', '']
      : [
          tagline.slice(0, index),
          tagline.slice(index, index + concept.term.length),
          tagline.slice(index + concept.term.length),
        ]

  if (!match) return <>{tagline}</>
  return (
    <>
      {before}
      <abbr
        title={note}
        aria-label={note}
        data-ui-concept={concept.term}
        className="cursor-help underline decoration-dotted decoration-from-font underline-offset-2"
      >
        {match}
      </abbr>
      {after}
    </>
  )
}
