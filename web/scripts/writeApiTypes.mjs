// `npm run api:types` — write src/generated/api.d.ts from src/generated/openapi.json (O70).
// The generator is scripts/genApiTypes.ts (imported natively by Node 24's type
// stripping); this file only does the I/O the app tsconfig cannot type.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { generate } from './genApiTypes.ts'

const here = dirname(fileURLToPath(import.meta.url))
const schemaPath = resolve(here, '../src/generated/openapi.json')
const typesPath = resolve(here, '../src/generated/api.d.ts')

const text = await generate(JSON.parse(readFileSync(schemaPath, 'utf8')))
writeFileSync(typesPath, text, { encoding: 'utf8' })
console.log('wrote src/generated/api.d.ts')
