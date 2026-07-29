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

**Rolled 2026-07-29:** steps 43–48 collapsed (applied in PORT-REPORT-94132c80); the
live ledger is step 49 only. Step 49 additionally tags every sub-stream with its
producer-side VERIFICATION STATUS — `[SME-SIGNED]`, `[LIVE-VERIFIED]`, `[TEST-PINNED]`,
`[STAGING-ONLY]`, `[RECORD-CORRECTION]`, `[UNRULED]` — so the company review can spend
its attention on what is genuinely open instead of re-deriving what is already proven.
Anything not tagged confirmed is NOT confirmed; treat contracts as ASSUMED until your
side validates them (the T10/T13 discipline).

Authorities are unchanged: [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml) is the WHAT
(per-path disposition, first-matching-glob-row wins); [`git-readme.md`](../git-readme.md)
is the WHY + the acceptance oracle; this prompt is sequencing + delta context only.

## Last completed port

- **Producer head `94132c8`** (2026-07-28), applied company-side as
  **PORT-REPORT-94132c80** — covered producer range `6fd3270..94132c8`
  (steps 43–48 in full).
- **Producer review verdict (2026-07-28): accepted, with four findings — ALL FOUR
  back-flowed producer-side the same day** (`0c629e4` #1 dev-environment.yaml
  canonical-company entry_rule on both manifests; `855b09d` #2 live-capability test
  gated on config so `test_probe_instrument.py` stays byte-identical both sides;
  `f6b9ca0` #3 the O33 anchor invariant made unconditional on every QuerySpec +
  #4 the starlette-derived httpx/httpx2 pyproject test). Each was fixed at the RULE,
  not the instance — see step 49a for what that means on your side (mostly
  near-no-ops where you already patched by hand).
- The step-48 `config/dev-environment.yaml` caveat is **RESOLVED — do not re-decide**:
  the port ruled it canonical-company, the producer manifest carries the matching row,
  both sides agree. Each side keeps its own file; new producer KEYS are adapted by
  hand, never adopted; remote/URL values never cross (PUBLISH-BOUNDARY).
- Owed action **48e** from that report is now tracker row **T18** (your depgraph fork
  lacks the U6 resolver; `capability_assert: false` until it catches up).
- **Applied steps, collapsed** (full text: git history + PORT-REPORT-94132c80;
  Tier B holds in 43/45b were discharged by the T12 SUPERSEDE ruling):
  - 43 — C12 platforms-taxonomy stream (SchedulerKind → registry model; C13/C14).
  - 44 — UI acceleration stream (theme pass, /under-the-hood, two-track UI plan).
  - 45 — lineage + rua/DPL chain + Epic R (ADR 0007 accepted; R2 live; G18/G20/G25;
    folder property diet; MAC clone layout; phased-loader reverse port).
  - 46 — S3 identity gate (`seal_id`→`app_id` RULING only, build deferred) +
    publish-boundary hardening (J14/J15, apply-first) + loader refusals + G28–G30 +
    P3 hosts/RUNS_ON + G21/G24/G26 + seal-app-ref gate v3 §G + no-shadow guard.
  - 47 — G33 self-documentation code-graph (Tier A) + PORT-MANIFEST coverage
    overhaul (J16) + G39/G40 cmdline staging stand-in + P5 patch-window (Epic P
    complete) + L17/O33/O34 + G41 glue seam + Snowflake catalog plan.
  - 48 — DataLens UI + U7/U8 instrument self-policing (snapshot.ps1 REFUSES on an
    incapable sibling checkout) + D8 bootstrap constraint guard (port-first) +
    C15/C16/L18/J17 + depgraph fork consolidation (single `main`).

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
   `web/src/generated/gates.json` + `enforcement-matrix.json` (both now ride the
   default-paths board render — J17/J20 — so one `render_board.py` run refreshes all
   three), `docs/plan/board.html` (from the reconciled backlog), `docs/design/*.html`
   + `*.print.html` (YOUR canonical-company renderer, both variants tracked).
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

8. WRITE A PORT-REPORT-<head>.md in the established pattern (source & mechanism,
   clean-applies, collisions + resolutions, company-side adaptations, deliberately
   deferred, acceptance numbers, manifest adherence, state/reversibility, NEW
   divergences observed). The producer reviews it against producer git.

9. BOUNDARIES: one-way only — never add company main as a remote on the producer,
   never push back to ce-wilson/DryDocs. drydocs/data/ sample CSVs stay local. Never
   commit real SIDs, credentials, server addresses, GHE org names, or production data
   values; internal/ is the only home for confidential data (PUBLISH-BOUNDARY.md).
   Never overwrite the company pyproject version string; never import producer git tags.

STANDING DIVERGENCES LEDGER (expected collisions — resolve as stated, do NOT "fix"):
- README.md: company one-line footer stays (producer's lives at internal/repo-README.md).
- .github/**: adapt-rather-than-adopt — company CI/workflow config wins.
- config/dev-environment.yaml: canonical-company on BOTH manifests since
  PORT-REPORT-94132c80 (back-flow #1). Each side keeps its own file; new producer
  KEYS arrive as STRUCTURE to adapt by hand (surface the structural delta in the
  PORT-REPORT), values are always yours, remote/URL values never cross. The
  `depgraph.capability_assert` flag inside it is the T18 seam: false your side until
  your fork catches up.
- scripts/render_enforcement_matrix.py: company carries 4 company-only SURFACES rows
  (graph-tests/, ingestion-config.yaml, knowledge-scan-keywords.yaml, go-links.yaml)
  and drops the producer-only test_publishing.py guard (PORT-REPORT-6fd3270 adaptation).
  Re-apply the company adaptation on every collision. Producer back-flow candidate:
  make the SURFACES registry data-driven so the script returns to canonical-producer.
- tests/unit/test_doc_traceability_loader.py: two assertions pinned to the company's
  ahead controlm-ingestion-tdd.md (9 matrix rows incl. NFR-CMI-002). Keep company pins.
  Producer back-flow candidate: derive expected counts from the doc under test.
- EXPECTED_CONSTRAINTS: producer 51 at step-49 head (unchanged since G33 — D8 was a
  guard, not new constraints; the step-49 range adds none). Evaluate counts
  COMPANY-BASED every port against your own prior PORT-REPORT number; never
  double-add a shared addition — the K4 precedent.
- Canonical-company set (manifest rows): controlm-ingestion-tdd.md, the design_doc
  renderer output, review internals (drydocs-review back-flow stream), oracle_adapter,
  company sources/supplements, dev-environment.yaml (above). Producer touches = drop
  the incoming side.
- docs/restructure/IDEAS.md union-superset: the company copy retains blocks the
  producer already groomed into backlog items G18–G25. Before any company groom pass,
  annotate those retained blocks "groomed producer-side → G18..G25" (or check the
  ported backlog first) — prevents double-capture as duplicate items.
- Vocab prose on REQUIRES_SCHEDULER / seal_requires_scheduler / reg_uses_software +
  the requires-scheduler map open questions: names have diverged across repos; entries
  stay planned/proposed (inert). Resolve at the company platforms gate, not by editing.

OWED COMPANY-SIDE:
- L7 RATIFICATION ENTRY in the company gate-log (Tier A adopted-via-port; paste-ready
  snippet provided in the producer session 2026-07-21 — subject: 6 doc_* edges + 6 doc
  node classes active, doc-traceability-feedback confirmed; references producer gate
  0252d29 via PORT-REPORT-6fd3270). Still outstanding as of 2026-07-29 (tracker T11).
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
| T12 | Company platforms gate: AIS position vs producer C12 | **RULED — SUPERSEDE, 2026-07-21**, company gate-log: the `:AisCapability`/`:AisTool` layer superseded by the software-registry model; excision APPLIED company-side (initial-load runbook steps 7b/10); Tier B holds in old steps 43/45b discharged 2026-07-27; session packs retired from the tree (git history if re-litigated) |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending |
| T14 | rua collector convergence: company's own -n implementation vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible. Step 49e's G45 listing fallback is the same family — reconcile together | pending |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways; primary on-main checkout, never a worktree) → `drydocs load-code-snapshot` into your graph; second `:Project` root is INTENDED (gate §B3(a)); rides with the Tier A ratification entry (guardrail 6) | pending |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 staging stand-in as the feed (G40 parse stays as cross-check); premise correction folded into G22 prep. NOTE step 49g: if the XML export becomes a standing feed, this retirement gains a SECOND path — the unruled precedence question decides, not the port | pending |
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | pending |
| T18 | Depgraph fork capability catch-up (owed action 48e, PORT-REPORT-94132c80): your separately-owned depgraph fork lacks the U6 multi-root resolver (and `--tree`), and the producer remote is unreachable from it, so the port could not remediate. Until it catches up, `config/dev-environment.yaml` keeps `depgraph.capability_assert: false` (test skips, owed action recorded). When it gains the capabilities: flip the flag true and your `snapshot.ps1` refusal guard goes live | pending |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section. T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10/T13: until a real export parses with zero mismatches, treat the
  field names as ASSUMED.

STEP LEDGER — delta since `94132c8` (numbering continues; steps 43–48 are collapsed
above). Every sub-stream carries its producer-side verification status in [BRACKETS]
— review effort belongs on the [UNRULED] and RECONCILE items, not on re-proving the
tagged ones.

49. BACK-FLOW ENACTMENTS + DEV-INFRA + XML-FED CMDLINE CHAIN + UI/SME SWEEP
    (2026-07-28 → 2026-07-29; `94132c8..cewilson/main` — compute the range live and
    record the exact head in the PORT-REPORT; 42 commits to `3fe69c1` known at
    2026-07-29, and the UI stream (h) was still ACTIVE producer-side at that time).
    Apply order: (a) first — it enacts your own port report's findings and changes
    what the guards expect; the rest in the order below.
    a. YOUR OWN REVIEW, ENACTED [VERIFIED BY CONSTRUCTION — these commits ARE the
       producer's acceptance of PORT-REPORT-94132c80; expect near-no-ops where you
       already patched by hand — RECONCILE, don't clobber]:
       - `0c629e4` #1: config/dev-environment.yaml canonical-company entry_rule on
         the PRODUCER manifest. ACTION: verify both manifests now agree (the row was
         "sent back" — this is it); from now on new keys in that file arrive as
         structure to adapt (see (b) for the live case).
       - `855b09d` #2: the U7 live-capability test gates on
         `depgraph.capability_assert` config — `test_probe_instrument.py` is now
         BYTE-IDENTICAL on both sides and your divergence lives in the one file
         already ruled canonical-company. Your flag stays false until T18 clears.
       - `f6b9ca0` #3: `ownership.escalation-routing.v1` gains `WHERE NOT
         n:SchemaMeta`, and the O33 guard now requires the predicate on EVERY spec
         unconditionally (a no-op on never-stamped labels, so it cannot go stale).
         Your hand-patched spec is now guard-enforced — adopt the guard, expect a
         no-op on the spec itself. Negative-probed producer-side.
       - `f6b9ca0` #4: httpx-vs-httpx2 resolved by ASKING starlette — a test derives
         the expected dependency from `starlette.testclient.httpx.__name__` and
         fails if pyproject disagrees. Neither side was broken; your suite will tell
         you when to switch. Never overwrite the company pyproject version string
         (guardrail 9).
    b. DEV-INFRA: THE PLUGINS FIX [LIVE-VERIFIED producer-side: apoc 174 procs +
       gds 471 after the fix] (`33cfc68`; also `35a7797` SDK-review re-home to
       internal/ — default_ok union/evaluate, never blind checkout):
       `NEO4J_PLUGINS=[apoc]` had SILENTLY never installed APOC in the producer
       container — plugins are now a mounted volume. Two actions your side:
       (1) audit YOUR container the same way — count procedures live
       (`SHOW PROCEDURES`), never trust the env var; (2) the file's new `plugins:` +
       `plugins_volume` keys are the first live case of the (a)#1 entry_rule —
       adapt the STRUCTURE, decide the values locally.
    c. G22 SESSION PREP [NOTHING DECIDED — gate spec only] (`49667dd` prompt
       DRAFTED session-ready, `1ac23df` first real-data reference): clean-add. The
       real-data reference cites YOUR OWN staging profile (hash-absent occurrences,
       the live collision feed) — verify the citation matches what your staging
       actually shows and report divergence back. G22 remains the activation gate
       for the whole rua/DPL staging family; nothing in this range writes the graph.
    d. STALE-CLAIM FIXES + THE AIS REFUSAL PACK [RECORD-CORRECTION] (`87ba693`,
       `a90fdad`): two stale scheduler_kind claims corrected, and the formal
       refusal grounds for the AIS back-flow proposal a company session raised
       2026-07-28 — the premise was false (the producer has no AIS layer to
       back-flow into; C12 took the direct :SchedulerKind route). This is tracker
       T17 action (1) — union-append the docs; nothing to build.
    e. THE G45/C20/J20/R10 BATCH [TEST-PINNED] (`ff4d922`, `60b199e`, `59ddf3f`,
       `d637b31`):
       - G45 rua listing fallback: bundles with a metadata-only scripts.csv now
         stage the LISTING instead of silently dropping every script — producer
         parity with YOUR OWN 561-script incident fix. RECONCILE against your
         implementation (the T14 convergence family), don't clobber.
       - C20: the K4 deprecation comment in constraints.cypher now names its actual
         scope (SEAL-loader-specific; role/membership keys are live catalog writes).
       - J20: enforcement-matrix.json rides the default-paths board render — after
         this, ONE `render_board.py` run refreshes board + gates.json + matrix
         (guardrail 5 wording updated to match). Regenerate YOUR side after config
         edits as always.
       - R10: google-adk pinned `>=2,<3` + ADR 0007 revisit-check date-stamped
         PASSED. agents/ has its own venv — the pin takes effect at your next
         pip install, by design.
    f. G42 SNOWFLAKE DATA-CATALOG SEAM [STAGING-ONLY; field contract is YOURS to
       validate] (`c071f09`): source registered (`confirmed: false`), catalog_dir
       landing zone, taxonomy-first extractor staging both views (three-shape
       discrimination, sentinel counted, latest-per-GUID, origin routing, urn fact
       column). G43 (cross-checks) and G44 (gate prompt) arrive todo. Your REAL
       curated views are the validation surface — the T10/T13 discipline: amend
       header + fixtures together, cite provenance.
    g. G46–G48: THE XML-FED CMDLINE RESOLUTION CHAIN [STAGING-ONLY; BUILT FOR YOUR
       XML FEED; ONE QUESTION DELIBERATELY UNRULED] (`2106a73` G46, `6045d4a` G47,
       `ba6b83b` G48; runbook in (i)):
       - G46: `resolve_command_line` — the public CMD_LINE entry point on the
         SHARED resolver (one scope-chain walk, substitution provenance with the
         winning scope, %%VAR-launcher round-trip proven by test).
       - G47: Control-M XML export seam — taxonomy-first staging of defs + ordered
         variables. This is YOUR native format (9.0.21.300 exports XML; the JSON
         API files were demoted to conceptual reference long ago) — the chain
         exists so your export can feed resolution directly.
       - G48: resolve-cmdline-staging — store v3, `cmd_line_resolved` DERIVED
         BESIDE the verbatim column with `resolution_quality` provenance; verbatim
         is never overwritten.
       - *** [UNRULED — DO NOT INFER A RULING] ***: which source wins per object
         when the XML export and the psgmgr replica DISAGREE is an open
         config/precedence.yaml question, deliberately parked (producer IDEAS
         2026-07-29, HITL — user/SME rules it, never a port or a groom). The build
         fills a nullable derived column and decides NOTHING about source-of-truth;
         disagreement evidence is COUNTED, never resolved. Also touches T16: if
         the XML export becomes the standing feed, the CM_DEF_VJOB_DETAIL
         retirement gains a second path.
       - No graph writes anywhere in the chain; G22 remains the activation gate.
         Producer proved the chain against fixtures — running it against a REAL
         XML export is your verify (T9 spirit).
    h. UI SWEEP O35–O41 + SME FEEDBACK FB-01..FB-04 [SME-SIGNED where stated;
       web/** canonical-producer clean-apply; STREAM STILL ACTIVE — compute the
       range live] (`77f68c5` O36/O37, `7a3da45` O38/O39/O41, `37f88d3` O40,
       `c8b0e67` O35, `12bf7a5` close, `7aa0792` wireframes current, `0007657`
       FB-03, `6029f36` + `da248fb` + `3fe69c1` FB-04):
       - O35–O41 [SME feedback FB-01/FB-02 driven; both themes screenshot-checked,
         build+lint green]: category-first landing, clipping root-cause fix +
         radius tokens, IdChip/StageBadge convention, runtime-view slot (renders
         nothing unset), StatTiles click-to-filter, status-vocab map.
       - FB-03 [EXECUTED per SME feedback]: page role designation —
         `ModuleDef.access` ('all'|'sme'|'admin') + nav filter + route guards.
         DISPLAY-GATING ONLY under mock auth; server enforcement rides the O1 ADR
         — do not mistake it for a security boundary.
       - FB-04 [SME GATE SIGN-OFF 2026-07-29, producer config/gate-log.md]: the
         Agent Test harness, re-ruled STANDALONE — `web/public/agent-test.html`,
         dark-only, no auth, read-only per O20, ships in dist. **THIS PAGE EXISTS
         FOR YOUR REVIEW**: it was built expressly so the company port can live-test
         agents — dropdown of the registry's non-deterministic modules, per run:
         interpretation → Cypher → return path → answer → metrics, and (`3fe69c1`)
         a run timeline with thinking + per-stage token counts, plus its SME
         runbook. After `npm ci && npm run build --prefix web` the page is in dist;
         point it at your ADK service (VITE_ADK_URL). ADK unreachable → a
         SYNTHESIZED demo trace with the standard banner — treat demo-trace output
         as SYNTHESIZED, never as your graph's answer.
       - The FB-03/FB-04 retro-groom into backlog ids is still PENDING producer-side
         (IDEAS inbox 2026-07-29) — do not invent ids for them in your backlog.
    i. CMDLINE RESOLUTION RUNBOOK Rev 1 [GOVERNED RENDER] (`055524f`):
       docs/design/drydocs-cmdline-resolution-runbook.md — the G39→G48→G40 chain as
       an operable procedure. The .md ports; the .html regenerates YOUR side
       (guardrail 5).
    j. GROOMS + EPIC V (`fffd788`, `ed091cd`, `f5cf0dd`, `3ef2e62`): backlog
       per-entry as always — G42, G45–G48, C20, J20, R10, O35–O41 arrive `done`;
       N3–N6 (the generated load map: loader→source joins, one declared load
       sequence, a rendered one-view of taxonomy-by-source/ontology/extract/loads)
       and V1–V10 (NEW Epic V: per-module SME runbooks behind a V1 coverage rule
       with a frozen shrink-only RUNBOOK_PENDING list) arrive `todo`; N4 widened in
       place 2026-07-29. Re-insert the company DD-series and recompute the summary
       exactly as test_backlog does. Epic V exists because of a producer SME
       directive ("a SME-Runbook for each module") — your side may want the twin,
       but that is your call, not a port step.
    Snapshots in the range (`1b1bcf8`, `ca2cace`, `d25f901`, `3f6df3b`) are
    EXCLUDED class (guardrail 4 + the never-port manifest row).
    Producer reference at `3fe69c1`: full suite 1144 passed / 5 skipped, Track-1
    subset 124 passed / 0 skipped — BOTH measured with the production CSV PRESENT
    on the measuring machine; expect a larger skip count where it is absent.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `3fe69c1` (step 49): 124 passed / 0 skipped WITH the
  production CSV present (sample-backed tests skip without it — at step 48 the
  CSV-absent figure was 114 / 3). Company baseline is ABOVE the producer floor —
  compare against your own PORT-REPORT-94132c80 numbers, not these.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR,
  capability_assert=false skips per T18).
  Producer reference at the current head (step 49, `3fe69c1`): 1144 passed /
  5 skipped, production CSV present (step-48 head 8a82e3b was 1099 / 7 CSV-absent;
  step-47 head 947920c was 1070 / 8; step-46 head 78ba7fd was 982 / 6).
  Company reference: your own PORT-REPORT-94132c80 baseline.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (producer-side at the
  back-flow enactment: 12 passed / 4 skipped; the J16 manifest-coverage /
  default_ok / backlog-no-regression checks run unconditionally, no env var needed).
- Historical per-step producer counts (483 → 831 across steps 28–42): archive file.
```
