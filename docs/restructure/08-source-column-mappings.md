# 08 — Source column mappings (per-source column ledger: profiled → projected → graph)

**Status: PLANNED — captured 2026-07-07, not started.** Groom to `backlog.yaml`
before building. KISS constraint (plan-07 discipline): one YAML per source, one
typed accessor, test-enforced coverage — everything else deferred until a query
demands it.

## Problem

Every source we ingest is a **wide table we use narrowly**, and the record of
*which columns we use, which we deliberately don't, and why* is scattered:

- `CM_DEF_VJOB` has 100+ columns; the extract projects ~26. The decision lives
  in a SQL header comment (`drydocs/loaders/sql/controlm_jobs.sql`), in doc 06a's
  ER review, and in the `controlm-q1q3-phase1` gate's provenance blocks — three
  places, none machine-checkable, none complete.
- The same principle recurs on every future source. Example: an **HR roster
  table** has dozens of fields; we would use only the subset needed for a
  location / cost-center roll-up mapping (SID, location code, cost center) and
  must *provably exclude* the rest (names, comp — Internal-Confidential).
- The db skills can **profile** a table (full column inventory, types, null %,
  distincts) — but nothing reconciles that inventory against what the loaders
  actually project and what the graph actually stores. Unaccounted columns are
  invisible rather than deliberate.

Target questions the ledger must answer:

- *Which columns of source X do we use, and where does each land in the graph?*
  (source column → staging field → node label.property)
- *Which columns did we deliberately exclude, and why?* (scope choice vs
  sensitivity vs junk — `MEMNAME` is a different "no" than `SALARY`)
- *Did the source or the extract drift?* (profile shows a column the ledger has
  never dispositioned; SQL projects a column the ledger says is unused)

## Prior art / best practice (checked 2026-07-07)

The industry shape for this is the **data contract** / **source-to-target
mapping (STM)**. The current standard is the **Open Data Contract Standard
(ODCS) v3.x** (Bitol, a Linux Foundation project) — YAML, schema section with
per-property definitions; the older Data Contract Specification was deprecated
in favor of ODCS as of 3.1. Python tooling exists (`datacontract-cli`,
`open-data-contract-standard` on PyPI) for lint/test/import/export. Adjacent
patterns: dbt's `schema.yml` (docs live beside the transform), OpenLineage
column-level facets, pandera/pydantic for load-time frame validation, and
sqlglot for extracting projections from SQL.

**Decision: borrow the vocabulary, not the dependency.** ODCS is a
producer↔consumer contract format; our need is an *internal disposition ledger*
integrated with `config/source-registry.yaml`, the HITL gate, and the
classification boundary — the repo's existing idiom (small schema-versioned
YAML + typed accessor + drift tests, like `review-labels.yaml`,
`software-registry.yaml`, `crosswalks/`). We keep field names ODCS-compatible
where free, and an ODCS *export* is a mechanical later step if governance
alignment ever wants it (forward-positioning only — per the audience strategy,
never a current dependency).

**Document vs DataFrame:** the YAML is the source of truth (diffable,
reviewable, gate-transcribable in git). A DataFrame is a *view* the accessor
can emit (`to_records()`), used when joining against a fresh profile — never
the ledger itself.

## Direction (KISS)

One file per registered source: **`config/source-mappings/<source-id>.yaml`**,
schema `drydocs.source-mapping.v1`, where `<source-id>` is the
`config/source-registry.yaml` id — that is the integration key.

```yaml
# config/source-mappings/controlm-psgmgr.yaml  (shape sketch)
schema: drydocs.source-mapping.v1
source: controlm-psgmgr                 # MUST exist in config/source-registry.yaml
classification: Internal-Public         # mechanism-only: column names + rules, no values
objects:
  - name: CM_DEF_VJOB
    kind: view
    profile:                            # provenance of the column census
      profiled_on: 2026-07-07
      via: controlm-db skill            # or: vendor schema doc
      column_count: 104                 # inventory size the coverage test checks against
    columns:
      - {name: JOB_ID,     disposition: projected, target: "ControlMJob.job_id", origin: source}
      - {name: CMD_LINE,   disposition: projected, target: "ControlMJob.cmd_line", origin: source,
         note: "Phase-3 USES_SOFTWARE signal (plan-07)"}
      - {name: MEMNAME,    disposition: projected, target: "ControlMJob.memname", origin: source,
         note: "informational only — DEMOTED, never a key", decided_by: controlm-q1q3-phase1}
      - {name: CREATION_USER, disposition: projected, target: "ControlMJob.source_created_by",
         origin: source, decided_by: controlm-q1q3-phase1,
         derived_also: {target: "ControlMJob.employee_sid", rule: "strip trailing 'p'"}}
      - {name: IS_CURRENT_VERSION, disposition: filter-only,
         note: "WHERE = '1'; domain probe pending (legacy folders)"}
      - {name: DAY_STR,    disposition: excluded, reason: scope,
         note: "schedule detail — surface when a use case demands (SQL header rule)"}
      # ... every profiled column gets exactly one row; a blanket entry is allowed:
    default_disposition: {disposition: excluded, reason: scope,
                          note: "phase-1 inventory+lineage projection (06a)"}
```

Field semantics:

