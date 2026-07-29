import { runtimeViewUrl, type RuntimeKind } from '../../lib/runtimeView'

// IdChip — the identifier-rendering convention (O38 / DL-6 + DL-11a;
// UI-WIP/ui-conventions.md §2): Control-M / product / run identifiers render
// in Plex Mono inside a subtle chip, colored ONLY through the shared status
// vocabulary tokens (§1) — same object, same look, on every surface. When the
// O39 runtime-view template is configured (VITE_RUNTIME_VIEW_URL_TEMPLATE),
// the chip grows an external-link affordance to the runtime monitor; with the
// template unset it renders nothing extra (the two-track seam: mechanism
// here, company URL binding company-side only).

export function IdChip({
  id,
  token,
  title,
  runtimeKind,
}: {
  id: string
  /** status token per the shared vocabulary; omit for the neutral identifier look */
  token?: '--green' | '--yellow' | '--teal' | '--blue-br' | '--status-fail-soft' | '--muted'
  title?: string
  /** set to render the O39 runtime-view link when the env template is configured */
  runtimeKind?: RuntimeKind
}) {
  const href = runtimeKind ? runtimeViewUrl(runtimeKind, id) : null
  const style = token ? { borderColor: `var(${token})`, color: `var(${token})` } : undefined
  return (
    <span
      className={
        'inline-flex max-w-full items-center gap-1 rounded border bg-bg-2/60 px-1.5 py-0.5 font-mono text-[10px] ' +
        (token ? '' : 'border-edge-soft text-muted')
      }
      style={style}
      title={title ?? id}
    >
      <span className="truncate">{id}</span>
      {href && (
        <a
          href={href}
          target="_blank"
          rel="noreferrer noopener"
          aria-label={`Open ${id} in the runtime view`}
          className="text-blue-bright no-underline hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          ↗
        </a>
      )}
    </span>
  )
}

// Medallion stage badge (DL-11a): stage names are the ecosystem's shared
// vocabulary (both neighboring tools render RAW → TRUSTED → REFINED →
// SNOWFLAKE) — flat mono badge, uppercase, no semantic tint (a stage is a
// place, not a status).
export function StageBadge({ stage }: { stage: 'RAW' | 'TRUSTED' | 'REFINED' | 'SNOWFLAKE' }) {
  return (
    <span className="inline-flex items-center rounded border border-edge bg-panel-2 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-muted">
      {stage}
    </span>
  )
}

export default IdChip
