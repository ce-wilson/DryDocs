// Shared SYNTHESIZED demo-frame table with Explorer-style selection linking
// (extracted at O17): row click selects the row's graph node; a selected node
// highlights its rows. Selection is a plain node id — panes resolve labels.

export interface LinkedFrameData {
  cols: readonly string[]
  rows: readonly (readonly string[])[]
  nodeIds: readonly string[]
}

export default function LinkedDemoFrame({
  frame,
  notice,
  selectedId,
  onSelect,
}: {
  frame: LinkedFrameData
  notice: string
  selectedId: string | null
  onSelect: (id: string | null) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        {notice}
      </p>
      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {frame.cols.map((c) => (
                <th key={c} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {frame.rows.map((row, i) => {
              const nodeId = frame.nodeIds[i]
              const isSelected = selectedId === nodeId
              return (
                <tr
                  key={i}
                  onClick={() => onSelect(isSelected ? null : nodeId)}
                  className={
                    'cursor-pointer ' +
                    (isSelected ? 'bg-panel-2' : i % 2 ? 'bg-bg-2/40 hover:bg-bg-2' : 'hover:bg-bg-2')
                  }
                >
                  {row.map((cell, j) => (
                    <td key={j} className="border-b border-edge-soft px-2.5 py-1.5 text-text">
                      {cell}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
