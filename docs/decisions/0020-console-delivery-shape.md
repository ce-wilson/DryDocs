# ADR 0020 — The console's delivery shape: same-origin behind one reverse proxy, the API base is a PATH, and a production bundle inlines no deployment coordinate

```yaml
status: PROPOSED        # drafted under WEB10 clause (a), 2026-09-06 (desktop); awaiting the user's ruling
date: 2026-09-06
authored_by: the WEB10 draft, from the 2026-09-05 web module review finding S3 (docs/reviews/modules/web-2026-09-05.md)
deciders: [chad.wilson]
layer: cross-cutting    # the console (drydocs-web), drydocs-api and the agent tier (agents/) share one origin or do not
relates_to:
  - 0005-browser-neo4j-access-path.md          # settled ACCESS: the thin API; "HTTPS/443; SSO-terminable" is the deployment it names
  - 0019-credential-propagation-to-the-agent-tier.md   # the console -> agent hop this ADR puts on the same origin
  - 0014-runtime-substrate.md                  # everything configurable, nothing hardcoded; per-machine facts live in env
  - web/src/lib/auth.ts                        # apiBaseUrl(): the ONE definition of the API base (WEB12 collapsed 16 files to it)
  - web/src/lib/reachability.ts                # O85: the probe that tells "blocked origin" from "down" - the cost of cross-origin, in code
  - drydocs_api/app.py                         # create_app(): the CORS allowlist and DRYDOCS_CORS_ORIGINS
  - agents/serve.py                            # --allow_origins: the SECOND allowlist, for the agent server
  - web/playwright.config.ts                   # the O80 suite: three dedicated ports, one of them an origin the allowlist must learn
backlog: [WEB10, O72, WEB12]
```

## Context

The console reaches its API at `import.meta.env.VITE_API_URL`, a value Vite inlines
into the bundle at `npm run build`, falling back to `http://localhost:8001`. When the
web review measured this on 2026-09-05 (`bcae4d02`) the literal sat in twelve files;
WEB12 collapsed it the same day to ONE definition, `apiBaseUrl()` in
`web/src/lib/auth.ts` (16 files to 1 by its own count). The agent server's base has
the same shape in two files (`AskRoute.tsx`, `CypherConsole.tsx`:
`VITE_ADK_URL ?? 'http://localhost:8000'`), and the O39 runtime-view link template
(`VITE_RUNTIME_VIEW_URL_TEMPLATE`, a company hostname) is inlined the same way. Three
consequences follow, none of them about code quality:

1. **One build cannot be promoted.** Every environment needs its own `npm run build`,
   so the artifact that was tested is never the artifact that ships. CI builds `dist/`
   and uploads it; nothing consumes it.
2. **The unset case is silent and wrong.** A production bundle built with the variable
   unset points every user's browser at the user's own machine, and the O85 message
   then tells a support analyst to run `poetry run uvicorn` on their desktop. Nothing
   fails the build.
3. **Nothing serves the console.** There is no Dockerfile, proxy config, Compose file
   or static mount in `drydocs_api` (its `static/` holds the one dev demo page at
   `/demo`). So the console is cross-origin to its API in every environment that
   exists, and cross-origin to the agent server too.

That third fact is the expensive one, because the code already pays for it three
times over, and each payment is a place for drift:

- **Two allowlists.** `create_app()` names `localhost:5173`, `:4173`, `:5199` and
  extends from `DRYDOCS_CORS_ORIGINS`; `agents/serve.py` takes `--allow_origins`.
  The API's comment block on the allowlist runs twenty-two lines, and it exists to explain
  why a verification port that five real tests ran on was not in the list.
- **A diagnostic probe to explain the allowlist.** `reachability.ts` (O85) issues a
  `no-cors` probe so the console can tell "the server is down" from "the server
  answered and the browser discarded the answer for an origin rule" — two failures
  the fetch API reports identically. Its header records that the documented
  verification port and the allowlist drifted apart from O69 until 2026-08-30 with
  nobody noticing (Idea-200). That is the class of defect this ADR retires: a
  same-origin console has no allowlist to drift from.
- **Three dedicated ports in the e2e harness.** `web/playwright.config.ts` runs the
  API on 8011 and the console on 5273 and has to pass `DRYDOCS_CORS_ORIGINS` for the
  second, because "the web port is an origin" — its own comment names this as the
  second of three bugs the harness hit on its first run.

**What ADR 0005 already fixed, and what it left open.** 0005 ruled ACCESS: the browser
never speaks bolt in a deployment; a thin API holds the credentials, enforces read-only
and database routing, and is where SSO/OIDC terminates company-side; its network row
reads "HTTPS/443; SSO-terminable". Every one of those properties assumes something in
front of the API that owns the origin, the certificate and the identity — which is a
reverse proxy in every corporate deployment that exists. 0005 did not say where the
console's bytes come from or whether they share that origin. This ADR does.

