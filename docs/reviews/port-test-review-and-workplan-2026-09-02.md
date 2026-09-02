# Port test review, and the company-side apply in coding chunks

**Date:** 2026-09-02 · **Trigger:** `/testing-strategy` — review the port tests as they stand
and as proposed, then plan the internal (company-side) port work in logical coding chunks.
The 2026-09-01/02 sessions (J68–J72, T24, RELAY-20–22, dossier 4) built and corrected the
reconciliation machinery; this document is the plan for USING it.
**Method:** the six `tests/unit/test_port_*.py` files read test by test (127 tests); the
modules they guard; the `reconcile-port` skill's procedure; `PORT-MANIFEST.yaml`; the
port-prompt's apply section, relays and T-rows; the company's own apply reports as relayed
(slices A–E, the +83, the acronym rename). Every claim cites where it was read.
**Classification:** Internal-Public (mechanism only; no org values, no instance names).
**Asks nothing back** — the company keeps its own ledger; this documents intent.

- **Reviewed at:** commit `75bfc3c5` on `main`, port base `port-base-20260901`; venue MSI.
  *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

---

## 0. Verdict

**The port test suite is strong where the port has been burned and absent where it has not
yet been.** 127 tests, 6 files, three deliberate detector-plus-companion pairs, entry rules as
code, a rename detector proven on the two real traps. What it does not have is a test of the
APPLY itself: every test checks a rule, a row, a parser or a detector in isolation, and the
three failures of the 2026-09-01 apply were none of those — they were slices that were not
closed under dependency (config→core, tests→scripts, tests→renders), caught by hand each
time. The one tier missing is a rehearsal: a synthetic consumer tree, a producer ref, the
apply run class by class, the guards asserted afterward. Part A proposes it, small.

**The company-side work is nine chunks, and their ORDER is the plan.** The order is not the
order of the directories and not the order of the ledger; it is: sources before renders, both
renames before the wipe, DROP DATABASE not DETACH DELETE, the CLI seam before the reload that
needs it, and the report last. Each chunk is one commit, closed under dependency, with a named
guard that turns green at its end. Part B.

**One producer-side action the plan forces, today:** the next roll carries PLAN1 (the letter
freeze, merged AFTER `port-base-20260901` — 113 commits already sit past the base), and the
company's `G10001–G10003` / `DD10001–DD10003` fail the frozen-series guard the day it lands.
Idea-242's trigger has fired: mint **PLAN3 = FROZEN_BAND** now, before that roll, not with
PLAN2.

---

# Part A — the port tests as they stand

## A1. Shape

| File | Tests | Reads | Guards |
|---|---|---|---|
| `tests/unit/test_port_preflight.py` | 27 | fixtures only (synthetic ledger/relay strings, fake `_exists`) | the opening sequence: ritual detection, ledger coverage, relay basis tags, cited-path resolution, next base tag |
| `tests/unit/test_port_reconcile_guards.py` | 38 | fixtures + the REAL tree + 7 consumer-only (`RECONCILE_BEFORE_DIR`) | entry rules as code (no downgrade, gate-bound activation, append-only), J16 fall-through, dead rows, the overlay seam |
| `tests/unit/test_port_rename_detect.py` | 28 | fixtures only | J72: id-set and text measures, structural and vanished-twin signals, ranking cap, idf discount, git rename parse |
| `tests/unit/test_port_backlog_union.py` | 17 | fixtures + 2 real-tree | J42: union diff, exclusions hygiene, reader failure modes, ASCII report |
| `tests/unit/test_port_manifest.py` | 13 | the REAL manifest | shape, vocabulary, shadowing, J68 coupling (declaration ↔ guard), J71 totality |
| `tests/unit/test_port_dispositions.py` | 4 | 2 synthetic, 2 real (manifest + port-prompt section order) | J69: classification order, render, every live disposition has an apply rule |

Pyramid reading: **unit 118 / integration 0 / consumer-side 7 / end-to-end 0.** The base is
wide and fast (the whole set runs in under 15 s inside a 4m07s suite). There is no middle.

