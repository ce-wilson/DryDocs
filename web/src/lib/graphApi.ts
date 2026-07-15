import type { GraphAccess } from './graph'

// The deployment adapter: HTTP to the drydocs-api thin API (ADR 0005; the
// component is backlog O5). Deliberately fails loud until the endpoints
// exist — it must NEVER fall back to bolt silently, or the seam would leak
// the dev path into deployment behavior.
export function createApiAccess(baseUrl: string): GraphAccess {
  return {
    kind: 'api',
    async runRead(): Promise<never> {
      throw new Error(
        `drydocs-api is not available at ${baseUrl} — the api adapter goes live with ` +
          `backlog O5; until then dev-mode bolt (admin role + dev build) is the only live path`,
      )
    },
  } satisfies GraphAccess
}
