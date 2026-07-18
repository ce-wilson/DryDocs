# Mapping-store plan — relational taxonomy↔ontology mapping (SQLite)

> Saved 2026-07-17 from chat research ("lightweight SQL db that works well with React and
> agents"). Status: **BUILT 2026-07-18 on `feat/mapping-store` — M0 through M4 plus the
> wf-mapping-01 live demo (`/demo` on drydocs-api).** Deltas from plan: the store and the
> pure manual-CSV validation moved to `drydocs_core/` (mapping_store.py, manual_mappings.py)
> because BOTH the load and api components consume them and components never import each
> other (MODULE_MAP boundary); M3's flip is the `mapping_rows()` default (`DRYDOCS_MAPPING_READ=yaml`
> is the fallback); M2's submit is the artifact-download shape (no server-side git — resolves
> the O13 open item conservatively). No new HITL gates: changesets travel the existing
> K2-gated config/manual-loads/ mechanism; grid rows enter/leave via the committed sources only.
> Classification: internal-public (mechanism only, no company data).
>
> **Prime directive: do not break the current working model.** YAML/CSV in git stays the
> source of truth and the HITL gate keeps reviewing text diffs at every phase. The SQLite
> file is always a *derived, rebuildable materialization* — never the thing the gate reviews,
> and deletable at any moment without data loss.

## 1. The decision

| Question | Call |
|---|---|
| Engine | **SQLite** (WAL mode), server-side, accessed only via `drydocs-api` (ADR 0005 thin API — React never touches the DB) |
| Analytics companion | **DuckDB** — reads the same `.db` via its sqlite extension; pandas/Polars/Parquet native; never the store of record (single-writer) |
| Source of truth | **Committed per-table CSV dumps in git** — the gate reviews CSV diffs exactly as it reviews YAML today; DB ⇄ CSV round-trip is deterministic |
| Agent access | Agents **query** (text-to-SQL; MCP: DBHub / sqlite servers), never read wide grids — narrow tall tables + views solve the "agents don't read column data well" problem |
| Rejected | PGlite / DuckDB-WASM (client-side fights ADR 0005); full Postgres (wrong weight now) |
| Escape hatch | libSQL/Turso or Postgres later if multi-user SaaS — the schema below is portable as-is |

## 2. The core table — the mapping quintuple

One row per proposed/confirmed graph loading rule (this is `config/taxonomy-ontology-map.yaml`
relationalized; it is also the row shape the O13 mapping screen drafts):

```sql
CREATE TABLE mapping (
  id                INTEGER PRIMARY KEY,
  source_label      TEXT NOT NULL,   -- e.g. ControlMJob
  source_property   TEXT NOT NULL,   -- e.g. (folder_id, job_id) key expr
  relationship_type TEXT NOT NULL,   -- from relationship_vocabulary.yaml ONLY
  target_label      TEXT NOT NULL,   -- e.g. BusinessApplication
  target_property   TEXT NOT NULL,   -- e.g. seal_id
  status            TEXT NOT NULL CHECK (status IN ('proposed','planned','confirmed','retired')),
  rationale         TEXT NOT NULL,   -- provenance; REQUIRED (gate context)
  gate_ref          TEXT,            -- HITL gate session/decision reference
  author            TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);
```

Ontology guardrails unchanged: `relationship_type` must exist in
`relationship_vocabulary.yaml`; new types still route through `docs/RELATIONSHIP_GUIDE.md`
+ the HITL gate; rows enter as `proposed`, never `confirmed`, from any UI or agent.

## 3. Phases (each phase leaves the current model fully working)

- **Phase M0 — derive, consume nothing.** `scripts/build_mapping_db.py` builds
  `mapping.db` read-only from the existing YAML/CSV (taxonomy-ontology-map,
  relationship_vocabulary, manual-loads). Nothing reads it. Acceptance: build is
  deterministic; round-trip dump equals source; unit test guards drift.
- **M1 — dual-read behind a flag.** Reconcilers/loaders gain an optional SQLite read
  path (default OFF, YAML remains default). Acceptance: parity test — YAML-derived and
  DB-derived mapping sets are identical.
- **M2 — API + UI read path.** `drydocs-api` mapping endpoints serve the O13 screen
  (dropdowns = SELECT DISTINCT against reference tables). Writes UNCHANGED: still CSV
  change artifacts → git → gate → merge; DB rebuilt post-merge (M0 script in CI/ritual).
- **M3 — flip the read default.** DB becomes the materialization of record for *reads*;
  committed CSV dumps remain the gate-reviewed truth. Retire YAML per-table only after
  parity has held; keep the dump-back path so diffs never disappear.
- **M4 (later, optional).** DuckDB analytics views (coverage %, conflict queues);
  agent MCP access (read-only, allow-listed); libSQL/Postgres only on a real
  multi-user need.

## 4. Branch model

**Feature branch, not a fork.** Per CLAUDE.md §0 this is exactly the "multi-commit epic
slice / structural change" case: `feat/mapping-store` → `--no-ff` merge → delete. A fork
is not part of this repo's model at all — the only two-repo split is the producer→company
port, which is a cherry-pick relationship, not a fork of this work. M0 alone (one script +
one test, zero consumers) could land as small main commits, but M0–M3 as a reviewable
unit belongs on the branch.

## 5. Context / drivers

- Internal team adopting **DataHub** for the catalog — overlaps some ingested metadata;
  its relational-DB-alongside-graph architecture validates this split (graph = meaning,
  relational = mappings/records). Future: "publish to DataHub" QuerySpec export target
  now has a named internal customer.
- **ETL-tooling inventory** is a gap no catalog covers (they inventory data assets, not
  the tooling estate) — candidate DryDocs domain; groom separately.
- Research trail: IDEAS.md inbox 2026-07-17 entries ("Relational mapping store research",
  "SaaS knowledge-graph scaffold research"); chat sources incl. MotherDuck/Kestra/PostHog
  embedded-DB comparisons, DBHub MCP, DataHub storage-layer docs.

## 6. Next actions (when groomed)

Groom M0–M3 into `backlog.yaml` as a new epic (module: config or drydocs-api per item;
M0 has no dependencies and is startable now). O13's acceptance gains "dropdowns read
mapping.db via drydocs-api" once M2 exists.