**Three detector + companion pairs** — the pattern the repo treats as the standard for a guard
(`test_port_manifest.py:150`, `:264`, `:367`; `test_port_preflight.py:198`;
`test_port_reconcile_guards.py:918`; `test_port_rename_detect.py:446`). Every guard added by
Part A follows it: a detector, and the injected fault that proves it fires.

**Manifest:** 145 rows; `canonical-producer` 27, `per-entry` 26 (33 `entry_rule`s),
`canonical-company` 15, `never-port` 12, `evaluate` 8, `derived` 7, `union-append` 3,
`clean-add` 2, plus the `default_ok:` and `row_may_match_nothing:` blocks. All 145 are
shape-checked, shadow-checked, coupling-checked and totality-checked against the live file.

## A2. What is covered well

- **Rules as code, with the live tree passing its own rules**
  (`test_port_reconcile_guards.py:403`) — the consumer runs the same test with
  `RECONCILE_BEFORE_DIR` set and gets the before/after comparison for free.
- **The manifest cannot silently lie** — a row shadowed by an earlier glob (`:133`), a
  declaration whose guard carries a different disposition (`:249`, the J68 finding), a
  per-entry rule with a hole (`:354`, J71), a tracked path that falls through to `default:`
  with nothing written down (`test_port_reconcile_guards.py:854` — the guard that caught
  T1 in the tech-debt review the same day).
- **The rename trap is closed on both shapes** — a split keeps ids and loses prose; a rename
  keeps prose and loses the id; two measures, each proven to catch what the other misses
  (`test_port_rename_detect.py:81`, `:166`), and the idf discount proven never to switch
  containment off (`:580`, the `c6a3c6bc` fix).
- **Encoding is a test, not a memory** — the ASCII report (`test_port_backlog_union.py:244`)
  and the explicit `utf-8` in `port_rename_check.py`, because both machines are Windows.
- **J37/J66 clean.** The one prose assertion (`test_port_dispositions.py:105`, apply section
  above `STEP LEDGER`) guards the parser's own markers and says so; every other string
  assertion is on output the module itself renders.

## A3. Gaps

**G1 — No apply rehearsal (the missing middle).** Nothing exercises "given a consumer tree
and a producer ref, apply by disposition class and check the guards." The three dependency
failures of the 09-01 apply were all of this shape, and none of the 127 tests could have
caught them. Effort: medium. This is the one gap worth a day.

**G2 — The git/subprocess layer is untested end to end.** `port_preflight.run_checks`,
`venue_line`, `range_commits`, `added_documents`; `port_backlog_union.materialize_ref`,
`run_union_check`; `render_port_dispositions.newest_base_tag`, `changed_paths`;
`port_rename_check.producer_files`, `consumer_files`. Every `main()` in the four scripts is
unasserted, including the exit-code contract (0/1/2) the skill's step 5 documents. Effort:
low — a tmp git repo with two commits and a tag is a 20-line fixture.

**G3 — Seven tests can only run at the company.** The `@_needs_before` set
(`test_port_reconcile_guards.py:485,:497,:508,:521,:535,:601,:608`) skips here because the
before-snapshot directory only exists on the consumer. The comparison functions are pure
(`status_downgrades`, `unsigned_activations`, `append_only_violation`, `dropped_names`); only
`before_text`'s source needs redirecting. A committed fixture of the four snapshot files (plus
the two optional lists) and a `monkeypatch.setenv` would run all seven here, on every push.
Effort: low.

**G4 — The skill's before-snapshot one-liners are untested.** `SKILL.md:367–380` tells the
company to run four `python -c` one-liners that dump `relationship_vocabulary`,
`taxonomy-ontology-map`, the backlog and the gate log, plus two optional lists
(`detect.CONFORMANCE_RULE_IDS`, the runbook keys). If any of those import paths moves
(S2, S5, O58 have each moved one), the snapshot step fails at the consumer with no producer
signal. Effort: low — one test that runs each one-liner in a subprocess and asserts non-empty
output.

**G5 — Slice closure is nobody's test.** A slice is closed when every test it takes has its
subject in the same slice and every derived artifact it takes has its sources before it.
The repo knows both relations: `test_port_manifest.py` pairs declarations with guards; the
manifest's `derived` rows name their renderers; `tests/unit/*` import their subjects. Effort:
medium, and it is G1's core.

