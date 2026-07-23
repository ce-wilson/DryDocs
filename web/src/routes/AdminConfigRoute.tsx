import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Link } from 'react-router-dom'
import type { ModuleDef } from '../modules/registry'
import { useRightSidebar } from '../layout/rightSidebarContext'
import ModuleTemplate from './ModuleTemplate'
import EmptyState from '../components/ui/EmptyState'
import matrix from '../generated/enforcement-matrix.json'

// /admin/config (O12): the config-as-code TRACEABILITY LENS. NO edit controls
// anywhere — config edits travel repo + gate flow; this page shows what is
// configured, which code consumes it, which test enforces it, which gate
// approved it. Data = the GENERATED enforcement-matrix.json artifact
// (scripts/render_enforcement_matrix.py; test_enforcement_matrix.py is the
// drift guard — the matrix cannot drift from the repo).

interface Surface {
  id: string
  title: string
  file: string
  code_resident: boolean
  consumers: string[]
  guard_tests: string[]
  gate_ref: string | null
  status: 'enforced' | 'unguarded' | 'gate-pending'
  pending_entries: number
  env_refs: string[]
  files: string[]
  content: string | null
  extra_contents: Record<string, string>
}

const SURFACES = matrix.surfaces as Surface[]
const CI_NOTE: string | null = (matrix as { ci_note: string | null }).ci_note
const CI_LAST_RUN = (matrix as { ci_last_run: Record<string, unknown> | null }).ci_last_run

const adminModule: ModuleDef = {
  id: 'admin-config',
  label: 'Configuration',
  path: '/admin/config',
  tagline: 'Config-as-code traceability lens · read-only — edits stay behind the gates',
  backsOnto: 'enforcement-matrix.json (generated)',
  tabs: ['Enforcement matrix', 'Surface detail', 'Gate log'],
  phase: 3,
}

type ChainNodeData = { label: string; role: string; token: string }
type ChainRFNode = Node<ChainNodeData, 'chain'>

function ChainNode({ data }: NodeProps<ChainRFNode>) {
  return (
    <div
      className="rf-node max-w-52 rounded-md border-2 bg-panel px-2.5 py-1.5 text-center shadow-sm"
      style={{ borderColor: `var(${data.token})`, '--rf-glow': `var(${data.token})` } as CSSProperties}
    >
      <Handle type="target" position={Position.Left} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
      <div className="break-all text-[11px] font-semibold text-text">{data.label}</div>
      <div className="font-mono text-[10px]" style={{ color: `var(${data.token})` }}>
        {data.role}
      </div>
      <Handle type="source" position={Position.Right} className="!h-1.5 !w-1.5 !border-0 !bg-transparent" />
    </div>
  )
}

const nodeTypes = { chain: ChainNode }

