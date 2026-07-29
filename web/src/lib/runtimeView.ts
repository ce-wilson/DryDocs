// O39 (DL-8, internal/datalens-reference/continuity.md) — the cross-tool
// deep-link seam, MECHANISM ONLY. A page is "ported" when it renders company
// config with zero component edits: this module reads an optional URL
// template from the environment; binding a real runtime-monitor URL is a
// company-side DD-series item and never lands in this repo (no company URL
// or hostname here — enforced by the publish boundary).
//
// Template shape (web/.env.example):
//   VITE_RUNTIME_VIEW_URL_TEMPLATE="https://runtime.example.internal/{kind}/{id}"
// {kind} ∈ job | folder | dataset | run · {id} is URI-encoded.

export type RuntimeKind = 'job' | 'folder' | 'dataset' | 'run'

export function runtimeViewUrl(kind: RuntimeKind, id: string): string | null {
  const tpl = import.meta.env.VITE_RUNTIME_VIEW_URL_TEMPLATE as string | undefined
  if (!tpl) return null
  return tpl.replace('{kind}', kind).replace('{id}', encodeURIComponent(id))
}
