import { readFileSync } from 'node:fs'

import { defineConfig, type ProxyOptions } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// ADR 0020 - the console is SAME-ORIGIN with its API and its agent server, in
// every environment. In production one reverse proxy path-routes `/api/*` to
// drydocs-api and `/agent/*` to the ADK server, prefix stripped, and serves
// dist/ for everything else (O72's Compose stack is where that proxy first
// runs). Here, Vite's own dev and preview servers play the proxy, so the code
// the browser runs is the same code in both places: it fetches `/api/...` and
// `/agent/...` on the page's own origin and never learns where the services
// live. That is what retired both CORS allowlists and DRYDOCS_CORS_ORIGINS.
//
// THE PATH MAP IS DECLARED ONCE, in web/delivery.json, and read by this file
// and by src/lib/auth.ts (apiBaseUrl / agentBaseUrl). The two cannot drift
// because neither holds the strings; tests/unit/test_console_delivery.py reads
// the same file.
//
// WHERE THE SERVICES LIVE is a fact about THIS machine, so it is read from the
// Vite PROCESS's environment (`process.env`, never `import.meta.env`) and is not
// inlined into anything the browser downloads. The e2e harness sets
// DRYDOCS_API_UPSTREAM to its own API port; a developer running drydocs-api on
// a non-default port sets it in the shell that runs `npm run dev`.
const delivery = JSON.parse(readFileSync(new URL('./delivery.json', import.meta.url), 'utf8')) as {
  api: { prefix: string }
  agent: { prefix: string }
}

const API_UPSTREAM = process.env.DRYDOCS_API_UPSTREAM ?? 'http://localhost:8001'
const AGENT_UPSTREAM = process.env.DRYDOCS_AGENT_UPSTREAM ?? 'http://localhost:8000'

/** One proxied prefix: `<prefix>/x` is forwarded as `/x` on the upstream, and
 *  the key is anchored (`^/api(/|$)`) so `/api-notes` would not match `/api`.
 *
 *  A DEAD UPSTREAM ANSWERS 502, as nginx and Caddy do. http-proxy's default on
 *  a connection error is to destroy the socket, which the browser reports as
 *  the same TypeError a dead page server produces - and the console reads a
 *  502/503/504 as "the service behind this path is down" (src/lib/reachability.ts,
 *  isUpstreamDown). Writing the 502 here keeps dev and the Compose stack on
 *  one meaning for one failure. */
function route(prefix: string, target: string): [string, ProxyOptions] {
  const anchored = new RegExp(`^${prefix}(?=/|$)`)
  return [
    `^${prefix}(/|$)`,
    {
      target,
      changeOrigin: true,
      rewrite: (path) => path.replace(anchored, '') || '/',
      configure: (proxyServer) => {
        proxyServer.on('error', (_err, _req, res) => {
          if (!('writeHead' in res) || res.headersSent) return
          res.writeHead(502, { 'Content-Type': 'text/plain' })
          res.end(`upstream for ${prefix} (${target}) is not answering`)
        })
      },
    },
  ]
}

const proxy: Record<string, ProxyOptions> = Object.fromEntries([
  route(delivery.api.prefix, API_UPSTREAM),
  route(delivery.agent.prefix, AGENT_UPSTREAM),
])

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy },
  preview: { proxy },
})
