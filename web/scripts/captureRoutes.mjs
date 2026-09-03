// `npm run paper` — capture executed console routes to self-contained printable
// HTML (O88), the console's paper form for the L6 pen-and-paper feedback loop.
//
//   npm run paper -- --persona mouse                       # the named starting set
//   npm run paper -- --persona trinity --routes /gates,/software,/load-map --web http://localhost:5173
//   echo "$SECRET" | npm run paper -- --persona mouse --secret-stdin
//
// CAPTURE, DO NOT RE-IMPLEMENT (clause a). The console is a React SPA over a
// live API, so its paper form is the EXECUTED DOM: this script drives the running
// console through headless Edge — the same browser the `verify` skill's design-doc
// recipe launches — and writes what the browser rendered. Edge is DRIVEN through
// Playwright rather than flagged with --dump-dom because a flag cannot sign in,
// and clause (d) forbids a sign-in screen presented as a captured page. Without
// Edge on the machine, --browser chromium uses the O80 harness's build; the
// manifest records which executed the page.
//
// THE PAYLOAD IS NOT COMMITTED (clause e). A capture of a live console can carry
// real graph values, so it lands under DRYDOCS_DATA_ROOT/console-captures/<utc
// stamp>/ (mandatory, G81 — no default root; --out overrides). The committed
// artifacts are this script, src/lib/paperForm.ts and src/styles/print.css.
//
// THE SECRET NEVER TOUCHES ARGV OR THE ENVIRONMENT. It is read from a no-echo
// prompt, or from stdin with --secret-stdin, used once in the sign-in form, and
// never written anywhere — O80's provenance record distinguishes a prompted
// secret from a generated one, and a flag would be a third, unrecorded origin.
//
// THE FOOTER NAMES THE MOMENT (clause b): route, the capture host's HEAD (with
// "(dirty)" when the tree differed), the UTC time, the API origin the page ITSELF
// requested at sign-in (observed, not configured), the persona, the browser.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'

// `playwright` is the runtime package `@playwright/test` (a devDependency) pins at
// its own version; `@playwright/test` re-exports only the test API, not the
// browser launchers, so the launcher comes from the package that owns it.
import { chromium } from 'playwright'
import { JSDOM } from 'jsdom'

import { assemblePaperDocument, externalReferences, routeSlug } from '../src/lib/paperForm.ts'

const HERE = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = resolve(HERE, '..', '..')

// The named starting set (clause d): the three SME-designated governed surfaces,
// which render from COMMITTED GENERATED ARTIFACTS and therefore need no graph —
// capturable on any machine, and exactly the pages FB-03 says get reviewed.
// Graph-backed routes are opt-in via --routes and are only as good as the graph
// behind the API at capture time; the footer's commit and time say which moment.
const DEFAULT_ROUTES = ['/gates', '/software', '/load-map']

function usage(message) {
  if (message) console.error(`captureRoutes: ${message}`)
  console.error(
    'usage: node scripts/captureRoutes.mjs --persona <id> [--routes /a,/b] [--web URL] ' +
      '[--out DIR] [--browser msedge|chromium] [--secret-stdin] [--verify-print]',
  )
  return 2
}

function parseArgs(argv) {
  const opts = {
    persona: null,
    routes: DEFAULT_ROUTES,
    web: 'http://localhost:5173',
    out: null,
    browser: 'msedge',
    secretStdin: false,
    verifyPrint: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = () => {
      i += 1
      if (i >= argv.length) throw new Error(`${arg} needs a value`)
      return argv[i]
    }
    switch (arg) {
      case '--persona':
        opts.persona = next()
        break
      case '--routes':
        opts.routes = next()
          .split(',')
          .map((r) => r.trim())
          .filter(Boolean)
        break
      case '--web':
        opts.web = next().replace(/\/+$/, '')
        break
      case '--out':
        opts.out = next()
        break
      case '--browser':
        opts.browser = next()
        break
      case '--secret-stdin':
        opts.secretStdin = true
        break
      case '--verify-print':
        opts.verifyPrint = true
        break
      default:
        throw new Error(`unknown option ${arg}`)
    }
  }
  if (!opts.persona) throw new Error('--persona is required')
  if (!['msedge', 'chromium'].includes(opts.browser)) throw new Error('--browser is msedge or chromium')
  for (const r of opts.routes) if (!r.startsWith('/')) throw new Error(`route must start with /: ${r}`)
  return opts
}

