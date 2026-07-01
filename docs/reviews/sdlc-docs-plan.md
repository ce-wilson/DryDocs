# DryDocs — SDLC Documentation Session Plan

> **STATUS: Superseded (2026-07-01).** This review/plan is complete; its findings were rolled
> into `docs/decisions/` (ADRs), `MODULE_MAP.md`, and `docs/restructure/backlog.yaml`.
> Kept for historical reference.

Resumable, persona-driven maintenance of living SDLC documents for the two primary
DryDocs flows: **Oracle Ingestion** and **Neo4j Schema Meta**.

Documents are machine-first (structured for model consumption); human-readable
derivations are produced later from these sources. Every section carries stable
IDs and status fields so the model can update individual items without rewriting
the whole file.

---

## EXECUTION PROTOCOL — read this first, every run

1. Read `docs/reviews/SDLC-CHECKPOINT.md`. If `status: COMPLETE` → stop.
2. Append one line to its `## Run log`: `- <ISO timestamp> wake`.
3. Determine `current_phase` / `current_task` / `next_action`.
4. Load persona skill(s) for the current phase (see below).
5. Do the **smallest next unit of work** and write/append to the target doc.
6. **Rewrite SDLC-CHECKPOINT.md** (status, phase, task, next_action, last_updated,
   +1 log line) **before doing more work**.
7. Repeat 5–6 until budget runs out or plan is COMPLETE.

**Secrets discipline:** architecture-level only; no real SIDs, data values,
credentials, emails, or org names. Schema object names (already in repo) are fine.

**Update vs. append:** most tasks UPDATE a section in-place by reading the current
file and rewriting the target section. Only `§LOG` (change log) is append-only.

---

## Output files (one per persona)

| File | Persona | Flow |
|---|---|---|
| `docs/reviews/sdlc-oracle-ingestion.md` | Oracle DBA (`db` skill) | Oracle Ingestion |
| `docs/reviews/sdlc-neo4j-schema.md` | Neo4j Architect (`neo4j-*` skills) | Neo4j Schema Meta |

---

## Phase 1 — Oracle DBA (skill: `db`)

Target: `docs/reviews/sdlc-oracle-ingestion.md`

Tasks (each a checkpointable unit):

- **1.1 §C1 — Context diagram.** Generate the Mermaid C1 flowchart showing
  PSGMGR / SEAL / PAT (external) → OracleAdapter → Normalizer → DRYDOCS_STG →
  Neo4j (downstream). Verify against actual loader file paths.

- **1.2 §DES/full-refresh — Full-refresh sequence diagram.** Mermaid sequenceDiagram
  showing the actor sequence for a full-load run: STG_RUN open → CM_DEF_VJOB query →
  normalize → write STG_ tables → close STG_RUN. Reference the actual Python files
  and SQL objects.

- **1.3 §DES/incremental — Incremental load sequence diagram.** Mermaid
  sequenceDiagram: read HWM from STG_LOAD_CONTROL → changed-job extract → per-batch
  (cleanup staging → insert → advance HWM) → graph sync. Reference
  `incremental_controlm.py` (planned) and `incremental_changed_jobs.sql` (planned).

- **1.4 §DES/er — STG_ tables ER diagram.** Mermaid erDiagram showing
  STG_RUN, STG_LOAD_CONTROL, STG_SAMPLE_MANIFEST, STG_VARIABLE, STG_APP_FACT,
  STG_INVOCATION, STG_FILE_REF, STG_FILE_OP, STG_NOTIFICATION, STG_PARSE_QUALITY,
  STG_UNPARSED_COMMAND with their key relationships.

- **1.5 §TM — Traceability matrix.** For each FR-OI-*, map to: triggering UC-OI-*,
  implementation file (SQL/Python), status, and open questions that block it.

- **1.6 §FR + §UC verification.** Read `drydocs/loaders/sql/`, the staging DDL files,
  and `controlm_variables_scenarios.sql`. Verify each FR-OI-* is accurately stated;
  update or add items as needed. Add `verified_against:` field per FR.

- **1.7 Finalize.** Update §META last_updated/version; ensure §LOG records this
  review pass; set phase 1 task status in SDLC-CHECKPOINT.md.

---

## Phase 2 — Neo4j Architect (skills: `neo4j-getting-started-skill`, `neo4j-modeling-skill`, `neo4j-cypher-skill`)

Target: `docs/reviews/sdlc-neo4j-schema.md`

Tasks:

- **2.1 §C1 — Context diagram.** Generate Mermaid C1 flowchart showing
  DRYDOCS_STG (upstream) → Client → Schema Layer → Loader Layer → Neo4j Instance →
  Consumers (CLI, query library). Verify against actual file paths.

- **2.2 §DES/schema — Graph schema diagram.** Mermaid graph showing all active
  node labels, their NODE KEY properties, and the full relationship matrix. Include
  PROV-O class annotation per node.

- **2.3 §DES/ontology — Ontology hierarchy diagram.** Mermaid graph showing the
  SUBCLASS_OF chain from local classes to PROV-O / W3C ORG parent classes.

- **2.4 §DES/incremental — Incremental graph load sequence diagram.** Mermaid
  sequenceDiagram: read HWM → stale_edge_cleanup.cypher → jobs UNWIND MERGE →
  conditions re-assert → JobRun annotation. Reference actual cypher files.

- **2.5 §TM — Traceability matrix.** For each FR-NS-*, map to triggering UC-NS-*,
  implementation file (cypher/python/yaml), status, and open questions.

- **2.6 §FR + §UC verification.** Read `drydocs/schema/`, `drydocs/loaders/cypher/`,
  `relationship_vocabulary.yaml`. Verify each FR-NS-* is accurately stated; update
  as needed. Flag any gaps between declared FRs and actual files.

- **2.7 Finalize.** Update §META; ensure §LOG records this pass; set phase 2
  status in SDLC-CHECKPOINT.md.

---

## Phase 3 — Cross-Reference

No skill load needed.

- **3.1 Cross-doc linkage.** Add a `§XREF` section to each doc with explicit
  cross-references: which Oracle staging tables / views feed which graph loaders;
  which FRs in one doc are dependencies of FRs in the other; shared open questions.

- **3.2 Finalize.** Set `status: COMPLETE` in SDLC-CHECKPOINT.md; commit locally
  with message "sdlc-docs: initial living document set complete".

---

## Maintenance cadence (ongoing, after COMPLETE)

When `status: COMPLETE`, the session resumes in **maintenance mode**:

- Check for new commits on `feature/oracle-ingestion` that affect the two flows.
- If new loader files, DDL, or cypher files are detected → update the relevant
  §FR, §UC, §SRC sections and append to §LOG.
- Re-run traceability matrix (§TM) if FRs changed.
- Set `status: COMPLETE` again when done; update `last_updated`.