**G6 — The disposition renderer and the skill's Track-1 list are two hand-kept lists.**
`SKILL.md:339` enumerates the Track-1 pytest files; `render_port_dispositions.APPLY_ORDER`
enumerates the classes. Nothing asserts the Track-1 files exist or that a guard the manifest
names is in the list. Effort: trivial.

**G7 — The overlay file's CONTENT is unchecked producer-side** — only its declaration
(`test_port_reconcile_guards.py:1052`). The overlay is the company's rebind seam (D2); a
malformed overlay is found at the company. Effort: low.

## A4. Proposed tests

| Id | Test | Type | Closes | Example case |
|---|---|---|---|---|
| P1 | `tests/unit/test_port_apply_rehearsal.py` — build a tmp consumer tree from a fixture (12 files spanning all eight classes), a tmp producer ref two commits ahead with one change per class plus one rename, run `render_port_dispositions.classify` over the diff, apply each class by its rule (`git checkout` for canonical-producer, entry-rule merge for per-entry, append for union-append, skip for canonical-company/never-port, regenerate for derived), then run the reconcile guards against a before-snapshot taken at the start | integration (tmp git, no network) | G1, G5 | the consumer's extra per-entry row survives; the derived file is regenerated, not carried; the renamed file is reported before the clean-add class runs; a per-entry take with the entry rule removed FAILS (companion) |
| P2 | `test_slice_is_closed_under_dependency` — for any proposed path set, compute the closure: tests → subjects (import scan through `tests/source_scan.py`), derived → sources (manifest `derived` rows), declaration → guard (J68 pairs); assert the set contains its closure or name what is missing | unit | G5 | `tests/unit/test_world_map_generated.py` alone → names `scripts/render_world_map.py` and `external/geo/...` as missing; the E slice as applied on 09-01 → names the three renderers |
| P3 | `test_port_scripts_exit_codes` — each `scripts/port_*.py` `main()` in a subprocess against a tmp repo: clean → 0, finding → 1, misuse → 2; output stripped of ANSI | CLI contract (allowed by J37: exit code + message IS the contract) | G2 | `port_backlog_union.py --producer-ref <tag>` with an injected deleted item → 1 and the id in the message |
| P4 | `tests/fixtures/port_before_snapshot/` + a fixture that sets `RECONCILE_BEFORE_DIR` to it — the seven consumer-only tests run here | unit (unskipped) | G3 | the fixture's vocabulary carries one `active` entry the live tree deprecates WITH a gate citation → passes; strip the citation → fails |
| P5 | `test_skill_snapshot_one_liners_run` — the four/six one-liners extracted from `SKILL.md` between markers, run in a subprocess, non-empty output | subprocess (allowed: the prose IS the subject, and it says so) | G4 | move `yaml_fragments.merged_text` → the test names the one-liner that broke |
| P6 | `test_track1_list_resolves` — every path in the skill's Track-1 list exists; every guard named by a manifest `guard:` field is in it | unit | G6 | delete a test file → named |
| P7 | `test_overlay_content_well_formed` — parse the overlay, every row has a path that matches a manifest row, no row re-declares a `never-port` | unit | G7 | overlay row for `internal/**` → fails |

**Coverage target for the port layer:** every function in `drydocs/port_*.py` imported by at
least one test (today: the pure layer 100%, the git layer 0%); the four scripts' `main()`
each with one exit-code test; the seven consumer-only tests unskipped producer-side; P1 green
on the fixture AND on a replay of the 09-01 D+E slice (the real failure, as a regression).
Runtime budget: +20 s to the suite, all of it P1 and P3 (tmp git).

**Not proposed, on purpose:** a live-Neo4j test of the wipe/reload (that is the company's
run, on the company's graph — J18 says a live claim names its venue, and this venue is not
theirs); a coverage threshold on the port modules (report first — the tech-debt review's T2
rule); retries.

---

# Part B — the company-side apply, in chunks

## B0. Where the apply stands (as relayed; the company's ledger is the record)

