# ADR 0019 — Credential propagation to the agent tier: the agent authenticates itself, the console passes a session HANDLE, and no credential rides in a message part

```yaml
status: ACCEPTED        # drafted under WEB9 clause (a) and RULED option C by the user, both 2026-09-06 (desktop)
date: 2026-09-06
authored_by: the WEB9 draft, from the 2026-09-05 web module review finding S2 (docs/reviews/modules/web-2026-09-05.md)
deciders: [chad.wilson]
layer: cross-cutting    # the console (drydocs-web), the agent tier (agents/), and drydocs-api meet at one seam
relates_to:
  - 0005-browser-neo4j-access-path.md          # decision 3: the browser holds an opaque token; the server re-resolves role per request
  - 0007-agentic-qa-architecture.md       # decision 4: ephemeral session-scoped specs — the requirement whose CARRIER this ADR rules
  - agents/graph_qa/control.py                 # the in-band control part (R5) and its stored form (R23)
  - agents/common/session_redaction.py         # R23: the persistence seam, today's only defence
  - agents/common/ephemeral_client.py          # the agent's call back to drydocs-api — agent key + owner token
  - drydocs_api/ephemeral_specs.py             # register_ephemeral(agent_key, owner_token, ...); the store keyed (owner_token, ref)
  - drydocs_api/sessions.py                    # Session(token, persona_id) — a token and nothing else identifies a session
  - web/src/ask/askApi.ts                      # controlPart(apiToken, apiUrl) — where the credential leaves the trust boundary
backlog: [WEB9]
```

## Context

The Ask spoke (R5) sends two message parts to the ADK `api_server` on every turn:
the question, and a control part built by `controlPart(apiToken, apiUrl)` in
`web/src/ask/askApi.ts`:

```json
{ "text": "{\"drydocs_control\": {\"api_token\": \"<the browser's drydocs-api bearer token>\", \"api_url\": \"http://localhost:8001\"}}" }
```

The agent reads the control part (`graph_qa.control.split_question_and_control`),
and uses the token as the **owner token** when it registers each executed Cypher as
an ephemeral spec (`agents/common/ephemeral_client.py` →
`POST /specs/ephemeral`, ADR 0007 decision 4). The token is what scopes the spec
to the asking session: Open-in-Explorer and Export resolve the ref for that
session's bearer and nobody else's (`EphemeralSpecStore` keys on
`(owner_token, ref)`).

**The requirement is legitimate. The carrier is the finding** (web review S2,
2026-09-05). Message content is the one thing agent frameworks persist, replay,
echo and log; a credential placed there inherits the transcript's retention. Three
facts fix the weight of the problem:

1. **It has already leaked once, to disk.** ADK persists the user message
   verbatim, and on 2026-08-21 the desktop's `agents/graph_qa/.adk/session.db`
   held 10 events carrying a live `api_token` (R23 clause (d)). R23 (done
   2026-08-25) redacts the value on the way to the store by replacing the ONE ADK
   function `fast_api` calls to build the session service (`serve.py
   _install_control_redaction`, refusing to start if the seam moves). That is a
   correct fix for the sink it names, and a patch on a framework internal for
   every other sink: the SSE echo (redacted, because it is the stored event), the
   agent's own request logging, a future ADK trace exporter, an ADK upgrade that
   builds the service somewhere else. Each new sink is a new place to remember.
2. **The token is the browser's real session.** It is not scoped to
   registration: whoever holds it can call every authenticated read route as that
   persona until the O69 expiry. It crosses origins (`:5173` → `:8000`) to a server
   with no authentication of its own, in a body, over plain HTTP in every
   deployment that exists today.
3. **The blast radius is bounded, and the ADR should say so** rather than
   over-rule: the token is read-only, expires server-side (O69/O75), and the
   agent server is local in every deployment that exists. The exposure is a live
   read session for its remaining TTL, not a durable credential.

Company-side, OIDC replaces the whole handshake (ADR 0005, Evidence). The ruling
here should therefore be the one that is **closest to the OIDC end state** — a
service authenticating itself and a user identity travelling as a claim — so it is
replaced rather than unwound.

## Decision

**D1 — No credential rides in a message part. Ever.** The control part is
configuration and identity, never a secret. `SECRET_CONTROL_FIELDS` in
`graph_qa/control.py` stays as it is — `api_token` remains a redacted field — so a
stale console build that still sends one is still redacted at the store (defence in
depth, not the mechanism).