- **`disposition`** — `projected` (lands in staging/graph) | `filter-only`
  (used in WHERE, never projected) | `excluded` (deliberate no; `reason:
  scope | sensitivity | junk | duplicate`) | `deferred` (known future use,
  named phase). One disposition per column; `default_disposition` sweeps the
  long tail so 100+ column files stay writable, while the coverage test still
  forces the *count* to reconcile.
- **`target`** — `Label.property` for graph-bound columns; staging-only
  columns say `staging:<field>`. **`origin: source | derived`** reuses the
  gate-page vocabulary exactly (a `derived_also` block records a second,
  transformed landing like `employee_sid`).
- **`decided_by`** — gate id when a disposition was HITL-gated; the mapping is
  the *cumulative* transcription target, gate provenance blocks remain the
  per-gate view. New sensitivity-relevant dispositions go THROUGH the gate;
  scope-only dispositions batch (routing rules in 03-hitl-sme-flow.md apply).
- **`classification`** — per-file, with the **ccb- twin convention** for
  confidential sources: the HR example ships producer-side as a *shape
  template* (generic column roles: sid / location_code / cost_center
  projected; person-name / comp excluded with `reason: sensitivity`), while
  the real column census lives in the gitignored internal twin. CM_ column
  names are vendor-public mechanism — full census is committable.

## Enforcement (what makes it a ledger, not another doc)

1. **Typed accessor** `drydocs/review/source_mappings.py` (pattern:
   `review_labels.py`) — load/validate; `projected(object)`,
   `unaccounted(profile_columns)`, `to_records()` for the DataFrame view.
2. **Coverage test** — per object: rows + default sweep must account for
   `profile.column_count` exactly; an unaccounted column fails with its name
   (the A2 "every BMC doc accounted for" pattern, applied to columns).
3. **SQL drift guard** — parse each loader's `SELECT ... AS ...` list (house
   style is a single flat SELECT — start with a strict regex, upgrade to
   sqlglot only if the regex ever lies) and assert set-equality with the
   mapping's `projected` columns per object, and that WHERE-referenced columns
   are `projected` or `filter-only`. Catches both drift directions.
4. **Registry integration** — `config/source-registry.yaml` entries gain a
   `mapping:` pointer (like `crosswalk:`/`gate_spec:`); a test requires a
   mapping file for every `confirmed: true` source (same shape as the planned
   `audit-fields.yaml` drift gate in doc 06 — the two ledgers are siblings:
   audit-fields = *envelope* columns, source-mappings = *all* columns; the
   envelope entries cross-reference rather than duplicate).
5. **Profile refresh loop** — the db skill profiles the table → column
   inventory (names/types only, no values) → update `profile:` + disposition
   any new columns. A profile date older than a threshold is a warning, not a
   failure (replicas evolve slowly).

## Phases

- **Phase 0 — schema + accessor + first ledger.** `drydocs.source-mapping.v1`,
  `source_mappings.py` + unit tests, and `controlm-psgmgr.yaml` seeded by
  TRANSCRIBING already-gated decisions (06a §SME resolutions +
  `controlm-q1q3-phase1`: audit envelope, `employee_sid`, MEMNAME demotion,
  `IS_CURRENT_VERSION`/`USER_DAILY` filters, excluded VERSION_* duplicates) +
  the SQL headers' scope rules. No new gate needed — this is transcription;
  the blanket `excluded (scope)` sweep for unprojected columns matches the
  already-accepted phase-1 scope.
- **Phase 1 — drift guards.** Coverage test + SQL parse guard + registry
  `mapping:` pointer with its confirmed-source test.
- **Phase 2 — profile integration.** Run the db-skill profile against
  CM_DEF_VTAB/VJOB/LNK*/SETVAR for the real column census (`column_count`,
  new-column detection); internal-twin flow for the first confidential source
  (HR roster shape template as the worked example).
- **Phase 3 — render + publish.** HTML "mapping sheet" per source
  (gate-page/board rendering pattern; SOURCE/DERIVED badges reused) +
  Confluence publish via the existing pipeline — this is the SME-facing
  source-to-target document.
- **Phase 4 — deferred until a query demands.** Loading mappings into the
  graph as column-level lineage (`(:Column)-[:LANDS_IN]->(:Property)`), ODCS
  export, pandera load-time frame validation.

## Deliberately NOT doing (KISS)

- No ODCS/datacontract-cli dependency now (vocabulary compatibility only).
- No per-column quality rules/expectations (that is a different tool's job;
  revisit with pandera in Phase 4 if load-time validation earns its keep).
- No graph write of the ledger itself until a support question needs it.
- No retro-gating of scope-only exclusions (already covered by the accepted
  phase-1 scope decision); only sensitivity dispositions need the gate.

## Risks / open questions

- **Blanket sweep honesty:** `default_disposition` keeps files short but can
  hide a column someone assumed was reviewed. Mitigation: the profile refresh
  lists NEW columns since last census explicitly — new columns never fall into
  the sweep silently; they must be dispositioned by name.
- **WHERE-clause parsing** (filter-only detection) is fuzzier than SELECT-list
  parsing; acceptable to start SELECT-only and add WHERE coverage when the
  regex→sqlglot upgrade happens.
- **Confidential column names:** for sources where even the column *census* is
  sensitive, the producer file holds only the shape template + counts; the
  coverage test must then run company-side against the twin (same split as
  audit-fields).
