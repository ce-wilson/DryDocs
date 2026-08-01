# Port prompt — producer → company (rolling)

**Format (v3 rolling, 2026-07-31).** This prompt carries ONLY (1) the durable
guardrails and (2) the step ledger since the last completed port. Steps 1–42 are frozen
in `port-prompt-archive-steps-1-42.md` (guardrail 1 has the path); numbering continues
here at 43. On completion company-side: update **Last completed port**, fold new standing
divergences into the ledger, and collapse the applied steps to ONE LINE each. The archive
is FROZEN — applied steps ≥43 are never appended there; their full text lives in git
history and the company PORT-REPORT.

**LENGTH DISCIPLINE (v3 rule, and the reason for it).** This file regrew to 567 lines by
step 51 because each roll added prose that the next roll never removed. A prompt nobody
finishes reading is not a control document. So:
- a step-ledger sub-stream gets **≤ 8 lines**: what changed, its verification tag, and
  the ONE caution that would cost you a rework. Everything else belongs in the commit
  message, which is one `git show` away;
- a tracker row gets **one sentence plus a pointer**, never a paragraph;
- a roll REPLACES the previous roll note; it does not stack another one;
- if a section can only be understood by reading it twice, cut it rather than expand it.

**Roll state.** Steps 50 + 51 are BOTH live (50 was authored 2026-07-30, 51 appended
2026-07-31; neither had been applied company-side when 51 was written, so nothing was
collapsed). A port takes both — read 51(b) first, it carries the registry schema v2
landing. Steps keep the verification tags introduced at step 49 — `[SME-SIGNED]`,
`[LIVE-VERIFIED]`, `[TEST-PINNED]`, `[STAGING-ONLY]`, `[RECORD-CORRECTION]`, `[UNRULED]`
— so review effort goes to what is genuinely open. Anything untagged is NOT confirmed:
treat contracts as ASSUMED until your side validates them (the T10/T13 discipline).

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
- **Applied steps, collapsed** (full text: git history + the PORT-REPORTs):
  43–48 — one line each in PORT-REPORT-94132c80. 49 — back-flows, dev-infra plugins,
  G22 prep, AIS refusal pack, G45/C20/J20/R10, G42 catalog seam, G46–G48 cmdline
  chain, UI sweep O35–O41, cmdline runbook Rev 1, grooms. N3–N5 arrived inside the
  range and were deferred (T19).

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
   TWO CITED DOCS ARE NOT IN YOUR TREE (both `docs/port-*.md` = never-port). Read them
   at the fetched producer ref, same idiom as above:
   - `...:docs/port-prompt-archive-steps-1-42.md` — resolves every "archive step N"
     citation, and holds the Done-means for T1–T10, which appear nowhere else.
   - `...:docs/port-ais-supplement-company-prompt.md` — the T17 pack. NOT part of any
     port (no payload; four actions on company-local code). Run it as its own session.
   A citation with no openable path is a DEFECT — send it back, do not work around it.

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
   COMMIT THE PORT TO THE BRANCH BEFORE WRITING THE PORT-REPORT, and prove it:
   `git rev-list --count <tag>..HEAD` must be ≥1, and the report's reversibility
   section quotes that output — not the claim alone. A port left in the working tree
   is NOT revertable: the branch equals main equals the tag, so the documented undo
   `git reset --hard <tag>` DESTROYS the port instead of restoring a safe point.
   (2026-07-31, PORT-REPORT-57914bf4: 159 tracked + ~25 untracked, ZERO commits,
   reversibility asserted anyway. Producer review cannot catch this — it checks
   report claims against PRODUCER state, never your git. Only you can.)
   If committed config references company-local code that is still uncommitted, land
   that code as its OWN commit FIRST and move the tag onto it. Folding it into the
   port commit poisons the revert; leaving it out commits a config whose loader is
   not in history.

4. ALWAYS EXCLUDED: `knowledge/depgraph-snapshots/*.json` — producer-local derived
   artifacts with producer git metadata; regenerate your own via the session-end ritual.

