# DryDocs — Port Guide (producer `ce-wilson/DryDocs` → `<company-org>/DryDocs`)

> **This repo is version 1: a structural rewrite of the original DryDocs, not an increment on it.**
> It re-founds the project on the four-layer model (taxonomy → ontology → knowledge
> graph → context graph) with a clean external/internal split, a configuration layer,
> and an SME guided gate — see [`CLAUDE.md`](CLAUDE.md) and [`docs/restructure/`](docs/restructure/).
> The earlier off-track producer was archived as `ce-wilson/DryDocs-v0-archive` (read-only,
> dead history) and the v1 rewrite was renamed into its place. Throughout this guide,
> "producer" means `ce-wilson/DryDocs` (github.com).

> **Machine-readable dispositions: [`PORT-MANIFEST.yaml`](PORT-MANIFEST.yaml) is the
> AUTHORITY** for how each path resolves on collision (first match wins; guarded by
> `tests/unit/test_port_manifest.py`). This guide and `docs/port/port-prompt.md` are the
> narrative around it — when they disagree, the manifest wins and the prose is stale.

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
  `docs/history/genesis/` design trail (moved from `SDLC-Docs/extracted/` on 2026-09-02, ADR 0018 Q3). All **clean-adds** — take FROM this repo. ADR 0002 foretells a
  structural `drydocs/ → drydocs-core` move (Phase B, **EXECUTED 2026-07-10** — thin variant per
  ADR **0002-a-1**: core is physically `drydocs_core/`, the remainder KEEPS the `drydocs` name; see the
  dedicated section below). (ADR **0002-c** — depgraph-lineage re-home — is a newer clean-add in the same set.)
- **`drydocs-review` back-flow (NEW — REVERSE direction)** — the company-authored SME/HITL toolkit,
  reproduced here generically. **Canonical-COMPANY on collision** — keep your version. See the dedicated
  "`drydocs-review` — back-flow stream" section below.
- **`drydocs-plan` project board (NEW — Epic I)** — `drydocs/plan/plan_board.py` + `scripts/render_board.py`
  render `backlog.yaml` (now **schema v2**) into `docs/plan/board.html`; plus the `groom-backlog` skill and
  a new `tests/unit/test_backlog.py` schema guard. All **clean-adds** — take FROM this repo. `plan_board`
  is its own `plan` component group in the boundary guard (imports core only).
- **`drydocs-docmeta` document ingestion (P0 CORPUS LOAD SHIPPED; rest PLANNED).** A document-
  ingestion component (vendor docs + internal guidance + SME context → `drydocs_docs` /
  `drydocs_context`) planned in
  [`knowledge/upgrade-plans/docmeta-component.md`](knowledge/upgrade-plans/docmeta-component.md).
  **Its first increment has now shipped:** the **bmc-docs lexical loader** (P0) — the converted BMC
  docs corpus as a deterministic `Document`→`Chunk` graph, gate-accepted 13/13 and loaded live
  producer-side (see the "Newer streams" bullet below + `docs/port/port-prompt.md` step 22). The rest is
  still a **mixed** stream: pipeline/registry/tests are clean-adds; the working Confluence connector
  wiring is **Canonical-COMPANY** (same rule as `drydocs-review`); and the company side must
  **supplement** vendor fetches blocked producer-side (documents.bmc.com 403), T4 connector
  credentials (Graph API, mailbox, Toby), and the multi-DB Neo4j target — **G7 is now done
  producer-side** (Aura dropped 2026-07-06; the `neo4j:5.26-enterprise-ubi10` container IS the
  producer target), but the **company-side live multi-DB deploy remains a port concern**. Full
  disposition table + two-track acceptance oracle: plan §6.
- **`seal_app_ref` attribution (Epic K) — back-flow-origin, check before taking wholesale.** Additive
  `status: planned`/`proposed` entries in `drydocs_core/ontology/relationship_vocabulary/` (the S5 fragment directory) +
  `config/taxonomy-ontology-map/` (both normally Canonical-here; both were single files when this was written). It was **groomed from company
  reconciliation** — the concept came FROM you. While `planned`/`proposed` it is inert (no graph impact),
  so taking the producer files is safe. **But if company `main` has already promoted `m3_seal_app_ref` to
  `active`/`confirmed` (or has a live loader), that entry is a back-flow COLLISION — keep your active
  version, do not downgrade it to the producer's `planned` state.** Reconcile that entry per-item, not by
  blindly overwriting the file.
