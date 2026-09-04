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

### R7 - the "module-local-cache bug" has no producer-side trace

The desktop's notes say the `cli_consumer` rewire fixed a module-local-cache bug. Nothing
producer-side records it: not the inbox, the port-prompt, the manifest, `cli_shared.py`, `cli.py`,
or any commit subject. If the fix touched `cli_shared.py` or `cli.py` (both canonical-producer,
the seven rows from RELAY-25 (2)), the next wholesale take erases it and it must back-flow now;
if it lived in `cli_consumer.py` (canonical-company), nothing is owed. One question to the
company: which file.

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
