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

**OPENING SEQUENCE (J41, 2026-08-09 — MANDATORY, producer-side, before any company
session starts).** J35 above is the CLOSING half. For nine months there was no opening
half, so every port began on a base nobody had certified. That cost a full cycle on
2026-08-09: a company session was handed a thorough 8-phase plan and could not run it
solo, and two real failures rode in the offered range invisibly (a `FORCE_COLOR`
colour-vs-behaviour test failure, and a duplicate `Idea-101` from a two-session id
collision that would have failed `test_idea_ids_are_unique` on apply). Run
`poetry run python scripts/port_preflight.py --base <last-ported-head> --tag`; it
performs all six and refuses to certify on any failure:
1. **Suite green** on the exact commit offered, **venue-stamped (J18)**.
2. **Ledger rolled** through that commit, coverage verified COMMIT-BY-COMMIT.
3. **Every producer action triggered by company state is landed** — anything the
   company would otherwise have to do to a `canonical-producer` file. This is the one
   that failed: the plan asked the company to edit `PORT-MANIFEST.yaml`, which its own
   apply phase takes wholesale, so the edit would have been reverted in the same session.
4. **Renders current** (re-render, then `git diff --quiet`).
5. **Relay basis tags** present on every live relay (see the RELAY section).
6. **Base tagged `port-base-YYYYMMDD` and pushed.**

**THE BASE IS A TAG, NOT `HEAD` (J41).** The company still fetches fresh — never a
cached ref, the 2026-08-05 lesson stands — but ports `<last-ported>..port-base-YYYYMMDD`,
not `..HEAD`. Producer `HEAD` moves while a session reads it: on 2026-08-09 the base
moved 42 → 45 commits mid-hold and every prompt had to carry an awkward "verify, the
producer is still committing". A tag is immutable and certified; if HEAD has moved past
it, those commits ride the NEXT port, which is normal rather than a discrepancy.

**ONE OWNER PER PHASE (J41).** A port plan names exactly ONE owner per phase and NEVER
crosses the repo boundary. If a phase's owner differs from the phase before it, the plan
ENDS there and a new plan begins after the handoff. A plan that cannot name one owner per
phase has a hidden handoff in it — and no amount of instruction detail rescues a phase
its assignee cannot durably perform.

**LENGTH DISCIPLINE (v3 rule, and the reason for it).** This file regrew to 567 lines by
step 51 because each roll added prose that the next roll never removed. A prompt nobody
finishes reading is not a control document. So:
- a step-ledger sub-stream gets **≤ 8 lines**: what changed, its verification tag, and
  the ONE caution that would cost you a rework. Everything else belongs in the commit
  message, which is one `git show` away;
- a tracker row gets **one sentence plus a pointer**, never a paragraph;
- a roll REPLACES the previous roll note; it does not stack another one;
- if a section can only be understood by reading it twice, cut it rather than expand it.

**Roll state (2026-08-10, the post-`ae21ee4` roll).** The ledger is rolled through
the certified tag **`port-base-20260810b` (`ae21ee4`)** — the FIRST TAG-BASED PORT,
and the opening sequence worked end-to-end: range verified at fetch time against
the certified 9/15, zero J16 fall-through, the +39 suite delta = exactly the two
new guard files. Steps **122-123 are APPLIED** (verified commit-by-commit: 9
commits, 4 cited in steps 122/123, 5 ritual). Live ledger restarts at **124+**,
delta since `ae21ee4`.

> **`ae21ee4` IS MERGED (SME, 2026-08-10) — the port branch is REMOVED.** Port commit
> `12420373` (+ report `297d25bc`) applied onto `main @ 308dda92`, `--no-ff` merged onto
> company `main`, branch `drydocs-port-20260810` deleted at close-out. The port loop is
> FULLY CAUGHT UP on both sides. `6f03264`'s port (`feeb0706`)
> DID land: merged as `308dda92` and pushed BEFORE this port began, so Phase 0 was
> satisfied on arrival.
> **J41 landed `done` company-side** — deliberate call, correctly distinguished from
> the U18/U19 `todo` shape: a script that exists-but-is-not-invoked is not an
> unadopted enabling pin. Their `test_module_boundary.py` now carries BOTH component
> groups (producer `port` + company-only `docmeta-acquire`) — the rework trap
> handled as step 122 warned.
> **Company fence pre-check: clean (11/11).** Their never-port `port-prompt.md` does
> NOT carry the producer-lineage fence defect — independently maintained, verified
> before their full suite ran.

**Last completed port — the four required fields (J35).**
- **Range:** `6f03264..ae21ee4` (= tag `port-base-20260810b`) — **9 commits / 15
  changed paths**, ledger steps 122-123; range verified AT FETCH TIME against the
  certified expectation, not only at report time.
