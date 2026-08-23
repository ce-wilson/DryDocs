import { useEffect, useMemo, useState } from 'react'
import { MODULES } from '../modules/registry'
import ModuleTemplate from './ModuleTemplate'
import MiniDag, { type DagEdgeDef, type DagNodeDef } from '../components/MiniDag'
import StatTiles from '../components/StatTiles'
import EmptyState from '../components/ui/EmptyState'
import type { Persona } from '../lib/auth'
import { createApiAccess } from '../lib/graphApi'
import VendorIcon from '../software/VendorIcon'
import {
  ACRONYMS,
  COVERAGE_STATS,
  DRYDOCS_APPLICATION_ID,
  PRODUCTS,
  VENDOR_BY_ID,
  VENDORS,
  VENDORS_WITHOUT_ICONS,
  corpusOf,
  currency,
  edgeState,
  gateState,
  inGraphLabel,
  relationship,
  unclaimedCorpora,
  type Product,
} from '../software/softwareModel'

// /software (Q16) — READ-ONLY ledger view of vendor -> product -> corpus -> graph.
// Static generated JSON (software-registry.json + the doc-corpus rows of
// load-map.json), plus ONE live spec for the in-graph column.
//
// NOT a corpus browser — that is /docs. What is missing from the console is the
// JOIN: a registry without the docs column is a vendor list, and a corpus list
// without the product column is a file inventory. The intersections are the only
// interesting cells.

const softwareModule = MODULES.find((m) => m.id === 'software')!

function edgeChip(state: ReturnType<typeof edgeState>): { text: string; token: string } {
  switch (state) {
    case 'withheld-cross-db':
      // A RULING, not a gap — never red. vendor_docs.cypher withholds this edge
      // deliberately: a relationship cannot span Neo4j databases.
      return { text: 'withheld by design (G32)', token: '--teal' }
    case 'unregistered-corpus':
      return { text: 'corpus not registered', token: '--red' }
    case 'no-corpus':
      return { text: 'no corpus declared', token: '--faint' }
    default:
      return { text: 'possible', token: '--green' }
  }
}

