import { useState, type ReactNode } from 'react'

export interface TabDef {
  id: string
  label: string
  content: ReactNode
}

// A minimal ReUI-free "Tabs" primitive (hand-authored, copied-in convention —
// see ResizableSplit.tsx). Used for the data-frame tab strip in the shared
// module template (site-plan §3 / wf-module-subpage-01).
export default function Tabs({ tabs, initialId }: { tabs: readonly TabDef[]; initialId?: string }) {
  const [active, setActive] = useState(initialId ?? tabs[0]?.id)
  const activeTab = tabs.find((t) => t.id === active) ?? tabs[0]

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div role="tablist" aria-label="Data frames" className="flex shrink-0 gap-1 border-b border-edge-soft px-2 pt-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={t.id === activeTab?.id}
            onClick={() => setActive(t.id)}
            className={
              'rounded-t-md border border-b-0 px-3 py-1.5 text-sm font-medium transition-colors ' +
              (t.id === activeTab?.id
                ? 'border-edge bg-bg text-text'
                : 'border-transparent text-muted hover:text-text')
            }
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3">{activeTab?.content}</div>
    </div>
  )
}
