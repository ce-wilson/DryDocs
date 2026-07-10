# IDEAS — the idea board (inbox)

Low-friction capture. Jot anything here from any surface — a "what if", a bug you spotted,
a doc that needs writing, a future source to ingest. **No schema required.** Messy is fine.

This is the **inbox**, not the backlog. Nothing here is committed to until it is *groomed*
into [`backlog.yaml`](backlog.yaml) with an id, owner agent, inputs, and an acceptance test.

## How this feeds the backlog

```
capture here (any surface)  ──groom──▶  backlog.yaml item  ──▶  agent pulls it
```

**Grooming ritual** (you, or an Opus `main` session, ~weekly): read this list top to bottom;
for each idea either (a) promote it to a `backlog.yaml` item, (b) merge it into an existing
item, or (c) drop it. Strike through or delete what's been groomed so the inbox stays short.

## Capture format (loose)

`- [tag] one line. (optional: why / where you saw it)`

Tags help grooming: `idea` · `bug` · `doc` · `source` (new data source) · `question` · `chore`.

## Inbox

<!-- add new ideas at the top -->

- 2026-07-09 — [idea] `:SchedulerKind` slated for **DEPRECATION → `:AisCapability` + `:AiTool`**
  (user 2026-07-09). Today SchedulerKind is a small placeholder vocab (ControlM/Autosys/Airflow,
  seeded `ontology.cypher` + the `scheduler_kind` constraint) with no `node_classifications` entry.
  The replacement classes are **not yet defined** — needs the SME to specify what `:AisCapability`
  and `:AiTool` represent and how the app batch port's `REQUIRES_SCHEDULER` re-targets them (one
  edge or two). Touches: the C6 `requires-scheduler` map entry (target provisional), F1/F2
  orchestrator crosswalks, `ontology.cypher` seeds + the `scheduler_kind` constraint, README.
  Ontology/node-meaning ⇒ HITL gate; groom into an item once the two classes are defined.
  Reconciliation placeholder created: `config/taxonomy/platforms.yaml` (status: placeholder).

- 2026-07-08 — [doc] **BRD outline (Epic L, deferred)** — the third canonical doc type after
  TDD (L1) and Runbook (L8). Parked, not promoted: the BRD is a work-in-progress upstream and
  the user flagged it as "definitely a later phase", so there is no stable outline to write an
  acceptance test against yet. When the BRD shape settles, promote as `docs/design/templates/
  brd.outline.yaml` (reuse the `drydocs.doc-outline.v1` schema + traceability spine) into Epic L.
  Seed from the corpus: `SDLC-Docs/BRD - Table of Contents.docx`, `business requirements document
  template 31.docx`, `Business Requirements Template - FULL CDI Version.docx`.
- 2026-07-06 — [idea] **`drydocs-docmeta` component plan written** — full plan in
  `knowledge/upgrade-plans/docmeta-component.md`: component boundary (new `docmeta`
  COMPONENT_GROUP, imports core only, CLI via entrypoint exemption), config
  `doc-source-registry.yaml` + test guard, `drydocs_docs` DB + composite delta, phases
  P0 (benchmark) → P7 (T4 connectors), Port A inventory (bkup scraper → producer:
  carry cleaner/tokenizer/manifest, adapt registry/confluence-interface, drop migrate),
  Port B git-readme §6 (clean-adds / Canonical-COMPANY connector wiring / company
  supplements: blocked vendor fetches, Graph-API creds, Enterprise multi-DB target).
  Heads-up bullet added to git-readme.md. Groom phases P1–P3 to backlog after the P0
  benchmark verdict; ADR 0004 is the P1 gate output. The four T1–T4 tier lines were folded
  INTO this sequenced plan (P0→P7) and moved to the audit trail (2026-07-09). P0's corpus
  load is already substantially executed: the bmc-docs lexical loader (Document→Chunk,
  llm-graph-builder pattern) shipped and gate `bmc-docs-lexical-load` was ACCEPTED 13/13,
  LOADED LIVE (commits 12423f4/24d6a4b) — the WRITTEN benchmark verdict (traversal vs
  manifest-routed markdown vs vector RAG) + ADR 0004 still remain before P1–P3 promote.
- 2026-07-03 — [chore] the local `neo4j-drydocs-ee` Docker container's password is literally the
  string `<password>` (copy-paste artifact at creation). Fine for sandbox; change it before
  anything less throwaway. (Found while wiring web/ + agents/ to it.)- 2026-07-03 — [question] LLM key strategy for the ADK agents (core_ingest, controlm_fix):
  GOOGLE_API_KEY (Gemini) vs routing to Anthropic via LiteLLM; company side is Fusion SmartSDK
  on ADK, so Gemini-shaped is the safer default.
