import { Link } from 'react-router-dom'
import type { Persona } from '../../lib/auth'
import { canDrill } from '../../lib/views'
import { TOWER_KEYS, TOWERS } from '../../data/towers'
import TowerIcon from '../../components/TowerIcon'

// The mock's four CTO-tower cards (Auto / Home Lending / Cards / Shared
// Services) — NOT modules; site-plan §3 is explicit that they are demo
// *content* that lives inside Explorer, kept with their EXAMPLE DATA ·
// ILLUSTRATIVE honesty tag. Ported from the old Landing.tsx "Explore by
// Tower" section (O2), now Explorer's graph-pane placeholder until a real
// tower/app drill-down graph replaces it.
export default function TowerDemoGrid({ persona }: { persona: Persona }) {
  return (
    <div className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Explore by Tower</h3>
        <span className="rounded border border-yellow/50 bg-yellow/10 px-2 py-0.5 font-mono text-[10px] text-yellow">
          EXAMPLE DATA · ILLUSTRATIVE / ANONYMIZED
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {TOWER_KEYS.map((key) => {
          const t = TOWERS[key]
          const allowed = canDrill(key, persona)
          return (
            <Link
              key={key}
              to={allowed ? `/explorer/tower/${key}` : '#'}
              aria-disabled={!allowed}
              title={allowed ? undefined : 'outside this persona’s ServiceNow-derived access (mock)'}
              className={
                'flex flex-col items-center gap-1.5 rounded-lg border border-edge bg-panel p-3 text-center no-underline transition-colors ' +
                (allowed ? 'hover:border-faint' : 'pointer-events-none opacity-40')
              }
            >
              <TowerIcon tower={key} />
              <span className="text-sm font-semibold text-text">{t.title}</span>
              <span className="flex gap-3 text-[11px] text-muted">
                {t.stats.map(([n, unit]) => (
                  <span key={unit}>
                    <b className="text-text">{n}</b> {unit}
                  </span>
                ))}
              </span>
            </Link>
          )
        })}
      </div>
      <p className="mt-3 text-center text-xs text-faint">
        Live dependency graph:{' '}
        <Link to="/explorer/live" className="text-blue-bright">
          /explorer/live
        </Link>{' '}
        (real WAS_INFORMED_BY edges, backlog O6)
      </p>
    </div>
  )
}
