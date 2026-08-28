# Web scaffolding review — what to take from full-stack-fastapi-template and ss-python

<!-- anchor: front-matter -->
- **Scope:** an evaluation, not a runbook and not a decision record. It compares two public
  project scaffolds against what the DryDocs console already has, and names the pieces worth
  adopting. Each adoption gets a backlog item; this page is the reasoning behind those items.
- **Status:** DESCRIPTIVE — **Rev 1, 2026-08-27.**
- **Classification:** External reasoning over Internal-Public context (both reviewed projects
  are public; nothing here carries company values, credentials or internal URLs)
- **Reviewed:** `fastapi/full-stack-fastapi-template` (MIT) and `serious-scaffold/ss-python`
- **Companion:** `docs/design/drydocs-web-console-runbook.md`,
  `docs/design/drydocs-api-runbook.md`, ADR 0005 (the browser-to-graph access path)

<!-- anchor: why-now -->
## Why this review happened now

The console has run on **mock authentication since 2026-07-13** (item O2). Its banner still
reads "access path pending the O1 ADR" — but O1 closed, ADR 0005 ruled the thin API, and no
successor item for real authentication was ever minted. So the console's only access control
is a client-side persona picker with no owner and no ticket.

**The stated reason for holding off was uncertainty about how internal authentication is
handled, and the user has ruled that this is not the deciding factor.** That ruling is what
unblocks the work, and it is also the right call on the merits: the producer repo is a
personal proof of concept whose long-term goal is a sanitized standalone template. A
self-contained credential path is what a template needs. Whatever the company binds at its
own seam — OIDC, SAML, an internal gateway — replaces the credential half and reuses
everything above it, exactly the way ADR 0005 already anticipated when it made the SERVER
the role authority rather than the browser.

<!-- anchor: what-we-already-have -->
## What DryDocs already has

The gap is narrower than "we have no authentication," and being precise about that is what
keeps the adopted scope small.

| Piece | State |
|---|---|
| Thin API, server-side role resolution | **Present.** ADR 0005 decision 3: the client holds an opaque token, the role is resolved server-side per request. |
| Token issue / resolve / revoke | **Present.** `drydocs_api/sessions.py` — `InMemorySessionStore`, `secrets.token_urlsafe(24)`, issued-at stamp. |
| A login endpoint | **Present but credential-free.** It takes a `persona_id` and returns a session; an unknown persona is a 401. There is no secret to prove. |
| Client session + role gating | **Present, client-side and mock.** `web/src/lib/auth.ts` re-derives role from the persona table so a forged blob degrades to sign-in; `lib/views.ts` holds one `canSee` registry. |
| Frontend build | **Present.** Vite, React 19, Tailwind v4, ReUI, react-router-dom 7, oxlint. |
| Frontend tests | **ABSENT.** No test runner of any kind — no Vitest, no Playwright. O43 still poses this as an open question. |
| Typed API client | **ABSENT.** `web/src/lib/graphApi.ts` is hand-written `fetch` with hand-kept response types. |
| One-command local stack | **ABSENT.** Four processes started by hand from the runbook. |
| Pre-commit hooks | **ABSENT.** No `.pre-commit-config.yaml`. |

<!-- anchor: fastapi-template -->
## full-stack-fastapi-template — what is worth taking

The template's stack is close enough to ours that the comparison is useful rather than
aspirational: FastAPI, Pydantic settings, pytest, Vite, TypeScript, Tailwind, and
shadcn-style components. We already run the same shapes. Four pieces are worth adopting.

### 1. The authentication pattern, not the user model

The mechanism, named exactly: `OAuth2PasswordBearer(tokenUrl=".../login/access-token")` for
extraction; `pwdlib` with `Argon2Hasher()` primary and `BcryptHasher()` fallback for hashing;
HS256 JWT carrying `sub` and `exp`; and — the part worth copying most — the **dependency type
aliases**: `SessionDep`, `TokenDep`, `CurrentUser`, plus a separate
`get_current_active_superuser`. A route declares `CurrentUser` and authentication becomes a
signature, not a body of code repeated per handler.

**What we take:** the alias pattern, the hashing library choice, and the token shape.
**What we do not take:** SQLModel, PostgreSQL, Alembic and a `User` table. DryDocs has no
relational user store and should not grow one to hold four personas; the credential store is
a small deliberate decision of its own, and the item names it as such rather than importing
an ORM to answer it.
**What we do not need at all:** email-based password recovery, React Email, Mailpit. A
proof-of-concept console with a handful of accounts does not need a mail path, and adding one
would put an SMTP dependency and an email template corpus into a repo whose publish boundary
we would then have to reason about.

### 2. The generated frontend client

