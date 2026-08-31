// Why did that fetch throw? (O85)
//
// THE DEFECT THIS CLOSES. A browser fetch that fails reports the SAME opaque
// TypeError whether the server is down or the server answered and the browser
// discarded the answer for a cross-origin rule. Both call sites in this console
// picked one of those and asserted it: "drydocs-api unreachable at
// http://localhost:8001 — start it with: poetry run uvicorn ...". When the real
// cause was a blocked origin, that message sent the reader to start a server
// that was already running, and it is how a documented verification port and
// the API's allowlist stayed out of step from O69 until 2026-08-30 with nobody
// noticing (Idea-200, found while verifying O77 on a fallback port).
//
// THE PROBE, and why it can tell them apart when the failed request could not.
// A `mode: 'no-cors'` request is not subject to the allowlist: the browser
// sends it, and hands back an OPAQUE response it will not let the page read.
// Opaque is still a resolved promise. So:
//
//   probe resolves  -> something answered on that origin. The server is up, and
//                      the original request was discarded by a browser rule.
//   probe rejects   -> nothing answered. The server is not listening there.
//
// A 404 from the probe path is a RESOLVED opaque response and therefore a
// success here, which is correct: reachability is the question, not routing.
//
// WHAT IT DOES NOT PROVE, stated because the message must not overclaim. A
// reachable server plus a failed request is very strong evidence of a blocked
// origin and is not proof — a request aborted mid-flight, or a TLS failure on
// the real request only, would look the same. So the blocked-origin branch says
// what it OBSERVED (the server answered) and names the allowlist as the likely
// cause with the fix beside it, rather than asserting a diagnosis the way the
// message it replaces did.

export type NetworkVerdict = 'blocked-origin' | 'unreachable'

export interface NetworkDiagnosis {
  verdict: NetworkVerdict
  message: string
}

/** The command that starts the API, quoted in both messages. */
const START_COMMAND =
  'poetry run uvicorn drydocs_api.app:create_app --factory --port 8001'

/**
 * Diagnose a failed request to `baseUrl` with one extra probe.
 *
 * `fetchImpl` is injected so the branches are testable without a browser; it
 * defaults to the global fetch.
 */
export async function diagnoseNetworkFailure(
  baseUrl: string,
  fetchImpl: typeof fetch = fetch
): Promise<NetworkDiagnosis> {
  let reachable: boolean
  try {
    await fetchImpl(`${baseUrl}/docs`, { mode: 'no-cors' })
    reachable = true
  } catch {
    reachable = false
  }

  if (reachable) {
    return {
      verdict: 'blocked-origin',
      message:
        `${baseUrl} answered, so the API is running — the browser discarded the response. ` +
        `That is almost always a cross-origin rule: this page's origin (${pageOrigin()}) is ` +
        `not in the API's allowlist. Start the API with ` +
        `DRYDOCS_CORS_ORIGINS=${pageOrigin()}, or serve the console on a port the ` +
        'allowlist already names.',
    }
  }

  return {
    verdict: 'unreachable',
    message: `nothing answered at ${baseUrl} — start drydocs-api with: ${START_COMMAND}`,
  }
}

/** The page's own origin, or a readable stand-in outside a browser. */
function pageOrigin(): string {
  return typeof location === 'undefined' ? '(this origin)' : location.origin
}
