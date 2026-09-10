import type { LoadMapSystem } from './laneBasis'

// WEB23 — the registry systems the BDAT lane basis groups, fetched when that
// basis is chosen and not before.
//
// THE WHOLE FILE IS ONE DYNAMIC IMPORT, and that is the point of it. A static
// import anywhere reachable from /lineage puts web/src/generated/load-map.json
// (139 KB on disk, 79 KB in the bundle) into the entry chunk, which every
// persona downloads before anything renders. WEB7 left it there with a stated
// ACCESS reason — /lineage is open to every role, so the artifact is admissible
// to a user — and that reason is correct. It is not the same question as WHEN it
// arrives. The BDAT basis is one of two lane bases, reached by a picker or a
// ?lanes=layer deep link, so most sessions never ask for it at all.
//
// MEASURED, not assumed (the item's clause a): the entry chunk was 2,506,022
// bytes against a 2,505,000 ceiling — over it — and is 2,426,767 with this
// split, which restores the three-percent margin WEB7 set and the ceiling then
// RATCHETS DOWN rather than being raised. The artifact does not vanish; it
// becomes its own chunk, shared with the two lazy routes that already read it.
//
// IT DOES NOT CACHE, on purpose. The browser caches the chunk, which is the
// layer that should — a module-level promise here would be a second cache with
// no invalidation story, over a file that changes only at a release.

/** The registry systems, fetched on demand. Returns an empty list rather than
 *  throwing if the artifact ever ships without the key: an empty BDAT basis is a
 *  visible finding on the surface, and a thrown error inside a lane picker is
 *  not. */
export async function loadLayerSystems(): Promise<LoadMapSystem[]> {
  const mod = await import('../generated/load-map.json')
  const data = (mod.default ?? mod) as { systems?: LoadMapSystem[] }
  return (data.systems ?? []).slice()
}