export default function SoftwareRoute({ persona }: { persona: Persona }) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [live, setLive] = useState<Map<string, number> | null>(null)

  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
  const access = useMemo(() => createApiAccess(apiUrl, persona.id), [apiUrl, persona.id])

  useEffect(() => {
    let cancelled = false
    access
      .runSpec('software.doc-coverage.v1')
      .then((r: { rows: unknown[] }) => {
        if (cancelled || !r.rows.length) return
        const counts = new Map<string, number>()
        for (const row of r.rows as unknown as { product_id: string; documents: number }[]) {
          counts.set(row.product_id, Number(row.documents ?? 0))
        }
        setLive(counts)
      })
      .catch(() => {
        /* declaration-only view; the banner says so */
      })
    return () => {
      cancelled = true
    }
  }, [access])

  const selected = PRODUCTS.find((p) => p.id === selectedId) ?? null

  const { nodes, edges } = useMemo(() => {
    if (!selected) return { nodes: [] as DagNodeDef[], edges: [] as DagEdgeDef[] }
    const vendor = VENDOR_BY_ID.get(selected.vendor)
    const corpus = corpusOf(selected)
    const chip = edgeChip(edgeState(selected))
    const nodes: DagNodeDef[] = [
      { id: 'vendor', label: vendor?.name ?? selected.vendor, sub: 'Vendor', token: '--blue', x: 0, y: 0 },
      { id: 'product', label: selected.name, sub: 'SoftwareProduct', token: '--green', x: 300, y: 0 },
    ]
    const edges: DagEdgeDef[] = [
      { id: 'e-made-by', source: 'product', target: 'vendor', label: 'MADE_BY' },
    ]
    if (corpus) {
      nodes.push({
        id: 'corpus',
        label: corpus.id,
        sub: `corpus · ${corpus.target_db ?? 'no target_db'}`,
        token: chip.token,
        x: 600,
        y: 0,
        flag: chip.text,
      } as DagNodeDef)
      edges.push({ id: 'e-describes', source: 'corpus', target: 'product', label: `DESCRIBES · ${chip.text}` })
    }
    return { nodes, edges }
  }, [selected])

  const banner = (
    <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
      <b>Nothing on this page is red by accident.</b> Every gap below is a recorded ruling — a gate awaiting an
      SME, a corpus with no connector built, or an edge deliberately withheld pending the G32 database-residency
      ruling. <b>DECLARED</b> is what config/ says; <b>IN GRAPH</b> is what the drydocs database holds right now.
      They differ on purpose. {live ? '' : 'The in-graph column is unavailable (needs drydocs-api) — it reads “not queried”, never 0.'}
    </p>
  )

  const productsTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      {banner}
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['Product', 'Vendor', 'Category', 'Versions', 'Relationship', 'Docs declared', 'In graph'].map((h) => (
                <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PRODUCTS.map((p: Product, i: number) => {
              const graph = inGraphLabel(p, live)
              return (
                <tr
                  key={p.id}
                  onClick={() => setSelectedId(selectedId === p.id ? null : p.id)}
                  className={
                    'cursor-pointer ' +
                    (selectedId === p.id ? 'bg-panel-2' : i % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                  }
                >
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{p.name}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5">
                    <span className="flex items-center gap-1.5">
                      <VendorIcon vendor={VENDOR_BY_ID.get(p.vendor)} />
                      <span className="text-muted">{VENDOR_BY_ID.get(p.vendor)?.name ?? p.vendor}</span>
                    </span>
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{p.category ?? '—'}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {p.versions.join(', ') || '—'}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{relationship(p)}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {p.documentation?.corpus ?? '—'}
                  </td>
                  <td
                    className={
                      'border-b border-edge-soft px-2.5 py-1.5 text-[10px] ' +
                      (graph.numeric ? 'font-mono tabular-nums text-text' : 'text-faint')
                    }
                  >
                    {graph.text}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="shrink-0 text-[10px] text-faint">
        Snowflake is absent from this table by construction — it is a registered SOURCE system but has no
        software-registry product row. <code>drydocs docs-coverage</code> lists every such system.
        {DRYDOCS_APPLICATION_ID ? ` · self: ${DRYDOCS_APPLICATION_ID}` : ''}
        {Object.keys(ACRONYMS).length
          ? ` · ${Object.entries(ACRONYMS).map(([k, v]) => `${k}: ${v}`).join(' · ')}`
          : ''}
      </p>
    </div>
  )

  const vendorsTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['', 'Vendor', 'Publisher', 'Products', 'Icon provenance'].map((h) => (
                <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {VENDORS.map((v, i) => (
              <tr key={v.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
                <td className="border-b border-edge-soft px-2.5 py-1.5">
                  <VendorIcon vendor={v} size={20} />
                </td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{v.name}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                  {v.publisher_url ? (
                    <a href={v.publisher_url} target="_blank" rel="noreferrer" className="underline">
                      {v.publisher_url}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">
                  {PRODUCTS.filter((p) => p.vendor === v.id).map((p) => p.id).join(', ') || '—'}
                </td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-faint">
                  {v.icon ? `${v.icon.source} · verified: ${v.icon.verified}` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2 py-1 text-[11px] text-muted">
        <b>{VENDORS_WITHOUT_ICONS.length} of {VENDORS.length} vendors have no manifest icon</b> — reported, never
        silent, never an error: {VENDORS_WITHOUT_ICONS.join(', ')}.
      </p>
    </div>
  )

  const coverageTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      {banner}
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['Product', 'Corpus', 'Declared via', 'Gate', 'Product edge', 'Target DB', 'In graph', 'Docs vs runtime'].map(
                (h) => (
                  <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {PRODUCTS.filter((p) => p.documentation).map((p, i) => {
              const corpus = corpusOf(p)
              const chip = edgeChip(edgeState(p))
              const cur = currency(p)
              const graph = inGraphLabel(p, live)
              return (
                <tr key={p.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-text">{p.name}</td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px]">
                    {p.documentation!.corpus}
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 text-[10px] text-muted">
                    product.documentation
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5">
                    <span
                      className="rounded border px-1.5 py-0.5 font-mono text-[10px]"
                      style={{
                        borderColor: gateState(p) === 'confirmed' ? 'var(--green)' : 'var(--yellow)',
                        color: gateState(p) === 'confirmed' ? 'var(--green)' : 'var(--yellow)',
                      }}
                    >
                      {gateState(p)}
                    </span>
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5">
                    {/* INDEPENDENT of the gate chip: a corpus can be both
                        gate-blocked AND permanently edge-less, and one chip would
                        imply that signing the gate produces coverage. */}
                    <span
                      className="rounded border px-1.5 py-0.5 font-mono text-[10px]"
                      style={{ borderColor: `var(${chip.token})`, color: `var(${chip.token})` }}
                    >
                      {chip.text}
                    </span>
                  </td>
                  <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                    {corpus?.target_db ?? '—'}
                  </td>
                  <td
                    className={
                      'border-b border-edge-soft px-2.5 py-1.5 text-[10px] ' +
                      (graph.numeric ? 'font-mono tabular-nums text-text' : 'text-faint')
                    }
                  >
                    {graph.text}
                  </td>
                  <td
                    className="border-b border-edge-soft px-2.5 py-1.5 text-[10px]"
                    style={{ color: cur.drifted ? 'var(--yellow)' : 'var(--muted)' }}
                  >
                    {cur.label}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="shrink-0 text-[10px] text-faint">
        Only products carrying a <code>documentation:</code> block appear here — one of {PRODUCTS.length} today.
        Run <code>drydocs docs-coverage</code> for the full picture, including every product with no documentation
        at all, the corpora no product declares, and any DESCRIBES edge with no declaration behind it.
      </p>
    </div>
  )

  const corporaTab = (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['Corpus', 'Tier', 'Curation', 'Trust', 'Classification', 'Connector', 'Target DB', 'Gate', 'Locator'].map(
                (h) => (
                  <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {unclaimedCorpora().map((c, i) => (
              <tr key={c.id} className={i % 2 ? 'bg-bg-2/40' : ''}>
                <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-text">{c.id}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{c.tier ?? '—'}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{c.curation ?? '—'}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{c.trust_default ?? '—'}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{c.classification ?? '—'}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-muted">{c.connector ?? '—'}</td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 font-mono text-[10px] text-muted">
                  {c.target_db ?? '—'}
                </td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-[10px] text-muted">
                  {c.confirmed ? 'confirmed' : 'awaiting gate'}
                </td>
                <td className="border-b border-edge-soft px-2.5 py-1.5 text-[10px] text-faint">
                  {c.graph_locator?.match === 'none'
                    ? 'not on the lexical backbone — by ruling'
                    : (c.graph_locator?.match ?? '—')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="shrink-0 text-[10px] text-faint">
        These corpora are named by no product's <code>documentation:</code> block. That is a config gap, not a
        derivation to make here: no file maps a corpus's taxonomy path to a product id.
      </p>
    </div>
  )

  return (
    <ModuleTemplate
      module={softwareModule}
      selection={selected?.name}
      toolbarActions={
        <span className="font-mono text-[10px] text-faint" title="read-only ledger">
          read-only ledger — corpora load through the gate flow, never here
        </span>
      }
      graphPane={
        <div className="flex h-full min-h-0 flex-col gap-3">
          <StatTiles
            tiles={[
              { value: String(COVERAGE_STATS.products), label: 'Products' },
              { value: String(COVERAGE_STATS.vendors), label: 'Vendors' },
              {
                value: `${COVERAGE_STATS.vendorsWithIcons}/${COVERAGE_STATS.vendors}`,
                label: 'Vendor icons',
              },
              { value: String(COVERAGE_STATS.corpora), label: 'Doc corpora' },
              { value: String(COVERAGE_STATS.corporaAwaitingGate), label: 'Awaiting gate' },
              {
                value: `${COVERAGE_STATS.productsWithDocs}/${COVERAGE_STATS.products}`,
                label: 'Docs declared',
              },
            ]}
          />
          <div className="min-h-0 flex-1">
            {selected ? (
              <MiniDag
                nodes={nodes}
                edges={edges}
                title={`Declared chain — ${selected.name}`}
                badge="GENERATED from software-registry.json + the doc corpora — DECLARED links only; the in-graph column is live"
                selectedId={null}
                onSelect={() => {}}
              />
            ) : (
              <EmptyState
                title="Select a product"
                hint={`${COVERAGE_STATS.products} products, ${COVERAGE_STATS.productsWithDocs} with a documentation pointer. Click a row to see its declared vendor → product → corpus chain.`}
              />
            )}
          </div>
        </div>
      }
      tabContent={{
        Products: productsTab,
        Vendors: vendorsTab,
        'Documentation coverage': coverageTab,
        Corpora: corporaTab,
      }}
    />
  )
}
