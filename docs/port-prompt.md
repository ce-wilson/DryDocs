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

**Roll state.** Steps 50 + 51 COLLAPSED at the 2026-08-01 roll (both applied in
PORT-REPORT-57914bf4). The live ledger is **step 52 only**. Steps keep the
verification tags introduced at step 49 — `[SME-SIGNED]`, `[LIVE-VERIFIED]`,
`[TEST-PINNED]`, `[STAGING-ONLY]`, `[RECORD-CORRECTION]`, `[UNRULED]` — so review
effort goes to what is genuinely open. Anything untagged is NOT confirmed: treat
contracts as ASSUMED until your side validates them (the T10/T13 discipline).

Authorities are unchanged: [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml) is the WHAT
(per-path disposition, first-matching-glob-row wins); [`git-readme.md`](../git-readme.md)
is the WHY + the acceptance oracle; this prompt is sequencing + delta context only.

## Last completed port

- **Producer head `57914bf4`** (2026-07-31), applied company-side as
  **PORT-REPORT-57914bf4** — range `e60822fc..57914bf4`, 55 commits, scoped
  TREE-RECONCILE. Landed as merge `7b85a034` (`--no-ff`; pre-port baseline
  `7ffd430c` preserved as FIRST PARENT — which is what makes `git show
  7ffd430c:<path>` a durable pointer from any clone), and **pushed to company
  origin 2026-08-01** (reported, not producer-verifiable). Company acceptance:
  Track-1 `120 / 3 / 0`, full `1569 / 24 / 0`.
- **Steps 50 + 51 applied in full**, collapsed: 50 — manifest row, J21 registry
  hardening, T19 capture, registry-redesign directive, Unity Catalog note.
  51 — N7 gate + N9 schema v2, J23 classification collapse, J22, Epic R
  (R3/R4/R5), Q13 vendor-docs, UI ledgers, L21/J25.