5. DERIVED ARTIFACTS regenerate AFTER all config edits, never hand-merge:
   `web/src/generated/gates.json` + `enforcement-matrix.json` + `load-map.json`
   and `docs/plan/load-map.html` (all ride the default-paths board render —
   J17/J20/N4/N5 — so one `render_board.py` run refreshes all five; COMPANY-SIDE
   under T19 your render currently EXCLUDES the load-map pair — keep that exclusion
   until the T19 gate rules),
   `docs/plan/board.html` (from the reconciled backlog), and `docs/design/*.html`
   — SINGLE SURFACE, screen + `@media print` in one file (L13). There is no
   `*.print.html` twin on either side; the twins were retired company-side and
   this line said otherwise until 2026-07-31.
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

6a. PASTE-READY L7 RATIFICATION ENTRY (discharges tracker T11).
   §6 Tier A requires the ratification entry to land in the COMPANY gate-log, and
   port-prompt has said since 2026-07-21 that a snippet "was provided in the producer
   session" — but the block itself was never committed, so no company session could
   open it. It is committed here now. Copy it verbatim into the company `gate-log.md`
   in gate-log date order, fill the four `[...]` placeholders from YOUR port report,
   and flip T11.

   WHAT IS PRE-FILLED vs WHAT YOU FILL: the subject, the producer gate reference, and
   the six-and-six inventory are FACTS OF THE PRODUCER GATE — verified against
   `config/gate-log.md` (2026-07-20 entry), `relationship_vocabulary.yaml`, and
   `config/taxonomy-ontology-map.yaml`, so they are written out. The check RESULTS and
   the sign-off are yours: they describe what ran against the COMPANY tree, which no
   producer session can know. They are bracketed placeholders, deliberately not
   invented — an entry citing numbers nobody ran is worse than no entry.

   ```markdown
   ## [PORT DATE] — L7 · Documentation traceability + review feedback — RATIFIED (Tier A, adopted via port)

   - **Tier:** A — the company held no signed position on documentation traceability
     at adoption time. Per the two-tier gate-adoption doctrine (port-prompt §6), a
     port MAY adopt a producer-signed outcome; this entry is the required company
     record. A PORT-REPORT is evidence, not a gate ledger.
   - **Subject:** the product-plane documentation ontology — 6 node classes
     (DesignDoc, DocSection, Requirement, Component, TestCase, FeedbackNote) and 6
     `doc_` relationship vocabulary entries (doc_section_part_of,
     doc_requirement_specified_in, doc_requirement_implemented_by,
     doc_requirement_verified_by, doc_feedback_annotates, doc_feedback_authored_by)
     activated planned → active; taxonomy-ontology map entry
     `doc-traceability-feedback` proposed → confirmed.
   - **Producer gate reference:** producer gate-log 2026-07-20, "L7 · Documentation
     traceability + review feedback (doc-traceability-feedback) — SIGNED OFF";
     21 confirmed / 0 edited / 0 rejected; SME chad.wilson; gate spec
     `config/gate-prompts/doc-traceability-feedback.yaml`; producer commit `0252d29`.
     Adopted into this repo by `PORT-REPORT-6fd3270`.
   - **Same-SME condition (§6 Tier A clause a):** MET — the SME who signed the
     producer gate is the SME signing here.
   - **Checks performed company-side (§6 Tier A clause b):**
     - Full unit suite: [N] passed, [N] skipped.
     - J7 reconcile guards with `RECONCILE_BEFORE_DIR` set: no active/confirmed/
       applied downgrade, no dropped per-entry rows, gate-log append-only — [RESULT].
     - Vocabulary + map entries resolved BY ID (never whole-file checkout); summaries
       recomputed as the guard tests do — [RESULT].
     - [Any company-side adaptation applied at adoption, or "none".]
   - **Graph writes:** NONE ruled in by this entry. Per §6 and tracker T9, adoption
     flips config status only; loading `load-doc-traceability` against the company
     graph and verifying it remains a separate company action.
   - **Signed off:** [SME NAME], [DATE].
   ```

   Note the deliberate shape: this ratifies an ADOPTION, so it records no new
   decisions. If the company ever wants to change any of the 21 producer rulings,
   that is a full company gate session (Tier B), not an edit to this entry.

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

