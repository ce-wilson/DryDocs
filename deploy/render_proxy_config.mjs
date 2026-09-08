// ============================================================================
// deploy/render_proxy_config.mjs — nginx server block, rendered from delivery.json
// ============================================================================
// ADR 0020 declares the console's path map ONCE, in web/delivery.json, and says
// the two readers are web/vite.config.ts and web/src/lib/auth.ts. The Compose
// stack adds a third reader that cannot read JSON at all: nginx. So the map is
// rendered into its config at IMAGE BUILD TIME by this script, from the same
// file, and the prefixes appear nowhere else.
//
// Why a renderer rather than a hand-written nginx.conf with `/api` in it: a
// hand-written one is a fourth copy of the map, and the failure it produces is
// the worst kind — change delivery.json, and dev keeps working (Vite re-read it)
// while the stack silently forwards nothing, because a prefix that matches no
// location falls through to the SPA fallback and answers 200 with index.html.
// A wrong answer that looks like a right one.
//
// Run in the node build stage (see deploy/console.Dockerfile):
//   node render_proxy_config.mjs <delivery.json> <out.conf>
// Upstreams come from the environment, defaulting to the Compose service names.

import { readFileSync, writeFileSync } from 'node:fs'

const [, , deliveryPath, outPath] = process.argv
if (!deliveryPath || !outPath) {
  console.error('usage: render_proxy_config.mjs <delivery.json> <out.conf>')
  process.exit(2)
}

// The Compose service names are the defaults, not localhost: inside the network
// each service IS a hostname, and `localhost` in the proxy container is the
// proxy container. Overridable so the same image can front upstreams elsewhere.
// `||` and not `??`: an unset Dockerfile ARG expands to the EMPTY STRING, not to
// undefined, so `??` would accept it and render `proxy_pass /;` — a config that
// fails at nginx start with a message about the URI, three steps from the cause.
const API_UPSTREAM = process.env.DRYDOCS_API_UPSTREAM || 'http://api:8001'
const AGENT_UPSTREAM = process.env.DRYDOCS_AGENT_UPSTREAM || 'http://agent:8000'

const delivery = JSON.parse(readFileSync(deliveryPath, 'utf8'))

/** Assert loudly rather than render a config that silently forwards nothing. */
function prefixOf(key) {
  const prefix = delivery?.[key]?.prefix
  if (typeof prefix !== 'string' || !prefix.startsWith('/')) {
    throw new Error(`${deliveryPath}: ${key}.prefix is missing or is not an absolute path`)
  }
  return prefix.replace(/\/$/, '')
}

const apiPrefix = prefixOf('api')
const agentPrefix = prefixOf('agent')

// The shared proxy headers. `Host` is left to nginx's default ($proxy_host, the
// upstream) — that is what Vite's `changeOrigin: true` does, so a service that
// reflects the Host header behaves the same in dev and here.
//
// ORIGIN IS CLEARED, and this is the header that made ADR 0020 half true. The
// ADR's premise is that the browser never makes a cross-origin request: it calls
// /api and /agent on the page's own origin, so no allowlist is needed anywhere.
// That holds at the BROWSER and breaks at the UPSTREAM. Both proxies rewrite Host
// and forwarded `Origin` untouched, so a service listening on its own port
// received `Origin: <the page's origin>` and correctly read it as cross-origin.
// The ADK server (agents/serve.py, which passes no --allow_origins on this ADR's
// reasoning) has origin checking ON with an EMPTY allowlist, so it answered
// 403 "origin not allowed" to every console Ask while /api worked — drydocs-api
// has no origin check at all, which is why only one prefix ever failed.
//
// Clearing it here restores the ADR's own premise at the hop where it was lost:
// the request reaching the upstream is not cross-origin, because it no longer
// claims to be. `""` makes nginx omit the header entirely (the documented way),
// which is the state the ADK already accepts — it answers 200 with no Origin.
// The proxy is the trust boundary; the upstreams are not published, so the CSRF
// signal dropped here is one the upstream was not the right place to read.
const COMMON = `        proxy_http_version 1.1;
        proxy_set_header Origin "";
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;`

/** One proxied prefix, as the two locations nginx needs to match what Vite
 *  matches with one anchored regex (`^/api(/|$)`).
 *
 *  The trailing slash on proxy_pass is what STRIPS the prefix: `location /api/`
 *  + `proxy_pass http://api:8001/` forwards /api/health as /health. Dropping
 *  that one character forwards /api/health as /api/health, which every upstream
 *  answers 404 — the single most common way this file gets broken.
 *
 *  A DEAD UPSTREAM ANSWERS 502 here with no configuration: it is nginx's default
 *  for a refused connection, and it is the behaviour vite.config.ts had to be
 *  taught by hand so that dev and this stack report one failure one way
 *  (src/lib/reachability.ts reads 502/503/504 as "the service behind this path
 *  is down"). */
function route(prefix, upstream) {
  return `    # ${prefix}/* -> ${upstream}, prefix stripped
    location = ${prefix} {
        proxy_pass ${upstream}/;
${COMMON}
    }

    location ${prefix}/ {
        proxy_pass ${upstream}/;
${COMMON}
    }`
}

// /agent/run_sse is the Ask module's server-sent-events stream. nginx BUFFERS
// proxied responses by default, which for a stream means the page sits blank and
// then receives the whole answer at once, at the end — a "slow model" that is
// actually a proxy setting. Exact-match location, so it wins over the prefix
// location above regardless of order.
const sse = `    # SSE: no buffering, or the Ask page gets the whole answer at once, at the end
    location = ${agentPrefix}/run_sse {
        proxy_pass ${AGENT_UPSTREAM}/run_sse;
${COMMON}
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 1h;
        chunked_transfer_encoding on;
    }`

const conf = `# GENERATED by deploy/render_proxy_config.mjs from web/delivery.json — DO NOT EDIT.
# Edit delivery.json (the one declaration ADR 0020 names) and rebuild the image.
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # The console is a single-page app: every non-asset path is a client route,
    # so an unknown path serves index.html rather than 404. This location is LAST
    # in intent — nginx picks the most specific match, so the proxied prefixes
    # above win over it — and it is why a MISSING proxy route is dangerous: it
    # would land here and answer 200 with the page instead of failing.
    location / {
        try_files $uri $uri/ /index.html;
    }

${route(apiPrefix, API_UPSTREAM)}

${route(agentPrefix, AGENT_UPSTREAM)}

${sse}
}
`

writeFileSync(outPath, conf, 'utf8')
console.log(`rendered ${outPath}: ${apiPrefix} -> ${API_UPSTREAM}, ${agentPrefix} -> ${AGENT_UPSTREAM}`)
