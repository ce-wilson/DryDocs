import type { TowerKey } from '../data/towers'
import { CreditCardsGlyph, HomeLendingGlyph, InfrastructureGlyph, TowerAutoGlyph } from './icons/HubGlyphs'

// Tower glyphs now come from the shared O22 hub set (icons/HubGlyphs.tsx) —
// token-driven, no hard-coded hex. 'shared' (Shared Services) renders the
// Infrastructure glyph: icons.md reuses it for the core-infrastructure nodes,
// which is what the shared tower represents in the demo data.
export default function TowerIcon({ tower }: { tower: TowerKey }) {
  switch (tower) {
    case 'home':
      return <HomeLendingGlyph size={42} />
    case 'auto':
      return <TowerAutoGlyph size={44} />
    case 'cards':
      return <CreditCardsGlyph size={44} />
    case 'shared':
      return <InfrastructureGlyph size={44} />
  }
}