**D2 — The agent authenticates itself; the console passes a session HANDLE.**
The agent already holds a credential of its own: `DRYDOCS_AGENT_REG_KEY`, presented
as `X-Drydocs-Agent-Key` on `/specs/ephemeral`, is what makes it the trusted
registrar today. What the owner token contributes is only *which session owns the
spec*. That is identity, not authority, and identity can travel as a non-secret
handle:

- `drydocs_api/sessions.py`: a `Session` gains a **public `session_id`** minted
  beside the token at issue time (random, opaque, not derivable from the token,
  never accepted as a bearer). The login response returns both; the browser
  stores both.
- `controlPart(sessionId, apiUrl)` replaces `controlPart(apiToken, apiUrl)`; the
  control key becomes `session_id`. `api_token` is removed from the builder, and
  a test over `askApi` asserts the request body carries no token (WEB9 (b)).
- `register_ephemeral(agent_key, expected_key, owner_session, ...)` resolves the
  owner by `session_id` (a live session, else 401 exactly as today). The
  `EphemeralSpecStore` keys on `(session_id, ref)`; `resolve` on `/specs/{ref}/run`
  and `/export` maps the caller's bearer to its `session_id` first, so a ref still
  resolves only for the owning session.
- The API audit's actor on `/specs/ephemeral` (`audit.observe(token=...)`) records
  the owner's `session_id` — the correlation it was there for, without a
  credential in the audit line.

**D3 — What the handle authorizes, stated so it is not over-read.** A `session_id`
authorizes nothing on its own: `/specs/ephemeral` still requires the agent key, and
`/specs/{ref}/run` and `/export` still require the owner's bearer. A party holding
the agent key AND a `session_id` can register a spec into that session — which is
exactly what the agent can do today with the token, minus the ability to read as
that user. The registrar is the trusted party either way; this ADR removes the
part of the trust that was never needed.

**D4 — Persisted sessions that carry a token part (WEB9 (c)).** Both machines'
stores were inspected and the desktop's purged at R23 clause (d), 2026-08-25
(laptop: 4 events, none with a token, file predates R5). Under D1/D2 a new store
can never gain one from a current console. The only remaining path is a stale
console build against a current agent, and R23 redacts that at the seam. Ruling:
**no further purge; the R23 record is the record.** A store found to carry a
token after this ADR is a defect in the console build that sent it, not in the
store.

**D5 — Scope.** This ADR rules the carrier of session identity across the
console→agent boundary. It does not rule agent-tier authentication (the ADK server
still trusts its `--allow_origins` list and nothing else — that is WEB10's
delivery-shape question), and it does not change ADR 0007 decision 4's ephemeral
spec model (TTL, session scope, bounded store), only its owner key.

## Options considered

### A — Authorization header on the ADK call

The console sets `Authorization: Bearer <token>` on `/run` and `/run_sse`; a
FastAPI middleware in `serve.py` lifts it into a per-request context the agent
reads.

| Dimension | Assessment |
|---|---|
| Complexity | Medium — a middleware plus a contextvar, and a second `serve.py` patch on the ADK app |
| Credential still leaves the browser toward the agent tier | **Yes** — the real session token, in a header instead of a body |
| Persisted / echoed | No (headers are not message content) |
| Logged | Access logs omit headers by default; a debug or proxy log does not |
| Distance from the OIDC end state | Medium — a bearer on the call is OIDC-shaped, but it is the USER's bearer handed to a service |

**Pros:** smallest console change; no API change. **Cons:** the agent tier still
receives a credential that reads as the user everywhere; ADK's request pipeline is
not built to forward headers to the agent, so this is a second framework patch of
the R23 kind; leaves R23 as the only guard for every other sink. **Rejected**: it
moves the credential one field over and keeps every trust property that was wrong.

### B — Short-TTL exchange token minted by drydocs-api, scoped to registration

Before each turn the console calls `POST /sessions/exchange` and receives a token
valid for a short TTL and only on `/specs/ephemeral`; that token rides in the
control part.

