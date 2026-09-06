import { useMemo, type ReactNode } from 'react'

import { apiBaseUrl } from '../lib/auth'
import { createApiAccess, createApiClient } from '../lib/graphApi'
import { GraphAccessContext, type GraphAccessValue } from './graphAccess'

/** WEB12 — ONE GraphAccess for the session, mounted above the routes.
 *
 * Sixteen routes used to build their own with
 * `useMemo(() => createApiAccess(apiUrl, persona.id), [...])`, each re-deriving
 * the base URL from import.meta.env beside `apiBaseUrl()` which already did it.
 * One client per session is not only tidier: it is what lets the R4 ephemeral
 * specs the Ask agent registers resolve for this session's later reads.
 *
 * It is alone in this file so the module exports exactly one component — the
 * fast-refresh rule oxlint enforces, and WEB13 is about to make warnings fatal.
 */
export function GraphAccessProvider({
  personaId,
  children,
}: {
  personaId: string
  children: ReactNode
}) {
  const value = useMemo<GraphAccessValue>(() => {
    const apiUrl = apiBaseUrl()
    const client = createApiClient(apiUrl, personaId)
    return {
      access: createApiAccess(apiUrl, personaId, client),
      apiUrl,
      getSessionId: client.getSessionId,
    }
  }, [personaId])
  return <GraphAccessContext.Provider value={value}>{children}</GraphAccessContext.Provider>
}
