import { PERSONAS, signIn, type Session } from '../lib/auth'

// Full-page persona picker — the no-session state. MOCK: picking a card IS the
// whole "authentication"; see lib/auth.ts for why this exists pre-O1-ADR.
export default function SignIn({ onSignIn }: { onSignIn: (s: Session) => void }) {
  return (
    <main className="signin-page">
      <h1>DryDocs Console</h1>
      <div className="signin-panel">
        <div className="signin-head">
          <h2>Sign in</h2>
          <span className="tag">MOCK SIGN-IN · SYNTHESIZED</span>
        </div>
        <p className="note">
          Persona selection only — no credentials, no real authentication. The real
          access path (bolt-from-browser vs thin API) is pending its ADR (backlog O1).
        </p>
        <div className="persona-list">
          {PERSONAS.map((p) => (
            <button key={p.id} className="persona-card" onClick={() => onSignIn(signIn(p.id))}>
              <span className="persona-name">{p.displayName}</span>
              <span className="persona-id">{p.id}</span>
              <span className={`role-badge role-${p.role}`}>{p.role}</span>
              <span className="persona-chip">{p.chip}</span>
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}
