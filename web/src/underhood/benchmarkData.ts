// FIXTURE DATA · from committed benchmark record (same honesty-tag idiom used
// across the console — see docsmod/demoDocs.ts's NOTICE strings). Every
// number below is a verbatim transcription of the 2026-07-16 live benchmark
// verdict — nothing here is invented or estimated:
//   docs/design/graph-retrieval-benchmark-explainer.md (Rev 2, commit 0e036ff)
//   knowledge/upgrade-plans/docmeta-p0-verdict.md (the scoring tables)
//
// "Under the Hood" (/under-the-hood) renders this fixture as a benchmark
// showcase — how the DryDocs agent could retrieve knowledge three different
// ways, and the live test that decided BUILD over shrink-to-registry-only.

export type StrategyId = 'manifest' | 'fulltext' | 'traversal'

export interface StrategyInfo {
  id: StrategyId
  label: string
  /** the mono kicker shown on the strategy card, e.g. "unstructured files" */
  kicker: string
  how: string
  recall: string
  tokens: string
  latency: string
  failureModes: string
  /** css custom-property token name (no leading `var()`), e.g. '--yellow' */
  token: string
}

export const STRATEGIES: readonly StrategyInfo[] = [
  {
    id: 'manifest',
    label: 'Manifest-routed reading',
    kicker: 'unstructured files · human index',
    how: 'Read the human-maintained SOURCE-MANIFEST, pick the likely file(s), read them whole.',
    recall: '10/12 (2 partial)',
    tokens: '≈449,500 ch (~112.4k tok)',
    latency: '~instant to route, then whole files to read',
    failureModes: 'Aggregation/provenance questions come back as "the rule says…", not numbers — the tally lives nowhere.',
    token: '--yellow',
  },
  {
    id: 'fulltext',
    label: 'Full-text search',
    kicker: 'indexed chunks · Lucene top-3',
    how: 'Keyword index over chunk heading/text (Neo4j’s built-in Lucene index); return the top-3 matches.',
    recall: '7/12',
    tokens: '≈31,400 ch (~7.9k tok)',
    latency: '12ms median',
    failureModes: 'Ranking dilution, the paraphrase gap, and confident noise on out-of-scope questions (the worst failure mode).',
    token: '--blue-br',
  },
  {
    id: 'traversal',
    label: 'Graph traversal',
    kicker: 'structured lexical graph · Cypher',
    how: 'Document→Chunk graph with trust tiers as properties; fetch or compute over exactly the chunks that answer the question.',
    recall: '12/12',
    tokens: '≈16,400 ch (~4.1k tok)',
    latency: '75ms median',
    failureModes: 'Query quality: naive keyword phrasing misses paraphrased questions until support vocabulary is mapped to document vocabulary.',
    token: '--green',
  },
]

export const CORPUS = {
  docCount: 26,
  label: '26 Control-M docs + manifest',
  totalChars: 313_350,
  chunkCount: 374,
  tiers: [
    { tier: 'GROUNDED', chunks: 257, chars: 194_516, token: '--blue-br' },
    { tier: 'SYNTHESIZED', chunks: 115, chars: 100_310, token: '--yellow' },
    { tier: 'VERBATIM', chunks: 2, chars: 7_597, token: '--green' },
  ],
} as const

export const TOTALS = {
  traversal: { chars: 16_400, tokens: '~4.1k', recall: '12/12', latencyMedianMs: 75 },
  fulltext: { chars: 31_400, tokens: '~7.9k', recall: '7/12', latencyMedianMs: 12 },
  manifest: { chars: 449_500, tokens: '~112.4k', recall: '10/12 (2 partial)', latencyLabel: 'routing ~instant' },
} as const

export const EFFICIENCY = {
  headline: '27.4×',
  label: 'manifest-vs-traversal token efficiency',
  perQuestionRange: '28×–60×',
} as const

export type ResultKind = 'pass' | 'fail' | 'partial' | 'abstain' | 'hallucination'

export interface StrategyResult {
  kind: ResultKind
  /** characters retrieved/ingested for this question, this strategy */
  chars: number
  ms?: number
  /** e.g. "informed" — naive phrasing failed, domain-mapped terms succeeded */
  qualifier?: string
}

export type QuestionClass =
  | 'structure/aggregation'
  | 'exact lookup'
  | 'paraphrase'
  | 'multi-doc'
  | 'provenance'
  | 'out-of-scope'

