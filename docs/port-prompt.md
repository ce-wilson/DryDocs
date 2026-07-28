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
   path — first matching glob row wins; `**` spans separators, `*`/`?` do not) and
   `git show cewilson/main:git-readme.md` (narrative WHY + acceptance oracle) BEFORE
   touching anything. Do not improvise around them. Coverage is EXPLICIT since J16
   (2026-07-28): a path matching no row is legitimate only if listed under
   `default_ok:` with a reason; a path in NEITHER is an un-made decision, not a
   clean-add — stop, decide it, and send the row back (guarded by
   test_port_reconcile_guards.py::test_no_tracked_path_falls_through_silently).

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
- EXPECTED_CONSTRAINTS: company 52 (at the last port) vs producer 51 at `947920c`
  (48 at 6fd3270 → 49 across the step-45/46 ranges → 51 after G33: +project_id
  +codemodule_file_id). Company base carries +4 from local consolidation; both sides
  added the 2 K4 constraints independently. Evaluate counts company-based every port;
  never double-add a shared addition — the K4 precedent. Adopting the G33 stream
  (step 47b) adds the same 2 company-side.
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
| T12 | Company platforms gate: 06-29 AIS position vs producer C12 — supersede-or-reconcile (Tier B, gated step 43's flips) | **RULED — SUPERSEDE, 2026-07-21, company `config/gate-log.md`.** Evidence (producer review 2026-07-27, company Control-M Initial-Load Runbook): step 7b reads "AIS platform catalog — RETIRED (T12 company platforms gate, SUPERSEDE, 2026-07-21)" — the `:AisCapability` / `:AisTool` class layer is superseded by the software-registry model (role over class), the seeds are commented-out audit tags, `apply-platforms-supplement` is a NO-OP on a fresh graph and no longer a prerequisite. Excision APPLIED: step 10 confirms `USES_TOOL` → `:AisTool` retired from the app-code link, the edge landing on `USES_SOFTWARE {source:'batch-port'}` via C14. **This also closes the 2026-07-24 open question** ("`Ais*` live in the app-code loader may falsify the pack's declared-only premise — count edges first"): the retirement is applied, so the premise no longer matters. **Tier B holds in steps 43 and 45b are DISCHARGED.** Session materials (`port-T12-company-gate-pack.md`, `port-T12-ais-excision-company-prompt.md`) retired from the tree 2026-07-27 — spent; recoverable from git history if the ruling is ever re-litigated |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending |
| T14 | rua collector convergence: company's own -n implementation (observed 2026-07-20, internals unseen) vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible | pending |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways — each side loads its own; run it from the primary on-main checkout, never a worktree, or abs_path pollutes) → `drydocs load-code-snapshot` into your graph. A second `:Project` root is ruled INTENDED (gate §B3(a)). Rides with the Tier A ratification entry for the gate itself (guardrail 6) | pending |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 temporary staging stand-in as the feed (the G40 Python parse stays as the cross-check); the premise correction is already folded into G22 prep (step 47c) | pending |

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
      + the port-prompt v2 rolling restructure, and any later commits.
        (The T12 session materials that were a clean-add here have since been
        RETIRED producer-side — step 46i / the T12 tracker row. Do NOT clean-add
        them: they were spent by the company's own 2026-07-21 ruling, and a range
        computed live at port time will show them added then deleted. Net: absent.)
    *** TIER B HOLD — DISCHARGED 2026-07-27 ***: the hold existed because the company
    held its OWN signed position on platforms — the 2026-06-29 AIS gate (AisCapability
    skos:Concept / AisTool prov:SoftwareAgent, USES_TOOL + IN_CAPABILITY) — which C12's
    registry-model ruling contradicts. **T12 has since RULED: SUPERSEDE, 2026-07-21**
    (company gate-log; see the tracker row). The company's own position now MATCHES
    C12's registry model, and the excision is already applied company-side. Apply this
    stream NORMALLY — no gate session to convene, nothing to hold. Historical record of
    the hold kept here deliberately: the PORT-REPORT for this range should say the hold
    was discharged by a company ruling, not silently dropped.
    Mechanics (post-discharge):
    - config/gate-log.md: union-append producer's C12 entry as usual (append-only).
      The company's T12 entry already stands alongside it — both records, no conflict.
    - config/taxonomy/platforms.yaml + C12-driven vocab/registry status effects: apply
      normally. NOTE the producer has since excised the Ais* capture entirely
      (`15c9d3f`, step 46i) — reconcile against a company file that has already had its
      own excision applied; expect near-no-op rather than a large diff.
    - backlog.yaml: per-entry as always; C12 arrives done, C13/C14 arrive todo —
      re-insert company DD-series, recompute the summary exactly as test_backlog does.
    - C13/C14 build commits (SchedulerKind retirement, USES_SOFTWARE migration) are no
      longer Tier B-gated. C14's loader has also been HARDENED since (step 46d): it now
      REFUSES when either endpoint registry is absent, so a company run against a graph
      missing :SoftwareProduct or :BusinessApplication fails loudly instead of writing
      nothing and reporting OK. Read that before scheduling the first company run.
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
       SchedulerKind leftover sweep; wipe-and-rebuild doctrine): *** Tier B hold
       DISCHARGED 2026-07-27 *** — T12 ruled SUPERSEDE 2026-07-21 (tracker row +
       step 43). Apply normally; union-append the log trail as usual.
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

