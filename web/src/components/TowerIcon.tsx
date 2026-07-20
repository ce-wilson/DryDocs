import type { TowerKey } from '../data/towers'

// The four tower glyphs from the mockup, JSX-ified (house / car / card / stack).
export default function TowerIcon({ tower }: { tower: TowerKey }) {
  switch (tower) {
    case 'home':
      return (
        <svg width="42" height="42" viewBox="0 0 42 42" aria-hidden="true">
          <path d="M21 7 L36 20 H31 V34 H24 V25 H18 V34 H11 V20 H6 Z" fill="none" stroke="#4D8BE0" strokeWidth="2.4" strokeLinejoin="round" />
        </svg>
      )
    case 'auto':
      return (
        <svg width="46" height="42" viewBox="0 0 46 42" aria-hidden="true">
          <path d="M9 25 L12 15 Q13 12 16 12 H30 Q33 12 34 15 L37 25 M7 25 H39 V31 H35 M11 31 H7 Z" fill="none" stroke="#2AB3A6" strokeWidth="2.4" strokeLinejoin="round" />
          <circle cx="14" cy="30" r="3.4" fill="none" stroke="#2AB3A6" strokeWidth="2.4" />
          <circle cx="32" cy="30" r="3.4" fill="none" stroke="#2AB3A6" strokeWidth="2.4" />
          <line x1="15" y1="19" x2="31" y2="19" stroke="#2AB3A6" strokeWidth="2" />
        </svg>
      )
    case 'cards':
      return (
        <svg width="46" height="42" viewBox="0 0 46 42" aria-hidden="true">
          <rect x="7" y="11" width="32" height="21" rx="3" fill="none" stroke="#3AAE6B" strokeWidth="2.4" />
          <line x1="7" y1="18" x2="39" y2="18" stroke="#3AAE6B" strokeWidth="3.4" />
          <line x1="12" y1="26" x2="22" y2="26" stroke="#3AAE6B" strokeWidth="2.2" />
        </svg>
      )
    case 'shared':
      return (
        <svg width="46" height="42" viewBox="0 0 46 42" aria-hidden="true">
          <g fill="none" stroke="#D9B831" strokeWidth="2.4" strokeLinejoin="round">
            <path d="M23 8 L37 14 L23 20 L9 14 Z" />
            <path d="M9 21 L23 27 L37 21" />
            <path d="M9 28 L23 34 L37 28" />
          </g>
        </svg>
      )
  }
}
