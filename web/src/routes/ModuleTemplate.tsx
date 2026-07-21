import type { ReactNode } from 'react'
import type { ModuleDef } from '../modules/registry'
import ModuleToolbar from '../layout/ModuleToolbar'
import ResizableSplit from '../components/ui/ResizableSplit'
import Tabs, { type TabDef } from '../components/ui/Tabs'
import EmptyState from '../components/ui/EmptyState'

interface ModuleTemplateProps {
  module: ModuleDef
  /** third breadcrumb segment, e.g. a selected node's label */
  selection?: string
  /** graph pane content — defaults to the module's empty state */
  graphPane?: ReactNode
  /** per-tab content override, keyed by tab label; unset tabs render the
   *  shared "no QuerySpec yet" empty state */
  tabContent?: Partial<Record<string, ReactNode>>
  toolbarActions?: ReactNode
}

// The shared module subpage template (site-plan §3 / wf-module-subpage-01):
// ONE component instantiated by every module route. Per that file's own rule
// (annotation 7): "Per-module instantiation = { route, QuerySpecs per tab,
// graph query, node-type set for the inspector, toolbar extras}. NOTHING else
// may vary — template drift is a review flag." O8 builds this shell; wiring
// real QuerySpecs per tab is O9+ (the acceptance here is the skeleton, not the
// module views).
export default function ModuleTemplate({ module, selection, graphPane, tabContent, toolbarActions }: ModuleTemplateProps) {
  const tabs: TabDef[] = module.tabs.map((label) => ({
    id: label,
    label,
    content: tabContent?.[label] ?? (
      <EmptyState
        title={`${label} — no data source wired yet`}
        hint={`This tab's QuerySpec against ${module.backsOnto} lands in a later backlog item (phase ${module.phase}).`}
      />
    ),
  }))

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* breadcrumb layer stays breadcrumbs-only (2026-07-21 user call);
          page actions live on the heading row below */}
      <ModuleToolbar
        crumbs={[{ label: 'Home', to: '/' }, { label: module.label }, ...(selection ? [{ label: selection }] : [])]}
      />
      <div className="flex flex-wrap items-end gap-2 px-4 pt-3">
        <div className="min-w-0 flex-1">
          <h2 tabIndex={-1} data-view-heading className="text-lg font-semibold text-text outline-none">
            {module.label}
          </h2>
          <p className="mt-0.5 text-xs text-faint">{module.tagline} · backs onto {module.backsOnto}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {toolbarActions ?? (
            <>
              <ToolbarButton label="Layout" disabled />
              <ToolbarButton label="Fit" disabled />
              <ToolbarButton label="Refresh" disabled />
              <ToolbarButton label="Export ▾" disabled />
            </>
          )}
        </div>
      </div>
      <div className="min-h-0 flex-1 p-4">
        <div className="h-full min-h-[420px] overflow-hidden rounded-lg border border-edge bg-panel">
          <ResizableSplit
            storageKey={`drydocs.split.${module.id}.v1`}
            top={
              graphPane ?? (
                <EmptyState
                  title="No selection — pick a node once the graph pane is wired up"
                  hint={`${module.label}'s graph query lands with its QuerySpec (site-plan §4).`}
                />
              )
            }
            bottom={<Tabs tabs={tabs} />}
          />
        </div>
      </div>
    </div>
  )
}

function ToolbarButton({ label, disabled }: { label: string; disabled?: boolean }) {
  return (
    <button
      type="button"
      disabled={disabled}
      title={disabled ? 'Wired up in a later backlog item' : undefined}
      className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted disabled:cursor-not-allowed disabled:opacity-50"
    >
      {label}
    </button>
  )
}
