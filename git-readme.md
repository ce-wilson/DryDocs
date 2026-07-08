# DryDocs — Port Guide (producer `ce-wilson/DryDocs` → `<company-org>/DryDocs`)

> **This repo is version 1: a structural rewrite of the original DryDocs, not an increment on it.**
> It re-founds the project on the four-layer model (taxonomy → ontology → knowledge
> graph → context graph) with a clean external/internal split, a configuration layer,
> and an SME guided gate — see [`CLAUDE.md`](CLAUDE.md) and [`docs/restructure/`](docs/restructure/).
> The earlier off-track producer was archived as `ce-wilson/DryDocs-v0-archive` (read-only,
> dead history) and the v1 rewrite was renamed into its place. Throughout this guide,
> "producer" means `ce-wilson/DryDocs` (github.com).

This repo is the **producer** side. Work is built here on `main`, committed, and
pushed to `github.com/ce-wilson/DryDocs`. The **company** target is
`<company-org>/DryDocs` on GitHub Enterprise (`[github]` host); its maintainer
fetches `main` from the producer and applies it onto the company `main`. This file
is the instruction set for that apply; it rides inside the repo, so the
company-side reader has it.

> **Publishing boundary.** This is the **public** producer end of a one-way pipe.
> Only sanitized `internal-public`-tier content may be committed here — no real
> SEAL/app IDs, LOB/Product names, internal system code-names, infra object names,
> or org rosters. See [`PUBLISH-BOUNDARY.md`](PUBLISH-BOUNDARY.md) for the rule and
> [`config/classification.yaml`](config/classification.yaml) for the tiers. Real source material
> stays gitignored under `drydocs/data/`.

**The two histories are disjoint.** This repo was `git init`-ed fresh, not cloned
from company `main`, so there is **no common ancestor** — git has no merge-base to
3-way merge against. "Rebase" here therefore means **cherry-pick / `git am` the
commits onto `main`**, and every path is exactly one of:

- a **clean-add** — the path does not exist on `main`, so it applies untouched; or
- a **collision** — both sides created the same path independently. Git **cannot**
  auto-merge it (no base), so it must be reconciled by hand, every time.

The job of this file is to tell the company-side reader which paths are which and
what to keep in each collision. Direction is one-way (producer → company); company
`main` never becomes a remote here, and nothing is pulled back.

