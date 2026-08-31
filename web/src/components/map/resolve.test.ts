// Unit tests for resolveRows (O80).
//
// WHY THIS MODULE IS THE NAMED CASE. The Z5 map's two synthetic cities could
// never resolve: the index keyed them one way and every lookup asked another.
// No Python guard could see it — the defect was in TypeScript, and the Python
// side's own gazetteer guard was green throughout, because the artifact it
// checks was correct. The bug lived entirely in how this file READ that correct
// artifact. It was found by rendering the tab and reading the unplaceable list.
//
// These tests run against the REAL generated gazetteer rather than a fixture,
// deliberately. A fixture would have been written with the same wrong
// assumption the code had, and would have passed while the page stayed broken.
// The artifact is committed and deterministic, so this costs nothing in
// stability and buys the one property that matters: the test fails if either
// the code or the artifact drifts out of agreement with the other.
import { describe, expect, it } from 'vitest'

import { resolveRows, type LocationRow } from './resolve'

/** A row with only the fields a test cares about; the rest default to null. */
function row(over: Partial<LocationRow>): LocationRow {
  return {
    origin: 'srv-1',
    origin_kind: 'server',
    data_center: null,
    city: null,
    state: null,
    country: null,
    location_grain: null,
    ...over,
  }
}

describe('resolveRows — the synthetic-city regression (Z5)', () => {
  // THE REGRESSION ITSELF. Synthetic cities carry no numeric country_id, only
  // the alias 'SYN'. The index once lower-cased that alias into its key while
  // every lookup asked with the canonical id verbatim, so the fixture cities —
  // the one class of row that exists so an EMPTY graph still draws something —
  // were the only class that could not be drawn.
  it('places both synthetic cities, which is the case that was broken', () => {
    const result = resolveRows([
      row({ origin: 'syn-a', city: 'Otherton', country: 'Synthetica' }),
      row({ origin: 'syn-b', city: 'Sampleville', country: 'Synthetica' }),
    ])

    expect(result.unplaceable).toEqual([])
    expect(result.sites.map((s) => s.cityName).sort()).toEqual(['Otherton', 'Sampleville'])
    expect(result.sites.every((s) => s.synthetic)).toBe(true)
  })

  // A DEFECT THIS RUNNER FOUND ON ITS FIRST RUN, left failing on purpose and
  // marked so the suite is green while the gap stays visible. `it.fails` asserts
  // the CORRECT expectation and passes only while that expectation is unmet — so
  // the day resolve.ts is fixed, this line goes red and tells whoever fixed it to
  // flip `it.fails` back to `it`. Pinning the wrong value instead would have
  // enshrined the bug in a test, which is worse than having no test.
  //
  // THE DEFECT: Synthetica is declared `no_shape: true`, but the site reports
  // countryHasNoShape === false, so the UI offers an outline to tint and drill
  // into for a country that has none. The cause is the SAME FAMILY as the
  // original city-index bug this file was written to catch — the code reads
  // `city.country_id` and ignores `country_alias`, and a synthetic city carries
  // only the alias. `COUNTRY_NO_SHAPE.has(city.country_id ?? '')` asks for the
  // empty string and misses 'SYN'. `countryId` is null for the same reason, so
  // synthetic countries also never reach `countryIds`.
  //
  // NOT FIXED HERE by O80's scope guard: this item buys the test capability and
  // proves it, and changing what the map draws is Z-series work with its own
  // review. Inboxed to IDEAS.md at the build.
  it.fails('marks Synthetica as having no drawable outline rather than hiding it', () => {
    const [site] = resolveRows([row({ city: 'Otherton', country: 'Synthetica' })]).sites
    expect(site.countryHasNoShape).toBe(true)
  })
})

