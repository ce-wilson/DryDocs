import { expect, it } from 'vitest'

import { generate } from '../../scripts/genApiTypes'
import committed from './api.d.ts?raw'
import schema from './openapi.json'

// O70. The gates.json pattern applied to the API client: the committed types must
// equal a fresh generation from the committed schema, so a schema that moved
// without `npm run api:types` is a red test rather than a stale client. The
// schema's OWN drift guard is Python-side (tests/unit/test_openapi_client.py reads
// the importable app, never /openapi.json over HTTP — J37); together they hold the
// whole chain: drydocs_api → openapi.json → api.d.ts → tsc.

const lf = (text: string) => text.replace(/\r\n/g, '\n')

it('src/generated/api.d.ts is exactly what scripts/genApiTypes.ts generates from openapi.json', async () => {
  expect(lf(await generate(schema))).toBe(lf(committed))
})

it('the schema declares the response models the GraphAccess seam is pinned to', () => {
  // Names, not shapes: the shapes are asserted at compile time in lib/graphApi.ts.
  // This is the runtime twin, so a schema regenerated from a server that dropped
  // a declaration fails here with the model's name in the message.
  const schemas = Object.keys(schema.components.schemas)
  for (const name of ['NamedRunOut', 'SpecRunOut', 'SpecOut', 'LoginOut', 'NamedQueryOut']) {
    expect(schemas, `${name} is no longer declared by drydocs_api.schemas`).toContain(name)
  }
})
