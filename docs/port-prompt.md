# Port prompt — producer → company (rolling)

**Format (v2 rolling, 2026-07-21):** this prompt carries only (1) the durable
guardrails and (2) the step ledger SINCE the last completed port. The full historical
steps 1–42 (everything through producer head `6fd3270`) are frozen in
[`port-prompt-archive-steps-1-42.md`](port-prompt-archive-steps-1-42.md) — any external
reference to "port-prompt step N" for N ≤ 42 resolves there; numbering continues here
at 43. When a port completes company-side: update **Last completed port**, fold any new
standing divergences into the ledger, and collapse the applied steps into a one-line
entry under **Last completed port** (pointer to the PORT-REPORT). The steps-1-42
archive is FROZEN — applied steps ≥43 are summarized here, never appended there; their
full text survives in git history and the company PORT-REPORT.

Authorities are unchanged: [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml) is the WHAT
(per-path disposition, first-matching-glob-row wins); [`git-readme.md`](../git-readme.md)
is the WHY + the acceptance oracle; this prompt is sequencing + delta context only.

## Last completed port

- **Producer head `6fd3270`** (2026-07-21), applied company-side as
  **PORT-REPORT-6fd3270** — branch `drydocs-port-20260721`, backup tag
  `pre-cewilson-port-20260721`; 95-commit super-range via scoped tree-reconcile,
  168 files.
- **Producer review verdict (2026-07-21): clean.** Verified exact against producer git:
  range count (95); backlog recompute (producer 18/1/0/121 at head + re-inserted
  DD1/DD2/DD3 = 21/1/0/121, 143 items); EXPECTED_CONSTRAINTS arithmetic (company 52 =
  base 44 + 2 K4 + 6 traceability vs producer 48 = base 40 + 2 + 6 — the shared K4 pair
  correctly NOT double-added); manifest adherence (snapshots excluded, derived artifacts
  regenerated post-config-edit, union-appends append-only, per-entry files never
  whole-file checked out, canonical-company preserved). The hermetic oracle-kerberos
  `_MODULE_DIR` fix retired the standing known non-port failure from prior reports.
- The review's findings are folded into this document: the standing-divergences ledger,
  the Tier B hold in step 43, and the owed-company-side items below.