- **Port commit:** `12420373` (branch `drydocs-port-20260810`); report as `297d25bc`.
- **Backup tag:** `pre-cewilson-port-20260810` @ `308dda92`;
  `rev-list --count <tag>..HEAD` = 2 (payload + report — the report body's "1" was
  written pre-report-commit, the send-back's "2" is final).
- **Acceptance:** full suite **2045 passed / 32 skipped / 1 failed** — the single
  failure is the pre-existing WP1.4/T19 infra-block, proven not-port-introduced by
  the strongest argument yet: byte-identical inputs at pre-port HEAD fail identically.
  **2006 + 39 = 2045, and the two new guard files ARE 39 tests** (28 port_preflight
  + 11 markdown_fences; producer-verified). Track-1 **123/3/0**; J7 guards **21**;
  CI guards green; 0 J16 fall-through.

**Steps 122-123, one line each.** 122 J41 opening-sequence machinery (module +
guards + `port` group + SKILL.md certified-tag check; company runs nothing). 123 the
markdown-fence fix + portable guard (company ran it against their own docs: clean).

(Steps 116-121 collapsed at the prior roll — one-liners in PORT-REPORT-6f03264 and
this file's git history. The FORCE_COLOR / Idea-101 findings that motivated J41 are
recorded there too.)

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

````text
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
- **THE HELD K7–K15 FOLDER-ATTRIBUTION UI IS A NAMED EXCEPTION TO `web/**` AND
  `config/**` BEING CANONICAL-PRODUCER — a wholesale directory take re-lands it EVERY
  port** (registered 2026-08-09, after the second catch). Company-side
  `web/src/routes/AppCodeCascadePane.tsx` is DELETED and `MappingsRoute.tsx` is held at
  its pre-K11 revision — the Tier-B `seal-app-ref-edge-reshape` hold, where
  `m3_belongs_to_application` stays `planned` and the folder-attribution loader is not
  built company-side. Both files are canonical-producer by manifest row, so
  `git checkout cewilson/main -- web/src` silently re-adopts held work: caught at
  PORT-REPORT-a14a8028 (quick-wins rider) and again at the port in flight 2026-08-09.
  The hold ends by GATE, never by port (guardrail 6 Tier B). Resolve as: drop
  `routes/AppCodeCascadePane.tsx`; keep the company `MappingsRoute.tsx`; take the
  `config/taxonomy/ui-components.yaml` rows EXCEPT `AppCodeCascadePane` (their
  `test_no_ledger_entry_points_at_a_missing_file` reds on it); company
  `test_ui_components.py` asserts producer's total MINUS ONE with bound UNCHANGED —
  the component is UNBOUND, so only the total moves (producer `(29, 68)` at this
  roll → company `(29, 67)`). Two facts checked here so they need not be re-derived:
  no port range has touched either file since a14a8028 (`git log <base>..HEAD --` on
  both is empty at `5417ef10`), and the pre-K11 `MappingsRoute` is already pure
  Tailwind token classes — O30's App.css cull does NOT strip the held version's
  styling. When the company gate rules, strike this bullet with its date.
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
- **The `JOBISN=1` FOLDER PSEUDO-JOB IS A DELIBERATE PRODUCER GAP, not a porting miss**
  (registered 2026-08-11 at G75). Your `drydocs_core/adapters/controlm_xml_adapter.py`
  builds a pseudo-job at `<folder_id>.1` so folder-level `PL-<folder>-OK` OUTCONDs
  attach to a real node instead of dangling. G75 back-flowed the adapter's two PURE
  mechanisms (`normalize_export_timestamp`, `condition_scope`/`condition_identity`) and
  deliberately left this one behind: it is a LOADER idiom and the producer has no
  XML-to-graph adapter to host it, so building it here would mean inventing the caller.
  TRIGGER that retires this entry: the first producer-side loader that models
  folder-level conditions. Until then the adapter itself stays company-only and is NOT
  a back-flow candidate — see the next bullet for why.
- **`controlm_xml_adapter.py` is company-canonical AND is not a producer target**
  (2026-08-11, from the 19-screenshot capture at
  `internal/controlm-config/reference/controlm-xml-processor-capture.md`). Three reasons,
  recorded so no future port "helpfully" back-flows it: it encodes the description-token
  model C30 RETIRED (`INBOUND_ROUTE`/`OUTBOUND_ROUTE`, `ENV` in its transfer-instance
  meaning, `PDN_SNOW_QUEUE`); it flattens the C30 scope ladder into one dict per job; and
  its `FOLDER_ORDER_METHOD` filter skips manual-order folders — right for a live-graph
  load mirroring the Oracle `USER_DAILY IS NOT NULL` filter, WRONG for a conformance
  pass, where hand-built and inactive folders are the entire drift population. The
  producer conformance path is `drydocs_lineage/extractors/controlm_xml.py` +
  `drydocs_remediation/xml_bridge.py` instead. Two loads with OPPOSITE correctness
  conditions must not share an adapter.
- **`drydocs_core/orchestration/controlm/resource_pool.py` exists BOTH SIDES and the
  split is the contract** (G76, 2026-08-11). Company-side the module compiles its
  vocabulary in — the match regexes and the app-code prefix are estate data. Producer
  ships the MECHANISM only: the grammar, `PoolClassification`, and an ORDERED
  `tuple[PoolRule, ...]` the caller supplies, defaulting to `()` so an un-configured
  deployment classifies everything `unknown`. Resolve a collision by keeping the
  producer module and moving your table into caller-supplied data; do NOT take the
  producer file and then re-inline your regexes, and do NOT push your table producer-side.
  The ordering is load-bearing — a broad rule placed before a narrow one silently steals
  its pools (`test_controlm_resource_pool.py` proves it both ways), so a table stored as
  a mapping keyed by category is a defect, not a refactor. `CATEGORY_LABEL` is the
  PROPOSED label vocabulary and is not ratified producer-side: nothing there writes a
  graph, and minting those labels is HITL-gate territory.
  **APPLIED AND CONFIRMED at PORT-REPORT-caa0406** — the company took the mechanism
  wholesale with `DEFAULT_RULES` empty and moved its estate vocabulary to a new
  `drydocs_core/orchestration/controlm/resource_pool_company.py` (caller-supplied
  ordered rules + app-code regex), re-pointing the adapter and its classifier test.
  Regexes were NOT re-inlined and ordering was preserved. That company module is
  **canonical-company and never flows back**; the producer file stays mechanism-only.
- **`description_tokens.py` IS UNION-MERGED, NOT WHOLESALE** (new 2026-08-11 at
  PORT-REPORT-caa0406). The two sides hold DIFFERENT MODELS in one module with **zero
  name overlap**, verified producer-side rather than asserted: producer exports
  `parse_description` / `required_tokens` / `validate` (the C30 conformance model,
  consumed only by its own test), while the company-canonical adapter imports
  `parse_tokens` / `classify_job_role` (the C30-retired live-load model). Neither name
  set touches the other, so both survive in one file and the manifest's
  `orchestration/**` canonical-producer row yields to the held adapter's dependency.
  Resolve future collisions the same way — union, never wholesale — until the
  back-flow below lands. **Producer back-flow candidate, and it is the real fix:**
  split the conformance model and the live-load parser into separate modules
  producer-side, which removes the union entirely. Recorded because a union that
  depends on two name sets never colliding is one careless rename from breaking.
- **`drydocs_remediation/detect.py` IS UNION, and the `Finding` shape is SHARED**
  (new 2026-08-11, same report). Producer contributes R30–R40 plus `xml_bridge`; the
  company contributes `detect_dpl_findings` (with `DPL-*` rule ids) and `dpl_review`.
  Both are kept. The shared `Finding` dataclass is what makes the union cheap and is
  the thing to protect: `tests/unit/test_no_shadow_definitions.py` forbids a second
  Finding class producer-side, and the same discipline is what keeps these two rule
  families reportable in one list. A company `DPL-*` id must never collide with a
  producer `R<n>` id — the two namespaces are deliberately disjoint.
- **`tests/unit/test_runbook_currency.py` IS DEFERRED COMPANY-SIDE, and the producer
  disagrees mildly** (2026-08-11). The company removed rather than adopted it, because
  all three of its failures are T19/T22 company deferrals — producer surfaces
  (`docs/plan/load-map.html`, `web/src/generated/load-map.json`) and CLI verbs
  (`sweep-removed`, `load-essential-graphrag`) absent company-side by design. The
  reasoning is sound and the call is the company's. **But the guard has the escape
  hatches for exactly this case** — `FOREIGN_PATHS` (a path in another repo) and
  `HISTORICAL_PATHS` (a statement about the past), both of which take a written
  reason — so adopting it with three exemption entries preserves the protection
  instead of dropping it. Worth doing because the guard is not theoretical: it caught
  a real producer defect inside this very range, when the step-134 ledger roll
  backticked three module paths in an abbreviated form that did not exist. Backticks
  are an existence claim on both sides.
- **THE TWO COMPANY-ONLY SUPPLEMENTS ARE NOT A PAIR, and treating them as one is how
  the wrong one gets dropped** (split 2026-08-11; the earlier framing, in G59's notes,
  lumped them as "two supplements the producer does not run"). Producer's chain is five
  — ontology / seal / catalog / registry / sosa — re-verified against the tree at this
  split, not taken from the note. The company's two are in OPPOSITE states:
  **`resource_pools_supplement` — LIVE and company-only.** It declares the
  `:ResourcePool` ontology, the `:CONSUMES_FROM_POOL` term and the
  `resource_pool_name` constraint, and it backs `controlm_quantitatives`, which is
  wired solely into the company's `ingest-controlm-xml`. It MUST be in your chain, or
  in your `CHAIN_EXCLUSIONS` with a written reason — G59's own warning is that adopting
  `apply-supplements` as the one chain without adding it drops the supplement silently
  and whatever MATCHes its terms goes quiet.
  **`platforms_supplement` — RETIRED, and a no-op.** T12 ruled SUPERSEDE (2026-07-21):
  the AIS layer is superseded by the software-registry model, role over class. Seeds are
  commented out and audit-kept, so the verb is a NO-OP on a fresh graph and is no longer
  a prerequisite for the Control-M app-code step. It belongs in `CHAIN_EXCLUSIONS` WITH
  ITS REASON, not in the chain — an excluded-with-reason retired supplement and a
  silently-absent live one look identical from the chain's point of view, which is
  precisely what G59's written-reason requirement exists to separate.
  **Why the producer has neither, and why that is correct rather than a gap:** the
  producer XML path (`controlm_xml.py` staging + `resolve-cmdline-staging`) writes ZERO
  graph by construction, so it can never need the pools supplement. Producer does carry
  the classifier half — `drydocs_core/orchestration/controlm/resource_pool.py` (G76),
  mechanism-only with an empty rule table — and stops there deliberately: the loader
  writes `:ResourcePool` / `:CONSUMES_FROM_POOL`, and minting those labels is HITL-gate
  territory, not a back-flow.
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

**EVERY LIVE RELAY DECLARES ITS BASIS (J41, 2026-08-09). Unlabelled means
unverified.** The tracker below has carried this caveat since T11 — "STATUS IS A
PRODUCER BELIEF, NOT COMPANY STATE ... every `pending` means *not known to be done*"
— and the RELAY section, added later as J38, never inherited it. RELAY-5 is what that
cost: it told the company "you already pushed a software-registry change with the
internal URL", and their `git log --all -S "in-house"` showed it was never there.
- `[VERIFIED-PRODUCER]` — a fact about the PRODUCER tree, checkable from here.
- `[SME-REPORTED]` — told to the producer by the SME; **unverifiable company-side**.
  Say what to do if it is NOT found; never phrase it as established company state.
- `[COMPANY-CONFIRMED]` — came back in a PORT-REPORT. The ONLY tag that may assert
  company state.
`scripts/port_preflight.py` fails the port if any live relay lacks one.

- **RELAY-1 (was R1) — AIS acronym expansion: transplant the VALUE across files**
  `[VERIFIED-PRODUCER]` (standing
  since 2026-07-21; re-verified at the 2026-08-09 roll). Producer's
  authoritative home is `config/taxonomy/software-registry.yaml#acronyms`
  (`AIS: "Application Integration Streaming"`); YOUR provisional gloss sits in
  a different file (your source-registry entry for the internal AIS docs
  portal), with your own manifest row expecting the producer expansion. Carry
  the VALUE into your file — never a same-file overwrite, the files do not
  correspond. Rider from the same note: your 06-29 gate (the Ais* class
  removal) has no company gate-log entry — an audit gap on your side; the
  producer offered a backfill.
- **RELAY-2 (was R2) — run-log adoption asks** `[VERIFIED-PRODUCER]`
  (standing since 2026-07-22; re-verified — the
  run-log family in `drydocs_core/run_log.py` + BaseLoader wiring is long
  ported). Two asks remain YOURS because they sit in your adapter code: (a)
  attach the WARN-stream tee in the XML EXTRACTOR stage — the
  `description_tokens` WARN flood happens PRE-loader, in the adapter, so the
  loader-stage tee never catches it; (b) once the stream lands in a file,
  consider raising the console handler to WARNING-summary-only — the file is
  the review surface, the console shows counts.
- **RELAY-3 (was R3) — 2026-07-21 port-report heads-ups** `[COMPANY-CONFIRMED]`
  **(re-verified 2026-08-09; (b) and (c) discharged on company-run evidence):**
  (a) `test_schema_graph.py` drift-guard sequencing — re-add that test ONLY
  after your own doc-vocab gate; the trap is written in the reconcile-port
  skill's ledger (SKILL.md, "Sequencing trap"). Status unknown company-side —
  confirm or strike in your next PORT-REPORT.
  (b) ~~confirm docs/restructure/internal-backlog.yaml (plain text on purpose —
  it should not exist anywhere anymore) was DELETED after the DD-series merge~~
  — **STRUCK 2026-08-09: DISCHARGED.** Venue per J18: company-side, run by the
  SME on BOTH `main` and the port branch `drydocs-port-20260809`;
  `git ls-files docs/restructure/internal-backlog.yaml` returns empty on each.
  Checking both is stronger than the relay asked — it proves the deletion held
  AND that the `5417ef10..0d3761a9` port did not reintroduce the file.
  `388a30d` had proved the DD-series merge happened; this is the deletion half,
  open since 2026-07-21 and carried at three rolls. Producer-side the file is
  likewise absent.
  EVIDENCE, quoted rather than summarised — `git ls-files "docs/restructure/*backlog.yaml*"`
  company-side returns exactly one line:

      docs/restructure/backlog.yaml

  A glob is what makes that conclusive: it surfaces whatever IS there, so an
  absent file is distinguishable from a mistyped one. The corrected exact-path
  lookup returned empty on both branches as well; the two agree.
  THE AUDIT TRAIL IS KEPT DELIBERATELY, because the correction is the useful
  part: this was struck, UN-struck, and struck again within one day. The first
  strike rested on a run whose path was misspelled (`intenral-backlog.yaml`,
  r/n transposed), which returns empty whether or not the file exists — so it
  was withdrawn. STANDING LESSON, and it generalises past this relay: an
  exact-path `git ls-files` fails silently, because a wrong path and an absent
  file produce the identical empty result. Answer any presence/absence relay
  with a GLOB and quote the OUTPUT, never the verdict. The same defect class in
  a different costume produced the `airflow-crosswalk` false ratification on the
  same day — a check whose failure mode looks exactly like success.
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
- **RELAY-5 (was R5) — DPL + Snowflake registry entries** `[SME-REPORTED]`
  **— AND THE "you were mid-flight on the same change" HALF WAS WRONG. CORRECTED
  2026-08-09 pm at PORT-REPORT-6f03264, by the company, on evidence.** This relay
  told you the reconcile half as established fact. It is not: `git log --all -S
  "in-house" -- config/taxonomy/software-registry.yaml` company-side returns ONLY the
  producer commit `aef10c54`, and `git grep in-house` in `config/` is empty. The SME
  did do that work internally on 2026-08-07, but it never reached a pushed company
  branch — so the producer asserted the state of a tree it cannot see. The company
  handled it exactly right: treated it as a stale producer belief, took the producer
  `software-registry.yaml` verbatim, and did NOT fabricate an internal URL. **So this
  is a CLEAN ADD unless and until a company internal-URL edit surfaces on an unmerged
  machine; reconcile it when that lands.** This correction is why the basis-tag rule
  above exists — the producer half of the relay below remains sound, the company half
  never had a basis.

  The PRODUCER-SIDE facts, which ARE checkable from here (new 2026-08-09, gate
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
  (c) **THE PUBLISH-BOUNDARY ASYMMETRY, which stands regardless of the correction
  above.** If a company internal-URL edit does surface, keep it —
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

- **RELAY-6 — THE COMPANY HOLDS A SIGNED SERVICENOW MODEL THE PRODUCER CANNOT SEE,
  AND GUARDRAIL 6 HAS NO SLOT FOR THAT DIRECTION** `[SME-REPORTED]` (new 2026-08-11,
  from screenshots of a company session; the producer-side half IS verified — see
  below). The company has SIGNED `snow-hpsm-queue-to-group` (2026-07-15) and PARTIALLY
  BUILT it — **corrected 2026-08-11: the loaders are marked DRAFT and the source entry stays
  `confirmed: false` pending the final loader build, so "built and signed" overstated the build
  half.** What exists:
  `snow_support_crosswalk.py` + `.cypher`, a `load-snow-support-crosswalk` CLI, the
  node classes `:ServiceNowGroup` and `:HpsmQueue`, and the shape
  `(:BusinessApplication {seal_id})-[:HAS_SUPPORT_QUEUE]->(:HpsmQueue)-[:RESOLVED_BY]->(:ServiceNowGroup)`,
  fed from a hand-verified Internal YAML crosswalk keyed on SEAL.
  **`[VERIFIED-PRODUCER]`: none of it exists producer-side and none of it ever has** —
  absent from the working tree and from `git log --all` on every one of those paths.
  So this is company-ORIGINATED work, not a producer artifact awaiting a port.
  **WHY IT IS A RELAY RATHER THAN A CURIOSITY:** guardrail 6 rules the company
  adopting a PRODUCER-signed gate (Tier A / Tier B) and says nothing about the
  reverse. Everything else the port calls "company-only" is a path or a config row,
  which is inert — a MODELLING POSITION is not, because the producer can
  independently invent a competing one against the same source. It nearly did:
  G35's walk on 2026-08-11 was about to admit ServiceNow group-scoped roles and
  would have minted a second group→application shape. It was stopped by the SME
  showing the screenshots, not by anything in this repo.
  **RULED AT THAT WALK (gate-log 2026-08-11 RECORD):** G35 admits the group-scoped
  role TYPES into the vocabulary and mints NO graph shape — the shape stays owned by
  `snow-hpsm-queue-to-group`. **What the company session should do with this relay:**
  confirm the gate and loader still exist and are signed, and say whether the
  producer should hold a READ-ONLY record of the model (names, node classes, edge
  shape — no code) so producer-side gates stop drafting blind. Recorded producer-side
  in `knowledge/upgrade-plans/servicenow-replica-evidence.md` (§9, §10.4-§10.6).
  **THREE ASKS ADDED 2026-08-11, each from a company code search the producer cannot repeat.**
  (i) CONFIRM THE PATHS. Only one full path was ever shown to the producer; the rest were bare
  filenames. Producer convention would put the gate at `config/gate-prompts/<id>.yaml`, the
  loader under `drydocs/loaders/`, the cypher under `drydocs/loaders/cypher/` — INFERRED, never
  observed. Confirm or correct, so producer-side documents stop citing names without homes.
  (ii) THE TIER PARSER HAS A GAP AT THE SRE CASE. It derives L3 from a development token and L2
  from a support token and returns None otherwise — the SME's support-SRE code is not among
  them. G35 ruled SRE presence DERIVED from the group-name convention, so the derivation it
  relies on does not currently cover that case. Rule whether the parser gains the token, or
  whether SRE is derived some other way.
  (iii) DOES `:LogicalDeployment` ALREADY EXIST COMPANY-SIDE? It appears in the primary-resolver
  edge shape. DryDocs has NO deployment-grain node, and both C10's gate-bound candidate #1 and
  Idea-101 are open questions about whether to adopt one. If the company already models a
  deployment concept, two sides are about to model it independently — which is precisely the
  collision this relay exists to prevent, and it is a bigger one than the group shape was.
  **A rider worth ruling while you are there:** the crosswalk is hand-verified YAML,
  per-machine and gitignored, while the ServiceNow TOM tables carry the same
  app→group→technician mapping FROM THE SOURCE, with the crosswalk's `l2`/`l3` tiers
  corresponding to TOM's incident-resolver tiers. That is a real upgrade path for the
  crosswalk and it belongs to YOUR gate, not to G35 — but G35's §D4 ruling
  (hand-verified > ServiceNow TOM > SEAL extract) already assumes both can coexist,
  so a decision to retire either one needs to reach the producer.

- **RELAY-7 — YOUR `email-dl-contact-point` GATE PROMPT NOW ASKS A QUESTION THAT HAS
  BEEN ANSWERED** `[VERIFIED-PRODUCER]` (raised 2026-08-11 at the producer review of
  PORT-REPORT-caa0406). The port correctly dropped producer edits to
  `config/gate-prompts/email-dl-contact-point.yaml` — the file is canonical-company and
  the disposition is right. But the dropped content was not a producer preference, it
  was an **SME ruling**: producer commit `5405ab6` re-posed §G4 because `<DOMAIL>` is
  removed alongside the shouts, so the option that clause used to weigh no longer
  exists. Checkable from here: `git show 5405ab6 --stat` lists that yaml.
  **What this means for you:** your copy still frames §G4 as though generated mail
  survives. Running the gate on it will produce a ruling on a dead option. Re-pose §G4
  your side — the new question is what corroborates §B2 now that the wired feed is
  gone (psets, intended-only, or the ServiceNow incident record). Do NOT resolve this
  by changing the file's disposition; canonical-company is correct and a future port
  should drop producer edits to it again.
  **A rider that arrived in the same range and belongs to the same gate:** §G6 carries
  the Idea-105 rider — two claimants on the 4000-char `DESCRIPTION` on generated
  objects. A fourth exit now exists that the rider does not list: a versioned sentinel
  prefix (`DD1|`) partitions the field, so the generator's literal stays untagged and
  E1's exact match is unaffected, with zero migration on any deployed object. Producer
  is writing that up; take it as an input to your gate rather than re-deriving it.

- **RELAY-8 — `pat_app_links.cypher` IS STILL ON THE PRE-S3 KEY, and reordering the
  loaders hides it rather than fixing it** `[VERIFIED-PRODUCER]` (raised 2026-08-11
  from an SME load failure; a T23 residue). The SME hit
  `ConstraintValidationFailed` loading `seal_applications` after PAT, diagnosed it
  correctly company-side, and intends to reload in a different order. The order works.
  The defect does not go away.
  **What the producer can verify from here, and did:** the collision cannot occur
  producer-side, for a reason worth knowing — `pat_product_mapping.cypher` L66 MERGEs
  on `{app_id: trim(raw_app_id)}`, the SAME neutral key `seal_applications.cypher` L25
  uses, dual-writing `seal_id` only as a deprecated alias `ON CREATE`. Same key both
  sides of the join means no stub, no second node, no order dependency. Producer also
  has NO `pat_app_links` loader or cypher at all.
  **So the company's `MERGE (a:BusinessApplication {seal_id: row.seal_id})` with
  `is_stub=true` is a loader that never got re-keyed at S3.** It mints a node with a
  null `app_id`; the uniqueness constraint ignores nulls, so `seal_applications` cannot
  match it, mints a second canonical node, and `SET a.seal_id` then collides on the
  unique `seal_id`. THE FIX IS THE RE-KEY, not the ordering: point that MERGE at
  `app_id` like every other site, and the load order stops mattering. Until then the
  ordering rule below is a live workaround, and any NEW loader that stubs on `seal_id`
  reintroduces it.
  **The RuntimeError was the guard working, not a bug.** `app_identity.py`
  `_assert_no_pre_cutover_applications` refused to load on finding null-`app_id`
  `:BusinessApplication` nodes, which is exactly its job — it stopped a partially
  doubled graph from being compounded. That guard IS producer-side and ports.
  **The ordering rule, while the re-key is outstanding:** `seal_applications` loads
  BEFORE any PAT loader that can mint a `:BusinessApplication`. Producer's
  `REFRESH_REFERENCE_CHAIN` already satisfies it (seal_applications and seal_contacts
  precede pat_product_mapping), so this is a company-side sequencing correction, not a
  producer change. Note the company runbook's step 8 currently sequences the PAT block
  BEFORE the SEAL block, which is what produced the failure.
  Rides T23, which already carries the S3 re-key and its all-8-sites-in-one-apply rule.
  **CORRECTION TO A COMPANY-SIDE MEMORY NOTE, 2026-08-11 — please strike it.** A
  company session recorded `load-order-seal-before-pat.md` saying the fix "is
  producer-owned — the canonical `CANONICAL_LOAD_SEQUENCE` will be corrected upstream
  and port down; don't patch the company order ad hoc in the meantime." **No producer
  correction is owed and none is coming.** Verified here: `REFRESH_REFERENCE_CHAIN`
  already runs `seal_applications` and `seal_contacts` at positions 4-5 and
  `pat_product_mapping` at 7, and producer's PAT loader MERGEs on `app_id` anyway, so
  producer has neither the wrong order nor the collision. A session that waits for that
  port waits forever, and the note's "don't patch ad hoc" clause argues against exactly
  the v3 reorder that was correct. **The company order fix is company-owned; the
  `pat_app_links` re-key is the durable half.**
  **THE T23 BLAST RADIUS INCLUDES PROSE, and that is the reusable lesson.** The v2
  runbook stated "running SEAL after PAT is safe either way" — TRUE before the S3
  re-key and false after it, with nothing to catch the change. T23's
  all-8-key-bearing-sites-in-one-apply rule covers CODE sites; a document asserting the
  old invariant is a ninth site of a different kind. When the re-key lands, sweep the
  prose for order and identity claims as well as the Cypher. Producer was checked at
  this entry and carries no equivalent claim.
  **One more, because fixing the page does not fix the source (the J37 family):** the v2
  page is GENERATED from a repo fragment by the company's docs-publish verb (company-only;
  not registered producer-side) and carries the
  "generated" banner; v3 is a standalone manual page. Left as is, the authoritative-
  looking page keeps republishing the buggy order while the correct one looks like
  somebody's notes. Fix the fragment, then let v3 be the render — same reasoning as
  "never parse a render", applied one step upstream. That fragment is company-only;
  producer has no copy of it.

- **RELAY-9 — THE PAT TEAM REPORT *DOES* CARRY aligned/flex/dedicated; it is named
  `Relationship Type`, and the column that looks like ours is a decoy**
  `[VERIFIED-PRODUCER]` (raised 2026-08-11; producer commit `2f33e5c` pins it).
  A company session building the `dev_teams` / `pat_product_mapping` projection held
  off loading the mapping half, concluding that neither `pat-team-member-details-report`
  nor `TEAM_ACTIVE_SOURCES_REPORT` carries an alignment column and that `team_type`
  therefore had no source. **Holding off was right; the premise is wrong.**
  **The mapping, from the SME's TEAM_DETAILS_REPORT column layout:**
  `Relationship Type` → `team_type` (values Aligned | Flex | Dedicated) ·
  `Product ID` → `product_id` · `Supporting Area Product ID` → `area_product_id` ·
  `Sponsoring Area Product ID` → `sponsored_area_product_id` · `Seal IDs` → `seal_ids`
  (semicolon-delimited, 1..n — which is why `PatProductMappingRow` normalizes `;` → `,`).
  **THE DECOY, and it is the whole reason this relay exists.** The same report also
  carries **`Team Type Name`** — the team's DISCIPLINE (Technology, Product, Design,
  Data & Analytics, Portfolio, SRE). It is not our field. Mapping by column-name
  similarity picks it every time, because the correct column shares no words with
  `team_type` and the wrong one matches it exactly. The two are orthogonal facts: a
  Technology team may be Aligned, Flex or Dedicated.
  **Do NOT take the "the ontology is stale" exit.** `docs/Product/Technology_Team_Types.md`
  §3 is the governing PAT definition of Aligned / Dedicated / Flex and states that Team
  Types are maintained in the PAT Product Catalog. Aligned/flex/dedicated is an asserted
  governance fact (who prioritizes the backlog, who funds it), not the discipline and not
  derivable from whether a `product_id` is populated.
  **Producer-side the consequence is louder than a wrong edge property:**
  `PatProductMappingRow._check_team_type` RAISES on anything outside
  `{aligned, flex, dedicated}`, so feeding the discipline rejects EVERY row rather than
  writing a bad value. If your row model kept that validator, the same is true your side.
  **The discipline is deliberately not modelled** — it is a property of the TEAM, while
  every field on that row is a property of the team's RELATIONSHIP to a product.
  `extra="ignore"` drops it silently, same handling as Sponsoring Product Line. Adopting
  it needs its own home and its own gate; do not bolt it onto this row.
  **Two checks producer ran so you do not have to.** (a) The report's five `Sponsoring*`
  columns reconcile EXACTLY to the G6-RIDER inventory — four ID+Name pairs plus two
  name-only — so C17 §b/§c stand unchanged and there is no coverage gap. (b) The report
  carries a **`Legacy Team ID`** (opaque UUID-shaped predecessor key), unmodelled either
  side; `team_id` remains the only team key. Do not let it become a second one.
  **STILL OPEN, and it is yours as much as ours:** `sponsored: bool` has no named source
  column in the layout. It is plausibly derived from whether a sponsoring column is
  populated, but that is inference — and since cypher §3a/§3b already hard-code
  `sponsored = true` on their own edges, the flag may only be load-bearing on the §2
  alignment edge. Confirm against the extract before deriving it.

