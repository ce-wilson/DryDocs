// WEB10 (b) — no deployment coordinate in the built bundle. Run by the `web`
// CI job after the build, beside the initial-chunk ceiling.
//
// ADR 0020: one build is promoted through every environment, which is only
// true if the bundle names no host and no port. Before WEB10 it named one on
// every build - `import.meta.env.VITE_API_URL ?? 'http://localhost:8001'` -
// so an unset variable pointed every browser at the user's own machine and a
// set one made the build environment-specific. Both are the same defect: a
// coordinate where a PATH belongs. The console now fetches `/api` and `/agent`
// on its own origin (web/delivery.json), and this is the check that it stays so.
//
// WHAT IT SCANS: every text asset in dist/ (js, css, html), comments and all -
// this is a scan of the OUTPUT, so J66's read-code-not-prose rule does not
// apply: a coordinate in a shipped comment is still a coordinate a reader of
// the bundle would act on.
//
// WHAT IT REJECTS: a `localhost:<port>` or `127.0.0.1:<port>`, and any absolute
// http(s) URL carrying an explicit port, which is the shape a service
// coordinate takes. Schema-namespace URLs (w3.org, the SVG namespace) carry no
// port and pass. A `//` followed by a bare host is deliberately not chased:
// the false-positive surface (protocol-relative asset paths in third-party
// CSS) is wider than the defect.

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const dist = resolve(here, '../dist')

// A coordinate the bundle DISPLAYS rather than CALLS. config/dev-environment.yaml
// is rendered verbatim on the admin config page (src/generated/enforcement-matrix.json
// carries the file's text), and it documents the local Neo4j container's ports.
// Keyed by chunk-name prefix; every entry must still be hit, so the list shrinks
// with the code rather than outliving it.
const ALLOWED = {
  'assets/AdminConfigRoute-': {
    'localhost:7474': 'dev-environment.yaml quoted as a document: the local Neo4j browser port',
    'localhost:7687': 'dev-environment.yaml quoted as a document: the local Neo4j bolt port',
    'http://localhost:7474': 'the same line of dev-environment.yaml, matched by the URL pattern too',
  },
}

const PATTERNS = [
  { name: 'localhost with a port', re: /localhost:\d{2,5}/g },
  { name: 'loopback with a port', re: /127\.0\.0\.1:\d{2,5}/g },
  { name: 'absolute URL with an explicit port', re: /https?:\/\/[A-Za-z0-9.-]+:\d{2,5}/g },
]

function* textFiles(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) yield* textFiles(p)
    else if (/\.(js|css|html|mjs)$/.test(name)) yield p
  }
}

let files
try {
  files = [...textFiles(dist)]
} catch (err) {
  // An instrument failure, and it says so: a missing dist/ would otherwise be
  // a vacuous pass, which is exactly what this check must never report.
  console.error(`dist check: cannot read ${dist} (${err.message}). Did the build run?`)
  process.exit(2)
}
if (files.length === 0) {
  console.error(`dist check: no js/css/html under ${dist}. Did the build run?`)
  process.exit(2)
}

const hits = []
const allowedHit = new Set()
for (const file of files) {
  const rel = relative(dist, file).split(sep).join('/')
  const text = readFileSync(file, 'utf8')
  const allowedHere = Object.entries(ALLOWED).find(([prefix]) => rel.startsWith(prefix))
  for (const { name, re } of PATTERNS) {
    for (const m of text.matchAll(re)) {
      if (allowedHere && m[0] in allowedHere[1]) {
        allowedHit.add(`${allowedHere[0]}${m[0]}`)
        continue
      }
      hits.push(`${rel}: ${name}: ${m[0]}`)
    }
  }
}

const stale = Object.entries(ALLOWED).flatMap(([prefix, coords]) =>
  Object.keys(coords).filter((c) => !allowedHit.has(`${prefix}${c}`)).map((c) => `${prefix}*: ${c}`),
)
if (stale.length) {
  console.error(`dist check FAILED: ${stale.length} ALLOWED entr(y/ies) no longer occur - remove them`)
  for (const s of stale) console.error(`  ${s}`)
  process.exit(1)
}

if (hits.length) {
  console.error(`dist check FAILED: ${hits.length} deployment coordinate(s) in the bundle`)
  for (const h of hits) console.error(`  ${h}`)
  console.error(
    'A production bundle names no host and no port (ADR 0020). The console calls the PATHS ' +
      'in web/delivery.json on its own origin; where the services live is the reverse proxy\u2019s ' +
      'business (DRYDOCS_API_UPSTREAM / DRYDOCS_AGENT_UPSTREAM for the Vite proxy, the Compose ' +
      'stack in production). Keep the coordinate out of src/, or behind import.meta.env.DEV.',
  )
  process.exit(1)
}

console.log(`dist check OK: ${files.length} text asset(s), no deployment coordinate`)
