// The 7 hub glyphs from UI-WIP/icons.md (O22), replicated as inline SVG so the
// set is reusable, recolorable, and crisp at any size. Conventions carried from
// icons.md: 120×120 viewBox, ~2.2px stroke. Palette is TOKEN-ONLY (no hard-coded
// hex — the O8 token sheet themes them for free):
//
//   icons.md token      →  tokens.css
//   --red-0 / --red-1   →  --red / --red-soft   (brand sphere; red = brand core only)
//   --teal              →  --teal               (healthy / left-column accent)
//   --amber             →  --yellow             (warning / right-column accent)
//   --panel-border      →  --edge               (structure lines, frames)
//
// Accent layers carry className="glyph-accent" and paint with currentColor,
// with the accent token bound via `color` — so the icons.md feGaussianBlur glow
// is realised as `drop-shadow(currentColor)` applied ONLY under `.dark`
// (site-plan §2: light mode gets the solid-outline equivalent, no glow) — see
// index.css. Structure layers (var(--edge)/var(--faint)) never glow.
//
// The 7-slot hub composition (Infrastructure is deliberately reused for BOTH
// core-infrastructure nodes, per icons.md "Glyphs (7)"):
//   TowerAuto · Infrastructure · HomeLending · [BrandMark core] ·
//   DataLineage · CreditCards · Infrastructure

type GlyphProps = { size?: number; className?: string; title?: string }

function svgProps({ size = 42, className, title }: GlyphProps) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 120 120',
    className,
    role: title ? ('img' as const) : undefined,
    'aria-hidden': title ? undefined : true,
  }
}

const stroke = { fill: 'none', strokeWidth: 2.2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

/** Accent-layer group: currentColor stroke + the accent token bound as `color`,
 *  so the dark-mode glow (drop-shadow currentColor) matches the accent hue. */
function accent(token: string) {
  return { className: 'glyph-accent', stroke: 'currentColor', style: { color: `var(${token})` } }
}

/** 1. Brand mark — red sphere + revolving translucent rectangles (header lockup / hub core). */
export function BrandMarkGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      {/* orbit track */}
      <ellipse cx="60" cy="60" rx="46" ry="20" {...stroke} stroke="var(--faint)" strokeDasharray="5 7" transform="rotate(-18 60 60)" />
      {/* core sphere: flat token fill + token highlight (no gradient → no hex stops) */}
      <circle cx="60" cy="60" r="21" fill="var(--red)" />
      <ellipse cx="53" cy="52" rx="8" ry="5.5" fill="var(--red-soft)" opacity="0.55" />
      {/* revolving translucent panels — each its own accent color */}
      <g {...accent('--teal')} fill="currentColor" strokeWidth="2.2">
        <rect x="8" y="48" width="15" height="21" rx="2.5" fillOpacity="0.28" transform="rotate(-14 15.5 58.5)" />
      </g>
      <g {...accent('--blue-br')} fill="currentColor" strokeWidth="2.2">
        <rect x="96" y="52" width="15" height="21" rx="2.5" fillOpacity="0.28" transform="rotate(12 103.5 62.5)" />
      </g>
      <g {...accent('--yellow')} fill="currentColor" strokeWidth="2.2">
        <rect x="52" y="8" width="16" height="12" rx="2.5" fillOpacity="0.28" transform="rotate(-6 60 14)" />
      </g>
    </svg>
  )
}

/** 2. Tower Auto — city block + car badge (Auto Finance tower node). */
export function TowerAutoGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      {/* city block with window grid */}
      <g {...stroke} stroke="var(--edge)">
        <rect x="22" y="18" width="34" height="62" rx="3" />
        <rect x="56" y="34" width="26" height="46" rx="3" />
      </g>
      <g stroke="var(--faint)" strokeWidth="2.2" strokeLinecap="round">
        <path d="M30 30h6M42 30h6M30 42h6M42 42h6M30 54h6M42 54h6" />
        <path d="M63 44h5M72 44h5M63 56h5M72 56h5" />
      </g>
      {/* car badge */}
      <g {...stroke} {...accent('--teal')}>
        <path d="M52 96 55 88q1.5-3.5 5-3.5h20q3.5 0 5 3.5l3 8M49 96h42v7h-5M56 103h-7" />
        <circle cx="60" cy="102" r="4" />
        <circle cx="82" cy="102" r="4" />
      </g>
    </svg>
  )
}

/** 3. Infrastructure — server rack (3 rows, status LEDs) + orchestration gear.
 *  Reused for BOTH core-infrastructure hub nodes. */
