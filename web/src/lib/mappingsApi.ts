import type { Schemas } from './apiClient'
import { unwrap } from './apiClient'
import { createApiClient } from './graphApi'

// The O13 mappings client — the /mappings/* surface of drydocs-api
// (steward/admin only, enforced SERVER-side; the UI gate is convenience).
// Reads come from the mapping-store SQLite materialization; the ONLY
// "write" is draftChangeset, which returns a config/manual-loads/ change
// ARTIFACT (CSV text + manifest snippet) — the server writes nothing, the
// loader stays the only graph writer (wf-mapping-01's one rule).
//
// WEB8 — "the day drydocs_api.schemas models them" arrived. The note that stood
// here said the response types were hand-declared because the server declared
// these routes as free objects, and that when it modelled them the casts would
// go and the interfaces would become aliases. Both have happened.
//
// THIS MODULE IS WHY THE ITEM WAS PRIORITISED. It is the only one in the group
// with WRITE surfaces (draft, promote), so a route drifting from its declared
// shape here writes wrong rather than renders wrong — the web review's T3.
// Nine casts stood between the console and the server on exactly that surface.
//
// The `rows` of a grid and the label/relationship option lists stay
// `Record<string, unknown>`, and now do so BY DECLARATION rather than by
// default: those are per-domain SELECTs whose columns belong to the domain, not
// to the route, so the server models the envelope and leaves the row open. See
// the note on MappingGridOut in drydocs_api/schemas.py.

export type MappingDomain = Schemas['MappingDomainOut']
export type MappingGrid = Schemas['MappingGridOut']
export type MappingOptions = Schemas['MappingOptionsOut']

// STALE, AND WEB8 COULD NOT FIX IT HERE. The server refuses this shape: at K7
// §A1 the job-grain changeset was retired, and POST /mappings/changeset now
// requires `app_code` + `app_id` per entry ("authoring is per app code", §B1).
// Found by driving the route in tests/unit/test_response_models.py, which is
// the first thing in the suite to send it a request.
//
// It survives here because WEB8 declares RESPONSES: the request body is
// `ChangesetBody.entries: list = []` server-side — a free list — so no
// generated type covers an entry, and correcting this interface alone would
// swap one unguarded hand-declaration for another. Modelling the request
// bodies is its own item; handed back in the WEB8 close notes.
export interface DraftEntry {
  folder_id: string
  job_id: string
  app_id: string
  rationale: string
  create_target_if_missing?: boolean
}

export type ChangesetArtifact = Schemas['ChangesetArtifactOut']

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
export type DraftReceipt = Schemas['DraftReceiptOut']

export type PromotedDiff = Schemas['PromotedDiffOut']

export type OpenDraft = Schemas['OpenDraftOut']

export type CorrectionsReport = Schemas['CorrectionsReportOut']

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
      const body = unwrap(
        await api.GET('/mappings/domains'),
        'mappings/domains',
      )
      return body.domains
    },
    async grid(domainId) {
      return unwrap(
        await api.GET('/mappings/grid/{domain_id}', { params: { path: { domain_id: domainId } } }),
        `mappings/grid/${domainId}`,
      )
    },
    async options() {
      return unwrap(await api.GET('/mappings/options'), 'mappings/options')
    },
    async draftChangeset(entries) {
      return unwrap(
        await api.POST('/mappings/changeset', { body: { entries } }),
        'mappings/changeset',
      )
    },
    async draftOverride(entries, draftId) {
      return unwrap(
        await api.POST('/mappings/overrides/draft', { body: { entries, draft_id: draftId } }),
        'mappings/overrides/draft',
      )
    },
    async draftAppCode(entries, draftId) {
      return unwrap(
        await api.POST('/mappings/app-code/draft', { body: { entries, draft_id: draftId } }),
        'mappings/app-code/draft',
      )
    },
    async drafts(domain) {
      const body = unwrap(
        await api.GET('/mappings/drafts', { params: { query: domain ? { domain } : {} } }),
        'mappings/drafts',
      )
      return body.drafts
    },
    async promoteDraft(draftId) {
      return unwrap(
        await api.POST('/mappings/drafts/{draft_id}/promote', {
          params: { path: { draft_id: draftId } },
        }),
        'mappings/drafts/promote',
      )
    },
    async correctionsReport() {
      return unwrap(
        await api.GET('/mappings/overrides/report'),
        'mappings/overrides/report',
      )
    },
  }
}