- **Range:** `port-base-20260826..port-base-20260901`, 296 commits, 519 touched paths across
  eight classes (canonical-producer 129, per-entry 154, default_ok 165, evaluate 29,
  union-append 16, canonical-company 14, never-port 8, derived 4); 88 diverged paths on the
  company's own census. Both numbers are right; they count different things.
- **Applied:** slices A–C, then **D committed alone** (the `cli.py` surgical merge and
  `validate_fact_rows` — the hard-won parts, protected per J31).
- **Held:** slice E, because its new tests assert generated artifacts that do not exist
  until the renderers run (RELAY-22: the +83 is a render step, not a port problem).
- **Applied 2026-09-02:** the retired-acronym rename — 13 renames, 50 files, 201 mentions,
  residual outside `internal/` zero, J55 green (RELAY-21 correction). T24 item (2) is
  therefore done; the T24 row's status cell still says deferred and should be read as
  "done for (2), open for (1)".
- **Deferred by SME ruling (T24):** (1) the vocabulary migration — 44 id renames, 5 fragment
  renames, the fold of `41-local-seal` / `42-local-catalog` into `52-local-human`, AND its
  code dependency: `drydocs_lineage/writer.py` and
  `drydocs_lineage/extractors/controlm_inventory.py` reference the new ids exclusively and
  cannot port before it.
- **Owed on the live graph (T23):** the S3 re-key (`DROP CONSTRAINT port_unique` then
  `CREATE CONSTRAINT port_app_key`, `drydocs_core/schema/constraints.cypher:75–76`, all eight
  key-bearing sites in one apply), the C17 orphan count before the every-run flag, the
  SF1/F1 edge migration. S10's `PreCutoverApplicationGuard`
  (`drydocs/loaders/app_identity.py:42`) prevents the crash on all five company MERGE sites;
  it repairs nothing.
- **Owed in the CLI (T22 / DD6):** `_client(database)`, the `docs-verify` and
  `bootstrap-schema-graph` verbs, the `ddschema` provisioning DDL.
- **Unexamined:** ~430 files, 217 of them classifying as clean-adds; the rename detector
  has not yet been run over them (RELAY-20).
- **Already past the base, riding the next roll:** 113 commits including PLAN1 (the freeze),
  the J72 detector's six revisions (hand-carried by dossier 4, pin `c6a3c6bc`), the
  `web/src/generated/**` → `derived` manifest fix, the RELAY-21 correction, the gate
  `ontology-domain-registry-and-edition-grain` and its eight items.

## B1. The five ordering rules the chunks obey

1. **Classes, not directories.** Work the manifest's apply order — canonical-producer →
   canonical-company (no action) → per-entry → union-append → evaluate → DEFAULT → derived.
   A derived class is worked LAST by construction because it is regenerated from everything
   before it. The 09-01 apply failed closure three times working directory-led; J69 exists so
   the next apply does not.
2. **Sources before renders (F before G).** Never `git checkout` a generated artifact: a
   carried render passes the drift guard while describing the producer's estate.
3. **Both renames before the wipe.** Reload under the old vocabulary and you write ~22,956
   `seal_has_port` edges and then migrate them; adopt the vocabulary first and the reload
   writes `business_application_has_port` natively and `migrate_vocab_ids_g101.cypher` is a
   no-op you never run.
4. **DROP DATABASE, not DETACH DELETE — and read the undeclared-constraints report first.**
   A data-only wipe leaves every constraint standing, including the `membership_id` residue
   dropped at G99 and still enforcing on both instances (G130). `drydocs bootstrap` prints
   the live-but-undeclared list (`drydocs/cli_schema.py:320`); read it, then drop schema and
   data together. Per database: `drydocs` and `ddschema` are separate.
5. **One commit per chunk, closed under dependency, a named guard green at its end.** If the
   guard is red, the chunk is not done; nothing in a later chunk is started to make it green.

## B2. The chunks

Each chunk: scope · order inside it · the commands · the guard that closes it · what it does
NOT do. Commands are from the company checkout with the producer remote fetched
(`git fetch cewilson`), `RECONCILE_BEFORE_DIR` set to the snapshot taken in chunk 1.

### Chunk 1 — Rehearsal prep: snapshot, classify, look before adding (no apply)

