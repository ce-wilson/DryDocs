# ADR 0005 — Browser↔Neo4j access path: a thin API, not bolt-from-browser

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED — the SME call that closes O1's crux
date: 2026-07-14
deciders: [chad.wilson, main]
layer: graph-infra / drydocs-web boundary
affects:
  - web/src/lib/neo4j.ts          # today's bolt-from-browser path
  - web/src/lib/auth.ts           # the O2 mock login this decision eventually replaces
  - agents/common/neo4j_tool.py   # the read-only-guard precedent the API generalizes
  - docs/restructure/backlog.yaml # O1 (this IS its acceptance's "decision recorded"); follow-up items on acceptance
  - MODULE_MAP.md                 # a new Python component if the API is built producer-side
  - PUBLISH-BOUNDARY.md           # secrets move server-side; SSO wiring is a company-side twin
```

## Context

The web console needs a decided answer to *how the browser reaches Neo4j*. Today
`web/` is a sandbox: the bundled `neo4j-driver` opens a bolt/WebSocket connection
**from the browser**, with the database URI, user, and password typed into form
fields (`web/src/lib/neo4j.ts`, seeded from `VITE_NEO4J_*`). That was fine for a
throwaway test page; it cannot carry the console's real requirements:

- **Real sign-in.** The O2 mock persona login (localStorage, zero security) was
  built deliberately decision-neutral so the design pass could proceed. Its
  replacement is *shaped by this decision*: bolt-from-browser implies every
  console user is a Neo4j user (native auth + EE RBAC); a thin API implies app
  sessions with the server holding one service credential.
- **The live graph view.** O1's remaining build (a real C4/graph rendering
  against the live EE DB) issues live queries; whether they travel over a
  browser WebSocket or an HTTP endpoint shapes the whole data layer.
- **Credential hygiene.** Browser-held DB credentials mean the database is
  network-reachable from, and its secret present in, every client. The publish
  boundary already forbids secrets in `web/`; bolt-from-browser structurally
  fights that.
- **Write protection.** The standing rule — graph writes go through loaders +
  the HITL gate, never through an interactive surface — is enforced today by
  `agents/common/neo4j_tool.py`'s write-token guard on the ADK path. The
  browser bolt path has no equivalent enforcement point short of DB-level roles.

Related precedent: the console already has a *second*, server-mediated data path
— the ADK `api_server` (browser → HTTP → agent → Neo4j, read-only guard
included). Bolt-from-browser is the outlier path, not the norm, even inside this
repo.

## Evidence — the company deployment already runs the thin-API pattern

*Sanitized, mechanism-not-instance, per PUBLISH-BOUNDARY / the back-flow rule.
Source: company-side module documentation reviewed 2026-07-14 (screenshot held
out of the repo); endpoint names, hostnames, and module identifiers withheld.*

The company environment operates an interactive web application whose access
architecture is exactly the thin-API shape:

1. **Interactive user SSO, server-side.** A Python API server (FastAPI-class)
   fronts browser users via the enterprise OIDC identity provider: login route →
   IdP redirect → callback → authorization-code-for-token exchange → JWT
   validated (signature + issuer, with issuer auto-discovery) → the user's
   corporate SID stored in the **server** session. Role claims are extracted
   server-side from validated claims.
2. **Machine-to-machine credentials never reach the browser.** Service-to-service
   tokens (LLM suite scope) are fetched by a certificate-authenticated service
   principal, cached and auto-refreshed **in the server process**; key material
   lives on the server filesystem.
3. **Host-aware identity dispatch.** A third integration selects its identity
   mechanism per host (desktop Kerberos vs OAuth2 on servers) — again resolved
   at the server/process layer, never in a client.

Implications for this decision:

- A browser holding database credentials would be an **architectural outlier**
  in the company environment; there is no enterprise SSO path for
  bolt-from-browser (the IdP speaks OIDC to server apps, not bolt to Neo4j).
- The thin API is not an invented architecture — the company port would *align*
  with an in-production pattern, and the eventual SSO wiring is a swap-in
  (company twin) rather than a redesign.
- The O2 mock maps 1:1 onto that pattern: mock persona id → session SID; the
  `views.ts` role registry → roles-from-claims; the sign-in screen → the IdP
  redirect. The mock was built as a placeholder for exactly this shape.

## Options considered

### A — Bolt-from-browser (status quo generalized) — REJECTED (proposed)

Browser keeps the bundled `neo4j-driver`; real login = Neo4j native users; user
vs admin = EE RBAC roles; the graph view queries bolt directly.

- **For:** zero new infrastructure; real DB-level enforcement (RBAC is not
  cosmetic); EE already supports it; one less process to run locally.
- **Against (structural):** every console user must exist as a Neo4j user
  (provisioning burden, no SSO path — the enterprise IdP cannot authenticate a
  bolt handshake); DB credentials and network reachability exposed to every
  browser; no single enforcement point for the read-only rule (DB roles only);
  CORS/WebSocket posture in a corporate network; contradicts the company's
  in-production pattern (Evidence) so the port would diverge, not align.

### B — Thin API (RECOMMENDED)

A minimal Python API service owns the Neo4j driver: it holds the one service
credential, exposes scoped **read** endpoints for the console (graph view,
label counts, drill queries), enforces authn (sessions; enterprise OIDC on the
company side, local stub on the producer side) and authz (role → endpoint map,
the server-side twin of `views.ts`), and generalizes the
`agents/common/neo4j_tool.py` write-token guard as its single write-protection
point.

- **For:** credentials server-side only; SSO-compatible (Evidence — the pattern
  is in production company-side); one enforcement point for read-only + role
  gating; the browser needs nothing but HTTP; converges with the ADK path
  instead of maintaining a parallel bolt path; testable with the existing
  offline patterns (pure handlers + a duck-typed graph runner, the
  `graph_verify` precedent).
- **Against:** a new component to build, run, and port (module boundary, CORS,
  deploy surface); some duplication with the ADK `api_server` (mitigated below);
  local dev needs one more process (mitigated: the admin sandbox can keep
  direct bolt as a dev tool — see Consequences).

### C — Hybrid: API for product surfaces, bolt kept as a dev tool — folded into B

Not a distinct architecture: under B, the existing admin-only Cypher sandbox may
keep its direct-bolt flow as a **local development tool** (it is already gated
behind the admin role and labeled as pre-dating this ADR). Product surfaces
(landing, drill-downs, My Apps, the live graph view) go through the API only.
Whether the sandbox's bolt flow survives long-term is a later cleanup call, not
part of this decision.

## Decision (proposed)

**Option B.** The browser↔Neo4j access path is a thin API:

1. **New Python component** (working name `drydocs-api`; final name at scaffold
   time) in the monorepo on `drydocs-core`, per the ADR 0002 component rules:
   its own `COMPONENT_GROUP` in `tests/unit/test_module_boundary.py` +
   MODULE_MAP row; imports core only; **read-only against the graph** — it
   reuses/generalizes the write-token guard so no interactive surface can write
   (writes remain loaders + HITL gate only).
2. **Not** an extension of the ADK `api_server`: that process is an agent
   runtime (LLM keys, sessions, eventing), not a query API; coupling the console
   to it would drag agent dependencies into every console deploy. The two share
   the guard pattern and may share a host, nothing more.
3. **Auth in two stages:** producer-side, the API issues real server sessions
   with the two synthetic personas replacing the localStorage mock (the browser
   stops holding role truth); company-side, the session issuer swaps to the
   enterprise OIDC flow (SID + roles-from-claims) as a gitignored/internal twin,
   per the Evidence pattern. `web/src/lib/auth.ts` and the `views.ts` registry
   survive as the client cache of what the server says, not the authority.
4. **Deliberately not decided here:** endpoint shapes, the graph-view rendering
   library (NVL vs successor), session transport details (cookie vs bearer),
   and the sandbox bolt flow's retirement date.

## Consequences

- The **O2 mock login is formally transitional** — its replacement path is now
  named. The mock banner's "pending the O1 access-path ADR" line resolves to
  this document once accepted.
- `web/src/lib/neo4j.ts` stops being the product data path; new console features
  must not extend it (admin sandbox dev-tool use excepted, per Option C note).
- The local EE container's placeholder password (parked IDEAS chore) becomes
  **server config** — change it when the API lands; it never ships to a browser
  again.
- Company port story: the producer ships the generic API + local-session stub;
  the OIDC wiring is a company-side supplement (the H4/H5 gitignored-twin
  convention). PORT-MANIFEST gains the component's rows at scaffold time.
- Rejected alternative recorded so it is not re-litigated: bolt-from-browser
  fails on SSO-incompatibility + credential exposure + no single read-only
  enforcement point — re-proposing it means answering those three, not
  rediscovering them.

## Follow-ups (groom into Epic O on acceptance)

1. `drydocs-api` scaffold: component boundary + session auth (synthetic
   personas server-side) + first read endpoint; web/ login switches to it.
2. Live C4/graph view over the API against the local EE DB (the remaining O1
   build), rendering library decision folded in.
3. Sandbox bolt flow disposition (keep as dev tool vs retire) once 1–2 land.
