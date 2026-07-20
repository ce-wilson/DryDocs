import { useRightSidebar } from './rightSidebarContext'

// Renders whatever the active route pushed into the right-sidebar context
// (or nothing). The column itself is always present in the shell grid
// (shellConfig.ts reserves it); only its width — driven by isOpen — collapses
// to 0 when there's no content, per wf-module-subpage-01 annotation 2.
export default function RightSidebarSlot() {
  const { content, isOpen } = useRightSidebar()
  return (
    <aside
      aria-label="Inspector"
      className="h-full overflow-y-auto border-l border-edge-soft bg-panel"
      style={{ display: isOpen ? 'block' : 'none' }}
    >
      {content}
    </aside>
  )
}
