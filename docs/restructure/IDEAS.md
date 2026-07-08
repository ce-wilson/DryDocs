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

- 2026-07-08 — [question] **SEAL ontology reshape + scraped-docs source-of-record (GATE-BOUND).**
  `:Application` is mis-typed `prov:SoftwareAgent` but also carries `dprod` ports (Entity),
  `org:Membership→org:Role` (Organization), and K1/K2 `wasAssociatedWith` (Agent) — 3 incompatible
  types. Reshape: `:Application` → **`prov:Entity`/`dprod:DataProduct`**; its Technical-Operating-Model
  governance roles (CTO / application-owner / information-owner / data-owner / operate-manager /
  risk-compliance — DISTINCT from the PAT product org) → **`prov:qualifiedAttribution`+`prov:hadRole`**
  (Role = shared skos vocab), NOT `org:Membership` (keep `org:` for the PAT hierarchy only); deprecate
  `seal_has_membership`/`seal_of_role`/`seal_held_by`, keep `seal_has_port`. Scraped SEAL/PAT pages =
  source of record via `config/precedence.yaml` authority + **`prov:hadPrimarySource`** on extracted
  facts (Entity→Entity — the reason the app record must be an Entity); pages land as `Document` entities
  in `drydocs_context` (VERBATIM/GROUNDED/SYNTHESIZED trust). K1/K2 job→app needs re-shaping (needs Agent
  today, still `proposed`). Route: `ontology-mapper` → HITL gate; register hadPrimarySource / wasAttributedTo
  / qualifiedAttribution(+hadRole) + TOM Role vocab as `planned`, flip the `:Application` node class, re-open
  K2, log `gate-log.md`. Full write-ups: `knowledge/upgrade-plans/docmeta-component.md` + `git-readme.md`.
- 2026-07-08 — [bug] **Design-doc HTML render — Chrome vs Brave.** Chrome did NOT render the
  L3 output as a full page; **Brave (latest — brave.com/latest) rendered it correctly**. Seen on
  `docs/design/controlm-ingestion-tdd.html`. Investigate the Chrome discrepancy (likely a CSS /
  print-view / `file://` quirk, not the markup — anchors + tables validated fine). Brave is the
  reference VIEWER; L4's headless PDF uses **Edge/Chrome** — Brave's background services HANG
  headless `--print-to-pdf` on this box (confirmed 2026-07-08, 2× 180s timeouts; Edge rendered in
  3.5s). Same Chromium print engine, so the PDF layout is identical. Still: confirm the screen
  `.html` renders full-page in Chrome, or adjust the screen CSS.
- 2026-07-08 — [doc] **BRD outline (Epic L, deferred)** — the third canonical doc type after
  TDD (L1) and Runbook (L8). Parked, not promoted: the BRD is a work-in-progress upstream and
  the user flagged it as "definitely a later phase", so there is no stable outline to write an
  acceptance test against yet. When the BRD shape settles, promote as `docs/design/templates/
  brd.outline.yaml` (reuse the `drydocs.doc-outline.v1` schema + traceability spine) into Epic L.
  Seed from the corpus: `SDLC-Docs/BRD - Table of Contents.docx`, `business requirements document
  template 31.docx`, `Business Requirements Template - FULL CDI Version.docx`.
- 2026-07-07 — [idea] **Property-level ontology terms for the audit envelope**: the four
  envelope props (audit-fields.yaml) deserve standard-term bindings — dct:creator/dct:created/
  dct:modified (Dublin Core) or PROV qualified attribution (prov:wasAttributedTo +
  prov:generatedAtTime). relationship_vocabulary.yaml covers EDGES only; decide whether
  property-term bindings get their own registry or a vocabulary-file section (SOSA is NOT the
  home — the envelope is authorship provenance, not observation). Route via ontology-mapper.
- 2026-07-07 — [question] **Same-row-derived node relationships** (city/state/country
  pattern): when ONE source row fans out into multiple nodes at different hierarchy
  grains, check what relationships (if any) belong BETWEEN those derived nodes — not
  just from each back to the row's entity. Live case: a CM_DEF_VTAB row (+ header join)
  now yields folder + ControlMServer + ControlMApplication; folder connects to both
  (SCHEDULED_ON / CONTAINS_FOLDER), but should app↔server relate directly, or only
  through the folder (risk: fan-out edges that restate a join)? Generic rule wanted for
  the ontology layer (chain the hierarchy city→state→country vs star-to-entity), then
  verify existing loaders against it. Route through ontology-mapper + the HITL gate;
  candidate m3-verify/graph-tests invariant once decided.
