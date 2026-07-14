import type { Persona } from '../lib/auth'
import { MY_APPS_BY_PERSONA, type MyApp } from '../data/myApps'

// Read-only user landing view: ServiceNow-derived app access rolling up to a CTO
// tower, dev teams from PAT. All data SYNTHESIZED (data/myApps.ts). No actions
// by construction — the user role is read-only.
export default function MyApps({ persona }: { persona: Persona }) {
  const apps = MY_APPS_BY_PERSONA[persona.id] ?? []
  const tower = apps[0]?.tower
  return (
    <main>
      <div className="view-head">
        <h1>My Apps</h1>
        <span className="tag">USER VIEW · SYNTHESIZED</span>
      </div>
      {tower ? (
        <p className="note">
          {apps.length} apps roll up to {tower.name} (<code>{tower.id}</code>) —
          apps: ServiceNow access · teams: PAT
        </p>
      ) : (
        <p className="note">No app access derived for this persona.</p>
      )}
      <div className="app-cards">
        {apps.map((a) => (
          <AppCard key={a.id} app={a} />
        ))}
      </div>
      <p className="note">
        assembled from: ServiceNow (app access) · PAT (dev team alignment) — all synthesized
      </p>
    </main>
  )
}

function AppCard({ app }: { app: MyApp }) {
  return (
    <div className="app-card">
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
