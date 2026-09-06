// End-to-end runner for the console (O80).
//
// WHAT THIS PROVES THAT A UNIT TEST CANNOT. The acceptance asks for a path a
// person has actually had to verify by hand — sign in, reach a module, assert a
// rendered value — against the REAL dev server rather than a mocked shell. That
// means three real processes: Vite serving the app, drydocs-api answering
// /login, and a browser doing what a person does. A mocked login would prove the
// mock works.
//
// WHY THE CREDENTIAL IS BOOTSTRAPPED HERE, AT CONFIG LOAD. A fresh clone has no
// credential file and therefore no account that can sign in — the correct
// default, and the reason a naive e2e run would fail with "invalid credentials"
// on any machine but the author's. So the harness mints a throwaway one into a
// TEMP directory before anything starts. Doing it at config load rather than in
// globalSetup removes an ordering question outright: `webServer` processes
// inherit the env below, and they cannot start before the module that defines
// them has finished evaluating.
//
// THE SECRET IS PER-RUN AND NEVER TOUCHES THE REPO. It is generated here, lives
// in the environment of three child processes, and dies with the temp directory.
// The bootstrap script REFUSES to write to the machine's real credential path,
// so running this suite can never overwrite the secret a person signs in with.
import { execFileSync } from 'node:child_process'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { randomBytes } from 'node:crypto'

import { defineConfig, devices } from '@playwright/test'

// DEDICATED PORTS, NOT THE DEV DEFAULTS (8001 / 5173), and the reason is a bug
// this harness hit on its first local run. Playwright's `reuseExistingServer`
// would happily adopt an API a developer already had running — one pointed at
// their REAL credential file, which cannot verify the throwaway secret minted
// below, so every sign-in was refused and the suite failed on a machine where
// nothing was wrong. Reusing is never right for the API: this suite's login
// depends on the credential path it starts the process with. Separate ports mean
// the suite never adopts, never collides with, and never has to stop a console
// session somebody is using.
const API_PORT = 8011
// THE WEB PORT USED TO BE AN ORIGIN, which was the second bug the harness hit:
// the API's CORS allowlist named exactly two browser origins (vite dev 5173 and
// preview 4173), so serving the console anywhere else failed every /login
// preflight and the page showed "Failed to fetch"; the fix was an allowlist
// extension, DRYDOCS_CORS_ORIGINS, passed from here. ADR 0020 (WEB10) retired
// that whole class: the console is same-origin with its API - the page fetches
// `/api/...` on its own origin and the Vite dev server proxies it to
// DRYDOCS_API_UPSTREAM, which is the ONE place this harness now says where its
// API is. There is no allowlist to extend and no origin to declare; the port is
// still dedicated so the suite never collides with a console session in use.
const WEB_PORT = 5273
const REPO_ROOT = join(import.meta.dirname, '..')

// MINTED ONCE PER RUN, NOT ONCE PER PROCESS — the third bug the harness hit, and
// the least obvious. Playwright evaluates this config in the runner AND AGAIN in
// every worker process, so a straight `randomBytes` here minted a second secret
// in the worker while the API was still holding the first, and every sign-in came
// back 401 from a correctly configured server. Workers inherit the runner's
// environment, so the env vars are the handoff: whoever finds them already set is
// a worker and adopts them, and only the process that finds them absent generates
// and bootstraps. That also makes the whole block idempotent, which is what lets
// it sit at module scope safely.
const inherited = process.env.DRYDOCS_E2E_SECRET && process.env.DRYDOCS_CONSOLE_CREDENTIALS
const credentialPath =
  process.env.DRYDOCS_CONSOLE_CREDENTIALS ??
  join(mkdtempSync(join(tmpdir(), 'drydocs-e2e-')), 'console-credentials.json')
const secret = process.env.DRYDOCS_E2E_SECRET ?? randomBytes(24).toString('base64url')

process.env.DRYDOCS_CONSOLE_CREDENTIALS = credentialPath
process.env.DRYDOCS_E2E_SECRET = secret

if (!inherited) {
  execFileSync('poetry', ['run', 'python', join('web', 'e2e', 'bootstrap_credential.py')], {
    cwd: REPO_ROOT,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  })

  // Best-effort: the OS clears its temp dir anyway, but leaving a credential file
  // behind for the length of a CI job is a habit worth not forming. Registered
  // only in the process that created the directory — a worker deleting it would
  // pull the file out from under the still-running API.
  const credentialDir = dirname(credentialPath)
  process.on('exit', () => {
    try {
      rmSync(credentialDir, { recursive: true, force: true })
    } catch {
      /* the temp dir outliving the process is not worth failing a run over */
    }
  })
}

export default defineConfig({
  testDir: './e2e',
  // One worker and no retries: the suite drives a shared signed-in console
  // against one API process, so parallel workers would be racing over the same
  // session store for no gain at this size. Revisit when the suite is big enough
  // for that to cost real wall-clock.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // No Neo4j: the driver is created lazily, so the API boots and serves
      // /login without a graph. The e2e path is deliberately chosen to need
      // nothing more than that — see console.spec.ts.
      command: `poetry run uvicorn drydocs_api.app:create_app --factory --port ${API_PORT}`,
      cwd: REPO_ROOT,
      port: API_PORT,
      // Never reused, on any machine: this process must be the one started with
      // the throwaway credential path above (see the port comment).
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
      env: {
        DRYDOCS_CONSOLE_CREDENTIALS: credentialPath,
      },
    },
    {
      command: `npm run dev -- --port ${WEB_PORT} --strictPort`,
      cwd: import.meta.dirname,
      port: WEB_PORT,
      reuseExistingServer: false,
      timeout: 120_000,
      // The Vite PROCESS reads this to know where to proxy `/api` (vite.config.ts);
      // the page itself learns nothing but the path. Without it the proxy would
      // forward to the developer's 8001 rather than the suite's API.
      env: { DRYDOCS_API_UPSTREAM: `http://localhost:${API_PORT}` },
    },
  ],
})
