import { Link } from 'react-router-dom'
import { DEPENDENCY_MATRIX, TOWERS, type TowerKey } from '../data/towers'
import GraphSvg from './GraphSvg'

// Per-tower drill-down mock page: illustrative lineage Cypher + rendered graph,
// schema definition, anonymized row preview, inter-tower dependency matrix.
// All content synthesized (data/towers.ts). Route access is gated upstream
// (ExplorerTowerRoute's canDrill check) — this component only renders.
export default function TowerDrill({ towerKey }: { towerKey: TowerKey }) {
  const t = TOWERS[towerKey]
  return (
    <div className="wrap">
      <div className="d-bar">
        <Link className="back" to="/explorer">◀ Back to Explorer</Link>
        <h2 tabIndex={-1} data-view-heading className="outline-none">{t.title} — Example Data &amp; Dependencies</h2>
        <span className="tag">EXAMPLE DATA · ILLUSTRATIVE / ANONYMIZED</span>
        {towerKey === 'home' && (
          <Link className="btn-myapps" to="/ownership">◉ My Apps / Ownership — user view ▸</Link>
        )}
      </div>

      <div className="d-top">
        <div className="panel">
          <div className="p-head">Cypher — lineage query <span className="m">neo4j browser</span></div>
          {/* static in-repo literal (data/towers.ts), not user input */}
          <pre className="cypher" dangerouslySetInnerHTML={{ __html: t.cypherHtml }} />
        </div>
        <div className="panel">
          <div className="p-head">
            Graph result <span className="m">{t.graph.nodes.length} nodes · {t.graph.edges.length} rels</span>
          </div>
          <div className="graphbox">
            <GraphSvg graph={t.graph} ariaLabel={`${t.title} lineage graph`} />
          </div>
        </div>
      </div>

      <div className="d-grid">
        <div className="panel">
          <div className="p-head">Schema Definition <span className="m">{t.schemaName}</span></div>
          <table>
            <thead><tr><th>Column Name</th><th>Type</th></tr></thead>
            <tbody>
              {t.schema.map(([col, type]) => <tr key={col}><td>{col}</td><td>{type}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <div className="p-head">Row Preview <span className="m">{t.previewName}</span></div>
          <table>
            <thead><tr>{t.prevCols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>
              {t.preview.map((row, i) => <tr key={i}>{row.map((c, j) => <td key={j}>{c}</td>)}</tr>)}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel matrix-panel">
        <div className="p-head">Inter-Tower Dependency Matrix <span className="m">shared S3 buckets · Snowflake</span></div>
        <table className="matrix">
          <thead><tr>{DEPENDENCY_MATRIX.cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {DEPENDENCY_MATRIX.rows.map((row, i) => <tr key={i}>{row.map((c, j) => <td key={j}>{c}</td>)}</tr>)}
          </tbody>
        </table>
      </div>

      <div className="foot">
        All identifiers, row values and metrics on this page are synthesized / anonymized examples · © 2026 DryDocs
      </div>
    </div>
  )
}
