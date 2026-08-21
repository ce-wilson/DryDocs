import { useMemo, useState } from 'react'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import StatTiles from '../components/StatTiles'
import EmptyState from '../components/ui/EmptyState'
import {
  AD_HOC_COMMANDS,
  DEFECT_COUNT,
  DOC_CORPUS_COUNT,
  KINDS,
  MAP_ENTRIES_WITHOUT_SOURCE,
  RETIRED,
  SEQUENCE,
  SOURCELESS_LOADERS,
  SOURCES,
  SYSTEMS,
  ledgerPath,
  ledgerState,
  pipelineReach,
  type LoadMapSource,
} from '../loadmap/loadMapModel'

// /load-map (O57) — the console lens on web/src/generated/load-map.json.
//
// READ-ONLY and DECLARATION-ONLY. Every cell is a fact the registries declare,
// never a graph read: this page cannot tell you whether a load SUCCEEDED (that
// is /loads and its :JobRun envelope) — only what is registered to load, in
// what order, and what is known to be broken about that declaration.
//
// It reads the committed JSON and never re-derives, so it cannot disagree with
// docs/plan/load-map.html. That page is N5's print/PDF surface for the SME
// loop and keeps its own audience; this is the interactive one.

const loadMapModule = MODULES.find((m) => m.id === 'loadmap')!

const TH = 'border-b border-edge px-2.5 py-1.5 font-semibold text-muted'
const TD = 'border-b border-edge-soft px-2.5 py-1.5'

