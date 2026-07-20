import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'

interface ResizableSplitProps {
  /** localStorage key — the divider position is "persisted per-module"
   *  (wf-module-subpage-01 annotation 5). */
  storageKey: string
  top: ReactNode
  bottom: ReactNode
  /** graph pane ~55%, data frames ~45% (site-plan §3 shared template). */
  defaultTopPct?: number
  minTopPct?: number
  maxTopPct?: number
}

// A minimal ReUI-free "Resizable" primitive (hand-authored, ReUI-free-tier
// convention: a copied-in component, not a package) — vertical split with a
// draggable divider. The graph pane may collapse toward 0% (table-first
// modules — Gates, Loads, per wf-module-subpage-01 annotation 5); it never
// fully disappears (a 0% pane still renders its empty state, so users always
// know it's there).
export default function ResizableSplit({
  storageKey,
  top,
  bottom,
  defaultTopPct = 55,
  minTopPct = 0,
  maxTopPct = 100,
}: ResizableSplitProps) {
  const [topPct, setTopPct] = useState(() => {
    try {
      const stored = Number(localStorage.getItem(storageKey))
      return Number.isFinite(stored) && stored > 0 ? stored : defaultTopPct
    } catch {
      return defaultTopPct
    }
  })
  const containerRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)

  const clamp = useCallback((v: number) => Math.min(maxTopPct, Math.max(minTopPct, v)), [minTopPct, maxTopPct])

  const persist = useCallback(
    (v: number) => {
      try {
        localStorage.setItem(storageKey, String(v))
      } catch {
        /* ignore */
      }
    },
    [storageKey],
  )

  useEffect(() => {
    function onMove(e: PointerEvent) {
      if (!dragging.current || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const pct = clamp(((e.clientY - rect.top) / rect.height) * 100)
      setTopPct(pct)
    }
    function onUp() {
      if (!dragging.current) return
      dragging.current = false
      setTopPct((v) => {
        persist(v)
        return v
      })
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [clamp, persist])

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setTopPct((v) => {
        const next = clamp(v - 3)
        persist(next)
        return next
      })
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setTopPct((v) => {
        const next = clamp(v + 3)
        persist(next)
        return next
      })
    }
  }

  return (
    <div ref={containerRef} className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 overflow-auto" style={{ height: `${topPct}%` }}>
        {top}
      </div>
      <div
        role="separator"
        aria-orientation="horizontal"
        aria-label="Resize graph pane / data frames"
        tabIndex={0}
        onPointerDown={() => {
          dragging.current = true
        }}
        onKeyDown={onKeyDown}
        className="h-2 shrink-0 cursor-row-resize border-y border-edge-soft bg-panel-2 hover:bg-edge focus-visible:bg-blue-bright"
      />
      <div className="min-h-0 flex-1 overflow-auto">{bottom}</div>
    </div>
  )
}