async function readSecret(fromStdin) {
  if (fromStdin) {
    const chunks = []
    for await (const chunk of process.stdin) chunks.push(chunk)
    return Buffer.concat(chunks).toString('utf8').replace(/\r?\n$/, '')
  }
  // No-echo prompt: readline with a muted output stream (the standard idiom).
  const rl = createInterface({ input: process.stdin, output: process.stdout, terminal: true })
  const muted = { muted: false }
  const write = rl._writeToOutput.bind(rl)
  rl._writeToOutput = (s) => {
    if (!muted.muted) write(s)
  }
  return new Promise((resolveSecret) => {
    rl.question('console secret (not echoed): ', (answer) => {
      muted.muted = false
      process.stdout.write('\n')
      rl.close()
      resolveSecret(answer)
    })
    muted.muted = true
  })
}

function gitCommit() {
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO_ROOT, encoding: 'utf8' }).trim()
  const dirty = execFileSync('git', ['status', '--porcelain'], { cwd: REPO_ROOT, encoding: 'utf8' }).trim()
  return dirty ? `${head} (dirty)` : head
}

function outputDir(explicit, stamp) {
  if (explicit) return resolve(explicit)
  const root = process.env.DRYDOCS_DATA_ROOT
  if (!root) {
    throw new Error(
      'DRYDOCS_DATA_ROOT is not set and --out was not given. Captures land under the data ' +
        'root by the same rule as every other output (G81: no default root) — set it, or pass --out.',
    )
  }
  return join(root, 'console-captures', stamp)
}

/** In the page: turn every <img> and <canvas> into a data URI so the capture
 *  fetches nothing on open, and gather every stylesheet's rules as text. */
async function inlineAndCollect(page) {
  return page.evaluate(async () => {
    const toDataUrl = async (url) => {
      const res = await fetch(url)
      const blob = await res.blob()
      return await new Promise((ok, fail) => {
        const reader = new FileReader()
        reader.onload = () => ok(reader.result)
        reader.onerror = () => fail(reader.error)
        reader.readAsDataURL(blob)
      })
    }
    for (const img of Array.from(document.images)) {
      const src = img.currentSrc || img.src
      if (!src || src.startsWith('data:')) continue
      try {
        img.setAttribute('src', await toDataUrl(src))
        img.removeAttribute('srcset')
      } catch {
        img.setAttribute('data-dd-uninlined', src)
      }
    }
    for (const canvas of Array.from(document.querySelectorAll('canvas'))) {
      try {
        const img = document.createElement('img')
        img.src = canvas.toDataURL('image/png')
        img.width = canvas.width
        img.height = canvas.height
        img.setAttribute('data-dd-from', 'canvas')
        canvas.replaceWith(img)
      } catch {
        /* a tainted canvas stays a canvas; the reference sweep reports nothing for it */
      }
    }
    const css = Array.from(document.styleSheets)
      .map((sheet) => {
        try {
          return Array.from(sheet.cssRules)
            .map((r) => r.cssText)
            .join('\n')
        } catch {
          return ''
        }
      })
      .join('\n')
    // @font-face rules point at font files; the print sheet names system fonts
    // and the screen copy falls back to them, so the rules go rather than the
    // files coming along (hundreds of kB each and an external request otherwise).
    return { css: css.replace(/@font-face\s*\{[^}]*\}/g, ''), html: document.documentElement.outerHTML }
  })
}

async function signIn(page, web, personaId, secret) {
  await page.goto(`${web}/`, { waitUntil: 'networkidle' })
  const heading = page.getByRole('heading', { name: 'DryDocs Console' })
  await heading.waitFor({ timeout: 15_000 })
  // A sign-in button's accessible name is the persona's display name — the id
  // capitalised (lib/auth.ts) — followed by its role chip, so match the name at
  // the START of the button text, case-insensitively, as a whole word.
  await page.getByRole('button', { name: new RegExp(`^${personaId}\\b`, 'i') }).click()
  await page.locator('#console-secret').fill(secret)
  await page.getByRole('button', { name: 'Sign in' }).click()
  try {
    await heading.waitFor({ state: 'hidden', timeout: 15_000 })
  } catch {
    throw new Error(`sign-in as ${personaId} was refused — the sign-in screen is still up`)
  }
}