OWED COMPANY-SIDE:

> **RATIFICATION EVIDENCE MUST NAME ITS PROVENANCE (new 2026-08-09, and it has
> already produced one false positive).** A company-side gate-log entry is NOT
> evidence of company ratification, because `config/gate-log.md` is
> `union-append` — producer entries land there BY DESIGN. The same is true of
> the crosswalk yamls and `source-registry.yaml` confirmed flags: all three
> port. So "the entry is present company-side" is consistent with a genuine
> ratification AND with the producer's own record having arrived by port, and
> nothing in the artifact distinguishes them.
> **PROVED, not theorised:** the `airflow-crosswalk` Step-1 check reported
> RATIFIED on three corroborating signals, all three of which port. The
> discriminating command —
> `git log --oneline -S "Airflow/MWAA" -- config/gate-log.md` — returned exactly
> one commit, `80d0fc0e`, whose subject is
> `port(cewilson): apply eeaffa2..f7970e5 (step 31 — web console O2 + 2026-07-14
> gate session) onto branch`. A PORT commit. The entry arrived from the producer;
> the ratification was never performed, and the producer's byte-identical
> `confirmed:` comment string confirms the copy.
> **RULE: before reporting any gate RATIFIED, run the provenance check** —
> `git log --oneline -S "<a distinctive phrase from the entry>" -- config/gate-log.md`
> — and quote the introducing commit. A port commit means NOT ratified. A
> company-authored commit unrelated to any port means ratified, and that commit
> id is what gets ledgered.
> The strongest positive evidence is content the producer has never seen: an
> entry that rules company-only rows (e.g. the nine company-only source entries
> in `audit-fields.yaml`) cannot be a ported producer artifact.
> **STRONGER STILL — an entry class that is self-proving BY CONSTRUCTION (new
> 2026-08-09).** A Tier-A `RATIFICATION (... adopted-via-port)` entry can NEVER be
> a ported artifact, because the producer never writes one: it is the CONSUMER's
> record of RECEIVING a port, and the producer has nothing to adopt. Verified
> producer-side rather than assumed — grepping `adopted-via-port` and
> `RATIFICATION (Tier A` across producer `config/gate-log.md` returns NOTHING; the
> §6a template lives in this file, and every instance of the shape lives in YOUR
> gate-log. For that class the pickaxe is therefore not the proof — it is only how
> the commit id gets named for the ledger.
> **CORRECTION, SAME DAY, AND IT IS THE PRODUCER'S OWN ERROR — a `port(...)`
> subject does NOT prove an entry arrived from the producer.** The rule above was
> first written implying the pickaxe would return a company-authored, non-port
> commit for a Tier-A entry. It does not. The company's audit-envelope-phase4
> re-check returned a PORT commit for the Tier-A adoption at their
> `gate-log.md:1645` — because the RECONCILE step is exactly where the consumer
> writes its own adoption record, and that work commits under the port's subject.
> **THE EXAMPLE IS SHARPER THAN FIRST RECORDED (attribution corrected 2026-08-09
> pm, by the company session, against the producer's own miscite of `b75871b8`).**
> `12fa680e` — `port(cewilson): apply 6713c142..5f79d145 (steps 59-81) onto company
> main`, 2026-08-04 — carries BOTH entries at once:
>   L1590, the producer's own `audit-envelope-phase4` sign-off (13/13). PORTED.
>   L1645, the company's Tier-A adoption of it. COMPANY-AUTHORED, written during
>   that same reconcile.
> One commit, one subject, two authorships. That is the whole argument in a single
> object, and no subject-based test can separate them. So the subject test is sound
> in ONE direction only:
>   `gate(...)` / company-authored, unrelated to a port -> RATIFIED. Dispositive.
>   `port(...)` -> NOT dispositive either way. It means the commit applied a port;
>   it does not tell you who authored the lines inside it.
> **The reliable discriminator is CONTENT, not subject: does the producer's tree
> contain this entry?** For the Tier-A class the answer is structurally no, which
> is why that class still resolves — the reasoning holds, the mechanism named for
> it was wrong. Read the company session's own gloss with the same care: it first
> labelled L1645 a "ported artifact, as expected", and it is not one — the
> producer has no entry of that shape to port. **Challenged, that session
> re-verified and corrected itself the same day**, and its doctrine note is the
> cleanest statement either side has produced, so it is adopted here verbatim in
> substance: *when a heading's shape is company-only — a Tier-A adoption, or a
> ruling over company-only rows — the entry is company-authored EVEN WHEN CARRIED
> BY A `port(...)` COMMIT; do not let the commit subject alone demote it.*
> Net effect on that gate: two of its three heading-named entries are company
> ratification content, which makes RATIFIED **stronger** than first stated, not
> weaker. Both sides reached the same rule independently, from opposite errors —
> the producer over-trusting the subject, the company over-trusting the entry.
> **But read the SUBJECT field, not the heading.** §6a fixes Subject as "the exact
> statuses flipped", so such an entry discharges the gates its SUBJECT flips; a
> gate named only in the heading is a citation, not a ratification (the J28
> heading-vs-body distinction, in its ratification costume).

- **BOTH crosswalk gates: NOT RATIFIED** (checked 2026-08-09, company `main` @
  `a4c4ce37`). Each read RATIFIED at Step 1 on three portable signals; the
  provenance check overturned both. The producer's own sign-offs ported across
  and were read back as company confirmation.
  - `airflow-crosswalk` (producer F2, 2026-07-14, 17 confirmations, ACCEPTED IN
    FULL) — `-S "Airflow/MWAA"` returns ONE commit, `80d0fc0e`, a port.
  - `autosys-crosswalk` (producer F1, 2026-07-14, 13 confirmations, ACCEPTED IN
    FULL) — `-S "autosys-crosswalk"` returns TWO, `e2cf3485`
    (PORT-REPORT-57914bf4) and `80d0fc0e`. Both ports; no `gate(ratify):`
    commit exists for it.
  So the report line "both crosswalk gates are signed off company-side,
  matching the producer" is exactly inverted — they are the producer's,
  matching itself. Both ratifications are owed. Neither session wasted work:
  each correctly stopped before steps 2–3.
  The same check is owed on the remaining three staged prompts before any is
  marked ratified.
  **DEFERRED 2026-08-09 (SME) — owed, but not scheduled, and the trigger is a
  PRECONDITION rather than a date.** Neither orchestrator is ingested on either
  side; `external/orchestration/{autosys,airflow}/` hold a README each and no
  source is registered. A company session spent here today buys nothing
  operationally, and company sessions are the scarce resource — P8, the
  `ui-write-surface` entry, T22/DD6 and the T23 graph legs all have live
  consumers. **TRIGGER: ratify BEFORE the first AutoSys or Airflow source is
  registered for ingestion — not after, and not at the ingestion review.**
  WHY THE TRIGGER HAS TO BE A PRECONDITION, and this is the part that makes
  deferral safe rather than merely cheap: `drydocs_core/orchestration/crosswalk.py`
  gates `resolve()` on `require_confirmed=True`, and BOTH crosswalk yamls carry
  `status: confirmed` — which PORTED. So the only runtime gate protecting these
  mappings is already satisfied company-side by an artifact the company never
  ratified. Nothing calls `resolve()` today (verified producer-side: no caller
  outside the module and its own tests), so the gate is open onto an empty room.
  But the first ingestion wires a caller, and at that moment `resolve()` succeeds
  SILENTLY — there is no second checkpoint where the missing ratification would
  surface. That is this session's recurring defect class in its purest form: a
  check that reads like a gate and passes for the wrong reason. Deferring is
  correct; forgetting would not be.
- **`audit-envelope-phase4`: GENUINELY RATIFIED — company commit `838857e7`,
  entry at company `gate-log.md:2624`** (re-checked under the stricter rule
  2026-08-09, company `main` @ `48252f72`; first checked @ `a4c4ce37`).
  Subject `gate(audit-envelope-phase4): company extension - rule 9 company
  sources + sp...` — a `gate(...)` subject, company-authored, unrelated to any
  port. THAT is the ledgerable id, and it was missing from the first pass: the
  original finding was right but rested on three entries rather than a named
  commit. THE THREE-WAY READ, corrected 2026-08-09 pm and worth keeping intact
  because it is the reference example for the whole provenance rule:
    L1590 — the PRODUCER's own sign-off (13/13). Ported. Portable.
    L1645 — the COMPANY's Tier-A adoption. Company-authored, and it rode inside
            the SAME port commit `12fa680e` as L1590.
    L2624 — the COMPANY's nine-source extension, via `gate(...)` commit
            `838857e7`. Company-authored, unambiguous by subject too.
  Two of the three are company ratification content. The producer's earlier
  attribution of L1645 to `b75871b8` was wrong and is corrected here. Three heading-named entries, and the session
  correctly separated them rather than counting them as three signals:
  - `gate-log.md:1590` — the PRODUCER gate (M3, 13/13, 2026-08-04). Identified
    unprompted as arriving via the a14a8028 / 5417ef10 ports. This one is the
    ported artifact, and on its own it would have been another false positive.
  - `gate-log.md:1645` — `## 2026-08-04 — RATIFICATION (Tier A,
    adopted-via-port): doc-06 audit envelope — M3 + M4`. An explicit Tier-A
    adoption entry, the §6a/L7 template shape.
  - `gate-log.md:2624` — `## 2026-08-07 — GATE: audit-envelope-phase4 (company
    extension — the nine company-only N9 sources) — SIGNED OFF, 9/9 +
    audit-download trigger`, signed chad.wilson.
  **THE THIRD ENTRY IS PROOF, not inference.** It rules nine sources the
  producer has never seen, and the producer VERIFIED it carries none of them —
  no `hr:` sources and no `repo:org-location` exist in
  `config/source-registry.yaml` at all. Content the producer does not have
  cannot have arrived from the producer. That is the positive evidence the
  pickaxe cannot supply, and it is why this check is trustworthy where the two
  crosswalk checks were not.
  The producer's concern on the staged prompt — "your audit-fields.yaml carries
  NINE company-only confirmed-source entries the producer cannot see" — is
  DISCHARGED: all nine were ruled 2026-08-07 by the producer's own method, no
  divergence, every ruling landing `status: stub` so no loader writes envelope
  properties. The audit-download trigger stands DORMANT (not reachable from
  that venue; ingesting it is an SME decision).
  **`envelope-property-terms`: DISCHARGED ON STRUCTURAL GROUNDS, 2026-08-09 —
  and settled from the PRODUCER side, which is unusual enough to say why.** The
  Tier-A entry above (`gate-log.md:1645`) names **M3 + M4**, and M4 IS
  `envelope-property-terms` (producer gate-log:1392, 10/10, 2026-08-04). It is a
  Tier-A adopted-via-port entry, and by the rule above that class cannot be a
  ported artifact — so no company-side pickaxe is needed to establish that it is
  genuine. This is the one pack of the five that did NOT need a company session
  to resolve.
  TWO SMALL THINGS ARE STILL OWED: (1) quote the introducing commit id, so this
  ledgers like the other true positive rather than as a producer inference; and
  (2) confirm the entry's SUBJECT field flips M4's statuses rather than merely
  naming M4 in the heading — if the Subject turns out to cover M3 only, the pack
  is LIVE and its Step 1 runs as written against `gate-log.md:1645`.
  **NAMING, worth recording:** the nine use the producer's registry-v2 grammar
  (`origin:artifact` / `origin@db.schema.table`) — `controlm:app-codes`,
  `snow@[db].[schema].itsm`, `hr:emp-hierarchy`, and one deliberate re-home,
  `repo:org-location` → `hr:emp-location`. The v2 grammar is holding on
  sources the producer never authored, which is the strongest test it has had.
- **`ui-write-surface`: RATIFIED 2026-08-09 — company commit `48252f72`,
  entry at company `gate-log.md:2711`.** Subject:
  `gate(ratify): ui-write-surface company ratification - NEVER RUN -> SIGNED OFF
  (write-path census of deployed drydocs-api console)`. THAT SUBJECT IS THE
  DISPOSITIVE EVIDENCE — a `gate(ratify):` commit, not a `port(cewilson):` one,
  which is exactly what the rule above names as proof. Committed on company
  `main`, unpushed at the time of report.
  This row was deliberately held at "SIGN-OFF GIVEN, ENTRY NOT YET WRITTEN"
  until the commit existed, rather than flipped on the SME's authorisation —
  the whole point being that an intention and a ratification are different
  artifacts. Both riders were met in the committed entry: the `gate(ratify):`
  subject convention (the `ecdf0af` shape from seal-app-ref-edge-reshape), and
  the census placed IN the entry rather than pointed at.
  **BUT THE SELF-PROVING ARGUMENT IS OVERSTATED, AND THIS IS THE THIRD
  INSTANCE OF TODAY'S DEFECT CLASS — VERIFIED PRODUCER-SIDE, NOT SUSPECTED.**
  The report offers four bullets as content "the producer cannot have". TWO OF
  THE FOUR ARE PRODUCER ARTIFACTS THAT PORTED:
  the computed source-first `v_seal_contact_grid` view is producer code at
  `drydocs_core/mapping_store.py:216-231` — the same UNION ALL emitting literal
  `'source'` / `'override'`, source-first, never merged; and the
  `app_code_mapping.origin NOT NULL CHECK` is producer code at the same file,
  lines 258-259, introduced by producer commit `17d9e08` (K9, 2026-08-03).
  Both are O24/M2 producer work. A provenance check resting on those two would
  have failed the same way the crosswalk checks did.
  What IS genuinely company-only, and what the row therefore rests on: the
  census of the DEPLOYED console's routes with tiers, the "no M3-shaped path
  found" verdict against their tree, and the precedence-grep negative with its
  company-tree line references. Those the producer cannot have. The ratification
  stands; two of its four stated proofs do not.
  METHOD NOTE, because it bit the producer too: a first grep for
  `origin TEXT NOT NULL` returned EMPTY and nearly confirmed the company's
  reading — the column is whitespace-padded (`origin             TEXT NOT NULL`),
  so the pattern missed. An empty grep is not evidence of absence; that is the
  RELAY-3(b) lesson arriving in a third costume, on the same day.
  Step 1 was provenance-verified as NEVER RUN before the work began — the check
  returned two PORT commits (`afa2deeb` on branch `drydocs-port-20260721`, and
  `12fa680e`), so the producer's O20 sign-off had ported across exactly as it
  did for the two crosswalks. **This is the first time the rule PREVENTED a
  false positive rather than catching one afterwards**, one day after it was
  written.
  The Step-2 census is genuine company-only content and is what will make the
  entry self-proving: a full write-path route census with tiers, `/raw-cypher`
  as the only graph-touching surface and read-pinned behind two layers
  (`ensure_read_only` + `RoutingControl.READ`), **no M3-shaped path found**, and
  a repo-wide grep confirming NO executable code assumes either precedence
  direction. Dispositions map 1:1 onto the producer's O20 (`config/gate-log.md`
  §701, Confirmed 4 · Edited 0 · Rejected 0), with no divergence.
  WORTH CARRYING BACK, because it is the company AHEAD of the ruling rather
  than conforming to it: the producer ruled M2 requires an always-visible origin
  flag; the company implemented it so the flag CANNOT be absent — `app_code_mapping`
  rejects an unflagged insert at the DB constraint (`origin TEXT NOT NULL CHECK`),
  and `seal_contact_override` makes it structurally impossible by computing origin
  source-first in the grid view and emitting every row as a literal `'source'` or
  `'override'` via UNION ALL, never merged.
  Two things stay open on their side, correctly: PRECEDENCE (override-vs-graph
  remains a future gate on both sides) and the admin/SUPER-USER page, which O20
  §SME-1 records as EXPECTED but which has no route built — company-side scoping,
  not producer work.
