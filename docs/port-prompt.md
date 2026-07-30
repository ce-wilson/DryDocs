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

**Rolled 2026-07-30:** step 49 collapsed (applied in PORT-REPORT-e60822fc — WITH the
N3–N6 load-map deferral, now tracker **T19**); the live ledger is step 50 only. Steps
keep the verification-status tags introduced at step 49 — `[SME-SIGNED]`,
`[LIVE-VERIFIED]`, `[TEST-PINNED]`, `[STAGING-ONLY]`, `[RECORD-CORRECTION]`,
`[UNRULED]` — so the company review can spend its attention on what is genuinely open
instead of re-deriving what is already proven. Anything not tagged confirmed is NOT
confirmed; treat contracts as ASSUMED until your side validates them (the T10/T13
discipline).

Authorities are unchanged: [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml) is the WHAT
(per-path disposition, first-matching-glob-row wins); [`git-readme.md`](../git-readme.md)
is the WHY + the acceptance oracle; this prompt is sequencing + delta context only.

## Last completed port

- **Producer head `e60822f`** (2026-07-29), applied company-side as
  **PORT-REPORT-e60822fc** — covered producer range `94132c8..e60822f` (step 49 in
  full, plus the N3–N5 load-map builds that landed inside the range after the step
  was authored).
- **The N3–N6 load-map stream was DEFERRED company-side — now tracker row T19.**
  Two real blockers, both acknowledged producer-side (IDEAS 2026-07-29): (1) the
  `catalog-pat` ≠ `pat-catalog` id collision — same string, different meaning across
  repos (see the divergence ledger row below); (2) ~13 company-only loaders carry no
  class `source_id`, so the N3 derivation would drop them from gating. Company
  actions taken: kept the hardcoded `LOADER_SOURCE`, dropped `render_load_map` +
  the N4/N5/N6 surfaces from the company board render, marked N3/N4/N5 blocked,
  filed T19, requested a gate review. Producer answers-in-progress: the manifest
  row your agent had to improvise around is fixed (`1b51c04`, step 50a), the N7
  per-side overlay candidate and the registry-redesign directive are inboxed
  (step 50c/50d) — **do not adopt producer source_id VALUES for the catalog family
  until the T19 gate rules.**
- The PORT-REPORT-94132c80 findings loop is CLOSED: all four back-flows were
  enacted producer-side (`0c629e4`, `855b09d`, `f6b9ca0`) and applied company-side
  as step 49a. `config/dev-environment.yaml` remains canonical-company on both
  manifests — do not re-decide. Owed action 48e remains tracker **T18**.
- **Applied steps, collapsed** (full text: git history + the PORT-REPORTs;
  steps 43–48 summaries retired to PORT-REPORT-94132c80 at this roll):
  - 43–48 — one line each in PORT-REPORT-94132c80 (C12 platforms taxonomy; UI
    acceleration; lineage/rua/DPL + Epic R; S3 identity gate + boundary hardening;
    G33 code-graph + J16 manifest overhaul + G39/G40 + Epic P; DataLens UI +
    U7/U8 + D8 + depgraph fork consolidation).
  - 49 — back-flow enactments (49a) + dev-infra plugins fix (49b) + G22 prep (49c)
    + AIS refusal pack (49d) + G45/C20/J20/R10 (49e) + G42 Snowflake catalog seam
    (49f) + G46–G48 XML-fed cmdline chain (49g, precedence question still UNRULED)
    + UI sweep O35–O41 / FB-01..FB-04 (49h) + cmdline runbook Rev 1 (49i) + grooms
    incl. Epic V (49j). N3–N5 arrived built inside the range; company deferred
    them (T19, above).

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
   `web/src/generated/gates.json` + `enforcement-matrix.json` + `load-map.json`
   and `docs/plan/load-map.html` (all ride the default-paths board render —
   J17/J20/N4/N5 — so one `render_board.py` run refreshes all five; COMPANY-SIDE
   under T19 your render currently EXCLUDES the load-map pair — keep that exclusion
   until the T19 gate rules),
   `docs/plan/board.html` (from the reconciled backlog), `docs/design/*.html`
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
- **`catalog-pat` ≠ `pat-catalog` (recorded BOTH sides regardless of the T19 ruling):
  the same string names DIFFERENT feeds across repos.** Producer `catalog-pat` = the
  whole catalog+PAT sample feed (one registry entry). Company `pat-catalog` = the PAT
  People-Report org catalog (confirmed, gates 8 catalog loaders); company
  `catalog-pat` = a separate team-report feed. NEVER adopt producer source_id VALUES
  for the catalog family — presence/resolution tests do not catch a wrong-but-
  resolving value (the value-level guard gap). Resolution belongs to the T19 gate +
  the registry redesign (step 50d), not to a port.
