# Carve-out 6 readiness - the company's carve-out 3 / chunk 5 report, and the plan for carve-outs 6-9

**Date:** 2026-09-04 · **Trigger:** the desktop lane's session notes (the CFG1 → CFG2 → PLAN2
proposal and the chunk-5 debts) and the company's carve-out 3 / chunk 5 report, relayed by the
SME 2026-09-04 with one question: is anything needed before carve-out 6? **Lens:** none - a plan
review against the tree (`/system-design` ran earlier in this session on a different subject).
**Classification:** Internal-Public (mechanism only; company commits are cited by sha as reported,
never with their bodies). **Pen:** reviews. **Decides nothing** - every ruling named here is a
signed one; anything new is written as DOC2 or gate material.

- **Reviewed at:** commit `5803d091` on `main`, port base `port-base-20260902`; venue NewThinkpad.
  *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Subject documents:** the ten-chunk workplan
  (`docs/reviews/port-test-review-and-workplan-2026-09-02.md`, chunks 4-10 and B3); ledger steps
  305-308 and RELAY-24/25 with their seven postscripts (`docs/port/port-prompt.md`);
  `PORT-MANIFEST.yaml` rows for `tests/unit/test_backlog.py`, `tests/unit/test_runbook_currency.py`,
  `drydocs_core/component_map.py` and the `row_may_match_nothing` block; items CFG1, CFG2, DOC1,
  DOC2, PLAN1, PLAN2, PLAN3, LIN2; `config/gate-prompts/idea-series-grammar.yaml`; the allocator
  (`.claude/skills/groom-backlog/validate.py`) and its guards (`tests/unit/test_backlog.py`).

## 0. Verdict

**Nothing on the tree blocks carve-out 6.** PLAN1, PLAN3 and the signed gate are inside the range
the company is applying (`375dd962`, `e7dc4153` and `39b90843` are all ancestors of
`port-base-20260902`); the freeze guard passes the company's known id set (run here, R1); and
ledger step 305 already carries the interim mint rule. **One thing changes how carve-out 6 is
applied:** `tests/unit/test_backlog.py` is a per-entry file, and the ledger's brackets at steps
305 and 308 call it canonical-producer - the same wholesale-take class that destroyed the
company's `DEFERRED_VERBS` table at carve-out 2. Apply it by the row (R1). **One thing is missing
from the plan as reported, and it is not carve-out 6's:** the vocabulary migration, T24 (1),
appears nowhere in "next: 6, 7, 8, 9", and the SME ruling puts it before the wipe (R2).

Premises verified: 12 of 13 held. The one that did not: "RELAY-23 says take `component_map.py`
canonical-producer" was true at the tag and is fixed past it - the per-entry row landed at
`fe4df356` (their Idea-10017), which carve-out 7 must take with the manifest (R3).

## 1. The report, transcribed

As relayed; the producer holds no transcript.

| sha | what |
|---|---|
| `d0f6610a` | carve-out 3 - post-tag producer fixes, by name (9 files) |
| `d773dd18` | chunk 5 - component map, its two readers, the `cli_consumer` rewire (12 files, 768+/290-) |

Suite: 22 failed / 2810 passed / 71 skipped - 0 new, identical set across both commits. All 38
reconcile guards green with `RECONCILE_BEFORE_DIR` armed.

Four things the company carried forward, condensed from its words:

1. The seventh postscript closed both its debts: `test_cli_registry.py` came back by name and
   lands 4 passed / 3 skipped as predicted; the `test_source_bindings.py` manifest row arrived at
   `02580f2c`.
2. A regression of its own, found by an armed guard rather than by reading: carve-out 2 took
   `test_runbook_currency.py` wholesale though its row is per-entry, destroying the company's
   `DEFERRED_VERBS` table and its test - invisible until now because
   `test_port_reconcile_guards.py` had been excluded from suite runs. Ruled accept rather than
   restore: S8's `cli.py` registers both verbs, so T22 is discharged and the guard's shrink-only
   rule requires them gone.
3. The finding it most wants the producer to act on (their Idea-10017): `component_map.py` has no
   manifest row and RELAY-23 says take it canonical-producer, but it is the third file holding the
   facts that made `test_module_boundary.py` and `MODULE_MAP.md` per-entry at J68. Measured: 19
   unclassified modules, the same three families J68 names.
