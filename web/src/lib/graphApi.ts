import { type Api, createAuthedApi, requireToken, type Schemas, type SessionHooks, unwrap } from './apiClient'
import { sessionRejected, sessionToken } from './auth'
import type { GraphAccess, GraphResult, NamedResult, SpecExport, SpecResult } from './graph'

// The deployment adapter (ADR 0005): HTTP to the drydocs-api thin API.
// Sessions are server-side; this adapter READS the token the sign-in flow
// obtained and never obtains one itself. It must NEVER fall back to bolt
// silently, or the seam would leak the dev path into deployment behavior —
// every failure here is loud.
//
// O69 CHANGED THE 401 BEHAVIOUR, and the change is the point rather than a
// side effect. This client used to hold a persona id and silently log in
// again on any 401, which was only possible because logging in took no
// secret; a client that can re-authenticate itself out of a rejection is a
// client for which the rejection means nothing. Now a 401 is terminal: the
// local session is dropped, the app is told, and the user lands on the
// sign-in screen. Expiry and revocation therefore actually take effect.
//
// O70 REPLACED THE TRANSPORT UNDERNEATH THE SEAM. The fetch calls below are
// openapi-fetch over the generated `paths` (lib/apiClient.ts): the path
// literals, the path/query parameters, the JSON bodies and the response types
// all come from drydocs-api's own OpenAPI schema, so a server change the
// console has not caught up with fails `tsc -b` instead of a page. The
// GraphAccess interface (lib/graph.ts) is untouched — the components consume
// exactly what they did — and the assertions below pin its hand-owned result
// types to the server's declared ones.

const SESSION: SessionHooks = { token: sessionToken, rejected: sessionRejected }

/** The shared HTTP client behind every drydocs-api surface (GraphAccess here;
 *  the O13 mappings client in mappingsApi.ts, the O47 intake client). One auth
 *  policy — read the session's token, treat a 401 as the end of that session —
 *  so no surface can drift its own behaviour on rejection. */
export interface ApiClient {
  /** The typed drydocs-api client (O70). Every call goes through it; a path or
   *  body the schema does not declare does not compile. */
  readonly api: Api
  /** The session's own bearer token. R5 hands it to the graph_qa agent as the
   *  R4 owner token, so ephemeral specs the agent registers resolve for THIS
   *  session's runSpec/exportSpec calls — which is why the Ask spoke must
   *  share ONE client between token and GraphAccess. Rejects when there is no
   *  session; it cannot create one. */
  getToken(): Promise<string>
}

// personaId is kept in the signature for the ~15 call sites that pass it and
// for the error text; it is no longer a credential, because it never was one.
export function createApiClient(baseUrl: string, personaId: string): ApiClient {
  return {
    api: createAuthedApi(baseUrl, SESSION, personaId),
    async getToken(): Promise<string> {
      return requireToken(SESSION, personaId)
    },
  }
}

// The seam's result types stay hand-owned (ADR 0005; the components import
// graph.ts, never the schema). These pin them to the server's declaration:
// if drydocs_api.schemas drops or retypes a field the seam promises, this
// file stops compiling HERE, which is the whole point of generating the
// client. An extra server field (SpecRunOut.ephemeral) is fine — the seam
// promises a subset.
type Extends<A, B> = A extends B ? true : false
type AssertTrue<T extends true> = T
export type NamedRunOutCoversNamedResult = AssertTrue<Extends<Schemas['NamedRunOut'], NamedResult>>
export type SpecRunOutCoversSpecResult = AssertTrue<Extends<Schemas['SpecRunOut'], SpecResult>>

export function createApiAccess(
  baseUrl: string,
  personaId: string,
  client: ApiClient = createApiClient(baseUrl, personaId),
): GraphAccess {
  const { api } = client

  return {
    kind: 'api',
    async runRead(query: string): Promise<GraphResult> {
      const { keys, rows } = unwrap(await api.POST('/raw-cypher', { body: { cypher: query } }), 'api /raw-cypher')
      return { keys, rows }
    },
    async runNamed(queryId: string, params = {}): Promise<NamedResult> {
      const { keys, rows, database } = unwrap(
        await api.POST('/query/{query_id}', { params: { path: { query_id: queryId } }, body: { params } }),
        `api /query/${queryId}`,
      )
      return { keys, rows, database }
    },
    async runSpec(specId: string, params = {}): Promise<SpecResult> {
      return unwrap(
        await api.POST('/specs/{spec_id}/run', { params: { path: { spec_id: specId } }, body: { params } }),
        `spec ${specId}`,
      )
    },
    async exportSpec(specId, params, format): Promise<SpecExport> {
      const exported = await api.POST('/specs/{spec_id}/export', {
        params: { path: { spec_id: specId }, query: { format } },
        body: { params },
        parseAs: 'blob',
      })
      const blob = unwrap(exported, `export ${specId}`) // stream fully consumed → manifest registered
      const exportId = exported.response.headers.get('X-DryDocs-Export-Id')
      const disposition = exported.response.headers.get('Content-Disposition') ?? ''
      const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `${specId}.${format}`
      if (!exportId) throw new Error('export missing export id header')
      // The manifest is a ledger record and stays a free object server-side on
      // purpose; the typed path is what the schema checks here.
      const manifest = unwrap(
        await api.GET('/exports/{export_id}/manifest', { params: { path: { export_id: exportId } } }),
        'manifest fetch',
      ) as Record<string, unknown>
      return { filename, blob, manifest }
    },
  } satisfies GraphAccess
}
