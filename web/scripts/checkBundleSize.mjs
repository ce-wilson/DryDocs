// WEB7 (b) — the initial-chunk ceiling. Run by the `web` CI job after the build.
//
// S8's bundle-budget half: nothing measured the bundle, so it grew from nobody
// deciding to. A ceiling turns growth into a decision — the number moves when
// someone moves it and writes down why, which is the whole mechanism.
//
// THE INITIAL CHUNK, not the total. Total dist size is the wrong number here:
// splitting a route out of the entry chunk does not shrink the total by one
// byte, and a ceiling on the total would score this item's own change as a
// no-op. What matters is what a browser downloads before it can render
// anything, which is `assets/index-*.js`.
//
// RAW BYTES, not gzip. Gzip is what crosses the wire, but it moves with the
// compressor version and would make the recorded number un-reproducible between
// a runner and a laptop. Raw is deterministic for a given build.

import { readdirSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * The ceiling, in raw bytes.
 *
 * 2026-09-05, WEB7: measured at 2,430,851 bytes, down from 3,711,290 before the
 * split — 1,280,439 bytes of role-gated and unopened-tab code that used to ship
 * to every persona. The ceiling is set ~3% above the measurement so a
 * whitespace-level change is not a red build; anything larger is a real growth
 * and should be looked at.
 *
 * IT RATCHETS DOWN, NEVER UP, WITHOUT A NOTE. Lowering it needs only a fresh
 * measurement. RAISING it means the initial download grew, so the line that
 * raises it says what arrived and why it belongs in the entry chunk rather than
 * behind a lazy boundary — that sentence is the point of the number.
 *
 * 2026-09-10, WEB23: RATCHETED DOWN to 2,500,000, measured at 2,427,507 bytes —
 * 72,493 of margin, 3.0%, which is the margin WEB7 set and which had been spent
 * without anyone deciding to spend it. It was NOT lowered to today's build; the
 * margin was restored by moving 79 KB out of the entry chunk, and this number
 * follows that measurement.
 *
 * WHAT MOVED, because the docstring is where the decision lives.
 * web/src/generated/load-map.json was in the entry chunk because
 * lineage/laneBasis.ts imported it statically and /lineage is open to every
 * role. WEB7 left it there on an ACCESS argument — the artifact is admissible to
 * a user — and that argument is still correct. It answers whether a persona may
 * have the file, not whether every persona must download it before anything
 * renders. Only the BDAT lane basis reads it, behind a picker most sessions
 * never touch, so it is fetched on demand now (lineage/layerSystems.ts) and
 * shares a chunk with the two lazy routes that already read it. Nothing was
 * hidden from anyone; 79 KB stopped arriving first.
 *
 * The ceiling was ALREADY EXCEEDED when this ran — 2,506,022 against 2,505,000 —
 * which is the condition WEB23 was minted from: the budget had 812 bytes left on
 * 2026-09-09 and the next change of any size was going to red the web job for
 * whoever made it. That is a guard naming the wrong author, so the margin is the
 * fix and not the number.
 */
const CEILING_BYTES = 2_500_000

const here = dirname(fileURLToPath(import.meta.url))
const assets = resolve(here, '../dist/assets')

const entries = readdirSync(assets).filter((f) => /^index-.*\.js$/.test(f))
if (entries.length !== 1) {
  // Not a size failure — an instrument failure, and it says so. A glob that
  // matched nothing would otherwise report a comfortable zero, which is the
  // vacuous pass this check would be worthless for.
  console.error(
    `bundle check: expected exactly one dist/assets/index-*.js, found ${entries.length} ` +
      `(${entries.join(', ') || 'none'}). Did the build run, or did the entry chunk get renamed?`,
  )
  process.exit(2)
}

const bytes = statSync(join(assets, entries[0])).size
const pct = ((bytes / CEILING_BYTES) * 100).toFixed(1)
const line = `initial chunk ${bytes.toLocaleString()} bytes / ceiling ${CEILING_BYTES.toLocaleString()} (${pct}%)`

if (bytes > CEILING_BYTES) {
  console.error(`bundle check FAILED: ${line}`)
  console.error(
    'The initial chunk is what every persona downloads before anything renders. ' +
      'Put the new code behind a lazy boundary, or raise CEILING_BYTES in ' +
      'web/scripts/checkBundleSize.mjs with a line saying what arrived and why it belongs here.',
  )
  process.exit(1)
}

console.log(`bundle check ok: ${line}`)