- **SEAL entity reshape + scraped-docs source-of-record — SIGNED OFF 2026-07-10 (K3), APPLIED at K4
  2026-07-15 (port-prompt step 35). TAKE AS APPLIED:** the `:Application` → `:BusinessApplication`
  label + `prov:Entity`/`dprod:DataProduct` reclass, the TOMRole qualified-attribution pattern
  (revised 7-role scheme), the three `seal_*` membership deprecations (gate-authorized — the
  vocabulary per-entry never-downgrade rule does NOT apply to them), the `arch_develops` →
  `WAS_ATTRIBUTED_TO {role: developed_by}` flip (+ migration cypher), `seal_had_primary_source`
  edge-active, and the `seal-pat-source-of-record` precedence authority. Only
  `seal-doc-source-of-record` stays confirmed-not-applied (docmeta loader pending) and the K1/K2
  edge reshape stays deferred (§F rider). The paragraph below is the ORIGINAL 2026-07-08 proposal,
  kept as history: Two linked decisions the `drydocs-docmeta` scrape drives —
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
- **Newer streams (2026-07 — index only; the actionable per-path steps live in
  [`docs/port/port-prompt.md`](docs/port/port-prompt.md)).** These shipped after the streams narrated above and are
  not all expanded into tables here; the port-prompt step number is the authority for each:
    - **Software registry** (plan-07 / ADR 0004) — `config/taxonomy/software-registry.yaml` + loader +
      supplement + `load-software-registry`/`apply-registry-supplement` CLI + vocab `reg_made_by`/
      `reg_uses_software`; clean-adds. ONE company-side rename of the back-flow seed twins
      (`vendor-bmc-*` → `bmc-docs-*`). **Step 17.**
    - **Gate-page STANDARD + prepped gates** — generic `gate_pages.py` meta-card + provenance extension
      (Canonical-COMPANY mechanism), five `status: proposed` gate specs + crosswalks (none SME-confirmed),
      `gate-log.md` append-only union. **Step 18.**
    - **Control-M load-order contract + `:ControlMApplication`** — contractual ingest order + header-row
      APPLICATION → `:ControlMApplication` grouping node; Canonical-here Control-M loaders; a new
      `controlmapplication_name` constraint. **Step 19.**
    - **Design-doc pipeline — `drydocs-docgen` (Epic L)** — deterministic `.md`→HTML/print/PDF renderers,
      all clean-adds, not wired into `cli.py`; plus the **L6 paper-HITL loop** (print-margin anchors +
      `transcribe-doc-markup` skill; scans dir Internal). **Step 20.**
    - **Provenance audit envelope (doc 06 / M-series)** — Phase 1 (source audit envelope) **and** Phase 2
      (M1: `WAS_GENERATED_BY` **delta-only**, `row_checksum`) SHIPPED; Control-M loaders/cyphers +
      `base.py` are Canonical-here; `graph-tests/provenance-diet.yaml` is a back-flow seed; confidential
      source→column maps authored company-side only (one-way). **Steps 15 + 22.**
    - **Source-governance column ledger (doc 08 / N1)** — `drydocs/review/source_mappings.py` (pure config
      accessor, parked in the review boundary group) + `config/source-mappings/psgmgr.yaml` (`controlm-psgmgr.yaml` when this shipped);
      clean-adds, but the `MODULE_MAP.md` row + boundary-guard membership must travel. **Step 23.**
    - **bmc-docs lexical corpus — docmeta P0, SHIPPED & gate-accepted** — converted BMC docs →
      `Document`→`Chunk` lexical graph (`drydocs/loaders/bmc_docs.py` + cypher + `drydocs_core/models/docs.py`,
      `load-bmc-docs`), 4 `active` `docs_*` edges, +2 constraints. Generic loader = clean-add;
      `config/gate-prompts/bmc-docs-lexical-load.yaml` + `graph-tests/bmc-docs-lexical.yaml` are back-flow
      (Canonical-COMPANY); `gate-log.md` union. **Step 22.**
    - **Release / versioning (v0.3.0)** — `VERSIONING.md` + `CHANGELOG.md` clean-adds; the
      `pyproject.toml` version is the **producer's** cadence — **KEEP the company's version string** on
      collision, and the annotated `v0.3.0` tag does **not** cherry-pick. **Step 24.**
    - **`NODE_QUICK_REFERENCE.md` rehomed** — moved `docs/` → `knowledge/ontology/` (a delete+add rename
      across disjoint history; README + `docs/RELATIONSHIP_GUIDE.md` links repointed). The table in
      §"PAT Product Ontology" below now names the new path.

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
| `config/` | configuration layer: `precedence.yaml`, `source-registry.yaml`, `classification.yaml` (sensitivity axis), `taxonomy-ontology-map/`, `taxonomy/` (Control-M + BusinessApplication + LOB→Product→Team + Oracle-schema captured) | clean-add |
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
- **Backlog id allocation — the cross-repo convention (user decision 2026-07-20, after the first
  bundle-port reconcile):** company-side-only items take the reserved **DD-series** (`DD1`, `DD2`, …).
  The producer NEVER allocates DD ids; the company side NEVER allocates producer-style epic-letter
  ids. (Motivating incident: the 2026-07-20 reconcile re-added company-only items as `C10`/`K6`/`N3`,
  colliding with producer `C10`/`K6` shipped in the very next range — renumber those three to
  `DD1`–`DD3` at the next company session.) Ids are stable references: on any future collision the
  DD-series is the escape hatch — producer ids are never renumbered.