> Note on merge drivers: a `.gitattributes merge=ours` rule does **not** help here.
> With no merge-base, cherry-pick keeps the current branch (company `main`) and
> drops the incoming side — the opposite of porting work *in*. Use the **Canonical-
> here** list below instead (take this repo's version wholesale for those paths).

What diverges, by stream:

- **v1 restructure (NEW — the defining change of this version)** — the four-layer
  re-foundation: `reference/` + `external/orchestration/` (external tiers), `config/`
  (configuration layer), `internal/` (confidential split), `.claude/agents/` (sub-agents),
  `CLAUDE.md` (routing brain), `docs/restructure/` (model + plan + backlog + HITL flow).
  Almost entirely **clean-adds** — take FROM this repo. See the dedicated section below.
- **Control-M C3/C4 normalization** (variable taxonomy → resolver → command parser) —
  authored **here first**, Phases A/B/C complete; apply TO company, never overwrite locally.
- **Product ontology** (PAT/SEAL roles, AreaProduct hierarchy) — take FROM this repo.
- **Internal standards** (`knowledge/standards/`) — folder/data-center naming,
  description-metadata + calendar-projection plans, and the Control-M **governance
  corpus** (remediation flow, DAT/HLT naming, NFR catalog, escalation/SCIM, rules
  registry); additive, take FROM this repo.
- **Context graph — SOSA/SSN (EXPERIMENTAL)** — observation/temporal vocabulary for layer 4,
  wired as early-adoption: opt-in supplement, never in bootstrap, not a declared *company*
  standard. Entirely additive **clean-adds** — take FROM this repo. See the dedicated section below.
- **Schema consolidation** — patch files deleted, bootstrap order cleaned up; evaluate per file.
- **Architecture decisions + modular split (NEW)** — `docs/decisions/` ADRs (0001 ontology base
  scope; 0002 component & database topology + 0002-a core-extraction plan), `MODULE_MAP.md` +
  `tests/unit/test_module_boundary.py` (the core/component boundary guard), and the
  `SDLC-Docs/extracted/` design trail. All **clean-adds** — take FROM this repo. ADR 0002 foretells a
  structural `drydocs/ → drydocs-core` + component-package move (Phase B, **not yet executed**); see the
  dedicated section below. (ADR **0002-c** — depgraph-lineage re-home — is a newer clean-add in the same set.)
- **`drydocs-review` back-flow (NEW — REVERSE direction)** — the company-authored SME/HITL toolkit,
  reproduced here generically. **Canonical-COMPANY on collision** — keep your version. See the dedicated
  "`drydocs-review` — back-flow stream" section below.
- **`drydocs-plan` project board (NEW — Epic I)** — `drydocs/plan_board.py` + `scripts/render_board.py`
  render `backlog.yaml` (now **schema v2**) into `docs/plan/board.html`; plus the `groom-backlog` skill and
  a new `tests/unit/test_backlog.py` schema guard. All **clean-adds** — take FROM this repo. `plan_board`
  is its own `plan` component group in the boundary guard (imports core only).
- **`drydocs-docmeta` document ingestion (PLANNED — heads-up, not yet built).** A document-
  ingestion component (vendor docs + internal guidance + SME context → `drydocs_docs` /
  `drydocs_context`) is planned in
  [`knowledge/upgrade-plans/docmeta-component.md`](knowledge/upgrade-plans/docmeta-component.md).
  When it lands it is a **mixed** stream: pipeline/registry/tests are clean-adds; the working
  Confluence connector wiring is **Canonical-COMPANY** (same rule as `drydocs-review`); and the
  company side must **supplement** vendor fetches blocked producer-side (documents.bmc.com 403),
  T4 connector credentials (Graph API, mailbox, Toby), and the multi-DB Neo4j target. Full
  disposition table + two-track acceptance oracle: plan §6.
- **`seal_app_ref` attribution (Epic K) — back-flow-origin, check before taking wholesale.** Additive
  `status: planned`/`proposed` entries in `drydocs/ontology/relationship_vocabulary.yaml` +
  `config/taxonomy-ontology-map.yaml` (both normally Canonical-here). It was **groomed from company
  reconciliation** — the concept came FROM you. While `planned`/`proposed` it is inert (no graph impact),
  so taking the producer files is safe. **But if company `main` has already promoted `m3_seal_app_ref` to
  `active`/`confirmed` (or has a live loader), that entry is a back-flow COLLISION — keep your active
  version, do not downgrade it to the producer's `planned` state.** Reconcile that entry per-item, not by
  blindly overwriting the file.
- **SEAL entity reshape + scraped-docs source-of-record (2026-07-08 review — GATE-BOUND, inert until
  SME-confirmed; do NOT take as applied).** Two linked decisions the `drydocs-docmeta` scrape drives —
  full write-up in [`knowledge/upgrade-plans/docmeta-component.md`](knowledge/upgrade-plans/docmeta-component.md)
  + IDEAS.md 2026-07-08. **(1) The `:Application` node is mis-typed.** It is `prov:SoftwareAgent` yet also
  carries `dprod` ports (→ Entity), `org:Membership → org:Role` (→ Organization), and the K1/K2
  `wasAssociatedWith` (→ Agent) — three incompatible types on one node. It should be a
  **`prov:Entity` / `dprod:DataProduct`** (an asset/record). Its Technical-Operating-Model role-holders
  (CTO, application owner, information owner, data owner, operate manager, risk & compliance officer — a
  governance model **distinct from the PAT product org**) become **`prov:qualifiedAttribution` +
  `prov:hadRole`** (Role = shared `skos:Concept` vocab), NOT `org:Membership` — which stays for the PAT
  hierarchy ONLY. Deprecate `seal_has_membership`/`seal_of_role`/`seal_held_by`; keep `seal_has_port`.
  **K1/K2 must be re-shaped** (they need Agent today) — still `proposed`, so fix it there. **(2) Scraped
  SEAL/PAT pages are the source of record** via `config/precedence.yaml` authority + **`prov:hadPrimarySource`**
  on every extracted fact (Entity→Entity — which is *why* the app record must be an Entity). **Port impact:**
  if company `main` has already typed `:Application` as Agent or applied any `seal_*` membership edge, this
  is a back-flow reconciliation to resolve at the gate — do not blind-overwrite in either direction. Route
  via `ontology-mapper` + the HITL gate; log in `config/gate-log.md`.

---

## v1 restructure — the new top-level layout (take FROM this repo)

The defining change of version 1. These are the structural commits (`8800946` restructure
+ `be1eac9` drift-guard) and are almost entirely **clean-adds** on the company side (the
paths don't exist there yet). Take them wholesale.

| Path | What it is | Disposition |
|---|---|---|
| `CLAUDE.md` | routing brain: four layers, all external refs, sub-agents, precedence | clean-add |
| `reference/` | Tier-1 external: Neo4j/Oracle platforms + ontology standards (PROV-O, ORG, DPROD, SOSA/SSN, DCAT) + research, indexed by `REGISTRY.yaml` | clean-add |
| `external/orchestration/` | Tier-2 external: BMC baseline (moved from `vendor/bmc-controlm/`) + AutoSys/Airflow placeholders + crosswalks | rename + clean-add |
| `config/` | configuration layer: `precedence.yaml`, `source-registry.yaml`, `classification.yaml` (sensitivity axis), `taxonomy-ontology-map.yaml`, `taxonomy/` (Control-M + BusinessApplication + LOB→Product→Team + Oracle-schema captured) | clean-add |
| `internal/` + `PUBLISH-BOUNDARY.md` | confidential split for the private-but-sometimes-public repo | clean-add |
| `.claude/agents/` | four sub-agents (reference-librarian, taxonomy-importer, ontology-mapper, pipeline-config) | clean-add |
| `docs/restructure/` | conceptual model, project plan, sub-agent backlog, HITL SME flow | clean-add |

**One rename to handle on the company side:** `vendor/bmc-controlm/` →
`external/orchestration/bmc-controlm/`. If company `main` still has `vendor/bmc-controlm/`,
delete it after taking the new path (across disjoint history git sees the move as
delete+add). Doc/code references to the old path were repointed in the same commit.

**Three guards now enforced (require PyYAML, a dev dep):**
- `tests/unit/test_schema.py` — fails CI if a relationship is `active` without its supplement
  block (the ontology-drift safety net).
- `tests/unit/test_classification.py` — fails CI if any source in `source-registry.yaml` lacks a
  valid sensitivity `classification` + `source` (the publish-boundary safety net). Sensitivity
  tiers: `External` / `Internal-Public` / `Internal` / `Internal-Confidential`
  (`config/classification.yaml`), distinct from the provenance tier in each `SOURCE-MANIFEST`.
- `tests/unit/test_backlog.py` (NEW — Epic I) — fails CI if `docs/restructure/backlog.yaml` violates
  **schema v2**: missing `title/type/module/phase`, duplicate/cyclic/unresolved ids, unknown module or
  phase, or a `summary:`/`next_ready:` roll-up that drifts from the items (both are computed views).

**Post-push code-structure snapshot (drift comparison):** after each push, generate a
timestamped dependency-graph snapshot with the `depgraph` tool (a stdlib-only sibling repo) and
compare to the previous one — see
[`knowledge/depgraph-snapshots/README.md`](knowledge/depgraph-snapshots/README.md).

> **Next upgrade — internal import:** the internal data sources (SEAL, the LOB→Product→Team
> org taxonomy, Oracle schemas) are imported through the new taxonomy → config → ontology →
> HITL → loader flow, with confidential data isolated in `internal/`. The implementation
> plan is [`knowledge/upgrade-plans/internal-import.md`](knowledge/upgrade-plans/internal-import.md).

---

## Architecture decisions + modular split (NEW — clean-adds; structural change ahead)

Newer than the v1 restructure commits. All **clean-adds** on the company side (paths absent there);
take FROM this repo.

| Path | What it is | Disposition |
|---|---|---|
| `docs/decisions/0001-*.md` | ADR 0001 — ontology base scope (PROV spine) | clean-add |
| `docs/decisions/0002-*.md`, `0002-a-*.md`, `0002-b-*.md`, `0002-c-*.md` | ADR 0002 — component & database topology + core-extraction plan + spinoff-rebase checklist + depgraph-lineage re-home | clean-add |
| `MODULE_MAP.md` | the `drydocs-core` ↔ component boundary (authoritative) | clean-add |
| `tests/unit/test_module_boundary.py` | stdlib guard enforcing the boundary (Track-1 portable, no data) | clean-add |
| `SDLC-Docs/extracted/*.md` | design trail (feasibility, C+D adoption, issue-driven loop, modular plan) | clean-add |

**Heads-up — a structural path-move is coming (ADR 0002 D3, Phase B).** The modular split will move
code out of the flat `drydocs/` package into `drydocs-core` + component packages (`drydocs-load` /
`drydocs-lineage` / `drydocs-deepdoc`). When that lands, expect a large **rename wave**: across disjoint
history git sees each move as delete+add (same as the `vendor/ → external/` rename above), and the
per-file collision rules in this guide will be **superseded** by the package boundary in
`MODULE_MAP.md`. Until Phase B executes, the layout is unchanged and all current cherry-pick rules still
apply. The boundary guard is **Track-1 portable** (pure stdlib, no sample data) — add it to the Track-1
acceptance run.

---

## `drydocs-review` — back-flow stream (Canonical-COMPANY; KEEP YOUR VERSION)

**This is the one place the normal direction reverses.** The company authored a
generic SME-review / HITL toolkit — the **`drydocs-review` component** — to close the
"how does the SME see what loaded and tell the agent what to change" loop. The
producer committed to the HITL SME gate as a concept but shipped it *docs-only*, so
that tooling is being **reproduced generically here** as a public template (plan:
[`docs/restructure/05-drydocs-review-backflow.md`](docs/restructure/05-drydocs-review-backflow.md)).
It is re-implemented from descriptions, **not** copied from company code.

Consequence for you, the company-side reader: once the producer's generic versions
land, these paths exist on **both** sides and will show up as **collisions**. Resolve
them the **opposite** way to everything else in this guide:

> **Canonical-COMPANY — keep your version; do NOT apply the producer's copy over it.**
> The producer's `drydocs-review` files are the sanitized *public template*. Yours carry
> the real Confluence wiring (`toby_publish_confluence`), the real `review-labels.yaml`,
> the real space coordinates, and real `SME[SID]` data. Take **company wholesale** for:
>
> - `drydocs/graph_review.py`, `drydocs/graph_verify.py`, `drydocs/review_labels.py`,
>   `drydocs/sme_notes.py`
> - `drydocs/gate_pages.py` (the HITL prompt-page generator) + any generated `pages/`
> - `drydocs/publishing/**`
> - `config/review-labels.yaml`, `config/gate-prompts/**`, `graph-tests/**` (seed spine,
>   gate-prompt specs, acceptance suites — company's real ones win)

If you have `git fetch`ed and see the producer touch these, drop the incoming side and
keep `main`'s. This is the reverse of the Canonical-here rule — it protects your wired,
internal-data originals from being clobbered by the public template. (Mirrored in the
`reconcile-port` skill's divergence ledger and [`docs/port-prompt.md`](docs/port-prompt.md).)

**Boundary guard note:** the producer will also add a `review` `COMPONENT_GROUP` to
`tests/unit/test_module_boundary.py` + `MODULE_MAP.md`, and flip the guard to
**default-deny** (every module must classify into exactly one bucket, else the test
fails). That change is generic and Track-1 portable — take it FROM the producer; it is
what forces your company-only modules to be classified rather than silently unguarded.

**2026-07-07 update — three refinements to this stream** (details: port-prompt steps
17–18):

1. **Seed-file rename (ADR 0004):** `graph-tests/vendor-bmc-smoke.yaml` →
   `bmc-docs-smoke.yaml` and `config/gate-prompts/vendor-bmc-example.yaml` →
   `bmc-docs-example.yaml` (ids renamed too). The producer's generic tests now assert
   the new names — apply the same rename to your seed twins as a deliberate
   company-side commit; your real suites/specs under other filenames are untouched.
2. **Gate-page STANDARD format:** `gate_pages.py` gained a generic meta-card +
   SOURCE/DERIVED provenance extension, directed in `03-hitl-sme-flow.md`
   §"Gate-page format" and test-enforced for every committed gate spec. Pure
   mechanism — fold it into your copy and upgrade your real specs to the standard
   (or decline the delta AND its tests together, logged).
3. **`config/gate-log.md` is append-only audit:** on collision merge additively
   (union of entries, chronological); never drop either side's gate records.

---

## Commit range to apply

Don't hand-maintain a hash list — it goes stale and a rebase rewrites the SHAs.
Regenerate it instead:

The deliverable lives on `main` (the `controlm-spinoff` branch is not used for the
port). On the company side, after fetching, list the commits to apply:

```
git log --oneline --reverse cewilson/main    # full line — histories are disjoint, so all of it is "new" vs company main
```

Hashes are transferred intact by `git fetch`, so a SHA you see locally resolves
identically on the company side once the branch is fetched. Identify commits by
**subject**, not SHA. The Control-M normalization stream is the three commits with
subjects **"…variable taxonomy (Phase A)…" → "…variable resolver… (Phase B)…" →
"…Phase C command/script parser…"**, applied in that order; everything else is
additive docs + ontology.

---

# Applying this work onto `<company-org>/DryDocs` `main` (disjoint histories)

There is no merge-base, so this is a cherry-pick, not a true rebase. Each path is
either a **clean-add** (applies untouched) or a **collision** (hand-reconcile).

## How the company side applies it

```
git remote add cewilson https://github.com/ce-wilson/DryDocs.git
git fetch cewilson main
git switch -c drydocs-port main
git cherry-pick <oldest>^..<newest>     # range from the log command above
```

Clean-adds apply silently. Cherry-pick stops on each collision; resolve per the
Collisions table, `git add`, then `git cherry-pick --continue`. Equivalent path:
`git format-patch` on the producer side + `git am --3way` on the company side.

## Canonical-here — take this repo's version wholesale on collision

For these paths, **do not hand-merge** — this repo is authoritative; replace
`main`'s version. They are local-authored in full:

- `drydocs/controlm/` — the entire normalization package (Phase A/B/C).
- `knowledge/standards/` — every file (naming standards, governance corpus, plans).
- `drydocs/loaders/sql/controlm_variables.sql`, `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql`.
- `drydocs/ontology/relationship_vocabulary.yaml`, `drydocs/schema/catalog_ontology_supplement.cypher`.
- **v1 restructure — entire new top-level layout (all canonical-here, take wholesale):**
  `CLAUDE.md`, `PUBLISH-BOUNDARY.md`, `reference/`, `external/orchestration/`, `config/`,
  `internal/`, `.claude/agents/`, `docs/restructure/`.

`drydocs/data/` is `.gitignore`d — sample CSVs stay local and never transfer.

## Clean-adds — apply untouched (paths absent on company `main`)

| File | Phase | Purpose |
|---|---|---|
| `drydocs/controlm/variables.py` | A | `VariableKind` (9 kinds) + `classify_variable()` / `classify_job_variables()` |
| `drydocs/controlm/variable_report.py` | A | `VariableCoverage` accumulator |
| `drydocs/loaders/sql/controlm_variables.sql` | A | Variable extract query (`psgmgr.CM_DEF_SETVAR` — **name unverified**) |
| `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` | A | Full staging-layer DDL (8 STG_ tables + views) |
| `drydocs/controlm/resolver.py` | B | Offline AutoEdit substitution engine |
| `drydocs/controlm/staging.py` | B (ext. C) | STG_ row builder — `build_staging_bundle` / `collect_jobs` |
| `drydocs/controlm/commands.py` | C | Shell parser + `LAUNCHER_REGISTRY` |
| `drydocs/controlm/paths.py` | C | Path canonicalization + ref_role classification |
| `drydocs/controlm/facts.py` | C | Fact / notification routing |
| `docs/controlm-c3-normalization-status.md` | B (ext. C) | Status + operational runbook |
| `tests/unit/test_variable_classifier.py` | A | |
| `tests/unit/test_variable_resolver.py` | B | |
| `tests/unit/test_variable_staging.py` | B (ext. C) | |
| `tests/unit/test_command_parser.py` | C | |

## Collisions — git cannot auto-merge; reconcile by hand

Two kinds of row here, and they collide differently:

- **Integration points** — `drydocs/cli.py`, `drydocs/models/controlm.py`,
  `drydocs/models/__init__.py`. These are pre-existing DryDocs infrastructure, so
  they exist on company `main` and **will** conflict — hand-merge per the column.
- **Phase-evolution rows** — `drydocs/controlm/*.py` (`__init__.py`, `variables.py`,
  `staging.py`, `variable_report.py`). The multi-phase tag describes how they grew
  A→B→C *here*. They collide on the company side **only if** company `main` already
  has a `drydocs/controlm/` package; if not, they're clean-adds. Either way they're
  Canonical-here — take this repo's version, don't merge.

With no merge-base, cherry-pick conflicts on each integration point. Resolve by
preserving the column below.

| File | Phases | What to preserve when resolving |
|---|---|---|
| `drydocs/controlm/__init__.py` | A, B, C | Re-exports accumulate each phase. Final `__all__` must export: `VariableKind`, `ClassifiedVariable`, `classify_variable`, `classify_job_variables`, `VariableCoverage` (A); `ResolvedVariable`, `resolve_job`, `resolve_layers` (B); `Invocation`, `FileOp`, `parse_command`, `extract_container_command`, `FileRef`, `build_file_ref`, `canonicalize_path`, `classify_role`, `route_fact`, `build_staging_bundle`, `build_staging_rows`, `collect_jobs` (C). |
| `drydocs/cli.py` | A, B, C | Adds two commands: `analyze-variables` (A, `--resolve` flag added in B) and `normalize-variables` (B, extended in C to write 8 CSVs). Imports from `.controlm` and `.controlm.staging`. No existing command bodies changed. |
| `drydocs/models/controlm.py` | A | Adds `ControlMVariableRow` (and an `AliasChoices` import). Existing row models untouched — conflicts here mean someone else also edited the model file. |
| `drydocs/models/__init__.py` | A | Adds `ControlMVariableRow` to imports + `__all__`. |
| `drydocs/controlm/variables.py` | A, B | B reworked the token grammar (system-var registry, `%%$` century syntax, global/pool refs). If you patched A's `variables.py`, reapply onto B's grammar — see the `KNOWN_SYSTEM_VARIABLES` / `KNOWN_SYSTEM_FUNCS` registries. |
| `drydocs/controlm/staging.py` | B, C | C restructured the B builder around `StagingBundle`. `build_staging_rows` survives as a back-compat shim returning `(variable, parse_quality)`. |
| `drydocs/controlm/variable_report.py` | A, B | B added system-var / global-ref counters. |

## Load / dependency order (import-time)

```
variables.py      (no intra-package deps)
  ├── variable_report.py   (imports variables)
  ├── resolver.py          (imports variables: ENV_LETTER_MAP, _is_system_func/_var)
  ├── paths.py             (standalone)
  ├── commands.py          (standalone)
  ├── facts.py             (imports variables)
  └── staging.py           (imports models, commands, facts, paths, resolver, variables)
```

`__init__.py` imports `staging` last (it pulls in everything). If you split or move
any of these, keep `staging` downstream of the rest.

## Acceptance oracle — how the company side confirms the port landed

The code is re-applied, not byte-compared, so behavior is the contract. The
variable-stream tests split in two: most are **inline** (no data file) and run
anywhere; a few read the **production sample CSV**, which is `.gitignore`d and
does not transfer. So there are two tracks.

### Track 1 — portable (any clone, no sample present)

```
poetry run pytest tests/unit/test_variable_classifier.py \
                  tests/unit/test_variable_resolver.py \
                  tests/unit/test_variable_staging.py \
                  tests/unit/test_command_parser.py -q
```

Expect **86 passed, 3 skipped** — the 3 skips are the sample-backed tests
(`test_sample_*`), which skip (not fail) when the production CSV is absent. Full
suite `pytest tests/unit/` is green: passing + sample-skips + the 4 `test_schema.py`
PyYAML skips. **Zero failures is the Track-1 contract.** A `FileNotFoundError` on
`controlm_variables__sample.csv` means the skip guard was lost in the port.

### Track 2 — full (production sample present, or pulled fresh from `psgmgr`)

Either restore a sample at `drydocs/data/samples/controlm_variables__sample.csv`,
or pull fresh (read-only):

```
poetry run drydocs normalize-variables --use-oracle --folder 'CCB_AUTO_%' --row-cap 5000 --out-dir stg_out
```

With the **bundled sample**, the counts are deterministic and verified
(2026-06-18): the four-file suite is **89 passed**; `normalize-variables` emits
jobs=82, definitions=323, `stg_variable`=326, `stg_parse_quality`=82,
**`stg_invocation`=6, `stg_file_op`=16, `stg_file_ref`=92, `stg_notification`=14,
`stg_app_fact`=66**, fully_resolved=86.2%.

With a **fresh production pull** the counts will differ (different population) — so
judge it on *runs clean, no `UNKNOWN` invocation leakage, plausible coverage %*,
not the bundled numbers. Every `psgmgr` extract accepts the scope binds
`--folder`, `--developer-sid`, and `--row-cap` (NULL = full population);
job-bearing extracts also take `--run-as`. `--run-as` = the tenant FID/service
user (`J.OWNER`); `--developer-sid` = the human who authored/changed the def
(`AUTHOR`/`CREATION_USER`/`CHANGE_USERID` on jobs, `LAST_UPDATED_USER` on
folders) — Control-M SIDs start lowercase and a trailing lowercase `p` marks the
automation release process, not a person. Use these to keep a fresh pull small
and targeted. (Operational *who-ran-it* identity is separate and deferred — it
lives in the action-audit table `psgmgr.CM_AUD_ACTS`, not the definition rows.)

If a Track-1 test fails (not skips), the port is incomplete — diff the failing
area against the phase descriptions below, not against commit hashes.

> **History:** before `62753b3`, six tests in `test_schema.py`,
> `test_folder_name_parser.py`, and `test_controlm_cypher.py` failed on `main`.
> They were **not** Control-M-stream bugs — they asserted pre-refactor behavior
> (constraint count, the `"Group Table/Smart folder"` label, the `(folder_id,
> name)` Condition key, the `:WAS_INFORMED_BY` edge rename, and the
> `ontology_supplement.cypher` rename) left stale by the schema-consolidation
> work documented below. `62753b3` realigned them to the shipped code. If you
> are rebasing across that boundary and see these resurface, take the updated
> assertions — do not delete the tests; they guard live code.

> **Concat-dot bugfix (`89d6648`):** `resolver.py` mishandled variable names
> containing a dot-separator (e.g. `%%SCRIPT_PATH.%%ENV`). The token boundary
> logic was treating the dot as part of the variable name rather than a literal
> separator, causing over-substitution. If you are rebasing Phase B work across
> this commit, re-verify resolver output on any variables that use the
> `name.suffix` or `prefix.%%ref` concatenation pattern — the fix changes
> resolved values, not just parse counts.

---

# Control-M C3/C4 normalization — current state (push TO company)

Three phases below the existing job-to-job lineage, all delivered here. The company
site has a more complete Control-M *loader* implementation, but the **normalization
pipeline (A/B/C) was authored here** and should be pushed TO company, not pulled over.
Do not overwrite local files under `drydocs/loaders/controlm/`,
`drydocs/schema/ontology_supplement.cypher` (Control-M content), or the Control-M SQL
loaders with versions from elsewhere.

Architecture: **SQL extract → Python normalize → Oracle staging (`DRYDOCS_STG`,
QA in SQL Developer) → Neo4j under PROV `:JobRun`.** Variable resolution and command
parsing happen in Python, not recursive SQL.

## Phase A — variable taxonomy + staging output (`91882df`, output side completes the phase)

`VariableKind` (9 kinds, precedence order):

| Kind | Description |
|---|---|
| `MALFORMED` | Empty / whitespace / invalid name token |
| `EMBEDDED_SHELL` | `PRECMD` / `POSTCMD` (+ observed `POSCMD` typo) — shell text for Phase C |
| `PLUGIN_NS` | `%%FileWatch-*`, `%%UCM-*` — routed to APPL_TYPE handler |
| `FLOW_REF` | `%%\VAR` global / `%%\\POOL\VAR` pool — cross-job shared state, kept verbatim |
| `DYNAMIC_NAME` | Adjacent `%%refs` compose a name at runtime — per-env expansion in B |
| `SEMANTIC_FACT` | Fact-registry name (SEAL, FID_*, DATAFLOW...) — mined into `STG_APP_FACT` |
| `SYSTEM_FUNC` | Only system tokens (CALCDATE/SUBSTR/GETENV/WCALC/BLANK + system vars) |
| `VAR_REF` | References other user `%%vars` — resolved in B |
| `LITERAL` | None of the above |

Output side (`staging.py` + `normalize-variables`) writes `STG_RUN`, `STG_VARIABLE`,
`STG_PARSE_QUALITY` with columns matching the DDL exactly. ~1.1M variable rows across
4 DCs (~18.8K folders / ~240.6K jobs); 59% of jobs have zero variables.

## Phase B — variable resolver (`520f9ca`)

`resolver.py` — offline AutoEdit simulation. Sequential assignment (ordered defs,
last binding wins, forward refs stay unresolved); longest-defined-name matching at
each `%%` site; canonical symbolic tokens (`{ODATE}`, CALCDATE compaction `{ODATE-1}`);
cross-pass blocked-set kills self-reference loops; env-triplet variant expansion
(`%%SCRIPT_PATH_%%HOSTNM`); global/pool refs kept verbatim. Sample: 86% fully resolved.

Vendor validation (`external/orchestration/bmc-controlm/controlm-variables.md`) corrected three things in
`variables.py`: system variables exist without `$` (`%%ORDERID`, `%%JOBNAME`); `%%$X`
is century-format syntax; `%%\VAR` (global) vs `%%\\POOL\VAR` (pool) both captured.

## Phase C — command / script parser (`cb6e056`)

Parses the executable side into the five remaining staging tables.

| Module | Produces |
|---|---|
| `commands.py` | `STG_INVOCATION` (data-driven `LAUNCHER_REGISTRY`: `.m`→ABINITIO, `pmcmd`→INFORMATICA, `run_data_validation.sh`→VALIDATION_UTIL, `python`→PYTHON/PYSPARK, …), `STG_FILE_OP` (mkdir/cp/mv/rm/sed) |
| `paths.py` | `STG_FILE_REF` (canonical paths, `{TS16}` wildcards, ref_role) |
| `facts.py` | `STG_APP_FACT` + `STG_NOTIFICATION` |

`normalize-variables` now writes all 8 STG_ CSVs. Sample: 6 invocations (0 UNKNOWN),
16 file ops, 92 file refs, 14 notifications, 66 app facts.

Grow `LAUNCHER_REGISTRY` (add a `(basename regex, invocation_type, rule_id)` tuple)
as the UNKNOWN backlog reveals new launchers — that is Phase E. Vendor docs read for
this phase: `controlm-{os-job-parameters,file-watcher,api-job-types,file-transfer-job}.md`.

## Staging DDL (`controlm_staging_ddl.sql`, schema `DRYDOCS_STG`)

8 tables: `STG_RUN`, `STG_VARIABLE`, `STG_PARSE_QUALITY`, `STG_INVOCATION`,
`STG_FILE_OP`, `STG_FILE_REF`, `STG_NOTIFICATION`, `STG_APP_FACT`, plus base read views
and `STG_COVERAGE_SUMMARY`. Surrogate identity PKs (duplicate `(job, var_name)` defs are
legitimate). All keys carry `DATA_CENTER` (TABLE_ID may collide across the 4 DCs).
< 3M rows / < 2 GB; no partitioning.

> **TODO (DBA)**: confirm the variable source view name. The SQL Developer extract used
> `TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE` (`TABLE_NAME` carries `TABLE_ID`
> values). The query uses `psgmgr.CM_DEF_SETVAR` — verify before running. Flagged in
> both `controlm_variables.sql` and the DDL.

See `docs/controlm-c3-normalization-status.md` for the full status + operational runbook.

---

## Take FROM this repo → company

### 1. PAT Product Ontology — `AreaProduct` node + team alignment model

**Commit: `6c5b7b5`**

Added `AreaProduct` (Area Product Group / Team of Teams) as an intermediate org
level between `Product` and `DevTeam`, team type edge properties on `SUPPORTS`,
and the full PAT human role vocabulary.

| File | What was added |
|---|---|
| `drydocs/ontology/relationship_vocabulary.yaml` | `AreaProduct` node classification + 6 new local relationships |
| `drydocs/schema/catalog_ontology_supplement.cypher` | `AreaProduct` LocalClass, 5 LocalRelationship declarations, all 31 Role seeds |
| `drydocs/schema/constraints.cypher` | `area_product_id` uniqueness constraint |
| `drydocs/schema/schema_graph.cypher` | `AreaProduct` SchemaMeta node + 6 relationship MATCH/MERGE blocks |
| `drydocs/models/catalog.py` | `AreaProductRow`, `PatProductMappingRow`, `PatTeamRoleRow` Pydantic models |
| `drydocs/loaders/catalog.py` | `AreaProductsLoader`, `PatProductMappingLoader`, `PatTeamRolesLoader` |
| `drydocs/loaders/cypher/area_products.cypher` | MERGE AreaProduct + HAS_AREA_PRODUCT to parent Product |
| `drydocs/loaders/cypher/pat_product_mapping.cypher` | HAS_APPLICATION (Product→Application) + SUPPORTS edges |
| `drydocs/loaders/cypher/pat_team_roles.cypher` | DevTeam HAS_MEMBERSHIP n-ary pattern |
| `drydocs/models/seal.py` | Added `"tech partner": "CTO"` to `_ROLE_CANONICAL` |
| `docs/NODE_QUICK_REFERENCE.md` | `AreaProduct` row in Catalog (active) table |
| `docs/Product/` | `product-overview.md`, `Technology_Team_Types.md`, `technology_roles_and_responsibilities.md`, `quad-mermaid.js` |

**New graph topology:**
```
Product -[:HAS_APPLICATION]-> Application
Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam
DevTeam -[:SUPPORTS {team_type, sponsored}]-> Product | AreaProduct
DevTeam -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE]-> Role -[:HELD_BY]-> Employee
```

- `team_type` on `SUPPORTS`: `aligned` | `flex` | `dedicated` (edge property, not node property)
- `sponsored: bool` on `SUPPORTS`: edge property, not a separate relationship type
- 31 Role nodes seeded — all MERGE on `name` to match how SEAL loaders MATCH roles at runtime

**Key alias added to `models/seal.py`:**
PAT calls the application-level tech lead "Tech Partner"; SEAL calls it "CTO".
Without this alias, PAT contact data fails role canonicalization.

### 2. `.gitignore` — exclude sample data

`drydocs/data/` is now ignored. Sample CSVs stay local and off-repo.
Apply this if the company repo is also tracking sample files you want to stop committing.

---

## Schema consolidation — evaluate against company baseline

These changes clean up patch files that existed because the M0 seed was stale.
The company site may have already fixed this differently — review each change before applying.

### Deleted files (absorbed elsewhere)

| Deleted | Content moved to |
|---|---|
| `drydocs/schema/m3_constraints_upgrade.cypher` | `drydocs/schema/constraints.cypher` |
| `drydocs/schema/m1_role_vocabulary_update.cypher` | Eliminated — roles now seeded correctly from the start in `catalog_ontology_supplement.cypher` |
| `drydocs/schema/m3_ontology_supplement.cypher` | Renamed to `drydocs/schema/ontology_supplement.cypher` |

### `constraints.cypher` — Control-M key corrections

The M3 draft used incorrect composite keys (included `version_serial` and `cyclic_type`).
Corrected to natural keys; loaders filter `IS_CURRENT_VERSION='1'` so one canonical node per logical entity:

```cypher
-- OLD (wrong)
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.job_id, j.version_serial) IS NODE KEY;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name, c.cyclic_type) IS NODE KEY;

-- NEW (correct)
DROP CONSTRAINT controlmjob_key IF EXISTS;
CREATE CONSTRAINT controlmjob_key FOR (j:ControlMJob) REQUIRE (j.folder_id, j.job_id) IS NODE KEY;
DROP CONSTRAINT condition_key IF EXISTS;
CREATE CONSTRAINT condition_key   FOR (c:Condition)   REQUIRE (c.folder_id, c.name) IS NODE KEY;
```

### `ontology.cypher` — stale M0 role seeds removed

The original M0 seed had 8 stale Role nodes with wrong names (`"App Owner"`,
`"Agility Lead"`, `"Product Contact"`, etc.). These were removed. If the company
site still has them, the correct nodes from `catalog_ontology_supplement.cypher`
will coexist alongside the stale ones. Clean up stale nodes only if no
memberships reference them:

```cypher
MATCH (r:Role) WHERE r.name IN ['App Owner', 'Agility Lead', 'Product Contact']
AND NOT EXISTS { MATCH ()-[:OF_ROLE]->(r) }
DELETE r;
```

### `cli.py` — command rename

| Old | New |
|---|---|
| `apply-m3-supplement` | `apply-ontology-supplement` |

Stale constants removed: `M1_ROLE_VOCAB_UPGRADE`, `M3_SUPPLEMENT_FILE`, `M3_CONSTRAINTS_UPGRADE`.
Added: `ONTOLOGY_SUPPLEMENT_FILE`, `SOSA_SUPPLEMENT_FILE` (+ `apply-sosa-supplement` command — see
below). Also fixed: `m3-verify` Cypher used `RUNS_ON` (now `SCHEDULED_ON`).

### Context graph — SOSA/SSN (EXPERIMENTAL / early adoption, clean-add)

Seeds the layer-4 observation/temporal vocabulary. SOSA/SSN is a W3C standard but **not a
declared *company* standard**, so it is deliberately fenced off from the production model and
every term carries `adoption:"experimental"`. All paths are **clean-adds / additive** — take
FROM this repo. Files touched:

| Path | Change |
|---|---|
| `drydocs/schema/sosa_experimental_supplement.cypher` | NEW — seeds 6 `sosa:` classes + 6 properties, `:CAN_ACT_AS` role wiring (ControlMJob/ControlMFolder → `sosa:FeatureOfInterest`), 4 `LocalRelationship`→`MAPS_TO`→`sosa:*` edges. Opt-in only. |
| `drydocs/ontology/namespaces.py` | + `sosa` / `ssn` prefixes (note trailing `/`, not `#`) |
| `drydocs/ontology/relationship_vocabulary.yaml` | + 4 SOSA node classes & 4 relationships (`domain: context`, `status: planned`); new `sosa_maps_to` field; `domain` enum gains `context` |
| `config/taxonomy-ontology-map.yaml` | `jobrun-observation` unblocked + `adoption: experimental` |
| `reference/standards/README.md` + `reference/REGISTRY.yaml` | standards split into **Declared/Adopted** vs **Experimental/Early-Adoption**; SOSA tagged `adoption: experimental` |
| `drydocs/cli.py` | + `apply-sosa-supplement` (opt-in; NOT in bootstrap) |
| `tests/unit/test_namespaces.py` | + sosa/ssn prefix + trailing-slash expand assertions |

Promotion to **Declared/Adopted** happens only after the SME confirms the `jobrun-observation`
mapping through the HITL gate (backlog Epic E); the `ontology-mapper` owns that step. No instance
data (Observations/Sensors/Results) is loaded — that is the gated context-graph pilot (E2).

### Bootstrap order (authoritative)

```
1. constraints.cypher
2. ontology.cypher
3. ontology_supplement.cypher         (was m3_ontology_supplement.cypher)
4. seal_ontology_supplement.cypher
5. catalog_ontology_supplement.cypher  (owns all 31 Role seeds)

Optional / experimental — NOT part of `drydocs bootstrap`:
6. sosa_experimental_supplement.cypher  (run via `drydocs apply-sosa-supplement`)
```

> Note: step 6's `:CAN_ACT_AS` role edges MATCH the Control-M anchors from step 3, so apply it
> after the backbone exists. On a graph without the backbone it lands the self-contained terms
> but silently no-ops the role wiring (re-run after bootstrap — idempotent).