```text
You are porting the DryDocs PRODUCER repo (ce-wilson/DryDocs, github.com) onto the
company <company-org>/DryDocs base (GitHub Enterprise). ONE-WAY producer→consumer
apply. Work in a clean checkout of company `main`.

GUARDRAILS (durable — apply to every port):

1. AUTHORITIES FIRST: read `git show cewilson/main:PORT-MANIFEST.yaml` (disposition per
   path — first matching glob row wins; unmatched paths: clean-add if absent
   consumer-side, evaluate if both sides created it) and
   `git show cewilson/main:git-readme.md` (narrative WHY + acceptance oracle) BEFORE
   touching anything. Do not improvise around them.

2. DISJOINT HISTORIES: no common ancestor exists — never `git merge`/`git pull`.
   Small ranges: cherry-pick / `git am --3way`, resolving collisions per manifest.
   Ranges dominated by chore(ritual)/derived-file commits: scoped TREE-RECONCILE —
   classify every path in `git diff <last-ported-head> <new-head>` by manifest
   disposition, apply, regenerate derived artifacts company-side, validate BEHAVIOR
   (the PORT-REPORT-6fd3270 pattern). Bytes are never the contract.

3. BRANCH MECHANICS: `git fetch cewilson main`; tag `pre-cewilson-port-<date>` on
   company main; `git switch -c drydocs-port-<date> main`. NOT pushed until reviewed;
   land as a `--no-ff` merge or PR; never fast-forward company main; NEVER push back
   to cewilson.

4. ALWAYS EXCLUDED: `knowledge/depgraph-snapshots/*.json` — producer-local derived
   artifacts with producer git metadata; regenerate your own via the session-end ritual.

5. DERIVED ARTIFACTS regenerate AFTER all config edits, never hand-merge:
   `web/src/generated/gates.json` + `enforcement-matrix.json` (their render scripts),
   `docs/plan/board.html` (from the reconciled backlog), `docs/design/*.html` +
   `*.print.html` (YOUR canonical-company renderer, both variants tracked).
   Run render scripts from the PROJECT VENV with PYTHONPATH=repo root and verify the
   output path resolves into the workspace repo before trusting any regen. Beware
   NTFS junctions: the company workspace path is a junction and Path.resolve()
   follows it, so correct outputs can REPORT a foreign-looking path (2026-07-21
   incident — first misdiagnosed as a second checkout; same repo, two path spellings).

6. GATE ADOPTION DOCTRINE (two-tier — SME-ruled in-chat 2026-07-21, prompted by
   PORT-REPORT-6fd3270 adopting the producer L7 doc-traceability gate):
   - Tier A — the company holds NO signed position on the subject: a port MAY adopt a
     producer-signed gate outcome (config status flips, vocab activations) provided ALL
     of: (a) the same SME signed the producer gate; (b) the port verifies
     company-context compatibility (reconcile guards + full suite green, checks
     documented in the PORT-REPORT); (c) a short RATIFICATION ENTRY lands in the
     COMPANY gate-log — subject, producer gate reference, checks performed, sign-off.
     A port report is evidence, not a gate ledger. Precedent: the L7 adoption in
     PORT-REPORT-6fd3270.
   - Tier B — the company holds ITS OWN signed position on the subject: adoption is
     PROHIBITED; a full company gate session must supersede-or-reconcile before (or
     instead of) the flip.
   - Graph WRITES are always yours regardless of tier (tracker T9): adoption can flip
     config status, never substitute for load verification against the company graph.

7. RECONCILE GUARDS: full unit suite green PLUS the J7 reconcile guards with
   RECONCILE_BEFORE_DIR set (proves no active/confirmed/applied downgrade, no dropped
   per-entry rows, gate-log append-only). Per-entry files (relationship_vocabulary,
   taxonomy-ontology-map, backlog) are resolved BY ID, never whole-file checkout;
   summaries recomputed exactly as their guard tests do.
   GUARD SCOPE: the no-downgrade guards are PORT-scoped — run them across port
   commits only, never across a GATE commit (a gate legitimately deprecates/rejects;
   the guards false-positive on those authorized downgrades — the gate-log entry is
   the authority there). Established at the T12 enactment, 2026-07-21.

8. WRITE A PORT-REPORT-<head>.md in the PORT-REPORT-6fd3270 pattern (source &
   mechanism, clean-applies, collisions + resolutions, company-side adaptations,
   deliberately deferred, acceptance numbers, manifest adherence, state/reversibility,
   NEW divergences observed). The producer reviews it against producer git.

9. BOUNDARIES: one-way only — never add company main as a remote on the producer,
   never push back to ce-wilson/DryDocs. drydocs/data/ sample CSVs stay local. Never
   commit real SIDs, credentials, server addresses, GHE org names, or production data
   values; internal/ is the only home for confidential data (PUBLISH-BOUNDARY.md).
   Never overwrite the company pyproject version string; never import producer git tags.

STANDING DIVERGENCES LEDGER (expected collisions — resolve as stated, do NOT "fix"):
- README.md: company one-line footer stays (producer's lives at internal/repo-README.md).
- .github/**: adapt-rather-than-adopt — company CI/workflow config wins.
- scripts/render_enforcement_matrix.py: company carries 4 company-only SURFACES rows
  (graph-tests/, ingestion-config.yaml, knowledge-scan-keywords.yaml, go-links.yaml)
  and drops the producer-only test_publishing.py guard (PORT-REPORT-6fd3270 adaptation).
  Re-apply the company adaptation on every collision. Producer back-flow candidate:
  make the SURFACES registry data-driven so the script returns to canonical-producer.
- tests/unit/test_doc_traceability_loader.py: two assertions pinned to the company's
  ahead controlm-ingestion-tdd.md (9 matrix rows incl. NFR-CMI-002). Keep company pins.
  Producer back-flow candidate: derive expected counts from the doc under test.
- EXPECTED_CONSTRAINTS: company 52 vs producer 48 (company base +4 from local
  consolidation; both sides added the 2 K4 constraints independently). Evaluate counts
  company-based every port; never double-add a shared addition — the K4 precedent.
- Canonical-company set (manifest rows): controlm-ingestion-tdd.md, the design_doc
  renderer output, review internals (drydocs-review back-flow stream), oracle_adapter,
  company sources/supplements. Producer touches = drop the incoming side.
- docs/restructure/IDEAS.md union-superset: the company copy retains blocks the
  producer already groomed into backlog items G18–G25. Before any company groom pass,
  annotate those retained blocks "groomed producer-side → G18..G25" (or check the
  ported backlog first) — prevents double-capture as duplicate items.
- Vocab prose on REQUIRES_SCHEDULER / seal_requires_scheduler / reg_uses_software +
  the requires-scheduler map open questions: names have diverged across repos; entries
  stay planned/proposed (inert). Resolve at the company platforms gate (step 43), not
  by editing.

OWED COMPANY-SIDE (from the 6fd3270 review):
- L7 RATIFICATION ENTRY in the company gate-log (Tier A adopted-via-port; paste-ready
  snippet provided in the producer session 2026-07-21 — subject: 6 doc_* edges + 6 doc
  node classes active, doc-traceability-feedback confirmed; references producer gate
  0252d29 via PORT-REPORT-6fd3270).
- TRACKER (T1–T8 origin steps live in the archive; statuses tracked here):

| # | Item | Status |
|---|------|--------|
| T1  | K2 live attribution load + job-seal-app-ref confirmed→applied flip | pending |
| T2  | FID→seal_id reconciliation table sourced + wired (TierReconcilers) | pending |
| T3  | ALIAS reconciliation table sourced + wired | pending |
| T4  | Real tier-5 manual CSVs under internal/ + own manifest entries | pending |
| T5  | P1 internal probes P0/P4 — unblocks P2 loader (archive step 31) | pending |
| T6  | Docs Track-2: docs-fetch/docs-load vs real sources (archive step 16) | pending |
| T7  | Live multi-DB Enterprise Neo4j deploy — G7 half (archive step 16) | pending |
| T8  | M0 equivalence unblocks: A3 filename + B1 dot rule (archive step 29) | pending |
| T9  | Lineage curated live load — YOUR vocab gate + m3_* flips, then write_curated on your graph | pending |
| T10 | MAC field contract validated vs a REAL DPL export — amend dpl_mac.py contract + fixtures together | pending |
| T11 | L7 ratification entry in company gate-log (Tier A record; see above) | pending |
| T12 | Company platforms gate: 06-29 AIS position vs producer C12 — supersede-or-reconcile (Tier B, gates step 43's flips) | pending — session pack ready: [`port-T12-company-gate-pack.md`](port-T12-company-gate-pack.md) (2026-07-21); post-sign-off sweep prompt: [`port-T12-ais-excision-company-prompt.md`](port-T12-ais-excision-company-prompt.md) (2026-07-25). **Observed company-side 2026-07-24:** `Ais*` live in `drydocs/controlm_app_codes.py` / `load controlm_app_codes` — a loader referencing `USES_TOOL` may falsify the pack's "declared only, zero edges" premise; count edges before ruling deprecate-vs-remove |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending |
| T14 | rua collector convergence: company's own -n implementation (observed 2026-07-20, internals unseen) vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible | pending |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section. T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10: until a real per-pipeline MAC export parses with zero mismatches,
  treat pipeline.json/dataset_flow field names as ASSUMED.

STEP LEDGER — delta since `6fd3270` (numbering continues from the archive):

43. C12 PLATFORMS-TAXONOMY STREAM (`6fd3270..cewilson/main` — compute the range live at
    port time; it is still growing). Known at 2026-07-21 pm:
      3af2538  chore(backlog): groom — 3 promoted (C13 SchedulerKind-retirement build,
               C14 batch-port USES_SOFTWARE migration promoted into next_ready)
      603acba  feat(gates): C12 platforms-taxonomy gate SIGNED OFF — SchedulerKind
               retires into the registry model (touches config/taxonomy/platforms.yaml,
               gate-log, backlog, gates.json, enforcement-matrix.json)
      bea7159  chore(ritual): snapshot (EXCLUDED class — guardrail 4)
      74716cf  docs(port): gate-adoption doctrine
      27102d6  feat(ontology): C13 DONE — SchedulerKind retirement build (seeds retired
               audit-kept; seal_requires_scheduler deprecated/superseded; map entry
               closed rejected/superseded; Ais* straggler sweep) — Tier B-gated by T12
      2adec42  feat(load): C14 DONE — batch_port_orchestrator loader, live-verified
               producer-side (edge MERGE keyed {source:'batch-port'}; software_registry
               .cypher hardened to key {source:'registry'}) — code ports normally;
               RUNNING it company-side is T12-gated + T9 (your graph, your verify)
      fb8ac23  chore(ritual): snapshot (EXCLUDED class — guardrail 4)
      + the port-prompt v2 rolling restructure, docs/port-T12-company-gate-pack.md
        (T12 session materials — clean-add), and any later commits.
    *** TIER B HOLD ***: the company holds its OWN signed position on platforms — the
    2026-06-29 AIS gate (AisCapability skos:Concept / AisTool prov:SoftwareAgent,
    USES_TOOL + IN_CAPABILITY) — which C12's registry-model ruling contradicts.
    Per guardrail 6 Tier B: DO NOT flip platforms semantics via this port. Hold a
    company gate session FIRST (tracker T12) to supersede-or-reconcile, then apply.
    Mechanics:
    - config/gate-log.md: union-append producer's C12 entry as usual — append-only is
      safe; it RECORDS the producer decision without enacting it company-side.
    - config/taxonomy/platforms.yaml + any C12-driven vocab/registry status effects:
      HOLD until T12 rules. If the tree-reconcile needs the file to move, land the
      producer content on the port branch but keep company semantics authoritative
      until the gate — state the hold explicitly in the PORT-REPORT.
    - backlog.yaml: per-entry as always; C12 arrives done, C13/C14 arrive todo —
      re-insert company DD-series, recompute the summary exactly as test_backlog does.
    - C13/C14 build commits (SchedulerKind retirement, USES_SOFTWARE migration) are
      producer-side follow-ups that will land in this range — they are Tier B-gated
      company-side by the same T12 ruling.
    Producer-side reference at 74716cf: 833 passed / 4 skipped (tests/unit);
    at 2adec42 (C13+C14 landed): 840 passed / 6 skipped.

44. UI ACCELERATION STREAM (2026-07-23; hashes are post-rebase onto `b6296ae`, as
    pushed). Merge `e185241` (--no-ff, 3 commits: `4d3ceba` theme pass, `4b7b490`
    /under-the-hood route, `e3b3663` dead-route cleanup) + `955df1f` docs +
    `53ff1e5` IDEAS capture + `4ca8878` (this step + manifest row). All web/** + UI-WIP/** = canonical-producer (step 31 rows):
    clean-apply, NO Tier B interaction, no gate adoption involved (read-only console,
    O20 untouched — the build was a producer-side intended bypass, recorded in IDEAS).
    Mechanics/notes:
    - web/: additive components (HeroArt, StatTiles, underhood/*) + edits to
      Overview/Header/Aside/graph panes + DELETES web/src/routes/SkeletonModuleRoute.tsx
      (dead code). Zero new npm deps — package.json/lock unchanged; company `npm ci &&
      npm run build --prefix web` is the acceptance check (producer: tsc+vite clean,
      oxlint no new warnings). web/src/generated/* untouched by this range.
    - web/src/underhood/benchmarkData.ts: fixture HAND-CARRIED from the committed P0
      verdict (knowledge/upgrade-plans/docmeta-p0-verdict.md). Port as-is; re-running
      the benchmark against the COMPANY corpus is Track-2 work (see
      UI-WIP/two-track-ui-plan.md), not a port step.
    - internal/context-graph-analysis/** : NEW manifest row (canonical-producer,
      private-remote-only). Content is analysis OF the company's own incubator repos —
      fine on GHE, never public.
    - UI-WIP/two-track-ui-plan.md: clean-add; it defines the producer/company UI seam
      (producer owns components+fixtures; company owns QuerySpec data + env) — read it
      before planning any company-side UI work so surfaces don't collide.
    Interleaved docs/ontology commits since fb8ac23 (`a4e7e15`, `9343d9b`, `1cc627b`,
    `c1ee13f`) remain part of step 43's live-computed range and its Tier B hold rules.

45. LINEAGE + RUA/DPL CHAIN + EPIC R STREAM (2026-07-23; `4ca8878..bf33c8a`, 27
    commits, pushed). Six distinct sub-streams — they port DIFFERENTLY:
    a. EPIC R / AGENTIC Q&A (`1a89047` ADR 0007 draft, `6f3164e` groom 8 promoted,
       `b4d1188`, `bfa0240` R1 gate SIGNED OFF — ADR 0007 ACCEPTED, `8c5deb8`,
       `00ee729` + `a739d3a` R2 graph_qa Tier-0/1 live-verified): clean-apply.
       Gate adoption: Tier A (no company position on agentic Q&A) — ratification
       entry per guardrail 6; the R2 live smoke is YOURS to re-run against the
       company graph + api_server env (T9 spirit — producer live-verify never
       substitutes).
    b. C13 COMPLETION SWEEPS (`575269a` one-time migration dropped, `9d9aef2`
       SchedulerKind leftover sweep; wipe-and-rebuild doctrine): *** Tier B-gated
       by T12 *** — same hold as step 43's C13/C14. Union-append the log trail;
       do not enact platforms semantics before the T12 ruling.
    c. PHASED-LOADER REVERSE PORT (`1b7744f`, `12bc94e` TDD Rev 4, `df31354`
       --no-ff merge): this stream came FROM your Rev 6 — the first
       company→producer reverse port. RECONCILE/SKIP: expect near-no-op on
       drydocs/loaders/** + cli; controlm-ingestion-tdd.md is canonical-company
       (drop incoming per the standing ledger). Producer-only residue: sample
       CSV slimmed (stays local per guardrail 9), smoke.ps1 count, vocab/
       supplement prose (per-entry as always).
    d. FOLDER PROPERTY DIET (`c1c3a0a` loader change, `0b6c9b5` TDD Rev 5): NEW
       for you — the 2026-07-23 SME ruling (naming-convention decode OFF folder
       nodes; app_code KEPT as the join key; f.lob='Retail' collided with the
       org-taxonomy LOB). Code ports normally; gate-log union-append carries the
       ruling + Tier A ratification entry; your canonical-company TDD needs its
       OWN rev documenting the diet (producer Rev 5 content is the source);
       no migration — your rebuild goes wipe-and-rebuild via bootstrap
       (per-folder `--phase nodes`, then one unscoped `--phase relationships`).
    e. MAC CLONE LAYOUT + RUNBOOK Rev 2/3 (`4e77c1c` name#guid discovery /
       per-folder scope / swagger work list, `2cc7692`, `41c4879` + `bed3ee0`
       clone-authority caveat — main lags, by-SEAL bulk = backup discovery,
       `bfac053` + `793fc5d` IDEAS): clean-apply; runbook .md ports, .html
       regenerates (guardrail 5). Fixes the runbook's wrong SQL path
       (drydocs_core/... → drydocs/loaders/sql/controlm_jobs.sql) and pins the
       curated-load step to the psgmgr-shaped graph.
    f. RUA/DPL CHAIN G18+G20+G25 (`78651f3` collector v2 -n script capture,
       `db3ca3f` bundle extractor, `bf33c8a` dpl-registry ingestion +
       cross-check): G20/G25 clean-add (staging-only, NO graph writes; G22 is
       the activation gate). G18 is RECONCILE-DON'T-CLOBBER: you already run
       your own -n implementation (tracker T14) — converge before mixing
       bundles. source-registry.yaml gains dpl-registry (confirmed:false, G22
       f/g) — per-entry apply + regenerate the enforcement matrix YOUR side.
       dpl_registry.py's field contract is ASSUMED until a real per-SEAL export
       validates it (tracker T13; the cross_check clone-lag column is where
       your stale-main measurement comes from).
    Snapshots in the range (`46f83ba`, `b5c5332`, `be5dd87`) are EXCLUDED class
    (guardrail 4). backlog.yaml per-entry: Epic R items arrive (R1/R2 done),
    G18/G20/G25 arrive done; re-insert company DD-series, recompute the summary
    exactly as test_backlog does. Producer reference at `bf33c8a`:
    900 passed / 6 skipped.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable, no production sample present):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference: 90 passed / 3 skipped (sample-backed tests skip without the
  gitignored production CSV). Company baseline is ABOVE this (113 at the last port) —
  compare against your own prior report, not the producer floor.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR).
  Producer reference at the current head (step 45, `bf33c8a`): 900 passed /
  6 skipped (step-43 head 2adec42 was 840 / 6).
  Company reference at the last port: 1174 passed / 21 skipped / 0 failed.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (9 at the last port).
- Historical per-step producer counts (483 → 831 across steps 28–42): archive file.
```