**The 0019 principle applies here unchanged:** rule the shape closest to the company
end state so it is replaced by substitution, not unwound. Company-side the console
WILL sit behind an SSO-terminating proxy on 443; the producer stack should have the
same topology at localhost scale, so the drift class is retired on both sides by the
same mechanism.

**Scale, stated so the ruling is proportionate.** The audience is application support
teams — tens of concurrent users, not thousands (memory: DryDocs audience strategy).
No option below needs a CDN, a build-per-tenant, or an edge cache; a static directory
behind one proxy is the right size.

## Decision

**Option C: same-origin behind ONE reverse proxy, path-routed to three upstreams.** The
console, the API and the agent server are served from one origin. The proxy owns the
path map; the upstreams are unchanged.

1. **The path map is the contract, and it is declared once.**

   | Path | Upstream | Prefix |
   |---|---|---|
   | `/api/*` | drydocs-api (`:8001` locally) | stripped — the API's routes stay exactly `/specs`, `/login`, `/health` |
   | `/agent/*` | the ADK `api_server` (`agents/serve.py`, `:8000` locally) | stripped — `/list-apps`, `/run_sse` unchanged |
   | `/*` | the built console (`web/dist/`) | SPA fallback to `index.html` |

   Prefix stripping is what keeps this an ADR about DELIVERY and not about the API:
   `dump_openapi.py --check` is unchanged, the agent server's Swagger is unchanged,
   and a curl against `:8001/specs` still works on the dev bench. The three prefixes
   are declared in ONE committed file the Vite dev proxy, the Vite preview proxy and
   the production proxy config all read or are guarded against (the build decides
   the file; the invariant is that no second copy of the map can drift).

2. **The API base is a PATH, not a URL.** `apiBaseUrl()` returns `/api`; the agent
   base returns `/agent`. Both are relative to the document origin, so they are the
   same string in every environment and there is nothing to configure, inline, or
   forget. `VITE_API_URL` and `VITE_ADK_URL` are RETIRED — removed from
   `.env.example`, the code and the e2e harness — and clause (b)'s "fail rather than
   fall back to localhost" is met the strongest way: the failure mode no longer has a
   setting to be missing. The residual localhost that remains is the DEV PROXY TARGET
   (below), and that is the one place localhost is the truth.

