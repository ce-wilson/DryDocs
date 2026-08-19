# Technical Design — the mapping-store SQLite materialization (`var/mapping.db`)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — documents the built store as of **Rev 1, 2026-07-22**, authored
at commit `22d1a39` (plan M0–M4 built; O24 override table landed `b241661`, 2026-07-21). ·
**Classification:** Internal-Public — mechanism only; every SID, role holder, and mapping
row named here is SYNTHESIZED or empty; real values live company-side under `internal/`. ·
**Audience:** engineers touching `drydocs_core/mapping_store.py`, `drydocs_api/mappings.py`,
or the analytics path; the SME reviewing why the UI can query mappings without the YAML
ever ceasing to be the truth. ·
**Companion:** `knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md` (the M0–M4 plan);
`docs/design/drydocs-web-console-tdd.md` (the console that consumes it);
`docs/design/drydocs-mapping-store-runbook.md` (operate it);
`docs/design/drydocs-mapping-demo-runbook.md` (the `/demo` page it backs).

Worked example throughout: an SME edits a fragment in `config/taxonomy-ontology-map/` (the S5 fragment directory), flipping one
entry from `proposed` to `rejected`. Nothing rebuilds the store explicitly — the next
`/mappings` request notices the source-hash drift (`is_current()` → False), rebuilds
`var/mapping.db` in place, and `v_status_summary` answers `applied 8 · confirmed 22 ·
proposed 2 · rejected 1`. The YAML was the decision; the SQLite file just caught up.

> **Read-me-first.** The store is a *derived, rebuildable materialization* — deletable at
> any moment without data loss, never the artifact a gate reviews. The committed YAML/CSV
> in git remain the single source of truth. Every anomaly in the file means "rebuild",
> never "investigate"; every consumer treats `is_current() == False` as exactly that.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Specify the SQLite materialization of the mapping layer: what it ingests,
the tables and views it exposes, the determinism and staleness contracts, and the three
consumer paths (API/UI, loader read seam, analytics) that query it instead of parsing YAML.

**In scope.**
- `drydocs_core/mapping_store.py` — DDL, build, staleness (`source_hashes`/`is_current`),
  deterministic CSV dumps, the M1/M3 read seam.
- `scripts/build_mapping_db.py` and `scripts/mapping_analytics.py` — the CLI entry points.
- The consumption contract of `drydocs_api/mappings.py` (the O14 rebuild-on-read guard).

**Out of scope** (delegated): the mapping-stewardship UI itself and the changeset-artifact
flow (`drydocs-web-console-tdd.md`); the tier-5 manual loader that writes the graph
(`config/manual-loads/README.md` + K2 gate); the FID/ALIAS reconciler tables (planned,
not built — their domains render greyed-out in `/demo`); Oracle/Neo4j entirely — this
store touches neither.

<!-- anchor: context-frame -->
## Where this sits — the four-layer frame

The store is **layer-2 support machinery**: it materializes the *ontology* decision
ledgers (the taxonomy→ontology map, the relationship vocabulary, the manual mapping
assertions) into a queryable form. It holds no layer-3 knowledge-graph content and never
writes the graph — the loader remains the only graph writer, and the store's own writes
are confined to the derived file under `var/`.

Upstream: the committed config ledgers (`config/taxonomy-ontology-map/`,
`drydocs_core/ontology/relationship_vocabulary/` — both fragment directories since S5, `config/manual-loads/`,
`config/overrides/seal-contact-overrides.csv`). Downstream: `drydocs_api` `/mappings/*`
(the O13 stewardship surface and O24 override grid), the tier-5 loader's read seam, and
the M4 DuckDB analytics path. It lives in `drydocs_core` because both the load component
and the api component consume it, and components never import each other (the MODULE_MAP
boundary).

<!-- anchor: definitions -->
## Definitions, acronyms & references

- **Materialization** — a derived database built entirely from committed sources; the
  inverse of a system of record. Deleting it loses nothing.
- **The quintuple** — one `ontology_mapping` row: (source label, relationship type, role,
  target label, PROV term) plus the HITL lifecycle (`proposed → confirmed → applied`,
  or `rejected`).
- **M0–M4** — the plan phases (`knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md`):
  M0 build, M1/M3 loader read seam, M2 origin-flagged override store, M4 analytics views.
- **O13 / O14 / O24** — Epic O items: the `/mappings` API surface; the staleness guard
  (rebuild-on-read); the SEAL-contact override table (ui-write-surface gate SME-3).
- **K2** — gate `seal-attribution-match-policy` (signed off 24/24, 2026-07-14), governing
  the manual-loads tier the store ingests.
- **Origin flag** — the O24 rule that a SEAL source value and its user override render as
  adjacent rows (`origin: source` / `origin: override`), never merged.

<!-- anchor: design-summary -->
## Design summary