export const CLASS_TOKEN: Record<QuestionClass, string> = {
  'structure/aggregation': '--teal',
  'exact lookup': '--blue-br',
  paraphrase: '--yellow',
  'multi-doc': '--green',
  provenance: '--red',
  'out-of-scope': '--faint',
}

export interface CypherSnippet {
  label: string
  code: string
}

export interface BenchmarkQuestion {
  id: string
  cls: QuestionClass
  text: string
  traversal: StrategyResult
  fulltext: StrategyResult
  manifest: StrategyResult
  note: string
  cypher?: readonly CypherSnippet[]
}

export const QUESTIONS: readonly BenchmarkQuestion[] = [
  {
    id: 'SA1',
    cls: 'structure/aggregation',
    text: 'How many documents are in the corpus, and which has the most content?',
    traversal: { kind: 'pass', chars: 67, ms: 110 },
    fulltext: { kind: 'fail', chars: 2079, ms: 149 },
    manifest: { kind: 'pass', chars: 75_940 },
    note: 'graph-only: aggregation over doc/chunk properties; manifest = read SOURCE-MANIFEST + hand count',
  },
  {
    id: 'SA2',
    cls: 'structure/aggregation',
    text: 'How much of the corpus is Claude inference (SYNTHESIZED) vs vendor-grounded?',
    traversal: { kind: 'pass', chars: 179, ms: 49 },
    fulltext: { kind: 'fail', chars: 2700, ms: 13 },
    manifest: { kind: 'partial', chars: 0, qualifier: 'rule only' },
    note: "graph-only: provenance is a per-chunk property; files don't record the tally anywhere",
    cypher: [
      {
        label: 'traversal — aggregation',
        code:
          'MATCH (c:Chunk)\n' +
          'RETURN c.provenance AS tier, count(*) AS chunks, sum(c.char_count) AS chars\n' +
          'ORDER BY chars DESC',
      },
    ],
  },
  {
    id: 'EL1',
    cls: 'exact lookup',
    text: 'What is %%LIBMEMSYM?',
    traversal: { kind: 'pass', chars: 3526, ms: 52 },
    fulltext: { kind: 'pass', chars: 3548, ms: 46 },
    manifest: { kind: 'pass', chars: 20_842 },
    note: 'manifest reads entire controlm-variables.md for one definition',
    cypher: [
      {
        label: 'traversal — CONTAINS lookup',
        code: "MATCH (c:Chunk)\nWHERE c.text CONTAINS '%%LIBMEMSYM'\nRETURN c.heading, c.text",
      },
      {
        label: 'full-text — top-3',
        code:
          "CALL db.index.fulltext.queryNodes('p0_chunk_ft', 'LIBMEMSYM')\n" +
          'YIELD node, score\n' +
          'RETURN node.heading, node.text, score\n' +
          'ORDER BY score DESC\n' +
          'LIMIT 3',
      },
    ],
  },
  {
    id: 'EL2',
    cls: 'exact lookup',
    text: 'What does the ctmcreate utility do?',
    traversal: { kind: 'pass', chars: 1312, ms: 20 },
    fulltext: { kind: 'fail', chars: 3125, ms: 8 },
    manifest: { kind: 'pass', chars: 7850 },
    note: "full-text ranking dilution: 'utility'-dense chunk outranked the rare term ctmcreate",
  },
  {
    id: 'EL3',
    cls: 'exact lookup',
    text: 'What does ODAT mean?',
    traversal: { kind: 'pass', chars: 1750, ms: 76 },
    fulltext: { kind: 'pass', chars: 4042, ms: 9 },
    manifest: { kind: 'pass', chars: 20_842 },
    note: '—',
  },
  {
    id: 'PC1',
    cls: 'paraphrase',
    text: 'How do I make one job wait for another job to finish before it runs?',
    traversal: { kind: 'pass', chars: 1309, ms: 49, qualifier: 'informed' },
    fulltext: { kind: 'fail', chars: 1539, ms: 12 },
    manifest: { kind: 'pass', chars: 12_100 },
    note: "naive traversal ('wait for another job') → 0 rows; informed ('prerequisite condition') → correct. The paraphrase gap.",
    cypher: [
      {
        label: 'traversal — naive (0 rows)',
        code: "MATCH (c:Chunk)\nWHERE c.text CONTAINS 'wait for another job'\nRETURN c.heading, c.text",
      },
      {
        label: 'traversal — informed (correct)',
        code: "MATCH (c:Chunk)\nWHERE c.text CONTAINS 'prerequisite condition'\nRETURN c.heading, c.text",
      },
    ],
  },
  {
    id: 'PC2',
    cls: 'paraphrase',
    text: 'Can a job start automatically when a file arrives?',
    traversal: { kind: 'pass', chars: 2086, ms: 75, qualifier: 'informed' },
    fulltext: { kind: 'pass', chars: 2503, ms: 9 },
    manifest: { kind: 'pass', chars: 13_702 },
    note: "naive → 0 rows; informed ('file watcher') → correct",
  },
  {
    id: 'PC3',
    cls: 'paraphrase',
    text: 'How do I keep jobs from running on holidays?',
    traversal: { kind: 'pass', chars: 2118, ms: 75 },
    fulltext: { kind: 'pass', chars: 2029, ms: 11 },
    manifest: { kind: 'pass', chars: 20_271 },
    note: '—',
  },
  {
    id: 'MD1',
    cls: 'multi-doc',
    text: 'Which docs cover pool variables, and how do they relate to %% user variables?',
    traversal: { kind: 'pass', chars: 446, ms: 109 },
    fulltext: { kind: 'pass', chars: 3039, ms: 8 },
    manifest: { kind: 'pass', chars: 43_853 },
    note: "hand-adjudicated: mechanical scorer missed marker in traversal's 446-char structural answer; 3 whole files for manifest",
  },
  {
    id: 'MD2',
    cls: 'multi-doc',
    text: 'Which Control-M version do these docs target, and is the Automation API compatible with it?',
    traversal: { kind: 'pass', chars: 1506, ms: 98 },
    fulltext: { kind: 'pass', chars: 3080, ms: 12 },
    manifest: { kind: 'pass', chars: 83_270 },
    note: 'hand-adjudicated; traversal returns target_version property 9.0.21.300 directly',
  },
  {
    id: 'PV1',
    cls: 'provenance',
    text: 'Are the JSON job-definition examples in the API docs vendor ground truth?',
    traversal: { kind: 'pass', chars: 1053, ms: 81 },
    fulltext: { kind: 'fail', chars: 2833, ms: 13 },
    manifest: { kind: 'partial', chars: 0, qualifier: 'rule only' },
    note: "graph-only: filter chunks by provenance='SYNTHESIZED'; answer: no — they are our inference",
    cypher: [
      {
        label: 'traversal — provenance filter',
        code:
          "MATCH (c:Chunk)\nWHERE c.heading CONTAINS 'JSON job definition' AND c.provenance = 'SYNTHESIZED'\n" +
          'RETURN c.heading, c.provenance, c.text',
      },
    ],
  },
  {
    id: 'OS1',
    cls: 'out-of-scope',
    text: 'How do I define an AutoSys global variable?',
    traversal: { kind: 'abstain', chars: 0, ms: 17, qualifier: 'correct' },
    fulltext: { kind: 'hallucination', chars: 3678, ms: 34 },
    manifest: { kind: 'abstain', chars: 0, qualifier: 'correct' },
    note: 'full-text returned 3,678 chars of confident, irrelevant Control-M variable text at score 4.24 — the worst support-agent failure mode',
    cypher: [
      {
        label: 'traversal — empty-result abstention',
        code:
          "MATCH (c:Chunk)\nWHERE c.text CONTAINS 'AutoSys' AND c.text CONTAINS 'global variable'\n" +
          "RETURN c.heading, c.text\n// 0 rows -> \"not covered in this corpus\"",
      },
      {
        label: 'full-text — confident noise (score 4.24)',
        code:
          "CALL db.index.fulltext.queryNodes('p0_chunk_ft', 'AutoSys global variable')\n" +
          'YIELD node, score\n' +
          'RETURN node.heading, node.text, score\n' +
          'ORDER BY score DESC\n' +
          'LIMIT 3',
      },
    ],
  },
]

export const PROVENANCE_LINE =
  'Live benchmark 2026-07-16 · full record: knowledge/upgrade-plans/docmeta-p0-verdict.md · ' +
  'explainer: docs/design/graph-retrieval-benchmark-explainer.md · commit 0e036ff'