- **CONFIRMED GENUINE, from the same session — the row-6 / `cm_hosts` answer.**
  Unlike the ratification claim this CANNOT be a ported artifact, because it
  describes company loader-tier state the producer cannot see: their CM_HOSTS
  extract is staging-only (supplement/loader not built), so `cm_hosts` stays
  `confirmed: false` while its P3 host stage is unwired. Producer-side the same
  row is `confirmed: true` (hosts loader + RUNS_ON shipped at P3, 2026-07-27).
  That is the **Q1-B standing divergence**, now confirmed from the company side
  for the first time rather than assumed. Their reading is correct and worth
  keeping: a crosswalk maps CONCEPTS, not loads, so a loader-tier hold does not
  touch the crosswalk ratification — row 6 lands with no pattern or ontology
  divergence, and the host-topology resolution a future AutoSys loader would
  face is a loader-gate matter.
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
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | **(2) DISPOSITION SETTLED 2026-08-11 (SME): the verb is DEPRECATED-IN-PLACE — no-op on a fresh graph, seeds commented out and audit-kept, kept in the sequence only for old-graph deprecate-in-place, optional to run. It belongs in `CHAIN_EXCLUSIONS` WITH ITS REASON, not in the chain (see the supplements bullet in the divergence ledger). Clauses (1), (3) and (4) remain producer belief as of 2026-08-01.** |
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

