// Decorative hero art for the Overview landing (site-plan §2/§3, wf-landing-01
// theme pass): the mockup's signature visual — a red core sphere wrapped in
// blue/green/yellow gradient "petal" shell segments, faint concentric "web"
// rings, and a background node network — reproduced from
// UI-WIP/drydocs-landing-dark.html (`heroNet()` + the hero-art `<svg>` markup;
// same 640×480 coordinate space as OverviewRoute's radial hub, so this layer
// sits directly behind the module spokes with no repositioning).
//
// Dark mode carries the mock's gradients + soft highlight, exactly as
// designed. Light mode (site-plan §2 "no glow" rule) swaps every gradient/url
// fill for a flat token color with a plain 2px outline — gated entirely by
// Tailwind's `dark:` variant (two parallel `<g>` groups per element), so nothing
// here branches in JS on the current theme.
//
// A slow opacity pulse on the dark network is the "subtle CSS animation" the
// theme pass calls for; the global `prefers-reduced-motion` rule in index.css
// already neutralizes all animation/transition, so no extra guard is needed
// here.

const NET_NODES: readonly [x: number, y: number, token: 'blue' | 'green' | 'teal' | 'yellow', r: number][] = [
  [320, 42, 'blue', 9], [452, 66, 'green', 7], [540, 120, 'blue', 8], [598, 200, 'teal', 13],
  [590, 300, 'green', 9], [560, 382, 'yellow', 12], [470, 430, 'teal', 7], [360, 446, 'blue', 8],
  [248, 432, 'green', 7], [152, 392, 'blue', 10], [86, 318, 'teal', 8], [62, 228, 'blue', 12],
  [92, 140, 'green', 8], [168, 78, 'teal', 7], [236, 50, 'blue', 6],
  [500, 180, 'yellow', 6], [150, 250, 'green', 6], [490, 330, 'green', 6], [190, 160, 'blue', 5],
]

const NET_LINKS: readonly [a: number, b: number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12],
  [12, 13], [13, 14], [14, 0], [2, 15], [15, 3], [11, 16], [16, 10], [5, 17], [17, 4], [12, 18], [18, 16],
  [1, 15], [8, 17],
]

const PETALS = [
  { d: 'M -18 -118 A 118 118 0 0 1 82 -86 L 58 -60 A 84 84 0 0 0 -12 -83 Z', token: 'yellow' },
  { d: 'M 96 -72 A 120 120 0 0 1 116 28 L 82 20 A 86 86 0 0 0 68 -50 Z', token: 'blue' },
  { d: 'M 108 44 A 120 120 0 0 1 30 116 L 22 82 A 86 86 0 0 0 76 32 Z', token: 'green' },
  { d: 'M 8 120 A 120 120 0 0 1 -90 78 L -64 55 A 86 86 0 0 0 5 85 Z', token: 'yellow' },
  { d: 'M -102 62 A 120 120 0 0 1 -117 -32 L -83 -22 A 86 86 0 0 0 -73 44 Z', token: 'blue' },
  { d: 'M -112 -50 A 120 120 0 0 1 -38 -114 L -28 -81 A 86 86 0 0 0 -80 -36 Z', token: 'green' },
] as const

export default function HeroArt() {
  return (
    <svg viewBox="0 0 640 480" className="absolute inset-0 h-full w-full" aria-hidden="true">
      <defs>
        <radialGradient id="heroCore" cx="35%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#F0666F" />
          <stop offset="50%" stopColor="var(--red)" />
          <stop offset="100%" stopColor="#5E070E" />
        </radialGradient>
        <linearGradient id="heroPetal-blue" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--blue-br)" />
          <stop offset="100%" stopColor="#1D4B8F" />
        </linearGradient>
        <linearGradient id="heroPetal-green" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#4FC98A" />
          <stop offset="100%" stopColor="#1E6B42" />
        </linearGradient>
        <linearGradient id="heroPetal-yellow" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--yellow)" />
          <stop offset="100%" stopColor="#9C7F12" />
        </linearGradient>
        <radialGradient id="heroNode-blue" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#6FA6E8" /><stop offset="100%" stopColor="#173B6E" />
        </radialGradient>
        <radialGradient id="heroNode-green" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#65D49A" /><stop offset="100%" stopColor="#175537" />
        </radialGradient>
        <radialGradient id="heroNode-teal" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#57C9C9" /><stop offset="100%" stopColor="#134A4A" />
        </radialGradient>
        <radialGradient id="heroNode-yellow" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="var(--yellow)" /><stop offset="100%" stopColor="#6E5A0C" />
        </radialGradient>
      </defs>

      {/* faint concentric web rings — both themes, structure-only token color */}
      <g fill="none" stroke="var(--edge)" strokeWidth="1" opacity=".6">
        <ellipse cx="320" cy="240" rx="270" ry="200" />
        <ellipse cx="320" cy="240" rx="215" ry="152" transform="rotate(-12 320 240)" />
        <ellipse cx="320" cy="240" rx="165" ry="120" transform="rotate(9 320 240)" />
      </g>

      {/* background node network — edges */}
      <g className="dark:hidden" strokeWidth="1">
        {NET_LINKS.map(([a, b], i) => {
          const p = NET_NODES[a]
          const q = NET_NODES[b]
          return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke="var(--edge)" opacity=".55" />
        })}
      </g>
      <g className="hidden dark:block hero-net" strokeWidth="1.3">
        {NET_LINKS.map(([a, b], i) => {
          const p = NET_NODES[a]
          const q = NET_NODES[b]
          return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={`var(--${p[2] === 'teal' ? 'teal' : p[2]})`} opacity=".45" />
        })}
      </g>

      {/* background node network — nodes (radial gradient = the "glow") */}
      <g className="dark:hidden">
        {NET_NODES.map(([x, y, token, r], i) => (
          <circle key={i} cx={x} cy={y} r={r * 0.7} fill={`var(--${token})`} opacity=".55" />
        ))}
      </g>
      <g className="hidden dark:block hero-net">
        {NET_NODES.map(([x, y, token, r], i) => (
          <circle key={i} cx={x} cy={y} r={r} fill={`url(#heroNode-${token})`} />
        ))}
      </g>

      {/* shell petals + core */}
      <g transform="translate(320 240)">
        {/* light: flat fills, solid 2px outline, no gradient/highlight */}
        <g className="dark:hidden">
          {PETALS.map((p, i) => (
            <path key={i} d={p.d} fill={`var(--${p.token})`} stroke="var(--bg)" strokeWidth="2" />
          ))}
          <circle r="62" fill="var(--red)" stroke="var(--red-soft)" strokeWidth="2" />
        </g>
        {/* dark: gradient petals + gradient core + soft highlight */}
        <g className="hidden dark:block">
          {PETALS.map((p, i) => (
            <path key={i} d={p.d} fill={`url(#heroPetal-${p.token})`} stroke="var(--bg)" strokeWidth="2" />
          ))}
          <circle r="62" fill="url(#heroCore)" />
          <ellipse cx="-18" cy="-24" rx="22" ry="14" fill="#fff" opacity=".28" />
        </g>
      </g>
    </svg>
  )
}