```
committed sources (git = truth)                 var/mapping.db (derived)
────────────────────────────────                ─────────────────────────
config/taxonomy-ontology-map/ ────┐           7 tables + 7 views
ontology/relationship_vocabulary ───┤  build()  ┌──────────────────────┐
config/manual-loads/ (manifest+CSV) ├─────────► │ meta (source hashes) │
config/overrides/seal-contact-…csv ─┘           └──────────┬───────────┘
                                                 is_current() compares
consumers (all read-only):                       hashes → False = rebuild
  drydocs_api /mappings/*  (O14 rebuild-on-read)
  drydocs.loaders read seam (M1/M3 parity)
  DuckDB / sqlite3 analytics (M4 views)
  dump_csv() → gate-reviewable text twin
```

`build()` replaces the file wholesale from the four committed sources, stamping `meta`
with the schema version and a sha256 per source. `is_current()` recomputes those hashes
and compares — one dict equality is the entire staleness protocol. Consumers open the
file read-only (`mode=ro`); the only writer is `build()` itself.

<!-- anchor: detailed-design -->
## Detailed design

**Build.** `build(db_path)` deletes any existing file (it is derived), creates the schema
from a single DDL script, then ingests the four sources in fixed order: vocabulary →
ontology map → manual loads → SEAL overrides. Insertion order is file order (`seq`,
`line_no`), so identical sources always produce identical row order.

**Validation is the loader's, reused.** Manual CSVs pass through `parse_mapping_csv` —
the *same* chain the tier-5 loader uses (manifest registration gate, vocabulary check,
supported shape) — so the store can never accept a row the loader would refuse. Override
rows fail loudly per row at build time: the role must canonicalize to the SEAL role
vocabulary, `rationale` and `authored_by` are required, `status` is enum-checked, and an
override equal to the captured SEAL value is refused (it is not a correction). A bad row
is a mistake to fix at the committed source, never something to guess around.

**Staleness (O14).** `source_hashes()` computes the meta rows a build *would* store —
including per-CSV hashes for every loadable manifest entry, so an added or removed file
counts as drift. `is_current()` returns False for a missing, unreadable, foreign, or
drifted file; `drydocs_api`'s connection helper calls `build()` whenever it does, which
is why config edits are picked up on the next request without a restart.

**Determinism.** No wall-clock values are stored (meta carries content hashes, not
timestamps); `dump_csv()` writes one CSV per table ordered by primary key with `\n`
terminators. Byte-identical dumps for identical sources is an asserted invariant, and
the dumps are the gate-reviewable text twin of the binary file.

**The M1/M3 read seam.** `manual_mapping_rows_from_store()` builds an in-memory store
and reads one registered CSV back across the SQL boundary as `ManualMappingRow` objects.
Validation is identical to the legacy path by construction; what the seam adds is the
DB round-trip, guarded by the parity test.

**Views (the query surface).** `v_mapping_quintuple` and `v_status_summary` serve the
lifecycle; `v_vocab_active` / `v_label_options` serve the vocabulary pickers;
`v_manual_conflicts` is the steward conflict queue (same job key → more than one SEAL);
`v_seal_contact_grid` implements the origin flag (source row first, override adjacent,
never merged); `v_source_corrections` feeds the AO-facing corrections report
(outstanding `active` rows only). DuckDB reads the same views through its sqlite
extension — one store, two engines, identical answers.

<!-- anchor: design-data-mapping -->
### Source → column-level field mapping

| Source (committed) | Table | Column handling |
|---|---|---|
| `taxonomy-ontology-map/` fragments' `mappings[]` | `ontology_mapping` | `id`; `seq` = file order; `taxonomy.source/element`; `ontology.from_node/to_node/neo4j_label/role/prov_maps_to/matrix_row`; `precedence_authority`; `vocab_id`; `status` (CHECK enum) + `confirmed_by/on`, `applied_on`. Nullable columns mirror the YAML's reality (property supplements have no target, infrastructure edges no PROV term). |
| `relationship_vocabulary/` fragments' `local_relationships[]` | `relationship_vocabulary` | `id`, `neo4j_label`, `role`, `from_node`, `to_node`, `prov_maps_to`, `sosa_maps_to`, `domain`, `status`, `note` — verbatim. |
| `relationship_vocabulary/` fragments' `node_classifications[]` | `node_classification` | `label` (PK), `class`, `prov_type`, `note`. |
| `manual-loads/manifest.yaml` `files[]` | `manual_load_file` | every entry registered (audit); only `pending-load`/`loaded` materialize rows. |
| each loadable manual CSV | `manual_mapping` | via `parse_mapping_csv`: `folder_id`, `job_id`, `seal_id`, `create_target_if_missing` (0/1), `authored_by/on`, `note`; PK `(file, line_no)`, FK → `manual_load_file`. |
| `overrides/seal-contact-overrides.csv` | `seal_contact_override` | `line_no` (PK), `app_seal_id`, `role_name` (canonicalized), `seal_holder_sid` (captured source value), `override_holder_sid/name`, `rationale`, `authored_by/on`, `status` (CHECK enum). |
| (computed) | `meta` | `schema_version` = `drydocs.mapping-store.v1`; one `source:<path>` = sha256 row per source file. |