- N3–N5 load-map machinery: company runs hardcoded `LOADER_SOURCE` and excludes
  `render_load_map` from its board render until T19 rules; producer runs the N3
  class-declaration derivation. Both are correct on their own side — reconcile at
  the gate, not in a port.
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
- EXPECTED_CONSTRAINTS: producer 51 at step-50 head (unchanged since G33 — D8 was a
  guard, not new constraints; the step-49 and step-50 ranges add none). Evaluate
  counts COMPANY-BASED every port against your own prior PORT-REPORT number; never
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
| T19 | N3–N6 load-map adoption gate (deferral filed at PORT-REPORT-e60822fc; gate review requested by the user): rule (1) the catalog-pat/pat-catalog id collision (divergence ledger row) and (2) the ~13 sourceless company-only loaders BEFORE adopting the N3 class-declaration derivation, N4/N5 renders, or N6. Producer inputs waiting on this ruling: the N7 per-side overlay candidate (loader→source_id config overlay, canonical-company file), the URN cross-repo identity handle, the reconcile same-id/changed-meaning guard, and the registry-redesign directive (step 50d) — the producer holds ALL FOUR for ONE design session so the gate rules once, not four times | pending |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section. T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10/T13: until a real export parses with zero mismatches, treat the
  field names as ASSUMED.

STEP LEDGER — delta since `e60822f` (numbering continues; steps 43–49 are collapsed
above). Every sub-stream carries its producer-side verification status in [BRACKETS]
— review effort belongs on the [UNRULED] and RECONCILE items, not on re-proving the
tagged ones.

