# ADR 0020 needs one amendment — for whoever holds the `adr` pen

**This file is a hand-off, not a decision.** It was written by a session that held
`code:drydocs-web` and NOT `adr` (Lane A, desktop, has been declaring
`pen: backlog · port · adr · gates · snapshot` on every commit), so it proposes wording
and changes nothing in `docs/decisions/`. Apply it and delete this file — it is
self-retiring and has no other reader.

- **Reviewed at:** commit `f74d6d0c` on `fix/agent-origin-403`, port base `port-base-20260905`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

## What happened

`f74d6d0c` fixes a defect the ADR's own reasoning produced: the console's Ask answered
**403 Forbidden: origin not allowed** to every question, in dev and (unfixed) in the
Compose stack, while every other page worked.

ADR 0020's premise is that the browser makes no cross-origin request — it calls `/api`
and `/agent` on the page's own origin, so no service needs an allowlist. **That is true
at the browser and false at the upstream.** Both proxies rewrite `Host` and forwarded
`Origin` untouched, so a service listening on its own port received
`Origin: <the page's origin>` and correctly read it as cross-origin, which at that hop
it is. `agents/serve.py` passes no `--allow_origins` on this ADR's reasoning, which
leaves ADK's origin checking **ON with an EMPTY allowlist** — an allowlist of one, its
own origin.

Reproduced both directions before the fix, and again after:

| request to the ADK | before | after |
|---|---|---|
| no `Origin` header | 200 | 200 |
| `Origin: http://localhost:8000` (its own) | 200 | 200 |
| `Origin: http://localhost:5173` (the page) | **403** | 200 |

`drydocs-api` was never affected — it has no origin check to fail, which is exactly why
only one prefix broke and why this survived WEB10, O72 and V10's runbook audit.

## The one sentence that is wrong

`## Consequences`, the **Easier** bullet, currently reads:

> the API and agent servers lose their origin configuration entirely

The API did. **The agent server did not.** Not passing `--allow_origins` to ADK is not
"no origin configuration" — it is an empty allowlist, which is *stricter* than none.
That distinction is the whole defect, and the ADR states its opposite as a benefit.

## Proposed amendment (wording, for the pen-holder to accept, reword or reject)

**1. Correct the Easier bullet.** Replace *"the API and agent servers lose their origin
configuration entirely"* with something that keeps the claim true of the API and honest
about ADK, e.g.:

> drydocs-api loses its origin configuration entirely; the agent server keeps ADK's
> own origin check, which with no `--allow_origins` is an EMPTY allowlist rather than
> no check — so the proxy, not the upstream, is what must not present a foreign origin

**2. Add a clause to the Decision — the proxy owns the request it presents.** Clause 1
says the proxy owns the path map. The defect is that it also owns the *headers*, and
that was never written down. Suggested addition:

> **The proxy presents a same-origin request, and that is the proxy's job, not a
> property of the browser.** `Origin` is cleared at every proxied prefix
> (`web/vite.config.ts` removes it on `proxyReq`; `deploy/render_proxy_config.mjs`
> renders `proxy_set_header Origin "";` into `COMMON`). Without this the premise holds
> at the browser and breaks at the upstream, which is how the ADK answered 403 to every
> Ask between WEB10 and 2026-09-08. Guarded by
> `tests/unit/test_console_delivery.py::test_the_nginx_renderer_clears_origin_on_every_proxied_prefix`
> and `::test_the_vite_proxy_removes_the_origin_header`.

**3. Consider a Revisit trigger.** The existing Revisit bullet covers SSO/OIDC and a
second console. A third belongs beside them: *if an upstream is ever published directly
rather than only through the proxy, the cleared `Origin` stops being safe and that
upstream needs a real allowlist.* Today none is published, which is why clearing the
header is the right call and not a weakening.

## What this is NOT proposing

- **No change to the topology or the path map.** Option C stands; the defect was in an
  unstated consequence of it, not the choice.
- **No `--allow_origins` on the ADK.** That was considered and rejected: it would put
  the allowlist back that this ADR retired, and re-create the drift
  `test_console_delivery.py` exists to prevent (the O69→2026-08-30 failure the file's
  own header describes).
- **No security downgrade claim needing a gate.** The CSRF signal dropped at the ADK hop
  is one the upstream was not the right place to read — the proxy is the trust boundary
  and the upstreams are not published. If the pen-holder disagrees, that IS a gate
  question and the fix should be revisited rather than the ADR reworded.

## Retirement

Delete this file once ADR 0020 carries the correction. Nothing cites it and nothing
depends on it; it exists because the session that found the defect could not hold the
`adr` pen and did not want the finding to survive only in a commit message.