4. Its own error, caught by the currency guard: two missing `MODULE_MAP.md` rows authored from the
   packages' own docstrings, whose path citations were both stale. Reading the source was right;
   trusting its pointers was not.

Three producer debts inboxed there: Idea-10015 (the drop guard has no accepted-drop seam),
Idea-10016 (lane-handoff needs a producer-side `row_may_match_nothing`), Idea-10017 (the
component-map row).

Next per its plan: carve-out 6 (PLAN1 + PLAN3; the `series:` map already landed as chunk 5's
coupled data), then 7 (`.claude/**` path-by-path), 8 (`web/**` by name, K7-K15), 9 (the acronym
sweep with the J55 test). The known-red `test_company_mints_in_the_company_band` still wants
`PRODUCER_BASELINE` bumped to `port-base-20260902`.

## 2. Findings that change what happens at carve-out 6

### R1 - `test_backlog.py` is per-entry; steps 305 and 308 bracket it canonical-producer

Step 305 opens `[allocator + guards canonical-producer; modules.yaml per-entry; CLAUDE.md
canonical-producer]` and step 308 `[validate.py + test_backlog.py canonical-producer]`. The
manifest row for `tests/unit/test_backlog.py` is **per-entry**: "the ALLOCATOR-BAND block is
per-side ... producer asserts <= 9999, the company asserts >= 10000, and each keeps its own
PORTED_COMPANY_IDS." The row's own warning: "Taking this file wholesale would make the company's
suite demand that its own 10000+ ids are illegal." The company's carve-out 2 regression (§1,
item 2) is exactly this class, and the report says the guard that caught it was excluded from
runs until now.

Apply carve-out 6 by the row:

- **Crosses whole (mechanism):** `FROZEN_ON`, `FROZEN_SERIES`, `FROZEN_BAND`, `_frozen_strays`,
  and the freeze and module tests (`test_the_allocator_and_the_guard_agree_on_the_frozen_snapshot`,
  `test_every_module_has_a_series_code_and_no_code_can_collide`,
  `test_frozen_series_take_no_new_ids`, `test_the_legacy_band_ids_pass_and_the_next_one_does_not`,
  `test_a_module_series_id_belongs_to_that_module`); `validate.py` whole (`.claude/**` is
  canonical-producer, `PORT-MANIFEST.yaml:815`); `modules.yaml` by its union rule (never drop a
  company module).
- **Stays the company's:** the ALLOCATOR-BAND block - `PRODUCER_BAND_CEILING` as they hold it,
  their inverted comparison, their `PORTED_COMPANY_IDS`, and
  `test_company_mints_in_the_company_band`.

Verified here, sample-reproducible (laptop, `5803d091`): `_frozen_strays` over `DD1`, `DD7`,
`DD10`, `G10001`-`G10003`, `DD10001`-`DD10003`, `G136`, `LOAD12`, `PLAN3`, `CFG2` returns `[]`;
the controls `G137`, `G10004`, `DD10004`, `J10001` are strays. A DD number below the ceiling is
judged against neither table (DD is reserved, not frozen), so the company's DD1-DD10 pass without
a fixture. The agreement guard needs `validate.py` and `test_backlog.py` taken at the same commit
or later (`e7dc4153` and after; both are inside the range).

**Producer-side fix (port pen):** the row's `entry_rule` predates PLAN1 and names only the band
block, so it does not say which side of the split the freeze block sits on; add one sentence
naming the freeze block as mechanism that crosses whole, and correct the two brackets at steps
305 and 308 to `test_backlog.py per-entry`. The mislabel is not hypothetical on this tree: the
same bracket shape is what sent `test_runbook_currency.py` wholesale.

**The one place the ported mechanism can go red on the company's data, and the fix is theirs:**
`test_every_module_has_a_series_code_and_no_code_can_collide` asserts every name in
`modules.yaml` `modules:` has an entry in its `series:` map (`test_backlog.py:400-419`;
`module_series()` reads the map, `validate.py:301-310`). The company's `modules.yaml` is a
per-entry UNION that keeps its own modules ("never drop one"), and its `component_map.py`
carries at least one company-only group (`docmeta-acquire`, per the `test_module_boundary.py`
row) that CORE1's join guards tie to a `modules.yaml` name. Every company-only module therefore
needs a `series:` code at carve-out 6 - three or more uppercase letters, not a frozen letter,
not `DD`, unique across the union and not one of the producer's twenty (`CORE`, `LOAD`, `REV`,
`PLAN`, `DOCGEN`, `LIN`, `DEEP`, `REM`, `WEB`, `API`, `AGENT`, `META`, `PORT`, `LIBS`, `REF`,
`TAX`, `ONT`, `CFG`, `GRAPH`, `DOC`). The code is per-side data in a per-entry map; it is not a
licence to mint under it (R4) - the code, like the id, becomes edition-scoped when PLAN2 ports.
Said here rather than left to the guard, because the fix a session reaches for when a ported
test names its own module is to delete the test, which is the `DEFERRED_VERBS` class again.