3. **Dev is same-origin too, through Vite's own proxy.** `vite.config.ts` gains
   `server.proxy` (and `preview.proxy`) entries for `/api` and `/agent`, each with a
   prefix rewrite, targeting upstreams read from the shell that runs Vite
   (`DRYDOCS_API_UPSTREAM`, `DRYDOCS_AGENT_UPSTREAM`; defaults `http://localhost:8001`
   and `:8000`, the runbook's own ports). These are read by the Vite PROCESS, never
   inlined into the bundle. Consequences the ruling accepts on purpose:
   - `npm run dev`, `npm run preview` and the O80 suite are all same-origin, so the
     API's allowlist and `DRYDOCS_CORS_ORIGINS` have no remaining caller and are
     REMOVED, not reduced; `agents/serve.py --allow_origins` likewise. The twenty-two-line
     comment goes with them; its history is in git and in this ADR.
   - The e2e harness keeps its dedicated ports (that reasoning — never adopt a
     developer's API — stands) and drops the origin plumbing: it points the Vite
     proxy at `:8011` instead of teaching an allowlist about `:5273`.
   - `reachability.ts`'s `blocked-origin` verdict has no production path. It is
     retired, and the module keeps the `unreachable` verdict; the message that
     quotes `poetry run uvicorn` is a dev-bench message and is guarded by
     `import.meta.env.DEV`. In production the proxy answers `502`/`503`/`504` when an
     upstream is down, and the console renders THAT as "drydocs-api is not answering
     behind the proxy" — a status code, not a TypeError, which is the diagnosis the
     probe existed to approximate.

4. **A production bundle inlines NO deployment coordinate.** The invariant, guarded
   in CI beside `bundle:check`: the built `dist/` contains no `localhost:` and no
   absolute `http(s)://` service URL. The `VITE_*` variables that survive are the
   ones 0005 already scoped to the dev bench — the bolt adapter's URI/user/database
   and `VITE_DEV_CONSOLE_SECRET` — all baked out by `import.meta.env.DEV`.

5. **Non-secret deployment settings that vary by environment are served at runtime.**
   The one that exists today is the O39 runtime-view link template, a company
   hostname currently inlined at build. It moves to `GET /api/config` — a small,
   unauthenticated, non-secret JSON the console reads at boot — read by the API from
   its environment (`DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE`), per 0014's rule that a
   per-machine operational fact lives in env. Absent means the affordance does not
   render, exactly as today. This is the `/config` endpoint clause (a) names; it
   carries the values that need it, and the API base is not one of them.

6. **The agent resolves the API from its OWN environment.** The 0019 control part
   carries `api_url` so the agent can register ephemeral specs against the API that
   issued the session. A relative base (`/api`) cannot be forwarded to a different
   process, so the console stops sending `api_url`; `agents/common/ephemeral_client.py`
   already reads `DRYDOCS_API_URL` and falls back to its default, and that becomes the
   only path. Server-to-server URLs are the server's configuration, not the browser's.

7. **O72's Compose stack is where the shape is first exercised, and it is where the
   proxy lives.** O72 composes the runbook's processes; this ADR adds the proxy as the
   fourth service (Neo4j stays optional) and makes the console a STATIC directory the
   proxy serves, so the Vite dev server is a dev-bench process and not part of the
   deployable stack. The proxy binary is O72's choice; the ADR rules the path map and
   two properties any choice must meet: prefix stripping, and streaming for
   `/agent/run_sse` (no response buffering — nginx needs `proxy_buffering off`, Caddy
   `flush_interval -1`). The runbook's Startup gains the one-command path and keeps
   the per-process one, as O72 already says.

8. **What this ADR does NOT rule.** TLS, certificates and the SSO integration at the
   proxy are company-side configuration on the shape (0005 Evidence); a Dockerfile for
   the API; any change to the API's route space or to the ADK server; and the O72
   health checks, which O72 owns. It also does not rule the choice between one proxy
   and the API serving `dist/` itself for a single-user bench — option B below is
   rejected as THE shape and is not built as a convenience either, for the reason
   given there.

## Options considered

### A — Stay cross-origin, rule it, and add runtime configuration

Keep three origins. Replace the build-time `VITE_API_URL` with a boot-time
`GET <api>/config` or an injected `window.__DRYDOCS__`, fail the bundle when the base
is unset, and keep both allowlists as the price of the shape.

| Dimension | Assessment |
|---|---|
| Complexity | Low to change; HIGH to keep — the allowlists, the env override, the probe and the harness plumbing all stay, and each is a drift site |
| Config surface | Grows: the base URL becomes a required runtime setting on top of two allowlists |
| Fit with 0005 | Poor: 0005's "SSO-terminable, HTTPS/443" deployment already has a proxy in front; refusing to use it for the console is paying for a proxy and a CORS story |
| One-build promotion | Achieved, but only by adding the setting whose absence is the failure being fixed |

**Pros:** the smallest diff; no new process. **Cons:** it keeps everything S3 named as
cost and adds a bootstrap setting; the 2026-08-30 drift class stays live; the ADK hop
stays a second allowlist with a second flag. Rejected: this rules the symptom.

### B — drydocs-api serves `dist/`

Mount the built console on the API process (`StaticFiles` with an SPA fallback, API
routes taking precedence). One process, one origin for console and API.

| Dimension | Assessment |
|---|---|
| Complexity | Low: one mount and a build step that copies `dist/` next to the package |
| Config surface | The API base becomes a path with no proxy in the picture |
| Fit with 0005 | Partial: company-side the proxy still exists for SSO/TLS, so the API serving static files is a second server behind a server |
| The agent hop | UNSOLVED — `/agent` is still a different origin, so `serve.py --allow_origins` and the Ask spoke's cross-origin call survive, and with them half the drift class |

**Pros:** one fewer process on the bench. **Cons:** it makes a thin read API a static
file server, which is not its job and not what 0005 shaped it for; it solves one of two
cross-origin hops; and it does not mirror the company topology, so it would be
unwound rather than substituted when SSO lands. Rejected as the shape. Not adopted as a
bench convenience either: two ways to serve the console is two path maps, and clause 1
exists to have one.

### C — One reverse proxy, path-routed to three upstreams (**chosen**)

| Dimension | Assessment |
|---|---|
| Complexity | Medium once: a proxy config (tens of lines), Vite proxy entries, retirements across `web/`, `drydocs_api/app.py`, `agents/serve.py`, the harness |
| Config surface | SHRINKS: two allowlists, one env override, two `VITE_*` variables and one build-time hostname go; two dev-bench upstream variables and one runtime `/config` arrive |
| Fit with 0005 | Exact: the proxy IS the "SSO-terminable, HTTPS/443" front 0005 assumes; company config lands on it, producer config is its localhost twin |
| One-build promotion | Achieved by construction — the bundle has no coordinate to vary |
| The agent hop | Solved: same origin, no `--allow_origins`, and the 0019 handle travels same-origin |

**Pros:** retires the drift class rather than diagnosing it; one path map, declared
once; dev, preview, e2e and production share the topology; the smallest surviving
configuration surface of the three. **Cons:** a proxy is a real process with its own
config to keep in step with the map (hence the guard); SSE through a proxy needs one
deliberate setting; the API is no longer reachable from the console at a bare port,
so the dev habit of `VITE_API_URL=http://localhost:8011` becomes
`DRYDOCS_API_UPSTREAM=http://localhost:8011`.

## Trade-off analysis

The choice is between diagnosing a boundary and removing it. A, and every incremental
fix before it (the allowlist's env override, the O85 probe, the harness's dedicated
origin), treats "the console is cross-origin to its API" as a fact of nature and builds
instruments to explain its failures — and the review's evidence is that the instruments
were needed because the boundary drifted unobserved for a month. B removes the
boundary for one of the two hops and leaves the API doing a job 0005 did not give it.
C removes it for both hops with the component every target deployment already has, and
makes the producer bench a small copy of the company topology, which is the 0019 test
for a ruling that gets substituted rather than unwound.

The cost C carries that A and B do not is one more process on the bench. That cost is
already scheduled: O72 exists to compose the bench's processes and to give each a
health check, and a proxy with a health check is the least of them. The cost A and B
carry that C does not is permanent: an allowlist is a list, lists drift, and this one
already did.

## Consequences

- **Easier:** one `npm run build` for every environment; `web/dist/` becomes an artifact
  that something consumes; the API and agent servers lose their origin configuration
  entirely; the e2e harness loses one of its three port stories; the O85 probe's
  hardest branch (the one that had to say "likely" because it could not prove a
  diagnosis) is retired rather than made more careful.
- **Harder:** the dev bench gains a process when run as the deployable stack (O72), and
  a developer who runs the API on a non-default port sets an UPSTREAM variable for Vite
  instead of a `VITE_*` one. Debugging a `502` means reading the proxy's log, a habit
  the runbook's Troubleshooting section must teach.
- **Cross-pen:** the build touches `drydocs-web`, `drydocs-api` and `drydocs-agents` and
  lands as one merged unit, as WEB9 did.
- **Revisit:** when company-side SSO/OIDC lands, the proxy is where the identity claim
  is injected and the API's `/login` becomes the dev-bench path; this ADR's topology is
  what that configuration is applied to. If a second console (the Team Edition
  instances, ADR 0015) needs a different path map, clause 1's single declaration is
  what changes.

## Action items (the build — WEB10 clauses (b)–(d); after the ruling)

1. [ ] `web/vite.config.ts`: `server.proxy` and `preview.proxy` for `/api` and `/agent`
   with prefix rewrite, targets from `DRYDOCS_API_UPSTREAM` / `DRYDOCS_AGENT_UPSTREAM`.
2. [ ] `web/src/lib/auth.ts` `apiBaseUrl()` returns `/api`; an `agentBaseUrl()` beside it
   returns `/agent`; `AskRoute.tsx`, `CypherConsole.tsx` use it; `VITE_API_URL` and
   `VITE_ADK_URL` removed from `.env.example`, the code and `web/playwright.config.ts` (CI sets neither).
3. [ ] `drydocs_api/app.py`: CORS middleware and `DRYDOCS_CORS_ORIGINS` removed;
   `GET /config` added (runtime-view template from `DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE`);
   `dump_openapi.py --check`, `npm run api:types`.
4. [ ] `agents/serve.py`: `--allow_origins` removed; runbook Startup step 3 updated.
5. [ ] `web/src/ask/askApi.ts` + `agents/graph_qa/control.py`: `api_url` leaves the control
   part; the agent resolves the API from `DRYDOCS_API_URL` only.
6. [ ] `web/src/lib/reachability.ts`: `blocked-origin` retired; `unreachable` kept and
   DEV-guarded; proxy `502`/`503`/`504` rendered as "upstream not answering".
7. [ ] `web/playwright.config.ts`: `DRYDOCS_CORS_ORIGINS` plumbing replaced by the proxy
   upstream variable; ports unchanged.
8. [ ] CI guard beside `bundle:check`: no `localhost:` or absolute service URL in `dist/`.
9. [ ] O72's plan gains the proxy service, the path map file, and the SSE setting; the
   runbook's Startup and Troubleshooting sections gain the one-command path and the
   `502` reading. This ADR's status flips to ACCEPTED with the ruling, and
   `docs/decisions/README.md` gets its row.