| Dimension | Assessment |
|---|---|
| Complexity | **High** — a second token class, its store, TTL and scope checks; a pre-turn round trip; "single-use" does not hold because one turn registers several Cypher statements |
| Credential still leaves the browser toward the agent tier | Yes, but a scoped, short-lived one |
| Persisted / echoed | Yes — still message content; R23 still redacts |
| Logged | Yes, wherever content is logged; harmless after TTL |
| Distance from the OIDC end state | Medium — token exchange IS an OIDC pattern (RFC 8693), but built here by hand |

**Pros:** bounded blast radius by construction; the in-band carrier stays.
**Cons:** the most machinery of the three for a boundary that OIDC replaces; still
puts a credential in a transcript, just a weaker one; two token classes to reason
about in every audit line. **Rejected**: proportionate blast radius bought with
disproportionate mechanism — and the property the review actually asked for
("no credential lands in an agent transcript") is not met.

### C — Agent's own credential + a non-secret session handle (**chosen**)

| Dimension | Assessment |
|---|---|
| Complexity | Low–medium — one new field on `Session`, one key change in the ephemeral store, one control field renamed; the agent key already exists |
| Credential still leaves the browser toward the agent tier | **No** |
| Persisted / echoed | The HANDLE is, and may be — it authorizes nothing |
| Logged | Same — safe to log, useful in a trace |
| Distance from the OIDC end state | **Closest** — a service credential for the service, a subject identifier for the user |

**Pros:** meets the review's property literally; retires the framework patch as the
load-bearing defence (R23 becomes belt-and-braces); the handle is USEFUL in a
stored trace where a redaction marker is not; no new token class. **Cons:** touches
three modules (web, agents, api) in one change; the ephemeral store's key changes,
so existing refs (in-memory, TTL-bounded) do not survive the API restart that
ships it — acceptable, they never survived a restart.

## Trade-off analysis

The three options differ on one axis: **does a credential leave the browser toward
the agent tier at all?** A and B say yes and argue about how weak the credential
is; C says no and argues about whether identity needs to be secret. It does not:
the API already trusts the agent key to decide who may register, and the token was
only ever answering *for whom*. Separating *who may* from *for whom* is the same
move ADR 0005 decision 3 made for the browser (an opaque token, role re-resolved
server-side), applied one hop further.

The cost C pays is coordination — three modules, one change, and a restart that
drops in-flight ephemeral refs. That cost falls inside one repo and one commit
series; A's and B's costs (a second framework patch; a second token class) are paid
on every future audit.

## Consequences

- **Easier:** the R23 monkeypatch stops being the thing standing between a live
  credential and disk; an ADK upgrade that moves the seam degrades to "a redacted
  field that was never secret", not to a leak. Agent traces can carry the handle
  in the clear and correlate to the API audit by it.
- **Harder:** the login response and the stored auth blob gain a field; every
  fixture that builds a `Session` or an ephemeral spec learns `session_id`. The
  build is one item (WEB9 (b)) but crosses the `drydocs-web`, `drydocs-agents` and
  `drydocs-api` pens — it lands as one merged unit, not three.
- **Revisit:** when company-side OIDC lands, `session_id` becomes the subject
  claim and the agent key becomes a client credential; this ADR's shape is what
  that replaces, and the replacement should be a substitution, not a redesign.

## Action items (the build — WEB9 clause (b); ruled 2026-09-06, option C; built the same day on `wip/WEB9-desktop`)

1. [x] `drydocs_api/sessions.py`: `Session.session_id` minted at issue; `resolve_by_id`; login returns it.
2. [x] `drydocs_api/ephemeral_specs.py` + `app.py`: `owner_session` replaces `owner_token` on registration; store keyed `(session_id, ref)`; run/export map bearer → `session_id`; audit actor = `session_id`.
3. [x] `agents/common/ephemeral_client.py` + `graph_qa/agent.py`: send `owner_session`; `control.get("session_id")`.
4. [x] `web/src/ask/askApi.ts` + `lib/auth.ts`: store `sessionId`; `controlPart(sessionId, apiUrl)`; the request-body-has-no-token test.
5. [x] `graph_qa/control.py`: docstring names `session_id` as the control field; `api_token` stays in `SECRET_CONTROL_FIELDS` with a one-line reason (stale builds).
6. [x] `dump_openapi.py --check`, `npm run api:types`; ADR 0007 decision 4 gains a one-line pointer here.