- **N9 registry v2 was FULL-ADOPTED, not deferred** — all 57 company v1 sources
  migrated, 18 company loaders rebound through `config/loader-source-overlay.yaml`
  (D2's first real use, and what made full adoption possible). **T19 therefore
  narrows to the N3–N6 load-map stream ONLY.**
- **Tier-A ratifications landed** in the company gate-log 2026-07-31:
  `source-registry-v2` (N7/N9) and `J23`. L7 was already ratified 2026-07-27 —
  T11 is discharged.
- **Owed company-side** (config adoption never substitutes for graph writes):
  T9/T15 graph loads of the v2-registered datasets, code-graph and
  doc-traceability; T15 P3 host wiring; **DD5** the 18 dropped `reference_docs`
  re-home; T18/48e depgraph fork consolidation (their snapshot ritual is blocked
  until it clears).
- Earlier ports: 43–48 in PORT-REPORT-94132c80, 49 in PORT-REPORT-e60822fc.

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
- **`catalog-pat` ≠ `pat-catalog` — RESOLVED 2026-07-31 by the v2 rename, kept as
  history because it is the reason D4 exists.** The same string named DIFFERENT feeds
  in the two repos, and presence/resolution tests cannot catch a wrong-but-resolving
  value. The N7 ruling replaced both with `pat:product-catalog` + `pat:people-report`
  — matching NEITHER legacy string, so neither repo's wrong value survived — and both
  legacy ids sit in the D4 retired-id refusal list, which now makes the recurrence
  structurally impossible rather than merely documented.
- **Registry v2 is now a COMPANY-CANONICAL SURFACE (PORT-REPORT-57914bf4).** The v2
  systems/datasets shape, `loader-source-overlay.yaml` (18 company loaders) and the
  retired-id refusal list are company-canonical from here. Future ports reconcile
  **v2 ↔ v2**, not v1 → v2; a producer row and a company row with the same dataset id
  are the SAME thing now, which is what the D4 refusal list exists to keep true.
- **Gate-state values diverge by design, and the tests know it:** `cm_hosts`
  `confirmed: false` company-side (T15, P3 not wired) vs producer `true`;
  `controlm:deftable-xml-export` `confirmed: true` company-side (live XML ingestion)
  vs producer `false`. The company `test_source_registry` gate-state list is adapted
  to match. Do NOT "fix" either direction — the value follows each side's reality.
- **Company `.gitignore` additions are standing:** `/scratch/`, `/.oracle-config/`,
  `/workspace/`, local model/log ignores. J22's untracked-sweep guard requires the
  company working tree to be gitignored-clean, so these are load-bearing, not noise.
- **NEVER `git clean` during a port.** The company tree carries ~25 untracked paths
  including the `internal/**` data corpora and `UI-WIP/**`. `git reset --hard` leaves
  untracked files alone; `git clean -fd` destroys them with NO reflog recovery.
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
  **2026-07-31 (L21, applied at PORT-REPORT-57914bf4): a THIRD pin in this same file moved —
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
- L7 ratification: **DISCHARGED** (company gate-log 2026-07-27; T11). §6a below stays
  as the STANDING Tier-A template — `source-registry-v2` and `J23` both used its shape
  at PORT-REPORT-57914bf4, and every future Tier-A adoption needs one.
- TRACKER (T1–T8 origin steps live in the archive — guardrail 1 has the path).
  **STATUS IS A PRODUCER BELIEF, NOT COMPANY STATE.** The producer cannot see your
  gate-log or your tree, so every `pending` here means "not known to be done", never
  "confirmed open" — T11 read `pending` for four days after the company had already
  ratified it. Rows now carry an as-of date; correct any that are stale in your
  PORT-REPORT and the producer will flip them:

| # | Item | Status |
|---|------|--------|
| T1  | K2 live attribution load + job-seal-app-ref confirmed→applied flip | pending (producer belief, as of 2026-08-01) |
| T2  | FID→seal_id reconciliation table sourced + wired (TierReconcilers) | pending (producer belief, as of 2026-08-01) |
| T3  | ALIAS reconciliation table sourced + wired | pending (producer belief, as of 2026-08-01) |
| T4  | Real tier-5 manual CSVs under internal/ + own manifest entries | pending (producer belief, as of 2026-08-01) |
| T5  | P1 internal probes P0/P4 — unblocks P2 loader (archive step 31) | pending (producer belief, as of 2026-08-01) |
| T6  | Docs Track-2: docs-fetch/docs-load vs real sources (archive step 16) | pending (producer belief, as of 2026-08-01) |
| T7  | Live multi-DB Enterprise Neo4j deploy — G7 half (archive step 16) | pending (producer belief, as of 2026-08-01) |
| T8  | M0 equivalence unblocks: A3 filename + B1 dot rule (archive step 29) | pending (producer belief, as of 2026-08-01) |
| T9  | Lineage curated live load — YOUR vocab gate + m3_* flips, then write_curated on your graph | pending (producer belief, as of 2026-08-01) |
| T10 | MAC field contract validated vs a REAL DPL export — amend dpl_mac.py contract + fixtures together | pending (producer belief, as of 2026-08-01) |
| T11 | L7 ratification entry in company gate-log (Tier A record) | **RATIFIED 2026-07-27** (company gate-log, prior port; reported at PORT-REPORT-57914bf4). The producer row read `pending` until 2026-07-31 — producer-side staleness, not a company gap. §6a stays as the STANDING Tier-A template (source-registry-v2 and J23 both used that shape) |
| T12 | Company platforms gate: AIS position vs producer C12 | **RULED — SUPERSEDE, 2026-07-21** (company gate-log): the AIS layer is superseded by the software-registry model; excision applied, Tier B holds discharged 2026-07-27, session packs retired |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending (producer belief, as of 2026-08-01) |
| T14 | rua collector convergence: company's own -n implementation vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible. Step 49e's G45 listing fallback is the same family — reconcile together | pending (producer belief, as of 2026-08-01) |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways; primary on-main checkout, never a worktree) → `drydocs load-code-snapshot` into your graph; second `:Project` root is INTENDED (gate §B3(a)); rides with the Tier A ratification entry (guardrail 6) | pending (producer belief, as of 2026-08-01) |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 staging stand-in as the feed (G40 parse stays as cross-check); premise correction folded into G22 prep. NOTE step 49g: if the XML export becomes a standing feed, this retirement gains a SECOND path — the unruled precedence question decides, not the port | pending (producer belief, as of 2026-08-01) |
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | pending (producer belief, as of 2026-08-01) |
| T18 | Depgraph fork capability catch-up (owed action 48e, PORT-REPORT-94132c80): your separately-owned depgraph fork lacks the U6 multi-root resolver (and `--tree`), and the producer remote is unreachable from it, so the port could not remediate. Until it catches up, `config/dev-environment.yaml` keeps `depgraph.capability_assert: false` (test skips, owed action recorded). When it gains the capabilities: flip the flag true and your `snapshot.ps1` refusal guard goes live | pending (producer belief, as of 2026-08-01) |
| T19 | N3–N6 LOAD-MAP adoption gate — **narrowed 2026-08-01**: registry v2 is ADOPTED (N9 full-adopt at PORT-REPORT-57914bf4), so this row now covers ONLY the N3 class-declaration derivation, the N4/N5 renders and N6. The id-collision blocker is resolved by the v2 rename (`pat:product-catalog` / `pat:people-report`); what remains is the sourceless company-only loaders. Company `cli.py` still has no `COMMAND_LOADERS`/`CANONICAL_LOAD_SEQUENCE` and the load-map pair stays out of the company board render until this rules | pending (producer belief, as of 2026-08-01) |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section (guardrail 1 has the `git show` path; they are NOT restated here). T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10/T13: until a real export parses with zero mismatches, treat the
  field names as ASSUMED.

STEP LEDGER — delta since `57914bf4` (steps 43–51 collapsed above). Each sub-stream
carries its producer-side verification status in [BRACKETS]; spend review on [UNRULED].