- **Port baseline after the 2026-07-20 history squash + bundle:** the producer squashed its history
  to `c5a84c3` "Initial import" AFTER cutting the `3ae9b08` bundle you already applied
  (your PORT-REPORT-bd7952f.md) — your main holds the complete pre-squash history. Every future
  port range is a cherry-pick of `c5a84c3..<producer-tip>`; `c5a84c3` itself is never ported (its
  tree equals `3ae9b08`'s). The step-by-step apply instructions for each range live in
  `docs/port/port-prompt.md` — the first post-bundle range starts at its step 37, whose precondition is
  the `DD1`–`DD3` renumber above.

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
| `docs/decisions/0001-*.md` | ADR 0001 — ontology base scope (PROV backbone) | clean-add |
| `docs/decisions/0002-*.md`, `0002-a-*.md`, `0002-b-*.md`, `0002-c-*.md` | ADR 0002 — component & database topology + core-extraction plan + spinoff-rebase checklist + depgraph-lineage re-home | clean-add |
| `MODULE_MAP.md` | the `drydocs-core` ↔ component boundary (authoritative) | clean-add |
| `tests/unit/test_module_boundary.py` | stdlib guard enforcing the boundary (Track-1 portable, no data) | clean-add |
| `docs/history/genesis/*.md` | design trail (feasibility, C+D adoption, issue-driven loop, modular plan) | clean-add |

**The structural path-move LANDED (ADR 0002 D3, Phase B — EXECUTED 2026-07-10, thin variant per
ADR 0002-a-1).** Core moved physically into `drydocs_core/` (models, adapters, controlm minus the
staging builder, ontology + vocabulary, schema `.cypher`, neo4j_client, config, precedence,
source_registry); the **remainder keeps the `drydocs` package name** (load / review / plan / docgen —
the per-component split is Phase C). Consequences for the NEXT port range:
- Expect the **rename wave**: across disjoint history git sees each move as delete+add (same as the
  `vendor/ → external/` rename above). Apply the renames, then apply content per disposition.
- **PORT-MANIFEST.yaml carries the current paths** (its rows were re-pathed with the move — the
  promised "path-column diff"); paths in this guide's older tables predate the relocate — where they
  disagree, the manifest wins.
- The port-frozen `oracle_adapter.py` and the per-entry `relationship_vocabulary.yaml` moved WITH
  core: apply the rename, keep your content (see their manifest notes).
- the former `controlm` staging module is now `drydocs/staging.py` (stays in the remainder; core's
  `controlm/__init__` no longer re-exports it — consumer code importing the staging builder from
  `drydocs.controlm` must repoint to `drydocs.staging`).
The boundary guard is **Track-1 portable** (pure stdlib, no sample data) — it now enforces
`drydocs_core` as the core prefix.

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
> - `drydocs/review/graph_review.py`, `drydocs/review/graph_verify.py`, `drydocs/review/review_labels.py`,
>   `drydocs/review/sme_notes.py`
> - `drydocs/review/gate_pages.py` (the HITL prompt-page generator) + any generated `pages/`
> - `drydocs/review/publishing/**`
> - `config/review-labels.yaml`, `config/gate-prompts/**`, `graph-tests/**` (seed backbone,
>   gate-prompt specs, acceptance suites — company's real ones win)

If you have `git fetch`ed and see the producer touch these, drop the incoming side and
keep `main`'s. This is the reverse of the Canonical-here rule — it protects your wired,
internal-data originals from being clobbered by the public template. (Mirrored in the
`reconcile-port` skill's divergence ledger and [`docs/port/port-prompt.md`](docs/port/port-prompt.md).)

**Boundary guard note:** the producer will also add a `review` `COMPONENT_GROUP` to
`tests/unit/test_module_boundary.py` + `MODULE_MAP.md`, and flip the guard to
**default-deny** (every module must classify into exactly one bucket, else the test
fails). That change is generic and Track-1 portable — take it FROM the producer; it is
what forces your company-only modules to be classified rather than silently unguarded.

**2026-07-07 update — three refinements to this stream** (details: port-prompt steps
17–18):

1. **Seed-file rename (ADR 0004):** the two `vendor-bmc-*` seed twins became
   `graph-tests/bmc-docs-smoke.yaml` and `config/gate-prompts/bmc-docs-example.yaml`
   (ids renamed too). The producer's generic tests now assert
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

---

## Where the rest of this guide went

The apply instructions that used to follow here — the commit range, the canonical-here /
clean-add / collision lists, the Control-M C3/C4 phase tables, the PAT ontology and SOSA
deltas, the bootstrap order — were the July 2026 port guide. They are superseded by
[`docs/port/port-prompt.md`](docs/port/port-prompt.md) (the rolling ledger and the
disposition-led apply section) and [`PORT-MANIFEST.yaml`](PORT-MANIFEST.yaml) (the rows), and
kept as a record at
[`docs/history/git-readme-port-guide-2026-07.md`](docs/history/git-readme-port-guide-2026-07.md).
This file is the WHY guide for the cross-repo model; the port-prompt is the HOW.
