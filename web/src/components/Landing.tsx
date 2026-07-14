import type { Persona } from '../lib/auth'
import { canDrill, hashForTower } from '../lib/views'
import { TOWERS, TOWER_KEYS, type TowerKey } from '../data/towers'
import TowerIcon from './TowerIcon'
import TowerDrill from './TowerDrill'

// The Overview page: hero (core-and-petals + node network), feature strip,
// Explore by Tower cards. With a tower in the route it renders the drill-down
// instead. Ported from the UI-WIP dark-landing mockup (dd270b2).
export default function Landing({ tower, persona }: { tower?: string; persona: Persona }) {
  if (tower) return <TowerDrill towerKey={tower as TowerKey} persona={persona} />
  const heroTarget = persona.role === 'admin' ? 'home' : (persona.towerKey ?? 'home')
  return (
    <>
      <section className="hero wrap">
        <div>
          <h1>DryDocs</h1>
          <h2>A Don't Repeat Yourself Knowledge Graph</h2>
          <p className="desc">
            Visualize and understand your DevOps landscape. Connect pipelines, jobs,
            systems, and data across towers, products, and teams.
          </p>
          <div className="hero-btns">
            <a className="btn-primary" href={hashForTower(heroTarget)}>Explore the Graph</a>
            <a className="btn-ghost" href="#/landing">▶&ensp;Watch Demo</a>
          </div>
        </div>
        <HeroArt />
      </section>

      <section className="features">
        <div className="feat-in">
          <Feature title="Knowledge Graph" text="Connect everything, see the big picture.">
            <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
              <g stroke="#4D8BE0" strokeWidth="2" fill="none">
                <line x1="9" y1="10" x2="24" y2="8" /><line x1="9" y1="10" x2="14" y2="25" />
                <line x1="24" y1="8" x2="14" y2="25" /><line x1="24" y1="8" x2="28" y2="22" />
              </g>
              <circle cx="9" cy="10" r="4.5" fill="#2E6BC4" /><circle cx="24" cy="8" r="3.5" fill="#4D8BE0" />
              <circle cx="14" cy="25" r="4" fill="#2E6BC4" /><circle cx="28" cy="22" r="3" fill="#4D8BE0" />
            </svg>
          </Feature>
          <Feature title="Pipeline & Job Lineage" text="Trace every step, end to end.">
            <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
              <g stroke="#3AAE6B" strokeWidth="2.2" fill="none" strokeLinecap="round">
                <path d="M8 12 a5 5 0 1 1 5 5" /><path d="M26 22 a5 5 0 1 1 -5 -5" />
                <line x1="13" y1="17" x2="21" y2="17" /><path d="M18.5 14.5 L21 17 L18.5 19.5" />
              </g>
            </svg>
          </Feature>
          <Feature title="Environment Mapping" text="Understand where things run.">
            <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
              <g stroke="#3AAE6B" strokeWidth="2" fill="none">
                <rect x="7" y="7" width="20" height="5.5" rx="1.5" /><rect x="7" y="15" width="20" height="5.5" rx="1.5" />
                <rect x="7" y="23" width="20" height="5.5" rx="1.5" />
              </g>
              <circle cx="11" cy="9.8" r="1.3" fill="#3AAE6B" /><circle cx="11" cy="17.8" r="1.3" fill="#3AAE6B" />
              <circle cx="11" cy="25.8" r="1.3" fill="#3AAE6B" />
            </svg>
          </Feature>
          <Feature title="Team & Access" text="Built for collaboration, designed for scale.">
            <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
              <path d="M17 5 L28 9 V17 C28 24 23 28.5 17 30 C11 28.5 6 24 6 17 V9 Z" fill="none" stroke="#D9B831" strokeWidth="2.2" />
              <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" fill="#D9B831" />
            </svg>
          </Feature>
        </div>
      </section>

      <section className="explore wrap">
        <h2>Explore by Tower</h2>
        <div className="towers">
          {TOWER_KEYS.map((key) => {
            const t = TOWERS[key]
            const allowed = canDrill(key, persona)
            return (
              <a
                key={key}
                className={allowed ? 'tower' : 'tower tower-locked'}
                href={allowed ? hashForTower(key) : undefined}
                aria-label={allowed ? `Open ${t.title} drill-down` : `${t.title} — outside this persona's access`}
                title={allowed ? undefined : 'outside this persona’s ServiceNow-derived access (mock)'}
              >
                <div className="icon"><TowerIcon tower={key} /></div>
                <h3>{t.title}</h3>
                <div className="stats">
                  {t.stats.map(([n, unit]) => <span key={unit}><b>{n}</b> {unit}</span>)}
                </div>
              </a>
            )
          })}
        </div>
      </section>
      <div className="foot wrap">
        All identifiers, row values and metrics on this page are synthesized / anonymized examples · © 2026 DryDocs
      </div>
    </>
  )
}

function Feature({ title, text, children }: { title: string; text: string; children: React.ReactNode }) {
  return (
    <div className="feat">
      {children}
      <div><h3>{title}</h3><p>{text}</p></div>
    </div>
  )
}