<!-- anchor: classification-security -->
## Classification & security

Internal-Public, mechanism only. The producer-side sources are synthesized or empty
(the overrides CSV is header-only; the manifest registers no files); real SIDs, SEAL
ids, and rosters exist only company-side under `internal/`. `var/` is gitignored, so
the binary DB — which company-side *would* contain Internal-Confidential values once
sources are populated — can never be committed by construction. No secrets: the store
holds no credentials and connects to nothing. The enforcement matrix carries the
`config/overrides/` surface row (guard tests `test_mapping_store.py`,
`test_mapping_api.py`) per `scripts/render_enforcement_matrix.py`.

<!-- anchor: qa-tests -->
## QA & tests

- `tests/unit/test_mapping_store.py` — the parity test (legacy YAML path vs the SQL
  round-trip, row-for-row), determinism (byte-identical dumps), staleness semantics,
  and per-row override validation failures.
- `tests/unit/test_mapping_api.py` — the `/mappings/*` handlers over a fixture store,
  including the O24 origin-flagged grid and drafted-artifact (no-write) contract.
- `tests/unit/test_manual_loads.py` — the shared validation chain the store reuses.
- Graph verify (m1/m3-verify) does not apply: the store never writes the graph.

<!-- anchor: hitl-gate -->
## HITL gate & open questions

The store itself is deliberately **not** a gated artifact — gates review the committed
sources it derives from. The governing gates are upstream: K2
`seal-attribution-match-policy` (24/24, 2026-07-14) for the manual-loads tier, and
`ui-write-surface` SME-3 (O20, signed off 2026-07-21) for the O24 override store, whose
M2 follow-up built `seal_contact_override`. Open: the FID/ALIAS reconciler tables
(domains exist in the API registry, tables unbuilt — company-side K2 tiers unblock);
whether the deterministic CSV dumps get adopted as the gate-reviewable artifact of
record (plan M-open; today gates read the YAML/CSV sources directly).

<!-- anchor: traceability-matrix -->
## Requirements traceability matrix

| Requirement / capability | Design section | Component | Test / verify | Status |
|---|---|---|---|---|
| Committed YAML/CSV remain truth; DB derived + rebuildable | purpose-scope | `mapping_store.build` | `test_mapping_store.py` (rebuild replaces file) | built |
| Byte-deterministic builds and dumps | detailed-design | `dump_csv`, `_DUMP_ORDER` | `test_mapping_store.py` determinism assert | built |
| Staleness = one hash comparison; drift → rebuild | detailed-design | `source_hashes` / `is_current` | `test_mapping_store.py`; O14 guard in `test_mapping_api.py` | built |
| Store can never accept a row the loader refuses | detailed-design | `parse_mapping_csv` reuse | `test_manual_loads.py` + parity test | built |
| M1/M3 read seam serves loader rows across SQL boundary | detailed-design | `manual_mapping_rows_from_store` | parity test in `test_mapping_store.py` | built |
| O24 origin flag: source + override adjacent, never merged | design-data-mapping | `v_seal_contact_grid` | `test_mapping_api.py` grid assertions | built |
| Override ≠ captured SEAL value, rationale required | detailed-design | `_ingest_seal_overrides` | `test_mapping_store.py` validation cases | built |
| No graph writes anywhere in the store/API path | context-frame | `drydocs_api/mappings.py` | `test_mapping_api.py` artifact-only contract | built |
| FID/ALIAS reconciler tables | hitl-gate | (planned) | n/a — domains greyed out in `/demo` | planned |

<!-- anchor: decisions-discussions -->
## Decisions & discussions

Placement in `drydocs_core` (not `drydocs.loaders` or `drydocs_api`) follows the
MODULE_MAP no-cross-import rule — both components consume it, so it sits below both.
DuckDB was chosen as the analytics engine *over* adding a second store: it attaches the
same SQLite file, so analytics can never drift from the API's answers. Timestamps were
deliberately excluded from `meta` in favour of content hashes to keep builds
byte-deterministic (the same decision pattern as the board/design renders).

<!-- anchor: appendices -->
## Appendices

Current producer-side row counts (rebuilt 2026-07-22, all sources committed):
`ontology_mapping` 33 · `relationship_vocabulary` 75 · `node_classification` 52 ·
`manual_load_file` 0 · `manual_mapping` 0 · `seal_contact_override` 0 · `meta` 5.
Lifecycle: applied 8, confirmed 22, proposed 2, rejected 1. Empty tables are faithful:
the manifest registers no files and the overrides CSV is header-only.
