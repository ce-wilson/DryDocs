// wf-module-subpage-01 annotation 4: "every pane has explicit empty/loading/
// error states... never a blank." A shared, consistent look for all three.
export default function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex h-full min-h-[120px] flex-col items-center justify-center gap-1 p-6 text-center">
      <p className="text-sm text-muted">{title}</p>
      {hint && <p className="max-w-sm text-xs text-faint">{hint}</p>}
    </div>
  )
}