- **Scope:** the opening sequence of the `reconcile-port` skill, plus the two looks the
  09-01 apply skipped.
- **Do:** `git tag -f pre-cewilson-port`; take the before-snapshots (the skill's four
  one-liners plus the two optional lists) into `RECONCILE_BEFORE_DIR`; run
  `poetry run python scripts/render_port_dispositions.py` for the range to get the eight class
  lists; run `poetry run python scripts/port_rename_check.py --producer-ref port-base-20260901`
  over the WHOLE tree (drop `--path-prefix`) and disposition every flagged pair
  adopt / decline / false-positive in the commit message — this is the look RELAY-20 asks
  for before D/E/F, and 217 clean-adds are still unexamined.
- **Guard:** `pytest tests/unit/test_port_reconcile_guards.py` green with the snapshot set
  (set-but-broken fails by design, `:450`); the rename check's exit code recorded.
- **Not:** no file changes; this chunk is one commit of records (the class lists, the
  rename dispositions).

### Chunk 2 — Slice F: the SOURCES slice E's tests read

- **Scope:** the per-entry and canonical-producer rows E's new tests depend on, and the
  vendored asset. `external/geo/world-atlas/countries-110m.json` (default_ok, clean-add);
  the config, taxonomy and registry rows behind `web/src/generated/world-*.json`,
  `gates.json`, `enforcement-matrix.json`, `load-map.json`; `drydocs_core/env_refs.py`
  (per-entry: the company's own `DECLARED_VARIABLES` stay).
- **Order:** canonical-producer files by NAME (never `web/src` wholesale — the K7–K15 hold);
  then per-entry with each row's `entry_rule` read first; then the one clean-add.
- **Guard:** `test_port_reconcile_guards.py` (no downgrade, no dropped entry) green; E's
  tests now fail ONLY on missing generated artifacts — anything else is a merge miss, fix it
  here.
- **Not:** no renderer run, no generated file taken.

### Chunk 3 — Slice G: RUN the renderers, then commit slice E

- **Scope:** the `derived` class. `python scripts/render_board.py` (writes `gates.json`,
  `enforcement-matrix.json`, `load-map.json`, `board.html`, `roadmap.html`, `ideas.html`),
  `render_world_map.py`, `render_remediation_profile.py`, `render_env_example.py`
  (`.env.example` is a render of `DECLARED_VARIABLES`, G129), `render_design_doc.py` over
  `docs/design/*.md`.
- **Order:** renderers after every source they read is merged (chunk 2), in one run; then
  E's tests and their subjects land in the same commit.
- **Guard:** the drift guards (`test_render_determinism.py`, `test_gates_json.py`,
  `test_load_map_json.py`, `test_plan_board.py`, `test_env_doctor.py`) green on the COMPANY's
  sources; the +83 either cleared or each residual named as a QuerySpec content difference
  (`test_query_specs`, reconciled here, not ported).
- **Not:** no `git checkout` of anything under `web/src/generated/`, `docs/plan/`,
  `docs/design/*.html` — the manifest now says `derived` for all three.

### Chunk 4 — The remaining classes for this range: clean-adds, evaluates, union-appends

- **Scope:** everything in the class lists not touched by A–G: the clean-add balance (after
  chunk 1's rename dispositions), `evaluate` 29 (hand-merge, an un-made decision until made),
  `union-append` 16 (append, never reorder, never drop yours — `config/gate-log.md` among
  them), `canonical-producer` balance by file list.
- **Order:** the manifest's apply order, class by class, one commit per class if the class
  is large (evaluate will be — 29 decisions, each written down).
- **Guard:** `scripts/port_backlog_union.py --producer-ref port-base-20260901` exit 0 (no
  producer id missing, none doubled); `test_port_reconcile_guards.py` with the snapshot green
  (gate-log append-only, vocabulary no-downgrade — the vocabulary migration is NOT in this
  chunk, so the 44 renames do not appear here); the full Track-1 list green.
- **Not:** the two lineage modules (`writer.py`, `controlm_inventory.py`) — they are chunk
  5's by construction; `config/gate-prompts/**` content (canonical-company: the company's
  DRAFT status and missing signature stay).

### Chunk 5 — T24 (1): the vocabulary migration, config AND code

- **Scope:** 44 id renames + 5 fragment renames + the fold into `52-local-human`, applied as
  the G87 shape (add-new + `deprecated_at` on the old, never a rename of a signed id); then
  the two lineage modules that reference the new ids exclusively. Two corrections from the
  producer's measurement: 44 of 45 carry `deprecated_at: 2026-08-21`, the odd one
  (`seal_requires_scheduler` → `reg_uses_software`, gate C12, 2026-07-21) needs NO data
  migration because its target label was retired at C13; and `migrate_vocab_ids_g101.cypher`
  is an ancestor of `port-base-20260826` — check the tree before pricing it as unsourced.
- **Order:** fragments first (the ids exist), the vocabulary guards green, then the two
  modules in the same commit as their tests (`test_lineage_writer.py`,
  `test_lineage_inventory.py` — J68's paired-declaration rule).
- **Guard:** the vocabulary guards green (`tests/unit/test_schema.py`, `test_yaml_fragments.py`, and the
  42 test files that read the fragments); `test_port_reconcile_guards.py` gate-bound activations green — every
  activation cites its signing gate, and the company's is the company's gate, not the
  producer's; zero dangling vocabulary references (grep the two modules against the merged
  fragment ids — the producer verified 5 and 3 referencing lines, zero old refs).
- **Not:** do not run the migration cypher. It becomes a no-op at chunk 8.

### Chunk 6 — T22 / DD6: the CLI seam the reload needs

- **Scope:** `_client(database)` on the company's `cli.py` (the latent crash in
  `patch_window_cmd` closes with it); wire the two deferred verbs `docs-verify` (Q7) and
  `bootstrap-schema-graph` (targets `ddschema`); the `ddschema` provisioning DDL (the G51
  twin). Modules are already ported; only the thin wrappers wait.
