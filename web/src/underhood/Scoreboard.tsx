import { CLASS_TOKEN, QUESTIONS, type StrategyResult } from './benchmarkData'
import ResultChip from './ResultChip'

// The 12-row scoreboard (docmeta-p0-verdict.md's Results table, reproduced
// live): one row per fixed support question, a color-chipped class tag, and
// a result chip + cost per strategy. Row click lifts the selection up to
// UnderTheHoodRoute, which renders the matching QuestionDetail panel.
export default function Scoreboard({
  selectedId,
  onSelect,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-edge bg-panel">
      <table className="w-full min-w-[720px] border-collapse text-xs">
        <thead>
          <tr>
            {['#', 'Class', 'Question', 'Traversal', 'Full-text', 'Manifest'].map((h) => (
              <th
                key={h}
                className="border-b border-edge bg-panel-2 px-2.5 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-faint"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {QUESTIONS.map((q) => (
            <tr
              key={q.id}
              onClick={() => onSelect(q.id)}
              className={'cursor-pointer hover:bg-bg-2 ' + (q.id === selectedId ? 'bg-panel-2' : '')}
            >
              <td className="border-b border-edge-soft px-2.5 py-2 font-mono text-[11px] text-muted">{q.id}</td>
              <td className="border-b border-edge-soft px-2.5 py-2">
                <span
                  className="rounded border px-1.5 py-0.5 font-mono text-[9.5px] whitespace-nowrap"
                  style={{ borderColor: `var(${CLASS_TOKEN[q.cls]})`, color: `var(${CLASS_TOKEN[q.cls]})` }}
                >
                  {q.cls}
                </span>
              </td>
              <td className="max-w-xs border-b border-edge-soft px-2.5 py-2 text-text">{q.text}</td>
              <ResultCell r={q.traversal} />
              <ResultCell r={q.fulltext} />
              <ResultCell r={q.manifest} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ResultCell({ r }: { r: StrategyResult }) {
  return (
    <td className="border-b border-edge-soft px-2.5 py-2">
      <div className="flex items-center gap-1.5">
        <ResultChip kind={r.kind} compact />
        <span className="font-mono text-[10px] text-faint">
          {r.chars.toLocaleString()}ch{r.ms != null ? ` · ${r.ms}ms` : ''}
        </span>
      </div>
    </td>
  )
}
