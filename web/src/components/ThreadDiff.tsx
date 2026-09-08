// The inline thread diff: the O46 delta payload, new content highlighted.
//
// O50 MOVED THIS OUT OF IntakeRoute. It now has two consumers — the SME's
// upload row, where the delta is the thing being ruled on, and the admin review
// panel, where the same delta is the record of what the machine computed and
// what the SME decided about it. Rendering the SME's evidence one way and the
// admin's re-read of it another is how the two disagree about what the SME saw,
// which is the exact failure the plan's VERBATIM-render discipline exists to
// stop ("what the SME confirmed is exactly what admin review later sees").
export default function ThreadDiff({ delta }: { delta: string }) {
  return (
    <pre className="max-h-48 overflow-auto rounded border border-edge-soft bg-panel-2 p-2 text-xs">
      {delta.split('\n').map((line, i) => (
        <div key={i} style={{ background: 'color-mix(in srgb, var(--teal) 18%, transparent)' }}>
          {line || ' '}
        </div>
      ))}
    </pre>
  )
}