STEP LEDGER — delta since `ae21ee4` (steps 43–105 collapsed above; 106–123 are the
`5417ef10..ae21ee4` range, already ported and MERGED company-side per step 128, kept
for context). Steps 124–134 are the NEW delta this base certifies. Each
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

(Steps 116-121 are APPLIED at PORT-REPORT-6f03264 and collapse into **Last completed
port** above. The live ledger restarts at 122, delta since `6f03264`.)

122. J41 — THE OPENING SEQUENCE [TEST-PINNED] (`f32aadc` mechanism, `9a71479` docs).
    The producer half J35 never had, and the three rules at the top of this file are
    the payload: run the six checks before offering a base, port a `port-base-*` TAG
    rather than `HEAD`, and name ONE OWNER PER PHASE. `drydocs.port_preflight` +
    `scripts/port_preflight.py --base <last-ported> --tag` enforce it; the
    ledger-coverage check mechanises the ROLL-PROCEDURE RULE.
    **Nothing here is yours to run** — this is producer machinery, and the only part
    that reaches you is the reconcile-port SKILL.md change: if the producer offers a
    bare SHA or "HEAD" instead of a `port-base-*` tag, STOP and ask for the tag.
    THE ONE CAUTION THAT WOULD COST YOU A REWORK: `tests/unit/test_module_boundary.py`
    gains a new `port` component group. If your copy has diverged, take the GROUP with
    the module or the classification guard fails on an unclassified `drydocs.port_preflight`.
    Follow-up `c89cf9f`: the ledger-ROLL commit is ritual, found by running the check
    against its own repo — the commit that writes the citations can never be among
    them, so without the exemption the check never terminates.