- 2026-07-07 — [idea] **Source column mappings** (per-source column ledger): every source is a
  wide table used narrowly (CM_DEF_VJOB 100+ cols → ~26 projected; HR roster → SID/location/
  cost-center subset) and the used/excluded/why record is scattered (SQL headers, 06a, gate
  provenance). Plan: `08-source-column-mappings.md` — `config/source-mappings/<source-id>.yaml`
  keyed to source-registry (gains a `mapping:` pointer), dispositions
  projected/filter-only/excluded/deferred with origin source|derived reused from gate pages,
  coverage test vs db-skill profile census, SQL SELECT-list drift guard, ccb- twin for
  confidential censuses. ODCS v3 vocabulary-compatible, no dependency. Groom Phase 0–1 to
  backlog when ready.
- 2026-07-07 — [idea] Third-party software registry ("TechStack"): Vendor → SoftwareProduct →
  `(:Application)-[:USES_SOFTWARE {version}]->()` — answers "which apps use Ab Initio / Oracle 19"
  and gives Oracle/Neo4j the classification BMC already has. Kills the `vendor-bmc` tooling id
  (→ `bmc-docs`) and reduces "vendor" to one meaning (brand). Modeled on the internal software
  library's Vendor/Product/status/version-status shape; Phase 3 derives edges from CMD_LINE via
  the command parser (`APPL_TYPE` = dead-end per SME — Ab Initio/Informatica run as OS cmds,
  job types under-used). Plan: `07-software-registry.md`. Phase 0 = ADR 0004 + vocab gate.
- 2026-07-06 — [idea] **`drydocs-docmeta` component plan written** — full plan in
  `knowledge/upgrade-plans/docmeta-component.md`: component boundary (new `docmeta`
  COMPONENT_GROUP, imports core only, CLI via entrypoint exemption), config
  `doc-source-registry.yaml` + test guard, `drydocs_docs` DB + composite delta, phases
  P0 (benchmark) → P7 (T4 connectors), Port A inventory (bkup scraper → producer:
  carry cleaner/tokenizer/manifest, adapt registry/confluence-interface, drop migrate),
  Port B git-readme §6 (clean-adds / Canonical-COMPANY connector wiring / company
  supplements: blocked vendor fetches, Graph-API creds, Enterprise multi-DB target).
  Heads-up bullet added to git-readme.md. Groom phases P1–P3 to backlog after the P0
  benchmark verdict; ADR 0004 is the P1 gate output. Supersedes/absorbs the four
  T1–T4 lines below into a sequenced plan.
