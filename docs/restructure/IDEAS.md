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

- 2026-07-09 — [idea] **Control-M Workbench as the remediation greenfield test bed — PARKED**
  (user call, 2026-07-09). The Workbench Docker image (dev Control-M, plain `docker run`, no
  Kubernetes/Helm) would let fix packages be DEPLOYED + EXECUTED against a disposable env
  before the Jira handoff — stronger than the offline equivalence proof, still SoD-safe.
  Blocked here: image lives on distribution.bmc.com (not Docker Hub; pull attempt 401) and
  needs an EPD-entitled account + identity token — an entitlement/machine-boundary question,
  not a technical one. Ports 8443/7005 verified free on this box. Revisit when OQ-1 closes
  company-side or entitlement is resolved. Refs: `controlm-api-installation.md` (corpus,
  §Workbench + SYNTHESIZED notes), `drydocs-remediation-tdd.md` §HITL OQ-1. (Control-M for
  Kubernetes / Helm-chart offering deliberately SKIPPED — different product, agents-in-K8s,
  no current use case.)
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

- 2026-07-09 — [idea] design-doc feedback: per-subsection annotate controls when a section
  has >2 subsections (1.a/1.b/1.c… or steps 1/2/3) so feedback keys to the exact subsection
  → **L11**. (chat note, same review pass as L10; design core = stable derived sub-anchors)
- 2026-07-09 — [idea] design-doc feedback widget: appendix "SME - Feedback" panel (divider +
  static HITL how-to: annotate, Copy feedback, create docs/design/feedback/<doc>-rev<N>.yaml,
  paste, save) → **L10** (amended same day: instruction block, not a free-text notes field).
  (chat note after reviewing docs/design/feedback/scans/; answered the open question — the
  export is .yaml per feedback_yaml, not markdown)

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
- 2026-07-09 — **CM_HOSTS host topology** prepped to the gate via the NEW `add-source-object`
  skill (the "add an object to an existing source" walkthrough — profile → ledger → ontology →
  gate → extract). Artifacts: `sql/controlm_hosts.sql` + `sql/adhoc/profile_cm_hosts.sql`,
  ledger object CM_HOSTS (staging-only), vocab `m3_runs_on_host_group` /
  `m3_host_group_contains_host` / `m3_host_group_defined_on` (planned), gate
  `config/gate-prompts/controlm-hosts-topology.yaml` (AWAITING SME). Groom: (1) the gate
  session; (2) the hosts loader + RUNS_ON resolution pass build (blocked on the gate);
  (3) the **maintenance-window use case** — host → jobs → avg folder start/end quiet-window
  query; depends on the temporal runtime supplement (cm_avg_run) which should be promoted
  from PLANNED. Also new: `locator:` block on source-registry entries (SEAL app → platform →
  service → schema → mapping); real SEAL/service values = internal/ twin.