- 2026-07-03 — [chore] `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.- [idea] cli.py regroup: split the 937-line flat command list into domain subcommand groups
  (schema/ingest/verify/variables) — NOT milestone names; rename m1-verify/m3-verify →
  verify-reference/verify-controlm with deprecation aliases at the v1.0 window. (same review)
- [idea] Integration tests: testcontainers[neo4j] is already a dev dep but unused — one end-to-end
  CSV→Neo4j load test would cover the untested Cypher-execution path. (same review; verified
  unused + kept parked in the 2026-07-09 groom.)

## Recently groomed (audit trail)

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-09 groom run (Opus session) — 4 promoted / 1 retired; web/ became a plan change:
  - [chore] repo `.venv` has no pytest / poetry not on PATH → **RETIRED (resolved this session)**:
    pipx + Poetry 2.4.1 installed, in-project `.venv`, dev deps synced; `poetry run pytest -q`
    → 453 passed / 3 skipped. The documented gate now runs. (See memory `drydocs-python-toolchain`.)
  - [doc] `run-drydocs/SKILL.md` stale Gotchas → **J4** (Epic J, phase 8). Verified 2026-07-09:
    still claims "PyYAML not installed" (×2), "159 pass", Aura, and `apply-m3-supplement` — all stale.
  - [chore] CI (GitHub Actions gates + classification publish-boundary guard) → **J5** (user
    confirmed promote 2026-07-09).
  - [chore] unused deps → **J6** (Epic J), **scoped after verification**: only `streamlit` +
    `streamlit-agraph` are dead; `pandas` is intentional (`csv_adapter.py`) and `pypdf` is now used
    (`scripts/ingest_jpmc_reports.py`) — the original note's "imported nowhere" claim corrected.
  - [idea] web/ front end → **O1** + NEW module `drydocs-web` + NEW **phase 12 "Web console /
    graph visualization"** (plan change, user-approved). Marked in_progress — design pass in flight
    (branches `feature/ui-dark-landing-myapps` + `feat/web-console-design-pass`, untracked `UI-WIP/`).
  - Kept parked: BRD outline (later phase), `drydocs-docmeta` plan (gated on the P0 benchmark verdict
    + ADR 0004), the `<password>` EE container (deferred), LLM-key strategy (open question), `common/`
    in `/list-apps` (cosmetic), cli.py regroup (gated on the v1.0 rename window), and the testcontainers
    integration test (testcontainers[neo4j] confirmed unused; not selected this run).

- 2026-07-09 — [chore] Versioning reset (parked since 2026-07-01) → **J3** (Epic J, phase 8),
  executed same day: adopted SemVer (VERSIONING.md), bumped pyproject 0.1.0 → 0.3.0, back-filled
  CHANGELOG.md from the completed epics, cut annotated tag **v0.3.0** (user decision over v0.2.0 —
  matches plan phase 8's `release:` field). Sibling parked lines (CI, cli.py regroup, unused-dep
  removal, integration tests) stay in the inbox.

- 2026-07-09 groom run (this session) — weekly inbox groom, 2 promoted / 5 retired / 2 kept-updated:
  - [doc] README still says `:DEPENDS_ON` for the derived job→job edge → **J2** (Epic J, phase 8).
    VERIFIED 2026-07-09: the loader `controlm_dependencies_derived.cypher` MERGEs `:WAS_INFORMED_BY`
    and vocab `m3_was_informed_by` is active ("Replaces DEPENDS_ON") — README is the stale side
    (4 refs: README.md:16,139,152,231). Naming-drift doc hygiene, same class as J1.
  - [idea] `REQUIRES_SCHEDULER` (:BatchProcessing → :SchedulerKind) unregistered → **C6** (Epic C,
    phase 2 — re-opened). VERIFIED 2026-07-09 still absent from `relationship_vocabulary.yaml`;
    register `status: planned` + HITL gate before wiring the post-load step (edge-meaning ⇒ gate).
  - [idea] **T1** vendor-doc KG traversal benchmark → SUPERSEDED by the `drydocs-docmeta` plan (its
    P0 spike) AND substantially executed: the bmc-docs lexical loader (Document→Chunk,
    llm-graph-builder) shipped + gate `bmc-docs-lexical-load` ACCEPTED 13/13, LOADED LIVE (commits
    `12423f4`/`24d6a4b`). Written benchmark verdict + ADR 0004 still pending before P1–P3 promote.
  - [source] **T2/T3/T4** internal-platform / product-process / SME-context ingestion → ABSORBED into
    the `drydocs-docmeta` sequenced plan (`knowledge/upgrade-plans/docmeta-component.md`, phases
    P0→P7); tracked there until the P0 verdict + ADR 0004 gate, per the docmeta note's own instruction.
  - [bug] `node_classifications` ControlMFolder-vs-`:JobFolder` drift → CLOSED (already RESOLVED
    2026-07-05, ADR 0003 + rename migration); the struck line is retired from the inbox.
  - kept + updated in-inbox: the `drydocs-docmeta` plan note (records the bmc-docs load; T1–T4 folded)
    and the web/ front-end note (flagged the now-active design-pass branches). Parked pending user
    decisions (semver start, CI, cli.py regroup, unused-dep removal, integration tests), open
    questions (LLM key strategy), and piggyback chores stay in the inbox.

- 2026-07-08 groom run (this session) — **new phase 11 "Source governance ledgers"** + 9 items:
  - [question] SEAL ontology reshape + scraped-docs source-of-record → **K3** (gate session;
    K2 gains `depends_on: K3` — the wasAssociatedWith/Entity type conflict means the reshape
    gate runs before the match-policy gate is ticked). Prep was already on main (`0986d6d`).
  - [bug] design-doc HTML Chrome-vs-Brave render discrepancy → **L9**.
  - [idea] provenance diet + source audit fields (2026-07-05) → **M1–M3** (doc-06 Phases 2–5;
    Phases 0–1 shipped 2026-07-07 pre-groom via gate `controlm-q1q3-phase1` + commit `62673ed`).
  - [idea] property-level ontology terms for the audit envelope (2026-07-07) → **M4**.
  - [question] same-row-derived node relationships (city/state/country, 2026-07-07) → **C5**
    (re-opens phase 2 — methodology gap).
  - [idea] source column mappings (doc 08, 2026-07-07) → **N1–N2** (Phases 0–1 per the plan's
    own groom note; later phases stay in the plan doc).
  - [idea] TechStack software registry (2026-07-07) → CLOSED, executed directly as plan-07
    (Phases 0–2 done `caa1e79`/`eb0fe56`; Phase 3 at the software-usage-patterns gate; Phase 4
    deferred). Not backlog-itemized — the plan doc tracks it; itemize the P3 build when its
    gate passes.
  - [idea] "Application contains folders" support view (2026-07-01 review) → SUPERSEDED by the
    gate-confirmed header-row design (`controlm-q1q3-phase1` + `107581d`): ControlMApplication
    + CONTAINS_FOLDER now load in the folder pass from CM_DEF_VJOB JOB_ID=1 — NOT derived from
    per-job APPLICATION reconciliation as the line proposed (that column stays informational).

- 2026-07-08 — Epic L (**documentation infrastructure**, new phase 10) groomed into `backlog.yaml`
  from the deterministic-documentation design conversation. Canonical per-doc-type outlines (stable
  anchors = the render/traceability/HITL id namespace), md-as-source deterministic render, and the
  digital + pen/paper markup loop. `tdd.outline.yaml` drafted same day (L1 in_progress). New module
  `drydocs-docgen`. Sequence (user-set): TDD (L1) → render/feedback (L3–L7) → Runbook (L8, capstone);
  runbook resequenced from L2 → L8. BRD parked above (later phase). Distinct from the
  `drydocs-docmeta` ingestion idea (2026-07-06).
- 2026-07-01 — [source] seal_app_ref attribution → **K1 + K2** (Epic K, phase 9). CORRECTED
  during grooming by the company reconciliation answers: the edge is spec-level on BOTH sides
  (their FR-NS-013/UC-NS-005 docs read ACTIVE with no loader/vocab/gate behind them); the feed
  is STG_APP_FACT semantic facts, NOT job.APPLICATION (explicitly unreliable for SEAL identity).
  Promoted as build items with the company's write shape, gate sequence, and verify shapes.
- 2026-07-01 — [chore] fragment cleanup (naming drift, banners, SDLC-Docs README) → **J1**
  (Epic J, release-infrastructure) via the groom-backlog skill's demonstration run. Sibling
  lines (versioning reset, CI, cli regroup, unused deps, integration tests) stay in the inbox
  pending user decisions (semver start version, rename window).
- 2026-07-01 — Epic I (I1–I4, project board & planning infrastructure) groomed into `backlog.yaml`
  from the architecture-review plan; schema upgraded to `drydocs.backlog.v2` (I1 done same day).
- 2026-06-20 — initial backlog A1–F2 seeded directly into `backlog.yaml` from `02-backlog.md`.
- 2026-07-09 — [idea] **Port-boundary tech-debt audit written** (`docs/reviews/tech-debt-port-boundary.md`,
  /tech-debt run): the publisher→consumer break points CAN be segregated — six break classes
  (A reverse-direction Canonical-COMPANY, B per-entry, C integration hand-merges, D env/wiring,
  E gitignored assets, F rename waves) + the meta-debt (dispositions are prose-only across
  git-readme/port-prompt/reconcile-port, no guard). Groom: (1) PORT-MANIFEST.yaml +
  test_port_manifest (priority 40 — MUST land BEFORE ADR 0002 Phase B rename wave);
  (2) per-entry reconciler guards (status-downgrade, gate-log append-only); (3) Class-A
  connector/overlay physical split (do with Phase B).