function chainGraph(s: Surface): { nodes: ChainRFNode[]; edges: Edge[] } {
  const nodes: ChainRFNode[] = []
  const edges: Edge[] = []
  const edge = (id: string, source: string, target: string): Edge => ({
    id,
    source,
    target,
    style: { stroke: 'var(--faint)', strokeWidth: 1.4 },
    markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--faint)', width: 14, height: 14 },
  })

  nodes.push({
    id: 'file',
    type: 'chain',
    position: { x: 0, y: 40 },
    data: {
      label: s.file,
      role: s.code_resident ? 'code-resident (the migration argument)' : 'config file',
      token: s.code_resident ? '--red' : '--blue',
    },
  })
  s.consumers.forEach((c, i) => {
    const id = `consumer-${i}`
    nodes.push({ id, type: 'chain', position: { x: 260, y: i * 90 }, data: { label: c, role: 'code consumer', token: '--yellow' } })
    edges.push(edge(`e-file-${id}`, 'file', id))
  })
  if (s.guard_tests.length === 0) {
    nodes.push({ id: 'no-guard', type: 'chain', position: { x: 520, y: 40 }, data: { label: 'NO GUARD TEST', role: 'unguarded — the page KPI', token: '--red' } })
    s.consumers.forEach((_, i) => edges.push(edge(`e-c${i}-ng`, `consumer-${i}`, 'no-guard')))
  }
  s.guard_tests.forEach((t, i) => {
    const id = `test-${i}`
    nodes.push({ id, type: 'chain', position: { x: 520, y: i * 90 }, data: { label: `tests/unit/${t}`, role: 'guard test', token: '--green' } })
    s.consumers.forEach((_, j) => edges.push(edge(`e-c${j}-${id}`, `consumer-${j}`, id)))
  })
  nodes.push({
    id: 'gate',
    type: 'chain',
    position: { x: 780, y: 40 },
    data: { label: s.gate_ref ?? 'no gate reference', role: 'gate', token: s.gate_ref ? '--teal' : '--faint' },
  })
  const lastCol = s.guard_tests.length ? s.guard_tests.map((_, i) => `test-${i}`) : ['no-guard']
  lastCol.forEach((id, i) => edges.push(edge(`e-${id}-gate-${i}`, id, 'gate')))
  return { nodes, edges }
}

function StatusChip({ status, pending }: { status: Surface['status']; pending: number }) {
  const cls =
    status === 'enforced'
      ? 'border-green/60 text-green'
      : status === 'unguarded'
        ? 'border-red/60 text-brand-soft'
        : 'border-yellow/60 text-yellow'
  return (
    <span className={`whitespace-nowrap rounded border px-1.5 py-0.5 font-mono text-[10px] ${cls}`}>
      {status}
      {status === 'gate-pending' && ` (${pending})`}
    </span>
  )
}