123. MARKDOWN FENCES — `docs/port-prompt.md` meant something other than what it said,
    for five days [TEST-PINNED] (`40302a2`). The pasteable prompt is wrapped in a
    ```` ```text ```` fence with a ```` ```powershell ```` example nested inside it,
    BOTH three backticks — so the inner block's closer closed the OUTER one and 872
    lines of guardrails, relays, tracker and ledger leaked out of the payload. Live
    since `84ed7e3` (2026-08-05), through four ports. Nothing errored.
    **The rule, and it is the whole fix: an outer fence must be LONGER than anything
    nested inside it.** `tests/unit/test_markdown_fences.py` guards `docs/**` and is
    the portable part — take it, then run it against YOUR docs tree, because the same
    defect class is not producer-specific. A sweep of all 507 tracked `.md` files found
    six; one more was ours (`docs/decisions/0002`, orphan trailing fence, fixed here).
    The rest sit in captured transcripts and vendored skill packs and were inboxed
    (Idea-103) rather than edited — fixing somebody else's capture to satisfy a guard
    is a provenance call, not a formatting one. Same question applies on your side.

124. LOCAL-INFRA CHORES + ONE ADR [venue-pinned / docs] (`8c4ee1e` G49, `5a6208e`
    G50, `3304666` G49 follow-up, `034eb70` G53). G49/G50 are DESKTOP-VENUE facts —
    an MCP server registered and live-verified, four dangling Docker volumes removed —
    and their deliverable is a backlog close, not code. Nothing to apply your side;
    re-run the equivalents against YOUR venue if you want the same assurance (J18:
    a live-verification claim names its machine, and these name ours). `3304666` is
    worth one line on its own: the G49 CLAIM commit shipped with its own guard red,
    and the fix removes it from `next_ready` — the claim-before-work rule working as
    intended, catching a bad claim rather than hiding it. `034eb70` is ADR 0011, the
    SINGLE-DATABASE CONTINGENCY — written while there is time rather than under
    pressure. Take it: it is the decision record for the topology question your side
    also carries, and an ADR is cheaper to read now than to re-derive during an outage.

