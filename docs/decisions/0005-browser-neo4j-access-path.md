# ADR 0005 — Browser ↔ Neo4j access path: thin API is the deployment shape; bolt-from-browser survives only as a dev-mode adapter

```yaml
status: ACCEPTED        # PROPOSED | ACCEPTED | SUPERSEDED — accepted 2026-07-14, SME chad.wilson (in-session ratification; O3)
date: 2026-07-14
deciders: [chad.wilson]
layer: cross-cutting    # architecture; the web console is the layer-3 read surface, and layer-4 projections need a server-side home
affects:
  - web/src/lib/neo4j.ts               # today's bolt path — becomes the dev-mode adapter behind the seam
  - web/src/lib/auth.ts                # mock personas — module header already defers real authn/authz to this ADR
  - web/src/components/CypherConsole.tsx  # raw-Cypher panel + VITE_NEO4J_* defaults — gated + de-secreted by this ADR
  - docs/restructure/backlog.yaml      # O1 (this is its crux); spawns the thin-API build item at next groom
```

## Context

The web console (Epic O, `drydocs-web`) is a **read surface** over the knowledge
graph: towers, drill-downs, My Apps, and O1's real C4/graph rendering. Writes
never come from a browser — they go through loaders behind the HITL gate
(ADR 0002; working agreement "ontology edges are not casual"). The open
question O1 names as its crux: how does the browser reach Neo4j?

What exists today (post O2 merge):

- `web/src/lib/neo4j.ts` — `neo4j-driver` **in the browser** (bolt over
  WebSocket), one driver per page, sessions forced `READ`.
- `CypherConsole.tsx` — uri/user/password as form fields, defaulted from
  `VITE_NEO4J_URI` / `VITE_NEO4J_PASSWORD`. **Vite inlines `VITE_*` values into
  the built bundle** — a committed or CI-provided password becomes a secret
  inside a publishable artifact.
- `web/src/lib/auth.ts` — mock personas whose header comment explicitly says
  real authn/authz "arrives with that ADR and replaces this module."
- `agents/` — an ADK `api_server` REST tier the UI already calls
  (`web/src/lib/adk.ts`); a server tier is already part of the architecture.

The forces:

1. **Two deployment realities.** Producer sandbox: one developer, local Docker
   EE, an ephemeral `drydocs` DB, localhost creds. Company: bank network
   zoning (no bolt/7687 from user desktops), corporate SSO, SME/support users
   who will never hold database credentials, and app-access entitlements
   sourced from ServiceNow (the persona chip already anticipates this).
2. **The trust axis is the DB boundary** (ADR 0002 D1): `drydocs` (ground
   truth) vs `drydocs_context` (uncertain) vs the `drydocs_all` composite.
   Which database a console view reads is a **routing decision** that must be
   enforced somewhere, not left to whatever string reaches a session option.
3. **The publish boundary** (PUBLISH-BOUNDARY.md): no secrets in `web/`;
   `VITE_*` inlining makes the browser bundle structurally unable to hold them.
4. **Layer 4 is coming.** Context-graph = task-scoped projections (temporal
   state, ownership, permissions, health). Something server-side has to
   compute and scope those; the browser is the wrong altitude.

## Decision

**The thin API is the access path for any shared or company deployment.
Bolt-from-browser is retained only as a local dev mode. Both sit behind one
adapter seam in `web/src/lib/`, and the seam is the guarantee.**

Concretely:

1. **One `GraphAccess` interface** in `web/src/lib/` is the only way console
   code reads the graph. Two adapters implement it: `bolt` (today's
   `neo4j.ts`, refitted) and `api` (fetch to the thin API). View components
   never import `neo4j-driver` directly.
2. **The thin API is a new monorepo component** (per ADR 0002 D3's
   components-on-core pattern): server-side Neo4j driver, credentials from
   server env, **read-only enforcement and per-view database routing**
   (`drydocs` / `drydocs_all`) at the endpoint layer, named queries shaped for
   the console's views (towers, drill-downs, C4/graph payloads for NVL), plus
   a raw-Cypher endpoint gated to admin.
3. **Real authn/authz terminates at the thin API** — SSO/OIDC company-side,
   mapping identity → role + app entitlements (the ServiceNow derivation).
   It replaces `auth.ts`, exactly as that module's header promises.
4. **Dev-mode bolt** activates only behind an explicit dev flag + admin role:
   form-entered localhost credentials only; **no `VITE_NEO4J_PASSWORD` is ever
   committed or CI-injected**, keeping secrets out of the bundle by construction.

