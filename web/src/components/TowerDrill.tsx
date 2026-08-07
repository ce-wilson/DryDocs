import { Link } from 'react-router-dom'
import { DEPENDENCY_MATRIX, TOWERS, type TowerKey } from '../data/towers'
import GraphSvg from './GraphSvg'

// Per-tower drill-down mock page: illustrative lineage Cypher + rendered graph,
// schema definition, anonymized row preview, inter-tower dependency matrix.
// All content synthesized (data/towers.ts). Route access is gated upstream
// (ExplorerTowerRoute's canDrill check) — this component only renders.
// O30: styled inline via Tailwind/token classes (App.css retired). The mockup's
// dark hardcodes (#c8d2de text, #0a111b code bg, the cypher syntax colors) stay
// verbatim for parity — O32 owns the light pass. The .kw/.lbl/.rel/.str spans
// live inside data/towers.ts cypherHtml literals, so they are styled from the
// <pre> via arbitrary-variant descendant selectors rather than a stylesheet.

const PANEL = 'overflow-hidden rounded-md border border-edge bg-panel'
const P_HEAD =
  'flex items-center justify-between gap-2.5 border-b border-edge bg-panel-2 px-3.5 py-2.5 text-[13.5px] font-semibold'
const P_HEAD_M = 'font-mono text-[10.5px] font-normal text-muted'
const TABLE = 'w-full border-collapse text-[12.5px]'
const TH = 'border-b border-edge bg-panel-2 px-3 py-2 text-left font-semibold text-[#c8d2de]'
const TD = 'border-b border-edge-soft px-3 py-2 font-mono text-[11.5px] text-[#b9c4d2]'
const TD_FIRST = 'border-b border-edge-soft px-3 py-2 text-[12.5px] font-medium text-text'
const TD_MATRIX = 'border-b border-edge-soft px-3 py-2 text-xs text-[#b9c4d2]'
const TD_MATRIX_FIRST = 'border-b border-edge-soft px-3 py-2 text-xs font-semibold text-text'

export default function TowerDrill({ towerKey }: { towerKey: TowerKey }) {
  const t = TOWERS[towerKey]
  return (
    <div className="mx-auto max-w-[1180px] px-[30px]">
      <div className="flex flex-wrap items-center gap-3.5 pb-4 pt-6">
        <Link
          className="rounded-sm border border-edge bg-panel px-[15px] py-2 text-[13px] font-semibold text-[#c8d2de] no-underline hover:border-faint"
          to="/explorer"
        >
          ◀ Back to Explorer
        </Link>
        <h2 tabIndex={-1} data-view-heading className="text-[21px] font-bold outline-none">{t.title} — Example Data &amp; Dependencies</h2>
        <span className="whitespace-nowrap rounded-xs border border-yellow/50 bg-yellow/8 px-[9px] py-1 font-mono text-[10.5px] font-medium text-yellow">
          EXAMPLE DATA · ILLUSTRATIVE / ANONYMIZED
        </span>
        {towerKey === 'home' && (
          <Link
            className="ml-auto rounded-sm border border-blue bg-blue/12 px-[15px] py-2 text-[13px] font-semibold text-[#9cc0f0] no-underline hover:bg-blue/25"
            to="/ownership"
          >
            ◉ My Apps / Ownership — user view ▸
          </Link>
        )}
      </div>

      <div className="mb-4 grid grid-cols-1 gap-4 min-[901px]:grid-cols-[1fr_1.15fr]">
        <div className={PANEL}>
          <div className={P_HEAD}>Cypher — lineage query <span className={P_HEAD_M}>neo4j browser</span></div>
          {/* static in-repo literal (data/towers.ts), not user input */}
          <pre
            className="min-h-[240px] overflow-x-auto bg-[#0a111b] px-[18px] py-4 font-mono text-[12.5px] leading-[1.7] text-[#d7e3f0] [&_.kw]:font-semibold [&_.kw]:text-[#7cc4ff] [&_.lbl]:text-[#8ce99a] [&_.rel]:text-[#ffb86b] [&_.str]:text-[#f1fa8c]"
            dangerouslySetInnerHTML={{ __html: t.cypherHtml }}
          />
        </div>
        <div className={PANEL}>
          <div className={P_HEAD}>
            Graph result <span className={P_HEAD_M}>{t.graph.nodes.length} nodes · {t.graph.edges.length} rels</span>
          </div>
          <div className="p-2.5">
            <GraphSvg graph={t.graph} ariaLabel={`${t.title} lineage graph`} />
          </div>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-4 min-[901px]:grid-cols-2">
        <div className={PANEL}>
          <div className={P_HEAD}>Schema Definition <span className={P_HEAD_M}>{t.schemaName}</span></div>
          <table className={TABLE}>
            <thead><tr><th className={TH}>Column Name</th><th className={TH}>Type</th></tr></thead>
            <tbody>
              {t.schema.map(([col, type]) => (
                <tr key={col}><td className={TD_FIRST}>{col}</td><td className={TD}>{type}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className={PANEL}>
          <div className={P_HEAD}>Row Preview <span className={P_HEAD_M}>{t.previewName}</span></div>
          <table className={TABLE}>
            <thead><tr>{t.prevCols.map((c) => <th key={c} className={TH}>{c}</th>)}</tr></thead>
            <tbody>
              {t.preview.map((row, i) => (
                <tr key={i}>{row.map((c, j) => <td key={j} className={j === 0 ? TD_FIRST : TD}>{c}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={`${PANEL} mb-4`}>
        <div className={P_HEAD}>Inter-Tower Dependency Matrix <span className={P_HEAD_M}>shared S3 buckets · Snowflake</span></div>
        <table className={TABLE}>
          <thead><tr>{DEPENDENCY_MATRIX.cols.map((c) => <th key={c} className={TH}>{c}</th>)}</tr></thead>
          <tbody>
            {DEPENDENCY_MATRIX.rows.map((row, i) => (
              <tr key={i}>{row.map((c, j) => <td key={j} className={j === 0 ? TD_MATRIX_FIRST : TD_MATRIX}>{c}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pb-[46px] pt-5 text-center font-mono text-[11px] text-faint">
        All identifiers, row values and metrics on this page are synthesized / anonymized examples · © 2026 DryDocs
      </div>
    </div>
  )
}
