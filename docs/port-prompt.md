# Port prompt — apply DryDocs onto the original `<company-org>/DryDocs` base

Hand this prompt to an agent working in a clean checkout of the company
`<company-org>/DryDocs` `main` (GitHub Enterprise). It executes the one-way
producer→consumer port described in [`git-readme.md`](../git-readme.md). Since 2026-07-09
the per-path dispositions are machine-readable in [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml)
(repo root) — the manifest is the WHAT (mechanical, first-matching-glob-row-wins);
`git-readme.md` stays the narrative authority (the WHY); this prompt is the actionable
wrapper whose numbered steps carry sequencing + context, not disposition authority.

```text
You are porting the DryDocs PRODUCER repo (ce-wilson/DryDocs, github.com) onto the
original/superseded <company-org>/DryDocs base (GitHub Enterprise). This is a ONE-WAY
producer→consumer apply. Work in a clean checkout of company `main`.

AUTHORITATIVE INSTRUCTIONS: the producer carries its own port guide at `git-readme.md`
(repo root) AND the machine-readable `PORT-MANIFEST.yaml` (repo root, schema
drydocs.port-manifest.v1 — see step 25). For WHAT to do with a path, the manifest is the
authority: first row whose glob matches the path wins, top-down; unmatched paths take its
default (clean-add if absent consumer-side, evaluate if both sides created it). For WHY
and the acceptance oracle, git-readme.md wins over this prompt. Fetch and internalize
BOTH before touching anything. Do not duplicate or improvise around them.

CRITICAL CAVEAT — DISJOINT HISTORIES. The producer was `git init`-ed fresh; there is NO
common ancestor with company main, so there is no 3-way merge base. This is a CHERRY-PICK
/ `git am --3way`, NOT `git merge`/`git pull`. A `merge=ours` gitattributes rule does NOT
help (it keeps the wrong side). Every path is either a clean-add (applies untouched) or a
collision (reconcile by hand, every time).

PROCEDURE:
1. From the company main checkout:
     git remote add cewilson https://github.com/ce-wilson/DryDocs.git
     git fetch cewilson main
2. READ THE GUIDES FIRST: `git show cewilson/main:git-readme.md` AND
   `git show cewilson/main:PORT-MANIFEST.yaml`. Internalize the manifest's disposition
   rows + the guide's three tables (Canonical-here, Clean-adds, Collisions) before
   touching anything.
3. git switch -c drydocs-port main
4. List the commit range (histories disjoint → all of it is new vs company main):
     git log --oneline --reverse cewilson/main
   Identify commits by SUBJECT, not SHA (a rebase rewrites SHAs). The Control-M
   normalization stream is the three subjects "…variable taxonomy (Phase A)…" →
   "…variable resolver (Phase B)…" → "…Phase C command/script parser…", applied in that
   order; everything else is additive docs + ontology + the v1 restructure.
5. Cherry-pick the range: git cherry-pick <oldest>^..<newest>   (or format-patch +
   `git am --3way`). Clean-adds apply silently; cherry-pick stops on each collision.
6. RESOLVE EACH COLLISION per git-readme.md:
   - Canonical-here (take the producer version WHOLESALE, do not hand-merge): the entire
     v1 restructure — CLAUDE.md, PUBLISH-BOUNDARY.md, reference/, external/orchestration/,
     config/, internal/, .claude/agents/, docs/restructure/; plus drydocs/controlm/,
     knowledge/standards/, the Control-M SQL loaders, relationship_vocabulary.yaml,
     catalog_ontology_supplement.cypher.
   - Integration points (PRE-EXIST on company main → WILL conflict, hand-merge preserving
     exactly the "what to preserve" column): drydocs/cli.py (gains `analyze-variables` +
     `normalize-variables` commands and `.controlm` imports; existing command bodies
     unchanged), drydocs/models/controlm.py, drydocs/models/__init__.py.
   - Then `git add <path>` and `git cherry-pick --continue`.
7. ONE RENAME: vendor/bmc-controlm/ → external/orchestration/bmc-controlm/. If company main
   still has vendor/bmc-controlm/, delete it after taking the new path (across disjoint
   history git sees the move as delete+add); references were already repointed producer-side.
8. SCHEMA CONSOLIDATION (constraints.cypher key corrections, deleted m1/m3_* patch files,
   `apply-m3-supplement`→`apply-ontology-supplement` rename): the company baseline may have
   fixed these differently — EVALUATE each against company main before applying, per
   git-readme's "Schema consolidation" section. Authoritative bootstrap order:
   constraints → ontology → ontology_supplement → seal_ontology_supplement →
   catalog_ontology_supplement.
9. ARCHITECTURE-DECISIONS STREAM + MODULAR SPLIT (all clean-adds): docs/decisions/ (ADR 0001
   ontology base; ADR 0002 component & database topology + 0002-a/0002-b), MODULE_MAP.md, and
   tests/unit/test_module_boundary.py apply untouched — see git-readme.md's "Architecture decisions
   + modular split" section. UPDATE (2026-07-10): the drydocs/ → drydocs-core move has now been
   EXECUTED (Phase B, thin variant per ADR 0002-a-1 — core is physically drydocs_core/, the
   remainder keeps the drydocs name). Ranges cut BEFORE 2026-07-10 target the flat layout; the
   relocate range arrives as a rename wave — PORT-MANIFEST.yaml carries the current paths and
   git-readme.md's "structural path-move LANDED" section carries the rename-wave rules.

10. BACK-FLOW STREAM — REVERSE DIRECTION (Canonical-COMPANY): the producer is
   reproducing the company-authored `drydocs-review` SME/HITL toolkit GENERICALLY as a
   public template (drydocs/graph_review.py, graph_verify.py, review_labels.py, sme_notes.py,
   gate_pages.py, drydocs/publishing/**, config/review-labels.yaml, config/gate-prompts/**,
   graph-tests/**). If the producer touches any of these, KEEP COMPANY'S VERSION — drop the incoming side. The
   producer copy is sanitized; yours holds the real Confluence wiring
   (toby_publish_confluence), real review-labels.yaml, and real SME[SID] data. This is
   the OPPOSITE of the Canonical-here rule. See git-readme.md "`drydocs-review` — back-flow
   stream". (The `review` COMPONENT_GROUP + default-deny flip in test_module_boundary.py
   IS taken FROM the producer — it is generic and forces your modules to be classified.)

11. ORACLE-KERBEROS-LOGIN MODULE (clean-add, with ONE company-side caveat):
   `libs/oracle_kerberos/**` (spider_login.py + __init__.py + README.md +
   oracle_kerberos_connection.sample.txt) and tests/unit/test_oracle_kerberos_login.py
   are a standalone Kerberos external-auth login for the Spider/PSGMGR schema. They apply
   UNTOUCHED — the module has no drydocs/ imports and does NOT touch the port-frozen
   drydocs/adapters/oracle_adapter.py. The .gitignore gains three protective rules
   (`libs/oracle_kerberos/oracle_kerberos_connection.txt`, `/internal-local/`, and the root
   `oracle-connection-*.png`/`raiidr-*.png`/`ss-*.png` screenshot globs) — MERGE these into
   company .gitignore additively (keep any company rules).
   CAVEAT: the producer copy is SANITIZED (placeholders only; the real filled config and
   consolidated notes live in the gitignored `internal-local/`, which never transfers). If
   company main already carries its own `libs/oracle_kerberos/` reproduced from the raiidr
   project (real hosts/SID/alias in a tracked file), treat it like the back-flow stream
   (step 10): KEEP COMPANY'S VERSION, drop the incoming sanitized side. Only clean-add when
   the path is absent company-side. Acceptance: `poetry run pytest
   tests/unit/test_oracle_kerberos_login.py -q` → 27 passed (no oracledb/network needed).

12. VENDOR ICON REGISTRY (clean-add): `drydocs-icons/**` — self-contained asset
   package (manifest.json as the single source of truth: id -> label/category/paths/
   brand hex/provenance/verified; vendors/{packaged,generic,external}; png/ rasters;
   SOURCE.md provenance + colour-status table; Plex-embedded index.html sheet).
   ~2.7MB of public vendor marks, classification External, no code imports — applies
   untouched, no collisions expected.

13. CONTROL-M AGENT SKILLS (clean-add): `.claude/skills/controlm-db/**` and
   `.claude/skills/controlm-runbook-automation/**` — two self-contained Claude Code
   skill bundles (each a SKILL.md plus a references/ folder, no code imports).
   `controlm-db` ingests and queries the CM_ replica (references: er-model,
   schema-crosswalk, ingest, query-cookbook); `controlm-runbook-automation` covers
   plan → fix-package → toolchain remediation. Both live under `.claude/skills/`,
   which the company base does not carry, so they apply UNTOUCHED — no collisions
   expected. (These merged to producer main from the feature/controlm-db-skill
   stream; they are independent of the step-12 icon bundle — either can be ported
   alone.)

14. CONTROL-M CHAIN — COMPANY-SIDE CHANGE TO PRESERVE (2026-07, see ADR 0003):
   ORACLE BIND RENDERER FIX (Canonical-COMPANY, back-flow rule): company commit
      "fix(oracle-adapter): don't treat :tokens in SQL comments/strings as binds"
      hardened `_render_sql` in the company `jdbc_oracle_adapter.py` to substitute
      binds ONLY in code regions (`--` and `/* */` comments, 'single-quoted strings',
      "quoted identifiers" copied verbatim). The producer does not carry this file —
      but do NOT "fix" the same bug by editing the producer's `.sql` files during
      conflict resolution: `:Application` / `:DEPENDS_ON` in comments and the
      `':depends_on'` literal in controlm_dependencies_recursive.sql (lines 62/124)
      are correct as-is and must survive the port byte-identical. If any incoming
      producer commit de-colonizes SQL comments, DROP that hunk (a producer-side
      attempt was made and reverted 2026-07-05; verify none leaks into the range).

15. PROVENANCE AUDIT-FIELDS + WAS_GENERATED_BY — PHASES 1-2 SHIPPED (2026-07; was plan-only).
    docs/restructure/06-provenance-source-audit-fields.md (SME-signed-off) ports as a doc.
    Phase 1 has now SHIPPED (commit subject "…source audit envelope") — the plan's "when it
    ships" list below is now REAL, apply it:
    - config/audit-fields.yaml (public, Canonical-here) = frozen envelope prop names
      (source_created_at/_by, source_updated_at/_by) + the full Control-M entry (BMC
      columns are publishable mechanism) + STUB entries for every other registry id.
    - Confidential source→column mappings (SEAL, catalog-pat, oracle-schemas — all
      Internal-Confidential) are authored COMPANY-SIDE ONLY in a gitignored internal
      twin the loader merges over the public file; they never flow back (one-way).
    - test_audit_fields.py (ships both sides) is the drift gate: every confirmed:true
      registry source MUST have an audit-fields entry, same id, envelope props only.
      On company main it stays RED until the stub is filled via 03-hitl-sme-flow.md —
      that red test IS the sync signal. Sequence producer-first.
    - PHASE 2 (M1, commit "…WAS_GENERATED_BY only on create/change") NOW SHIPPED — Canonical-here
      (Control-M loaders, step 6): drydocs/loaders/base.py computes a sha256 row_checksum in
      to_params (volatile fields excluded, key-order independent) and LoadSummary gains rows_changed;
      all four node-writing Control-M cyphers (controlm_folders/jobs/conditions_in/conditions_out.cypher)
      guard the WAS_GENERATED_BY tail with FOREACH-over-CASE on checksum change + SET n.row_checksum
      (DELTA-ONLY edges — kills the full-refresh :JobRun supernode); JobRun.rows_changed derived at
      _close_run. tests/unit/test_row_checksum.py is a clean-add; graph-tests/provenance-diet.yaml is a
      BACK-FLOW seed (Canonical-COMPANY, step 10 — keep yours on collision). The prov_was_generated_by
      vocab note is now delta-only semantics (note-only, no status change).

16. DOCMETA — DOCUMENT INGESTION (P0 CORPUS LOAD SHIPPED — see step 22; the rest PLAN ONLY; MIXED stream).
    P0 (corpus load) has SHIPPED as the bmc-docs lexical loader — apply it per STEP 22. The remaining
    docmeta docs still port as clean-adds, untouched: knowledge/upgrade-plans/docmeta-component.md,
    docs/reviews/doc-knowledge-ingestion-review.md, the git-readme.md heads-up bullet, and the
    IDEAS.md T1–T4 capture lines. When the rest of the component SHIPS (plan §6 becomes the authority):
    - Clean-adds: drydocs/docmeta/** (pipeline/registry/cleaner/tokenizer/manifest/chunker/
      curation/freshness + connector INTERFACES), config/doc-source-registry.yaml +
      tests/unit/test_doc_registry.py, the `docmeta` COMPONENT_GROUP in
      test_module_boundary.py + MODULE_MAP.md row, the drydocs_docs provisioning delta.
    - Canonical-COMPANY (back-flow rule, step 10 applies): your wired Confluence connector
      internals (toby/confluence.exe), real space keys/site ids, real curation_owner SIDs,
      any registry entries carrying internal coordinates. If your side still runs the old
      drydocs.scrapers package, keep your connector internals inside the producer's docmeta
      structure, then retire drydocs.scrapers once Track 1 is green.
    - COMPANY MUST SUPPLEMENT (cannot be built producer-side): vendor fetches blocked by
      bot-protection (documents.bmc.com 403 — complete the XML-definition acquisition stub
      from the company network or local .dtd files), Graph API app registration for
      SharePoint/Teams, mailbox access for email, the multi-DB Enterprise Neo4j target
      (G7 — DONE producer-side on the neo4j:5.26-enterprise-ubi10 container after Aura was dropped
      2026-07-06; the COMPANY-side live multi-DB deploy is what remains), and all SME curation
      (producer content arrives unapproved).
    - Acceptance: Track 1 = docmeta unit tests pass with no network/credentials (connector
      stubs SKIP, not fail); Track 2 = docs-fetch/docs-load run clean against real sources.

17. SOFTWARE REGISTRY STREAM (plan-07, ADR 0004 — mostly clean-adds, ONE rename to coordinate):
    docs/decisions/0004-*.md + docs/restructure/07-software-registry.md,
    config/taxonomy/software-registry.yaml (6 vendors / 7 products; includes an
    `invocation_patterns:` section that is status: proposed and INERT to the loader —
    Phase 3 is gated, do not wire it), drydocs/loaders/software_registry.py +
    software_registry.cypher + registry_ontology_supplement.cypher, the
    `load-software-registry` / `apply-registry-supplement` CLI commands, vocabulary
    entries reg_made_by/reg_uses_software (active), tests/unit/test_software_registry.py,
    and the `software-registry` source-registry entry — all generic, apply untouched.
    THE RENAME (plan-07 Phase 2, 2026-07-07): the producer renamed the back-flow seed
    files `graph-tests/vendor-bmc-smoke.yaml` → `bmc-docs-smoke.yaml` (suite id
    `bmc-docs-smoke`) and `config/gate-prompts/vendor-bmc-example.yaml` →
    `bmc-docs-example.yaml` (spec id `bmc-docs-structural`). These paths are
    Canonical-COMPANY (step 10) — but the producer's GENERIC tests
    (test_graph_verify.py, test_gate_pages.py), which you DO take, now assert the NEW
    names. So apply the rename to your own seed twins as a deliberate COMPANY-SIDE
    commit (`git mv` + suite/spec id, JobFolder-rename playbook) — your REAL suites and
    gate specs under other filenames are untouched. If you skip the rename, drop the
    producer's two renamed test functions in the same commit and log why; do not leave
    Track-1-adjacent tests red.

18. GATE-PAGE STANDARD + PREPPED-GATES BATCH (2026-07-07 — EVALUATE the renderer, clean-add the rest):
    - drydocs/gate_pages.py gained a GENERIC extension (meta header card;
      ProvenanceBlock/PropRow with origin source|derived badges), the format is directed
      in docs/restructure/03-hitl-sme-flow.md §"Gate-page format (STANDARD)", and
      tests/unit/test_gate_pages.py now ENFORCES it for every committed
      config/gate-prompts/*.yaml (meta keys Module/Source/Registry ref/Classification +
      ≥1 provenance block). gate_pages.py is a step-10 Canonical-COMPANY path, but this
      delta is pure mechanism (no wiring): FOLD it into your copy (or take the producer
      file if your copy has no divergent wiring), then bring your real gate specs up to
      the standard before the enforcement test lands — otherwise take neither the
      renderer delta nor the new tests, as one deliberate decision.
    - Clean-adds (all stopped AT the HITL gate — status: proposed / confirmed: false;
      NOTHING here is SME-confirmed; no gate-log entries were written): five gate specs
      (sosa-jobrun-observation, autosys-crosswalk, airflow-crosswalk,
      seal-attribution-match-policy, software-usage-patterns), config/crosswalks/
      (autosys-to-bmc.yaml, airflow-to-bmc.yaml), the jobrun-observation map-entry
      enrichment, and source-registry deltas (crosswalk/gate_spec pointers on
      autosys-export/airflow-mwaa; NEW stg-app-fact entry, confirmed: false). Per the
      Epic-K back-flow bullet: if your registry already carries a live STG_APP_FACT
      entry or an active seal_app_ref, that is a COLLISION — keep yours.
    - config/gate-log.md is an APPEND-ONLY AUDIT: on collision, merge additively
      (union of entries, chronological) — never drop either side's gate records.

19. CONTROL-M LOAD-ORDER CONTRACT + :ControlMApplication (2026-07, commit "enforce the ingest
    load order; ControlMApplication lands in the folder pass" — Canonical-here + ONE constraint bump):
    the ingest-controlm chain order is now CONTRACTUAL (test_ingest_chain_order_is_enforced) and the
    folder pass derives a SECOND grouping node — header-row APPLICATION -> :ControlMApplication (+
    CONTAINS_FOLDER), distinct from :ControlMServer AND from the SEAL :Application. Carries: the
    controlm_folders/jobs .cypher + Control-M SQL deltas + folder_name.py (Canonical-here — the
    Control-M loaders, step 6), a NEW constraint controlmapplication_name (EXPECTED_CONSTRAINTS 37 ->
    38 for THIS stream in test_schema.py; step 22 later adds document_id + chunk_id, so the CURRENT
    baseline is 40 — reconcile the final count with any company-side constraint edits), and the
    companion docs docs/design/controlm-ingestion-tdd.md + docs/restructure/08-source-column-mappings.md
    (clean-add docs). Load-order contract detailed in docs/controlm-staging-ingestion-flow.md §3a.

20. DESIGN-DOC PIPELINE — drydocs-docgen (Epic L, 2026-07-08 — all CLEAN-ADDS):
    a component that renders design docs deterministically from their .md source (the .md is the
    single source of truth). Apply untouched (new paths, no company collision expected): drydocs/
    doc_outline.py (canonical-outline completeness + traceability validator), drydocs/design_doc.py
    (stdlib markdown->HTML/print.html renderer, NO new dependency), drydocs/doc_pdf.py (headless-
    Chromium print.html->PDF), scripts/render_design_doc.py + scripts/doc_to_pdf.py, docs/design/
    templates/tdd.outline.yaml, docs/design/feedback/README.md, tests/unit/{test_doc_outline,
    test_design_doc,test_doc_pdf}.py, the `docgen` COMPONENT_GROUP in test_module_boundary.py + the
    MODULE_MAP.md rows, and the .gitignore rule `docs/design/*.pdf` (MERGE additively). The committed
    renders docs/design/controlm-ingestion-tdd.{html,print.html} port as generated artifacts; the
    .pdf is BUILD-ON-DEMAND (gitignored — do NOT port it, regenerate company-side). snapshot.ps1 gains
    a design-doc render step + the CLAUDE.md ritual stale-render check (Canonical-here). Not wired into
    cli.py (entrypoint-boundary TODO).
    L6 UPDATE (2026-07-08, all additive): design_doc.py gained PRINT-ONLY margin anchors (dd-margin-tag
    spans in a padding gutter, headless-Chromium-safe) + a Rev/commit FOOTER derived from the doc front
    matter (never git state/timestamps — render stays byte-deterministic); the screen surface is
    untouched. NEW skill .claude/skills/transcribe-doc-markup/ (scanned annotated printout -> faithful
    transcription shown FIRST -> anchor-keyed feedback via the SAME feedback_yaml() as the L5 digital
    loop) + its fixture (tests/fixtures/transcribe_doc_markup/) and test (test_transcribe_doc_markup.py)
    — clean-adds. The scans dir docs/design/feedback/scans/** is TRIPLE-GUARDED Internal (.gitignore +
    classification excluded_paths + README) — MERGE the .gitignore and classification rules ADDITIVELY.
    test_doc_outline now GLOB-tests every committed docs/design/*-tdd.md. The drydocs-remediation TDD
    (docs/design/drydocs-remediation-tdd.{md,html,print.html}; contract = ADR 0002-B, detect ->
    transform -> prove -> Jira, no graph write / SoD) is a clean-add rendered design doc.
    L10/L11 UPDATE (2026-07-10 merge, all additive): design_doc.py gained the appendix
    "SME - Feedback" panel (a STATIC HITL how-to block: annotate, Copy feedback, save the
    docs/design/feedback/<doc>-rev<N>.yaml — not a free-text field) + per-subsection annotate
    controls when a section has >2 subsections (feedback keys to derived sub-anchors);
    doc_outline.py + test_design_doc/test_doc_outline extended; the committed
    controlm-ingestion-tdd / drydocs-remediation-tdd .html renders are REGENERATED — take the
    code and the regenerated renders together (or re-render company-side; renders are
    deterministic). docs/design/feedback/README.md + the verify skill's SKILL.md deltas ride along.

21. SEAL ONTOLOGY RESHAPE + SCRAPED-DOCS SOURCE-OF-RECORD — GATE-BOUND PROPOSAL (2026-07-08;
    NOTHING applied — collision-sensitive; read the git-readme.md heads-up "SEAL entity reshape…"):
    relationship_vocabulary.yaml + config/taxonomy-ontology-map.yaml are step-6 Canonical-here, but
    this delta only ADDS planned/proposed material: 5 planned edges (hadPrimarySource, wasAttributedTo,
    qualifiedAttribution, agent, hadRole), Document/Attribution/TOMRole node classes, proposed_deprecation
    notes on the ACTIVE seal_has_membership/seal_of_role/seal_held_by edges, a proposed_reclass note on
    :Application (SoftwareAgent -> Entity/DataProduct), and 3 proposed map entries + a re-opened
    job-seal-app-ref (K1). COLLISION RULE (Epic-K back-flow, step 18): if company main has ALREADY typed
    :Application as Agent or promoted any seal_* membership edge to active, KEEP YOURS and reconcile the
    reshape at the gate — do not blind-take the producer's proposed statuses. Clean-adds: config/
    gate-prompts/seal-tom-attribution-reshape.yaml (step-18 gate-page standard), the config/precedence.yaml
    `proposed_additions` key (inert to the resolver), and the config/gate-log.md entry (APPEND-ONLY, union
    on collision). Nothing is SME-confirmed; no active graph impact.
    K3 UPDATE (2026-07-10, commit "K3 BusinessApplication entity-reshape gate SIGNED OFF"): the reshape
    gate has now been HELD and SIGNED OFF — config/gate-log.md carries the 2026-07-10 K3 entry (union
    APPEND-ONLY as ever) confirming the DIRECTION: :Application reclasses prov:SoftwareAgent ->
    prov:Entity/dprod:DataProduct and the label normalizes :Application -> :BusinessApplication, with
    TOMRole attribution + seal_* edge deprecations to follow. The APPLICATION has NOT shipped (producer
    backlog K4, todo): vocabulary/map statuses in this range still read proposed/planned and the
    collision rule above applies UNCHANGED. A LATER port carries the label rename + status flips —
    git-readme.md's SEAL-reshape heads-up gets rewritten then (K4's notes track exactly that), and the
    PORT-MANIFEST sequencing note (step 25) makes that rename wave a path-column diff.

22. BMC-DOCS LEXICAL LOADER — DOCMETA P0, SHIPPED & GATE-ACCEPTED (2026-07-08; commits "…bmc-docs
    lexical loader … STOPPED AT GATE" then "ACCEPTED 13/13 … LOADED LIVE" — MIXED stream). The
    converted BMC docs corpus (external/orchestration/bmc-controlm/, 27 pages — 26 at first load;
    controlm-api-installation.md joined 2026-07-09 via the remediation OQ-1 spike, with its
    SOURCE-MANIFEST entry; tests pin EXPECTED_DOC_COUNT = 27) loads as a DETERMINISTIC
    llm-graph-builder LEXICAL graph — no LLM/embeddings: H2-section chunking (seq-0 preamble), :Document
    + :Chunk nodes (BOTH prov:Entity) with PART_OF + FIRST_CHUNK/NEXT_CHUNK chains (out-degree <= 1),
    per-chunk trust tier VERBATIM|GROUNDED|SYNTHESIZED stamped per the SOURCE-MANIFEST default rule
    (SYNTHESIZED is Claude inference, NEVER vendor ground truth), and the software-ontology hook
    (Document)-[:DESCRIBES {target_version}]->(SoftwareProduct controlm). LOAD ORDER: the software
    registry (step 17) loads FIRST — DESCRIBES MATCHes the product, never MERGEs a stub.
    - Clean-adds (generic — take FROM producer): drydocs/loaders/bmc_docs.py,
      drydocs/loaders/cypher/bmc_docs.cypher, drydocs/models/docs.py (BmcDocChunkRow),
      tests/unit/test_bmc_docs.py.
    - Canonical-here (step 6): +2 constraints document_id + chunk_id in constraints.cypher (these drive
      EXPECTED_CONSTRAINTS to 40 — see step 19); 4 now-ACTIVE edges docs_describes / docs_chunk_part_of
      / docs_first_chunk / docs_next_chunk in relationship_vocabulary.yaml + their matching
      ontology_supplement.cypher blocks (test_schema.py REQUIRES the supplement block for every active
      edge); 4 confirmed entries in config/taxonomy-ontology-map.yaml.
    - Integration points (collision, ADDITIVE — preserve existing bodies): drydocs/cli.py gains the
      load-bmc-docs command + a `from .loaders.bmc_docs import …`; drydocs/models/__init__.py adds
      BmcDocChunkRow to imports + __all__.
    - source-registry: NEW `bmc-docs` entry (classification External, confirmed: true, gate_spec
      pointer) — merge into config/source-registry.yaml (test_classification gate).
    - BACK-FLOW (Canonical-COMPANY, step 10/18 rule): config/gate-prompts/bmc-docs-lexical-load.yaml and
      graph-tests/bmc-docs-lexical.yaml are gate-seed twins — if company main carries its own, KEEP
      COMPANY'S and drop the incoming; config/gate-log.md gains the 2026-07-08 acceptance entry — merge
      APPEND-ONLY (union).
    - Acceptance: poetry run pytest tests/unit/test_bmc_docs.py -q (portable — the corpus .md files are
      committed under external/, no network/DB). The company-side LIVE load is a Track-2 concern.

23. SOURCE-GOVERNANCE COLUMN LEDGER — doc 08 / N1 (2026-07-08 — clean-adds + one boundary-guard row).
    drydocs/source_mappings.py (schema drydocs.source-mapping.v1; a TYPED, PURE-config accessor in the
    review_labels pattern — no pandas/Neo4j; projected / filter-only / excluded / deferred disposition
    per profiled column), config/source-mappings/controlm-psgmgr.yaml (transcribes ONLY already-decided
    dispositions from the q1q3 gate + audit-fields: 5 objects, 69 projected rows; census pending — doc
    08 Phase 2), tests/unit/test_source_mappings.py. All CLEAN-ADDS — take FROM producer. BOUNDARY
    GUARD: source_mappings.py is classified into the drydocs-review COMPONENT_GROUP (parked there as a
    pure config accessor) — its MODULE_MAP.md row + the test_module_boundary.py membership MUST travel
    with it (default-deny guard, step 10/18), else test_module_boundary goes red. It is GENERIC doc-08
    tooling, NOT the company's wired review internals, so take it clean — unlike the rest of the review
    group. doc-08 authority: docs/restructure/08-source-column-mappings.md (a step-19 clean-add doc).

24. RELEASE / VERSIONING — v0.3.0 (2026-07-09 — clean-add docs; DO NOT take the version string).
    VERSIONING.md (SemVer policy: single source = the pyproject version, annotated vX.Y.Z tags mirror
    it, 0.x pre-1.0 bump rules, the public surface, the release ritual) and CHANGELOG.md (Keep a
    Changelog; [0.3.0] back-filled from phases 0-11, cross-referencing backlog ids) are CLEAN-ADDS —
    take FROM producer. pyproject.toml version (0.1.0 -> 0.3.0) is the PRODUCER's release
    cadence: on collision KEEP COMPANY'S version string (the company repo versions on its own schedule).
    Git TAGS are NOT transferred by cherry-pick — the v0.3.0 annotated tag stays producer-side; the
    company tags its own releases.

25. PORT-MANIFEST — MACHINE-READABLE DISPOSITIONS (2026-07-09, commit "PORT-MANIFEST.yaml —
    machine-readable port dispositions + guard"; READ IT AT STEP 2, EVERY PORT):
    PORT-MANIFEST.yaml (repo root; schema drydocs.port-manifest.v1, classification Internal-Public)
    is now THE mechanical authority for per-path dispositions — first glob row that matches a path
    wins, top-down; unmatched paths take the default (clean-add if absent consumer-side, evaluate if
    both sides created the path). Its disposition vocabulary (clean-add / canonical-producer /
    canonical-company / union-append / per-entry / evaluate / never-port) subsumes this prompt's
    Canonical-here / back-flow / append-only phrasing; the numbered steps here remain narrative
    (sequencing + why). PER-ENTRY rows (relationship_vocabulary.yaml, taxonomy-ontology-map.yaml,
    pyproject.toml, …) FORBID whole-file checkout — resolve inside the file by id, never downgrading
    a consumer entry whose status is active/confirmed/applied. Clean-adds: PORT-MANIFEST.yaml itself
    + tests/unit/test_port_manifest.py (its portable guard) + the reconcile-port skill repoint +
    docs/reviews/tech-debt-port-boundary.md (its origin audit). SEQUENCING NOTE (recorded in the
    manifest header): the manifest lands BEFORE the ADR 0002 Phase B package split, so that rename
    wave arrives in a later range as a manifest path-column diff, not a prose rewrite.

26. CM_HOSTS + CM_AVG_RUN ONBOARDING — EPIC P: EXTRACT + GATE ONLY, NO LOADERS YET (2026-07-09/10,
    commits "add-source-object walkthrough skill + CM_HOSTS host topology to the gate" ->
    "controlm-hosts-topology SME sign-off — 18/18" -> "CM_AVG_RUN runtime-stats supplement to the
    gate" -> "CM_AVG_RUN P4 join performance guard" -> "confirm CM_DEF_SETVAR -> CM_DEF_SETVAR_VW;
    filter V.IS_CURRENT_VERSION" + sweep stragglers):
    - Clean-adds: .claude/skills/add-source-object/ (guided object-onboarding walkthrough — the
      step-13 skills rule applies), the extract + profile SQL (drydocs/loaders/sql/controlm_hosts.sql,
      controlm_avg_run.sql, adhoc/profile_cm_hosts.sql, adhoc/profile_cm_avg_run.sql — the adhoc/
      dir is new), and the two gate specs config/gate-prompts/controlm-hosts-topology.yaml +
      controlm-avg-run-supplement.yaml (step-18 gate-page standard; gate-seed twin rule does NOT
      apply — these are producer-authored gates, not company back-flow seeds).
    - Per-entry merges (manifest rules): config/source-registry.yaml gains the cm_hosts + cm_avg_run
      objects under controlm-psgmgr; config/source-mappings/controlm-psgmgr.yaml grows 5 -> 7 object
      ledgers (supersedes step 23's "5 objects" count; test_source_mappings extended to match);
      taxonomy-ontology-map.yaml + relationship_vocabulary.yaml gain the host-topology entries —
      ExecutionHost/HostGroup node classes and the m3_runs_on_agent_host / m3_runs_on_etl_host /
      m3_runs_on_host_group edges (RUNS_ON label, role-disambiguated) with UPDATED feed notes
      (psgmgr CM_HOSTS + the NODE_ID resolution pass: hard-coded 1-hop vs group 2-hop).
    - GATE STATUS SPLIT (do not conflate): controlm-hosts-topology is SME-CONFIRMED 2026-07-09,
      18/18 (config/gate-log.md union-append; its map entries read status: confirmed);
      controlm-avg-run-supplement is AWAITING SME (proposed — a ControlMJob PROPERTY supplement:
      avg/min/max/std-dev run times + a scoped join-performance smoke test first, NOT a node
      stream). The m3_runs_on_* edges stay status: planned — NO loaders, cypher, CLI commands, or
      constraints shipped for either object (producer backlog P3/P4) — EXPECTED_CONSTRAINTS stays 40.
    - SETVAR_VW FIX (Canonical-here, the step-6 Control-M SQL rule): CM_DEF_SETVAR is confirmed as
      the CM_DEF_SETVAR_VW view + the V.IS_CURRENT_VERSION filter wherever the variables extract
      joins it (variables SQL + both new extracts + the controlm-db skill references). If your
      replica exposes the base table instead, reconcile the view name as a DELIBERATE company-side
      decision — do not silently drop the IS_CURRENT_VERSION filter.
    - knowledge/standards/technology/data-center-naming-convention.md gained the hosts-gate DC scope
      note (Canonical-here, step-6 knowledge/standards rule).

27. TAXONOMY-ONTOLOGY MAP GUARD + VOCAB_ID MIGRATION + C6 REGISTRATION (2026-07-09, commits
    "tech-debt F1+F3", "tech-debt F4+F2 point fixes", "C6 — register REQUIRES_SCHEDULER",
    "platforms.yaml placeholder"):
    - tests/unit/test_taxonomy_ontology_map.py — NEW portable drift guard (clean-add, PyYAML-only):
      the map's summary block is COMPUTED (recount enforced after any merge), entries carry
      vocab_id linkage into relationship_vocabulary.yaml, statuses must be real (the F2 fix made
      `applied` truthful). TAKE IT — the manifest's per-entry rules lean on this guard. The F3
      migration rewrote existing map entries with vocab_id (per-entry merge; never downgrade
      confirmed/applied). F4 deduped the Document node-class label in the vocabulary.
    - C6: REQUIRES_SCHEDULER (:BatchProcessing -> :SchedulerKind) is now REGISTERED in
      relationship_vocabulary.yaml + the map as status: planned, GATE-BOUND — do NOT activate.
      Heads-up riding with it: :SchedulerKind itself is slated for deprecation -> :AisCapability +
      :AiTool (parked in IDEAS.md until the SME defines the classes); config/taxonomy/platforms.yaml
      is a status: placeholder clean-add recording that reconciliation.
    - Audit docs (clean-adds): docs/reviews/tech-debt-taxonomy-ontology-map.md (the F1-F5 origin;
      tech-debt-port-boundary.md already rode in with step 25).

28. PHASE B PHYSICAL RELOCATE — THE RENAME WAVE (2026-07-10; commits "0002-A-1 — Phase B thin
    relocate (amends 0002-A step 4)" -> "G2 physical relocate — drydocs-core extraction (thin,
    per ADR 0002-A-1)" -> "re-path moved core references" -> "G2 DONE", merged --no-ff as
    "Merge feat/g2-core-relocate: …"). Port this range ON ITS OWN — do not mix it with feature
    ranges. Read git-readme.md's "structural path-move LANDED" section + the re-pathed
    PORT-MANIFEST.yaml FIRST.
    - WHAT MOVED (42 renames, content ~unchanged): models/, adapters/, controlm/ (minus the
      staging builder), ontology/ (+ relationship_vocabulary.yaml), schema/ (.cypher resources),
      neo4j_client.py, config.py, precedence.py, source_registry.py -> drydocs_core/;
      drydocs/controlm/staging.py -> drydocs/staging.py. The drydocs/ package REMAINS (load /
      review / plan / docgen components — the drydocs-load rename was DELIBERATELY not executed,
      ADR 0002-A-1); the drydocs console script, `import drydocs.cli`, and the single-pyproject
      packaging are all unchanged (drydocs_core was already in packages since the step-9 shim).
    - APPLY THE RENAMES FIRST: across disjoint history each move arrives as delete+add. Safest:
      replay the moves as your own `git mv` batch (producer content is byte-identical for pure
      moves), then apply the range's content diffs on top; if you cherry-pick instead, verify
      every "deleted" core file reappeared under drydocs_core/ before resolving content.
    - MOVED canonical-company paths (see their manifest notes): drydocs_core/adapters/
      oracle_adapter.py (PORT-FROZEN) and drydocs_core/ontology/relationship_vocabulary.yaml
      (per-entry) — apply the RENAME, keep YOUR content/entries at the new path.
    - COMPANY-SIDE REPOINT (your files — the incoming commits cannot do this for you): every
      consumer-only module (locations.py, seal_deployments.py, controlm_app_codes.py, the wired
      review internals, your cli.py command bodies) that imports drydocs.models / .adapters /
      .controlm / .neo4j_client / .config / .precedence / .source_registry / .ontology must
      repoint to drydocs_core.*. The staging builder (build_staging_bundle / build_staging_rows /
      collect_jobs) moved to drydocs.staging and core's controlm/__init__ NO LONGER re-exports
      it — repoint those imports too. Any hardcoded drydocs/schema | drydocs/ontology paths in
      your local configs/scripts follow the same rewrite.
    - tests/unit/test_module_boundary.py is canonical-producer and arrives with
      CORE_PREFIXES = drydocs_core: after taking it, RE-ADD your consumer-only modules to its
      COMPONENT_GROUPS (default-deny fails on unclassified modules — same drill as when
      default-deny first landed).
    - Clean-adds riding along: docs/decisions/0002-a-1-phase-b-thin-relocate.md; MODULE_MAP.md /
      CLAUDE.md / git-readme.md / PORT-MANIFEST.yaml updates are canonical-producer as usual.
      Side-fix in the range: drydocs/__init__.py __version__ bumped to match pyproject — on
      collision keep YOUR version string (step-24 rule).
    - Acceptance: full unit suite green AFTER your repoint; boundary test green; the CLAUDE.md §6
      gates unchanged (import drydocs.cli / drydocs --help). Producer reference at range head:
      483 passed / 3 skipped.

29. REMEDIATION COMPONENT STREAM — G3 / ADR 0002-B EXECUTED END-TO-END (2026-07-10, after the
    step-28 relocate; commits "G3 step 2 — archive inventory" -> "G3 doc port" -> "G10 —
    sanitized re-review item" -> "scaffold drydocs_remediation" -> "M0 PoC slice" -> "Tier-1
    transform engine + Jira handoff boundary" -> "G3 CLOSED — corroboration wired", plus the
    planning chores around them):
    - NEW PACKAGE (clean-adds; manifest row drydocs_remediation/** canonical-producer):
      drydocs_remediation/ — formats (DefinitionFormat seam: TranscriptDefinitionFormat live,
      schema drydocs.remediation.transcript.v1; XmlDefinitionFormat BLOCKED on the vendor
      schema acquisition — do NOT implement it from memory), detect (R1 dot-smuggling over the
      core classifier; findings ratified=False until the registry is machine-readable),
      transform (ratified-only Tier-1 engine + canonical-variable-rename; rule VALUES are
      COMPANY-SIDE — inject your ratified name map, never commit it producer-side), equivalence
      (order-paired resolved-watch proof via drydocs_core), jira (pure render + JiraSubmitter
      boundary — your REST impl + credentials stay company-side config), corroborate
      (reconcile_variables + ReadOnlyGraph, the component's SOLE graph path — write Cypher
      refused before the driver; write your live schema-specific queries THROUGH this wrapper).
    - pyproject.toml (per-entry): the packages list gains { include = "drydocs_remediation" } —
      apply that delta; keep your version string as ever.
    - tests/unit/test_module_boundary.py (canonical-producer): gains the remediation
      COMPONENT_GROUP + PKG_ROOT — after taking it, RE-ADD your consumer-only modules to the
      groups (the step-28 drill). NEW portable suites (all clean-adds, no network/DB):
      test_remediation_{scaffold,m0,tier1,handoff,no_graph_write,corroborate}.py + the
      SYNTHETIC fixtures tests/fixtures/remediation/ (mechanism twins; real values never in tests).
    - internal/remediation/** (clean-add; manifest row canonical-producer): the spinoff doc
      port (rules registry R1-R29, remediation plans, governance corpus subset) + the real M0
      transcripts and the 2026-07-10 engine-run record. Internal BY CONTENT — fine on the
      private company remote, NEVER in any public mirror. TWO governance docs are deliberately
      ABSENT repo-wide (user keep-out decision): their identities live ONLY in
      internal/remediation/README.md §HELD; re-entry is backlog G10 (sanitized — do not name
      them in publishable files, including this prompt). Company-side additions under this
      tree (e.g. G10 landings) are yours alone and never flow back.
    - DECISION DOCS (canonical-producer): 0002-B is fully ticked + DONE; ADR 0002 records the
      controlm-spinoff archive SUPERSEDED — company-side, STOP treating the archive branch as
      live source; it remains readable reference only. 0002-A-1 rode in with step 28.
    - DESIGN DOC: docs/design/drydocs-remediation-tdd.md traceability matrix statuses updated
      (NFR-REM-1/2 done, most FRs partial) + regenerated .html/.print.html — take the .md and
      renders together or re-render (deterministic).
    - PLANNING STREAM (producer planning, take as prior practice): backlog.yaml (G3 done, G10
      added SANITIZED, model field `fable` now legal), tests/unit/test_backlog.py +
      .claude/skills/groom-backlog/ (MODELS enum gains "fable"; matrix text), board render,
      IDEAS.md union-append (one Phase-C packaging capture line).
    - KNOWN-PENDING carried by design (do not "fix" during the port): the real M0 unit's
      equivalence verdict awaits the ground-truth watched filename (A3) + the var.text dot
      rule (B1) — BOTH are company-side unblocks; the core resolver is deliberately untouched
      until then. Tier-2 agentic lane (FR-REM-4) and XML I/O are future slices per the TDD.

30. LINEAGE COMPONENT STREAM — G4 SCAFFOLD + G9 / ADR 0002-C RE-HOME + THE SQL RUN-LOG PORT
    (2026-07-10/11; commits "G4 — scaffold drydocs_lineage (C2) + drydocs_deepdoc (C3)" ->
    "G9 slice 1 — re-home depgraph model + inventory extractor onto core" -> "0002-C slice-1
    record" -> the port/depgraph-lineage-rehome branch commits (tech-debt inbox, node_target
    rename, slice 2 + close) -> merge --no-ff, plus the SQL-logging merge "port/oracle-sql-run-log"
    that landed mid-stream):
    - NEW PACKAGES (clean-adds; canonical-producer): drydocs_lineage/ — model (ProcessNode/
      DataAssetNode reconciled to the ControlMJob NODE-KEY composite; rels normalized to the
      REGISTERED planned vocabulary m3_invokes/m3_triggers/m3_reads_from/m3_writes_to),
      extractors/controlm_inventory (parses via the SHARED core parser — no fork), review
      (self-contained SME page; CLI `drydocs lineage-review`), collect/ (RHEL run-as-user
      collector, *.sh is LF — .gitattributes rule rides along), writer (Fork-3: plan_curated +
      write_curated — GATE-BOUND: refuses live load while the four m3_* registry entries are
      status: planned, and refuses any DB but drydocs). drydocs_deepdoc/ — scaffold only
      (investigate/writer stubs; write target drydocs_context).
    - CORE DELTAS that rode with G9 (take them; they are core changes, not component forks):
      Invocation.target property + regression test (fold delta #4); the G8 parser deltas were
      already in your core if you took step 28/29.
    - SQL RUN-LOG (PARALLEL IMPLEMENTATION — read item 14 first): producer's OracleAdapter +
      NEW drydocs_core/adapters/sql_run_log.py now tee every --use-oracle extract to a per-run
      log (SPIDERP_LOGDIR/SPIDERP_CALLER; render display-only, execution stays parameterized;
      born with your bind-renderer hardening). Company-side you ALREADY log via the JDBC path
      (jdbc_oracle_adapter.py/SpiderpRunner) — take these files only if you also run the
      python OracleAdapter path; either way DO NOT port your JDBC files back here.
    - tests/unit/ (clean-adds): test_lineage_{inventory,review,writer}.py +
      test_lineage_deepdoc_scaffold.py + test_sql_run_log.py + tests/fixtures/lineage/jobs.csv
      (SYNTHETIC twin — value-fake). test_module_boundary.py gains the lineage/deepdoc
      COMPONENT_GROUPS + PKG_ROOTS — after taking it, RE-ADD your consumer-only modules (the
      step-28 drill). pyproject packages list gains lineage/deepdoc includes.
    - DECISION DOCS (canonical-producer): 0002-C DONE (all §4 dispositions + §5 ticks); ADR
      0002 affects: block records ce-wilson/depgraph@feat/controlm-lineage (PR #2, 5b09a0d)
      SUPERSEDED for the lineage assets — company-side, stop treating that branch as live
      lineage source. docs/oracle-sql-logging.md is the producer-path logging guide (mechanism
      only; your JDBC guide stays yours).
    - KNOWN-PENDING carried by design (do not "fix" during the port): write_curated refuses
      until the HITL gate flips the vocabulary active (that refusal IS the D2 contract);
      curation.curate is a stub (phased-cadence trigger wiring, G4-scoped future);
      node_target is POLYMORPHIC (gate controlm-hosts-topology) — resolution is Epic P.

31. QUALITY BATCH + DOCS + WEB CONSOLE (O2) + THE 2026-07-14 GATE SESSION (2026-07-11 →
    2026-07-14; 48 commits, subjects "fix(lineage): restore +x on collect/rua_inventory.sh" →
    "docs(ui): wf-console-01 — add paired blank sketch sheets after every view"; four streams):
    - NON-HITL QUALITY BATCH (J-series + G11 + N2, 2026-07-12): J5 adds .github/workflows CI
      running the CLAUDE.md test gates + a publish-boundary guard (NEW manifest row .github/**
      = evaluate: the guard is producer-remote-specific and GHE Actions runners/policies are
      yours — keep consumer workflows, adapt rather than adopt). J9 adds a testcontainers
      end-to-end load suite (needs Docker; auto-deselected without it — the "3 deselected" in
      the acceptance numbers). J7 adds tests/unit/test_port_reconcile_guards.py — these test
      THE PORT ITSELF and skip producer-side; consumer-side they RUN once RECONCILE_BEFORE_DIR
      is set (your 3 extra passes). J6 drops streamlit + streamlit-agraph from pyproject
      (per-entry rule: apply the removal only if you never used them — producer-dead deps).
      J8 skip-guard policy test, N2 column-ledger drift guards, G11 extractor coverage
      accounting, J2 README edge rename (:DEPENDS_ON → :WAS_INFORMED_BY), J4 run-drydocs
      skill refresh, and the /tech-debt documentation-audit record.
    - DOCS/GOVERNANCE STREAM (2026-07-12/13): whitepaper Rev 1 + deterministic HTML renders
      and project TDD Rev 1→2 (module topology + C4 views, Epic L outline-conformant) — take
      each .md WITH its renders or re-render (deterministic house renderer). **G10 CLOSED:**
      the held governance docs are PERMANENTLY out-of-repo by SME gate (2026-07-12); their
      identities live ONLY in internal/remediation/README.md §HELD — do not reintroduce them
      from any company-side copy, and keep them out of publishable files (including this one).
    - WEB CONSOLE STREAM (O2 + the UI reconcile, 2026-07-13/14): web/ leaves its test-page
      state — persona MOCK auth (localStorage, SYNTHETIC personas; real authn/authz is
      explicitly deferred to ADR 0005), role-gated shell, My Apps view, CypherConsole; plus
      the UI-WIP/ design record (wireframe guide/PDF, nav-flow mermaid, design review, dark
      landing mock; wf-console-01.{html,pdf} — the range's two closing commits — is the
      printable SME-review wireframe: per-view element keys, Neo4j label key tables, and a
      paired blank sketch sheet after every view — the Epic-L pen/paper HITL loop pointed at
      the UI). NEW manifest rows: web/** and UI-WIP/** canonical-producer. web/ ships
      .env.example ONLY — Vite inlines VITE_* values into the built bundle, so a committed
      VITE_NEO4J_PASSWORD is a secret in a publishable artifact; your .env.local stays
      gitignored. .gitattributes gains `*.pdf binary` (take it — guards committed PDFs against
      autocrlf corruption). ADR 0005 (PROPOSED): thin API is the deployment access path;
      bolt-from-browser is dev-mode-only behind a GraphAccess seam — read it BEFORE building
      company deployment on web/'s current direct-bolt lib. Dead branch
      feature/ui-dark-landing-myapps was deleted producer-side (its TDD copy was obsolete);
      origin/feat/web-console-design-pass still holds an unmerged design mockup.
    - GATE-SESSION STREAM (2026-07-14 — the config/ + tests coupling, read carefully):
      - software-registry.yaml gains vendors apache/broadcom + products airflow/autosys
        (ADR 0004 shapes; MWAA is deliberately NOT a separate product — stock object model).
      - config/crosswalks/: ExecutionHost wording fixed against the signed-off host-group
        model (airflow row 8 split 8a/8b/8c — queue is 1-to-many via ControlMHostGroup;
        autosys row 6 demoted exact→approximate — machine: is polymorphic), THEN both
        crosswalk gates SIGNED OFF: files + all rows now status: confirmed.
      - source-registry.yaml: airflow-mwaa + autosys-export flipped confirmed: true —
        SOURCE-ROW ONLY, no loaders exist. These flips are a UNIT with: audit-fields.yaml
        stub entries, test_source_mapping_drift.py LEDGER_PENDING (+airflow-mwaa,
        +autosys-export), and test_source_registry.py gate-state pins — take config + tests
        together or Track-1 breaks. Your own gate sessions govern YOUR flips (gate-prompts
        are canonical-company); producer gate-log entries ride in via union-append.
      - P2 avg-run gate SIGNED OFF with one SME edit: **ctlm_id (folder_id.job_id, e.g.
        161015.7) is YOUR internal psgmgr derived column** — the producer records only the
        mechanism (join prefers ctlm_id, weak (SCHED_TABLE, JOB_MEM_NAME) key demotes to
        fallback); verify your CM_AVG_RUN extract exposes it (probes P0/P4). Map entry
        job-runtime-stats-supplement → confirmed.
      - K2 match-policy gate SIGNED OFF 24/24: map entry job-seal-app-ref → confirmed WITH
        the K3 type-conflict rider intact (the WAS_ASSOCIATED_WITH shape re-opens when K4
        applies the :Application reclass — per-entry rule: never downgrade, never drop the
        rider). m3_seal_app_ref stays planned; it flips active WITH the K2 loader build
        (back-flow-origin id — consumer-canonical once you promote it).
      - NEW config/manual-loads/ (manifest row: manifest.yaml = per-entry/union): the tier-5
        SME-authored CSV mapping mechanism — PIN semantics (automation never silently
        supersedes a manual edge; retirement is human-only via the manifest), nodes a CSV
        creates are stamped manually_created: true, every file registers with a REQUIRED
        replaces_with automation path. Producer ships mechanism + empty lists; YOUR real CSVs
        live under internal/ and YOUR manifest entries never come from a port.
      - E1 SOSA gate DEFERRED (nothing flips); gate-log gains five entries (union-append);
        docs/decisions/README gains the 0005 row; IDEAS union-append (ctlm_id ripple,
        render_board venv gotcha).
    - KNOWN-PENDING carried by design (do not "fix" during the port): no airflow/autosys
      loaders (activation is source-row only, each loader gets its own gate); P2 loader
      blocked on the P1 probes (company-side run); K2 loader authorized, not built
      (BUILT same day — step 32 supersedes this line); ADR 0005 awaiting acceptance;
      E1 deferred.

32. K2 SEAL ATTRIBUTION LOADER BUILD — m3_seal_app_ref GOES ACTIVE (2026-07-14, same day as
    the step-31 gate session; branch feat/k2-seal-attribution-loader merged --no-ff, commit
    "feat(load): K2 SEAL attribution loader …"). Implements the seal-attribution-match-policy
    gate exactly; read that gate-log entry (incl. its "Build landed" bullet) before resolving.
    - Clean-adds (drydocs/loaders/** + tests are canonical-producer rows):
      drydocs/loaders/seal_attribution.py (pure match-policy resolver — tier precedence
      SEAL > FID > APP_NAME > ALIAS, SEAL-alone, one-to-one accept, deterministic multi-hit
      tie-break flagged for audit, PIN-aware; TierReconcilers seam — APP_NAME reconciles from
      the loaded SEAL reference, FID/ALIAS ship EMPTY awaiting company-side tables, facts stay
      counted-unresolved, never guessed), seal_attribution.cypher (gate §D shape EXACTLY:
      MATCH-only endpoints — creates NO nodes; ON CREATE first_seen_at/source/match_method,
      SET last_seen_at/last_run_id; manual-pin WHERE guard), manual_loads.py +
      manual_seal_attribution.cypher (§F tier 5: manifest-gated, never mints a relationship
      type, manually_created stamps), controlm_app_facts.sql (its ORDER BY stg_run.started_at,
      app_fact_sk IS the tie-break contract — do not drop it), drydocs_core/models/
      attribution.py (StgAppFactRow/SealAttributionRow/ManualMappingRow), tests/unit/
      test_seal_attribution.py + test_manual_loads.py + tests/fixtures/attribution/ (SYNTHETIC).
    - Integration points (collision, ADDITIVE — preserve existing bodies): drydocs/cli.py gains
      load-seal-attribution (source-gated, §E sequencing precondition, coverage printed +
      invariant enforced) + load-manual-mappings + the two loader imports;
      drydocs_core/models/__init__.py adds the three attribution rows (union rule, manifest row).
    - Canonical-here (step 6) / per-entry (manifest): relationship_vocabulary.yaml
      m3_seal_app_ref planned -> ACTIVE with supplement ontology_supplement.cypher + loader
      seal_attribution.cypher recorded — per-entry rule: never downgrade; the K3/K4 rider stays
      in the note (the K4 reclass re-opens the edge SHAPE at its own gate).
      ontology_supplement.cypher gains the role-discriminated WAS_ASSOCIATED_WITH block
      (iri #wasAssociatedWithSealAppRef, MAPS_TO prov:wasAssociatedWith) — test_schema.py
      requires it for the active entry. EXPECTED_CONSTRAINTS UNCHANGED (40): edges only.
    - SOURCE-ROW FLIP, ONE UNIT (the step-31 coupling pattern — take config + tests together):
      source-registry stg-app-fact confirmed: true (per the activation condition that entry has
      carried since K1 — the now-logged match-policy gate) + gate_spec/loader pointers;
      audit-fields.yaml stg-app-fact stub; test_source_mapping_drift.py LEDGER_PENDING
      (+stg-app-fact — ledger belongs to the doc-08 STG census); test_source_registry.py
      gate-state pin (+stg-app-fact). Your own registry rows follow YOUR gate sessions as ever.
    - graph-tests/seal-attribution-coverage.yaml: producer-authored verify suite (6 TCs — §D
      shape props, one-to-one automated attribution, match_method vocabulary, JobRun coverage
      reconciliation matched+unmatched+pinned=eligible, latest-run edge bookkeeping,
      manual-node stamps). graph-tests/** is canonical-company ON COLLISION; absent
      company-side it clean-adds.
    - config/gate-log.md: the 2026-07-14 K2 entry gains a "Build landed" lifecycle bullet —
      union-append as ever. Planning stream: backlog K2 -> done (+ phase 9 -> in_progress),
      board render, IDEAS captures (schema_graph.cypher staleness; FID/ALIAS reconciliation
      tables = company-side unblocks).
    - COMPANY MUST SUPPLEMENT (cannot be built producer-side): the FID -> seal_id and alias
      reconciliation tables (wire them into TierReconcilers at the CLI); the LIVE attribution
      load (Track-2 — run after your jobs + SEAL loads; the map entry job-seal-app-ref flips
      confirmed -> applied only when a live run writes edges); real manual CSVs under internal/
      with YOUR manifest entries (never from a port, step-31 rule). Tracked as rows T1–T4 in
      the COMPANY-SIDE TRACKER below — flip statuses there, in your copy.

33. ADR 0005 ACCEPTED + GRAPHACCESS SEAM (O4) + DRYDOCS-API SCAFFOLD (O5) (2026-07-14, after
    step 32; commits "docs(adr): 0005 ACCEPTED — browser↔Neo4j access path ratified by the SME
    (O3 done)", merge "feat/o4-graphaccess-seam …", merge "feat/o5-drydocs-api …", + the two
    backlog chores "O4 done" / "O5 done"). Step 31's "ADR 0005 awaiting acceptance" is now
    resolved: thin API is the deployment access path; bolt-from-browser is dev-mode-only.
    - O3 (clean-add per docs/decisions/**): 0005-browser-neo4j-access-path.md flips
      PROPOSED → ACCEPTED. Read it before resolving O4/O5 — it is the WHY for both.
    - O4 (web/** canonical-producer wholesale, step-31 row): the GraphAccess seam —
      web/src/lib/graph.ts (the seam), graphApi.ts (api-adapter stub), neo4j.ts (dev-mode
      bolt gating), CypherConsole.tsx (gated raw-Cypher), .env.example + README. The step-31
      secret caveat stands: your real VITE_NEO4J_* values stay in YOUR .env.local, never ported.
    - O5 (NEW python component — clean-adds): drydocs_api/** (app.py FastAPI wiring behind the
      OPTIONAL `api` poetry group; guard.py read-only Cypher guard — comments/strings stripped
      first, word-boundary clause match; routing.py per-view DB routing drydocs vs drydocs_all,
      fail-closed; queries.py named view queries incl. the two support queries proven live
      2026-07-14 — folder-census + dependency-chain — and the c4-graph O6 payload; personas.py
      + sessions.py auth stub — roles resolved server-side, OIDC is YOUR company-side twin;
      handlers.py framework-free) + tests/unit/test_drydocs_api.py.
    - Collisions: MODULE_MAP.md + tests/unit/test_module_boundary.py are canonical-producer
      (gain the `api` COMPONENT_GROUP row + classification); pyproject.toml is per-entry
      (union the `api` optional group's deps, KEEP your version string); poetry.lock has no
      manifest row — REGENERATE consumer-side after the pyproject union, don't hand-merge it.
    - COMPANY MUST SUPPLEMENT (unchanged from the ADR Evidence): enterprise OIDC twin for the
      auth stub; the live multi-DB deploy remains T7.

34. PSGMGR VERSION-FILTER FIX (D4) + JOB-TYPE TABLES PLAN (2026-07-15; commits "docs(controlm):
    plan job-type detail tables …", "chore(backlog): groom - 2 promoted (D4, O7) …",
    "fix(loaders): psgmgr version filter IS_CURRENT_VERSION = 'Y' (was '1') — D4",
    "docs(loaders): SETVAR_VW version domain SME-confirmed 'Y' - D4 residual closed").
    ORIGIN NOTE: the 'Y' correction came FROM your finalized controlm-ingestion TDD (captured
    producer-side as a local-only reference) — the producer is CONVERGING to your reality, so
    most collisions in this range resolve to content you already have.
    - The fix (canonical-producer rows; on collision the two sides should now AGREE on 'Y' —
      if any consumer file still carries '1' outside historical prose, take the producer side):
      controlm_{folders,jobs,conditions_in,conditions_out,variables,variables_scenarios}.sql,
      adhoc/profile_cm_hosts.sql + profile_cm_avg_run.sql + preflight_open_questions.sql
      (touches step-26 probe files — probes not yet run per T5, so nothing to re-run),
      ddl/controlm_staging_ddl.sql + supplement DDL view filters, controlm_jobs.cypher
      (.active = row.is_current_version = 'Y'), constraints.cypher comment,
      drydocs_core/models/controlm.py description, drydocs_lineage controlm_inventory.py
      (current = 'Y'; '1' tolerated for legacy synthetic CSVs), tests
      (test_controlm_cypher/models/lineage_inventory) + fixture CSVs flipped '1'/'0'→'Y'/'N'
      (tests/fixtures/lineage/jobs.csv + 3 drydocs/data/samples CSVs — synthetic, canonical-producer).
    - docs/design/controlm-ingestion-tdd.{md,html,print.html}: NEW MANIFEST ROWS —
      canonical-company. YOUR finalized TDD is ahead (SPIDERP §7f etc.); KEEP IT. The
      producer's Rev-3 mirror only gained the 'Y' literals your doc already has.
    - config/source-mappings/controlm-psgmgr.yaml (canonical-producer per the config/** row):
      IS_CURRENT_VERSION entry — the gate controlm-q1q3-phase1 §Q2 domain probe is RESOLVED
      'Y' (2026-07-15); derived_also rule now 'Y'; SETVAR_VW default_disposition note updated.
    - Skills (canonical-producer): .claude/skills/controlm-db/** ('Y' in SKILL.md,
      query-cookbook, schema-crosswalk, ingest), reconcile-port SKILL.md divergence-ledger
      line corrected. git-readme.md 'Y' corrections ride the normal canonical-producer rule.
    - Clean-adds: docs/controlm-job-type-tables-plan.md (planned STG_JOB_FILEWATCH /
      STG_JOB_OS_COMMAND_VW / STG_LAUNCH_DETAIL extension of the C3 stream — plan only, no
      code yet), docs/Product/seal/seal-application-hierarchy.md (describes a SEAL 4-tier
      hierarchy diagram via a FICTIONAL example; the referenced image-2.md diagram is not in
      the producer repo — supply/keep yours if you have the real one).
    - Planning stream (Canonical-here as ever): backlog.yaml D4 done + O7 added-and-closed
      (the two live-proven support queries — already shipped by O5's queries.py, step 33;
      the item records the audit trail, no new code), board render, IDEAS audit trail. Historical docs/reviews (persona-*, superseded sdlc-oracle-ingestion) deliberately
      KEEP the old '1' literals — do not "fix" history.
    - EXPECTED_CONSTRAINTS UNCHANGED; no schema/edge changes; Track-1 counts unchanged.

35. K4 — BUSINESSAPPLICATION ENTITY-RESHAPE APPLIED (2026-07-15, branch
    feat/k4-businessapplication-reshape, 7 gate-disciplined commits "K4(1)".."K4(7)" + this
    port-narrative commit; gate sign-off 2026-07-10 in config/gate-log.md). SUPERSEDES the
    step-21 "gate-bound proposal" framing and git-readme's old "do NOT take as applied" —
    the reshape IS applied now. Resolve in commit order:
    - (1) LABEL RENAME :Application -> :BusinessApplication + prov:Entity/dprod:DataProduct
      reclass, EVERYWHERE (vocabulary, constraints businessapplication_*, supplements incl.
      LocalClass iri, ALL loaders that MERGE the app node — seal_applications, seal_contacts,
      software_registry, pat_product_mapping — snapshots/writer, cli, tests, graph-tests).
      Company graphs: run the supplements (idempotent SoftwareAgent-edge cleanup included);
      relabel live nodes with your own migration (producer has none for node labels — CSV-mode
      producer graphs rebootstrap; your live multi-DB needs
      MATCH (a:Application) SET a:BusinessApplication REMOVE a:Application, plus constraint
      re-create — YOUR change, coordinate with T7).
    - (2) TOMRole scheme + QUALIFIED_ATTRIBUTION/HAS_AGENT/HAD_ROLE active (new prov anchors
      in ontology.cypher; tom_roles SkosConceptScheme, fixed 7, operate_manager L1/L2 as a
      level property).
    - (3) seal_has_membership/seal_of_role/seal_held_by DEPRECATED — the manifest per-entry
      rule now carries the gate-authorized-deprecation exception: TAKE these downgrades.
      PAT (catalog_dev_team_has_membership) untouched.
    - (4) seal_had_primary_source ACTIVE (edge-only; Document loader waits on docmeta/T6).
    - (5) arch_develops -> WAS_ATTRIBUTED_TO {role: developed_by} + NEW
      migrate_develops_to_was_attributed_to.cypher — RUN IT on your live graph (matches the
      old :Application label too).
    - (6) SEAL loaders rewritten to the qualified-attribution shape (seal_contacts carries
      the role-name crosswalk; unmapped names load flagged unmapped_role=true, never guessed).
      Map entries application-as-dataproduct + seal-tom-attribution -> APPLIED,
      seal-doc-source-of-record -> CONFIRMED (map summary 8/20/3, updated: 2026-07-15).
    - (7) precedence.yaml: seal-pat-source-of-record wired at authority 3 (above
      lob-product-team, now 4) — live but silent until docmeta feeds it.
    - STILL DEFERRED: the K1/K2 job->app WAS_ASSOCIATED_WITH edge shape (§F rider on
      m3_seal_app_ref — unchanged, needs its own gate); K5 Product Cabinet.
    - EXPECTED_CONSTRAINTS count UNCHANGED (names changed: application_* ->
      businessapplication_*) — reconcile your count per the step-25 rule, keep your number.

COMPANY-SIDE TRACKER — LIVE-LOAD + SUPPLEMENT STATUS (maintained COMPANY-SIDE):
The steps above name company-side obligations in scattered "COMPANY MUST SUPPLEMENT" /
Track-2 notes; this table consolidates the trackable ones so you can see at a glance whether
the live load is done. The Status column is CANONICAL-COMPANY: the producer ships every row
`pending` (it cannot observe your graph) and NEVER flips one — you flip rows in YOUR copy as
work lands (`pending` / `in-progress` / `done` / `n-a`, with a date). On a re-port collision
KEEP YOUR statuses; producer edits only add rows or refine the done-means criteria.

| Row | Item (origin step)                                        | Status  |
|-----|-----------------------------------------------------------|---------|
| T1  | K2 LIVE attribution load — Track-2 (step 32)              | pending |
| T2  | FID -> seal_id reconciliation table wired (step 32)       | pending |
| T3  | ALIAS reconciliation table wired (step 32)                | pending |
| T4  | Real tier-5 manual CSVs, as needed (step 32)              | pending |
| T5  | P1 internal probes P0/P4 — unblocks P2 loader (step 31)   | pending |
| T6  | Docs Track-2: docs-fetch/docs-load vs real sources (16)   | pending |
| T7  | Live multi-DB Enterprise Neo4j deploy — G7 half (16)      | pending |
| T8  | M0 equivalence unblocks: A3 filename + B1 dot rule (29)   | pending |

Done-means (checkable — a row flips `done` only when ALL its checks hold):
- T1: `drydocs load-seal-attribution` run AFTER your Control-M jobs + SEAL reference loads
  (the §E sequencing precondition exits 2 otherwise); the printed coverage reconciles —
  matched + unmatched + pinned = eligible, exit 0 (the command exits 1 on violation);
  graph-tests/seal-attribution-coverage.yaml all 6 TCs green via graph_verify; THEN flip the
  map entry job-seal-app-ref confirmed -> applied in config/taxonomy-ontology-map.yaml — that
  flip is the durable record of T1 (`applied` = a loader has written the graph). Unmatched
  facts do NOT block done — §B: they are surfaced on the JobRun, never silently dropped.
- T2/T3: the reconciliation table is sourced and wired into TierReconcilers at the CLI
  (both tiers ship EMPTY — facts count unresolved, never guessed); done when that tier's
  facts resolve in coverage. After wiring, RE-RUN T1's load — edges MERGE idempotently and
  newly resolvable jobs attribute on the re-run.
- T4: real CSVs under internal/ + YOUR manifest entries (replaces_with REQUIRED, never from
  a port); `drydocs load-manual-mappings` clean; coverage TC-06 manual-node stamps green.
  Flip `n-a` if automation coverage suffices and no manual pins are needed.
- T5–T8: done-means live in their origin steps (31 / 16 / 16 / 29 respectively) — this table
  only carries their status so one section answers "what is still owed company-side".

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable, no production sample present):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Expect 90 passed, 3 skipped — the four variable-stream files give 86 passed / 3 skipped (the 3
  skips are sample-backed test_sample_*, which skip when the .gitignore'd production CSV is absent),
  plus 4 from the stdlib core/component boundary guard (test_module_boundary.py, ADR 0002-a Phase A;
  pure stdlib, no data — includes the default-deny test_every_module_is_classified and the
  entrypoint-exemption test from Epic H6). A FileNotFoundError on controlm_variables__sample.csv
  means the skip guard was lost — fix it.
- Full `pytest tests/unit/` must be green (passes + sample-skips + the PyYAML test_schema.py
  skips). ZERO failures is the contract. Now also covers the docgen tests (test_doc_outline /
  test_design_doc / test_doc_pdf), the newer-stream tests (test_bmc_docs, test_source_mappings,
  test_row_checksum, test_transcribe_doc_markup, test_port_manifest, test_taxonomy_ontology_map)
  AND the remediation suites (step 29: test_remediation_scaffold / _m0 / _tier1 / _handoff /
  _no_graph_write / _corroborate — synthetic fixtures, no network/DB). All portable: stdlib +
  PyYAML, the committed BMC corpus under external/, no network/DB.
  test_schema.py expects EXPECTED_CONSTRAINTS = 40 (steps 19 + 22; UNCHANGED by steps 25-32 — the
  Epic P loaders are not built yet, remediation loads nothing, the step-31 gate session flips
  config statuses only, and the step-32 K2 loader writes edges only) and a supplement block for the
  4 active `docs_*` edges + the step-32 m3_seal_app_ref WAS_ASSOCIATED_WITH block;
  test_bmc_docs pins EXPECTED_DOC_COUNT = 27 (step 22). Both CI guards
  must pass: test_schema.py (no `active` relationship without its supplement block) and
  test_classification.py (every source in source-registry.yaml has a valid sensitivity
  classification). New dep: PyYAML.
  Producer-side reference: 483 passed / 3 skipped at the step-28 relocate head;
  516 passed / 3 skipped at the step-29 remediation head (2026-07-10);
  588 passed / 6 skipped / 3 deselected at the step-31 gate-session head (2026-07-14 — the 3
  deselected are the J9 testcontainers e2e without Docker; 3 of the 6 skips are the J7 reconcile
  guards, which RUN consumer-side once RECONCILE_BEFORE_DIR is set);
  625 passed / 6 skipped at the step-32 K2-loader head (2026-07-14 — +37 attribution/manual-loads
  tests; same deselect/skip structure). Step-31/32 coupling reminder: source-registry confirmed
  flips + audit-fields stubs + LEDGER_PENDING + the test_source_registry gate-state pins move as
  ONE unit.

BOUNDARIES:
- One-way only. Never add company main as a remote on the producer; never push back to
  ce-wilson/DryDocs.
- drydocs/data/ is .gitignore'd — sample CSVs stay local, never transfer.
- Never commit real SIDs, credentials, server addresses, GHE org names, or production data
  values; internal/ is the only home for confidential data and is stripped on publish
  (PUBLISH-BOUNDARY.md).
- The producer versions on its own cadence (v0.3.0, step 24): never overwrite the company's
  pyproject version string and never import the producer's git tags.
- When done, open drydocs-port as a PR onto company main; do not fast-forward main directly.
```
