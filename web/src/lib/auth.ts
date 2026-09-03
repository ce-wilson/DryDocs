// Console authentication (O69). Signing in means proving a secret to
// drydocs-api and holding the opaque token it returns; the persona picker that
// stood here from O2 until 2026-08-28 was a client-side choice with nothing
// verifying it, and the banner said so.
//
// WHAT THE BROWSER HOLDS: a token and its expiry. Never the secret — that is
// sent once, on the login call, and is not stored anywhere. Never a role that
// matters: `role` below drives which nav entries render, and the SERVER
// re-resolves the real one from the token on every request (ADR 0005 decision
// 3). Editing the stored blob by hand still buys nothing, because the fields
// that gate anything are re-derived from PERSONAS here and re-checked there.
//
// THE IDS ARE OBVIOUSLY FICTIONAL, and that is the point rather than a joke.
// They were SID-shaped until 2026-08-28 (jdoe4821, asmith7734, kchen2190),
// which read as realistic in a demo and carried a standing risk with it: an id
// that looks like a real corporate SID is one somebody can mistake for one, in
// a screenshot, a bug report, or a file that escapes the publish boundary. A
// name no directory could ever issue cannot be mistaken that way. The secrets
// behind them are machine-local — see drydocs_api/credentials.py and
// scripts/set_console_credential.py.

import { createPublicApi, detailOf } from './apiClient'

export type Role = 'user' | 'steward' | 'admin'

export interface Persona {
  id: string
  displayName: string
  role: Role
  chip: string
  /** the tower this persona's apps roll up to — users may drill only their own */
  towerKey?: string
}

export const PERSONAS: readonly Persona[] = [
  {
    id: 'morpheus',
    displayName: 'Morpheus',
    role: 'admin',
    chip: 'platform admin · all towers',
  },
  {
    id: 'trinity',
    displayName: 'Trinity',
    role: 'steward',
    chip: 'mapping steward · manual tiers (O13)',
  },
  // O47: the intake persona. Deliberately role 'user' — SME is WHO they are,
  // not a fourth role tier (adding one would ripple through canAccessModule
  // for a single page). /intake gates on `id === SME_PERSONA_ID || role !==
  // 'user'`, and towerKey scopes the area cascade's default exactly as it
  // scopes the other user-tier drills. NOTE: the plan says "towerId"; the
  // roster field has been towerKey since O-series auth landed — field name wins.
  {
    id: 'neo',
    displayName: 'Neo',
    role: 'user',
    chip: 'app-support SME · context intake',
    towerKey: 'home',
  },
  // Three user-tier seats, identical in rights and distinct only in identity.
  // Several console behaviours are scoped per PERSONA rather than per role —
  // the Ask panel's stored last turn is the case O64 tested — and proving that
  // isolation needs two accounts that differ in nothing else.
  {
    id: 'mouse',
    displayName: 'Mouse',
    role: 'user',
    chip: 'app access derived from ServiceNow',
    towerKey: 'home',
  },
  {
    id: 'tank',
    displayName: 'Tank',
    role: 'user',
    chip: 'app access derived from ServiceNow · second seat',
    towerKey: 'home',
  },
  {
    id: 'dozer',
    displayName: 'Dozer',
    role: 'user',
    chip: 'app access derived from ServiceNow · third seat',
    towerKey: 'home',
  },
]

/** The persona whose ?as= id opens /intake without steward/admin role (O47). */
export const SME_PERSONA_ID = 'neo'

/** May this persona open the intake page? SME persona, steward, or admin. */
export function canAccessIntake(persona: Persona): boolean {
  return persona.id === SME_PERSONA_ID || persona.role !== 'user'
}

