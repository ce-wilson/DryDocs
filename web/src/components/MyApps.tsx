import type { Persona } from '../lib/auth'
import { MY_APPS_BY_PERSONA, type MyApp } from '../data/myApps'
import { MY_APPS_ROLLUP } from '../data/towers'
import GraphSvg from './GraphSvg'

// Read-only user landing view: ServiceNow-derived app access rolling up to a CTO
// tower, dev teams from PAT. All data SYNTHESIZED (data/myApps.ts). No actions
// by construction — the user role is read-only.
export default function MyApps({ persona }: { persona: Persona }) {
  const apps = MY_APPS_BY_PERSONA[persona.id] ?? []
  const tower = apps[0]?.tower
  return (
    <main className="wrap">
      <div className="d-bar">
        <h2 tabIndex={-1} data-view-heading className="outline-none">My Apps — Home Lending</h2>
        <span className="tag">USER VIEW · SYNTHESIZED</span>
        <span className="userchip">◉ {persona.id} · {persona.chip}</span>
      </div>

      {tower ? (
        <div className="panel rollup-panel">
          <div className="p-head">
            App rollup — CTO Tower &amp; Dev Teams <span className="m">apps: ServiceNow access · teams: PAT</span>
          </div>
          <div className="graphbox">
            <GraphSvg
              graph={MY_APPS_ROLLUP}
              viewBox="0 0 620 290"
              ariaLabel={`${apps.length} applications from the user's ServiceNow access rolling up to the ${tower.name} CTO tower`}
            />
          </div>
        </div>
      ) : (
        <p className="note">No app access derived for this persona.</p>
      )}

      <div className="app-cards">
        {apps.map((a) => (
          <AppCard key={a.id} app={a} />
        ))}
      </div>
      <div className="foot">
        User view assembled from: ServiceNow (my app access) · PAT (dev team alignment) — all synthesized
      </div>
    </main>
  )
}

function AppCard({ app }: { app: MyApp }) {
  return (
    <div className="app-card panel">
      <div className="app-card-row">
        <code className="app-id">{app.id}</code>
        <span className={`badge-snow badge-snow-${app.snowPermission.toLowerCase()}`}>
          SNOW · {app.snowPermission}
        </span>
      </div>
      <div className="app-name">{app.name}</div>
      <div className="app-desc">{app.description}</div>
      <div className="app-card-row app-card-foot">
        <span>{app.team.name} · {app.team.engineers} engineers</span>
        <span className="badge-pat">PAT</span>
      </div>
    </div>
  )
}
