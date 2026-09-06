// Why did that call fail? (O85, reshaped by ADR 0020)
//
// THE DEFECT O85 CLOSED, and why it is now a RETIRED CLASS rather than a live
// branch. A browser fetch that fails reports the same opaque TypeError whether
// the server is down or the server answered and the browser discarded the
// answer for a cross-origin rule. Both call sites in this console picked one of
// those and asserted it ("drydocs-api unreachable ... start it with ..."), which
// sent readers to start a server that was already running, and it is how a
// documented verification port and the API's allowlist stayed out of step from
// O69 until 2026-08-30 with nobody noticing (Idea-200). O85 answered with a
// no-cors probe that told the two apart.
//
// ADR 0020 (WEB10) removed the boundary the probe diagnosed. The console is
// same-origin with drydocs-api in every environment: it calls the PATH `/api` on
// its own origin and a reverse proxy forwards it. There is no allowlist, so
// there is no blocked-origin verdict to reach, and the `mode: 'no-cors'` probe
// that reached it is gone with it. What a failed call can mean now is two
// things, and both are told apart by the RESPONSE, not by a second request:
//
//   the fetch THREW        -> nothing answered on this page's own origin. The
//                             server that serves the page is not answering (or
//                             the network is gone) - `unreachable`.
//   the proxy answered     -> the page's server is up but drydocs-api is not
//   502 / 503 / 504           answering behind it - `upstream-down`. Vite's
//                             proxy writes 502 on a dead upstream (vite.config.ts)
//                             so dev and the Compose stack read the same.
//
// The start-command hint is DEV-only: in production the reader cannot start
// anything from the page, and the hint would name a port the bundle must not
// carry (web/scripts/checkDistCoordinates.mjs).

export type NetworkVerdict = 'unreachable' | 'upstream-down'

export interface NetworkDiagnosis {
  verdict: NetworkVerdict
  message: string
}

/** The command that starts the API, quoted in DEV messages only. */
const START_COMMAND =
  'poetry run uvicorn drydocs_api.app:create_app --factory --port 8001'

/** The statuses a reverse proxy answers with when the service behind a path
 *  is not there: bad gateway, unavailable, gateway timeout. */
export function isUpstreamDown(status: number): boolean {
  return status === 502 || status === 503 || status === 504
}

/** The message for a proxy that answered for an absent upstream. `where` is
 *  the base path the call went to (`/api`, `/agent`). */
export function upstreamDownMessage(status: number, where: string): string {
  const dev = import.meta.env.DEV
    ? ` In dev that is Vite's proxy to DRYDOCS_API_UPSTREAM - start drydocs-api with: ${START_COMMAND}.`
    : ''
  return (
    `the server behind ${where} is not answering (the page's own server returned ${status} ` +
    `for it) - the service is down or not yet started, not this page.${dev}`
  )
}

/**
 * Diagnose a request to `baseUrl` that THREW. Kept async and with the same
 * name as O85's probe so its callers did not move; there is no probe left to
 * run, because there is no second cause left to separate.
 */
export async function diagnoseNetworkFailure(baseUrl: string): Promise<NetworkDiagnosis> {
  const dev = import.meta.env.DEV
    ? ` In dev that means the Vite dev server itself, not drydocs-api (a dead API answers 502 here); ` +
      `if it is drydocs-api you are starting: ${START_COMMAND}.`
    : ''
  return {
    verdict: 'unreachable',
    message:
      `nothing answered at ${baseUrl} on this page's own origin (${pageOrigin()}) - ` +
      `the server that serves this page is not answering.${dev}`,
  }
}

/** The page's own origin, or a readable stand-in outside a browser. */
function pageOrigin(): string {
  return typeof location === 'undefined' ? '(this origin)' : location.origin
}