9. RUFF / FORMAT CONVERGENCE (J10 — each side formats its OWN tree). Authority:
   `git show cewilson/main:docs/ruff-format-convergence.md`. Find the boundary BY
   COMMIT SUBJECT, never by SHA — every commit is tagged `J10 stage <N>`:
   stage 0 PORTS (the shared contract: `ruff = "0.5.7"` EXACT + settled `[tool.ruff*]`
   + `*.py text eol=lf`); stages 1–3 DO NOT PORT — regenerate them on your own tree
   once stage 0 lands; stage 4 PORTS normally (per-rule fixes + reasoned
   `per-file-ignores`); stage 5 PORTS but apply it only AFTER your residuals are zero
   — it makes the CI ruff step blocking and would otherwise red you out by
   construction. Until both sides run 1–3, resolve `.py` layout collisions by taking
   YOUR formatting; never hand-merge whitespace. After both converge, this collision
   class disappears — that is the whole point.

10. BOUNDARIES: one-way only — never add company main as a remote on the producer,
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
  the registry redesign (step 50d), not to a port. **Producer N7 gate ruling
  2026-07-31 (SME naming note, feeds — never pre-empts — your T19 review): the
  replacement dataset name is `pat:product-catalog` (industry-standard naming; the
  people report splits out as `pat:people-report`) — deliberately matching NEITHER
  legacy string, so neither repo's wrong value survives the v2 migration; both
  legacy ids land in the D4 retired-id refusal list.**
- N3–N5 load-map machinery: company runs hardcoded `LOADER_SOURCE` and excludes
  `render_load_map` from its board render until T19 rules; producer runs the N3
  class-declaration derivation. Both are correct on their own side — reconcile at
  the gate, not in a port.
- **`config/loader-source-overlay.yaml` (NEW at N9, 2026-07-31): canonical-PER-SIDE by
  design.** The file itself ports (it is the D2 mechanism + its guard); its CONTENTS
  never do. Producer ships `overrides: {}` because producer class defaults already are
  the registered v2 dataset ids. Yours is where your ~8 mismatched and ~13 unbound
  loaders re-point — in config, without touching ported loader modules. Treat an
  incoming non-empty `overrides:` block as a porting mistake, not as data.
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
  **2026-07-31 (L21, step 51h): a THIRD pin in this same file moved —
  `header["rev"] == 4` → `5` for the startup-refresh runbook.** That one is NOT a
  company pin: it tracks `docs/design/drydocs-startup-refresh-runbook.md`, which is
  `evaluate` disposition. If you take the Rev 5 runbook, take the rev pin with it; if
  you hold your own runbook rev, keep your own number. The failure mode is silent
  either way — the pin only fails when the two disagree, which is the point. Note the
  file now carries pins of BOTH kinds; do not resolve the whole file one way.
- EXPECTED_CONSTRAINTS: producer 51 at step-51 head (unchanged since G33 — D8 was a
  guard, not new constraints; the step-49, step-50 and step-51 ranges add none —
  registry v2 is an identity refactor and ships no new active edges). Evaluate
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
- L7 RATIFICATION ENTRY in the company gate-log (Tier A adopted-via-port). The
  paste-ready block is **§6a below** — committed, not "provided in a session". Open
  as of 2026-07-31 (tracker T11).