## Options considered

### A — Bolt-from-browser everywhere (status quo)

| Dimension | Assessment |
|---|---|
| Complexity | Low — already running |
| Cost | None new |
| Credential shape | Per-user Neo4j accounts, or a shared secret in browser/bundle |
| Network fit | Requires 7687/WebSocket desktop→DB — not routable in the company |
| Dev loop | Excellent |

**Rejected as the deployment shape** — structural, not taste: the browser sits
on the wrong side of *both* governing boundaries. The credential boundary — a
publishable bundle plus browser storage cannot hold secrets, and `VITE_*`
inlining turns configuration into leakage. The trust boundary — nothing
server-side enforces read-only or `drydocs` vs `drydocs_all` routing; it all
rides on client strings and RBAC config staying perfect. Company network
zoning independently kills it.

### A′ — Neo4j Query API (HTTP) from the browser

Same trust and credential shape as A, over HTTPS instead of bolt.
**Rejected: it changes the port, not the boundary.** Credentials still reach
the browser, routing is still client-decided, and there is still no home for
layer-4 projections — while giving up the driver's typing and routing without
gaining any control point.

### B — Thin API only (retire bolt everywhere, including local dev)

The purest shape. **Rejected for the sandbox**: it inserts a
build-and-run server between one developer and an ephemeral local database.
The Cypher console is today's SME/dev instrument for interrogating the graph,
and O1's remaining work (the real C4/graph render against local EE) is fastest
against bolt. Local-only, single-user, localhost creds: the deployment forces
simply don't apply there.

### C — Thin API as the deployment shape + dev-mode bolt behind one seam (**chosen**)

| Dimension | Assessment |
|---|---|
| Complexity | Medium — one new component + one interface refit |
| Cost | The thin API build (grooms into Epic O) |
| Credential shape | Server-side only in deployment; localhost form-entry in dev |
| Network fit | HTTPS/443; SSO-terminable |
| Dev loop | Preserved via the bolt adapter |

The seam is what makes the convenience safe: the `api` adapter is the default;
the `bolt` adapter activates only on dev flag + admin role, so sandbox habits
cannot silently become deployment behavior.

## Trade-off analysis

The deciding structure: **every force that distinguishes the two deployments —
credentials, SSO, network zoning, entitlements, layer-4 projections — lands
server-side; every force favoring bolt is local-dev-only.** So the architecture
splits exactly along the force line: server shape for deployment, bolt for the
bench, one interface so the split is enforced by types rather than discipline.

The thin API is also not net-new work invented by this ADR: NVL payload
shaping, per-view database routing, and eventually task-scoped context
projections have to be written *somewhere*. Writing them once server-side
beats duplicating them into a browser client that deployment then can't use.

## Consequences

- **Easier:** SSO/OIDC later (one termination point); read-only + DB routing
  enforced once; no secrets in `web/` by construction; server-shaped NVL
  payloads; a natural home for layer-4 projections; agents tier and console
  converge on one server discipline.
- **Harder:** one more component to build, run, and document (its build/run
  doc is already in O1's acceptance); two adapters to keep honest — the seam
  needs a conformance test so `bolt` and `api` don't drift; an HTTP hop of
  latency (immaterial at support-console scale).
- **Revisit if:** company policy ever grants per-user Neo4j accounts *and* an
  approved gateway exposes the Query API to desktops — reopening A′ then means
  arguing against the projection/SSO/routing reasons above, not just
  connectivity.

## Action items

1. [x] SME review of this ADR → `status: ACCEPTED` (satisfies O1's "decision
       recorded" acceptance clause). DONE 2026-07-14 — accepted as written
       (no edits); backlog O3.
2. [ ] Refit `web/src/lib/`: extract the `GraphAccess` interface; `neo4j.ts`
       becomes the bolt adapter behind it (O1, with the C4 render work).
3. [ ] Groom the thin-API component build into Epic O as a new backlog item
       (scope: read endpoints + per-view DB routing + gated raw-Cypher +
       auth stub) via the groom-backlog flow — not added here.
4. [ ] Gate `CypherConsole` raw-Cypher behind admin + dev flag (pairs with the
       design-review.md finding that Cypher-before-graph misorders the UI).
5. [ ] Verify no `VITE_NEO4J_PASSWORD` in any committed env file; document the
       dev-mode credential rule in `web/README.md`.