### R2 - T24 (1), the vocabulary migration, is not in the plan as reported

The company's "next" is 6 (PLAN1 + PLAN3), 7 (`.claude/**`), 8 (`web/**`) and 9 (the acronym
sweep, which is T24 (2)). The workplan's chunk 5 - 44 id renames, 5 fragment renames, the fold
into `52-local-human`, then `drydocs_lineage/writer.py` and
`drydocs_lineage/extractors/controlm_inventory.py` - is absent, and what the company calls
chunk 5 (`d773dd18`) is component-map and `cli_consumer` work, which the workplan files under
chunk 4. Either the company renumbered and T24 (1) has a slot the report does not show, or it is
unscheduled.

Why it is not carve-out 6's problem but is the next one's: the SME ruling is renames BEFORE the
wipe (the T24 row; workplan B3), the reload in chunk 8 must write `business_application_has_port`
natively so `migrate_vocab_ids_g101.cypher` stays a no-op, and the two lineage modules cannot be
taken before it without dangling vocabulary ids. Carve-outs 6-9 are all pre-wipe, so the order
still closes if T24 (1) is inserted before the bootstrap-and-wipe step. Also absent from the
report: chunk 4's union check (`scripts/port_backlog_union.py --producer-ref port-base-20260902`
exit 0), which B3 makes the precondition of everything in chunks 5-8.

### R3 - carve-out 7 (`.claude/**` path-by-path) needs the manifest at `fe4df356` or later

