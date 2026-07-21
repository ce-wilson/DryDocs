import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { MODULES } from '../modules/registry'
import ModuleIcon from '../components/ModuleIcon'
import ModuleToolbar from '../layout/ModuleToolbar'

// The Overview / landing route (`/`, site-plan §3 row 0, wf-landing-01):
// radial hub — brand core center, one spoke per module, same registry that
// drives the aside nav (wf-landing-01 annotation 1 — one array, two
// renderings). No page actions in this toolbar (wf-landing-01: "(no page
// actions)"); Overview has no spoke of its own — the core sphere IS its
// representation (annotation 3).
export default function OverviewRoute({ persona }: { persona: Persona }) {
  const cx = 320
  const cy = 240
  const r = 190

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home' }]} />
      <h2 tabIndex={-1} data-view-heading className="sr-only">
        Overview
      </h2>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-4 py-8">
          {/* radial hub — desktop/tablet */}
          <div className="relative mx-auto hidden aspect-[640/480] w-full max-w-3xl md:block">
            <svg viewBox="0 0 640 480" className="absolute inset-0 h-full w-full" aria-hidden="true">
              <g fill="none" stroke="var(--edge)" strokeWidth="1" opacity=".6">
                <ellipse cx={cx} cy={cy} rx={r + 40} ry={r + 10} />
              </g>
              {MODULES.map((m, i) => {
                const angle = (-90 + i * 45) * (Math.PI / 180)
                const x = cx + r * Math.cos(angle)
                const y = cy + r * Math.sin(angle)
                return <line key={m.id} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--edge)" strokeWidth="1.5" />
              })}
              <circle cx={cx} cy={cy} r="58" fill="var(--red)" opacity="0.9" />
              <circle cx={cx - 18} cy={cy - 20} r="18" fill="#fff" opacity=".22" />
            </svg>

            <div
              className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center text-center"
              style={{ left: `${(cx / 640) * 100}%`, top: `${(cy / 480) * 100}%` }}
            >
              <span className="font-bold text-white drop-shadow">DryDocs</span>
            </div>

            {MODULES.map((m, i) => {
              const angle = (-90 + i * 45) * (Math.PI / 180)
              const x = cx + r * Math.cos(angle)
              const y = cy + r * Math.sin(angle)
              return (
                <Link
                  key={m.id}
                  to={m.path}
                  className="group absolute flex w-32 -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1 rounded-lg p-2 text-center no-underline hover:bg-panel-2"
                  style={{ left: `${(x / 640) * 100}%`, top: `${(y / 480) * 100}%` }}
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-full border border-edge bg-panel text-muted group-hover:border-blue-bright group-hover:text-blue-bright">
                    <ModuleIcon id={m.id} className="h-5 w-5" />
                  </span>
                  <span className="text-sm font-semibold text-text">{m.label}</span>
                  <span className="line-clamp-1 text-[11px] text-faint">{m.tagline}</span>
                  {/* health glyph: static neutral until the Loads module's JobRun
                      QuerySpec lands (wf-landing-01 annotation 4) — no fake green */}
                  <span
                    aria-hidden="true"
                    title="Health: not yet wired up"
                    className="h-1.5 w-1.5 rounded-full bg-faint"
                  />
                </Link>
              )
            })}
          </div>

          {/* module card grid — narrow screens (wf-landing-01 annotation 8: the
              radial SVG is desktop-only sugar, never the only path) */}
          <div className="grid grid-cols-2 gap-3 md:hidden">
            {MODULES.map((m) => (
              <Link
                key={m.id}
                to={m.path}
                className="flex flex-col gap-1 rounded-lg border border-edge bg-panel p-3 no-underline hover:border-faint"
              >
                <ModuleIcon id={m.id} className="h-5 w-5 text-muted" />
                <span className="text-sm font-semibold text-text">{m.label}</span>
                <span className="text-[11px] text-faint">{m.tagline}</span>
              </Link>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <Link
              to="/explorer"
              className="rounded-md border border-blue-bright bg-blue px-5 py-2.5 text-sm font-semibold text-white no-underline hover:bg-blue-bright"
            >
              Explore the Graph
            </Link>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-4 border-t border-edge-soft pt-6 sm:grid-cols-2 lg:grid-cols-4">
            <BenefitCard title="Automated Discovery" text="Pipelines and jobs surface themselves as the graph loads." />
            <BenefitCard title="Impact Analysis" text="See what breaks downstream before you change anything." />
            <BenefitCard title="Governance & Posture" text="Ownership, trust tier, and provenance travel with every node." />
            <BenefitCard title="Change Management" text="Findings, fix batches, and gates stay linked to their source." />
          </div>

          <OnboardingChecklist />

          <p className="mt-8 text-center font-mono text-[11px] text-faint">
            Signed in as {persona.displayName} ({persona.role}) · demo/synthetic content is tagged EXAMPLE
            DATA · ILLUSTRATIVE
          </p>
        </div>
      </div>
    </div>
  )
}

function BenefitCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border border-edge bg-panel p-4">
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      <p className="mt-1 text-xs text-muted">{text}</p>
    </div>
  )
}

// Onboarding checklist (site-plan §3 row 0: "benefit cards + onboarding
// checklist instead" of data frames; gemini-wire-frame.md's
// UserOnboardingChecklist). Checked state persists locally — it's a personal
// tour tracker, not server state.
const ONBOARDING_KEY = 'drydocs.onboarding.v1'
const ONBOARDING_STEPS = [
  { id: 'explore', label: 'Explore a tower pipeline in the Explorer graph', to: '/explorer' },
  { id: 'inspect', label: 'Click a graph node — the inspector opens, the data frames filter', to: '/explorer' },
  { id: 'theme', label: 'Try the System / Dark / Light theme toggle in the header', to: null },
  { id: 'live', label: 'Open the live dependency graph (real WAS_INFORMED_BY edges)', to: '/explorer/live' },
  { id: 'console', label: 'Run a read-only query in the Cypher console', to: '/console' },
] as const

function OnboardingChecklist() {
  const [done, setDone] = useState<readonly string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(ONBOARDING_KEY) ?? '[]') as string[]
    } catch {
      return []
    }
  })

  function toggle(id: string) {
    setDone((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
      try {
        localStorage.setItem(ONBOARDING_KEY, JSON.stringify(next))
      } catch {
        /* ignore */
      }
      return next
    })
  }

  return (
    <div className="mt-6 rounded-lg border border-edge bg-panel p-4">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-text">Getting started</h3>
        <span className="font-mono text-[11px] text-faint">
          {done.length}/{ONBOARDING_STEPS.length}
        </span>
      </div>
      <ul className="mt-2 flex flex-col gap-1.5">
        {ONBOARDING_STEPS.map((s) => (
          <li key={s.id} className="flex items-center gap-2 text-xs">
            <input
              id={`onboard-${s.id}`}
              type="checkbox"
              checked={done.includes(s.id)}
              onChange={() => toggle(s.id)}
              className="h-3.5 w-3.5 accent-(--blue-br)"
            />
            <label htmlFor={`onboard-${s.id}`} className={done.includes(s.id) ? 'text-faint line-through' : 'text-muted'}>
              {s.label}
            </label>
            {s.to && (
              <Link to={s.to} className="text-blue-bright no-underline hover:underline">
                go →
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
