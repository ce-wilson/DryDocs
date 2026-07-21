import { BrandMarkGlyph } from './icons/HubGlyphs'

// The brand mark: red sphere + revolving translucent rectangles, from the O22
// hub glyph set (red = brand core only, site-plan §2 brand rule). Token-driven —
// the old two-ring version hard-coded hex and predated icons.md.
export default function BrandMark({ size = 26 }: { size?: number }) {
  return <BrandMarkGlyph size={size} />
}
