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
1. Write the PORT-REPORT (guardrail 8) with every producer-tree citation SHA-stamped,
   and INCLUDE THE BACKLOG UNION BLOCK (J42): `poetry run python
   scripts/port_backlog_union.py --producer-ref port-base-YYYYMMDD`, run company-side
   after the apply, diffs the producer base's backlog item-id set against the applied
   tree and FAILS naming every dropped id. The manifest has promised "never drop a
   file" for `docs/restructure/backlog/items/*.yaml` all along while every backlog
   guard read only ONE copy, so an under-delivering port left both sides green.
   Exit 2 (a side unreadable) is a FAILURE, never "no difference" — the tombstone
   `docs/restructure/backlog.yaml` carries no `items` key, so a check aimed there
   would compare two empty sets and pass for being wrong. UNION half only; status
   regression stays with the J16 reconcile guard.
   **BASIS — this sub-step applies only to a range that CONTAINS the script.**
   `scripts/port_backlog_union.py` lands at `35e6d103`, which is AFTER
   `port-base-20260820`: a session applying `7c18ff4b..port-base-20260820` does not
   have it and must not be held up looking for it. For that one port the shard
   sequence's own **`PROOF OK`** (hand-prompt step 3) is the item-integrity check —
   quote that line in the PORT-REPORT where the union block would go. Hand-carrying
   the script is not a substitute: the backlog tree is each side's own output.
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
performs all seven and refuses to certify on any failure:
1. **Suite green** on the exact commit offered, **venue-stamped (J18)**.
2. **Ledger rolled** through that commit, coverage verified COMMIT-BY-COMMIT.
3. **Every producer action triggered by company state is landed** — anything the
   company would otherwise have to do to a `canonical-producer` file. This is the one
   that failed: the plan asked the company to edit `PORT-MANIFEST.yaml`, which its own
   apply phase takes wholesale, so the edit would have been reverted in the same session.
4. **Renders current** (re-render, then `git diff --quiet`).
5. **Relay basis tags** present on every live relay (see the RELAY section).
6. **Cited paths resolve** in every document the range ADDS (2026-08-12). A merge
   validates text overlap, never whether the prose still describes the tree: a doc
   branch idle since 07-21 merged clean on 08-12 with two brand marks still listed
   under *Approved / canonical* that main had deleted as rejected on 07-28. Docs
   under `tests/unit/test_runbook_currency.py` are skipped (that guard resolves them
   inside check 1, and one defect reported twice reads as two); a document whose
   header declares `status: DATED RECORD` exempts itself, which is how a record gets
   kept without pretending its paths are current.
7. **Base tagged `port-base-YYYYMMDD` and pushed.**

**AND ONE THAT REPORTS RATHER THAN REFUSES - THE SPLIT-PAIR CHECK (PORT12, 2026-09-10).**
`python scripts/port_split_pair_check.py <previous-base-tag>` names every SPLIT PAIR in
the range: a definition the range adds to a file the consumer reconciles BY HAND, and a
reference the same range adds to it from a file that crosses unattended. Deliberately
NOT one of the seven, and deliberately not inside `--tag`'s refusal set: a split commit
is legitimate, the dispositions behind it are right, and what it owes is a RELAY LINE,
not a blocked roll. Its verdict line goes in the PORT-REPORT beside the completeness
check's, and each pair becomes a line in the roll's relay so the consumer knows which
definitions their hand-merge has to carry.
Born from G130 (`01761011`, 2026-08-30), which added `constraints_detail` to
`drydocs_core/neo4j_client.py` and a call to it in `drydocs/cli_schema.py` in one
commit. The caller is canonical-producer and crossed wholesale; the method's path falls
to the manifest default, evaluate-on-collision for a file both sides authored, so it
waited on a hand-merge. The consumer took the caller, the sixteen lines did not arrive,
and `drydocs bootstrap` raised `AttributeError` ten days later. There was no earlier
signal available: an uncalled missing method raises nothing until it is called, and the
completeness check could not see it because every path involved is present on BOTH
sides. Three outcomes, never silence: pairs found, clean over a named range, or NOT
CHECKED with the revision that would not resolve (exit 2).

**THE BASE IS A TAG, NOT `HEAD` (J41).** The company still fetches fresh — never a
cached ref, the 2026-08-05 lesson stands — but ports `<last-ported>..port-base-YYYYMMDD`,
not `..HEAD`. Producer `HEAD` moves while a session reads it: on 2026-08-09 the base
moved 42 → 45 commits mid-hold and every prompt had to carry an awkward "verify, the
producer is still committing". A tag is immutable and certified; if HEAD has moved past
it, those commits ride the NEXT port, which is normal rather than a discrepancy.

**A ROLL NAMES ITS RED COMMITS (J77, 2026-09-08).** Wherever a roll describes a
commit range (the `LEDGER ROLLED` note, a roll relay, a `PORT-REPORT`), one sentence
names the commits inside the range that were RED at push - CI failed at that sha, or
the sha was never verified - or states that none were, written by the session that made
them, the way the session that re-mints ids names the range it re-minted. The reason is
`git bisect`: a red commit inside the range is one bisect will land on and misattribute,
and the consumer's range is exactly the one that crosses it. This is a CONVENTION, NOT A
GUARD, on purpose: a guard written red first and turned green in the same commit is
normal practice here (J68 was written that way), so the fact that matters - was it green
by the time the range closed - is one only the author knows. What mostly neutralizes it:
`--no-ff` merges keep a branch's red commits off `main`'s first-parent line, so
`git bisect --first-parent` never visits them; the exposure that remains is bisecting the
branch itself, or a range that crosses the merge boundary, which a port range does. Starts
forward with the eighth roll; the rolls before it carry no such line and none is added.
Observed on `feat/ui-web` (2026-09-01): `e7e95f07` and `f44fb40d` red on
`test_ui_components`, `e0c12d10` the green tip.

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

**Roll state (2026-08-17, the post-`caa0406` roll).** The ledger is rolled through
the certified tag **`port-base-20260811` (`caa0406`)**. Steps **124-134 are
DELIVERED AND PRODUCER-REVIEWED** — PORT-REPORT-caa0406 exists and was reviewed at
`ca7a121` (four divergences ledgered, RELAY-7 raised) — but **no close-out
confirmation ever reached this file**, so unlike `ae21ee4` there is no "IS MERGED,
branch removed" line below. Treat 124-134 as delivered, NOT as closed. Live ledger
restarts at **135+**, delta since `caa0406` — **115 commits: 93 cited across steps
135-157, 22 ritual.** This roll certifies a NEW base, tagged **`port-base-20260817`** at the roll
commit itself (`python scripts/port_preflight.py --base caa0406 --tag`).

**LEDGER EXTENDED 2026-08-19 (desktop, pre-K17) — NOT a base certification.**
Steps **158-170** cover the **116-commit delta `port-base-20260817..a4e65d26`**,
verified commit-by-commit: every non-ritual commit is cited in exactly one step,
ritual commits (grooms, claims, renders, snapshots, PR merge commits, handoff
rolls) fall under the standing exemption; the four `docs(port):` commits
(`9dda538e` RELAY-10, `be0c39ae` RELAY-11, `7c6eb730` its first rider,
`991d59e6` RIDER 2) are SELF-DOCUMENTING — their payload IS the relay text in
this file's relay section, cited there rather than in a step; and step 170 is a
DELIBERATE
RESERVATION — DISCHARGED 2026-08-19 evening: K17 SIGNED 33/33 and step 170 is
restated with the outcome (steps extended through `337d6a6f` + the gate
commits). **CERTIFIED 2026-08-19 evening: `port-base-20260819` @ `7c18ff4b`,
preflight 7/7 green (tree clean, relay basis tags, ledger coverage 131/131
cited-or-ritual, cited paths resolve, renders current, suite 2224/5 venue MSI,
tag pushed).** Steps 135-170 are ONE offerable range: `caa0406..port-base-20260819`.
A company plan drafted against the pre-certification wording of this paragraph
("158-170 ride the next port") is superseded — take the whole range in one port.
Ritual/self-referential commits cited for the coverage check, none carrying
apply-content: `30e2b9bb` `e0ae9bab` `3643c36f` (the Q9/Q10/Q11 batch-claim,
close and next_ready backlog flips — the work itself is step 165), `8c84adef`
(the PR #7 merge — content at step 161), `f21b3e3a` `6e7735bd` `f1d777bc`
(summary-block merge resolutions, recompute-from-items each time), `3680e9a3`,
`04f92515` and `c82648d7` (this roll, its step-170 restatement, and the
coverage-line addendum — the roll write itself terminates via the script's
chore(port): roll exemption).
**CI NOTE:** the Actions billing block that made everything in this range
local-run-evidence-only is RESOLVED — `main` is green at HEAD (the K17 sign-off
and both commits after it all passed). Earlier acceptance claims in this range
remain local-run statements as written; from here CI corroborates.

**LEDGER ROLLED 2026-08-25 — THIS ROLL EXTENDS THE 2026-08-24 SERIES; PORT THE LONGEST
RANGE, `213e1d12..port-base-20260825`.** Steps **221-227** cover the extension
`dd71116e..HEAD` (ADR 0014 accepted with amendments, G105 log-kinds + dictConfig, G107
batch run logs, R23 with both machines' stores accounted for, the escalation-census
relay, the alias sanitization + Scan D, and the C27 CatalogSubLOB ruling). Certification
figures are stated AT THE TAG by `port_preflight.py` — venue (J18): desktop. **Two steps
in this extension need reading before the apply is planned: 226 (Scan D fails on your
alias ids until your `[db]` revert — sequencing is yours, make it deliberate) and 223
(the legacy log env var's deprecation drop trigger is THIS port).** The range's hand prompt (`catalog-sublob-and-db-alias-company-prompt.md`, under
docs/company-prompts/ AT THE TAG) was DELIVERED BY HAND and executed company-side
2026-08-25 (the Option 1 relabel ran the same day), then retired producer-side per the
manifest's delivery-pack rule -- the deletion rides the NEXT range; your copy arrives
with THIS apply and is yours to retire at close-out. Steps 221-227 carry per-step APPLY
notes as usual, and step 226's Scan D sequencing instruction stands on its own below. If your apply is already in flight against
`port-base-20260824c`, finish it and take `port-base-20260824c..port-base-20260825` as
the next range — do not re-target mid-apply.

**LEDGER ROLLED AND RE-CERTIFIED 2026-08-24 — THIS ROLL REPLACES THE 2026-08-20 ONE AND
BOTH EARLIER 2026-08-24 ONES.** Steps **178-220** cover the **208-commit delta
`213e1d12..port-base-20260824c`**, verified commit-by-commit by `port_preflight.py`.
**CERTIFIED 7/7** (tree clean, relay basis tags, ledger coverage 208/208
cited-or-ritual, cited paths resolve, renders current, suite **2385 passed /
9 skipped**, tag pushed). **Venue (J18): laptop `NewThinkpad`**, and the skip
composition is stated rather than summarised — 6 reconcile guards with
`RECONCILE_BEFORE_DIR` unset, 3 with the production sample CSV ABSENT (gitignored, so
absent in any fresh clone). Your figure is not comparable to this one and never was.

**WHY THERE ARE THREE TAGS FOR ONE DAY, AND WHICH ONE TO PORT. Port
`213e1d12..port-base-20260824c`.** All three certified 7/7 against the same base; each
later one is the earlier one plus commits, so there is nothing to choose between them
beyond taking the longest.
- **`port-base-20260824`** (`68b53716`, 182 commits, steps 178-213) — the morning base.
  Certified cleanly, never applied, overtaken.
- **`port-base-20260824b`** (`68b1c03b`, 205 commits, steps 178-220) — producer HEAD had
  moved 22 commits past the morning tag while the range sat unapplied, so rather than
  leave those to an immediate third wave they were ledgered as steps 214-220 plus a
  second coverage footnote.
- **`port-base-20260824c`** (208 commits, same steps) — a ledger ACCURACY repair, no new
  payload: step 219 as first written described a `data_root.py` resolver derivation that
  G109 does not contain (G81 had already done that, and G109 records it as overtaken),
  and step 216 named the driver script instead of the module that holds the fix. Both
  now match the commits. Superseding a certified tag for a wrong STEP is the cheaper
  half of the J41 bargain — the alternative is a company session planning an apply
  around a change it will not find.

None of 214-220 changes behaviour, so the five "read this first" steps below are
unchanged. **If your apply is already IN FLIGHT against an earlier tag, finish it and
take the remainder as the next range; do not re-target mid-apply.**
`git log port-base-20260824..port-base-20260824c` shows exactly what grew.

**A COUNT MEASURED BEFORE THE ROLL COMMIT IS WRONG BY THE ROLL COMMIT — the first
2026-08-24 roll learned this the expensive way, and the lesson is kept rather than the
arithmetic.** That roll wrote 179; CI then failed it on ONE citation,
`docs/reviews/port-review-7c18ff4b-20260820.md`, which `103f240c` untracked but which
was still on the producer laptop's disk — so the currency guard, which asks the
FILESYSTEM rather than git, passed locally and failed in a fresh clone. The repair and
its coverage addendum put the real figure at 182, at a tag two commits past the roll
commit. Both numbers were honestly measured; only one was measured last. So the figures
above are measured AT THE TAG, and
`git rev-list --count 213e1d12..port-base-20260824c` is the check that settles it. This
repo has already spent one follow-up condition on a 478-vs-479 mismatch.

**PRECONDITION — the `7c18ff4b..port-base-20260820` port must be MERGED and closed
out before this range starts.** That range carried step 175, the backlog shard, which
has its own apply sequence; a mid-apply range finishes on the monolith and this one
begins after it. Steps 171-176 stay live below for exactly that reason.

**WHAT IS DIFFERENT ABOUT THIS RANGE, in one paragraph.** It is large (208 commits,
five days) and three steps change BEHAVIOUR rather than content: **195** splits
`cli.py` into six modules and is the biggest hand-merge here, **209** removes the
`refresh-reference` command by name, and **210** makes `DRYDOCS_DATA_ROOT` mandatory
so the first data-path command after the port exits 2 until it is exported. **188**
migrates vocabulary ids you may hold and ships two `.cypher` migrations that must run
against your graph. **212** deletes a file from the producer tree that you may have
taken at the last port — an untracking, not a retraction. Read those five before you
plan the apply; the rest applies by the manifest as usual.

**COMPANY CLOSE-OUT OF THE `port-base-20260820` PORT: REPORTED COMPLETE, FIELDS NOT
YET RECEIVED (2026-08-24, USER-REPORTED).** The user states the internal port is
complete. That is a dated report, not the J35 record: the four required fields —
applied RANGE with its `rev-list --count`, the PORT COMMIT(s), the BACKUP TAG with
its `rev-list --count <tag>..HEAD` proof, and the ACCEPTANCE NUMBERS — have not
reached this file. Per the standing rule, no producer-side figure may stand in for a
company acceptance number, so nothing is filled in from this side. **First action at
the next port: fill them from the company PORT-REPORT.** The `caa0406` block below
records what an unfilled close-out costs, and it is the reason this paragraph exists
rather than a checkmark.

> **THE `caa0406` PORT'S CLOSE-OUT IS UNRECORDED — ask before assuming it landed.**
> `ae21ee4` got an explicit `06d4469` "MERGED company-side, branch removed" commit.
> `caa0406` got a report, a producer review, and then nothing. The producer cannot
> see that repo, so this is a GAP IN THE RECORD, not evidence the port failed — but
> two things ride on closing it. RELAY-7 (re-pose the `email-dl-contact-point` §G4
> clause, which now asks a question the `5405ab6` DOMAIL ruling already answered) is
> owed company-side and unconfirmed. And the four divergences at `ca7a121` —
> `resource_pool` split, `description_tokens` UNION, `detect.py` shared-`Finding`
> namespaces, `test_runbook_currency` deferred — are producer BELIEFS about company
> state until somebody re-checks them. This is the T11 class: a fact whose only home
> was a chat stops existing when the chat does. **First action at the next port:
> fill the three UNRECORDED fields below.**

**Last CONFIRMED-COMPLETE port — the four required fields (J35).** Still the
`ae21ee4` port, because `caa0406`'s close-out never reached this file (block above).
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

**Last DELIVERED port — `caa0406`, close-out UNRECORDED.** Range
`ae21ee4..caa0406` (= tag `port-base-20260811`), ledger steps 124-134; report
**PORT-REPORT-caa0406**; producer review `ca7a121` (2026-08-11). Port commit, backup
tag and company acceptance figures never reached the producer — the `1946 passed / 5
skipped` in that review commit is the PRODUCER's own tree, never a company number.
Do not quote it as an acceptance figure.

**Steps 124-134 stay live below rather than collapsing** — a step collapses once its
range is confirmed merged, and this one is not. Collapsing them would retire the only
producer-side description of work whose landing nobody has verified. They collapse at
the roll after `caa0406` is confirmed.

(Steps 106-123 collapsed AT THIS ROLL — the `5417ef10..ae21ee4` range, merged
company-side per step 128 and confirmed at `06d4469`. One-liners live in
PORT-REPORT-5417ef10, PORT-REPORT-ae21ee4 and this file's git history, along with the
FORCE_COLOR / Idea-101 findings that motivated J41.)

## Last completed port

> **FETCH RESOLVED (2026-08-06) — the 2026-08-05 blocker is CLOSED.** SME confirms
> producer fetch works company-side, so guardrail 1 is executable again: read at producer
> **HEAD**, not at the ref you last fetched. The prior failure was access (the repo was
> `PRIVATE` and healthy throughout), and its lesson stands rather than expires — a failed
> fetch degraded silently into answering from a cached `5f79d145`, which reads exactly like
> a current answer. **If fetch fails again, STOP and say so; do not fall back to a cached
> ref.** That fallback is the one failure guardrail 1 exists to prevent, and it cost a
> cycle of "the producer tracker says…" answers that were two days stale.

- **Producer base `port-base-20260910b` (`6da347ae`), the TENTH roll — CERTIFIED 2026-09-10,
  venue desktop (MSI). A same-day RE-ROLL, cut before the ninth was applied, and the reason is
  the whole point of it.** Range `port-base-20260910..port-base-20260910b` = 11 commits, steps
  387–388. All eight preflight checks green, CI green at the sha before the tag was cut, and the
  split-pair check reports CHECKED CLEAN over the range.
  **WHY IT EXISTS:** `CLAUDE.md` §2 routed every Neo4j task to a Claude Code PLUGIN, which loads
  in no venue without a plugin loader — it resolves to nothing, with no error and no lens. A
  company-side session hit exactly that, diagnosed it correctly, and began repairing it on FIVE
  canonical-producer paths. Applying the ninth roll would therefore have reverted their work AND
  reinstated the dead route: a regression, not a fix. Rolling again before the apply costs one
  preflight. Step 387 is the producer-side repair — a filesystem `neo4j-db` skill that loads
  everywhere, five pre-existing dead plugin routes swept, four `apoc.cypher.runMany` claims that
  had been wrong for eight weeks, a server-version fact that would have crossed wrong, seven dead
  local-mirror citations, and `reference/**` brought under the currency guard that ADR 0018 D5
  never extended to it.
  **THE NINTH ROLL'S STEPS 368–386 STAND UNCHANGED** — this range only adds — so the consumer
  still applies ONE range, now **`port-base-20260908..port-base-20260910b` = 330 commits / 459
  changed paths**, with the eighth, ninth and tenth rolls inside it and nothing parked or
  hand-carried. The three live relays (55, 56, 57 with its first roll-close postscript) are
  unchanged and all act in it. The seventh roll's apply stays IN PROGRESS; no company figure is
  claimed here. **NEXT-PORT BASE: `port-base-20260910b`.**

- **Producer base `port-base-20260910` (`bb73c182`), the NINTH roll — CERTIFIED 2026-09-10,
  venue desktop (MSI).** Range `port-base-20260909..port-base-20260910` = 144 commits, 228
  changed paths in 8 classes, steps 368–386. All eight preflight checks green at the tag,
  including the suite (4199 passed / 16 skipped) and CI green at `bb73c182` before it was cut.
  **THE EIGHTH ROLL (`port-base-20260909`, 175 commits, steps 354–367) WAS NEVER APPLIED**, so
  the two are ONE RANGE for the consumer exactly as the fourth and fifth were: the next apply
  is `port-base-20260908..port-base-20260910` = **319 commits / 447 changed paths**, and
  nothing is parked or hand-carried between them. Three relays act in it — RELAY-55 (a gate-log
  redaction declares whose act it was, so the consumer may keep the true name), RELAY-56 (the
  one-method `constraints_detail` fix for the bootstrap `AttributeError`) and RELAY-57 with its
  first roll-close postscript. **RELAY-57 IS WHY THIS ROLL WENT OUT WHEN IT DID**: three of its
  split pairs had not shipped, and the worst of them puts a module-scope import in
  canonical-producer `drydocs/cli_docs.py` against constants in a file the consumer
  hand-merges — an `ImportError` while `drydocs/cli.py` is still importing, which kills every
  command including `drydocs --help`. This roll carries both halves, so it PREVENTS that break
  rather than reporting it afterwards. The seventh roll's apply stays IN PROGRESS and its
  close-out is answered by `docs/company-prompts/port-base-20260908-premerge-company-prompt.md`;
  no company figure is claimed here. **NEXT-PORT BASE: `port-base-20260910`.**
- **Producer base `port-base-20260908` (`314b1715`)**, the seventh roll, range
  `port-base-20260905..port-base-20260908` = 407 commits / 493 changed paths. Company apply
  REPORTED IN PROGRESS `[SME-REPORTED]`: Phases 0 and 1 and the Phase 3 corrections are read in
  the SECOND POSTSCRIPT TO RELAY-46; no close-out has been reported, so the J35 four fields are
  NOT here - no producer figure stands in for a company acceptance number. Re-certified on the
  fixed preflight 2026-09-09 (THIRD POSTSCRIPT TO RELAY-46): base resolves, 407 commits, 0
  uncited, 10 added documents, 0 unresolved. **NEXT-PORT BASE: `port-base-20260909`** - the
  eighth roll, `port-base-20260908..port-base-20260909`, 172 commits, steps 354–367,
  RELAY-53.
- **Producer base `port-base-20260905` (`5cad5653`)**, reported applied company-side as
  **PORT-REPORT-port-base-20260905** (2026-09-08) — range
  `port-base-20260902..port-base-20260905` = **186 commits / 323 changed paths, REPORTED
  COMPLETE at company `main` `d527afce`** — `[SME-REPORTED]` end to end, no producer
  figure in this bullet: branch `port/20260905` cut from company `bc4d63e3` (backup tag
  `pre-cewilson-port-20260905`), carve-outs A `941e553e`, B `2b2a1235`, C `df996636`, C2
  `beb5cadf`, D `c1f09f8d`, E `066c96f9`, G `8e5f4a5d`, I `b9bc042c`, H `fe21d49c` (no F),
  the RELAY-35 owed-path sweep `825235ba` (87 owed, 82 from a roll that had closed
  COMPLETE), measured tree `f8c2233c`, then `25bace48` (the `--no-ff` merge, 22 commits),
  `b485ab72` (ruff sweep), `d1451fe5` (N19 YAML) and the close-out `d527afce`. Acceptance by
  test id, as the restated gate asks: 61 failing = 2 deliberate regressions awaiting ruling
  + 20 pre-existing + 38 new tests + 1 unskipped, the 38 not yet itemized (RELAY-45 §Five's
  condition stays open). Company CI has never run on that remote. Transcribed in the
  POSTSCRIPT and SECOND POSTSCRIPT to RELAY-45; answered by the hand prompt
  `docs/company-prompts/port-base-20260905-closeout-company-prompt.md`. **NEXT-PORT BASE:
  `port-base-20260908`** — the seventh roll, `port-base-20260905..port-base-20260908`, 407
  commits / 493 changed paths, steps 334–353, RELAY-46; the one ruling owed from this side
  (a §3 redaction against the line-based append-only guard, RELAY-46) lands as a rider, not
  in the base.
- **Producer base `port-base-20260902` (`df0b0437`)**, applied company-side as
  **PORT-REPORT-port-base-20260902** (2026-09-05) — range
  `port-base-20260826..port-base-20260902` = **433 commits / 738 changed paths, COMPLETE
  at company `main` `4d9ddba7`**, applied in nine carve-outs (6 `d9bd3a6d`, 7 `d110acd1`,
  the 09-05 renumber `2961720f`, 8 `71f181fe`, 9 `a23204fd`, 8-tail `4d9ddba7`; the
  earlier five closed chunks 0–3 and 4). Acceptance by SET-COMPARE, not count: 21
  failures on the branch against 21 at the company's own main, identical sets, the one
  order-dependent test named. The report was reviewed producer-side on 2026-09-05
  (EIGHTEENTH POSTSCRIPT: one SME finding accepted — the ui-components hold retired; two
  producer claims withdrawn — `internal/**` crosses, it never PUBLISHES; the company's
  three apply mistakes are now reconcile-port skill rules). **NEXT-PORT BASE:
  `port-base-20260905`** — the sixth roll, `port-base-20260902..port-base-20260905`, 186
  commits / 323 changed paths, steps 313–333, RELAY-26; Lane B's three in-flight `wip/`
  branches (API1, WEB3, WEB4) land in the range after this one. **REPORTED APPLIED
  COMPLETE company-side at `d527afce` (2026-09-08)** as
  **PORT-REPORT-port-base-20260905** — `[SME-REPORTED]`, transcribed in the POSTSCRIPT TO
  RELAY-45, not producer-verified: the counts and shas are the close-out's, this side has
  read none of them, and RELAY-45 §Five's condition on that COMPLETE (the 38 "new tests
  failing" bucket named by test id) is still open. Nothing here is a producer figure. That
  COMPLETE was closed carrying one red the company has since re-diagnosed as its own
  placement, not a guard defect (SECOND POSTSCRIPT to RELAY-45) - the guard it was read
  against is `aef8dfcb^`, superseded here and landing next roll.
- **Producer base `port-base-20260826` (`9ef606b4`)**, applied company-side as
  **PORT-REPORT-e33f8d02** (2026-08-26) — range
  `port-base-20260825..port-base-20260826` = **44 commits / 46 files
  (+4,967/−297), PRODUCER-VERIFIED 2026-08-26** (rev-list count matches; item
  count 519 matches; report reviewed producer-side pre-push, verdict sound).
  Port commit `e33f8d02` direct on company `main` (block of 3: `afe25946` the
  prior 20260825 report + backup tag, `e33f8d02` payload, `f38999b7` report +
  last-completed-port roll); backup tag `pre-cewilson-port-20260826` @
  `afe25946`; **PUSHED** (company `origin/main` at `0155475c` after the
  same-day G70 adoption block). Acceptance: Track-1 **123/3/0**; J42 backlog
  union **PASS** (producer 519 / consumer 529, none missing); full suite
  **2610 passed / 55 failed / 76 skipped** with **zero true regressions** vs
  `afe25946` — all 55 are the documented deferred-feature clusters, one fewer
  than the prior port. Strategy: continue-defer (SME-chosen) — ontology +
  lineage + G68/G69 clusters stay company-divergent with the three hand-carried
  adoption dossiers as the path; the G70 adoption slice began the SAME DAY
  company-side (6 commits: register reconciled with three SME rulings, wiring
  blockers cleared, drift guard authored — see the tom-role-vocabulary
  divergence-ledger entry and its 2026-08-27 manifest row). New divergences
  from the report: the `detect.py` union (dossier 1) and the `run_as_detect.py`
  ASCII fix (already ENDED producer-side, `64ec0e7e`).

  **NEXT-PORT BASE — CURRENT AS OF 2026-09-01, and it supersedes the
  `port-base-20260826` pointer this entry originally carried.** Two bases have
  been certified since this port was applied and NEITHER has been applied
  company-side, so they are ONE range for you, not two ports:
  `port-base-20260829` (`e8e69a77`, steps 241–272) and **`port-base-20260901`
  (cut at the commit carrying the fourth roll, steps 273–296)**. Take the whole
  span `port-base-20260826..port-base-20260901` — **296 producer commits, 167 in
  the first roll and 129 in the second** — and read step 272 FIRST: the nineteen-id re-mint is in the earlier half and a naive
  union of the range re-introduces exactly the collisions it resolves.

- **PRIOR — producer head `5417ef10`** (2026-08-07), applied company-side as
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
  above the docs/company-prompts/** never-port glob; REMOVE those five rows
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
  `docs/company-prompts/port-fix-a14a8028-company-prompt.md`):** branch `drydocs-port-20260806` at
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
  94 C24 sparse-refresh blanking fix. 95 W1–W3 + cdo-crosswalk gate SIGNED 13/13.
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
   TWO CITED DOCS ARE NOT IN YOUR TREE (both docs/port/** = never-port). Read them
   at the fetched producer ref, same idiom as above:
   - `...:docs/port/port-prompt-archive-steps-1-42.md` — resolves every "archive step N"
     citation, and holds the Done-means for T1–T10, which appear nowhere else.
   - `...:docs/company-prompts/port-ais-supplement-company-prompt.md` — the T17 pack. NOT part of any
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

   REVIEW PROVENANCE, ON THE PRODUCER SIDE (J63) — stated here as a DESCRIPTION OF
   OUR PRACTICE and not as a request for anything back. Producer review, triage and
   research surfaces now name the tree they were read against: commit, branch and
   port base (`docs/style/review-provenance.md`). The reason is measured on our own
   side, three times: a review run against an un-ported checkout reports absences as
   DEFECTS when they are simply not-yet-ported, and reading the importable object
   faithfully still reports a stale tree faithfully, so no method rule closes it.
   Nothing about this binds the company side, and a company-side artifact arriving
   without a stamp is read exactly as it always was. It is written down because it
   explains why producer documents suddenly carry a SHA line, not because anything
   is owed.

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
  including the `internal/**` data corpora and `docs/design/ui-exploration/**`. `git reset --hard` leaves
  untracked files alone; `git clean -fd` destroys them with NO reflog recovery.
  **This rule has been here since J22 and the extracts were deleted anyway**, so treat
  it as a reminder attached to a control, not as the control. The mechanics that make
  it enforceable:
  - **`.gitignore` is NOT protection.** `git clean -fd` takes untracked, non-ignored
    files; `git clean -fdx` takes untracked files *including ignored ones*. A source
    payload can never be tracked (PUBLISH-BOUNDARY.md), so in-tree it is always in one
    of those two buckets. Whether a given CSV survived a past sweep was down to whether
    it happened to be ignored and whether that sweep carried `-x` — luck, not design.
  - **Run `drydocs landing-zones --check` before AND after any port step that touches
    the working tree.** It resolves every `acquisition.mode: manual` row in
    `config/source-registry.yaml` and reports what is actually in each zone. `absent`
    is the healthy first state of a source nobody has dropped into yet — **and, stated
    plainly because the first draft of this bullet got it wrong, it is ALSO what a
    `git clean -fd` leaves behind**: `-d` removes the untracked directory itself, so a
    swept zone and a never-used zone look identical without a baseline. `--check` does
    not fail on `absent` for that reason. **`EMPTY` — the folder present, its contents
    gone — is the narrower signature** (a selective delete, a half-finished restore),
    and `--check` exits 1 on it. So treat the doctor as the weaker half of this control:
    it catches the partial case now instead of at the next load, and the bullet below is
    what actually removes the broad one.
  - **The real fix is location, and it is declared:** `acquisition.drop_dir_base`
    states whether a zone is rooted at `DRYDOCS_DATA_ROOT` (outside the tree, where no
    git operation of any strength can reach it) or at the repo (permitted only when the
    contents are TRACKED artifacts, which survive every clean).
    `tests/unit/test_landing_zones.py` enforces both halves, so a new manual source
    cannot quietly declare an untracked in-tree corpus as its landing zone.
  - **Company-side action if a zone reads `EMPTY`, or reads `absent` where you know you
    dropped files:** the payload is not in the reflog and
    `git clean` writes no log. Re-export from the source system, or recover from the
    internal twin — then re-run `--check` to confirm the zone is green before loading.
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
- **DOCMETA DIVERGENCE — RECONCILE DECISION RECORDED (J40, 2026-08-26), three parts,
  all standing until the company's docmeta ADOPTION PASS (the e1ce510b port deferred the
  docs-verify/docmeta cluster as a coherent whole, so that pass is the named trigger).**
  (a) THE ADR NUMBER COLLISION IS PERMANENT AND HARMLESS ONCE NAMED: the company carries
  its docmeta ADR at **0005** while the producer's 0005 is the browser-to-Neo4j access
  path and its docmeta ADR is **0006**. RULED: each side's numbering is canonical IN ITS
  OWN REPO and nothing is ever renumbered (ids are join keys — the G87 rule); a reader of
  either repo learns the mapping HERE and from the docs/decisions/** manifest row, which
  now says it. Cross-repo ADR citations must therefore cite by TITLE + side, never by
  bare number.
  (b) THE PACKAGE PATH IS DELIBERATELY DIVERGENT, WITH A CONVERGENCE TARGET: company
  `drydocs/docmeta/` (drydocs.docmeta) vs producer top-level `drydocs_docmeta/`. The
  producer layout is the convergence target because the module-boundary guard
  (tests/unit/test_module_boundary.py) enforces components as top-level packages —
  `drydocs.docmeta` nests a component inside the CLI package, which ADR 0002-A's
  invariant forbids — and the producer package was AUTHORED against the described shape,
  never copied (T21, discharged 2026-08-04). Convergence happens AT the docmeta adoption
  pass, not before: a rename mid-divergence would collide with the deferred cluster.
  (c) `prompts.py` AND `pipeline.py` ARE BACK-FLOW CANDIDATES, not company-only-forever:
  both are company capability the producer's Q6 authoring deliberately did not include.
  They join the drydocs-review back-flow set (mechanism-only reproduction; no company
  values), and until that lands they are protected by the canonical-company rows below.
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

**A STRUCTURAL REFACTOR OF AN EVALUATE PATH IS A MANDATORY RELAY (J73, 2026-09-07).**
A commit whose subject begins `refactor(` and touches a path whose manifest disposition
is `evaluate` — an explicit `evaluate` row, or no row at all so the path falls to an
evaluate-on-collision default — gets a relay in this section at the roll that carries
it, written by the session that made the refactor, while it still knows why. The relay
names three things and no more: **the file**, **the new shape**, and **where your
content goes in that shape**. One paragraph. It is not a change log and not a merge
guide; the ledger step already holds the reasoning and the manifest row already holds
the merge rule. **What an evaluate note cannot say, and why this exists:** an evaluate
note tells you how to merge CONTENT, and no wording of it can say "the producer
changed the SHAPE of this file — take the shape and re-home your content". **The
case that wrote this rule:** S8 (2026-08-21, `f5e7229d`, subject `refactor(S8): split
cli.py (3184 lines) into a thin composition root + six per-domain command modules`)
shipped under a `drydocs/cli.py` row that read "composition root; both sides add
commands — merge per collision ledger". No relay was written. TWO ports walked past
it: the row was followed literally and producer verbs were merged INTO the consumer
monolith, twice, while the six modules it should have imported sat orphaned beside it
(RELAY-24 is the relay S8 should have carried, written twelve days late). **Scope:**
the trigger is the conjunction — `refactor(` subject AND evaluate path. A refactor of
a `canonical-producer` path needs none (you take the file whole; the shape comes with
it). A content change to an evaluate path needs none (the row already says how to
merge it). Nothing checks the trigger for you: `port_preflight.py` fails a live relay
without a basis tag, and does not know a refactor from a fix. That is deliberate —
the producer author is the one party who knows which of their commits changed a
shape, and whether to mechanise the trigger is a separate question, not proposed here.

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
  relaying the company's signed model, not by anything in this repo.
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
  **UPDATE 2026-08-23 (G79) — the rule is now DECLARED, not a position in a tuple.**
  The statement above was true and is now enforced. `REFRESH_REFERENCE_CHAIN` no longer
  exists: it split into `refresh-catalog` / `refresh-applications` / `refresh-teams`
  (`cli.CHAINS`), and the ordering rule rides that split as
  `cli.BUSINESS_APPLICATION_MINTERS` + `cli.APPLICATION_IDENTITY_LOADER` with a guard
  asserting the identity loader's command precedes every minter's in
  `CANONICAL_LOAD_SEQUENCE`. So the invariant survives a reorder instead of depending on
  one, which is exactly what a split threatened. **Nothing changes for the company
  side:** the fix is still company-owned, and producer still has neither the wrong order
  nor the collision — it is simply no longer luck that it does not.
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
  **Do NOT take the "the ontology is stale" exit.** `knowledge/org/technology-team-types.md`
  (relocated from docs/Product at S14, 2026-08-27)
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

- **RELAY-10 — THE SERVICENOW TOM-RESPONSIBILITY BUILD: the decisions your session
  took with the producer in-chat, written down so they outlive the chat**
  `[SME-REPORTED]` (raised 2026-08-18; the producer-side facts below are each marked
  where independently verified). Your session is building the sourced ServiceNow TOM
  loaders (the scoped-app `x_<scope>_cmdb_tom_main` / `_tom_roles` extension tables on
  the Snowflake replica, per the `snow` system row's ruled grammar). Seven artifacts,
  gate-bound, DO-NOT-RUN until the `snow-tom-responsibility` gate signs. These are the
  rulings that shaped them:
  **(1) ONE PERSON SPINE — `:Worker {sid}` was DROPPED for `:Employee`.** The draft
  minted a second person class; the SME's own finding killed it (`user_name` IS the
  SID, which is `:Employee`'s key — verified producer-side: `constraints.cypher`
  `employee_id` unique, `seal_applications.cypher` MERGEs on the SID). Two labels on
  one SID would have made "which roles does this person hold across PAT / SEAL / ITSM"
  unanswerable in one traversal. If `:Worker` survives anywhere in your tree, it is a
  residue of the draft, not a decision.
  **(2) THE THREE OPERATE-MANAGER ROLES ARE NEVER NORMALIZED** — SME instruction,
  2026-08-18. L1 Operate Manager / L2 Operate Manager / Operate Manager are THREE
  `:TOMRole` concepts; collapsing them was the coercion G35 fixed, and
  `Attribution.level` was retired as a discriminator. Match on the FULL role name;
  anything outside the confirmed set flags `unmapped_role=true`, never a stripped
  prefix. **DUAL CITATION ANCHORS, both real:** the producer gate-log carries a
  dedicated `2026-08-06` RECORD for this ruling; YOUR gate-log carries it inside the
  2026-08-11 G35 round-2/3 record (§G7/§G8/§G9) after your session removed its own
  duplicate. The two logs are never-port and independently maintained — a port review
  seeing different anchors for one ruling is correct, not a discrepancy.
  **(3) THE RESPONSIBILITY ROLE JOINS `:TOMRole`; `:SnowRole` IS A DIFFERENT
  REGISTER.** TOM responsibilities join the G35-ruled register (9 concepts), not a
  string and not a new scheme. `:SnowRole` (producer-registered, planned) stays for
  TECHNICIAN-GROUP support roles — the SENG/ASUP mapping — and is not in competition:
  "app has an L2 Operate Manager" and "this person is in the group as SENG" are
  different facts. Precedence across the three surfaces is G35 §D4, CITED not
  re-derived: hand-verified > ServiceNow TOM > SEAL extract.
  **(4) TWO NEW TRIPLES, DECLARED NOT REUSED** `[VERIFIED-PRODUCER]` (the C8 check:
  `schema_graph.py` refuses duplicate (from, label, to)). `Attribution -[HAS_AGENT]->
  :ServiceNowGroup` is a different to_node from the registered Employee triple, so it
  needs its own entry (yours: `snow_attribution_has_group_agent`); and if the gate
  lands the grain on `:LogicalDeployment`, that QUALIFIED_ATTRIBUTION triple is also
  new vs the registered `:BusinessApplication` one. **Producer naming divergence,
  yours to keep:** the producer's sibling family sits under `itsm_*` ids
  (`50-local-itsm.yaml`); your `snow_*` prefix is your registry's convention.
  `:LogicalDeployment` itself is company-only — producer registers `:Deployment`.
  **(5) THE ATTRIBUTION KEY carries SCOPE and AGENT** —
  `{anchor}|SNOW-TOM|{role_source_name}|{scope}|{agent_key}` — or a Group and an
  Individual responsibility for the same app+role collide on one node. Row-derived
  end to end (truncate-and-reload discipline). `{role_source_name}` over the
  crosswalked id is correct BY NECESSITY, do not "fix" it: an `unmapped_role=true`
  row has no id, so keying on crosswalk output would collide every unmapped role.
  **(6) UNRESOLVED AGENT IS A GATE CLAUSE, NOT A LOADER DEFAULT.** An OPTIONAL MATCH
  that misses leaves an Attribution with no HAS_AGENT edge — a silent orphan. Ruled:
  flag + count (`unresolved_agent=true`, surfaced in the load summary), the SME
  choosing at the gate, symmetric with `unmapped_role`.
  **RIDER 2026-08-18, same day — the SME refined the INDIVIDUAL half: STUB-AND-ENRICH.**
  "The HR database has ~300k; my expectation is that it will be the stub and
  supplemented with HR data later." So an Individual-scope miss does NOT leave an
  edge-less Attribution: MERGE the stub `:Employee {employee_id: <SID>}` and let the
  HR supplement enrich it — the `seal_applications.cypher` idiom, now ruled policy
  (producer gate-log RECORD 2026-08-18; G74 clause 2 owns harmonizing the runbook,
  whose "never a stub" phrasing LOST). `unresolved_agent` then means "agent is a
  stub pending HR enrichment", not "no agent". The GROUP half is different: an
  unloaded `:ServiceNowGroup` is load ORDER, not roster coverage — the direction
  does not cover it, so flag-or-sequence stays the gate's call there.

- **RELAY-11 — YOUR IDEAS.md IS MISSING THE Idea-50..75 BLOCK, and it was lost at
  the a14a8028 PORT MERGE** `[VERIFIED-PRODUCER]` (raised 2026-08-18, from your own
  report that the inbox numbering jumps 49 → 76). The block is REAL and LIVE
  producer-side — verified by enumeration, not assumption. What happened, dated:
  **`deeb808a` (2026-08-05) numbered the whole inbox IN PLACE** — "number the inbox,
  give every entry a status + priority, review all 69" — an EDIT of ~75 existing
  lines, not an append. That commit rode the `5f79d145..a14a8028` range applied as
  PORT-REPORT-a14a8028 (2026-08-06). IDEAS.md is `union-append` in the manifest and a
  proven conflict site (3x on 2026-07-09), and your copy is a known UNION-SUPERSET
  (it retains blocks the producer had already groomed — the acceptance-check note in
  this file says exactly that). An in-place sweep across a superset copy is the
  maximal conflict surface, and the middle of the inbox lost the producer side of the
  merge. Ideas 76+ appended cleanly at the top afterward, which is why your gap has
  clean edges.
  **THE REPAIR IS A TEXTUAL UNION FROM PRODUCER HEAD, not a replay of `deeb808a`** —
  three weeks of edits have moved entries since. Take the `Idea-50..75` entries from
  the producer's current `docs/restructure/IDEAS.md` (inbox + audit trail both) and
  re-insert them into yours, keeping your own entries untouched. **Idea-63 is NOT
  missing** — it was never minted (the sweep skipped it; `git log -S` finds nothing),
  so do not manufacture one.
  **BEFORE GROOMING ANY RECOVERED ENTRY, CHECK ITS STATUS LINE — the double-capture
  trap is live and Idea-59 is the proof.** Idea-59 (the FID directory ingest) was
  groomed producer-side on 2026-08-04 into **K16 + K17**: K16 is the FID census that
  is BLOCKED awaiting YOUR counts, and K17 is the fid-identity gate that
  rua-load-shapes §A1 and this file's step records repeatedly cite. Grooming Idea-59
  fresh on your side would mint duplicates of both and fork the K17 identity work the
  ports keep converging on. Producer-consumed in the block so far: 51, 52, 54, 55, 59
  (→ K16/K17), 73 (→ G74). The standing rule at the acceptance-check note applies:
  annotate recovered blocks "groomed producer-side → <ids>" rather than re-capturing.
  **ONE CHECK WORTH RUNNING YOUR SIDE:** the same merge that dropped the inbox middle
  may have clipped the AUDIT TRAIL region below it — after the union repair, diff
  your "Recently groomed" section against producer HEAD's and union that too.
  **RIDER 2026-08-18, same day:** SME direction — company-side grooming is PAUSED;
  the producer backlog is the active lane for now. So do not expect this repair to
  have been done by a company groom pass: **the union repair becomes NEXT-PORT-SESSION
  work**, performed with the port's IDEAS.md merge rather than waited on.
  **RIDER 2 — 2026-08-18, later the same day: THAT ENTRY IS NOW `Idea-135`, NOT
  `Idea-59`, AND THE RENUMBER IS WHAT MAKES THIS REPAIR SAFE FOR YOU.** The producer
  allocator bands landed after this relay was written (`IDEAS.md` header, "Allocator
  bands"): producer allocates **1-9999**, company **10000+**, and the one live
  cross-side collision was settled at the same time. Producer's `Idea-59` (the FID
  directory ingest, groomed → K16 + K17) **moved to `Idea-135`** — its capture date
  is unchanged at 2026-08-04, and it now sits in the audit trail, not the inbox.
  Producer's was the side that moved because yours is the cited one: your `Idea-59`
  is `snow_tom_responsibilities`, which your own grooming is citing right now.
  **What this changes about the union repair above:** the `Idea-50..75` block you
  pull from producer HEAD **no longer contains a 59** — do not read that gap as a
  second loss, and do not manufacture an entry to fill it (same rule as `Idea-63`).
  Take the FID entry from `Idea-135` in the audit trail instead. Everything else in
  the block is unchanged. Had the renumber NOT happened, this repair would have
  merged two different ideas into one number in a `union-append` file — which is the
  precise failure the bands exist to prevent, arriving one port later.
  **(7) STANDING TAIL:** `source_label: 'snowflake'` is a 13th value outside the
  declared `csv|oracle|agent|human` enum that 12 of 28 producer loaders already sit
  outside, unenforced — the re-sourcing pass is the moment to rule the field's
  meaning (producer Idea-132 carries it). And the wider extract re-sourcing
  (hand-pulled CSV/YAML → SQL over the replica) is Idea-132's subject; the producer's
  G100 technician-group lookup builds against the SOURCED feed for the same reason.

- **RELAY-12 — `DRYDOCS_DATA_ROOT` IS NOW MANDATORY, and one `drop_dir` was wrong
  since N12** `[VERIFIED-PRODUCER]` (raised 2026-08-24). **BASIS:** both changes ride
  the range AFTER `port-base-20260820` — G81 lands at `fcf973b5` — so they are NOT in
  the `7c18ff4b..port-base-20260820` port the backlog-shard hand prompt carries. Do
  not go looking for either in that range. Two things change for you when the range
  after it ports, and one of them is about the machine that had the incident.
  **(a) `DRYDOCS_DATA_ROOT` is MANDATORY — there is no `~/data/DryDocs` default.** The
  first data-path command after the port (`landing-zones`, a `--source` chain run,
  anything resolving a zone) exits 2 with a message naming the variable until it is
  exported. `drydocs --help` and the unit suite are unaffected. This is deliberate:
  the old silent fallback meant the same command in two shells targeted two different
  trees, which is a candidate mechanism for the 2026-08-11 overwrite. The console
  script moved to `drydocs.cli:run` so these render as exit 2 rather than a
  traceback — an existing install keeps the old shim until `poetry install`, which
  costs only error *rendering*, not behaviour.
  **(b) The `dpl:*` rows' `drop_dir` was corrected from `dpl/` to `dpl-registry/`.**
  The registry and `dpl_registry_dir()` had NEVER agreed, since N12. If anyone there
  followed the registry, **their Swagger exports are sitting in `dpl/` where nothing
  reads them** — worth a look before the corrected row makes `dpl-registry/` the only
  place anything checks. Producer took the code's path because that is what the G25
  flow actually reads; no data was moved on either side.
  **Full diagnosis** — the four measured overlaps and the ranked candidate mechanisms
  for the incident — is producer-machine-local (`docs/reviews/**` is gitignored as of
  `103f240c`); ask for it if you want the reasoning rather than the outcome.

- **RELAY-13 — YOUR `01_databases.cypher` MAY STILL PROVISION `ddcontext` AND THE `ddall`
  COMPOSITE, AND THE FOLD OWES YOU A PER-MACHINE SEQUENCE NOBODY TRACKED**
  `[VERIFIED-PRODUCER]` for everything about the producer tree below; the ONE claim about
  yours is tagged separately (raised 2026-08-24). The G32/G102 fold rode the
  `caa0406..port-base-20260819` range — `988bf0d6` is the fold commit — so this is not new
  payload. It is what that range owed you and may not have delivered.
  **(1) DIAGNOSE — two commands, and the failure text already tells you which case you are
  in.** `poetry run pytest tests/unit/test_database_names.py tests/unit/test_dev_environment.py -q`
  and `poetry run drydocs docs-verify`.
  **(a)** suite GREEN and your cypher still says `CREATE DATABASE ddcontext` → nothing of the
  fold landed. **(b)** `test_provisioning_creates_the_expected_topology` fails with a 4-name
  expectation against a 2-name actual → you have the cypher, not the guard. **(c)** that test
  fails the other way AND `test_superseded_names_are_really_superseded` reports *"provisioning
  creates ['ddall', 'ddcontext'], which this test calls superseded"* → you have the guard, not
  the cypher; that second failure is the discriminator, and it fires in no other case.
  **(d)** suite green, but `SHOW DATABASES` still lists the retired names → your repo is right
  and only the graph work in (4) is owed.
  **THE ONE THING WE CANNOT SEE** `[SME-REPORTED]`: the SME reports a copy still carrying
  `CREATE DATABASE ddcontext` and `CREATE COMPOSITE DATABASE ddall`. **If yours is already
  folded, this relay costs you two commands — say so and it is struck.** Never read it as a
  statement that your tree is broken; RELAY-5 is why that sentence is written this way.
  **(2) WHY A CORRECT APPLY MAY HAVE PRODUCED THIS, so nobody goes looking for a mistake.**
  `988bf0d6` changed THREE files under THREE dispositions:
  `drydocs_core/schema/provisioning/01_databases.cypher` is canonical-producer and crosses
  wholesale; `config/dev-environment.yaml` is **canonical-company** and must never cross;
  `tests/unit/test_database_names.py` falls to the `tests/**` evaluate default. Take the
  cypher, correctly decline the config, and your suite goes RED on
  `test_databases_match_provisioning_script` — whose message names the two databases and says
  nothing about the config file you also had to fold. The cheapest exit from that red is to put
  the cypher back, and ledger step 158 licensed it by calling provisioning DDL "your graph". So:
  **the fix is one commit containing the folded cypher, both guard tests, AND your own edit to
  your `config/dev-environment.yaml` keys.** Any one of them alone is red.
  **(3) TAKING THE FOLDED FILE IS SAFE EVEN IF YOUR GRAPH HAS NOT FOLDED — and that is the
  sentence that unblocks this.** `CREATE DATABASE … IF NOT EXISTS` never drops, so an existing
  container keeps `ddcontext` and `ddall` online and inert; nothing reading them stops working.
  The only real difference is a FRESH container, which would not get `ddcontext` — and that
  fails LOUDLY at session open with `DatabaseNotFound`, naming the database, rather than
  stranding data. Your Tier-A discretion is over what you DROP from a live DBMS, never over
  what the repo's provisioning DDL says. Before you decide, run
  `git grep -n "ddcontext\|ddall"` over your own loaders: if a company-only writer still
  targets one, the ruling is yours — and then keeping it is a divergence recorded in BOTH files,
  not a silent revert of one.
  **(4) THE PER-MACHINE SEQUENCE, previously recorded only on a done item and therefore
  invisible.** Once the repo half is right, each of your machines still owes: the R3
  delete-and-reload of the DESCRIBES edges, the ebook-corpus reload, and the drop of the two
  retired databases. **Sequence the delete and the reload in ONE session** — the gate's own risk
  entry says so, because the window between them is a graph with a capability the gate removed.
  Producer figures, quoted as OUR venue and NOT as a count to expect (J18, laptop `neo4jtest`
  `drydocs`): 27 edges → 0 → 27, 374 chunks, `:Uncertain` 0.
  **(5) THE TRAP WE HIT, so you do not.** `drydocs load-essential-graphrag` carried its own
  `--database` default of `ddcontext` that the fold sweep missed, and it STRANDED the book
  corpus in the retired database. It was caught only because `docs-verify` deliberately sweeps
  the retired name one last time (`drydocs/cli_docs.py`, self-retiring via a `SHOW DATABASES`
  intersection, so it silently stops once you drop the database). Fixed producer-side; the
  default is now `drydocs` and the fix rides the port. **This is why (1) runs `docs-verify` and
  not only pytest** — the suite cannot see a stranded corpus.
  **WHAT TO SEND BACK:** the case letter from (1) and the actual command OUTPUT, not the
  verdict (RELAY-3(b)). If you are in case (d) or already folded, that discharges this relay.

- **RELAY-14 — THE ID-SPACE PARTITION IS STILL ONE-SIDED, AND IT HAS NOW COST A
  CAPTURE** `[SME-REPORTED]` for the company-side observation; `[VERIFIED-PRODUCER]`
  for every producer-tree fact below (raised 2026-08-24). Step 160 asked for the mirror
  assertion and said "until that lands the partition is one-sided and the next
  Idea-59-class collision is a matter of time". **On 2026-08-24 a company session
  captured an inbox entry with NO id at all** — it did not allocate in the 10000+ band,
  and nothing stopped it.
  **THE CHEAP HALF NEEDS NO DECISION ABOUT BANDS.** Two of the four guards in
  `tests/unit/test_plan_ideas.py` carry no band assumption and port as-is:
  `test_every_inbox_entry_carries_the_header` (every entry must match the `Idea-<n>`
  header, so an unheadered capture fails loudly instead of reading as "nothing to review
  here") and `test_idea_ids_are_unique` (whole file, not just the inbox, because
  union-append is exactly when a duplicate arrives). Those two make the failure that
  just happened impossible, today. **The band half is still yours:** write `n >= 10000`
  and grandfather your existing low ids as a committed constant.
  **TWO CLAIMS FROM THAT SESSION ARE WRONG FOR THE PRODUCER TREE — corrected here so
  they are not carried forward.** (a) "No allocator-bands section in `IDEAS.md`" is true
  of yours, not of ours: the section has been in producer `IDEAS.md` since 2026-08-18.
  (b) "`test_plan_ideas.py` is absent on both sides, recorded in the port ledger" — the
  file exists producer-side with 12 tests, and `PORT-MANIFEST.yaml` marks it
  `disposition: per-entry`, reading *"The render/header guards are producer-canonical
  and port whole. The ALLOCATOR-BAND block does NOT"*. The ledger says take the file and
  invert one block; it never says the file is absent.
  **WHAT TO SEND BACK:** whether the two band-free guards landed, and the constant you
  grandfathered. Producer-side action: none — all four guards are green here.

- **RELAY-15 — CONTROL-M EXTRACTION IS INTERNAL-ONLY WORK, THE EXTRACTS HAVE NO
  DATA-CENTER DIMENSION, AND THE DBA ASK IS ALREADY WRITTEN** `[VERIFIED-PRODUCER]` for
  the code facts; `[SME-REPORTED]` for the estate volumetrics (raised 2026-08-24;
  producer Idea-168 + Idea-169).
  **(1) PROFILING IS YOURS BY DESIGN, and its numbers need tuning where the data is.**
  The producer has no psgmgr access, so nothing here is blocked producer-side — but four
  expectations baked into the profile prose are producer GUESSES only an internal run
  can correct: the ~30% join-coverage expectation, the grain-dedupe discriminator, the
  run-time sanity cap, and the estate-wide-join performance flag. Two different things
  are called "profiling" and only one is done: the doc-08 COLUMN CENSUS is complete 7/7
  (step 220); per-column DATA profiling — null rates, distinct counts, value domains —
  and the CM_HOSTS definition-side probes are not.
  **(2) NEITHER EXTRACT FILTERS BY DATA CENTER.**
  `drydocs/loaders/sql/controlm_folders.sql` and `drydocs/loaders/sql/controlm_jobs.sql`
  bind exactly `:folder_filter`, `:run_as`, `:developer_sid`, `:row_cap` —
  `_scope_binds()` builds that set and no other. There is no `:data_center` bind and one
  was deliberately NOT built: WHICH data centers load is an SME scope call, not a
  producer default. `--folder` filters `SCHED_TABLE`, a different axis; do not reach for
  it as a stand-in.
  **(3) DO NOT RE-SPECIFY THE STAGING SCHEMA TO YOUR DBAs — it exists.**
  `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` is already a DBA implementation
  script and already data-center-shaped: a pre-flight asking whether `TABLE_ID` is
  unique ACROSS data centers, `stg_run.data_centers` as the comma list processed per
  run, every staging table keyed `(run_id, data_center, folder_id, job_id)`, grants, and
  a full-refresh load pattern sized under 3M rows / 2 GB with no partitioning needed.
  What is missing is a per-DC RUN RECIPE, not a schema. **What forces staging is the
  VARIABLES extract, not jobs** — the census puts `CM_DEF_SETVAR_VW` near 4.7M rows
  against roughly 1.1M raw job rows.
  **(4) SCOPE IS A FIRST CUT WITH A NAMED REASON TO REVISIT.** Three data centers are in
  scope; a fourth — the largest by folder count — is a DELIBERATE CUT (SME, 2026-08-24),
  because the graph and the UI get exercised against the three-DC load before more is
  ingested. Real data-center identifiers are Internal and live only in
  `internal/standards/technology/data-center-inventory.md`; this file is publishable, so
  it names none.

- **RELAY-16 — THE `run_as` DETECTOR SHIPS; THE RUN IS YOURS, AND ITS NUMBERS LAND IN
  THE SAME EVENT K16's 0-COUNTS ROW IS WAITING ON** `[VERIFIED-PRODUCER]` for the code
  and the runner text; the finding it looks for is `[SME-REPORTED]` (2026-08-19). New
  at the 2026-08-26 roll (producer K25, step 238).
  **(1) WHAT LANDED AND WHAT DID NOT.** `drydocs/run_as_detect.py` ports with the range —
  pure, injected, counts-only, thirteen synthetic tests. The DATA does not and cannot:
  the producer has no estate extract, so every number this detector can produce is
  yours. Producer-side it has been exercised against a fixture ONLY, and the fixture is
  synthetic by construction (J18: this claim names its venue — desktop, no psgmgr).
  **(2) THE ASK.** Run it against your Control-M extract and record the counts. The
  runner prompt with the exact invocation is `docs/company-prompts/`
  `k25-run-as-detection-company-prompt.md`, which is `never-port` and therefore NOT in
  your tree — this relay is the channel, so either hand-carry that file or read the
  invocation from the module docstring, which carries the same contract.
  **(3) WHAT THE OUTPUT IS FOR.** The numbers belong in the same company-side event that
  K16's 0-counts row is still waiting on; `docs/restructure/09-fid-identity-and-scope.md`
  gains a `0-K25` method row saying exactly that. Nothing touches the graph in either
  direction.
  **(4) THE TWO THINGS NOT TO RE-DECIDE WHILE RUNNING IT.** How a platform account is
  RECOGNIZED stays K17's ruling — the injected set is the seam, and doc 09's S3 ranking
  is the evidence-backed proposal, not a default to override quietly. And a FileWatcher
  on the platform account beside payload jobs on the application account is the DESIGNED
  pattern, not a finding: the detector counts platform-class jobs and EXCLUDES them from
  the directory comparison for that reason. A payload job on the platform account is the
  countable anomaly.
  **IF THE RUN IS NOT DONE THIS PORT:** say so in the PORT-REPORT rather than leaving it
  silent — an unactioned relay with a reason is a live relay; an unmentioned one reads as
  discharged and is how RELAY-5's false company-state claim happened.

- **RELAY-17 — STUB-AND-ENRICH IS THE RULED :Employee CREATION POLICY; YOUR RUNBOOK
  (v2 AND PUBLISHED v3) FORBIDS WHAT BOTH SIDES' LOADERS DO — HARMONIZE THE DOC AND
  VERIFY THE RECONCILIATION HALF** (standing since 2026-08-28; from G74, closed
  2026-08-27).
  `[VERIFIED-PRODUCER]` for the ruling and the producer surfaces: stub-and-enrich WINS
  (SME direction 2026-08-18, producer gate-log RECORD same date; G74 clause 2 applied
  it 2026-08-27). `seal_applications.cypher` mints `:Employee` placeholders at lines
  145/169/192 (app-owner / CTO / info-owner SIDs) with `ON CREATE SET e.source='SEAL'`;
  `source` IS the awaiting-enrichment marker and nothing else is minted (ruled on the
  Employee class row in `10-node-classifications.yaml`); the count of `source='SEAL'`
  survivors after a roster load is the HR-coverage report BY DESIGN, not debris.
  `human_employee_reports_to` is registered `planned` (REPORTS_TO, Employee->Employee,
  `52-local-human.yaml`, org:reportsTo); NO producer loader exists or may exist for it —
  the source is your HR hierarchy through your `hr-emp-hierarchy` gate.
  `[SME-REPORTED]` for the two surfaces only you hold — treat as expectation, never as
  established state: (1) your "backbone-and-enrich" runbook prose (v2 and the published
  v3) states `:Employee` is created ONLY by `load-employee-roster`, SEAL attaching
  enrich-only via OPTIONAL MATCH — the opposite of the ruled behavior; (2) your
  `load-employee-roster` MERGEs on the same key and flips `source` SEAL->HR
  (authoritative), which is the reconciliation that makes the placeholder pattern safe.
  Neither is checkable from the producer (T21 already records the roster test as
  company-only; no such runbook prose exists under producer `docs/design/`).
  **ACTION AT THE PORT THAT CARRIES THIS:** (1) harmonize the runbook text (v2 + v3) to
  the placeholder pattern — the loader behavior is the policy; the doc is what changes;
  a design doc that forbids what the loader does hands the next reader whichever truth
  they open first. (2) VERIFY the reconciliation half live on your graph: a SID in both
  upgrades to `source=HR` and gains REPORTS_TO; a roster-only SID creates fresh as HR; a
  SEAL-only SID survives as the coverage report. **IF EITHER SURFACE IS NOT AS DESCRIBED
  — the prose differs, or your roster loader does not flip `source` — STOP AND SCOPE:**
  record what you actually hold in your ledger and leave the harmonization to a shape
  that matches your tree; do not force this relay's description onto it. Outcomes live
  in YOUR ledger. Same asymmetry class as RELAY-6: the producer holds the code that
  mints; you hold the doc that forbids it and the loader that reconciles it.

- **RELAY-18 — THE RECONCILE-PORT SKILL WAS ASSERTING DISPOSITIONS AND FOUR OF THEM
  WERE WRONG; `PORT-MANIFEST.yaml` IS NOW THE ONLY SOURCE, AND TWO ROWS CHANGED**
  (new 2026-09-01; from J68, which your own 2026-09-01 apply found).
  `[VERIFIED-PRODUCER]` — every claim below re-checked against the producer tree
  before this relay was written.
  **THIS LANDS AFTER `port-base-20260901` AND CHANGES NOTHING ABOUT THE APPLY YOU
  ARE RUNNING NOW.** You applied at the tag; these commits are past it and ride the
  next roll. Nothing here asks you to redo work you have already hand-merged — you
  reached the right answer on all three, by hand, which is the reason the producer
  found the rest.
  **WHAT YOU REPORTED, AND WHAT IT TURNED OUT TO BE.** You found the skill's
  collision ledger saying `tests/unit/test_module_boundary.py` was "take producer
  wholesale" while the manifest said `per-entry`, and you were right that the
  guidance was stale. Chasing it producer-side found the same defect **four times**,
  because a hand-kept list of dispositions rots against a manifest that is guarded:
  1. `tests/unit/test_module_boundary.py` — the one you hit. Ledger said wholesale,
     manifest says `per-entry`.
  2. **The `Canonical-here` bullet in step 3 named `relationship_vocabulary.yaml` for
     a `git checkout` wholesale take.** That file is `per-entry` in the manifest AND
     no longer exists as a file (sharded into per-domain fragments at S5). Taking it
     as instructed would have **flattened your own ontology entries — including the
     19-class TOM register your G70 session ruled.** This is the one worth reading
     twice; it never fired only because the path was already gone.
  3. The same bullet named `drydocs_core/controlm/`, which moved under
     `drydocs_core/orchestration/` and has not existed for some time.
  4. The `tests/unit/test_variable_*` row asserted a disposition it happened to get
     right — harmless, and still removed, because a correct copy of a fact is what
     the next stale copy grows from.
  **THE FIX:** the ledger is now headed *"HOW to merge — never WHETHER to take"*, and
  no row in that skill may assert that a file is taken wholesale, kept or dropped.
  Resolve disposition from `PORT-MANIFEST.yaml`, per path, always. On any
  disagreement the manifest wins.
  **TWO MANIFEST ROWS CHANGED, both from your findings:**
  - `MODULE_MAP.md` — was `canonical-producer`, is now **`per-entry`**. Its guard was
    already `per-entry`, and that split is what dropped your `drydocs.scrapers.*`,
    `drydocs.docmeta.*` and `drydocs.seal_projection` rows. Module rows union;
    producer mechanism (the placement test, the core-imports-nothing invariant, the
    S7 rule, the `CORE_PREFIXES`/`COMPONENT_GROUP` vocabulary) crosses whole.
  - `config/source-registry.yaml` — had **no row at all** and fell through to
    `config/**` canonical-producer, which is what drove your `test_source_registry`
    from 1 failure to 7. Now **`per-entry`**: your systems and datasets stay, the id
    grammar and `authority` semantics cross whole. Third instance of that
    fall-through — `dev-environment.yaml` (2026-07-28) and `source-bindings.yaml`
    were the first two.
  **AND A GUARD, so this is not a third round of the same lesson:**
  `test_every_declaration_names_the_guard_that_reads_it` — a declaration file and
  the guard that reads it must NAME each other in the manifest. Deliberately not
  "must share a disposition": `01_databases.cypher` / `test_database_names.py` are
  split on purpose (topology is a signed ruling, `SCANNED_PACKAGES` is extensible)
  and that split is correct. Naming is the property that was missing.
  **ACTION AT THE PORT THAT CARRIES THIS:** take both manifest rows before the files
  they govern, then re-run your own classification of the range — the two rows move
  paths out of your wholesale bucket and into per-entry, so a census taken before
  this relay will disagree with one taken after. **One stale number you should not
  copy:** the ledger's `EXPECTED_CONSTRAINTS = 44` is retired rather than updated —
  PORT-REPORT-40c35724 measured 55 your side, and a count in a producer file rots
  between ports. Read it from your own run.

- **RELAY-19 — FOUR MERGE RULES HAD NO ANSWER FOR FIELDS THAT EXIST, WHICH IS WHY
  `source-bindings.yaml` DROPPED; THE RULES ARE NOW TOTAL AND FOUR FIELDS ARE OWED
  BACK** (new 2026-09-01; J71, from the SME's own catch).
  `[SME-REPORTED]` for the drop, `[VERIFIED-PRODUCER]` for everything measured below.
  **YOU DID NOT MISS THIS — THE RULE DID.** `config/source-bindings.yaml` was not
  carried from `1bd29b42` (G129), which added `twin:` to every profile. The row's
  field split ENUMERATES: producer-owned `id, carrier, platform, classification,
  serves, note` plus the env-map keys; company-owned the variable names and `status`.
  **`twin` and `reason` are in neither list.** The rule was written at `683d85fe`
  (G125) and `twin` landed the next day at `1bd29b42`; nobody went back to classify
  it. A per-entry merge with no instruction for a field has no defensible move.
  **AND TAKING IT WOULD ALSO HAVE BEEN WRONG,** which is the part worth reading:
  `twin` holds a path under internal-local/ — machine-local and gitignored, so it
  exists on exactly one machine. By the row's own principle — *the WHAT crosses and the WHERE never does* —
  **the KEY is producer mechanism and the VALUE is yours.** Take the field and its
  header comment; point it at YOUR twin. Neither "take the file" nor "skip the file"
  was ever the right instruction, and the manifest said neither.
  **WHAT IS OWED BACK, by file. Each is a FIELD to adopt, not a value to copy:**
  1. `config/source-bindings.yaml` — add `twin:` to each profile (yours, or `~` with
     the reason in its note) and `reason:` on `unbound[]` rows. Both stay yours.
  2. `config/doc-source-registry.yaml` — five fields the rule never named:
     `classification`, `describes_product`, `replaces`, `source_url` are WHAT and
     **cross on take**; `landing_zone` is a WHERE and **stays yours**. Five commits in
     the applied range touched this file (`87fca339`, `63de2acc`, `ff87227f`,
     `3afa8307`, `3c2bfcdd`) — worth a diff against `port-base-20260901` rather than
     an assumption about which way each went.
  3. `config/audit-fields.yaml` — `notes` and `objects` cross; **`status` is per-repo
     and `decided_by` travels with it**, so yours stand. Two commits (`07d9caab`,
     `3c2bfcdd`).
  4. `config/source-registry.yaml` — see RELAY-18: it was `canonical-producer` during
     your apply, so its failure was the opposite one (overwritten, not dropped, which
     is your `test_source_registry` 1 -> 7). It is `per-entry` now.
  **THE STRUCTURAL FIX, so this stops recurring:** every per-entry `entry_rule` is now
  **TOTAL** — it names the fields it wants to name and then declares, under a literal
  `UNNAMED FIELDS:` marker, which side owns everything else. A field added tomorrow has
  an answer the day it lands. `test_every_per_entry_rule_is_total` enforces it, written
  red first against all four rows. **One default is worth knowing before you merge
  anything:** on `source-bindings.yaml`, when a new field is genuinely ambiguous,
  **KEEP YOURS.** An unfamiliar producer value can point you at something that does not
  exist on your machine; keeping your own only leaves you a version behind — and the
  second failure is visible where the first is silent.
  **AND ONE ADMISSION, because it is the best argument for the change:** the
  `source-registry.yaml` rule that RELAY-18 announces was written the same morning and
  named 6 of that file's 29 fields. The defect reappeared in the row that fixed it.

- **RELAY-20 — THE CONTENT-SIMILARITY CHECK YOU ASKED FOR IS BUILT AND PROVEN ON
  THE REAL RENAMES; RUN IT BEFORE THE NEXT CLEAN-ADD SLICE** (new 2026-09-01; J72,
  from your own request after the trap fired twice).
  `[VERIFIED-PRODUCER]` — proven against real history, not fixtures.
  **THE COMMAND**, from your checkout with the producer remote fetched:
  ```
  poetry run python scripts/port_rename_check.py --producer-ref port-base-20260901 --path-prefix config/
  ```
  Exit 0 = no proposed clean-add resembles a file you already hold. Exit 1 = at
  least one does, and it names the pair. Drop `--path-prefix` for the whole tree;
  add `--any-directory` only for a deliberate sweep (both known traps were
  in-directory, and the wide compare is quadratic).
  **PROVEN ON YOUR TWO TRAPS, on real commits.** Run across `496aa268~1..496aa268`
  — the commit that actually applied the gate rename — it reports both pairs at
  **id-set similarity 1.00**: `40-local-scheduler.yaml` ← `40-local-controlm.yaml`,
  and `41-local-business-application.yaml` ← `41-local-seal.yaml`. That second pair
  is the one that cost you 62 failures.
  **TWO MEASURES, AND YOU NEED BOTH — your two traps have opposite shapes.** A
  SPLIT (41-local-seal → business-application + human) diverges in prose and keeps
  its ids, so the id-set measure catches it. A RENAME (the crosswalk prompt's
  retired-acronym name → `cdo-crosswalk`) renames the id — the id IS the filename stem — and keeps its body,
  so only the text measure catches it. The id measure ABSTAINS below three ids on
  either side, precisely so a one-id-each miss cannot score the gate pair 0.00 and
  silence the measure that scores it 0.88.
  **IT REPORTS, IT DOES NOT DECIDE.** Every flagged pair is adopt / decline / false
  positive, and the output says so. Your two failures came from acting without
  looking, not from looking and choosing wrong — this restores the looking step and
  nothing else.
  **ONE FINDING FROM BUILDING IT THAT IS YOURS TOO.** Its first run raised
  `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d` — `subprocess(...,
  text=True)` decodes with the platform locale, cp1252 on Windows. **That is the
  same trap you reported an hour earlier**, where a comparison script mojibaked
  every em-dash and fabricated 18 of 25 "differences". Fixed here with an explicit
  `encoding="utf-8"`, and worth applying to any comparison tooling you keep: a
  similarity check that mis-decodes one side compares a corrupted document against
  a clean one and reports the corruption as a difference. Both machines are Windows;
  neither of us gets this for free.
  **ACTION AT THE PORT THAT CARRIES THIS:** it lands after `port-base-20260901`, so
  it is not in the range you are applying — take the three files by name if you want
  it now (`drydocs/port_rename_detect.py`, `scripts/port_rename_check.py`,
  `tests/unit/test_port_rename_detect.py`), or run it from the producer checkout
  against your tree. Either way, run it before D/E/F, where ~430 files remain
  unexamined and 217 of them classify as clean-adds.

- **RELAY-21 — THE ACRONYM RENAME IS ACCEPTED (SME, re-stated 2026-09-01). APPLY IT
  AS A RENAME OF PATHS, NEVER AS A TAKE OF CONTENT — that distinction dissolves the
  gate-state objection entirely** (supersedes the defer recommendation in the
  producer's own earlier advice).
  `[SME-REPORTED]` for the ruling; `[VERIFIED-PRODUCER]` for the file list.
  **THE RULING IS ACCEPT.** The SME gave it once before the scope was known and
  again after. The producer previously recommended deferring it beside the
  vocabulary migration; **that recommendation is withdrawn** — it was reasoning
  about a content take when the ruling is about names.
  **WHY THE GATE-STATE OBJECTION DOES NOT SURVIVE THE DISTINCTION.** The objection
  was that the producer's `cdo-crosswalk.yaml` reads SIGNED OFF, 13 confirmations,
  where yours reads DRAFT with a session pending, and `config/gate-prompts/**` is
  canonical-company. That is entirely correct **about CONTENT**. It says nothing
  about the NAME. The manifest's `canonical-company` disposition protects what is
  IN your file; it does not freeze what the file is CALLED. So:
  **RENAME YOUR OWN FILE AND KEEP YOUR OWN CONTENT.** `git mv` the path; do not
  `git checkout` the producer's version. Your prompt stays DRAFT, unsigned, session
  pending — under its new name. No signature crosses, and the acronym is retired
  from the surface as ruled.
  **THE INSTRUCTION SET IS GIT'S, NOT A GREP.** `git diff -M --diff-filter=R
  --name-status port-base-20260826..HEAD` reports the rename set exactly, with
  similarity scores. The eleven in this family:
  `config/crosswalks/*-vocabulary.yaml` (R082), `config/gate-prompts/*-crosswalk.yaml`
  (R075), `docs/company-prompts/*-frameworks-load-company-prompt.md` (R093),
  `tests/unit/test_*_crosswalk.py` (R088), and the six under
  `internal/*-reference/` (R083–R100). Use that list rather than a token sweep —
  it is the same 72-file change measured exactly, and it will not touch a prose
  mention that happens to contain the string.
  **THE ORDER THAT MATTERS:** rename the TEST with its subject in the same commit.
  `test_*_crosswalk.py` reads `config/crosswalks/*-vocabulary.yaml`, so renaming one
  without the other is the paired-declaration failure J68 exists for, and it will
  fail on arrival.
  **AND THE ONE THING THAT IS NOT A RENAME:** `internal/**` is company-side
  Internal content and never crosses. Rename your own directory if you hold one;
  do not take the producer's six transcripts.
  **CORRECTED 2026-09-05 (your carve-out 9 found it):** "never crosses" was wrong;
  the word is "never PUBLISHES". `internal/**` is `default_ok`, and its manifest
  reason says the private company remote is exactly where Internal content
  belongs - a private remote is not a public mirror. So the transcripts cross, they
  stay as captured (the file-scoped rule below), and `internal/cdo-reference/
  README.md` reached you as a clean-add carrying its own RENAMED note. See the
  EIGHTEENTH POSTSCRIPT.
  **CORRECTION (2026-09-02, from your own apply) — THE SWEEP IS REQUIRED, AND THE
  RELAY ABOVE SAID THE OPPOSITE.** "Use that list rather than a token sweep" was
  wrong, and the guard caught it on your side: `tests/unit/
  test_publish_boundary_retired_org_acronym.py` (J55, in this range) fails on ANY
  occurrence of the retired token outside `internal/`, prose included, allowlist
  EMPTY. The producer's own change was 13 path renames PLUS a prose sweep of every
  publishable file (`gate-log.md`, `IDEAS.md`, `doc-source-registry.yaml` — the
  four-letter form became the three-letter form even inside quoted committee
  names); the only text that keeps the old token is the VERBATIM
  capture under `internal/`, because `internal/` never publishes. So the rule is
  scoped by FILE, not by case and not by path-vs-prose: **outside `internal/`, the
  token goes everywhere; inside `internal/`, captured text stays as captured and
  only the directory moves.** What "never a take of content" MEANT — and still
  means — is narrower than the sentence read: the gate prompt's STATUS and
  SIGNATURE do not cross. Rename it, sweep its prose, keep it DRAFT and unsigned.
  You derived this from the tree and applied it correctly (13 renames, 50 files,
  201 mentions, residual outside `internal/` zero, J55 green); this note exists so
  the next reader does not have to.

- **RELAY-22 — YOUR +83 ON SLICE E IS NOT A PORT PROBLEM, IT IS A RENDER STEP; AND THE
  MANIFEST WAS TELLING YOU TO TAKE ARTIFACTS YOU SHOULD REGENERATE** (new 2026-09-02;
  from your own D+E attribution, which was right).
  `[VERIFIED-PRODUCER]` for the manifest defect and the renderer list; `[SME-REPORTED]`
  for the failure counts.
  **YOUR ATTRIBUTION IS RIGHT.** The +83 concentrates in E's newly-added tests asserting
  that generated artifacts exist — `web/src/generated/world-*.json` and the vendored
  `external/geo/world-atlas/countries-110m.json`. The failures are missing ARTIFACTS,
  not broken code. Your recommendation — **commit D alone, hold E for F+G** — is the
  right call, and the producer agrees with it and with your reason (J31: D's
  `cli.py` surgical merge and `validate_fact_rows` are the hard-won parts; protect them).
  **BUT THE MANIFEST HAD A DEFECT THAT WOULD HAVE MADE F+G WRONG TOO.**
  `web/src/generated/**` had **no row** and fell through to `web/**`
  canonical-producer — so the manifest told you to `git checkout` producer's generated
  JSON. Fixed 2026-09-02: it is now **`derived`**, the same row shape `docs/plan/*.html`
  already has. **Regenerate, never carry (J43).** Every file there is written by a
  `scripts/render_*.py` renderer from committed sources and has a drift guard asserting
  the committed copy matches a fresh render. A carried copy would make those tests pass
  while reflecting PRODUCER's gates, load-map and software registry rather than yours —
  a passing suite describing the wrong estate, which is the worst outcome available.
  **SO F+G IS TWO DIFFERENT KINDS OF STEP, and the order matters:**
  1. **F — take the SOURCES.** `external/geo/world-atlas/countries-110m.json` is a
     vendored asset (default_ok, clean-add). The config, taxonomy and registry rows
     your E tests read are per-entry or canonical-producer per the manifest.
  2. **G — RUN the renderers, do not port their outputs.** You already pulled
     `render_world_map.py`, `render_remediation_profile.py` and
     `set_console_credential.py` forward as subjects. Add `render_board.py` (it writes
     `gates.json`, `enforcement-matrix.json` and `load-map.json` in one run) and run
     `python scripts/render_board.py` plus the others. The drift guards then pass on
     YOUR sources, which is what they are for.
  **YOUR TWO UNTRACED CLUSTERS, traced here:** `test_env_doctor` (13) reads
  `render_env_example.py` and `.env.example`, and `.env.example` is itself a RENDER of
  `DECLARED_VARIABLES` (G129) — so it clears by running `render_env_example.py` after
  `env_refs.py` merges, not by porting the file. `test_query_specs` (6) reads
  `drydocs_api/query_specs.py` (default_ok), which you pulled forward in the sibling
  sweep; if it still fails after that, it is a QuerySpec registry content difference
  and yours to reconcile, not an artifact gap. **Both are render-or-merge shaped, not
  port-shaped — consistent with your "+83 clears at G" hypothesis, and still a
  hypothesis until you run it, as you said.**
  **ONE THING TO CARRY INTO D'S COMMIT MESSAGE:** your slicing has now failed to be
  closed under dependency three times (config→core, tests→scripts, tests→renders), each
  caught before a commit. That is the argument for the disposition-led apply in J69
  rather than directory-led slices — a `derived` class is worked LAST by construction
  because it is regenerated from everything before it. Worth saying in the record so the
  next apply starts from classes, not directories.

- **RELAY-23 — FOUR FLAT COMPONENTS BECAME SUBPACKAGES; APPLY IT AS ONE CARVED SLICE OF
  RENAMES, YOUR CONTENT FIRST, THE SHIMS SECOND** (new 2026-09-02; ADR 0018 D4 as amended
  at acceptance — the SME ruled "take the hit now, carve that into the sole port").
  `[VERIFIED-PRODUCER]` for the move and the shims (3,071 unit tests green on the moved
  tree); `[SME-REPORTED]` for the ruling.
  **WHAT MOVED.** Seventeen modules and one package (eighteen moves) left the flat
  `drydocs/` root for four subpackages, keeping their basenames: `drydocs/review/` (graph_verify, review_labels,
  source_mappings, graph_review, sme_notes, gate_pages, fid_census, run_as_detect, and the
  `publishing/` package), `drydocs/plan/` (plan_board, plan_roadmap), `drydocs/port/`
  (port_preflight, port_backlog_union, port_rename_detect), `drydocs/docgen/` (doc_outline,
  design_doc, doc_pdf, plan_ideas). `load` stays the package root. Every old path is now a
  one-line `sys.modules` re-export SHIM — `drydocs.gate_pages` and
  `drydocs.review.gate_pages` are the SAME module object, so every old import, patch
  target and citation still resolves — for ONE port cycle; the shims retire at the roll
  after next, and the manifest rows that pin them go with them.
  **WHY IT IS ONE SLICE AND WHERE IT SITS.** It touches no vocabulary and no config value,
  so it sits between the range's classes and the vocabulary migration (workplan chunks 4
  and 5, `docs/reviews/port-test-review-and-workplan-2026-09-02.md`). `git diff -M
  --diff-filter=R --name-status port-base-20260901..<next base> -- drydocs/` reproduces
  the rename set exactly, with similarity 100 on every row; `scripts/port_rename_check.py`
  reports the same pairs. Do not let the eighteen old paths classify as clean-adds of the
  shims while the new paths classify as clean-adds of the modules — that is the J72 trap
  with the sign flipped, and it would leave you two copies of every module.
  **THE ORDER, and it is the RELAY-21 distinction again — names versus content.** Six of
  the moved paths are `canonical-company` (the five review modules and `publishing/**`):
  YOUR files carry the real wiring and the producer's are templates. The manifest rows now
  name the NEW paths for that content. So: (1) `git mv` YOUR files under those six rows to
  their subpackage paths - five modules and the whole `publishing/` package, twelve paths
  on your tree - content moves, nothing crosses; (2) THEN take the producer's shims at the old
  paths, which the manifest pins `canonical-producer` with a note saying exactly this;
  (3) take the twelve plan/port/docgen modules at their new paths as ordinary
  `default_ok` producer code (nine, once `review`'s three non-canonical-company modules are
  counted with them - the arithmetic is in your report; the rule is the same) (you hold producer copies; `evaluate` resolves to "take" unless
  you extended one — the D-slice `cli.py` merge is the only place you did, and `cli.py`
  did not move); (4) take the four `__init__.py` files and `drydocs_core/component_map.py`
  (canonical-producer — it is the declaration the boundary test now imports, ADR 0018 D1).
  A shim taken BEFORE step 1 overwrites your wiring with an alias to a file that is not
  there yet.
  **WHAT ELSE CROSSES WITH IT, all mechanism:** the boundary test imports the map and gains
  four join guards (every group names a `modules.yaml` module; the registry is exactly
  core + groups + the declared non-Python set; every top-level directory has an owner);
  `modules.yaml` registers `drydocs-port` (series `PORT`) and `drydocs-libs` (`LIBS`) with
  runbook-coverage exemptions and roadmap judgments — `modules.yaml` is per-entry, union
  by name; `MODULE_MAP.md` gains a RENDERED component-map section between
  `<!-- component-map:begin/end -->` markers (`scripts/render_module_map.py`,
  `test_module_map_render.py` fails on drift — regenerate, never carry, J43; the hand tables
  around it are per-entry as before); PORT-MANIFEST rows for the six canonical-company
  paths now name the new paths, and eighteen shim rows (twelve new plus the six flipped) pin the old ones; every guard
  declaration in `config/**` that named a moved module by path (`review_labels.py`,
  `source_mappings.py`, `fid_census.py`, `design_doc.py` in the gate prompts, source
  mappings and `review-labels.yaml`) names the new path — those are per-entry files, so
  the path string moves inside YOUR entry, not by taking the producer's file.
  **THE ONE THING THAT DID NOT MOVE ON PURPOSE:** `drydocs/cli.py` and the six `cli_*.py`
  command modules stay at the root (they ARE the load component's root, and your `cli.py`
  is a surgical merge — Idea-241). Nothing in this relay touches them.

- **RELAY-24 — ADOPT THE S8 CLI SPLIT BEFORE YOU RETRY THE APPLY: TAKE THE SHAPE, RE-HOME
  YOUR VERBS INTO `drydocs/cli_consumer.py`, AND STOP EDITING `cli.py` FOR GOOD** (new
  2026-09-02; S16 built the seam, the SME ruled "don't merge this port, try again with S8").
  `[VERIFIED-PRODUCER]` for the seam and its guards; `[SME-REPORTED]` for the ruling.
  **WHY TWO PORTS WALKED PAST IT.** `drydocs/cli.py` carried an `evaluate` row that read
  "both sides add commands - merge per collision ledger", and you followed it literally:
  producer verbs merged INTO your monolith, twice, while the producer had already split
  the file (S8, 2026-08-21: a thin composition root plus six per-domain `cli_*.py`; S13:
  `cli_shared.py`). An evaluate note can say how to merge CONTENT; no wording of it can
  say "the shape of this file changed, take the shape and re-home your content". That
  is why your Defect 6 exists: you hold the six modules (canonical-producer by default)
  and a root that does not import them, so they sit orphaned and `test_env_doctor`
  fails three. The row is now `canonical-producer`, and this relay is the sentence the
  row could not say.
  **THE SEAM (S16, producer-side, past your base - take it by name or wait for the
  roll).** `drydocs/cli.py` now discovers ONE optional consumer module -
  `drydocs.cli_consumer`, `importlib.util.find_spec`, never a hard import - and registers
  its verbs LAST, after `COMMAND_MODULES`, so a consumer verb shadows nothing by
  accident. The producer ships no such file; absent is the normal state and it is
  silent. Guards: `tests/unit/test_cli_registry.py` proves both directions with a fixture
  module (present registers last; absent is silent; importing it first never executes
  the root), `tests/unit/test_cli_import_order.py` adds it to the subprocess-per-import
  list wherever it exists, and the boundary map classifies it `load`.
  **THE ADOPTION, six steps - and the ORDER CORRECTION that followed the first reading
  (2026-09-02, later the same evening):** the eight S8 files import loaders and helpers
  that arrive IN THE RANGE you are re-applying (`chain_inputs`, `manual_loads`,
  `batch_port_orchestrator`, the G82/G128 loaders), so a wholesale take of `cli.py` on
  your pre-port `main` does not import. Step 1 therefore happens INSIDE the retry, in the
  canonical-producer class of chunk 4, where the import closure is the range itself;
  chunk 0 on `main` is steps 2 and 4 only - author your module, park the branch.
  1. Take `drydocs/cli.py`, `drydocs/cli_shared.py` and the six `drydocs/cli_*.py`
     WHOLESALE - in chunk 4's canonical-producer pass, from a producer tree that carries
     S16 (`9b63527a` or later; the seam is past `port-base-20260901`, so these eight are
     a take-by-name from that sha, the dossier-4 shape). `python -c "import drydocs.cli"`
     is the closure check: every ImportError names a loader the range has not landed
     yet. The row is canonical-producer now; the `cli.py` line is not a merge any more.
  2. Diff your old `cli.py` against the producer's six modules: every verb of yours that
     is NOT a producer verb goes into `drydocs/cli_consumer.py`. Module shape = any of the
     six: its own `typer.Typer()`, verbs registered on it, shared state imported from
     `drydocs.cli_shared`, and `_client` resolved THROUGH the root inside the function
     (a function-local import of the root module, then `return _root._client(database)` - the six modules show the exact lines) - never a
     module-scope import of `drydocs.cli`, which is the S13 cycle and the guard fails
     you by name. Your `patch_window_cmd` and the scrapers / docmeta / seal_projection
     verbs are the ones you know about; the diff is the list.
  3. DD6 (T22) closes in the same move: the producer's root `_client(database)` already
     takes the database, so `docs-verify` and `bootstrap-schema-graph` register from the
     producer's `cli_docs.py` / `cli_schema.py` without a wrapper of yours; the `ddschema`
     provisioning DDL is still yours to run (chunk 6 of the workplan).
  4. `drydocs/cli_consumer.py` is canonical-company (its row is already in the manifest,
     and it matches nothing producer-side by construction). Add it to YOUR overlay if you
     keep one; never send it.
  5. Guards green, in this order: `python -c "import drydocs.cli"`;
     `pytest tests/unit/test_cli_import_order.py tests/unit/test_cli_registry.py` (the
     consumer module joins the first list automatically once it exists); then
     `drydocs --help` lists your verbs after the producer's. `test_env_doctor`'s three
     clear with the orphans gone. THE REFERENCE FILES THAT MOVE WITH THE EIGHT, all
     take-by-name from the same sha: `tests/unit/test_cli_registry.py` (new) and
     `tests/unit/test_cli_import_order.py` (gains the optional module); the two
     `PORT-MANIFEST.yaml` rows (`drydocs/cli.py` canonical-producer,
     `drydocs/cli_consumer.py` canonical-company + its `row_may_match_nothing` entry -
     the manifest is canonical-producer, so they arrive with it); and ONE line in YOUR
     `tests/unit/test_module_boundary.py` (per-entry): add `"drydocs.cli_consumer"` to
     the `load` group, or default-deny fails your module as UNCLASSIFIED - producer-side
     that line lives in `drydocs_core/component_map.py` (CORE1, also past your base).
  6. Then and only then: park `port/20260901b` as the reference branch it is (the
     dispositions record, the `validate_fact_rows` merge and the suite trajectory are
     worth keeping; nothing on it merges), branch fresh from your main, re-take the
     before-snapshot (chunk 1), and re-apply by class. With `cli.py` wholesale, slice D's
     surgical merge does not happen again.
  **WHAT THIS RELAY DOES NOT DO:** it does not move any producer verb, does not change
  `drydocs --help` producer-side, and does not author your module - the diff in step 2
  is the only place your verbs are known.
  **ADDENDUM 2026-09-03, from your chunk-0 build - four things the first consumer module
  hit, and one producer gap among them.** (a) THE GAP, producer's: your module wires your
  own components (docmeta, publishing, sme_notes) and
  `test_components_do_not_import_each_other` failed it on eleven imports, because S16 said
  a consumer module "may import anything" and then left it out of `ENTRYPOINT_MODULES`.
  Fixed producer-side after `port-base-20260902` (the entry is in
  `drydocs_core/component_map.py`); until that ports, add `"drydocs.cli_consumer"` to
  `ENTRYPOINT_MODULES` in YOUR `test_module_boundary.py` beside the `load` classification -
  same file, two lines. (b) IMPORTING THE MODULE BEFORE CHUNK 4 FAILS BY DESIGN: it imports
  `cli_shared`, which imports loaders the range carries (`folder_attribution` ->
  `seal_attribution.validate_fact_rows` is the first ImportError you will see, and it is
  the D-slice merge you parked). Author and lint it in chunk 0; import it in chunk 4, or
  test-import it in a worktree checked out at `port-base-20260902` with your module
  dropped in. (c) THE SIX `DEFAULT_*` CONSTANTS your extractor reported missing
  (`DEFAULT_GROUPS_CSV`, `DEFAULT_CROSSWALK`, `DEFAULT_TOM_CSV`, `DEFAULT_ROSTER_DIR`,
  `DEFAULT_APP_GROUP_CSV`, `DEFAULT_MEMBERS_CSV`) are company-side inputs the producer
  never had - they belong in your module, not in `cli_shared`. (d) 1,520 LINES IS A
  MONOLITH AGAIN: the seam discovers ONE name, but that name may be a PACKAGE -
  a `cli_consumer/` directory under `drydocs/` whose package init exposes `app`, with per-domain modules inside on
  the S8 shape - and `find_spec` and the import-order guard treat it identically. Your
  call; the shape is the same either way.

- **RELAY-25 — YOUR CHUNK-1 REPORT ON `port-base-20260902`: FIVE PRODUCER CORRECTIONS
  LANDED, AND THE MECHANISM ANSWERS TO YOUR SEVEN QUESTIONS** (new 2026-09-03; the rulings
  that are yours stay yours). `[VERIFIED-PRODUCER]` for every fix named by sha;
  `[SME-REPORTED]` for what your report measured.
  **WHAT YOU FOUND THAT WAS OURS, fixed after `port-base-20260902` (take by name, or wait
  for the roll):** (1) the `drydocs/publishing/` shim aliased four submodules by name and
  your package holds six - it now aliases every submodule `pkgutil` finds, so
  `confluence_client` and `manifest` are one object each, not two; (2) `cli_shared.py` and
  the six `cli_*.py` had no manifest row and fell to `default_ok` (evaluate on collision) -
  seven canonical-producer rows now say "take wholesale with `cli.py`"; (3) RELAY-23's
  counts - seventeen modules plus the package, eighteen shim rows, six ROWS covering
  twelve of your paths - corrected in place; (4) the measured block reads 194 / 10, yours
  was right, the producer measured before its own `*-workspace/**` row; (5) J55 is now
  FAIL-CLOSED on a full clone: a tree that carries `internal/` but whose
  `internal/cdo-reference/README.md` has no RENAMED note FAILS with the sentence to
  author, instead of skipping - "J55 green" on your side meant nothing until this.
  **THE FINDING THAT CHANGES THE PLAN, and it is right:** the rename-look's 357 proposed
  clean-adds are a TREE diff (producer at the tag versus your HEAD), and the 738 are a RANGE
  diff (tag..tag). A file that predates `port-base-20260826` and never reached you -
  `drydocs/loaders/cypher/folder_attribution.cypher` is your example - is in the first set
  and not the second, so a chunk-4 pass that works only the range's classes never adds it.
  **Chunk 4's population is the union**: the range's classes, plus every tree-diff clean-add
  dispositioned ADOPT in chunk 1, classified through the same manifest. The workplan says so
  now. That cypher is a plain clean-add; the vocabulary's "held/absent" note is about the
  LOAD (K8 is T23 family, grain-breaking - the file lands in chunk 4, the verb runs after
  chunk 7's wipe).
  **YOUR SEVEN QUESTIONS - the mechanism half:** Q1 answered above. Q2: yes, the company
  authors its own RENAMED note (one sentence naming the former directory) - the guard's
  regex reads `internal/<token>-reference/`, and (5) makes its absence a failure.
  [CORRECTED 2026-09-05: the premise was wrong on both sides - the README crossed as a
  clean-add under the `internal/**` default_ok row, so nobody authors a second note; your
  close-out's Q2 strike-through is the answer of record. EIGHTEENTH POSTSCRIPT.] Q3 and Q5
  are company housekeeping - the `never-port` row on `docs/company-prompts/` protects the
  directory from producer DELETIONS; moving your own flat stragglers into it is your call
  and nothing here objects; the one orphan left under your `docs/Product/` after the S14 move likewise (it is a company-only file; move it beside the rest under `knowledge/org/`, delete it, or give it a row). Q4: the
  retired `docs/port-prompt.md` stub is yours - a one-line pointer to your PORT-REPORT that
  is never refreshed, or delete it; it stays in FOREIGN_PATHS here either way. Q6: yes,
  deliberate - the before-state is the tree the RANGE meets, and chunk 0 authored one
  company file the snapshot's six do not include. Q7: not a port question, and worth the
  look - inboxed producer-side (Idea-251): a HITL feedback artifact whose rev1 and rev11
  normalize to the same anchor set is either an unfilled template or a normalizer that
  discards the payload.
  **ONE THING YOUR REPORT GOT WRONG, for the record:** `cli_consumer.py` being classified
  `load` and importing docmeta/publishing/sme_notes is not a `DECLARED_COMPONENT_IMPORTS`
  case; it is the ENTRYPOINT case (the consumer's composition surface), and the producer's
  map says so since `30d2e870`. Your declared-imports resolution works; the entrypoint line
  is the one that ports, so switch to it when the seam arrives, or carry both until then.
  **POSTSCRIPT (chunk 2, carve-out 1):** `test_the_totality_detector_catches_an_injected_hole`
  crashed on your tree with `FileNotFoundError` for `config/source-bindings.yaml` - the
  companion hard-coded that subject, and a consumer holds the manifest before it holds
  every per-entry file. It now SKIPS, by name, when the subject is absent (the detector
  itself still runs); fixed producer-side after the tag. And the ruling you asked for:
  **do the two tree-diff `git mv` batches in chunk 2, right after the manifest take** -
  the eleven `SDLC-Docs/extracted/` and `docs/Product/` files to `docs/history/genesis/`
  and `knowledge/org/`. They are your own content moving to producer paths (ADOPT
  verdicts already given, nothing crosses), and a fall-through guard red for a known
  reason cannot report a new fall-through a later carve-out introduces. A guard is
  allowed to be red only when the NEXT carve-out is its fix.
  **SECOND POSTSCRIPT (after the moves):** the `test_markdown_fences.py` canary you
  re-pointed was a producer defect, not a divergence to carry. It pinned
  `docs/port/port-prompt.md` - the file the defect was found in - and `docs/port/**` is
  never-port, so a canonical-producer test asserted a file that cannot exist on your
  side. It now pins `docs/style/us-business-english.md` (`docs/style/**` crosses whole).
  Take the producer's test by name past the tag and drop your divergence; the
  `test_plan_ideas.py` revert was right - its subject `drydocs/docgen/plan_ideas.py`
  arrives with carve-out 2 (RELAY-23 content first), so the test goes with that.
  **THIRD POSTSCRIPT (carve-out 2, the retired stub's third guard):** same defect class,
  same fix. `test_runbook_currency.py` read `docs/port/port-prompt.md` unconditionally
  through `EXTRA_DOCS`, so all four of its tests failed on your tree, and you emptied
  `EXTRA_DOCS` as a divergence - which drops the three routing docs (CLAUDE.md,
  MODULE_MAP.md, git-readme.md) from the currency guard on your side. The producer's
  test now carries `NEVER_PORT_ZONE_OF`: an entry under a never-port zone is skipped by
  name when the zone directory is absent, and still required when it is present. Take
  the test by name past the tag and restore `EXTRA_DOCS` whole. Your observation stands
  and is recorded: one retired stub broke three separate guards, and only the full-suite
  baseline diff caught the last two - that is why the baseline diff is part of the ritual.
  Your second finding is applied too: the zone check reads TRACKED content (`git ls-files`),
  not `is_dir()`, so your `docs/port/` holding only the gitignored `port-dispositions.md`
  reads as absent. Take the test by name again, at or after this commit - and one
  correction to that instruction, both times I gave it: `test_runbook_currency.py` is
  PER-ENTRY (its manifest row, J51): the GUARD code crosses whole - `EXTRA_DOCS`,
  `NEVER_PORT_ZONE_OF` and the checks are mechanism - while the three EXEMPTION tables
  are per-side data, union by key, your reasons kept verbatim. So `docs/plan/load-map.html`
  (derived, deferred on your side under T19) goes in YOUR `HISTORICAL_PATHS` beside the
  four T19 entries you already hold, not in a producer table. Two more from your
  currency findings: `git-readme.md` is DEFAULT (evaluate), deliberately uncovered - the
  row says both sides may hold their own copy - so a take is a legitimate evaluate
  outcome only after a diff shows your copy carries nothing but the 21 stale paths; and
  `MODULE_MAP.md` is per-entry as you read it - the three `controlm/*` rows resolve
  against the merged map, and a company-only row that cites a path that no longer
  exists is stale on your side, not protected by the rule.
  **FOURTH POSTSCRIPT (carve-out 2 closing):** two rulings on what you reported. (1) The
  eleven producer exemptions you retired because their only citer is the never-port
  ledger: that is now the row's own rule (`test_runbook_currency.py` entry_rule - a
  producer entry cited only from under a never-port zone is dropped by the consumer),
  so the next union does not bring them back. (2) Reordering the S8 take to be the next
  carve-out is allowed by the red-only-when-next-fixes-it rule, on one condition the
  workplan gave for deferring it in the first place: the eight S8 files import EIGHT
  `drydocs_core` modules that are in this range - `data_root`, `data_zones`,
  `docs_verify`, `env_doctor`, `env_refs`, `mapping_store`, `schema/supplements`,
  `source_bindings` (you already hold the last two; `drydocs.loaders.vendor_docs` and
  `drydocs.chain_inputs` are imported too but are NOT in this range, so they are already
  yours). Take those WITH the eight, one commit, and the guard is
  chunk 0's: `python -c "import drydocs.cli"`, `test_cli_import_order.py`,
  `test_cli_registry.py`, and `drydocs --help` listing your `cli_consumer` verbs last.
  Your monolithic `cli.py` is replaced by the take; every verb of yours must already be
  in `cli_consumer.py` before that commit, or it is gone.
  **FIFTH POSTSCRIPT:** the row you flagged as owed is added - `tests/unit/test_source_bindings.py`
  is `evaluate` on the `test_schema.py` shape (keep your automated-dataset count, take
  the drift-guard logic). Your binding outcome is the right one: a carrier is what the
  dataset's `system` field says, an origin that reaches the graph through a replica is
  not a carrier, and a system with no automated dataset needs no profile - the flag you
  left on the one real unbound carrier is the honest state, not a gap.
  **SIXTH POSTSCRIPT - your two chunk-4 questions, answered producer-side:**
  (1) *The seventeen dropped loader registrations.* Your option D was right - S16 gave
  `cli_consumer` a VERB seam and no DECLARATION seam, and `LOADER_REGISTRY.update()` from
  your side would have left `LOADER_SOURCE` and the unchained set stale exactly as you said.
  The seam now exists: `drydocs.cli_shared.register_loaders(registry, chains=..., unchained_exclusions=...)`,
  re-exported from the root, re-derives the views IN PLACE (the root re-exports the dict
  objects, so a rebind would strand every earlier import), refuses a name that would shadow
  a producer loader, and is proven by `test_cli_registry.py` in a subprocess with a fixture
  consumer. Call it ONCE at the top of `cli_consumer.py`, before your `app`, with your
  seventeen loaders and your own chains; `test_load_map_declarations` reads the composed
  root, so it holds over the union. Take `cli_shared.py`, `cli.py` and the test by name past
  the tag (or carry your option B until the next roll - it is a one-call swap either way).
  (2) *`:data_center` -> `:data_center_filter`.* Confirmed, behavior-preserving. And the
  contradiction you left standing is resolved in your favor: P6 is right, the G115 docstring
  was wrong - CM_DEF_VTAB carries the SHORT server code, CM_HOSTS / CM_AVG_RUN the LONG form,
  and the producer's own `controlm_folders.sql` comment agreed with you all along; the
  2026-07-22 probe profiled CM_AVG_RUN alone. Docstring and option help are corrected
  producer-side; the mechanism (a second bind carrying the short code from the DECLARED
  inventory, never derived from the string) is LOAD2. Until it lands, one `--data-center`
  value serves one family per run: short code for folders/jobs/variables, long form for
  hosts/avg-run - a long-form value against the VTAB family returns zero rows and reads as
  an empty data center, which is the failure to warn your operators about. Your per-DC
  shards were not silently empty by luck: P6 (the collision probe) still blocks the first
  multi-data-center load on both sides.
  **SEVENTH POSTSCRIPT - your two named debts after the S8 carve-out, both closed
  producer-side:** (1) `test_cli_registry.py` on a consumer tree: right, the fixture probes
  appended a fake module to `drydocs.__path__`, and where a REAL `cli_consumer.py` exists
  the package directory wins the import, so every probe silently exercised your module.
  The test now branches on whether `drydocs/cli_consumer.py` exists: the two producer-only
  facts (the producer ships none; absence is silent) and the fixture loader probe SKIP by
  name with the reason, and the two properties that hold for any consumer are asserted
  against the REAL module - its verbs are the last registered, and importing it first
  does not execute the root. Proven here by simulating a consumer tree (4 passed,
  3 skipped) and on the producer (7 passed). Take it by name. (2) The manifest row pinning
  `test_source_bindings.py`'s count landed at `02580f2c` (evaluate, the `test_schema.py`
  shape - keep your 17, take the drift-guard logic): the fifth postscript above. Nothing
  else from your report is outstanding on this side.

  **EIGHTH POSTSCRIPT - carve-out 6, three producer corrections (2026-09-04; your report
  is transcribed and verified in
  `docs/reviews/company-carve-out-6-readiness-review-2026-09-04.md` §6):** (1) The
  brackets at steps 305 and 308 called `tests/unit/test_backlog.py` canonical-producer.
  Its manifest row says per-entry and has since 2026-08-24; the brackets are corrected
  in place above and the row now names the split by NAME: the freeze block
  (FROZEN_SERIES / FROZEN_BAND, `_frozen_strays`, the agreement guards) is mechanism and
  crosses whole; the band block stays yours, in your spelling. Your
  `PRODUCER_BAND_CEILING = COMPANY_BAND_FLOOR - 1` is that rule applied exactly, and it
  diffs clean next roll. One forward note rides with it: COMPANY_BAND_FLOOR retires with
  the band rule (gate §C4, when PLAN2 ports) and `_frozen_strays` does not, so when the
  constant goes, pin PRODUCER_BAND_CEILING to a literal 9999 with the reason, or the
  freeze guard's band arm goes with it. (2) The step 305 addendum that every company-only
  module needs a `series:` code had no subject: `docmeta-acquire` is a component GROUP in
  `component_map.py` mapped to the already-registered `drydocs-docmeta` module, and your
  `modules.yaml` equals the producer's at 20 and 20. The rule stands for any FUTURE
  company-only module; the measurement retires the caution. (3) ITEM FILES ARE TAKEN AT
  THE TAG. "At `<sha>` or later" is a mechanism idiom — a guard or a module that changed
  past the tag is the same guard, newer — and it does not survive contact with a file
  whose `status` is data: CFG1 and CFG2 taken from HEAD arrive `done` while every
  artifact their acceptance names landed past the tag and outside your range (a board
  that lies), and PLAN2 taken from HEAD names a second gate prompt you cannot hold and
  turns a guard red. So: `docs/restructure/backlog/items/*.yaml` at `port-base-20260902`,
  always; a sha only where a postscript rules a take-by-name, and then for the named
  mechanism file alone. Your 642 baseline is the producer's item count at the tag to the
  id, so your range discipline already reads tag-pinned; this writes the rule where the
  next work order will read it. Also verified from your report: the two red tests
  (`KeyError: CFG2`) were slice closure — PLAN2 depends on CFG2 depends on CFG1 — and
  taking the transitive closure as clean-adds was the right move; that is the workplan's
  G5 firing for the second time, and its test (P2) is producer debt, not yours.

  **NINTH POSTSCRIPT - THE PRODUCER MUST NEVER PREDICT ONE OF YOUR IDS, AND TWICE NOW IT
  HAS (2026-09-04, from your carve-out 7):** a producer document said "`Idea-10018` next"
  and your allocator returned `Idea-10022`, because `Idea-10018`-`10021` were already
  taken in your history. You asked the tool instead of trusting the instruction and no
  duplicate was minted - which is exactly the I6 collision class, caught by the mechanism
  built for it. The defect is the producer's and it is a CLASS, not a typo: the producer
  holds no transcript of your inbox, so any producer sentence naming your next number is
  a guess dressed as an instruction, and a work order derived from it inherits the guess.
  **The rule, both directions: an id is obtained from `validate.py --next-id <series>` on
  the tree that will hold it, never read off a document.** Where a producer note needs to
  refer to your ids at all it cites ones you have REPORTED, by number, in the past tense.
  If a future work order names a specific next id, treat it as the error it is and run the
  allocator.

  **TENTH POSTSCRIPT - THE TWO CARVE-OUTS THAT REMAIN, AND THE ONE TRAP IN EACH
  (2026-09-04, written here rather than into a work order because a work order is where
  the `Idea-10018` prediction came from - the ledger is the channel):**

  **`web/**` - the trap is that a `derived` row sits INSIDE a canonical-producer tree.**
  `web/**` is canonical-producer, but `web/src/generated/**` is `derived` and its row
  comes FIRST (first match wins), so the generated subtree is REGENERATED on your side
  and never carried as bytes. This matters more than a usual derived row because
  `gates.json` carries GATE STATE: take it as a file and you import the producer's gate
  status into a surface your own console reads. Regenerate with `poetry run python
  scripts/render_board.py` (default paths refresh `gates.json`,
  `enforcement-matrix.json`, `load-map.json` and both load-map surfaces together), and
  run it AFTER every source it reads is merged, in one pass - the order the workplan
  already sets for renderers. Then `git diff --quiet` on the generated paths: a diff
  means a source did not land, not that the renderer is wrong. Your own chunk-1 report
  already found this class from the other end (the seven `web/src/generated/**`
  re-dispositions that moved `derived` 4 -> 11); this is the same fact at apply time.

  **The acronym sweep - the trap is a file class, not a string.** Two things the sweep
  must not do. (1) `config/gate-prompts/**` is **canonical-company**: your gate specs
  win and the producer's never cross. The producer's `cdo-crosswalk.yaml` reads SIGNED
  OFF 2026-08-05 with 13 confirmations by name; your twin reads DRAFT with a session
  pending. A sweep that rewrites that file from the producer's copy fabricates a company
  ratification that never happened, inside the file class `config/gate-log.md` cites as
  authority - and a dropped field is merely absent while a fabricated sign-off is
  present and confident. T24 (2) records that a partial application already imported a
  gate signature once; carve it out by hand. (2) The J55 guard derives the retired token
  at TEST TIME from `internal/cdo-reference/README.md`'s RENAMED sentence and never
  writes it, so on your tree that note must exist or the guard FAILS CLOSED - by design,
  and the design is yours: it was hardened on 2026-09-03 from your own chunk-1 report,
  where the README existed without the note and the guard skipped green on the tree that
  publishes. If `internal/` is absent entirely it SKIPS and says the skip proves nothing;
  if `internal/` is present the note is required. Authoring one sentence is the fix, and
  it is cheaper than reading a green skip as a pass.

  **Sequencing, unchanged and worth restating because it is counter-intuitive:** T24 (2)
  is DEFERRED out of the range and runs BEFORE the wipe-reload, not after - the wipe is
  precisely when the new names must already be in place.

  **ELEVENTH POSTSCRIPT - THE IDEA-SERIES RENUMBER PASS: LEAVE `Idea-10018`-`10021`
  WHERE THEY ARE (2026-09-05; from your research-tooling landing report, which found
  the collision and correctly did not execute the repair):**

  Your `feat/dd_lineage` branch appended `Idea-10006`-`10021`; your main independently
  minted `Idea-10009`-`10017` for different content, so twelve of the branch's ids
  collide and must move. Your own count says `10018`-`10021` are FREE on main. Do not
  move those four. "A single allocator pass from 10022" renumbers all sixteen and
  breaks a citation the producer cannot follow: **`Idea-10021` (F-1, the Control-M QR
  for jobs using MFTS 6) is cited by number here** - in a backlog item's acceptance
  (`C44`: "F-1 ... is company-band Idea-10021 and stays theirs"), in the `Idea-236`
  inbox entry, and in the transcribed `JOB-MFTS-MM-research.md`, the same document your
  branch-side inventory lists as `(10021)`. The citation channel is ONE-WAY by the
  standing rule - the producer cites your ids as reported and never renames them - so if
  `10021` moves, a producer item points at whatever you allocate there next. Renumber
  only `10006`-`10017`, keep the `(renumbered from ...)` marker on each moved entry (the
  shape your own `Idea-10009` already carries), and leave `10018`-`10021` untouched.

  The same inventory confirms the producer's OTHER company-band citations are safe:
  `10012` / `10015` / `10016` / `10017` are your main-native 09-03 mints and do not move;
  `10018` here is the prediction already recorded as wrong; `10022` is your allocator's
  own answer. `10021` is the producer's whole exposure.

  Two of your other conclusions are adopted producer-side rather than argued with. (1)
  Per-file by authorship, not a blanket rewrite: the main-native citations
  (`G116.yaml:21` "from Idea-10010", `G117.yaml:21` "from Idea-10011", `roadmap.yaml:93`,
  `cli_consumer.py:131`) are correct today and a `+13` sweep would break them while
  repairing the two files whose join keys point into the branch's numbering. (2) The
  pending-file pen: a research session writes candidate ideas to a per-branch pending
  file and the landing session mints them into `IDEAS.md` in one allocator pass. That
  removes the race rather than asking two sessions to be careful, and it is the shape
  the path-scoped extraction already handles as a clean-add. It is being minted here as
  the groom-backlog venue-and-band item, alongside the allocator gap your collision
  exposed on this side: the Idea path computes `highest + 1` and never consults the band
  ceiling that the item path enforces (`validate.py:363`), so the allocator that "refuses
  the company band by itself" does so for items only. Nothing is asked back.

  **TWELFTH POSTSCRIPT - THE RENUMBER PASS LANDED, AND THE PRODUCER'S RECORDS OF IT
  WERE ONE OFF (2026-09-05, from your report of `fix/idea-series-renumber` at
  `8c3541ee`, pushed and unmerged at the time of the report):**

  What landed, by your report and in the past tense: `Idea-10006`-`10017` moved to
  **`10023`-`10034`**, each with a `(renumbered 2026-09-05 from ...)` marker in the shape
  your `Idea-10009` already carried; `10018`-`10021` untouched and unmarked, so the
  producer's one citation (`Idea-10021`, C44 / Idea-236) stands; the band contiguous
  `10009`-`10034` with zero duplicates; per-file by authorship, so the main-native
  citations (`G116`, `G117`, `PLAN2.yaml`, `roadmap.yaml`, `cli_consumer.py`) were left
  as they were, correctly. Branched off carve-out 7 rather than main, which is why the
  numbers came out contiguous: carve-out 7 had minted `Idea-10022` and edited `IDEAS.md`,
  so a branch off main would have collided at the append point AND taken a number already
  spoken for.

  The producer's records said `10022`-`10033`. That was the range the plan implied before
  `10022` was counted as already taken, and it went into the `idea-series-grammar` record
  (signed 9/9 the same morning) and its prompt header as "by report". Both now carry a
  dated CORRECTION postscript; no clause moves, because C1 rules the SHAPE of a band idea
  from an undeclared venue and the shape is the same at `10023` as at `10022`. This is the
  NINTH POSTSCRIPT's class again in a milder form - not a predicted next id, but a
  predicted RANGE, written from a plan instead of a landing. The rule that follows is the
  same one: the producer records your ids after they land, from your report, never from
  the plan that preceded it.

  Two things you told your own port thread are recorded here only so this ledger does not
  contradict them: your next free idea id was `10035` at the report, and the order that
  keeps the numbering monotonic is 6 -> 7 -> the renumber branch -> 8 -> 9. Both are yours
  to run, and the number is already stale by the time anyone reads it - an id is obtained
  from `validate.py --next-id Idea` on the tree that will hold it (NINTH POSTSCRIPT).
  Nothing is asked back.

  **THIRTEENTH POSTSCRIPT - ONE MANIFEST ROW, ADDED BETWEEN THE RANGE AND THE NEXT ROLL
  (2026-09-05):** `config/taxonomy/data-centers.yaml` (LOAD2, the short-code / long-name
  data-center spelling registry) now has a `per-entry` row on the `lob-product-team.yaml`
  shape - rows keyed by `code`, your real rows stay, the producer's `sample: true` rows
  never overwrite them, header / schema / field list cross whole. Without it the file fell
  through to the `config/**` canonical-producer default, the third instance of the class
  that dropped `lob-product-team.yaml` rows once and drove `test_source_registry` 1 -> 7.
  It does not reach carve-outs 8 or 9 (neither takes the manifest), and the file itself is
  after `port-base-20260902`, so at the next roll it arrives as a clean-add and the row
  first does work the roll after, when your real rows exist. `editions.yaml` and
  `domains.yaml` already had their rows. Nothing is asked back.

  **FOURTEENTH POSTSCRIPT - CARVE-OUT 8 IS WIDER THAN `web/**`, AND THE TENTH POSTSCRIPT
  UNDERSTATED THE RENDER CHAIN (2026-09-05, from your carve-out 8 scoping report; the
  widened scope is CONFIRMED):** `web/src/generated/**` is `derived`, and three of its
  seven changed artifacts are written by renderers that live OUTSIDE `web/**`:
  `scripts/render_gazetteer.py` (reads `config/taxonomy/location-gazetteer.yaml`,
  classification External), `scripts/render_remediation_profile.py` (self-contained) and
  `scripts/render_world_map.py` (reads `external/geo/world-atlas/countries-110m.json`).
  Each has a drift guard that REGENERATES and compares (`test_location_gazetteer`,
  `test_remediation_profile_json`, `test_world_map_generated`), so taking the bytes without
  the renderers leaves three guards red with no way to green them - the renderers are what
  the disposition means. All are clean-adds in the range (`scripts/**` is evaluate, which
  is moot for a file you do not have; take `external/geo/**` as a directory, its
  `SOURCE-MANIFEST.md` and `LICENSE` ride with the data). Two corrections to the tenth:
  (1) **take `scripts/render_board.py` too.** At the port base it already chains
  `render_gazetteer`, `render_remediation_diff` and `render_remediation_profile`
  (`render_board.py:59-90`); yours "writes five of seven" because your copy is behind the
  base, and it will stay behind on every future render until it crosses (hand-merge if you
  edited it, wholesale otherwise). (2) **`world-map.ts` is deliberately NOT in that
  chain** (`:76-78`: its input is vendored data that changes only when someone moves
  editions) - run `poetry run python scripts/render_world_map.py` separately. So the pass
  is: `web/**` minus generated (wholesale) -> the three renderers + `render_board.py` ->
  the two inputs -> `render_board.py` AND `render_world_map.py` -> `git diff --quiet` on
  all seven generated paths -> the three drift guards green. Nothing is asked back.

  **FIFTEENTH POSTSCRIPT - WHEN PLAN2 PORTS, YOUR ALLOCATOR ASKS FOR YOUR EDITION
  (2026-09-05; PLAN2 built, not yet in a port range):** `.claude/**` is canonical-producer,
  so `validate.py` becomes the PLAN2 allocator on your side at the next roll. It reads
  `config/dev-environment.yaml` `edition:` - your copy, canonical-company, never overwritten
  by a port - to know which edition it mints into. Until that key names the code your own
  edition gate mints into `config/taxonomy/editions.yaml`, `--next-id --module <m>` REFUSES,
  and the refusal names the key and both files: that is §C4 as signed ("the company mints
  nothing new until it has minted its edition code"), not a defect. `--next-id Idea` still
  answers, band-shaped above 9999 - the shape `Idea-10009`-`10034` already have - until the
  key is set (rider idea-series-grammar C1). The number band and the DD reserve retired
  forward-only; nothing you hold moves, and `G10001`-`G10003` / `DD10001`-`DD10003` stay
  legal under FROZEN_BAND. Once the key is set, your items mint `<code>-<MODULE><n>` and
  your ideas `<code>-Idea-<n>`, counting from 1 in your own inbox of numbers. The producer
  cannot name your code (CFG2 c) and does not. Nothing is asked back.

  **SIXTEENTH POSTSCRIPT - "TAKE `render_board.py` TOO" MEANT ITS WHOLE CHAIN, AND TWO OF
  THE CHAIN'S INPUTS ARE PER-ENTRY (2026-09-05, from your carve-out 8 apply notes):** at
  the base `scripts/render_board.py` imports and runs TEN renderers - `render_gates`,
  `render_enforcement_matrix`, `render_load_map`, `render_software_registry`,
  `render_context_types`, `render_gazetteer`, `render_remediation_diff`,
  `render_remediation_profile`, `render_ideas`, `render_roadmap` - so taking it means each
  renderer at the base AND each renderer's input at its manifest ROW, not wholesale. The
  fourteenth named the two `web/**` inputs and stopped there; that is the sentence that
  left you finding the rest by running the chain. Two of those inputs are per-entry, and
  you hit both: (1) `docs/restructure/roadmap.yaml` HAS a per-entry row (structure from the
  producer and any module you lack; YOUR stage / built / remaining / estimate judgments and
  your `drydocs-libs` / `drydocs-port` modules stay on collision) - the wholesale take was
  a misread of the manifest, not a gap in it, and what you then did (restore your file,
  sweep only the acronym) IS the row's rule. (2) `config/taxonomy/software-registry.yaml`
  had NO row and fell through to the config/** default - the producer's omission, the same
  class as source-registry at the 2026-09-01 apply - so the wholesale take that dropped
  your `servicenow` vendor and product rows was the manifest working as written, and
  wrong. A per-entry row exists now (rows keyed by `id` union; a row one side holds stays;
  `seal_id`, `drydocs_application_id` and `used_by_drydocs` are yours; `acronyms` is the
  producer's authoritative home at the O68 (d) shape, which is also why the render broke on
  your pre-O68 copy). Carve-out 8 does not take the manifest, so the row reaches you at the
  next roll; your restore is what it prescribes. ONE COUNT TO RE-READ: at
  `port-base-20260902` the producer's registry is 14 vendors / 16 products; the `axway` /
  `mfts` rows are C43, 2026-09-03, OUTSIDE the range. 15 / 17 reconciles as 14 + servicenow
  and 16 + servicenow only with axway ABSENT - so either your file has no axway and "the
  producer added the Axway/MFTS row" misattributed the seventeenth product (the numbers
  are right, the explanation was not), or it has axway, the input was taken past the base,
  and one servicenow row is still missing (16 / 18 is then the target). The file says
  which; `grep -c "id: axway"` settles it. The backlog items swept acronym-only with your
  status intact is the items row's Clause 4 rule, correctly applied. Nothing is asked back.

  **SEVENTEENTH POSTSCRIPT - THE COUNT CHECK WAS ANSWERED, AND THE ANSWER SHOWS WHY A COUNT
  IS NOT A COMPOSITION (2026-09-05, from your carve-out 8 close report):** `id: axway` -> 0,
  so the first branch held: your numbers were right and the Axway attribution was not. But
  the render you then reported - **15 vendors / 16 products, "the company's original"** - is
  the PRE-RANGE file grafted back, and the range is not empty for this file: O81 (2026-08-31,
  inside port-base-20260826..20260902) added the `neo4j-nvl` product row, 15 -> 16 at the
  producer. Your original was 15 + `servicenow` = 16; the per-entry rule (a row one side
  holds stays) makes the landed target **15 / 17**, and 16 matches the producer's base count
  only by coincidence - `servicenow` standing where `neo4j-nvl` should. A count cannot see
  that; `grep -c "id: neo4j-nvl" config/taxonomy/software-registry.yaml` can, and 1 is the
  answer. It is not cosmetic: `test_software_registry.py::
  test_web_console_stack_matches_the_locked_site_plan` at the base asserts `neo4j-nvl` in the
  web-console stack, and `test_docs_coverage.py`'s 16/14 pin passes on your file for the
  wrong reason. Add the row from the base (`git show port-base-20260902:config/taxonomy/
  software-registry.yaml`, the `neo4j-nvl` block under `products`), keep `servicenow`.
  **The gap you found is real and the fourteenth caused it:** it named the three drift
  guards as bare stems in parentheses, and the paste repeated them, so they read as test
  functions when they are FILES - `tests/unit/test_location_gazetteer.py`,
  `test_remediation_profile.py`, `test_remediation_profile_json.py`,
  `test_world_map_generated.py` - in the tree since 2026-08-22 / 08-25 / 08-31 and never
  listed as part of the carve-out. `tests/**` is evaluate-on-collision, which is moot for
  a file you do not have: clean-adds, taken at the base, as you did (45 passed). One
  wording correction to your report, so the ledger does not carry it: the guards had "no
  guard on either side" is not so - they existed producer-side with their artifacts; they
  were absent on yours because the scope note left them out. Everything else on the list
  closed as written. Nothing is asked back.

  **EIGHTEENTH POSTSCRIPT - THE CLOSE-OUT IS READ, THE RANGE IS CLOSED, AND TWO PRODUCER
  CLAIMS ARE WITHDRAWN (2026-09-05, from your PORT-REPORT on `port-base-20260902`,
  COMPLETE at your `4d9ddba7`):** `[SME-REPORTED]` for what your report measured;
  `[VERIFIED-PRODUCER]` for what changed here. Your acceptance method is the right one and
  is now the skill's method: `--lf` on the branch, a detached worktree at your main sha run
  with the MAIN repo's interpreter, and a set-compare of the two failure lists - 21 against
  21, identical, the one order-dependent test named. A COUNT of failures proves nothing
  (the seventeenth postscript said why for rows; it holds for tests); a set-compare does.
  **THE FINDING FOR THE SME - accepted, and the manifest row is rewritten
  [VERIFIED-PRODUCER]:** the K7-K15 hold on `AppCodeCascadePane` was stale. Your tree
  carried the route row and the route file before carve-out 8 began, and honoring
  "producer MINUS the held row" would have failed three guards on your side at once. The
  `config/taxonomy/ui-components.yaml` entry_rule now reads rows-union, counts tracked per
  side, hold retired. The hold's subject was always the LOAD (`m3_belongs_to_application`
  stays planned your side, T23 family), never the taxonomy row - a component that exists
  is classification, and classification is not gated. Your 40/88 is the producer's 40/88
  at `08af6985`. Nothing to do on your side; the row reaches you at the next roll and
  describes what you already hold. The row also records why it went stale: an entry_rule
  may describe the producer's tree, and one that describes the CONSUMER's ("company =
  producer minus X") is stale the moment the consumer moves - and only the consumer can
  see that it did.
  **THE PREMISE CORRECTION - accepted, and three producer sentences are corrected in
  place [VERIFIED-PRODUCER]:** `internal/**` is `default_ok`, and its recorded reason says
  the private company remote is exactly where Internal content belongs. So
  `internal/cdo-reference/README.md` reached you as a clean-add carrying its own RENAMED
  note, J55 reads it, and nobody authors a second one. RELAY-21's "`internal/**` ... never
  crosses", RELAY-25's Q2 answer, and step 303's note on the two `internal/research/` logs
  were wrong for one reason: they read "never publishes" (true - never to a public mirror)
  as "never crosses" (false - a private remote is not a mirror). Each now carries a dated
  correction beside the original. The J55 docstring says "never publishes" and was right
  all along.
  **YOUR THREE MISTAKES ARE THE SKILL'S RULES NOW [VERIFIED-PRODUCER]:** the reconcile-port
  skill carries them in your words. (2) Run the affected suites BEFORE a package-level
  take: `drydocs_api/**` is `default_ok`, and "hand-merge on collision" is not "take the
  package". (3) For a themed sweep, apply the DELTA to the company file and take whole
  files only from the certified tag: a mid-range commit's file is the tree at that commit
  and carries every earlier commit with it. (1) was already the software-registry
  per-entry row and the seventeenth postscript. On the `script-scm-status` row you backed
  out: it is G61 (2026-08-25, gate `script-provenance-gaps`, proposed and unsigned) and
  predates the range - a gate-bound map row your own gate rules on, so backing it out of
  an acronym sweep was right.
  **THE PERSONAS RESOLUTION** - one user-tier seat, the two producer demo rows dropped, the
  SME persona relabeled, the O69 mechanism kept whole - is a relabel under the
  `drydocs_api/**` hand-merge rule and is yours; the producer's roster is its demo roster
  and nothing here revisits it. **YOUR SEVEN QUESTIONS** were answered in RELAY-25; your
  Q2 strike-through supersedes that relay's Q2, as above, and Q1's cypher is the chunk-4
  union clean-add RELAY-25 already names. Nothing is asked back.

- **RELAY-26 — THE SIXTH ROLL, `port-base-20260902..port-base-20260905`: WHAT IT CARRIES
  FOR YOU, AND THE FOUR DECLARATIONS ONLY YOU CAN MAKE** (new 2026-09-05, at the roll).
  `[VERIFIED-PRODUCER]` throughout — every sha here is on the producer's `main` under the
  new tag, and nothing here restates a ruling that is yours.
  **THE RANGE:** 186 commits at the tag, 132 of them in ledger steps 313–333 (the rest are the ritual
  patterns `port_preflight.py` already recognizes); **323 changed paths across 8 classes**,
  the table is in the disposition section above. Your `port-base-20260902` apply is
  COMPLETE at your `4d9ddba7` (EIGHTEENTH POSTSCRIPT), so this is one range, tag..tag,
  with no parked apply behind it and nothing hand-carried. Lane B's three in-flight
  branches (API1, WEB3, WEB4) are NOT in it — their claims are, their work lands next roll.
  **THE PROMISED FIXES ARE IN IT (step 328):** the publishing shim that aliases every
  submodule, the seven `drydocs/cli_*.py` canonical-producer rows, J55 fail-closed
  (`40d2461d`), the software-registry per-entry row (`0003ea28`), the data-centers
  per-entry row (`f2ec87db`), the ui-components row rewritten as rows-union with the hold
  retired (`920a4107`), and `drydocs.cli_consumer` as an ENTRYPOINT in `component_map.py`
  (`30d2e870`). Each one describes something you already did by hand during carve-outs
  6–9; taking it retires the hand edit and nothing else.
  **FOUR DECLARATIONS ONLY YOU CAN MAKE** — each is per-side DATA inside a mechanism that
  crosses whole, and none of them is written for you by any file in this range:
  (1) `edition:` in your `config/dev-environment.yaml` (PLAN2, step 332; the file is
  canonical-company). Since `43fd345c` a venue with no `edition:` key mints NO item and
  the refusal names the key; your idea channel stays open meanwhile (the gate's C1, the
  shape your 09-05 renumber already has). Your code is yours to choose.
  (2) Your rows in `config/taxonomy/editions.yaml` (CFG2, step 332; per-entry) — replace
  the two `sample: true` rows with your real editions keyed to `area_product_id`; the
  collision check and the `:AreaProduct` resolution are pure functions your suite drives
  with your inputs.
  (3) Your `CEILING` in `tests/unit/test_publish_boundary_history_ceiling.py` (J74, step
  326; per-entry, row added this roll). The producer's 34 was measured on the producer's
  2,057 commits; your history is disjoint. Run the test's own log command, set your
  number with the recorded reason, take the mechanism whole.
  (4) Your company-only YAML files in `CLASSES` of `tests/unit/test_config_identity_header.py`
  (J58, step 327; per-entry, row added this roll). The walk is default-deny over EVERY
  tracked YAML, so it goes red on arrival by design; each entry is a path prefix, a class,
  and a reason. The two new manifest rows exist so that the `tests/**` default cannot
  revert (3) and (4) at the port after this one — the `test_backlog.py` shape.
  **YOUR OWN CARRY-FORWARD, IN THIS RANGE'S TERMS:** `PRODUCER_BASELINE` in
  `tests/unit/test_backlog.py` becomes `port-base-20260905` and
  `tests/unit/producer_backlog_ids.txt` regenerates from it in the same commit, as a STEP
  of the apply, not a fix after it; `scripts/port_backlog_union.py --producer-ref
  port-base-20260905` exits 0 before any per-entry class begins; `RECONCILE_BEFORE_DIR`
  armed for the reconcile tests; items are taken AT THE TAG, never "or later" (EIGHTH
  POSTSCRIPT); workplan references re-pointed to the new tag. T24 (1) — the vocabulary
  fragments — stays the G87 add-new + deprecate shape you used in chunk 5.
  **TWO GATE PROMPTS ARRIVE DRAFT** into your canonical-company directory as clean-adds:
  `idea-series-grammar` (SIGNED 9/9 producer-side on `de8159eb`; the gate-log record
  union-appends, the prompt reads DRAFT on your tree — as `cdo-crosswalk` did, TENTH
  POSTSCRIPT) and `controlm-folder-identity-grain` (`863c6733`, DRAFT on both). Your
  sessions rule them; producer sign-off is not company sign-off.
  **THE LINEAGE CLUSTER GREW (steps 325, 330):** LIN1/LIN2 (`drydocs lineage-extract` /
  `lineage-load`, `drydocs_lineage/staging.py`, a `curated` zone in `data_root.py`) and Z4
  (`drydocs_lineage/extractors/lb_resolution.py`) are the largest additions since the 2026-08-26
  continue-defer. They are the adoption dossier's next chapter, not a take, and nothing in
  this relay changes that strategy — the call is yours.
  **YOUR PERSONAS RELABEL MEETS THREE PRODUCER CHANGES UNDER `drydocs_api/**`:** O70
  (`schemas.py` new, `app.py` reshaped for the generated client, step 316), R9
  (`agent_query.py` new, `execute_spec` extracted, step 317), and the O87 SME-seat badge
  in the console reads `SME_PERSONA_ID` from the roster, so your `sme` id is what it shows
  (step 320). Hand-merge on collision, never take the package — your rule 2, now the
  skill's. The generated `web/src/generated/openapi.json` and `api.d.ts` are DERIVED:
  regenerate from your `drydocs_api`, never carry the producer's.
  Nothing is asked back.

- **RELAY-27 — `scripts/reconcile_before.py` EXISTS ON BOTH SIDES WITH TWO SHAPES, AND
  YOUR DURABLE BEFORE-DIR NEEDS ONE FILE BEFORE THE SEVENTH ROLL'S GUARDS READ IT** (new
  2026-09-07, mid-apply; acts at the NEXT roll, nothing here changes the range you are in).
  `[VERIFIED-PRODUCER]` — the producer built `scripts/reconcile_before.py` over
  `drydocs/port/reconcile_before.py` at `2aa90898` on 2026-09-05, AFTER `port-base-20260905`
  (`5cad5653`) was cut: the tag holds neither file and its `.claude/skills/reconcile-port/SKILL.md` never
  names the script, so nothing in your current range mentions it. The producer shape: ONE
  call writes the four mandatory before-files the J7/J16 guards read
  (`relationship_vocabulary.yaml`, `taxonomy-ontology-map.yaml`, `backlog.yaml`,
  `gate-log.md`), the two optional J51 lists when their modules import, and a one-line stamp
  **`BASE.sha`** — the full 40-hex sha of the commit snapshotted. It refuses a dirty source.
  `tests/unit/test_port_reconcile_guards.py` (`77cae33a`) runs
  `test_reconcile_before_dir_stamp_describes_this_tree_live` FIRST and fails BY NAME on a
  before-dir with no `BASE.sha`, a sha that does not resolve, one that is not an ancestor of
  `HEAD`, a `gate-log.md` that differs from `git show <sha>:config/gate-log.md`, or a sha
  that is not where the apply branch left `main` (J76 — the phantom 22nd baseline failure of
  2026-09-05 was a before-dir from the EARLIER apply that outlived a skipped teardown).
  `--describe` prints the line the PORT-REPORT carries.
  `[SME-REPORTED]` — during this apply you wrote your own `scripts/reconcile_before.py`
  (`--repo <tree> --dest <dir>`, a `SNAPSHOT-META.txt` with taken_at / head sha / describe
  / subject; commit `a4603b7e` on your apply branch), took a durable before-dir OUTSIDE your
  data root, verified all six files SHA256-identical to your pre-apply tag's tree, and set
  `RECONCILE_BEFORE_DIR` at **User** scope so it survives a reboot. If none of that is on
  your branch, this relay's second and third paragraphs do not apply and the first is a
  clean-add at the next roll; nothing else changes.
  **WHAT HAPPENS AT THE SEVENTH ROLL IF NOTHING IS DONE:** `scripts/**` is `evaluate`, so
  the two `scripts/reconcile_before.py` files COLLIDE and hand-merge (your rule; the
  producer's is a 61-line wrapper over the `drydocs/port/` module, which arrives as a
  clean-add). `tests/**` is DEFAULT, so the guard arrives as written — and your durable
  before-dir has NO `BASE.sha`, so the stamp test fails by name against a snapshot you
  cannot retake, because the apply has moved the tree. That failure would be the
  INSTRUMENT, not the subject (J76).
  **THE ONE-FILE FIX, YOURS TO APPLY WHEN THE SEVENTH ROLL LANDS (not before — the guard is
  not on your tree yet):** write your pre-apply commit's FULL 40-hex sha, one line, no
  newline required, to `BASE.sha` inside the durable before-dir. That commit is the one
  your `pre-cewilson-port-20260905`-shaped tag points at — the tree your six files were
  verified against. Then every one of the five checks passes on that dir: the sha
  resolves, it is an ancestor of your branch's `HEAD`, it is where the branch left `main`,
  and the `gate-log.md` you already proved byte-identical equals `git show <sha>:config/
  gate-log.md` by construction. Keep `SNAPSHOT-META.txt` beside it — the producer's
  `write_snapshot` ignores files it did not write and the guards read only what they name.
  When the two scripts hand-merge, keep the producer's stamp and refusals (the guards
  import `drydocs.port.reconcile_before`, so the module's contract is the one that
  matters) and carry your `--repo` argument and your META file forward if you want them;
  they are additive.
  **THE TEARDOWN CONSEQUENCE, WHICH YOU FOUND FIRST:** a User-scope `RECONCILE_BEFORE_DIR`
  outlives its directory far more easily than a process-scope one, and the guards then
  FAIL on set-but-unusable, they do not skip. The producer skill's step 4 now says so
  (`[Environment]::SetEnvironmentVariable('RECONCILE_BEFORE_DIR', $null, 'User')` beside
  `Remove-Item Env:`), taken from your report. Nothing is asked back.

- **RELAY-28 — THERE IS NO `-fork` TAG, AND THE DISPOSITION RENDERER NOW REFUSES A REF THAT
  DOES NOT RESOLVE INSTEAD OF WRITING "0 PATHS"** (new 2026-09-07, mid-apply; acts at the
  NEXT roll, nothing here changes the range you are in). `[SME-REPORTED]` — your carve-out D
  plan named `port-base-20260905-fork` as the render base; your Phase 0 check found no
  `-fork` tag of any date and STOPPED before applying; you tabled what the tree holds (your
  pre-apply branch point, `port-base-20260902`, `port-base-20260905`), measured the candidate
  ranges (323 = producer delta this roll; 1511 = full divergence since your branch point; 211
  = already applied by A/B/C/C2) and chose the 323 range. That choice is right, and so was the
  method. The producer cuts ONE tag per roll, `port-base-<date>`, and never a `-fork`; the
  other end of a consumer range is YOUR ref — the pre-apply branch point your own tag marks
  — which the producer cannot name because it does not exist here. The 1511 range is the
  STANDING divergence, worked as dispositions across rolls and never an apply range; the
  range a roll brings is `<previous port-base>..<this port-base>`.
  `[VERIFIED-PRODUCER]` — the same plan exposed a producer defect: on the producer tree at
  `55c2a204`, `scripts/render_port_dispositions.py port-base-20260905-fork port-base-20260905`
  wrote the dispositions file with `0 paths` and exited 0, because `_git` swallows a failed
  `git diff` into an empty string — the instrument failing into clean (J76). Fixed at
  `df7a57c3`: both refs are checked with `git rev-parse --verify` before the diff; a ref
  that does not resolve is named on stderr, exit 1, nothing written. Pinned by
  `test_a_ref_that_does_not_resolve_is_refused_by_name_not_rendered_empty` in
  `tests/unit/test_port_dispositions.py`. When the seventh roll lands, the two-argument
  consumer form you already use (`<your pre-apply ref> <port-base tag>`, see step 333)
  refuses a typo'd ref for you; your Phase-0 table is still the right thing to keep doing,
  because the renderer checks that the refs EXIST, not that they are the right two. Nothing is
  asked back.

- **RELAY-29 — `classification:` IS A SIDE-LOCAL JUDGMENT, AND THE J58 HEADER MADE IT A FIELD
  A PER-ENTRY TAKE CAN CARRY: ON EVERY per-entry ROW THE VALUE IS YOURS** (new 2026-09-07,
  mid-apply; acts at the NEXT roll — at D you have already ruled it correctly).
  `[SME-REPORTED]` — your merge of `docs/restructure/roadmap.yaml` first took the producer's
  new `classification: Internal-Public` verbatim, beside your own header comment reading
  Internal; your reviewer caught it and the session fixed it to Internal with the reason
  inline, then audited `config/source-bindings.yaml` and the vocabulary `00-header.yaml`
  and kept both Internal-Public on a content-not-path test: real firm data (production DC
  names, rosters, real object names) → Internal; mechanism-only → Internal-Public. That
  discriminator is the producer's too, so those two are consistent, not a second exception.
  `[VERIFIED-PRODUCER]` — J58 (`182523e7`, 2026-09-05) added the `schema` /
  `classification` / `updated` triple to every governed YAML. Before that no manifest row
  had to say who owns `classification`, because a comment does not cross on a per-entry
  take; a field does. One row said the wrong thing: `config/taxonomy/software-registry.yaml`'s
  entry_rule listed `classification` among the producer mechanism that crosses whole.
  Corrected at `df7a57c3`, and the rule is written once on that row for every per-entry
  YAML: **`schema` is the producer's (mechanism), `classification` is the consumer's
  (judgment about what THIS tree's rows hold), `updated` is the row owner's.** The
  producer's repo is outside the firm, so its Internal-Public means "publishable from the
  producer's public mirror" and says nothing about the same file on your tree. The same
  commit fixed the producer's own `docs/restructure/roadmap.yaml`, where the 2026-08-07
  header comment read Internal beside the 2026-09-05 field reading Internal-Public — the
  contradiction you found inside one file was on the producer's tree first, and there the
  FIELD is the one that is right (the file is in the public push). Nothing is asked back.

- **RELAY-30 — THE GATE-PROMPTS CLEAN-ADD IS NOW AN `entry_rule`, AND THE COUNT IN THE
  REPORT IS THE COMMIT'S, NOT THE ENUMERATION'S** (new 2026-09-07, mid-apply; acts at the
  NEXT roll — at D you already did the right thing on a note). `[SME-REPORTED]` — your
  carve-out D enumerated every slug your items' `gates:` name, found the prompts missing
  (all present at the tag, none yours), took them, and flagged that the take reached into a
  `canonical-company` row on the strength of that row's `note:` alone. You then found the
  reported count was wrong by one — the commit holds ten files, the enumeration found nine
  AFTER the first was taken on a direct ruling — and reconciled ten against the six new
  `prompt-only` gates.json entries: six with no prior gate-log record, three whose gates
  the log already carried (file missing, no new entry), one a RIDER that renders no page of
  its own. That reconciliation is correct and is now the rule's own text.
  `[VERIFIED-PRODUCER]` — at `PORT-MANIFEST.yaml` the `config/gate-prompts/**` row carries
  an `entry_rule` (promoted from the note this day): consumer specs win and are never
  overwritten; a producer slug the consumer does not hold crosses whole, because
  `test_declared_gates_are_lists_of_known_prompt_slugs` requires every declared slug to
  resolve and `gates.json` is derived from the files present; enumerate from `gates:` plus
  the gate-log citations minus the files on disk; a rider crosses the same way; and the
  count reported is `git show --name-only`'s. A note explains, an entry_rule authorizes —
  the inference you had to flag is the rule you will read next roll. Nothing is asked back.

- **RELAY-31 — TWO `test_backlog.py` TESTS READ THE PRODUCER'S VENUE FILE, AND ONE OF YOUR
  TWO "DELIBERATE" EDITION-ABSENT REDS WAS A PRODUCER DEFECT** (new 2026-09-07, mid-apply;
  acts at the NEXT roll — leave both red as they are, the fix arrives with the range).
  `[SME-REPORTED]` — after removing `edition:` on the producer's ruling, your suite showed
  two edition-absent failures in `tests/unit/test_backlog.py` and you recorded both as the
  intended state until your edition gate mints a code. `[VERIFIED-PRODUCER]` — only ONE of
  them is that. `test_next_free_is_max_plus_one_and_never_fills_a_gap` called
  `alloc.next_id("PLAN", taken)` with no `venue=`, so it read the live
  `config/dev-environment.yaml` and hit the allocator's refusal before it ever counted;
  its siblings pin `venue="base"` and it now does too. The gap rule was never red — the
  test was reading the wrong instrument (J76). The other,
  `test_the_venue_is_declared_in_the_venue_file_and_the_producer_is_the_base`, asserted
  two things in one test — that the allocator reads the file faithfully, and that the file
  says `base` — and the second is a fact about the PRODUCER's tree, red on every consumer
  tree by construction (undeclared until your gate, then declared as your own code; the
  PORT3 shape). Split at the producer: `..._reads_the_venue_from_the_venue_file_and_nowhere_else`
  pins the READ and passes on any tree, declared or not; `test_the_producer_declares_itself_the_base`
  carries the producer-only fact and says in its docstring that a per-entry take drops it.
  Replayed on the producer tree with `edition:` commented out: the gap test and the read
  test pass, the producer-fact test fails, by name. When the range lands, take the two
  fixed tests, drop the one that names itself producer-only, and your `test_backlog.py`
  edition-absent count goes from two to zero — your edition gate then owes nothing to the
  suite, only to the allocator. Nothing is asked back.

- **RELAY-32 — A NEVER-PORT SKILL'S TEST IS NEVER-PORT TOO, AND `domain:` ON A SHARED
  VOCABULARY ENTRY IS THE PARTITION KEY** (new 2026-09-07, mid-apply; acts at the NEXT
  roll — at G you already did the right thing). `[SME-REPORTED]` — your carve-out G dropped
  `tests/unit/test_lane_handoff.py` rather than naming it, because its subject
  `.claude/skills/lane-handoff/scripts/handoff.py` is `never-port` while the test fell to
  the `tests/**` default_ok, and you named the contradiction: two rows disagree and nothing
  catches it. You also declined an overlay `row_may_match_nothing` entry because
  `tests/**` matches plenty. `[VERIFIED-PRODUCER]` — both readings are right, and the fix
  is producer-side: `PORT-MANIFEST.yaml` now carries a `never-port` row for
  `tests/unit/test_lane_handoff.py` beside the skill's row, with its own
  `row_may_match_nothing` entry (company-side the test never exists, by construction — the
  skill's own shape), and `test_port_manifest.py` holds the invariant as
  `test_no_test_is_more_portable_than_its_never_port_subject`: for every never-port row
  under `.claude/skills/<x>/`, no tracked `tests/unit/test_<x>*.py` may resolve to a
  portable disposition. It was the first test in the tree whose subject is never-port.
  Second, `test_domain_registry` (3 red) is NOT a rename that slipped through D.
  `controlm -> scheduler` and `seal -> business-application` are real producer renames at
  `496aa268` (2026-08-12, `port-base-20260817`, four rolls ago); `corporate`, `itsm`,
  `infrastructure` and `human` were ADDED, never renamed from anything; and the producer has
  never had a `company` or `snow` domain — those two are YOUR domain values on YOUR
  entries. The vocabulary row's `entry_rule` never said who owns `domain:` on a shared id,
  so a per-entry merge that kept `domain: controlm` for four rolls followed the rule as
  written; it now says `domain:` is the partition key, a gate-ruled rename travels with the
  entry, and a domain only one side has registered in `config/taxonomy/domains.yaml` is
  that side's mint. Which makes your three reds a RULING your own manifest already
  describes (`domains.yaml`, per-entry: the company base mints ITS OWN domains at ITS OWN
  gate): register `company` and `snow` as `minted_by: company` rows, or adopt
  `corporate` / `itsm` through your own vocabulary-domains gate — never rename the fragments
  to the producer's names to make the test pass, because that re-rules a domain without a
  gate. The `scheduler` / `business_application` half takes the producer's `domain:` with
  the entry at the next roll under the amended rule. Nothing is asked back.

- **RELAY-33 — THREE POINTERS FROM THE G CLOSE: THE INTERLOCK TEST HAS A PRODUCER TWIN, THE
  `ideas.html` OVERLAY ENTRY WENT STALE AT E, AND A WORKTREE BASELINE MOVES ONE TEST** (new
  2026-09-07, mid-apply; nothing here waits for the roll). `[SME-REPORTED]` —
  `test_bundled_demo_interlock` (Z7) is red because your PAT sample's teams own no
  application any folder runs for; the sample is `never-port` and yours to fix, deferred.
  `[VERIFIED-PRODUCER]` — the producer's bundled samples fail the same contract the other
  way round (the SEAL capture declares three applications, the sample folders carry seven
  other ids, one folder attributes) and that is backlog item LOAD4, in build this week; the
  test's expectation — the bundled samples must reference EACH OTHER — is the contract,
  and each side fixes its own fixture under `drydocs/data/**` never-port. Second,
  `[SME-REPORTED]` your overlay's `row_may_match_nothing` entry for `docs/plan/ideas.html`
  says you do not render that surface, yet E's `render_board.py` run moved it.
  `[VERIFIED-PRODUCER]` — a default-paths `scripts/render_board.py` run imports and runs
  `render_ideas.main()` and the producer row for the page is `derived`; the entry stopped
  being true the moment the renderer ran, and retiring it is overlay housekeeping on your
  side. Third, `[SME-REPORTED]` a fourth "turned green" at G was
  `test_repo_paths::test_swept_defaults_resolve_inside_a_real_worktree`, and you recorded
  it as a venue artifact because the baseline ran inside a worktree. `[VERIFIED-PRODUCER]` —
  that test spends a real `git worktree add` (J48 (b)) and is venue-sensitive to running
  inside one; the reconcile-port skill's set-compare step now names it: exclude it by name
  or take the baseline from a plain checkout. Your refusal to bank it was correct. Nothing
  is asked back.

- **RELAY-34 — TWO VERDICTS FROM YOUR LINEAGE WORKTREE READ A TREE BEHIND THE BASE, ONE
  REGISTRY ROW CARRIES A DUPLICATE KEY, AND TWO GATE PROMPTS WERE CORRECTED IN PLACE** (new
  2026-09-07, mid-apply; nothing here waits for the roll). `[SME-REPORTED]` — a sweep on
  your lineage worktree (one commit past an old main) reported the data-flow-overview
  gate's "`:DataFlow` plus five edges registered planned" as false and the
  controlm-folder-identity-grain gate as non-existent. `[VERIFIED-PRODUCER]` — both are
  in `port-base-20260905`: the `DataFlow` label and the five architecture and docs edges
  are registered `planned` in the per-domain vocabulary fragments (the 2026-08-21 commit
  that closed the drafting item), and the folder-identity gate prompt was drafted
  2026-09-04. Neither reaches your tree until the ontology class is taken, which you have
  deferred since 2026-08-26 by choice; "absent here" is that deferral, not a defect. The
  sweep printed no `reviewed_commit`, which is the whole failure (J63) — a verdict names
  the tree it read. Second, `[SME-REPORTED]` your `config/source-registry.yaml` row for
  the definition-table export carries the `adapter:` key twice. `[VERIFIED-PRODUCER]` on
  the YAML behavior only — `yaml.safe_load` keeps the LAST duplicate key and says
  nothing, so whichever `adapter:` sits lower in the row is the one every reader sees; the
  producer row has one `adapter: ~`, so this is a company build defect in the per-entry
  merge, same class as the `stack:` finding. Third, `[VERIFIED-PRODUCER]` two UNSIGNED
  producer gate prompts were corrected in place on 2026-09-07 and ride the next roll under
  the gate-prompts entry_rule: dpl-dataset-registry-contract restates its B3 axis (the
  registry `zone` is a multi-valued enum, not a lake-layer triple; `version_id` is opaque;
  audit actors are mixed) as dated amendments plus proposal rows C1-a/b/c and C2-a, shape
  only — the counts that motivated them are your §B profile and stay with you; and
  code-graph-package-layer retires a pointer to the pre-fragment vocabulary path and marks
  its 2026-08-02 header counts as dated. Your own copies of those prompts, if amended
  company-side, merge per-entry as the rule already says. Nothing is asked back.

- **RELAY-35 — A PER-ENTRY MERGE THAT READS THE RANGE DIFF ACCUMULATES EVERY ROW IT EVER
  SKIPPED; A ROLL CLOSED COMPLETE CARRIES ITS DEFERRALS BY PATH; AND T24 IS THE DISPOSITION
  FOR EVERY `drydocs_lineage/**` COLLISION** (new 2026-09-07, mid-apply; nothing here waits
  for the roll). `[COMPANY-CONFIRMED]` — your carve-out I close re-ran the range and found
  that the per-entry pass had merged the RANGE'S DELTAS where the entry_rule says union by id
  against the producer file: a product row and a Q27 `current_for` in
  `config/taxonomy/software-registry.yaml`, and two corpora in `config/doc-source-registry.yaml`,
  all present at `port-base-20260902`, all absent on your tree after that roll closed
  COMPLETE. `[VERIFIED-PRODUCER]` — every one of those rows landed between 2026-08-27 and
  2026-08-31, INSIDE the previous roll's own range, so a delta pass should have seen them
  too; the fix does not depend on which pass skipped them. The rule the manifest already
  states, restated as its failure mode: a per-entry row unions against the file AT THE BASE
  TAG (`git show <base-tag>:<path>`), never against `git diff <prev>..<base> -- <path>` — a
  row added in an earlier range and never merged is in neither tree's diff and stays
  invisible to every later delta pass, forever. Second, `[VERIFIED-PRODUCER]` seven paths
  your carve-out I reverted or found absent — the corpus-status module the API app imports,
  the mapping report function `test_mapping_api.py` needs, four test files your UI-tests
  ledger names, the publishing guard the enforcement matrix lists, and the server-inventory
  sample CSV the fixture interlock reads — are all present at `port-base-20260902`
  (`git ls-tree -r --name-only port-base-20260902 -- <path>`), none touched in
  0902..0905. "Not in this roll" is true and is not a disposition: they are owed by a CLOSED
  roll, and nothing on either side records them as deferred — only the lineage pair has a
  named deferral (T24). So two instruments, together, at every roll close: your
  `git diff --numstat <base> <next> -- <path>` answers "this roll or not" and prints empty
  for a forgotten path exactly as it does for a deferred one; the complement is
  `git ls-tree -r --name-only <base-tag>` minus your tree minus the never-port and
  canonical-company rows, expected EMPTY, and every path that survives is either written
  into the roll's deferral list by name or applied. Third, `[VERIFIED-PRODUCER]` the
  lineage revert re-found T24 (2026-09-01): `drydocs_lineage/writer.py` and
  `drydocs_lineage/extractors/controlm_inventory.py` were ruled deferred behind the
  vocabulary migration,
  and `model.py`'s two gates — the `scheduler_*` ids and the kind constant — are two rolls
  old (2026-08-21 and 2026-08-25) and live in the same deferred file. Carve-out G's note
  that I would close the lineage failures contradicted T24; carve-out I corrected it back.
  T24 is the disposition for every `drydocs_lineage/**` collision until the vocabulary class
  is taken. Fourth, `[VERIFIED-PRODUCER]` the ruff hit your close fixed in
  `scripts/build_schema_matrix.py` is a CONFIGURATION divergence, not a producer defect: the
  producer `pyproject.toml` has ignored RUF002 and RUF003 since 2026-08-12 (ambiguous
  Unicode in prose; the suggested replacements are wrong for it) at the same 0.5.7 pin, and
  the file passes here. Your `pyproject.toml` is per-entry and does not carry that ignore;
  the comment reword is harmless and is not being carried back. Fifth, one attribution for
  your port report, `[VERIFIED-PRODUCER]`: the relationship-vocabulary directory at
  `port-base-20260902` already holds all 17 fragments — the four renames and the two
  additions — and the single file that changed in 0902..0905 is `00-header.yaml`
  (2026-09-04, the header becomes a pointer to the domain registry). Your carve-out D
  handled this roll's share correctly; the rename set is the gate-bound class deferred since
  2026-08-26, one roll older than your carve-out I commit body says. Nothing is asked back.

- **RELAY-36 — TWO CORRECTIONS FOR THE PORT REPORT: THE PRE-START LOAD-MAP ADVICE READ THE
  PRODUCER TREE, AND THE RUFF DIVERGENCE IS A MANIFEST GAP, NOT A MISSED UNION** (new
  2026-09-08, mid-apply; nothing here waits for the roll). First, `[VERIFIED-PRODUCER]` a
  correction to what you were told before carve-out H started: "the renderer has no skip flag,
  so render then check out the two load-map files" and "four tests red by design" were facts
  about the PRODUCER tree — `scripts/render_board.py` calls the load-map renderer here (since
  2026-07-29) and `tests/unit/test_load_map_json.py` has no module skip here. Your copies of
  both are your own evaluated versions (`scripts/**` and `tests/**` evaluate on collision;
  neither file changed in 0902..0905), consistent with your ruling that the load-map surfaces
  are out of scope, so on your tree the render could not write load-map and the two tests skip.
  Your close report has it right; the pre-start advice did not, and it is the J63 failure mode
  the manifest keeps naming — absent-on-your-tree read from present-on-this-one. Second,
  `[COMPANY-CONFIRMED]` the stale `web/src/generated/load-map.json` you found — your own ids,
  weeks behind your registry, its guard skipped — is a real finding with the cause stated
  wrong: the renderer does emit it here, and on your tree the CALL was removed and the GUARD
  skipped together, so nothing sees the file go stale. `[VERIFIED-PRODUCER]` the disposition
  the manifest already gives that directory is regenerate-or-nothing (`web/src/generated/**`,
  derived): a committed copy no renderer stands behind is the exact "reflects someone else's
  sources" failure the row was written for, and the T19 exemption your
  `tests/unit/test_runbook_currency.py` carries says out of scope while the tree says
  present-and-stale. Delete it, or if your console reads it, regenerate it from your own
  sources; either way it is a by-path disposition in your port report, so the next roll can
  tell it from a miss. Third, `[VERIFIED-PRODUCER]` on the RUF003 hit in
  `scripts/build_schema_matrix.py`: RELAY-35's fourth point stands (configuration divergence,
  not carried back), and your "third instance of the delta-vs-union defect" framing is half
  right. `pyproject.toml` IS per-entry, but its entry_rule covers dependencies only ("union of
  dependencies; keep the consumer's version string") and says nothing about `[tool.ruff]` —
  so no union of the ignore list was specified and none was missed; the row is
  under-specified. The intent is already written elsewhere: `.pre-commit-config.yaml` is
  canonical-producer (J62, same hooks at the same standard on both sides) and the ruff pin
  upgrades in lockstep, so the lint STANDARD is meant to be one thing on both sides. The
  producer closes that gap in `PORT-MANIFEST.yaml` at the next roll — the `[tool.ruff]` block
  named producer-canonical inside the per-entry file — and until then the collision you
  predicted is real and is a hand-merge in your favor of the producer block. One more note on
  the close report's measurement, `[VERIFIED-PRODUCER]` from the numbers as reported: "the
  same eight fail both ways" compares a 75-test run with a 135-test run, so it holds over the
  intersection only; your planned full-suite by-test-id pass is the instrument that settles
  it. Nothing is asked back.

- **RELAY-37 — THE GATE-LOG UNION-APPEND HAS NOT LANDED A PRODUCER ENTRY SINCE THE 0825 ROLL:
  TEN ENTRIES ACROSS THREE ROLLS, AND THE GUARD CAN SEE EXACTLY ONE OF THEM** (new 2026-09-08,
  mid-apply; nothing here waits for the roll). `[VERIFIED-PRODUCER]` — your
  `test_gates_json::test_every_log_entry_and_prompt_has_a_row` failure on `idea-series-grammar`
  is the visible corner of a larger gap. The producer `config/gate-log.md` carries eleven
  entries after the 2026-08-25 `CatalogSubLOB` ruling; ten of them are owed by tags you have
  applied or are applying, listed here with the first `port-base-*` tag that carries each:
  `standard-identity-and-carrier` DRAFTED (2026-08-25, 0826); `tech-partner-attach-level`
  DRAFTED (2026-08-26, 0826); the org-acronym `cdo-*` rename record (2026-08-26, 0829); the
  extract-vintage convention record (2026-08-27, 0829); `source-connection-and-run-identity`
  DRAFTED (2026-08-28, 0829); `replica-derivation-edge` DRAFTED (2026-09-01, 0901); the schema
  publish-ceiling re-ask for Teams Edition (2026-09-01, 0902); the PLAN1 record freezing the 27
  letter series (2026-09-02, 0902); `ontology-domain-registry-and-edition-grain` SIGNED OFF
  14/14 (2026-09-02, 0902); `idea-series-grammar` SIGNED OFF 9/9 (2026-09-05, 0905). The
  eleventh, the 2026-09-07 DEFERRED entry for three catalog gates, is after the 0905 tag and is
  not owed. `[SME-REPORTED]` — the tail of your file, as captured, runs from the 2026-08-22
  vendor-docs entries through the CatalogSubLOB ruling and then your own two 2026-08-27
  records, and ends there; none of the ten appears in it, and a file that is chronological to
  that point cannot hold a 2026-08-28-or-later entry anywhere else in order. The check is one
  `grep -n -F` per heading against your file; the two 2026-08-25/26 DRAFTED records are the
  ones that could in principle sit earlier by date, so check those first. Second,
  `[VERIFIED-PRODUCER]` why the guard saw one: `scripts/render_gates.py` gives every prompt a
  row — a `prompt-only` row when no log entry accounts for it — unless the prompt self-declares
  (`^# SIGNED OFF` / `^# DEFERRED`, `_SELF_DECLARED_RE`), and of the ten only
  `config/gate-prompts/idea-series-grammar.yaml` self-declares. So on your tree today four
  drafted gates render as "session not yet run" instead of "recorded", and a signed 14/14 gate
  — the domain-registry ruling behind the allocator refusing letter series, which your copy of
  `.claude/skills/groom-backlog/validate.py` already enforces — renders as never run. The
  entry-count check in the same test compares the render to the same file and cannot see a
  missing entry. Nothing in the tree can; this is the PORT6 completeness class for the
  union-append rows, and the producer will add the by-heading check for them next roll. Third,
  `[VERIFIED-PRODUCER]` the same 0902 range swept the two 2026-08-05 headings in place to
  the `cdo-*` slugs (the org-acronym retirement, 2026-08-26; the old string does not appear
  in publishable files, this one included — the mapping is `internal/cdo-reference/README.md`
  on your side); under union-append a producer-authored entry takes the producer's current
  heading, and the render keys rows on heading text. The repair
  is one commit: for each of the ten headings, in producer order, take the section from
  `git show port-base-20260905:config/gate-log.md` (a section runs from its `## ` heading to
  the next), append it, apply the two heading renames, run `scripts/render_board.py` so
  `web/src/generated/gates.json` refreshes with it, and confirm `tests/unit/test_gates_json.py`
  green. Your own entries stay where they are; the render does not care that the order is by
  side rather than by date. The port report's gate-log line should then say ten appended and
  two headings renamed, not one. Nothing is asked back.

- **RELAY-38 — `render_load_map.main()` IS IN `render_board.py`'S DEFAULT RUN, AND HAS BEEN AT
  EVERY BASE TAG; AND A COMPARISON FIGURE IN A 0905 REPORT SHOULD COME FROM THE 0905 TAG** (new
  2026-09-08, on the in-progress PORT-REPORT at your e7f70e20; two corrections, nothing waits
  for the roll). First, `[VERIFIED-PRODUCER]` — the report's load-map section says
  `render_load_map` is still not wired into `render_board`'s default run, so the drift guard
  and not the session ritual keeps the two load-map surfaces current. On the producer tree
  that has been false since N4 (`0b95a118`, 2026-07-29): `scripts/render_board.py` calls
  `render_load_map.main()` in the default-paths branch, beside `render_gates.main()` and
  `render_enforcement_matrix.main()`, and `git show <tag>:scripts/render_board.py` shows
  the call at every `port-base-*` tag from 0810 through 0905; the file did not move in
  0902..0905. If the sentence is true of YOUR tree, your `scripts/render_board.py` (class
  `evaluate`, `scripts/**`, hand-merge on collision) lost the line in an earlier hand-merge —
  which would also explain how your board renders kept succeeding from 2026-08-20 while
  `render_load_map` could not run, since a wired `render_board.py` dies on
  `CadenceDerivationError` at every render. Either way the consequence is the one you just
  named: the next `render_board.py` run leaves `load-map.json` and `load-map.html` stale
  again. The check is `grep -n "render_load_map.main()" scripts/render_board.py` on your
  side; if it is absent, the producer's file at the base tag is the reference for the
  default-paths block, and the report's sentence should then say the line was missing here
  rather than unwired there. Second, `[VERIFIED-PRODUCER]` — "producer `gates.json` at
  `2e71ede1` reads 114 gates / 21 open-deferred-pending" is right for the commit named,
  and that commit is dated 2026-09-07, 228 commits past `port-base-20260905`; the report's
  J63 block names 0905 as the reviewed base. At `port-base-20260905` the producer
  `gates.json` reads 116 gates / 23 open-deferred-pending (19 open, 3 pending, 1
  deferred). Cite the tag's figure, or say in the sentence why the comparison reaches past
  the base; RELAY-36 was this class in the other direction. The rest of the report checks
  out against the tree — the nine `cadence:` rows at 0901/0902/0905, the three DERIVED steps
  of 21, the guard names and messages, the RUF002/RUF003 reframing, the `replaces` schema
  reading, the `auth.ts` contradiction — and RELAY-37's gate-log append is the sixth
  Outstanding item, not repeated here. Nothing is asked back.

- **RELAY-39 — RELAY-38'S HAND-MERGE HYPOTHESIS IS WITHDRAWN: THE ABSENCE IS YOUR SIGNED
  DEFERRAL; BOTH RELAY-35 CORRECTIONS ACCEPTED; AND `scripts/reconcile_before.py` COLLIDES
  NEXT ROLL** (new 2026-09-08, on the corrected PORT-REPORT at your 5671f745; nothing waits
  for the roll). First, `[COMPANY-CONFIRMED]` — your correction 6 is right and the corrected
  sentence stands as written: the `render_load_map.main()` call is absent on your tree by a
  signed company deferral, recorded on your side five times, not lost in a hand-merge. The
  producer's own machine-local record of your ninth and twenty-first reports already said the
  call "correctly stayed off the chain" under that deferral; RELAY-38 should have read it
  before offering the hypothesis, and the hypothesis is withdrawn. What stands from RELAY-38
  is the half your correction carries as its first paragraph — the producer has called it at
  every base tag since N4 (`0b95a118`) — and a company DEFERRED gate is yours to hold or
  retire; nothing here overrules it. Your correction 11 follows the same ruling: the producer's
  `tests/unit/test_render_determinism.py` lists `render_load_map.py` in both
  `COMMITTED_RENDERERS` and `COMMITTED_SURFACE_WRITERS`, and which of the two your copy keeps
  is the wiring decision's to make. Second, `[VERIFIED-PRODUCER]` — your correction 7's
  producer row matches the tag exactly: `git show port-base-20260905:web/src/generated/gates.json`
  holds 116 gates — 19 open, 3 pending, 1 deferred, 57 recorded, 36 signed-off. The 8-vs-1
  deferred column is the intended divergence, as you say. Third, `[VERIFIED-PRODUCER]` —
  both of correction 12's corrections to RELAY-35 are accepted. The fixture-interlock CSV
  RELAY-35 named is the half you hold (`tests/fixtures/server_inventory/synthetic-server-export.csv`,
  present at the tag on both trees); the half absent on your side is
  `drydocs/data/samples/controlm_hosts__sample.csv`, which sits under the `drydocs/data/**`
  never-port row — a gitignored tree whose fourteen tracked samples are grandfathered, and
  whose absence `tests/unit/test_server_inventory_fixture.py` skips on by design. Not owed,
  and RELAY-35's count is one short of what it said. The classification behind your table
  also reads as the producer manifest reads: `default:` is quoted verbatim; `docs/decisions/**`,
  `docs/reviews/**`, `drydocs-icons/**`, `internal/**`, `scripts/**` and `tests/**` are
  default-resolved rows (clean-add when absent), `docs/design/**` is evaluate, `graph-tests/**`
  and `config/gate-prompts/**` are canonical-company, and every path in the 87 that was
  spot-checked here exists at the tag. The table is the first real-values fixture for the
  producer's completeness instrument (PORT6), which is where "deciding what to APPLY" gets a
  by-path deferral list to refuse COMPLETE against. Fourth, `[VERIFIED-PRODUCER]` — your
  correction 8's `scripts/reconcile_before.py` is your own file, and it collides next roll.
  At `port-base-20260905` the reconcile-port skill set `RECONCILE_BEFORE_DIR` and shipped no
  script for it, which is why you wrote one at `a4603b7e`. The producer closed that gap the
  day the tag was cut, after it: `scripts/reconcile_before.py` landed at `2aa90898`
  (2026-09-05) as a short wrapper over `drydocs/port/reconcile_before.py`, whose write sites
  pin `newline=""` (J49 — your Windows CRLF reasoning is the rule's own), and the skill's
  close step now cites its `--describe <before-dir>` output. `scripts/**` is evaluate, so the
  next roll hand-merges the two; the producer's is the reference for the CLI the skill
  cites, and your `89c54ee6` fix has nothing to carry anywhere. Nothing is asked back.

- **RELAY-40 — THE ROLL-CLOSE COMPLETENESS CHECK EXISTS, THE DEFERRAL LIST IS A FENCED BLOCK
  IN THIS FILE, AND CANONICAL-COMPANY IS A RULING BAND, NOT AN OWED ONE** (new 2026-09-08;
  lands with the next roll, and the recipe in RELAY-35 stays valid until it does).
  `[VERIFIED-PRODUCER]` — `scripts/port_completeness_check.py` is the by-hand recipe from
  RELAY-35 as a script: it lists every path at the base tag that your tree does not hold,
  bucketed by the disposition `PORT-MANIFEST.yaml` resolves for it, in the table shape your
  correction 12 used (disposition | carried | new | total, where carried = already absent at
  the previous tag, a roll that closed COMPLETE), and for the union-append markdown files it
  lists every `## ` heading the tag's copy has and yours lacks — the gate-log shape RELAY-37
  described, at entry grain. It exits 0 only when every survivor is in a `deferred-paths`
  row or is canonical-company. Three things about it worth knowing before you run it. (1)
  ONE classifier. `drydocs/port/dispositions.py` now holds the manifest reading, and both
  `scripts/render_port_dispositions.py` and this check import it, so the two cannot bucket a
  path differently — your sweep and RELAY-35 disagreed about a `drydocs/data/**` sample
  because there were two readings, and now there is one; `tests/unit/test_port_dispositions.py`
  asserts the renderer's name IS the module's function. (2) The deferral list lives in THIS
  file, in a fenced `deferred-paths` block under DEFERRED BY PATH, first row T24, cumulative
  across rolls and retired by date rather than deleted; `docs/port/**` never crosses, so the
  check reads it with `git show <base-tag>:docs/port/port-prompt.md`, which your clone can do
  because you hold the producer tags. A deferral only you have ruled goes in a file of your
  own, same fence, `--deferrals FILE`. (3) Canonical-company paths absent your side are
  LISTED and do not fail — your correction was right that they need a ruling, not a default,
  and the table says "ruling, not owed" on that band so nobody reads it as a gap. What the
  check is NOT: it is PRESENCE only. A path present on both sides with different content —
  the T24 shape, `drydocs_lineage/writer.py` — does not show, and neither does the per-entry
  delta-vs-union defect; those stay with `--numstat` and the J7 reconcile guards. So two
  instruments at every close, and the reconcile-port skill's close step now names both with
  the question each answers: `--numstat` for "this roll or not", the completeness check for
  "ever applied or not". The fixture behind it is your incident at its shape: a path added in
  range 1 and never applied, at range 2's close, where `--numstat` over range 2 prints nothing
  for it and the check names it as carried. Nothing is asked back.

- **RELAY-41 — THE ACCEPTANCE KEYS ON THE FAILING-TEST SET, NOT THE TOTAL (2026-09-08,
  J57):** `[VERIFIED-PRODUCER]` Your eighteenth-postscript method — `--lf` on the branch, the
  main sha in a detached worktree, a set-compare of the two failure lists — is now written
  where the acceptance is asked for, not only where it was praised. The ACCEPTANCE GATE below
  gains a bullet: the sorted `FAILED` node ids from `pytest tests/unit -q -rf`, diffed against
  your last PORT-REPORT's set, with the total kept beside it as the reading. The reconcile-port
  skill's Track-1 acceptance carries the same rule with its one-sentence reason (two sessions
  agreed on a failing total on 2026-08-27 and one failure was new), its report template gains
  a `Failing set` line and a `Clean-claim guard family` line, and a "clean" claim after a
  targeted fix is defined as one that also ran the repo-wide guards the skill names by test
  path — module boundary, render determinism, no-render-parsing, repo-path currency — whose
  failures a targeted run cannot see. The snapshot ritual's green-at-HEAD check was examined
  and left alone: its verdict is CI's conclusion at HEAD's sha, an identity, not a count. No
  test, guard or CI stage changed. Nothing is asked back.

- **RELAY-42 — A CONFIG SURFACE, ITS SURFACES ROW AND THE MATRIX IT FEEDS ARE ONE
  COUPLING (2026-09-08, J75):** `[VERIFIED-PRODUCER]` Your D-slice apply of
  port-base-20260826..20260901 found it: `config/source-bindings.yaml` had arrived in an
  earlier slice without its row in `scripts/render_enforcement_matrix.py` SURFACES, so
  "regenerate, never carry" made `web/src/generated/enforcement-matrix.json` UNPRODUCIBLE
  rather than stale (the renderer refuses the unlisted entry; render_board.py exits 1), and
  the J55 acronym guard then failed on the stale carried copies. `PORT-MANIFEST.yaml` now
  names the triple the way J68 names declaration/guard pairs: a new per-entry row for
  `scripts/render_enforcement_matrix.py` (SURFACES union by id, your company-only rows
  kept, producer rows cross with their config surface) carries the enumeration of every
  triple that exists today — 26 SURFACES rows, read from the constant by import, not from
  a render — and the reason the tree guard `tests/unit/test_enforcement_matrix.py` cannot
  cover it: a guard fires after the take, and a slice is not a tree. The
  `web/src/generated/**` derived row and the `config/source-bindings.yaml` row each name
  their other two members. The APPLY BY DISPOSITION section gains the one-sentence reading
  rule: a slice touching a `config/` path is read with its SURFACES row and the matrix in
  the same breath. No test, guard or CI stage changed. Nothing is asked back.

- **RELAY-43 — THE GATE-LOG GUARD NOW READS LINES, NOT BYTES; A LOADER SQL FILE GETS ITS
  OWN ROW; A CURRENCY MESSAGE NAMES WHAT MOVED (2026-09-08, port-base-20260905 apply):**
  `[VERIFIED-PRODUCER]` Three producer-owed fixes from your twenty-fifth report, each a
  commit past `port-base-20260905` that lands with the next roll by its manifest row.
  **One — the ruling you asked for.** `test_reconcile_gate_log_append_only_live` was
  stricter than the rule it enforces: the manifest row for `config/gate-log.md` says
  chronological union, dropping either side's entries is the violation; the guard demanded
  the pre-merge text be a byte PREFIX of the merged text, which forbids a dated postscript
  under any record that is not the last one and forbids interleaving the other side's
  records by date. Your T19 postscript was the first shape; the producer's own log already
  carried one (2026-09-07, under the ADR 0007 record) that no run had ever seen, because the
  `_live` guards skip producer-side. `append_only_violation` in
  `tests/unit/test_port_reconcile_guards.py` is now an ordered LINE SUBSEQUENCE: every
  pre-merge line must survive, in order; insertions anywhere pass; the byte-prefix case is
  the fast path; and a failure names the first pre-merge line, by number and text, that is
  missing or altered, instead of a character offset. The mechanics test pins the three
  permitted shapes (postscript under a non-last record, a record interleaved by date,
  pure append) and the two still forbidden (a line dropped from the middle, records
  reordered). Your T19 postscript passes under it. One thing the new reading will surface
  that the old one hid behind the postscript: the producer commit `55c2a204` redacted a
  company product name IN PLACE in one signed line under the ADR 0007 record (its postscript
  says so). If your pre-merge copy carried the pre-redaction spelling, the guard will name
  that line. That is a true in-place edit of a signed line, the guard reading correctly; on
  your side the original spelling is not a publish-boundary matter, so keeping either
  spelling is your call, and re-taking the snapshot after you decide is the mechanism, not
  a workaround. **Two — the manifest gap.** `drydocs/loaders/sql/controlm_jobs.sql` sat
  under the wholesale `drydocs/loaders/**` canonical-producer row while your own signed gate
  had added a derived column to it, so the take dropped the column and your guard caught it
  (correction 14, item 1). It now has its own `per-entry` row ABOVE the wildcard (the
  manifest is first-match-wins; `test_port_manifest.py` guards the shadow): an entry is one
  SELECT-list column keyed by alias, producer columns cross whole, a column your gate ruled
  survives the take. Same family as the MODULE_MAP.md / test_module_boundary.py pair (J68).
  **Three — the instrument.** `test_documentation_currency_drift_is_visible_not_hidden`
  failed with a message that printed the drift line that WAS present, pointing away from the
  missing one (correction 14, item 3; J76). It now reports `missing:` and `unexpected:`
  separately. A guard changed this time — the append-only guard is looser in exactly the
  two shapes the manifest rule permits and no looser anywhere else; no CI stage changed.
  Nothing is asked back.

- **RELAY-44 — THE DPL DATASET GATE'S B3 WAS RESTATED ON THE REGISTRY'S REAL ZONE AXIS
  AFTER YOUR BASE WAS CUT; THE G64 PAGE GREW FOUR CLAUSES; AND ONE COMMIT TO CHECK ON YOUR
  SIDE (2026-09-08, post port-base-20260905):** `[VERIFIED-PRODUCER]` Three things, each
  a commit past `port-base-20260905` that the next roll carries by its manifest row.
  **One.** `config/gate-prompts/dpl-dataset-registry-contract.yaml` at `ecc1622c`
  (2026-09-07): B3 no longer asks for a RAW/TRUSTED/REFINED reading of the registry's
  `zone` - the page now treats it as a multi-valued enum, lake layer for object-store rows
  and database technology otherwise - and proposal rows C1-a, C1-b, C1-c and C2-a carry the
  rulings that follow from that (zone axis, opaque version string, unregistered and
  registered-but-empty keys, two audit actor classes). Your copy of the page at the base
  still carries the old B3, so a G65 session convened from the base would ask for an axis
  the data does not have; the page you want is the one that lands with the roll. **Two.**
  `config/gate-prompts/dpl-pipeline-registry-contract.yaml` (2026-09-08): four clauses
  added so the page can hold what a section-B run produces - A3 admits a fleet-grain
  corroborating surface beside the A1 export; C5 rules non-GUID registry ids (the extractor
  admits any non-empty id, the launcher join requires an anchored GUID, so today such an id
  silently never matches); C6 rules the OQ-8 intake-naming question the extractor docstring
  has promised to this gate since G25; C3-a rules a fourth candidate usage signal beside
  active. The composite-key `(guid, connectorName)` question is deliberately NOT on this
  page - `config/gate-prompts/dpl-dataset-identity-zone.yaml` owns it, and a G64 table
  that signs it would rule identity inside a contract gate. **Three - SME review status
  on the recording half of G121.** The whole of G121's recording half is ONE producer
  commit, `3f5b5769` (2026-08-27), inside every base from `port-base-20260829` on: it adds
  the `run_meta` parameter to `BaseLoader.__init__` in `drydocs/loaders/base.py`, the
  `_csv_acquisition_meta` helper in `drydocs/cli_ingest.py`, and
  `tests/unit/test_load_csv_acquisition.py`. Producer-side all 22 registered loaders
  accept `run_meta` and the test file is present. A tree that carries the helper in
  `cli_ingest.py` but a `BaseLoader.__init__` without the parameter, and no test file, is
  the shape of a `base.py` cherry-pick conflict resolved to the receiving hunk - the
  `_acquisition_mode` helper that lives in that region on your side does not exist here,
  so the two hunks collide exactly there. Whether your post-apply `base.py` carries the
  parameter is one import and one attribute check, and if it does not, the manifest row
  for `drydocs/loaders/**` is doing what it says and the resolution is the place to look.
  Nothing is asked back.

- **RELAY-45 — YOUR PORT-REPORT FOR port-base-20260905 READ AGAINST PRODUCER `main`: ONE
  ITEM IS TREE-LAG, TWO PRODUCER DEFECTS IT NAMED ARE FIXED, AND THE ACCEPTANCE GATE BELOW
  IS RESTATED TO SAY WHAT YOUR BY-TEST-ID INSTRUMENT ALREADY MEASURES (2026-09-08, post
  port-base-20260905):** `[VERIFIED-PRODUCER]` Read at producer `d274e5ee`, against your
  report at its correction-16 state and the session that merged `port/20260905` and the ruff
  sweep into your `main` (`25bace48`, `b485ab72`, `d1451fe5`). **One - tree-lag, not a gap.**
  The line-based reading of the gate-log append-only guard your report asks for exists:
  `aef8dfcb` (RELAY-43), which is NOT in `port-base-20260905` and lands with the next roll.
  Same commit carries the `controlm_jobs.sql` per-entry row (your correction 14, item 1) and
  the currency message that names what moved. Nothing to do on your side until the roll. **Two
  - a producer defect your close-out found, fixed at `1a5d30b0`.** `depgraph.capability_assert`
  was read by `tests/unit/test_probe_instrument.py` and never by
  `knowledge/depgraph-snapshots/snapshot.ps1`, so the guard said recorded divergence and the
  ritual said defect about the same checkout. The script now reads the flag: `false` warns,
  writes a degraded snapshot, and the meta header carries `capability_assert` and
  `capability_gap` so the artifact describes its own degradation. Two of its messages guessed
  a cause and both guessed wrong on your tree - the refusal's "a checkout stranded on an older
  revision is the likely cause" fired on a checkout that matched its pin, and the CI check's
  "gh not authenticated?" fired on a remote whose workflow has never run. Both now report the
  measurement (checkout-vs-pin; gh-failed vs zero-runs, the latter printed as UNVERIFIED) and
  list the causes without picking one (J76). **Three - the ruff block, fixed at `3d1278aa`.**
  `PORT-MANIFEST.yaml`'s `pyproject.toml` row now says what RELAY-36 promised and your
  correction 4 asked for: the `[tool.ruff]`, `[tool.ruff.lint]`,
  `[tool.ruff.lint.per-file-ignores]` and `[tool.ruff.format]` tables cross WHOLE, producer
  text verbatim, and an exception one side needs is asked for as a ported change to that block,
  never made as a local edit. `[SME-REPORTED]` Your sweep left `ruff check` red by decision
  on fifteen RUF002/RUF003 findings pending exactly this row - under it, the producer's
  ignore list crosses whole at the next roll and those fifteen clear without a local edit. The
  ten other findings your table lists (B007, N999, RUF013, N812, E722) are per-site judgment
  calls on your own files and are not this row's business. The row also now names the `ruff`
  DEV DEPENDENCY PIN as crossing whole (PORT7, `5637d694`): it is the one dependency entry
  that does not union, because J10 stage 0 holds only at one exact version and
  `.pre-commit-config.yaml`'s rev is that pin. That was assumed on both sides and enforced by
  nothing across the two repos - if your pin has drifted from `0.5.7`, the next roll is where
  it converges, and until it does a green `ruff format --check` on one side says nothing about
  the other. **Four - the load-map absence.**
  Your report's "stale-by-blocked-renderer" reading matches RELAY-39: the missing
  `render_load_map` call is your signed T19 deferral, and no producer hypothesis about it
  stands. **Five - SME review status on the one number the report does not itemize.** At
  `f8c2233c` the buckets reconcile to the total (2 regressions + 20 pre-existing + 38 new
  tests + 1 unskipped = 61), and the
  regression bucket is itemized by test id with a ruling beside each of the two that remain.
  The 38 "new tests failing" bucket is the only one that is a count and not a list: tests that
  DID cross in this range and DO fail on your tree, un-named. Under the ACCEPTANCE GATE as now
  restated (Six), that bucket is where COMPLETE turns - a count is not a bucket, a list of ids
  is. **Six - the ACCEPTANCE GATE sentence is restated below**, from "ZERO failures is the
  contract" to zero regressions BY TEST ID against your own prior PORT-REPORT, with every other
  failing id bucketed by name. Your correction 14 built exactly that instrument and applied it
  correctly; the producer sentence lagged it. What this does NOT change: the reference figures
  stay producer figures, never your acceptance number, and a failure that is not bucketed is
  still a failure. **Seven - every `PORT-MANIFEST.yaml` entry_rule was swept for the shape your
  carve-out 8 apply reported, and a guard now holds the line (PORT5, `58a76d3f`).** The rule
  that cost you three guards said what YOUR tree contained; the sweep found five more rules
  doing a milder version of the same thing - a count of your rows, a named set of your
  company-only groups, a claim that one of your exemption tables was empty - and rewrote each
  as what the UNION contains, with any reading of your tree marked as a dated observation of
  one report on one day. Nothing about the take changes: the same rows cross, the same rows
  stay. What changes is that a rule no longer goes stale when you move, and
  `test_no_entry_rule_asserts_the_consumers_tree` fails the next author who writes one that
  would. If a rule still describes your tree wrongly, it is a producer defect and the roll is
  where it is fixed. Nothing is asked back.

  **POSTSCRIPT TO RELAY-45 - YOUR CLOSE-OUT FOR THE SIXTH ROLL, TRANSCRIBED (2026-09-08;
  your `PORT-REPORT-port-base-20260905.md` close-out at company `main` `d527afce`):**
  `[SME-REPORTED]` Read producer-side at `65b9037f` on `main`, port base
  `port-base-20260905`; venue NewThinkpad. RELAY-45 was written against the report at its
  correction-16 state and the three merge commits; this is the FOURTH commit and the four
  measurements RELAY-45 did not have. Recorded as YOUR words, verified against nothing on
  this side - company commits cannot be read from here, so every sha and count below is
  reported, not confirmed.

  **The roll is closed company-side.** `main` = `d527afce`, pushed, working tree clean.
  Four commits: `25bace48` the `--no-ff` merge of `port/20260905`, 22 commits; `b485ab72`
  the `--no-ff` merge of `chore/ruff-sweep-20260908`; `d1451fe5` the gate-prompt scalar
  fold, verified content-neutral; `d527afce` the report close-out, **Status: COMPLETE**.

  **What the session produced beyond applying the four relays**, in your close-out's own
  terms: (1) **9 missing `cadence: rows`** - a committed render had sat 20 sources stale
  for three weeks while the record called it "deferred"; the fourth instance of the
  per-entry delta-vs-union defect, and the first with a functional consequence. (2) **87
  owed paths, 82 of them from a roll that closed COMPLETE** - RELAY-35 named seven, the
  instrument found eighty-two. (3) **5 regressions; "zero regressions" was never true** -
  three fixed, including a gate-bound column a wholesale take silently dropped. (4) **CI
  has never run on this remote** - `state: active`, `total_count: 0`.

  **Four corrections you made against your own claims:** the ledger miscount, the
  "pre-existing" mislabel, the overstated ruff count, and the CI framing. Each recorded
  rather than quietly patched, on the stated reason that the report criticizes unmeasured
  counts and carrying one silently would have cost more than the fix. **The lesson you
  name, repeated three times: check the instrument before the subject** (J76 producer-side,
  same finding independently) - `git diff --quiet` cannot answer a determinism question
  about an intentionally-modified file; hashing `load-map.json` across two board renders
  proves nothing when the board render never touches it; buckets that do not sum to their
  own total are not measuring what they claim.

  **Two things you left open, both yours to decide, neither resolved here.** (1) **The
  gate-log guard conflict - the roll's main owed decision.** The guard names its violation
  as "dropping or editing" an audit entry but implements a file-level prefix check, so it
  trips on a postscript that does neither; the convention requires postscripts under the
  signed record and the guard forbids them anywhere but the end. **Merged red on purpose.**
  Adjacent but NOT the same defect as RELAY-43's bytes-vs-lines fix (`aef8dfcb`, not in
  this range) - do not assume that fix clears this; the two are recorded separately until
  one of us reads them against each other. (2) **Branch cleanup** - `port/20260905` and
  `chore/ruff-sweep-20260908` are both merged and pushed, convention says delete after
  `--no-ff`, and you have not touched them.

  **THREE THINGS THIS POSTSCRIPT DOES NOT DO, said so nobody reads the transcription as a
  ruling.** (a) The COMPLETE above is your verdict, and RELAY-45 §Five's condition on it is
  still open: the 38 "new tests failing" bucket is a count, and under the restated
  ACCEPTANCE GATE that bucket is where COMPLETE turns - a count is not a bucket, a list of
  ids is. The close-out does not itemize it. (b) The 82 owed paths get NO row in the
  `deferred-paths` block. A row is a path or a glob and a producer ruling; a count is
  neither, and 82 unnamed paths cannot be written as a pattern. Ask for the list and the
  rows follow - that is exactly the record RELAY-35 asked for and PORT6 built the block to
  hold. (c) Nothing in the "Last completed port" tracker is promoted from reported to
  verified; the pointer for this base now carries the close-out and its sha, and nothing
  more.

  **SECOND POSTSCRIPT TO RELAY-45 - THE GATE-LOG CONFLICT IS RESOLVED, AND MY OWN CAUTION
  AT (1) ABOVE WAS WRONG: IT IS THE SAME GUARD, ALREADY FIXED ON THIS SIDE, AND YOU ARE
  READING THE SUPERSEDED COPY (2026-09-08; your gate-log walk-through, same session as the
  close-out):** Read producer-side at `df006a05` on `main`, venue NewThinkpad. The first
  postscript said the conflict was "adjacent but NOT the same defect as RELAY-43's
  bytes-vs-lines fix - do not assume that fix clears this." **That is withdrawn.** It is
  the same guard and that fix does clear it. The function your walk-through quotes -
  `"""None if before_text is a byte prefix of after_text; else a message."""` - is
  `aef8dfcb^` verbatim, the version RELAY-43 replaced at 11:01 on 2026-09-08, and
  `aef8dfcb` is NOT in `port-base-20260905`. RELAY-45 point one already told you the
  line-based reading lands with the next roll; the first postscript then fenced the two
  apart on a guess rather than reading the parent commit, which is the J76 failure your own
  close-out names three times, committed here on the fourth. Corrected by rider, not by
  editing the paragraph above.

  **ONE - YOUR RETRACTION IS RIGHT ABOUT THE TREE YOU HOLD, AND THE RENDERING DEFECT IS
  REAL ON EVERY TREE.** `[SME-REPORTED]` On your copy the check IS a strict byte prefix, a
  `### POSTSCRIPT` subsection inserted mid-file at your line 3454 DOES break it, and the
  guard was reporting a real placement defect. Two things stand independently of any guard:
  a `###` renders as part of the 2026-08-20 entry rather than as its own dated record, and
  your relocation test (`before is prefix of MOVED-to-EOF: True`, signed text
  byte-identical) proves the move is content-neutral.

  **TWO - KEEP THE FIX, CHANGE ITS REASON, AND SOFTEN CORRECTION 18.** `[VERIFIED-PRODUCER]`
  Promote the block to a top-level `##` dated entry at EOF - but for the RENDERING reason,
  not the guard reason. Under `aef8dfcb` a mid-file postscript PASSES:
  `append_only_violation` now reads "every line of `before_text` survives in `after_text`,
  in order. Insertions anywhere are allowed - a dated postscript under any signed record,
  the other side's entries interleaved chronologically," with the byte-prefix case kept as
  the fast path, and `test_gate_log_append_only_mechanics` names exactly your shape ("a
  postscript under a record that is not the last one") as permitted. So correction 18
  should NOT read as a clean self-retraction: your original claim - the guard is stricter
  than the rule it names - was ACCEPTED on this side and fixed seven hours before you wrote
  the retraction, on a commit your tree does not hold. What was wrong was the placement, on
  your tree, under the guard you have. The rule-versus-implementation gap you named was
  real.

  **THREE - THE CONVENTION CLAIM IS WRONG ON THIS TREE, AND THE STRUCTURE IS NOT ONLY
  YOURS.** `[VERIFIED-PRODUCER]` `config/gate-log.md:803` carries
  `- **POSTSCRIPT 2026-09-07 (desktop):**` INSIDE the signed 2026-07-23 ADR 0007 entry that
  opens at line 779 - bullet-level, mid-file, under a signed record. The guard's own test
  blesses the shape. Your reading of `03-hitl-sme-flow.md` is otherwise sound and the rule
  is L25 producer-side: a correction is a dated rider appended BESIDE the signed entry,
  never an edit of the signed text. "Beside" has been satisfied both ways here.

  **FOUR - THE ONE THAT NEEDS A RULING, AND IT IS COMING AT YOU NEXT ROLL.**
  `[VERIFIED-PRODUCER]` The same commit that added that postscript, `55c2a204` (after
  `port-base-20260905`), also ALTERED SIGNED TEXT IN PLACE inside that entry: a
  company-internal product name, redacted per CLAUDE.md §3, in clause C of a gate signed
  2026-07-23. Not named here, and it is not to be reconstructed - the whole point of the
  commit was to remove it from tracked prose. **A changed line is what the line-based guard
  still fails**, by design, and it CANNOT be fixed the way your postscript can: a
  publish-boundary redaction has nowhere to relocate to. So at the next roll your
  `append_only_violation` will fail on producer text, correctly, and neither side has a
  ruling for it. **The open question, stated and not answered here:** how does a
  union-append append-only guard survive a MANDATORY redaction of already-ported signed
  text - accepted-drop seam (PORT4), an exemption keyed to a publish-boundary commit, or a
  rule that §3 redactions are ported as riders that supersede rather than as in-place
  edits? Producer-side question, producer-side answer owed, and it is owed before the roll
  rather than at it.

  **FIVE - THE COUNT.** Your 144 → 145 is yours and stands. Note only that the producer
  postscript at 803 adds NO `##` entry, so nothing in the next roll moves that count for
  it; `config/gate-log.md` has 98 top-level entries producer-side.

- **RELAY-46 — THE SEVENTH ROLL, `port-base-20260905..port-base-20260908`: WHAT IT CARRIES
  FOR YOU, WHERE THE NINETEEN MID-APPLY RELAYS LAND, AND THE ONE RULING STILL OWED FROM
  THIS SIDE** (new 2026-09-08, at the roll). `[VERIFIED-PRODUCER]` throughout except the
  two company figures marked `[SME-REPORTED]` — every producer sha here is on `main` under
  the new tag, and nothing here restates a ruling that is yours.
  **THE RANGE:** 407 commits at the tag, 303 of them in ledger steps 334–353 (the rest are
  the ritual patterns `drydocs/port/port_preflight.py` already recognizes); **493 changed
  paths across 8 classes**, the table is in the disposition section above. Your
  `port-base-20260905` apply is reported COMPLETE at your `d527afce` (`[SME-REPORTED]`, the
  POSTSCRIPT and SECOND POSTSCRIPT to RELAY-45), so this is one range, tag..tag, with no
  parked apply behind it. Nothing is hand-carried except what already is: the close-out
  hand prompt (step 353) is in your hands and cites no producer path.
  **THE PROMISED FIXES ARE IN IT (step 338).** Relays 27–45 were written while your 0905
  apply ran and each said "acts at the next roll"; this is that roll, and here is where
  each lands. RELAY-27 and RELAY-39: `scripts/reconcile_before.py` collides, two shapes,
  under `scripts/**` default_ok — hand-merge it; the producer's shape is the one stamped
  call with `drydocs/port/reconcile_before.py` behind it (`2aa90898`) and the guards that
  check the instrument come with it. RELAY-28/29: `scripts/render_port_dispositions.py` refuses an unresolvable ref
  (`eee64ce3`, `df7a57c3`), and `classification:` on a per-entry row is yours. RELAY-30/31:
  the gate-prompts `entry_rule` and the two `test_backlog.py` tests. RELAY-35 and RELAY-40:
  `scripts/port_completeness_check.py <base> --prev <prev>` (`6f8c7825`, PORT6) — run it at
  the END of this apply with `port-base-20260908 --prev port-base-20260905`; it is the
  instrument your by-hand sweep of 87 owed paths stood in for, and this roll is the first
  it can close. RELAY-36 + `3d1278aa` + PORT7 (`5637d694`): the ruff tables AND the pin
  cross whole inside the `pyproject.toml` per-entry row — take the block, keep your version
  string. RELAY-37: gate-log union-append, and RELAY-43 (`aef8dfcb`): the append-only guard
  reads LINES, which is the guard your walk-through quoted one commit behind (SECOND
  POSTSCRIPT) — under it your promote-to-EOF postscript passes. RELAY-41: acceptance by
  test id (J57, `6f0a8662`). RELAY-42: J75. RELAY-45: PORT5 (`58a76d3f`, `5656439a`) — five
  manifest rules no longer describe your tree, they describe the union and date their
  observations of yours; PORT2 (`e8600cd6`) — two revisions of one document are never a
  rename candidate, so your chunk-1 1.00 pair scores as what it is.
  **THE WEB STACK IS THE BULK OF THE RANGE.** 151 of the 184 canonical-producer paths are
  `web/**` — nineteen WEB items plus O43/O50/O51/O63/O68/O89/Z6/R12 from Lane B's six
  queues (steps 334–336, 343–345). Take `web/**` whole, regenerate `web/src/generated/**`
  (derived — `scripts/dump_openapi.py` renders before opening and a failed dump leaves
  `web/src/generated/openapi.json` byte-identical, API3), take the `js-cookie` override
  (`6be9be06`) and let your lockfile resolve it, and take the coverage-report ignore rule
  (`aa7e5836`) — 184 generated files rode in under WEB13 before it existed. TypeScript
  strict is ON with a guard (WEB4); a local `any` you carry will fail the build, and the
  build is the contract.
  **THE STACK SHAPE.** ADR 0019 (credentials to the agent tier, option C) and ADR 0020
  (the console's delivery shape, one path-routed reverse proxy, same-origin) both land
  ACCEPTED (step 340) — records, default class, the producer's rulings on the producer's
  stack. `compose.yaml` is canonical-company: take the SHAPE by hand (O72's five services,
  `deploy/render_proxy_config.mjs` under `deploy/**` canonical-producer), the values are
  yours. Your own console shape is your own ruling; nothing here changes it.
  **TWO THINGS YOUR OWN RECORD STILL LACKS**, for your own report and no one else's: the 38
  "new tests failing" bucket as a list of test ids (RELAY-45 §Five's condition on your
  COMPLETE, still open in the close-out), and the 82 owed paths AS A LIST — a
  deferred-paths row is a path or a glob, and a count cannot be written as a pattern, so
  no row exists for them on this side until they are names. Both are in the hand prompt's
  section 5; both are yours to record where you record things.
  **THE ONE RULING OWED FROM THIS SIDE, STATED AND NOT YET ANSWERED.** `55c2a204` (step
  352) redacted a company-internal product name IN PLACE inside a signed `config/gate-log.md`
  entry, per CLAUDE.md §3. A changed line is what the line-based append-only guard fails, by
  design, and a publish-boundary redaction has nowhere to relocate to — so at this roll your
  `append_only_violation` will fail on that one producer line, correctly, and neither side
  yet has a rule for it. The question is producer-side and the answer is owed producer-side;
  it was raised before this roll (SECOND POSTSCRIPT, §Four) and the roll was cut with it
  open, deliberately, so that the base does not wait on a ruling and the ruling does not
  get made by a roll. It lands as a dated rider to this relay or as RELAY-47. Until it does:
  when the guard fails on that line, stop, name it in your report, invent no local
  exemption, and do NOT reconstruct the redacted name — removing it from tracked prose was
  the point of the commit. The hand prompt's section 4 says the same in your own terms.
  **NEVER-PORT THIS ROLL, so you do not go looking:** the lane handoff file under `docs/`
  and the `lane-handoff` skill with its test `tests/unit/test_lane_handoff.py` (producer
  two-machine coordination, step 337), `docs/company-prompts/**` (hand-carried by
  definition), `docs/port/port-prompt.md` (this file), and the depgraph snapshot JSON.
  Seven paths; the table names them.
  Nothing is asked back.

  **POSTSCRIPT TO RELAY-46 - THREE OF ITS FIGURES ARE SUPERSEDED, AND THE OWED PATHS ARE
  ALREADY A LIST (2026-09-08, after the roll; your hand-carried carve-out review and your
  landing report, plus the producer's review of the first):** Read producer-side at
  `05e365dd` on `main`, port base `port-base-20260908`; venue desktop. The relay above was
  written at the roll and stands as written (L25: a rider, never an edit); this postscript
  says what moved after it. **One - your `main` is `b73fd9d1`, not `d527afce`**
  `[SME-REPORTED]`: all five of the hand-carried fixes landed, both working branches are
  deleted local and remote, and the "2 deliberate regressions" in RELAY-46 and in the sixth
  base's bullet under `## Last completed port` are now ONE.
  `test_reconcile_gate_log_append_only_live` went green with the signed 2026-08-20 text
  byte-identical - so it was never a regression of the record, only of the guard's copy
  (SECOND POSTSCRIPT TO RELAY-45, its opening paragraph).
  `test_reconcile_runbook_exemptions_no_drop_live` remains, and remains correctly: it
  reports the two `HISTORICAL_PATHS` rows the T19 ruling
  dropped, which is the guard doing its job on a ruled drop, not a defect. Of the 38 "new
  tests failing", 30 sit in T24 and the vocabulary rename `[SME-REPORTED]`, unchecked from
  here. **Two - RELAY-46 said the 82 owed paths were owed AS A LIST. They already are one.**
  Your `sme-path-carveout-review.md` and its `.csv` twin, produced against section 5 of
  `docs/company-prompts/port-base-20260905-closeout-company-prompt.md`, name 87 paths; the
  relay was written before that document was carried over, and its "a count cannot be
  written as a pattern" stands only as history. `[VERIFIED-PRODUCER]` The producer read that
  list with its own classifier - `drydocs.port.dispositions.classify` against
  `PORT-MANIFEST.yaml`, the importable object (J37), never a render - and the result is
  `docs/reviews/company-owed-path-review-2026-09-08.md` (`775248a7`, amended `fcf3c00b`):
  **the manifest already rules 73 of the 87.** Five are canonical-producer, seven are
  per-entry (blocked on T24, not on a ruling), three are derived (regenerate, never carry),
  and 51 are `default_ok` - every one of them matched an explicit J16 row with a `reason:`,
  none fell through to the bare default, so the decision for those 51 IS recorded and the
  review's §3 says where. **Fourteen need the SME**: the 13 `docs/design/**` rows the
  manifest classes `evaluate`, and `graph-tests/tom-required-contacts.yaml`, whose
  canonical-company row carries a note and no rule. **The one item with a clock is not among
  the fourteen:** seven of the eight canonical-company rows are `config/gate-prompts/**`
  specs, and that row's entry_rule already rules them - a producer spec whose slug the
  consumer does not hold is a CLEAN-ADD, taken whole. They wait on nobody, and a missing
  prompt is a gate page that cannot render (review §2). One reading correction to your own
  document, for your own record: the summary table's canonical-company cells are transposed
  (the `1 | 7` cells should read `7 | 1`; review §4). No `deferred-paths` row is written on this
  side for any of the 87: a row is a producer ruling, only 14 are needed, and the 14 are the
  SME's to make. **Three - the pointer, which is what this postscript is for.** Your fetch
  of the producer works now (guardrail 1: read at producer HEAD, not at the ref you last
  fetched), so this relay is a pointer and not a payload: **read producer `main` at
  `05e365dd`** - `git show 05e365dd:<path>` from the fetched ref reads a file without
  applying it, and `docs/port/**` stays never-port whether or not you read it. Three files
  are worth naming. The review above. The hand prompt named above, whose section 4 is the
  standing instruction for the §3-redaction line until the ruling lands. And
  `docs/style/review-provenance.md`, which since `fcf3c00b` and `05e365dd` carries J76's
  fourth failure mode - the instrument is correct and read correctly and is STALE, a
  superseded function under the same name, signature and docstring; the check is
  `git log -1 -- <file>` against your base, and the 2026-08-06 FETCH RESOLVED note (a failed
  producer fetch degrading silently to a cached `5f79d145`) was its single-case form. That
  is the shape the SECOND POSTSCRIPT TO RELAY-45 found on this side by hand. **RELAY-47 stays
  reserved for the §3-redaction ruling**; nothing in this postscript is that ruling.
  Nothing is asked back.

  **SECOND POSTSCRIPT TO RELAY-46 - THREE CORRECTIONS TO YOUR 0908 APPLY, READ AT ITS PHASE 3
  (2026-09-08, producer main `d1016072`, base `port-base-20260908`, venue desktop; your report of
  the apply is `[SME-REPORTED]`, each correction is checked at the tag):** Your Phase 0, Phase 1
  and the stale-step correction (`PRODUCER_BASELINE` gone, `edition:` deliberately unset until your
  own mint) read correctly from here, and your correction-21 handling of `55c2a084` - stop, name
  it, take producer text, reconstruct nothing, no local exemption - is the right handling; that
  ruling is producer-owned and RELAY-47 stays reserved for it. Three things in your Phase 3 do not
  survive a read of the producer tag. **One - the writer did not drop `--repo`.**
  `[VERIFIED-PRODUCER]` `scripts/reconcile_before.py` at `port-base-20260908` declares it
  (`--repo`, default the checkout containing the cwd, help text "the consumer checkout to
  snapshot"), beside the positional before-dir and `--describe`; it arrived in producer `2aa90898`
  on 2026-09-05 and the file is byte-identical between the tag and producer `main`. Your Phase 1
  invocation - a detached worktree at the tag, then the writer with `--repo <worktree>` - is the
  producer CLI's own documented shape. The "hand-merge in the diverged class" is a diff against
  your 0905-era local copy reading the library-plus-CLI refactor as a drop (J76's fourth failure
  mode, from the first postscript: `git log -1 -- <file>` against the tag before comparing text).
  Take the fast-forward. **Two - there is no bootstrapping problem, so the stamp guard clears
  today.** `[VERIFIED-PRODUCER]` The stamp your `BASE_SHA` names is `BASE.sha` - one line, the
  40-hex sha, `drydocs/port/reconcile_before.py` - and the guard is
  `test_reconcile_before_dir_stamp_describes_this_tree_live` in
  `tests/unit/test_port_reconcile_guards.py`. The writer's refusal is narrower than "a dirty
  tree": it is `git status --porcelain` over the snapshot's SOURCE files only, run in the `--repo`
  checkout. Point it at a worktree detached at `pre-cewilson-port-20260908` and the sources are
  clean by construction; the stamp it writes is `b73fd9d1`, which is an ancestor of
  `port/20260908` and is where that branch left `main`, so every check the guard makes passes -
  missing, unresolvable, not-an-ancestor, gate-log byte mismatch, not-the-fork-point. Nothing has
  to land first; the library is already on your branch as a clean-add and the CLI is a
  fast-forward. **Three - PORT6 is closed, and was never a home for owed-path rows.**
  `[VERIFIED-PRODUCER]` PORT5, PORT6 and PORT7 are `done` on the producer; PORT6 was the clean-add
  completeness check. The 87 owed paths already have a producer reading in
  `docs/reviews/company-owed-path-review-2026-09-08.md` (first postscript: 73 ruled by the
  manifest, 14 need the SME), and any new row for them is PORT4's accepted-drop seam or a fresh
  mint - keeping the 87 out of this roll is the right scope call either way. **Two notes, not
  corrections.** Your 2-of-3 interlock caution is the manifest's own rule: `MODULE_MAP.md`,
  `drydocs_core/component_map.py` and `tests/unit/test_module_boundary.py` are one `per-entry`
  classification in `PORT-MANIFEST.yaml` ("three files, one classification"), so a wholesale take
  of any of the three is the defect the row exists to stop. And your closing lesson - the unit of
  application is the dependency closure, not the disposition class - is now producer inbox
  Idea-307, mechanism only: the classifier answers per path, the `pairs_with` column records the
  closure by hand and nothing reads it, and the depgraph snapshot already holds the import edges
  to derive it. Nothing is asked back.

  **THIRD POSTSCRIPT TO RELAY-46 - THE SEVENTH ROLL RE-CERTIFIED ON THE FIXED INSTRUMENT
  (2026-09-09, producer PORT8, venue desktop) [VERIFIED-PRODUCER]:** the module sweep's slot 7
  found that the preflight's git helper discarded the exit code, so a base git could not
  resolve yielded an EMPTY commit range and both range-derived checks (ledger coverage, cited
  paths resolve) passed on emptiness - the worse the base, the greener the certification.
  PORT8 makes the preflight fail closed: a base-resolves check runs first, a git failure is
  loud, and a check that could not run reports NOT CHECKED, which blocks the tag as a failure
  does. Re-run over `port-base-20260905..port-base-20260908` with the fixed instrument: the
  base resolves; 407 commits, 0 uncited; 10 added documents, 0 unresolved citations. The
  seventh roll's certification therefore holds as issued - the defect was latent, not
  exercised, because its base was a real tag. From this postscript on, a certification quotes
  the preflight's summary word, and a roll whose preflight is re-run after a preflight fix
  carries a postscript like this one. Nothing is asked back.

- **RELAY-47 — THE SECTION-3 REDACTION RULING: A PUBLISH-BOUNDARY REDACTION OF SIGNED
  GATE-LOG TEXT IS DECLARED, NEVER EXCUSED** (new 2026-09-08, producer `main` after
  `port-base-20260908` / `314b1715`, venue desktop; the commit that carries this relay also
  carries the mechanism). `[VERIFIED-PRODUCER]` throughout. This is the ruling RELAY-46
  reserved this number for, and it answers section 4 of
  `docs/company-prompts/port-base-20260905-closeout-company-prompt.md`; that section stays as
  written (L25) and is superseded by this text for the one line it names.
  **THE RULING.** The reconcile guard for `config/gate-log.md` stays line-subsequence
  append-only: every pre-merge line survives, in order, insertions free. It gains exactly one
  ruled state and no exemption. A publish-boundary redaction (CLAUDE.md section 3) of a line
  inside a signed record is DECLARED, one row per redacted line, in
  `config/gate-log-redactions.yaml`: the redacting commit, the date, which signed record, the
  REPLACEMENT line exactly as it now reads (leading spaces included), and `reason:
  publish-boundary` - the only reason the schema accepts, because anything else is a rider
  under the record (L25), never an edit of it. The registry holds the AFTER text only. It never
  quotes what was removed, since a registry that quoted the removed string would put the name
  back in tracked prose, which is what the redaction existed to take out. Three consequences,
  each a guard and not a convention. **One - a declared redaction is LISTED, never silence and
  never a failure.** `drydocs.port.gate_log_redactions.check_append_only` walks the before
  lines as before; a pre-merge line that does not survive is ruled when the merged line
  standing where it stood is a declared replacement, and the live test prints it under
  `RULED REDACTIONS` (the `UNION_EXCLUSIONS` shape you already know from the backlog union).
  The rule is positional on purpose: the replacement must stand exactly where the removed
  line stood, so a declared line somewhere else in the file excuses no drop. **Two - an
  undeclared change fails exactly as it did**, and the message now says where a redaction is
  declared. Nothing about the guard softened; a second edit of the same record, a drop of the
  redacted line, or a redaction nobody declared are all still the violation, and the mechanics
  test (`test_gate_log_declared_redaction_is_ruled_not_failed`) asserts each of the three.
  **Three - a STALE declaration fails.** `stale_redactions` reports any row whose replacement
  is nowhere in the live file - the redaction was reverted or the record reworded, and the row
  now protects nothing - and `test_gate_log_redaction_registry_is_well_formed_and_live` fails
  on it in every checkout, before-dir or not. That clause is what makes the registry safe to
  have. **WHERE IT LIVES AND WHY THERE.** Your before-snapshot carries the old line, so YOUR
  guard is the one that fails, and you take `tests/unit/test_port_reconcile_guards.py` as a
  fast-forward. A ruling inside the producer's test file reaches you; a ruling inside a
  side-local overlay would not. So the registry is `canonical-producer` - a redaction is a
  producer ruling about producer text - with its own row in `PORT-MANIFEST.yaml` directly
  under the `config/gate-log.md` row, ahead of the `config/**` fall-through; the reader is
  `drydocs/port/gate_log_redactions.py` (its `MODULE_MAP.md` row is in the same commit, the
  boundary guard being default-deny); and the guard file imports it, its former local
  `append_only_violation` now a wrapper over the library. A tree that predates the registry
  has declared nothing and the guard behaves exactly as before - absent is not an error. **THE
  ONE ROW TODAY** is `55c2a204` (2026-09-07): clause C of the ADR 0007 agentic-QA gate record,
  signed 2026-07-23 - pre-merge line 795 in the producer's own reproduction, your snapshot's number for it is your union's - with the dated POSTSCRIPT under the
  record that already said so. Reproduced from here against the pre-redaction text at
  `55c2a204^`: with the registry, the live test passes and prints `pre-merge line 795 ->` the
  replacement; with the registry removed, the original failure returns naming the line. This
  is not PORT4's seam: PORT4 is an accepted DROP of a PATH, ruled in the side-local overlay;
  this is a changed LINE in a file both sides hold, and it needed its own file. PORT4's notes
  say so. **WHAT THIS MEANS AT YOUR CARVE-OUT.** Take producer text for the redacted line, as
  RELAY-46 and section 4 already said. Reconstruct nothing. Invent no local exemption. The
  mechanism lands after `port-base-20260908`, so the tag you are applying does not carry it
  and your 0908 close still fails the live test on that one line, correctly; that failure is
  the RULED state named by hand in your report, the way you already name the ruled
  `HISTORICAL_PATHS` drops. The eighth base, when it is cut, carries the registry as a
  clean-add, the library as a clean-add, and the guard as a fast-forward, and the line goes
  from a named failure to a listed ruling with no action of yours beyond the apply. If the
  guard still fails on that line after that base: check the instrument first (J76) - the
  registry is present, `git log -1 -- tests/unit/test_port_reconcile_guards.py` reads the
  base's version and not a superseded one, and the merged line is byte-identical to the
  producer's, four leading spaces included. **ONE CORRECTION TO THIS SIDE'S OWN TEXT**, as a
  rider: the SECOND POSTSCRIPT TO RELAY-46 wrote the redacting commit as `55c2a084`; it is
  `55c2a204`, as RELAY-46 itself and the registry row have it. The postscript stands as
  written; this line is its correction. Nothing is asked back.

- **RELAY-48 — THE ID CONVENTION, STATED WHOLE: 27 LETTERS FROZEN, THE SERIES IS THE
  MODULE, THE EDITION IS A DECLARED SEGMENT, BOTH PARTITION RULES RETIRED — AND STEP
  160'S MIRROR-ASSERTION ACTION IS WITHDRAWN** (new 2026-09-08, producer `main` after
  `port-base-20260908` / `314b1715`, venue desktop; this is DOC2, the "freeze relay proper"
  step 305 promised, and it takes the next free number as DOC2's note said it would).
  `[VERIFIED-PRODUCER]` throughout except where marked. **Read this first: it changes no
  file of yours.** Every mechanism it names is already in a base you have applied —
  `port-base-20260902` carried PLAN1 (`375dd962`), the gate `39b90843` and PLAN3
  (`e7dc4153`); `port-base-20260905` carried PLAN2 (`43fd345c`), CFG1, CFG2 and the rider
  gate `de8159eb` — and your 0905 close-out reports them applied `[SME-REPORTED]`. What
  was missing is one place where the convention is written as a whole rather than as
  four ledger steps, two postscripts and two relays, and one withdrawal the ledger still
  owes you. That is this entry.

  **ONE — THE FREEZE HALF (PLAN1 + PLAN3).** The 27 legacy series are FROZEN at the
  highest number each ever took on the producer's tree, refs and history, as of
  `FROZEN_ON = "2026-09-02"`. The table is the constant in
  `.claude/skills/groom-backlog/validate.py`, and this is it, quoted: A 4, B 5, C 44,
  D 11, E 2, F 2, G 136, GN 2, H 8, I 8, J 78, K 30, L 29, M 4, MM 14, N 28, O 92, P 6,
  Q 28, R 23, S 16, U 27, V 11, W 3, X 4, Y 7, Z 9. A letter recorded WHEN a phase opened,
  not what an item is about — G alone absorbed 136 items across six epics — so the freeze
  is not a cleanup, it is the end of a grouping axis that had stopped grouping.
  `--next-id G` is refused, and the message names the replacement ("the G-series was
  FROZEN on 2026-09-02 at G136 ... New ids take the module code: validate.py --next-id
  --module <module>"); `--next-id DD` is refused, and its message names the retired
  partition rule and the edition segment that replaced it. **The series is the module.**
  `docs/restructure/backlog/modules.yaml` `series:` maps 20 module names to 20 codes —
  CORE LOAD REV PLAN DOCGEN LIN DEEP REM WEB API AGENT META PORT LIBS REF TAX ONT CFG
  GRAPH DOC — and `validate.py --next-id --module <module>` is the only mint. Codes are
  three or more letters PRECISELY so a company mint can never be confused with a frozen
  letter, and none is DD. The file's manifest row is per-entry, and as of this relay its
  `entry_rule` says who owns the map: `series:` unions by module name, the producer's
  codes for shared modules cross whole, and a module only you hold gets its code from
  you and is never written by a port. Your `modules.yaml` equalled the producer's at 20
  and 20 on 2026-09-04 (EIGHTH POSTSCRIPT (2)), so today that rule has no company-only
  subject; it is written for the first one. **PLAN3 is why the freeze ported green.**
  FROZEN_SERIES was measured on the producer's tree and admits nothing above G136, so
  read against that table alone your `G10001`–`G10003` and `DD10001`–`DD10003` — legal
  when minted under the band rule — fail `test_frozen_series_take_no_new_ids` the day
  the freeze lands. `FROZEN_BAND = {G: 10003, DD: 10003}` judges a band-shaped number
  against the band's own max, so the six pass and `G10004` / `DD10004` / `G137` are
  strays. Your six band ids are READ and LISTED, never re-minted, and nothing you hold
  moves. `test_backlog.py` is per-entry by its row: the freeze block (FROZEN_SERIES,
  FROZEN_BAND, `_frozen_strays`, the agreement guards) is mechanism and crosses whole;
  the band block stays yours, in your spelling.

  **TWO — THE PREFIX HALF (PLAN2 + CFG2).** The id grammar is `[<EDITION>-]<MODULE><n>`
  for an item and `[<EDITION>-]Idea-<n>` for an inbox entry: edition first, the BASE
  edition unprefixed, so every existing id on either side parses unchanged. Which
  edition a checkout mints into is DECLARED, never inferred — read from
  `config/dev-environment.yaml` `edition:` and from nowhere else. That file is
  canonical-company; nothing in any range writes it. **You mint your own code at your
  own gate (§C3)**, into `config/taxonomy/editions.yaml`, whose per-entry row keeps your
  real rows (keyed by `code`, each with its `area_product_id`) and lets the producer's
  two `sample: true` rows never overwrite or shadow them. This relay names the file and
  the columns, not the code: the producer cannot name your code (CFG2 c) and does not.
  Both partition rules are RETIRED FORWARD-ONLY (§C4): the 2026-07-20 DD reserve and the
  2026-08-18 number band (producer 1–9999, company 10000+) govern no new mint; every id
  they produced stays readable — your `DD1`–`DD10`, `DD10001`–`DD10003`, `G10001`–`G10003`
  and your band-shaped ideas. Between the roll that carried PLAN2 and your code mint you
  mint no new ITEM — and that is a MECHANISM, not a request: the allocator reads the venue
  file, finds no `edition:` key, refuses, and names the key and both files in the refusal.
  Your idea channel stays open meanwhile, band-shaped above 9999 (rider
  `idea-series-grammar` C1; the shape your 09-05 renumber already has). **The one line
  you write once your code is minted** is `edition: <your-code>` in your
  `config/dev-environment.yaml`; from then on your items mint `<code>-<MODULE><n>` and
  your ideas `<code>-Idea-<n>`, counting from 1 in your own number space, and nothing
  about the code is decided here. Your 0908 apply's "`edition:` deliberately unset until
  your own mint" `[SME-REPORTED]` is exactly this state, read correctly.

  **THREE — STEP 160 IS WITHDRAWN.** Step 160 in the ledger below says, in bold, "YOUR
  ACTION: write the MIRROR assertion (`n >= 10000`, grandfathering your existing low ids as
  a committed constant) and allocate new ids at 10000+." **Do not.** The band it mirrors
  retired forward-only at §C4, and a mirror written today would declare `<code>-LOAD1`
  illegal on your own tree the day you set `edition:`. The replacement is the
  edition-segment check that PLAN2 already put in `validate.py` and
  `drydocs_core/backlog_store.py`: a segment is legal only if `editions.yaml` declares
  it, an undeclared segment is a typo and never a tenant, and a base id above 9999 is
  refused as the retired rule's shape. Step 160 stays in the ledger as written (an
  applied step is a record), and this paragraph is its withdrawal; the ledger's step 273
  region reads the same way wherever it leans on the band. If you already wrote a mirror
  assertion, keep it as the grandfathering constant it also is (your `COMPANY_BAND_FLOOR`
  reading of the band block is that) and let FROZEN_BAND, not the mirror, be the guard
  that reads your six.

  **FOUR — TWO AXES, SO THAT "BOTH MACHINES AND BOTH REPOS" STOPS READING AS ONE THING.**
  Axis 1 is REPOS: producer and company, disjoint histories, a one-way port. The edition
  prefix separates THESE — your ids carry your segment, the producer's carry none. Axis 2
  is CHECKOUTS: every machine, worktree or session on one side is a checkout of the same
  trunk. The push-before-work claim (`status: in_progress`, pushed) and the `wip/` branch
  rule separate THESE — two checkouts of one repo minting in the same second are what the
  allocator's remote-ref union exists for. The number band was a repo-axis rule wearing a
  checkout-axis shape (it never stopped two producer machines from minting one number;
  the push-the-stub protocol does). "Both machines and both repos" meant axis 2 on our
  side and axis 1 between us; an agent that reads them as one axis will either write a
  mirror band (axis 1 by numbers) or skip the pushed stub (axis 2 by hope), and both have
  happened.

  **FIVE — WHERE THIS LIVES IN YOUR APPLY.** The APPLY BY DISPOSITION section above gains
  one paragraph, "THE ID CONVENTION'S ROWS", naming the three per-entry rows
  (`config/taxonomy/domains.yaml`, `config/taxonomy/editions.yaml`,
  `docs/restructure/backlog/modules.yaml` `series:`), the one canonical-company key
  (`edition:`), and the canonical-producer trio that reads them (`CLAUDE.md` section 0's
  mint rule, `validate.py`, `backlog_store.py`) — the mint rule in `CLAUDE.md` now says
  the edition segment and "declared in `config/dev-environment.yaml`, never inferred", so
  a wholesale take of `CLAUDE.md` is right for you as written: its `base` is the
  producer's declaration in the producer's venue file, not an instruction to yours. One
  item that DOC2's acceptance said would ride this relay does not: MM13's correction to
  the `data-flow-overview` gate prompt (nine MM3 sites that mean MM7) is still `todo` on
  the producer, and a relay that tells you to correct your copy before the producer has
  corrected its own would put your DRAFT ahead of the producer's; it rides with MM13's
  build. Nothing is asked back.

- **RELAY-49 — THREE LIVE-CONFIG COUNT PINS LEFT THEIR TESTS: THE NUMBERS ARE NOW A
  `census:` BLOCK IN YOUR OWN `config/dev-environment.yaml`, AND THE THREE TEST FILES
  CROSS BYTE-IDENTICAL FROM THE NEXT BASE ON** (new 2026-09-08, producer `main` after
  `port-base-20260908` / `314b1715`, venue desktop; this is PLAN9, minted from your
  sixteenth report's hand-merge list `[SME-REPORTED]`). `[VERIFIED-PRODUCER]` throughout.

  **WHAT MOVED, AND WHY.** Three unit guards pinned a count over a REAL config file
  so the picture could not drift silently, and each count was a fact about ONE
  checkout's rows, because every file they count is `per-entry` in `PORT-MANIFEST.yaml`
  and you hold rows the producer never sees. Checked into the TEST, the number collided
  at every roll and you re-pinned it by hand — three times per port, as your list said.
  The survey the item required found exactly these three and no others (the vocabulary
  fragment count the item named as a candidate is not pinned anywhere; the
  `ui-tests.yaml` pins in `test_ui_tests_ledger.py` count a `canonical-producer` file,
  so they are the same on both sides after a take and are not this class):

  | test | pinned over | producer value | your value at the 2026-09-03 apply |
  |---|---|---|---|
  | `tests/unit/test_docs_coverage.py::test_the_live_coverage_census_is_pinned` | `config/taxonomy/software-registry.yaml` + `config/doc-source-registry.yaml` | (17, 15, 10, 8) | your own tuple, hand-merged each roll |
  | `tests/unit/test_schema.py::test_constraint_count` (`EXPECTED_CONSTRAINTS`) | `drydocs_core/schema/constraints.cypher` | 55 | ahead — your supplement blocks |
  | `tests/unit/test_source_bindings.py::test_reports_cover_every_automated_dataset` | `config/source-registry.yaml` `acquisition.mode: automated` | 15 | 17 |

  One shape for all three, the one `capability_assert` already uses in the same file:
  the value lives in `config/dev-environment.yaml`, which is `canonical-company` — each
  side keeps its own, a port never overwrites it — and the test READS it. The guard
  keeps its teeth (a wrong number in the venue file fails the test with a message that
  names the key), the test file carries no count of its own, and the history of each
  number stays in the test's docstring and comments, where a reader looking at the guard
  finds it. The producer's block, as shipped:

  ```yaml
  census:
    docs_coverage:
      products: 17
      products_no_corpus: 15
      corpora_total: 10
      corpora_unclaimed: 8
    schema_constraints: 55
    automated_datasets: 15
  ```

  **WHAT TO DO AT THE NEXT BASE THAT CARRIES THIS** (it is not in `port-base-20260908`).
  (1) Take the three test files wholesale — they fall to the `tests/**` default and carry
  no number now, so there is nothing to hand-merge; `test_schema.py` and
  `test_source_bindings.py` keep their `evaluate` rows for whatever ELSE your copies
  carry, and both rows' notes now say the count is not one of those things. (2) Add the
  `census:` block to YOUR `config/dev-environment.yaml` with YOUR numbers — the file is
  yours, so this is the "new producer KEYS are ADAPTED BY HAND" case its own manifest row
  already describes; a copy with no block fails all three guards with a message naming
  the missing key, which is the same refusal shape as the allocator's `edition:`. The
  numbers you write are the ones your current hand-merged pins hold today: read them off
  your test files before the take, not after. (3) `tests/unit/test_dev_environment.py`
  gains `test_census_declares_every_pin_the_guards_read`, a shape check on the block
  (six integer keys) — it crosses with the file. (4) The generated
  `drydocs_core/schema/schema_graph.cypher` moves two comment lines (the render no
  longer names `EXPECTED_CONSTRAINTS`); it is a derived render, so re-run
  `scripts/render_schema_graph.py` on your side rather than taking the file. From then
  on, when your registries move, you edit `census:` and say why in the commit — never
  the test. Nothing is asked back.

- **RELAY-50 — THE `updated:` HEADER KEY IS PER-SIDE: A PORT NEVER WRITES IT, AND THE
  MANIFEST NOW SAYS SO** (new 2026-09-09, producer `main` after `port-base-20260908` /
  `314b1715`, venue desktop; **renumbered from 48 to 50 on 2026-09-09** — it was drafted
  the same day RELAY-48 and RELAY-49 landed and took a number already in use. Neither
  colliding entry had shipped: both postdate `port-base-20260908`, so nothing you hold
  cites either number. RELAY-48 is and stays the id convention). `[VERIFIED-PRODUCER]`
  throughout. J59 (built on the laptop
  lane, merged 2026-09-09) adds a commit-time check, `scripts/check_header_freshness.py`
  behind `.pre-commit-config.yaml`, that holds the `updated:` header key J58 made required
  against the file's actual change: a staged governed file must say today. The hook is
  machine-local and only runs where `pre-commit install` has been run (the J62 step in the
  session ritual). The half that concerns a port is clause (c), landed in this commit: git
  dates DO NOT survive the port. The two repos have disjoint histories, so on your side a
  ported file's git date is the day it arrived, not the day its content changed - which is
  why the IN-FILE date is the cross-repo freshness mechanism, and why a port that copied
  the producer's `updated:` would make every ported file look freshly touched on your side
  and hand the hook a lie to check. `PORT-MANIFEST.yaml` therefore gains a top-level
  `per_side_fields:` block declaring `updated` per-side on every governed file: a take
  applies CONTENT and leaves the key as your side last wrote it, and your side refreshes
  it when the applied content changed your tree - that is a change on your side. The block
  WINS over any per-entry row's "UNNAMED FIELDS: producer-owned" default; the rows that
  already say "`updated` is the row owner's" are consistent with it and are unchanged.
  What this changes for your apply: one hand step, because the apply is hand-merged by
  the reconcile-port ledger and no script writes governed files for you - at a
  canonical-producer take of a governed file whose content changed, set `updated:` to your
  apply date instead of accepting the producer's; where nothing changed, leave it. The
  J59 hook, once you have run `pre-commit install`, then holds you to the same rule on your
  own edits. Nothing is asked back.

- **RELAY-51 — THE `venues:` KEYS ARE A HAND-COPY YOU WERE NEVER TOLD TO MAKE, AND
  RELAY-31'S "TWO TO ZERO" IS NOW "TWO TO ONE"** (new 2026-09-09, producer `main` after
  `port-base-20260908` / `314b1715`, venue desktop; raised by your `port-base-20260908`
  report's D5 `[SME-REPORTED]`). `[VERIFIED-PRODUCER]` throughout.

  **THE CORRECTION FIRST, BECAUSE IT IS A PROMISE THIS PROMPT MADE AND CANNOT KEEP.**
  RELAY-31 (2026-09-07) split two `test_backlog.py` tests so a producer-only fact would
  stop being red on your tree by construction, and it told you that when the range landed
  your edition-absent count "goes from two to zero." **That is now wrong, and the cause is
  producer-side.** PLAN6 landed the next day (`de0e5b7c`, 2026-09-08) and added
  `test_declared_venues_are_lists_of_codes_the_venue_file_declares` carrying an
  unconditional `assert codes, "config/dev-environment.yaml declares no venues: section"`
  — the same shape RELAY-31 had just carved out, reintroduced one commit after its own
  fix. Your D5 named both standing failures correctly; the second one is ours, not yours.

  **FIXED AT THE PRODUCER, IN THIS COMMIT, ON RELAY-31'S OWN PATTERN.** The guard is split
  the way `test_the_venue_is_declared_in_the_venue_file...` was:
  `test_declared_venues_are_lists_of_codes_the_venue_file_declares` keeps the SHAPE check
  and the membership check, and holds on any tree — the membership half is checked only
  where a `venues:` block exists, so a tree carrying ported items with `venue:` and no
  block yet passes instead of failing on a fact about the producer. The presence assertion
  moves to `test_the_producer_declares_its_venues`, which says in its docstring that it
  carries a producer-only fact and that a per-entry take drops it. Both read one helper,
  `_declared_venue_codes()`, so they cannot drift.

  **WHAT TO DO WHEN THE RANGE LANDS.** Take the split guard; drop
  `test_the_producer_declares_its_venues` the way you drop
  `test_the_producer_declares_itself_the_base`. Your edition-absent count then does reach
  zero. Separately and independently of the suite: `config/dev-environment.yaml` is
  `canonical-company` and you adopt new KEYS by hand, so **copy the three `venues:` keys
  in** — `controlm-server`, `oracle-replica`, `neo4j` — with **your** `available:` values,
  not the producer's. The keys are the shared vocabulary; the availability is your local
  fact, exactly as the block's own header says. Until they are in, the membership half of
  the guard resolves nothing and `lane-handoff`'s V mark cannot see a venue wall — but
  nothing goes red, which is the point of the split. `edition:` remains yours to mint at
  your own gate and is untouched by this.

  Nothing is asked back.

- **RELAY-52 - NINETEEN GATE PROMPTS CARRY A DATED S5 PATH RIDER; YOUR COPIES WIN, SO TAKE THE
  RIDER BLOCK BY HAND** [VERIFIED-PRODUCER] (2026-09-09, producer CFG7, venue desktop). The
  premise-drift review measured 30 broken path citations across 19 of the 60 gate prompts, 25 of
  them one pair: config/taxonomy-ontology-map.yaml and
  drydocs_core/ontology/relationship_vocabulary.yaml, both DIRECTORIES of the same name since
  `d84d86bc` (S5, the per-domain shard). CFG7 swept them ONCE, deliberately not with a guard: the
  sanctioned edit shape keeps the old path in the text, so a bare-path guard would fail on the
  marker recording its own fix. The sweep is a header RIDER - a dated comment block after each
  page's leading comment, saying which of the two names the page cites and what each is now - and
  NO clause text moved (L25: a signed page gets a rider, never an edit; a signed record's
  citation still matches the text). `updated:` moved to 2026-09-09 on the nineteen, per the
  per-side rule in `per_side_fields` (RELAY-50): set it to YOUR apply date if you take the rider.
  `config/gate-prompts/**` is canonical-company, so nothing here reaches you by a take; the
  nineteen are: bmc-docs-lexical-load, code-graph-package-layer, controlm-avg-run-supplement,
  controlm-hosts-topology, controlm-q1q3-phase1, doc-traceability-feedback, email-dl-contact-point,
  envelope-property-terms, fid-identity-and-scope, platforms-taxonomy, product-cabinet-attribution,
  rua-load-shapes, seal-app-ref-edge-reshape, seal-attribution-match-policy,
  seal-tom-attribution-reshape, self-documentation-code-graph, software-usage-patterns,
  software-version-context, sosa-jobrun-observation. The three open items whose NOTES cite the
  old names (K26, E1, L19) were left alone: a note describing 2026-06 or 2026-08 work names the
  file as it was, which is a record, not a claim. Nothing is asked back.

- **RELAY-53 - THE EIGHTH ROLL: `port-base-20260908..port-base-20260909`, 172 COMMITS, AND WHERE
  RELAYS 47 TO 52 LAND** [VERIFIED-PRODUCER] (2026-09-09, venue desktop). A SMALL roll on
  purpose, cut at the Lane A close so the per-side fixes reach you while your tech-debt work is
  under way: the range is steps 354-367. 294 changed paths in 8 classes (canonical-producer 70, canonical-company 20, never-port 6, per-entry 107, union-append 2, evaluate 17, default_ok 65, derived 7) What it carries that your apply must know:
  (1) `PORT-MANIFEST.yaml` gains the `per_side_fields:` block (RELAY-50) and the epics row's
  `order:` is per-side (`fe557fce`); (2) the three `venues:` keys are a hand-copy (RELAY-51);
  (3) the nineteen gate-prompt riders are a hand-take, your copies win (RELAY-52); (4) the
  redaction registry `config/gate-log-redactions.yaml` and its reader arrive canonical-producer
  (RELAY-47) - read RELAY-47's contract before your first §3 redaction; (5) PLAN9's `census:`
  block in `config/dev-environment.yaml` wants YOUR numbers (RELAY-49); (6) the port preflight
  now fails closed with a NOT CHECKED verdict (`2425c206`, step 366) - a certification quotes
  the verdict word, and the seventh roll re-certified on the fixed instrument holds as issued;
  (7) `S11` is closed as SUPERSEDED - no `drydocs_plan/`, `drydocs_docgen/` or `drydocs_port/`
  package move is coming; the subpackages you already hold are the ruling (ADR 0018 D4); (8) the
  eighteen ADR 0018 re-export shims are NOT removed in this range - that is GRAPH5, minted, and
  it lands in the NINTH roll with its own relay, so nothing in this range breaks an import path;
  (9) 56 new backlog items and one new epic (`team-edition`, order 28 - per-side, seat yours as
  you like) are clean-adds by id; (10) three new module runbooks (`drydocs-lineage`,
  `drydocs-review`, `drydocs-docgen`) and their committed HTML arrive under `docs/design/**`
  (evaluate on collision). RED AT PUSH (J77): one - `5f0e730c`, RELAY-47's landing, failed three guards and
  `1f54b5d4` fixed them one commit later; the eighth footnote names the cancelled runs. Nothing
  is asked back.

- **RELAY-54 - THE WIRING FACT HAS ITS OWN HOME AND IT IS PER SIDE: `wired` IS A SIXTH
  DESCRIPTOR AXIS, `confirmed` CROSSES AGAIN ON SHARED ROWS, AND YOUR TWO STANDING PINS
  RETIRE** [VERIFIED-PRODUCER] (2026-09-09, venue desktop; lands in the NINTH roll). Two gates
  signed in one sitting on 2026-09-09 - `registry-wiring-readiness` (18/18) and
  `source-descriptor-axes` (13/13) - and CFG13 is the build. What changes for you: (1)
  `config/source-descriptors.yaml` gains a `wired:` block, one entry per registry-home dataset,
  `true` or `{value: false, reason: <forty characters or more>}`; the reader refuses a missing
  block, a missing entry, an unknown id, a bare false and a short reason at construction, so a
  dataset you register without answering fails on its first read - by design; (2) the block is
  PER SIDE (`per_side_fields` names `wired`): your entries say what is built on YOUR tree and are
  never overwritten by a port in either direction - on take, keep your block and add entries
  only for ids new to you; (3) `require_confirmed()` refuses unless confirmed AND wired and its
  message says which failed; `UnwiredSourceError` is a subclass of `UnconfirmedSourceError`, so
  every gate that caught the old refusal still does; (4) the source-registry entry_rule is
  amended per the sitting's E1: `confirmed` and its `_by`/`_at` stamps now CROSS on shared rows
  as the producer's signed WHAT - a company that has not ratified a producer sign-off records
  that in its own gate-log; company-only rows stay yours, as per-entry already rules; (5) your
  two standing pins - `cm_hosts` and `controlm:deftable-xml-export` - RETIRE: declare each row's
  own `wired` value in your block and record the retirement as a gate-log entry (C4) rather than
  deleting the pinned entries; (6) the load map's wiring cross reads the declared value on
  registry-home rows, and `test_the_key_reports_and_never_rules` is amended to admit the axis
  while still forbidding a wiring field on the registry row - take the test with the renderer;
  the console model's matching read lands under the web pen with its own step; (7) the DataHub emission carries `wired` as its own property and tag,
  and `confirmed` on an asset means the semantic ruling only (C2). One count, corrected here so
  the record and the build agree: the sitting's B5 said the 21 loading rows declare true - 21 is
  the `confirmed` count; by command 13 registry-home datasets have a loader bound producer-side
  and declare true, and 17 declare false with their reason (E3: counts by command, never
  carried). Nothing is asked back.

- **RELAY-55 - A GATE-LOG REDACTION NOW DECLARES WHOSE ACT IT WAS, AND YOU MAY KEEP THE TRUE
  NAME** [VERIFIED-PRODUCER] (2026-09-10, venue desktop; lands in the NINTH roll). You raised
  this at the close of `port-base-20260908` and you were right: a publish-boundary redaction
  (CLAUDE.md section 3) is a PRODUCER-venue act, because the producer is the side that
  publishes. Company-side there is no publish boundary, and the string in question is a
  company-internal system name in a private repo - which is exactly the venue entitled to hold
  it. Importing the redaction removed a true name from the only tree allowed to keep it, and
  you took it anyway because the alternative was worse: the registry's own header rules that a
  declared replacement missing from the live file is STALE, so a tree keeping the true name
  would have held a permanently failing declaration with no exemption path. That was a stopgap
  and this removes it. What changes: (1) every row in `config/gate-log-redactions.yaml` carries
  `side: producer | company`, and the reader refuses a missing or off-vocabulary value; (2) the
  stale check is scoped to that side - only the OWNING side's declaration can go stale, and on
  that side it is exactly as strict as before, which is the clause that makes the registry safe
  to have; (3) which side a checkout is runs on a new `side:` key in
  `config/dev-environment.yaml`, which is canonical-company, so YOUR copy declares `side:
  company` - that file's entry_rule already says new producer keys are adapted by hand, and
  this is one of them; (4) a checkout that has not declared reports NOT CHECKED with the reason
  naming the key, never clean and never stale - assuming producer would recreate the failure
  on the tree least able to notice, so it is not assumed. WHAT THIS MEANS FOR THE ONE EXISTING
  ROW (`55c2a204`, the ADR 0007 clause C redaction, `side: producer`): once you declare `side:
  company` you may restore the true name in your own `config/gate-log.md` under a dated
  postscript on that record, and the guard stays green - the row is not yours and cannot go
  stale on your tree. You may equally leave the producer's text in place; both states are legal
  and your `side:` is what says which one you are in. The choice is yours and the producer holds
  no opinion on it. Nothing is asked back.

- **RELAY-56 - `drydocs bootstrap` RAISES AN AttributeError ON YOUR INSTANCE, AND IT IS ONE
  MISSING METHOD, NOT A CONSTRAINT PROBLEM** [SME-REPORTED] [VERIFIED-PRODUCER] (2026-09-10,
  producer verification venue desktop, by command over this tree). You reported
  `AttributeError: 'Neo4jClient' object has no attribute 'constraints_detail'` at
  `drydocs/cli_schema.py:346`. FIRST, the reassuring half: your declared constraints are fine.
  The D8 guard ran and its missing list was empty, so every declaration landed; the crash is one
  line later, in the INVERSE check G130 added - what is live that nobody declared. No constraint
  is wrong on either side and nothing about your schema needs attention because of this.
  THE FIX IS ONE METHOD on your `drydocs_core/neo4j_client.py`, and nothing else in that file
  needs to move:

  ```python
  def constraints_detail(self) -> tuple[dict, ...]:
      """Name, kind, entity, labels and properties for every live constraint (G130)."""
      return tuple(
          dict(r)
          for r in self.run(
              "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
              "RETURN name, type, entityType, labelsOrTypes, properties ORDER BY name"
          )
      )
  ```

  WHY YOU HAVE THREE QUARTERS OF ONE COMMIT, because the reason is more useful than the patch.
  `01761011` (G130, 2026-08-30) added all three halves of that call chain together:
  `constraints_detail` on the client, `undeclared_constraints` in
  `drydocs_core/schema/constraints.py`, and the caller in `drydocs/cli_schema.py`. Your
  traceback shows the import on the line above succeeding and the caller running, so you hold
  both of the canonical-producer files and took them wholesale - exactly as the manifest says
  to. The fourth file resolves through `default_ok` to the DEFAULT, which is
  evaluate-on-collision because both sides authored it, so it waited on a hand-merge and the
  sixteen lines did not make it. Nobody did anything wrong; the commit was split across two
  dispositions and only one of them crosses unattended. G130 has been in every roll since
  `port-base-20260901`, and an uncalled missing method raises nothing until it is called, which
  is why it sat this long.
  PRODUCER-SIDE FOLLOW-UP, so you do not have to watch for the next one: PORT12 is minted to
  report this shape at roll time - a name added to a hand-merge file in a range and newly
  referenced from an unattended file in the same range - with G130 as its positive control. When
  it lands, a split pair arrives as a relay line naming both halves. Nothing is asked back.

- **RELAY-57 - THE SPLIT-PAIR CLASS, SWEPT ACROSS EVERY ROLL YOU HAVE APPLIED: TWENTY-ONE
  CONFIRMED PAIRS, AND THREE OF THEM WOULD KILL YOUR CLI OUTRIGHT** [VERIFIED-PRODUCER]
  (2026-09-10, venue desktop; the three CLI-killers land in the NINTH roll and are PREVENTABLE,
  the rest are already on your tree). RELAY-56 gave you the one-method fix for
  `constraints_detail`. This is the same defect shape swept across all seventeen roll ranges
  with the PORT12 instrument, then triaged and adversarially refuted name by name: 82 candidate
  pairs were examined, 61 were killed, and these 21 survived. Every one is a definition added to
  a file YOU reconcile by hand while the same range added a reference to it from a file that
  reaches you unattended.
  **FIRST, THE THREE THAT HAVE NOT SHIPPED YET - the ninth roll can carry them and the break
  never happens.** `drydocs/cli_docs.py` (canonical-producer, taken wholesale) gains a
  MODULE-SCOPE import of three constants defined in `drydocs/docs_coverage.py` (which falls to
  the manifest default, so you hand-merge it): `CLASS_LOADED`, `CLASS_SEMANTIC_HOLD`,
  `CLASS_WIRING_HOLD`. This is worse than the G130 case in kind, not just degree. G130 gave an
  AttributeError when one verb ran; this raises `ImportError` while `drydocs/cli.py` is still
  importing, so EVERY command dies - `drydocs --help` included, and
  `python -c "import drydocs.cli"` with it. When you apply the ninth roll, take
  `drydocs/docs_coverage.py`'s new class block in the same sitting as `cli_docs.py`, or take
  neither. Six more names from that same file - `blocker`, `blocker_reason`, `classes_probe`,
  `count_note`, `dataset_id`, `loaded` - are runtime rather than import-time, same file,
  same sitting. (This sentence said FOUR and listed five until the roll-close run below
  counted them; `blocker_reason` is the one it was missing.)
  **THEN THE ONES ALREADY ON YOUR TREE, worth a grep each rather than a project.** From
  `drydocs_core/data_root.py`: `dpl_mac_dir`, `glue_inventory_dir`, both reached from
  `drydocs/cli.py`. From `drydocs_lineage/curation.py`: `DecisionsError`, `load_decisions`, also
  from `cli.py`. From `drydocs_lineage/writer.py`: `ExtractProvenance`, `gate_bound_labels`.
  From `drydocs_api/exports.py`: `execute_spec`, reached from `drydocs_api/agent_query.py`.
  Each is a one-line check on your side - does the name resolve in your copy of the defining
  file - and if it does, there is nothing to do.
  **AND SIX THAT ONLY REDDEN YOUR SUITE**, listed so a red test is attributable rather than
  mysterious: `EXPORT_LIMIT_CEILING` and `execute_spec` (test_result_completeness,
  test_agent_query), `BadCredentialsError` (test_console_auth), `Neo4jDriverBounds`
  (test_neo4j_client), `bounds` (test_neo4j_client), `DECISIONS_SCHEMA`
  (test_cli_lineage_load). A test file that is NEW in a range arrives as a clean-add while the
  definition it exercises waits on your hand-merge, which is the same split one level down.
  **WHAT WE ARE NOT CLAIMING.** The producer cannot read your tree, so every line above is
  "this pair exists in the range" and not "this is broken on your instance". Several of the 61
  we killed were killed precisely because your own apply reports showed the definition had
  already crossed. Treat the list as where to look, not as a defect report - and if a name
  resolves fine in your copy, that pair is closed with no action.
  **GOING FORWARD** the producer runs `scripts/port_split_pair_check.py <previous-base-tag>` at
  every roll close and each pair becomes a relay line, so this is the last time the list arrives
  as a backlog rather than as a paragraph. Nothing is asked back.

- **POSTSCRIPT TO RELAY-57 - THE FIRST ROLL-CLOSE RUN, AND IT FOUND A FAMILY THE HAND TRIAGE
  HAD COLLAPSED TO TWO NAMES** [VERIFIED-PRODUCER] (2026-09-10, venue desktop, at the ninth
  roll's tag). The paragraph above promised a run per roll; this is it, over
  `port-base-20260909..HEAD`: 18 pairs across 114 changed Python files, 12 names too
  ambiguous to attribute, 6 new files carried whole as clean-adds. THE THREE CLI-KILLERS ARE
  UNCHANGED and are the reason this roll went out - `CLASS_LOADED`, `CLASS_SEMANTIC_HOLD` and
  `CLASS_WIRING_HOLD` in `drydocs/docs_coverage.py`, imported at MODULE SCOPE by
  `drydocs/cli_docs.py`. Take that file's new class block in the same sitting as
  `cli_docs.py`, or take neither.
  WHAT IS NEW is the whole CORE13 bounds family, which the August sweep surfaced as two names
  and is actually eight. `drydocs_core/config.py` (default_ok, so you hand-merge it) gains
  `Neo4jDriverBounds`, `DRIVER_BOUND_DEFAULTS`, `load_driver_bounds`, `connection_timeout`,
  `connection_acquisition_timeout`, `transaction_timeout` and `max_transaction_retry_time`,
  and `drydocs_core/neo4j_client.py` gains `bounds` - every one of them reached only from
  `tests/unit/test_neo4j_client.py`, which is also default_ok. So this one REDDENS A SUITE and
  breaks no command: take the config block and the test together, or neither, and step 375
  is the content. The reason the earlier list said two is that a hand triage reads the names
  a human noticed and an instrument reads all of them, which is the whole argument for
  running it per roll rather than per sweep. Nothing is asked back.

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
| T13 | DPL registry field contract validated vs a REAL per-SEAL export (pipeline_id.json/dataset_id.json) — amend dpl_registry.py header + fixtures together, cite provenance (the T10 discipline) | **THE VALIDATION RAN 2026-08-31** (company-side; both halves profiled, session logged at `internal/research/G64-SME-MM-research.md`, pending back-flow) — but the row asks for the AMENDMENT, not the profile, so it stays **pending**. What the profile found is the `dpl-pipeline-registry-contract` gate's clause C1 to rule (G64) and its dataset sibling's (G65); neither has signed. Producer-side the profile changed one thing that needed no gate: G135 makes the extractor able to REPORT a wrong contract (per-field census, absent-vs-unreadable active flag, seal-inferred-from-path counted, unmatched JSON counted) without moving a single field name |
| T14 | rua collector convergence: company's own -n implementation vs producer G18 v2 — reconcile to ONE v2 (flags, scripts.tsv columns incl. sha256, size cap, COLLECTOR_VERSION stamp) so bundles stay cross-ingestible. Step 49e's G45 listing fallback is the same family — reconcile together | pending (producer belief, as of 2026-08-01) |
| T15 | G33 company code-graph load: run YOUR post-U6 `snapshot.ps1` (snapshot `*.json` is never-port BOTH ways; primary on-main checkout, never a worktree) → `drydocs load-code-snapshot` into your graph; second `:Project` root is INTENDED (gate §B3(a)); rides with the Tier A ratification entry (guardrail 6) | pending (producer belief, as of 2026-08-01) |
| T16 | CM_DEF_VJOB_DETAIL built for real in psgmgr — retires the G39 staging stand-in as the feed (G40 parse stays as cross-check); premise correction folded into G22 prep. NOTE step 49g: if the XML export becomes a standing feed, this retirement gains a SECOND path — the unruled precedence question decides, not the port | pending (producer belief, as of 2026-08-01) |
| T17 | AIS platform supplement follow-through (company-local; NO producer payload): (1) the back-flow REFUSAL — producer grounds formalized in `87ba693` (premise false: producer has no AIS layer; C12 took the direct route); (2) apply-platforms-supplement disposition (fold/delete/keep); (3) ais_* constraint CREATEs vs commented seeds on the scheduler_kind precedent, with EXPECTED_CONSTRAINTS arithmetic written in; (4) commit the company-local cli.py wording fix before the next port branch. One fact owed back: are any company Neo4j environments carried forward rather than rebuilt from bootstrap? | **(2) DISPOSITION SETTLED 2026-08-11 (SME): the verb is DEPRECATED-IN-PLACE — no-op on a fresh graph, seeds commented out and audit-kept, kept in the sequence only for old-graph deprecate-in-place, optional to run. It belongs in `CHAIN_EXCLUSIONS` WITH ITS REASON, not in the chain (see the supplements bullet in the divergence ledger). Clauses (1), (3) and (4) remain producer belief as of 2026-08-01.** |
| T18 | Depgraph fork capability catch-up (owed action 48e, PORT-REPORT-94132c80): your separately-owned depgraph fork lacks the U6 multi-root resolver (and `--tree`), and the producer remote is unreachable from it, so the port could not remediate. Until it catches up, `config/dev-environment.yaml` keeps `depgraph.capability_assert: false` (test skips, owed action recorded). When it gains the capabilities: flip the flag true and your `snapshot.ps1` refusal guard goes live | pending (producer belief, as of 2026-08-01) |
| T19 | N3–N6 LOAD-MAP adoption gate — **narrowed 2026-08-01**: registry v2 is ADOPTED (N9 full-adopt at PORT-REPORT-57914bf4), so this row now covers ONLY the N3 class-declaration derivation, the N4/N5 renders and N6. The id-collision blocker is resolved by the v2 rename (`pat:product-catalog` / `pat:people-report`); what remains is the sourceless company-only loaders. Company `cli.py` still has no `COMMAND_LOADERS`/`CANONICAL_LOAD_SEQUENCE` and the load-map pair stays out of the company board render until this rules | pending (producer belief, as of 2026-08-01) |

| T20 | **Catalog-loader review (8 findings on the company's `pat_*`/`product_lines`/`products`/`snow_support_crosswalk` cypher) — DISCHARGED at PORT-REPORT-40c35724** (2026-08-03): item 1, the `products.cypher` orphan fix, is APPLIED company-side; items 2–8 live in the company's own backlog/inbox; count-orphans-before-applying rides T23. The full 8-finding text was retired from this row at the 2026-08-05 condensation — it lives in this file's git history and PORT-REPORT-40c35724. Producer-side the same shape closed as C22 (step 70) + C24 (step 94). | **DISCHARGED 2026-08-03** (status cell corrected 2026-08-04 — producer-side staleness, the T11 class) |
| T22 | **`_client(database)` follow-up — company backlog row DD6** (created 2026-08-03, the port's own finding): company `cli.py` `_client()` takes no `database` param, which (a) is already a LATENT crash in `patch_window_cmd` (calls `_client(database=...)` today), and (b) blocked the two new verbs — `docs-verify` (Q7) and `bootstrap-schema-graph` (targets `ddschema`). DD6 = add the param, wire both DEFERRED verbs, add the `ddschema` provisioning DDL (the G51 twin). Modules are already ported; only the thin CLI wrappers wait | pending (producer belief, as of 2026-08-03; company row DD6) |
| T23 | **S3/C17 GRAPH writes on the company graph** — config/code landed at PORT-REPORT-40c35724, loads did NOT (guardrail 6: always yours). S3 re-key: **DROP `port_unique` FIRST**, then create `port_app_key` — a same-name re-declare succeeds and does nothing (verified live producer-side); all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance silently doubles canonical nodes. C17: count existing orphans BEFORE the every-run `orphan` flag goes live (report's own note). **RIDER 2026-08-05, from a company-side T23 lookup the producer was shown:** that session first read T23 broadly (as C23 `IN_DIMENSION` bootstrap + G51 `ddschema` populate + all S3/C17 re-keys + the folder-attribution migration) from downstream references, then corrected itself against this row and converged on it — so the row is right as written, and G51 `ddschema` populate is **T22/DD6 territory, not T23**. **DIRECT EVIDENCE 2026-08-04 — this row's own prediction FIRED, so it is no longer only a producer belief.** The company ran `drydocs load seal_applications` against a graph that took the S3 CODE but never the S3 re-key and got `Neo.ClientError.Schema.ConstraintValidationFailed: Node(97) already exists with label 'BusinessApplication'`. Mechanism confirmed against producer source: pre-S3 nodes carry `seal_id` and NO `app_id`; `MERGE (a:BusinessApplication {app_id: row.app_id})` cannot match them because a uniqueness constraint IGNORES NULLS, so it mints a second node, and the next line `SET a.seal_id = row.app_id` then collides with the original's `seal_id` (both properties are separately unique-constrained, `constraints.cypher:43-44`). That is this row's "all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance silently doubles canonical nodes", happening. **Remedy relayed:** backfill `app_id = seal_id` on the pre-cutover nodes BEFORE re-running, after checking whether the partial run already doubled any — batches commit per flush, so a mid-load crash leaves a partially-doubled graph, not a clean rollback. **Producer payload now exists (S10, built 2026-08-05, lands with this port):** all four `:BusinessApplication` MERGE loaders refuse up front when the target database holds a node with a null `app_id`, before any write and before the :JobRun. The refusal does NOT substitute for this row — it prevents the crash, it does not repair live state. Two things to keep straight, though. (1) **A CLOSED LOADER IS NOT A PERFORMED MIGRATION.** The company closed the folder-attribution *loader* (`folder_attribution.py` / `.cypher`) on 2026-08-04; the T23 leg is the SF1/F1 edge migration on LIVE state, which is exactly what step 55's `F1/G4-RIDER` note says wipe-and-rebuild does not cover. Do not let "the folder-attribution slice closed" on a board read as the migration being done. (2) That session could not fetch the producer and answered from a cached `cewilson/main @ 5f79d145` — see the fetch-access warning at the top of this file; a T-row read under those conditions is dated by construction. **RIDER 2026-08-06 (PORT-REPORT-a14a8028):** the company extended `PreCutoverApplicationGuard` (S10) to their own 5th `:BusinessApplication` MERGE site, `PatAppLinksLoader` — crash-prevention now covers all five company sites. Prevention only: the S3 graph re-key and C17 orphan-count legs remain owed on the live company graph | pending (producer belief, as of 2026-08-06 — the S3 re-key and C17 orphan-count legs were still open company-side at PORT-REPORT-a14a8028; the SF1 folder-attribution *loader* is closed, its edge migration is not; S10 guard now covers all 5 company MERGE sites) |
| T24 | **TWO REPO-WIDE RENAMES ARE DEFERRED OUT OF THE 20260901 APPLY, AND BOTH RUN BEFORE THE WIPE-RELOAD, NOT AFTER** (new 2026-09-01; the SME ruled B-for-the-slice on both). **(1) THE VOCABULARY MIGRATION** — 44 id renames + 5 fragment renames + folding `41-local-seal` / `42-local-catalog` into `52-local-human`. Producer carries 175 vocabulary ids to the company's 111, and 44 of the 45 rename targets do not exist company-side, so no single rename can be applied in isolation — `u1_has_module` -> `arch_has_module` was attempted and reverted for exactly that reason. The 7 activations flagged as blocked are a SUBSET of this one migration, not separate items. **(2) THE cdo-* RENAME** — 72 producer files at `3c2bfcdd`, deferred beside it after a partial application imported a gate signature; see the gate-state note below. **THE SEQUENCING IS THE RULING AND IT IS COUNTER-INTUITIVE:** deferring reads as "do it at the wipe", and the wipe is precisely when the new vocabulary must ALREADY be in place. Reload under the old vocabulary and you freshly write ~22,956 `seal_has_port` edges and then migrate them; adopt the rename first and the reload writes `business_application_has_port` natively — **`migrate_vocab_ids_g101.cypher` becomes a no-op you never run.** Two producer-side corrections to the company's own measurement, both verified here: **44 of the 45 carry `deprecated_at: 2026-08-21`, not all 45** — the odd one is `seal_requires_scheduler` -> `reg_uses_software`, `deprecated_at: 2026-07-21` at gate C12 (platforms-taxonomy, signed 2026-07-21), and it needs **no data migration at all** because its target `:SchedulerKind` is a retired label whose constraint was removed at C13 on 2026-07-23; folding it into the G101 family sends you looking for nodes that cannot exist. And `migrate_vocab_ids_g101.cypher` landed at `8dc9a804`, an **ancestor of `port-base-20260826`** — the base already applied — so it is out of the CURRENT range but probably already in the company tree; check before pricing it as unsourced. **THE GATE-STATE NOTE, which is why (2) is not merely large:** the producer's `cdo-crosswalk.yaml` reads SIGNED OFF 2026-08-05, 13 confirmations, by name, while the company's twin reads DRAFT with a session pending, and `config/gate-prompts/**` is canonical-company. Taking it would fabricate a company ratification that never happened, in a file class `config/gate-log.md` cites as authority — a dropped field is absent, a fabricated sign-off is present and confident. Any complete workstream still carves that file out by hand. **THE VOCABULARY MIGRATION HAS A CODE DEPENDENCY, NOT ONLY A CONFIG ONE — found by your D+E apply, 2026-09-02, and it changes what item A blocks.** `drydocs_lineage/writer.py` and `drydocs_lineage/extractors/controlm_inventory.py` reference `scheduler_*` / `business_application_*` vocabulary ids EXCLUSIVELY (verified producer-side: 5 and 3 referencing lines, zero old-vocabulary refs in either). None of those ids exist on your side until the migration lands, so taking either file creates dangling vocabulary references. **Those two files structurally cannot port until item A does** — they belong to the deferred workstream, not to any slice. When A was scoped as "44 id renames + 5 fragment renames" that read as a config change; it is also the gate on two lineage modules, and any port that classifies them as fast-forwards before A lands will break. **AND "WIPE" IS TWO DIFFERENT OPERATIONS — SME clarification 2026-09-01, and the difference is how the constraint gap was FOUND.** `MATCH (n) DETACH DELETE n` removes nodes and relationships; it does NOT remove CONSTRAINTS OR INDEXES, which are schema. `DROP DATABASE` removes both. The SME has done both at different times, and it was the run that did NOT drop the database that surfaced the residue — recorded in `internal/research/triage-bootstrap-2026-08-28.md`: *"the constraints already existed at the zero baseline"*, 120 nodes / 18 rels against 60 constraints. G130 then measured it deliberately (producer desktop, `bolt://localhost:7687`, database `drydocs`): 56 live, 56 declared, and **one live-but-undeclared — `membership_id` on `:Membership`, dropped at G99 but still enforcing** — present on this desktop AND on the company instance. **What that means for both renames:** a data-only wipe leaves every constraint standing, so a residue constraint enforces a retired identity rule against the next load and is invisible until it refuses a write; and the T23 S3 re-key survives a data wipe untouched, so wiping does not discharge it. **Run `drydocs bootstrap` and read the live-but-undeclared report BEFORE the reload, whichever wipe you use.** Note also that a wipe is PER-DATABASE: `drydocs` and `ddschema` are separate, and clearing one leaves the other exactly as it was. | **DEFERRED 2026-09-01 by SME ruling; both owed company-side, sequenced BEFORE the wipe-reload.** Producer side is complete and needs nothing |
| T21 | **What are `drydocs/docmeta/connectors/` and `drydocs/scrapers/`?** — ANSWERED 2026-08-02: a company acquisition framework whose agnostic members (web/filedrop connectors + the base protocol) seeded producer Q6; the rest (confluence connector, `scrapers/`) is purely internal. **DISCHARGED 2026-08-04:** Q6 landed `drydocs_docmeta/` producer-AUTHORED against the described shape, never a copy (step 75). Full analysis retired to this file's git history at the 2026-08-05 condensation. | ANSWERED 2026-08-02; back-flow DISCHARGED 2026-08-04 (Q6) |

  Done-means for T1–T10 are unchanged — they live verbatim in the archive's tracker
  section (guardrail 1 has the `git show` path; they are NOT restated here). T9 reminder: producer sign-off never substitutes for load verification on
  your graph. T10: until a real export parses with zero mismatches, treat the
  field names as ASSUMED. **T13 has now had that parse (2026-08-31) and it did NOT come
  back clean** — so the DPL registry field names are no longer merely assumed, they are
  known-contested pending the G64/G65 gate rulings. Treat them as neither confirmed nor
  corrected until those sign.

APPLY BY DISPOSITION — READ THIS BEFORE THE STEP LEDGER BELOW (J69, 2026-09-01)

**A port is not applied chronologically, and this file was organized as though it
were.** The step ledger below is 296 steps of reasoning in commit order; the work is
done by DISPOSITION CLASS, one class at a time. Your own 2026-09-01 apply proved it —
you bucketed the diverged paths into the manifest's classes and worked them class by
class, escalating two rows to per-entry mid-apply, while the ledger sat open as
reference. That is the right shape. This section makes it the file's shape too.

**THE TABLE IS GENERATED, AND THAT IS THE POINT.** Run it against the base you are
applying FROM:

```
PYTHONPATH=. python scripts/render_port_dispositions.py <pre-apply-tag> <base-tag>
```

Two arguments on your side, always: `<pre-apply-tag>` is your own ref for the tree
BEFORE this apply, `<base-tag>` is the producer's `port-base-<date>`. One argument
(`<base-tag>` alone) renders `<base-tag>..HEAD`, which is right on the producer and wrong
on yours — HEAD is your apply branch, so it renders what you have already taken under a
plausible "wrote N paths" line (Idea-250; the two-argument form is `eee64ce3`).

**THE WORKPLAN RULE (PORT1 d, 2026-09-08). A chunk plan that names a script names the
COMMIT the script needs.** Your chunk 1 of 2026-09-01 was told to run this renderer, and
the renderer landed AFTER your base (J69 at `bed22549`); the two-argument form is
`eee64ce3`, the unresolvable-ref refusal is `df7a57c3`, and the one-classifier import is
`6f8c7825`. All four are in `port-base-20260908`; a plan written against an earlier base
names the one it needs and takes that file first, wholesale — `scripts/**` is default_ok,
so nothing else brings it. The second half of the rule is about WHICH MANIFEST does the
classifying: **classify with the manifest AT THE BASE, never with your current one.**
`PORT-MANIFEST.yaml` is canonical-producer, so `git checkout <base-tag> --
PORT-MANIFEST.yaml` is the first wholesale take of class 1 anyway; do it BEFORE you
render, or the table buckets the range by rows the range itself changed (the producer's
519, above, was measured with the manifest at HEAD instead of at the tag — the same
mistake from the other side). Then `git diff <pre-apply-tag> <base-tag> --
PORT-MANIFEST.yaml`: the rows that differ ARE the port's own manifest rows for this range,
and each one is a path class that moved — read them before the table, because they say
where a path you handled last roll is handled differently this roll.

It writes `docs/port/port-dispositions.md` — **gitignored working state, generated
per apply and never committed.** Its range is `<pre-apply-tag>..<base-tag>` on your side
(`<base-tag>..HEAD` on the producer's), so a committed copy would
be stale the moment anyone commits; the RENDERER is what carries guards. The file holds
every changed path in the range, bucketed
by the disposition `PORT-MANIFEST.yaml` resolves for it, with each row's `entry_rule`
attached where one exists. **No disposition is typed into this file by hand.** J68
(2026-09-01) removed four hand-kept disposition assertions from the reconcile-port
skill, two of which had drifted into being wrong — one of them would have flattened
your ontology entries. A generated table cannot drift; a typed one is how that
happened. `PORT-MANIFEST.yaml` owns disposition, here as everywhere.

**THE APPLY ORDER, and why it is not alphabetical.** Wholesale takes first because
they are mechanical and cannot be got wrong; hand-merges in the middle, where the
thinking goes; `derived` LAST, because a render regenerated before its sources land is
a render you throw away.

| # | Class | What you do |
|---|---|---|
| 1 | `canonical-producer` | take wholesale — `git checkout <producer-ref> -- <path>` |
| 2 | `canonical-company` | **NO ACTION by rule** — keep yours, do not even diff |
| 3 | `never-port` | **NO ACTION by rule** — never crosses, in either direction |
| 4 | `per-entry` | **merge by entry** — read the row's `entry_rule` FIRST; this is where a wholesale take drops the other side's rows |
| 5 | `union-append` | append the producer's entries; never reorder, never drop yours |
| 6 | `evaluate` | hand-merge — an un-made decision until a human makes it |
| 7 | DEFAULT | the manifest `default:` — clean-add when absent, evaluate when both sides have it |
| 8 | `default_ok` | the default ON PURPOSE (J16) — the row exists to record that somebody thought about it |
| 9 | `derived` | **regenerate, never carry** (J43) |

**READ THE TRIPLE IN ONE BREATH (J75, 2026-09-08):** when a slice touches a `config/`
path, check its row in `scripts/render_enforcement_matrix.py` SURFACES and
`web/src/generated/enforcement-matrix.json` in the same breath — the three are one
coupling in `PORT-MANIFEST.yaml`, and a slice that carries the surface without its row
makes the derived file unproducible, not stale.

**THE ID CONVENTION'S ROWS (DOC2 / RELAY-48, 2026-09-08):** the freeze, the module
mint and the edition segment are one convention spread over three classes, and a slice
that takes one class without reading the other two mints wrong or refuses forever.
Per-entry, your rows stay: `config/taxonomy/domains.yaml` (rows by `id`; your
`minted_by: company` mints are estate truth), `config/taxonomy/editions.yaml` (rows by
`code`; the producer's rows are `sample: true` and never shadow yours) and
`docs/restructure/backlog/modules.yaml` (`modules[]` unions by name, `series:` unions by
module name; a company-only module's code is yours). Canonical-company, never written
by a port: `config/dev-environment.yaml` — its `edition:` key is the ONE fact the
allocator reads to know whose venue it is running in; absent, it mints no item and says
so. Canonical-producer, take whole: `.claude/skills/groom-backlog/validate.py`,
`drydocs_core/backlog_store.py` and `CLAUDE.md`, whose section 0 mint rule reads
`[<EDITION>-]<MODULE><n>` and "declared in `config/dev-environment.yaml` `edition:`,
never inferred" — the word `base` there is the producer's declaration in the producer's
venue file, not an instruction to yours. Step 160's mirror-assertion action is
withdrawn (RELAY-48 THREE).

**MEASURED AT THIS ROLL** (`port-base-20260826..HEAD`, the full span since your last
applied base): **519 changed paths across 8 classes** — canonical-producer 129,
per-entry 154, default_ok 165, evaluate 29, union-append 16, canonical-company 14,
never-port 8, derived 4. **Do not compare that 519 against your own diverged-path
count and call the gap a discrepancy:** they measure different things by construction.
This counts every path the range TOUCHED; your census counts paths that exist on both
sides and DIFFER. Your 88 and this 519 are both right.
**CORRECTION (2026-09-02, from your chunk-1 census):** 519 was measured `..HEAD` at roll
time, three commits past the tag, against the manifest at that HEAD. Measured **tag..tag**
(`port-base-20260826..port-base-20260901`) with the manifest AT THE TAG the range is
**516 paths** — canonical-producer 130, per-entry 150, default_ok 165, evaluate 29,
union-append 16, canonical-company 14, never-port 8, derived 4 — and your 123 / 150 / 11
is exactly that table with the seven `web/src/generated/**` rows moved to `derived`
(130 − 7 = 123). Your census reconciles to the path; the producer's number was the one
measured at the wrong head. The renderer's head-ref adaptation you made is the fix
(Idea-250) — a range is tag..tag on both sides.
**MEASURED FOR THE RETRY (fifth roll, 2026-09-02; corrected 2026-09-03 from the company's
chunk-1 census)** — the range you apply is now `port-base-20260826..port-base-20260902`,
tag..tag, with the manifest at the new tag: **738 changed paths across 8 classes** —
default_ok 240, per-entry 200, canonical-producer 194, evaluate 34, canonical-company 32,
union-append 17, derived 11, never-port 10. (The roll's own `*-workspace/**` row moves one
path from canonical-producer to never-port; the producer measured before adding it.) The
extension alone (`port-base-20260901..port-base-20260902`) is 286 paths: default_ok 93,
canonical-producer 89, per-entry 56, canonical-company 18, union-append 12, evaluate 9,
derived 6, never-port 3. Measured at the roll commit's parent with the roll's own manifest
rows in place; the roll commit adds no path the range had not already touched.

**MEASURED FOR THE SIXTH ROLL (2026-09-05)** — the range you apply next is
`port-base-20260902..port-base-20260905`, tag..tag, one range with no parked apply behind
it (your `port-base-20260902` apply is COMPLETE at `4d9ddba7`): **323 changed paths across
8 classes** — default_ok 102, canonical-producer 67, canonical-company 67, per-entry 62,
never-port 10, derived 10, union-append 3, evaluate 2. Measured at the roll commit's
parent with the roll's two new rows in place (`tests/unit/test_config_identity_header.py`
and `tests/unit/test_publish_boundary_history_ceiling.py`, per-entry — they move two paths
out of default_ok, and the reason is in RELAY-26). The 67 canonical-company paths are
mostly `config/gate-prompts/**` and `graph-tests/**` touched by the J58 header
normalization (step 327) — NO ACTION by rule; the header block is the same shape on your
files, add it yourself. The 102 default_ok are dominated by `docs/reviews/**` records
(read, never edit), `docs/decisions/`, and `drydocs_lineage/**` + `drydocs_api/**` +
`tests/**` (hand-merge on collision — steps 316, 317, 330). Run
`PYTHONPATH=. python scripts/render_port_dispositions.py port-base-20260902` on your
tree with HEAD at `port-base-20260905` and the table you get is the work plan.

**MEASURED FOR THE SEVENTH ROLL (2026-09-08)** — the range you apply next is
`port-base-20260905..port-base-20260908`, tag..tag, one range with no parked apply behind
it (your `port-base-20260905` apply is reported COMPLETE at `d527afce`, `[SME-REPORTED]`):
**493 changed paths across 8 classes** — canonical-producer 184, per-entry 130, default_ok
127, evaluate 19, derived 10, union-append 9, canonical-company 7, never-port 7. Measured at
the roll commit's parent; the roll adds NO manifest row, because the table needed none —
every path resolved to a row or to an intentional default, and the one known collision
(`scripts/reconcile_before.py`, two shapes, RELAY-39) sits under `scripts/**` default_ok
where hand-merge is the rule. The 184 canonical-producer paths are 151 `web/**` (take whole,
regenerate `web/src/generated/**`), 7 `.claude/**` (three research-probe-discipline eval
files, the `reconcile-port`, `run-drydocs-console` and `controlm-db` skill files, and
`.claude/skills/groom-backlog/validate.py`), 8 `config/**`, 4 `deploy/**`, three
non-JSON files under `knowledge/depgraph-snapshots/**`, two under `drydocs/loaders/**`, and
one each of `PORT-MANIFEST.yaml`, `CLAUDE.md`, `.dockerignore`,
`docs/restructure/backlog/README.md`, `drydocs/cli_schema.py`, `drydocs_core/schema/**`,
`drydocs_remediation/**`, `internal/remediation/**` and `tests/unit/test_port_manifest.py`.
The 130 per-entry are 117 `docs/restructure/backlog/items/*.yaml` plus `MODULE_MAP.md`,
`config/source-registry.yaml`, `config/source-bindings.yaml`,
`config/taxonomy/ui-components.yaml`, `docs/restructure/roadmap.yaml`,
`drydocs_core/component_map.py`, `drydocs_core/schema/constraints.cypher`, `pyproject.toml`,
`scripts/render_enforcement_matrix.py` and four tests — union by key, your rows stay. The 127
default_ok are `tests/**` 58, `agents/**` 20, `drydocs_api/**` 16, `scripts/**` 8,
`drydocs_core/**` 7, `drydocs/**` 6, `docs/decisions/**` 5, `docs/reviews/**` 3 (read, never
edit), `internal/**` 2, `.env.example`, `.gitattributes` — hand-merge on collision. The 19
evaluate are 17 `docs/design/**` sources and renders, `.github/workflows/ci.yml` and
`tests/unit/test_controlm_cypher.py`. The 9 union-append are `config/gate-log.md`,
`docs/restructure/IDEAS.md` and seven epic files. The 7 canonical-company are `compose.yaml`,
`config/dev-environment.yaml` and five `config/gate-prompts/**` — NO ACTION by rule; the
producer's edits to unsigned prompts are dated PROPOSED clauses you accept or not. Run
`PYTHONPATH=. python scripts/render_port_dispositions.py port-base-20260905` on your tree
with HEAD at `port-base-20260908` and the table you get is the work plan; run
`scripts/port_completeness_check.py port-base-20260908 --prev port-base-20260905` when you
think you are done, and the clean-add class closes on a measurement for the first time.

**THE STEP LEDGER IS NOT REPLACED BY THIS AND IS NOT SUMMARIZED BY IT.** It stays
below, entire, and it is where the reasoning lives — why a change was made, what it
cost, what it did NOT authorize. The disposition table tells you the ORDER and the
RULE; the ledger tells you the MEANING, and a step is the thing you read when a
per-entry merge needs a judgment call. Steps are cited from the classes, never folded
into them.

DEFERRED BY PATH (new 2026-09-08, PORT6 — the roll's deferral record, machine-readable).
A roll closes COMPLETE on the collision classes and never on the clean-add class: a path
present at the base tag and absent from your tree has no diff to bucket and no `--numstat`
line to attribute, so a forgotten path and a deferred one print the same empty output.
Two rolls closed COMPLETE that way (2026-09-01 and 2026-09-05) and the paths surfaced as
carve-outs afterwards. The rule from RELAY-35 — a roll closed COMPLETE carries its
deferrals BY PATH — now has a place to carry them:

```deferred-paths
# pattern | roll deferred at | ref (T-row, relay or report) | retired (date, or - while active)
drydocs_lineage/** | port-base-20260901 | T24 | -
```

Rules for the block. One row per path or glob, in the manifest's glob grammar (`**`
spans separators, `*` does not). The list is CUMULATIVE across rolls: a path deferred at
roll N stays deferred at roll N+1 until it is applied or its row is RETIRED — never
deleted — by writing the date in the last cell, so the record of what was deferred and
for how long survives. T24 is the prose form of exactly one entry and is the first row;
a new deferral gets a row here AND its reasoning in a T-row or relay, the way T24 has
both. This block is what `scripts/port_completeness_check.py` reads (it reads this file
AT THE BASE TAG, `git show <base-tag>:docs/port/port-prompt.md`, because `docs/port/**`
never crosses and you have no working-tree copy); deferrals only you have ruled go in a
file of your own, same fence, passed with `--deferrals FILE`. Retiring a row is a
producer edit unless the deferral was yours.

---

STEP LEDGER — delta since `caa0406` (steps 43–123 collapsed above; 124–134 are the
`ae21ee4..caa0406` range, DELIVERED and producer-reviewed but with an unconfirmed
close-out, kept live for exactly that reason). Steps 135+ are the NEW delta this
base certifies. Each sub-stream carries its producer-side verification status in
[BRACKETS]; spend review on [UNRULED]. Grooms, claims, board/design renders and
depgraph snapshots in the range are ritual — per-entry backlog union, derived
regeneration, never-port outputs — and get no step. **Steps 273–296 are the
2026-09-01 (fourth) roll**, covering `port-base-20260829..port-base-20260901`;
steps 241–272 remain live below them because that base was certified and never
applied, so the two rolls are one range for the consumer. **Steps 297–312 are the 2026-09-02 (fifth) roll**, covering `port-base-20260901..port-base-20260902`, rolled BEFORE the company's retry so that the retry applies ONE range, `port-base-20260826..port-base-20260902`, with all seven live relays inside it and nothing hand-carried (RELAY-24; the 20260901 apply is parked unmerged). **Steps 313–333 are the 2026-09-05 (sixth) roll**, covering `port-base-20260902..port-base-20260905` — 186 commits at the tag, 132 cited, the first roll since 2026-08-26 to start from a range the company had already applied COMPLETE (its `4d9ddba7`), so nothing is parked and nothing is hand-carried; RELAY-26 is its one relay. **Steps 334–353 are the 2026-09-08 (seventh) roll**, covering `port-base-20260905..port-base-20260908` — 407 commits at the tag, 303 cited, one range again because the company reported the 0905 apply COMPLETE at its `d527afce` (`[SME-REPORTED]`); the nineteen relays written during that apply (27–45) all act in this range, RELAY-46 says where each lands, and it is the roll's one new relay. **Steps 368-386 are the 2026-09-10 (ninth) roll**, covering `port-base-20260909..port-base-20260910` - 141 commits at the roll, 105 cited, and the range in which the build lane's twenty-six branches merged. RELAY-55, RELAY-56 and RELAY-57 all act in it, and RELAY-57 is why it went out when it did: three of its twenty-one pairs had not shipped yet, and this roll carries both halves of each. **Steps 387-388 are the 2026-09-10 (tenth) roll**, a same-day re-roll cut before the consumer began applying the ninth, covering `port-base-20260910..port-base-20260910b`: it repairs a Neo4j route that loads in no venue without a plugin loader, which the consumer had already had to fix on their own side, on paths a port would have reverted.

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
    company-side with its branch removed — `docs/port/port-prompt.md` only. Nothing to
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

135. PORT MACHINERY — THREE GUARDS, A DOC, AND A MANIFEST ROW [TEST-PINNED]
    (`3bb5982`+`fac3d12`, `928eca7`, `77f2ff8`, `3af009b`+`ce7857e`, `02e7896`).
    `928eca7` is the one to take first: it asks J16's MIRROR question — which
    manifest rows match NO path — and the unmatched row is the more dangerous half,
    because it fails silently in the RIGHT-LOOKING direction. Its paths do not go
    ungoverned; they fall through to whatever broader row catches them next, usually
    generic `evaluate`, so a canonical-producer or never-port intent quietly degrades
    to hand-merge with no error anywhere. That is exactly what happened to
    `drydocs_core/controlm/**` for months (step 133). Run it against YOUR manifest
    before Phase C, not after. `77f2ff8` adds the seventh preflight check — backticked
    repo-relative paths in a NEWLY ADDED doc must resolve — and `3bb5982` makes a
    stale `RECONCILE_BEFORE_DIR` fail by name instead of four FileNotFoundError
    tracebacks that read as broken guards. `ce7857e` corrects the XML-test port doc:
    it over-claimed canonical-producer, and only `xml_vocab.py` + `drydocs_remediation/**`
    actually are — the rest fall to family `evaluate` defaults where a blind path
    checkout is forbidden. Diff-first there.

136. THE `caa0406` PORT REVIEW — RELAYS 7, 8 AND 9 [VERIFIED-PRODUCER]
    (`ca7a121`, `9bee368`+`f015c7e`, `b5c03f1`, `2d60e5d`). All four are ABOUT YOUR
    SIDE and cost you rework if skipped. RELAY-7: your `email-dl-contact-point` §G4
    asks a question already answered — `5405ab6` removed `<DOMAIL>` with the shouts,
    so the option that clause weighs no longer exists. Re-pose §G4; do NOT change the
    canonical-company disposition, which was right. RELAY-8: the `pat` stub you hit
    is a T23 re-key RESIDUE, not a load-order problem — reordering the load makes the
    symptom go away and leaves the defect, because producer-side `pat_product_mapping.cypher`
    MERGEs on the same neutral `app_id` key `seal_applications.cypher` uses, so no
    stub can exist here at all. `f015c7e` strikes a company memory note that is
    factually wrong. RELAY-9: the PAT alignment column is **`Relationship Type`**;
    `Team Type Name` is a DECOY that matches `team_type` by name and carries the
    team's discipline instead — column-name similarity picks the wrong one every
    time. `2d60e5d` splits G59's lumped pair: `resource_pools_supplement` is LIVE and
    company-only (must be in your chain or in CHAIN_EXCLUSIONS with a reason);
    `platforms_supplement` is RETIRED (T12 supersede) and belongs in CHAIN_EXCLUSIONS.

137. THE REMEDIATION xml_io EPIC — THE LARGEST BLOCK IN THIS RANGE [TEST-PINNED]
    (`ad081e6` step 0 re-home, `0a4b0a3`, `e533fc2`, `3ebb66d`, `d40c9cb`, `be6b8f5`,
    `bf37f49`, `339572e`, merge `6bf66fe`, then `3b9038b` DATA_CENTER). A lossless
    byte-splicing Control-M XML reader with identity round-trip proven on a 10-fixture
    hostile corpus, an EditScript with a three-layer self-check, and approved
    change-set compilation with gate-bound fix tracking. TWO DEFECTS WERE FOUND AND
    CLOSED INSIDE THE EPIC, and they are the part worth reading: A′, dangling rename
    references (fixed by a reference sweep plus four whole-document post-conditions,
    guard verified RED first), and B′, no-evidence-treated-as-proof (fixed by giving
    `prove_equivalence` a THREE-VALUED verdict — equivalent / not-equivalent / cannot
    tell — instead of letting silence read as pass). SEPARATION OF DUTIES IS
    STRUCTURAL: C1 EMITS a change-set, a write-authorized loader APPLIES it; nothing
    in xml_io writes a graph. `3b9038b` carries DATA_CENTER through model, locator and
    anchors — the other half of a folder's identity, and a locator without it is
    ambiguous across data centers. `drydocs_remediation/**` is canonical-producer.

138. VOCABULARY RATIFICATION — TWO GATES SIGNED THE SAME DAY [GATE-AUTHORIZED]
    (`b6b1423` draft, `26d7c39` sign-off 19/19 + 10/10, `496aa26` §A/§B, `35a1d2b`
    §D2, `34a6dc0` fix-tracking consequences, merge `2daf8ba`). Guardrail 7 applies:
    producer sign-off is not company sign-off, and your side runs its own gate. What
    landed producer-side: the `scheduler` / `business_application` domain renames, the
    `human` domain registered, an ID POLICY ruled (§B1), vocabulary hygiene at §D2,
    and the fix-tracking artifact moved to RATIFIED. G87-G91 groomed as follow-ups.
    IF YOU ADOPT THE DOMAIN RENAMES, adopt the id policy in the SAME change — the ids
    encode the domain, so taking one without the other mints ids that no longer match
    their fragment. `config/gate-log.md` is per-entry union as always.

139. THE `DD1|` SENTINEL — Idea-105 EXITS ON A FOURTH OPTION [TEST-PINNED]
    (`92d9296` the ruling + C34/G77, `3c4ef5d` G83+G84, `79020a7` format, `203d7bd`
    the backlog close).
    The 4000-char DESCRIPTION field had two claimants and three recorded exits, all
    bad. The resolution PARTITIONS the field instead of choosing: a description
    beginning `DD1|` is authored to the token standard; one that does not is the
    generator's literal or legacy filler. E1 keeps its exact match UNCHANGED, the
    parser never sees a generated object, and NOTHING ALREADY DEPLOYED MIGRATES.
    It also retires the proposed GENERATED_BY token — absence of the tag already IS
    the provenance signal. G83 then carries the C30 ruling into TOKEN_REGISTRY, which
    still encoded the C29 capture and returned SEVEN FALSE FINDINGS on a conformant
    description. Retired tokens are retired IN PLACE with the ruling named, never
    deleted: the estate still carries them, and deleting an entry would reclassify
    real data as a C16 annotation. Completeness is ERA-AWARE — an untagged legacy
    description is held only to the C29 set it was authored to.

140. G60 — PRECMD/POSTCMD FEED THE SAME G14 FILE-OP GRAMMAR AS CMD_LINE [TEST-PINNED]
    (`91bbf7b`, close `85c9bfa`). The extractor's file-op pass read `CMD_LINE` only, while
    the EMBEDDED_SHELL variables — PRECMD / POSTCMD, including the observed `POSCMD`
    typo — carry the same shell text, and production uses them for exactly the
    mv/backup forms the pass could not see. Same core parser, same endpoints, NO new
    relationship types, and pre/post invocations deliberately NOT emitted: file-op
    candidates only, inside G14's signed endpoints. Coverage keeps the two sources
    apart (`prepost_*` counters) so the added yield is measurable, and unmatched jobs,
    empty values and unparseable values are counted rather than dropped.

141. G96 — THE CONTROL-M API-CALL FRAMEWORK [TEST-PINNED] (`4c0fc87`, backlog
    `46f1466`/`9093e0b`/`bb9788b`). `drydocs_core/adapters/controlm` is the per-object
    call surface YOUR deploy/pull `.sh` wrappers invoke: folder/job/variable/calendar
    ops plus the in/out-condition seam, config-resolved in/out dirs off the data root.
    THE SPLIT IS DELIBERATE AND IT IS YOURS TO COMPLETE — producer owns the framework,
    the `.sh` and the filled config are company-side. Call shapes are CONFIG TEMPLATES
    wherever the corpus lacks verified syntax, and the 9.0.21.300 availability
    guardrail makes a templateless or no-corpus call **exit 3 as a REPORTED capability
    gap** rather than fall back silently. Sample cfg is mechanism-only; a filled cfg
    is never committed. 15 new tests.

142. THE DATA-CATALOG STREAM — G43 REPORTS, G44 GATE PROMPT, THE `:Port` EDGE
    [UNRULED] (`f4afd43` G43, `e7554f9`+`273eb87` G44, `7a59230`+`c3de648` the edge).
    G43's four cross-check reports (`catalog_crosscheck.py`) are ALL READ-ONLY — no
    graph writes, no edges — and share one shape worth copying: a row that cannot
    participate in the join is held OUT of the set arithmetic and given its own
    counted list, never folded into either side. Folding reports gaps that do not
    exist; dropping hides real defects. G44 drafts the catalog ontology gate (7
    sections, 24 confirmations) and renders OPEN, which is correct for an unsigned
    page — clause A (one node or two: `DataAsset` vs `:Dataset`+`:Distribution`) is
    written so neither reading wins silently, because every other clause inherits it.
    `273eb87` is a self-catch: the first pass PRE-DECIDED a ruling signed nine days
    earlier. The `:Port`→`:DistributionList` HAS_CONTACT_POINT edge is registered
    `status: planned` and NOTHING LOADS FROM IT; the node class ships with the edge
    deliberately, since declaring an edge whose label is unclassified is the exact gap
    closed for ControlMApplication on 2026-07-09.

143. G32 REOPENS DOWNWARD, AND THE FID JOIN IS THE NAME [UNRULED / VERIFIED-PRODUCER]
    (`4d61395`, `0b67338` G32 §F, `c326584` K17, `77f53a9` Q6). The database COUNT
    reopened downward to ONE on RETRIEVAL grounds — an agent that cannot see captured
    context beside the structured graph in one vector search may not be able to answer
    the question. That is NOT the argument ADR 0002 D1 weighed, and NOT the trigger
    ADR 0011 was written for (0011 plans the fold for Enterprise becoming unavailable,
    not for choosing it), so Q10 says amend 0011 with the real rationale rather than
    let the record claim a trigger that never fired. §F rules the two trust axes.
    THE FID HALF IS THE ACTIONABLE ONE: the join is `UPPER(EMP_LAST_NAME) =
    UPPER(OWNER)` — the NAME on both sides, case-insensitive. `EMP_ID` is what the
    crosswalk RESOLVES TO, never the join key, and the FID directory is a psgmgr
    TABLE, not an external system. The ledger was the outlier: gate `rua-load-shapes`
    A1 had already ruled run_as carries the linux tenant name while
    `config/source-mappings/psgmgr.yaml` went on calling OWNER a "Functional ID" —
    two records, one repo, opposite claims. Corrected here.

144. G16 AMENDED, G35 RESIDUALS CLOSED, AND THE ROLE CATALOG EXPORTED
    [GATE-AUTHORIZED] (`770d1cc`, `f71bfb6`, `2f9da55`, `7c96a31`). G16 moves REQUIRED
    → **OPTIONAL and DERIVED** for SRE, and the reason is structural rather than a
    preference: THE CARDINALITY IS INVERTED from every other line in the register.
    Each of the others is a per-application holding; an SRE team covers 20-60
    APPLICATIONS. It is a shared function pointing at many apps, not an accountability
    held by one, so section B's required/optional split does not apply cleanly. The
    original ruling stays readable and the amendment states what changed — no other
    register line moves. `f71bfb6` closes the G35 residuals (G16 stands as amended,
    G5 closed, revisit trigger recorded). The catalog export is 83 rows, NOT the
    "100+" the sign-off carried from an estimate, and it names which roles come from
    SEAL in its own description text. `2f9da55` corrects a producer belief: the naming
    convention IS parsed company-side; the SRE branch is the part that is missing.

145. THE LOAD-SURFACE RENAME — ADR 0012 AND THE `generic-naming` EPIC [UNRULED]
    (`5bd0ab6` G78-G80 + GN1/GN2, `68c8204` ADR 0012, `c7ee73c` narrows G78).
    READ THIS BEFORE IT REACHES CODE, because the verbs are a PUBLIC CONTRACT your
    crons and the `run-drydocs` skill call ACROSS THE REPO BOUNDARY — a rename lands
    on you as breakage, not as a refactor. The motivation is the SME's: company jargon
    (`seal`, `pat`, `m1`/`m3`) entered a repo meant to be generic from the start, which
    is the standalone-generalization goal rather than cosmetics. The model separates
    three axes collapsed into one `LoadStep` today — the command names the SUBJECT,
    the registry entry carries CADENCE and ACQUISITION, and a profile is DERIVED by
    filtering cadence. Three bands (prepare / load / verify) and only `load` is
    source-keyed. `m1-verify`/`m3-verify` rename with the rest, not exempted for being
    internal. Nothing is renamed yet — GN1 is the ADR, GN2 the execution.

146. THE PAT `team_type` COLUMN PIN — AND A REVERT WORTH READING [VERIFIED-PRODUCER]
    (`f6b4285`, `58b8d3c` revert, `2f33e5c` the pin). The pin is RELAY-9's other half:
    the source column behind `team_type` is `Relationship Type`. The revert is the
    instructive part. A folder-name pattern was scrubbed from a header as a suspected
    publish-boundary leak; the SME ruled `PRARAG-HLDM` an AUTHORED FIXTURE NAME, so
    the scrub was unnecessary and the ~36-file sweep was never run. It was REVERTED
    rather than left in place because the half-applied state — a placeholder in the
    prose while `config/taxonomy/controlm.yaml` carried the literal two directories
    away — is worse than either end state: it reads as though someone found a leak and
    fixed one instance. Applies to your side too if you carry fixture families.

147. TWO BACKLOG RULINGS THAT CONTRADICT LIVE LOADERS — G74, G82 [UNRULED]
    (`417cb4e`, `c7278a5`). G74 gains the `:Employee` CREATION-POLICY clause because
    the runbook forbids exactly what the loader does: "spine-and-enrich" says
    `:Employee` is created ONLY by `load-employee-roster`, with SEAL attaching
    enrich-only via OPTIONAL MATCH — "a SID not in the roster gets no edge, never a
    stub" — while `seal_applications.cypher` MERGEs `:Employee` placeholders for the
    owner, CTO and info-owner SIDs. Both surfaces are published; one of them is wrong,
    and the gate decides which. G82 records that THE LOADER IS NOT THE INCOMPLETE
    PART: `DevTeamsLoader` and `PatProductMappingLoader` both exist, wired, registered
    and sample-tested — the missing piece is the PAT team-report PROJECTION, so the
    dev-team load has never run on real data. Check whether that is also true your side.

148. J13 DONE — THE PUBLISH CEILING'S FOUR VALUE CLASSES RULED [TEST-PINNED]
    (`18d4eb5`). SME ruling: position 1 of a Control-M data-center name is the
    ENVIRONMENT letter, so the publishable tree now carries a non-production letter —
    no published example names a live production object, while the grammar the
    standards page exists to teach is untouched. Swept across 19 tracked files outside
    `internal/`; real values moved to `internal/standards/technology/data-center-inventory.md`.
    THE FINDING THAT MATTERS: A FIFTH DATA CENTER WAS FOUND BY THE NEW GUARD, NOT BY
    THE SWEEP — J13 named four, the standards page inventoried four, and a `P045` sat
    in a test fixture and the web demo data. A token-list sweep could not have caught
    it; only the SHAPE scan did. Third instance of the J15 lesson: enumerate the
    SHAPE, never the values. Scan E in `test_publish_boundary_values.py` enforces it.

149. THE `--run-as` BIND-VALUE FIX — A SILENT ZERO-ROW ANSWER [TEST-PINNED]
    (`887a0e7`). `CM_DEF_VJOB.OWNER` is stored ALL UPPER in psgmgr while the
    directory's `EMP_LAST_NAME` is mixed case. Three SQL files bind `J.OWNER =
    :run_as` as an exact match, so a lower-case `--run-as` returned ZERO ROWS and read
    as "that account runs no jobs" — a silent wrong answer, not an error. THE FIX GOES
    ON THE BIND VALUE, NOT THE COLUMN: `_scope_binds()` upper-cases `run_as` and the
    column stays bare on purpose, because it is already upper at rest and `UPPER(J.OWNER)`
    would be a no-op costing the b-tree index on a ~240k-row table. `None` survives as
    `None` — `"".upper()` would turn a missing filter into an empty-string match.

150. THE WORKTREE RENDER LEAK + THE J48 ANCHOR SWEEP [TEST-PINNED] (`ced651f`,
    `841dc6e`, `f9ef847`, `dd8d843` the close — worktrees and branches pruned under
    a user ruling). `drydocs` is installed editable with a `.pth` pinned at the
    MAIN tree, so a module anchoring default paths on `Path(__file__)` names the main
    tree from anywhere — a render run inside a worktree wrote into main. What made it
    silent is that the damage was PARTIAL: `render_board.py` invokes five sibling
    scripts by bare name and those resolved correctly out of the worktree, so only
    three HTML files routed wrong. J48 then swept all 27 repo-root anchors and RULED
    each one: 24 now resolve through `drydocs_core.repo_paths.repo_root()`, and the 3
    left as written are recorded AT THE SITE, because skipping a site is not a
    disposition. Relevant to you if you run agents in worktrees or forks.

151. LINE ENDINGS — THE RENDERERS WROTE CRLF AND BURIED THE STALE-RENDER SIGNAL
    [TEST-PINNED] (`7d885c9` the raise, `fcc8afa` .editorconfig, `b348b0c`
    .gitattributes, `ffca823`, `d0b2a93` the fix). All 11 `write_text(` sites producing a COMMITTED render
    surface now pass `newline="\n"`. WHY IT IS NOT COSMETIC: Python text mode emits
    `\r\n` on Windows, so every render rewrote its output as CRLF while the index held
    LF, and git normalized it straight back on commit — no blob ever changed, so
    nothing flagged it. The cost landed in the two places that read worktree state.
    The session ritual's stale-render check reported **25 changed files when 0 had
    changed**, and `snapshot.ps1` renders BEFORE it scans, so a snapshot recorded
    `meta.git.dirty: true` against a clean tree — the field that answers "does this
    header describe the code that was measured?" answering wrongly. Verified by
    re-rendering everything and getting a clean tree: 25 → 0. If your renders run on
    Windows, you have this defect too; the `.editorconfig`/`.gitattributes` pair is
    accumulate-and-union in the manifest (`02e7896`), not a wholesale take.

152. LINT TO ZERO, AND CI CHECKED BEFORE THE SNAPSHOT [TEST-PINNED] (`b7064bf`
    RUF100, `929b5d3` I001, `0a52b6d`, `c981964`, `d9b2b31`). Both CI ruff gates exit 0 for the first time since
    2026-08-05 — **100+ consecutive failing runs**, on exactly those two steps, while
    everything else stayed green and the unit suite passed the whole time, so nothing
    LOCAL ever looked wrong. 35 findings and 31 unformatted files to zero, FIXED not
    ignored (including six N818 exception renames across 54 references, each verified
    standalone first). `d9b2b31` is the process half: the session ritual now checks CI
    on HEAD's own sha before the snapshot runs, warn-only, because the failure being
    fixed is nobody LOOKING. Worth adopting whatever your lint posture is — the
    mechanism is "green at what you just pushed", not "green at somebody's older commit".

153. `MODULE_MAP.md` NAMED AS THE PHYSICAL PLACEMENT AUTHORITY [docs] (`5c7cb88`).
    CLAUDE.md routed file placement by the four conceptual layers and never mentioned
    the physical map, so agents answered "where does this file go" from the wrong
    document. One-paragraph fix, but it is the routing brain — if your CLAUDE.md
    forked from this one before 08-12, it likely carries the same gap.

154. DOCS, GATE RECORDS AND WIP SURFACES [default_ok] (`d9a2eac`+`429d829`+`e774127`+
    `b268cd3` the Claude Design UI prompt, `63050fa` the swimlane wireframe,
    `14a702e` the rua copy-path contract, `317261c` docmeta P4 revision, `70bdef4`
    G62 RECORD). Take or skip freely; none of it binds. Two are worth a look. The UI
    prompt was RECLASSIFIED as a dated record rather than edited, because a doc branch
    idle since 07-21 merged textually clean while still listing two brand marks main
    had deleted as rejected — that near-miss is what motivated the `77f2ff8` preflight
    check in step 135. `14a702e` is comment-only but closes a real gap: the rua
    mirror-layout contract existed as a single derived expression with nothing at the
    other end pointing back, so each half now names the other and says a layout change
    breaks G21/G24. G62 §A opened and identified bundle 1; §B runs COMPANY-SIDE.

155. THE GITNEXUS EVALUATION — VERDICT: DO NOT ADOPT [default_ok] (`dc0bdb0`,
    `be64c85`, `9e83379`). An `/architecture` comparison of GitNexus against the
    depgraph sibling + snapshot ritual, then an actual producer-side TRIAL. Honest
    framing: different tools sharing a noun — symbol-grain agent dev-tooling vs
    file-grain drift plus Control-M-seeded lineage under offline/stdlib constraints.
    THE DECISIVE FINDING is a governance lesson, not a tooling one: its method-grain
    impact claimed **epistemic `exact`** with `impactedCount=1` while missing
    receiver-annotated production call sites that plain grep finds. The concept worth
    keeping is the opposite of the verdict — label answers `exact` vs `lower-bound`,
    and make our own census honest where that one was not (Idea-124, unaffected by the
    rejection). Non-adoptions recorded explicitly: LadybugDB, community mining,
    symbol-grain estate parsing.

156. THE ROADMAP-ROW RETIREMENT — AND A DUPLICATE-COMMIT NOTE [TEST-PINNED]
    (`63551c8`). `test_real_roadmap_cites_only_live_inbox_ideas` was RED on producer
    `main` from 08-14 to 08-17: Idea-23 and Idea-47 had been groomed into backlog
    items, so their `roadmap.yaml` estimate rows no longer pointed at a live inbox
    entry. Rows retired, `roadmap.html` re-rendered, CI green at this sha. ONE THING
    TO KNOW IF YOU CUT A RANGE THAT SPANS IT: an IDENTICAL fix was committed
    independently on the producer's other machine and is still unpushed at this
    writing, so a later producer push may add a duplicate/empty commit making the same
    two deletions. It is benign — same bytes, merges clean or drops as empty — but do
    not read it as a second change.

157. IDEA-INBOX COMMITS — NOTHING TO APPLY, TWO THINGS TO KNOW [default_ok]
    (`cae542d` Idea-117..120, `4676a53` Idea-112/113/114, `9718f04` Idea-115,
    `4e99b87` Idea-117/118 UI examples, `6cdf3c8` a depgraph snapshot). These are
    `IDEAS.md` inbox appends and one snapshot, and they are HERE ONLY BECAUSE THE
    RITUAL EXEMPTION IS DELIBERATELY NARROW — it matches `chore(backlog): groom|claim`,
    `chore(depgraph): snapshot`, `chore(render|board):` and the roll itself, on the
    SUBJECT, so a substantive commit can never hide behind a prefix. `chore(ideas):`
    is not on that list and `6cdf3c8` used `chore(snapshot):` rather than the matched
    `chore(depgraph): snapshot`, so all five surfaced as uncited. Saying so is cheaper
    than leaving you to check. TWO ARE WORTH READING even though nothing ships:
    Idea-117..120 came out of a tech-debt audit and include **two graph-instrument
    bugs**, and Idea-112 records that `%%var` resolution has to happen BEFORE the G14
    parse — a sequencing constraint, not a wish. The SME-supplied UI examples in
    `4e99b87` are references only; their images and transcriptions are machine-local
    and deliberately never tracked.

158. THE CONTENT-TOPOLOGY FOLD — ONE CONTENT DATABASE [GATE-AUTHORIZED, and the
    biggest structural change in this range] (`30f18c1e` G32 SIGNED 32/32,
    `0316fca6` G102(a) the three ADR 0011 clause-1 guards, `988bf0d6` G102(b-d)
    the fold itself, `4763e63e` G102 verified live, `8d596c37` G31 the D1
    business-key spine re-scoped for one database, `ad2b52fe` Q20
    satisfied-by-fold, `50ed3589` G38 closed satisfied-by-fold — the ddall
    retirement swept and locked). The document-content topology FOLDS TO ONE
    DATABASE: the watermark is re-keyed on trust, and the federated ddall read
    path is retired with its name locked in SUPERSEDED_NAMES (which database is
    the one is the gate page's ruling — read it there, not here). The gate prompt
    (`document-content-topology.yaml`, 45KB) and ADR 0011 carry the reasoning.
    YOUR SIDE: the code and guards port wholesale; whether YOUR graph folds is
    your own Tier-A review against the signed gate — the clause-1 guards land
    first either way and refuse the mixed state. G31's spine guard and Q20's
    trace close ride the same review.

159. THE Z-SERIES — SERVER INVENTORY, LOCATION ONTOLOGY, THE TIERED
    ExecutionHost JOIN [GATE-AUTHORIZED + TEST-PINNED] (`3f2a647d` Z1 the
    infrastructure server export registered + hierarchy captured + fixture
    guarded, `7ff11d14` Z2 gate prompt + three planned vocabulary entries,
    `f93939ed` Z2 SIGNED 12/12 — C2 reshaped to the technology port, `a30dd952`
    Z3 the server-inventory loader + tiered ExecutionHost join, e2e green and
    idempotent). A new registry source (the server export), a signed
    server/location ontology, and a loader that joins Control-M hosts to a
    tiered ExecutionHost. Loader + vocabulary port; your server export and its
    confirmed flip are yours.

160. THE ID-SPACE PARTITION — PRODUCER 1-9999, COMPANY 10000+ [TEST-PINNED /
    **ACTION-REQUIRED, and it is YOUR half that completes it**] (`02f55975` the
    bands + the Idea-59 -> Idea-135 renumber, `8fc1fef0` merge; RELAY-11 RIDER 2
    is the companion read). Every id series (Idea-, every backlog letter) is now
    range-partitioned by allocator: producer mints 1-9999, company 10000+ —
    five digits or more reads as yours at a glance. Producer-side guards assert
    `<= 9999` in `test_plan_ideas.py` + `test_backlog.py`; BOTH band blocks are
    `per-entry` in PORT-MANIFEST (rows added in this range) and MUST NOT port
    wholesale — taking them as-is would declare your own ids illegal. **YOUR
    ACTION: write the MIRROR assertion (`n >= 10000`, grandfathering your
    existing low ids as a committed constant) and allocate new ids at 10000+.**
    Until that lands the partition is one-sided and the next Idea-59-class
    collision is a matter of time. The one live collision was settled by the
    G75/G76 precedent — producer's uncited side moved (Idea-135); YOUR Idea-59
    stays.

161. MANUAL LANDING ZONES FIRST-CLASS [TEST-PINNED / ACTION-REQUIRED]
    (`fabb1e4e` the build, `09e7a609` the wipe-signature correction). Every
    `acquisition.mode: manual` registry row now declares `drop_dir_base`
    (data_root|repo); `drydocs_core/landing_zones.py` resolves them,
    `drydocs landing-zones [--check]` inspects them (exit 2 on a data_root zone
    inside the tree, exit 1 with --check on EMPTY), and
    `test_landing_zones.py` enforces that repo-based zones hold TRACKED files.
    The correction commit matters as much as the build: a `git clean -fd`
    removes the DIRECTORY, so a swept zone reads `absent` (indistinguishable
    from never-used), NOT `EMPTY` — detection is the weak half, LOCATION is the
    control. **YOUR ACTION: set your own `DRYDOCS_DATA_ROOT`, and run
    `drydocs landing-zones --check` before AND after any port step that touches
    the working tree** (the guardrail bullet above was extended in this range).

162. FIVE GATES SIGNED IN-RANGE [GATE-AUTHORIZED] — adopt via your own gate-log
    review, per gate:
    (a) `corporate-backbone-vocabulary` 19/19 (`9d9208d6` draft, `3e208524`
        walk, `0622a655` backbone-not-spine rename, `faa0bdd8` consequences:
        :Company registered org:FormalOrganization, new 49-local-corporate.yaml,
        the §D3 endpoint guard — which found 8 unregistered endpoint labels,
        carried as DECLARED DEBT, not fixed silently; `1099d68d` the missing
        `corporate` domain registration CI caught; `1e29ba63`+`1cdfe277` the
        08-17 schema matrix made durable + its regenerator).
    (b) `pending-source-correction` 12/12 (`a10b0191` N12 — every registry
        dataset declares its ACQUISITION PATH, `0ce3b38a` N13 draft, `2b1430aa`
        signed; the confirmed-flip rule is now gated).
    (c) `email-folder-assignment` 8/8 (`dfdda0d1`) — the CONCERNS edge RULED,
        NOTHING WRITTEN: `docs_email_concerns` stays planned until its writer
        builds; aboutness is never attribution (the K7 §A1 fence held).
    (d) B5 medallion-stage vocabulary 6/6 (`dd7663e3`).
    (e) Z2 server/location 12/12 — step 159.

163. THE HELD-ENTRIES REVIEW AND THE ATTRIBUTION FAMILY [GATE-AUTHORIZED]
    (`4b731b91` G91 four of five held entries ruled + the m3_ ids retired,
    `38013e45` G91 closed 5/5 — the DevTeam leg joins qualified attribution,
    `fdfb419a` the claim commit shipped with its own guard red and was fixed —
    the claim-before-work rule catching a bad claim, `b17f24e5` the ITSM
    technician-group family lands fourth on the qualified-attribution pattern,
    `b0cfa37d` G99 pat_team_roles rewritten onto qualified attribution).
    NAMING NOTE for your vocab merge: `m3_executed_by` is DEPRECATED (id
    migration, concept held) — the live entries are `scheduler_executed_by`
    (run-grain, planned, double-blocked) and `scheduler_runs_as`
    (definition-grain, planned, NEW in this range — CM_DEF_VJOB.OWNER had no
    registered edge at all until G91's review caught it). Both fence on the
    fid-identity gate (the reserved step below).

164. S11 — THREE COMPONENT PACKAGES EXTRACTED [TEST-PINNED, path moves]
    (`97fb4f02`, merged `2ea4ecd9`). `drydocs_plan/`, `drydocs_docgen/` and
    `drydocs_port/` are now real packages — declared components that had never
    been extracted. Files MOVED; MODULE_MAP rows moved with them. Your apply
    takes the moves wholesale, but any local edit you carry against the old
    paths needs re-pointing at merge time — the collision ledger's business.

165. THE DOCMETA TRIO + THE CORPUS-ID GRAMMAR [TEST-PINNED] (`519bac3b` the
    corpus-id grammar — vendor doc sets become siblings, `bmc-docs` KEPT ITS
    NAME deliberately so the P0 benchmark record stays citable, `c1f6fa05` Q11
    document supersession registered planned + gate drafted, `65b7bccf` Q9 the
    Essential GraphRAG re-file as vendor documentation hooked to its product,
    `bb7200be` Q10 the failure/activity email corpus loads as the LEXICAL shape
    — Document→Chunk only, assignment deliberately absent until the (c) gate
    signs, `7fada596` Idea-136: snapshot.ps1's RED warn prints System.Object[],
    inboxed not fixed). Loaders and shapes port; the email corpus's msg/extract
    pair is a company-side system of record with a backup obligation.

166. Q19 — THE P0 BENCHMARK RE-RUN WITH A REAL PERSONA [TEST-PINNED]
    (`4f89105d` the direct add, `61a8df15` a count recompute, `0200f183` the
    run, merged `7671336b`). A Sonnet persona given ONLY schema + questions
    scored **11/12 mechanical vs the original hand-written 10/12 mechanical
    (12/12 after its two disclosed adjudications)** — recall held; the hidden
    cost was CONTEXT VOLUME, 6.6x. Quote "~27x token efficiency" as the
    hand-written CEILING with the persona floor beside it — your own
    PORT-REPORT-e60822fc comparisons should treat the persona numbers as the
    producer floor. New explainer `graph-retrieval-benchmark-persona-rerun.md`
    + persona_queries.json + results beside the originals.

167. N10 + N11 — THE WIRING-READINESS GATE PROMPT READS ON *YOUR* Q1-B PIN
    [TEST-PINNED / gate prompt] (`0268e305` N11, `6f0dbd26` N10, merged
    `826634c3`). N10 drafts `registry-wiring-readiness.yaml` (15
    confirmations): split pipeline-wiring readiness out of the semantic
    `confirmed` flag. ITS MOTIVATING CASE IS YOUR STANDING PIN — `cm_hosts`
    semantically signed yet false your side because your host stage is unwired,
    overwritten by canonical-producer every port and surviving only by your
    manual pin + re-arm trigger. If the gate signs, that pin CLASS retires
    (your gate-log records the retirement; entries are never deleted). Prompt
    is a clean-add under the manifest's gate-prompts rule; nothing applied.
    N11: the load-sequence surfaces guard's ingest.sh half was structurally
    dead (the derive-don't-list design guaranteed an empty scan that was
    unioned in as coverage) — the empty set now has to prove the derivation.

168. K23 — THE `kb_*` VERDICT [VERIFIED-SME / docs] (`3e467026` the export
    profile lands on the item's premise, `5ba443e1` evidence-doc §11 —
    attribution case FAILS: every purpose-built SEAL column 0-of-200, the
    de-facto link is application-grain owning-not-subject, recommendation OUT
    as attribution with the reason recorded, `1d429d17` §11.5 — the runbook
    baseline: remediation searches KB by Control-M folder, archives BEFORE
    replacing, capture-before-replace is a failed step if it fails, the archive
    is a SOURCE with a retention obligation, and G68's censuses give staleness
    a measured meaning). Reads on your §9 ServiceNow model; the profile ran on
    the SME machine — shapes only in the tree.

169. SMALL FIXES, POLICY AND HYGIENE [TEST-PINNED / docs] (`d3b443a4`+
    `6bacdb45` Idea-129 closed — the depgraph snapshot and schema_graph
    renderer write LF, the guard Idea-121 asked for exists; `2d107ce4`+
    `51be2fba`+`9474e467`+`dacca1b1` inbox appends — Idea-129/130/131/132/133,
    the last two of which became N12/N13 and the re-sourcing record; `b84a3ba5`
    S12 the environment-drift guard: the suite fails loudly when the
    interpreter's packages disagree with poetry.lock (born from a REAL
    cross-venv incident — the S13 "defect" it replaced was retracted as
    environment drift, recorded in S12's notes); `d5e7966d` the :Employee
    creation policy is STUB-AND-ENRICH, SME direction recorded and applied;
    `e298e217` seal_id joins the software registry as a NODE PROPERTY,
    USES_SOFTWARE untouched; `42405fc2` the cm_escalation_db registry note
    corrected — job-grain SUPPLEMENTS, never authors; `82512caf` repo-README:
    run the suite in the project venv; `fd57e0e5` G101 the seal_* vocabulary
    id migration item + the G87 title/priority fix; `b3b5e47b` L19 partial —
    clauses (c)(e)(f): all 19 design-doc references to the two S5-retired
    monoliths re-pointed at the fragment directories, the C9 HAS_APPLICATION
    row restated, the lineage model cited; (a)(b)(d) stay honestly open;
    `56cbeddd`+`9a7b4ab5` the IDEAS filing passes — 29 consumed entries to the
    audit trail, 7 partials kept in place, and the S12-era phantom
    PYTHONPATH defect RETRACTED with proof; `d1497925`+`e1b4a6a4`+`c4145090`+
    `a3935569` handoff rolls, never-port). Grooms (`7a3e2cf3`, `11cc9543`,
    `094bc3a3`, `01536824`, `3e409ba8`, `a4e65d26` — the last two include J50:
    gates.json's `unblocks` is a mention-scan, the J28 class opposite
    direction), claims, board/design renders, PR merge commits and depgraph
    snapshots in this range are ritual per the standing exemption.

170. THE FID K-SERIES — `fid-identity-and-scope` SIGNED OFF 33/33
    [GATE-AUTHORIZED; this range's other structural ruling beside the fold]
    (evidence: `7b0c4ae3` K16 unblocked, `5fe364b3` the two-source model,
    `76e343df` the platform-user clarification, `25239da5` job-grain run_as
    evidence landed on five surfaces, `1176a53d` session materials, `8ae771de`
    the S1-S5 session SQL; the gate: `b36ef388` round 1, `0b4746cc` round 2,
    `f857ff4b` rounds 3-5, `27c006ee` rounds 6-7, `d9cb2740`
    SIGNED, `337d6a6f` close-out residue). Ten rounds, one session,
    EVIDENCE-FIRST: the SME ran the session SQL on the replica and every
    section walked from numbers. Tally A4 B5 C4 D6 E3 F3 G8 (D6/G7/G8 added
    in-session).
    WHAT YOUR MERGE MUST KNOW, in order of blast radius:
    (a) **A SIGNED GATE IS FORMALLY AMENDED.** `seal-attribution-match-policy`
        §G3: the FID tier FILLS GAPS ONLY — it never overrides a confirmed
        mapping; disagreements are REPORTED, never written; the precedence
        order and match_method vocabulary are unchanged; the signed YAML is
        untouched (the amendment lives as a gate-log entry, N13 discipline).
        Your gate-log union-append must take that AMENDMENT entry with the
        sign-off entry — one without the other mis-states the tier.
    (b) **Identity ruled:** `:AppUser` keys on `fid`, `fid_name` is a property
        (§A1/§A2) — which CLEARS `scheduler_executed_by`'s identity blocker
        (its run-layer blocker stands; entry stays planned) and sets the key
        `scheduler_runs_as` builds against.
    (c) **Two new planned entries in fragment 41:**
        `seal_appuser_belongs_to_application` (BELONGS_TO_APPLICATION, role
        service_account, assignment_kind registration, as_of + origin) and
        `seal_appuser_owned_by` (OWNED_BY, role fid_owner — the Q7
        owner-of-record ruling; the two-human-owners rule attaches as a graph
        test). Both flip ACTIVE only at K26's build (flips-are-follow-ups).
    (d) **§D2 census classes:** non-account owner values are NAMED CLASSES
        outside the directory-join denominator (null/inherited, folder-header
        rows, variable-deferred, template placeholders, connection-profile
        placeholder) — counted, never joined. The platform-account curated
        list lives as a values-twin under `internal/`.
    (e) **§Q5 answered YES, with numbers:** 143 personal-id-shaped owners run
        11,948 jobs (2.3% of the estate); one SID-shaped owner carries 8,411
        jobs on a single app code (a G4-class report candidate). The type
        column is never a pull filter.
    (f) **A CORRECTION THAT MAY REACH YOUR COPY:** `OWNER` is MIXED-CASE at
        rest — the earlier ALL-UPPER claim recorded the normalization PLAN,
        not the data (doc 09 line ~360 carries the correction; a mixed-case
        sweep executed in round 2). If your side copied the ALL-UPPER fence
        from the session-SQL section, re-read it.
    (g) **E1 reshaped:** the directory dataset registers DATASET-ON-REPLICA
        (on the existing replica system row, layer human, Internal, SOR for
        account identity); `confirmed` flips with K26's build.
    OPEN, honestly: Q0's DIRECTORY half is pending (K16 stays in_progress —
    the directory-side counts are the one owed piece; the census company
    prompt in this range now asks for exactly that and nothing already
    answered), Q1 open with its consequence recorded, Q2 answered (no history
    surface exists — snapshot diffing IS the design). Follow-ups groomed:
    K26 (the build: registration, class-gated demand-set pull, name<->id
    crosswalk, the amended tier, the owner leg, retained snapshots — the
    fid-directory map entry is a CREATE there, it never existed) and K25
    (cross-application run_as detection) ride the same join. Your side adopts
    the gate via your own review, per your §9 model.

171. THE PORT-BOUNDARY FIXES THAT CLOSED THE 135-170 APPLY [config / docmeta]
    (`25556622` constraints.cypher re-dispositioned PER-ENTRY — the wholesale take at
    the 135-170 apply dropped two live company constraints (hpsm_queue_key,
    sn_group_name); the row now unions by constraint name. `bdb5886a` the
    cdo-frameworks doc-source row goes VERBATIM on the 2026-08-19 company fetch
    (the four crosswalk capture holes closed), the "context"-never-in-an-id naming
    rule lands in config/taxonomy/context-types.yaml's header, and the LOAD is a
    hand prompt (docs/company-prompts/cdo-frameworks-load-company-prompt.md) — loads are always
    yours; `963e93ca` the registry-embedding renders follow.)
    APPLY: constraints per-entry by name (your two stay); doc-source-registry now
    has its OWN per-entry row at step 175 — read that before taking this file.

172. ADR 0013 — THE BACKLOG SHARDING DESIGN, RULED WITH THE USER [docs / decisions]
    (`6d599c58` Y1 done: docs/decisions/0013-backlog-sharding.md ACCEPTED. Five
    mechanisms: one STANDALONE mapping per item, FLAT backlog/items/<id>.yaml (flat
    on graph grounds — epic: is a field, Y4 mints IN_EPIC from it); epic header
    comments become DATA (epics/<epic>.yaml groom_log); summary/next_ready DELETED
    from storage, derived by the board; a claim is a one-file flip; splitter + S5
    deep-equality proof + tombstone, and the splitter PORTS AS CODE — each side
    shards its OWN per-entry-unioned monolith, never receives the other's tree.
    Same day, the F4 amendment (step 174). Ritual beside it: `b0c823da` the C34
    claim, `16f370d0` the pre-reboot handoff roll.)
    APPLY: clean-add. The design; the build is step 175 and its apply sequence is
    the ONE thing in this range that is not "read the manifest as usual".

173. THE 7c18ff4b PORT REVIEW AND ITS TWO HAND PROMPTS [docs / review]
    (`5568be09` docs/reviews/port-review-7c18ff4b-20260820.md — range verified
    247/316 producer-side, five findings, verdict mergeable with conditions on the
    follow-up; `195e5561` + `bc14b6c8` docs/company-prompts/port-7c18ff4b-followup-company-prompt.md
    — the FID pair lands as ONE gate-log commit, the company-local fixes get a
    not-port-introduced section; REWRITTEN the same day so it asks for nothing
    back: records live in YOUR ledger, instance names nowhere (the standing rule
    from here on for every producer-facing text). `94f3d51b` Idea-147 (the scrape
    run <-> registry row join; re-issued as Idea-148 at the UI merge, step 176)
    and J51 widened to six paths.)
    APPLY: clean-add, all three. The review's F1/F2 are conditions on YOUR
    7c18ff4b follow-up, already in your ledger; nothing here changes your apply.

174. F4 RULED — STATUS IS PER-REPO AT A PORT; J51 THE SIX PER-ENTRY ROWS [config / manifest]
    (`46a2c2ef` the ruling (user, 2026-08-20): when both repos hold the same
    backlog id, the CONSUMER's status stands — a port never writes status, the
    producer's status + date fold into notes; what your 2026-08-11 union already
    did for 12 ids ("done never crosses"). Landed in ADR 0013 Clause 4 + 6 and
    the manifest entry_rule; "keep the further-along" is the intra-repo
    two-machine rule and still holds there. `0242fa43` J51 done: PORT-MANIFEST
    rows for description_tokens.py (per function), detect.py + __init__.py (per
    detector id), test_runbook_currency.py (per exemption table, retirement
    trigger named), email-dl-contact-point.yaml (you keep the file; producer SME
    intent crosses by section), ui-components.yaml (the K7-K15 hold IS the rule),
    doc-source-registry.yaml (field split: graph_locator / captured_at / manifest
    / source are yours; confirmed is per-repo). test_port_reconcile_guards gains
    no-drop checks for the two list-shaped files, live-gated on OPTIONAL
    before-snapshots (step 1 of the reconcile-port skill shows how to arm them).
    `4dac320c` its claim.)
    APPLY: PORT-MANIFEST is canonical-producer — take it; these rows are what
    resolve the six collisions caa0406 unioned by hand, so read them BEFORE those
    files. Idea-142 closed by this step.

175. Y2 — THE BACKLOG IS SHARDED; backlog.yaml IS A TOMBSTONE [drydocs-core / plan / guards]
    [THE ONE STEP WITH ITS OWN APPLY SEQUENCE — read
    docs/company-prompts/port-backlog-shard-company-prompt.md whole before
    touching the backlog]
    (`8a6b592d` the build: docs/restructure/backlog/ — items/<id>.yaml x469,
    epics/<epic>.yaml x26 (54 header blocks as groom_log data), plan.yaml,
    modules.yaml; drydocs_core/backlog_store.py the ONE reader (assembles the
    monolith's document shape, derives the roll-ups, dumps the assembled document
    for the reconcile guard; S5's duplicate-key loader; anchored on repo_root per
    Idea-109); scripts/shard_backlog.py the splitter with the deep-equality proof
    (469 items field-for-field, 157 inline comments harvested into an additive
    `annotations` field and checked, plan/modules identical, derived summary ==
    stored counts AND next_ready set) — run BEFORE the tombstone, and again at it;
    readers re-pointed (plan_board: derived counts + a "Ready to pull" strip =
    next_ready, `updated:` dropped; plan_roadmap; render_gates;
    build_schema_matrix; render_board CLI); guards (test_backlog: schema v3,
    path-is-identity, per-file duplicate keys, NO STORED ROLL-UP — the two
    recompute guards inverted —, derived-summary consistency, monolith-is-a-
    tombstone; test_runbook_coverage; test_port_reconcile_guards after-side via
    the store; test_plan_roadmap); writers (groom-backlog SKILL + validate.py,
    backlog-groomer agent); CLAUDE.md §0 pull rule + ritual; MODULE_MAP core row;
    reconcile-port before-snapshot = backlog_store.dump_document(); the manifest
    rows (items per-entry where THE ENTRY IS THE FILE, epics union-append,
    plan/modules per-entry, backlog.yaml carries the one-time sequence).
    `01cfd7dc` the --no-ff merge; `931883a8` Y2 done — the first one-file status
    flip; `4040c47e` the claim that FROZE backlog.yaml for the build; `df447e7d`
    the lull-port hand prompt. gates.json reorders once (unblocks lists follow
    item order) and is deterministic after.)
    APPLY — in this order and no other: (1) per-entry UNION your monolith with
    the producer's LAST monolith state, `git show 4040c47e:docs/restructure/
    backlog.yaml`, under the old rule — id-keyed, never drop, YOUR status stands,
    producer status + date into notes; commit that union on its own. (2) run the
    PORTED `scripts/shard_backlog.py --date <today>` on it — your items survive by
    construction. (3) the proof must print PROOF OK; a failure STOPS the port at
    this step, recorded in your ledger, monolith left in place. (4) `--tombstone`;
    commit tree + tombstone together. NEVER copy a file from the producer's
    backlog/ tree — the tree is each side's own output. If a range is mid-apply
    when you read this, finish it on the monolith; this is the first step of the
    NEXT range. After it, claims are one-file flips and the reconcile before-
    snapshot is the dumped document.

176. C34 — THE lob-product-team TREE DECLARED A skos:ConceptScheme; THE dcat:theme GATE DRAFTED
    [ontology / taxonomy] (`6e912c1d`: (a) config/taxonomy/lob-product-team.yaml
    gains `concept_scheme` — skos:ConceptScheme urn:drydocs:scheme:lob-product-team,
    top concepts = lobs, parent_* read as skos:broader, DevTeam excluded, the
    Taxonomy Framework cited by its cdo-frameworks registry row — layer 1, no
    gate, no edge; (b) config/gate-prompts/dcat-theme-subject-scheme.yaml DRAFTED,
    unsigned — §A records residency as ANSWERED BY THE G102 FOLD, §B IS-vs-HAS a
    concept (:Theme as its own label recommended, the TOMRole/ProductRole
    precedent), §C annotation depth as the grain control, §D the AreaProduct cap
    DEFERRED with reason + the annotation cap as a DETECTOR, §E pending vs
    out_of_scope; catalog_has_theme (HAS_THEME) + :Theme registered PLANNED;
    schema_graph.cypher / enforcement matrix / gates.json regenerated, 96 gates.
    The UI-branch merge trio rides here as ritual: `7f52f6d6` the WIP capture
    (agents read the root .env as fallback; the ownership pane's custom edge type;
    /ask last-turn persistence), `5a708ab4` its roll-up recount, `423192db` the
    --no-ff merge that put R18/R19 + Idea-143..147 into the monolith BEFORE the
    shard, and `fcdfe88c` two Idea-header slips fixed (Med not Medium; lowercase
    groomed).)
    APPLY: taxonomy/lob-product-team.yaml is per-entry (your real LOB rows stay;
    the `concept_scheme` block is mechanism — take it whole); gate-prompts/** is
    yours, the new prompt is a clean-add; the vocabulary fragments per-entry as
    always (two PLANNED entries, nothing active). You run your own gate on it.

177. S9 — THE DOCS ROOT IS GROUPED; FOUR MANIFEST ROWS ARE RE-PATHED
    [docs / manifest — ACTION-REQUIRED, and the action is on YOUR paths, not ours]
    (`c3cd5521`: producer-side moves only — `UI-WIP/` -> `docs/design/ui-exploration/`,
    `docs/port-prompt.md` + its steps-1-42 archive -> `docs/port/`, the eight
    `*-company-prompt.md` -> `docs/company-prompts/`, `docs/controlm-*.md` ->
    `docs/controlm/`; 169 files carried the rename; `drydocs/port_preflight.py`'s
    `PORT_PROMPT_PATH` re-pointed — it is built from path SEGMENTS, so no textual
    sweep sees it and the suite does not either.)

    WHY THIS STEP EXISTS. `PORT-MANIFEST.yaml` is `canonical-producer` — your apply
    phase takes it WHOLESALE — and four of its rows changed path here:
      `UI-WIP/**`                        -> `docs/design/ui-exploration/**`
      `docs/gate-*-company-prompt.md`    -> `docs/company-prompts/**`
      `docs/port-*.md`                   -> `docs/port/**`
      (new) `docs/controlm/**` in `default_ok:`; the `docs/*.md` entry re-scoped.
    The first still matches on your side. The middle two are PRODUCER-shaped
    directories that DO NOT EXIST in your tree, so the moment you take this manifest
    your `test_no_manifest_row_matches_nothing` goes RED on two dead rows — the rows
    that used to govern your `docs/port-prompt.md` and your delivered gate packs now
    govern nothing, and those files fall through to the next broader row. This is the
    exact rot that check was written for; it is not a false alarm.

    APPLY — pick ONE, and record which in your PORT-REPORT:
    (a) MIRROR THE MOVE (recommended if you still keep those docs): `git mv` your
        `docs/port-prompt.md` -> `docs/port/`, your `*-company-prompt.md` ->
        `docs/company-prompts/`, sweep your own references, done — the taken rows
        then govern real paths and both sides read the same shape.
    (b) OVERLAY IT: add `row_may_match_nothing:` entries for `docs/company-prompts/**`
        and `docs/port/**` to YOUR `PORT-MANIFEST.<side>.yaml` (the J34 seam, step
        160) with the reason "producer-shaped directory; this side keeps the flat
        docs-root layout". Correct, and cheaper, but the two trees stay divergent.
    Option (a) is the better fit if you are already acting on the
    `port-7c18ff4b-followup-company-prompt.md` (retired producer-side 2026-08-25 after the port closed; your copy is the live one) instruction to retire your `port-prompt.md` to a
    pointer — do the retirement and the move in one commit rather than twice.

    WHAT DOES NOT MOVE, and is worth knowing before you go looking:
    - `docs/port/**` and `docs/company-prompts/**` are BOTH `never-port`. None of
      these files crosses. This step changes where the ROWS point, nothing else.
    - The `reconcile-port` skill cites the port prompt by NAME, never by path, so it
      needs no edit on either side. Same for `git-readme.md`'s narrative mentions.
    - Producer-side historical records were deliberately left naming the OLD paths —
      `IDEAS.md`, the steps-1-42 archive, `docs/reviews/**`, `config/gate-log.md`, the
      depgraph snapshots. If you diff those and see `UI-WIP/`, that is intended, not a
      missed sweep. (The producer's own sweep proved the point: run over
      `docs/reviews/**` it turned a dated finding into a false claim and minted a path
      that never existed. Reverted.)
    - Your `docs/controlm-*.md`, if you hold your own, are governed by the re-scoped
      `docs/*.md` `default_ok` entry until you move them; nothing forces you to.

178. THE WEB CONSOLE — O57 /load-map, O64–O67, O55, O31 [web — canonical-producer,
    read K7–K15 first] (`72e75735` O57: a NEW nav module `loadmap` at /load-map,
    steward+admin access, reading the committed `load-map.json` and never re-deriving
    from the registries — the 30 sources, 16 systems, 19 sequence steps and BOTH declared
    defect lists N4 generated had no console reader at all. `6abf2106` O64 Ask keeps the
    last completed turn per persona across navigation; `152042cf` O65 dark mode reaches
    the React Flow chrome through the library's own `--xy-*` variables (cascade order,
    not missing rules); `6eaf48ac` O66 ONE shared `RelEdge` overlay for all three graph
    canvases; `e8fa5ff1` O67 `ModuleIcon` exhaustiveness — a `ModuleId` without a glyph
    case is now a `tsc` error; `b8962913` O55 npm audit clean, lockfile only; `154c5fa8`
    O31 `benchmarkData.ts` is RENDERED from the P0 harness run plus a verdict ledger,
    not hand-carried — the old scoreboard disagreed with its own rows.)
    APPLY: take by NAME, never `git checkout -- web/src` — the K7–K15 folder-attribution
    hold is still live and a wholesale checkout re-adopts the held UI. O31's `.ts` is
    DERIVED: take `scripts/render_benchmark_data.py` + `verdicts.yaml` and re-render it.

179. THE SME LAUNCH GUIDE NAMED THREE SERVICES AND THE STACK HAS FOUR
    [docs/design/ui-exploration — canonical-producer] (`90e79687`: live mode ran green on
    Neo4j + drydocs-api + Vite and `/ask` still failed, because `/ask` is the ONE view
    that does not go through drydocs-api — it talks to the `graph_qa` ADK agent on :8000,
    absent from the guide entirely. Two properties recorded because each costs a debugging
    session once: that server runs in its OWN venv, not the poetry env, and reads its OWN
    `agents/.env`, not the repo-root one — both gitignored, so a fresh clone or a new
    worktree has neither. `847ce8a7` + `8b38109f` add the chat-turn vs router-hop
    vocabulary page and fix its mermaid figures ignoring the page theme.)
    CAUTION: all three landed at the PRE-S9 `UI-WIP/` path and moved with step 177. Read
    177 before resolving them, or you will re-create a directory both sides just retired.

180. THE EXECUTIVE OVERVIEW, REV 10 [docs/overview — `default_ok`, audience differs]
    (`54f2d6df` first content refresh since rev 6: the ONE-DATABASE topology
    (`document-content-topology` signed 2026-08-18, ADR 0011 executed by choice —
    ddcontext/dddocs/ddall retired, ddschema stays separate), deepdoc re-chartered per
    G32 §E / MM1, ADRs 0008/0009/0010 accepted and built, new §03 agent decision tree.
    `ba8912a2` the executive module flow by default, full map behind a checkbox.
    `bb28f5d6` the page renders its own diagrams when opened from disk — it had NEVER
    carried a mermaid loader in any revision and relied on the artifact host, so a
    `file://` open showed diagram source.)
    APPLY: nothing. `default_ok` on purpose — outward-facing, and your audience is not
    ours. The mermaid-loader technique is worth lifting if your own HTML docs open from disk.

181. D10 — THE XML-vs-REPLICA PRECEDENCE GATE, DRAFTED AND UNSIGNED [gate-prompts]
    (`0baa7973`: `controlm-definition-precedence`, one question per object class with the
    Idea-43 candidate STATED rather than pre-picked, owner + sunset riders on every
    clause, the T16 second path carried. Registers nothing, decides nothing.)
    APPLY: `config/gate-prompts/**` is YOURS. Take it as a starting point if you like, but
    the ruling is your SME's — this side has not run it either.

182. Q14 — vendor-docs-entity-core: DRAFTED, SIGNED 21/21, THEN RENAMED [gate / ontology]
    (`5a0383e7` the draft — 5 sections / 20 confirmations, §E added as the corpus's own
    doc-graph gate with its chicken-and-egg stated in the prompt itself; `b8d70a78` the
    standard E6 safe-to-transcribe closing confirmation; `d316bf96` SIGNED OFF 21/21 the
    same day — `ControlMUtility` confirmed as a new Control-M-family class with the
    `PART_OF` product bridge, `DESCRIBES` reused as a new triple, vendor cross-links as
    `SEE_ALSO` with `rdfs:seeAlso` ADOPTED, and the real layer-3 chain ruled a new
    `INVOKES` triple with the active `scheduler_invokes` untouched; `cbb38458` RENAMED
    entity-spine → entity-core on the user's style ruling, sign-off transfers.)
    CAUTION ON THE RENAME: the SIGNED OFF `gate-log.md` entry was NOT edited (L25
    riders-not-edits) — a `RECORD:` entry carries the new slug with transfer wording. Take
    the entity-CORE spelling; the signed confirmations' body prose still reads "spine"
    deliberately, because that is what the SME saw.

183. MM2 — THE data-flow-overview GATE PROMPT, DRAFTED [ontology / gate-prompts]
    (`4176c125`: the per-data-flow overview record keyed on the `%%DATAFLOW` value the
    launcher itself names, reconciling three grains that existed unreconciled — the
    `%%DATAFLOW` variable fact, the designed-never-built `:AppDataFlow`, and the runbook
    data-series traversal. 27 confirmations in six sections, nothing pre-picked;
    `:DataFlow` plus five edges registered PLANNED, no loader touched.)
    APPLY: vocabulary fragments per-entry as always — five PLANNED entries, nothing
    active. Read it before MM7/MM8 land; it is where the grain question gets settled.

184. EPIC MM — deepdoc LEAVES THE PLACEHOLDER [drydocs-deepdoc / docs]
    (`cf58e4d8` mints MM1–MM10 and adds `docs/design/deepdoc-data-flow-overview.md`,
    synthesized MECHANISM-ONLY from one production support deep-dive whose verbatim
    transcript is machine-local and never committed; every field badged SOURCE/DERIVED,
    every label and edge `status: planned`. It establishes the Control-M Output tab as
    ITERATION 2 of the launcher contract — it asserts the job KIND, the provenance-GUID
    chain, the landing prefix and the compute target that CMDLINE cannot; no sysout
    ingestion existed anywhere before. `ff640638` and `f9e9d037` are same-day SME rulings
    on it. `42b57e98` MM1 restates the deepdoc charter where the package docstring,
    MODULE_MAP row, boundary-group comment and roadmap still carried the old one.)
    APPLY: `docs/design/**` evaluates. The `.md` is the source and the `.html` beside it
    is a deterministic render (Epic L) — never hand-merge the HTML, re-render it.

185. MM7 — THE OUTPUT-TAB PoC, AND THE SME RULING THAT REVERSED ITS HEADLINE
    [scripts/poc — `default_ok`; THE RULING IS THE PART THAT MATTERS] (`e124b3ee` the
    PowerShell parsers, one per job shape plus a cross-hop joiner, dispatching ONLY on the
    launcher's own "Identified <KIND> Job" line and never the job name — the R13 trap;
    `293a6439` the sanitized record of the first real run, eleven logs parsed, zero errors;
    `8adfa688` THE RULING — `provenanceGuid` is a run-scoped placement→ingestion handoff,
    a correlation token. It is NOT provenance in the PROV-O sense this repo reserves the
    word for, and it cannot validate or reconstruct Control-M lineage. The PoC asserted
    the opposite, printing "CHAIN BREAKS" at six of six transforms, and the first real-log
    run was read as six defects. There is no chain to break. `18f0e26c` job identity comes
    from the sysout FILE NAME — the modern wrapper writes none into the body; `075aeea3`
    takes the leading filename field by POSITION, not by how it looks. `3f1cac70` rewords
    two citations that named an extractor module MM7 has not written.)
    APPLY: throwaway-grade, not a component, writes no graph — take it only for the log
    patterns. Take the RULING regardless: any lineage design that assumes the GUID
    survives past ingestion is wrong, and that is a design fact, not a parser fact.

186. G34 — THE BUSINESS-GLOSSARY SCAFFOLD, RESERVATION ONLY [ontology / config]
    (`523b538b` reserves the names and the slot so the internal port cannot collide (SME
    reason at `business-application-identity` §F2) and STOPS — no term defined, no loader
    reading it, no gate run. `CatalogBusinessTerm` (skos:Concept, one node per SENSE),
    `CatalogValidValue`, `CatalogElement`, `CatalogEncodingInstance` planned; three edges
    planned in `42-local-catalog.yaml`; the classification split written down with both
    homes created — `config/glossary/` (Internal-Public, ports) and `internal/glossary/`
    (Internal, empty by design). `7ab95016` adds the first public sense: DRY.)
    CAUTION: the SME records that YOUR side runs a dedicated acronym tool. This is the
    slot, not a competitor — do not populate it before that question reaches your SME.

187. C33 — STOPPED AT Q3, STATUS `blocked` [config / taxonomy] (`31dda9a4`: §C1 gains the
    install-path pattern row `abinitio-install-path`, and the item then STOPS — symlink
    stability is unruled, so per its own acceptance the loader and the MERGE key were
    deliberately NOT written.)
    APPLY: nothing to run. Worth one read as the shape of an item that stops honestly
    instead of guessing past its own gate.

188. THE VOCABULARY IDS MIGRATE ONTO THE DOMAIN-DERIVED SCHEME — G87, G88, G101, G89
    [ontology — per-entry, AND THIS ONE CHANGES IDS YOU MAY HOLD] (`453d9c0b` G87
    force-migrates the 37 live epoch-tag ids: add-new + deprecate-old with `superseded_by`
    on every old row, map joins / lineage `VOCAB_IDS` / test pins repointed, and
    `migrate_vocab_ids_g87.cypher` re-stamps old `r.vocab_id` in the graph; `51a02e24` G88
    relocates the people/org family (ORG membership + PROV qualified attribution, 14
    entries) into domain `human` as new fragment `52-local-human.yaml` — a partition move
    only; `8dc9a804` G101 migrates the `seal_*` ids the same way, 5 per the census plus 2
    post-gate appuser entries as a named widening; `9ba88772` G89 repoints
    `runbooks.series.v1` off the PLANNED `TRIGGERS` edge onto the active `INVOKES`
    (`scheduler_invokes`) — it had also had the wrong `from_node`.)
    APPLY — IN THIS ORDER: fragments per-entry as always, but the OLD rows are kept with
    `superseded_by`, never deleted, so a union gives you both and that is correct. Run the
    two `migrate_vocab_ids_*.cypher` against YOUR graph or your stored `r.vocab_id` values
    keep pointing at deprecated ids. The port guard implements the manifest's
    gate-authorized-deprecation exception — this is the case it was written for.

189. C26 — THE COMPANY-CATALOG DIVERGENCE, WRITTEN WHERE A PORT READS IT [ontology /
    reconcile ledger] (`707cea34`: 5 differences plus a joint label/key ruling and 2 relay
    items land in the reconcile-port ledger; `catalog_has_sub_lob`,
    `catalog_sub_lob_has_product_line` and `CatalogSubLOB` reserved PLANNED and the two
    company map ids `proposed` — NOTHING adopted; LOB002 AWMCIB split into AWM + CIB @1.0
    as taxonomy capture.)
    APPLY: read the ledger entries first — they describe YOUR catalog, from producer
    observation, and the point of writing them here is that you can correct them. Nothing
    in this step is active; the adoption is a gate on your side.

190. G77 — ONE THEME VOCABULARY, TWO CORPORA [drydocs-docmeta / taxonomy]
    (`a13f4561`: `concept_scheme.py` reads the `lob-product-team` skos:ConceptScheme
    (IRI = scheme#notation; labels never resolve), a folder-scope THEME token is added for
    `JobType.FOLDER` (optional — findings, never raises), and the docmeta `PageRecord`
    gains `themes` / `theme_status` reporting classified / unclassified / out_of_scope
    APART rather than collapsed. Zero graph writes.)
    APPLY: `config/taxonomy/lob-product-team.yaml` is per-entry (step 176 + `b9dd1191`);
    the `concept_scheme` block is MECHANISM and crosses whole, your LOB rows stay.

191. G82 — THE MISSING PAT TEAM-REPORT PROJECTION [drydocs / config]
    (`adb8d301`: `drydocs/pat_projection.py` + `scripts/project_pat_team_report.py` write
    the two files `REFRESH_REFERENCE_CHAIN` reads. It REFUSES to guess a key header —
    `--header-map` pins the spellings at the first real run rather than guessing, and
    `Relationship Type` is taken, never the `Team Type Name` decoy. `pat-team-report.yaml`
    is authored from what it actually reads and `pat:people-report`'s `locator.mapping` is
    no longer null. `2c995f34` skip-guards the gitignored-fixture read.)
    CAUTION: the REAL-DATA run is yours — this side has no PAT export. And see step 209:
    G79 wired a third file, `pat_team_roles.csv`, that this projection does NOT emit
    (producer Idea-160). Your first SOURCE-mode `refresh-teams` will stop on it by name.

192. U21 — IMPORTS EDGES ARE RETRACTED PER SOURCE [drydocs/loaders]
    (`6c7e1514`: after the D7 node pass the code-snapshot loader DELETES its own
    IMPORTS / IS_ENCODED_IN / HAS_MEDIA_TYPE edges that this run did not re-assert, scoped
    to modules the snapshot contained — omitted modules and other loaders' edges untouched.
    Deleted, not marked, with the reason recorded; `edges_retracted` is reported in the
    summary, the envelope and on `:JobRun`. Unit + testcontainers guards.)
    APPLY: take it. Live-verified producer-side on `neo4jtest` (J18) — 1032 edges = the
    snapshot; re-verify against your own graph, since the two are independent.

193. J33 — THE THREE rich-ANSI FAILURES WERE `FORCE_COLOR` [tests]
    (`3045a22b`: `FORCE_COLOR=3` in one machine's environment made three tests fail on
    colour rather than behaviour. The unit conftest now clears it — and `TERM=dumb` — at
    IMPORT, before `drydocs.cli` builds its Console. Whole suite green under
    `FORCE_COLOR=3`; no assertion was loosened to get there.)
    APPLY: take the conftest change. If you have ever seen an unexplained rich-output
    failure on one machine and not another, this is very likely it.

194. J49 — THE TEN NON-RENDER `write_text` SITES ARE RULED [tests / scripts]
    (`aea3d584`: explicit `newline="\n"` at every one, each with its reason. None produces
    a committed artifact — the m0 transcripts and `SDLC-Docs/extracted` are hand-authored
    INPUTS — so the DECLARED tuple gains nothing; the census is now zero, which is what
    lets a repo-wide static rule replace the per-site fence.)
    APPLY: mechanical. Take it with the guard, or the census reopens on your next write site.

195. S8 — `cli.py` SPLITS INTO A COMPOSITION ROOT + SIX DOMAIN MODULES
    [drydocs — `evaluate`, AND THIS IS THE BIGGEST HAND-MERGE IN THE RANGE]
    (`f5e7229d`: 3184 lines become a thin root plus `cli_schema` / `cli_ingest` /
    `cli_verify` / `cli_variables` / `cli_docs` / `cli_plan`, merged flat — the SAME 43
    verbs under the SAME names, so the CLI contract does not move. `verify-reference` and
    `verify-controlm` are added with `m1-verify` / `m3-verify` kept as deprecated aliases.
    The three cross-component verbs stay in the root: no new boundary exemption.)
    APPLY — READ BEFORE YOU START: `drydocs/cli.py` is `evaluate` and the collision ledger
    rule is "keep consumer verbs, add producer verbs". That rule still holds, but the
    producer verbs now live in SIX files, so the merge is: take the six new modules whole,
    then reduce YOUR `cli.py` to the composition root plus your own verbs. Do not try to
    reconcile a 3184-line file against a 400-line one line-by-line.

196. G78 — A CHAIN STEP THAT CANNOT FIND ITS INPUT FAILS BY NAME, BEFORE ANY WRITE
    [drydocs / drydocs-core] (`9463beee`: `refresh-reference` no longer has a fixture
    default — you pass `--samples-dir` (fixtures) or `--source <id>` (the declared landing
    zone), with a per-step path table printed at close. `ingest-controlm` preflights and
    prints a FIXTURE RUN banner. Five previously untested loaders gain a direct test import.
    The fixture-naming divergence between the two sides is recorded in the port ledger.)
    APPLY: this is a BEHAVIOUR change to how a run is invoked — any script or runbook of
    yours that called `refresh-reference` bare now fails loudly by name, which is the point.
    Update your callers in the same commit you take it.

197. R20, R21, R22 — THE QUERY SPECS, THE NOTIFICATIONS, THE TOWER CONTRACT [drydocs-api /
    drydocs-core] (`06f9a76b` R20 audits all 32 query specs against the vocabulary AND the
    live schema: `ownership.teams.v1` was asking a NEVER-REGISTERED `DEVELOPS` edge (now
    `WAS_ATTRIBUTED_TO {role:'developed_by'}`), catalog-cascade's planned `HAS_APPLICATION`
    leg is written down via `QuerySpec.planned_terms`, and folder-applications was found
    CURRENT — the 08-20 zero was a load gap, not a spec defect. `d0069191` R21 carries Neo4j
    notifications instead of discarding them — one core shape, both runners, `StepRecord`,
    `:AgentRun` warnings, exposed on the admin path. `4519d585` R22 gives Tower a declared
    source contract text2cypher cannot cross: `config/taxonomy/ui-concepts.yaml` with
    `graph_binding: none`, plus a Tier-0 declared-term step that answers with provenance
    BEFORE the router — no Cypher, no LLM — drift-guarded against the TypeScript.)
    APPLY: R20's `DEVELOPS` fix is the one to check against your own specs — an unregistered
    edge type in a spec returns zero rows and reads as missing data, not as a bug.

198. Y5 — THE ROADMAP STALE-RENDER GUARD TOLERATES STATUS-ONLY DRIFT [plan / guards]
    (`f7744112`: a sources fingerprint — status normalised out, renderer bytes included —
    is embedded in `roadmap.html` and compared only when the page differs, so a
    claim commit that flips one `status:` no longer has to ship a render. Bounded by a test
    proving title / module / phase / dependency / new-item / renderer changes still FAIL.
    CLAUDE.md's pull rule and the backlog README now agree that a claim ships no render.)
    APPLY: take it with the guard. This is what makes the one-file claim flip cheap, which
    matters more on your side than ours if two sessions ever run at once.

199. THE SNAPSHOT RITUAL'S OWN INSTRUMENTS [knowledge/depgraph-snapshots — producer ritual,
    but the LESSON ports] (`22b8ad72` then `5c0308e6`: the CI check printed GREEN at a RED
    HEAD. PS 5.1's `ConvertFrom-Json` emits a JSON array as ONE WRAPPED ITEM — in pipeline
    AND in argument form, which the first fix missed — so the verdict's scalar tests became
    member-enumeration filters that passed if ANY recent run had. Caught live at a
    billing-blocked failure. `4bd82a47` U26/U24: the script resolves the depgraph sibling
    beside the MAIN working tree via git-common-dir, so it runs from a worktree.
    `cd48241c` U22: `drydocs code-graph-freshness` compares `max(:CodeModule.last_seen_at)`
    to the newest snapshot's `captured_at` with fresh/stale/empty/no-snapshot/unreachable
    verdicts — warn-only, never refreshing. `24bfbf9d` U25/G103: `debt-metrics.jsonl`, one
    append-only LF row per snapshot run, `merge=union`, exempt from U12 retention, and no
    row is written without a database.)
    APPLY: the `.ps1` is producer ritual and need not cross. The PS 5.1 finding should:
    any PowerShell of yours that reads `gh ... --json` and tests a scalar has this bug.

200. K24/J46 AND J47/J50 — GATE-PAGE IDS, RUN-LOG FLAKE, DECLARED UNBLOCKS, MANIFEST ORDER
    [guards / plan] (`2e8b5c3d`: a guard against REUSED question ids on gate pages, proven
    on the pre-renumber FID page pulled from history, plus the run-log collision test
    de-flaked by injecting the clock into `claim_log_path`. `0a72aed4`: `gates.json`
    unblocks edges are now DECLARED — item gates via a validated-slug field, sections
    hanging edges off the gate they are ABOUT — which takes 581 citation-inflated edges
    down to 25 genuine ones; and the PORT-MANIFEST ordering guard is DERIVED for every row
    (earlier-glob shadowing) instead of read from a hand-typed list.)
    APPLY: the manifest ordering guard is the one with teeth for you — it is what catches a
    new row added above an existing one and silently shadowing it.

201. U20 — THE CODE-GRAPH REVIEW PLAN NAMES WHERE ITS NUMBERS COME FROM [docs/reviews]
    (`f56cf601`: the plan is restated on the eight package roots, and the hand-typed
    per-root count list is replaced by where each number is DERIVED — a graph query for
    modules, the runbook-coverage test for docs — with a guard keeping the hand-typed form
    out. Re-measured counts live on the item, not in the prose.)
    APPLY: nothing. `docs/reviews/**` is a dated record on this side.

202. N16/S12 — `source_label` BECOMES A DECLARED ENUM; THE ENVIRONMENT-DRIFT GUARD
    [drydocs-core / tests] (`1afd7c97`: the widen-and-enforce ruling — `SOURCE_LABELS` is
    now declared and enforced, the retired agent value is out, and the mappings'
    `source_label` collision is stated rather than left implicit. Separately, a drift guard
    fails the session ONCE when installed packages disagree with `poetry.lock` — drift,
    never path, proven negative via `DRYDOCS_LOCK_PATH`.)
    CAUTION: this closes the standing tail carried at RELAY-11(7) — `source_label:
    'snowflake'` was a 13th value outside the declared enum that 12 of 28 producer loaders
    already sat outside, unenforced. If your loaders carry labels of your own, widen the
    enum in the same commit you take it or the guard fails on YOUR data, correctly.

203. J37/J31/J45 — NEVER PARSE A RENDER, AND WORK VISIBILITY [working agreements / guards]
    (`d91ac809`: the never-parse-a-render rule enters CLAUDE.md §6 with a sweep guard
    (`test_no_render_parsing.py`); census confirms no test parses `--help` any more. The
    work-visibility clause — `wip/<id>-<machine>`, push at the first substantive edit,
    check `git branch -r --list` before releasing someone else's claim — enters the pull
    rule. J45 verified as ALREADY DELIVERED at RELAY-5, not re-done.)
    APPLY: CLAUDE.md is canonical-producer; take it. The wip-branch clause is written for
    two machines on one repo and applies to you the same way it applies here.

204. L25/L26/J44/G110 — DATED RIDERS, THE WHITE PAPER TYPE, THE FENCE GUARD, agents/
    [docs / skills / guards] (`f748abbd`: citations on SIGNED pages get DATED RIDERS rather
    than edits — the D2-RIDER precedent plus the rule itself in the HITL flow doc; the
    documentation skill gains the White Paper type; the markdown fence guard widens to
    EVERY tracked markdown with five named, reasoned, shrink-only carve-outs; the `agents/`
    MODULE_MAP row is corrected and `requirements.txt` pinned to measured versions.)
    APPLY: the riders-not-edits rule is the one to adopt first — it is what step 182 relies
    on, and it is the difference between an audit trail and a rewritten one.

205. R14 — `/list-apps` LISTS ONLY THE REAL AGENT APPS [agents] (`6efc1b2b`: `agents/serve.py`
    hands the API server ADK's own `NestedAgentLoader` — the adk-web loader, `agent.py`
    directories only — so the shared `common/` package stays where the apps import it and
    disappears from discovery. The README states the app-vs-shared convention; a guard
    holds it; proven against the installed ADK.)
    APPLY: only if you run the agent stack. Cosmetic until you do, then immediately not.

206. THE "spine" → "backbone" SWEEP [style — repo-wide, mechanical] (`a56da422`: 82 files,
    163 swaps, pure 1:1 — insertions equal deletions. One file rename rides along
    (`test_business_key_spine.py` → `test_business_key_backbone.py` plus its one cypher
    pointer) and six test FUNCTION names, because underscore identifiers sit outside `\b`.
    Code changes are comments, docstrings, messages and local names only; repo-internal
    string contracts moved on BOTH sides together, and no graph data value carries the word
    — verified before sweeping. `5e28e11b` does IDEAS.md prose, 8 swaps and 2 deliberate
    survivors. `72a60da3` is the ruff-format follow: one swapped comment went over the line
    limit and the CI format gate is blocking.)
    CAUTION: this touches 82 files and will collide with anything you have edited in them.
    It carries no meaning — resolve every conflict in favour of YOUR content and just apply
    the word swap on top. `vendor-docs-entity-core` (step 182) is the one place the swap is
    an identifier rather than prose.

207. G80 — THE UNCHAINED-LOADER GUARD, AND TWO NEW LOAD-MAP DEFECT CLASSES [drydocs / web]
    (`0d53e4db`: `cli.unchained_loaders()` fails the suite BY NAME for any `LOADER_REGISTRY`
    loader that no `COMMAND_LOADERS` command runs, with `UNCHAINED_LOADER_EXCLUSIONS`
    carrying the written reasons. `load-map.json`, the N5 HTML and the O57 defects tab gain
    `unchained_loaders` and `steps_with_uncommitted_inputs` beside the two existing lists;
    the generated SEAL fixtures are declared presence-independent so the committed render
    cannot flap between machines. `f2fbee59` routes the new lists through the O57 console
    guard — every collection must have a reader — and closes the item.)
    APPLY: expect this guard to FAIL on your tree first time and treat that as the finding.
    A loader nothing runs is exactly what it is for.

208. J42 — DIFF THE TWO REPOS' BACKLOG ITEM-ID SETS, AND FAIL THE PORT REPORT ON A GAP
    [drydocs / port — THIS IS NOW A CLOSING-SEQUENCE STEP] (`35e6d103`:
    `drydocs/port_backlog_union.py` + `scripts/port_backlog_union.py`. The manifest has
    promised "never drop a file" for `backlog/items/*.yaml` all along while every backlog
    guard read ONE copy, so an under-delivering port left both sides internally consistent
    and green. The id set is the DIRECTORY LISTING (ADR 0013 Clause 6), read on both sides
    by `backlog_store.load_items`, so the vacuous-green cases fail loud: a file path (the
    tombstone) is refused outright, and absent/empty dirs and filename-vs-inner-id
    mismatches are errors rather than agreement. `1a4460e4`: the pasted block is pure ASCII
    and guarded — PS 5.1 mojibakes non-ASCII console output, which the first live run
    reproduced, and a corrupted paste is a silently wrong port report.)
    APPLY: run it at THIS port's close and paste the block into your PORT-REPORT. The
    script rides IN this range, so unlike the `port-base-20260820` port you now have it.

209. G79 — `refresh-reference` SPLITS INTO THREE SUBJECT COMMANDS [drydocs / config —
    BEHAVIOUR CHANGE] (`680b9e90` (c) part 1: `cadence: weekly | batch | repo-change` sits
    on the SOURCE row beside `acquisition` — acquisition is HOW data arrives, cadence is HOW
    OFTEN; nine rows carry it, derived from the sequence rather than hand-listed.
    `3f97b3cc` (a)(b)(c)(e): one command per SUBJECT replacing a seven-loader tuple that
    spanned three sources with three rhythms and so had no organising principle — which is
    why a loader could fall out of it and nothing noticed. `refresh-catalog` (LOB → product
    line → product), `refresh-applications` (SEAL apps + contacts), `refresh-teams` (dev
    teams, team roles, team↔app alignment); `business_segments` re-homed to refresh-catalog
    as the precondition of the reconciliation it feeds. `93aa8060` makes the invariant and
    the cadence derivation falsifiable rather than asserted. `118e2cbf` the docstrings, plus
    Idea-160.)
    CAUTION: `refresh-reference` IS GONE by that name. Update your runbooks and any
    scheduled invocation in the same commit. And see step 191 — a SOURCE-mode
    `refresh-teams` resolves `pat_team_roles.csv`, which nothing yet emits; G78 fails by
    name before any write, so you will get a clear message, not a partial load.

210. G81 — DECLARED PATH ZONES, AND `DRYDOCS_DATA_ROOT` BECOMES MANDATORY [drydocs-core /
    cli — SEE RELAY-12] (`701e1d22` (a)(b)(c)(e): a reconstruction of the write-capable
    surface measured FOUR live overlaps — `controlm_xml_dir()` aimed exactly at a declared
    drop zone, `rua/extracted/` and `rua/incoming/` sitting inside the declared `rua/` read
    zone, and `source_dir()`, an arbitrary-parts create-capable helper whose no-argument
    form is the root itself. Declared zones with modes plus a non-overlap invariant now
    forbid the class. `52996cee` (d): `resolve_data_root()` RAISES when `DRYDOCS_DATA_ROOT`
    is unset — the old `~/data/DryDocs` fallback meant the same command in two shells
    targeted two different trees and reported success either way. `DEFAULT_DATA_ROOT`
    survives only as the location the error message suggests. `96404367`: the console script
    points at `drydocs.cli:run()` so this renders as a message and exit 2, not a traceback —
    `landing-zones` exists so "my extracts are gone" is a one-command answer, and a stack
    trace defeats it at the moment it matters. `fcf973b5`: the "declared-equals-resolved"
    guard the reconstruction CLAIMED did not exist for the YAML half — the check matched by
    NAME, so renaming a zone's path and leaving the code alone fired nothing while both
    guard layers keyed on the declaration. Now a test, proven to fire on injected drift.)
    APPLY: export `DRYDOCS_DATA_ROOT` before the first data-path command after this port, or
    it exits 2 by design. `drydocs --help` and the unit suite are unaffected. An existing
    install keeps the old console-script shim until `poetry install` — that costs error
    RENDERING only, never behaviour. RELAY-12 carries this and the `dpl-registry/`
    `drop_dir` correction; action it there.

211. CI — SINGLE PYTHON 3.12 AND CONCURRENCY CANCELLATION [.github — `evaluate`]
    (`e955fce5`: an Actions-minutes cost fix. The 3.11/3.12 matrix halves to the version
    both dev machines run — `pyproject`'s `^3.11` floor is now deliberately untested and a
    comment records that — and a newer push to the same ref cancels the superseded in-flight
    run. Deliberately NO `paths-ignore`: docs pushes keep full guard coverage, per Idea-111,
    because the guards that catch stale docs live in the same suite.)
    APPLY: `.github/**` is `evaluate` — keep your workflows and adapt. The `paths-ignore`
    reasoning is the transferable part; the runner economics are not ours to judge.

212. TWO `.gitignore` RULINGS, ONE OF WHICH CHANGES WHAT A PORT DELIVERS [repo hygiene]
    (`103f240c`: `docs/reviews/port-review-*` now stays MACHINE-LOCAL. A producer review of
    a COMPANY port transcribes another side's session — acceptance numbers, branch and tag
    names, item counts, the verified-vs-claimed split the format exists for — and
    `docs/reviews/**` is `default_ok`, so a tracked review PORTS BACK to the repo it is
    about. Both halves in one commit, because `.gitignore` alone never untracks:
    `git rm --cached docs/reviews/port-review-7c18ff4b-20260820.md`, which was already
    tracked and had already crossed at the 20260820 port. `3298c8ce`: `.fig` (Figma's binary
    save format) is ignored — nothing reads one, git cannot delta-compress it, and a
    committed copy is permanent.)
    APPLY — READ THIS BEFORE YOU DIFF: this range DELETES
    `docs/reviews/port-review-7c18ff4b-20260820.md` from the producer tree. That is a
    producer-side UNTRACKING, not a retraction of the review. If you took the file at the
    20260820 port, keep your copy; nothing about its content changed.

213. RIDER ON STEP 176 — `lob-product-team.yaml` GETS ITS PER-ENTRY ROW [PORT-MANIFEST]
    (`b9dd1191`: step 176 told you the file was per-entry while the manifest still let it
    fall to `config/**` wholesale — J51 path (7), found by the company session at the
    lull-port apply. The row now exists, above the `config/**` default, with the entry rule
    spelled out: your REAL LOB rows are estate data and stay, the producer's are the
    synthetic publishable sample and never overwrite them, and the producer-owned MECHANISM
    blocks — the header, `concept_scheme`, `open_questions` by id — cross whole.)
    APPLY: `PORT-MANIFEST.yaml` is canonical-producer; you take it wholesale and this row
    comes with it. This is a producer defect your side found and it is fixed — thank you.

214. THE `neo4j-skills` TRIM NOTE IS CORRECTED — 10 SKILLS, A MEASURED COST, AND A
    VERSION-SCOPED SYMPTOM [`CLAUDE.md` — canonical-producer] (`ba9540c7`). The routing
    table claimed 9 skills and an unmeasured token cost. `claude plugin details
    neo4j-skills` prints the projected always-on figure, so the note now quotes it (29
    shipped, 10 run) and lists `document-import` in the keep set, where it was already
    in use. The load-bearing correction is the SYMPTOM: on Claude Code 1.x a pruned
    directory left in the manifest killed the WHOLE plugin silently; on 2.1.241 that did
    not reproduce. Step 2 of the trim is required for CORRECTNESS, not as a guaranteed
    tripwire.
    APPLY: `CLAUDE.md` is canonical-producer and crosses wholesale. Keep the two-step
    trim procedure and the "any install/update reverts it" caution; the skill list
    itself is a producer venue fact.

215. THE G102 FOLD REACHED THE CODE AND NOT THE PROSE [docs / skills — read with
    RELAY-13] (`703c2019` the topology prose, `034a476d` Idea-165). Two retired database
    names survived the fold in the places an AGENT reads rather than a test: the topology
    documentation, and the `data-context-extractor` skill, which was still routing agents
    at both dead databases. Both fixed; the two mentions that remain sit inside a comment
    saying they retired.
    APPLY: RELAY-13 carries the company-side half of this fold and is the read that
    matters. These two are the producer's prose tail — they change no behaviour.

216. DESIGN-DOC RENDERER — A FENCED CODE BLOCK INSIDE A LIST ITEM IS A BLOCK, NOT PROSE
    [renderer] (`eb55853e`). `drydocs/design_doc.py` — the module, not the thin
    `scripts/render_design_doc.py` driver — treated a fence nested in a list item as
    prose and reflowed it; `tests/unit/test_doc_traceability_loader.py` pins it. Renders are deterministic and the HITL loop keys
    feedback anchors on them, so a reflowed block silently breaks re-attachment — the
    same class as the "governed renders publish VERBATIM" rule, arriving from the
    renderer side instead of the sharing side.
    APPLY: take it with the renderer, then re-render your design docs and expect a diff
    on any doc holding a fence inside a list. A diff there is the fix landing, not drift.

217. RUNBOOK MULTI-COMMAND BLOCKS GET ANNOTATED [docs/design — evaluate] (`c0b36116`;
    startup-refresh Rev 13, load Rev 3). A block of several commands under one heading
    reads as a single action; each command now says what it does and when it may be
    skipped. `tests/unit/test_doc_traceability_loader.py` moves with it.
    APPLY: `docs/design/**` is evaluate-on-collision and your runbooks name your venues.
    Take the annotation discipline; the command list is ours.

218. G104 — ADR 0014, THE RUNTIME SUBSTRATE [ADR — PROPOSED, not accepted] (`566b5fbd`).
    Log directory, log level and the data root get ONE decision record instead of three
    conventions discovered separately. Status is **Proposed**: it writes down the
    decision the tree is already living by so it can be argued with, not a ratified rule.
    The 0009 reconciliation is an exception 0009 already permits — read that clause
    before treating this as a conflict between two ADRs.
    APPLY: `docs/decisions/**` is `default_ok` — take or skip freely, never checkout;
    both sides may hold the same ADR number for different decisions.

219. G109 — `landing-zones` STOPS COVERING HALF THE ZONES, AND THE CONFLUENCE CAPTURE
    IS RULED OUT OF THE TREE [config / drydocs-core] (`f0f02fac` claim, `240accc9` the
    build). **The premise moved between grooming and build, and the sharper defect is
    what shipped — read this before you look for a registry change that is not there.**
    The item said six zones had no `source-registry` row, so `drydocs landing-zones
    --check` was blind to them. Post-G81 all six DO have a declaration — in
    `config/data-zones.yaml` — and the command was STILL blind, because it read only the
    registry. Duplicating them into the registry would have been wrong twice over:
    `data-zones.yaml`'s own header FAILS a zone that duplicates a registry row, and a
    WRITE zone has no provenance, trust axis or acquisition mode, so its row would be
    nulls asserting a source that does not exist. The READ SURFACE is what changed:
    `landing-zones` now reports both declarations (26 zones, was 15) and `--check` is
    MODE-AWARE — an empty read zone fails, an empty write zone does not, because failing
    on an output directory the system rebuilds trains the operator to ignore the exit
    code. `.env.example` gains `DRYDOCS_LOGDIR` (G81 had already added the data root),
    and two of the five clauses were already satisfied by G81 — recorded as OVERTAKEN,
    acceptance text untouched, not re-done.
    **RULED (clause e): the `cdo-frameworks` Confluence capture MOVES; it gets no
    exception.** It had landed in-tree untracked AND not gitignored — the one category
    `git clean -fd` removes without `-x`. An in-tree zone is permitted only when TRACKED,
    and PUBLISH-BOUNDARY forbids ever tracking a verbatim capture carrying real names and
    internal URLs, so an exception could never expire where a ruling can.
    APPLY: reads with RELAY-12 (G81 made the data root mandatory). Nothing here REFUSES
    anything new — the command sees more, it rejects no more — so a company-only zone
    keeps working; it simply stays invisible to `--check` until it has a
    `config/data-zones.yaml` declaration. One deliberate non-change worth keeping: the
    doc-source row's historical `source:` path is left as written, because falsifying a
    provenance record to match a later ruling is the one thing a VERBATIM row may not do.

220. DOC 08 PHASE 2 — psgmgr CENSUSED 7/7, AND `CM_DEF_VJOB` IS A TABLE
    [config / TEST-PINNED] (`a8188d3a`). The column ledger stood 1/7 censused since
    2026-07-22; an internal session ran the read-only catalog census on the other six and
    the results are transcribed here. Every object now carries `census: complete`, a real
    `column_count`, a `profiled_on`, and a frozen `count:` on its `default_disposition`,
    so `census_failures()` reconciles explicit rows + swept count == `column_count`
    across all seven. `tests/unit/test_source_mappings.py` no longer pins the censused
    set to one name: a NEW object arrives `pending` and fails there until its census
    lands. ONE MODEL CORRECTION — `CM_DEF_VJOB` is `kind: table`, not `view`; the family
    name misleads exactly the way `CM_DEF_VTAB` does.
    APPLY — EXPECT A CONFLICT AND MERGE THE WORDING, NOT THE NUMBERS: your side edited
    the same ledger blocks the same day and the counts agree; only the prose differs. And
    keep the two classes apart — a census is COLUMN INVENTORY. Row and distinct counts
    are a different class and must never be written into `census` / `column_count`, or
    `census_failures()` starts passing on a reconciliation it never performed.

221. ADR 0014 RULED — RUNTIME SUBSTRATE ACCEPTED WITH FOUR AMENDMENTS, AND "EVERYTHING
    CONFIGURABLE, NOT HARDCODE" IS THE RECORDED PRINCIPLE [docs / decisions]
    (`6abc1359` the Idea-171 capture, `413b9186` the acceptance, `ecf8ab17` the
    G106/G108 rulings folded + Idea-172). The ADR drafted at step 218 is ACCEPTED
    2026-08-25 as an EXCEPTION ADR 0009 already permits (rule 1's own scope clause —
    no SME gates a log directory, no port carries one, no classification test guards
    one). Amendments: clause 1 per-KIND in `config/log-kinds.yaml`; clause 3 the naming
    rule DERIVES (the drafted rule matched 5 of 86 real files); clause 4 `prune-logs`
    reads retention from the declaration; clauses 5/6 — `drydocs_api` is OUT of clause
    5 (it has no batches) and the audit line WIDENS to routes that write. G106/G108
    carry the retention rulings as acceptance riders: `api` audit 90 days no Cypher
    text, `api-debug` a SEPARATE kind (verbose, short, carries Cypher), verbose is
    settings-level, and a CORRELATION id is required (the QA ledger holds question
    text, the audit holds route+outcome, nothing joined them).
    APPLY — record-only for you: your gates are your own, but the README row and the
    ADR's "What the ruling changed" section are the authority the G105/G107 code
    steps below build against.

222. G107 — ONE SHARED BATCH RUN LOG, WIRED INTO THE THREE COMPONENTS THAT HAVE
    BATCHES [drydocs-core / components] (`26ade9f4`). `batch_run_log()` context
    manager in `drydocs_core/run_log.py` — open, capture, re-raise, close in finally,
    an unwritable log dir swallowed (a run log is never the reason a batch fails).
    Wired by rename-plus-wrapper: lineage `write_curated`/`write_rua`, docmeta's two
    connectors (fetch stays the PUBLIC name — the Connector protocol is guarded), the
    vendor scrape's `capture`. THE CITED PRECEDENT DID NOT EXIST — G93 is still todo,
    so remediation logs nothing; G93 gained a rider to use this helper. DEEPDOC IS
    REFUSED, NOT SKIPPED: it is a scaffold until MM10 and both entry points raise on
    line one. 12 new guards, both paths per component.
    APPLY — your `drydocs_remediation` is the live one: when you take G93, use
    `batch_run_log`, never a hand-rolled block.

223. G105 — LOG KINDS ARE DECLARED, THE NAMING RULE DERIVES FROM THEM, dictConfig
    REPLACES basicConfig [drydocs-core / config] (`3ec2c436`). NEW
    `config/log-kinds.yaml` (schema drydocs.log-kinds.v1) + reader
    `drydocs_core/log_kinds.py` on the data-zones idiom. Six kinds: load/sql/cli/qa
    active, api/api-debug `planned` for G108. `claim_log_path` parses `<kind>.<name>`
    and REFUSES an undeclared kind; the SQL family gains the `sql.` segment it never
    had (it wrote `oracle.<ts>.log`); the per-day `qa` ledger is CONFORMING, not
    excepted. `RuntimeSettings` joins config.py; `cli.py`'s one `basicConfig` becomes
    `configure_logging()` (stdlib dictConfig, `--verbose` still wins); four components
    gain module loggers; graph_qa's telemetry swallow now WARNS (the swallow itself is
    unchanged and right). The legacy log env var resolves one more cycle WITH a
    DeprecationWarning — **the drop trigger is THIS port landing on your side.**
    APPLY — read `config/log-kinds.yaml` + `.env.example` first; your two company-only
    supplements precedent applies if you carry company-only log kinds: add them to
    YOUR declaration before adopting the refusal path.

224. R23 — THE ASK CONTROL TOKEN STOPS REACHING THE SESSION STORE, AND BOTH MACHINES'
    STORES ARE ACCOUNTED FOR [agents] (`bd0cd2dd` the fix, `26b0ce79` the handoff,
    `7e478283` the desktop purge record). The R5 control part carried the browser's
    api_token into ADK session events verbatim; the fix redacts it before the store
    (`agents/common/session_redaction.py` + guards). Producer stores: laptop checked
    clean at the fix; desktop confirmed 10 token-bearing events and PURGED 2026-08-25
    (J18 — machine named because an untagged "purged" reads as both). `.adk/` is
    gitignored; nothing ever reached either repo.
    APPLY — code applies by manifest. YOUR action: check your own `.adk/session.db`
    for `api_token` in events and purge if present; the tokens are replayable for the
    life of the API process.

225. DOC 08 PHASE 2 RELAY — THE CM_ESCALATION_DB CENSUS LANDS ON THE SIDE THE PORT
    CARRIES FROM [config / registry] (`6ea0b3d7` the census, `ede62d44` the internal
    `[db]` key, `0786cd41` the hand prompt). The escalation-table census (7/7 columns)
    is transcribed onto the PRODUCER's registry row — the canonical-producer side —
    so it survives ports instead of being overwritten with your local copy; the
    `[db]` placeholder finally has a machine-local key (`internal/standards/
    technology/database-inventory.md`, does NOT cross). The hand prompt
    (`escalation-census-company-prompt.md`, delivered by hand and executed 2026-08-25, then retired producer-side) told your side the
    census note there is temporary.
    APPLY — expect your census note on the old row to be superseded by this file
    arriving; your ledger already records that expectation.

226. THE REDACTED DATABASE ALIAS STOPS BEING PUBLISHED, AND SCAN D GUARDS IT
    [boundary / tests] (`f22da676` the sanitization + guard, `92115bf3` the hand
    prompt). SME ruling 2026-08-25: the token is an ALIAS, not a SID, and is still
    not published. Three producer prose leaks sanitized (the reconcile-port skill's
    tnsnames caution now names NO alias; PORT-MANIFEST + the steps-1-42 archive now
    say `psgmgr §7f` — the SCHEMA, which the signed grammar KEEPS, gate-log:2971).
    NEW Scan D in `tests/unit/test_publish_boundary_values.py`: sha256-pinned (the
    guard never writes the token), trailing-underscore allowance for the deprecated
    env prefix, proven to fire on injected drift.
    APPLY — **READ the range's hand prompt §3 (delivered by hand 2026-08-25;
    `catalog-sublob-and-db-alias-company-prompt.md`, in the range at the tag and on
    your side already) BEFORE taking `tests/**` from this range.** Scan D fails on your ten alias ids
    until your `[db]` revert lands; tests/** is evaluate-on-collision, so taking it
    red or after the revert is YOUR sequencing call — just make it deliberately.

227. C27 — THE SUB-LOB LABEL IS `CatalogSubLOB` (SME, OPTION 1), AND THE C26
    RESERVATIONS RETIRE [ontology / map] (`32f8f7b0`). The one catalog question your
    2026-08-06 gate reversal did not reach: the same label split one level down.
    RULED CatalogSubLOB; your side has ALREADY EXECUTED the relabel (Option 1 run
    2026-08-25, suite 2420 green — this step is the producer record catching up, not
    an instruction). Producer vocab entries STAY `planned` (no producer Sub-LoB grain,
    no capture, no loader — flips are follow-ups); the C26 map-id reservations move to
    `rejected` with `superseded_by` for naming ids nobody mints (you built
    `lob-has-sub-lob`/`sub-lob-has-product-line` and KEPT `lob-reconciles-to-segment`);
    your two real ids are recorded as names the producer must not mint. The
    reconcile-port divergence ledger items 3/4 are rewritten — label settled BOTH
    levels, do not re-open either as a divergence to preserve.
    APPLY — the map fragment merge is per-entry; your active entries survive by rule.
    Your two deliberate leftovers (review-labels spine, TDD prose) are yours to
    schedule and are recorded as such.

228. THE PUBLIC BUSINESS GLOSSARY GROWS BY 119 CANDIDATE TERMS [config —
    canonical-producer] (`af5f84a6` 110 terms, `edd9ee06` +4, `29a5ce71` +5 and one
    upgrade). `config/glossary/terms-public.yaml` (schema `drydocs.glossary.v1`, the
    G34 scaffold) is filled from a PUBLIC External source — the JPMorgan Chase annual
    report glossaries — extracted mechanically, three passes: the 2025 glossary
    wholesale, then a 2024 CCB home-and-auto lending sweep (TDR, UPB, GSE, FICO), then
    Credit Cards (GPCC) plus four mid-line entries the first anchor-based extraction
    missed (FDM, GAAP, LTD, VaR) and a GSE upgrade to the formal definition.
    EVERY sense is `confidence: candidate` and NOTHING is SME-confirmed — a candidate
    is a starting point for decoding a token, never an assertion about what a DryDocs
    surface means. Org-unit acronyms carry `scope: business-domain`, the rest
    `industry`. The source PDF is local and gitignored; each citation names the public
    DOCUMENT, never the file (the no-image-provenance discipline, applied to PDFs).
    APPLY: a clean take. Nothing reads this file yet — it is a decode aid for humans
    and a future term_id source; your company-specific senses belong in
    `internal/glossary/terms.yaml`, which this never touches.

229. FOUR SME GATE PROMPTS DRAFTED, ALL UNSIGNED, ALL DECIDING NOTHING [gate-prompts —
    canonical-company, and these are clean-adds] (`14c8c12f` C28
    business-layer-org-structure, `285034a0` G61 script-provenance-gaps, `8cb80d09`
    G95 standard-identity-and-carrier, `74670d8f` K20 tech-partner-attach-level).
    Read the manifest row before reacting to the count: `config/gate-prompts/**` is
    canonical-company — YOUR real specs win — and its note carves out exactly this
    case, "new producer specs that don't collide are clean-adds". None of the four
    collides. Each ships with a gate-log RECORD stub marked DRAFTED/unsigned, and J43's
    reconcile check treats a DRAFTED stub as NON-AUTHORITY: no vocabulary status may
    cite these headings, and none does. Subjects: C28 builds on the signed G98 rather
    than re-asking it; G61 §B2 ratifies a boundary G97 already operates (below);
    G95 prices three carriers for a standard identity and pre-picks none; K20 is an
    AMENDMENT gate re-opening one clause of the signed K5 (Tech Partner at product vs
    area-product level) on the G35 model. APPLY: take all four as files if you want the
    text; run none of them — a producer draft is not a company gate, and your side runs
    its own sessions on its own tracker.

230. G56 — THE COLLECTOR CAPTURES THE MOUNT TABLE, SO SHARED-VS-LOCAL STORAGE IS
    DERIVED [lineage — bundle schema v3] (`6fd395fb`). A deployment path may be SHARED,
    and then the same path on N hosts is ONE FILE SEEN N TIMES, not N deployments — a
    fact no section of the bundle could answer until now (the rua-load-shapes
    D-amendment). Collector emits `mounts.tsv` UNCONDITIONALLY (`findmnt -rn -o
    SOURCE,TARGET,FSTYPE,OPTIONS`, `/proc/mounts` fallback, `meta.txt` records which
    answered) — read-only and instant, so "optional" is the INGEST contract, not a
    config knob. Deliberately NOT `lsblk` (an NFS spec is not a block device, so a
    shared mount never appears) and NOT `fstab` alone (configured intent, not actual
    state). Extractor dispatches on PRESENCE, never on the `schema=` tag, so v1 and v2
    bundles come out byte-identical; each path resolves against the LONGEST matching
    mount target and `storage_scope` derives from fstype using exactly the amendment's
    set — an unlisted fstype is `unknown`, counted and NAMED, never guessed either way.
    APPLY: your collectors run on your hosts, so the value is yours to realise — re-run
    the collector to get v3 bundles; existing bundles keep working unchanged, which is
    the point of the presence dispatch.

231. G97 — LAUNCHER AND PAYLOAD STOP SHARING THE `INVOKES` FOLD [lineage + a migration]
    (`949b3b71`). The writer now emits `USES_ARTIFACT` to the PAYLOAD a launcher
    dispatches, `INVOKES` keeps the launcher, and `:Script` gains `script_role
    {launcher, payload}` plus the SME-3 artifact properties. Builds what two SIGNED
    gates already ruled; nothing is reopened, no vocabulary entry edited. THE ONE
    COLLISION IS WORTH YOUR ATTENTION because reading the rulings changed the answer:
    the item read as if `USES_ARTIFACT` takes the Script|ETLProcess union — it does
    not. `rua-load-shapes` B2 widened `scheduler_invokes` ONLY, and `cmdline-nfr-vetting`
    SME-2 ruled m7 as ControlMJob->Script{payload}, which the live vocabulary entry
    still says. So an Ab Initio pset or DPL pipeline reached THROUGH a launcher STAYS
    on `INVOKES`, counted as its own bucket and never as "unclassified" — the reason is
    a ruling, not missing evidence. The split is minted at EXTRACTION because three
    things forbid a writer-only variant (`add_rel` refuses labels outside `REL_TYPES`;
    `plan_curated` enforces confirmed <= graph.rels; `script_role` on both endpoints
    needs a launcher node the extractor never minted).
    APPLY: `drydocs/loaders/cypher/migrate_payload_invokes_to_uses_artifact_g97.cypher`
    ships with it — run it against any graph already carrying folded INVOKES edges, and
    read it before you do: it is the only file here that touches loaded data.

232. G92 — THE JOB'S SCOPE CHAIN RESOLVES BEFORE THE FILE-OP PARSE [lineage]
    (`30c7fb7e`). A job whose POSTCMD moves `%%R_PATH/out.dat` and a job whose CMD_LINE
    moves `/data/r/out.dat` planned edges to TWO DataAsset nodes for ONE file, because
    `_file_op` keyed the asset off the verbatim operand. BOTH passes had the defect;
    pre/post only made it visible, because that is where variable forms concentrate.
    A feed change, not a new parser and not a new resolver: the chain is built once per
    run before the jobs pass, and shell text goes through `resolve_command_line` — the
    one core resolver whose stated guardrail is that no caller may re-implement
    substitution, now pinned by a test asserting this module imports no regex engine.
    Raw stays BESIDE resolved (the G46 derived-fact shape): the asset keys on the
    resolved location and every distinct raw spelling ACCUMULATES in `raw_operands` —
    accumulated, not first-seen, because two jobs spelling one path two ways is exactly
    the evidence that makes a wrong binding findable. `{ODATE}`-class residue is
    EXPECTED and counted apart from a real miss; an unresolved user ref is counted AND
    still stages on its raw spelling. APPLY: like-for-like. Expect your DataAsset counts
    to FALL on the next inventory run — that is the duplicate collapsing, not data loss,
    and the five new resolve counters on the coverage summary line are how you show it.

233. G68 — THE FOLDER-SET PROFILE, PLUS THE SLOTS ONLY AN SME CAN FILL [remediation —
    canonical-producer] (`783f754d`). The READ half of the remediation loop: five
    censuses report what the export SAYS, and a substitution-slot list names what it
    does NOT carry. That division — the machine reports what IS, the SME supplies what
    is NOT THERE — is what keeps this out of the guessing that produced the drift C32
    documents. Transport is NAMED rather than defaulted: a CLI verb writing a JSON
    artifact, and the cost against ADR 0005 is NIL rather than merely acceptable —
    that ADR governs the browser-to-Neo4j path, this reads no graph and writes none.
    The verb lives in `drydocs/cli.py` deliberately (a new `cli_remediation` module
    would be a component importing a component; the composition root is the only exempt
    module and S8 adds no new exemption — `lineage-review` and `fid-census` already sit
    there). Census (b) reports `run_as` BY JOB TYPE, honouring the 2026-08-19 SME
    evidence rider: a FileWatcher on the platform account beside payload jobs on the
    application account is the DESIGNED pattern, and flattening it reads as "two
    accounts". APPLY: producer mechanism, your values — rule VALUES stay company-side
    and never flow back (the `drydocs_remediation/**` row says so).

234. G69 — R41-R44 REGISTERED AND DETECTED IN THE SAME CHANGE, AND ONE SHIPS WITHOUT A
    DETECTOR ON PURPOSE [remediation + `internal/remediation/**`] (`49202a88`). The
    PAIRING is the item: the registry is the single source for both gates, so a
    detector with no entry emits findings nothing can rank, nothing can turn into a fix
    and nothing can sign off on — the entry is the thing that gets ratified. R41
    must-fix names the ORDINAL ACCIDENT, which is what justifies the severity, and
    walks the RAW layers (a test pins that: `_declared` resolves into a dict and would
    make the rule unable to fire). R42 should-fix, cross-folder: mixed separators do
    not make a split FAIL, they make it return a different field count, so the
    positional read silently lands on the wrong field. R44 advisory with its limit in
    the message. R43 SHIPS REGISTERED WITH NO DETECTOR on evidence rather than
    convenience: the carrier-ownership question was searched for — governance corpus,
    guidelines page, gate prompts — and nothing rules shell-vs-Control-M ownership, so
    a detector firing against an undecided rule would put a finding in front of an SME
    with no defensible action attached. Its entry also records what it is NOT (R33 is
    one FACT on two carriers; R43 is one NAME on two resolvers).
    APPLY: R43 is a live question for YOUR governance side — if your standards own the
    answer, rule it and the detector is a small build.

235. G108 — THE FIRST AUDIT RECORD OF WHO ASKED THE GRAPH FOR WHAT [api + config —
    two log kinds go active] (`cf7fac1c`). `drydocs_api` logged NOTHING. Now every
    route that executes Cypher OR writes — twelve, enumerated in
    `drydocs_api/audit.py`'s docstring with the exclusions stated — leaves one lean
    line in the `api` kind (90-day metrics window, actor sha256-hashed the `:AgentRun`
    way, NEVER Cypher text, NEVER result values), plus optionally a verbose line in
    `api-debug` when THAT kind's declaration says `level: DEBUG` (ADR 0014 ruling C:
    settings-level, never per-request; Cypher bounded at 20k with a truncated flag).
    Ruling D wired end to end: `X-DryDocs-Run-Id` joins the audit line to the QA
    ledger's `run_id` — `ephemeral_client` sends it, `agent.py` closes it over
    `make_register` so `register_cypher`'s signature and every fake are unchanged;
    fallback is the hashed session token and `correlation_source` says which won.
    Both kinds flip planned->active WITH their writer named (`test_log_kinds` pins the
    flip). APPLY: reads with steps 221-223 (ADR 0014, G105 log kinds, G107 batch run
    log) — if you took those, this is the first consumer of the declaration. The
    retention numbers are DOMAIN facts in `config/log-kinds.yaml`, so a different
    company window is a config edit, not a code change.

236. G70 — THE TOM ROLE VOCABULARY BECOMES DATA: ONE UNIT, SIXTEEN CLASSES [ontology +
    a migration] (`4f28010d`). The G35 §A8 finding ends here. The role vocabulary lived
    HARDCODED across four surfaces in three languages (enum, alias map, Cypher CASE,
    scheme seed) and the only YAML copy was read by no code — it drifted TWICE inside
    one gate with the suite green. Now `config/taxonomy/tom-role-vocabulary.yaml` is the
    one declared surface, `drydocs_core/ontology/tom_role_vocabulary.py` reads it, and
    SEVENTEEN drift guards force every other surface to defer. Seeded from the SIGNED
    §G register: 7 required + 9 optional, the §G9 Operate Manager split (level property
    retired), both SRE rows derived, Risk Manager crosswalked to
    `technology_risk_controls` and stopped, retirement as an ACTIVE FLAG (§F6b),
    cardinality recorded once on the scheme (§B3). `SealRole` is retired AS THE
    ADMISSION GATE — an undeclared name loads FLAGGED, never dies at validation, so the
    four classes §A1d measured as silently lost now load; the raw source string survives
    verbatim beside the canonical (§A4b), retiring §A6c's accepted risk.
    `business-application.yaml`'s roles register is DELETED; the memberships stay as the
    sample, guarded against the declaration. APPLY: this is the largest behaviour change
    in the range and it ships with
    `drydocs/loaders/cypher/migrate_tom_role_split_g70.cypher`. Read it before running:
    the Operate Manager split changes role identity on loaded rows. If your side already
    diverged on role names, the declaration file is the ONE place to reconcile — that is
    the whole point of the change.

237. K22 — THE DEPLOYMENT MODULE CI PROPOSAL, DRAFTED AS A RIDER AND REGISTERED PLANNED
    [ontology — nothing loads] (`a7ee9239`). A `G0d-RIDER` on
    `tom-roles-enumeration-and-cardinality` (beside the signed §G0d, which already owns
    the subject — L25: riders, not edits) carrying five ruled things in order: the
    not-reopened fence, the CI-id-IS-the-business-key rule with the
    composite-name-as-key refusal, the SME's topology verbatim, the C10
    own-stable-name call (`:DeploymentModule`) with the twice-proven
    label-is-not-identity evidence, and the correction scoping the form-default finding
    to transactional records while the CI itself is real. Registered `planned` ONLY —
    the `:DeploymentModule` node class (PROPOSED) and
    `business_application_instantiates_deployment_module`; nothing loads, nothing flips
    active, attribution stays on `:BusinessApplication`.
    APPLY: informational. The rider is text on a gate page your side may hold its own
    copy of (canonical-company); take the vocabulary entries as planned rows or not —
    they write nothing either way.

238. K25 — THE CROSS-APPLICATION `run_as` DETECTOR, CLASS-FIRST AND PER-JOB, WITH A
    RUNNER THAT IS YOURS TO EXECUTE [review — and see RELAY-16] (`16c5ec2d`).
    `drydocs/run_as_detect.py` is `fid_census`'s sibling with the same discipline end to
    end: pure, injected, counts-only by return type. First cut is run_as CLASS
    (platform_user / application_fid / unresolvable — the 2026-08-19 SME clarification),
    per JOB and never per folder; the fixture reproduces the live IN-FOLDER split a
    folder-grain read would miss. FileWatcher x platform is the DESIGNED pattern; a
    payload job on the platform account is the countable anomaly. Platform-class jobs
    are counted and EXCLUDED from the directory comparison; how a platform account is
    recognized stays K17's ruling — the injected set is the seam, doc 09's S3 ranking
    the evidence-backed proposal. The §G5 split parks at CASE grain until a human rules
    each; unresolvable is counted by reason; case near-misses are reported on both joins
    and never folded. Nothing touches the graph.
    APPLY: the detector ports (`drydocs/**` default) — the DATA does not, and cannot.
    RELAY-16 carries the ask.

239. J39+J40+J43+J52 — THE RELEASE-INFRASTRUCTURE CLOSE-OUT BATCH [port machinery + one
    SQL alias] (`155916e3`, format follow-up `cc38238a`). Four items, one commit,
    every one of them about the port boundary itself. J43: manifest rows that carry
    ontology/map fragments gain `gate_bound: config/gate-log.md`, and a new
    `unsigned_activations()` reconcile check FAILS a reconcile that flips a vocabulary
    entry to an ACTIVE status without a SIGNED gate-log section citing it — DRAFTED
    stubs are explicitly not authority (step 229 depends on this). The same item adds
    the `derived` DISPOSITION to the manifest legend and moves all six render rows
    (board, roadmap, ideas, load-map, both TDD renders) onto it: take NEITHER side's
    copy, REGENERATE from the reconciled tree — the naming gap your send-back had
    already inboxed. J40: docmeta divergence decisions recorded (ADR numbers matched by
    title-and-side, package-path convergence deferred to the adoption pass,
    `prompts.py`/`pipeline.py` flagged as back-flow candidates with protective rows).
    J39: six consolidated dispositions, of which ONE reached code — the header-row join
    in `drydocs/loaders/sql/controlm_folders.sql` is re-aliased `H` -> `J` to match your
    copy, back-flowed mechanism-only so the two sides' file stops carrying a permanent
    cosmetic diff (two alias pins moved with it). J52: the verify skill gains a
    dev-server VENUE rule — a session may observe only a browser it launched, and an
    observation is cited as an observation. `cc38238a` is CI catching a `ruff format`
    gate I skipped by running a test subset; it is the fix, not a second change.
    APPLY: the manifest and the reconcile guards are the files your apply reads — take
    them first, then re-run your reconcile, because `unsigned_activations()` is new and
    may have something to say about entries already in your tree.

240. PRODUCER-SIDE PORT HOUSEKEEPING — SIX RETIREMENTS, ONE MANIFEST ROW, ONE DOC FOLD
    [never-port + docs] (`a796d13d`, `4a7f8a9c`, `5b67bcb4`, `26ddde09`, `00329469`,
    `c622b1e9`). Cited rather than exempted because two of them touch files your apply
    reads. The retirements: the sub-LoB/alias hand prompt (delivered by hand and
    executed your side), four consumed delivery packs (each moved with its execution
    evidence), and the 2026-07-16 internal-session checklist — 7 of its 9 items were
    owned elsewhere and the 2 ORPHANS WERE RE-HOMED FIRST, which is the whole rule for
    retiring a checklist. All land in `internal-local/archive/`, machine-local.
    `26ddde09` is the consequence and the lesson: deleting the checklist left a
    `PORT-MANIFEST.yaml` row matching nothing, CI caught it, and the fix is a
    `row_may_match_nothing` entry — a subset test run is not the suite, which is the
    second time that has cost a red build in this range. `00329469` folds a Mermaid
    diagram into the doc that described it and drops `image-2.md` (a screenshot-derived
    filename for a transcribed diagram); `c622b1e9` mints S14, which will relocate
    `docs/Product/` to `knowledge/org/` after K20 — NOT done in this range, so the
    paths cited by step 229's K20 prompt are still current.
    APPLY: nothing to do; the manifest row is the only line that changes behaviour.

LEDGER COVERAGE FOOTNOTE (2026-08-26 ROLL) — ritual commits in the
`port-base-20260825..HEAD` extension, cited because the coverage check reads ONLY
this section. DEPGRAPH SNAPSHOTS written `chore(snapshot):` instead of
`chore(depgraph): snapshot` — the fourth through eighth instances of the same
subject-line variant, still listed rather than fixed by loosening the pattern:
`219fbf3d` `8a619377` `823d1427` `961dff15` `267d325c`. HANDOFF ROLL — `a8a6cadf`,
`docs/next-session-handoff.md` plus the R23 desktop close: producer session state,
never-port.

LEDGER COVERAGE FOOTNOTE (2026-08-25 ROLL) — ritual commits in the
`dd71116e..HEAD` extension, cited because the coverage check reads ONLY this
section: `735c0ef3` `1ebc0088` (depgraph snapshots), `65fdcdcc` `e232d684`
`def4727f` `1b5a27a2` (claim flips for C27/G105/G107/R23 — the work is steps
221-227), plus the roll commit itself under the narrow roll exemption.

LEDGER COVERAGE FOOTNOTE (2026-08-19) — ritual and self-referential commits in
this range, cited here because the coverage check reads ONLY this section:
`30e2b9bb` `e0ae9bab` `3643c36f` (the Q9/Q10/Q11 batch-claim/close/next_ready
backlog flips; the work is step 165), `8c84adef` (the PR #7 merge; content at
step 161), `f21b3e3a` `6e7735bd` `f1d777bc` (summary-block merge resolutions,
recompute-from-items each), `3680e9a3` `04f92515` `c82648d7` (the ledger roll,
its step-170 restatement, and the first coverage addendum — all three used
docs(port) subjects, which the termination exemption deliberately does not
match; the terminating write is the chore(port) commit that adds this footnote);
`9dda538e` `be0c39ae` `7c6eb730` `991d59e6` (the RELAY-10/RELAY-11 writes and
riders — self-documenting, their payload IS the relay text in the STANDING
RELAYS section); `47b08085` `2cad34fb` (the PR #6 merge and the id-space
branch's merge-from-main; content at steps 169 and 160 respectively);
`74491c32` `4b7b0f9a` `c264fc33` (the PR #3/#4/#5 merges — content at
step 169's README/venv note, S12 drift guard, and G101 respectively).

LEDGER COVERAGE FOOTNOTE (2026-08-24) — ritual and self-referential commits in the
`port-base-20260820..HEAD` range, cited here because the coverage check reads ONLY
this section. 42 more were exempt by SUBJECT and needed no citation; these are the
ones whose subject line does not match a ritual pattern, grouped by why.
BACKLOG CLAIMS that did not use the `chore(backlog): claim` subject — the flip is
one `status:` key and carries no apply content: `bdca9927` `af676699` `f7964d61`
`46ae572f` `eafba5a7` `a25dc9b2` `d4915e66` `0a544396` `37e342b0` `e235b592`
`bba047a6` `dd1defd3` `f6b45701` `9e0c05cb` `ff22f527` `55c1f958` `6a94c19e`
`66106a08` `c93aaf4f` `a0dc400d` `70e75a86` `83123f36` `febccf44` `4f3ead03`
`b1f94511` `3cbf49c5` `65f8c836`. (Worth one line rather than a silent exemption:
the ritual patterns match `chore(backlog): claim`, and a session that writes
`chore(G77): claim` instead gets no exemption and lands in the UNCITED list. That
is the guard being narrow on purpose — matching `chore(*): claim` at large would
let a substantive commit hide behind the word — so the cost is this list, not a
loosened rule.)
BACKLOG CLOSE NOTES AND ITEM EDITS, same reasoning, status and notes only:
`12d39779` (O64–O67 done) `5857709e` (G79 done + Idea-159) `db2d96b8` (G81 done)
`74c3b985` `6cff472a` (O63 raised, then widened) `aaf5711d` (the ui-workstream
findings landed on main — R18 evidence, O62, two ideas renumbered past a collision).
BACKLOG YAML REPAIRS — the same defect twice, a raw newline inside a block scalar
breaking the item parse and the board render with it: `1b01c893` (J49's note)
`9a12569f` (U25's note).
IDEA CAPTURES — `docs/restructure/IDEAS.md` is `union-append`; an inbox entry is
not apply content: `6e68bdb1` (Idea-150) `c1cc8119` (the header still routed
grooming at the `backlog.yaml` tombstone) `7a48897c` (Idea-151) `46ac411d`
(Idea-152) `d6f40b1b` (Idea-154) `a25041e7` (Idea-161/162, the wave-2 blocker list
and the DD-band occupation).
DEPGRAPH SNAPSHOTS written with a `chore(snapshot):` subject instead of
`chore(depgraph): snapshot`: `61ab0f7c` `eb254002`.
HANDOFF ROLLS — `docs/next-session-handoff.md`, producer session state, never-port:
`b06cbb5d` `f46b9cec`.
MERGE COMMITS, content cited at the steps named: `b07d3a3b` `c583b761` (the
ui-workstream branch — content at steps 178/179), `fab69606` `bc002e07` (the S9 docs
hygiene branch — content at step 177), `de5506d3` (G79 — step 209), `ebea0e34`
(G81 — step 210).
SELF-DOCUMENTING — their payload IS text in this file or in a `never-port`
company prompt, so citing them at a step would restate the file inside itself:
`2adcd98a` (wrote step 177), `c78ab18f` `11229bbd` (defined "retire" for your
`port-prompt.md`, then dropped a push-URL note that was wrong — the guardrail is
physical), `4a42b659` `c733ae29` (the wave-1 handoff and the
`port-213e1d12-followup-company-prompt.md` hand prompt, both
`docs/company-prompts/**`, which is `never-port`).
ADDENDUM (same day, after the roll): `3b4d8e76` — step 212's citation of
`docs/reviews/port-review-7c18ff4b-20260820.md` resolved on this laptop, where the
untracked file still sits on disk, and NOT in a fresh clone; CI caught it at the roll
commit. The path is now a `HISTORICAL_PATHS` entry in
`tests/unit/test_runbook_currency.py` with its reason. Cited here rather than given a
step because it repairs this file's own coverage, and the terminating write is the
`chore(port): ledger` commit that adds this line.
LEDGER COVERAGE FOOTNOTE (2026-08-24, SECOND ROLL) — the `68b53716..HEAD` extension,
cited here because the coverage check reads ONLY this section.
IDEA CAPTURES — `docs/restructure/IDEAS.md` is `union-append` and an inbox entry is not
apply content. The three carrying a COMPANY action were PROMOTED TO RELAYS rather than
left in the inbox, which your repo never reads (RELAY-14 from Idea-170; RELAY-15 from
Idea-168 + Idea-169): `d222290e` (Idea-161 closed — the first wave-2 certification),
`ee1d905d` (Idea-163, a desktop-local `v0.3.0` tag pointing into orphaned history),
`870c9799` (the two findings the topology sweep deliberately left open), `21cc11c3`
(Idea-166 + Idea-167), `8570bbc2` (Idea-168), `865fde12` (Idea-169), `264748b8`
(Idea-170).
SELF-DOCUMENTING — `1598c3e4` WROTE RELAY-13; its payload IS the relay text in the
STANDING RELAYS section above, so a step would restate the file inside itself.
HANDOFF ROLL — `e8dc2c3c`, `docs/next-session-handoff.md`: producer session state,
never-port.
DEPGRAPH SNAPSHOT written `chore(snapshot):` instead of `chore(depgraph): snapshot` —
the third instance of the same subject-line variant, listed rather than fixed by
loosening the pattern: `28c1181a`.
241. Z5 + Z7 — THE LOCATION MAP MODULE AND THE FIXTURE INTERLOCK [like-for-like,
    canonical-producer] (`94157ba0` the module, `ae740be5` the synthetic-city fix,
    `1a9668af` Z7, `8b9a431e` + `4b71fb19` the fixture finding and its correction).
    A reusable world/country map console module that renders ANY located label, not a
    one-off page. The finding is worth more than the code: the Z1/Z3 and Z5 sample
    fixtures were each built correctly and never interlock, so the bundled demo lights
    up no single dimension end to end. `4b71fb19` corrects the first reading — the T1
    tier IS proven by the e2e; it is the fixtures that do not meet.

242. THE /mappings CONSOLE PASS [like-for-like, canonical-producer] (`5e72eaf1` domain
    strip, `4a51fc14` the registry delete, `d7e70ec7` the pane fix, `6d5b027e` grid
    filter/sort/resize/CSV, `d22b3328` the Ask Copy button, `c19f118a` the React icon).
    `4a51fc14` is marked `!` and means it: the retired job-application mapping domain is
    DELETED from the registry, not hidden. Check your side for callers before taking it.
    `d7e70ec7` is the honest one — 44 rows were being shown four at a time.

243. O68 — ACRONYMS GET A REAL SURFACE [like-for-like, canonical-producer] (`1042ca96`
    the item, `6b43c850` the build, `7ef523d1` a CI-line correction in the done note).
    An add path that produces an ARTIFACT rather than a silent write, and provenance
    stops living in a code comment. Pairs with the glossary work in 244.

244. THE GLOSSARY PASSES AND THE cdo-* RETIREMENT [canonical-producer + boundary]
    (`3d3e0e9b` fourth pass, `c860b4f5` fifth pass, `3c2bfcdd` the retirement sweep,
    `9256fc49` the merge, `64ec0e7e` an ASCII-x style fix that removes a 1-file port
    divergence). `3c2bfcdd` RETIRES AN INTERNAL ORG ACRONYM from every publishable
    surface — the `cdo-*` rename — because the token had leaked into 60+ publishable
    files. Cross-repo half: your registry rows and any loaded graph doc id may still
    carry the pre-rename string. That is a per-entry port-review question, NOT a
    wholesale rename on your side.

245. J55 — THE RETIRED ACRONYM CANNOT COME BACK [guard, canonical-producer]
    (`8c97a5c6` first cut, `90c624bf` the guard, `b2b89e4f` the close). The enforcement
    point behind 244: the token is never written literally in the test, it is read at
    run time from an Internal-only mapping file, so the guard cannot itself become a
    place the string leaks from. Skips cleanly where that file is absent, which is what
    your clone will do until you carry the mapping.

246. WEB-CONSOLE RUNBOOK REV 2 [docs, canonical-producer] (`3100ce37`). The ADK agent
    server joins the documented stack as the FOURTH process. If your console runbook
    still describes three, this is the correction.

247. REMEDIATION PACKAGE SURFACE — `profile` [like-for-like] (`2cbca5bc`, `95cd07e1`).
    G68 omitted `profile` from `__init__`; the second commit teaches the package-surface
    pin about it. `95cd07e1`'s note is the useful part for you: CI caught a subset run,
    the third instance of the same local-subset blind spot.

248. G93 — REMEDIATION COUNTS RIDE THE RUN LOG [like-for-like] (`732f18f1`, `8aedaf7c`,
    `9df95879`). The run's RECORDED counts travel into the Jira handoff rather than
    being recomputed at handoff time, so the ticket and the run agree by construction.

249. G71-G74 — ATTRIBUTION SURFACE AND THE :Employee BACKBONE [ontology, gate-bound]
    (`ba21e53b` G71 the required-contact completeness report plus a presence graph-test,
    `71ce7435` G72 the attribution-surface discriminator joins the precedence chain,
    `7b9c79f0` G73 the inheritance shape registered with K21 section 7.4 taking ancestor
    CIs for TOM rows only, `cc5b84a8` G74 REPORTS_TO registered and the creation policy
    recorded). READ `2946de82` WITH THIS: RELAY-17 carries the G74 stub-and-enrich
    company half, which is yours to run. Vocabulary fragments are `per-entry` — merge by
    id, never by path checkout.

250. K27 + K28 — TWO SURFACES STOP LYING [docs/config] (`595d076d` K27: pat_team_roles.csv
    is a hand-drop BY RULING and three surfaces now say so, `cdefec0a` K28: fid_census
    stops telling its reader the FID gate is unsigned when it signed 33/33 on 2026-08-19).

251. THE Q-SERIES — DOCMETA GROWS UP [like-for-like + one ADR] (`bcf70faa` Q15 four
    agent-navigation specs over the vendor-docs backbone, `2107af6a` Q17 ADR 0016
    PROPOSED on the jpmc-reports corpus shape, `ff87227f` Q18 the DESCRIBES target
    declared in the ledger and read by the loader, `7b25b7f7` Q21 the docs_email_concerns
    writer, `260e0f2c` Q23 a capture run names the registry row it fulfils or does not
    run, `63de2acc` Q26 corpus_id scoping measured live, `87fca339` Q27 the internal MWAA
    docs become a registered corpus and Airflow moves off no-corpus). ADR 0016 is
    PROPOSED and awaits a ruling; do not read it as decided.

252. S13 + S15 + S14 — THE IMPORT CYCLE REMOVED, AND docs/Product RELOCATED [structural]
    (`5ab0c1d2` the S8 cycle removed by hoisting shared state to `cli_shared`, NOT by
    reordering imports; `ac697959` S14 relocates docs/Product to knowledge/org, kebab-case,
    and dissolves seal/). CAUTION, and this is the one to read twice: `drydocs/cli.py` is
    `evaluate` in the manifest, and `76fbeec7` + `355a6f75` record that a cli de-dup
    reconcile was ALREADY IN PROGRESS on your side. These two streams will meet. Reconcile
    by hand against your de-dup result; do not take either side wholesale.

253. G121 + G122 — ACQUISITION ROUTES AND ENV NAMES [like-for-like] (`3f5b5769` G121:
    `load --csv` is a DECLARED acquisition route or it refuses, with a recorded override;
    `b4c10ef1` G122: every settings-group env var has a name-only line in `.env.example`).
    G121 will refuse loads your side may currently perform undeclared — that is the point,
    but it is a behavior change worth sequencing.

254. G111 — A ZONE'S DECLARED ENV VARIABLE IS HONORED [core, RED FIRST] (`13977357` the
    widened guard written red, `c1158395` the resolver fix, `621fced8` the core landing,
    `e6e5857d` the close). The guard walks EVERY zone now, not the sampled few.

255. G114 — THE SUPERSEDED-DATABASE GUARD SCANS WHERE THE STALE NAMES WERE [guard]
    (`3cb4e067` widen to agents/ and drydocs_docmeta/ with dddocs blocklisted, `83cb3c8b`
    re-point mentions to the escape-hatch wording, `c31f495d` the guard, `c938b7c4` the
    close, which records clause (e) as Idea-186 rather than pretending it landed).

256. K30 (a)+(c) — EVERY MAPPED PAT HEADER ABSENCE IS LOUD [load] (`f28eabc4`, `67173799`,
    `0f394d2c`). jira_board_id is acknowledged-absent rather than silently skipped. THE
    ITEM IS BLOCKED ON YOU: clauses (b)/(d)/(e) need the company G82 header list, and
    `0f394d2c` records the block rather than guessing the headers.

257. J53 — THE REFRESH WARNING NAMES ITS CAUSE [docs tooling] (`d7b0bb68`, `66b40be3`,
    `214e7eb8`). A partial render now lists what actually landed, and the snapshot refresh
    warning prints the cause instead of the word Traceback.

258. G112 + G113 — LINEAGE RESOLVES BEFORE IT COUNTS [like-for-like] (`d3d71392` and
    `fa71bf76` G112: the artifact pass runs its value through the G92 resolver BEFORE
    counting a gap, so a resolvable value stops reading as missing; `6e98d119` close;
    `f0377ddf` and `e79b43cd` G113: the multi-host identity flag reads scope and
    mount_source, not just host count, three ways; `861509c5` close).

259. G115 — THE DATA-CENTER SCOPE BIND [load] (`92c984b8`, `7063ad66`, `f50c16cc`). Joins
    the Control-M extract family, and the one-run-per-data-center recipe is DECIDED rather
    than left to the operator. Four production data centers behind the `[db]` placeholder
    makes this yours to re-run per venue.

260. N14 + N15 — THE UNION REPORT AND AGREEMENT CANDIDATES [api + load] (`8eb26ade` N14:
    the pending-source-correction union report, both domains in one age-ordered list;
    `0e25c9b5` N15: agreement-candidate detection where the LOAD PROPOSES, a steward
    confirms, and nothing auto-retires).

261. O69 + O73 + O74 + O75 + O76 — THE CONSOLE AUTHENTICATION CHAIN [canonical-producer,
    security-relevant] (`36601a10` O69 real authentication plus the credential carrier
    ADR 0009 did not cover, `65e92bcb` O73 credentials reload on change with a demo-login
    script that gets deleted at SSO, `453f898c` O74 personas become unmistakably fictional
    and gain the seats isolation testing needs, `36a7422a` O75 withdrawing an account now
    withdraws its live access, `e0b6d7a4` O76 the store records HOW each secret was set,
    `c16e4437` the Idea-164 groom). TAKE THIS AS A CHAIN, not file by file: O73/O75/O76
    each assume O69's shape. A fresh clone gets NO credential file, therefore no accounts,
    therefore every login refused with a message naming the bootstrap script — that is the
    designed default and it is stronger than a shipped demo account.

262. O77 AND THE OCCLUSION PAIR [like-for-like] (`358da344` O77: the ownership chips stop
    landing on the node names by MOVING rather than stacking, `33b8bbad` the capture of
    both occlusion bugs). O66 traded one occlusion for the other; O77 states that the
    cause is GEOMETRY, not z-order, so the next attempt cannot pass by flipping layers.

263. PORT MACHINERY [port, read before applying] (`e46cf8ab` three adoption dossiers for
    the deferred clusters -- remediation, lineage, ontology; `aed7229b` the SME-review-status
    capture protocol and the run-the-gate sweep; `fdaffd2f` the PORT-REPORT-e33f8d02
    close-out with the tom-role register protected by a per-entry manifest row; `ce5a071d`
    the Python 3.12 interpreter standard and venv rebuild hand prompt; `ad137c53` the
    DRYDOCS_DATA_ROOT rollout hand prompt after your G81 completion). The two hand prompts
    ask nothing back — they are yours to run and record in your own ledger.

264. GATES — WP-1 AND THE PRE-GATE SWEEPS [gate-bound, nothing built] (`bfa49e4b` drafts
    source-connection-and-run-identity and mints the two-issue work items; `95d90c12`
    pre-gate sweeps for G116/G117 confirming both pages CURRENT and both sessions runnable
    as drafted). Draft pages only. Nothing here writes the graph.

265. LANE B — A HANDOFF THAT RETIRES ITSELF [plan] (`7ed4eab2` the build-lane queue,
    `a9a89230` the queue empties and the handoff retires per its own lifecycle). Recorded
    because a handoff file that never retires becomes a stale instruction.

266. WEB SCAFFOLDING REVIEW [review + backlog] (`96002b6b`). The review and the five items
    it produced, in one commit.

267. THE CATALOG SUBSTRATE REVIEW [design, informs three open items] (`b58f3869` the
    second-pass survey of DataHub, OpenMetadata, Amundsen and OpenLineage; `1925cadd`
    folds its proposals into G81, G104 and G109). The finding worth your time: the
    three-part dataset key (platform, name, environment) has a documented ceiling —
    it cannot represent two deployments of one platform in one environment, which is
    exactly your four-data-center situation behind one `[db]` placeholder.

268. C28 — THE CHASE LEADERSHIP SCRAPE [evidence, External] (`3afa8307`). Membership-grain
    evidence plus a self-drift record for the business-layer gate. Evidence, not a ruling.

269. THE SOURCE-FILE MAP [design docs] (`368c4dfb`). Where ingestion input lands and what
    reads it. `docs/design/**` is `evaluate` — compare against your own map rather than
    taking it wholesale.

270. PAT — THE TEAM_DETAILS_REPORT COLUMN CENSUS CLOSES [like-for-like] (`42dc12e8`).
    A PINNED spelling was wrong; the census closes with it corrected.

271. TWO SMALL CORRECTIONS [docs + demo] (`23c62418` the load-map page named three things
    wrong about itself; `062d71f6` the depgraph demo queries in the console preset and the
    graph_query agent default now match the labels the self-documentation gate actually
    ruled -- `:CodeModule` / `IMPORTS` / `rel_path`, not `:CodeFile` / `DEPENDS_ON` /
    `relPath`. Both call sites returned `status: success, rowCount: 0` against a populated
    graph for as long as the drift stood, which is why nothing caught it).

272. THE MERGE AND THE ID RE-MINT [CRITICAL — READ BEFORE YOU TOUCH IDEAS.md OR ANY
    BACKLOG ITEM] (`3c250820` the merge, `846fa953` the re-mint, `1ad05b8c` the three
    independent artifacts). On 2026-08-29 two producer machines collided on NINETEEN ids
    at once. Resolution, and the rule it followed: ORIGIN KEEPS THE ID, the later mint
    renumbers, decided on dependency weight rather than push order. Concretely, in this
    range: backlog `O69`/`O70` keep their meaning and the desktop pair became `O81`/`O82`;
    the branch-side `J52`, `MM11`, `O68`, `O71` became `J62`, `MM12`, `O79`, `O80`; and in
    `IDEAS.md` the branch's `Idea-157` through `Idea-173` became `Idea-188` through
    `Idea-204`, with every citation followed across twelve files.
    WHY THIS MATTERS TO YOU MORE THAN ANY OTHER STEP IN THE RANGE:
    `docs/restructure/IDEAS.md` is `union-append` and `backlog/items/*.yaml` is
    `per-entry`. A naive union of this range re-introduces exactly the collisions the
    range resolves — you would end with two `Idea-160`s meaning different things. Apply
    the id set as it stands in the producer tree at the base; do NOT merge a pre-renumber
    copy from an earlier fetch. The J42 backlog-union block is the check that proves you
    did. `1ad05b8c` is unrelated content that rode the same cleanup: ADR 0015, a connector
    comparison and an internal brief, landed off a wip branch.


273. ADR 0017 + G124/G125/G126 — THE SOURCE-BINDING SUBSTRATE [config + core, READ
    FIRST OF THIS RANGE] (`03cc1227`/`83468602` G123 rules three merge-orphaned
    amendments follow-up, `ab5d4aec` claim, `53359622` ADR 0017 PROPOSED, `9e5cd178`
    Rev 2, `b9c9d1c0` the one open question named BEFORE acceptance, `81341df5` two
    of three acceptance rulings, `163cc8b6` ACCEPTED, `89113a06` G126, `9ebdb5d8`,
    `683d85fe` G125, `48c1e977` two follow-ups inboxed). The defect, measured rather
    than asserted: fifteen of thirty dataset rows are `acquisition.mode: automated`
    and declared NO binding at all — their system rows carried `locator.service: ~`
    with a comment saying the value lives in `internal-local/`, and nothing resolves
    a comment, so `drydocs landing-zones --check` reported a clean run over the
    manual half and said nothing about the other half. A check that silently covers
    half its subject reads as coverage. New: `config/source-bindings.yaml` +
    `drydocs_core/source_bindings.py` — one profile per CONNECTION CARRIER (not per
    origin: `origin: controlm` spans three systems and `system: psgmgr` carries
    three origins), naming ENVIRONMENT VARIABLES and never holding a value. Four
    carriers cover all fifteen. The system row carries `binding: <profile id>` or
    `binding: ~` with a `binding_note`, guarded in BOTH directions. G126 declares
    the credential file a read zone and makes an in-tree zone justify its place
    (`config/data-zones.yaml`, `drydocs_core/data_zones.py`).
    **APPLY NOTE — the manifest row is the load-bearing part.** `683d85fe` adds
    `config/source-bindings.yaml` to `PORT-MANIFEST.yaml` as `per-entry` with a
    FIELD SPLIT: producer-owned = id, carrier, platform, classification, serves,
    note and the KEYS of the env map; **company-owned and NEVER overwritten by a
    port = the VARIABLE NAMES those keys reference, and `status`.** Take the row
    first, then the file. Without the row it inherits the `config/**` default and a
    port carries ONE MACHINE'S BINDING onto the other side — the same omission that
    put `dev-environment.yaml` under that default until the 2026-07-28 port. ADR
    0017's reconciliation with ADR 0009 turns on that port test, and this row is
    what makes the test TRUE rather than assumed.

274. THE FIVE SUBSTRATE REVIEWS [design docs, default_ok, INFORMS C38 AND THE
    REGISTRY] (`c4daa879` the source-registry identity review, `b480c35d` +
    `cb5d45d8` DataHub passes four and five, `0b61b96b` OpenLineage read at source,
    `ff5d6f4e` + `1be090d3` two rulings that came out of it, `b6e3b74c` the subset
    qualifier, `dabb6d87` the `[taxonomy]`-prefixed id grammar assessed, `bdfbf6c2`
    the BDAT layer is system-scoped). Read `1be090d3` and `ff5d6f4e` even if you
    skip the rest: **psgmgr is a SCHEMA inside `spiderdb`, not a system of record**,
    and `spiderdb` PUBLISHES because it is the pronounceable head of the TNS alias —
    the name, not the coordinate. That closes the open question the identity review
    opened, and it is the reasoning behind every registry id you will read.
    `c4daa879` is the sharpest of the five: the redaction rule was deleting the
    identifiers the registry exists to carry. The reviews are `default_ok` — take or
    skip freely, they bind nothing — but the two rulings above are already applied
    in config.

275. THE COMPANY-SIDE BOOTSTRAP TRIAGE, TRANSCRIBED [internal, back-flow]
    (`ef9c0934`). `internal/research/triage-bootstrap-2026-08-28.md` — your own
    2026-08-28 session, transcribed producer-side and compared against main. It is a
    record of YOUR tree, so its paths are statements about that tree (the
    `is_record_document` convention). Nothing to apply; it exists so the producer can
    answer questions about that session without asking you to re-run it.

276. THE SUPPLEMENT CHAIN HAS BEEN FIVE SINCE Z3, AND NINE SURFACES SAID FOUR
    [core + docs, correctness] (`58aec7bf`, Idea-211). `default_chain()` returns
    base -> seal -> catalog -> registry -> infrastructure. Twelve occurrences across
    nine first-party surfaces said four, for eleven days: the run-drydocs skill,
    `cli.py`'s module header, the `apply-supplements` docstring, `supplements.py`'s
    own registry comment, `MODULE_MAP.md`, the startup-refresh runbook (three times),
    `RELATIONSHIP_GUIDE.md`, the SME checklist, `internal/repo-README.md` (twice).
    **The sharpest instance is a CORRECTION NOTE** — written because an earlier
    runbook left readers "quietly one supplement short" — which itself said the chain
    "has FOUR members". The note that fixed the defect became the next instance of
    it. Why no guard fired: `test_supplements.py` pinned the run-log envelope with a
    PREFIX assertion that a five-member chain still satisfies. If your tree carries
    any of those twelve sentences it carries the same wrong number; the text fix is
    cheap and the guard is the durable half.

277. G94 — WHICH STANDARD DOES A JOB VALIDATE AGAINST? [core] (`d8681e55`,
    `c4ffc14f`). `drydocs_core/orchestration/controlm/standard_selection.py`:
    `required_tokens(JobType)` selected on ONE dimension; the 2026-08-12 direction
    rules the real selection a TREE — a file watcher takes the FileWatcher standard;
    a command job selects on its ETL ENGINE first (DPL, Ab Initio, Informatica — the
    invocation types the launcher registry already classifies); anything else takes a
    generic standard AND SAYS WHY. Selection is separated from validation, so the
    tree can be re-ruled without touching the parser. The DD-digit guardrail is
    enforced structurally as well as functionally: the grammar version is ABSENT from
    `select_standard`'s signature, so someone reaching for the version slot as a
    selector has nowhere to put it. Unused is a convention; absent is enforcement.

278. G128 — THE RESOLVERS READ THROUGH THE ONE EXPANSION FUNCTION [core]
    (`2e929646`, `d1466b61`). Finishes what G125 started. The decision made first:
    `DataRootNotSetError` SUBCLASSES `UnsetVariableError` rather than being replaced
    by it — the specific type is load-bearing at two catch sites that print the data
    root's own remediation, so one flat type would have made an unset
    `NEO4J_PASSWORD` print advice about the data root. Exactly one exception identity
    changed, and only its base; every existing except clause still catches what it
    caught. `resolve_optional(name) -> (value, which_name)` is the non-raising
    accessor for callers where raising is wrong (a log directory called from inside
    `open()`); `expand()` still raises, which is right for a binding. Two functions,
    one declaration list.

279. G129 — THE INTERNAL TWIN BECOMES NAVIGABLE [core + tooling, AND IT FOUND A REAL
    TRAP] (`a2d6af58`, `1bd29b42`). `drydocs env-doctor [--check|--json]` over
    `drydocs_core/env_doctor.py`, plus `scripts/render_env_example.py` and
    `scripts/set_env_var.py`. **No value is printed by any of the three verbs.**
    Three states rather than two, for ADR 0017 clause 7's reason: the two machines
    hold different subsets, so an unset variable is a GAP only when something here
    wants it — it is required, or its profile is HALF configured. Every report names
    its venue (J18).
    **THE FINDING IS THE PART THAT MATTERS TO YOU — THERE ARE TWO CHANNELS.** The
    settings classes declare `env_file=.env`, so pydantic reads the machine-local
    file, while `env_refs.expand` reads `os.environ` and nothing else. **A variable
    set in the FILE ONLY is visible to a loader and invisible to a binding check.**
    Harmless producer-side today because no profile references the `NEO4J_*` names
    that answer from the file — but an `ORACLE_DSN` set in `.env` would have a loader
    connect while `landing-zones --check` calls the oracle carrier unbound. Your side
    has the live Oracle connection; check which channel yours answers from before you
    trust either report.

280. I6 — THE ID ALLOCATOR, AND THE TWO RULES THAT FOLLOWED IT [canonical-producer,
    CLAUDE.md] (`d11185cb`, `070a3b37`, `2317cfef` the union guard was testing the
    machine rather than the code, `294c8fd6` a mint stub carries its FINAL TITLE,
    `123c44a2` a mint stub carries its RENDER too). `--next-id` unions the local
    items, every remote ref's tree listing, and every id ever added in history, and
    returns max+1 — because next-free-in-my-tree is what produced the 2026-08-29
    nineteen-id collision in step 272. The two follow-on rules are corrections caught
    in flight: a title refined between the stub push and the body push reads to the
    collision guard as two machines minting one number (observed on J66), and a mint
    without its render fails `test_committed_roadmap_page_matches_its_sources` for the
    whole window between the two pushes (observed on G132/G133) — the Y5 tolerance
    forgives STATUS drift, not a new item. `CLAUDE.md` and `.claude/**` are
    canonical-producer: take them.
    **BAND NOTE, unchanged and worth re-stating on a port:** the allocator's bands
    (producer 1–9999, company 10000+) separate the two REPOS. They never separated
    the two producer machines, which is the collision that actually happened.

281. J63 — EVERY REVIEW SURFACE NAMES THE TREE IT RAN AGAINST [canonical-producer,
    AND IT IS ABOUT PORTS] (`1be32415`, `d069fa2a`).
    `docs/style/review-provenance.md` + `python scripts/review_stamp.py`, applied to
    all six existing design reviews and to `CLAUDE.md`'s working agreements. Every
    review, triage or research artifact states its `reviewed_commit`,
    `reviewed_branch` and `reviewed_port_base`. **The reason is your side:** without
    the port base, *absent here* reads as **broken** when it means **not yet
    ported** — which manufactured findings three times, most recently the 2026-08-28
    triage that called three registered refresh verbs backwards and seven existing
    commands unregistered. Note what this is NOT: J37 (read the importable object)
    was followed correctly every time. Reading faithfully still reports a STALE tree
    faithfully, so this is provenance and no method rule substitutes for it. This
    commit also edits `docs/port/port-prompt.md` itself.

282. G130 — BOOTSTRAP REPORTS LIVE-BUT-UNDECLARED CONSTRAINTS, AND FOUND ONE [guard +
    live finding] (`908b32ec`, `01761011`). The D8 guard asserts every DECLARATION
    landed; nothing asked the other question — what else is in there — which is how a
    retired label's constraint survives a data wipe and goes on enforcing an old
    identity rule against the next load that reuses the label. **It found one on its
    first run**, so clause (d)'s re-verification is not a formality. Venue (J18):
    producer desktop, `bolt://localhost:7687`, database `drydocs` — 56 live, 56
    declared across the tree, one live-but-undeclared: `membership_id` on
    `:Membership`, DROPPED at G99 (2026-08-18) with its last writer rather than ahead
    of it. **Not a producer defect — and live residue on this desktop exactly as on
    your instance, which the item did not predict.** Run it against yours before your
    next load; a residue constraint is invisible until it refuses a write.

283. J66 — A GUARD READS CODE, NOT THE PROSE AROUND IT [guard, canonical-producer]
    (`845716b9` mint, `cda15ef5` groom, `ae4dc314` claim, `1ec181eb` the build).
    `tests/source_scan.py` — `code_only` (comments and string literals stripped),
    `imported_modules`, `called_names` — and four existing guards moved onto it. The
    reason ships with the rule because the reason IS the rule: a guard that greps for
    a forbidden pattern also matches the **comment explaining why it is forbidden**,
    so it fails on the explanation and teaches people to stop writing explanations —
    which, in a repo whose comments carry its rulings, costs more than the guard is
    worth. It happened three times on 2026-08-30 alone (G128, G129, G130), each fixed
    from scratch. The one exception is a guard whose subject IS the prose — an error
    message, an operator-facing string — which reads raw source on purpose and says
    so. This is J37's disease at the other end.

284. G135 — THE DPL REGISTRY EXTRACTOR CAN REPORT A CONTRACT THAT IS WRONG, NOT ONLY
    ONE THAT IS BROKEN [lineage, T13-adjacent] (`6d7e76ef` mint, `72b3912f` bodies,
    `669a9c0a` the build). Every counter on `RegistryCoverage` was a SKIP counter, so
    a record that staged fine with five of its six fields empty fired none of them and
    the run summary was indistinguishable from a clean one. Now: `FieldCensus` per
    kind per contract field (present / empty / absent), run BEFORE any skip and
    reported as `"pipeline.version: absent 508/508"`; `active_absent` counted apart
    from `active_unknown` (a missing field is a contract question, a strange value is
    a data question); `seal_origin` / `seal_from_folder`, so a seal inferred from a
    directory name is visible as inferred rather than asserted as read;
    `_count_passed_over()`, so an intake-NAMING problem stops looking like an empty
    directory. **NO FIELD NAME MOVES** — amending the mapping is gate territory
    (G64/G65), and this is the instrument that measures it.

285. G136 — THE DPL DATASET IDENTITY RIDER [gate-bound, NOTHING BUILT] (`92d3898d`).
    `config/gate-prompts/dpl-dataset-identity-zone.yaml`, 3 sections / 9
    confirmations, DRAFTED and UNSIGNED. The argument it turns on is worth your
    attention because it is a reasoning defect and not a data defect:
    `rua-load-shapes` section G1 ruled managed assets key on the GUID alone "with
    version and zone as properties", and its sign-off cites `dpl_mac.py`'s own comment
    as evidence that this "was already the code's own assumption". That reads as
    corroboration and is not — **the comment is where the assumption came from. One
    belief, quoted twice.** Not a criticism of the ruling, which was reasonable on
    what was in hand; it is why a RIDER is the right instrument rather than a build.
    B2 forces amend-vs-carve-out on section G1 rather than letting a general rule go
    quietly false on its largest population.

286. THE T13 REVISIT FIRED, AND ONE ENTRY STOPS INHERITING AN OUTCOME [ledgers,
    note-only] (`07d9caab`, with `03d1c053` the CI fix that followed it). Note-only:
    no status moves, no entry is re-ruled, nothing loads differently.
    `dpl:pipeline-registry` records that a real export was pulled and profiled
    company-side on 2026-08-31 and that its status stays `stub` until the gate signs —
    a profile is evidence, not a ruling. `dpl:dataset-registry` now says what its
    cross-reference carries and what it does not: it inherits the 2026-08-07 ARGUMENT
    from its sibling and nothing else, because the two exports answer from different
    endpoints, which is why G64 and G65 are separate gates. **T13's row in this file
    changed with it** — the validation RAN, the amendment did not, so the row stays
    pending and now says which is which. `03d1c053` is the currency guard learning
    that `internal/research/G64-SME-MM-research.md` is a COMPANY-SIDE path: naming
    your artifact is the citation, not a stale claim about this tree.

287. O80 — THE CONSOLE GETS A TEST RUNNER [canonical-producer, CI CHANGES]
    (`0a981199`, `ce90669f`, `dd445a71`, `9c9cb91f`, `8565904d`, `ae1de732` the
    merge). Vitest for pure modules, Playwright for the browser path, both wired into
    `.github/workflows/ci.yml`, plus `config/taxonomy/ui-tests.yaml` as the ledger and
    `tests/unit/test_ui_tests_ledger.py` as its guard. **Two CI fixes ride it and both
    are environment facts you will hit too:** the web job needs `--with api` because
    it starts the API it tests, and it must declare a data root because the API
    refuses to boot without one. `web/**` and `.github/**` — read the K7–K15
    divergence block before taking `web/src` wholesale.

288. O81 + O78 + O83 + O84 — THE GRAPH CANVAS AND THREE CONSOLE FIXES
    [canonical-producer] (`534a9fbd`/`84d0ac6d` O81, the NVL canvas over QuerySpec
    results; `3e77be70`/`52dc4d04` O78, MiniDag adopts the shared `RelEdge` overlay so
    relationship names stop painting behind nodes; `aca4e3c1`/`b685c4b4` O83, the bolt
    panel defaults to the PROJECT database rather than the driver's home database;
    `29afe226`/`fad162fd` O84, first-party queries may only name labels the schema
    declares and an empty preset says WHICH are missing). O83 and O84 are the two to
    take early if you take nothing else from the console this port: both are the
    console silently answering from the wrong place.

289. O85 + O86 + O71 — THE CONSOLE AUTH BOUNDARY [canonical-producer + one gate draft]
    (`2a222c07`, `c9b38a23`, `908d7a79` the origins guard skips where fastapi is
    absent, `7acde151`). The console signs in where it says it does (a CORS origins
    fix), each graph canvas gets its own full-page route, and
    `config/gate-prompts/console-auth-boundary.yaml` is DRAFTED and UNSIGNED.
    `7acde151` is the one to read: **P3 states the JWT trade WITHOUT a recommendation,
    because its answer depends on a requirement nobody has stated.** A gate section
    that cannot be answered from the tree says so rather than guessing.

290. O58 + O61 + O60 + O62 — FOUR CONSOLE SURFACES, ONE UNRULED EDGE
    [canonical-producer, ONE ITEM IS [UNRULED]] (`2ab58b44`/`b54d1ef7` O58 the
    corpus-reconciliation surface and O61 the ownership product roll-up,
    `b6949083`/`4e6ca693` O60 the lineage swimlane with the lane basis as a parameter,
    `eece7b13` O62 the Ask file report and the first registered spec that actually
    filters, `22349056` the BDAT layers as a second lane basis).
    **[UNRULED] — O61 draws an edge the vocabulary has not ruled.** The commit subject
    says so on purpose. It is a DEMO surface over demo data, not a loader, and nothing
    writes it to a graph; do not let a rendered roll-up read as a ruled relationship.
    O60 is the contrast: it is restricted to edges the vocabulary ALREADY ruled, and
    `tests/unit/test_lineage_edge_backing.py` is what holds it there.

291. O59 — THE /remediation INTAKE SURFACE [canonical-producer] (`1dc99090`,
    `6984ba24`, `f105c403`). The machine reports what IS; the SME supplies what is NOT
    THERE. `scripts/render_remediation_profile.py` generates
    `web/src/generated/remediation-profile.json` and the route reads only the generated
    artifact — the generated-artifact + drift-test pattern, so the page cannot drift
    from its source without a guard failing.

292. O26 — A CLAIM RELEASED RATHER THAN WORKED [backlog hygiene, one line] (`150e08d4`).
    O26 was pulled and then released back to `todo` because an SME HOLD is live on it.
    Recorded because the release is the correct move and because the board now shows
    the gap: a `todo` item whose deps are all `done` still appears in Ready-to-pull
    even when a hold exists — the blindness Idea-232 captures in the footnote below.

293. CLAUDE.md ROUTING + Q28 [canonical-producer] (`d3f6e4f6` three stale routing
    pointers, `536437b2` the Oracle pointer dropped, `188bc4a4` the Oracle pointer
    RESTORED and venue-tagged, `9018b354`/`69955613`/`2be98f8d` Q28). The Oracle
    sequence is a decision to read rather than a churn to skip: the skill was first
    dropped producer-side for having no live connection, then RESTORED because **the
    skill tree PORTS** — `.claude/**` is canonical-producer, so the company inherits
    it while `settings.local.json` stays machine-local. The producer keeps `oracle-db`
    `"off"` in `skillOverrides`; **your side has the live `psgmgr` connection and is
    expected to turn it on.** Two adjacent pointers so nobody re-fixes this line
    wrongly: the vendor plugin `db@oracle-skills` is a DIFFERENT thing and is disabled
    at the user level, and `reference/platforms/` currently carries `neo4j/` only —
    there is no `oracle/` directory behind that link yet. `d3f6e4f6` also fixes
    `.claude/agents/backlog-groomer.md`'s schema pointer (`v2` -> `v3`). Q28 registers
    the 9.0.21 Parameters doc corpus and records that the tree refuses at CAPTURE, not
    at conversion.

294. THREE SMALL CORRECTIONS [docs] (`e0134168` VERSIONING's public-surface list had
    three stale pointers — `drydocs.backlog.v2` -> `v3`, `backlog.yaml` ->
    `backlog/items/<id>.yaml`, and `relationship_vocabulary.yaml` -> the per-domain
    fragment DIRECTORY (S5); `cd7ffa16` Idea-163 narrowed to the release call now that
    its orphan and drift halves are closed; `cf73bee6` the `rua_inventory.py` §D3
    comment now names G56, which resolved it, and states that the v1/v2 ambiguity is
    answered by RE-COLLECTING at v3).

295. THE THREE ONTOLOGY CORRECTIONS — OWNERSHIP IS NOT WHAT THE FIELD NAME SAYS
    [ontology, per-entry, READ ALL THREE BEFORE ANY FID WORK] (`3f3036e3`, `b35f79ae`,
    `f2e6d222`). All three amend ONE note — `human_appuser_owned_by` in
    `drydocs_core/ontology/relationship_vocabulary/52-local-human.yaml` — and each was
    a correction to the producer's own reading, kept in sequence rather than collapsed:
    (a) `3f3036e3` — the employee-hierarchy listing says "manager" because a functional
    account is the LOWEST level of the tree, so its owner is a manager BY TREE
    POSITION. It does not mean the owner manages people. Every seniority inference
    drawn from that field was drawn from a tree artifact.
    (b) `b35f79ae` — owning functional accounts is NOT owning applications. The
    convergence-means-technical-accountability reading was falsified by measurement:
    557 accounts against 6 applications. FCT ownership tracks who APPROVES ACCESS.
    (c) `f2e6d222` — "answered from ServiceNow TOM" is ambiguous, because **TOM has TWO
    SCOPES**: individual-scoped (ownership, single-digit CI counts) and group-scoped
    (support accountability, 65–153 CIs). A group-scoped answer reads as ownership if
    the scope is not stated, and the FCT owner field lands in NEITHER scope.
    **WHY THIS MATTERS ON YOUR SIDE SPECIFICALLY.** `52-local-human.yaml` is per-entry
    by manifest; only the live entry is touched here, and the superseded
    `seal_appuser_owned_by` twin deliberately keeps its original wording as filed
    history. Adjacent and NOT reopened: your 2026-08-26 G70 re-rule of the role
    register stands, protected by the per-entry `tom-role-vocabulary.yaml` manifest row
    (`fdaffd2f`). **The producer file declares SIXTEEN roles; yours declares NINETEEN.
    That gap is your re-rule, not producer drift — do not reconcile it by taking ours.**

296. C38 + G100 — THE REPLICA DERIVATION EDGE, AND MEASURED TIER EVIDENCE [ontology
    planned + gate-bound, NOTHING LOADS] (`0662e453` the claim, `cb7f58b9` C38,
    `0fe79795` G100). C38 registers `reg_derived_from` (DataAsset -> DataAsset,
    `prov:wasDerivedFrom`, domain `registry`) as **`status: planned`, with
    `supplement: ~` and `loader: ~`**, and drafts
    `config/gate-prompts/replica-derivation-edge.yaml` (5 sections / 11 confirmations),
    logged in `config/gate-log.md` as a RECORD stub — non-authority under J43, so no
    field may cite it. The gap it addresses: a replica says so THREE times and all
    three spellings are ATTRIBUTES — the id shape where `origin` differs from `system`
    (`controlm@[db].psgmgr.*`, `snow@[db].[schema].*`), `authority: ADS` against `SOR`
    (12 rows of 17), and prose in `notes` — so no query can walk from a replica to its
    origin. **Section A2 asks the prior question before any edge is minted: is
    TRAVERSAL actually wanted?** A reporting-only need is already served by the three
    attributes, and a gate that cannot end in "no edge" is not a gate. **Section C is
    the load-bearing half:** the sibling shape is the trap, because DataHub's
    `SiblingGraphService` ACTIVELY DELETES any lineage relationship between two
    siblings from the merged read path, which is the default — modelling replica-ness
    as aliasing DESTROYS the fact being recorded. The SME must reject it knowingly,
    not by omission.
    G100 gains the measured tier evidence: SENG/ASUP is a SEED, not the set — four
    tokens, `_SENG_`/`_SSRE_` -> L3 and `_ASUP_`/`_ISUP_` -> L2 — with group-scoped
    counts 118/129/190/237 and two cautions riding: console-export counts are FLOORS
    (the 200-row truncation) and the tier derivation is a naming-convention inference
    that doc 09's rule fences. **G100 is NOT on the derived gate queue** — it has no
    `gates:` field and no prompt file, and wiring it is its own unit (C39 is the item
    that makes the queue DECLARED rather than inferred).

LEDGER COVERAGE FOOTNOTE (2026-08-29, THIRD ROLL) — the `port-base-20260826..HEAD`
extension, cited here because the coverage check reads ONLY this section.
IDEA CAPTURES — `docs/restructure/IDEAS.md` is `union-append` and an inbox entry is not
apply content, so these get a citation rather than a step. Read 272 first: the ids in
this range were re-minted. `c0ae3004` (Idea-178, and it earns a mention — it predicted
that a cross-repo id rename would have to ride a port, which 272 is), `f1993e6f`
(Idea-161, Salt is preferred not mandated), `f6e2ae60` + `d8a556c6` (Idea-160 and its
KEPT-UPDATED correction), `06ae1383` + `3a7e1c93` (Idea-181, the lying `updated:` keys,
with a persona review scoping it by file class), `e81aa45b` (Idea-182), `83c858c4`
(Idea-183, set-not-count acceptance, adopted FROM your session's measured trap),
`2268b47c` (Idea-184), `cdb91a01` (Idea-159), `5758b2b0` (Idea-167, the mint-vs-pull
clause), `66eefc70` (Idea-169 gains the status field its header requires), `0292bacd`
(Idea-205a/205b — the allocator is a sentence, not a mechanism; the entry that followed
the collision in 272).
RITUAL PATTERN FIX — the footnote one roll above listed `chore(snapshot):` as "the third
instance of the same subject-line variant, listed rather than fixed by loosening the
pattern". This roll is the fourth and fixes it: `drydocs/port_preflight.py` learns four
drifted spellings the ledger header had exempted in words since the beginning — snapshot
under either scope, `chore(plan): render`/`re-render`, an item-scoped `claim`, and a claim
spelled `<ID> in_progress`. Eighteen commits in this range stopped reading as uncited. A
`close` is deliberately still substantive. The commit carrying this is a `chore(port):
ledger` roll and is ritual by the terminating-write rule.

LEDGER COVERAGE FOOTNOTE (2026-09-01, FOURTH ROLL) — the
`port-base-20260829..port-base-20260901` extension, cited here because the coverage
check reads ONLY this section. The commits below were enumerated at `0fe79795`, before
the roll commit existed; the tagged range is 129 because the roll commit IS the tag.
IDEA CAPTURES — `docs/restructure/IDEAS.md` is `union-append` and an inbox entry is not
apply content, so these get a citation rather than a step. Step 272's warning still
governs: apply the id set as it stands at the base, never a pre-renumber copy.
`1a34280a` + `6baeb3d6` (Idea-206, and the correction that the snapshot's stamp is
`meta.git`, not `meta.commit`), `aa04af2b` + `54a59b4c` (Idea-221, and the amendment
that the MCP server is a READ surface chosen per datapoint), `67468aac` (Idea-222,
access paths documented three times and never generalized), `c6b8a8cd` (Idea-228, the
recommendation was the lesser answer — three strategies recorded instead), `3c171013`
(Idea-229, a CANCELLED CI run is neither green nor red and nothing reads it as
unverified — worth your side's attention, since your CI check has the same hole),
`eafb0b2f` + `1cec2af3` + `2777476f` (Idea-230 and Idea-231, a dependency's growth has
no route to its dependent, and the console's access designations have no guard),
`6793d8df` + `fb5e9444` (Idea-232, the ready list is blind to a hold that exists
because the deps are done — see step 292), `9be42050` + `02cadd7a` (Idea-233, a CAPTURE
rung says how the bytes were obtained, which the trust axis does not).
MINTS AND BODIES — a mint stub is a reservation with its final title and its render
(I6, step 280), and a body fills it in. Neither is apply content on its own; the item
crosses in the `per-entry` backlog union either way, so like the idea captures they get
a citation, not a step: `845716b9` (J66), `cae680e7` + `6f141090` + `6cd0030f` (G132 +
G133, and the clause that moved between them), `a284016c` + `6116b778` (G134),
`2ba4ac82` + `a9526208` (O86), `6d7e76ef` + `72b3912f` (G135 + G136), `6f99d7a3` +
`9c834249` (C39 + C40 — C39 declares the gate queue, C40 gives a signed ruling a way to
be looked at again), `9018b354` + `69955613` (Q28, also in step 293).
RITUAL PATTERN FIX, THIRD TIME — the same three categories drifted into three more
spellings, and `drydocs/port_preflight.py` learns them rather than the ledger widening
its policy: the session-close snapshot written under a `session` scope
(`chore(session): depgraph snapshot at <sha> …`), a claim RELEASED with an article in
it (`chore(O26): release the claim …`), and a claim written as a `backlog(<ID>):` TYPE
(`backlog(G125): claim in_progress (desktop)`). Nine commits in this range stopped
reading as uncited. **Deliberately NOT widened, and this is the second such fence
after `close`:** `chore(<ID>): mint …` and `feat(backlog): <ID> body …`. A mint is not
in the header's ritual list, and under I6 it carries the item's FINAL TITLE and its
render — content, not bookkeeping. Mints are covered by the citation block above
instead. Exempting them would be a policy change and it is the user's to make.
PRODUCER-LOCAL HISTORY HYGIENE, stated so a new tag on the producer remote is not read
as a port artifact: three orphan refs that existed only on one producer machine were
pushed or retired on 2026-08-31 — `archive/old-history-2026-07-20` (411 commits, the
pre-squash history) and the `v0.3.0` release tag were pushed as-is, and
`pre-scrub-20260804` was REWRITTEN before pushing, as
`archive/prescrub-20260804-scrubbed`, because it carried an Internal workbook blob; the
unscrubbed original was deleted after equivalence verification. **None of this touches
`main`, and none of it crosses the port** — the two repos' histories are disjoint by
construction. It is recorded here only because those refs are now visible on
`ce-wilson/DryDocs` and a fetch will show them.

297. J68 + J69 + J71 — ONE SOURCE OF DISPOSITION TRUTH, THE APPLY SECTION LEADS WITH IT,
    AND EVERY MERGE RULE IS TOTAL [canonical-producer: skill, manifest, tests, port-prompt]
    (`de73fc4e` + `bc4df8bf` the two mints and bodies, `5c062e8a` J68, `bed22549` J69,
    `624b817f` + `c60a7b84` + `67d6b060` + `c5ebd2ce` J71). J68: the reconcile-port skill
    was asserting dispositions in four places and two were wrong (`test_module_boundary.py`
    read "take producer wholesale" while the manifest said per-entry, and the wholesale take
    had already dropped your extended groups once) — the manifest is the ONLY source of
    disposition truth now, the skill points at it, and `test_port_manifest.py` gains the
    COUPLING detector (a declaration and the guard that reads it share a disposition) with
    the companion that proves it fires. J69: this file's APPLY section now LEADS with the
    disposition classes in apply order, generated by `scripts/render_port_dispositions.py`
    (the step ledger stays below, entire — see the section header); RELAY-18 and RELAY-19
    carry J68/J69 and J71 respectively. J71: the four per-entry merge rules that enumerated
    fields had a hole for fields that exist and were not named — every rule now says what
    happens to UNNAMED fields (producer-owned by default, with the named exceptions), and
    `c5ebd2ce` retires a backticked machine-local path that only resolved on one machine.
    Take all of it; the two adaptations your chunk-1 apply made to the renderer (a head
    ref; the producer-only fourth guard skipping) are Idea-250's and come back to you as
    code at the roll after this.

298. J72 — A RENAME READS AS A CLEAN-ADD: THE CONTENT-SIMILARITY DETECTOR, SIX PINS, AND
    THE ONE THAT IS SAFE [canonical-producer; RELAY-20; hand-carried as dossier 4 —
    superseded by this range] (`553b80ac` mint, `b3b0bf37`, `6a8bd23f`, `978e7750`,
    `4f1a30d9`, `ed4ab6f7`, `ab3b8725`, `8915ea3d`, `d7c6b011`, `c6a3c6bc`, `2872fff7`
    close; `0ce33679` dossier 4). Built from your own request after the trap fired twice
    (the 41-local-seal split cost you 62 failures). Two measures because your two traps had
    opposite shapes — id-set for a split that keeps ids and loses prose, normalized text
    for a rename that keeps prose and loses the id — plus the same-slot and vanished-twin
    signals, containment, a per-file cap, and an idf discount that `c6a3c6bc` made
    conditional after it silently lost a known pair. **Only the final pin is safe**; the
    dossier's pin history says why, revision by revision. `ab3b8725` reads git's own rename
    record first (`git diff -M`) rather than re-deriving it. Your chunk-1 run of it over the
    whole tree (47 git renames + 45 candidates, every one dispositioned) is the intended
    use, and RELAY-20's "run it before every clean-add slice" stands.

299. THE PORT'S OWN CORRECTIONS, RECORDED WHERE THEY LAND [docs/port; T-rows]
    (`1fdc5c57` the fourth roll is 129 commits because the roll commit IS the tag;
    `e228652f` + `5d14003c` Idea-234, a green tip says nothing about the commits inside
    the range — the reason this roll exists rather than a take-by-name; `95d53ce3` + `17bc8985` RELAY-21
    and Idea-235 (mint and body), the acronym rename is accepted as a RENAME; `15d59628` the RELAY-21
    CORRECTION — the sweep IS required outside internal/, J55 caught the relay saying the
    opposite on your side; `e8bf46e0` C41 + the T24 row, the two things the 20260901 apply
    decided that nothing was recording; `0d035909` T24 gains its code dependency — the
    vocabulary migration gates `drydocs_lineage/writer.py` and `controlm_inventory.py`,
    not only config; `58ddff45` the roll's 519 was measured `..HEAD` past the tag, tag..tag
    is 516 and YOUR chunk-1 table reconciles exactly). Nothing to apply beyond this file
    and the T24 row; every one of these was found by your apply and written back here.

300. THE MANIFEST LEARNS THREE THINGS FROM THE APPLY [manifest rows; RELAY-22]
    (`febdf3ba` `web/src/generated/**` is `derived` — the port was telling you to carry
    rendered JSON; the roll's ledger-roll commit added `docs/lane-*-handoff.md` and
    `.claude/skills/*-workspace/**` as `never-port`, both producer working files that
    fell to a clean-add default). Regenerate, never carry (J43): every file under
    `web/src/generated/` is written by a `scripts/render_*.py` from committed sources and
    guarded for drift, so a carried copy passes the guard while describing the wrong
    estate. Your chunk-1 table already routes the seven this way; the row makes it the
    rule.

301. J70 + J70a — FOUR REGISTRY-ID REWRITES ARE NOT A FIND-AND-REPLACE, AND THE TEAMS
    EDITION SCHEMA-IDENTIFIER GATE IS DRAFTED [config/gate-prompts canonical-company —
    DRAFT, UNSIGNED, take nothing you have not ruled] (`4d7423ef` + `f34a6cf7` J70,
    `e6daa986` J70a, `d05ab9bf` the gates field). Two of the four requested rewrites are
    id renames that only a gate may make (an id is a join key cited inside signed
    records); the draft gate `schema-identifier-publish-ceiling-teams-edition.yaml` asks
    the questions. Producer-side it is a DRAFT; on your side the file, if you take it, is
    your DRAFT — the RELAY-21 distinction (name and status never cross as a signature).

302. THE CONSOLE WORKSTREAM — O87 TO O91, THE LOAD-MAP TABLE, THE TYPE SCALE, AND THE
    SKILL THAT RUNS IT [web/** canonical-producer BY NAME — read the K7–K15 hold before any
    `git checkout` of `web/src`] (`2698747a` run-drydocs-console skill: the console is three
    tiers, not one; `ce5f9ec0` + `ad3c6cba` O87; `d465aa5d` + `24644dc9` O88–O90;
    `4f35c2d9` + `e7e95f07` O90 the wiring key — report the cross, do not rule on it;
    `f44fb40d` + `88bbac87` load-map sort/filter/group/CSV + a Taxonomy column; `38618eee`
    + `0d8678fc` O91; `2156e5aa` one type pass; `e0c12d10` the dead header search removed
    and two unlisted components registered; `f3c0e19a` + `cf49c4b3` the landing-page
    sizes; `a66e4ff5` + `c3ff3023` + `168662a2` + `67e8448b` O91b–d, 23 type sizes down
    to 13 with a floor in the code; `bd7151ed` the `feat/ui-web` merge, with `fa302cbe`,
    `865b643d`, `9ce1256c`, `f3b6e7cf`, `d786ee59` its trunk merges — merges carry no
    content of their own). Component COUNT changes again (step 126's rule: re-derive, do
    not copy the assertion). `config/taxonomy/ui-components.yaml` is per-entry.

303. MM3 + THE RESEARCH SKILLS + TWO RESEARCH LOGS [skills canonical-producer;
    `internal/research/**` never-port] (`b5e84980` the shared entity/ID extractor, in
    core; `27dcb5bd` the mind-map state file — a slot fills only with evidence; `dffc5d96`
    the search log gains theme and novelty as a declared kind; `4c861213` MM3 close;
    `67cc583c` its merge; `6e8d1ad2` research-probe-discipline, the backbone; `75bedba6`
    research-general / research-job-failure / research-job-lineage; `bae7b874` +
    `9b754350` the shared ledgers — terms, platforms, id shapes beside the whitelist;
    `c7f58cdd` + `0a7fa3ac` the "unmerged branch" caveats added and then dropped when MM3
    reached main; `ab97ce23` the `feat/research-skills` merge; `e5c24574` the JOB→MFTS
    log transcribed + Idea-236; `fd3aa92b` + `2c184a79` the mind-map after-action review
    transcribed and attributed to an unmerged research branch; `9d0d2171` + `756e4989`
    Idea-236; `0b02a61d` + `303b27be` Idea-238). The skills cross whole. The two logs
    under `internal/research/` are Internal and never cross — they are named here so the
    range's `internal/**` additions read as deliberate, not as a leak. [CORRECTED
    2026-09-05: they never PUBLISH; they do cross - `internal/**` is `default_ok` and the
    private company remote is not a mirror. The point of naming them stands: deliberate,
    not a leak. EIGHTEENTH POSTSCRIPT.]

304. CI ON NODE 24 [.github evaluate — keep your workflows, adapt] (`10dcd15b`). Every
    action moved to the Node 24 runtime and the web app builds on 24; GHE runners are
    yours, so this is a note for your workflow, not a take.

305. PLAN1 — THE SERIES IS THE MODULE; THE 27 LETTERS ARE FROZEN [validate.py
    canonical-producer; test_backlog.py PER-ENTRY by its row — bracket corrected 2026-09-04,
    EIGHTH POSTSCRIPT; modules.yaml per-entry; CLAUDE.md canonical-producer; item files at
    `port-base-20260902`] (`100f018b`
    eighteen groom mints, `375dd962` PLAN1, `169a7a58` the ruling recorded and C41
    re-pointed, `8abcb359` an Idea header repaired, `6f2b91bc` a trunk merge, `664bca4a`
    CLAUDE.md gains ONE PEN PER SURFACE — the working agreement the 2026-09-02 collisions
    were missing, `c24ce720` the `--no-ff` merge). A backlog id is `<SERIES><n>` and the
    series comes from `modules.yaml` `series:` (`drydocs-load` → `LOAD12`); the 27 legacy
    letters are frozen at the highest number each ever took, and `validate.py --next-id
    --module <module>` is the only mint. **Your six band ids are safe because step 308
    ships with this range** — read it before running `test_backlog.py`. The freeze relay
    proper (DOC2) rolls separately with the edition segment (PLAN2); until then mint
    nothing new in a letter series and nothing at all in a module series until PLAN2's
    `edition:` key exists on your side — the allocator refuses the letters already.

306. C41 — GATE `ontology-domain-registry-and-edition-grain` SIGNED 14/14, EIGHT ITEMS
    MINTED, ONT2'S STORE RULED [config/gate-prompts canonical-company: the SIGNED prompt
    is the PRODUCER'S signature and never overwrites your DRAFT or absent file;
    gate-log union-append; items per-entry, at `port-base-20260902`] (`2978230e` C41 mint,
    `c1a883a5` the draft,
    `39b90843` SIGNED OFF, `12ec1b3c` the seven E1 bodies + the B5 rider, `6828e102` +
    `fb310c06` ONT2 — acronyms get their own store, the software-registry block was a
    holding place). The rulings that reach your tree as MECHANISM: domains.yaml comes
    (CFG1), a domain must own a fragment, the edition is a declared segment keyed to
    `area_product_id`, the DD reserve and the 10000 band retire forward-only, the
    declared ontology is base-common. None of it is built yet; the items are. Your own
    gate on the same questions is yours to convene (producer sign-off ≠ company sign-off).

307. THREE REVIEWS AND THE WORKPLAN YOU ARE APPLYING FROM [docs/reviews — records; the
    workplan is the retry's plan] (`1cde1a2a` the restructure design review, `441a957c`
    its eight edits folded into the item bodies, `7fe46e6b` Idea-242, `75bfc3c5` the
    tech-debt review — 29 scored findings, `3bc5b191` the port test review AND the
    ten-chunk workplan `docs/reviews/port-test-review-and-workplan-2026-09-02.md`,
    `9e7d61ea` its P2 corrected — the five `in_progress` items were shard-dated, not a
    burst; `e99e645d` Idea-250, three back-flow candidates from YOUR chunk-1 apply and the
    class-table question, resolved in your favor the same day). The workplan's chunk 0
    and RELAY-24 are the reason this range is being rolled before your retry rather than
    hand-carried.

308. PLAN3 — FROZEN_BAND, SO THE FREEZE CAN PORT GREEN [validate.py canonical-producer;
    test_backlog.py PER-ENTRY by its row — the freeze block crosses whole, the band block
    stays yours (bracket corrected 2026-09-04, EIGHTH POSTSCRIPT); PLAN3.yaml at
    `port-base-20260902`] (`5fa37ea7` mint, `e7dc4153` build). `FROZEN_SERIES` was measured
    on the producer's tree (G tops out at 136); YOUR `G10001–G10003` and `DD10001–DD10003`
    were legal when minted under the band rule. `FROZEN_BAND = {G: 10003, DD: 10003}`
    judges a band-shaped number against the band's own max, a letter-shaped one against
    the letter table; the six pass, `G10004` / `DD10004` / `J10001` / `G137` are strays.
    Agreement guard on both sides. Read and list; re-mint nothing.

309. ADR 0018 — COMPONENT IDENTITY IS A DECLARED, EXPORTED MAP, AND THE FOUR FLAT
    COMPONENTS BECAME SUBPACKAGES [RELAY-23 — one carved slice; content first, shims
    second] (`9f68b7d4` the ADR, `a8cc885e` ACCEPTED-WITH-AMENDMENTS — take the hit now;
    `fcd36285` three mints; `62c19a8e` CORE1 — `drydocs_core/component_map.py`, the
    boundary test imports it, four join guards, `drydocs-port`/`PORT` and
    `drydocs-libs`/`LIBS` registered; `2c128f6e` LOAD1 — eighteen modules and the
    publishing package to `drydocs/review`, `plan`, `port`, `docgen` with `sys.modules`
    shims at every old path for ONE cycle, MODULE_MAP's rendered component-map section,
    nineteen shim rows; `316dc24d` DOC3 — owners for every top-level directory,
    `SDLC-Docs/` to `docs/history/genesis/`, the four routing docs under the path guard,
    git-readme's July half to `docs/history/`, the plan cut and linked; `9792193a` the
    ADR's executed_by; `21fa5c30` the `--no-ff` merge). **`tests/unit/test_module_boundary.py`
    now IMPORTS `drydocs_core/component_map.py`** — the two land together or the test
    fails at import, and your one-line `load` addition for `drydocs.cli_consumer` (step
    312) goes in the MAP on your side once you hold it, not in the test. `MODULE_MAP.md`
    is per-entry with a RENDERED section between markers: regenerate the section
    (`scripts/render_module_map.py`), keep your hand rows.

310. THE SNAPSHOT ONE-LINERS RUN, AND A GUARD RUNS THEM [reconcile-port skill
    canonical-producer] (`acbd0af3`). The two J51 one-liners carried a real line break
    inside the `-c` string — found by you, chunk 1, exactly the test review's G4. `chr(10)`
    instead of an escape, and `tests/unit/test_reconcile_port_skill_snapshot.py` runs all
    four in a subprocess against a tmp TEMP. Your heredocs were right; the skill is now
    right too. The block also says a multi-day apply should not snapshot into TEMP.

311. THE lane-handoff SKILL [**never-port at the manifest sha below** — a SPECIFIC row
    above the `.claude/**` glob, first match wins; its `*-workspace/` and the generated
    `docs/lane-*-handoff.md` have their own never-port rows — step 300] (`fe120bf9`).
    The producer's two machines split a burst by a generated, self-retiring handoff file
    with a validated queue and a surface fence.
    **CORRECTION 2026-09-04 — THIS STEP AS FIRST WRITTEN SAID THE SKILL CROSSES, AND AT
    THE TAG IT DID.** The roll described the tree at `port-base-20260902`, where the
    skill sat under the `.claude/**` canonical-producer default and only its workspace
    was carved out. The user's producer-only ruling landed after the tag (`b1c0b782`),
    and `fe4df356` — the sha the paragraph below tells you to take — carries the row that
    makes `.claude/skills/lane-handoff/**` never-port. **So at that manifest the skill
    does NOT cross: do not take it.** The reason is in the row: lanes split a burst
    across two producer machines for throughput, and the company port is the opposite
    need — one pen, methodical, accuracy over speed — so a two-lane split tool is the
    wrong instrument on your side. Read the ROW, not this prose, wherever the two
    disagree; the manifest is the single source of disposition truth, and this
    correction exists because a path-by-path walk reads the ledger entry while it works.
    Note what this does to a count: some of the producer-only paths in a `.claude/**`
    diff are producer-only ON PURPOSE, so "N producer-only" is never "take N".
    **TAKE `PORT-MANIFEST.yaml` AT `fe4df356` — that sha exactly, not "or later"
    (corrected 2026-09-04 after your carve-out 7 said so, and you were right):** this
    skill's never-port row (`b1c0b782`) and the `row_may_match_nothing` entry that goes
    with it (`fe4df356`) are both PAST `port-base-20260902` and therefore outside the
    range you are applying. An out-of-range take is an EXCEPTION, and an exception is
    sized to the thing it excuses: "or later" would silently widen it to whatever the
    producer's HEAD happened to be on the day you ran, which is the same defect as the
    item-file "or later" the EIGHTH POSTSCRIPT retired, one level up. Take the file at
    `fe4df356`; anything the producer added to it after that sha arrives in a later
    range, in the ordinary way. Take the
    `.claude/**` tree with an older manifest and
    `test_no_manifest_row_matches_nothing` reports a hole for a row that is doing its
    job — the generated `docs/lane-<x>-handoff.md` and the eval workspace match nothing
    on your tree BY DESIGN, because both are producer-machine artifacts. Same commit
    carries `drydocs_core/component_map.py`'s per-entry row, which the ADR 0018 step
    above needs for the same reason. This is a take-by-name on ONE mechanism file, which
    is the only case the tag rule (EIGHTH POSTSCRIPT) admits.

312. S16 — THE COMPOSITION ROOT DISCOVERS `drydocs/cli_consumer.py`; `cli.py` IS
    CANONICAL-PRODUCER; RELAY-24 SAYS HOW TO ADOPT S8 [canonical-producer + the manifest
    rows] (`dc0367bc` S16, `9b63527a` its merge, `2e6c84f4` RELAY-24's order correction —
    the eight S8 files import loaders that arrive IN THIS RANGE, so the wholesale take is
    chunk 4's and chunk 0 only authors your module). The seam: `importlib.util.find_spec`
    for ONE optional module, registered LAST, silent when absent; `test_cli_registry.py`
    proves both directions with a fixture; `test_cli_import_order.py` joins it where it
    exists; the manifest moves `drydocs/cli.py` from evaluate to canonical-producer and
    adds `drydocs/cli_consumer.py` canonical-company. Defect 6 and DD6 (T22) close when
    the eight land in chunk 4 with your module beside them.

LEDGER COVERAGE FOOTNOTE (2026-09-02, FIFTH ROLL) — the
`port-base-20260901..port-base-20260902` extension, cited here because the coverage
check reads ONLY this section. Rolled before your RETRY rather than hand-carried, on
Idea-234's rule (a green tip says nothing about the commits inside the range); the
retry's range is `port-base-20260826..port-base-20260902` because the 20260901 apply
was parked unmerged (RELAY-24). The commits below were enumerated at the roll commit's
parent; the roll commit touches only paths already in the range.
MINTS AND BODIES — citations, not steps (I6, step 280): `c45c9dd9` + `41a714d9` (J67,
the measurement matters more than the blocker), `beec3bac` + `85f96da9` + `3123eb1e`
(Idea-239 and its header vocabulary fix), `47294acb` + `a59a489f` (Idea-240, the
boundary doc is silent on history — 34 of 1816 commit messages carry the token; your
`294b9cec` question is the same shape), `7e545fad` + `2a65b7ec` (Idea-241, the evaluate
row for `cli.py` can merge verbs but not a refactor — the idea that became S16 and J73).
RITUAL PATTERN, UNCHANGED — twelve of the 135 commits in this extension read as ritual
under the existing patterns (snapshots, claims, renders, groom); no spelling drifted this
roll, so `port_preflight.py`'s patterns are untouched. The two RECORD_PREFIXES it gains
(`docs/history/`, `internal/research/`) are the cited-paths check learning two document
classes whose paths are facts about the tree they described, not a policy change.

**SIXTH ROLL — `port-base-20260902..port-base-20260905` (2026-09-05).** 186 commits at the
tag (183 when the ledger was written, plus the roll commit, its ritual follow-up and one Lane B
claim that landed between them), 132 cited below in steps 313–333; the rest are the ritual patterns. The range was cut from
`origin/main` at `7a56f6f1` with Lane B's three `wip/` branches deliberately excluded (their
claims are in the range as status-only item commits; their work is the next range). Every
producer-owned surface the company hand-edited during carve-outs 6–9 now has the producer
change behind it (step 328), so this is the first roll since 2026-08-26 with nothing
hand-carried and nothing parked.

313. THE LANE MODEL RAN THREE BURSTS, AND THE HANDOFF FILE NEVER CROSSES [`docs/lane-*-handoff.md`
    never-port; `.claude/skills/lane-handoff/**` never-port; merges ritual] (`0f765355`,
    `f109280f`, `0aeba6fc`, `dc12fb16`, `6c51618e` the generated handoff files — five
    generations, each retired when its queue emptied; `ea90c4d9`, `ebb6f03e` the queue
    closes, the first of which also carried the `.pre-commit-config.yaml`
    canonical-producer row; `780a6d45` the skill carries the burst's three findings, and
    `config/dev-environment.yaml` names the runtime UTF-8 environment — that file is
    canonical-company, so read the producer's two lines and write your own; `9546268a` the
    second rebase hunk resolved and manifest rows deduplicated against `df0b0437`; the
    `--no-ff` merges `47e00ea1` `2467d992` `8f585a46` `163fad99` `b1821f10` `22742cff`
    `dc121d93` `8d495289` `4def9bda` `33ff9fa5` `8f150ea3` `548e0725` `52b849ea`
    `aee4e835` `75a45d07` `dfc3ad0f` `883fa5fc` `f6e2b4f7`, two of which resolved a
    collision (`b1821f10` web/package.json + README, `883fa5fc` config/taxonomy) and none
    of which carries content of its own; `6743ee9d` the review-branch merge). Nothing here
    is a take; what the bursts produced is steps 314–333.

314. O92 — TC-SHELL-08 AUTOMATED [`web/**` canonical-producer; `config/taxonomy/ui-components.yaml`
    per-entry] (`5bb80ec8` `web/src/modules/registry.test.ts`, `d618c3a3` close: the
    automated share 16/39 → 17/40 in the ui-components row). The role × designation matrix
    over the real module registry. The ui-components row it touches is rows-union under the
    rewritten entry_rule (EIGHTEENTH POSTSCRIPT).

315. G133 — THE JSON CHANNEL CARRIES EXIT 4 [`drydocs_core/adapters/**` default;
    `API-CALLS.md` canonical-producer] (`da267aaa`, `a7b82434` close). A tool the host
    cannot start returns exit 4 through the JSON channel, not a traceback; `API-CALLS.md`
    records both folder-export transports.

316. O70 — THE CONSOLE'S API CLIENT IS GENERATED FROM `drydocs_api`'s OPENAPI SCHEMA
    [`drydocs_api/**` default_ok — HAND-MERGE, never take the package; `scripts/dump_openapi.py`
    + `web/scripts/**` canonical-producer; `web/src/generated/**` DERIVED; `.github/**`
    evaluate] (`19537a17`, `be4e1195` the multipart proof, `abe7f90a` close). Two committed
    artifacts with drift guards, `web/src/generated/openapi.json` and `api.d.ts` — derived,
    regenerate from YOUR `drydocs_api`, never carry (the TENTH POSTSCRIPT's rule, two more
    files). `drydocs_api/schemas.py` is new and `app.py` changed: your personas relabel
    lives in that package, so hand-merge (your rule 2). CI gains a type-check step —
    `.github` is evaluate, adapt.

317. R9 — `drydocs_api.agent_query` [`drydocs_api/**` default_ok, hand-merge; `agents/README.md`]
    (`2ae6b2a2`, `94898659` close). Read-only deterministic QuerySpec navigation;
    `execute_spec` extracted so the CLI and `/specs/{id}/run` share one envelope.

318. O88 — THE CONSOLE'S PAPER FORM [`web/**` + `run-drydocs-console` skill canonical-producer;
    `tests/unit/test_console_print_gutter.py` default] (`e726824f`, `041006d9`). Headless
    Edge captures executed routes to printable HTML with the L6 gutter and a provenance
    footer (`web/scripts/captureRoutes.mjs`, `web/src/lib/paperForm.ts`). The browser is a
    machine tool — a venue fact, not a dependency.

319. J62 — PRE-COMMIT HOOKS FOR THE TWO COMMANDS CI BLOCKS ON [`.pre-commit-config.yaml`
    canonical-producer (row at `ea90c4d9`); `CLAUDE.md` canonical-producer;
    `tests/unit/test_precommit_config.py`] (`04f632df`, `0ccd3cac`). The hook rev is pinned
    to pyproject's ruff and the guard keeps them together. `pre-commit install` once per
    clone; deliberately not installed for anyone.

320. Z9 + O87 — TWO CONSOLE FIXES AND THE SME SEAT BADGE [`web/**`; `tests/unit`]
    (`2a905614`, `4a6341b1` Z9 — Synthetica's country through the alias fallback;
    `45b6ebdd`, `c21f113c`, `64536bf4` O87 — the persona picker marks the SME seat from
    `SME_PERSONA_ID`, derived from the roster constant and never a named id, so your `sme`
    relabel is what it shows; the ui-components ledger scan skips `*.test.tsx` /
    `*.spec.tsx`).

321. J76 — CHECK THE INSTRUMENT BEFORE THE SUBJECT [`CLAUDE.md`, `docs/style/**`
    canonical-producer; `scripts/**`; `tests/source_scan.py`;
    `tests/unit/test_subprocess_encoding.py`] (`d189ee36`, `b3632e71`). Every subprocess
    capture in `scripts/` and `tests/` decodes with an explicit encoding; the guard; the
    other two failure modes named in `review-provenance.md`. `scripts/port_preflight.py`
    and `render_port_dispositions.py` are among the fixed callers.

322. G134 — THE CAPTURE RUNG BEHIND EACH TRUST VERDICT [`config/doc-source-registry.yaml`
    PER-ENTRY] (`a6453ec1`, `e6bf8bf4`). The ladder declared once as data, `capture_rung`
    on every row with `unprobed` as an honest value, a one-directional VERBATIM guard.
    Per-entry: add the ladder and the field to YOUR rows; their rung values are yours.
    Two findings raised and left open in the close note — read it before setting a rung.

323. O54 — WHERE CONFIG LIVES vs WHETHER IT IS GUARDED [`scripts/render_enforcement_matrix.py`
    canonical-producer; `web/src/generated/enforcement-matrix.json` DERIVED] (`9f44aa51`,
    `3b21ac3e`). The matrix separates the two questions; the canonical load sequence joins
    as a code-resident row. Regenerate the matrix on your tree.

324. C43 — MFTS IS AXWAY SECURETRANSPORT 6.0.3, AND THE ROW A WHOLESALE TAKE WOULD LOSE
    [`config/taxonomy/software-registry.yaml` PER-ENTRY (`0003ea28`, SEVENTEENTH POSTSCRIPT);
    `scripts/render_software_registry.py`] (`530f5757`, `341a6fe9`). A white-label row,
    vendor beside product the way `controlm` carries `bmc`, `white_label` carrying the
    internal name. Your rows stay; the count is tracked per side.

325. Z8 + Z7 + Z4 — THE BUNDLED DEMO INTERLOCKS, THE TEAMS DIMENSION LIGHTS UP, AND
    LOAD-BALANCER NAMES RESOLVE [`tests/fixtures/**` default; `drydocs/data/**` NEVER-PORT;
    `drydocs_lineage/**` default — your continue-defer cluster] (`15f0b18e`, `0c377528`,
    `7f465b7c` Z8; `83f4efa5`, `8ae03bf1` Z7; `14d26b3f` Z4). Z8: a gazetteer row, aligned
    host names, an application the graph carries,
    `tests/unit/test_bundled_demo_interlock.py`, and a real skip guard where J8's file-level
    rule misreads a tracked sample. Z7: a fact feed under `drydocs/data/` (never-port — the
    bundled samples are the producer's demo, yours are yours) and
    `tests/fixtures/attribution/stg_app_fact__bundled-samples.csv`. Z4:
    `drydocs_lineage/extractors/lb_resolution.py` + `drydocs_lineage/collect/lb_resolve.sh` +
    `drydocs_lineage/collect/LB-RESOLVE.md` + synthetic nslookup fixtures under
    `tests/fixtures/lineage/lb_resolve/` — classified by outcome, never by name; a clean-add
    into a package you hold differently.

326. J74 — A CEILING GUARD FOR THE RETIRED ACRONYM IN COMMIT MESSAGES
    [`tests/unit/test_publish_boundary_history_ceiling.py` PER-ENTRY — new row this roll;
    `PUBLISH-BOUNDARY.md` canonical-producer] (`74cd5990`, `b65626fe`). `CEILING = 34` was
    MEASURED on the producer's history (34 of 2,057 commits) under the ruling that a push
    CARRIES history, so the 34 are accepted and the number may never rise. Your history is
    disjoint and your count is yours: measure it with the test's own log command, set YOUR
    ceiling with the recorded reason, take the mechanism whole. The token is read from
    `internal/cdo-reference/README.md`, which you hold (EIGHTEENTH POSTSCRIPT), and like
    J55 the test fails closed when it cannot read it.

327. J58 — ONE JSON SCHEMA FOR THE IDENTITY HEADER, DEFAULT-DENY BY FILE CLASS
    [`config/schemas/identity-header.schema.json` canonical-producer;
    `tests/unit/test_config_identity_header.py` PER-ENTRY — new row this roll;
    `config/gate-prompts/**` + `graph-tests/**` canonical-company; `internal/**` default_ok;
    `knowledge/upgrade-plans/**`, `docs/restructure/**`] (`182523e7` — one commit, about
    forty files: the schema, the test, and the header normalized across every class).
    `test_every_tracked_yaml_has_a_declared_class` walks EVERY tracked YAML and fails on one
    in no class — so every company-only YAML goes red on arrival, by design. The `CLASSES`
    dict in the test is the declaration: add your files with their class and reason, take
    the rest of the test whole — the `test_backlog.py` shape, and the manifest row says so.
    Your canonical-company files get the same header block, added by you.

328. THE PORT PEN'S OWN COMMITS — EVERY ONE ALREADY IN RELAY-25 OR ITS POSTSCRIPTS
    [`docs/port/**` never-port; `PORT-MANIFEST.yaml` canonical-producer; `tests/unit/test_port_*.py`
    + `test_reconcile_*.py`; `drydocs_core/component_map.py` per-entry;
    `.claude/skills/reconcile-port/**` canonical-producer] (`30d2e870` S16's
    `drydocs.cli_consumer` is an ENTRYPOINT in `component_map.py` — the line RELAY-24's
    addendum told you to add locally; `40d2461d` RELAY-25's five corrections — the
    publishing shim aliases every submodule, the seven `cli_*` rows, J55 fail-closed;
    `dd2bb7b2` the totality companion skips by name; `20449d47` the fence canary pins
    `docs/style`; `84ef2d97` + `af9194c4` the runbook-currency and never-port zone guards
    read tracked content and skip by name; `15a106d4` RELAY-25 itself; `c88261e0` fourth
    postscript; `02580f2c` the `test_source_bindings.py` evaluate row + fifth; `0f893f86`
    the consumer-seam probes hold on a tree with a real `cli_consumer.py` + seventh;
    `9e201135` eighth; `f74ad5b9` + `a5ff4a84` step 311's sha and its correction;
    `a060f8be` the overlay duplicate guard reads all three blocks + two carve-out-7
    corrections; `4dd7c8e1` tenth; `6af36e4c` eleventh; `f9c8605b` twelfth, which stamps a
    `config/gate-log.md` record (union-append); `f2ec87db` the data-centers per-entry row;
    `aa7c20b5` fourteenth; `9beb68d0` seventeenth; `0003ea28` the software-registry
    per-entry row; `920a4107` eighteenth + the ui-components row rewritten + the
    reconcile-port skill's three apply rules). These are the fixes promised "at the next
    roll"; the guards they changed are what made your chunk-2 FileNotFoundError and your
    chunk-1 Q5 unrepeatable.

329. `register_loaders` — THE DECLARATION HALF OF THE CONSUMER SEAM [`drydocs/cli.py` +
    `cli_shared.py` canonical-producer] (`f338097d`; LOAD2 minted in it — a citation, not a
    step, I6; RELAY-25 sixth postscript). Your loaders register through it at the S8 take;
    the data-center bind docstring states its two value domains, which is LOAD2's subject
    (step 331).

330. LIN1 + LIN2 — THE LINEAGE CHAIN EXTRACTS IN HOP ORDER AND LOADS PLAN-ONLY BY DEFAULT
    [`drydocs_lineage/**` default — your continue-defer cluster; `drydocs/cli.py`
    canonical-producer; `config/data-zones.yaml` canonical-producer; `MODULE_MAP.md`
    per-entry; `tests/integration/test_lineage_load_e2e.py`] (`da45a91f` the epic, the pair
    and the workplan review; `5c429f05` `drydocs lineage-extract`; `0170ed2c` the variables
    sample is machine-local so the default run treats it as optional; `93f4d832` the lane
    review applied — `code_commit` in the header, per-hop zone checks, LIN2 acceptance
    settled; `9fcce1fc` `drydocs lineage-load` — `plan_curated` over a staged artifact,
    `--write` for the active labels; `d94e4588` done, venue-tagged proof (desktop,
    `neo4jtest`, `drydocs`); `aba1ef21` Idea-254 — coverage serializes the distinct
    COUNT). `drydocs_core/data_root.py` gains a zone; `drydocs_lineage/staging.py` is new,
    `curation.py`, `review.py`, `writer.py` reshaped. The lineage cluster has been
    company-divergent since the 2026-08-26 continue-defer; this is the largest addition
    since, and it is the adoption dossier's next chapter, not a take.

331. LOAD2 — ONE `--data-center` VALUE REACHES THE TABLE THAT SPEAKS EACH SPELLING
    [`config/taxonomy/data-centers.yaml` PER-ENTRY (`f2ec87db`);
    `config/schemas/data-centers.schema.json` canonical-producer; `drydocs_core/data_centers.py`;
    `cli_shared.py` + loaders canonical-producer] (`3e211932`, `11c5993b` done, `b309a0d9`
    the non-derivability argument is the VENDOR BASELINE, not a time segment). The taxonomy
    file pairs both value domains per data center; the producer's rows are synthetic and
    yours are your production data centers — per-entry, rows keyed by id, the twin-aware
    reader. Plus `863c6733` the DRAFT gate prompt `controlm-folder-identity-grain` —
    canonical-company directory, clean-add, DRAFT and unsigned on your tree until your own
    session.

332. THE RESTRUCTURE CHAIN — PLAN2, THE `idea-series-grammar` GATE, CFG1, CFG2, DOC1, PLAN4
    [`.claude/skills/groom-backlog/validate.py` + `drydocs_core/backlog_store.py` + `CLAUDE.md`
    canonical-producer; `config/dev-environment.yaml` canonical-company;
    `config/taxonomy/domains.yaml` + `editions.yaml` PER-ENTRY; `config/gate-log.md`
    union-append; `config/gate-prompts/**` canonical-company; `docs/decisions/**` default;
    `git-readme.md` evaluate; `docs/restructure/ideas/README.md` canonical-producer;
    `docs/restructure/ideas/pending-*.md` never-port].
    PLAN2 (`fc4f7af7` the Idea series has no edition grammar yet — your Idea-10012;
    `43fd345c` the edition segment: `[<EDITION>-]<MODULE><n>` and `[<EDITION>-]Idea-<n>`,
    the edition DECLARED in `config/dev-environment.yaml` `edition:`, both partition rules
    retired forward-only, git-readme's "NEVER allocates" sentence retired, `drydocs/port`'s
    union reads the segment). Your action: declare `edition:` in YOUR `dev-environment.yaml`
    — the file is canonical-company, nothing here writes it, and a venue with no key mints
    no item (RELAY-26 (1)).
    The gate `idea-series-grammar` (`bf1a6f86` draft, `f071194f` pre-session refresh,
    `de8159eb` SIGNED OFF 9/9 producer-side) — union-append the gate-log record; the prompt
    lands in your canonical-company directory as a clean-add that reads DRAFT on your side.
    C1 is the carve-out that keeps your idea channel open before you declare, and your
    09-05 renumber (TWELFTH POSTSCRIPT) is recorded there as C1's shape.
    CFG1 (`2c744212`) `config/taxonomy/domains.yaml` + `drydocs_core/ontology/domain_registry.py`
    + `config/schemas/domains.schema.json`: the 13 domains with their REAL rulings;
    per-entry — your mints stay, mechanism crosses; the reader enforces base-owned minting.
    CFG2 (`df0c49de`, `ba7f7920`) `config/taxonomy/editions.yaml` +
    `drydocs_core/edition_registry.py` + `config/schemas/editions.schema.json`: Internal,
    two SYNTHETIC rows marked `sample: true`, your code unnamed; per-entry — replace the
    samples with your real rows keyed to `area_product_id` (RELAY-26 (2)).
    DOC1 (`5803d091`) ADR 0015 amended by dated section — D2 thin instance-owned backlog,
    D6 `--scope`, C1–C3 the edition as a declared segment. ADR text; default class.
    PLAN4 (`13333546` mint, `f1825cc9` body, `e1c82161` build, `70d6e14b` newline fix) —
    venue-aware grooming, the edit side: `--check-venue-edits` (REWRITE / UNSTAMPED /
    STATE FLIP), the pending file `docs/restructure/ideas/pending-*.md` and
    `--mint-pending`; `0e33826e` Idea-258..264 landed through it. `dbd13170` DOC2 /
    Idea-250 — producer records say "the company", never "their".

333. REVIEWS, THE MODULE SWEEP, AND THE SIXTEEN WEB ITEMS [`docs/reviews/**` default_ok
    records, J63-stamped — read, never edit; items per-entry AT THE TAG `port-base-20260905`]
    (`0cc996cf` the job-to-ETL binding second pass, `0015fcfa` its review, `1b615dc7` R8b,
    `33c058c5` APPLY, `796841f7` R7 narrowed; `127e6b4c` the second-review protocol between
    lanes; `2f9ebfc7` + `e1e72e86` the Ideas-to-Backlog intake review; `170e12ff` +
    `d62ac0e8` + `b35938e6` carve-out 6 readiness / R1 / VERIFY — the producer's review of
    YOUR carve-out 6, which records that two of its own findings were wrong and yours were
    right; `e44cc5b4` + `5f02599f` the module review sweep plan and its secondary review,
    slot 9 the web report at `docs/reviews/modules/web-2026-09-05.md`; `1e17651d` +
    `bcae4d02` + `be83296f` DOC4; `a1f2dad8` + `3014b7d8` WEB1–WEB15 + API1 minted with
    final titles and bodies; `7f60d26c` Idea-256, the five-tier naming formula reviewed).
    The three Lane B claims at the tag (API1, WEB3, WEB4 `in_progress`) are claims, not
    work — the work arrives in the next range.

    LEDGER COVERAGE FOOTNOTE (2026-09-05, SIXTH ROLL). 186 commits in
    `port-base-20260902..port-base-20260905` (`git rev-list --count` at the tag); 54 read as
    ritual under the existing patterns (snapshots, claims, renders, grooms); 132 are cited in
    steps 313–333 — the 131 the ledger was written against plus the roll commit itself. The
    counts were 183 / 52 / 131 when written and are corrected here at the tag, after the fact. No pattern
    spelling drifted this roll, so `port_preflight.py` is untouched. The roll commit
    (`7f676ce9`, subject `docs(port):` — outside the `chore(port): roll` ritual pattern, so
    it is cited here rather than exempted) touches `docs/port/port-prompt.md`,
    `PORT-MANIFEST.yaml` (the two per-entry rows named in RELAY-26) and the plan renders —
    no path the range had not already touched. The tag sits on the `chore(port): roll`
    follow-up that re-renders the board after Lane B's WEB12 claim (`3919f5a0`) landed
    between the roll's pull and its push.

334. LANE B'S FIRST WEB STACK — STRICT TYPES, RESULT COMPLETENESS, ROUTE AUTHORIZATION,
    THE DATA LAYER [`web/**` canonical-producer, 151 paths this roll; `web/src/generated/**`
    derived — regenerate, never merge; items per-entry] (`e6fdd0e5` + `8565b29e` WEB4 —
    TypeScript strict on in `web/`, with a guard that keeps it on; `95c89328` + `1555a411` +
    `cf4d45c7` + `047c8877` API1 — result completeness is part of the read contract, the
    server declares whether a page is exact or truncated; `139cee4e` + `67a8734e` + `00f39a5a`
    WEB3 — route authorization derives from the module registry, no hand-kept route list;
    `d3a64c9e` + `624508da` + `ccbb75a8` + `ac9415fd` WEB12 — the data layer: provider,
    `useGraphQuery` and the shared scanner; `a545b3b0`, `63ed6ddb`, `93162325` the `--no-ff`
    stack merges). The four were the `wip/` branches the 0905 bullet said would land in this
    range; they did, as one chain, each merged after the one below it.

335. LANE B'S SECOND WEB STACK — PROVENANCE, THE CI RATCHET, ERROR BOUNDARIES, STORAGE,
    THE SECURITY MODEL, TOKEN PARITY [`web/**` canonical-producer; items per-entry]
    (`7afe9f13` + `c8c17551` WEB1 — provenance of rendered data is a typed union; `ebf9ca7d`
    WEB13 — the web CI ratchet and a correction to the review; `452e7557` WEB5 — an error
    boundary per route outlet, keyed on pathname; `452b5583` WEB11 — one storage module, both
    sign-out paths clear it; `4f5712ed` WEB15 — the README states the security model the code
    implements; `6559f364` WEB14 — a token-parity guard for the two frozen sheets; `778d242d`,
    `e113e0ae`, `65db25e2`, `df5953e7`, `8fdc313b`, `fa23aed3`, `facd84f0` the stack merges;
    `aa7e5836` untracks the vitest coverage report — 184 generated files rode in with WEB13's
    `test:coverage` and nothing ignored them, so the ignore rule is the change to take;
    `c87e7cca` repairs cp1252 double-encoding in five item files — 47 mojibake em dashes and
    quotes read back as the characters they were; take the repaired bytes, the per-entry union
    keys on id and the content is the producer's).

336. LANE B'S THIRD QUEUE — THE ROW CEILING, THE ROW-SHAPE CHECK, CODE SPLITTING, THE
    STUB-ADK FIXTURE, THE LOG ESTATE [`web/**` canonical-producer; `agents/**` default_ok;
    `tests/fixtures/adk/stub-run-sse.txt` default_ok; items per-entry] (`4fcc0096` +
    `7810333a` WEB2 — the row ceiling is visible and the export stops claiming "full";
    `f38ba655` + `f04840db` WEB6 — one runtime row-shape check retires every double cast;
    `f3b61c57` WEB7 — code splitting follows the authorization boundary; `940325da` +
    `a622eb56` R12 — the stub-ADK harness is a committed fixture (`tests/stub_adk.py`);
    `805af17d` O43 — the last UI suite is seeded, 13 of 13; `b200d445` G131 — the agents' env
    fallback stops depending on `""` being falsy; `274e4b21` + `721abcd0` O89 — console anchors
    become content-derived; `56f4cab4` O68 — the log estate, with the debug tier unreachable by
    construction (`drydocs_core/log_estate.py`, `drydocs_api/log_estate.py`,
    `config/log-kinds.yaml`); `35ff19b3` O89 seeds drafts after a navigation and O68 exercises
    its endpoint; `fbf15b3d`, `17fa3199`, `4c99b802`, `ebacfe1a`, `8acd7be7`, `eab78418`,
    `8b1f660b`, `f07ce3fc` the merges).

337. THE LANE HANDOFFS, AND THE SKILL THAT GENERATES THEM [`docs/lane-*-handoff.md` and
    `.claude/skills/lane-handoff/**` never-port — the files are producer session
    coordination and retire themselves; `tests/unit/test_lane_handoff.py` never-port with
    them] (`5f5acab9`, `f9ac45b7`, `46e39327`, `21837abe`, `f06ff632`, `a15bb43e`, `e8b7200c`,
    `45f4723d` the handoff files written for each two-machine burst; `dae01ce0`, `c949f672`,
    `fe9ff979`, `d86954d9`, `afa3120c` their retirements at each burst's close, with the
    `--no-ff` merges of the laptop's `wip/` branches and the render catch-up; `04f72b5b` the
    Lane B hand-backs inboxed as Idea-266..268; `fc57826f` PLAN4's rule that a module-owned
    surface rides with the code pen — `config/taxonomy/ui-components.yaml` renders under
    `code:drydocs-web`; `cfc650eb` PLAN5 — the skill compares a queue's inputs against the
    OTHER queue's inputs, not only its pens; `de0e5b7c` PLAN6 — an item declares the venue it
    needs and the skill flags a machine that lacks it; `e89a66ca` + `47383aae` + `a8e7d2b5`
    Lane B's inputs-vs-inputs prototype preserved and pointed at from Idea-269). Nothing here
    crosses — the skill is the mechanism CLAUDE.md §0 names for a planned two-machine burst,
    and the company applies a port with one pen.

338. THE PORT INSTRUMENTS — RECONCILE-BEFORE, THE FORK POINT, THE DISPOSITION RENDERER,
    COMPLETENESS, AND THE FOUR CONSUMER-CORRECTION FIXES [`drydocs/port/**`, `scripts/**`,
    `tests/**` default_ok — take them, they are what the consumer runs; `PORT-MANIFEST.yaml`
    canonical-producer] (`2aa90898` `drydocs/port/reconcile_before.py` + the
    `scripts/reconcile_before.py` shim — the pre-apply reconciliation the consumer runs on
    its own tree; `90b93445` + `adb03f43` the fork point is measured from the two trees, never
    assumed from a tag; `eee64ce3` + `df7a57c3` `drydocs/port/dispositions.py` is the ONE
    reading of the manifest — `scripts/render_port_dispositions.py` imports it and the
    renderer refuses an unresolvable ref instead of rendering an empty table (RELAY-28);
    `6f8c7825` PORT6 — `drydocs/port/port_completeness.py` +
    `scripts/port_completeness_check.py <base> --prev <prev>`: every base-tag path absent
    from the consumer tree, by disposition, so a roll closes on the clean-add class and not
    only on the collision classes — two rolls closed without it and the consumer's by-hand
    sweep found 113 survivors at 0905 (RELAY-40); `b8a9be7d` + `a8f8bc4d` the completeness
    check covers union-append and the preflight's cited-path check reads real paths;
    `aef8dfcb` the gate-log union guard reads LINES, and `drydocs/loaders/sql/controlm_jobs.sql`
    gets its per-entry row (RELAY-43); `3d1278aa` the `pyproject.toml` row: the three ruff
    tables cross whole (RELAY-36); `6f0a8662` J57 — acceptance by test id, never by total;
    `70fdbfd6` J75 — a review that finds nothing says what it looked at; `5637d694` +
    `c15c29ba` PORT7 — the ruff PIN crosses whole with the tables, pinned by
    `tests/unit/test_port_manifest.py`; `84c042bd` + `58a76d3f` + `5656439a` PORT5 — a
    manifest rule describes the PRODUCER's tree, never the consumer's: five rows rewritten
    from "company = producer minus X" and bare consumer counts to dated observations, and a
    guard that reads the data and not the file's prose; `65b9037f` + `e8600cd6` PORT2 — two
    revisions of one document are never a rename candidate, `revision_siblings` in
    `drydocs/port/port_rename_detect.py`, measured on the consumer's real 1.00 pair). Every
    fix in this step answers a correction from the 0905 report; RELAY-46 lists them by relay
    number.

339. THE MID-APPLY RELAYS — WRITTEN AS THE 0905 REPORT ARRIVED [`docs/port/port-prompt.md`
    never-port; cited so the ledger accounts for the commits] (`f3bbac6f` + `ef5a9a36`
    RELAY-27 — the `BASE.sha` one-file fix and the `scripts/reconcile_before.py` hand-merge;
    `013b93d5` RELAY-28/29 — the renderer refuses an unresolvable ref, `classification:` is
    the consumer's on per-entry rows; `40fdc48e` RELAY-34; `ac5a6476` + `61dfe4c2` RELAY-35 —
    per-entry accumulation, deferrals by path, T24; `f2f59346` RELAY-36; `eb45a26d` RELAY-37 —
    gate-log union-append; `9fd73651` RELAY-38; `609aec91` RELAY-39; `f14c059c` RELAY-44 —
    G65/G64; `42338d48` RELAY-45 — the report read, the acceptance gate restated, the PORT5
    sweep; `9f86e3fc` J73). RELAY-46 below is this roll's one relay and it supersedes none of
    these — they said "acts at the next roll", and this is that roll.

340. ADR 0019 AND ADR 0020 — CREDENTIALS TO THE AGENT TIER, THE CONSOLE'S DELIVERY SHAPE,
    AND THE ORIGIN 403 [`docs/decisions/**` default_ok; `deploy/**` canonical-producer;
    `compose.yaml` canonical-company — the shape is the producer's, the values are yours;
    `web/**` canonical-producer] (`41ab34cf` ADR 0019 PROPOSED, `e755274b` ACCEPTED — option C,
    the agent names the session by its public handle and never by its token
    (`docs/decisions/0019-credential-propagation-to-the-agent-tier.md`); `d8b36d8e` +
    `77cae33a` + `de6cb614` + `7cc61842` WEB9 built and closed on it; `472001dc` the ADR's
    cited path is `web/src/lib/askApi.ts`; `c3d3b54f` ADR 0020 PROPOSED, `617cca63` ACCEPTED —
    option C, one path-routed reverse proxy, `/api` and `/agent` same-origin, no CORS
    (`docs/decisions/0020-console-delivery-shape.md`); `e2dc1223` + `08639e6a` + `96111884` +
    `a317dd36` WEB10 built and closed — the operator surfaces learn the same-origin shape,
    `docs/design/drydocs-web-console-runbook.md` Rev 4, `deploy/render_proxy_config.mjs`;
    `242fd6ad` + `ae846600` the ADR 0020 amendment — the proxy owns the request it presents;
    `f74d6d0c` + `ee97a351` neither proxy forwards the browser's Origin to an upstream — the
    console's Ask answered 403 on every question until this; `5605b6c5` + `dc73c4fa` U.S.
    English on the `/explorer` canvas labels and the ADK origin check described as
    same-origin-only). Two ADRs land as ACCEPTED in one range; both are the producer's
    rulings on the producer's stack and cross as records — the company's own console shape
    is its own ruling.

341. THE AGENT TIER, PART ONE — EPISTEMIC LABELS, THE THREE VERBS, THE GLOSSARY [`agents/**`
    default_ok; `drydocs_api/**` default_ok; `drydocs_core/**` default_ok; `web/**`
    canonical-producer] (`4d188307` + `169300ba` + `b1527e8c` + `887e859f` R15 — epistemic
    labeling on query answers, exact versus lower-bound with the causes named
    (`drydocs_api/epistemics.py`); `629622c7` + `544e4230` + `e067e2cf` R16 — the agent verbs
    impact, context and trace as names over reviewed QuerySpecs; `58666348` + `7e95a670` +
    `d8642a9d` + `7db46bf4` + `f3a05b92` + `2578155c` R19 — the glossary read surface and the
    term resolution index (`drydocs_core/glossary.py`)).

342. THE AGENT TIER, PART TWO — THE LEDGER READER, THE DECISION TRACE, THE ANSWER
    EVALUATOR, AND THE LANE B CHAIN [`agents/**`, `drydocs_api/**`, `tests/**` default_ok;
    `config/review-quality.yaml` canonical-producer] (`2004a01a` + `a61fc56a` + `7a3a6e7c` +
    `72aa868c` R8 — the ledger reader, the four on-demand tools and the agent-run grid;
    `3d159a59` + `cb25c85c` R18 — the qa-debug decision trace: writer, pipeline seams, admin
    read; `c0abab0f` + `066bd4b5` + `31b9905c` AGENT1 — the answer evaluator
    (`agents/common/answer_eval.py`) and `agents/graph_qa/control.py`; `ce18a957` + `ef3d3793`
    API4 — review quality (`drydocs_api/review_quality.py`); `3d16e9ac` + `14ea39fa` WEB18;
    `364d4bc8` + `ef309c81` V9; `0b20cdef` the `--no-ff` merge of the whole chain from
    `wip/v9-laptop`).

343. THE CONSOLE ITEMS — THE FREE ROUTES, THE INTAKE, THE ADMIN REVIEW QUEUE, THE REGISTRY
    CLOCK [`web/**` canonical-producer; `drydocs_api/**` default_ok; items per-entry]
    (`481d12d2` + `ca50288e` + `5cbde5b6` + `39614f82` + `2f8ea8b8` + `9a39ec2c` + `c541b858`
    WEB8 — the server declares the routes O70 left free; `5511a571` + `686cea65` + `c8c6b5dc`
    + `e57d7d5f` + `614d4374` O63 — built to ADR 0020's path map, not the retired
    `VITE_ADK_URL` or the ports, with `drydocs_api/intake.py`; `0924fdb8` + `f408b93e` +
    `7717d7f5` + `a9aea166` O50 — section 7 goes live, the admin review queue; `a6b53c1c` +
    `14f4b673` + `9fff5e57` + `7715ff16` Z6 — the spec, the registry route and the clock
    arithmetic).

344. LANE B'S FOURTH QUEUE — PROSE-FREE ASSERTIONS, THE LIST COLUMN, THE ATOMIC DUMP, THE
    LIMITS FILE, THE TYPES WRITER, TWO CLOSED SCHEMAS [`drydocs_core/**`, `drydocs_api/**`,
    `scripts/**`, `tests/**` default_ok; `web/**` canonical-producer; `config/**`
    canonical-producer] (`d364eb4c` + `30d06602` + `d2da9cbb` + `67fc7e6f` CORE2 —
    `tests/source_scan.py` gains `without_prose` and `absent()` with a mandatory positive
    control; `0c1aab8f` + `918ebd6d` + `4fa41e1d` API2 — `ColumnDef` grows a list type and the
    console exemption goes; `64319518` + `8bbae32c` + `6e351b7b` API3 — `scripts/dump_openapi.py`
    renders before opening, a failed dump leaves `web/src/generated/openapi.json`
    byte-identical; `d63f9ccc` + `359febaf` + `b19af3b5` + `0d978a91` O51 — the limits file,
    the derived signals, the admin block, three routes; `b905b892` + `edfab998` + `4a774d8f`
    WEB16 — `api:types` names the file, the writer and the variable the writer needs
    (`web/src/generated/api.d.ts`); `f2fc42e3` + `c3d8d730` + `a8bc0496` CFG3 — both schemas
    closed and clause (b) found something in each; `6be9be06` + `78277d1c` the js-cookie
    override to `^3.0.8` — clears the advisory and the five high audit findings without
    downgrading NVL; take the override, your lockfile is yours).

345. LANE B'S FIFTH QUEUE — THE STRICT TSCONFIG, THE CONSOLE STACK AS COMPOSE, FULL-HISTORY
    GATES, DEPENDENCY CURRENCY, THE NEVER-PORT ZONE IN A GUARD, THE VERSION CENSUS
    [`web/**` canonical-producer; `compose.yaml` canonical-company; `deploy/**`
    canonical-producer; `.github/workflows/ci.yml` evaluate; `tests/**` default_ok]
    (`4b2e7e94` + `058c0625` WEB17 — the strict tsconfig reaches every `.ts` outside `src`
    and the coverage HTML is ruled unpublished; `e8ff9285` + `03d28704` O72 — the console
    stack as Compose, its acceptance settled against ADR 0020; the manifest rows for
    `compose.yaml` (canonical-company) and `deploy/**` landed with the Lane A close in step
    337; `1dbbb668` + `7faddba8` + `ad65607d` + `2e94c00c` CORE3 — the gates job clones full
    history so the J74 ceiling guard measures instead of skipping; `3dacd5c3` + `445c4660` I8
    — a dependency committed more recently than its dependent is flagged, one mechanical
    question put to git, because `depends_on` is a scheduling edge and carries no currency
    claim; `8187e8f9` + `12c5a079` + `0178c126` G127 — a canonical-producer test that reads a
    never-port document mirrors `test_runbook_currency.py`'s never-port-zone idiom, so it does
    not fail on your tree as BROKEN when it means NOT HERE — this is J63's shape and the
    2026-09-03 apply hit it; `7a5e38ff` + `9ad272ab` + `ec09ce73` V10).

346. LANE B'S SIXTH QUEUE — THE SEAL WIDTH, THE SKIP-GUARD POLICY, THE BUNDLED FOLDER
    CAPTURE, THE PYTHON MATRIX, TWO RUNBOOKS, THE R10 CITATION [`drydocs_core/**`,
    `drydocs/**`, `tests/**` default_ok; `docs/design/**` evaluate; `.github/workflows/ci.yml`
    evaluate; `internal/remediation/standards-rules-registry.md` — `internal/**` crosses to
    the private company remote by rule, it never PUBLISHES] (`f0681b92` + `d45dcdf4` +
    `518baa1f` CORE5 — `drydocs_core/entity_extract.py`: the application-id width is 4 to 7
    digits with a floor, not exactly five, sourced from the tracked mapping and not relayed;
    `3871c0a6` + `e50076a2` + `f64e7b4d` CORE4 — `tests/unit/test_skip_guard_policy.py` asks
    "is this path in a fresh clone?" of `git ls-files`, so a force-tracked sample is not
    flagged like a machine-local extract; `41ed6d5e` + `7f6a52c3` + `4d59cb5e` LOAD4 — the
    synthetic SEAL capture grows to cover the seven bundled folder ids, the folder names are
    untouched; `4069c736` + `97f3e814` + `86e68b1b` J67 — the CI matrix proves more than one
    interpreter inside the declared range, and the comment that said both machines ran one
    version is gone; `5a1b5950` + `0418cb8a` L29 — the load runbook's CSV example is runnable;
    `9c33efb4` + `1dd55c92` V7 — `docs/design/drydocs-remediation-runbook.md`; `7072f54a` +
    `b77db824` REM1 — "registry R10" is the citation and the tree obeys it).

347. THE DESKTOP ITEMS — THE REGISTRY VIEW, THREE MFT SYSTEMS, THE COLLISION PROBE, THE
    TEAM REPORT PROFILE, THE HOLD KEY, THE CYCLIC-TYPE GUARD [`config/source-registry.yaml`
    per-entry — rows union by id, yours stay; `drydocs_core/**`, `drydocs/**` default_ok;
    `docs/plan/load-map.html` and `web/src/generated/load-map.json` derived; items and
    `config/taxonomy/ui-components.yaml` per-entry] (`b2445a63` + `d8540f58` + `3a9dea28` +
    `064415dc` N26 — `drydocs_core/registry_view.py`: one derivation feeds the load-map's
    By-class section, the web route's class view and `drydocs registry <loader> [--json]`;
    replica-ness is four states, never a boolean; `5c11aaea` + `2b99e4d3` N27 — three SYSTEM
    rows for the managed-file-transfer platforms, registered by pointer never by value, each
    row disambiguating the other two; `470315a2` + `fa8cf8ff` P6 — the data-center collision
    probe as `drydocs/loaders/sql/adhoc/probe_dc_table_id_collision.sql`, counts only;
    `3af331ba` K30 — the team-report header profile read against the tree, and the (f) fence
    that keeps estate volumetrics out of the tracked tree; `3f63961d` + `26afe5d5` Y7 —
    `drydocs.backlog.v3` gains the declared `hold:` key, the board's Held strip, and
    `derive_summary` excludes a held item from `next_ready` (ADR 0013 clause 3a); `697822dd`
    + `e15d319a` LOAD5 — the cyclic-type guard asserts the join is absent from executable
    SQL (`drydocs/loaders/sql/controlm_dependencies_recursive.sql`), not that a comment
    phrase is present).

348. THE CYCLIC-TYPE TRAP AND THE SMUGGLED DOT AS SKILL EVALS [`.claude/**`
    canonical-producer] (`2d45d693` the CYCLIC_TYPE trap as a research-probe-discipline
    eval — a letter that reads as cyclic and is not
    (`.claude/skills/research-probe-discipline/evals/files/cyclic-type-trap.md`); `72e86a8d`
    the smuggled dot — a value of `.` with no name a human would search for; `e0c0f4d0` the
    case's "guarded by" claim re-stated as true as of LOAD5; `2d2f96be` both cases re-verified
    at the current tree so they do not land carrying a 370-commit-stale pin; `639d841d`,
    `845bb67b`, `738028d7`, `ce1ce5fc`, `839eab1f`, `51a21690` the branch's trunk merges;
    `d31c7982` the `--no-ff` merge).

349. THE MODULE REVIEW SWEEP — CORE, LOAD, LINEAGE [`docs/reviews/**` default_ok records,
    J63-stamped — read, never edit] (`54ac5c9c` + `1ddb0781` + `2116257f` + `a53cd1c0` +
    `9fc44844` slot 1, `docs/reviews/modules/core-2026-09-07.md` — core owns the driver seam
    and it is the weakest, eight grooming candidates; `46b9970c` + `49e196cd` + `0c04fe2b` +
    `8fb4359e` + `a8a1c2f8` slot 2, `docs/reviews/modules/load-2026-09-08.md` — two findings
    that compound and a load path that does not truncate; `47f0cfc5` + `c6f52c18` +
    `fd5abe94` + `1871958d` + `3471ac73` slot 3, `docs/reviews/modules/lineage-2026-09-08.md`
    — a counted tier with no writer beside the strongest write boundary in the sweep;
    `f8c4953a` + `80078c7a` candidate 1 is two items, the gate rider then the build;
    `c2045ebe` the branch's trunk merge; `0813992d` the `--no-ff` merge, docs-only).

350. GATES AND CLOSES [`config/gate-log.md` union-append; `config/gate-prompts/**`
    canonical-company — the producer's edits to unsigned prompts are dated PROPOSED clauses,
    yours to accept or not; items per-entry] (`dd599680` K16 done on the K25 status call, the
    APPL_TYPE projection rehomed to K26; `e17dbad1` the older org/catalog gate sessions closed
    out — C35, C37, G119 SME-deferred to the Logical Container gate, C36 folded into C44;
    `f4f0b882` + `e2043d2a` C33 — Q3 ruled as the census key, a RECORD under
    software-version-context; `ecc1622c` G65 B3 restated on the registry's real zone axis
    plus proposal rows; `2f7f9485` four clauses the G64 session needs before it convenes, and
    three stale premises corrected on unsigned DPL prompts (RELAY-44 carried both);
    `7b4a4d09` four text defects from the 2026-09-08 transcription review closed, N14 done,
    Idea-305 minted).

351. MINTS AND IDEAS [`items/*.yaml` per-entry; `IDEAS.md` union-append] (`7067bfda` 21
    groom stubs, `051e781c` eight ids, `d7be63eb` 13 ids, `4e074c16` + `8977d0c7` Idea-277..283
    — the UI session's eval-case review; `8bd19f2a` + `d846951b` Idea-306 — a switch only a
    test reads; `3695a044` + `e0f2b799` CFG5, the runner item for the
    controlm-folder-identity-grain gate (`860c1d8f` corrects the second's message and carries
    the bodies for CORE6, CORE7, PORT6, PLAN9); `243992d2` Idea-269..273 — the Lane B close's
    five hand-backs; `05ac0ab8` Idea-286..290; `f59c1e56` Idea-302 — the `pyproject.toml`
    per-entry row covered dependencies and not the ruff block, the finding PORT7 closed;
    `e2260b84` Idea-303 + PORT6 (f); `5b8e2238` Idea-304 — one active data center per LB
    alias, a ruling before an edge; `69ff309f` Idea-305 — the registry's origin label is a
    domain, not a producer). Every id here minted through the allocator and pushed as a stub
    before its body (I6); the per-entry union keys on id, so a company id in the same series
    is not a collision.

352. THE PUBLISH BOUNDARY AND THE SNAPSHOT INSTRUMENT [`internal/**` crosses to the private
    company remote by rule; `agents/README.md` default_ok; `config/gate-log.md` union-append;
    `knowledge/depgraph-snapshots/**` canonical-producer; `CLAUDE.md` canonical-producer]
    (`b3ed74f2` the source-whitelist ledger instantiated with its first probed source —
    `internal/research/_registry/source-whitelist.yaml`, schema `drydocs.source-whitelist.v1`,
    no validator yet; `55c2a204` the company agent SDK's product name redacted from tracked
    prose — `agents/README.md`, `config/gate-log.md`, ADR 0007 and the renders; on your tree
    the name is yours to keep, this is the producer's publish boundary and not a correction
    of yours; `1a5d30b0` `knowledge/depgraph-snapshots/snapshot.ps1` honors
    `depgraph.capability_assert` and reports the measurement instead of guessing the cause —
    the fix for the capability gap your 0905 report recorded when the snapshot refused;
    `76cba80c` J78 — a cancelled CI run is neither green nor red, the snapshot check now says
    UNVERIFIED, `CLAUDE.md` §0 carries the three outcomes).

353. THE 0905 CLOSE-OUT, TRANSCRIBED — AND THE HAND PROMPT THAT ANSWERS IT
    [`docs/port/port-prompt.md` never-port; `docs/company-prompts/**` never-port — a hand
    prompt is hand-carried, by design self-contained, and cites no producer path]
    (`d8a52dc0` the company's port-base-20260905 close-out transcribed as the POSTSCRIPT TO
    RELAY-45 — `[SME-REPORTED]`, main = `d527afce`, four measurements RELAY-45 did not have,
    and three things the postscript refuses to do: COMPLETE stays the company's verdict, the
    82 owed paths get no deferred-paths row until they are a list, and the gate-log conflict
    is recorded adjacent to RELAY-43; `08f5113d` the SECOND POSTSCRIPT — that last caution
    withdrawn by rider: it IS the same guard, `aef8dfcb^` verbatim, and RELAY-43's fix clears
    it; keep the promote-to-EOF fix for the RENDERING reason; and the one question this side
    still owes, stated and not answered — how a union-append append-only guard survives a
    mandatory §3 redaction of already-ported signed text (the redaction in step 352); `42789fd6`
    the hand prompt, `docs/company-prompts/port-base-20260905-closeout-company-prompt.md`,
    six sections, asks for the 38-test bucket by id and the 82 owed paths as a list, nothing
    else). Laptop session, `pen: port`, pushed 2026-09-08 between this roll's pull and its
    write; the roll took them in rather than cutting the base under them.

    LEDGER COVERAGE FOOTNOTE (2026-09-08, SEVENTH ROLL). 407 commits in
    `port-base-20260905..port-base-20260908` (`git rev-list --count` at the tag); 104 read as
    ritual under the existing patterns (snapshots, claims, renders, grooms); 303 are cited in
    steps 334–353 — the 302 the ledger was written against plus the roll commit itself. No
    pattern spelling drifted this roll, so `drydocs/port/port_preflight.py` is untouched. The
    roll commit (`98270a44`, subject `docs(port):` — outside the `chore(port): roll` ritual
    pattern, so it is cited here rather than exempted) touches `docs/port/port-prompt.md`, the
    plan renders, and two research-probe-discipline eval fixtures whose machine-local
    transcript paths lost their backticks — preflight check 4 resolves every backticked path
    in the range, and a path that exists on one machine only is named plain (J71) — no
    manifest row changed, because the disposition table at the roll's parent needed none
    (RELAY-46 says why). The tag sits on the `chore(port): roll` follow-up
    that writes this sha in.

354. THE MODULE SWEEP, SLOTS 4 TO 10 AND WEB'S SECOND PASS — CYCLE 1 CLOSES ON ONE FINDING
    [`docs/reviews/**` default_ok records — point-in-time, the side that ran them keeps them]
    (`b6b0cb68` `68fc90eb` `28068704` `f4454344` `451d76ea` slot 4, api — a graph outage answers
    500 and the console reads it as a bug, no query bound anywhere; `f1a59ef1` `553dc477`
    `4fe80bee` `e3705f0f` `cf3bd014` slot 5, remediation — detect_all ships no rule denominator,
    17 of 45 rules; `cdb3d125` `fde56b88` `cd861d63` `f4800fcd` `418d94e8` slot 6, review-agents —
    four of six acceptance suites cannot fail on an empty graph, eighteen ADR 0018 shims past
    their trigger; `edb9788e` `079327e7` `0c60a919` `7383fd40` `b8046668` slot 7,
    port-docgen-docmeta — the preflight certifies a base it could not read, the most consequential
    finding of the cycle (PORT8 in step 366 is its fix); `6c272ce7` `aa6e5181` `4d606e26`
    `5767062d` `0272aa77` slot 8, plan-deepdoc-libs — the `_git` shape sweep answered negative;
    `a24d640a` `7803e3d6` `957e926a` `8097e4ed` `e3c9722a` slot 10, seams — the boundary holds
    against static imports only, and the cycle's conclusion: one defect shape seven times, six
    independent correct answers, zero written conventions; `828ba7dc` `8d62ceeb` `c323e0f9`
    `115008ba` `dcf41c32` slot 9 second pass, web — the completeness contract reached 3 of 8
    consumers, caught with dates; `3da5dfbd` `191a71ab` `b7fb5f54` `9389f246` `4167e3c9` the
    branch's merges of main into itself; `f06a5f00` the seven branch-only reports merged to main
    `--no-ff` at the Lane A close, the branch and its worktree kept as DOC4's standing venue).
    The eleven reports are the source of 41 of the 56 items minted in step 368; every candidate
    line in them says "none minted" because the backlog pen was Lane A's.

355. THE PREMISE-DRIFT REVIEW, THE OWED-PATH REVIEW, AND J76'S FOURTH MODE [`docs/reviews/**`
    default_ok; `CLAUDE.md` canonical-producer] (`f02ae4a9` Lane B's review of why five of five
    items in its burst had a premise wrong against the tree — three organs, not one: path drift
    (an existence guard closes it, PLAN12 in step 366), contract non-propagation (a shared return
    type, ADR 0021 in step 367), wrong at birth (an authoring rule only); measured 117 unresolved
    `inputs:` entries of which 4 on open items are actionable, and two things NOT to build - an
    `acceptance:` guard and a gate-prompt guard; `c25bca79` its merge; `775248a7` the company's
    hand-carried owed-path carve-out read through `drydocs.port.dispositions.classify` — the
    manifest already rules 73 of the 87, fourteen need the SME; `fcf3c00b` `05e365dd` J76 gains
    its fourth failure mode, check which VERSION of the instrument you hold, `git log -1 --
    <file>` against your base, and the fetch guardrail is recorded as its single-case form since
    2026-08-06).

356. RELAY-46'S TWO POSTSCRIPTS, RELAY-47, AND THE THREE PRODUCER DEFECTS THE 0908 REPORT
    SURFACED [`docs/port/port-prompt.md` never-port; `PORT-MANIFEST.yaml` canonical-producer;
    `config/gate-log-redactions.yaml` canonical-producer, its own row; `tests/unit/test_backlog.py`
    canonical-producer] (`9013fb72` POSTSCRIPT — company main is `b73fd9d1` not `d527afce`, the
    owed paths are already a list and 73 of 87 are ruled; `d5adcedc` SECOND POSTSCRIPT — three
    corrections to the 0908 apply read at its Phase 3, the writer never dropped `--repo`;
    `2dc38863` RELAY-6 corrected — the G35 walk was stopped by the SME relaying the company's
    signed model, not by an image; `5f0e730c` RELAY-47 — a section-3 redaction of signed gate-log
    text is DECLARED in `config/gate-log-redactions.yaml`, one row per redacted line, read by
    `drydocs/port/gate_log_redactions.py`, never excused; `1f54b5d4` its matrix row, repo_root
    anchor and refreshed renders; `fe557fce` the three producer-side defects the 0908 report
    surfaced — PLAN6 had reintroduced the unconditional `venues:` presence assert RELAY-31 carved
    out one commit earlier, split now into a travelling membership guard and a producer-only
    presence guard; RELAY-51 tells the company to hand-copy the three `venues:` keys; the epics
    row's `order:` is PER-SIDE because the producer's 28 epics carry a dense 0..27 that cannot
    seat a company-only epic; and the duplicate RELAY-48 renumbered to RELAY-50).

357. THE PORT INSTRUMENTS — THE DROP SEAM, THE NEVER-PORT PIN GUARD, THE CHUNK-1 BACK-FLOW,
    THE FRESHNESS CHECK, AND J77 [`drydocs/port/**` and `scripts/port_*.py` canonical-producer;
    `.claude/skills/reconcile-port/**` canonical-producer] (`220f293b` PORT4 — the port drop check
    gains an `accepted_drops:` seam so a ruled retirement is listed once and never re-reported at
    every chunk; `90899048` PORT3 — a crossing test that pins a never-port path now fails HERE,
    not on the consumer, `test_no_test_is_more_portable_than_its_never_port_subject`; `87a9eeaa`
    PORT1 — three back-flow adoptions from the company's chunk-1 apply, and the rule that a
    workplan naming a script names the commit it needs; `ca824405` `b855782d` J59 — the header
    freshness check `scripts/check_header_freshness.py`, and the premise it was built on had
    expired: (a) (b) (d) built, (c) handed to the port pen; `7daa2804` J59 clause (c) — the
    `updated:` header key is per-side, RELAY-50 says so and `PORT-MANIFEST.yaml` gains the
    `per_side_fields:` block that wins over any per-entry row's unnamed-fields default; `0a4e9d53`
    J77 — a roll names the commits that were red at push, convention not guard, and this roll's
    line is in its footnote; `f877f47b` DOC2 — RELAY-48, the id convention stated whole; `e48b7877`
    PLAN9 — the three live-config count pins move to a `census:` block in the venue file the
    tests read, RELAY-49).

358. THE SNAPSHOT TRIO, THE INBOX GUARD, AND VERSIONING [`knowledge/depgraph-snapshots/**`
    snapshot pen, `snapshot.ps1` canonical-producer; `tests/**` default] (`93a75bdb` the three
    snapshot.ps1 items claimed as one sitting; `4cb966c9` J65 — the script clears the leaked
    VIRTUAL_ENV before it calls poetry, so the board refresh stops skipping silently; `311d7386`
    J64 — the script refuses to scan a tree with tracked changes: scan after the commit, not
    before; `8d769863` `d43be241` `e3b820c7` `7e1c0e44` U27 — the CI check asks about the branch
    HEAD is on and Get-CiVerdict gets its five fixtures, merged `--no-ff` from `wip/u27-desktop`;
    `b5c7fbd8` I5 — an IDEAS.md capture anywhere in the file must carry the header and sit in a
    capture section; `6c84ef87` J54 closed — VERSIONING.md was already current, the fix shipped
    under Idea-163).

359. LANE B'S SEVENTH QUEUE — THE FIX-TRACKING LOADER, THE SKIP THAT COULD NEVER FIRE, THE
    VESTIGIAL GUARDS, THE CLAUDE.md SECTION 0 CLUSTER, THE DOCSTRINGS [`drydocs/**` per the
    manifest; `CLAUDE.md` canonical-producer] (`0b6d498c` `3f094b22` `438f14a6` `c6e6ac24` G90 —
    the fix-tracking loader the remediation-fix-tracking gate authorized, three properties not
    five, one resolution idiom shared with the preflight, the failing set named and confirmed as
    render staleness only; `36f242a9` `a3c8b448` LOAD7 — a skip that could never fire on a clone
    becomes a failure that can, and the path is resolved rather than guarded; `963e7cce` CORE9 —
    four vestigial guards removed, one kept, the item's own example was wrong; `97e2d5d3` three
    skips restored at the merge — a tracked never-port sample is absent on every consumer, and
    the two skip policies that disagreed are Idea-308; `ca2e1677` J61 — the shared-checkout
    recovery, executed before it was written; `4e1edb05` Y6 — a claim that MINTS ships its render;
    `7774ea60` I7 — the coordinator rule for fan-out inside one checkout; `fd876788` DOC7 — when
    the LOCAL wip branch goes; `dfd70efe` `2ca35267` `001d1621` the branch's merges of main;
    `25568a1e` `a58700b1` J60 — the eight packages with no docstring get one, D100/D104 enabled
    with the convention that keeps the rest off; `97eb9f02` `e9304fba` `51c49658` `10e5b465`
    `c3a53ce5` `e8196bf4` the six `--no-ff` merges; `d3090725` the render catch-up).

360. THE LANE HANDOFFS — THREE ISSUES FOR THE LAPTOP, TWO FOR THE DESKTOP [`docs/lane-*-handoff.md`
    never-port; `.claude/skills/lane-handoff/**` never-port] (`8e75d682` Lane A and Lane B
    handoffs closing the older base items in one burst; `776c216a` the laptop's queue, first
    issue; `5207a0b2` the second issue, 8 to 14 items; `41e018fc` the third issue at the mint-pass
    tip — 26 items for the laptop, 23 for the desktop, the overlap marks read as sequencing facts
    and ruled in the file, no web items because those belong to the UI-testing session by user
    ruling).

361. LANE B'S EIGHTH QUEUE — THE DESIGN-PAGE BYTE GUARD, THE SYNTHETIC FOLDER SET, THE ACRONYM
    CLASS, THREE MODULE RUNBOOKS, THE ADVISORY WARNINGS [`docs/design/**` evaluate on collision;
    `drydocs/**` per the manifest] (`1b55831f` `4c08cf5f` DOC9 — the committed `docs/design/*.html`
    get the roadmap guard's shape, on bytes, strict; `fe6e2fcc` `cac5c03c` REM2 — a synthetic
    Control-M folder set so the census verb is demonstrable in a clone, all 17 rules; `01518821`
    `eaaa2a9c` MM12 — acronym candidates as an extracted class with the sentence they were found
    in, 28 tests and four defects the instruments found; `880812b2` `749e06e1` `0209479b` V6 — the
    drydocs-lineage module runbook routes to the two chain runbooks and owns what neither covered,
    four of five asserted claims were wrong before measuring; `76edac30` `cf2ac76b` V4 — the
    drydocs-review module runbook, four surfaces, one verb, a live suite run; `1c3f22fd` `ef060af6`
    V5 — the drydocs-docgen module runbook and a stale count in the drift-prevention tool;
    `bda6e3d6` `71662cfc` DOC8 — the 3.14 advisory leg's 37 warnings are two classes, both
    dispositioned by name, 37/7/7/7 to 0/0/0/0; `22a50d07` `0fd80d97` `c34ee93f` `6f740ee6`
    `01143a9c` `0f10c989` `1226ae70` the seven `--no-ff` merges at the Lane A close, the V trio
    hand-resolved once on `tests/unit/test_runbook_coverage.py`).

362. THE SOURCE-REGISTRATION PROOF OF CONCEPT — FIVE AXES, SYNTHETIC STAND-INS, DUCKDB AND
    DATAHUB [`config/source-descriptors.yaml` per-entry, its own row; `config/datahub/**`
    canonical-producer; `drydocs/data/samples/**` never-port — the bundle is regenerated, never
    received; `drydocs/source_registration/**` and `drydocs_core/source_descriptors.py`
    canonical-producer] (`c3a2e2d7` `20e548dd` `5a5ede78` `bd593e4e` the TDD through Rev 2 — the
    red identity-header guard recorded, the byte-stability claim withdrawn; `fcc3c8bb` the PoC
    landed on main LINEARLY with both guard fixes — the recipes classed as somebody else's schema,
    the bundle parity compared on the decompressed payload; the five closed axes, derive then
    override then refuse, 30 descriptors, 16 stand-in tables for 10 datasets, one tracked bundle,
    DuckDB optional, a DataHub file-sink emission with no DataHub dependency; `413ff03b` Idea-309 —
    the data root is declared in three places and the one landing zone holding a payload sits in
    the repo tree; `3aed3de8` the DataHub Airflow plugin vendored into the Airflow placeholder as
    External reference; `0bf7e0fc` `d1016072` Idea-307 — a port applies by dependency closure, not
    by disposition class). Three SME questions the TDD leaves open — the right five axes, the
    catalog, axis values to the graph — are CFG8's page in step 368.

363. THE LANE A CLOSE OF 2026-09-09 [`docs/restructure/backlog/items/*.yaml` per-entry;
    `docs/plan/**` derived] (`1bd22b50` nine merges landed, six claims settled — E1 and G62 on
    hold with their reasons (an SME-deferred page; a convened-but-unconcluded session), L19 and
    MM7 back to todo under J31, DOC4 done on the first firing, S11 done as SUPERSEDED because it
    asked for ADR 0018 Option C — one Lane B note reworded at the merge for the publish-boundary
    values guard, the TDD's stale "ADR 0017 PROPOSED" mentions corrected, three new module
    runbooks gain their committed HTML for DOC9's byte guard; `feat/source-registration-poc`
    deleted local and remote on user ruling, the `../DryDocs-poc` worktree removed).

364. ADR 0021 — A RESULT NAMES WHAT IT DID NOT CHECK [`docs/decisions/**` canonical-producer]
    (`0736cae3` the number reserved by a pushed index line and stub; `981a76f6` the body —
    PROPOSED, acceptance is the SME's at sitting 1: one three-outcome type in core that never
    coerces to a boolean and renders every state; a probe returns it, never a bare bool or a
    silent empty; a declared probe registry with a guard that reads code; adoption scoped to the
    preflight and the doc-coverage report, the six precedent sites keep the name only; renders
    show NOT CHECKED where a finding would appear. Options A (convention only), B (name-based
    lint) and D (None-for-not-checked) rejected with reasons. `0736cae3` was red on DOC9's byte
    guard by construction — its `.md` edit rode without the render — and `981a76f6` is the fix,
    as its message says).

365. THE ONE MINT PASS AND THE TEAM EDITION EPIC [`docs/restructure/backlog/**` per-entry;
    `docs/restructure/backlog/epics/*.yaml` union-append, `order:` per-side; `plan.yaml`
    per-entry] (`7ed742d2` 56 items from the eleven sweep reports, the premise-drift review and
    the 2026-09-09 plan, every id from the allocator with one read per module and consecutive
    numbers after it, the render in the same commit (Y6): the completeness instrument (CORE10),
    the preflight defect (PORT8), graph_verify's anchorless suites (REV2), the boundary guard
    blind to importlib (GRAPH1), the ADR 0018 shim removal minted once for all eighteen (GRAPH5),
    the web completeness hook and its followers (WEB19 to WEB21), the `inputs:` guard (PLAN12),
    the S5 gate-prompt sweep (CFG7), the base's finish-line test (LOAD13), the coverage report
    (LOAD14), the Excel generator (DOC12), the lane-handoff mechanics (PLAN13), the
    descriptor-axes prompt and its run (CFG8, CFG9), the console-auth-boundary run (WEB22),
    Idea-309 (CORE18); epic `team-edition` (TE, order 28) with plan phase 18 — Phases 1, 2, 4 and
    6 minted (CORE19, PORT9, LOAD16, META3) with the file-class render (PORT10), the
    fragment-placement ruling (ONT6), the :CatalogField reservation (ONT5), use case 2's base
    halves (CFG10, LOAD15), the XMPL rail (CFG11), use case 3's capture (META2) and rows (CFG12),
    clause G for the data-flow gate (ONT4); Phase 0 rides N23 as clauses (h) and (i); Phases 3
    and 3a deliberately not minted; the `wired` build NOT minted because a drafted gate decides
    nothing). Your side keeps its own epics and `order:`; the 56 items are clean-adds by id.

366. THE PREFLIGHT FAILS CLOSED, AND THE INPUTS GUARD [`drydocs/port/**` and `scripts/**`
    canonical-producer; `tests/unit/test_backlog.py` canonical-producer; `.claude/skills/**`
    canonical-producer] (`0ad0e8a0` `2425c206` PORT8 — `_git` raises GitError on a non-zero exit;
    a base-resolves check runs first; `range_checks` turns an unresolvable base or a failed git
    read into NOT CHECKED on both range checks; CheckResult carries the third state and refuses
    `passed=True` with it; the CLI prints the verdict word and NOT CERTIFIED names the not-checked
    checks so `--tag` never runs; four tests pin it; the reconcile-port checklist carries the
    three-word verdict and the re-certification-postscript rule; the seventh roll re-run on the
    fixed instrument holds as issued — 407 commits, 0 uncited, 10 added documents, 0 unresolved
    (THIRD POSTSCRIPT TO RELAY-46); `6cd58802` `903060e2` PLAN12 — for every todo or in_progress
    item every `inputs:` string resolves against `git ls-files -z`, gitignored inputs skipped by
    `git check-ignore`, a malformed entry fails loudly, INPUT_EXEMPTIONS shrink-only and EMPTY at
    landing because the four genuine failures were fixed in the same commit (C42, C44, CFG4,
    DOC5, Y4), validate.py mirrors it, and it caught five fresh items citing test files they will
    create).

367. CFG7 — THE S5 PATH RIDER ON NINETEEN GATE PROMPTS, AND RELAY-52 [`config/gate-prompts/**`
    canonical-company — the rider reaches you ONLY through RELAY-52; `docs/port/port-prompt.md`
    never-port] (`6836c0c8` `e2bf8d53` — a dated header RIDER on each of the nineteen prompts still citing
    the pre-S5 monolith file names config/taxonomy-ontology-map.yaml and
    drydocs_core/ontology/relationship_vocabulary.yaml, both directories since `d84d86bc`; no
    clause text edited (L25); `updated:` moved to 2026-09-09 per the per-side rule; the three open
    items whose notes cite the names (K26, E1, L19) left alone as records of the past; RELAY-52
    names the nineteen so your copies, which win, can take the rider block by hand).

    LEDGER COVERAGE FOOTNOTE (2026-09-09, EIGHTH ROLL). 172 commits in
    `port-base-20260908..HEAD` at the roll (`git rev-list --count`; the tag lands on the
    `chore(port): ledger` fix one commit past the roll follow-up - the currency guard caught two
    retired names quoted in backticks in this very roll, the premise-drift review's own convention);
    36 read as ritual under the existing patterns (snapshots, claims, renders, grooms);
    136 are cited in steps 354–367. No pattern spelling drifted this roll.
    The disposition renderer at the roll's parent measured 294 changed paths in 8 classes (canonical-producer 70, canonical-company 20, never-port 6, per-entry 107, union-append 2, evaluate 17, default_ok 65, derived 7).
    RED AT PUSH (J77, the first roll to carry this line): ONE - `5f0e730c`, RELAY-47's landing
    (2026-09-08), failed three guards at push: the enforcement-matrix SURFACES row for
    `config/gate-log-redactions.yaml`, the stale roadmap render, and a `__file__` anchor
    resolving repo content without `repo_root()`. `1f54b5d4`, the very next commit, is its fix
    (its subject says so: matrix row, repo_root anchor, refreshed renders). A bisect that lands
    on `5f0e730c` is blaming the relay's landing, not this range's content.
    UNVERIFIED (J78 - a run cancelled by the next push, or no run at all): `6836c0c8`, `a6323c79`, `6cd58802`, `41e018fc`, `7ed742d2`, `0736cae3`, `1bd22b50`, `fe557fce`, `bd593e4e`, `5207a0b2`, `7daa2804`, `d3090725`, `ee6fe516`, `fdde7b36`, `c69cf037`, `ea810179`, `57356d56`, `b0035af3`, `6c84ef87`, `a5a8ad52`, `b5c7fbd8`, `0521ee1c`, `2673ae24`, `7e1c0e44`, `4cb966c9`, `93a75bdb`, `0a4e9d53`, `ee55d8ca`, `772ecdb6`, `e48b7877`, `f877f47b`, `813ddfa9`, `87a9eeaa`, `90899048`, `220f293b`, `7341f0e0`, `d1016072`, `0bf7e0fc`, `9013fb72`, `f06a5f00`, `1226ae70`, `0f10c989`, `01143a9c`, `6f740ee6`, `c34ee93f`, `0fd80d97`, `22a50d07`, `c25bca79`, `97e2d5d3`, `e8196bf4`, `c3a53ce5`, `10e5b465`, `51c49658`, `e9304fba`, `97eb9f02`, `fcf3c00b`, `775248a7`
    - each was re-verified by the next run that completed green on its descendant, except one
    that was red BY CONSTRUCTION and says so in its own message: `0736cae3` (ADR 0021's stub
    rode a design-doc edit without its render; `981a76f6` is the fix, one commit later). The
    20 markdown documents this range ADDS resolve every path they cite (preflight check 4).
    THE ROLL COMMIT: `8b7645f9` — `docs(port):` outside the ritual pattern, cited here.

368. L23 - THE SDLC LONG-FORM RUN BOOK GENERATOR [`.claude/skills/**` canonical-producer;
    `tests/unit/**` default_ok] (`e361dc04` the generator, spec-driven and clone-provable;
    `bd420478` section 6.0 carries the run order and the blast radius; `23c6528f` the cover
    reports what THIS run produced rather than what the spec hopes for; `c73d4e71` a table cell
    survives a pipe, a newline and a falsy zero; `612a1988` a parameter set is not a shell
    script; `9c7b5a01` the run book says whether the folder is still scheduling; `bf48829f` the
    command line is PARSED by the repo's own parser, not sliced; `cebb6571` the escalation label
    outlived the thing it described; `0bf1430e` four defects an adversarial pass found, two of
    them silent; `995b6836` three citations that survived a check without supporting their
    claim; `1a02fd64` five assertions the run book made that its sources never said; `f3b82f9c`
    the per-workflow block's empty rows say where the grain comes from; `a4d9d0d2` the parent
    skill's "no new skill needed yet" was true for a month; `8fbceccb` and `90a9cb17` the two
    guards; `5986da02` close; `1f1fa050` the merge; `5396ff37` the render catch-up).
    A SIBLING SKILL, not a change to `controlm-runbook-automation`: it generates the long-form
    SDLC run book from the graph, where the existing skill generates the template. Worth taking
    whole if you generate run books at all - and worth reading either way for the four fix
    commits above, each of which is a class of defect a generator makes that its own tests do
    not catch. `1a02fd64` is the one to read first: the generator asserted five things about a
    folder that no source it queried had said, which is what a template-shaped generator does
    when a cell has no data and the template has no way to say so.

369. SITTING 1 - TWO GATES SIGNED, ADR 0021 ACCEPTED, NINETEEN GATES DEFERRED WITH NAMED
    TRIGGERS [`config/gate-prompts/**` canonical-company - the prompts reach you only by hand;
    `config/gate-log.md` union-append; `docs/decisions/**` default_ok; `web/src/generated/**`
    and `docs/plan/*.html` derived] (`61395d3e` the source-descriptor-axes gate page and the
    wiring page swept for the sitting; `87bce0ec` CFG9 carries the slug, N18's BEFORE clause
    recorded; `783a7a4e` SIGNED OFF - registry-wiring-readiness 18/18 and source-descriptor-axes
    13/13, ADR 0021 ACCEPTED, nineteen non-blocker gates DEFERRED each with the trigger that
    re-arms it, CFG13 minted from the record).
    YOUR SIDE RUNS ITS OWN GATES and a producer sign-off is not yours - that rule is unchanged
    and this changes nothing about it. What crosses is the union-append gate-log entry and the
    two decisions the sitting made that have code behind them: the `wired` axis (step 370) and
    ADR 0021 (step 371). The nineteen deferrals are producer scheduling.

370. CFG13 - THE `wired` AXIS, A SIXTH DESCRIPTOR AXIS THAT IS PER SIDE [`PORT-MANIFEST.yaml`
    canonical-producer; `config/source-descriptors.yaml` per-entry with a NEW per-side field;
    `drydocs_core/**` default_ok; derived surfaces regenerate] (`df068d46` the axis declared per
    side and read by the gate, the load map and the DataHub emission; `321d0ae2` the boolean
    travels and the reason does not - the wiring prose leaves the console's initial chunk).
    READ THE MANIFEST ROW BEFORE THE CODE. `wired` says whether the pipeline that reads a
    dataset is BUILT, and that is a fact about ONE tree. `per_side_fields` now names it: the
    entry is never overwritten by a port in either direction, a shared dataset id carries an
    entry on BOTH sides, and a dataset with no entry is REFUSED by the reader until your side
    answers - the refusal is the reminder, not a bug. On take, keep your block and add entries
    only for ids that are new to you. TWO CONSEQUENCES FOR YOU SPECIFICALLY. Your two standing
    pins, `cm_hosts` and `controlm:deftable-xml-export`, retire under this rule: each row
    declares its own value and your gate-log records the retirement rather than the pinned
    entries being deleted (C4). And the `confirmed` flag is AMENDED by the same sitting - it
    leaves the per-side class and now crosses on shared rows as the producer's signed WHAT,
    because the second fact it was carrying, whether the pipeline is built, has its own home
    now. Company-only rows stay yours, as per-entry already rules; a producer sign-off you have
    not ratified is recorded in your gate-log, never by holding the flag.

371. CORE10 - ADR 0021's INSTRUMENT: A RESULT NAMES WHAT IT DID NOT CHECK [`drydocs_core/**`
    and `tests/unit/**` default_ok; `docs/decisions/**` default_ok; `CLAUDE.md`
    canonical-producer] (`eb18afde`).
    ONE THREE-OUTCOME TYPE in core - checked-clean, findings, or not-checked with a reason of
    forty characters or more - a DECLARED `PROBES` registry naming every adopter, and a guard
    that reads each adopter's return annotation. `bool()` on the type RAISES, so `if outcome:`
    cannot be written, and every state renders itself so a surface cannot show not-checked as
    `0` or as PASS. WHY IT IS WORTH YOUR TIME: the module sweep that produced it found the same
    defect shape SEVEN times in one cycle, with the correct answer already implemented six times
    and written down nowhere. The registry is the point - the guard finds nothing nobody
    registered, so registration is the act. Steps 375 through 378 are the first adopters.

372. ADR 0015 - WHAT AN INSTANCE INHERITS OF THE RECORD [`docs/decisions/**` default_ok]
    (`e9b22543`). A fourth file class, and the decision to ship requirements rather than
    deliberation. Take or skip freely; it binds no code.

373. CORE18 - THE DATA ROOT DECLARED ONCE [`PORT-MANIFEST.yaml` canonical-producer;
    `drydocs_core/**` default_ok; `config/**` per-entry] (`dc8dee7e`). Three files declared
    paths into one directory and the non-overlap invariant joined two of them; it now sees all
    three sources. The payload zone leaves the tree and the redirect prefix is DECLARED rather
    than inferred. Your data root is yours - what crosses is the invariant and the declaration
    shape, not any path.

374. THE BASE'S FINISH LINE, THE COVERAGE REPORT, AND THE EXCEL RUN BOOK [`tests/integration/**`
    and `drydocs/**` default_ok; `.claude/skills/**` canonical-producer] (`defda280` `1adb98dc`
    `d856b6ec` LOAD13 - from a clean clone, extract the synthetic stand-ins and run the chain to
    a generated artifact, six steps and two reasoned skips, auto-skipping WITH ITS REASON when
    Docker or the bundle is absent; `8b67f5ed` LOAD14 - the stand-ins' object classes on the
    coverage report that already exists, rather than a second verb; `6bfc9fb7` DOC12 - the
    two-tab workbook filled from the graph, and honest about the twenty columns it cannot fill).
    THE FINISH-LINE TEST IS THE ONE TO TAKE. It is the producer's answer to "does the base
    actually work end to end", it needs no company data, and it is the cheapest way for you to
    tell a broken apply from a broken tree. It landed as
    `tests/integration/test_e2e_base_finish_line.py`.

375. THE CORE CLIENT SEAM - CORE11 THROUGH CORE17, SEVEN ITEMS ON ONE FILE [`drydocs_core/**`
    and `tests/unit/**` default_ok; `config/dev-environment.yaml` canonical-company]
    (`229b323a` `31ea7be1` CORE11 - core's client gets a read path and stops dropping the
    driver's diagnostics; `6c14b941` `52281a74` CORE13 - four DECLARED waits, so an absent
    server is answered in under five seconds where it took 102.9; `30b4b0a5` CORE14 - four
    worlds stop being one `False` and the probe says which one it met; `81b0f783` CORE17 - the
    pooled-connection comment reasons from the container we actually run, not a retired service;
    `043fa44e` `b99af6d4` CORE15 - there were five silent handlers and the fifth was the one the
    item was about; `952fc509` CORE16 - the adapter handles declare the lifecycle they have, and
    a fourth site had it too; `6f5d33fd` `cd070767` CORE12 - what of core is public, declared as
    a registry; `c3f3d885` the merge order, recorded because these stack on one file).
    APPLY IN THE ORDER `c3f3d885` NAMES: core11, core13, core14, core17. They were built as
    separate items on one file and the order is not incidental. CORE13's four waits are the one
    with an operational payoff on your side; CORE14 is a first ADR 0021 adopter and turns "the
    server is unreachable" and "APOC is not installed" back into two different answers.

376. THE LOAD LANE - LOAD8, LOAD9, LOAD10, LOAD12 [`drydocs/**` and `tests/unit/**` default_ok]
    (`95090df1` LOAD8 - a scoped run node says it was scoped, and a tenant FID never reaches it;
    `c55bce86` LOAD9 - a missing audit trail is said in the line the operator reads, and a load
    stays non-fatal when the log directory is unwritable; `80ecd53f` LOAD10 - eleven duplicated
    field-validator wrappers become shared Annotated aliases, so a model that diverges from the
    helper is inexpressible; `0b3d0b52` LOAD12 - the tier with no writer says NOT CHECKED rather
    than reporting a bare `0`).
    LOAD12 IS THE ONE THAT MATTERS TO A READER OF YOUR REPORTS: `matched_dns_resolved: 0` for a
    tier that has no writer reads as "nothing matched" when it means "nothing looked", and that
    is the whole of ADR 0021 in one field.

377. THE NOT-CHECKED SWEEP ACROSS THE COMPONENTS - REV2, REM3, API5, LIN4 [`drydocs_api/**`,
    `drydocs_lineage/**` and `drydocs/review/**` default_ok; `drydocs_remediation/**` per-entry;
    `graph-tests/**` CANONICAL-COMPANY - YOURS WIN] (`e44af034` REV2 - an acceptance runner
    that cannot fail on an empty graph reports NOT RUN, never PASS; `dbd925c1` REM3 - the
    findings list gets its denominator, and unreadable stays unreadable; `0f416eec` API5 - a
    graph outage answers 503, so the console reads "down" rather than "bug"; `099b6425` LIN4 - a
    newer bundle is read AND said so about, instead of parsing silently at full apparent
    confidence).
    ONE CAUTION, AND IT IS THE ONLY PLACE IN THIS ROLL WHERE A WHOLESALE TAKE WOULD COST YOU
    SOMETHING: REV2 edits six files under `graph-tests/`, which is canonical-company. Your real
    specs win and are never overwritten. Take the `drydocs/review/graph_verify.py` half - the
    mechanism, which is what makes an empty-graph suite report NOT RUN - and re-apply the same
    shape to your own specs by hand. A wholesale `git checkout <producer-ref> -- graph-tests/`
    would replace your estate's acceptance suites with the producer's synthetic ones.

378. THE GUARD LANE - GRAPH1, GRAPH4, GRAPH7 [`tests/unit/**` and `drydocs_core/**` default_ok]
    (`fb191309` GRAPH1 - the module-boundary guard reads `importlib.import_module` and
    `__import__`, and the one real crossing is DECLARED with its reason; `e08f98cc` `6df8bb26`
    `b167786d` GRAPH4 - twenty raw-source-reading guards triaged, twenty converted to
    `source_scan`, six kept with written reasons and one deleted; `e70555a5` `30b375fd` GRAPH7 -
    the AIS typo-label guard retired, and what it got wrong said out loud).
    GRAPH7 IS THE PRODUCER PAYING A DEBT IT OWES YOU, and section 2 of the pre-merge prompt is
    the other half of it: that guard asserted a fact about YOUR tree from the producer's, where
    the labels never existed, so it passed vacuously here while being wrong. It is retired
    rather than narrowed. After you remove the labels your side passes either version, so
    nothing about this is blocking. GRAPH4 is worth reading if you maintain guards at all: a
    guard that greps raw source also matches the comment explaining the rule, which is J66, and
    the scanner built to detect that fell for it too.

379. REGISTRATIONS AND THE AGENT TIER - META2, Q28, DEEP1, AGENT2
    [`config/doc-source-registry.yaml` per-entry; `config/dev-environment.yaml`
    canonical-company; `agents/**` and `drydocs_deepdoc/**` default_ok] (`b5a36361` META2 - the
    legacy-capture corpus as a SHAPE, so an instance inherits decisions rather than restating
    them; `86403cd8` Q28 - the BMC 9.0.21 Parameters tree registered, so the capture stops
    refusing; `dfef7fd8` DEEP1 - investigate.py points at the charter instead of restating it;
    `5bbb32fd` AGENT2 - one bootstrap for the agent tier, retiring eight copied `sys.path`
    preambles and thirteen E402 suppressions).
    Q28's registration is the one with a live effect: the scraper could always capture that tree
    and the registry refused it. AGENT2 is a clean-add on eleven files under `agents/` and
    touches nothing else.

380. API7 AND THE CONSOLE'S COMPLETENESS PASS - WEB19, WEB20, WEB21, WEB23 [`drydocs_api/**`
    default_ok; `web/**` canonical-producer BUT read divergence #K7-K15 first] (`068014ce`
    `f00aa681` API7 - the intake write handlers authorize the record BEFORE the write, so a
    cross-persona mutation cannot commit and then be found; `b36e908e` `420d90bf` WEB19/WEB20 -
    the completeness envelope travels with the rows through one shared hook, five migrations,
    and a guard that fails the sixth; `0f9b86d9` WEB23 - 79 KB stops arriving first, the load
    map leaves the entry chunk; `affa37eb` WEB21 - the bundle ratchet was thirteen points under
    the tree and is re-pinned to a measurement this venue could actually take).
    API7 IS A REAL AUTHORIZATION FIX and is the one to take on its own terms: the handlers
    committed, then checked ownership. Take `drydocs_api/**` by name. For the four web commits,
    take files BY NAME rather than `git checkout <producer-ref> -- web/src`, which re-adopts the
    held folder-attribution UI.

381. CFG14 - THE CONSOLE ROSTER DECLARED ONCE, AND THE CONSOLE-AUTH GATE [`config/**` per-entry;
    `PORT-MANIFEST.yaml` canonical-producer; `MODULE_MAP.md` per-entry; `config/gate-prompts/**`
    canonical-company; derived surfaces regenerate] (`f48c5d7e` mint; `7ba7e2b8` gate
    `console-auth-boundary` SIGNED OFF - P1 confirmed, P2/P3/P5 declined, P4 deferred to a claim
    map, P6 added; `e02d844c` the roster declared once, the claim block DEFERRED rather than
    absent).
    The roster becomes a declared config file with a schema, and the derived row in the manifest
    gains `console-personas.json` - a default-paths `render_board.py` run refreshes it with the
    rest, so REGENERATE it, never carry it (J43). The claim block is deferred with its reason
    recorded, which is the shape to copy: absent-with-a-reason, not absent.

382. PORT11 - A GATE-LOG REDACTION DECLARES WHOSE ACT IT WAS [`config/gate-log-redactions.yaml`
    canonical-producer; `config/dev-environment.yaml` canonical-company; `drydocs/port/**`
    default_ok; `MODULE_MAP.md` per-entry] (`1e50820b` the gate-log close-out confirmed and
    PORT11 minted; `23a22dd0` the build).
    THIS IS RELAY-55, AND IT IS THE ONE THAT GIVES YOU SOMETHING BACK. Every row now carries
    `side: producer | company` and the stale check is scoped to the owning side, so once you
    declare `side: company` in `config/dev-environment.yaml` you may restore the true name in
    your own `config/gate-log.md` under a dated postscript and stay green. A checkout that has
    not declared reports NOT CHECKED with the reason naming the key - never clean and never
    stale, because assuming producer would recreate the failure on the tree least able to notice
    it. Both states are legal and the choice is yours.

383. PORT12 - A COMMIT SPLIT ACROSS TWO DISPOSITIONS PORTS AS A BROKEN HALF [`drydocs/port/**`
    and `scripts/**` default_ok; `docs/port/port-prompt.md` never-port; `MODULE_MAP.md`
    per-entry] (`aa3ce109` mint; `0d9deb80` the body, and RELAY-56; `3bd1171d` the detector and
    the class that has already landed).
    THIS IS THE INSTRUMENT BEHIND RELAY-57, and the reason that relay could be written at all. A
    range adds a definition to a file you hand-merge and a reference to it from a file that
    reaches you unattended; the two halves are one commit and only one of them crosses on its
    own. `scripts/port_split_pair_check.py <previous-base-tag>` REPORTS this rather than
    refusing - deliberately outside the preflight's seven checks, because a split commit is
    legitimate and what it owes is a relay line, not a blocked roll. G130 is its positive
    control, pinned first in its test file so the instrument cannot go quiet.

384. THE LANE MERGE OF 2026-09-10 - TWENTY-SIX BRANCHES, THIRTY ITEMS [merge commits; the
    dispositions are those of the steps above] (`83c72484` `43cdc972` `77cb98ce` `90e55ea6`
    `4402ecdc` `858b9ebd` `121aa4ed` `7ad51091` `91e5ef0d` `5ac451fc` `d66a25d7` `0016a73f`
    `a937c55f` `4e9b144b` `5a1964c3` `701c3f12` `a011f559` `a6c08d2b` `07fccc19` the build
    lane's `wip/*-laptop` branches; `d4abe8d1` `feat/web-completeness`; `2f14b064` the burst's
    renders, five status corrections and the two things the merge itself exposed; `47c29129` the
    handoff retires, 23 of 23 done).
    NOTHING TO APPLY FROM THE MERGES THEMSELVES - they are here because the ledger's ritual
    exemption is deliberately narrow and a merge is not on it. The CONTENT is steps 374 through
    379. One thing worth knowing if you bisect: `47c29129` is RED on the trunk and its own next
    commit is the fix (see the footnote).

385. THE PLANNING AND HANDOFF DOCUMENTS [`docs/restructure/EndGoalTeamsEdition.md` NEVER-PORT
    by a new manifest row; `docs/company-prompts/**` never-port; `docs/reviews/**` default_ok;
    `docs/design/**` evaluate] (`03e903eb` the Teams Edition plan and both ultra-review records,
    with a measured status block; `29247331` the pre-merge company prompt for `port/20260908`;
    `0ad69e99` `ff5430d3` `52cc7cf5` the lane handoffs; `0e1620c6` two citations the handoff's
    own retirement broke; `2c017f93` the plan gains an effort lever and records a
    model-availability hold).
    THE PLAN IS NEVER-PORT BY A NEW MANIFEST ROW and that is deliberate: it is the producer's
    own sequencing, it names producer venues and producer budgets, and it would read as an
    instruction on your side. `29247331` is the pre-merge prompt you already have. Nothing here
    is asked back.

386. THE PREFLIGHT LEARNS THAT A CITATION CAN BE DELIBERATE [`drydocs/port/**` and
    `tests/unit/**` default_ok] (`1b24ba2d`). The cited-paths check had `RECORD_PREFIXES` for a
    whole document and nothing for a single PATH, so it refused this roll over four correct
    citations - two naming YOUR tree, two naming files a held plan unit will create. Two
    declared tables now carry them, each entry with its reason, and the planned-path table
    EXPIRES: a guard fails when the file appears, so an exemption cannot outlive the work it
    waits on. Take it with the rest of `drydocs/port/**` if you run the preflight; the two
    corrections riding with it are producer-side documents.

    LEDGER COVERAGE FOOTNOTE (2026-09-10, NINTH ROLL). **144 commits in
    `port-base-20260909..port-base-20260910`, 39 ritual, 105 cited in steps 368-386**, and
    those are the numbers AT THE TAG. Read once as 142 / 37 / 105, which was true when the
    count ran and false two commits later, because A COVERAGE FOOTNOTE CANNOT COUNT ITSELF:
    the count is taken before the commit that writes it, so the roll's own
    `chore(port): ledger` commits are always outside it - here `327f2ec9` and `bb73c182`,
    both ritual, which is why the CITED number was right at both readings and only the
    totals moved. The eighth roll met the same thing and worked around it in prose ("the tag
    lands on the `chore(port): ledger` fix one commit past the roll follow-up"); stating the
    rule is cheaper than re-deriving it every roll. Take the totals as as-of the tag and the
    cited count as exact. No pattern spelling drifted this roll. The disposition renderer at HEAD measured 228 changed paths in 8 classes
    (canonical-producer 40, canonical-company 12, never-port 6, per-entry 52, union-append 2,
    evaluate 5, default_ok 102, derived 9).
    RED AT PUSH (J77): FIVE on the trunk, and the number needs its denominator or it reads far
    worse than it is - 34 further reds in this range sit on `wip/*-laptop` and
    `feat/web-completeness` commits, where a mid-item red is the build lane working and the
    merge is what settles it. The five on `main`: `550cec20` and `5b8d7289`, CLAIM commits that
    MINTED an item and shipped no render, which is the Y6 case where the status-only tolerance
    correctly does not apply (`df068d46` and `dc8dee7e` are their fixes); `5396ff37`, the web
    job's initial-chunk ceiling, which is the measurement WEB23 then went and fixed properly;
    `03e903eb`, a publish-boundary guard, and see the next line; and `47c29129`, where retiring
    the lane handoff turned HEAD red because `docs/design/drydocs-docgen-runbook.md` cited the
    self-deleting file (`0e1620c6` is its fix, one commit later).
    ONE OF THOSE FIVE GETS A SENTENCE OF ITS OWN, because it is a publish-boundary event and
    burying it in a count would be the wrong call. `03e903eb` added a review record carrying the
    retired internal org acronym that the J55 guard exists to keep out of the publishable tree,
    and `5b8d7289` inherited it. The window was three commits on `main`; `dc8dee7e` corrected
    the path that carried it, and the guard has been green since. The producer tree at this tag
    is clean, the file crosses as `default_ok`, and there is nothing here for you to act on - it
    is recorded because a roll that hides its own boundary failures is not worth reading.
    UNVERIFIED (J78 - a run cancelled by the next push, or no run at all): 55 of the 142,
    32 cancelled and 23 with no run at all. Each was re-verified by the next run that completed
    green on its descendant. The 7 markdown documents this range ADDS resolve every path they
    cite (preflight check 4), two of them by a DECLARED exemption naming YOUR tree rather than
    by resolving here - step 386 says which and why.
    THE ROLL COMMIT is cited in the follow-up `chore(port): ledger` commit, which is ritual and
    terminates the chain.

387. THE NEO4J ROUTE THAT LOADS IN EVERY VENUE, AND THE FIVE DRIFT POINTS IT LANDED ON
    [`.claude/skills/**`, `CLAUDE.md`, `reference/**` canonical-producer; `tests/unit/**`,
    `drydocs/loaders/**`, `drydocs_core/schema/**` default_ok; `internal/**` never-port]
    (`c4a3b16d` the skill and the sweep; `cff43145` the mirror citations).
    **TAKE THIS ONE WHOLE, and it may be the most immediately useful thing in the roll for a
    session that is not running Claude Code.** `CLAUDE.md` §2 routed every Neo4j task to the
    `neo4j-skills` PLUGIN. A plugin loads only under Claude Code; in any other venue that route
    resolves to NOTHING - no error, no lens, no signal - and a session can run a full sitting
    doing Neo4j work with no reference at all. `.claude/skills/neo4j-db/SKILL.md` is a
    FILESYSTEM skill, so it loads everywhere, and it carries what the vendor plugin cannot know:
    the two-database topology and the three retired names, the Cypher-25 empty-statement
    boundary and the client-side splitter that exists because of it, the `Neo4jClient` API with
    `run()` as the WRITE path, the four CORE13 waits, and eleven failure modes already paid for.
    The plugin route is NOT deleted - it is correct under Claude Code and stays as an additive.
    FIVE PRE-EXISTING DRIFT POINTS went with it, all of them routes to skills that load nowhere:
    the `aura-*` skills (deleted 2026-07-06), `agent-memory` and `snowflake-graph-analytics`
    (outside the declared keep-10, the second also disabled), a REGISTRY entry listing twelve
    plugin skills against CLAUDE.md's ten, and the Oracle row pointing at the disabled
    `db@oracle-skills` vendor plugin rather than the repo-local `oracle-db` skill.
    FOUR STALE `apoc.cypher.runMany` CLAIMS, wrong for eight weeks: that procedure has not been
    called anywhere since D5 (2026-07-18), having been dropped because it splits on semicolons
    inside comments AND silently no-ops DDL - the class that once printed "Constraints applied."
    having created zero. If your tree still routes multi-statement templates through it, that is
    the thing to check first.
    AND THE VERSION, which is the one that would have crossed WRONG: the platform reference said
    "Server: Neo4j 5.x" while the pin is `neo4j:2026.05.0-enterprise` with a store that cannot be
    downgraded. `neo4j = "^5.20"` in `pyproject.toml` is the PYTHON DRIVER floor (resolves 5.28.4)
    and is a different axis. `constraints.cypher`'s header now describes its DDL by SHAPE rather
    than by a version number, because a version in a comment goes stale and a shape does not.
    SEVEN DEAD LOCAL-MIRROR CITATIONS retired in `cff43145` (`llm-graph-builder`, `sdw-sosa-ssn` -
    neither exists on any machine this repo has run on), including one under a `verified:` stamp
    that asserted they resolved. J71 already rules the class: a machine-local path in a tracked
    document is an existence claim that is wrong on every other machine.
    THE GUARD IS THE PART THAT MATTERS TO YOU LONGER TERM. ADR 0018 D5 put four routing documents
    under `tests/unit/test_runbook_currency.py`; `reference/**` routes every platform task to a
    skill and was not among them, so nothing had looked at that tree since June. Four reference
    documents are now under it, and it caught a real stale citation on its first run. STILL OPEN,
    said so it is not mistaken for done: the cited-path checks resolve only paths carrying a known
    EXTENSION, so a bare DIRECTORY citation is invisible to both this guard and the preflight's -
    which is exactly how the seven mirror citations survived.

388. THE VENUE FINDINGS AND THE PLAN'S CAPABILITY AXIS [`docs/restructure/**` per-entry;
    `docs/restructure/EndGoalTeamsEdition.md` never-port; `internal/**` never-port]
    (`89dcecba` `c8fd9b49` `84ecb090` `679f665c` the findings and the three ideas; `dea57a69` the
    plan's close of the ninth roll).
    Producer-side capture, nothing owed. Recorded here because ONE fact in it may matter on your
    side: a capability layer has three reachability classes and this tree distinguishes none of
    them - filesystem skills and sub-agents are tracked and cross WHOLESALE, a Claude Code plugin
    lives outside the repo and crosses NEVER, and `skillOverrides` enablement is gitignored and
    also crosses never. So `.claude/settings.local.json` saying a skill is "off" is a producer
    machine's state and has never been yours; `oracle-db` is ON in any venue that does not read
    that file. If your venue loads filesystem skills from `.github/skills/` as well as
    `.claude/skills/`, note that this repo ships nothing under the former. Nothing is asked back.

    LEDGER COVERAGE FOOTNOTE (2026-09-10, TENTH ROLL - a same-day re-roll). 10 commits in
    `port-base-20260910..port-base-20260910b`, 3 ritual, 7 cited in steps 387-388. **WHY A
    SECOND TAG THE SAME DAY**, since a reader will ask: the ninth roll was certified and the
    consumer had not started applying it, and step 387 fixes a defect that would otherwise reach
    them as a REGRESSION - their own session had already built the same fix on their side, on
    five canonical-producer paths, so applying the ninth roll would have reverted their work AND
    reinstated the dead route. Rolling again before the apply is the cheaper of the two, and it
    is the shape the fifth roll used for the same reason. The ninth roll's steps 368-386 stand
    unchanged; this range only adds to them, so the consumer applies ONE range,
    `port-base-20260908..port-base-20260910b`.
    RED AT PUSH (J77): none in this range. UNVERIFIED (J78): checked at the tag.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare). **THREE TRACKS, RUN IN
ORDER, AND EACH ONE IS CHEAPER THAN THE ONE BELOW IT** — stop at the first that fails,
because every figure a later track produces is a figure about a tree the earlier one
already said is broken. The numbering was corrected 2026-09-10: this gate read
"Track 1 (portable)" followed by an unlabelled full-suite bullet, so it named one track,
implied a second, and delivered two — which is how the runtime smoke went missing for ten
rolls without anyone noticing there was a slot for it.
- Track 0 (RUNTIME SMOKE — added 2026-09-10, and it is FIRST because it is the cheapest
  and it is the one this gate has been missing):
    python -c "import drydocs.cli"
    drydocs --help
  Two commands, about a second, no database needed. **THE GATE HAS NEVER RUN THEM, and the
  cost is already on this roll's record.** RELAY-56: `constraints_detail()` was absent on the
  consumer tree while `drydocs/cli_schema.py` called it — every unit test passed, for TEN
  DAYS, and it surfaced only when a person typed `drydocs bootstrap`. RELAY-57 names a worse
  one in the same family: a module-scope import of three constants from a hand-merged file,
  whose symptom is `ImportError` while `drydocs/cli.py` is still importing, so EVERY command
  dies — `drydocs --help` included. A suite that imports modules individually never sees
  either. `CLAUDE.md` §6 has required all three parts of this gate (`pytest`, the root
  import, `--help`) for ordinary commits the whole time; a port was being held to a weaker
  standard than a one-line change. If Track 0 fails, stop: the remaining tracks will tell you
  which tests pass in a tree whose CLI does not start.
- Track 1 (portable):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Producer reference at `0c4105b` (step 54): 126 passed / 0 skipped WITH the
  production CSV present (+2 over step 52 from the S2 module-boundary additions;
  sample-backed tests skip without the CSV — at step 48 the CSV-absent figure was
  114 / 3). Company baseline is ABOVE the
  producer floor — compare against your own PORT-REPORT-e60822fc numbers, not these.
- Track 2 (FULL SUITE) — `pytest tests/unit/`. The contract is ZERO REGRESSIONS BY TEST ID against the
  consumer's OWN prior PORT-REPORT, with every other failing id bucketed BY NAME in the
  PORT-REPORT (pre-existing / new test that crossed / unskipped) — a failure that is not
  bucketed is a failure, a count is not a bucket, and a deliberate remaining regression
  carries the ruling that supersedes it beside its id (restated 2026-09-08, RELAY-45; the
  earlier "ZERO failures" wording described a tree no consumer has ever had, and the
  by-test-id comparison the 2026-09-08 apply ran is the instrument that settles it);
  producer reference at the CERTIFIED BASE (`port-base-20260824c`,
  laptop `NewThinkpad`, 2026-08-24): **2385 passed / 9 skipped**, with the production
  sample CSV ABSENT (3 of the skips) and `RECONCILE_BEFORE_DIR` unset (6). (The same-day first base
  `port-base-20260824` @ `68b53716` measured 2382 / 9 at the same venue; the delta is
  the guards that rode steps 214-220.) (The prior reference, two rolls back,
  was `a4e65d26` desktop 2026-08-19 at 2224 / 5 / 13 deselected — kept here only so the
  chain is readable; a producer figure is never your acceptance number.) With
  no RECONCILE_BEFORE_DIR — your figure lands ABOVE your own e60822fc baseline,
  never compared against ours; skips are
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
- THE FAILING SET, NOT THE TOTAL (J57, 2026-09-08). Every figure in the bullet above is a
  reading; the acceptance is the sorted set of failing test node ids
  (`poetry run pytest tests/unit -q -rf | grep "^FAILED" | sort`) diffed against the set in
  your last PORT-REPORT — added ids are the finding, removed ids are progress, and the total
  stays beside the set as the number people read. Reason, here because it is the rule: on
  2026-08-27 two sessions measured the same failing total on one tree and took the agreement
  as confirmation, and one failure was new and self-inflicted; the eighteenth postscript
  said it for rows and for the 21-against-21 compare, and it holds for every acceptance
  line on this page. A "clean" claim after a targeted fix also runs the repo-wide guard
  family the reconcile-port skill names by test-file path (module boundary, render
  determinism, no-render-parsing, repo-path currency) — a targeted run cannot see those.
- CI guards green: test_schema.py (EXPECTED_CONSTRAINTS company-based — see ledger;
  every active edge has its supplement block), test_classification.py,
  test_taxonomy_ontology_map.py, test_backlog.py, test_doc_outline.py,
  test_enforcement_matrix.py, test_gates_json.py.
- J7 reconcile guards with RECONCILE_BEFORE_DIR set: all pass (producer-side at the
  back-flow enactment: 12 passed / 4 skipped; the J16 manifest-coverage /
  default_ok / backlog-no-regression checks run unconditionally, no env var needed).
- The roll-close COMPLETENESS check (new 2026-09-08, PORT6): from the apply worktree,
  `python scripts/port_completeness_check.py <base-tag> --prev <previous-base-tag>`
  exits 0 — every path at the base tag absent from your tree is either in a
  `deferred-paths` row or in the canonical-company ruling band, and every union-append
  markdown file holds every `## ` heading the tag's copy has. PRESENCE only; it does not
  replace `--numstat`, which answers a different question (this roll or not). The
  PORT-REPORT carries its last line verbatim beside the `--describe` line.
````