- TRACKER (T1–T8 origin steps live in the archive — guardrail 1 has the path;
  statuses tracked here):

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
| T11 | L7 ratification entry in company gate-log (Tier A record) | **RATIFIED 2026-07-27** (company gate-log, prior port; reported at PORT-REPORT-57914bf4). The producer row read `pending` until 2026-07-31 — producer-side staleness, not a company gap. §6a stays as the STANDING Tier-A template (source-registry-v2 and J23 both used that shape) |
| T12 | Company platforms gate: AIS position vs producer C12 | **RULED — SUPERSEDE, 2026-07-21** (company gate-log): the AIS layer is superseded by the software-registry model; excision applied, Tier B holds discharged 2026-07-27, session packs retired |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending |
| T14 | rua collector convergence: company's own -n implementation vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible. Step 49e's G45 listing fallback is the same family — reconcile together | pending |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways; primary on-main checkout, never a worktree) → `drydocs load-code-snapshot` into your graph; second `:Project` root is INTENDED (gate §B3(a)); rides with the Tier A ratification entry (guardrail 6) | pending |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 staging stand-in as the feed (G40 parse stays as cross-check); premise correction folded into G22 prep. NOTE step 49g: if the XML export becomes a standing feed, this retirement gains a SECOND path — the unruled precedence question decides, not the port | pending |
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | pending |
| T18 | Depgraph fork capability catch-up (owed action 48e, PORT-REPORT-94132c80): your separately-owned depgraph fork lacks the U6 multi-root resolver (and `--tree`), and the producer remote is unreachable from it, so the port could not remediate. Until it catches up, `config/dev-environment.yaml` keeps `depgraph.capability_assert: false` (test skips, owed action recorded). When it gains the capabilities: flip the flag true and your `snapshot.ps1` refusal guard goes live | pending |
| T19 | N3–N6 load-map adoption gate (deferral filed at PORT-REPORT-e60822fc; gate review requested by the user): rule (1) the catalog-pat/pat-catalog id collision (divergence ledger row) and (2) the ~13 sourceless company-only loaders BEFORE adopting the N3 class-declaration derivation, N4/N5 renders, or N6. **INPUTS DELIVERED 2026-07-31 — the ONE design session ran and BUILT: gate `source-registry-v2` SIGNED OFF (`323f5aa`, N7) and schema v2 landed (`86914ad`, N9). All four inputs this row was holding are now concrete, not candidates: the per-side overlay IS `config/loader-source-overlay.yaml` (D2 — ships EMPTY producer-side, built explicitly as your rebind seam), the URN handle is D3, the same-id/changed-meaning guard is D4's retired-id refusal list, and the registry-redesign directive is the whole of N7. The catalog id collision has an SME naming ruling (`pat:product-catalog` / `pat:people-report`) that matches NEITHER legacy string. See step 51(a)/(b) for the port disposition and the CAUTION.** Your gate still rules — producer sign-off never substitutes for it | pending — inputs delivered, ruling open |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section (guardrail 1 has the `git show` path; they are NOT restated here). T9 reminder: producer sign-off never substitutes for load verification on
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