- 2026-07-06 — [idea] **T1 — vendor-doc KG traversal benchmark:** load ONE external vendor
  corpus (BMC Control-M — manifest + trust tiers already exist) into a local, throwaway
  Document→Chunk→Entity Neo4j graph (patterns from the mirrored `llm-graph-builder`; the
  graphrag upgrade plan's "no documents to chunk" skip is obsolete for this corpus). Benchmark
  agent retrieval — graph traversal vs manifest-routed markdown reading vs plain vector RAG —
  on a fixed support-question set (accuracy / latency / tokens). Only SYNTHESIZED-labeled
  chunks may carry inference; VERBATIM/GROUNDED cite the source URL. Outcome decides how big
  the doc-ingestion module gets. (Full review: `docs/reviews/doc-knowledge-ingestion-review.md`.)
- 2026-07-06 — [source] **T2 — internal platform guidance ingestion:** bring
  `knowledge/standards/{technology,business,data}/` into the software KG through the curation
  gate (SME-confirmed only). Frontmatter already binds each standard to `taxonomy_path` /
  `governs` / `applies_to_source` — those become the graph link keys. (same review)
- 2026-07-06 — [source] **T3 — internal product/agile/software guidance:** `docs/Product/`,
  SDLC docs, and the unmanaged root-level strays (PDFs/images) — classify, manifest, then
  ingest via the same pipeline. Prereq: a doc-source registry (documents get the
  `source-registry.yaml` treatment: classification + connector + trust default + `refresh:`
  policy, test-enforced); port the DryDocs-bkup scraper provenance machinery (sha256,
  token-count, curation_status ladder) into a single `drydocs-docmeta` component — one module
  for external AND internal, split lives in config not code. (same review)
- 2026-07-06 — [source] **T4 — SME business-application context:** Confluence (bkup scraper
  exists) → SharePoint/Teams (Graph API) → email connectors, landing in the EXISTING
  `drydocs_context` DB (Internal-Confidential, unverified-by-default, survives core rebuilds;
  promotion via the G5 gate path). Raw content stays `internal/`/gitignored; cross-link to
  business applications via the G1 proxy-node keys. Software KG target = new `drydocs_docs`
  DB in the composite (local now; live rides G7). (same review)
- 2026-07-05 — [idea] Provenance diet + source audit fields: Oracle-loaded Control-M shows
  generated-by/run-timestamp edges outnumbering the true domain relationships (full-refresh
  `WAS_GENERATED_BY` → `:JobRun` supernode, persona review Issue 3). Rework the time series to
  carry *changes to the record*: pull tracking becomes node properties (`last_seen_at`/
  `last_run_id`), source authorship becomes a standard envelope (job created by/at + last
  updated by/at from CM_ `CREATION_USER`/`CHANGE_USERID` etc.), edges only on actual change.
  Each source declares its own audit-field mapping — needs HITL per dataset. Big change;
  scope/approach/phases planned in `06-provenance-source-audit-fields.md`. Groom to backlog
  when ready; Phase 0 is a gate session.
- 2026-07-03 — [chore] the local `neo4j-drydocs-ee` Docker container's password is literally the
  string `<password>` (copy-paste artifact at creation). Fine for sandbox; change it before
  anything less throwaway. (Found while wiring web/ + agents/ to it.)
- 2026-07-03 — [idea] web/ front end shipped as a throwaway test page (no design pass). Needs:
  plan/wireframes, a real C4 rendering (NVL?), and a decision on whether the basic Cypher flow
  keeps talking bolt-from-browser or goes through a thin API.
- 2026-07-03 — [question] LLM key strategy for the ADK agents (core_ingest, controlm_fix):
  GOOGLE_API_KEY (Gemini) vs routing to Anthropic via LiteLLM; company side is Fusion SmartSDK
  on ADK, so Gemini-shaped is the safer default.
- 2026-07-03 — [chore] `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.
- 2026-07-03 — [chore] repo `.venv` has no pytest (and poetry isn't on PATH in plain PowerShell)
  — the `poetry run pytest -q` gate can't run as documented on this machine; reinstall dev deps.

- ~~[bug] node_classifications says label ControlMFolder but every loader/edge writes :JobFolder
  (controlm_folders.cypher MERGEs JobFolder:Collection; edge entries say from_node: JobFolder) —
  same drift visible in the company copy. Decide the winning name via the gate, then fix the
  losing side everywhere. (same screenshots)~~ RESOLVED 2026-07-05: `ControlMFolder` won
  (ADR 0003); repo-wide rename + `drydocs/migrations/20260705_rename_jobfolder_to_controlmfolder.cypher`.
- [doc] README.md still says :DEPENDS_ON for the derived job->job edge; the loader + m3-verify
  write :WAS_INFORMED_BY (vocab m3_was_informed_by; DEPENDS_ON retired). Reconcile the README.
  (2026-07-01 Control-M naming review with SME)
- [idea] REQUIRES_SCHEDULER (:BatchProcessing -> :SchedulerKind) appears in README/plans but is
  NOT registered in relationship_vocabulary.yaml — register status: planned + gate before wiring
  the post-load step. (same review)
- [idea] "Application contains folders" support view (SME's mental model): derive
  Folder -> :BatchProcessing from job.APPLICATION reconciliation + the folder-naming resolver;
  SME-gated DERIVED edge, never base ingest (BMC puts APPLICATION on the job; folders can hold
  mixed applications). (same review)
- [chore] Versioning reset: adopt semver policy (VERSIONING.md), cut first tag (v0.2.0 or v0.3.0
  with the board), start CHANGELOG.md back-filled from completed epics. (2026-07-01 architecture review)
- [chore] CI: GitHub Actions running the CLAUDE.md gates (pytest -q, import drydocs.cli,
  drydocs --help, ruff) on every push; classification test as publish-boundary guard. (same review)
- [doc] .claude/skills/run-drydocs/SKILL.md Gotchas are stale: PyYAML IS a runtime dep since D2
  (the "4 skipped tests / PyYAML not installed" notes are outdated), and test counts have moved.
  Refresh next time the skill is touched. (noticed 2026-07-01 while authoring groom-backlog)
- [idea] cli.py regroup: split the 937-line flat command list into domain subcommand groups
  (schema/ingest/verify/variables) — NOT milestone names; rename m1-verify/m3-verify →
  verify-reference/verify-controlm with deprecation aliases at the v1.0 window. (same review)
- [chore] Remove unused deps: pandas, streamlit, streamlit-agraph (runtime), pypdf (dev) — declared
  in pyproject.toml, imported nowhere; ~100MB install weight. (same review)
- [idea] Integration tests: testcontainers[neo4j] is already a dev dep but unused — one end-to-end
  CSV→Neo4j load test would cover the untested Cypher-execution path. (same review)

## Recently groomed (audit trail)

<!-- when you promote an idea, move its line here with the resulting backlog id -->

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
