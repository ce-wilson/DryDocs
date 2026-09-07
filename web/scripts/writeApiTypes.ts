// `npm run api:types` — write src/generated/api.d.ts from src/generated/openapi.json (O70).
// The generator is scripts/genApiTypes.ts. Both files are TypeScript, run
// natively by Node 24's type stripping, so `node scripts/writeApiTypes.ts` is
// the command. WEB16 moved this file off .mjs for a reason worth stating: it
// now EXPORTS its diagnostic so a test can import it, and an untyped .mjs
// import fails `tsc` at the call site rather than here.
//
// WEB16 — WHY THIS SCRIPT REPORTS ON A FILE IT DOES NOT WRITE. It reads
// openapi.json, which `scripts/dump_openapi.py` produces, and that writer needs
// DRYDOCS_DATA_ROOT set (it imports `create_app`, which resolves the root at
// import; G81 removed the default). Run the pair as the README's one-liner does
// and a missing root fails in the python half — but until API3 that failure
// TRUNCATED openapi.json first, so this step then failed on an empty document,
// three layers down from the cause, with a JSON parse error for a message. Both
// halves are fixed: the python side no longer touches the artifact when it
// cannot render it, and this side names the file, the writer, and the variable
// that writer needs instead of letting a parse error stand in for all three.
//
// NOTE WHAT IS **NOT** CLAIMED HERE: this script does not need
// DRYDOCS_DATA_ROOT. It reads a committed JSON file and writes a .d.ts, and it
// works perfectly well with the variable unset. Checking for it here would
// assert a precondition that is not real and would refuse a run that would have
// succeeded. What the variable belongs to is the writer, and that is what the
// message says.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

import { generate } from './genApiTypes.ts'

const here = dirname(fileURLToPath(import.meta.url))
const schemaPath = resolve(here, '../src/generated/openapi.json')
const typesPath = resolve(here, '../src/generated/api.d.ts')

/** The one place the chain is explained, so every failure below says the same thing. */
const HOW_TO_MAKE_IT = [
  'src/generated/openapi.json is written by scripts/dump_openapi.py, from the repo root:',
  '',
  '    DRYDOCS_DATA_ROOT=<your data root> poetry run python scripts/dump_openapi.py',
  '    cd web && npm run api:types',
  '',
  'DRYDOCS_DATA_ROOT is required by THAT script, not by this one: it imports',
  'create_app(), which resolves the data root at import and has no default (G81).',
].join('\n')

/** What is wrong with this schema text, or null when nothing is.
 *
 *  Split out from the I/O so the MESSAGES are testable
 *  (`src/generated/apiTypesDiagnostic.test.ts`). A diagnostic nobody exercises drifts into
 *  being wrong, and this one exists precisely because the diagnostic it
 *  replaces was a JSON parse error standing in for three different causes. */
export function schemaProblem(raw: string | null | undefined): string | null {
  if (raw === null || raw === undefined) {
    return 'cannot read src/generated/openapi.json'
  }
  if (raw.trim().length === 0) {
    // The exact state a pre-API3 failed dump left behind, called by its name
    // rather than reported as a syntax error at position 0.
    return 'src/generated/openapi.json is EMPTY — a previous dump was interrupted'
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch (err) {
    return `src/generated/openapi.json is not valid JSON (${(err as Error).message})`
  }
  if (!parsed || typeof parsed !== 'object' || !('paths' in parsed)) {
    return 'src/generated/openapi.json parsed but declares no `paths` — it is not an OpenAPI document'
  }
  return null
}

/** The whole message a failed run prints: the problem, then the chain that
 *  produces the file, then which command the variable actually belongs to. */
export function failureText(problem: string): string {
  return `api:types FAILED: ${problem}\n\n${HOW_TO_MAKE_IT}`
}

function fail(what: string): never {
  console.error(failureText(what))
  process.exit(1)
}

async function main() {
  let raw: string | null = null
  try {
    raw = readFileSync(schemaPath, 'utf8')
  } catch (err) {
    const oops = err as NodeJS.ErrnoException
    fail(`cannot read src/generated/openapi.json (${oops.code ?? oops.message})`)
  }

  const problem = schemaProblem(raw)
  if (problem) fail(problem)

  const text = await generate(JSON.parse(raw as string))
  writeFileSync(typesPath, text, { encoding: 'utf8' })
  console.log('wrote src/generated/api.d.ts')
}

// The I/O runs only when this file IS the command. Without the guard, importing
// it to test the messages above REWRITES a committed artifact as a side effect
// of collection — which the first version of the test did, and which is the
// kind of thing that shows up later as an unexplained diff.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main()
}