46. IDENTITY GATE + BOUNDARY HARDENING + LOADER REFUSALS (2026-07-23 → 2026-07-27;
    `bf33c8a..78ba7fd`, 58 commits, pushed). Ten sub-streams; APPLY IN THE ORDER
    BELOW — **(a) is deliberately first and is not optional.**
    COMPANION: `docs/port-step46-company-prompt.md` is the hand-off prompt for the
    executing company session — it carries the three corrections below in one place.
    Producer-side hand-off material like the retired T12 packs: PASTE it, do not
    clean-add it; retire it once the PORT-REPORT is written.
    HEAD NOTE (corrected 2026-07-27): this entry first declared the range end as
    `0ce7333`; the true end is `78ba7fd`. The tail matters — `5bb606f` (this ledger
    entry) ALSO repointed `config/taxonomy/platforms.yaml`, which is
    canonical-producer and carries the T12 provenance pointer, so stopping at
    `0ce7333` silently drops the T12 follow-through step 43 describes. **Do not pin a
    hash from this document at all** — it goes stale the moment the producer commits
    again (it already did once: `378f4ba` carries the manifest's new never-port rows,
    which the company NEEDS). Take whatever `ce-wilson/main` is at port-run time and
    record that exact hash in the PORT-REPORT. The only other tail content is `IDEAS.md`
    (union-append), one struck row in `docs/reviews/doc-inventory-2026-07-22.md`,
    this document (producer instruction doc, never ported), the two deleted
    `docs/port-T12-*.md` (see step 43 — do NOT re-add), and one snapshot (EXCLUDED).
    a. *** APPLY FIRST — PUBLISH-BOUNDARY HARDENING *** (`105aa9c` p0 sweep,
       `4d0f375` J14 split, `36ae382` J14 follow-up relocate, `68acf7d` J15
       value-shape guard + 14-value resweep): real SEALIDs found INSIDE prose and
       folder-name strings in the publishable tree, moved to internal/, and a new
       guard that matches on the VALUE SHAPE rather than the field name (a prior
       cleanup missed them because it swept field names). Reserved synthetic block
       70001-70099 is the substitute range. Apply before ANY other sub-stream: these
       commits change what is ALLOWED to cross the boundary, and landing later
       content first risks re-importing exactly what the guard exists to catch.
       Company-side the guard is additive — run it against your tree and expect it to
       find things; that is the point, not a port failure.
    b. S3 — BUSINESSAPPLICATION IDENTITY GATE, SIGNED OFF (`a3dd2fe` draft, `bbe29fb`
       v2 premise correction, `9e459c1` park, `d4940b2` v3 source-field-name axis,
       `b1d1b8d` v3.2 two-part naming rule, `57a094e` v3.3, `fc15191` SIGNED OFF,
       22/22). Ruling: **`seal_id` → `app_id` on the canonical node**, plus the
       TWO-PART naming rule (identity is source-neutral; EVIDENCE keeps the source's
       own term) and the finding that SEALID was never a source field name.
       *** SCOPE — READ THIS BEFORE TREATING IT AS TIER B *** (narrowed 2026-07-27
       after a file-level check): the S3 series touches **ZERO loader files and ZERO
       `.cypher` files**. `fc15191` is gate-log + taxonomy-ontology-map +
       business-application.yaml + ADR 0010 + backlog.yaml + the two generated
       surfaces, and the commit says so outright — *"Nothing is written to the graph
       at the gate itself — S3 is now build work."* `seal_id` is still live in ten
       producer cypher files. So this sub-stream ports **the ruling and the build
       backlog**; there is no key rename in the range, and your live graph and
       app-code link path are untouched by applying it. Apply it as an ordinary
       canonical-producer sub-stream.
       THE TIER B RISK IS REAL BUT DEFERRED — it belongs to the BUILD, not this port.
       When the flip is eventually built, it touches your initial-load runbook's
       app-code link step (step 10), which parses seal_id out of each Control-M app
       code and MATCHes on it. The gate warns of two traps that bite on the rename
       itself: constraint NAMES do not follow property renames, and Neo4j uniqueness
       constraints IGNORE nulls, so a half-renamed population passes its constraint
       silently. §C already rules the path: **rebuild, not migrate** — dual-write plus
       a graph-test through phases 1–3, because a partial cutover SILENTLY DOUBLES the
       canonical node rather than failing. Company decides its own build timing and
       re-runs T1 then.
    c. GRAPH-INFRA G28/G29/G30 (`a34a52e` multi-database naming drift closed + guarded,
       `84d0480` ONE verified apply-supplements chain with the legacy verbs kept as
       aliases, `a99ed86` curated lineage lands in `drydocs`, not `ddlineage`).
       G29 TOUCHES YOUR RUNBOOK: the initial-load runbook calls the individual
       `apply-ontology-supplement` / `apply-seal-supplement` / `apply-catalog-supplement`
       / `apply-registry-supplement` / `apply-resource-pools-supplement` verbs. They
       SURVIVE as aliases so the runbook keeps working unchanged — but the single
       verified chain is the new canonical form and the runbook should be revised to it
       (your doc, your rev). G30 pins where curated lineage writes; reconcile against
       your own multi-DB topology before applying.
    d. LOADER REFUSALS — the "succeeds loudly, does nothing" family (`b7f4cae` Q8
       bmc-docs, `069312f` batch-port orchestrator). Loaders that joined a prereq node
       through OPTIONAL MATCH + FOREACH used to report status OK with rows processed
       while writing ZERO edges when the prereq registry was absent from the database
       entirely. Both now REFUSE before `_open_run`, so a refused load writes nothing —
       not even the :JobRun — and per-row misses are reported instead of dropped.
       DIRECTLY RELEVANT TO YOUR RUNBOOK: its own "Order matters / out-of-order rows
       silently drop on the MATCH" note documents this failure as accepted behaviour
       managed by operator discipline. These two loaders now guard it instead. The
       batch-port loader additionally had a flag-correctness bug fixed
       (`batch_orchestrator_unmapped` was keyed on the node lookup rather than the
       crosswalk result, so a missing registry wrote the WRONG diagnosis onto
       correctly-mapped apps while the CLI coverage report said they mapped fine).
       Producer-side sweep found the same idiom unguarded in `doc_traceability` and
       `doc_feedback` — NOT fixed, logged in IDEAS; check yours.
    e. P3 — HOSTS + DERIVED RUNS_ON (`9e51e8d`, gate controlm-hosts-topology): new
       `controlm_hosts` stage inside `ingest-controlm` plus a derived `runs_on_resolution`
       pass in the relationships phase (group match wins; UNMATCHED/NULL surfaced as
       coverage, never guessed). Your runbook's step 9 says "full M3 chain incl.
       derived deps" — after this, that chain is wider than the runbook describes.
    f. EPIC G LINEAGE G21/G24/G26 (`50c98d2` rua code-operations through the
       software-ontology mappers, `ac84ea0` code-repo source seam + server/repo
       corroboration on content hash, `9319c0f` launcher registry moves from
       code-resident to a schema-guarded config file). G26 flips the enforcement-matrix
       row from `unguarded` to guarded — regenerate the matrix YOUR side after applying.
    g. SEAL-APP-REF GATE v3 + COMPANION §G (`79b7213` companion section G, `356b373`
       PAT grain-keying §G6-RIDER + backlog C17/C18, `0ce7333` §G4-RIDER). GATE SPEC
       ONLY — it PROPOSES; nothing is enacted and no vocabulary or loader changes.
       Sign-off moved G→H; every existing id A1–F2 is unchanged so the external
       citations of §B / §C1 / §E2 still resolve. §G4-RIDER already encodes YOUR
       behaviour (the app-code step marks the BatchProcessing port active; activation is
       currently DERIVED, not declared), so it should read correctly on arrival — if it
       does not, that is a divergence worth reporting back.
    h. C17/C18 + THE NO-SHADOW GUARD (`99e38cb`): deleted `drydocs_core/models/catalog.py`
       — a stale shadow of all 8 catalog row models that had drifted past the C9 §d
       ruling — and added `tests/unit/test_no_shadow_definitions.py`, which fails on any
       public top-level class defined in two production modules.
       *** CHECK BEFORE APPLYING ***: producer-side NOTHING imported the shadow, so the
       delete was a no-op. If your tree imports `drydocs_core.models.catalog`, this is
       NOT a clean-apply — reconcile to one definition your own way, then let the guard
       enforce it. The guard itself may fail on arrival if you carry legitimate
       duplicates; add them to its ALLOWLIST with a written reason (it rejects
       reason-less entries).
    i. Q6 REOPENED + Ais* EXCISION (`806e5c3` acronym entry withdrawn from Class C and
       routed back as an open question, `15c9d3f` superseded Ais* capture excised from
       platforms.yaml). Ties to T12, now ruled — see step 43's discharged hold.
    j. DOCS / ADRs / GUARDS (`ac80132` pre-UI structure review + ADRs 0008/0009/0010,
       `698c367` executive overview rev 6, `aa11fb5` Databricks Unity Catalog research
       note, `73ee97a` internal companion note, `432ea43` two holes closed in the
       module-boundary guard, `9f5ebe1` + `76be07c` supplement review pass and the stale
       catalog-supplement docstring — 31 Role seeds, was "19", `6af87eb` new phase 16 +
       Epic U self-documentation, grooms `f9167a5` / `eeabf2b` / `a37043a` / `791a278`,
       IDEAS captures `220954e` / `39e1258` / `974ecb5` / `323a2f5`).
    Snapshots in the range (`b7111d9`, `64fa3e9`, `3ece9d7`, `01132e7`, `a3ac887`,
    `ff1be3b`, `abd67f6`, `9b7d83e`, `c0008df`, `c69a482`, `78ba7fd`) are EXCLUDED
    class (guardrail 4; now also a never-port manifest row). `7164ff5` is the step-45
    ledger entry and `5bb606f` the step-46 one — this document — but note that
    `5bb606f` is NOT docs-only: see the HEAD NOTE above.
    backlog.yaml per-entry: P3/G21/G24/G26/Q8/J14/J15/C18 arrive done, C17 arrives todo,
    new Epic U + phase 16, ids C17/C18 newly allocated; re-insert company DD-series and
    recompute the summary exactly as test_backlog does. Producer reference at `78ba7fd`
    (unchanged from `0ce7333` — the tail commits are docs/config only): 982 passed /
    6 skipped.

