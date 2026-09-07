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
import ts from 'typescript'

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
    // WEB6: A BINARY FIELD IS A Blob IN A BROWSER, NOT A STRING. FastAPI
    // declares the evidence upload's `files` as binary and the default mapping
    // made it `string[]`, so the one call site that sends real File objects
    // needed a double cast to get past its own generated type — the compiler
    // switched off at a seam whose whole purpose is to be checked.
    //
    // BOTH SPELLINGS, because the server's is not the one the recipe names.
    // OpenAPI 3.0 says `format: "binary"`; 3.1 says
    // `contentMediaType: "application/octet-stream"`, and drydocs_api emits 3.1
    // (Pydantic v2). A transform written for `format` alone changed NOTHING
    // here and would have read as a working fix — the regenerated file was
    // byte-identical, which is the only reason it was caught.
    transform(schemaObject) {
      const binary =
        schemaObject.format === 'binary' ||
        (schemaObject as { contentMediaType?: string }).contentMediaType ===
          'application/octet-stream'
      return binary
        ? ts.factory.createTypeReferenceNode(ts.factory.createIdentifier('Blob'))
        : undefined
    },
  })
  return BANNER + astToString(ast)
}