The template generates its TypeScript client from the backend's OpenAPI schema. We hand-write
`graphApi.ts` and hand-maintain its response types against `drydocs_api`. That is a drift
surface with no guard, and this repo has already been bitten twice by the same class of
problem in a different place — a surface that restates a declaration instead of deriving from
it. Generating the client makes an API change a compile error in the browser code.

### 3. Playwright for end-to-end tests

The console has **no automated test of any kind**. Every UI verification this project has done
was a person or an agent driving Chrome and looking, and the ledger in
`config/taxonomy/ui-tests.yaml` records those observations as manual cases precisely because
nothing can run them. The Z5 map defect found on 2026-08-27 is the argument: a synthetic city
never resolved, no Python guard could see it because the bug was in TypeScript, and it took
rendering the page and reading a list to find. That is exactly what an E2E test automates.

### 4. Compose for the local stack

The runbook's Startup section is four processes with four success checks. Compose collapses
that to one command and makes the success checks a health-check declaration.
**What we do not take:** Traefik and automatic HTTPS. There is no deployment; a reverse proxy
would be scaffolding for a scenario that does not exist.

<!-- anchor: ss-python -->
## ss-python — what is worth taking

A Copier-based Python project scaffold: pdm, ruff, mypy, pytest with a coverage threshold,
Sphinx with Furo, semantic-release, Renovate, commitlint, pre-commit, dev containers, and a
Makefile that centralizes the common actions.

Most of it we either already have in a different form or have deliberately ruled against.

| Piece | Verdict |
|---|---|
| ruff, pytest | Already ours. |
| **pre-commit** | **ADOPT.** See below — this one has direct evidence behind it. |
| mypy | Consider separately. A type-checking sweep over an existing codebase is its own project, not scaffolding. |
| Sphinx + Furo + Read the Docs | **REJECT.** DryDocs has a deterministic `.md` to `.html` renderer whose output the HITL loop keys feedback anchors on. A second documentation system would compete with a governed surface. |
| semantic-release, commitlint | **REJECT for now.** This repo's commit discipline is a written convention with real reasons behind its shape; automating version bumps on a proof of concept buys nothing. |
| Renovate | **Worth an idea, not an item yet.** Useful once dependency drift is a real problem. |
| Makefile as the single task entry point | Partially ours already via `poetry run` verbs and `snapshot.ps1`; a unified entry point is a nice-to-have, not a gap. |
| **Copier template mechanics** | **The strategically interesting one.** DryDocs' long-term goal is a sanitized standalone template another organization can implement. Copier is a template that can be *updated in place* after generation, which is precisely the property that goal needs. Inboxed as an idea rather than an item, because it is a direction to rule on, not a task to schedule. |

### pre-commit, and why it earns its place

Between **2026-08-05 and 2026-08-12 this repo's CI ran red for over a hundred consecutive
runs** on `ruff check` and `ruff format --check`, while sessions kept pushing past it. It
stayed invisible because the unit suite passed the whole time, so nothing local ever looked
wrong. The session ritual now checks CI explicitly, and `snapshot.ps1` performs that check
itself — but both are *detection after the fact*. A pre-commit hook running the same two
commands makes the failure impossible to commit in the first place. This is the one piece of
ss-python's tooling that answers a failure this project actually had.

<!-- anchor: adoption -->
## Adoption plan

| Item | What it does |
|---|---|
| **O69** | Real authentication: a credential step and a durable session, replacing the persona picker. The headline item. |
| **O70** | Generate the TypeScript API client from the OpenAPI schema; retire the hand-written types. |
| **O71** | A frontend test runner — Vitest for units, Playwright for end to end — which also answers O43's open question. |
| **O72** | One-command local stack via Compose, with the runbook's success checks as health checks. |
| **J52** | pre-commit hooks running the two commands CI blocks on. |

Deliberately not items: Traefik, email recovery, Sphinx, semantic-release, an ORM and a user
table. Each is named above with the reason.

<!-- anchor: unresolved -->
## One unresolved reference

The review was asked to find a hardcoded login this project had built with users named
something like *monk* or *morpheus*. **It is not in this repository.** Searched: the working
tree, every branch and tag, and the archived pre-squash history
(`archive/old-history-2026-07-20`) with `git log --all -S`, plus the sibling projects on this
machine. Zero hits for `morpheus`; `monk` matches only `monkeypatch`, and `trinity` only BMC
event documentation. The only demo-user set found nearby is the vendored React theme under
`start_react_free_v1.0.0`, whose mock users are `admin`, `user` and `guest`.

If that login exists it is on the other machine, in the company checkout, or on a surface
outside git. Worth recovering before O69 starts only if it carried a decision we would
otherwise re-make; the mechanism itself is not something we would copy.
