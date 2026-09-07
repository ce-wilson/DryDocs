import type { Schemas } from './apiClient'
import { unwrap } from './apiClient'
import { createApiClient } from './graphApi'

// The O47 intake client — the /intake/* surface of drydocs-api (O46 store).
// Same shared ApiClient/auth policy as mappingsApi. The one shape difference:
// evidence upload is MULTIPART; the typed client carries it through a body
// serializer that builds the FormData (O70), so the path and parameter are
// still checked against the schema. The server writes files under
// DRYDOCS_DATA_ROOT/context-intake/ and SQLite; the graph is untouched until
// the O50 gated load.
//
// WEB8: the responses are schema-checked too now, and modelling them server-side
// FOUND A LIE IN THE TYPE BELOW. `list()` was declared `Promise<IntakeRecord[]>`
// — the same type a single record uses — so it promised an always-present
// `evidence: EvidenceRow[]` on every queue row. GET /intake has never sent one:
// `list_intakes` serializes each record and attaches its legal transitions and
// never touches the evidence table, which is one query per page instead of one
// per row. Nothing broke, because the queue never reads evidence; it was a claim
// with nothing behind it, which is the exact defect O70 set out to remove.
//
// So the two shapes are two types. `IntakeRow` is what the queue gets,
// `IntakeRecord` is what a single read gets, and the second extends the first.
// A page that wants evidence must read the record — which is what it already
// does, now said out loud by the compiler.

export type EvidenceRow = Schemas['EvidenceOut']
export type LegalTransitions = Schemas['LegalTransitionsOut']
/** A row of the queue: no `evidence` — see the note above. */
export type IntakeRow = Schemas['IntakeListRowOut']
/** One intake read whole. */
export type IntakeRecord = Schemas['IntakeRecordOut']
/** The evidence-upload response: the record, plus the id of the file stored. */
export type IntakeEvidenceReceipt = Schemas['IntakeEvidenceOut']

export interface IntakeApi {
  list(): Promise<IntakeRow[]>
  get(intakeId: string): Promise<IntakeRecord>
  create(contextType: string, area: Record<string, string | null>, note: string): Promise<IntakeRecord>
  uploadEvidence(intakeId: string, files: File[]): Promise<IntakeEvidenceReceipt>
  transition(intakeId: string, to: string, note?: string): Promise<IntakeRecord>
  threadDecision(intakeId: string, decision: 'adds-value' | 'no-new-value'): Promise<IntakeRecord>
}

type EvidenceBody = Schemas['Body_post_intake_evidence_intake__intake_id__evidence_post']

export function createIntakeApi(baseUrl: string, personaId: string): IntakeApi {
  const { api } = createApiClient(baseUrl, personaId)

  // WEB8: the `record` helper that stood here claimed IntakeRecord for every
  // call. It cannot any more, and should not have then — the upload answers
  // with a different shape. `unwrap` infers each route's own declared type, so
  // the helper has nothing left to do.
  return {
    async list() {
      return unwrap(await api.GET('/intake'), 'intake').intakes
    },
    async get(intakeId) {
      return unwrap(
        await api.GET('/intake/{intake_id}', { params: { path: { intake_id: intakeId } } }),
        `intake ${intakeId}`,
      )
    },
    async create(contextType, area, note) {
      return unwrap(
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
      return unwrap(
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
      return unwrap(
        await api.POST('/intake/{intake_id}/transition', {
          params: { path: { intake_id: intakeId } },
          body: { to, note },
        }),
        `intake ${intakeId} transition`,
      )
    },
    async threadDecision(intakeId, decision) {
      return unwrap(
        await api.POST('/intake/{intake_id}/thread-decision', {
          params: { path: { intake_id: intakeId } },
          body: { decision },
        }),
        `intake ${intakeId} thread decision`,
      )
    },
  }
}