Two of the company's three inboxed debts are closed past the tag in `PORT-MANIFEST.yaml`
(`fe4df356`): the `row_may_match_nothing` entry for `.claude/skills/lane-handoff/**` (their
Idea-10016 - without it their totality guard trips on a never-port row that matches nothing on
their side) and the per-entry row for `drydocs_core/component_map.py` (their Idea-10017 - "MOVES
WITH `tests/unit/test_module_boundary.py` and `MODULE_MAP.md`, ALWAYS"). The manifest is
canonical-producer; take it by name at `fe4df356` or later with carve-out 7, or the guard reports
Idea-10016 a second time. Two `.claude/` facts to keep straight while walking the directory:
`.claude/skills/*-workspace/**` is gitignored (`.gitignore:188`) and never arrives, so nothing
under it is missing; `.claude/settings.local.json` is machine-local, and the `oracle-db` skill the
company is expected to turn on lives there (CLAUDE.md §2).

## 3. Mechanics

### R4 - the interim mint rule is already relayed; its reason is not

Step 305 says: "until then mint nothing new in a letter series and nothing at all in a module
series until PLAN2's `edition:` key exists on your side." The mechanism behind it belongs in
DOC2 (a) as one sentence, because a rule with no reason gets patched around: `next_id()`
(`validate.py:313-352`) pools local items, every remote ref and history, takes max+1, and has no
notion of which side it runs on - so a company-side `--next-id --module load` returns the
producer's next number, and the next roll mints the same one (the I6 collision class). PLAN2's
edition-key refusal is what turns the request into a mechanism; until it ports, the sentence is
the guard. The Idea path is unaffected by carve-out 6: `_report_allocation` short-circuits `Idea`
before `next_id()` (`validate.py:360-364`), so `--next-id Idea` still captures company-side
(band-shaped, `Idea-10018` next) - which is the carve-out the unsigned rider `idea-series-grammar`
(C1) makes a ruling.

### R5 - `test_company_mints_in_the_company_band` and the `PRODUCER_BASELINE` bump

Bumping the baseline to `port-base-20260902` is housekeeping (the constant names which tree's ids
are the producer's) and is fine. The assertion itself - the mirror `n >= 10000` asked for at step
160 - is withdrawn forward-only by the signed gate (§C4), and DOC2 (b) replaces it with the
edition-segment check when PLAN2 ports. So: bump, extend nothing, retire it with the PLAN2 take.
It must not be made green by re-opening any mint path.

### R6 - "T22 is discharged": one leg remains, and it folds into chunk 7

The accept ruling on `DEFERRED_VERBS` is right: `_client(database)` is `drydocs/cli.py:207`,
`docs-verify` registers from `cli_docs.py`, `bootstrap-schema-graph` from `cli_schema.py`, and the
shrink-only rule wants the exemption gone. T22's third leg, the `ddschema` provisioning DDL
(`drydocs_core/schema/provisioning/`: `01_databases.cypher`, `02_proxy_constraints.cypher`,
`provision.ps1`), is a RUN on the company instance, not a take, and chunk 7 re-provisions after
`DROP DATABASE` anyway - so it is discharged at chunk 7, not now. The T22 row's status cell still
reads "pending (producer belief, as of 2026-08-03)"; refresh it with the company's chunk-5 sha
(port pen).

### R7 - the "module-local-cache bug" has no producer-side trace, but it has a producer-side candidate

The desktop's notes say the `cli_consumer` rewire fixed a module-local-cache bug. Nothing
producer-side records it by that name: not the inbox, the port-prompt, the manifest,
`cli_shared.py`, `cli.py`, or any commit subject. If the fix touched `cli_shared.py` or `cli.py`
(both canonical-producer, the seven rows from RELAY-25 (2)), the next wholesale take erases it and
it must back-flow now; if it lived in `cli_consumer.py` (canonical-company), nothing is owed.

**NARROWED 2026-09-04 (laptop), so the answer is a confirmation rather than an investigation.**
The producer already carries a fix for exactly this bug CLASS, and it is the seam the rewire was
made against. `register_loaders` (`drydocs/cli_shared.py:398`) exists because `LOADER_SOURCE` and
the unchained set are DERIVED from `LOADER_REGISTRY`, and the root re-exports the dict OBJECTS
(`cli.py:107-118`). Two failure modes follow, and both are module-local-cache bugs in the plain
sense that an imported name is a local cache of an object:

- **Rebinding** `LOADER_REGISTRY` in the consumer strands every module that already imported it.
  RELAY-25's sixth postscript names this: the seam "re-derives the views IN PLACE ... a rebind
  would strand every earlier import."
- **Mutating** `LOADER_REGISTRY` directly leaves the two derived views stale. The docstring says
  so, and records the discovery: "Found at the company's chunk-4 S8 take (2026-09-03): seventeen
  company loaders vanished from the ad-hoc `load` path because the monolith's registry was
  replaced and nothing declared them back."

That is the same seventeen loaders, the same take, and the same session the rewire belongs to. So
the likely answer is that the fix IS the rewire - a `register_loaders` call from
`cli_consumer.py`, replacing a direct mutation or rebind - in which case the producer half is
already `f338097d` (past the tag, take by name) and **nothing back-flows**. The question to the
company reduces to: confirm the fix is a call to the producer's seam from your own module, or
name the producer file it edited. Only the second answer owes a back-flow, and it owes it before
the next roll takes those seven rows wholesale.

### R8 - 22 known-red carried across two carve-outs

RELAY-25's first postscript rules: "a guard is allowed to be red only when the NEXT carve-out is
its fix." Twenty-two carried red across carve-out 3 and chunk 5 is consistent with that only if
each names its carve-out. The report's baseline-diff discipline ("0 new, identical set") is the
right instrument, and the list is the company's ledger to keep; worth asking for once, by fixing
carve-out, so a fall-through a later carve-out introduces is not hidden behind a known one - the
exact mechanism the first postscript describes.

## 4. Producer-side, before the next roll (none of these blocks the company)

| # | What | Where it stands | Pen |
|---|---|---|---|
| 1 | DOC2 (a), the freeze relay proper | `todo`; the interim rule is at step 305; add R4's one-sentence reason | backlog · port |
| 2 | R1's two fixes: the `test_backlog.py` `entry_rule` sentence, the brackets at steps 305 and 308 | not done | port |
| 3 | P3, P4, P6 from the workplan's Part A (chunk 10, item c) | not built, not inboxed, not minted; the seven consumer-only tests still skip here (`test_port_reconcile_guards.py` + `test_port_manifest.py`: 44 passed / 7 skipped, laptop) | backlog |
| 4 | The T22 status cell | stale since 2026-08-03 (R6) | port |
| 5 | The rider `idea-series-grammar` | DRAFTED, unsigned; the SME's ruling unblocks PLAN2 (b), which DOC2 (b) waits on | gates (the SME) |
| 6 | PLAN2 | `todo`, ready (CFG2 done); clause (b) waits on row 5 | backlog |

Landed since the desktop's notes, verified on this tree: CFG1 (`2c744212`), CFG2 (`df0c49de`,
`ba7f7920`), DOC1 (`5803d091`, CI green), PLAN3 (`e7dc4153`), the rider drafted (`bf1a6f86`), the
three company debts closed or inboxed (`fe4df356`). RELAY-26 does not exist; DOC2 takes the next
free number at roll time.

## 5. Checklist for the company's carve-outs 6-9, keyed to the workplan

| Carve-out | Take | Guard that closes it | Watch |
|---|---|---|---|
| 6 - PLAN1 + PLAN3 | `validate.py` whole; `test_backlog.py` BY THE ROW (R1); `modules.yaml` union, with a `series:` code for every company-only module (R1); `CLAUDE.md` mint rule | `test_frozen_series_take_no_new_ids`, `test_the_legacy_band_ids_pass_and_the_next_one_does_not`, `test_every_module_has_a_series_code_and_no_code_can_collide`, both agreement guards; `--next-id G` and `--next-id DD` refused by name | mint no module-series id until `edition:` exists (R4); bump `PRODUCER_BASELINE`, extend nothing (R5) |
| T24 (1) - where it goes | fragments first, the vocabulary guards green, then the two lineage modules with their tests | `test_schema.py`, `test_yaml_fragments.py`; gate-bound activations cite the company's gate; zero dangling ids | precondition: the union check exits 0 (R2); do not run the migration cypher |
| 7 - `.claude/**` | path-by-path; `PORT-MANIFEST.yaml` at `fe4df356` or later | the totality guard and `test_no_manifest_row_matches_nothing` in `test_port_reconcile_guards.py` | R3's two `.claude/` facts |
| 8 - `web/**` | by name, never `web/src` wholesale (K7-K15) | the drift guards on the company's sources; `web/src/generated/**` regenerated, never carried | the workplan's rule 2 |
| 9 - the acronym sweep (T24 (2)) | 72 producer files; `cdo-crosswalk.yaml` carved out by hand (canonical-company; DRAFT stays DRAFT) | J55 fail-closed: the company authors its RENAMED note in its `internal/<token>-reference/README.md` (RELAY-25, Q2) | never take a producer signature into a company gate prompt |

Then chunk 7's bootstrap audit and `DROP DATABASE` for both databases, the reload, and the
report, as the workplan has them.

---

## 6. VERIFY - carve-out 6 as executed (2026-09-04, laptop, re-read at `d62ac0e8`)

The company ran carve-out 6 and reported before its full suite landed: `test_backlog.py` 16
passed including all five ported freeze tests, both refusals firing by name, `validate.py`
ALL CHECKS PASS at items=540 phases=18 modules=20, 38 reconcile guards green with
`RECONCILE_BEFORE_DIR` armed, ruff clean, and a baseline regeneration of 519 to 642 ids. Three
findings came back. **All three hold. Two of them correct this review.**

### F1 - the ALLOCATOR-BAND block does not have the shape R1 described. Their fix is the right one

R1 told them to keep "your `PRODUCER_BAND_CEILING` line, your `PORTED_COMPANY_IDS`". They hold
neither: a 2026-08-24 company-polarity rework replaced both with `COMPANY_BAND_FLOOR = 10000`
and `PRE_PARTITION_COMPANY_IDS`. R1 was written from the producer's file and the manifest row's
wording, and the row describes the split rather than their names. **The review was wrong about
the shape; the split it named was right.**

Their resolution is better than the one R1 implied. `_frozen_strays` reads
`PRODUCER_BAND_CEILING` (`test_backlog.py:378`) to separate a legacy band id from a letter id,
so the ported mechanism needs the name. They defined `PRODUCER_BAND_CEILING = COMPANY_BAND_FLOOR
- 1` rather than editing the producer's function: the same boundary from their polarity, the
mechanism crosses verbatim, and the next roll diffs clean. That is the per-entry rule applied
exactly - mechanism whole, per-side data local - and it satisfies
`test_the_allocator_and_the_band_guard_agree_on_the_ceiling` (`:274`), which compares their
constant to the allocator's literal 9999.

**One forward note that rides with it.** `COMPANY_BAND_FLOOR` is a RETIRING constant: gate §C4
retires both partition rules forward-only, and the edition segment replaces the band when PLAN2
ports. `_frozen_strays` is not retiring - it judges legacy band ids for as long as the six exist.
So when the band rule goes, `PRODUCER_BAND_CEILING` must survive its source: pin it to a literal
9999 with the reason, or the derived alias disappears with the constant it derives from and takes
the freeze guard's band arm with it.

### F2 - no series code was needed. The measurement retires R1's addendum

R1's addendum said every company-only module needs a `series:` code and named `docmeta-acquire`
as the likely one. They measured: `docmeta-acquire` is a component GROUP in `component_map.py`
that maps to the already-registered `drydocs-docmeta` module, and their `modules.yaml` is
identical to the producer's at 20 modules and 20 codes, because carve-out 5 already unioned it.

Verified here. `component_map.py:243` states the join as group to module, `:256` carries the
producer's own `"docmeta": "drydocs-docmeta"`, and the guard at `:267` asserts modules.yaml
equals core plus the `COMPONENT_MODULE` values plus the work-area set - an equality on VALUES, so
two groups mapping to one module is legal and adds no row. `modules.yaml` carries 20 series
entries at `port-base-20260902` and 20 at HEAD, so the count is stable across the range.
**The addendum was a caution, and measurement is what retires a caution.** The rule it stated
stands for any FUTURE company-only module; it had no subject today.

### F3 - the slice was not closed under dependency, and this is the workplan's G5 firing

Taking the four named items turned `test_dependencies_resolve_and_are_acyclic` and
`test_derived_summary_is_consistent` red with `KeyError: CFG2`, both green before. They computed
the transitive closure instead of patching the symptom and took CFG1 and CFG2 as clean-adds.
Correct, and correctly diagnosed: the workplan's G5 is "slice closure is nobody's test", P2 is
the proposed test, and P2 is one of the three Part A items §4 row 3 records as not built, not
inboxed and not minted. **This is the second time G5 has cost a session real work.** It raises
P2 from a proposal to the item the evidence now names.

**What their closure rule is missing, and it is the reason to write it down rather than repeat
it.** An item file's closure is not `depends_on` alone. Three edges must resolve for the backlog
guards to pass, and the third is the one that bites next:

1. `depends_on` - `test_dependencies_resolve_and_are_acyclic` (`:633`). The one they hit.
2. `epic` - `test_path_is_the_identity` (`:110-119`) asserts every item's epic has a file under
   `epics/`. The three they took need `ontology-mapping`, `release-infrastructure` and
   `project-board`; all three are producer files added in range, so their tree had them.
3. `gates` - `test_declared_gates_are_lists_of_known_prompt_slugs` (`:610`) requires
   `config/gate-prompts/<slug>.yaml` to EXIST. `config/gate-prompts/**` is canonical-company and
   ledger 306 says the producer's signed prompt never overwrites their draft or absent file, so
   this edge crosses a class boundary: the item ports, the prompt it names does not.

Edge 3 has a live tripwire. `PLAN2.yaml` declares ONE gate at `port-base-20260902` and TWO at
producer HEAD - `idea-series-grammar` was added at `bf1a6f86`, past the tag, and its prompt file
is past the tag too. A PLAN2 taken from HEAD names a gate prompt that cannot exist company-side
and turns that guard red; a PLAN2 taken at the tag does not. Which leads to the one thing worth
confirming before carve-out 7.

### V1 - which ref did the item files come from? "or later" was wrong for item files

The hand-carried work order said "at `e7dc4153` or later" for the take-whole set. **That phrase
is safe for mechanism and unsafe for item files, and the defect is the work order's.** Measured
across the files it covered:

| File | Changed after `e7dc4153`? | Does "or later" matter? |
|---|---|---|
| `validate.py`, `test_backlog.py` | no commits | no |
| `modules.yaml` | one, `62c19a8e` (CORE1), IN range; 20 codes at the tag and at HEAD | no |
| `CLAUDE.md` | three, ALL PAST THE TAG - J76 the instrument rule, J62 pre-commit, lane-handoff iteration 2 | **yes** |
| `CFG1.yaml`, `CFG2.yaml` | `todo` at the tag, `done` at HEAD | **yes** |
| `PLAN2.yaml` | one gate slug at the tag, two at HEAD | **yes** |

Two consequences to check rather than assume:

- **CFG1 and CFG2 taken from HEAD arrive `done`,** while every artifact their acceptance names
  (`config/taxonomy/domains.yaml`, `editions.yaml`, the two registry modules, their two test
  files, the two JSON schemas) landed 2026-09-04, past the tag, outside the range. A `done` item
  whose subject is absent is a board that lies, and it self-corrects at no future roll because
  the file already matches. Taken at the tag they arrive `todo`, which is true on their tree and
  is exactly what the interim mint rule waits on. Their baseline regeneration measured 642, which
  is the producer's item count at `port-base-20260902` to the id (645 at HEAD), so their range
  discipline reads as tag-pinned; this is a confirmation to state, not an accusation.
- **`CLAUDE.md` taken from HEAD** carries three mechanisms outside their range, two of which cite
  paths they do not hold: `.pre-commit-config.yaml` (J62) and
  `.claude/skills/lane-handoff/SKILL.md` (never-port, and the row that makes it match nothing
  company-side is the `fe4df356` manifest R3 sends with carve-out 7). Their own carve-out 5
  finding was a stale path citation caught by the currency guard, so this is the same class.
  Take `CLAUDE.md` at the tag, or take it at HEAD deliberately and expect the currency guard to
  name those two.

**Producer-side fix (port pen), beyond R1's two:** the ledger's take instructions should say
`at port-base-20260902` for item files, and name a sha only where a postscript rules a
take-by-name. "Or later" is a mechanism idiom and it does not survive contact with a file whose
`status` is data.

### V2 - reconcile 16 against 26

The producer's `test_backlog.py` holds 26 test functions; their run reports 16 passed. The
per-entry split moves ONE block of three (`test_producer_allocates_below_the_company_band`,
`test_the_allocator_and_the_band_guard_agree_on_the_ceiling`,
`test_the_allocator_refuses_to_cross_into_the_company_band`) to their inverted equivalents, which
keeps the count at about 26. A ten-test gap is either a filtered run, a set of producer-only
guards absent by construction (`test_no_id_carries_two_different_titles_across_the_remote_trunk`
needs the producer trunk; `test_monolith_is_a_tombstone` needs their `backlog.yaml` tombstone),
or guards a wholesale take dropped earlier. **Name the delta in the report** - which producer
guards their file does not carry, and the reason for each. Shrink-only applies to exemption
tables; it applies to guards with more force.

### V3 - what the report already settles, and what is still owed

Settled and verified here: the baseline regeneration to **642** is the producer's item count at
the tag exactly; **C35, G116 and G117** are producer ids added at `aed7229b`, so their
reclassification as producer-origin is right, and retiring the known-red band guard on that basis
is sound. R5 is discharged by that bump, and nothing was extended to make it green.

Still owed, both deferred by the company to the post-suite report, both fine: **R7** in §3 (which
file held the module-local-cache fix) and **R2** in §2 (where T24 (1) sits, plus the chunk-4 union
check's exit code). One correction to §2 on that check: their backlog holds 540 items against the
tag's 642 producer ids, so the union cannot exit 0 until the remaining classes land. That is
expected mid-port, and it makes the check the END gate of the range rather than a carve-out 6
precondition - which is how B3 reads it, and §2 should have said so.

**Where the answers land, and what closes each (Lane A relay, 2026-09-04).** Both questions were
posed by this file, so both close in it, under the `reviews` pen; the desktop has stayed off it.
R7 is narrowed in §3 to a confirmation with a named producer-side candidate, so the closing form
is one of two sentences: *the fix is a `register_loaders` call from `cli_consumer.py`, nothing
back-flows*, or *it edited `<producer file>`, which back-flows before the next roll*. R2 closes on
two facts: the carve-out or chunk that carries T24 (1), and the union check's exit code with the
producer ref it ran against. Until those arrive, §2 and §3 stay open by design - an unanswered
question recorded as open is the point of the section, and neither blocks carve-out 7.

One process note. The full-suite run excluded `test_port_reconcile_guards.py` by `--ignore` and
ran it separately with the env var armed. That is the correct way to run a guard that needs a
fixture the bare suite cannot give it, and it is the carve-out 2 failure mode only when the
separate armed run is missing from the same report. Theirs is not.
