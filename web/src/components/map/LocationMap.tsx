// LocationMap — the Z5 reusable console map.
//
// MODULE FIRST, PAGES SECOND. The Z5 directive names reuse as the point, so nothing
// here knows what a Server, a Job or a DevTeam is. It takes a list of DIMENSIONS
// (each a spec id plus how to label it), runs the selected one through the shared
// QuerySpec read path, resolves rows against the gazetteer, and draws them. Adding
// the next located label is a new QuerySpec and one more entry in `dimensions` —
// never a change in this file. The relationship dropdown IS that list.
//
// WHY A SPEC ID PER DIMENSION RATHER THAN A LABEL PROP: a Cypher label cannot be a
// query parameter, so a `label` prop would have to be interpolated into a query,
// which is injection. The registry holds the reviewed traversals; this component
// holds none.
//
// WHAT THE MAP REFUSES TO DO. It never invents a position. Rows the gazetteer cannot
// place are counted and listed rather than dropped, because a map with a missing dot
// reads as "nothing there" — the Z3 UNMATCHED discipline, one layer up. The
// unplaceable count sits in the footer at all times, including when it is zero.

import { useEffect, useMemo, useState } from 'react'
import type { GraphAccess } from '../../lib/graph'
import { COUNTRY_BY_ID, COUNTRY_SHAPES } from '../../generated/world-map'
import { MapGlyph, type GlyphKind } from './MapGlyphs'
import { frameFor, viewBox, WORLD_BOX, zoomOf, type Box } from './projection'
import { COUNTRY_NAMES, resolveRows, type LocationRow, type PlacedSite } from './resolve'

export interface MapDimension {
  /** Registry spec id — must return the shared map column shape. */
  specId: string
  /** Dropdown label, e.g. "Jobs". */
  label: string
  /** Glyph for origins from this dimension. */
  kind: GlyphKind
  /** One line under the dropdown: what the dimension actually claims. */
  note?: string
}

export interface LocationMapProps {
  access: GraphAccess
  dimensions: readonly MapDimension[]
  /** What a located node IS here — "data centers", "offices". Display only. */
  placeNoun?: string
  params?: Record<string, unknown>
  className?: string
}

type Load =
  | { state: 'loading' }
  | { state: 'error'; message: string }
  | { state: 'ready'; rows: LocationRow[] }

