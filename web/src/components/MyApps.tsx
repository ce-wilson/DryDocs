import type { Persona } from '../lib/auth'
import { MY_APPS_BY_PERSONA, type MyApp } from '../data/myApps'
import { MY_APPS_ROLLUP } from '../data/towers'
import GraphSvg from './GraphSvg'

// Read-only user landing view: ServiceNow-derived app access rolling up to a CTO
// tower, dev teams from PAT. All data SYNTHESIZED (data/myApps.ts). No actions
// by construction — the user role is read-only.
// O30: styled inline via Tailwind/token classes (App.css retired). Values that
// were dark hardcodes in the mockup CSS stay verbatim — O32 owns the light pass.

const PANEL = 'overflow-hidden rounded-md border border-edge bg-panel'
const P_HEAD =
  'flex items-center justify-between gap-2.5 border-b border-edge bg-panel-2 px-3.5 py-2.5 text-sm/[1.5] font-semibold'
const P_HEAD_M = 'font-mono text-[11px] font-normal text-muted'
const BADGE = 'whitespace-nowrap rounded-xs border px-2 py-[3px] font-mono text-[10px] font-medium'
const SNOW_BADGE: Record<string, string> = {
  read: 'border-blue-bright bg-blue-bright/10 text-blue-bright',
  contribute: 'border-green bg-green/10 text-green',
  // DL-2: danger ≠ brand red
  admin: 'border-status-fail bg-status-fail/12 text-status-fail-soft',
}

export default function MyApps({ persona }: { persona: Persona }) {
  const apps = MY_APPS_BY_PERSONA[persona.id] ?? []
  const tower = apps[0]?.tower
  return (
    <main className="mx-auto max-w-[1180px] px-[30px]">
      <div className="flex flex-wrap items-center gap-3.5 pb-4 pt-6">
        <h2 tabIndex={-1} data-view-heading className="text-[21px] font-bold outline-none">My Apps — Home Lending</h2>
        <span className="whitespace-nowrap rounded-xs border border-yellow/50 bg-yellow/8 px-[9px] py-1 font-mono text-[11px] font-medium text-yellow">
          USER VIEW · SYNTHESIZED
        </span>
        <span className="max-w-[300px] overflow-hidden text-ellipsis whitespace-nowrap rounded-full border border-edge px-3 py-[5px] font-mono text-[11px] font-medium text-muted">
          ◉ {persona.id} · {persona.chip}
        </span>
      </div>

      {tower ? (
        <div className={`${PANEL} mb-4`}>
          <div className={P_HEAD}>
            App rollup — CTO Tower &amp; Dev Teams <span className={P_HEAD_M}>apps: ServiceNow access · teams: PAT</span>
          </div>
          <div className="mx-auto max-w-[720px] p-2.5">
            <GraphSvg
              graph={MY_APPS_ROLLUP}
              viewBox="0 0 620 290"
              ariaLabel={`${apps.length} applications from the user's ServiceNow access rolling up to the ${tower.name} CTO tower`}
            />
          </div>
        </div>
      ) : (
        <p className="mt-2 text-[13px] leading-[1.55] text-muted">No app access derived for this persona.</p>
      )}

      <div className="mb-4 grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
        {apps.map((a) => (
          <AppCard key={a.id} app={a} />
        ))}
      </div>
      <div className="pb-[46px] pt-5 text-center font-mono text-[11px] text-faint">
        User view assembled from: ServiceNow (my app access) · PAT (dev team alignment) — all synthesized
      </div>
    </main>
  )
}

function AppCard({ app }: { app: MyApp }) {
  return (
    <div className={`${PANEL} px-4 py-3.5`}>
      <div className="flex items-center justify-between gap-2.5">
        <code className="font-mono text-[11px] text-blue-bright">{app.id}</code>
        <span className={`${BADGE} ${SNOW_BADGE[app.snowPermission.toLowerCase()] ?? ''}`}>
          SNOW · {app.snowPermission}
        </span>
      </div>
      <div className="mt-2.5 text-[15px] font-semibold">{app.name}</div>
      <div className="mb-3 mt-[3px] text-xs/[1.5] text-muted">{app.description}</div>
      <div className="flex items-center justify-between gap-2.5 border-t border-edge-soft pt-2.5 text-[13px]">
        <span>{app.team.name} · {app.team.engineers} engineers</span>
        <span className={`${BADGE} border-yellow bg-yellow/8 text-yellow`}>PAT</span>
      </div>
    </div>
  )
}