125. O47 — THE /intake PAGE, SLICE 3 [like-for-like, canonical-producer]
    (`c90cd1d` API, `ad7b1e4` web). `drydocs_api/query_specs.py` gains
    `intake.area-tree.v1` — the area cascade in ONE call rather than a per-level
    round trip — and the web half adds `routes/IntakeRoute.tsx`,
    `components/IntakeStepper.tsx`, `lib/intakeApi.ts` and an `auth.ts` helper.
    `web/**` is canonical-producer BUT read divergence #K7–K15 first: a wholesale
    `git checkout cewilson/main -- web/src` re-adopts the held folder-attribution UI.
    Take these files by name, not the directory.

126. O53 + THE GRAPH-VS-FILES EXPERIMENT [like-for-like / default_ok] (`c9ea9fc`
    O53, `c353956` the record, `3c440ad` the HTML view). O53 removes `HeroArt.tsx`
    and adopts the experiment's ALPHA code set; `web/src/index.css` and
    `tests/unit/test_ui_components.py` move with it, so the component COUNT changes —
    if you carry the K7–K15 hold your total is producer's minus one, and this commit
    shifts the number the hold is measured against. Re-derive it, do not copy the
    assertion. `docs/reviews/graph-vs-files-experiment/**` is the full SME-reviewed
    record plus a later HTML view: `default_ok`, take or skip freely, it binds nothing.

127. L28 — KGoT REGISTERED, AND THE EXECUTIVE OVERVIEW GETS CITATIONS [reference]
    (`75b4855`). `reference/REGISTRY.yaml` gains the Knowledge-Graph-of-Thoughts
    entry and `reference/research/knowledge-graph-of-thoughts.md` the write-up.
    `reference/**` is External-tier and canonical-producer — clean add, no conflict
    expected. The overview change is the substantive half: claims that were bare now
    cite something.

