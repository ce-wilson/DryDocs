// MOCK AUTH — SYNTHESIZED personas with a localStorage session. No real security:
// anyone can pick any persona and nothing verifies it server-side. This exists so
// role-gated views can be built and demoed BEFORE the access-path decision
// (bolt-from-browser vs thin API — backlog item O1); real authn/authz arrives with
// that ADR and replaces this module. Persona ids are synthetic, never real SIDs
// (publish boundary).

export type Role = 'user' | 'admin'

export interface Persona {
  id: string
  displayName: string
  role: Role
  chip: string
}

export const PERSONAS: readonly Persona[] = [
  {
    id: 'jdoe4821',
    displayName: 'J. Doe',
    role: 'user',
    chip: 'app access derived from ServiceNow',
  },
  {
    id: 'asmith7734',
    displayName: 'A. Smith',
    role: 'admin',
    chip: 'platform admin · all towers',
  },
]

export interface Session {
  personaId: string
  role: Role
  signedInAt: string
}

const STORAGE_KEY = 'drydocs.mock-session.v1'

export function signIn(personaId: string): Session {
  const persona = PERSONAS.find((p) => p.id === personaId)
  if (!persona) throw new Error(`unknown persona: ${personaId}`)
  const session: Session = {
    personaId: persona.id,
    role: persona.role,
    signedInAt: new Date().toISOString(),
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  return session
}

export function signOut(): void {
  localStorage.removeItem(STORAGE_KEY)
}

// Role is re-derived from PERSONAS — the stored blob is untrusted, so a stale or
// hand-edited localStorage value can never invent a role. Any garbage → null.
export function currentSession(): Session | null {
  let raw: string | null
  try {
    raw = localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
  if (!raw) return null
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  if (typeof parsed !== 'object' || parsed === null) return null
  const { personaId, signedInAt } = parsed as { personaId?: unknown; signedInAt?: unknown }
  const persona = PERSONAS.find((p) => p.id === personaId)
  if (!persona) return null
  return {
    personaId: persona.id,
    role: persona.role,
    signedInAt: typeof signedInAt === 'string' ? signedInAt : '',
  }
}

export function personaFor(session: Session): Persona {
  const persona = PERSONAS.find((p) => p.id === session.personaId)
  if (!persona) throw new Error(`unknown persona: ${session.personaId}`)
  return persona
}
