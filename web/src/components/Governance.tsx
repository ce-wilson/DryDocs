const TILES = ['Audit Log', 'Compliance Status', 'Risk Score']

// Admin-only static placeholder (the gemini wireframe's Posture & Governance
// panel). Inert until governance data lands in the graph.
export default function Governance() {
  return (
    <main>
      <div className="view-head">
        <h1>Posture &amp; Governance</h1>
        <span className="tag">PLACEHOLDER · SYNTHESIZED</span>
      </div>
      <div className="gov-tiles">
        {TILES.map((label) => (
          <div key={label} className="gov-tile">
            <div className="gov-value">—</div>
            <div className="gov-label">{label}</div>
            <div className="gov-hint">populated when governance data lands in the graph</div>
          </div>
        ))}
      </div>
    </main>
  )
}
