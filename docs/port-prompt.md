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

**Roll state (2026-08-06).** Steps 52–54 COLLAPSED at the 2026-08-03 roll (applied in
PORT-REPORT-f71967db and PORT-REPORT-40c35724). The live ledger runs **55–101**
below, delta since `40c35724`. Two company ports (PORT-REPORT-6713c142,
PORT-REPORT-5f79d145) landed MID-RANGE with no producer-verifiable range or
acceptance numbers, so NO step is collapsed yet — collapse waits for a
PORT-REPORT the producer can review against git (guardrail 8), not a report
name cited second-hand. The
verification tags introduced at step 49 (`[SME-SIGNED]`, `[LIVE-VERIFIED]`,
`[TEST-PINNED]`, `[STAGING-ONLY]`, `[RECORD-CORRECTION]`, `[UNRULED]`) carry
forward; anything untagged is NOT confirmed — treat contracts as ASSUMED until
your side validates them (the T10/T13 discipline).
**ROLL-PROCEDURE RULE (added after two ledger gaps in one cycle):** currency is
verified by diffing the ledger's claimed coverage against
`git log <last-ported-head>..HEAD` COMMIT-BY-COMMIT — never by eyeballing back
from the newest entry. Both gaps (the f71967db port unrecorded here;
O27/O28/C17/Q7/R6/S1 never ledgered) were caught by the company session's own
range enumeration — the guardrail-2 safety net working, not a reason to keep
the habit.
**THIS ROLL (2026-08-06) IS THE FIRST ONE RUN THAT WAY, and it was run BEFORE the port
rather than reconstructed after it** — breaking the three-roll streak the note above
describes. 25 commits had landed since the step-96 roll (`0bad42a`) with no ledger
entry; walking `0bad42a..HEAD` commit-by-commit produced steps **97–101** and confirmed
the rest are ritual (7 snapshots/renders) or producer-only backlog state (claims, the
O44 groom, Idea-75). Unported range as of this roll: **`5f79d145..HEAD` = 106 commits.**

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
- **`PORT-MANIFEST.yaml` = canonical-producer + a company-only `default_ok:`
  appendix** (PORT-REPORT-*.md, .vscode/**, …). Take producer wholesale, then
  re-append the company block — dropping it reds their J16 coverage guard.
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

STEP LEDGER — delta since `40c35724` (steps 43–54 collapsed above, applied
through PORT-REPORT-40c35724). Each sub-stream carries its producer-side
verification status in [BRACKETS]; spend review on [UNRULED].

55. BACKLOG DUPLICATE-KEY GUARD [TEST-PINNED] (`c5b689e`). Direct answer to the
    defect YOUR DD6 session found: PyYAML is last-key-wins, so the duplicate
    `summary:` your port merge shipped passed every backlog guard. New
    `test_no_duplicate_mapping_keys` parses via a SafeLoader subclass that
    reports every duplicate key at every depth with both line numbers. Ports
    normally (no company adaptation known for this file). Run it against YOUR
    rebuilt backlog — it must pass; your pre-rebuild `1a3aff20` state is the
    proof-case it exists to catch. Phase 1 of the backlog-at-scale epic
    (IDEAS 2026-08-03); phases 2–3 (per-item sharding, graph query surface)
    are NOT in this range — they gate first.

56. G51 — `ddschema` PROVISIONED + DATABASE-NAME GUARD WIDENED [TEST-PINNED]
    (`21c46b8`, claim `f0ca0cc`). `01_databases.cypher` now creates `ddschema`
    (NOT aliased into `ddall` — deliberate, the comment says why);
    `test_database_names.py` matches any `*DATABASE*` constant (proof order:
    the widened guard failed on exactly `SCHEMA_GRAPH_DATABASE`/`ddschema`,
    then the DDL turned it green); topology anchor 4→5 names; ADR 0002
    amended; gate-log RECORD entry (a record, not a gate — nothing to ratify);
    runbook Rev 6 + rev pin 5→6 TOGETHER (the L21-noted mixed-pin file — take
    both or neither); run-drydocs skill chain updated.
    ***THIS DISCHARGES THE `ddschema`-DDL CLAUSE OF YOUR DD6*** — after
    applying, DD6 narrows to `_client(database)` + wiring the two deferred
    verbs (T22). `EXPECTED_CONSTRAINTS` does not move. The topology-anchor
    test asserts the producer's five-name SET — verify it against YOUR
    `01_databases.cypher` on apply rather than assuming the sets match.

57. L22 — U.S. BUSINESS-ENGLISH STYLE GUIDE + ADOPTION [SME-SIGNED]
    (guide `6aeaadd`, adoption `e4d05dd`; grooms/claims `480fa04`/`bf2e4bd`).
    NEW `docs/style/` (guide + idiom inventory) with a NEW PORT-MANIFEST row:
    `docs/style/**` = canonical-producer (the J16 guard forced the row, as
    designed). CLAUDE.md §6 gained the prose-style working agreement; the
    documentation skill opens with it; exec overview → rev 7 (21 idioms
    rewritten; HTML stays its single source — decision in the rev line);
    whitepaper: 2 edits applied identically to `.md` + both renders. FENCE:
    mechanism names are never renamed by a style pass, and "crosswalk(s)" is
    an SME-approved exception (company-internal vocabulary) — the guide
    records both. Company adaptation: none expected; your prose sessions
    inherit the guide via CLAUDE.md.

58. C23 — DQV SEED RULED **DEFER** [SME-SIGNED] (`11f9ab9`, claim `9c8e3d9`;
    gate-log `dqv-seed-disposition`). The bootstrap :Metric/:Dimension catalog
    STAYS; revival trigger (first measurement feed = temporal-runtime
    freshness observations) recorded in `ontology.cypher` above the seed.
    Vocabulary +4 `c23_*` entries (per-entry union: `c23_in_dimension` ACTIVE
    — registered retroactively for a bootstrap-written edge — the other three
    PLANNED; new `quality` domain). `schema_graph.cypher` + `gates.json`
    regenerated (both drift guards fired first). GUARDRAIL 6: this is a
    producer gate ruling — union-append the gate-log entry and take the vocab
    entries, but your OWN measurement-feed timeline decides when planned
    flips; nothing here writes your graph. `EXPECTED_CONSTRAINTS` unchanged.

59. G51 TAIL — THE TOPOLOGY GUARD THAT LET FOUR DATABASES STAND [TEST-PINNED]
    (`aa0a0eb`). Step 56 added `ddschema` to the DDL, not to the surfaces that
    ENUMERATE the topology. `test_databases_match_provisioning_script` was a
    subset check whose own docstring promised equality; it is now bidirectional
    and FAILED on `['ddschema']` before the config was touched. Same commit:
    runbook Rev 7 WITH the `test_doc_traceability_loader` rev pin 6→7 (the L21
    mixed-pin file — take both or neither), `ingest.sh` 5→6 steps, provisioning
    README/`provision.ps1`, repo-README, the run-drydocs skill's wrong
    `NEO4J_PLUGINS` advice, `enforcement-matrix.json` regenerated.
    ***CAUTION — THIS GUARD WILL RED YOUR TREE, CORRECTLY.***
    `config/dev-environment.yaml` is canonical-company and you took
    `01_databases.cypher` with `ddschema` at step 56, so the widened guard fails
    until YOUR file gains `schema_meta: ddschema` under `neo4j.databases`
    (structure to adapt by hand, value yours — the standing divergence).
    `EXPECTED_CONSTRAINTS` does not move.

60. K7 — APPLICATION↔CONTROL-M ATTRIBUTION CLOSE-OUT GATE **SIGNED OFF**
    [SME-SIGNED] (gate-log `seal-app-ref-edge-reshape`, 24/24; §G6-RIDER was
    already ruled at C17 2026-08-01 and is NOT re-opened). Grain moves job →
    FOLDER; the edge is `BELONGS_TO_APPLICATION` (LOCAL, `prov_maps_to: ~`)
    onto the app's Batch `:Port` — NOT `:BusinessApplication`, which is
    supernode avoidance, not taste. K2 matching DEMOTES to a fallback that is
    always DISCLOSED via the origin flag. `:Batch` bridge RETIRED
    (`arch_contains_batch`/`arch_contains_folder` planned→deprecated) — do NOT
    confuse these with `m3_contains_folder`, which stays ACTIVE and is the
    load-bearing fan-out path. Build items K8–K13 opened BY the gate.
    GUARDRAIL 6: union-append the gate-log entry, take the vocab entries
    (`m3_belongs_to_application` is PLANNED — no loader) and the map flip;
    every graph write stays yours.
    GUARDRAIL 7: this is a GATE commit — do NOT run the no-downgrade guards
    across it. The arch_* deprecation is an AUTHORIZED downgrade and the
    gate-log entry is its authority.
    ***YOUR T1 PREMISE CHANGED.*** T1 is the K2 JOB-grain live load; that grain
    is now superseded. Re-scope T1 to the folder grain rather than running it as
    written. Second live-behaviour note: your TWO app-code loaders (Control-M +
    the AutoSys twin) write `Port.active` by derivation — K10 replaces that
    boolean with per-port `active_state`, and your already-active ports
    grandfather as `confirmed` with the Control-M link as provenance (§G4-RIDER).
    `EXPECTED_CONSTRAINTS` does not move.

61. K9 — THE K7 DEFINED-MAPPING STORE [TEST-PINNED] (`17d9e08`; claim
    `a1b9388`, after the dead remote claim was released at `1807df0`). NEW
    `config/overrides/app-code-mappings.csv` → `app_code_mapping` table +
    `v_app_code_grid`/`v_dual_coded_migrations` in `var/mapping.db` → the
    `app-code-mapping` /mappings domain with an O24-verbatim draft endpoint;
    ONE shared validator (`validate_app_code_row`) serves ingestion AND
    drafting, so an artifact can never be refused at materialization. §E2
    asymmetries are built in: rows ARE the source of record, overrides may be
    PERMANENT (no status column; rationale required on override/manual-pin),
    and `matched-fallback` is REFUSED at authoring (derived at load, §B3).
    `K2_SHAPE` → `ControlMFolder -[BELONGS_TO_APPLICATION {seal_app_ref}]->
    Port`; `draft_changeset` rekeyed (app_code keys, `app_id=` target grammar
    — post-S3, and no committed manual CSV exists producer-side to protect);
    TEMPLATE rekeyed the same way. The manual-loads PARSER deliberately still
    enforces the job-grain shape until K8 — test-pinned with the rationale —
    so YOUR real tier-5 CSVs (T4) keep parsing unchanged; the new grammar
    arrives only in NEW artifacts, which queue fail-closed until your K8.
    Console note: the job-grain drafting tray now fails closed SERVER-SIDE
    (§A1, ruling cited in the error) until K11's steward screen lands.
    `EXPECTED_CONSTRAINTS` does not move; nothing writes the graph;
    `m3_belongs_to_application` stays planned.

62. COMPOSITE-KEY SERIALIZATION STANDARD [SME-RULED, TEST-PINNED]. Two
    in-chat SME rulings, same session as K9: (1) the `ctlm_id` DOT composite
    (`folder_id.job_id`, the psgmgr-derived convention, P2 §B precedent) is
    THE serialized form of the job node key; (2) key-cell `field=value`
    pairs join with **`:` not `;`** — the semicolon is the SQL statement
    terminator. NEW standard doc
    `knowledge/standards/technology/composite-key-serialization.md` (+ the
    standards README index row); `_parse_key` in
    `drydocs_core/manual_mappings.py` flipped `;`→`:`, fixtures updated.
    TIMING IS THE POINT: the flip landed while ZERO manual CSVs are
    committed producer-side (`manifest files: []`), so nothing migrated.
    ***YOUR SIDE IS DIFFERENT (T4):*** if you hold REAL registered tier-5
    CSVs under `internal/`, their key cells still say `;` — convert them in
    the same commit that takes this parser change, or hold the whole step
    back until you can; a half-applied step strands your committed rows at
    parse time. K14 (value-form conformance sweep) is groomed producer-side
    and ports as backlog only.

63. K8 — FOLDER-GRAIN ATTRIBUTION LOADER; THE K2 JOB-GRAIN WRITER RETIRES
    [TEST-PINNED, GRAIN-BREAKING] (`4df4df2`; claim `72777d8`). NEW
    `drydocs/loaders/folder_attribution.py` + `folder_attribution.cypher`
    write the ruled `(:ControlMFolder)-[:BELONGS_TO_APPLICATION
    {seal_app_ref}]->(:Port BatchProcessing)` edge — authored K9 rows fan
    out per app code, K2 DEMOTES to the per-folder unanimity fallback with
    `origin=matched-fallback` (§B3); ties/undeclared-platform folders are
    steward CONFLICTS, never auto-picks (1:1 OWNER-NOT-USER).
    DELETED: `seal_attribution.cypher` + the `SealAttributionLoader` class
    (the module keeps only the match-policy resolver); CLI
    `load-seal-attribution` → `load-folder-attribution` in
    `CANONICAL_LOAD_SEQUENCE`; graph-tests suite RENAMED
    seal-attribution-coverage → folder-attribution-coverage (8 TCs; TC-08
    asserts NO job-grain edges remain). Vocab: `m3_seal_app_ref`
    active→deprecated (AUTHORIZED by the K7 sign-off's "stays active until
    the K7 build migrates it" clause — guardrail-7 the J7 no-downgrade
    guards across this step), `m3_belongs_to_application` planned→active;
    supplement block swapped; `schema_graph.cypher` regenerated. Manual
    tier-5 chain rekeyed end to end: `SUPPORTED_SHAPE`, `_parse_key`
    requirements (app_code + app_id), the store's `manual_mapping` table
    columns (`app_code, folder_id NULL-able, app_id`), and the manual
    cypher now FANS OUT per code.
    ***YOUR SIDE — THREE CAUTIONS:***
    (a) T4/T23 SEQUENCING: your real tier-5 CSVs are JOB-grain; this step
    makes them UNPARSEABLE (parser now requires `app_code`/`app_id`). Take
    step 62's `;`→`:` conversion AND re-author those CSVs at the app-code
    grain in the same change that takes this step, or hold both steps
    together. (b) Your LIVE job edges + `active=true` ports are the real
    migration (K7 §F1/G4-RIDER) — T23 territory, wipe-and-rebuild does not
    exist for you; write your own migration before running the new loader.
    (c) Your `controlm_app_codes.cypher`/AutoSys twin still write the
    boolean flip — reconcile them with the new edge before both run, or a
    folder can carry contradictory attribution surfaces.
    `EXPECTED_CONSTRAINTS` does not move. Producer suite 1384→1399 (+15).
    BONUS in the same commit: the publish-boundary bare-id guard caught a
    REAL psgmgr folder id in step 62's standard doc examples — now
    synthetic. Verify your copy took the fixed examples, not the originals.

64. K12 + K14 + STATUS-DOC REFRESH [SMALL, LIKE-FOR-LIKE] (`5978d78`; claim
    `30ab908`, batch with the step-63 ledgering). K12: `controlm.yaml` gains
    the `applications:` app-code section (pure classification; jobless
    folders name-DERIVED and flagged) and the map entry's capture WAIVER is
    replaced with the real path — your side takes both wholesale
    (canonical-producer), but note the SECTION CONTENT reflects the
    producer's reduced sample; re-derive yours from your real extract if you
    maintain a parallel capture. K14: two ctlm_id strays converted to the
    dot form (MappingsRoute.tsx React key; mapping_demo.html slash join) —
    clean adds. Also the K2 rows in `docs/controlm-staging-ingestion-flow.md`
    and `docs/controlm-c3-normalization-status.md` now state the K8
    folder-grain shape; if your copies carry company edits, merge the row,
    do not overwrite the file. Suite stays 1399.

65. K10 — PORT ACTIVATION CUTOVER [TEST-PINNED, TOUCHES YOUR LIVE WRITERS].
    `seal_applications.cypher` seeds `active_state='declared'` +
    `declared_by/declared_at` ON CREATE only and NEVER writes 'confirmed';
    both attribution edge writers stamp the port
    `confirmed`/`confirmed_by`/`confirmed_at`/`confirmed_run_id` when the
    BELONGS_TO_APPLICATION edge lands (§G5 — derived, no separate trigger;
    coalesce-stable first-confirmation stamps). The `active` boolean is
    GONE; suite TC-09 fails any port still carrying it.
    ***YOUR SIDE:*** (a) §G4-RIDER is YOUR migration — grandfather your
    already-`active=true` ports as `confirmed` with the Control-M app-code
    link as provenance BEFORE taking TC-09, then drop the boolean; (b) your
    `controlm_app_codes.cypher` + AutoSys twin still write the boolean —
    re-point them (or retire them into the folder-attribution path, step
    63(c)) in the same change; (c) TC-10's two-way confirmation<->edge
    agreement will red any port confirmed by grandfathering whose folder
    edges have not yet been migrated — sequence the §F1/T23 edge migration
    FIRST, or hold this step with step 63. `EXPECTED_CONSTRAINTS` does not
    move. Producer suite 1399→1403.

66. K11 — STEWARD MAPPING CASCADE + THE §G1 ORCHESTRATOR-EDGE AUTHORING
    [TOUCHES YOUR TWO app_codes WRITERS AGAIN]. The K7 gate's §G act built
    end to end. Web: `AppCodeCascadePane.tsx` (new, clean add) on `/mappings`
    domain `app-code-mapping` — orchestrator-first cascade, unmapped-only
    folder queue, run_as_user sort, mandatory rationale, lifecycle chips as
    confirmation provenance (§G7); `MappingsRoute.tsx` wires the branch;
    `mappingsApi.ts` gains `draftAppCode` → `POST /mappings/app-code/draft`
    — a route K9's handler NEVER HAD (`app.py`; route-presence test added).
    LOADER SIDE IS THE PART THAT TOUCHES YOU: both attribution writers
    (`folder_attribution.cypher`, `manual_seal_attribution.cypher`) now
    AUTHOR `(:BusinessApplication)-[:USES_SOFTWARE {source:
    'app-code-mapping', origin: 'confirmed'}]->(:SoftwareProduct)` when a
    folder edge lands (§G1 — one mechanism with the K10 port confirmation;
    FOREACH-guarded on registry presence, shortfall stamped as
    `JobRun.orchestrator_edges` + warned). The orchestrator ref comes from
    `platforms.yaml` (`controlm`) via a NEW `BaseLoader.extra_cypher_params`
    hook — if you subclass BaseLoader with a custom `_flush`, merge the
    hook. `batch_port_orchestrator.cypher` stamps `origin =
    coalesce(u.origin, 'declared')` (§G2). Four new QuerySpecs
    (`mappings.catalog-cascade/orchestrators/app-orchestrators/
    unmapped-folders.v1`); suite TC-12 (confirmed-edge two-way agreement).
    ***YOUR SIDE:*** (a) your `controlm_app_codes.cypher` + AutoSys twin are
    now superseded TWICE over (boolean flip at step 65, orchestrator
    authoring here) — retiring them into the folder-attribution path is the
    clean end state; (b) TC-12 reds a confirmed app with an
    'app-code-mapping' edge but no confirmed Batch port — sequence with the
    steps 63/65 migrations; (c) `mappings.catalog-cascade.v1` binds
    HAS_APPLICATION, which is ACTIVE on your side (G6 ruled the COMPANY
    reading) — your cascade picker goes live immediately, no K13 wait; (d)
    the AutoSys twin domain slots in per §G by adding its own platforms.yaml
    ref + attribution loaders — the pane's orchestrator picker already
    renders it. `EXPECTED_CONSTRAINTS` does not move. Producer suite
    1403→1410 (+7); web build + oxlint clean. The legacy finding this step
    noted (`mappings.attribution-coverage.v1` reading the RETIRED job-grain
    edge) closed producer-side at step 91 (K15).

67. K13 — catalog_has_application SEMANTICS RECONCILED TO §G6 (docs/config
    only, no code behavior change). This is the producer ADOPTING YOUR
    reading — the gate ruled the company's structural-SUPPORT semantics
    (a Product supported by 2+ applications, front-end/back-end; 1:many BY
    DESIGN) over the producer's old "Product owns SEAL applications".
    Touched: `relationship_vocabulary.yaml` note (support reading leads;
    the old WAS_ATTRIBUTED_TO matrix hint recorded as FALLEN — both ends
    Entities post-K4, no PROV row; C9 history + `planned` status kept),
    `taxonomy-ontology-map.yaml` gains its FIRST entry for this edge
    (`product-has-application`, confirmed chad.wilson 2026-08-03 = the K7
    sign-off, capture waived on the C9 reason; map summary confirmed 24),
    `catalog_ontology_supplement.cypher` OntologyTerm notes (also removes a
    claim false since C9: "Written by pat_product_mapping loader"),
    data-context-extractor skill wording, and the step-66 surfaces' "K13
    back-flow" pointers re-aimed at the C9 extract condition.
    ***YOUR SIDE:*** (a) if your map already carries an entry for this edge,
    RECONCILE ids with `product-has-application` (union-append doctrine) —
    do not end up with two entries for one edge; (b) your vocabulary entry
    is presumably `active` with a loader — take the NOTE wording
    like-for-like but keep YOUR status/loader fields (the producer's stays
    `planned`, loader `~`); (c) the supplement's SET is idempotent MERGE —
    rerun refreshes the OntologyTerm notes; `EXPECTED_CONSTRAINTS` does not
    move, suite count does not move (1410/5, no test delta).

68. U12 — SNAPSHOT RETENTION ENFORCED IN snapshot.ps1 (+3 guard tests). The
    ruled newest-only retention (SME 2026-08-02) moved from prose+human into
    the script: after a successful write+filter, every other
    `<project>-<date>[-HHmm].json` is deleted (pattern-anchored — `-code-*`
    comparison files and `drydocs1-*` history names exempt; deliberately
    AFTER the write so a failed run cannot delete the only good snapshot;
    source order pinned by test). Proven live: the first enforcement run
    removed FIVE stale snapshots. README trued to the all-files instrument
    (whole-repo default + -CodeOnly, ruled retention replaces "keep ~10",
    fourth instrument-change marker: 238 -> 1457 nodes on unchanged code at
    the 2026-08-02 all-files boundary — instrument, not growth; absent-file
    citations restated as git history). NEW tests/unit/
    test_depgraph_snapshots.py: exactly-one committed all-files snapshot,
    script enforcement present and after-the-write, README currency.
    ***YOUR SIDE:*** the snapshot RITUAL is producer-machine-only, but the
    directory + tests PORT: (a) the exactly-one test reds a tree carrying a
    snapshot series — apply the same retention (keep newest, delete the
    rest) in the port commit; (b) if your ritual wrapper diverged from
    snapshot.ps1, take the retention block like-for-like. Suite 1410→1413.

69. U13+U14 — THE CODE-GRAPH QUERY PACK GETS TWO STANDING FILTERS (docs +
    skills only, no code change, no test delta — 1413/5). U13: every seed
    query (tech-debt A1–A6, the review plan's table, groom-backlog's two
    graph cross-checks) filters `removed_from_source_at IS NULL` or says in
    one line why tombstones belong (the plan's Phase 2 units 1–2 are the
    deliberate exceptions). U14: architecture metrics bind
    `m.project IN $packages` = the SEVEN package roots — an allow-list in
    the QUERIES, never a scanner exclude (U9's whole-tree artifact is the
    ruled shape). First-party Python outside the packages (agents/,
    scripts/, knowledge/) is a separate labeled orphan queue (22 today),
    reported beside the baseline, never folded in. Baselines restated with
    scope+date next to every number (fan-in 18→29, orphans 24→0 in-package,
    untested 29 scoped / 129 raw).
    ***YOUR SIDE:*** like-for-like docs/skills adoption; your graph carries
    its own numbers, so re-probe YOUR baselines rather than adopting the
    producer's (the producer's 2026-08-03 wipe left zero tombstones — a
    fresh-provisioned graph reads the same, an aged one will not).

70. C22 — THE CATALOG LOADER SWEEP (`+7` tests, 1413→1420/5). The silent
    parent joins C17 fixed in products.cypher only are now the ONE shape in
    all three hierarchy loaders: OPTIONAL MATCH, `orphan` written EVERY
    run, unresolved id kept (`pl.orphan_parent_lob_id`,
    `ap.orphan_parent_product_id`). All three name SETs coalesce, and the
    row models moved with it — ProductLineRow/ProductRow/AreaProductRow
    `name` is optional with ''→None normalization (a required name makes a
    sparse refresh reject wholesale, worse than the blanking it replaces);
    ids stay required. The C17-deferred question RULED EMIT:
    `drydocs.loader/unresolved-parent` (warning) rides the O28 envelope —
    BaseLoader gains `orphan_label` + a run-scoped count at close;
    per-node flag stays the durable record; envelope standard doc updated.
    ***YOUR SIDE:*** like-for-like — but if your tree carries loaded
    :Product/:ProductLine/:AreaProduct data, RE-RUN the catalog loaders
    after the port so the every-run orphan flags exist (nodes loaded under
    the old cypher have no flag until touched); and if you extended
    status-item type handling anywhere, note the new fifth type. The
    dev_teams/catalog_lobs same-shape gap closed at step 94 (C24) — it IS
    in this range after all.

71. J18+J26+J27+J28 — THE J-SERIES CLOSE-OUT (one batch, 1420→1427/5).
    J18: live-verification claims name their venue (backlog pull-rule step 5
    + CLAUDE.md §6; P3/G33 close notes retro-tagged). J26: text-guard sweep —
    negative assertions over committed Cypher/SQL now read COMMENT-STRIPPED
    text (strip_comments / a `--` line filter); the family inventory +
    self-description regression proofs live in
    tests/unit/test_text_guard_conventions.py. J27: the two .gitignore
    comments that named the org/domain are reworded to describe the corpus;
    J15's guard gained scan D (no domain-shaped token in .gitignore, empty
    allowlist). J28: render_gates.py classifies by SLUGIFIED-HEADING identity
    — a body citation or PARTIAL ruling never closes a gate; prompts may
    self-declare via a `# SIGNED OFF`/`# DEFERRED` marker line (F1/F2
    crosswalk prompts got theirs); gates.json 41→43 rows, 8→10 open.
    ***YOUR SIDE:*** all four are like-for-like, with two cautions. (a) J28
    re-renders gates.json from YOUR gate-log — expect YOUR open list to grow
    if your log carries citation-only or partial-ruling prompts; that is the
    fix working, not drift. If any of your signed gates use prose headings
    without the slug, add the `# SIGNED OFF` marker line to the prompt file
    (the F1/F2 pattern) rather than editing log headings. (b) J27's scan D
    reds a .gitignore that names any domain — reword or allowlist WITH a
    reason in the same commit that takes the guard. J13 (the publish-ceiling
    term sweep) remains OPEN and user-gated — not in this range.

72. M3+M4 — THE DOC-06 ENVELOPE GATES (two gates, one session, 1427→1430/5).
    M3 (gate `audit-envelope-phase4`, 13/13): the four remaining non-Control-M
    audit-envelope stubs are RULED, none confirmed — the SME evidence reversed
    the drafted recommendation: the SEAL registry's date fields are
    onboarding-LIFECYCLE milestones with two-era capture (legacy applications
    lack them), so creation_date is not record authorship; certification
    columns excluded as attestation; the PAT report extracts project zero
    audit columns (stub-until-projected); software-registry = permanent stub
    (git history is the envelope). Revisit trigger recorded: the registry UI
    exposes a per-application audit download. No loader change; audit-fields
    notes + loader README envelope section + doc 06 phase marks. M4 (gate
    `envelope-property-terms`, 10/10): the envelope properties bound
    dct:creator/created/contributor/modified in a NEW `property_terms`
    section (0b) of relationship_vocabulary.yaml; `dct:` registered in
    namespaces.py (+ ontology.cypher header sync, documentation-grade — no
    dct: OntologyTerm nodes seeded); reference/standards/dcmi-terms/ stub +
    REGISTRY row; +3 drift guards in test_audit_fields.py.
    ***YOUR SIDE:*** gate ADOPTION per the two-tier doctrine — the gate-log
    entries union-append and YOUR tree runs its own ratification if it wants
    the rulings load-bearing; the config/vocabulary/reference files are
    canonical-producer. Two cautions: (a) if your tree ever mapped SEAL or
    PAT envelope columns locally, the M3 rulings SUPERSEDE that — remove the
    mapping or record your own gate divergence; (b) the new test
    `test_every_envelope_property_carries_a_term_binding` reds a tree whose
    vocabulary file predates section 0b — take the vocabulary file in the
    same commit as the test.

73. Q13 — VENDOR-DOCS PIPELINE VERIFIED (laptop `6cbe44b`, 1430→1449/5;
    ledgered desktop-side — the close commit did not touch this file). The
    2026-07-31 pipeline was closed with three silent-reporting fixes, all the
    "succeeds loudly, does nothing" class: vendor_docs.cypher gained the
    delta-only WAS_GENERATED_BY tail (rows_changed was structurally 0 —
    placed ABOVE the SUBSECTION_OF empty-list UNWIND that drops TOC-depth<=1
    rows, ordering test-pinned); rows now carry BOTH the registry corpus_id
    and the capture id (docs-verify would have reported a loaded corpus as
    MISSING); bare-stem doc_id resolution. ***YOUR SIDE:*** like-for-like;
    if your tree loads vendor-docs corpora, RE-RUN the loader post-port so
    the change-reporting is honest, and expect docs-verify to reconcile
    where it previously read MISSING.

74. J29 — UTF-8 NO-BOM STANDARD for loader-read formats (1449→1450/5). SME
    ruling: every .cypher/.sql/.csv is UTF-8 WITHOUT BOM (UTF-8 itself was
    the deliberate readability choice; the BOM is a writer artifact —
    PowerShell Out-File/'>', Excel CSV export). Guard =
    tests/unit/test_file_encoding.py (J22 tracked+untracked walk), proven on
    a probe; three producer sample CSVs stripped; vendor .xsd captures
    exempt (XML self-declares encoding; VERBATIM trust). Diagnosis note: the
    M3-reload cypher-shell BOM rejection was a PS 5.1 PIPE injection, not
    repo files. ***YOUR SIDE:*** the guard WILL red any BOM'd .cypher/.sql/
    .csv in YOUR tree — likely candidates are Excel-exported tier-5 manual
    CSVs. Strip them in the same commit that takes the test (a BOM'd CSV
    read with plain utf-8 breaks header matching silently, so this is a fix,
    not churn). cypher-shell scripts: copy the file and use `-f`; never pipe
    content through PowerShell 5.1.

75. Q6+Q12 — THE DOCMETA COMPONENT (laptop `d647171`; T21 discharged in the
    same commit, which was the only ledger touch — this step closes that
    gap). `drydocs_docmeta/` lands: connectors (`base.py` protocol +
    `RawPage` + `SourceUnavailableError`; `web.py` stdlib urllib, injectable
    transport, SSRF scheme allow-list, and the Q12 page-count refusal;
    `filedrop.py`), pipeline + capture policy in one home; module-boundary
    rows added. Producer-AUTHORED against the T21 description, never a copy
    of your tree — your `connectors/` stays canonical-company.

76. SDLC APPLICATION RUN BOOK — FOURTH DOC TYPE (`995eb9a`)
    [LIKE-FOR-LIKE]. `docs/design/templates/sdlc-app-runbook.outline.yaml`
    (22 sections captured verbatim from a real 56-page Informatica-ETL run
    book) + synthesized `sdlc-app-runbook.example.md` (OrderHub, synthetic
    SEAL block). Deliberately in `templates/` — OUTSIDE the
    `docs/design/*-runbook.md` governed-sweep glob, so no rev machinery
    attaches. +2 outline pins in `test_doc_outline.py`.

77. EXCEL MINIMUM-VIABLE RUNBOOK SKILL (`69e1dbe`)
    `.claude/skills/controlm-runbook-automation-excel/`: template-spec.yaml
    (2 tabs: 48 Technical_Details rows + 35 job columns, per-field
    `source: graph|graph-partial|manual`) -> `generate_template.py`
    (openpyxl, new dev dep) -> committed xlsx. 31/35 job columns
    graph-derivable. Synthetic values only (SEAL 70004 — the J15 guard
    caught the original 90123 on first tracked run; reswept, not
    allowlisted). FILLED workbooks are Internal — never in the skill dir.

78. CONTROLM-PIPELINE-STUB CAPTURE + OPUS WORK ORDER (`0c77426`)
    [INTERNAL PATHS]. `internal/controlm-config/reference/
    controlm-pipeline-stub-capture.md` (verbatim: builder catalog, folder/
    job-name grammars, Folder.xsd contract, DoMail defaults, inheritance
    table) + `controlm-pipeline-stub-integration-plan.md` (items X1-X3/
    W1-W4/V1-V2/E1-E4/F1 for YOUR internal Opus agent; deploy/ = SoD,
    out of scope). Producer-twin groom trigger inboxed; DD-ids are yours.

79. G36 — :BusinessApplication INDEX DROPS (`ea66764`) [LIVE-VERIFIED
    desktop `neo4jtest`/`drydocs`]. `businessapplication_status/risk/name`
    removed AND explicitly `DROP INDEX IF EXISTS`'d (the port_unique
    belt-and-braces — removing the CREATE alone leaves live DBs carrying
    the stale claim). Recorded rulings: NO index for `manually_created` or
    `batch_orchestrator_last_run_id` (offline reporting at registry
    cardinality). `EXPECTED_CONSTRAINTS` does NOT move — these were
    indexes, not constraints. Re-run bootstrap after taking this.

80. L20 — FEEDBACK STRAY-FILE GUARD (`c075ee2`, +4 tests -> 1505/5).
    `DesignDocFeedbackAdapter.stray_files()`: top-level files in
    `docs/design/feedback/` that are neither `<doc>-rev<N>.yaml` nor
    README.md become findings; `DocFeedbackLoader` WARNs the list after
    load (duck-typed — fake adapters unaffected). A standing test asserts
    the committed feedback tree is stray-free — if YOUR feedback dir holds
    loose files, it reds correctly; rename or move them, don't exempt.

81. S5 — THE REGISTRY SPLIT [STRUCTURE-BREAKING for tooling; PORT-MANIFEST
    updated] (`d84d86b`, +10 tests -> 1515/5). BOTH central registries are
    now fragment DIRECTORIES (`config/taxonomy-ontology-map/`,
    `drydocs_core/ontology/relationship_vocabulary/`) read by ONE loader
    (`drydocs_core/yaml_fragments.py`: sorted-filename concatenation, loud
    on duplicate keys/ids, single files still first-class). Split-time
    proof: 83+38 entries deep-equal; ONLY entry order changed
    (domain-grouped) — `schema_graph.cypher` regenerated in the commit.
    ***YOUR SIDE:*** apply the SPLIT SHAPE, not a conflict resolution — the
    manifest rows now glob the directories and say exactly that. Any of
    your own scripts reading the two old file paths must repoint (grep for
    both names); the reconcile-port snapshot step now writes the MERGED
    documents (skill + guard docstring updated). Per-entry rules unchanged.

    (Chores in the same range, no separate steps: `5d2d5bc` groom promoted
    K15 — union by id as usual; claim/close/board/snapshot commits carry
    only backlog.yaml + renders, all per-entry/derived.)

82. U9 FILTER OFF-BY-ONE — GIT-IGNORED NAMES LEAKED THROUGH RELS
    [TEST-PINNED by the J15 value guard, which caught it]. A depgraph rel is
    `[src, TYPE, dst]`; `filter_ignored.py` checked endpoints at [0]/[1] —
    [1] is the TYPE string — so every CONTAINS rel to a dropped node
    SURVIVED, carrying git-ignored FILENAMES into the committed snapshot
    (here: real workbook screenshot names in the repo root). Fix checks
    [0]/[2] AND requires both endpoints to exist as kept nodes (dangling
    rels can never leak again). ***YOUR SIDE:*** you run the same script
    (step 68 retention); take the fix and REGENERATE your newest snapshot —
    your current one likely carries ignored names in rels the same way.

83. DDLINEAGE RETIRED — TOPOLOGY 5 -> 4 (X1 ADR amendment `bb934d0` + X2
    sweep `b97636c`) [LIVE-DB MIGRATION on your side]. Nothing ever wrote or read
    `ddlineage` (writer pinned to `drydocs` w/ TrustBoundaryError; your
    G30-equivalent spec repoint came in an earlier range) — ADR 0002 now
    carries a dated amendment retiring it; the deployed set is
    drydocs/ddcontext/ddall/ddschema (re-derive #4 — that list is a copy,
    and the LIVE `SHOW DATABASES` is what a drop must be judged against).
    Sweep: provisioning DDL + ddall
    alias dropped, provision.ps1 runs 02 twice not three times, smoke
    reads two constituents, cli.py DOC_SWEEP_DATABASES, dev-environment
    databases map (+ its key-set speed bump), startup-refresh runbook
    Rev 9, `ddlineage` JOINED test_database_names' SUPERSEDED_NAMES (the
    escape regex gained "retire" — a package source may name it only
    while admitting it is old). ***YOUR SIDE:*** the DDL diff ports
    like-for-like, but `CREATE ... IF NOT EXISTS` never DROPS: your live
    `ddlineage` survives a green provision.ps1 run and its removal is a
    MANUAL migration by your hand — alias out of `ddall` FIRST, then a
    zero-node emptiness probe, then `DROP DATABASE ddlineage`; a
    NON-EMPTY probe means something on your side writes a database the
    producer never did — STOP and treat that as a defect report, not a
    cleanup (the producer's per-machine drops are backlog X3/X4, same
    protocol). SUPERSEDED_NAMES will red any company-local module that
    names `ddlineage` without a retire/supersede admission — that is the
    sweep finding your stragglers, not a port failure.

    ***RIDER (2026-08-05) — BOTH PRODUCER DROPS ARE NOW DONE, and they
    taught two things worth having BEFORE you run yours.*** X3 closed on
    the desktop container and X4 on the laptop (`e495e88`, `e164e7f`);
    both probed zero nodes AND zero relationships first, so neither was
    a defect report. (1) **ALIAS-FIRST IS PLATFORM-ENFORCED, not just
    good manners** — `DROP DATABASE ddlineage` attempted ahead of the
    alias was REFUSED outright with `42N82, cannot drop database with
    aliases`, changing nothing. If you get 42N82 you have the order
    wrong, not a broken database. (2) **The clause order is
    `DROP ALIAS <name> IF EXISTS FOR DATABASE`** — NOT
    `DROP ALIAS <name> FOR DATABASE IF EXISTS`, which parses as a
    different statement and fails. (The alias name is back-quoted in
    Cypher because it contains a dot: `ddall.ddlineage`.) Also measured: `db.labels()` on the emptied
    database still returns `[DataAsset, ControlMJob]`; that is the label
    TOKEN store the 02_proxy_constraints pass registered, not data. A
    token is not a node — probe with node/relationship COUNTS, or you
    will talk yourself out of a legitimate drop. On the laptop the drop
    statements had to be run by the operator by hand (the agent's
    permission layer refused them on every route), so budget for a
    human step rather than an unattended one.

84. DEPGRAPH INSTRUMENT — PIN BUMP + A CURRENCY CHECK ON THE RITUAL
    (`299af39`, `a782860`). The depgraph sibling consolidated onto its
    own main at `773fb1e`; the pin in `config/dev-environment.yaml`
    moved `5006567 -> 773fb1e` and the sibling checkout was pulled to
    match. `snapshot.ps1` now compares the checkout it is about to run
    against that pin and classifies ahead / behind / diverged / unknown.
    It **WARNS, never refuses** — a snapshot taken on a drifted
    instrument is still a snapshot, and a ritual that blocks gets
    skipped. ***YOUR SIDE:*** `knowledge/depgraph-snapshots/**` is
    canonical-producer (tooling ports) while `*.json` is never-port
    (outputs never cross) — that row pair is unchanged and still
    correct. The `depgraph:` block in `config/dev-environment.yaml` is
    canonical-company: your fork lives at a GHE remote and your pin is
    your own, so **take the script, keep your block**. One defect worth
    knowing because it was caught only by a test matrix and not by
    running it: the first classifier compared a freshly-read `HEAD`
    instead of the resolved pin commit, and cheerfully reported
    "behind" as "ahead".

85. S4 — THE CONSOLE DRAFT SUBSTRATE (`0f87fb2`, + mapping-store runbook
    Rev 2 `f7c0502`). `var/mapping.db` gains a `draft` table and a
    `v_open_drafts` view; `SCHEMA_VERSION` -> `drydocs.mapping-store.v2`;
    `build()` now CARRIES drafts across a rebuild instead of losing
    them. `drydocs_api` gains draft writes (`/mappings/drafts`,
    `/mappings/drafts/{id}/promote`) that return a receipt and emit an
    ADDITIVE unified diff rather than editing config in place — ADR 0009
    rule 5, propose in the DB and land in git. ***YOUR SIDE:*** this is
    the first thing that ever WRITES to the mapping store, so the
    runbook line "nothing here can lose data because it is all derived"
    stopped being true the day S4 landed; Rev 2 says so. `drydocs_api/**`
    and `drydocs_core/**` are evaluate-on-collision — your QuerySpecs
    legitimately differ, so hand-merge rather than adopt.

86. J30 — `wip/k9-laptop` DISPOSED (`5467476`). A long-lived producer
    branch was audited against `main` and deleted; the one thing it held
    that `main` lacked — `app_code_migrations()` and
    `app_code_migration_report()` — was lifted into `drydocs_api`. Pure
    producer housekeeping; carried here only so the API surface delta is
    attributable rather than appearing from nowhere in a diff.

87. G54 — `provision.ps1` IS EXEC-AWARE: A DOCKER-ONLY HOST PROVISIONS
    WITH NO FLAGS (`13e1de6`, `f03a810`, `b1501ea`). `cypher-shell` ships
    INSIDE the Neo4j image (`/var/lib/neo4j/bin/cypher-shell`), so a
    machine whose only Neo4j is the container has none on PATH — the
    documented invocation could not complete there, and the header used
    to claim the image satisfied a requirement that is true of the IMAGE
    and not of the PATH. The script now detects that and falls back to
    `docker cp` + `docker exec … -f`, reading the container name from
    `config/dev-environment.yaml` (`neo4j.container`), overridable with
    `-Container`, forceable with `-ForceDockerExec`; it announces which
    transport it took, and pins the IN-container address to
    `bolt://localhost:7687` because the host port mapping is a host fact.
    ***YOUR SIDE:*** the SCRIPT is portable and needs no edit — it reads
    whatever container name your own `config/dev-environment.yaml`
    declares (canonical-company, so keep yours). What is not portable is
    the header's `docker run` block: container, ports, image tag and
    source, credential handling are yours to re-author.
    **A CORRECTION THAT MATTERS TO YOU SPECIFICALLY:** J29 (step 74)
    left a note here saying PS 5.1 pipes inject a BOM. That was stated
    too broadly, and a company screenshot disproved it — the pipe works
    on a default ANSI-codepage console and fails only where the console
    output encoding carries a preamble (`chcp 65001`, where
    `[Console]::OutputEncoding.GetPreamble().Length` is 3). The note is
    corrected in `drydocs_core/schema/provisioning/README.md`. `docker cp`
    + `-f` sidesteps
    console encoding entirely and is what the script does, so the
    RECOMMENDATION is unchanged; only the reason was wrong. A rule
    stated too broadly gets ignored the first time someone watches it
    not apply.

88. V-SERIES — MODULE RUNBOOKS, AND COVERAGE BECAME A TEST
    (`d11f6c0` V1, `b8eed6d` V8, `523b929` V2, `23889eb` V3, `0b67b66`).
    Three new module runbooks — `drydocs-api`, `drydocs-core`,
    `drydocs-load` — each carrying a `- **Module:** <name>` front-matter
    line, plus `tests/unit/test_runbook_coverage.py`, which asserts every
    module in `MODULE_MAP` either HAS a runbook or sits in a named
    exemption with a written reason. `RUNBOOK_PENDING` is shrink-only
    (the N2 `LEDGER_PENDING` idiom): six modules remain on it. ***YOUR
    SIDE:*** `docs/design/**` is `evaluate`, deliberately not
    canonical-producer — the controlm-ingestion-tdd rows are the
    precedent for a doc you finalize becoming your own canonical-company
    row. The coverage guard reads YOUR `MODULE_MAP`, so if your module
    set differs the guard will name the difference; that is the guard
    working. Worth one warning from the producer's own week: the
    `drydocs-core` runbook copied the topology database list inline and
    was stale within HOURS, because X1 retired `ddlineage` the same day.
    It now READS the list instead. Copy nothing into a runbook that a
    one-liner can re-derive.

89. RUNBOOK CURRENCY — THE SECOND GUARD, BECAUSE COVERAGE IS NOT TRUTH
    (`fa6e6e0`). V1 proves a runbook EXISTS. It says nothing about
    whether the runbook is still TRUE, and on one day that gap cost
    three separate catches, every one of them found by a person noticing
    rather than by a test. `tests/unit/test_runbook_currency.py` checks
    that the things a runbook NAMES still exist: repo-relative paths in
    backticks, and `drydocs` CLI verbs. It found four stale paths on its
    first run — two from the S5 monolith->directory split, one package
    relocate, one file that never existed — the class of change that
    updates every importer automatically and every DOCUMENT not at all.
    It also caught its own author, in the very rev note describing the
    error it was written for: **backticks are an existence claim**, so a
    note explaining that an earlier revision cited a dead path must
    quote that path as plain text. ***YOUR SIDE:*** it cannot prove a
    SENTENCE is still true — "nothing here can lose data" is not
    detectable by grep — so it narrows the gap rather than closing it.
    `HISTORICAL_PATHS` is the exemption dict, shrink-only, reason
    required.

90. N6 — ONE LOAD SEQUENCE, TWO PROFILES, AND THE RULING RECORDED
    (`7884b23`, with `7a60e99` as its precursor). Two files told an
    operator what to run — `scripts/ingest.sh` and the startup runbook's
    Appendix B — each carrying its own ordered list. They disagreed by
    five steps and NOTHING recorded whether that gap was a decision.
    **That ambiguity was the defect, not the step counts:** a deliberate
    subset and a forgotten step look identical from outside. The ruling:
    the scheduled list is deliberately shorter (a Control-M ingest is
    not a full refresh), and each standing step it skips now carries a
    reason in `cli.SCHEDULED_INGEST_EXCLUSIONS` — `refresh-reference` is
    a weekly chain on another cadence; `load-software-registry` and
    `load-bmc-docs` are repo-triggered corpora; `docs-verify` would FAIL
    that path by design, and under `set -e` would abort an ingest over a
    reconciliation never meant to hold there. Appendix B's omission was
    NOT deliberate and it gains `docs-verify` (runbook **Rev 10**).
    Mechanically: sequence steps widen from 3-tuples to a named
    `LoadStep` carrying `profiles`; `LOAD_PROFILES` +
    `load_profile(name)`; `ingest.sh` READS its profile at run time and
    has no list left to drift; `tests/unit/test_load_sequence_surfaces.py`
    holds Appendix B to the same declaration. The precursor `7a60e99` is
    the exhibit: `bootstrap-schema-graph` ran in BOTH operator surfaces
    while missing from the declaration, so the published load map
    counted 15 steps where both real paths ran 16 — the old completeness
    check walks `COMMAND_LOADERS` and therefore only ever reaches
    loader-backed verbs. The new guard starts at the SURFACES and works
    inward, which is the direction that catches a non-loader verb.
    ***YOUR SIDE — READ THIS AS NEW STRUCTURE, NOT A DIFF.*** Run
    re-derive #3 first: an ImportError is the honest answer that your tree
    has no declaration yet, and after adoption it is how you check the
    step-vs-profile table above against what you actually shipped. Company
    `cli.py` still has no `COMMAND_LOADERS` and no
    `CANONICAL_LOAD_SEQUENCE` at all; that is the open **T19** row, and
    N6 is the last of the N3–N6 slice it narrowed to. `drydocs/cli.py`
    is `evaluate` (keep consumer verbs, add producer verbs), so the
    declaration lands as an addition. If you adopt it, your profile
    membership is YOUR ruling to make — the reasons above are the
    producer's cadence, and your Control-M schedule may justify a
    different subset. What should NOT differ is that the subset is
    written down: an unexplained omission is indistinguishable from an
    oversight, which is the whole point.
    One incidental fix rides along, and it is a warning about guards in
    general: `test_runbook_currency.py::_cli_verbs` shelled out to
    `drydocs --help` and PARSED it. On a cp1252 console that decode
    fails on the box character `┐` (`0x90`) so `stdout` came back
    `None`, and the rows begin with `│` rather than `|` so the pattern
    would have matched nothing anyway — which makes EVERY documented
    verb look unregistered. A tightened regex was measured and did agree
    exactly (37/37), and was still the wrong fix. It now reads
    `app.registered_commands`: **never parse a render when the object is
    importable.**

91. K15 — THE JOB-GRAIN /mappings PANE RETIRED, NOT RE-BOUND (`192c510`)
    [SME-RULED direction; web/API only]. Closes the step-66 legacy finding:
    post-K8 the pane read the retired job-grain edge, reported every row
    "unresolved", and drafted changesets the server refuses. The SME fact
    that settled RETIRE over re-bind: a folder and its jobs carry the SAME
    app code, so a job-grain grid is N× rows of one folder-level fact.
    QuerySpec `mappings.attribution-coverage.v1` DELETED; the API domain row
    stays `available: false` so a bookmarked tab renders visibly retired
    rather than vanishing; MappingsRoute drops ~495 lines and defaults to
    app-code-mapping. Your console carries the same dead pane after steps
    63/66 — take this with them.

92. GATE PROMPTS DRAFTED, NOTHING RULED [UNRULED] (`6244347`, `8d45832`).
    Three new prompts await SME: software-version-context (loads at the
    AppUser grain — the version rows are (fid-name, install-path) facts, and
    the application is reached only through a MUTABLE ownership join, which
    is why it is TWO gates not one), fid-identity-scope, and G32
    content-topology. `6244347` also carries the naming-standard corrections
    the version evidence forced — those port like-for-like. The prompt FILES
    port; no config flips until signed. Your gates.json open list grows by
    three on re-render — J28 working, not drift.

93. S10 — REFUSE A PRE-CUTOVER GRAPH INSTEAD OF MINTING THE TWIN
    (`04b267a`) [TEST-PINNED; born from YOUR 2026-08-04 incident — see the
    T23 row]. `drydocs/loaders/app_identity.py` adds
    `PreCutoverApplicationGuard`, mixed in on all four loaders that MERGE
    the canonical `:BusinessApplication`; the check runs BEFORE preflight
    and before `_open_run`, so a refused load writes NOTHING — not even the
    :JobRun — and the refusal message carries the remedy (backfill or
    rebuild, count duplicates first), not just the symptom. The coverage
    test derives the MERGE-site list from the .cypher files, so a fifth
    site added without the guard reds. Fixed in passing:
    `batch_port_orchestrator`'s endpoint probe leaned on the deprecated
    seal_id alias. ***YOUR SIDE:*** the guard PREVENTS the crash you
    already hit; it does not repair live state — the S3 re-key/backfill
    stays T23, exactly as that row says. Suite 1575/5 at this commit.

94. C24 — catalog_lobs + dev_teams STOP BLANKING ON A SPARSE REFRESH
    (`6a45a02`) [TEST-PINNED]. The two loaders step 70 inboxed, closed:
    `catalog_lobs.cypher` coalesces BOTH `code` and `name` (code was losing
    data on every id-only refresh — the more visible loss); `DevTeamRow.name`
    goes optional with ''→None (a required name rejects a sparse row
    wholesale, `last_seen_at` never advances, and an unrefreshed team reads
    as retired); `team_id` stays required — optionality never leaks into
    keying. The C22 parametrized coalesce pin now covers FIVE loaders, so a
    sixth gets caught by the same test. ***YOUR SIDE:*** like-for-like;
    same re-run note as step 70.

95. W1–W3 + THE fcdo-crosswalk GATE — FCDO ALIGNMENT BUILT, SIGNED, AND THE
    CORPUS ACTIVATED [SME-SIGNED] (`eaa4469` W1, `46a2b8c` W2, `2e4e726` W3;
    gate `44a91ab` 13/13; activation `f53885d`). NEW
    `config/crosswalks/fcdo-vocabulary.yaml` — 8 rows binding DryDocs terms
    to standard CURIEs (PROV-O/DCAT/SKOS/ADMS/RDFS/OpenLineage),
    mechanism-only (a test forbids firm-namespace strings). Its schema is a
    SIBLING (`drydocs.vocab-crosswalk.v1`): `crosswalk.py` gains
    `SIBLING_SCHEMA_IDS` so the orchestrator-crosswalk loader SKIPS it in
    the directory scan while unknown schemas still fail loudly — take the
    loader change, the config and `tests/unit/test_fcdo_crosswalk.py`
    TOGETHER or the scan refuses the new file. Gate outcome: all rows
    confirmed EXCEPT row 5 (loader envelope ↔ Descriptive Metadata),
    blocked-on-recapture; the test pins the signed statuses. W2 registered
    the property/enum alignments PLANNED on three landing spots
    (ControlMJobRun Run semantics, SKOS-required attrs as the enum-gate
    idiom, ColumnShape names); W3 documented the builder skill. The
    `fcdo-frameworks` doc corpus flipped `confirmed: true` by user ruling
    (gate-log RECORD; plus an audit-fields stub entry — `test_audit_fields`
    requires one for every confirmed source, take them together).
    ***YOUR SIDE:*** (a) gate ADOPTION is two-tier as always; the file
    lands under the COMPANY enforcement-matrix row id `crosswalks`
    (standing divergence above); (b) the row-5 recapture is YOURS — the
    ruling waits on the company-side Confluence scrape, so that residue
    closes on your side first.

96. K18 — PLATFORM APP CODES CAN NO LONGER MASQUERADE AS TIER-1; `tier` →
    `row_kind` ON EVERY SURFACE [TEST-PINNED; FORMAT-BREAKING company-side —
    joins the T23 migration family] (`1386faf`; claim + the disagreement
    rule on the item `1755f9b`). THE RENAME, precisely — five surfaces move
    together, and taking a subset strands the others:
    (1) `config/overrides/app-code-mappings.csv` header column `tier` →
    `row_kind`; (2) the mapping-store column + views, `SCHEMA_VERSION` →
    `drydocs.mapping-store.v3` (derived — rebuilds; S4 drafts carry);
    (3) the wire (`AppCodeEntry.row_kind` in `mappingsApi.ts` /
    `drydocs_api`); (4) the row model (`FolderAttributionRow.row_kind`);
    (5) the EDGE PROPERTY — `folder_attribution.cypher` writes
    `r.row_kind`, not `r.tier`, on BELONGS_TO_APPLICATION folder edges.
    The K2 match-precedence tiers deliberately KEEP the word "tier" — no
    property of theirs surfaces, and the value spaces never collided.
    BEHAVIOR: the loader derives a row kind from PRAOCG name positions 3–5
    against a CLOSED six-code platform list read from
    `internal/standards/technology/platform-codes.yaml` (internal/ =
    never-port; a missing file leaves the guard INERT, so a tree without a
    twin behaves pre-K18). A platform-prefixed code never fans out even
    when authored seal-born; a code-level platform DECLARATION now
    REQUIRES `app_id` — the platform's OWN SEAL — plus rationale
    (declare-by-absence retired; the legacy empty-app_id shape still reads
    as a declaration, defensively). THE DISAGREEMENT RULE (SME, recorded
    on the item): two row-kind signals never resolve silently — derivation
    wins for BLOCKING fan-out, and every disagreement queues for a human
    (`RowKindDisagreement` in coverage + a JobRun count); the inverse
    direction (row says platform, name says application) queues without
    blocking anything.
    ***YOUR SIDE — FORMAT-BREAKING, sequence with steps 62/63:*** (a) your
    tier-authored CSV rows re-author under the new header AND the
    app_id-required rule in the same change that takes the store/loader;
    (b) live `r.tier` edges migrate with the K8/T23 reload — one more
    reason that migration is a single event, not a series; (c) the steward
    pane gains a fourth authoring mode, "platform DECLARATION", where the
    application you pick is the platform's own; (d) author YOUR OWN
    platform-codes twin from your frameworks — the producer's six values
    are its capture, not a contract. Suite 1597/5 at head (chain figure
    below). K19 (the follow-on) is producer-backlog, not in this range.

97. K19 — A MAPPING IS AN AS-OF ASSERTION; REUSED CODES QUEUE FOR REVIEW
    (`2ef0050`; claim `e4b09c9`) [TEST-PINNED]. The K18 follow-on, and NOT a
    format break. The 3-char app-code namespace is scarce, so codes get
    retired and REISSUED with a new meaning (DDC is the documented case);
    nothing stopped a reused code from silently inheriting its predecessor's
    mapping. `detect_mapping_age_suspects()` (pure, `folder_attribution.py`)
    flags any authored row whose `authored_on` strictly predates the
    first-seen date of a folder it applies to — one suspect per authored ROW,
    since each row is its own as-of assertion. Same-day is not postdating; no
    date on either side is no age claim. REVIEW-ONLY and deliberately OUTSIDE
    the coverage invariant: suspect folders stay attributed, because a
    reissued code and a growing application are indistinguishable without a
    human. Surfaced where the steward already looks (coverage `as_dict`,
    `run.mapping_age_suspects`, a loader warning, the CLI review-queue print).
    CHOICE recorded: detection only, NO `valid_from`/`valid_to` — effective
    dating IS preserved mapping history, which routes to a gate, and it would
    be a second CSV format break (v4) immediately behind K18's v3.
    ***YOUR SIDE:*** needs `ControlMFolder.first_seen_at` populated or every
    row reads "no age claim" and the queue is inertly empty — which looks
    identical to clean.

98. J32 — THE FIELD-MEANING RULE GETS A HOME (`cfccf6a`; claim `10ac1ee`)
    [prose only — no vocabulary entry, no map entry, no loader change].
    Ownership, routing and attribution are three different facts that all
    serialize as a SEAL id, and the graph has exactly ONE place where the
    third is authored — the confirmed app-code mapping. Everything else
    carrying a SEAL loads as what it IS (a registration, a routing
    instruction, a corroborating signal), never collapsed into
    BELONGS_TO_APPLICATION. New standing section in
    `docs/RELATIONSHIP_GUIDE.md` carrying the rule, the test for any new
    source (ask what the field's JOB is, not what it contains), and three
    observed instances as evidence. Rider: the AutoSys README now points at
    the guide as the canonical home.
    ***YOUR SIDE:*** take it before your next SEAL-bearing source, not after.

99. CODE-GRAPH — CONTAINMENT TREE + MEDIA-TYPE LAYER (`d7ae7af`, merged
    `78a2d92` `--no-ff`) [SME-RULED in-session 2026-08-05; LIVE-VERIFIED
    desktop / `neo4jtest` / `drydocs` DB]. Admits the two decisions G33
    deferred: directories enter the graph, and the non-`.py` majority gets
    typed. `:CodeDirectory` (prov:Collection, keyed `file_id`) +
    `CONTAINS_ENTRY` (prov:hadMember), ONE label for the whole tree so
    traversal is a single `-[:CONTAINS_ENTRY*]->`; the repo-root dir maps
    onto the existing `:Project`. New `code_tree.v1` loader running after
    `code_snapshot.v1` in `load-code-snapshot`. `HAS_MEDIA_TYPE`
    (dcat:mediaType) with 22 seeded `:MediaType` terms — 18 IANA-registered
    (iri = the registration page) + 4 conventional under
    `drydocs.local/format#` with `registered:false`; extensions with neither
    binding stay UNBOUND and CLI-reported, never guessed.
    **CONSTRAINT COUNT 52 → 53** (`codedirectory_file_id`) — your
    `EXPECTED_CONSTRAINTS` moves a SECOND time (it went 54→55 at the step-82
    port). ***THE CAUTION:*** `CodeTreeAdapter` keys its maps on RAW snapshot
    ids — after prefix stripping the repo root and the `drydocs/` package dir
    COLLIDE. Live: 1537 module + 264 dir rows, 0 rejected.

100. SFS TYPING CORRECTION — SNOWFLAKE IS A TARGET DB PLATFORM, NOT ETL
    (`ceff696`) [SME-RULED in-session 2026-08-05] [RECORD-CORRECTION].
    "Snowflake ETL" in the captured DAT SRE table names the
    loads-into-Snowflake JOB FAMILY the SFS code marks — not a software
    product. Consequence for the C25 prerequisite: the second missing
    software-registry row is `snowflake` the DATA PLATFORM (DBMS family,
    sibling of `oracle-db`), never a Snowflake ETL tool row, and an
    SFS-derived edge reads loads-into-Snowflake, not
    runs-a-Snowflake-ETL-framework. Recorded in both folder-naming twins and
    the platform-codes values twin (comment only — the K18 guard reads the
    CODE, all six still parse); the captured DAT table stays verbatim.
    ***YOUR SIDE:*** if you already authored a Snowflake registry row, check
    which family it landed in before C25.

101. G35 — THE SEAL TOM ROLE VOCABULARY: gate drafted, four clauses ruled,
    and ONE CODE FIX APPLIED AHEAD OF SIGN-OFF [SME-RULED; the fix
    TEST-PINNED; **the gate itself UNSIGNED**] (`867eadb`, `b79f691`,
    `3df06de`, `80fd9a1`, `80180c1`, `e5c5adc`, `50337ad`, `67daf0a`;
    O44 groom `ba712af`+`4188f81`; Idea-75 `d0123d5`).
    **THE ONLY PART THAT CHANGES BEHAVIOR is `50337ad`**, and it is a data-loss
    fix: `drydocs_core/models/seal.py` gains `SealRole.OPERATE_MANAGER` and
    re-points `_ROLE_CANONICAL["operate manager"]` from `"L2 Operate Manager"`
    to `"Operate Manager"`. Before it, a bare Operate Manager row was
    rewritten to L2 and MERGEd onto that person's genuine L2
    `attribution_id` — three source holdings became two, silently, survivor
    decided by batch order. NEW `tests/unit/test_seal_roles.py` (the module
    had NO tests) pins the invariant, not the instance: no alias may resolve
    to a canonical name asserting a level the alias does not itself name.
    RULED BUT NOT APPLIED — nothing ontological moved, the scheme still seeds
    7 concepts and `seal_contacts.cypher` still has its 4-branch crosswalk:
    L1/L2/bare Operate Manager are three classes; the `tech partner`→`CTO`
    alias STAYS (verified NOT a K5 breach — `HAD_ROLE` is minted only on a
    crosswalk hit and `cto` is not a branch); CBT is an optional class
    deliberately left unmapped so it loads flagged. Four clauses reached
    `config/gate-log.md` as two RECORD entries — the convention for a
    confirmed clause inside an unsigned gate.
    ***YOUR SIDE — CHECK BEFORE YOU RELOAD:*** if your real contact extract
    carries a bare "Operate Manager" alongside an L2 for the same person on
    the same app, those two have been ONE node. Taking `50337ad` makes them
    two, so it is a re-key, not a no-op. Producer has no bundled SEAL sample
    to reproduce with (both `seal_*__sample.csv` were deleted at `9d59f53`
    for carrying real seal_ids and never replaced), so this was measured on
    the synthetic taxonomy capture: 13 rows → 9 validating → 8 attributions
    before, 9 after.

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