export default function AdminConfigRoute() {
  const [selectedId, setSelectedId] = useState(SURFACES[0].id)
  const selected = SURFACES.find((s) => s.id === selectedId)!
  const sidebar = useRightSidebar()

  const { nodes, edges } = useMemo(() => chainGraph(selected), [selected])

  useEffect(() => {
    sidebar.set(<SurfaceInspector s={selected} />)
    return () => sidebar.clear()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected])

  const gateLog = SURFACES.find((s) => s.id === 'gate-record')?.extra_contents['config/gate-log.md']

  return (
    <ModuleTemplate
      module={adminModule}
      selection={selected.title}
      toolbarActions={
        <span className="font-mono text-[10px] text-faint" title="wf-admin-config-01: edit = repo path + gate flow">
          read-only — no edit controls by design
        </span>
      }
      graphPane={
        <div className="flex h-full min-h-0 flex-col">
          <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-edge-soft px-3 py-2">
            <span className="text-xs font-medium text-muted">
              Traceability chain — {selected.title}
            </span>
            <span className="ml-auto font-mono text-[10px] text-faint">
              config file → consumer(s) → guard test(s) → gate
            </span>
          </div>
          <div className="min-h-0 flex-1 bg-bg-2">
            <ReactFlow
              key={selected.id}
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.15 }}
              nodesDraggable={false}
              nodesConnectable={false}
              edgesFocusable={false}
              minZoom={0.3}
              maxZoom={2}
            >
              <Background color="var(--edge)" gap={22} />
              <Controls showInteractive={false} />
            </ReactFlow>
          </div>
        </div>
      }
      tabContent={{
        'Enforcement matrix': (
          <div className="flex h-full min-h-0 flex-col gap-1.5">
            <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
              GENERATED — scripts/render_enforcement_matrix.py; test_enforcement_matrix.py guards drift.{' '}
              {CI_LAST_RUN
                ? `CI last run: ${JSON.stringify(CI_LAST_RUN)}`
                : CI_NOTE}
            </p>
            <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
              <table className="w-full border-collapse text-left text-[11px]">
                <thead className="sticky top-0 bg-panel-2">
                  <tr>
                    {['Surface', 'File', 'Consumers', 'Guard tests', 'Env refs', 'Gate', 'Status'].map((h) => (
                      <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SURFACES.map((s, i) => (
                    <tr
                      key={s.id}
                      onClick={() => setSelectedId(s.id)}
                      className={
                        'cursor-pointer ' +
                        (s.id === selectedId ? 'bg-panel-2' : i % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                      }
                    >
                      <td className="border-b border-edge-soft px-2.5 py-1.5 font-medium text-text">{s.title}</td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                        {s.code_resident ? `${s.file} (code-resident)` : s.file}
                      </td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                        {s.consumers.join(', ')}
                      </td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                        {s.guard_tests.length ? s.guard_tests.join(', ') : '—'}
                      </td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                        {s.env_refs.length ? s.env_refs.join(', ') : '—'}
                      </td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5 text-[10px] text-muted">
                        {s.gate_ref ?? '—'}
                      </td>
                      <td className="border-b border-edge-soft px-2.5 py-1.5">
                        <StatusChip status={s.status} pending={s.pending_entries} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ),
        'Surface detail': (
          <div className="flex h-full min-h-0 flex-col gap-1.5">
            <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
              {selected.title} · rendered VERBATIM (secrets are .env-only — config carries env-var references, never
              values) · read-only
            </p>
            {selected.content ? (
              <pre className="min-h-0 flex-1 overflow-auto rounded-md border border-edge bg-bg-2/40 p-3 font-mono text-[11px] leading-relaxed text-text">
                {selected.content}
              </pre>
            ) : (
              <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge p-3">
                <p className="mb-1.5 text-[11px] font-medium text-muted">
                  Directory surface — {selected.files.length} file{selected.files.length === 1 ? '' : 's'}:
                </p>
                <ul className="space-y-0.5 font-mono text-[11px] text-text">
                  {selected.files.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ),
        'Gate log': gateLog ? (
          <pre className="h-full overflow-auto rounded-md border border-edge bg-bg-2/40 p-3 font-mono text-[11px] leading-relaxed text-text">
            {gateLog}
          </pre>
        ) : (
          <EmptyState title="Gate log unavailable" hint="config/gate-log.md missing from the generated matrix." />
        ),
      }}
    />
  )
}

function SurfaceInspector({ s }: { s: Surface }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="flex flex-col gap-2 p-3 text-xs">
      <h3 className="font-semibold text-text">{s.title}</h3>
      <dl className="space-y-1.5">
        <InspectorRow k="path" v={s.file} mono />
        <InspectorRow k="status" v={`${s.status}${s.pending_entries ? ` · ${s.pending_entries} pending` : ''}`} />
        <InspectorRow k="files" v={String(s.files.length)} />
        <InspectorRow k="env refs" v={s.env_refs.length ? s.env_refs.join(', ') : 'none'} mono />
        <InspectorRow k="gate" v={s.gate_ref ?? 'none recorded'} />
      </dl>
      <div className="mt-1 flex flex-col gap-1">
        <button
          type="button"
          onClick={() => navigator.clipboard.writeText(s.file).then(() => setCopied(true), () => setCopied(false))}
          className="rounded-md border border-edge bg-bg-2 px-2 py-1 text-left text-[11px] font-medium text-muted hover:text-text"
        >
          {copied ? 'repo path copied ✓' : 'copy repo path'}
        </button>
        <Link
          to="/gates"
          className="rounded-md border border-edge bg-bg-2 px-2 py-1 text-[11px] font-medium text-muted no-underline hover:text-text"
        >
          gate flow → /gates
        </Link>
      </div>
      <p className="mt-1 text-[10px] text-faint">
        Edits happen in the repo + gate flow — this console never writes config.
      </p>
    </div>
  )
}

function InspectorRow({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wide text-faint">{k}</dt>
      <dd className={'text-[11px] text-text ' + (mono ? 'break-all font-mono' : '')}>{v}</dd>
    </div>
  )
}