47. SELF-DOCUMENTATION GATE + PORT-CONTROL OVERHAUL + STAGING SEAMS (2026-07-27 →
    2026-07-28; `78ba7fd..cewilson/main` — compute the range live and record the
    exact head in the PORT-REPORT, the step-46 lesson; 52 commits to `947920c`
    known at 2026-07-28). Eight sub-streams; **(a) first — it rewrites the
    authorities this port runs under.**
    a. PORT-CONTROL + MANIFEST COVERAGE (`378f4ba` step-46 corrections + the
       depgraph never-port row, `bf3fd34` docs/port-*.md never-port, `0b7f391`
       J16, `fb0a612` J16-as-code, `f67e308`): PORT-MANIFEST.yaml is largely
       REWRITTEN (+~200 lines) — every top-level tracked path now has an explicit
       row, `default:` is legitimate only via `default_ok:` (guardrail 1, updated),
       and `test_port_reconcile_guards.py` gains the coverage + glob-semantics +
       backlog-no-regression guards (these run UNCONDITIONALLY, no
       RECONCILE_BEFORE_DIR needed). Read the NEW manifest before classifying
       anything else in this range. Company-side the coverage guard runs against
       YOUR tree: company-only paths it surfaces are un-made decisions to add rows
       for — findings, not port failures (the J15 spirit).
    b. G33 SELF-DOCUMENTATION CODE-GRAPH + EPIC U (gate
       `self-documentation-code-graph` SIGNED OFF 36/36 `c876b73`, spec walk
       `b46178d`/`fb0d4b5`, loader `7f5f1d3` — `drydocs load-code-snapshot`,
       LIVE-verified producer-side, v2 snapshot-schema accept `a45f124`, U1–U3
       persona reviews `6de57d9`, U4 skill `691cfb9`, U6 scanner blind-spot fix
       `047c319`): DryDocs' own source tree as a `(:Project {project_id:'drydocs'})`
       subgraph; first live use of the SWO layer. Gate adoption: Tier A (no company
       position on self-documentation) — ratification entry per guardrail 6.
       Schema effects: +2 constraints (project_id, codemodule_file_id) → producer
       EXPECTED_CONSTRAINTS 51 (ledger); vocab / map / audit-fields /
       source-registry (`depgraph-snapshot` arrives `confirmed: true` — the gate IS
       its confirmation) per-entry as always. THE LOADER'S INPUT IS NEVER-PORT:
       snapshot `*.json` stays each side's own — generate yours with the POST-U6
       instrument only (pre-U6 silently under-scanned: `279d84d` dropped such a
       snapshot, `fbff983` marks the scanner change in the README so the node-count
       jump is not read as growth) and load into YOUR graph; §B3(a) rules the second
       `:Project` root intended (tracker T15). Live-load verification is yours
       regardless of tier (T9).
    c. G39+G40 CMDLINE JOB-DETAIL STAGING (`4883778` build, `13a93a0` caveat v2 —
       resolved command lines ARE in scope as input; groom `3f7753f` folds a
       CM_DEF_VJOB_DETAIL premise correction into G22): temporary staging store +
       Python parse, a STAND-IN for the unbuilt psgmgr CM_DEF_VJOB_DETAIL.
       Staging-only, NO graph writes — G22 remains the activation gate. You own the
       real source: building the actual psgmgr table retires the stand-in feed
       (tracker T16); fold the premise correction into YOUR G22 session prep.
    d. P5 PATCH-WINDOW + EPIC P COMPLETE (`31dc41d` pushed claim, `db43baa` build):
       `drydocs patch-window --host|--group [--json]` — read-only committed cypher
       (asserted by test), busy time = interval UNION (critical-path extent, never
       a path sum — the TDQ-ETA rule, pinned by test), runtime outliers >=24h
       excluded + flagged, NODE_GROUP<->RUNS_ON cross-validation riding along as
       the remediation-feeder findings list. Producer verified STRUCTURE ONLY —
       the P4 timing supplement is company-side (your `15043cd`), so YOUR graph is
       the first place real patch windows appear; re-run the acceptance there.
    e. LOADER REFUSALS ROUND 2 + HYGIENE (`30bff33` L17, `36866f9` O33, `6dfab5e`
       shared-driver close, `d9c6644` e2e fixture onto Enterprise, `6b3fd76`,
       `422b141` O34): L17 closes EXACTLY the doc_traceability/doc_feedback
       unguarded-idiom gap step 46d told you to check — if you already patched
       yours, RECONCILE, don't clobber. O33: SchemaMeta exemplars can no longer
       contaminate QuerySpecs or the runs_on write path (`WHERE NOT n:SchemaMeta`
       is the standing anchor invariant). `6b3fd76` swaps httpx -> httpx2 for the
       TestClient transport — dependency change, evaluate against your own env;
       never overwrite the company pyproject version string (guardrail 9).
       `422b141` is web package-lock only.
    f. G41 GLUE BASE-TABLE INVENTORY SEAM (`b6dc6fe`): extractor + tests,
       nodes-only dataset population, staging — field contract ASSUMED until a
       real export validates it (the T10/T13 discipline: amend header + fixtures
       together, cite provenance).
    g. GENERIC SNOWFLAKE DATA-CATALOG PLAN (`985273e`): the sanitized twin —
       `<CATALOG>`/`AUTHORITY2` placeholders per the twin convention; your side
       reads it against the REAL curated views. Plan only, no code in this range;
       the G42–G44 backlog items encode the phases (extractor → cross-check → gate
       prompt); the DCAT dataset/distribution one-node-or-two question is the
       central gate decision and is deliberately NOT pre-decided.
    h. DOCS / CHORES: L16 startup runbook Rev 3 (`9a85fb9` — producer-local
       container names, adapt-don't-adopt), C19 `802f3fe` SWO anchor comment,
       home-db strays wipe `3bc461d` (producer-local graph op, no action for you),
       grooms `770f6dc` / `2905065` / `cedb3c6` / `3f8890a` (U5 executed in-run —
       Epic U closed 6/6), IDEAS union-appends incl. the depgraph-instrument
       capture chain (`fd2834d`, `5ad4bcc`, `947920c` — read these before trusting
       any snapshot diff: the instrument does not record its own scanner revision,
       and abs_path is machine/worktree-dependent).
    Snapshots in the range (`00e811b`, `403e10c`, `e99ff1f`, `a850b85`, `9113cc5`,
    `b2dc6ef`, `7ea6828`, `8f8de29`) are EXCLUDED class (guardrail 4 + never-port
    manifest row); `279d84d` deletes one producer-side (net no-op for you).
    backlog.yaml per-entry: G33/G39/G40/G41/L16/L17/J16/C19/O33/O34/U1–U6/P5/U5
    arrive done (Epic U complete 6/6, Epic P complete 5/5), G42/G43/G44/L18/L19/
    D8/J17 arrive todo; re-insert company DD-series, recompute the summary exactly
    as test_backlog does. Producer reference at `947920c`: 1070 passed / 8 skipped
    (production CSV absent on the measuring machine).

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable, no production sample present):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `947920c`: 114 passed / 3 skipped (sample-backed tests skip
  without the gitignored production CSV). Company baseline is ABOVE this (113 at the
  last port) — compare against your own prior report, not the producer floor.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR).
  Producer reference at the current head (step 47, `947920c`): 1070 passed /
  8 skipped with the production CSV absent (step-46 head 78ba7fd was 982 / 6;
  step-45 head bf33c8a was 900 / 6; step-43 head 2adec42 was 840 / 6).
  Company reference at the last port: 1174 passed / 21 skipped / 0 failed.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (9 at the last port;
  the guard file has since grown — the J16 manifest-coverage / default_ok /
  backlog-no-regression checks run unconditionally, no env var needed).
- Historical per-step producer counts (483 → 831 across steps 28–42): archive file.
```
