import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

// The right-sidebar slot (node inspector, wf-module-subpage-01 annotation 2):
// closed by default, content variant keyed by node type, opens on node click.
// A context (not props drilling) so any module route — or a component nested
// arbitrarily deep in its graph pane — can populate the slot without every
// intermediate layer needing to know about it. Shell.tsx renders the slot;
// routes call useRightSidebar().set(...)/clear() to fill or empty it.
// The grid column itself is ALWAYS reserved (shellConfig.ts) — only the width
// (open vs collapsed) changes, so opening the inspector never reflows content.

interface RightSidebarState {
  content: ReactNode | null
  isOpen: boolean
  set: (content: ReactNode) => void
  clear: () => void
}

const RightSidebarContext = createContext<RightSidebarState | null>(null)

export function RightSidebarProvider({ children }: { children: ReactNode }) {
  const [content, setContentState] = useState<ReactNode | null>(null)

  const value = useMemo<RightSidebarState>(
    () => ({
      content,
      isOpen: content !== null,
      set: setContentState,
      clear: () => setContentState(null),
    }),
    [content],
  )

  return <RightSidebarContext.Provider value={value}>{children}</RightSidebarContext.Provider>
}

export function useRightSidebar(): RightSidebarState {
  const ctx = useContext(RightSidebarContext)
  if (!ctx) throw new Error('useRightSidebar must be used within RightSidebarProvider')
  return ctx
}
