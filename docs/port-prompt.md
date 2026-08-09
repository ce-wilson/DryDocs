# Port prompt — producer → company (rolling)

**Format (v3 rolling, 2026-07-31).** This prompt carries ONLY (1) the durable
guardrails and (2) the step ledger since the last completed port. Steps 1–42 are frozen
in `port-prompt-archive-steps-1-42.md` (guardrail 1 has the path); numbering continues
here at 43. The archive is FROZEN — applied steps ≥43 are never appended there; their
full text lives in git history and the company PORT-REPORT.

**CLOSING SEQUENCE (J35, 2026-08-09 — MANDATORY, structural, in this order).** A port
is not closed until every step below is done; skipping any of them is how three
consecutive rolls discovered unrecorded ports after the fact (PORT-REPORT-f71967db,
PORT-REPORT-6713c142, PORT-REPORT-5f79d145 — the last two left NO producer-verifiable
range, port commit, backup tag or acceptance numbers, an absence no later roll can
repair). Company-side at completion:
1. Write the PORT-REPORT (guardrail 8) with every producer-tree citation SHA-stamped.
2. Update **Last completed port** here with the FOUR REQUIRED FIELDS — none may be
   omitted or deferred: (a) the applied RANGE (`<base>..<head>`, with `rev-list
   --count`); (b) the PORT COMMIT(s) on the port branch; (c) the BACKUP TAG and the
   `rev-list --count <tag>..HEAD` proof; (d) the ACCEPTANCE NUMBERS (full suite,
   Track-1, reconcile guards). A close missing any field is an unrecorded port by
   definition — the motivating class above.
3. Collapse the applied steps to ONE LINE each; fold new standing divergences into
   the ledger.
Producer-side at the next session: verify the roll against `git log
<last-ported-head>..HEAD` COMMIT-BY-COMMIT (the roll-procedure rule below), never by
eyeballing back from the newest entry.

**LENGTH DISCIPLINE (v3 rule, and the reason for it).** This file regrew to 567 lines by
step 51 because each roll added prose that the next roll never removed. A prompt nobody
finishes reading is not a control document. So:
- a step-ledger sub-stream gets **≤ 8 lines**: what changed, its verification tag, and
  the ONE caution that would cost you a rework. Everything else belongs in the commit
  message, which is one `git show` away;
- a tracker row gets **one sentence plus a pointer**, never a paragraph;
- a roll REPLACES the previous roll note; it does not stack another one;
- if a section can only be understood by reading it twice, cut it rather than expand it.

**Roll state (2026-08-09 pm, the post-`0d3761a9` roll).** The ledger is now rolled
through the NAMED deliberate end **`0d3761a9`**. Steps **106–115 are APPLIED** and
collapse into **Last completed port** below; the live ledger restarts at **116+**,
delta since `0d3761a9`.

> **`0d3761a9` IS BUILT, NOT YET MERGED.** The port commit sits on the company branch
> `drydocs-port-20260809` and is **not pushed** — the P8 merge is SME-gated. Treat the
> range as ported for LEDGER purposes (it is built, tested and reported) but NOT as
> landed for anything that depends on the merge: specifically, the **five staged
> `docs/gate-*-company-prompt.md` clean-add rows stay staged** until the branch merges
> (step 108). Do not remove them on the strength of this report.

**Last completed port — the four required fields (J35).**
- **Range:** `5417ef10..0d3761a9` — 68 commits, ledger steps 106–115.
- **Port commit:** `b077f746` (branch `drydocs-port-20260809`, 97 files); the
  PORT-REPORT + ledger roll landed separately as `1c102fc`.
- **Backup tag:** `pre-cewilson-port-20260809` @ `60de653d`.
- **Acceptance:** `tests/unit/` **1989 passed / 32 skipped / 1 failed** — the single
  failure is PRE-EXISTING (`test_code_snapshot_loader::test_committed_newest_snapshot_is_accepted_and_clean`,
  the T19/WP1.4 committed-snapshot infra-block; it fails on company HEAD's own adapter
  too, so it is not port-introduced). Track-1 contract **123 passed / 3 skipped**.
  J7/J34 reconcile guards **21 passed** with `RECONCILE_BEFORE_DIR` set — no status
  downgrade, no dropped entry, gate-log append-only, and the J34 overlay covering the
  9 company-only paths.

**What the range carried, in one line each.** J34 manifest-overlay migration landed
ATOMICALLY (producer `PORT-MANIFEST.yaml` + the overlay guards taken together, and
`PORT-MANIFEST.company.yaml` created with the 9 company-only `default_ok` rows) — a
verbatim manifest take can never again drop a company-only disposition, which is the
structural fix for the 2026-08-06 clobber. Backlog union **317 → 374**: 34 in-range plus
the **23-item pre-base gap-heal**, extracted from the exact SHA `0d3761a9` rather than
producer HEAD, with X3/X4/J30 venue-noted and the summary recomputed. One structural
collision, `C24`, resolved evidence-backed rather than by a silent pick: the company's
C24 was a duplicate of the already-`done` N8, so the producer's canonical C24 stood.

**THE CRITICAL CORRECTION, and it is a rule this file now carries.** The company's
initial vocabulary reconcile WRONGLY ACTIVATED the G55 `rua-load-shapes` lineage flips.
K8 (`seal-app-ref-edge-reshape`) is signed company-side; `rua-load-shapes` is a
DIFFERENT gate and is still UNSIGNED there. All three vocab fragments were reverted to
company HEAD so those entries stay `planned`, and the G23/rua code ported INERT because
it is gate-bound and refuses the planned labels.
**RULE: gate-bound files are never wholesale-take candidates.** "Identical to base" and
"per-entry equivalent" are BOTH insufficient tests for them — a producer vocabulary or
test file can be byte-identical to the base and still assume an active gate the consumer
has not signed. Status/id-set parity is not field-and-gate parity. Check the GATE, not
just the diff.

Prior roll state, retained for context: the ledger was previously rolled through
**`5417ef10`** (PORT-REPORT-5417ef10). Steps **55–105 are COLLAPSED** (one-liners in **Last completed
port** below): steps 84–105 were applied at the two producer-VERIFIED ports
(PORT-REPORT-a14a8028, PORT-REPORT-5417ef10); steps 55–83 were applied by the two
reported-only mid-range ports (PORT-REPORT-6713c142, PORT-REPORT-5f79d145) and carried
through the verified ports' green acceptance — their own range/backup/acceptance
fields remain unrecoverable, and this roll RECORDS that gap rather than inventing
values (the closing-sequence rule above exists so the class cannot recur). Steps
**102–105** ledger the `a14a8028..5417ef10` range that previously sat past step 101
unledgered (the cc3e98e inbox line, now closed). The live ledger runs **106+** below,
delta since `5417ef10`, rolled BEFORE the port that will carry it — the second roll
run that way. Verification tags (`[SME-SIGNED]`, `[LIVE-VERIFIED]`, `[TEST-PINNED]`,
`[STAGING-ONLY]`, `[RECORD-CORRECTION]`, `[UNRULED]`) carry forward; anything untagged
is NOT confirmed — treat contracts as ASSUMED until your side validates them (the
T10/T13 discipline).
**ROLL-PROCEDURE RULE:** currency is verified by diffing the ledger's claimed coverage
against `git log <last-ported-head>..HEAD` COMMIT-BY-COMMIT — never by eyeballing back
from the newest entry. Both historic gaps (the f71967db port unrecorded here;
O27/O28/C17/Q7/R6/S1 never ledgered) were caught by the company session's own range
enumeration — the guardrail-2 safety net working, not a reason to keep the habit.

