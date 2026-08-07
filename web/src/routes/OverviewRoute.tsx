import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { canDrill } from '../lib/views'
import { createApiAccess } from '../lib/graphApi'
import { parseStatusItems, type StatusItem } from '../lib/status'
import { HealthGlyph } from '../components/ui/StatusItems'
import { MODULES, canAccessModule } from '../modules/registry'
import { TOWERS } from '../data/towers'
import ModuleIcon from '../components/ModuleIcon'
import ModuleToolbar from '../layout/ModuleToolbar'
import BrandMark from '../components/BrandMark'

// The Overview / landing route (`/`) — O35 category-first rebuild per SME
// feedback FB-2026-07-28-01/02 (UI-WIP/wireframes/, keys WF-LND-*): the dense
// radial hub (HeroArt + spoke ring) is DEMOTED to a small decorative mark
// (WF-LND-04), the product name renders exactly ONCE (the header wordmark —
// this page's h1 is the value proposition, WF-LND-02), and navigation is two
// explicit pick-lists: modules ("what do you want to look at?", WF-LND-05,
// same registry as the aside nav) and business towers (WF-LND-06, scoping
// Explorer drill-down per persona). data-wf attributes keep the wireframe
// keys attached to the DOM for the L5/L6 feedback loop.
export default function OverviewRoute({ persona }: { persona: Persona }) {
  // O28 spoke health glyphs. The envelope is the contract, so a spoke lights up
  // as soon as SOME producer reports on it — today that is the loader stream
  // behind /loads. Every other spoke renders UNKNOWN rather than healthy, which
  // is the distinction the contract exists to preserve: a green tick for a
  // module nothing observes is how a dashboard ends up green because nothing is
  // watching. As producers land, they light their own spokes with no change here.
  const [loadHealth, setLoadHealth] = useState<StatusItem[] | null>(null)
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  useEffect(() => {
    let cancelled = false
    access
      .runSpec('loads.status-items.v1')
      .then((r) => {
        if (!cancelled) setLoadHealth(parseStatusItems(r.rows.map((row) => row.status_item)))
      })
      // No API (or no runs yet) leaves the spoke UNKNOWN — never a false green.
      .catch(() => {
        if (!cancelled) setLoadHealth(null)
      })
    return () => {
      cancelled = true
    }
  }, [access])

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home' }]} />
      <h2 tabIndex={-1} data-view-heading className="sr-only">
        Overview
      </h2>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-4 py-8">
          {/* hero — copy left, small mark right (WF-LND-02/03/04) */}
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="max-w-xl">
              <h1 data-wf="WF-LND-02" className="text-[clamp(1.9rem,4vw,2.6rem)] font-extrabold leading-tight tracking-tight text-text">
                A Don&rsquo;t-Repeat-Yourself Knowledge Graph
              </h1>
              <p data-wf="WF-LND-03" className="mt-3 max-w-lg text-[15.5px] leading-relaxed text-muted">
                What runs, what it depends on, who owns it, which application it belongs to. Pick an
                area below to start &mdash; every view is backed by the graph.
              </p>
              <div className="mt-6 flex flex-wrap gap-3.5">
                <Link
                  to="/explorer"
                  className="rounded-md border border-blue-bright bg-blue px-5 py-3 text-sm font-semibold text-white no-underline transition-colors hover:bg-blue-bright"
                >
                  Explore the Graph
                </Link>
                <Link
                  to="/under-the-hood"
                  className="rounded-md border border-edge px-5 py-3 text-sm font-semibold text-text no-underline transition-colors hover:border-faint"
                >
                  See how retrieval works &rarr;
                </Link>
              </div>
            </div>
            <div data-wf="WF-LND-04" className="hidden shrink-0 pr-6 md:block" aria-hidden="true">
              <BrandMark size={120} />
            </div>
          </div>

          {/* category pick-lists (WF-LND-05/06) */}
          <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_1fr]">
            <section data-wf="WF-LND-05" className="rounded-lg border border-edge bg-panel p-4">
              <h3 className="text-sm font-semibold text-text">What do you want to look at?</h3>
              <ul className="mt-3 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                {/* FB-03, matching Aside.tsx exactly: a module a persona cannot
                    open does not appear. VANISHING, not disabled-with-a-reason —
                    SME ruling 2026-08-07: the console is a proof of concept and
                    real authentication comes later, so a second access idiom is
                    complexity bought against a decision not yet made. Before
                    this, the pick-list rendered EVERY module while the aside
                    filtered, so `gates`/`underhood` (and then `software`) showed
                    here for the `user` persona and bounced to / on click. */}
                {MODULES.filter((m) => canAccessModule(m.access, persona.role)).map((m) => (
                  <li key={m.id}>
                    <Link
                      to={m.path}
                      className="group flex items-center gap-2.5 rounded-md border border-transparent px-2 py-1.5 no-underline hover:border-edge hover:bg-panel-2"
                    >
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-edge bg-panel text-muted group-hover:border-blue-bright group-hover:text-blue-bright">
                        <ModuleIcon id={m.id} className="h-4 w-4" />
                      </span>
                      <span className="min-w-0">
                        <span className="flex items-center gap-1.5 text-[13px] font-semibold text-text">
                          <HealthGlyph
                            items={m.id === 'loads' ? (loadHealth ?? []) : []}
                            unknown={m.id !== 'loads' || loadHealth === null}
                          />
                          {m.label}
                        </span>
                        <span className="block truncate text-[11px] text-faint">{m.tagline}</span>
                      </span>
                      <span className="ml-auto rounded border border-edge-soft px-1 py-0.5 font-mono text-[9px] text-faint">
                        P{m.phase}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>

            <section data-wf="WF-LND-06" className="rounded-lg border border-edge bg-panel p-4">
              <h3 className="text-sm font-semibold text-text">Business area / tower</h3>
              <p className="mt-0.5 text-[11px] text-faint">Pick a target &mdash; it scopes the Explorer drill-down.</p>
              <ul className="mt-3 flex flex-col gap-1.5">
                {Object.values(TOWERS).map((tw) => {
                  const drillable = canDrill(tw.key, persona)
                  const inner = (
                    <>
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: tw.color }} aria-hidden="true" />
                      <span className="text-[13px] font-semibold text-text">{tw.title}</span>
                      <span className="ml-auto font-mono text-[10px] text-faint">
                        {tw.stats.map(([v, l]) => `${v} ${l}`).join(' \u00b7 ')}
                      </span>
                    </>
                  )
                  return (
                    <li key={tw.key}>
                      {drillable ? (
                        <Link
                          to={`/explorer/tower/${tw.key}`}
                          className="flex items-center gap-2.5 rounded-md border border-transparent px-2 py-2 no-underline hover:border-edge hover:bg-panel-2"
                        >
                          {inner}
                        </Link>
                      ) : (
                        <div
                          className="flex items-center gap-2.5 rounded-md px-2 py-2 opacity-55"
                          title="Outside your persona's drill scope (mock auth)"
                        >
                          {inner}
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
            </section>
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
    <div className="hover-lift rounded-lg border border-edge bg-panel p-4">
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