function Table({ headers, children }: { headers: readonly string[]; children: React.ReactNode }) {
  return (
    <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
      <table className="w-full border-collapse text-left text-[11px]">
        <thead className="sticky top-0 bg-panel-2">
          <tr>
            {headers.map((h) => (
              <th key={h} className={TH}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

export default function LoadMapRoute() {
  const [kind, setKind] = useState<string | null>(null)

  const shown: LoadMapSource[] = useMemo(() => (kind ? SOURCES.filter((s) => s.kind === kind) : SOURCES), [kind])

  const banner = (
    <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
      <b>Declared, not observed.</b> Every row here comes from the registries via the generated
      <code className="mx-1">load-map.json</code> — what is registered to load and in what order. Whether a load
      actually ran is <b>/loads</b>. The {DOC_CORPUS_COUNT} doc-corpus sources are deliberately absent: they are
      rendered by <b>/software</b>, and the two pages split the file on the same key so no row is shown twice or
      dropped.
    </p>
  )

  const tiles = [
    { value: String(SOURCES.length), label: 'sources' },
    { value: String(SYSTEMS.length), label: 'systems' },
    { value: String(SEQUENCE.length), label: 'sequence steps' },
    { value: String(RETIRED.length), label: 'retired ids' },
    { value: String(AD_HOC_COMMANDS.length), label: 'ad-hoc commands' },
    { value: String(DEFECT_COUNT), label: 'declared defects' },
  ]

  const graphPane = (
    <div className="flex h-full min-h-0 flex-col gap-2 p-3">
      {banner}
      <StatTiles tiles={tiles} />
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge bg-panel-2 p-2">
        <p className="mb-1.5 text-[11px] font-semibold text-muted">Canonical load sequence</p>
        <ol className="flex flex-wrap items-center gap-1.5">
          {SEQUENCE.map((step, i) => (
            <li key={`${step.command}-${i}`} className="flex items-center gap-1.5">
              <span
                title={step.note ?? undefined}
                className="rounded border border-edge bg-panel px-1.5 py-0.5 font-mono text-[10px] text-text"
              >
                {step.command}
                {step.loaders.length ? (
                  <span className="ml-1 text-faint">·{step.loaders.length}</span>
                ) : null}
              </span>
              {i < SEQUENCE.length - 1 && <span className="text-faint">→</span>}
            </li>
          ))}
        </ol>
        <p className="mt-2 text-[10px] text-faint">
          Outside the sequence — run by hand, never scheduled:{' '}
          {AD_HOC_COMMANDS.map((c) => (
            <code key={c} className="mr-1.5">
              {c}
            </code>
          ))}
        </p>
      </div>
    </div>
  )

  const sourcesTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <div className="flex shrink-0 flex-wrap items-center gap-1.5">
        <span className="text-[11px] text-faint">kind:</span>
        <button
          type="button"
          onClick={() => setKind(null)}
          aria-pressed={kind === null}
          className={
            'rounded border px-2 py-0.5 text-[10px] ' +
            (kind === null ? 'border-blue-bright bg-panel-2 text-text' : 'border-edge text-muted hover:text-text')
          }
        >
          all ({SOURCES.length})
        </button>
        {KINDS.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setKind(kind === k ? null : k)}
            aria-pressed={kind === k}
            className={
              'rounded border px-2 py-0.5 font-mono text-[10px] ' +
              (kind === k ? 'border-blue-bright bg-panel-2 text-text' : 'border-edge text-muted hover:text-text')
            }
          >
            {k} ({SOURCES.filter((s) => s.kind === k).length})
          </button>
        ))}
      </div>
      <Table
        headers={[
          'Source id',
          'System',
          'Origin',
          'Kind',
          'Authority',
          'Classification',
          'Confirmed',
          'Ledger',
          'Pipeline reach',
          'Loaders',
        ]}
      >
        {shown.map((s, i) => {
          const reach = pipelineReach(s)
          const path = ledgerPath(s.ledger)
          return (
            <tr key={s.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
              <td className={`${TD} font-mono text-[10px] text-text`}>
                {s.id}
                {s.derived && <span className="ml-1 text-faint">· derived</span>}
                {s.replaces && <span className="ml-1 text-faint">· replaces {s.replaces}</span>}
              </td>
              <td className={`${TD} text-muted`}>{s.system ?? '—'}</td>
              <td className={`${TD} text-muted`}>{s.origin ?? '—'}</td>
              <td className={`${TD} font-mono text-[10px] text-muted`}>{s.kind}</td>
              <td className={`${TD} text-muted`}>{s.authority ?? '—'}</td>
              <td className={`${TD} text-muted`}>{s.classification ?? '—'}</td>
              <td className={`${TD} ${s.confirmed ? 'text-text' : 'text-faint'}`}>
                {s.confirmed ? 'yes' : 'not yet'}
              </td>
              <td className={`${TD} font-mono text-[10px] text-muted`} title={path ?? undefined}>
                {ledgerState(s.ledger)}
              </td>
              <td className={`${TD} text-[10px] ${reach.loaded ? 'text-text' : 'text-faint'}`}>{reach.label}</td>
              <td className={`${TD} font-mono text-[10px] text-muted`}>
                {s.loaders.map((l) => l.cli_name ?? l.name).join(', ') || '—'}
              </td>
            </tr>
          )
        })}
      </Table>
      <p className="shrink-0 text-[10px] text-faint">
        “Pipeline reach” names the stages a source has actually been taken through — it is not a score. A source that
        stops at <i>registered only</i> may be entirely correct; the registries say what exists, not what ought to.
      </p>
    </div>
  )

  const systemsTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <Table headers={['System', 'Name', 'Layer', 'Classification', 'Sources', 'Taxonomy captures']}>
        {SYSTEMS.map((sys, i) => (
          <tr key={sys.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
            <td className={`${TD} font-mono text-[10px] text-text`}>{sys.id}</td>
            <td className={`${TD} text-muted`}>{sys.name}</td>
            <td className={`${TD} text-muted`}>{sys.layer ?? '—'}</td>
            <td className={`${TD} text-muted`}>{sys.classification ?? '—'}</td>
            <td className={`${TD} tabular-nums text-muted`}>{SOURCES.filter((s) => s.system === sys.id).length}</td>
            <td className={`${TD} tabular-nums text-muted`}>{sys.taxonomy_captures.length}</td>
          </tr>
        ))}
      </Table>
    </div>
  )

  const sequenceTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <Table headers={['#', 'Command', 'Mode', 'Profiles', 'Loaders', 'Note']}>
        {SEQUENCE.map((step, i) => (
          <tr key={`${step.command}-${i}`} className={i % 2 ? 'bg-bg-2/40' : ''}>
            <td className={`${TD} tabular-nums text-faint`}>{i + 1}</td>
            <td className={`${TD} font-mono text-[10px] text-text`}>{step.command}</td>
            <td className={`${TD} text-muted`}>{step.mode}</td>
            <td className={`${TD} font-mono text-[10px] text-muted`}>{step.profiles.join(', ') || '—'}</td>
            <td className={`${TD} font-mono text-[10px] text-muted`}>
              {step.loaders.map((l) => l.cli_name ?? l.name).join(', ') || '—'}
            </td>
            <td className={`${TD} text-muted`}>{step.note ?? '—'}</td>
          </tr>
        ))}
      </Table>
      <p className="shrink-0 text-[10px] text-faint">
        Ad-hoc, outside the sequence: {AD_HOC_COMMANDS.join(', ')}.
      </p>
    </div>
  )

  const retiredTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <Table headers={['Retired id', 'Replaced by', 'Why']}>
        {RETIRED.map((r, i) => (
          <tr key={r.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
            <td className={`${TD} font-mono text-[10px] text-text`}>{r.id}</td>
            <td className={`${TD} font-mono text-[10px] text-muted`}>
              {r.replaced_by.length ? r.replaced_by.join(', ') : '—'}
            </td>
            <td className={`${TD} text-muted`}>{r.reason}</td>
          </tr>
        ))}
      </Table>
      <p className="shrink-0 text-[10px] text-faint">
        Retired ids are kept, never deleted: a port or an older capture can still name one, and a reader who meets it
        needs to be told what replaced it.
      </p>
    </div>
  )

  const defectsTab = (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
        <b>These are the known-broken rows, shown on purpose.</b> The generator already computes both lists; a page
        that quietly dropped them would read as “all clear” while the defects sat in the JSON unread. A written
        exemption is not the same as a defect — where one exists it is printed in full, so the reason can be argued
        with.
      </p>
      {DEFECT_COUNT === 0 ? (
        <EmptyState
          title="No declared defects"
          hint="Both generator-computed lists are empty in the committed load-map.json."
        />
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-auto">
          <div>
            <p className="mb-1 text-[11px] font-semibold text-muted">
              Loaders with no registry source ({SOURCELESS_LOADERS.length})
            </p>
            <Table headers={['Loader', 'Class', 'Commands', 'Stated reason']}>
              {SOURCELESS_LOADERS.map((l, i) => (
                <tr key={l.name} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  <td className={`${TD} font-mono text-[10px] text-text`}>{l.name}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{l.class}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{l.commands.join(', ') || '—'}</td>
                  <td className={`${TD} text-muted`}>{l.reason}</td>
                </tr>
              ))}
            </Table>
          </div>
          <div>
            <p className="mb-1 text-[11px] font-semibold text-muted">
              Map entries whose source is unregistered ({MAP_ENTRIES_WITHOUT_SOURCE.length})
            </p>
            <Table headers={['Entry', 'Status', 'Label', 'Names source', 'Exemption']}>
              {MAP_ENTRIES_WITHOUT_SOURCE.map((e, i) => (
                <tr key={e.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  <td className={`${TD} font-mono text-[10px] text-text`}>{e.id}</td>
                  <td className={`${TD} text-muted`}>{e.status}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{e.label}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{e.source}</td>
                  <td className={`${TD} text-muted`}>{e.exemption}</td>
                </tr>
              ))}
            </Table>
          </div>
        </div>
      )}
    </div>
  )

  return (
    <ModuleTemplate
      module={loadMapModule}
      graphPane={graphPane}
      tabContent={{
        Sources: sourcesTab,
        Systems: systemsTab,
        'Load sequence': sequenceTab,
        'Retired ids': retiredTab,
        Defects: defectsTab,
      }}
    />
  )
}
