---
standard: composite-key-serialization
domain: technology
taxonomy_path: technology/orchestration/control-m/identity
governs: serialized composite identities (ctlm_id) + key-cell pair grammar
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: active
trust_tier: internal / SME-asserted / mutable
---

# Internal Standard — Composite-Key Serialization (ctlm_id + key-cell grammar)

**Corpus:** INTERNAL (company-specific standard) — *not* vendor documentation.
**Authority:** SME ruling 2026-08-03 (in-chat, this repo's session log); the
composite value form was first signed at the P2 avg-run gate §B join upgrade
(`config/gate-log.md`, 2026-07-14).

Two rules, one page, because they answer the same question — *how does a
multi-part identity travel as one string?* — at two different grains.

## Rule 1 — the composite VALUE joins with a DOT: `ctlm_id = folder_id.job_id`

Wherever the `(folder_id, job_id)` ControlMJob node key is rendered as a
single string, the form is the psgmgr-derived **`ctlm_id`** composite:
`folder_id.job_id` (synthetic example: `1015.7`). Split on `.` recovers the
node key exactly.

- **Precedent:** the internal psgmgr schema derives this column
  (`TABLE_ID || '.' || JOB_ID`); the P2 gate (§B, 2026-07-14) made it the
  preferred join for the avg-run supplement.
- **Live conforming surfaces:**
  `drydocs/loaders/sql/controlm_dependencies_recursive.sql` (both
  endpoints), `drydocs_core/models/controlm.py` dependency rows
  (`'<folder_id>.<job_id>' (ctlm_id form)`),
  `drydocs/loaders/controlm_dependencies_derived.py`, the deferred
  dependency pass in `drydocs/cli.py`.
- **Do not invent sibling forms.** A colon, pipe, or underscore join of the
  same pair mints a second identity grammar; any surface that needs the
  pair as one string uses ctlm_id. (The K14 sweep, 2026-08-04, converted
  the two known strays — the web mapping tray's colon-joined React list
  key and the static mapping demo's slash join — and found no others
  across web/src, drydocs_api and drydocs/loaders.)
- **Caveat that stays true:** not every CM_ table carries the derived
  column (CM_AVG_RUN does not — P0 probe); absence means fallback join,
  never a different serialization.

## Rule 2 — key-cell PAIRS join with a COLON: `field=value:field=value`

The manual-loads template's `source_key`/`target_key`/`rel_props` cells (and
any future cell that carries labeled key pairs) join `field=value` pairs
with **`:`** — **never `;`**.

- **Why not `;` (the SME's stated reason):** the semicolon is the SQL
  statement terminator, and these cells travel beside SQL extracts and
  Cypher all day; a separator that doubles as a terminator invites paste
  and quoting accidents.
- **Why labeled pairs at all (vs a bare positional composite):** `k=v` is
  self-describing and order-independent across node labels whose key
  shapes differ — `ControlMJob` is two-part where `Port` is not.
- **Compatibility by construction:** key values are identifiers and never
  contain `:`; the Rule-1 dot composite nests cleanly as a value
  (`ctlm_id=1015.7`).
- **Parser:** `drydocs_core/manual_mappings.py::_parse_key` enforces this
  grammar for both the tier-5 loader and the mapping-store
  materialization. Changed from `;` to `:` on 2026-08-03 while ZERO manual
  CSVs were committed (`config/manual-loads/manifest.yaml` `files: []`),
  so no data migrated; from the first committed CSV onward the grammar is
  pinned.

## What this standard does NOT govern

- The registry dataset grammar `origin@db.schema.table`
  (`config/source-registry.yaml`) — its own ruled grammar, N7 gate.
- SQL inside adhoc profiling scripts (e.g. `'|'`-joined DISTINCT probes) —
  throwaway diagnostics, not serialized identities.
- Which FIELDS key a row — that is per-gate (the K7 rekey moved manual
  authoring to `app_code=`); this page rules only how parts join.