describe('resolveRows — nothing vanishes', () => {
  // The rule the file exists to enforce: a row that cannot be placed comes back
  // in `unplaceable` with a reason. A missing dot reads as "nothing there",
  // which is a different and worse claim than "we could not place this".
  it.each([
    ['no-country', row({ origin: 'a' })],
    ['unknown-country', row({ origin: 'b', city: 'Nowhere', country: 'Atlantis' })],
    ['no-city', row({ origin: 'c', country: 'United Kingdom' })],
    ['unknown-city', row({ origin: 'd', city: 'Nowhere', country: 'United Kingdom' })],
  ])('reports %s instead of dropping the row', (reason, input) => {
    const result = resolveRows([input as LocationRow])
    expect(result.sites).toEqual([])
    expect(result.unplaceable).toHaveLength(1)
    expect(result.unplaceable[0].reason).toBe(reason)
    expect(result.total).toBe(1)
  })

  it('accounts for every input row exactly once, placed or not', () => {
    const rows = [
      row({ origin: 'a', city: 'Edinburgh', country: 'United Kingdom' }),
      row({ origin: 'b', country: 'United Kingdom' }),
      row({ origin: 'c' }),
    ]
    const { sites, unplaceable, total } = resolveRows(rows)
    const placedOrigins = sites.reduce((n, s) => n + s.origins.length, 0)
    expect(placedOrigins + unplaceable.length).toBe(total)
    expect(total).toBe(3)
  })

  // Country-grain data is real and common (the Idea-90 mixed-grain finding). It
  // is NOT placed as a pin, because a pin asserts a position the source never
  // gave — but the country still counts as touched.
  it('does not invent a pin for country-grain rows', () => {
    const result = resolveRows([row({ country: 'United Kingdom' })])
    expect(result.sites).toEqual([])
    expect(result.unplaceable[0].reason).toBe('no-city')
  })
})

describe('resolveRows — forgiving in case and spacing, strict in country', () => {
  it('normalizes city and country tokens', () => {
    const result = resolveRows([row({ city: '  eDinBurgh  ', country: 'united   kingdom' })])
    expect(result.unplaceable).toEqual([])
    expect(result.sites[0].cityName).toBe('Edinburgh')
  })

  it('accepts a country alias as readily as its full name', () => {
    const byAlias = resolveRows([row({ city: 'Edinburgh', country: 'UK' })])
    const byName = resolveRows([row({ city: 'Edinburgh', country: 'United Kingdom' })])
    expect(byAlias.sites[0].key).toBe(byName.sites[0].key)
  })

  // City names are not globally unique — there is a London in Ontario — so the
  // country is part of the key, always. Asking for a real city under the wrong
  // country must miss rather than silently place the other one.
  it('keys on country, so a city under the wrong country does not resolve', () => {
    const result = resolveRows([row({ city: 'Edinburgh', country: 'Australia' })])
    expect(result.sites).toEqual([])
    expect(result.unplaceable[0].reason).toBe('unknown-city')
  })
})

describe('resolveRows — aggregation', () => {
  it('merges rows at one city and de-duplicates data centres and origins', () => {
    const result = resolveRows([
      row({ origin: 'srv-a', city: 'Edinburgh', country: 'UK', data_center: 'DC1' }),
      row({ origin: 'srv-a', city: 'Edinburgh', country: 'UK', data_center: 'DC1' }),
      row({ origin: 'srv-b', city: 'Edinburgh', country: 'UK', data_center: 'DC2' }),
    ])
    expect(result.sites).toHaveLength(1)
    expect(result.sites[0].dataCenters).toEqual(['DC1', 'DC2'])
    expect(result.sites[0].origins.map((o) => o.name)).toEqual(['srv-a', 'srv-b'])
  })

  it('treats an unrecognized origin_kind as a server rather than failing', () => {
    const result = resolveRows([
      row({ origin_kind: 'wildly-unexpected', city: 'Edinburgh', country: 'UK' }),
    ])
    expect(result.sites[0].origins[0].kind).toBe('server')
  })

  it('sorts sites by how many origins they carry', () => {
    const result = resolveRows([
      row({ origin: 'only', city: 'Glasgow', country: 'UK' }),
      row({ origin: 'a', city: 'Edinburgh', country: 'UK' }),
      row({ origin: 'b', city: 'Edinburgh', country: 'UK' }),
    ])
    expect(result.sites[0].cityName).toBe('Edinburgh')
  })

  it('reports each country once in countryIds', () => {
    const result = resolveRows([
      row({ origin: 'a', city: 'Edinburgh', country: 'UK' }),
      row({ origin: 'b', city: 'Glasgow', country: 'UK' }),
    ])
    expect(result.countryIds).toEqual(['826'])
  })

  it('is empty and honest about it for no rows at all', () => {
    expect(resolveRows([])).toEqual({ sites: [], unplaceable: [], countryIds: [], total: 0 })
  })
})
