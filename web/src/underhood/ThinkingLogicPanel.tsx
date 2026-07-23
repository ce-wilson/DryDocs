// The "why does this work the way it does" panel (explainer §5/§6): the
// graph-only questions, the paraphrase gap + its mitigation hierarchy, and
// vectors as the named-but-not-yet-built fourth arm.
const GRAPH_ONLY = [
  { id: 'SA1', label: 'Corpus structure', detail: '"largest document?" — no file lists its own rank; the graph counts.' },
  { id: 'SA2', label: 'Aggregation', detail: '"how much is SYNTHESIZED?" — trust tier is a per-chunk property; files never tally it.' },
  { id: 'MD2', label: 'Version property', detail: 'target_version (9.0.21.300) is a graph edge property, not prose to re-parse.' },
  { id: 'PV1', label: 'Per-chunk provenance', detail: '"is this example ground truth?" — filter by provenance=SYNTHESIZED, a property, not a rule of thumb.' },
] as const

const MITIGATION_STEPS = [
  { step: '1. Term mapping', detail: 'the graph carries its own :SchemaMeta / :OntologyTerm inventory the agent consults before querying — "wait for another job" → prerequisite condition.' },
  { step: '2. Full-text backup', detail: 'if a mapped term still misses, the standing keyless Lucene index catches most exact/easy-paraphrase lookups.' },
  { step: '3. Vectors when the key lands', detail: 'embeddings retrieve by meaning, not keyword — the named missing arm, gated on an approved embedding key (not core-path today).' },
] as const

export default function ThinkingLogicPanel() {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <div className="rounded-lg border border-edge bg-panel p-4">
        <h3 className="text-sm font-semibold text-text">Four questions only the graph could answer</h3>
        <ul className="mt-2.5 flex flex-col gap-2.5">
          {GRAPH_ONLY.map((g) => (
            <li key={g.id} className="border-b border-edge-soft pb-2 last:border-0 last:pb-0">
              <span className="font-mono text-[10.5px] text-teal">{g.id}</span>{' '}
              <span className="text-xs font-semibold text-text">{g.label}</span>
              <p className="mt-0.5 text-[11px] leading-relaxed text-muted">{g.detail}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border border-edge bg-panel p-4">
        <h3 className="text-sm font-semibold text-text">The paraphrase gap + mitigation hierarchy</h3>
        <p className="mt-1.5 text-[11px] leading-relaxed text-muted">
          Support asks &ldquo;make a job wait for another job&rdquo;; the docs say <em>prerequisite condition</em>.
          Naive keyword matching inside Cypher misses this — the graph is only as good as the query layer in
          front of it.
        </p>
        <ol className="mt-2.5 flex flex-col gap-2">
          {MITIGATION_STEPS.map((m) => (
            <li key={m.step} className="rounded-md border border-edge-soft bg-bg-2 p-2">
              <span className="text-xs font-semibold text-blue-bright">{m.step}</span>
              <p className="mt-0.5 text-[11px] leading-relaxed text-muted">{m.detail}</p>
            </li>
          ))}
        </ol>
        <p className="mt-2.5 rounded-md border border-yellow/40 bg-yellow/10 p-2 text-[11px] leading-relaxed text-yellow">
          Vectors&rsquo; own risk: vector search <em>always</em> returns nearest neighbors, even for
          questions the corpus can&rsquo;t answer — so the OS1 abstention behavior needs an explicit
          score threshold once vectors are pluggable, not a free win.
        </p>
      </div>
    </div>
  )
}
