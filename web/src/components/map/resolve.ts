// Turn QuerySpec rows into things a map can draw — and, just as importantly, into
// an honest account of what it could NOT draw.
//
// THE RULE THIS FILE EXISTS TO ENFORCE. A row the gazetteer cannot place must never
// simply vanish. A map with a missing dot reads as "nothing there", which is a
// different and much worse claim than "we could not place this". Z3 established the
// discipline one layer down — its loader records match_tier / UNMATCHED "so coverage
// gaps are visible instead of dropped" — and `resolveRows` carries it up: everything
// that fails to resolve comes back in `unplaceable`, with the reason, for the caller
// to show.

import gazetteer from '../../generated/gazetteer.json'
import { project, type Point } from './projection'

export interface LocationRow {
  origin: string
  origin_kind: string
  data_center: string | null
  city: string | null
  state: string | null
  country: string | null
  location_grain: string | null
}

export type OriginKind = 'server' | 'job' | 'team'

export interface PlacedSite {
  /** Stable key: the finest identity the row carried. */
  key: string
  cityName: string
  state: string | null
  countryId: string | null
  countryName: string
  /** The source is too coarse to draw this country (e.g. Singapore at 1:110m).
   *  The point still plots; there is simply no outline to tint or drill into,
   *  and the UI says so rather than letting it read as missing data. */
  countryHasNoShape: boolean
  point: Point
  synthetic: boolean
  /** Declared grain of the underlying data (Idea-90 / Z2), NOT of the pin. */
  grain: string
  /** Data centres seen at this place — the building icon's subjects. */
  dataCenters: string[]
  origins: { name: string; kind: OriginKind }[]
}

export interface Unplaceable {
  origin: string
  kind: OriginKind
  /** What the row said, so the gap is diagnosable without opening the graph. */
  said: string
  reason: 'no-country' | 'unknown-country' | 'no-city' | 'unknown-city'
}

export interface ResolveResult {
  sites: PlacedSite[]
  unplaceable: Unplaceable[]
  /** Countries with at least one placed site — drives the drill-down list. */
  countryIds: string[]
  total: number
}

interface GazCity {
  id: string
  name: string
  state: string | null
  country_id: string | null
  country_alias: string | null
  lat: number
  lon: number
  x: number
  y: number
  grain: string
  synthetic: boolean
}

const COUNTRY_LOOKUP = gazetteer.country_lookup as Record<string, string>
const COUNTRY_NAME = new Map(gazetteer.countries.map((c) => [c.id, c.name]))
const COUNTRY_NO_SHAPE = new Set(
  gazetteer.countries.filter((c) => c.no_shape).map((c) => c.id),
)
const CITIES = gazetteer.cities as GazCity[]

/** Matching normal form — must agree with render_gazetteer.py's `_norm`. */
function norm(token: string): string {
  return token.trim().split(/\s+/).join(' ').toLowerCase()
}

/** city name + country -> gazetteer row. City names are not globally unique
 *  (there is a London in Ontario), so the country is part of the key, always. */
const CITY_INDEX = new Map<string, GazCity>()
for (const city of CITIES) {
  // The key's country half is the CANONICAL id verbatim — `country_lookup`
  // returns exactly that, so normalizing here would build a key the lookup can
  // never produce. It did: a synthetic city carries no numeric country_id, so
  // this line lower-cased its alias to `syn|` while every lookup asked for
  // `SYN|`, and both fixture cities silently reported "city not in the
  // gazetteer" — the one class of row that exists so an empty graph still draws
  // something was the only class that could not be drawn.
  const countryKey = city.country_id ?? city.country_alias ?? ''
  CITY_INDEX.set(`${countryKey}|${norm(city.name)}`, city)
}

function toKind(raw: string): OriginKind {
  return raw === 'job' || raw === 'team' ? raw : 'server'
}

export function resolveRows(rows: readonly LocationRow[]): ResolveResult {
  const sites = new Map<string, PlacedSite>()
  const unplaceable: Unplaceable[] = []

  for (const row of rows) {
    const kind = toKind(row.origin_kind)
    const said = [row.data_center, row.city, row.state, row.country]
      .filter(Boolean)
      .join(', ')

    if (!row.country) {
      unplaceable.push({ origin: row.origin, kind, said: said || '(no geography)', reason: 'no-country' })
      continue
    }
    const countryId = COUNTRY_LOOKUP[norm(row.country)]
    if (!countryId) {
      unplaceable.push({ origin: row.origin, kind, said, reason: 'unknown-country' })
      continue
    }
    if (!row.city) {
      // Country-grain data is real and common (the Idea-90 mixed-grain finding).
      // It is NOT placed as a pin, because a pin asserts a position the source
      // never gave — it is reported instead, and the country still counts as
      // touched via `countryIds` below.
      unplaceable.push({ origin: row.origin, kind, said, reason: 'no-city' })
      continue
    }
    const city = CITY_INDEX.get(`${countryId}|${norm(row.city)}`)
    if (!city) {
      unplaceable.push({ origin: row.origin, kind, said, reason: 'unknown-city' })
      continue
    }

    const key = city.id
    let site = sites.get(key)
    if (!site) {
      // Z9: the SAME fallback the index key uses above. A synthetic city carries
      // no numeric country_id, only its alias, so every country-keyed read here
      // must ask with the key the gazetteer's countries table actually carries.
      // Reading country_id alone asked COUNTRY_NO_SHAPE for '' and missed SYN
      // (Synthetica offered an outline it does not have), and left countryId
      // null (Synthetica never reached countryIds or the drill-down list) — the
      // Z5 family: an identifier read on one axis while the data carries it on
      // another. O80's runner found it on its first run.
      const countryKey = city.country_id ?? city.country_alias
      site = {
        key,
        cityName: city.name,
        state: city.state,
        countryId: countryKey,
        countryName: COUNTRY_NAME.get(countryKey ?? '') ?? row.country,
        countryHasNoShape: COUNTRY_NO_SHAPE.has(countryKey ?? ''),
        // Re-projected from lat/lon rather than trusting the artifact's cached
        // x/y, so the two can never silently disagree; the guard asserts they
        // agree, and this makes the runtime independent of that.
        point: project(city.lon, city.lat),
        synthetic: city.synthetic,
        grain: row.location_grain ?? city.grain,
        dataCenters: [],
        origins: [],
      }
      sites.set(key, site)
    }
    if (row.data_center && !site.dataCenters.includes(row.data_center)) {
      site.dataCenters.push(row.data_center)
    }
    if (!site.origins.some((o) => o.name === row.origin && o.kind === kind)) {
      site.origins.push({ name: row.origin, kind })
    }
  }

  const placed = [...sites.values()].sort((a, b) => b.origins.length - a.origins.length)
  for (const site of placed) {
    site.dataCenters.sort()
    site.origins.sort((a, b) => a.name.localeCompare(b.name))
  }
  return {
    sites: placed,
    unplaceable,
    countryIds: [...new Set(placed.map((s) => s.countryId).filter((id): id is string => !!id))],
    total: rows.length,
  }
}

export const COUNTRY_NAMES = COUNTRY_NAME
