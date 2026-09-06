import type { SpecResult } from '../lib/graph'

// WEB6 — the one runtime check at the spec-result-to-typed-row seam.
//
// THE DEFECT (review 2026-09-05, finding T5): twenty double casts, clustered at
// one boundary — `res.rows as unknown as LocationRow[]`. The DOUBLE cast is
// required precisely because the two types do not overlap; a single cast would
// be rejected. So the compiler was switched off at exactly the point where the
// server's contract meets the render, and a spec that dropped a column produced
// `undefined` in a cell, or a blank panel, or nothing at all — never a sentence
// naming the column.
//
// WHAT THE CALLER DECLARES, AND WHAT IT MUST NOT. TypeScript types are erased,
// so the caller has to name the columns its row type requires; there is no way
// to read them off `LocationRow` at runtime. It does NOT declare their types:
// those come from `result.columns`, which drydocs_api sends with every result
// from its own `ColumnDef` declarations. That is the difference between this and
// a hand-written schema per row type — a second copy of the server's contract is
// exactly what would drift, and clause (a) forbids it.
//
// THREE THINGS THAT WOULD MAKE THIS FAIL ON DAY ONE IF ASSUMED AWAY, each read
// out of the server rather than guessed at:
//
//   1. NULL SATISFIES EVERY DECLARED TYPE. `explorer.jobs.v2` fills
//      `data_center` from an OPTIONAL MATCH and declares it `string`; a job with
//      no server yields null. Rejecting null would fail on real, correct data.
//   2. EPHEMERAL SPECS CARRY NO REAL TYPES. R4 registers an agent's columns as
//      `ColumnDef(name=str(c), type="string")` for every column, whatever it
//      holds — the names are the contract and the types are a placeholder. So an
//      ephemeral result is checked for PRESENCE only. (This is why the seam
//      carries the server's `ephemeral` flag: see graph.ts.)
//   3. TWO SERVER DECLARATIONS ARE WRONG TODAY, and they are named below rather
//      than papered over.
//
// WHAT THIS IS NOT: a general-purpose schema validator. It checks the columns a
// panel says it needs, against the types the server says it sends. Anything more
// is a second contract.

/** The columns a row type requires, by name. `keyof T & string` so a typo is a
 *  compile error rather than a runtime miss — the list is checked against the
 *  type it describes, which is the one part of this a compiler can still do. */
export type RowShape<T> = readonly (keyof T & string)[]

/** Columns whose SERVER declaration does not match what the spec returns.
 *
 * Both return a LIST under `type: "string"`:
 *   runbooks.series.v1        `lands`      = collect(DISTINCT d.assetId)
 *   lineage.schema-definition.v1 `properties` = [k IN keys(d) WHERE ...]
 *
 * Verified by reading the registry, not the render: the Cypher aliases a
 * collect()/comprehension to the name, and `ColumnDef` has no list type to
 * declare. The console already treats `lands` as an array — nvl-mapping's series
 * mapper iterates it — so the DECLARATION is what is wrong, not the data.
 *
 * `drydocs_api/query_specs.py` is the api pen and not this lane's to edit, so
 * these are exempted from the TYPE check (never from the presence check) and
 * handed back in WEB6's close note. The dead-entry test below is what makes the
 * exemption self-retiring: when the server grows a list type, an entry that no
 * longer matches a declared column fails. */
export const DECLARED_TYPE_EXCEPTIONS: Readonly<Record<string, readonly string[]>> = {
  'runbooks.series.v1': ['lands'],
  'lineage.schema-definition.v1': ['properties'],
}

export type ShapeResult<T> = { ok: true; rows: T[] } | { ok: false; message: string }

/** How many rows to type-check. The presence check reads the RESULT's columns
 *  and is O(1); the value check is per row per column, and a 500-row grid times
 *  a dozen columns on every render is a cost with no matching benefit — a spec
 *  that returns the wrong type returns it in row 0 as surely as in row 499.
 *  Stated as a number rather than left implicit so the trade is visible. */
export const TYPE_CHECK_ROWS = 50

function describe(v: unknown): string {
  if (v === null) return 'null'
  if (Array.isArray(v)) return 'array'
  return typeof v
}

/** True when `value` satisfies the server's declared type for that column.
 *  Null always satisfies (see note 1 above). An unrecognised declared type
 *  passes: the vocabulary is the server's, and a console that rejected a type it
 *  had not heard of would break on the next one drydocs_api adds. */
function satisfies(value: unknown, declared: string): boolean {
  if (value === null || value === undefined) return true
  if (declared === 'string') return typeof value === 'string'
  if (declared === 'int') return typeof value === 'number' && !Number.isNaN(value)
  return true
}

/**
 * Check a spec result against the columns a row type requires.
 *
 * Returns the rows AS the row type, or a message naming the spec, the column,
 * the row index and what was expected versus what arrived. The single cast in
 * the success branch is the one the whole item is about: it is reached only
 * after the columns have actually been checked, so it asserts something that
 * has just been established rather than something nobody looked at.
 */
/** What a row source has to tell the check about itself. */
export interface RowSource {
  /** Named in every message — the reader's first question is "which query". */
  source: string
  keys: readonly string[]
  rows: readonly Record<string, unknown>[]
  /** Column name to server-declared type. Empty for a source that declares no
   *  types (the O13 mappings grid returns keys and rows and nothing else), in
   *  which case the check is presence only — which is still the check that
   *  catches a renamed or dropped column. */
  types?: ReadonlyMap<string, string>
  /** Column names exempt from the TYPE check, never from the presence check. */
  exempt?: ReadonlySet<string>
}

/** The core check, over any keys-and-rows source. */
export function validateRowsOf<T>(src: RowSource, required: RowShape<T>): ShapeResult<T> {
  const types = src.types ?? new Map<string, string>()
  const present = new Set<string>([...src.keys, ...types.keys()])

  const missing = required.filter((name) => !present.has(name))
  if (missing.length > 0) {
    return {
      ok: false,
      message:
        `${src.source} did not return ${missing.length === 1 ? 'the column' : 'the columns'} ` +
        `${missing.map((m) => `'${m}'`).join(', ')} that this panel requires. ` +
        `It returned: ${src.keys.join(', ') || '(no columns)'}.`,
    }
  }

  const exempt = src.exempt ?? new Set<string>()
  const limit = Math.min(src.rows.length, TYPE_CHECK_ROWS)
  for (let i = 0; i < limit; i++) {
    const row = src.rows[i]
    for (const name of required) {
      const type = types.get(name)
      if (type === undefined || exempt.has(name)) continue
      if (!satisfies(row[name], type)) {
        return {
          ok: false,
          message:
            `${src.source} column '${name}' is declared ${type}, ` +
            `but row ${i} carries ${describe(row[name])}. ` +
            `The server's contract and this panel disagree; nothing is rendered rather than a row that is not the row.`,
        }
      }
    }
  }

  return { ok: true, rows: src.rows as T[] }
}

/** The QuerySpec case: types come from the result's own column declarations. */
export function validateRows<T>(result: SpecResult, required: RowShape<T>): ShapeResult<T> {
  return validateRowsOf<T>(
    {
      source: `QuerySpec ${result.spec_id}`,
      keys: result.keys,
      rows: result.rows,
      // Presence only for an ephemeral spec — its declared types are
      // placeholders (note 2). The names still had to be there, which is the
      // check that matters for an agent-registered query.
      types: result.ephemeral ? undefined : new Map(result.columns.map((c) => [c.name, c.type])),
      exempt: new Set(DECLARED_TYPE_EXCEPTIONS[result.spec_id] ?? []),
    },
    required,
  )
}
