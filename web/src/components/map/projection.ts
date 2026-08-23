// The TypeScript twin of scripts/render_world_map.py's projection.
//
// THE ONE INVARIANT: this must produce the same numbers as the Python. The country
// shapes in ../../generated/world-map.ts were baked with that formula; a point
// plotted with a different one lands off the shape it belongs to, and nothing about
// the resulting picture looks broken — a data centre simply sits in the sea near
// where it should be. That silent-wrongness is exactly why the projection is
// equirectangular: it is two lines of arithmetic, so "the two sides agree" is
// something a guard can assert rather than something we hope for.
// tests/unit/test_location_gazetteer.py::test_projection_matches_the_world_map pins it.

import { MAP_HEIGHT, MAP_WIDTH } from '../../generated/world-map'

export interface Point {
  x: number
  y: number
}

/** Equirectangular lon/lat (decimal degrees, WGS84) -> canvas units. */
export function project(lon: number, lat: number): Point {
  return {
    x: ((lon + 180) / 360) * MAP_WIDTH,
    y: ((90 - lat) / 180) * MAP_HEIGHT,
  }
}

export type Box = readonly [x: number, y: number, w: number, h: number]

export const WORLD_BOX: Box = [0, 0, MAP_WIDTH, MAP_HEIGHT]

/**
 * Grow `box` until it contains every point, then pad.
 *
 * This is what stops the country drill-down from cropping outlying sites. The
 * generated per-country bbox frames that country's LARGEST landmass — deliberately,
 * because a bbox spanning every territory zooms the France view out to the Atlantic
 * (see the generator's `_bbox_and_centroid`). The cost of that choice is that a site
 * in an overseas territory would fall outside the default frame, so the frame is
 * widened here to include whatever is actually being drawn. Narrow by default,
 * never cropping in practice.
 */
export function frameFor(box: Box, points: readonly Point[], pad = 12): Box {
  let [minX, minY] = [box[0], box[1]]
  let maxX = box[0] + box[2]
  let maxY = box[1] + box[3]
  for (const p of points) {
    minX = Math.min(minX, p.x)
    minY = Math.min(minY, p.y)
    maxX = Math.max(maxX, p.x)
    maxY = Math.max(maxY, p.y)
  }
  minX -= pad
  minY -= pad
  maxX += pad
  maxY += pad
  // Never let the frame escape the canvas — beyond it there is no map, only
  // background, and a viewBox hanging off the edge reads as a rendering bug.
  minX = Math.max(0, minX)
  minY = Math.max(0, minY)
  maxX = Math.min(MAP_WIDTH, maxX)
  maxY = Math.min(MAP_HEIGHT, maxY)
  return [minX, minY, Math.max(1, maxX - minX), Math.max(1, maxY - minY)]
}

/** `viewBox` attribute text for a box. */
export function viewBox(box: Box): string {
  return `${box[0]} ${box[1]} ${box[2]} ${box[3]}`
}

/**
 * Scale factor a box is magnified by relative to the whole world.
 *
 * Markers are drawn in canvas units, so zooming the viewBox would balloon them:
 * a 6-unit pin in a 40-unit-wide country frame is a blob covering the country.
 * Dividing marker sizes and stroke widths by this keeps them visually constant at
 * every zoom level, which is the behaviour anyone who has used a map expects.
 */
export function zoomOf(box: Box): number {
  return MAP_WIDTH / box[2]
}
