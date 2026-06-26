# ADR 0002-A — `drydocs-core` extraction plan (thin)

```yaml
status: PLANNED         # PLANNED | IN_PROGRESS | DONE
date: 2026-06-26
companion_to: docs/decisions/0002-component-database-topology.md   # ADR 0002, D3
gated_by: ADR 0002 PROPOSED → ACCEPTED        # no file moves until accepted
principle: CLAUDE.md §3 (publish boundary), §4 (config precedence)
```

> Realizes ADR 0002 follow-up #2. **Thin = define the boundary and move with zero behavior
> change; do not redesign.** The seam is "shared transformation vs. component logic," matching
> the dependency rule: *components depend only on `core`, never on each other.*

---

## 1. Goal / non-goal

- **Goal:** carve a `drydocs-core` package out of today's `drydocs/` that holds the shared
  models, adapters, driver, config layer, ontology vocab, and the **Control-M command-line /
  lineage parser** — the code C2 (`drydocs-lineage`) and C3 (`drydocs-deepdoc`) both need and
  the rebased spinoff (`drydocs-remediation`) re-homes onto.
- **Non-goal (this step):** no new features, no DB provisioning, no Jira wiring, no behavior
  change. Loaders keep working against `drydocs` exactly as today. Splitting C2/C3/remediation
  packages is a *later* follow-up; this plan only produces `core` + leaves the rest as
  `drydocs-load`.

## 2. Module disposition (every current module)

Grounded in the present tree. Rule of thumb: **pure parse/resolve/typed-model/driver/config →
core; anything that writes the graph or owns a run cadence → a component.**

| Current module | → Home | Why |
|---|---|---|
| `models/` (catalog, controlm, seal) | **core** | Typed rows/entities; pure data shapes. |
| `adapters/` (base, csv, oracle) | **core** | Source adapters; transformation, no graph write. |
| `neo4j_client.py` | **core** | Driver/session lifecycle. Components pass their own DB name. |
| `config.py`, `precedence.py`, `source_registry.py` | **core** | The declarative config layer (CLAUDE.md §4). |
| `ontology/namespaces.py` | **core** | URN/namespace vocab; shared identity. |
| `controlm/commands.py` | **core** | **The shared command-line parser** — the literal overlap C2/C3 wrap. |
| `controlm/{facts,folder_name,paths,resolver,variables}.py` | **core** | Pure Control-M parse/resolve (Phase A/B). |
| `controlm/variable_report.py` | **core** (utility) | Reporting over parsed facts; no graph write. |
| `controlm/staging.py` | **load** (borderline — see §6) | Builds the staging bundle *for the loaders*; load-cadence-coupled. |
| `loaders/**` (controlm*, seal*, catalog, business_segments, base) | **load** | Write `drydocs`; main-load cadence. |
| `snapshots/writer.py` | **load** (borderline — see §6) | Hash-snapshot **writes to the graph**; runs in the load pipeline. |
| `cli.py` | **split** | Bootstrap/ingest/refresh commands → `load`; core exposes no CLI of its own yet. |
| `schema/*.cypher`, `ontology/*.cypher` | **core** (resources) | Ground-truth DDL/seed; shared, read by load + provisioning. |

## 3. `drydocs-core` public API (the seams components import)

Keep the surface small and explicit — this *is* the modular seam (ADR 0002, Consequences:
"clear public API, no component→component imports").

- `drydocs_core.models` — `ControlMVariableRow`, catalog/seal entities.
- `drydocs_core.adapters` — `CsvAdapter`, `OracleAdapter`, `BaseAdapter`.
- `drydocs_core.controlm` — `resolve_job`, `classify_job_variables`, `VariableCoverage`,
  `Invocation`, `FileOp`, `extract_container_command` (the parser surface in
  `controlm/__init__.py` today).
- `drydocs_core.neo4j` — `Neo4jClient(database=...)` (caller supplies `drydocs` |
  `drydocs_context`).
- `drydocs_core.config` — `load_settings`, precedence resolver, source registry.
- `drydocs_core.urn` / `drydocs_core.ontology` — namespace + URN builders.

Everything not in this list stays component-private.

## 4. Import rule + enforcement

- **Rule:** `core` imports nothing from any component; components import only `drydocs_core.*`,
  never each other.
- **Enforcement (test, in `tests/unit/`):** a `test_module_boundary.py` that walks
  `core/`'s AST imports and asserts none resolve to `drydocs_load`/`drydocs_lineage`/
  `drydocs_deepdoc`/`drydocs_remediation`; and that no component imports another component.
  This is the structural guard that keeps the seam from eroding.

## 5. Packaging mechanics (monorepo)

- One repo, multiple Poetry packages; `core` is a **path dependency** of each component
  (`drydocs-core = { path = "../core", develop = true }`). No publish step needed for a
  single-team monorepo.
- Preserve `drydocs` as the installed console script during transition: the `drydocs` CLI
  becomes `drydocs-load`'s entry point; `core` ships no script.
- **Sensitivity:** the move touches only code, not data — `internal/` and `drydocs/data/`
  stay put and gitignored (CLAUDE.md §3). No classification labels change.

## 6. Sequenced, test-gated steps (small + reversible)

Each step ends green on the existing gates: `poetry run pytest -q`,
`python -c "import drydocs.cli"`, `drydocs --help` (per CLAUDE.md §6).

1. Introduce `core/` package skeleton + `pyproject`; **re-export** from it while files
   physically still live in `drydocs/` (shim) — zero risk.
2. Move the unambiguous core modules (§2 rows marked core) into `core/`; update imports; run
   gates.
3. Resolve the two borderline modules (§6 decisions below); run gates.
4. Rename the remainder to `drydocs-load`; point the `drydocs` script at it; run gates.
5. Add `test_module_boundary.py`; run gates. **Stop here** — C2/C3 packaging is a separate
   follow-up (Phase C). The `drydocs-remediation` rebase is **planned in 0002-b** and executed in a
   separate module/effort (depends on this extraction being DONE).

**Borderline decisions (flagged, not silently chosen):**
- `controlm/staging.py` → **load.** It assembles the loader bundle; C2/C3 build their own
  staging from the core parser, so it isn't shared. Revisit only if a second consumer appears.
- `snapshots/writer.py` → **load.** It writes the graph, which the dependency rule reserves to
  components. If `deepdoc` later needs snapshotting into `drydocs_context`, extract the *pure
  hashing* into core and leave the *write* in each component.

## 7. Risks

- **Over-extraction:** pulling load-only helpers into core to "share early" recreates the
  tangle. Mitigation: §2 table + the boundary test; when unsure, leave it in `load`.
- **CLI churn:** the bootstrap/ingest commands are load's; don't scatter them. Keep one CLI in
  `load` until a component genuinely needs its own.
- **Resource files:** `schema/*.cypher` must ship inside the `core` package data so loaders and
  provisioning both find them after the move.

## 8. Done criteria

`drydocs-core` imports cleanly with no component dependency; `drydocs-load` runs the existing
pipeline unchanged; the boundary test passes; gates green. Then proceed to **Phase C** —
scaffolding `drydocs-lineage` and `drydocs-deepdoc` on core. (`drydocs-remediation` rebase is
planned in 0002-b, executed in a separate module/effort.)
