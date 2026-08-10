import { createApiClient, readDetail, type ApiClient } from './graphApi'

// The O47 intake client — the /intake/* surface of drydocs-api (O46 store).
// Same shared ApiClient/auth policy as mappingsApi. The one shape difference:
// evidence upload is MULTIPART, which authedPost cannot carry (it pins
// Content-Type: application/json), so uploadEvidence builds its own fetch on
// the client's bearer token. The server writes files under DRYDOCS_DATA_ROOT/
// context-intake/ and SQLite; the graph is untouched until the O50 gated load.

export interface EvidenceRow {
  evidence_id: string
  intake_id: string
  filename: string
  rel_key: string
  sha256: string
  size: number
  kind: 'msg' | 'json' | 'txt'
  pair_key: string
  preview: Record<string, unknown> | null
  uploaded_at: string
  superseded: boolean
}

export interface LegalTransitions {
  status: string
  transitions: { to: string; action: string }[]
  waiting_on_gate: boolean
  terminal: boolean
  thread_decision_required?: boolean
  thread_decisions?: string[]
}

export interface IntakeRecord {
  intake_id: string
  created_at: string
  created_by: string
  origin: string
  classification: string
  context_type: string
  note: string
  status: string
  review_payload: string | null
  area: Record<string, string | null>
  thread_of: string[]
  thread_flagged: boolean
  thread_decision: 'adds-value' | 'no-new-value' | null
  evidence: EvidenceRow[]
  legal_transitions: LegalTransitions
}

export interface IntakeApi {
  list(): Promise<IntakeRecord[]>
  get(intakeId: string): Promise<IntakeRecord>
  create(contextType: string, area: Record<string, string | null>, note: string): Promise<IntakeRecord>
  uploadEvidence(intakeId: string, files: File[]): Promise<IntakeRecord>
  transition(intakeId: string, to: string, note?: string): Promise<IntakeRecord>
  threadDecision(intakeId: string, decision: 'adds-value' | 'no-new-value'): Promise<IntakeRecord>
}

export function createIntakeApi(baseUrl: string, personaId: string): IntakeApi {
  const client: ApiClient = createApiClient(baseUrl, personaId)

  async function json<T>(res: Response): Promise<T> {
    if (!res.ok) throw new Error(await readDetail(res))
    return (await res.json()) as T
  }

  return {
    async list() {
      const res = await client.authedGet('/intake')
      return (await json<{ intakes: IntakeRecord[] }>(res)).intakes
    },
    async get(intakeId) {
      return json<IntakeRecord>(await client.authedGet(`/intake/${intakeId}`))
    },
    async create(contextType, area, note) {
      return json<IntakeRecord>(
        await client.authedPost('/intake', { context_type: contextType, area, note }),
      )
    },
    async uploadEvidence(intakeId, files) {
      const form = new FormData()
      for (const f of files) form.append('files', f, f.name)
      const token = await client.getToken()
      const res = await fetch(`${baseUrl}/intake/${intakeId}/evidence`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      })
      return json<IntakeRecord>(res)
    },
    async transition(intakeId, to, note = '') {
      return json<IntakeRecord>(
        await client.authedPost(`/intake/${intakeId}/transition`, { to, note }),
      )
    },
    async threadDecision(intakeId, decision) {
      return json<IntakeRecord>(
        await client.authedPost(`/intake/${intakeId}/thread-decision`, { decision }),
      )
    },
  }
}