- **Order:** the root `_client` first, the verbs second, the DDL third — each importable
  after its step (`python -c "import drydocs.cli"`; the eight-entrypoint import-order guard
  `test_cli_import_order.py` if the S8 split is taken; the D-slice merge kept `cli.py`
  surgical, so this is verbs, not a refactor — Idea-241's reading).
- **Guard:** `drydocs --help` lists both verbs (the guard reads `app.registered_commands`,
  J37); `test_cli_import_order.py` green; the `docs-verify` table runs against the empty
  target and reports zero rather than crashing.
- **Not:** no graph write. `bootstrap-schema-graph` is wired here and RUN in chunk 8.

### Chunk 7 — Bootstrap audit and the wipe (schema and data together)

- **Scope:** the pre-reload state check and the wipe, on both databases.
- **Do, in this order:** `drydocs bootstrap` and READ the live-but-undeclared constraints
  report (expect `membership_id` on `:Membership`; anything else is a company-side residue
  to record); then `DROP DATABASE` for `drydocs` and for `ddschema` — not `MATCH (n) DETACH
  DELETE n`, which keeps every constraint; re-provision (`drydocs_core/schema/provisioning/`
  is manual by design); `drydocs bootstrap` again; assert live == declared (56 / 56 on the
  producer desktop at G130; the company's number is the company's).
- **Guard:** the undeclared report empty after the drop; `drydocs check` clean;
  `test_bootstrap_guard.py` green.
- **Not:** no load. And note what the drop DISCHARGES: T23's S3 re-key on live state (a
  fresh graph has no pre-cutover nodes; `port_app_key` is created by the declared schema)
  and the SF1/F1 edge migration (the reload writes the current edges natively). What it
  does NOT discharge: C17's orphan count, which is read from chunk 8's first run.

### Chunk 8 — The reload, under the new vocabulary

- **Scope:** the load chains in their declared order (`cli.CHAINS`), with S10's guards in
  place on all five MERGE sites; `bootstrap-schema-graph` into `ddschema`.
- **Order:** the chain resolver (`drydocs/chain_inputs.py`, G78) resolves every input BEFORE
  the first write — run it, read its report, then load. Read the C17 orphan count from the
  first run's :JobRun before the every-run `orphan` flag is switched on.