51. REGISTRY SCHEMA v2 LANDS + THE T19 INPUTS ARRIVE + EPIC R RUNTIME + THE LEDGERS
    (2026-07-30 → 2026-07-31; `e0dc403..cewilson/main` — compute the range live and
    record the exact head in the PORT-REPORT; 45 commits to `6113d10` known at
    2026-07-31). Read (b) FIRST: it decides whether you take this step whole or in
    two passes.
    a. N7 SOURCE-REGISTRY-V2 GATE [SME-SIGNED] (`323f5aa`; claim `9c98b71`).
       **This is the design session your T19 row was holding four inputs for — it
       ran, and it ruled once rather than four times, exactly as intended.** Ten
       rulings, two SME amendments, one explicit residual, SME chad.wilson; gate
       prompt `config/gate-prompts/source-registry-v2.yaml`, outcome in the
       union-append gate-log. The four rulings that matter to you:
       - **D1 two-level identity** — SYSTEM rows (connection/locator/classification)
         split from DATASET rows (gate/crosswalk/feeds_taxonomy, each with its OWN
         `confirmed`); loaders bind to the DATASET. Amendment: `seal_id` is a
         standing PLACEHOLDER on committed system rows (ccb-twin convention).
       - **D2 per-side overlay** — config wins over class defaults. This is your
         rebind seam; see the divergence ledger row.
       - **D3 URN** `urn:drydocs:dataset:{carrier-or-origin},{artifact},prod`,
         derived deterministically — a render, never a hand-maintained field.
       - **D4 reconcile guard** — renamed rows carry `replaces:`, retired ids land
         in a refusal list, and BOTH `SourceRegistry.from_yaml` and the overlay
         guard refuse a retired id. Same-string-different-meaning — the T19 failure
         itself — becomes structurally impossible rather than merely documented.
       Q1 fixed the id grammar (`{origin}@{db}.{schema}.{table}` for replicas,
       `{system}:{artifact}` born-here, lowercase; real db/schema are connection
       coordinates → internal twin only, committed ids carry `[db].[schema]`
       placeholders). Q6 ruled that signed gates TRANSFER across renames — identity
       refactoring is not meaning change — so no previously-signed gate re-opens.
       RESIDUAL, stated: the 18-row migration table was NOT block-confirmed; rows
       confirmed individually at the build.
       **Producer sign-off does not substitute for your T19 review.** This feeds it.
    b. N9 SCHEMA v2 BUILD [TEST-PINNED] (`86914ad`; claim `c0b623a`). 15 systems /
       28 datasets / 17 retired ids; 14 loaders rebound; ledgers, captures, the
       taxonomy-ontology map and audit-fields re-keyed; doc-registry pipeline twins
       dropped per Q5 (one home per source); the `snow` SaaS system registered per
       Q4; URNs derived; a gate-log AMENDMENT entry maps every old id → new id so
       history keyed on v1 ids stays traceable.
       ***CAUTION — this is the one sub-stream that can break your loaders.***
       `SourceRegistry.from_yaml` now REFUSES any id on the D4 retired list, and
       **both `catalog-pat` and `pat-catalog` are on it** (the T19 ruling replaces
       them with `pat:product-catalog` + `pat:people-report`, deliberately matching
       neither legacy string). Your loaders bind those strings today.
       - Do NOT resolve this by adopting producer source_id values — the
         divergence-ledger rule is unchanged, and a wrong-but-resolving value is
         precisely what presence tests do not catch.
       - The intended path is (a)'s D2 overlay: your loaders keep their names, and
         `config/loader-source-overlay.yaml` maps them to whatever dataset ids YOUR
         T19 gate rules. That file is the seam; it exists for you.
       - Legitimate disposition: DEFER (a)+(b) as one unit under T19 and take
         (c)–(h) now. They are independent — nothing in (c)–(h) reads the registry
         schema. Document the split in the PORT-REPORT.
       Retires step 50(b)(2)'s caution: the loader-field agreement guard now reads
       through the overlay, so it no longer presupposes N3 class declarations.
    c. J23 CLASSIFICATION COLLAPSE [RECORD-CORRECTION + GUARD] (`dba8150`; rationale
       `9f9744c`, claim `e477b9f`). Four tiers → three: **Internal-Confidential is
       gone**, folded into Internal (a 4th tier can return if a real handling
       difference ever materializes; confidential handling now rides as a note on
       the entry). Touches `config/classification.yaml`, `config/README.md`, 8
       registry entries and 3 taxonomy files, plus the CLAUDE.md / PUBLISH-BOUNDARY
       tables.
       ***CHECK BEFORE APPLYING:*** `test_classification.py` is in your acceptance
       gate, and there is no unlabelled default. If ANY company-only source row is
       still labelled `Internal-Confidential`, the incoming classification.yaml
       refuses it and your suite goes red. Sweep your registries first; the fix is a
       relabel to Internal plus a handling note, not a re-added tier.
    d. J22 UNTRACKED-PATH GUARD [LIVE-VERIFIED] (`e2bf366`; claim `889488f`).
       Closes the blind spot step 50(a) called "a known producer IDEAS bug": the J16
       manifest-coverage guard now walks tracked paths AND
       `--others --exclude-standard`, so a new file catches its missing manifest row
       BEFORE it is staged. Proven with a pre-add probe. Adopt — it is the guard that
       would have caught the load-map.html row 50(a) had to correct by hand.
    e. EPIC R AGENT RUNTIME [LIVE-VERIFIED producer-side] (`59250cf`, `7e9ed8b`,
       `66eadb5`; follow-ups inboxed `8801e1f`). R4 ephemeral session-scoped
       QuerySpecs (`eph.<hash>` refs, agent-key-gated, frozen params, TTL + capacity
       bounds; `/raw-cypher` untouched). R3 agent-run telemetry — a per-call JSONL
       ledger in `DRYDOCS_LOGDIR` (full question text is ledger-only, never graph)
       plus `:AgentRun` written to **ddcontext** by a dedicated writer that refuses
       drydocs. R5 the Ask spoke (streamed steps over SSE, citations carrying trust +
       classification, metrics chip).
       Your side: the R3 graph half needs the multi-DB deploy — that is still **T7**.
       The JSONL ledger works without it. `google-adk` stays pinned `>=2,<3` (R10).
    f. Q13 VENDOR-DOCS PIPELINE [TEST-PINNED — mechanism only, NO corpus]
       (`e549f07`, `8a1780c`, `1c183d6`, `5a9160e`, `9713118`). A STANDALONE external
       vendor doc pipeline: capture (`scripts/external_vendor_scrape.py`, with the
       Q12 page-count refusal that stops a 2k–11k-page scrape before it starts) →
       convert → load, with two new CLI verbs and its own `:Document`/`:Chunk`
       writer. New `bmc-controlm-utilities` doc-registry entry ships
       `confirmed: false`, so `_gate_loader` refuses the load until a gate signs it —
       adopt the config as-is, do not flip it. **No captured content crosses:** the
       HTML lands out-of-repo under `DRYDOCS_DATA_ROOT` and is gitignored. Also adds
       a `documentation:` currency pointer on the `controlm` registry product
       (docs_version vs the version you actually run).
    g. UI LEDGERS [TEST-PINNED] (`31dcfe5`, `975a144`, `369f1f6`, `133eaf0`).
       `config/taxonomy/ui-components.yaml` (62 first-party React components, drift-
       guarded in BOTH directions against `web/src`) and `config/taxonomy/ui-tests.yaml`
       (suites keyed to console modules; `execution: manual` — no runner exists, and a
       test enforces that flag). Both land as `canonical-producer` via `config/**`.
       ***Expect the drift guard to fail on arrival if your `web/src` differs from
       producer's*** — that is the guard working. Disposition: adapt the ledger to YOUR
       tree (it is an inventory of what each side built), do not delete the guard.
    h. DOCS + PROCESS [RECORD] — J19 pull-rule discipline now explicit in CLAUDE.md §0
       and the backlog header (`bff98f5`, `16de770`); FCDO framework capture re-homed
       to `internal/` with an alignment plan (`8abc05f`); the registry-redesign plan
       that became N7 (`2d6f705`, `8747fed`); grooms (`1bae5ac`, `3c76234`, `db74546`,
       `e9ece37`, `c9ba402`).
       **L21 + J25 (`554a4e8`) concern you directly:**
       - **§6a of this prompt is NEW — it is the paste-ready T11 ratification block.**
         It was previously only ever "provided in a session", which is why T11 has read
         `pending` since 2026-07-21 with nothing openable behind it. Fill the four
         bracketed placeholders from your PORT-REPORT and append it to your gate-log.
       - L21 revised the startup-refresh runbook to Rev 5: the per-file supplement
         verbs collapse to the one `apply-supplements` chain. Step 46(c) warned this
         was coming ("your doc, your rev"). Producer-side the collapse also fixed a
         real defect — the old block listed base/seal/catalog and OMITTED registry, so
         the runbook told readers to skip the supplement that `load-software-registry`
         depends on. **Check your initial-load runbook for the same omission**; it is
         a content bug, not a style one. Rev 5 also names `load-doc-traceability` in
         the ingest step. See the divergence ledger for the rev-pin note.
       - RETIRED from the producer tree: `docs/port-step46-company-prompt.md` — spent
         per its own lifecycle note once PORT-REPORT-94132c80 was written; its durable
         content lives in the PORT-MANIFEST rows it created. Recoverable from git
         history. `docs/port-ais-supplement-company-prompt.md` STAYS (T17 open).
    Snapshots `fea4f03` / `b940d25` / `f7b2806` / `ecf49d4` / `6113d10` are EXCLUDED
    class (guardrail 4 + the never-port manifest row).
    Producer reference at `6113d10`: full suite **1269 passed / 5 skipped**, Track-1
    **124 passed / 0 skipped** — both with the production CSV PRESENT on the measuring
    machine. `EXPECTED_CONSTRAINTS` is UNCHANGED at 51 across the whole step-51 range
    (v2 is an identity refactor; it adds no active edges).

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `6113d10` (step 51): 124 passed / 0 skipped WITH the
  production CSV present (unchanged since step 49; sample-backed tests skip without
  it — at step 48 the CSV-absent figure was 114 / 3). Company baseline is ABOVE the
  producer floor — compare against your own PORT-REPORT-e60822fc numbers, not these.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR,
  capability_assert=false skips per T18; a temporary company-side failure on the
  J21 loader-field guard is EXPECTED until the step-50(b)(2) adaptation is applied —
  step 51(b) retires that particular adaptation, but introduces its own: if you take
  51(b) without your T19 ruling, retired-id refusals will fail loudly, which is the
  guard doing its job and the signal to DEFER (a)+(b) rather than to weaken it).
  Producer reference at the current head (step 51, `6113d10`): 1269 passed /
  5 skipped, production CSV present. Earlier heads (e0dc403 1163/5, 3fe69c1 1144/5,
  8a82e3b 1099/7, 947920c 1070/8, 78ba7fd 982/6) and the 483→831 series for steps
  28–42 are in git history and the archive — do not re-derive them here.
  Company reference: your own PORT-REPORT baseline.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (producer-side at the
  back-flow enactment: 12 passed / 4 skipped; the J16 manifest-coverage /
  default_ok / backlog-no-regression checks run unconditionally, no env var needed).
```
