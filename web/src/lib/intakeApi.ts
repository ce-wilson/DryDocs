import type { Schemas } from './apiClient'
import { unwrapAs } from './apiClient'
import { createApiClient } from './graphApi'

// The O47 intake client — the /intake/* surface of drydocs-api (O46 store).
// Same shared ApiClient/auth policy as mappingsApi. The one shape difference:
// evidence upload is MULTIPART; the typed client carries it through a body
// serializer that builds the FormData (O70), so the path and parameter are
// still checked against the schema. The server writes files under
// DRYDOCS_DATA_ROOT/context-intake/ and SQLite; the graph is untouched until
// the O50 gated load.
//
// O70: paths and request bodies are schema-checked; the response type stays
// the hand-declared IntakeRecord until drydocs_api.schemas models it.

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

type EvidenceBody = Schemas['Body_post_intake_evidence_intake__intake_id__evidence_post']

export function createIntakeApi(baseUrl: string, personaId: string): IntakeApi {
  const { api } = createApiClient(baseUrl, personaId)

  const record = (result: { data?: unknown; error?: unknown; response: Response }, what: string) =>
    unwrapAs<IntakeRecord>(result, what)

  return {
    async list() {
      return unwrapAs<{ intakes: IntakeRecord[] }>(await api.GET('/intake'), 'intake').intakes
    },
    async get(intakeId) {
      return record(
        await api.GET('/intake/{intake_id}', { params: { path: { intake_id: intakeId } } }),
        `intake ${intakeId}`,
      )
    },
    async create(contextType, area, note) {
      return record(
        await api.POST('/intake', { body: { context_type: contextType, area, note } }),
        'intake create',
      )
    },
    async uploadEvidence(intakeId, files) {
      // WEB6: NO CASTS HERE ANY MORE. The generated body now declares
      // `files: Blob[]` (scripts/genApiTypes.ts maps the schema's binary
      // content type), and `File extends Blob`, so the real objects satisfy the
      // real type. Both double casts existed only because the generator had
      // typed a binary upload as a string.
      const body: EvidenceBody = { files }
      return record(
        await api.POST('/intake/{intake_id}/evidence', {
          params: { path: { intake_id: intakeId } },
          body,
          bodySerializer: (declared) => {
            const form = new FormData()
            // `name` is a File's, not a Blob's — the serializer receives what
            // this method was handed, so the narrowing is real and local.
            for (const f of declared.files) {
              form.append('files', f, f instanceof File ? f.name : undefined)
            }
            return form
          },
        }),
        'evidence upload',
      )
    },
    async transition(intakeId, to, note = '') {
      return record(
        await api.POST('/intake/{intake_id}/transition', {
          params: { path: { intake_id: intakeId } },
          body: { to, note },
        }),
        `intake ${intakeId} transition`,
      )
    },
    async threadDecision(intakeId, decision) {
      return record(
        await api.POST('/intake/{intake_id}/thread-decision', {
          params: { path: { intake_id: intakeId } },
          body: { decision },
        }),
        `intake ${intakeId} thread decision`,
      )
    },
  }
}