/** The one place the API base URL is decided for auth calls. */
export function apiBaseUrl(): string {
  return (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8001'
}

export interface Session {
  personaId: string
  role: Role
  signedInAt: string
  /** The opaque bearer token. The server is the only thing that can read it. */
  token: string
  /** ISO-8601. The server enforces this; the client honours it so the shell
   *  does not render a signed-in console whose every call is about to 401. */
  expiresAt: string
}

const STORAGE_KEY = 'drydocs.session.v2'

/** Thrown when the credentials are refused. Carries no detail about WHICH half
 *  was wrong, because the server deliberately does not say. */
export class SignInError extends Error {}

/** Sign in against drydocs-api. The secret leaves this function in one request
 *  and is never stored. */
export async function signIn(personaId: string, secret: string): Promise<Session> {
  // O70: the public typed client — no session yet, so no bearer middleware. The
  // path, the body (LoginBody) and the response (LoginOut) are the server's own
  // declaration; a login response this console cannot read is now a compile
  // error here rather than a runtime check.
  const { data, error, response } = await createPublicApi(apiBaseUrl())
    .POST('/login', { body: { persona_id: personaId, secret } })
    .catch((err: unknown) => {
      // O85: a dead server and a blocked origin are the same TypeError to fetch;
      // the client's probe has already said which, and this keeps its message.
      throw new SignInError(err instanceof Error ? err.message : String(err))
    })
  if (error !== undefined || !response.ok || !data) {
    // A non-JSON refusal body is still a refusal; the server's one message for
    // both a wrong secret and an unknown id is deliberate (account enumeration).
    throw new SignInError(detailOf(error, response) || 'invalid credentials')
  }
  const persona = PERSONAS.find((p) => p.id === data.persona_id)
  if (!persona) throw new SignInError(`server issued a session for unknown persona: ${data.persona_id}`)
  const session: Session = {
    personaId: persona.id,
    role: persona.role,
    signedInAt: new Date().toISOString(),
    token: data.token,
    expiresAt: data.expires_at,
  }
  store(session)
  return session
}

function store(session: Session): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  } catch {
    // A console that cannot persist still works for this tab; a reload signs
    // out. Failing the sign-in over it would be worse.
  }
}

/** Clear the local session, and tell the server to forget the token too. The
 *  server call is best-effort: a browser that is closing, or an API that is
 *  down, must not leave the user looking signed in. */
export function signOut(): void {
  const session = currentSession()
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* nothing to clear */
  }
  if (!session) return
  // The token is passed explicitly: the local session is already gone, so the
  // authed client (which reads it) is the wrong tool here. Plain fetch, not the
  // diagnosing one — a best-effort revoke must not spend a reachability probe.
  void createPublicApi(apiBaseUrl())
    .POST('/logout', {
      headers: { Authorization: `Bearer ${session.token}` },
      fetch: (request) => globalThis.fetch(request),
    })
    .catch(() => undefined)
}

/** The stored session, or null. Any garbage, any missing token, and any
 *  expiry that has passed all read as signed out — the sign-in screen is the
 *  one recovery path, and it must be reachable from every bad state. */
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
  const { personaId, signedInAt, token, expiresAt } = parsed as {
    personaId?: unknown
    signedInAt?: unknown
    token?: unknown
    expiresAt?: unknown
  }
  if (typeof token !== 'string' || !token) return null
  // Role is re-derived from PERSONAS — the stored blob is untrusted, so a stale
  // or hand-edited value can never invent a role client-side, and the server
  // re-resolves it from the token regardless.
  const persona = PERSONAS.find((p) => p.id === personaId)
  if (!persona) return null
  const expiry = typeof expiresAt === 'string' ? expiresAt : ''
  if (expiry && Date.parse(expiry) <= Date.now()) return null
  return {
    personaId: persona.id,
    role: persona.role,
    signedInAt: typeof signedInAt === 'string' ? signedInAt : '',
    token,
    expiresAt: expiry,
  }
}

/** The current bearer token, or null. The HTTP clients read it here rather
 *  than being handed a persona id they could log in with on their own. */
export function sessionToken(): string | null {
  return currentSession()?.token ?? null
}

/** Drop the local session because the server refused its token. Distinct from
 *  signOut(): there is no point telling the server to revoke a token it has
 *  already rejected, and the caller is mid-request. */
export function sessionRejected(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* nothing to clear */
  }
  window.dispatchEvent(new CustomEvent(SESSION_REJECTED_EVENT))
}

/** Fired when the server refuses the held token. App.tsx listens and drops to
 *  the sign-in screen, so one 401 anywhere signs the console out everywhere
 *  rather than leaving a dead shell rendering empty panels. */
export const SESSION_REJECTED_EVENT = 'drydocs:session-rejected'

export function personaFor(session: Session): Persona {
  const persona = PERSONAS.find((p) => p.id === session.personaId)
  if (!persona) throw new Error(`unknown persona: ${session.personaId}`)
  return persona
}
