import { useEffect, useSyncExternalStore } from 'react'

import { createPublicApi } from './apiClient'

// O39 (DL-8, internal/datalens-reference/continuity.md) — the cross-tool
// deep-link seam, MECHANISM ONLY. A page is "ported" when it renders company
// config with zero component edits: this module reads an optional URL
// template from the API; binding a real runtime-monitor URL is a company-side
// DD-series item and never lands in this repo (no company URL or hostname
// here — enforced by the publish boundary).
//
// WHERE THE TEMPLATE COMES FROM (ADR 0020, WEB10). It used to be inlined at
// build time from VITE_RUNTIME_VIEW_URL_TEMPLATE, which made the bundle
// environment-specific: one build could not be promoted from test to
// production because the production URL was baked into the test build. It is
// now a per-deployment, non-secret value the API serves from its own
// environment (DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE) on GET /config, read ONCE at
// shell mount by useRuntimeConfig. Until it arrives, chips render no link
// rather than a wrong one; when it never arrives (API down) the console
// behaves exactly as it does with the template unset.
//
// Template shape: "https://runtime.example.internal/{kind}/{id}"
// {kind} ∈ job | folder | dataset | run · {id} is URI-encoded.

export type RuntimeKind = 'job' | 'folder' | 'dataset' | 'run'

let template: string | null = null
const listeners = new Set<() => void>()

function setTemplate(next: string | null): void {
  if (next === template) return
  template = next
  for (const l of listeners) l()
}

function subscribe(l: () => void): () => void {
  listeners.add(l)
  return () => listeners.delete(l)
}

/** The template as last served by GET /config; null before the load and
 *  when the deployment configures none. */
export function runtimeViewTemplate(): string | null {
  return template
}

/** Bind a kind and id into a template. Pure, so IdChip can call it with the
 *  value the hook handed it; null when there is no template to bind into. */
export function runtimeViewUrl(kind: RuntimeKind, id: string, tpl: string | null = template): string | null {
  if (!tpl) return null
  return tpl.replace('{kind}', kind).replace('{id}', encodeURIComponent(id))
}

/** One GET /config. A failure leaves the template as it was: a deep link is a
 *  convenience, and the readiness probe is where "the API is down" is said. */
export async function loadRuntimeConfig(apiUrl: string, signal?: AbortSignal): Promise<void> {
  try {
    const res = await createPublicApi(apiUrl).GET('/config', { signal })
    if (res.data) setTemplate(res.data.runtime_view_url_template ?? null)
  } catch {
    // nothing to say here that the readiness banner is not already saying
  }
}

/** Subscribe a component to the template; re-renders when the load lands. */
export function useRuntimeViewTemplate(): string | null {
  return useSyncExternalStore(subscribe, runtimeViewTemplate, runtimeViewTemplate)
}

/** The shell's one load, beside its one readiness probe (SystemBanner). */
export function useRuntimeConfig(apiUrl: string): void {
  useEffect(() => {
    const ctl = new AbortController()
    void loadRuntimeConfig(apiUrl, ctl.signal)
    return () => ctl.abort()
  }, [apiUrl])
}

/** Test seam: forget what was loaded. */
export function resetRuntimeConfigForTests(): void {
  setTemplate(null)
}