Authorities are unchanged: [`PORT-MANIFEST.yaml`](../PORT-MANIFEST.yaml) is the WHAT
(per-path disposition, first-matching-glob-row wins); [`git-readme.md`](../git-readme.md)
is the WHY + the acceptance oracle; this prompt is sequencing + delta context only.

## Last completed port

> **FETCH RESOLVED (2026-08-06) — the 2026-08-05 blocker is CLOSED.** SME confirms
> producer fetch works company-side, so guardrail 1 is executable again: read at producer
> **HEAD**, not at the ref you last fetched. The prior failure was access (the repo was
> `PRIVATE` and healthy throughout), and its lesson stands rather than expires — a failed
> fetch degraded silently into answering from a cached `5f79d145`, which reads exactly like
> a current answer. **If fetch fails again, STOP and say so; do not fall back to a cached
> ref.** That fallback is the one failure guardrail 1 exists to prevent, and it cost a
> cycle of "the producer tracker says…" answers that were two days stale.

- **Producer head `5417ef10`** (2026-08-07), applied company-side as
  **PORT-REPORT-5417ef10** — range `a14a8028..5417ef10` = **50 commits / 63 changed
  paths, PRODUCER-VERIFIED 2026-08-07** (rev-list and diff counts match; G22 sign-off
  `3648cfcd` in range; the gate-log heading the report quotes matches verbatim).
  Branch `drydocs-port-20260807` (2 port commits, HEAD `6ec69db2`), backup tag
  `pre-cewilson-port-20260807` @ `cb5b83d8`; **`--no-ff` MERGED onto company `main`
  2026-08-07 (SME).** The G22 ratification session runs against the merged tree —
  verify the 28/28 gate-log line first, per the staged prompt (the company's merged
  copy of that prompt is the live one; the producer original is archived, see the
  prompt-retirement note in this entry's commit). Suite **1925 / 1 / 27** (single fail = WP1.4 infra-blocked carryover);
  Track-1 123/3; reconcile guards 25 passed; zero graph writes; G23 load deferred in
  words. **Initiation note:** the port was run company-side from the staged G22 prompt's
  blocked precondition — the session correctly STOPPED, offered hold/port/verify, and
  the SME chose "land the port first"; the rolling guardrails held without a hand-given
  prompt. **CAUTION for the merge review:** the range head `5417ef10` is itself the
  "claim G55 in_progress" commit — the ported backlog shows G55 claimed with the work
  NOT in range; G55 apply (`2435a7d`), the G23 curated-load build (`ba7fbaf`) and G58
  (`461ea8e`) are among the **25 producer commits pending** for the next port
  (base `5417ef10`). **Guardrail-3 miss:** the report quotes no
  `rev-list --count <tag>..HEAD` — quote it at merge time. **Relays actioned
  producer-side (2026-08-07):** #2 audit-fields.yaml + test_module_boundary.py
  per-entry/union rows APPLIED to `PORT-MANIFEST.yaml` (this commit); the
  `confirmed`-flag drift relay was already Idea-81 and same-day groomed → **N10**
  (gate-prompt draft; schema change waits on the gate). Seal-samples §A3 fixture
  divergence (`Cloud Enablement Lead` synthetic role) is SANCTIONED — the producer
  pin's own comment names it as the set that must change; no producer edit.
  **STAGED FOR THE NEXT PORT (2026-08-07 pm):** five NEW company packs for the
  producer-signed gates with unknown company status — autosys-crosswalk (F1),
  airflow-crosswalk (F2), audit-envelope-phase4 (M3), envelope-property-terms (M4,
  run after M3), ui-write-surface (O20) — each opens with a STATUS question (an
  already-ratified answer stops the session), then an internal-dataset profile, then
  the producer rulings to finish per-item. Explicit clean-add manifest rows ride
  above the `docs/gate-*-company-prompt.md` never-port glob; REMOVE those five rows
  after the delivering port merges.
- **Producer head `a14a8028`** (2026-08-06), applied company-side as
  **PORT-REPORT-a14a8028** — range `5f79d145..a14a8028` = **107 commits, PRODUCER-VERIFIED
  2026-08-06** (range enumerated against producer git; both cited never-port docs exist;
  tracker-highest-row and `codedirectory_file_id` claims check out) — the first verifiable
  port since `40c35724`, and the first run against a ledger rolled BEFORE the port
  (steps 97–101). Port commit `fb265a26` on `drydocs-port-20260806`; backup tag
  `pre-cewilson-port-20260806` at `5e5ae723`; `rev-list --count` = 1 (guardrail 3 held).
  **Status: committed, NOT pushed/merged — awaiting company review.** Scoped
  TREE-RECONCILE, 129 changed paths, 0 J16 fall-through. Company acceptance:
  **1856 / 16 / 31** (from 69 failed at reconcile start); `EXPECTED_CONSTRAINTS`
  55→**56** company-based (`codedirectory_file_id`). The 16 remaining failures are ALL
  OWED company-side, none a silent loss. **ROOT-CAUSE COLLAPSE (company run, 2026-08-06;
  corrects this entry's first draft, which mis-blamed S4):** the 16 collapse to ~4 causes.
  A ×4 = company data (BOM CSV, 30-snapshot prune ×2 to newest-only, snapshot
  unmapped-extensions contract — CORRECTED 2026-08-06: the §E2 restatement (`e3f65af`,
  in range) demands NON-empty `unmapped_extensions` on an all-files snapshot + all
  seeded extensions bound; the "clean == {}" first-draft relay was stale, caught by
  the company session's static inspection). **B1 ×6 = the K8 folder-grain edge
  reshape was not applied to the company's EXTENDED `manual_mappings` writer** (a
  clobber-audit re-merge file) — their writer still speaks job-grain
  `{ControlMJob, WAS_ASSOCIATED_WITH}`, producer fixtures use
  `ControlMFolder -[BELONGS_TO_APPLICATION {role: seal_app_ref}]->` (producer
  `drydocs_core/manual_mappings.py`); this is ledger step 63's GRAIN-BREAKING caution
  firing, and the fix couples with the held folder-attribution stream AND K18
  tier→row_kind (step 96, also in this range) — one T23-family migration, do them
  together. B2 ×5 = per-item config/data divergence: `cm_hosts` not confirmed
  company-side (producer is `confirmed: true`, gate controlm-hosts-topology 2026-07-09,
  registry note says the confirmation TRANSFERS per Q6 — company may flip citing it, or
  ratify under the two-tier doctrine); namespace table 5 rows vs ≥6; a `;`-split
  citation parse; `control-m.md` stray feedback file; `AppCodeCascadePane` route
  clean-added but its ledger row missed. B3 ×1 = the manifest clobber (below).
  **QUICK-WINS RIDER (2026-08-06, company commit `e21c9f2f`, branch at 3 commits, revert
  tag unchanged):** B3 FIXED — company `default_ok` block re-added verbatim from the tag
  (9 rows covering all 89 paths, guard green). ui_components FIXED **by reversal, not
  ledger-add**: `AppCodeCascadePane` is HELD company-side (K7–K15 folder-attribution /
  app-code reshape is a Tier-B hold — the port had wrongly clean-added the WEB half of
  held K18 work); component removed + `MappingsRoute` reverted to the held version — it
  joins the folder-attribution hold. This SUPERSEDES the "copy `ui-components.yaml:91`
  verbatim" relay above, and is the second silent-over-adoption-of-held-work catch this
  cycle. Suite company-side now **14 failed** (was 16); remaining = Group A ×4 + K8
  reshape ×6 + config/data divergence ×4. Decisions applied: Epic X `ddlineage`
  retirement adopted at CONFIG level (live DB drop owed, `SHOW DATABASES` first);
  **company Catalog gate 2026-06-25 REVERSED** → full producer catalog model adopted
  (`code` reinstated, TC-CAT-003 retired, logged in company `config/gate-log.md`);
  5 producer gate-prompts landed as DRAFTS (unsigned company-side, correct per
  producer-sign-off ≠ company-sign-off); S10 guard extended to company's
  `PatAppLinksLoader` (→ T23 rider); G35 `Operate Manager` promoted to its own class;
  SEAL-role "admits+flags" claim record-corrected (company refuses unknown roles, same
  as producer; divergence gate-bound to G35 §A3). Clobber audit re-merged 8
  company-extended canonical-producer files; **known conscious deferral: the take
  clobbered the company's `default_ok` section in `PORT-MANIFEST.yaml`** (canonical-producer
  wins) — quantified at the root-cause run as **89 company-only paths** falling through
  `default:` (PORT-REPORT-*.md, docs/build_*, docs/site/*, docs/prompts/*, settings.json, …);
  company re-adds via `git diff pre-cewilson-port-20260806..HEAD -- PORT-MANIFEST.yaml`.
  Next-port base = `a14a8028`; 28 producer commits (G22 rulings, N8, O42, O45/O46
  intake slices) were already pending at review time.
  **FIX-SESSION CLOSE-OUT (company run, 2026-08-06; producer fix prompt
  `docs/port-fix-a14a8028-company-prompt.md`):** branch `drydocs-port-20260806` at
  **7 commits** (`rev-list pre-cewilson-port-20260806..HEAD` = 7), still **NOT merged**,
  backup tag intact. Suite **14 → 7 failed (1865 / 7 / 31)** — all 7 are documented
  deferrals, none silent: WP1.4 + the WP2 ×6. Per-package: `4283305` B3-proper
  (**corrects the quick-wins rider above — `e21c9f2f` never actually committed
  `PORT-MANIFEST.yaml`**; the 9-row `default_ok` block lived uncommitted AND
  mojibake-corrupted; re-added clean UTF-8 here); `7392e56` WP1 (BOM strip in Python,
  ASCII-ify two .ps1, prune 29 snapshots to newest-only, −3); `a4f9c46` WP3 (−5: the 4
  named + a masked deftable-xml one); `722884e` PORT-REPORT close-out. **Decisions:**
  (1) **Q1-B** — `cm_hosts` stays `confirmed: false` + namespace floor `>=5`, guards
  PINNED with re-arm triggers, standing divergence registered in company `gate-log.md`;
  a **masked second divergence surfaced and was pinned too**:
  `controlm:deftable-xml-export confirmed: true` (live XML ingestion). (2) **WP1.4
  DEFERRED as infra-blocked, not faked** — company's newest snapshot is roots-only
  (predates the all-files default); a clean all-files snapshot needs the depgraph
  instrument, but theirs (`@ 1b969ef`) reports `multi_root: false` and `snapshot.ps1`
  refuses. (3) **WP2 — B ruling, folder-attribution stayed HELD, zero WP2 edits.** The
  company vocab holds the K8 seal-app-ref reshape explicitly (`m3_belongs_to_application`
  `status: planned` / "COMPANY HOLD (Tier B) … pending a company gate that
  supersedes-or-reconciles" the still-`active` job-grain K2 edge `m3_seal_app_ref`) —
  so greening the 6 is a GATE decision, not mechanics; the **`seal-app-ref-edge-reshape`
  gate is queued as its own session**, and this SUPERSEDES the fix prompt's WP2 framing
  (which presented the reshape as owed mechanics) and the prompt's ~1870/0/31 close-out
  expectation. (4) `control-m.md` stray = company-only draft feedback, renamed to
  `controlm-ingestion-tdd-rev7.yaml` so its notes load. (5) Company memory corrected:
  **no publish boundary company-side** — seal_id / server / schema names are the graph
  metadata DryDocs documents, not PII; the classification lens is DIRECTIONAL (applies
  at the export/back-flow crossing, not at rest in company GHE). **For the producer
  (ledgered here):** `confirmed`-field semantics drift — producer uses it for semantic
  confirmation (Q6 transfer), company additionally encodes P3 wiring readiness; company
  suggests a separate `wired`/`ready` flag rather than overloading `confirmed` (inboxed
  as an idea). **T23 now BLOCKS on the `seal-app-ref-edge-reshape` gate**; its
  live-graph sequence is recorded company-side (2026-08-04 partial-doubling check →
  DROP `port_unique` → backfill `app_id = seal_id` → S10 refuses on nulls; all 8
  key-bearing sites in ONE apply). The `--no-ff` merge onto company `main` remains the
  SME's decision.
- **Producer head `5f79d145`** (2026-08-04), applied company-side as
  **PORT-REPORT-5f79d145**. Reported, not producer-verifiable.
- **Producer head `6713c142`** (2026-08-03), applied company-side as
  **PORT-REPORT-6713c142** (71 commits before `5f79d145`). Reported, not
  producer-verifiable.
- **Both of the above went UNRECORDED here until this roll (2026-08-05)**, and the
  section below still named `40c35724` as the last port — two ports stale, not one. They
  surfaced only because a company-side T23 lookup cited both report names. This is the
  third consecutive roll to discover an unrecorded port after the fact (the `f71967db`
  one is admitted in the `40c35724` entry below): **the ledger is not being rolled at the
  port, it is being reconstructed afterwards.** Neither report's range, port commit,
  backup tag or acceptance numbers reached the producer, so those fields are simply
  unknown for both — an absence this section cannot repair retroactively.
- **Producer head `40c35724`** (2026-08-03), applied company-side as
  **PORT-REPORT-40c35724** — range `f71967db..40c35724`, 34 commits, scoped
  TREE-RECONCILE. Port commit `1a3aff20` on `drydocs-port-20260803`
  (`rev-list --count` = **1** quoted in the report — guardrail 3 held; backup
  tag `pre-cewilson-port-20260803` at `8502c95c`), **merged + pushed
  2026-08-03** (reported, not producer-verifiable). Company acceptance: full
  `1652 / 28 / 0` (+84), Track-1 `123 / 3 / 0`, J7 guards 17 passed,
  `EXPECTED_CONSTRAINTS` 54→**55** company-based.
- **Applied in full, collapsed at the 2026-08-09 J35 roll — steps 55–105** (55–83 via
  the two reported-only ports, carried through verified acceptance; 84–105 at the
  verified PORT-REPORT-a14a8028 / PORT-REPORT-5417ef10; full text in this file's git
  history):
  55 backlog duplicate-key guard. 56 G51 `ddschema` DDL + database-name guard.
  57 L22 U.S. business-English guide (docs/style/** row). 58 C23 DQV seed DEFER.
  59 G51 tail — bidirectional topology guard. 60 K7 seal-app-ref-edge-reshape gate
  SIGNED 24/24. 61 K9 defined-mapping store. 62 composite-key standard (`:` join,
  ctlm_id dot form). 63 K8 folder-grain loader [GRAIN-BREAKING; T23 family].
  64 K12+K14 app-code taxonomy + strays. 65 K10 port activation cutover (`active`
  boolean gone). 66 K11 steward cascade + §G1 orchestrator edges. 67 K13
  catalog_has_application semantics. 68 U12 snapshot retention. 69 U13+U14 query-pack
  filters. 70 C22 catalog-loader orphan sweep. 71 J18/J26/J27/J28 batch. 72 M3+M4
  envelope gates. 73 Q13 vendor-docs pipeline. 74 J29 UTF-8 no-BOM. 75 Q6+Q12 docmeta
  component. 76 SDLC app-runbook outline. 77 Excel runbook skill. 78 controlm-pipeline
  stub capture (internal/). 79 G36 index drops. 80 L20 feedback stray-file guard.
  81 S5 registry fragment split [STRUCTURE-BREAKING]. 82 U9 rel-filter leak fix.
  83 ddlineage retired (topology 5→4) [LIVE-DB MIGRATION yours]. 84 depgraph pin bump.
  85 S4 console draft substrate (mapping-store v2). 86 J30 branch disposal. 87 G54
  exec-aware provision.ps1. 88 V-series module runbooks + coverage test. 89 runbook
  currency guard. 90 N6 one load sequence, two profiles. 91 K15 job-grain pane
  retired. 92 three gate prompts drafted [UNRULED]. 93 S10 pre-cutover refusal guard.
  94 C24 sparse-refresh blanking fix. 95 W1–W3 + fcdo-crosswalk gate SIGNED 13/13.
  96 K18 `tier`→`row_kind` [FORMAT-BREAKING; T23 family]. 97 K19 mapping-age suspects.
  98 J32 field-meaning rule. 99 code-graph containment tree + media types
  (EXPECTED_CONSTRAINTS 52→53). 100 SFS = target DB platform [RECORD-CORRECTION].
  101 G35 TOM-roles: four clauses ruled, gate UNSIGNED, Operate-Manager data-loss fix.
  **102–105, the `a14a8028..5417ef10` range (previously unledgered past step 101):**
  102 G22 rua-load-shapes gate session, opened→SIGNED OFF 28/28 (`47325f1`→`3648cfc`),
  including section C's .ksh SWO binding (`a4328dd` — the estate's unbound majority
  typed). 103 SEAL sample GENERATOR replaces committed samples (`180f4ae`).
  104 code-graph ASSET rulings — images (`5359b00`) then fonts (`6a11064`) skipped as
  ASSET_EXTENSIONS_SKIPPED, SME 2026-08-06. 105 the range remainder: O42 web import
  edges (`326e4c2`), N8 map-source rulings (`c2a6f58`), the SME context-intake plan +
  O45/O46 slices (`a4108fc`, `fd29f3a`), four staged company gate prompts (`4dd5720`,
  `edf2705`), port housekeeping/ledgering.
- **Applied in full, collapsed:** 52 — J10 stages + CI determinism (applied at
  PORT-REPORT-f71967db, 2026-08-01; that port went unrecorded here until this
  roll). 53 — S3 identity cutover (constraints DROP+create applied; graph
  re-key open → T23) + S2 orchestration parent (company's two extra
  `controlm/` modules RELOCATED not deleted, 3 importers repointed). 54 — J24
  sweep incl. the company-local pass, package-layer gate draft ported UNRULED,
  meta-graph/`ddschema` modules (CLI verbs deferred → T22), snapshot-series
  ruling kept a company decision, groom +9 items unioned by id.
  **PLUS six never-ledgered features**, applied by manifest classification:
  O27 `b6a2e68`, O28 `5ca0b4d`, C17 `778a90d` (orphan fix = T20 item 1
  applied), Q7 `539b400` (verb deferred → T22), R6 `e31a3fb`, S1 ADRs `8045725`.
- Earlier ports: 43–48 in PORT-REPORT-94132c80, 49 in PORT-REPORT-e60822fc,
  50–51 in PORT-REPORT-57914bf4 (N9 full-adopt; T19 narrowed to N3–N6),
  52 in PORT-REPORT-f71967db.

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
   READ AT PRODUCER **HEAD**, NOT AT THE REF YOU LAST FETCHED: `git fetch cewilson`
   FIRST, then `git show cewilson/main:<path>`. "The producer ref" was ambiguous and
   that ambiguity cost a real answer — at PORT-REPORT drydocs-port-20260801 the tracker
   was read at pinned `f71967d`, correctly found T1–T19 there, and concluded T20/T21
   "were never created"; both existed at producer HEAD, and T20 was eight findings about
   the company's own catalog loaders. QUOTE IN THE PORT-REPORT the producer SHA you read
   the tracker at AND the tracker's highest row number. Reading at a ref is unverifiable
   from outside; a row count makes staleness self-announce as a mismatch instead of a
   confident "that row does not exist."

   RE-DERIVE, DON'T TRUST THE PROSE (added 2026-08-05). The steps below quote facts
   that live in code and config, and a quoted fact is a COPY — it is current the day
   it is written and silently wrong afterwards. `tests/unit/test_runbook_currency.py`
   now covers this file, but it can only prove the things named here EXIST; it cannot
   prove a step's instructions are still right. So the four facts a port actually acts
   on each ship a command that regenerates them. **The output wins over the prose,
   always — if they disagree, the prose is the stale one and says so here in advance.**
   Run each in YOUR checkout, not the producer's: that is the point of them, because a
   disposition, a verb set and a load sequence are all legitimately yours to differ on.

   ```powershell
   # 1. MANIFEST DISPOSITION for one path — first matching row wins, and hand-reading
   #    that order is exactly what goes wrong. Reports the winning row, the default_ok
   #    fall-back, or an undecided path (J16).
   poetry run python -c "import re,sys,yaml;g=lambda p:re.compile(''.join('.*' if s=='**' else '[^/]*' if s=='*' else '[^/]' if s=='?' else re.escape(s) for s in re.split(r'(\*\*|\*|\?)',p)));m=yaml.safe_load(open('PORT-MANIFEST.yaml',encoding='utf-8'));q=sys.argv[1];r=[x for x in m['rows'] if g(x['path']).fullmatch(q)];o=[x for x in m['default_ok'] if g(x['path']).fullmatch(q)];print(q,'->',(r[0]['path']+'  '+r[0]['disposition']) if r else ('default_ok '+o[0]['path']+'  '+m['default']) if o else 'FALLS THROUGH - undecided (J16)')" drydocs/cli.py

   # 2. REGISTERED CLI VERBS — the T22 deferrals are about verbs; this is the live set.
   poetry run python -c "from drydocs.cli import app;print(*sorted(i.name or i.callback.__name__.replace('_','-') for i in app.registered_commands),sep='\n')"

   # 3. THE CANONICAL LOAD SEQUENCE and its operator profiles (step 90 / T19). Absent
   #    company-side until T19 rules, in which case this raises ImportError — which is
   #    itself the answer.
   poetry run python -c "from drydocs.cli import CANONICAL_LOAD_SEQUENCE as s;print(*[f'{x.mode:9} {sorted(x.profiles)}  {x.command}' for x in s],sep='\n')"

   # 4. THE DATABASE TOPOLOGY (step 83) — config, not prose. Compare against a live
   #    SHOW DATABASES before any drop.
   poetry run python -c "import yaml;d=yaml.safe_load(open('config/dev-environment.yaml',encoding='utf-8'))['neo4j']['databases'];print(*[k+': '+v for k,v in d.items()],sep='\n')"
   ```

   All four were run in both PowerShell 5.1 and bash before being written here, because
   a one-liner that does not work is worse than none — the reader stops trusting the
   idiom rather than the line. Two things they deliberately do NOT cover: commit SHAs
   (three cited here legitimately resolve in another repo — two company-side, one the
   `depgraph` sibling) and the acceptance test counts, which are measurements and
   already carry their own "trust the live test files over this note" rule.

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
   `web/src/generated/gates.json` + `enforcement-matrix.json` + `load-map.json`,
   `docs/plan/load-map.html` and `docs/plan/ideas.html` (all ride the
   default-paths board render — J17/J20/N4/N5, ideas since 2026-08-05 —
   so one `render_board.py` run refreshes all six; COMPANY-SIDE
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
   - RATIFICATION-NOT-OWED PRECEDENT (C17, PORT-REPORT-40c35724): when the producer
     gate entry arrives by gate-log union-append (its manifest disposition) and the
     adoption flips NO config status — no vocab activation, no map status change —
     no separate Tier-A ratification entry is owed. The union-appended entry is the
     company record; the ported code and its tests are the enforcement.

6a. TIER-A RATIFICATION TEMPLATE (T11 discharged 2026-07-27; the paste-ready L7
   block that lived here was retired at the 2026-08-05 condensation — full text in
   this file's git history). The COMPANY gate-log now holds three live instances of
   the shape: L7 (ratified 2026-07-27), then `source-registry-v2` and `J23` (both
   at PORT-REPORT-57914bf4). For any future Tier-A adoption, copy the newest
   instance in YOUR gate-log and fill it. The required fields are fixed: Tier line
   (why Tier A applies — "a PORT-REPORT is evidence, not a gate ledger"), Subject
   (the exact statuses flipped), Producer gate reference (log date, counts, SME,
   spec path, producer commit), Same-SME condition, Checks performed COMPANY-SIDE
   (suite numbers, J7 guards, by-id resolution — REAL results, never invented),
   Graph writes: NONE (T9), Sign-off. Facts of the producer gate are pre-knowable;
   the check results and sign-off are yours alone. A ratification records no new
   decisions — changing a producer ruling is a Tier-B gate session, not an edit.

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
   SHA-STAMPED CITATIONS (J35): every producer-tree citation in the report — a file
   read, a tracker row, a config value, a step's claim — QUOTES THE SHA it was read
   at (`read at cewilson/main @ <sha>`). A citation with no SHA is unreviewable; a
   citation at a stale SHA announces itself as one instead of reading like a current
   answer — the cached-`5f79d145` failure mode (see the fetch note at the top of
   this file) is the motivating incident. Then close per the MANDATORY CLOSING
   SEQUENCE in the header: the four required fields (range, port commit, backup
   tag, acceptance numbers) land in **Last completed port** before the port is
   considered closed.

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
- **`catalog-pat` ≠ `pat-catalog` — RESOLVED 2026-07-31 by the v2 rename** to
  `pat:product-catalog` + `pat:people-report` (matching NEITHER legacy string); both
  legacy ids sit in the D4 retired-id refusal list, making recurrence structurally
  impossible. Kept one entry because it is the reason D4 exists.
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
- **Ruff config splits in two, and only one half is the contract (PORT-REPORT
  drydocs-port-20260801).** `ruff = "0.5.7"` + `[tool.ruff]` + `[tool.ruff.lint]`
  `select`/`ignore` + all of `[tool.ruff.format]` are BYTE-IDENTICAL both sides — that is
  the format contract, and a divergence there makes the repos format differently forever.
  `per-file-ignores` and `extend-exclude` are per-repo and MUST NOT be assumed equal.
  Verified state: the 7 producer rows are all exercised company-side (none inert — proven
  by re-running with `per-file-ignores` overridden empty, not assumed), plus 5
  company-only rows. `extend-exclude` is identical because `.claude/**` is
  canonical-producer, so the "we don't author these" judgement transfers by construction.
  Quantitative divergence to expect: `drydocs/cli.py` surfaces 26 B008 producer-side vs
  ~38 company-side — the company loader superset, not a config difference.
- **The 5 company-only `per-file-ignores` are an unintended MODULE INVENTORY, and two of
  them name capability the producer does not have.** `drydocs/docmeta/connectors/base.py`
  and `drydocs/scrapers/registry.py` — `drydocs/docmeta/` and `drydocs/scrapers/` do not
  exist producer-side at all; `tests/unit/test_employee_roster.py` and a `test_snow_supp*`
  are likewise absent. (`drydocs/publishing/validator.py` exists both sides and diverges
  in content — sanctioned, `drydocs/**` is evaluate-on-collision.) See T21.
- **`PORT-MANIFEST.yaml` = canonical-producer, and the company-only rows now have
  a home a verbatim take cannot touch (J34, 2026-08-09).** The manifest declares an
  `overlay:` seam: side-local rows live in `PORT-MANIFEST.company.yaml` (company-tracked,
  never-port), and the J16 guard UNIONS overlay rows/default_ok with the manifest —
  overlay rows append AFTER producer rows, so producer dispositions keep precedence.
  ONE-TIME MIGRATION at the port that delivers J34: move your 89 company-only
  `default_ok` paths (PORT-REPORT-*.md, docs/build_*, docs/site/*, docs/prompts/*,
  settings.json, …) out of your manifest copy into `PORT-MANIFEST.company.yaml`.
  After that, take the producer manifest wholesale — the re-append-after-every-port
  ritual (and its failure mode, the PORT-REPORT-a14a8028 89-path drop) retires.
- **Enforcement-matrix SURFACES: `config/crosswalks/` lives under the COMPANY row id
  `crosswalks`** — producer's `orchestrator-crosswalks` was folded into it at
  PORT-REPORT-40c35724 (runtime consumer + drift test carried). Resolve future
  collisions into the company row; do not re-mint the producer id.
- **Company test/doc adaptations that track THEIR deferrals** (PORT-REPORT-40c35724):
  `AUTHORING.md` namespace table = 5 rows (no ControlMHostGroup — T15/P3) with the
  count floor tracking it; `test_code_snapshot_loader` all-files assertion is
  T18-conditioned (`== {}` + note) — reinstate producer's non-empty assertion when
  the fork gains tree mode; `test_loader_run_log.py` is absent company-side, so
  producer deltas to it are moot.
- **Backlog statuses are PER-SIDE REALITY** (ruled at PORT-REPORT-40c35724): items
  union in by id, but `done` never crosses unmodified — U9/C21 landed `todo`
  company-side with reconciliation notes because their deliverables are T18/T22
  deferred. Never "sync" statuses in either direction.
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

> **IDS RENAMED 2026-08-09 — `R<n>` → `RELAY-<n>`, and the reason is a real
> misfire, not tidiness.** Relay ids collided head-on with Epic R backlog ids:
> `R1`–`R5` exist in BOTH namespaces and are meaningful in both. Asked to
> confirm relay R3(b), the company session searched for the literal string
> "R3(b)" — which does not appear, because the sub-clauses are `(a)`/`(b)`/`(c)`
> bullets under the relay heading — then anchored on backlog `R3` (the
> `:AgentRun` telemetry item) and answered a question nobody asked. The same
> collision bit twice in one investigation: it also read relay `R1` as the
> ADR 0007 R1-gate. Old ids are kept in the headings so a reader who remembers
> `R3` still lands on `RELAY-3`. Cite sub-clauses as `RELAY-3(b)`.

STANDING RELAYS (J38 — read this section at EVERY port; it is the channel the
producer's "tell the next company session" notes travel by, replacing the idea
inbox, which your repo never reads. Rules: every relay is RE-VERIFIED at the
roll that carries it — nothing is relayed from memory, a stale relay is worse
than none; a discharged relay is STRUCK with a dated reason, never silently
deleted; action a relay in the port that carries it or record why not in the
PORT-REPORT):

- **RELAY-1 (was R1) — AIS acronym expansion: transplant the VALUE across files** (standing
  since 2026-07-21; re-verified at the 2026-08-09 roll). Producer's
  authoritative home is `config/taxonomy/software-registry.yaml#acronyms`
  (`AIS: "Application Integration Streaming"`); YOUR provisional gloss sits in
  a different file (your source-registry entry for the internal AIS docs
  portal), with your own manifest row expecting the producer expansion. Carry
  the VALUE into your file — never a same-file overwrite, the files do not
  correspond. Rider from the same note: your 06-29 gate (the Ais* class
  removal) has no company gate-log entry — an audit gap on your side; the
  producer offered a backfill.
- **RELAY-2 (was R2) — run-log adoption asks** (standing since 2026-07-22; re-verified — the
  run-log family in `drydocs_core/run_log.py` + BaseLoader wiring is long
  ported). Two asks remain YOURS because they sit in your adapter code: (a)
  attach the WARN-stream tee in the XML EXTRACTOR stage — the
  `description_tokens` WARN flood happens PRE-loader, in the adapter, so the
  loader-stage tee never catches it; (b) once the stream lands in a file,
  consider raising the console handler to WARNING-summary-only — the file is
  the review surface, the console shows counts.
- **RELAY-3 (was R3) — 2026-07-21 port-report heads-ups, re-verified 2026-08-09:**
  (a) `test_schema_graph.py` drift-guard sequencing — re-add that test ONLY
  after your own doc-vocab gate; the trap is written in the reconcile-port
  skill's ledger (SKILL.md, "Sequencing trap"). Status unknown company-side —
  confirm or strike in your next PORT-REPORT.
  (b) ~~confirm docs/restructure/internal-backlog.yaml (plain text on purpose —
  it should not exist anywhere anymore) was DELETED after the DD-series merge~~
  — **STRUCK 2026-08-09: DISCHARGED.** Venue named per J18: run COMPANY-SIDE by
  the SME, `git ls-files docs/restructure/internal-backlog.yaml` returning empty
  on BOTH `main` and the port branch `drydocs-port-20260809`. Checking both is
  stronger than the relay asked for — it proves the deletion held AND that the
  `5417ef10..0d3761a9` port did not reintroduce the file. `388a30d` had proved
  the DD-series merge happened; this is the deletion half, unproven since
  2026-07-21 and asked at three rolls. Producer-side the file is likewise absent
  (untracked, no such path).
  (c) ~~remote-URL/fetch defect (stale pre-rename `cewilson` remote; fetch
  404s)~~ — **STRUCK 2026-08-09: resolved 2026-08-06** (SME confirmed fetch
  works; the fetch note at the top of this file carries the standing lesson).
- ~~**RELAY-4 (was R4) — the J34 overlay migration (one-time):** move your company-only
  `default_ok` paths into `PORT-MANIFEST.company.yaml`.~~ — **STRUCK 2026-08-09:
  DISCHARGED at PORT-REPORT-0d3761a9.** Done atomically, which is what made it
  work: the producer manifest and the overlay guards were taken in the SAME
  commit as the new `PORT-MANIFEST.company.yaml`, so the reader and the file it
  reads landed together. 9 company-only rows lifted (`.vscode/**`,
  `docs/build_*.py`, `docs/drydocs-design-document.*`, `docs/prompts/**`,
  `docs/site/**`, and four report/log artifacts). The 21 reconcile guards pass
  with the overlay covering them. A verbatim manifest take can no longer drop a
  company-only disposition — the 2026-08-06 clobber (Idea-79) is structurally
  fixed, not procedurally avoided.
- **RELAY-5 (was R5) — DPL + Snowflake registry entries: the producer is canonical, and you
  were mid-flight on the same change** (new 2026-08-09, gate
  `software-version-context` / C25). The SME began this expansion COMPANY-SIDE
  on 2026-08-07 and stopped deliberately so the two copies would match, so this
  is a producer-first divergence with a waiting consumer rather than a
  collision. Producer now carries, in `config/taxonomy/software-registry.yaml`:
  the `dpl` product row (`vendor: in-house`, `type: internal`, `role: tool`),
  the `snowflake` product row (`role: data-platform` — a TARGET DB platform,
  never an ETL product), the new `in-house` vendor with **no** `publisher_url`,
  and `DPL: "Data Pipeline Library"` in `acronyms:`.
  THREE RIDERS, each of which has already cost something if skipped:
  (a) Take the VALUE across files if your copy diverges, exactly as RELAY-1 requires
  — that lesson was learned on an acronym that lives in a different file on
  each side, and this change touches the same `acronyms:` block.
  (b) `versions: []` on `dpl` is DELIBERATE. The container base image is
  `datapipeline-apache-spark-3.5.1` tagged with the DPL image version, so
  3.5.1 is the EMBEDDED SPARK release and DPL's own version is the tag —
  writing 3.5.1 there records a dependency's version as the product's.
  (c) **THIS IS A RECONCILE, NOT A CLEAN ADD — corrected 2026-08-09 pm on the
  SME's FYI.** You already pushed a software-registry change with the INTERNAL
  URL on 2026-08-07, then stopped so the two sides would match. So company state
  exists and must not be overwritten: **reconcile ids and keep YOUR internal
  URL.** The two sides are correctly asymmetric here, and neither is wrong —
  the producer's `in-house` vendor OMITS `publisher_url` because a company URL
  in an Internal-Public file would cross the publish boundary; your tree is not
  published, so the real internal URL belongs in yours.
  `tests/unit/test_software_registry.py` was narrowed to require
  `publisher_url` of THIRD-PARTY vendors only, via an explicit allow-list, plus
  a second guard that a product of an exempt vendor must be `type: internal`.
  Take both guards with the rows — the allow-list without them re-opens the
  hole it closes.
  **A DEFECT IN THAT GUARD WAS FOUND AND FIXED BEFORE IT REACHED YOU, and it is
  worth knowing because it is the Idea-100 class:** the first draft asserted the
  exempt vendor had NO `publisher_url` at all, which would have failed YOUR
  suite for doing the correct thing. The exemption now means "not required",
  never "forbidden" — a real URL is accepted, a non-URL placeholder is still
  rejected. A producer-only precondition written as a universal invariant is
  exactly what breaks a consumer, and only the SME's mention of the internal
  URL caught it.
  Also reconcile the IDS rather than assuming them: the producer uses vendor
  `in-house` and products `dpl` / `snowflake`. If your 08-07 push chose
  different ids, one side renames — say which in your PORT-REPORT so the
  registry does not fork on identity.
  WHY THE ROW EXISTS AT ALL, so it is not read as cosmetic: DPL was already an
  ETLProcess `engine` value while Ab Initio carried BOTH an engine value and a
  `products:` row, and that asymmetry is what the 2026-07-27 G26 guard catch
  cited when it removed the `abinitio-dtlaunch-wrapper` pattern row —
  `dtlaunch.sh` is the DPL spine and `coverage_policy` forbids a pattern row
  without a real product id. This row is what lets a correct DPL pattern row
  exist.

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
| T11 | L7 ratification entry in company gate-log (Tier A record) | **RATIFIED 2026-07-27** (company gate-log; §6a is the standing template) |
| T12 | Company platforms gate: AIS position vs producer C12 | **RULED — SUPERSEDE, 2026-07-21** (company gate-log): the AIS layer is superseded by the software-registry model; excision applied, Tier B holds discharged 2026-07-27, session packs retired |
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | pending (producer belief, as of 2026-08-01) |
| T14 | rua collector convergence: company's own -n implementation vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible. Step 49e's G45 listing fallback is the same family — reconcile together | pending (producer belief, as of 2026-08-01) |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways; primary on-main checkout, never a worktree) → `drydocs load-code-snapshot` into your graph; second `:Project` root is INTENDED (gate §B3(a)); rides with the Tier A ratification entry (guardrail 6) | pending (producer belief, as of 2026-08-01) |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 staging stand-in as the feed (G40 parse stays as cross-check); premise correction folded into G22 prep. NOTE step 49g: if the XML export becomes a standing feed, this retirement gains a SECOND path — the unruled precedence question decides, not the port | pending (producer belief, as of 2026-08-01) |
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | pending (producer belief, as of 2026-08-01) |
| T18 | Depgraph fork capability catch-up (owed action 48e, PORT-REPORT-94132c80): your separately-owned depgraph fork lacks the U6 multi-root resolver (and `--tree`), and the producer remote is unreachable from it, so the port could not remediate. Until it catches up, `config/dev-environment.yaml` keeps `depgraph.capability_assert: false` (test skips, owed action recorded). When it gains the capabilities: flip the flag true and your `snapshot.ps1` refusal guard goes live | pending (producer belief, as of 2026-08-01) |
| T19 | N3–N6 LOAD-MAP adoption gate — **narrowed 2026-08-01**: registry v2 is ADOPTED (N9 full-adopt at PORT-REPORT-57914bf4), so this row now covers ONLY the N3 class-declaration derivation, the N4/N5 renders and N6. The id-collision blocker is resolved by the v2 rename (`pat:product-catalog` / `pat:people-report`); what remains is the sourceless company-only loaders. Company `cli.py` still has no `COMMAND_LOADERS`/`CANONICAL_LOAD_SEQUENCE` and the load-map pair stays out of the company board render until this rules | pending (producer belief, as of 2026-08-01) |

| T20 | **Catalog-loader review (8 findings on the company's `pat_*`/`product_lines`/`products`/`snow_support_crosswalk` cypher) — DISCHARGED at PORT-REPORT-40c35724** (2026-08-03): item 1, the `products.cypher` orphan fix, is APPLIED company-side; items 2–8 live in the company's own backlog/inbox; count-orphans-before-applying rides T23. The full 8-finding text was retired from this row at the 2026-08-05 condensation — it lives in this file's git history and PORT-REPORT-40c35724. Producer-side the same shape closed as C22 (step 70) + C24 (step 94). | **DISCHARGED 2026-08-03** (status cell corrected 2026-08-04 — producer-side staleness, the T11 class) |
| T22 | **`_client(database)` follow-up — company backlog row DD6** (created 2026-08-03, the port's own finding): company `cli.py` `_client()` takes no `database` param, which (a) is already a LATENT crash in `patch_window_cmd` (calls `_client(database=...)` today), and (b) blocked the two new verbs — `docs-verify` (Q7) and `bootstrap-schema-graph` (targets `ddschema`). DD6 = add the param, wire both DEFERRED verbs, add the `ddschema` provisioning DDL (the G51 twin). Modules are already ported; only the thin CLI wrappers wait | pending (producer belief, as of 2026-08-03; company row DD6) |
| T23 | **S3/C17 GRAPH writes on the company graph** — config/code landed at PORT-REPORT-40c35724, loads did NOT (guardrail 6: always yours). S3 re-key: **DROP `port_unique` FIRST**, then create `port_app_key` — a same-name re-declare succeeds and does nothing (verified live producer-side); all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance silently doubles canonical nodes. C17: count existing orphans BEFORE the every-run `orphan` flag goes live (report's own note). **RIDER 2026-08-05, from a company-side T23 lookup the producer was shown:** that session first read T23 broadly (as C23 `IN_DIMENSION` bootstrap + G51 `ddschema` populate + all S3/C17 re-keys + the folder-attribution migration) from downstream references, then corrected itself against this row and converged on it — so the row is right as written, and G51 `ddschema` populate is **T22/DD6 territory, not T23**. **DIRECT EVIDENCE 2026-08-04 — this row's own prediction FIRED, so it is no longer only a producer belief.** The company ran `drydocs load seal_applications` against a graph that took the S3 CODE but never the S3 re-key and got `Neo.ClientError.Schema.ConstraintValidationFailed: Node(97) already exists with label 'BusinessApplication'`. Mechanism confirmed against producer source: pre-S3 nodes carry `seal_id` and NO `app_id`; `MERGE (a:BusinessApplication {app_id: row.app_id})` cannot match them because a uniqueness constraint IGNORES NULLS, so it mints a second node, and the next line `SET a.seal_id = row.app_id` then collides with the original's `seal_id` (both properties are separately unique-constrained, `constraints.cypher:43-44`). That is this row's "all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance silently doubles canonical nodes", happening. **Remedy relayed:** backfill `app_id = seal_id` on the pre-cutover nodes BEFORE re-running, after checking whether the partial run already doubled any — batches commit per flush, so a mid-load crash leaves a partially-doubled graph, not a clean rollback. **Producer payload now exists (S10, built 2026-08-05, lands with this port):** all four `:BusinessApplication` MERGE loaders refuse up front when the target database holds a node with a null `app_id`, before any write and before the :JobRun. The refusal does NOT substitute for this row — it prevents the crash, it does not repair live state. Two things to keep straight, though. (1) **A CLOSED LOADER IS NOT A PERFORMED MIGRATION.** The company closed the folder-attribution *loader* (`folder_attribution.py` / `.cypher`) on 2026-08-04; the T23 leg is the SF1/F1 edge migration on LIVE state, which is exactly what step 55's `F1/G4-RIDER` note says wipe-and-rebuild does not cover. Do not let "the folder-attribution slice closed" on a board read as the migration being done. (2) That session could not fetch the producer and answered from a cached `cewilson/main @ 5f79d145` — see the fetch-access warning at the top of this file; a T-row read under those conditions is dated by construction. **RIDER 2026-08-06 (PORT-REPORT-a14a8028):** the company extended `PreCutoverApplicationGuard` (S10) to their own 5th `:BusinessApplication` MERGE site, `PatAppLinksLoader` — crash-prevention now covers all five company sites. Prevention only: the S3 graph re-key and C17 orphan-count legs remain owed on the live company graph | pending (producer belief, as of 2026-08-06 — the S3 re-key and C17 orphan-count legs were still open company-side at PORT-REPORT-a14a8028; the SF1 folder-attribution *loader* is closed, its edge migration is not; S10 guard now covers all 5 company MERGE sites) |
| T21 | **What are `drydocs/docmeta/connectors/` and `drydocs/scrapers/`?** — ANSWERED 2026-08-02: a company acquisition framework whose agnostic members (web/filedrop connectors + the base protocol) seeded producer Q6; the rest (confluence connector, `scrapers/`) is purely internal. **DISCHARGED 2026-08-04:** Q6 landed `drydocs_docmeta/` producer-AUTHORED against the described shape, never a copy (step 75). Full analysis retired to this file's git history at the 2026-08-05 condensation. | ANSWERED 2026-08-02; back-flow DISCHARGED 2026-08-04 (Q6) |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section (guardrail 1 has the `git show` path; they are NOT restated here). T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10/T13: until a real export parses with zero mismatches, treat the
  field names as ASSUMED.

STEP LEDGER — delta since `5417ef10` (steps 43–105 collapsed above). Each
sub-stream carries its producer-side verification status in [BRACKETS]; spend
review on [UNRULED]. Grooms, claims, board/design renders and depgraph
snapshots in the range are ritual — per-entry backlog union, derived
regeneration, never-port outputs — and get no step.

106. G22 AFTERMATH TRIO — G55 vocabulary consequences + G23 curated load + G58
    archival report [TEST-PINNED] (`2435a7d`, `ba7fbaf`, `461ea8e`). G55 applies
    the signed gate's flips (guardrail 7: GATE-AUTHORIZED — do not run the
    no-downgrade guards across it); G23 is the rua curated load per the signed
    shapes (loads are always yours — T9); G58 the dead-script archival report
    with the gate's safety bar. G23 depends on G55 — the ordering constraint is
    recorded in the backlog (`6a65d4f`), verified in code, not prose.

107. OLDEST-NON-HITL SWEEP — six small items [like-for-like] (O29 `afd6594`
    trust-tier legend; O30 `74b0f1a` App.css retired; O32 `604c0b6` light-mode
    cascade fix; S7 `31bd162` folder-vs-module naming rule in MODULE_MAP.md;
    S6 `94924a5` JSON Schemas for the six config families; A4 `9f1bb62` dcat
    per-standard README). web/** and MODULE_MAP.md are canonical-producer. S6's
    schemas validate YOUR config copies at editor time — a squiggle on your
    adapted values is the schema working; widen a schema only where your grammar
    legitimately differs, and note it in the PORT-REPORT.

108. PORT MACHINERY HOUSEKEEPING at the 5417ef10 review (`7934c41`): Relay #2
    applied (config/audit-fields.yaml + test_module_boundary.py per-entry/union
    rows). FIVE company packs staged (`2f3c385`, clean-add rows above the
    never-port glob — REMOVE those five rows after this port merges) + FOUR
    post-G22 data-profile gate prompts drafted (`b001eb8`) [UNRULED]. Six
    DELIVERED company prompts retired to local archive (`6b3a957`) — the
    deletions are covered by the `docs/gate-*-company-prompt.md` never-port row,
    so your live copies are untouched by design; verify they survived the apply.

109. K16 PRODUCER HALF — the FID census METHOD (`232e88f`) + `drydocs
    fid-census` (`20f6431`) [TEST-PINNED]. Counts-only by return type; the
    COUNTS are Internal and cannot be produced producer-side — the item sits
    `blocked` on your directory extract, and the census prompt is
    `docs/k16-fid-census-company-prompt.md` (in-tree, not a gate pack).
    cli.py is evaluate: add the verb, keep yours.

110. Q16(a) — `drydocs docs-coverage` + THE /software LEDGER PAGE (`b297268`,
    `0ddf880`, `9b4cf59`, `71276d5`). Software→documentation coverage report;
    the vendor→product→corpus→graph declared-vs-loaded console surface;
    generated software-registry.json gains the doc-governance fields. The page
    reads YOUR registry and corpora at render — regenerate under guardrail 5,
    never take producer generated JSON. Overview pick-list persona-filter fix
    rides along.

111. SMALL GUARDS [TEST-PINNED, like-for-like] — G59 apply-supplements
    completeness (`1490d02`: a supplement on disk can no longer be silently
    skipped; the applied set is derived from the directory); J36 ryuk workaround
    automatic (`9bf7ebb` — integration suite needs no manual prep); skip-guard
    prose fix (`2c26e2f`); runbook-currency historical exemption (`cbb8b3d`).

112. ROADMAP — THE THIRD PLANNING SURFACE (`3c60e2e`). drydocs/plan_roadmap.py
    + scripts/render_roadmap.py join the default board render; authored
    judgments live in docs/restructure/roadmap.yaml (module-coverage +
    idea-citation guards in test_plan_roadmap.py). Manifest rows landed with
    J34: the .html is a DERIVED canonical-company render; the .yaml is evaluate
    — YOUR stage/remaining judgments describe YOUR tree, take structure only.
    board.html links to the new page.

113. BACKLOG RE-SHAPES [per-entry union as usual] — Epic Z groomed (`d95a64a`:
    six server-location/geography items; the Z2 gate carries the standing
    caution that the infrastructure data-center field is NOT the Control-M
    same-named field) and G57 WITHDRAWN-CLOSED (`913861a`, user ruling): the
    rua_*→bkup_* family rename is OFF THE BOOKS — the G22-session file rename
    was a comparison maneuver, not a directive, and the rua_* names STAND. If
    your rua-load-shapes ratification session queued a rename expectation,
    strike it.

114. REVIEWS + PROSE [default_ok / internal] — persona review Run 2 (three
    `docs/reviews/persona-*-2026-08.md` files + checkpoint + Idea-91..95; the
    tech-writer mandate now cites the US-English guide, `afc79c4`);
    business-layer location experiment (`f156cc7`,
    internal/context-graph-analysis/**); L24 exec overview rev 8 (`b2287fa`);
    MWAA implementation-docs locator (`9674403` — value in internal/, pointers
    everywhere else); G32 close checklist (`250e355`). docs/reviews/** is
    default_ok — point-in-time records of the side that ran them.

115. THE PORT-MACHINERY TRIO — J34 + J35 + J38, one branch, three commits
    [STRUCTURE for your manifest copy]. J34: the overlay seam — your ONE-TIME
    migration of the 89 company-only default_ok paths into
    PORT-MANIFEST.company.yaml happens at THIS port (standing-divergence bullet
    has the procedure). J35: this roll, the mandatory closing sequence (header)
    and SHA-stamped citations (guardrail 8). J38: the RELAY section above the
    tracker — read it at every port from now on.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `0c4105b` (step 54): 126 passed / 0 skipped WITH the
  production CSV present (+2 over step 52 from the S2 module-boundary additions;
  sample-backed tests skip without the CSV — at step 48 the CSV-absent figure was
  114 / 3). Company baseline is ABOVE the
  producer floor — compare against your own PORT-REPORT-e60822fc numbers, not these.
- Full `pytest tests/unit/` — ZERO failures is the contract; skips are
  environment/fixture-absence by design (production CSVs, XML fixtures, fastapi
  optional dep, essential-graphrag PDF, J7 guards without RECONCILE_BEFORE_DIR,
  capability_assert=false skips per T18). A retired-id refusal from
  `SourceRegistry.from_yaml` is the D4 guard WORKING, not a port failure — rebind the
  loader in `loader-source-overlay.yaml`, never by re-adding the retired id.
  Producer chain reference (like-for-like venue: CSV-PRESENT desktop, no
  RECONCILE_BEFORE_DIR) — at step 83, the ddlineage retirement:
  1539
  passed / 5 skipped with the production CSV PRESENT and no
  RECONCILE_BEFORE_DIR (4 J7 guards + the graphrag PDF) — the like-for-like
  chain: step 58 1356/5 → step 61 1384/5 (+28 K9 guards) → step 63 1399/5
  (+15 K8) → step 65 1403/5 (+4 K10) → step 66 1410/5 (+7 K11; step 67 no
  delta) → step 68 1413/5 (+3 U12; step 69 no delta) → step 70 1420/5
  (+7 C22) → step 71 1427/5 (+7 J18/J26/J27/J28) → step 72 1430/5 (+3 M4
  property-term guards) → step 73 1449/5 (+19 Q13) → step 74 1450/5
  (+1 J29) → steps 75–78 1501/5 (measured at `0c77426`: Q6/Q12 docmeta
  suites + SDLC outline pins) → step 80 1505/5 (+4 L20) → step 81 1515/5
  (+10 S5 fragments) → step 83 1539/5. **Steps 84–90 are now ledgered
  (2026-08-05) — that instruction is discharged; what those steps still
  LACK is a like-for-like figure, for a venue reason worth stating
  rather than papering over (J18).** The only measurement at step 90 was
  taken on the LAPTOP: **1551 passed / 7 skipped**, with the production
  CSV **ABSENT** and no RECONCILE_BEFORE_DIR. The 1539/5 above was
  CSV-**PRESENT**, so the two differ in two environment dimensions at
  once and `1539 -> 1551` is NOT a `+12` delta: three CSV-backed tests
  are skipping here that were passing there, and the graphrag PDF is
  present here where it was absent there. Reconciling those by
  arithmetic would give ~1554/4 — which is a calculation, not a run, and
  the chain is a chain of RUNS. Extend it from a CSV-present desktop
  run; do not adopt the laptop number as the reference. Your own
  baseline is above the producer floor either way — compare against your
  last PORT-REPORT, never against these. **The chain RESUMES like-for-like
  on the desktop (2026-08-05):** step 93 (S10) **1575/5** (quoted in
  `04b267a`), and the current head after step 96 (K18) measured
  **1597 passed / 5 skipped** — that is the producer reference figure;
  steps 84–90 remain the venue-noted gap in between. The
  step-60 figure (1354 / 7) was CSV-ABSENT without RECONCILE_BEFORE_DIR and is
  not comparable line-for-line; `aa0a0eb`'s commit message quotes 1358 / 3,
  which is the step-59 run with RECONCILE_BEFORE_DIR set. Earlier producer
  heads are in git history and the archive — do not re-derive them here.
  Company reference (PORT-REPORT-40c35724): full `1652 / 28 / 0`, Track-1
  `123 / 3 / 0`, `EXPECTED_CONSTRAINTS` 55 company-based.
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
