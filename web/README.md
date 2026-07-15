# DryDocs Console (web/)

## Mock persona sign-in (SYNTHESIZED)

The console is gated by a **mock** persona sign-in — a client-side picker with a
localStorage session (`drydocs.mock-session.v1`) and **zero real security**: anyone
can pick any persona; nothing is verified anywhere. It exists so role-gated views
can be built and demoed now. **This is not an architecture decision** — the real
access path (bolt-from-browser vs a thin API) is still open as backlog item O1's
ADR, and real authn/authz arrives with that decision, replacing `src/lib/auth.ts`.

Two synthetic personas (never real SIDs — publish boundary):

| Persona | Role | Sees |
|---|---|---|
| `jdoe4821` (J. Doe) | user | My Apps only (read-only, ServiceNow-derived app access, synthesized) |
| `asmith7734` (A. Smith) | admin | everything: Console (the bolt/ADK sandbox), Posture & Governance placeholder, cosmetic Prod\|UAT\|Dev env toggle, My Apps |

Role gating lives in one place, `src/lib/views.ts` (`canSee` / `viewFromHash` —
unauthorized deep links fall back to the role's default view). The ADK agent flow
uses the signed-in persona id as its `userId`.

Run it: `cp .env.example .env.local` (point `VITE_NEO4J_URI` at your local Neo4j,
e.g. the EE container on `bolt://localhost:7689`), then `npm install && npm run dev`.

## Graph access (ADR 0005) — the GraphAccess seam

Console code reads the graph ONLY through the `GraphAccess` interface
(`src/lib/graph.ts`); view components never import `neo4j-driver`. Two adapters:

- **`api`** (`src/lib/graphApi.ts`) — the deployment path (the `drydocs-api`
  thin API); fails loud until that component lands, never silently falls back
  to bolt.
- **`bolt`** (`src/lib/neo4j.ts`) — a **dev-mode tool only**: reachable only in
  dev builds (`import.meta.env.DEV`) AND for the admin role (`boltAllowed()`);
  production bundles have the path compiled out.

**Dev-mode credential rule:** the Neo4j password is form-entered at runtime,
localhost targets only. Never define `VITE_NEO4J_PASSWORD` in any env file or
CI — Vite inlines `VITE_*` values into the built bundle, so a committed or
injected password becomes a secret inside a publishable artifact.

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
