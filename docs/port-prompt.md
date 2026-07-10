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
  test_design_doc / test_doc_pdf) AND the newer-stream tests (test_bmc_docs, test_source_mappings,
  test_row_checksum, test_transcribe_doc_markup, test_port_manifest, test_taxonomy_ontology_map)
  — all portable: stdlib + PyYAML, the committed BMC corpus under external/, no network/DB.
  test_schema.py expects EXPECTED_CONSTRAINTS = 40 (steps 19 + 22; UNCHANGED by steps 25-27 — the
  Epic P loaders are not built yet) and a supplement block for the 4 active `docs_*` edges;
  test_bmc_docs pins EXPECTED_DOC_COUNT = 27 (step 22). Both CI guards must pass: test_schema.py
  (no `active` relationship without its supplement block) and test_classification.py (every source
  in source-registry.yaml has a valid sensitivity classification). New dep: PyYAML.
  Producer-side reference at this range head (2026-07-10): 483 passed / 3 skipped.

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