52. CI DETERMINISM FIX + **J10 COMPLETE PRODUCER-SIDE** (2026-07-31 → 08-01;
    `57914bf4..cewilson/main` — compute the range live; 16 commits to `0ab54cd` known
    at 2026-08-01). ***READ (b) BEFORE PLANNING THE RANGE.*** The diff is dominated by
    a 284-file whole-tree reformat that you must NOT apply as content — classifying it
    path-by-path under guardrail 2 would be 284 wrong decisions.
    a. RENDER DETERMINISM [LIVE-VERIFIED] (`7ccc655`). Producer CI was RED every run
       2026-07-21..07-31 on `test_committed_matrix_matches_regeneration` claiming
       `enforcement-matrix.json` drift. It had not drifted: the renderer sorted `Path`
       OBJECTS, and `PurePath.__lt__` compares a key that is case-FOLDED on Windows and
       case-SENSITIVE on POSIX, so a matrix committed from Windows can never match its
       own regeneration on a Linux runner. Fixed with `key=lambda p: p.as_posix()`;
       `tests/unit/test_render_determinism.py` now asserts the RULE (a drift guard
       compares a render against itself and can never catch this class).
       ***YOUR `render_enforcement_matrix.py` IS A 3-WAY MERGE WITH COMPANY SURFACES
       ROWS*** — take the `key=` change into YOUR file; do not overwrite it wholesale.
    b. J10 ALL SIX STAGES LANDED [LIVE-VERIFIED] (`f18c88e`, `966b324`, `f90ad92`,
       `2a4f0be`, `3a8bdbd`, `6d4a10a`, `1fcbf63`, merged `--no-ff` as `fb798c5`).
       **1,017 findings → 0**; 284 of 328 files reformatted; producer CI now BLOCKS on
       both `ruff check` and `ruff format --check`. Guardrail 9 has the port
       disposition per stage and it is unchanged — but the range now carries stages
       1–5, not just stage 0, so the DO-NOT-PORT half is live:
       - **stages 1/2/3 are the 284-file sweep. Do not apply, do not hand-merge, do
         not tree-reconcile.** Take stage 0, then run the same pinned tool on YOUR
         tree; the plan doc §3 is the regeneration procedure.
       - **stage 4 PORTS** (`pyproject` ignores + the vendored-skills `extend-exclude`)
         but its CONTENT was a per-origin judgement: 177 of 362 residual findings were
         vendored Anthropic skill scripts we do not author. Re-make that call against
         YOUR residual — do not assume the same split.
       - **stage 5 PORTS LAST**, only once your own residual is zero, or your CI reds
         out by construction.
       - `.git-blame-ignore-revs` is `never-port` (manifest row): those are PRODUCER
         SHAs and mean nothing on a disjoint history. List your own stage-3 SHA.
       Three execution findings that would be buried by the cheap option — ruff's F841
       unsafe fix leaves dead code, a `pytest.raises(Exception)` proving nothing, and
       RUF003 hiding a double-encoded character — are written up in the plan doc's
       "Three findings from execution". Read them before running stage 2.
    c. B023 FIX [PORTS normally] (`b3b90dc`) — `marker=marker` late-binding bind in
       `benchmark_p0.py`. Hand-authored, NOT a mechanical stage-2 commit.
    d. PORT-CONTROL DOCS [never-port, but they change YOUR next port] (`7f6c5d2`,
       `6e993d2`): guardrail 3 now requires the port to be COMMITTED before the
       PORT-REPORT is written, with `rev-list --count` quoted as proof; guardrail 5
       drops the `.print.html` twins claim; T11 recorded discharged; v3 length
       discipline added. Your copy of this file is your own — re-read it at the
       producer ref rather than assuming your copy is current (yours was stale at
       94132c80 this port).
    Producer reference at `6e993d2`: full suite 1272 / 5 skipped, Track-1 124 / 0.
    `EXPECTED_CONSTRAINTS` unchanged at 51.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `6e993d2` (step 52): 124 passed / 0 skipped WITH the
  production CSV present (unchanged since step 49; sample-backed tests skip without
  it — at step 48 the CSV-absent figure was 114 / 3). Company baseline is ABOVE the
  producer floor — compare against your own PORT-REPORT-e60822fc numbers, not these.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR,
  capability_assert=false skips per T18). A retired-id refusal from
  `SourceRegistry.from_yaml` is the D4 guard WORKING, not a port failure — rebind the
  loader in `loader-source-overlay.yaml`, never by re-adding the retired id.
  Producer reference at the current head (step 52, `6e993d2`): 1272 passed /
  5 skipped, production CSV present. Earlier producer heads are in git history and the
  archive — do not re-derive them here.
  Company reference (PORT-REPORT-57914bf4): full `1569 / 24 / 0`, Track-1 `120 / 3 / 0`.
  COUNT THE RIGHT THING: producer "changed paths" (the range diff) and company
  "files in the port commit" are different numbers by construction — 139 vs 135 this
  port, because the company figure counts the APPLIED RESULT (regenerated derived
  artifacts + adaptations) and drops excluded paths. And `git status --short` line
  count is NOT a file count: `MM` and rename double-entries inflate it (that is where
  the transient "159" came from). Reconcile the three in your PORT-REPORT.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (producer-side at the
  back-flow enactment: 12 passed / 4 skipped; the J16 manifest-coverage /
  default_ok / backlog-no-regression checks run unconditionally, no env var needed).
```
