import { unwrapAs } from './apiClient'
import { createApiClient } from './graphApi'

// The O13 mappings client — the /mappings/* surface of drydocs-api
// (steward/admin only, enforced SERVER-side; the UI gate is convenience).
// Reads come from the mapping-store SQLite materialization; the ONLY
// "write" is draftChangeset, which returns a config/manual-loads/ change
// ARTIFACT (CSV text + manifest snippet) — the server writes nothing, the
// loader stays the only graph writer (wf-mapping-01's one rule).
//
// O70: the paths, path/query parameters and request bodies below are checked
// against the generated schema (lib/apiClient.ts). The RESPONSE types on this
// page are still the hand-declared interfaces, because the server declares
// these routes as free objects — the day drydocs_api.schemas models them, the
// casts at each `unwrap` go and the interfaces become aliases of the schema.

export interface MappingDomain {
  id: string
  title: string
  kind: 'quintuple' | 'manual' | 'override' | 'defined'
  source: string
  tier: number | null
  available: boolean
}

export interface MappingGrid {
  domain: string
  keys: string[]
  rows: Record<string, unknown>[]
}

export interface MappingOptions {
  labels: Record<string, unknown>[]
  relationships: Record<string, unknown>[]
  status_summary: { status: string; n: number }[]
}

export interface DraftEntry {
  folder_id: string
  job_id: string
  app_id: string
  rationale: string
  create_target_if_missing?: boolean
}

export interface ChangesetArtifact {
  filename: string
  csv: string
  manifest_snippet: string
  entries: number
  lifecycle: string
  note: string
}

// O24 — SEAL-contact overrides (ui-write-surface gate SME-3, M2 tier).
// Drafting returns the COMPLETE updated committed file (commit-by-replace);
// the report is the AO-facing source-corrections artifact. Server writes
// nothing; the graph is never touched by an override.
export interface OverrideEntry {
  app_id: string
  role_name: string
  seal_holder_sid?: string
  override_holder_sid: string
  override_holder_name?: string
  rationale: string
}

// S4 (ADR 0009 rule 5): drafting no longer hands back a whole replacement
// file. It writes ROWS to the mapping.db draft buffer and returns this
// receipt; a separate promote call turns the draft into a unified diff. The
// old shape could not survive two editors — each held a full file built from
// the same base, so whichever was committed last erased the other.
export interface DraftReceipt {
  draft_id: string
  domain: string
  entries: number
  pending: number
  committed_rows: number
  note: string
}

export interface PromotedDiff {
  draft_id: string
  domain: string
  path: string
  filename: string
  diff: string
  entries: number
  note: string
}

export interface OpenDraft {
  draft_id: string
  domain: string
  entries: number
  authored_by: string
  authored_on: string
}

export interface CorrectionsReport {
  filename: string
  markdown: string
  count: number
  generated_on: string
  generated_by: string
}

// K9/K11 — the K7 defined-mapping store (app-code -> application). Drafting
// writes rows to the draft buffer (S4, O24 mechanics verbatim); validation is
// the store's own rule set server-side, so a stored draft can never be refused
// at materialization. authored_by is server-stamped from the session — never
// sent from here.
// K18: `tier` renamed `row_kind` on the wire (the K7 kind enum; the K2 match
// tiers keep the word). app_id is required on EVERY row — a code-level
// platform DECLARATION carries the platform's OWN SEAL; the loader suppresses
// its fan-out by kind, never by a missing field.
export interface AppCodeEntry {
  app_code: string
  row_kind: 'seal-born' | 'platform' | 'dual-coded'
  app_id?: string
  folder_id?: string
  declared_end_state?: string
  origin?: 'defined' | 'override'
  rationale?: string
}

export interface MappingsApi {
  domains(): Promise<MappingDomain[]>
  grid(domainId: string): Promise<MappingGrid>
  options(): Promise<MappingOptions>
  draftChangeset(entries: DraftEntry[]): Promise<ChangesetArtifact>
  draftOverride(entries: OverrideEntry[], draftId?: string): Promise<DraftReceipt>
  draftAppCode(entries: AppCodeEntry[], draftId?: string): Promise<DraftReceipt>
  drafts(domain?: string): Promise<OpenDraft[]>
  promoteDraft(draftId: string): Promise<PromotedDiff>
  correctionsReport(): Promise<CorrectionsReport>
}

export function createMappingsApi(baseUrl: string, personaId: string): MappingsApi {
  const { api } = createApiClient(baseUrl, personaId)
  return {
    async domains() {
      const body = unwrapAs<{ domains: MappingDomain[] }>(
        await api.GET('/mappings/domains'),
        'mappings/domains',
      )
      return body.domains
    },
    async grid(domainId) {
      return unwrapAs<MappingGrid>(
        await api.GET('/mappings/grid/{domain_id}', { params: { path: { domain_id: domainId } } }),
        `mappings/grid/${domainId}`,
      )
    },
    async options() {
      return unwrapAs<MappingOptions>(await api.GET('/mappings/options'), 'mappings/options')
    },
    async draftChangeset(entries) {
      return unwrapAs<ChangesetArtifact>(
        await api.POST('/mappings/changeset', { body: { entries } }),
        'mappings/changeset',
      )
    },
    async draftOverride(entries, draftId) {
      return unwrapAs<DraftReceipt>(
        await api.POST('/mappings/overrides/draft', { body: { entries, draft_id: draftId } }),
        'mappings/overrides/draft',
      )
    },
    async draftAppCode(entries, draftId) {
      return unwrapAs<DraftReceipt>(
        await api.POST('/mappings/app-code/draft', { body: { entries, draft_id: draftId } }),
        'mappings/app-code/draft',
      )
    },
    async drafts(domain) {
      const body = unwrapAs<{ drafts: OpenDraft[] }>(
        await api.GET('/mappings/drafts', { params: { query: domain ? { domain } : {} } }),
        'mappings/drafts',
      )
      return body.drafts
    },
    async promoteDraft(draftId) {
      return unwrapAs<PromotedDiff>(
        await api.POST('/mappings/drafts/{draft_id}/promote', {
          params: { path: { draft_id: draftId } },
        }),
        'mappings/drafts/promote',
      )
    },
    async correctionsReport() {
      return unwrapAs<CorrectionsReport>(
        await api.GET('/mappings/overrides/report'),
        'mappings/overrides/report',
      )
    },
  }
}
