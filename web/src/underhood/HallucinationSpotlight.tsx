import { QUESTIONS } from './benchmarkData'
import ResultChip from './ResultChip'

// OS1 spotlight (explainer §6 "abstention is a feature"): side-by-side of
// what each strategy actually did on the one out-of-scope question. The
// point isn't the chars saved — it's that full-text answered confidently and
// wrongly, which for a 3 a.m. support agent is the worst outcome of the
// three, worse than an honest "I don't know".
export default function HallucinationSpotlight() {
  const os1 = QUESTIONS.find((q) => q.id === 'OS1')!

  return (
    <div className="rounded-lg border border-red/40 bg-red/5 p-4">
      <h3 className="text-sm font-semibold text-text">Hallucination spotlight — {os1.id}</h3>
      <p className="mt-1 text-xs text-muted">&ldquo;{os1.text}&rdquo; — this corpus cannot answer it (it&rsquo;s AutoSys, not Control-M).</p>

      <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-3">
        <SpotlightCard label="Graph traversal" kind={os1.traversal.kind} text={`0 rows → says "not covered here"`} good />
        <SpotlightCard
          label="Full-text search"
          kind={os1.fulltext.kind}
          text="3,678 chars of confident, irrelevant text, score 4.24"
        />
        <SpotlightCard label="Manifest routing" kind={os1.manifest.kind} text="empty routing → abstains" good />
      </div>

      <p className="mt-3 text-xs leading-relaxed text-muted">
        Abstention is a feature, not a gap. Confident noise at 3 a.m. becomes a wrong action — a retrieval
        component that can&rsquo;t say &ldquo;I don&rsquo;t know&rdquo; is worse than one that&rsquo;s merely slow.
      </p>
    </div>
  )
}

function SpotlightCard({
  label,
  kind,
  text,
  good,
}: {
  label: string
  kind: 'pass' | 'fail' | 'partial' | 'abstain' | 'hallucination'
  text: string
  good?: boolean
}) {
  return (
    <div
      className={
        'rounded-md border p-2.5 ' + (good ? 'border-teal/40 bg-teal/5' : 'border-red/40 bg-red/10')
      }
    >
      <div className="flex items-center justify-between gap-1.5">
        <span className="text-[11px] font-semibold text-text">{label}</span>
        <ResultChip kind={kind} compact />
      </div>
      <p className="mt-1 font-mono text-[10.5px] text-muted">{text}</p>
    </div>
  )
}