async function verifyPrintGutter(browser, file) {
  const page = await browser.newPage()
  try {
    await page.goto(`file://${file}`)
    await page.emulateMedia({ media: 'print' })
    return await page.evaluate(() => {
      const tag = document.querySelector('.dd-margin-tag')
      const footer = document.querySelector('.dd-print-footer')
      return {
        tagDisplay: tag ? getComputedStyle(tag).display : null,
        footerDisplay: footer ? getComputedStyle(footer).display : null,
      }
    })
  } finally {
    await page.close()
  }
}

async function main() {
  let opts
  try {
    opts = parseArgs(process.argv.slice(2))
  } catch (err) {
    return usage(err.message)
  }
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').replace(/-\d{3}Z$/, 'Z')
  const outDir = outputDir(opts.out, stamp)
  const secret = await readSecret(opts.secretStdin)
  if (!secret) return usage('an empty secret cannot sign in')
  const commit = gitCommit()

  let browser
  let browserName = opts.browser
  try {
    browser = await chromium.launch({ channel: opts.browser === 'msedge' ? 'msedge' : undefined, headless: true })
  } catch (err) {
    if (opts.browser !== 'msedge') throw err
    console.error(`captureRoutes: headless Edge unavailable (${err.message.split('\n')[0]}); using chromium`)
    browser = await chromium.launch({ headless: true })
    browserName = 'chromium'
  }
  const browserLabel = `${browserName} ${browser.version()}`

  const manifest = {
    schema: 'drydocs.console-capture.v1',
    captured_at: new Date().toISOString(),
    commit,
    web: opts.web,
    api: null,
    persona: opts.persona,
    browser: browserLabel,
    routes: [],
  }

  try {
    const context = await browser.newContext({ colorScheme: 'light', viewport: { width: 1280, height: 900 } })
    const page = await context.newPage()
    // The API the page READ, observed from its own sign-in request.
    page.on('request', (req) => {
      if (req.method() === 'POST' && /\/login$/.test(req.url())) manifest.api = new URL(req.url()).origin
    })
    await signIn(page, opts.web, opts.persona, secret)
    if (!manifest.api) throw new Error('no /login request was observed — cannot name the API the page read')

    mkdirSync(outDir, { recursive: true })
    for (const route of opts.routes) {
      await page.goto(`${opts.web}${route}`, { waitUntil: 'load' })
      // Best-effort quiet: a route that polls never reaches "networkidle", and a
      // capture must not hang on it — 15 s of trying, then whatever the page shows,
      // which the footer's timestamp is honest about either way.
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined)
      await page.waitForTimeout(1_000) // the last spec run's rows land after the network goes quiet
      const capturedAt = new Date().toISOString()
      const { css, html } = await inlineAndCollect(page)
      const provenance = { route, commit, capturedAt, api: manifest.api, persona: opts.persona, browser: browserLabel }
      const dom = new JSDOM(html)
      const tags = assemblePaperDocument(dom.window.document, { css, provenance })
      const text = `<!doctype html>\n${dom.window.document.documentElement.outerHTML}\n`
      const leftovers = externalReferences(text)
      const file = join(outDir, `${routeSlug(route)}.html`)
      writeFileSync(file, text, { encoding: 'utf8' })
      const entry = {
        route,
        file,
        captured_at: capturedAt,
        margin_tags: tags,
        bytes: Buffer.byteLength(text, 'utf8'),
        sha256: createHash('sha256').update(text).digest('hex'),
        self_contained: leftovers.length === 0,
        external_references: leftovers,
      }
      if (opts.verifyPrint) entry.print_media = await verifyPrintGutter(browser, file)
      manifest.routes.push(entry)
      console.log(
        `${route} -> ${file} (${tags} tags, ${entry.bytes} bytes${leftovers.length ? `, ${leftovers.length} EXTERNAL REFERENCES` : ''})`,
      )
    }
  } finally {
    await browser.close()
  }

  const manifestPath = join(outDir, 'capture-manifest.json')
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, { encoding: 'utf8' })
  console.log(`manifest -> ${manifestPath}`)
  const unclean = manifest.routes.filter((r) => !r.self_contained)
  if (unclean.length) {
    console.error(`captureRoutes: ${unclean.length} capture(s) still reference external resources — not self-contained`)
    return 1
  }
  return 0
}

try {
  process.exitCode = await main()
} catch (err) {
  // A refused sign-in, an unreachable console, a browser that would not launch:
  // one line naming it, exit 1 — a stack trace is not the operator's outcome.
  console.error(`captureRoutes: ${err instanceof Error ? err.message.split('\n')[0] : String(err)}`)
  process.exitCode = 1
}
