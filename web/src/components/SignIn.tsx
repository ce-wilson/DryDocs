import { useState } from 'react'
import { PERSONAS, signIn, SignInError, type Persona, type Session } from '../lib/auth'

// Full-page sign-in — the no-session state. O69: picking a card no longer signs
// anybody in; it chooses WHICH account to prove a secret for, and the secret is
// checked by drydocs-api. The accounts are still synthetic, and the secrets that
// back them are machine-local: a fresh clone has none, and the API says so in
// the error rather than failing silently.
// O30: styled inline via Tailwind/token classes (App.css retired).

const NOTE = 'mt-2 text-[13px] leading-[1.55] text-muted'
const ROLE_BADGE: Record<string, string> = {
  user: 'border-blue-bright bg-blue-bright/10 text-blue-bright',
  // DL-2: danger ≠ brand red
  admin: 'border-status-fail bg-status-fail/12 text-status-fail-soft',
}

export default function SignIn({ onSignIn }: { onSignIn: (s: Session) => void }) {
  const [selected, setSelected] = useState<Persona | null>(null)
  const [secret, setSecret] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  function choose(persona: Persona) {
    setSelected(persona)
    setSecret('')
    setError(null)
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!selected || pending) return
    setPending(true)
    setError(null)
    try {
      onSignIn(await signIn(selected.id, secret))
    } catch (err) {
      // The server does not say which half was wrong, and neither do we.
      setError(err instanceof SignInError ? err.message : String(err))
      setSecret('')
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="mx-auto max-w-[520px] px-[30px] pt-[12vh]">
      <h1 className="mb-[18px] text-[34px] font-extrabold tracking-[-0.02em]">DryDocs Console</h1>
      <div className="rounded-md border border-edge bg-panel p-[18px]">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold">Sign in</h2>
          <span className="whitespace-nowrap rounded-xs border border-edge bg-bg-2 px-[9px] py-1 font-mono text-[11px] font-medium text-muted">
            SYNTHETIC ACCOUNTS
          </span>
        </div>
        <p className={NOTE}>
          {selected
            ? 'Enter this account’s secret. It is checked by drydocs-api and never stored in the browser.'
            : 'Choose an account, then prove its secret. The identities are synthetic; their secrets are machine-local and set with scripts/set_console_credential.py.'}
        </p>
        <div className="mt-3.5 flex flex-col gap-2.5">
          {PERSONAS.map((p) => (
            <button
              key={p.id}
              type="button"
              aria-pressed={selected?.id === p.id}
              className={`grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5 rounded-md border px-3.5 py-3 text-left transition-colors ${
                selected?.id === p.id
                  ? 'border-blue-bright bg-blue-bright/8'
                  : 'border-edge bg-bg-2 hover:border-faint'
              }`}
              onClick={() => choose(p)}
            >
              <span className="font-semibold">{p.displayName}</span>
              <span className="col-start-1 row-start-2 font-mono text-xs text-blue-bright">{p.id}</span>
              <span
                className={`col-start-2 row-start-1 self-start rounded-xs border px-2 py-[3px] font-mono text-[11px] font-semibold uppercase ${ROLE_BADGE[p.role] ?? ''}`}
              >
                {p.role}
              </span>
              <span className="col-span-2 row-start-3 text-xs text-muted">{p.chip}</span>
            </button>
          ))}
        </div>

        {selected && (
          <form className="mt-4 flex flex-col gap-2.5" onSubmit={submit}>
            <label className="text-[13px] font-medium text-muted" htmlFor="console-secret">
              Secret for {selected.id}
            </label>
            <input
              id="console-secret"
              type="password"
              autoComplete="current-password"
              autoFocus
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              className="rounded-md border border-edge bg-bg-2 px-3 py-2 font-mono text-sm outline-none focus:border-blue-bright"
            />
            <button
              type="submit"
              disabled={pending || secret.length === 0}
              className="rounded-md border border-blue-bright bg-blue-bright/12 px-3.5 py-2 font-semibold text-blue-bright transition-colors hover:bg-blue-bright/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pending ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        )}

        {error && (
          <p
            role="alert"
            className="mt-3 rounded-md border border-status-fail/50 bg-status-fail/10 px-3 py-2 text-[13px] text-status-fail-soft"
          >
            {error}
          </p>
        )}
      </div>
    </main>
  )
}
