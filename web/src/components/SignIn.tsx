import { PERSONAS, signIn, type Session } from '../lib/auth'

// Full-page persona picker — the no-session state. MOCK: picking a card IS the
// whole "authentication"; see lib/auth.ts for why this exists pre-O1-ADR.
// O30: styled inline via Tailwind/token classes (App.css retired).

const NOTE = 'mt-2 text-[13px] leading-[1.55] text-muted'
const ROLE_BADGE: Record<string, string> = {
  user: 'border-blue-bright bg-blue-bright/10 text-blue-bright',
  // DL-2: danger ≠ brand red
  admin: 'border-status-fail bg-status-fail/12 text-status-fail-soft',
}

export default function SignIn({ onSignIn }: { onSignIn: (s: Session) => void }) {
  return (
    <main className="mx-auto max-w-[520px] px-[30px] pt-[12vh]">
      <h1 className="mb-[18px] text-[34px] font-extrabold tracking-[-0.02em]">DryDocs Console</h1>
      <div className="rounded-md border border-edge bg-panel p-[18px]">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold">Sign in</h2>
          <span className="whitespace-nowrap rounded-xs border border-yellow/50 bg-yellow/8 px-[9px] py-1 font-mono text-[10.5px] font-medium text-yellow">
            MOCK SIGN-IN · SYNTHESIZED
          </span>
        </div>
        <p className={NOTE}>
          Persona selection only — no credentials, no real authentication. The real
          access path (bolt-from-browser vs thin API) is pending its ADR (backlog O1).
        </p>
        <div className="mt-3.5 flex flex-col gap-2.5">
          {PERSONAS.map((p) => (
            <button
              key={p.id}
              className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5 rounded-md border border-edge bg-bg-2 px-3.5 py-3 text-left transition-colors hover:border-faint"
              onClick={() => onSignIn(signIn(p.id))}
            >
              <span className="font-semibold">{p.displayName}</span>
              <span className="col-start-1 row-start-2 font-mono text-xs text-blue-bright">{p.id}</span>
              <span
                className={`col-start-2 row-start-1 self-start rounded-xs border px-2 py-[3px] font-mono text-[10.5px] font-semibold uppercase ${ROLE_BADGE[p.role] ?? ''}`}
              >
                {p.role}
              </span>
              <span className="col-span-2 row-start-3 text-xs text-muted">{p.chip}</span>
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}
