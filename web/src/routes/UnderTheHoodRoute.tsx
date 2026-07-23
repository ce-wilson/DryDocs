import { useState } from 'react'
import ModuleToolbar from '../layout/ModuleToolbar'
import StatTiles from '../components/StatTiles'
import { CORPUS, EFFICIENCY, PROVENANCE_LINE, QUESTIONS, TOTALS } from '../underhood/benchmarkData'
import StrategyCards from '../underhood/StrategyCards'
import Scoreboard from '../underhood/Scoreboard'
import QuestionDetail from '../underhood/QuestionDetail'
import TokenMemoryChart from '../underhood/TokenMemoryChart'
import HallucinationSpotlight from '../underhood/HallucinationSpotlight'
import ThinkingLogicPanel from '../underhood/ThinkingLogicPanel'

// /under-the-hood (registry id `underhood`, phase 1): a benchmark showcase,
// NOT a ModuleTemplate instantiation — like AssetPathRoute, this is a bespoke
// page with its own ModuleToolbar breadcrumb, because its content (a fixed
// 12-question live benchmark) doesn't fit the graph-pane + data-frame shape
// every other module page shares. Data is the committed docmeta P0 verdict,
// transcribed verbatim into underhood/benchmarkData.ts — nothing here is
// invented.
export default function UnderTheHoodRoute() {
  const [selectedId, setSelectedId] = useState<string>(QUESTIONS[0].id)
  const selected = QUESTIONS.find((q) => q.id === selectedId) ?? QUESTIONS[0]

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar crumbs={[{ label: 'Home', to: '/' }, { label: 'Under the Hood' }]} />
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h2 tabIndex={-1} data-view-heading className="text-lg font-semibold text-text outline-none">
            Under the Hood — how the agent retrieves knowledge
          </h2>
          <p className="mt-1 max-w-3xl text-xs leading-relaxed text-faint">
            Three ways an AI support agent can pull answers from a vendor documentation corpus, benchmarked
            head-to-head on 12 fixed support questions — the live test that decided DryDocs would{' '}
            <span className="font-semibold text-text">build</span> its document-ingestion component as a graph,
            not shrink it to a file registry.
          </p>

          {/* 1. at-a-glance stat tiles */}
          <div className="mt-4">
            <StatTiles
              tiles={[
                { value: `${TOTALS.traversal.recall}`, label: 'Traversal recall' },
                { value: EFFICIENCY.headline, label: 'Token efficiency' },
                { value: `${TOTALS.traversal.tokens} vs ${TOTALS.manifest.tokens}`, label: 'Tokens ingested' },
                { value: `${TOTALS.traversal.latencyMedianMs}ms`, label: 'Median traversal latency' },
                { value: `${CORPUS.chunkCount} / ${CORPUS.docCount}`, label: 'Chunks / docs' },
                { value: '3', label: 'Strategies tested live' },
              ]}
            />
          </div>

          {/* 2. the three strategy cards */}
          <section className="mt-6">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Three retrieval strategies</h3>
            <StrategyCards />
          </section>

          {/* 3. the scoreboard + detail panel */}
          <section className="mt-6">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">
              The scoreboard — 12 fixed support questions
            </h3>
            <div className="grid grid-cols-1 gap-3 xl:grid-cols-[1.3fr_1fr]">
              <Scoreboard selectedId={selectedId} onSelect={setSelectedId} />
              <QuestionDetail question={selected} />
            </div>
          </section>

          {/* 4. token-memory tracker */}
          <section className="mt-6">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Token-memory tracker</h3>
            <TokenMemoryChart />
          </section>

          {/* 5. hallucination spotlight */}
          <section className="mt-6">
            <HallucinationSpotlight />
          </section>

          {/* 6. thinking-logic panel */}
          <section className="mt-6">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Reading the result</h3>
            <ThinkingLogicPanel />
          </section>

          {/* corpus footnote + provenance */}
          <p className="mt-6 text-[11px] leading-relaxed text-faint">
            Corpus: {CORPUS.label} · {CORPUS.totalChars.toLocaleString()} chars · {CORPUS.chunkCount} chunks · trust
            tiers{' '}
            {CORPUS.tiers.map((t, i) => (
              <span key={t.tier}>
                {i > 0 ? ' / ' : ''}
                <span className="font-mono" style={{ color: `var(${t.token})` }}>
                  {t.chunks} {t.tier}
                </span>{' '}
                ({t.chars.toLocaleString()} ch)
              </span>
            ))}
            . Per-question efficiency range {EFFICIENCY.perQuestionRange}.
          </p>

          <p className="mt-2 font-mono text-[10px] text-faint">{PROVENANCE_LINE}</p>
          <p className="mt-1 font-mono text-[10px] text-yellow">FIXTURE DATA · from committed benchmark record</p>
        </div>
      </div>
    </div>
  )
}
