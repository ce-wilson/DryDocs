import { CLASS_TOKEN, STRATEGIES, type BenchmarkQuestion } from './benchmarkData'
import ResultChip from './ResultChip'

// The scoreboard's detail panel: full question text, a per-strategy behavior
// readout (chars/ms/qualifier), the adjudication note, and — where the
// benchmark recorded one — the representative Cypher (including the
// naive-vs-informed pair for the paraphrase questions, docs/design/graph-
// retrieval-benchmark-explainer.md §6's "paraphrase gap").
export default function QuestionDetail({ question }: { question: BenchmarkQuestion }) {
  return (
    <div className="rounded-lg border border-edge bg-panel p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <span
            className="rounded border px-1.5 py-0.5 font-mono text-[9.5px]"
            style={{ borderColor: `var(${CLASS_TOKEN[question.cls]})`, color: `var(${CLASS_TOKEN[question.cls]})` }}
          >
            {question.id} · {question.cls}
          </span>
          <h3 className="mt-1.5 text-sm font-semibold text-text">{question.text}</h3>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-3">
        {STRATEGIES.map((s) => {
          const r = question[s.id]
          return (
            <div key={s.id} className="rounded-md border border-edge-soft bg-bg-2 p-2.5">
              <div className="flex items-center justify-between gap-1.5">
                <span className="text-[10.5px] font-semibold text-text">{s.label}</span>
                <ResultChip kind={r.kind} compact />
              </div>
              <p className="mt-1 font-mono text-[10.5px] text-faint">
                {r.chars.toLocaleString()} ch{r.ms != null ? ` · ${r.ms} ms` : ''}
                {r.qualifier ? ` · ${r.qualifier}` : ''}
              </p>
            </div>
          )
        })}
      </div>

      {question.note !== '—' && <p className="mt-3 text-xs leading-relaxed text-muted">{question.note}</p>}

      {question.cypher && question.cypher.length > 0 && (
        <div className="mt-3 flex flex-col gap-2.5">
          {question.cypher.map((c) => (
            <div key={c.label} className="overflow-hidden rounded-md border border-edge-soft">
              <div className="border-b border-edge-soft bg-panel-2 px-2.5 py-1 font-mono text-[10px] text-muted">
                {c.label}
              </div>
              <pre className="overflow-x-auto bg-bg p-2.5 font-mono text-[11px] leading-relaxed text-muted">
                {c.code}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
