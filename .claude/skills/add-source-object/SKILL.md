---
name: add-source-object
description: >
  Guided walkthrough to add ONE new table/view (an "object") to an EXISTING
  source in config/source-registry.yaml — the "web form" that pre-populates
  from configuration, profiles the object on its platform, and walks the
  series: profile → column ledger → ontology proposal → HITL gate spec →
  extract SQL. Use when the user says "add this table", "onboard cm_<x>",
  "new object from psgmgr/PAT/SEAL", or wants a new CM_ replica object
  ingested. Everything it produces is gate-bound — nothing loads until the
  SME confirms.
---

# add-source-object — onboard one object of an existing source

**Scope:** one object (table/view) of a source that already exists in
`config/source-registry.yaml`. Registering a whole NEW source is
`pipeline-config` agent territory, not this skill.

**The contract:** pre-populate everything derivable from config; ask the user
only what cannot be derived; STOP at the HITL gate. All artifacts land as
`proposed`/`planned`. Mechanism-only in every committed file — column names
and counts are fine; real data values (host names, SIDs, folder names,
service names) never are.

## Step 0 — Pre-populate (read, don't ask)

Read these; carry the answers through every later step:

| From | Pre-fills |
|------|-----------|
| `config/source-registry.yaml` (the source's entry + `locator:` block) | platform product, schema, service env-pointer, classification ceiling, orchestrator, precedence authority |
| `config/source-mappings/<source>.yaml` | existing objects (dupe check — is this object really new?), house disposition style |
| `config/taxonomy/software-registry.yaml` | the platform's SoftwareProduct row (version, role) |
| the source's domain skill if one exists (e.g. `controlm-db` for CM_ objects) | concept→table crosswalk, house extract rules, guardrails |

Confirm with the user: object name, and the *stated use case* for ingesting it
(projections are added behind a use case, never speculatively).

## Step 1 — Profile the object on its platform

Dispatch by `locator.platform`:

- **oracle-db** → follow the oracle-db skill's schema-discovery sequence:
  object type → column census → constraints/indexes → stats/volume → grain
  check → value domains → cross-object join-coverage probes against the
  objects it must join.
  - **No live connection here (producer machine)** → emit the probes as
    `drydocs/loaders/sql/adhoc/profile_<object>.sql` for the user to run
    internally in SQL Developer; they bring back CONCLUSIONS (counts,
    domains, match rates) — never result rows.
  - **Live connection (company side)** → run read-only via the
    `libs/oracle_kerberos` adapter.
- **csv / yaml / markdown** → profile the file directly (headers, row count,
  key candidates).

Record conclusions in the gate spec (step 4) and the ledger `via:` note —
the formal column census stays `census: pending` until doc-08 Phase 2 runs.

## Step 2 — Column ledger entry

Add the object to `config/source-mappings/<source>.yaml`: one disposition per
profiled column (`projected` | `filter-only` | `excluded`+reason | `deferred`),
a `default_disposition` sweep, and `staging:*` targets while the graph landing
is still gate-bound (the CM_DEF_SETVAR_VW precedent). Update the ledger's
`updated:` date and `tests/unit/test_source_mappings.py`'s expected-objects
list (+ one object-specific assertion).

## Step 3 — Ontology proposal (ontology-mapper pass)

Never invent an edge inside a loader. For each new concept:

1. Classify new node labels via the PROV matrix
   (`drydocs_core/ontology/relationship_vocabulary.yaml` §0/§1); check for label
   collisions with existing properties/labels before naming.
2. Register vocabulary entries as `status: planned`, `supplement: ~`,
   `loader: ~` (the SEAL-reshape precedent for gate-bound terms).
3. Add `config/taxonomy-ontology-map.yaml` entries as `status: proposed`
   and bump the `summary:` counts. Every entry carries BOTH structured
   fields (C7 — `tests/unit/test_taxonomy_ontology_map.py` enforces them on
   everything confirmed after 2026-07-10):
   - `vocab_id:` — the `relationship_vocabulary.yaml` id(s) the entry reuses
     or registers. If there is genuinely no vocabulary term (e.g. a property
     supplement or node reclass), write an explicit `~` PLUS a
     `vocab_id_reason:` one-liner — a YAML comment is not a reason.
   - `capture:` — the `config/taxonomy/` file the classification came from
     (taxonomy-first, CLAUDE.md §1). If no capture exists, waive explicitly:
     `capture: waived — <reason>` (the platforms.yaml retrofit is the
     precedent for what a silent skip costs — never omit the field).

## Step 4 — Gate spec

Write `config/gate-prompts/<source-short>-<topic>.yaml`
(`schema: drydocs.gate-prompt.v1`, classification: Internal-Public,
mechanism-only). Carry: the modelling options with a recommendation, the
profile conclusions, every open question from step 1, and the stated use
case. **This skill stops here** — the SME runs the gate
(`docs/restructure/03-hitl-sme-flow.md`) and logs to `config/gate-log.md`;
only then do statuses flip and a loader get written.

## Step 5 — Extract SQL (draft, gate-bound)

`drydocs/loaders/sql/<source-prefix>_<object>.sql` per the domain skill's
extract rules (for CM_ objects: controlm-db `references/ingest.md` §RULES —
project don't `SELECT *`, keep the scope binds that apply at this grain,
read-only against the source schema, staging DDL delta separately). Note the
load-order position (e.g. derived resolution passes run after both sides are
loaded — the WAS_INFORMED_BY pattern).

## Step 6 — Record and verify

- `config/source-registry.yaml`: extend the source's `feeds_taxonomy` if the
  object adds a new taxonomy feed; keep `notes` current.
- Append one line to `docs/restructure/IDEAS.md` so the gate session gets
  groomed into `backlog.yaml`.
- `poetry run pytest -q` must pass before commit.

## Worked example

`CM_HOSTS` (psgmgr replica of BMC CMS_NODGRP — host-group membership):
`sql/adhoc/profile_cm_hosts.sql`, `sql/controlm_hosts.sql`, ledger object
`CM_HOSTS`, vocabulary `m3_runs_on_host_group` / `m3_host_group_contains_host`
/ `m3_host_group_defined_on` (planned), gate
`config/gate-prompts/controlm-hosts-topology.yaml`.