- **Guard:** the `drydocs/graph_verify.py` runner over the `graph-tests/` TC suites (Epic H) green; `code-graph-freshness`
  FRESH after `load-code-snapshot`; `docs-verify` reconciles declared vs loaded; the
  `migrate_vocab_ids_g101.cypher` precondition query returns zero rows (the no-op proof).
- **Not:** no re-key cypher, no edge migration cypher — chunk 7 made them unnecessary; if
  either finds work to do, the wipe was a data-only wipe and chunk 7 is re-run.

### Chunk 9 — Report, provenance, close-out

- **Scope:** the PORT-REPORT for `port-base-20260901` on the skill's template; the Tier-A
  `RATIFICATION (... adopted-via-port)` entry in the company's `config/gate-log.md`; the
  provenance check before any gate is reported RATIFIED
  (`git log --oneline -S "<distinctive phrase>" -- config/gate-log.md` — a port commit
  means NOT ratified); the T-row statuses the company's ledger owns (T22 closed, T23 closed
  by construction with the chunk-7 note, T24 (1) closed, (2) already closed); `git tag`
  the applied base.
- **Guard:** `scripts/port_backlog_union.py` exit 0; `test_port_reconcile_guards.py` with the
  chunk-1 snapshot green end to end; the full suite green at the company's own count.
- **Not:** nothing sent back. The producer reads the next roll's diff, not a reply.

### Chunk 10 — The next roll (producer-side prerequisites, then the company's chunk 1 again)

- **Producer, before rolling:** (a) mint **PLAN3 = FROZEN_BAND** (`{"G": 10003, "DD": 10003}`
  in `validate.py` and `test_backlog.py` with the agreement guard) — the trigger in Idea-242
  has fired because PLAN1 is already past the base; (b) make DOC2's freeze half depend on
  PLAN3 and drop the table from PLAN2 (c); (c) land P3/P4/P6 from Part A so the git layer
  and the seven consumer-only tests are green here before the company runs them; (d) roll
  the ledger (`chore(port): roll`) with the freeze relay — "your three band ids are read and
  listed, not re-minted; mint nothing until `edition:` exists" — which is DOC2's text.
- **Company, on arrival:** chunk 1 again on the new range; PLAN1's guards will name the six
  band ids and FROZEN_BAND will pass them; the J72 detector arrives as payload rather than
  as dossier 4.

## B3. Sequencing, in one line

```
1 prep/snapshot/look  →  2 F sources  →  3 G renders + E  →  4 remaining classes
→  5 vocabulary (config, then the two lineage modules)  →  6 DD6 CLI seam
→  7 bootstrap audit + DROP DATABASE x2 + re-provision  →  8 reload + C17 count
→  9 report + provenance  →  10 next roll (PLAN3 first, producer-side)
```

Chunks 2–4 are the range. Chunks 5–8 are the deferred work and the order the SME ruled
counter-intuitive: renames BEFORE the wipe. Chunk 6 sits between 5 and 7 because the reload
needs the seam and the seam needs no graph. Nothing in 5–8 starts before 4's union check
exits 0.

## B4. Where the chunks would fail, and which guard catches it

| Failure | Chunk | Guard |
|---|---|---|
| A clean-add that is a renamed file the company already holds | 1 | `port_rename_check.py` exit 1 names the pair |
| A wholesale take that drops company-only rows | 2, 4 | reconcile guards: dropped entry / no downgrade (`:292`, `:240`) |
| A carried render describing the producer's estate | 3 | drift guards pass on the wrong sources — the ONLY silent one; rule 2 is the defense, and the manifest's `derived` row now names it |
| The two lineage modules taken before the vocabulary | 4 | the vocabulary guards (dangling ids) — which is why they are chunk 5's by name |
| The migration cypher run "to be safe" after the reload | 8 | its precondition query returns zero rows; running it is harmless but proves the order was wrong |
| A data-only wipe | 7 | `drydocs bootstrap` undeclared report non-empty after the wipe |
| A gate reported RATIFIED from a ported entry | 9 | the pickaxe provenance check |
| PLAN1 arriving without FROZEN_BAND | 10 | `test_frozen_series_take_no_new_ids` red on six ids — the reason PLAN3 is minted first |