export function InfrastructureGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      {/* rack, 3 rows */}
      <g {...stroke} stroke="var(--edge)">
        <rect x="24" y="22" width="52" height="72" rx="4" />
        <path d="M24 46h52M24 70h52" />
      </g>
      {/* per-row status LEDs (healthy, healthy, warning) + vents */}
      <g className="glyph-accent" fill="currentColor" style={{ color: 'var(--green)' }}>
        <circle cx="34" cy="34" r="3" />
        <circle cx="34" cy="58" r="3" />
      </g>
      <g className="glyph-accent" fill="currentColor" style={{ color: 'var(--yellow)' }}>
        <circle cx="34" cy="82" r="3" />
      </g>
      <g stroke="var(--faint)" strokeWidth="2.2" strokeLinecap="round">
        <path d="M46 34h20M46 58h20M46 82h20" />
      </g>
      {/* orchestration gear */}
      <g {...stroke} {...accent('--teal')}>
        <circle cx="92" cy="84" r="10" />
        <circle cx="92" cy="84" r="3.5" />
        <path d="M92 70v-5M92 98v5M78 84h-5M106 84h5M82 74l-3.5-3.5M102 94l3.5 3.5M102 74l3.5-3.5M82 94l-3.5 3.5" />
      </g>
    </svg>
  )
}

/** 4. Home Lending — house with roof, door and window (Mortgage tower node). */
export function HomeLendingGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      <g {...stroke} {...accent('--teal')}>
        <path d="M60 20 104 56h-12v42H28V56H16Z" />
      </g>
      <g {...stroke} stroke="var(--faint)">
        <path d="M52 98V74h16v24" />
        <rect x="66" y="60" width="14" height="11" rx="1.5" />
      </g>
    </svg>
  )
}

/** 5. Data Lineage — two data frames joined by directional elbow connectors (pipeline node). */
export function DataLineageGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      {/* two data frames with header + rows */}
      <g {...stroke} stroke="var(--edge)">
        <rect x="12" y="18" width="42" height="34" rx="3" />
        <rect x="66" y="68" width="42" height="34" rx="3" />
        <path d="M12 28h42M66 78h42" />
      </g>
      <g stroke="var(--faint)" strokeWidth="2.2" strokeLinecap="round">
        <path d="M18 36h20M18 44h28M72 86h20M72 94h28" />
      </g>
      {/* directional elbow connectors */}
      <g {...stroke} {...accent('--yellow')}>
        <path d="M33 52v22a6 6 0 0 0 6 6h20" />
        <path d="M54 74l6 6-6 6" />
        <path d="M54 35h34a6 6 0 0 1 6 6v20" />
        <path d="M88 55l6 6 6-6" />
      </g>
    </svg>
  )
}

/** 6. Credit Cards — three fanned cards, each a different accent stripe (Cards tower node). */
export function CreditCardsGlyph(props: GlyphProps) {
  return (
    <svg {...svgProps(props)}>
      {props.title && <title>{props.title}</title>}
      <g transform="rotate(-10 60 66)">
        <rect x="22" y="30" width="62" height="40" rx="5" {...stroke} stroke="var(--edge)" />
        <path d="M22 42h62" className="glyph-accent" stroke="currentColor" strokeWidth="4" style={{ color: 'var(--blue-br)' }} />
      </g>
      <g transform="rotate(-2 60 66)">
        <rect x="28" y="44" width="62" height="40" rx="5" {...stroke} stroke="var(--edge)" />
        <path d="M28 56h62" className="glyph-accent" stroke="currentColor" strokeWidth="4" style={{ color: 'var(--yellow)' }} />
      </g>
      <g transform="rotate(6 60 66)">
        <rect x="34" y="58" width="62" height="40" rx="5" {...stroke} stroke="var(--edge)" />
        <path d="M34 70h62" className="glyph-accent" stroke="currentColor" strokeWidth="4" style={{ color: 'var(--teal)' }} />
        <path d="M42 88h16" stroke="var(--faint)" strokeWidth="2.2" strokeLinecap="round" />
      </g>
    </svg>
  )
}

/** The hub composition, spoke order as drawn in the landing mock — 7 slots,
 *  Infrastructure appearing twice by design (icons.md). */
export const HUB_GLYPHS = [
  { key: 'tower-auto', label: 'Tower Auto', Glyph: TowerAutoGlyph },
  { key: 'infrastructure-left', label: 'Core Infrastructure', Glyph: InfrastructureGlyph },
  { key: 'home-lending', label: 'Home Lending', Glyph: HomeLendingGlyph },
  { key: 'brand-core', label: 'DryDocs', Glyph: BrandMarkGlyph },
  { key: 'data-lineage', label: 'Data Lineage', Glyph: DataLineageGlyph },
  { key: 'credit-cards', label: 'Credit Cards', Glyph: CreditCardsGlyph },
  { key: 'infrastructure-right', label: 'Core Infrastructure', Glyph: InfrastructureGlyph },
] as const
