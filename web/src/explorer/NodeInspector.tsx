import { Link } from 'react-router-dom'
import type { Persona } from '../lib/auth'
import { canDrill } from '../lib/views'
import { TOWERS } from '../data/towers'
import { connectionsOf, KIND_TOKEN, type NodeKind, type Selection } from './demoGraph'
import IdChip, { StageBadge } from '../components/ui/IdChip'

// The right-sidebar node inspector (O9, wf-module-subpage-01 annotation 2):
// content variant keyed by node type. Fed into the shell's RightSidebarSlot by
// ExplorerRoute whenever the shared selection changes.

const KIND_BLURB: Record<NodeKind, string> = {
  Tower: 'CTO tower — the demo drill-down entry point.',
  EtlJob: 'ETL process node. In the live graph this is a :ControlMJob-scheduled transform.',
  ControlMJob: 'Scheduler job. Live equivalent carries folder/job identity + run stats.',
  Dataset: 'Data asset flowing between jobs and stages.',
  S3Stage: 'Landing/staging zone (RAW → TRUSTED → REFINED in the live model).',
  Warehouse: 'Analytical warehouse target.',
  Platform: 'Shared platform owned by Shared Services.',
  Application: 'Business application (SEAL-keyed in the live graph).',
}

export default function NodeInspector({ selection, persona, onSelect }: {
  selection: Selection
  persona: Persona
  onSelect: (sel: Selection | null) => void
}) {
  const token = KIND_TOKEN[selection.kind]
  const tower = TOWERS[selection.tower]
  const connections = connectionsOf(selection)

  return (
    <div className="flex w-64 flex-col gap-3 p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-text">{selection.label}</h3>
          <span
            className="mt-1 inline-block rounded-full border px-2 py-0.5 font-mono text-[10px]"
            style={{ borderColor: `var(${token})`, color: `var(${token})` }}
          >
            {selection.kind}
          </span>
        </div>
        <button
          type="button"
          onClick={() => onSelect(null)}
          aria-label="Close inspector"
          className="rounded px-1.5 text-muted hover:bg-panel-2 hover:text-text"
        >
          ✕
        </button>
      </div>

      <p className="text-xs text-muted">{KIND_BLURB[selection.kind]}</p>

      {selection.kind === 'S3Stage' && (
        // DL-11a: the medallion stage vocabulary renders as flat mono badges
        // (the same words both neighboring tools use), never prose-only.
        <div className="flex flex-wrap items-center gap-1" aria-label="Medallion stages">
          <StageBadge stage="RAW" />
          <span className="text-[10px] text-faint">→</span>
          <StageBadge stage="TRUSTED" />
          <span className="text-[10px] text-faint">→</span>
          <StageBadge stage="REFINED" />
          <span className="text-[10px] text-faint">→</span>
          <StageBadge stage="SNOWFLAKE" />
        </div>
      )}

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        <dt className="text-faint">Tower</dt>
        <dd className="text-text">{tower.title}</dd>
        <dt className="text-faint">Node id</dt>
        <dd>
          {/* O38 IdChip convention; O39: grows a runtime-view link once the env template is set */}
          <IdChip
            id={selection.id}
            runtimeKind={selection.kind === 'ControlMJob' || selection.kind === 'EtlJob' ? 'job' : 'dataset'}
          />
        </dd>
        <dt className="text-faint">Provenance</dt>
        <dd className="font-mono text-[10px] text-yellow">SYNTHESIZED · illustrative</dd>
      </dl>

      {connections.length > 0 && (
        <div>
          <h4 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-faint">Connections</h4>
          <ul className="flex flex-col gap-1">
            {connections.map((c, i) => (
              <li key={i}>
                <button
                  type="button"
                  onClick={() => onSelect({ id: c.other.id, label: c.other.label, kind: c.other.kind, tower: c.other.tower })}
                  className="flex w-full items-center gap-1.5 rounded border border-edge-soft bg-bg-2/50 px-2 py-1 text-left text-[11px] text-text hover:border-faint"
                >
                  <span className="font-mono text-[10px] text-muted">{c.dir === 'out' ? '→' : '←'}</span>
                  <span className="font-mono text-[10px] text-teal">{c.rel}</span>
                  <span className="truncate">{c.other.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {selection.kind === 'Tower' && canDrill(selection.tower, persona) && (
        <Link
          to={`/explorer/tower/${selection.tower}`}
          className="rounded-md border border-blue-bright px-3 py-1.5 text-center text-xs font-semibold text-blue-bright no-underline hover:bg-blue/10"
        >
          Open {tower.title} drill-down
        </Link>
      )}
    </div>
  )
}