128. PORT-LOOP BOOKKEEPING (`06d4469`). The `ae21ee4` port is recorded MERGED
    company-side with its branch removed — `docs/port-prompt.md` only. Nothing to
    apply; it is here because the ledger's ritual exemption is deliberately narrow
    (`chore(port): roll|ledger` only), so a substantive `chore(port):` such as
    retiring manifest rows still has to be told to you. This one is not substantive,
    and saying so is cheaper than leaving you to check.

129. THE SERVICENOW REPLICA EVIDENCE RUN [UNRULED — evidence, not a decision]
    (`3d9fc97`, `5662e21`, `7d08fc6`, `9d4b2f7`, `7385412`, `ac24a12`, `ca3c65e`).
    Seven commits building `knowledge/upgrade-plans/servicenow-replica-evidence.md`
    from the K21 screenshots, plus read-only probes at
    `drydocs/loaders/sql/adhoc/servicenow_relationship_open_questions.sql`. THREE
    findings reverse earlier producer beliefs and are the reason this is a step and
    not a footnote: (a) the edge vocabulary is 54 rows and the SHORTFALL is a question
    about the replica itself, not about our mapping; (b) the API evidence REWRITES the
    query plan — the edge table drops out of it; (c) the seed is ~200 applications,
    not 14,683, which changes the mechanism and not just the number. `9d4b2f7` is a
    correction worth reading before you run anything: the probes COULD NOT HAVE RUN as
    first written — views are UPPERCASE and columns are quoted lowercase. The SQL is
    adhoc and read-only; run it against YOUR replica or not at all. Every value here
    is mechanism — no counts, no names crossed the boundary.

130. G35 — TOM ROLES: ENUMERATION AND CARDINALITY, SIGNED OFF [GATE-AUTHORIZED]
    (`f9b480b` release, `0b86f78` drafting, `6e7989e` round 1, `b737181` rounds 2–3,
    `4c0c834` the inheritance ruling, `9268f94` SIGN-OFF). Guardrail 7 applies: this
    is gate-authorized producer-side and your side runs its OWN gate — a producer
    sign-off is not a company sign-off. THE ONE THING TO CHECK BEFORE APPLYING, and it
    is a shape collision: G35 admits group-scoped role TYPES and mints NO graph shape;
    the `(:BusinessApplication)-[:HAS_SUPPORT_QUEUE]->(:HpsmQueue)-[:RESOLVED_BY]->
    (:ServiceNowGroup)` shape stays owned by your signed `snow-hpsm-queue-to-group`.
    Confirm that gate and its loader still exist your side, and do NOT let G35 re-mint
    a competing group→app shape. `4c0c834` carries a producer self-correction —
    inheritance is COMPUTED, not typed, and the earlier E1b reading was wrong to doubt
    the blank state. `config/gate-log.md` is per-entry union as always.

131. THE CONTROL-M GREENFIELD JOB STANDARD — C29 → C32 + G66/G67 [UNRULED, and the
    largest substantive block in this range] (`5613ea0` C29+G66, `4b39960` the casing
    conflict, `e1d9ac0` C30+G67, `8471e40` C31, `5405ab6` the DOMAIL ruling, `5dfa9c6`
    C32). Reads the estate's own standards corpus, the DPL generator capture and live
    folders, and reconciles three sources that disagreed. What lands: the DESCRIPTION
    read seam (`drydocs_lineage/extractors/controlm_xml.py` +
    `drydocs_core/orchestration/controlm/description_tokens.py`, zero graph writes);
    the greenfield standard as a publishable page; and R30–R40 with a working
    conformance detector over real staged XML. FOUR SME RULINGS ride it and are
    binding on any company adaptation: notification is REMOVED as a mechanism (the
    ServiceNow incident is the call to action — never wire a DL to a `DOMAIL DEST`,
    never bind the unset `%%NOTIFY`); PDN is Production DELAY Notification to
    downstream BUSINESS users and is NOT a support tier; no ServiceNow queue belongs
    in a Control-M variable, because the escalation DB owns technician routing; and the
    post-execution `cat` is TOK/CTL only, never a data file. `internal/**` captures
    carry the values; the `knowledge/**` twins carry the mechanism — verify the split
    survives on your side, since your captures are the ones with real names in them.
    `5405ab6` is the ruling that closed the last open item: `<DOMAIL>` goes with the
    shouts, so R40 covers three tags. NOTE the correction inside C32 — the "deletion
    costs nothing" rationale is TRUE of generated folders and FALSE of hand-built ones,
    which declare a real address; a fix batch must separate the two populations.

132. REMEDIATION BACKLOG ONLY — no code [per-entry union] (`95738a8` G68+O59,
    `2d6cbb4` G69). Three items raised and deliberately NOT built: the folder-set
    PROFILE seam, the `/remediation` intake surface behind it, and R41–R44 registered
    AND detected in one change. `drydocs_remediation/overview_readme.md` arrives with
    G69 and is the readable part — the governance ladder (open → provisional →
    ratified), why status is independent of severity, and why a detector without a
    registry entry cannot be signed off. Worth reading even if you never pull the items.

133. THE COMPANY XML PROCESSORS, CAPTURED — AND TWO MECHANISM BACK-FLOWS BUILT
    [TEST-PINNED] (`382cdb6` capture, `dbb57e2` the raise, `406cbd6` G75+G76 built).
    THIS ONE IS ABOUT YOUR CODE, so read the three standing-divergence bullets above
    before applying. The capture transcribes your three processors verbatim into
    `internal/**`; from it, two PURE mechanisms came producer-side —
    `drydocs_core/orchestration/controlm/audit_time.py` (BMC compact timestamp → ISO) and
    `drydocs_core/orchestration/controlm/conditions.py` (`PL-`/`PG-` scope + a `condition_identity`
    that makes "two LOCAL conditions sharing a name in different DCs are DISTINCT"
    executable) — and `drydocs_core/orchestration/controlm/resource_pool.py` arrived as
    MECHANISM-here / VOCABULARY-yours. Three consequences for you: your
    `controlm_xml_adapter.py` is company-canonical and is NOT a back-flow target; the
    `JOBISN=1` folder pseudo-job stays a deliberate producer gap with a trigger; and a
    PORT-MANIFEST row that had pointed at `drydocs_core/controlm/**` since the S2
    relocate is corrected to `orchestration/**` — which means the whole package was
    silently evaluate-on-collision rather than canonical-producer, on both sides, for
    as long as that row was wrong. Re-derive your dispositions for that package rather
    than trusting the previous port's outcome. ONE DELIBERATE DIVERGENCE from your
    code, stated so it does not read as a porting error: your `_ts` DOCUMENTS returning
    None for an unparseable value but falls through to returning its input; the
    producer version implements the documented promise and preserves the Oracle
    pass-through by matching the ISO-ish shape explicitly.

134. TRUNK REPAIR — READ THIS BEFORE CUTTING ANY RANGE THAT SPANS IT [TEST-PINNED]
    (`ffc29b6`, `d05811a`). `docs/restructure/backlog.yaml` on producer `main` briefly
    DID NOT PARSE: a concurrent two-machine push committed conflict markers
    (`<<<<<<< Updated upstream` / `>>>>>>> Stashed changes`) into the summary block,
    and the same push allocated G70–G74 over two ids the other machine had already
    pushed, so the file carried two different G70 and two different G71. Both repaired
    here — counts RECOMPUTED from items rather than merged textually, and the
    DESKTOP pair renumbered to G75/G76 because `config/gate-log.md` cites G73/G74
    inside a SIGNED-OFF gate record and a sign-off citation must not be falsified to
    settle a numbering clash. WHY IT MATTERS TO YOU: a base cut anywhere inside
    `9268f94..ffc29b6` lands mid-repair and inherits an unparseable backlog. The
    certified `port-base-*` tag exists precisely to make that impossible — take the
    tag, never a bare SHA or HEAD. `d05811a` inboxes the two guard gaps this exposed
    (no guard asserts a PORT-MANIFEST path exists; the override-ordering check knows
    only four hardcoded rows), now groomed as J47.

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
  Likewise four `test_port_reconcile_guards` failures naming a before-dir mean a
  stale `RECONCILE_BEFORE_DIR` is still set in that shell from an earlier reconcile
  — clear it (reconcile-port step 4) and re-run; that is the guard WORKING too, not
  a port failure.
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
````