50. T19 FOLLOW-THROUGH: MANIFEST ROW + J21 REGISTRY HARDENING + THE REDESIGN
    DIRECTIVE (2026-07-29 pm → 2026-07-30; `e60822f..cewilson/main` — compute the
    range live and record the exact head in the PORT-REPORT; 7 commits to `e0dc403`
    known at 2026-07-30). A small range, but most of it exists BECAUSE of your
    PORT-REPORT-e60822fc — it answers your report, it does not re-open T19.
    a. MANIFEST ROW FOR docs/plan/load-map.html [RECORD-CORRECTION] (`1b51c04`):
       the row your agent had to improvise around — the producer J16 coverage guard
       caught it (a NEW render committed without its manifest row; the guard's
       tracked-only blind spot is a known producer IDEAS bug). The ROW ports
       (coverage is explicit — guardrail 1); the RENDER itself stays OFF your side
       under T19 (guardrail 5 note).
    b. J21 SOURCE-REGISTRY HARDENING [TEST-PINNED] (`087a685`; claim/close
       `c7e5fb9`/`19c5424` ride the backlog per-entry rule): three parts with
       DIFFERENT port dispositions —
       - (1) pk check: `SourceRegistry.from_yaml` REFUSES a duplicate source id
         (`DuplicateSourceIdError` naming the id — last-one-wins would let file
         position decide the D3 gate), plus a shipped-registry uniqueness pin.
         ADOPT CLEANLY: your `pat-catalog` and `catalog-pat` are DISTINCT ids, so
         the guard does not conflate them — it prevents the third failure mode
         (a duplicated entry deciding a gate by position).
       - (2) loader:-field agreement guard
         (`test_registry_loader_fields_agree_with_class_source_id`): registry
         entries carrying a `loader:` field must AGREE with that module's
         class-level `source_id`. ***CAUTION — this test PRESUPPOSES the N3 class
         declarations you deferred under T19.*** If your loader classes carry no
         `source_id` (you kept the hardcoded `LOADER_SOURCE`), this test will fail
         or error your side. Disposition: adapt — skip or adjust it under your T19
         deferral (document the adaptation in the PORT-REPORT), and adopt it for
         real when the T19 gate rules. Do NOT resolve the failure by adding
         producer source_id values to your classes (the divergence-ledger rule).
       - (3) stale-note refresh: `autosys-export` / `airflow-mwaa` notes corrected
         to the recorded 2026-07-14 crosswalk-gate sign-off facts (both still said
         "SME not yet run" against `confirmed: true`). Adopt; pure record accuracy.
    c. THE T19 CAPTURE + N7 CANDIDATE [RECORD — union-append] (`49cb365`): the
       producer IDEAS entry recording YOUR deferral verbatim (both blockers, your
       actions, the N7 per-side overlay direction: class declarations stay the
       producer DEFAULT, a canonical-company config overlay loader→source_id wins
       over the class value, guard tests byte-identical both sides). Held inboxed
       until your T19 gate rules — nothing to build either side yet.
    d. REGISTRY-REDESIGN DIRECTIVE [UNRULED — DO NOT INFER A RULING] (`19c5424`,
       IDEAS 2026-07-30, user directive): the flat registry `id` conflates the
       source SYSTEM with the extracted DATASET — one system yields multiple
       datasets across ontology domains (Product Catalog → DPROD datasets
       Product/AreaProduct/Team AND ORG datasets; Control-M → SWO/database/code).
       Direction to design (NOT decided): two-level identity — system carries
       connection/locator/classification; each extracted dataset carries its own
       gate/crosswalk/feeds_taxonomy/confirmed state; loaders bind to the dataset.
       Producer intent: ONE design session bundling this with the N7 overlay, the
       URN handle, and the reconcile same-id/changed-meaning guard — HITL-gated as
       registry schema v2, FEEDING your T19 gate review. J21 (b) hardened the
       CURRENT shape so nothing drops meanwhile.
    e. UNITY CATALOG REFERENCE NOTE [RECORD — union-append] (`0a7e4d0`):
       reference/ prose only (headings/categories-at-a-glance, 4 category systems,
       Discover homepage detail, subdomains). Clean-add.
    Snapshot `e0dc403` is EXCLUDED class (guardrail 4 + the never-port manifest
    row).
    Producer reference at `e0dc403`: full suite 1163 passed / 5 skipped, Track-1
    subset 124 passed / 0 skipped — BOTH measured with the production CSV PRESENT
    on the measuring machine; expect a larger skip count where it is absent, and
    expect (b)(2) to move your failure count until adapted.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `e0dc403` (step 50): 124 passed / 0 skipped WITH the
  production CSV present (unchanged from step 49; sample-backed tests skip without
  it — at step 48 the CSV-absent figure was 114 / 3). Company baseline is ABOVE the
  producer floor — compare against your own PORT-REPORT-e60822fc numbers, not these.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR,
  capability_assert=false skips per T18; a temporary company-side failure on the
  J21 loader-field guard is EXPECTED until the step-50(b)(2) adaptation is applied).
  Producer reference at the current head (step 50, `e0dc403`): 1163 passed /
  5 skipped, production CSV present (step-49 head 3fe69c1 was 1144 / 5 CSV-present;
  step-48 head 8a82e3b was 1099 / 7 CSV-absent; step-47 head 947920c was 1070 / 8;
  step-46 head 78ba7fd was 982 / 6).
  Company reference: your own PORT-REPORT-e60822fc baseline.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (producer-side at the
  back-flow enactment: 12 passed / 4 skipped; the J16 manifest-coverage /
  default_ok / backlog-no-regression checks run unconditionally, no env var needed).
- Historical per-step producer counts (483 → 831 across steps 28–42): archive file.
```
