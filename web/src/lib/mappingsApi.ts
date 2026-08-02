import { createApiClient, readDetail, type ApiClient } from './graphApi'

// The O13 mappings client — the /mappings/* surface of drydocs-api
// (steward/admin only, enforced SERVER-side; the UI gate is convenience).
// Reads come from the mapping-store SQLite materialization; the ONLY
// "write" is draftChangeset, which returns a config/manual-loads/ change
// ARTIFACT (CSV text + manifest snippet) — the server writes nothing, the
// loader stays the only graph writer (wf-mapping-01's one rule).

export interface MappingDomain {
  id: string
  title: string
  kind: 'quintuple' | 'manual' | 'override'
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

export interface OverrideArtifact {
  filename: string
  csv: string
  entries: number
  total_rows: number
  note: string
}

export interface CorrectionsReport {
  filename: string
  markdown: string
  count: number
  generated_on: string
  generated_by: string
}

export interface MappingsApi {
  domains(): Promise<MappingDomain[]>
  grid(domainId: string): Promise<MappingGrid>
  options(): Promise<MappingOptions>
  draftChangeset(entries: DraftEntry[]): Promise<ChangesetArtifact>
  draftOverride(entries: OverrideEntry[]): Promise<OverrideArtifact>
  correctionsReport(): Promise<CorrectionsReport>
}

async function json<T>(res: Response, what: string): Promise<T> {
  if (!res.ok) throw new Error(`${what} failed (${res.status}): ${await readDetail(res)}`)
  return (await res.json()) as T
}

export function createMappingsApi(baseUrl: string, personaId: string): MappingsApi {
  const client: ApiClient = createApiClient(baseUrl, personaId)
  return {
    async domains() {
      const body = await json<{ domains: MappingDomain[] }>(
        await client.authedGet('/mappings/domains'),
        'mappings/domains',
      )
      return body.domains
    },
    async grid(domainId) {
      return json<MappingGrid>(
        await client.authedGet(`/mappings/grid/${domainId}`),
        `mappings/grid/${domainId}`,
      )
    },
    async options() {
      return json<MappingOptions>(await client.authedGet('/mappings/options'), 'mappings/options')
    },
    async draftChangeset(entries) {
      return json<ChangesetArtifact>(
        await client.authedPost('/mappings/changeset', { entries }),
        'mappings/changeset',
      )
    },
    async draftOverride(entries) {
      return json<OverrideArtifact>(
        await client.authedPost('/mappings/overrides/draft', { entries }),
        'mappings/overrides/draft',
      )
    },
    async correctionsReport() {
      return json<CorrectionsReport>(
        await client.authedGet('/mappings/overrides/report'),
        'mappings/overrides/report',
      )
    },
  }
}