export default function LocationMap({
  access,
  dimensions,
  placeNoun = 'data centers',
  params,
  className,
}: LocationMapProps) {
  const [dimIndex, setDimIndex] = useState(0)
  const [load, setLoad] = useState<Load>({ state: 'loading' })
  const [countryId, setCountryId] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  const dimension = dimensions[dimIndex]
  const paramKey = JSON.stringify(params ?? {})

  useEffect(() => {
    let live = true
    setLoad({ state: 'loading' })
    access
      .runSpec(dimension.specId, params)
      .then((res) => {
        if (!live) return
        setLoad({ state: 'ready', rows: res.rows as unknown as LocationRow[] })
      })
      .catch((err: unknown) => {
        if (!live) return
        // Loud, never a silent empty map: an empty map and a failed query look
        // identical to a reader, and only one of them means "nothing is there".
        setLoad({ state: 'error', message: err instanceof Error ? err.message : String(err) })
      })
    return () => {
      live = false
    }
  }, [access, dimension.specId, paramKey, params])

  const resolved = useMemo(
    () => resolveRows(load.state === 'ready' ? load.rows : []),
    [load],
  )

  // Drilling into a country filters the sites; the frame then grows to include
  // whatever survived, so an outlying territory is never cropped.
  const visible = useMemo(
    () => (countryId ? resolved.sites.filter((s) => s.countryId === countryId) : resolved.sites),
    [resolved.sites, countryId],
  )
  const box: Box = useMemo(() => {
    const base = countryId ? (COUNTRY_BY_ID.get(countryId)?.bbox ?? WORLD_BOX) : WORLD_BOX
    return frameFor(base, visible.map((s) => s.point))
  }, [countryId, visible])
  const zoom = zoomOf(box)

  const touched = useMemo(() => new Set(resolved.countryIds), [resolved.countryIds])
  const maxOrigins = Math.max(1, ...visible.map((s) => s.origins.length))
  const active = visible.find((s) => s.key === selected) ?? null

  return (
    <section className={className} aria-label="Location map">
      {/* ---- controls: the relationship dropdown + the drill-down state ---- */}
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-[13px]">
          <span style={{ color: 'var(--muted)' }}>Show</span>
          <select
            className="rounded-md border px-2 py-1 text-[13px]"
            style={{
              borderColor: 'var(--edge)',
              background: 'var(--panel)',
              color: 'var(--text)',
            }}
            value={dimIndex}
            onChange={(e) => {
              setDimIndex(Number(e.target.value))
              setSelected(null)
            }}
          >
            {dimensions.map((d, i) => (
              <option key={d.specId} value={i}>
                {d.label} → {placeNoun}
              </option>
            ))}
          </select>
        </label>

        <span className="inline-flex items-center gap-1.5 text-[13px]" style={{ color: 'var(--muted)' }}>
          <MapGlyph kind={dimension.kind} size={15} />
          <span aria-hidden="true">→</span>
          <MapGlyph kind="building" size={15} />
        </span>

        {countryId && (
          <button
            type="button"
            className="rounded-md border px-2 py-1 text-[12px]"
            style={{ borderColor: 'var(--edge)', color: 'var(--text)', background: 'var(--panel)' }}
            onClick={() => {
              setCountryId(null)
              setSelected(null)
            }}
          >
            ← World
          </button>
        )}
        {countryId && (
          <span className="font-mono text-[12px]" style={{ color: 'var(--text)' }}>
            {COUNTRY_NAMES.get(countryId) ?? COUNTRY_BY_ID.get(countryId)?.name ?? countryId}
          </span>
        )}
      </div>

      {dimension.note && (
        <p className="mb-2 text-[12px]" style={{ color: 'var(--faint)' }}>
          {dimension.note}
        </p>
      )}

      {load.state === 'error' && (
        <p
          className="mb-2 rounded-md border px-3 py-2 font-mono text-[12px]"
          style={{ borderColor: 'var(--status-fail-soft)', color: 'var(--status-fail-soft)' }}
          role="alert"
        >
          {dimension.specId} failed — {load.message}
        </p>
      )}

      {/* ---- the map ---- */}
      <div
        className="overflow-hidden rounded-lg border"
        style={{ borderColor: 'var(--edge)', background: 'var(--bg2)' }}
      >
        <svg
          viewBox={viewBox(box)}
          className="block h-auto w-full"
          role="img"
          aria-label={`${dimension.label} by location`}
          strokeLinejoin="round"
        >
          {COUNTRY_SHAPES.map((c) => {
            const isTouched = touched.has(c.id)
            const isFocus = countryId === c.id
            return (
              <path
                key={c.id}
                d={c.d}
                fill={
                  isFocus
                    ? 'color-mix(in srgb, var(--blue) 24%, var(--panel))'
                    : isTouched
                      ? 'color-mix(in srgb, var(--blue) 14%, var(--panel))'
                      : 'var(--panel)'
                }
                stroke="var(--edge-soft)"
                strokeWidth={0.4 / zoom}
                style={{ cursor: isTouched ? 'pointer' : 'default' }}
                onClick={() => {
                  if (!isTouched) return
                  setCountryId(countryId === c.id ? null : c.id)
                  setSelected(null)
                }}
              >
                <title>{c.name}</title>
              </path>
            )
          })}

          {visible.map((site) => {
            const r = (3 + 3 * Math.sqrt(site.origins.length / maxOrigins)) / zoom
            const isActive = site.key === active?.key
            return (
              <g
                key={site.key}
                style={{ cursor: 'pointer' }}
                onClick={() => setSelected(isActive ? null : site.key)}
              >
                <circle
                  cx={site.point.x}
                  cy={site.point.y}
                  r={r}
                  fill={
                    site.synthetic
                      ? 'color-mix(in srgb, var(--yellow) 65%, transparent)'
                      : 'color-mix(in srgb, var(--teal) 70%, transparent)'
                  }
                  stroke={isActive ? 'var(--text)' : site.synthetic ? 'var(--yellow)' : 'var(--teal)'}
                  strokeWidth={(isActive ? 1.6 : 0.9) / zoom}
                />
                <title>
                  {`${site.cityName}${site.state ? `, ${site.state}` : ''} — ` +
                    `${site.origins.length} ${dimension.label.toLowerCase()}` +
                    `${site.dataCenters.length ? ` · ${site.dataCenters.join(', ')}` : ''}` +
                    `${site.synthetic ? ' · synthetic fixture' : ''}`}
                </title>
              </g>
            )
          })}
        </svg>
      </div>

      {/* ---- footer: coverage, always shown, including when it is zero ---- */}
      <Coverage
        placed={resolved.sites.length}
        origins={resolved.total}
        unplaceable={resolved.unplaceable.length}
        loading={load.state === 'loading'}
      />

      {active && <SiteDetail site={active} placeNoun={placeNoun} />}

      {resolved.unplaceable.length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-[12px]" style={{ color: 'var(--yellow)' }}>
            {resolved.unplaceable.length} row(s) could not be placed — see why
          </summary>
          <ul className="mt-1 space-y-0.5 font-mono text-[11px]" style={{ color: 'var(--muted)' }}>
            {resolved.unplaceable.slice(0, 40).map((u, i) => (
              <li key={`${u.origin}-${i}`}>
                <span style={{ color: 'var(--text)' }}>{u.origin}</span> — {u.said || '(no geography)'}{' '}
                <span style={{ color: 'var(--yellow)' }}>[{REASONS[u.reason]}]</span>
              </li>
            ))}
            {resolved.unplaceable.length > 40 && <li>…and {resolved.unplaceable.length - 40} more</li>}
          </ul>
        </details>
      )}
    </section>
  )
}

