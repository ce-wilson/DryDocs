// The three glyphs the Z5 dropdown names: a job, a person/team, and a building for
// a data centre or office location.
//
// Inline SVG rather than a font or sprite sheet, for the same reason the map itself
// is generated: the console must work offline (Z5 — "no external tile or font
// fetch"). They are drawn on a 16x16 grid and inherit `currentColor`, so a caller
// controls colour by CSS and the icon works in both themes without a second asset.
// Same idiom as HubGlyphs (O22).

export type GlyphKind = 'server' | 'job' | 'team' | 'building'

interface GlyphProps {
  kind: GlyphKind
  size?: number
  className?: string
  title?: string
}

/** Paths only — the wrapper below owns sizing, colour and accessibility. */
function paths(kind: GlyphKind) {
  switch (kind) {
    case 'job':
      // A run: a play triangle inside a rounded square. Reads as "a thing that
      // executes" rather than "a document", which is the distinction that matters
      // next to a server in the same legend.
      return (
        <>
          <rect x="1.5" y="1.5" width="13" height="13" rx="3" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M6.4 5.2 L11 8 L6.4 10.8 Z" fill="currentColor" />
        </>
      )
    case 'team':
      // Two overlapping figures — a team, not one person. The map never claims to
      // know where an individual is (see map.team-locations.v1: reach, not
      // residence), so the plural glyph is the honest one.
      return (
        <>
          <circle cx="6" cy="5.4" r="2.4" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M1.9 13.6c0-2.4 1.9-4 4.1-4s4.1 1.6 4.1 4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          <circle cx="11.4" cy="6.2" r="1.9" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.75" />
          <path d="M10 10.2c2 0 4.1 1.1 4.1 3.4" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.75" />
        </>
      )
    case 'building':
      // A data centre or office: a block with windows and a door.
      return (
        <>
          <path d="M2.5 14V3.2a1 1 0 0 1 1-1h6.2a1 1 0 0 1 1 1V14" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
          <path d="M10.7 6.4h2.8a1 1 0 0 1 1 1V14" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
          <path d="M1 14h14" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          <rect x="4.6" y="4.8" width="1.8" height="1.8" fill="currentColor" />
          <rect x="7.4" y="4.8" width="1.8" height="1.8" fill="currentColor" />
          <rect x="4.6" y="8" width="1.8" height="1.8" fill="currentColor" />
          <path d="M7.4 14v-3.1h1.8V14" fill="none" stroke="currentColor" strokeWidth="1.2" />
        </>
      )
    case 'server':
    default:
      // Stacked rack units with status lamps — the inventory spine.
      return (
        <>
          <rect x="2" y="2.4" width="12" height="4.6" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <rect x="2" y="9" width="12" height="4.6" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="4.6" cy="4.7" r="0.85" fill="currentColor" />
          <circle cx="4.6" cy="11.3" r="0.85" fill="currentColor" />
          <path d="M7.2 4.7h4.4M7.2 11.3h4.4" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" opacity="0.7" />
        </>
      )
  }
}

export function MapGlyph({ kind, size = 16, className, title }: GlyphProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      className={className}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      focusable="false"
    >
      {title ? <title>{title}</title> : null}
      {paths(kind)}
    </svg>
  )
}
