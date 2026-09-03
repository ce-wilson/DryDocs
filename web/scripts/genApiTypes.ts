// The one generator for src/generated/api.d.ts (O70) — pure, so the vitest drift
// guard (src/generated/api.test.ts) can import it under the app's tsconfig and
// regenerate in memory. The file WRITER is scripts/writeApiTypes.mjs (needs
// node:fs, which the app config deliberately has no types for); `npm run
// api:types` runs it. The openapi-typescript CLI is not used anywhere: it
// prepends a banner the programmatic API does not, so a file written by the CLI
// and checked against the API would never match.
//
// The schema itself is written by scripts/dump_openapi.py (repo root) from the
// importable app — regenerate in that order after any drydocs_api change:
//
//   poetry run python scripts/dump_openapi.py && (cd web && npm run api:types)

import openapiTS, { astToString } from 'openapi-typescript'

export const BANNER = [
  '// GENERATED from src/generated/openapi.json by scripts/genApiTypes.ts (O70).',
  '// Do not edit: regenerate with `poetry run python scripts/dump_openapi.py`',
  '// (repo root) then `npm run api:types`. src/generated/api.test.ts guards drift.',
  '',
].join('\n')

/** The generated module text for a schema object — deterministic for a given schema. */
export async function generate(schema: unknown): Promise<string> {
  const ast = await openapiTS(schema as Parameters<typeof openapiTS>[0], {
    // Every response body is declared by the server (drydocs_api.schemas) or is a
    // free object on purpose; the defaults keep unknown keys as `unknown`, which is
    // the honest type for a route the server has not modelled yet.
    alphabetize: true,
    exportType: true,
  })
  return BANNER + astToString(ast)
}