// Hero illustration: red core, colored shell petals, surrounding node network.
// Node/edge coordinates ported from the mockup's heroNet().
const HERO_PTS: readonly (readonly [number, number, string, number])[] = [
  [320, 42, 'nBlue', 9], [452, 66, 'nGreen', 7], [540, 120, 'nBlue', 8], [598, 200, 'nTeal', 13],
  [590, 300, 'nGreen', 9], [560, 382, 'nYellow', 12], [470, 430, 'nTeal', 7], [360, 446, 'nBlue', 8],
  [248, 432, 'nGreen', 7], [152, 392, 'nBlue', 10], [86, 318, 'nTeal', 8], [62, 228, 'nBlue', 12],
  [92, 140, 'nGreen', 8], [168, 78, 'nTeal', 7], [236, 50, 'nBlue', 6],
  [500, 180, 'nYellow', 6], [150, 250, 'nGreen', 6], [490, 330, 'nGreen', 6], [190, 160, 'nBlue', 5],
]
const HERO_LINKS: readonly (readonly [number, number])[] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12],
  [12, 13], [13, 14], [14, 0], [2, 15], [15, 3], [11, 16], [16, 10], [5, 17], [17, 4], [12, 18], [18, 16],
  [1, 15], [8, 17],
]
const HERO_EDGE_COLOR: Record<string, string> = {
  nBlue: '#2E6BC4', nGreen: '#3AAE6B', nTeal: '#2AB3A6', nYellow: '#D9B831',
}

function HeroArt() {
  return (
    <svg
      className="hero-art" viewBox="0 0 640 480" xmlns="http://www.w3.org/2000/svg" role="img"
      aria-label="A red core sphere wrapped in blue, green and yellow shell segments, surrounded by a network of connected nodes"
    >
      <defs>
        <radialGradient id="core" cx="35%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#F0666F" /><stop offset="50%" stopColor="#C8202E" /><stop offset="100%" stopColor="#5E070E" />
        </radialGradient>
        <linearGradient id="pBlue" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#4D8BE0" /><stop offset="100%" stopColor="#1D4B8F" /></linearGradient>
        <linearGradient id="pGreen" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#4FC98A" /><stop offset="100%" stopColor="#1E6B42" /></linearGradient>
        <linearGradient id="pYellow" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#EFD35C" /><stop offset="100%" stopColor="#9C7F12" /></linearGradient>
        <radialGradient id="nBlue" cx="35%" cy="30%" r="75%"><stop offset="0%" stopColor="#6FA6E8" /><stop offset="100%" stopColor="#173B6E" /></radialGradient>
        <radialGradient id="nGreen" cx="35%" cy="30%" r="75%"><stop offset="0%" stopColor="#65D49A" /><stop offset="100%" stopColor="#175537" /></radialGradient>
        <radialGradient id="nTeal" cx="35%" cy="30%" r="75%"><stop offset="0%" stopColor="#57C9C9" /><stop offset="100%" stopColor="#134A4A" /></radialGradient>
        <radialGradient id="nYellow" cx="35%" cy="30%" r="75%"><stop offset="0%" stopColor="#EFD35C" /><stop offset="100%" stopColor="#6E5A0C" /></radialGradient>
      </defs>

      <g fill="none" stroke="#22354E" strokeWidth="1" opacity=".6">
        <ellipse cx="320" cy="240" rx="270" ry="200" />
        <ellipse cx="320" cy="240" rx="215" ry="152" transform="rotate(-12 320 240)" />
        <ellipse cx="320" cy="240" rx="165" ry="120" transform="rotate(9 320 240)" />
      </g>

      <g fill="none" strokeWidth="1.3" opacity=".75">
        {HERO_LINKS.map(([a, b], i) => {
          const p = HERO_PTS[a]
          const q = HERO_PTS[b]
          return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={HERO_EDGE_COLOR[p[2]]} opacity=".45" />
        })}
      </g>
      <g>
        {HERO_PTS.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={p[3]} fill={`url(#${p[2]})`} />)}
      </g>

      <g transform="translate(320 235)">
        <path d="M -18 -118 A 118 118 0 0 1 82 -86 L 58 -60 A 84 84 0 0 0 -12 -83 Z" fill="url(#pYellow)" stroke="#0D1520" strokeWidth="2" />
        <path d="M 96 -72 A 120 120 0 0 1 116 28 L 82 20 A 86 86 0 0 0 68 -50 Z" fill="url(#pBlue)" stroke="#0D1520" strokeWidth="2" />
        <path d="M 108 44 A 120 120 0 0 1 30 116 L 22 82 A 86 86 0 0 0 76 32 Z" fill="url(#pGreen)" stroke="#0D1520" strokeWidth="2" />
        <path d="M 8 120 A 120 120 0 0 1 -90 78 L -64 55 A 86 86 0 0 0 5 85 Z" fill="url(#pYellow)" stroke="#0D1520" strokeWidth="2" />
        <path d="M -102 62 A 120 120 0 0 1 -117 -32 L -83 -22 A 86 86 0 0 0 -73 44 Z" fill="url(#pBlue)" stroke="#0D1520" strokeWidth="2" />
        <path d="M -112 -50 A 120 120 0 0 1 -38 -114 L -28 -81 A 86 86 0 0 0 -80 -36 Z" fill="url(#pGreen)" stroke="#0D1520" strokeWidth="2" />
        <circle r="62" fill="url(#core)" />
        <ellipse cx="-18" cy="-24" rx="22" ry="14" fill="#fff" opacity=".28" />
      </g>
    </svg>
  )
}