const REASONS: Record<string, string> = {
  'no-country': 'row carried no country',
  'unknown-country': 'country not in the gazetteer',
  'no-city': 'country-grain only — no city to place',
  'unknown-city': 'city not in the gazetteer',
}

function Coverage({
  placed,
  origins,
  unplaceable,
  loading,
}: {
  placed: number
  origins: number
  unplaceable: number
  loading: boolean
}) {
  return (
    <p className="mt-2 font-mono text-[12px]" style={{ color: 'var(--muted)' }}>
      {loading ? (
        'loading…'
      ) : (
        <>
          <span style={{ color: 'var(--text)' }}>{origins}</span> rows ·{' '}
          <span style={{ color: 'var(--teal)' }}>{placed}</span> place
          {placed === 1 ? '' : 's'} drawn ·{' '}
          <span style={{ color: unplaceable ? 'var(--yellow)' : 'var(--muted)' }}>
            {unplaceable} unplaceable
          </span>
        </>
      )}
    </p>
  )
}

function SiteDetail({ site, placeNoun }: { site: PlacedSite; placeNoun: string }) {
  return (
    <div
      className="mt-2 rounded-lg border p-3"
      style={{ borderColor: 'var(--edge)', background: 'var(--panel)' }}
    >
      <div className="flex items-center gap-2">
        <MapGlyph kind="building" size={16} />
        <span className="font-mono text-[13px]" style={{ color: 'var(--text)' }}>
          {site.cityName}
          {site.state ? `, ${site.state}` : ''} · {site.countryName}
        </span>
        <span className="text-[11px]" style={{ color: 'var(--faint)' }}>
          grain: {site.grain}
        </span>
        {site.synthetic && (
          <span className="text-[11px]" style={{ color: 'var(--yellow)' }}>
            synthetic fixture
          </span>
        )}
        {site.countryHasNoShape && !site.synthetic && (
          <span
            className="text-[11px]"
            style={{ color: 'var(--faint)' }}
            title="Natural Earth at 1:110m does not draw this country, so it never highlights and cannot be drilled into. The point itself is placed correctly."
          >
            no outline at this map resolution
          </span>
        )}
      </div>

      {site.dataCenters.length > 0 && (
        <p className="mt-1.5 font-mono text-[12px]" style={{ color: 'var(--muted)' }}>
          {placeNoun}: {site.dataCenters.join(' · ')}
        </p>
      )}

      <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
        {site.origins.slice(0, 60).map((o) => (
          <li
            key={`${o.kind}-${o.name}`}
            className="inline-flex items-center gap-1 font-mono text-[12px]"
            style={{ color: 'var(--text)' }}
          >
            <MapGlyph kind={o.kind} size={13} />
            {o.name}
          </li>
        ))}
        {site.origins.length > 60 && (
          <li className="text-[12px]" style={{ color: 'var(--muted)' }}>
            …and {site.origins.length - 60} more
          </li>
        )}
      </ul>
    </div>
  )
}
