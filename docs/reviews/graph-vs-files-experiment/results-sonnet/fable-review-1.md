# Fable review 1 — ALPHA vs BETA groom plans (Ideas 96–103), blind

Reviewed blind against working tree `main` @ `a5319a3` (2026-08-11). All verification
read-only; no repo edits beyond this file, no commits, no git-mutating commands. The
second live session's in-flight work (`drydocs_remediation/`, `drydocs_lineage/`) was
not touched.

## Scores

| Dimension | ALPHA | BETA |
|---|---|---|
| Accuracy | **6** | **9** |
| Completeness | **5** | **9** |
| Sizing quality | **6** | **9** |
| Convention fidelity | **7** | **9** |
| Compliance | **VALID** | **VALID** |

One-sentence justifications:

- **ALPHA Accuracy 6** — every structural claim I spot-checked verified exactly (some
  impressively so), but the Idea-99 disposition is a material factual error: the relay
  it promotes as owed already exists in the tree, and the plan had the file in hand
  without reading it.
- **ALPHA Completeness 5** — all eight ideas dispositioned, but every drafted item is
  missing three of the twelve fields `tests/unit/test_backlog.py` `REQUIRED_FIELDS`
  enforces (`title`, `type`, `status`), so none is paste-ready.
- **ALPHA Sizing 6** — sizes are grounded in real graph fan-in/fan-out numbers and the
  limits are honestly flagged, but structural coupling is a weak proxy for new-mechanism
  effort (Idea-96 called S when the work is a genuinely new two-tree diff; Idea-98
  called M against a gate spec it never opened), and one sizing (J44 S/M) rests on an
  admitted un-run query.
- **ALPHA Convention 7** — ids all correctly next-free in their series (J42–J45, C31,
  U20, G68 vs maxima J41/C30/U19/G67), epics/modules/phases match siblings exactly
  (C31 mirrors C25's ontology-mapping/ontology/2), but the uniform main/sonnet
  assignment is uncalibrated and the missing schema fields bleed into convention.
- **BETA Accuracy 9** — all three spot-checks verified to the cited line number,
  including the decisive RELAY-5 finding; only trivial slips (a line count of 46 vs 45,
  a hit count of 9 vs ~12 matching lines, one "Idea-98" typo where Idea-99 was meant).
- **BETA Completeness 9** — 8/8 dispositioned, every draft carries all twelve required
  fields plus `inputs`/`notes`, `depends_on` targets exist (C25 signed, K21 real), and
  the one file named-but-not-read (`test_code_graph_review_plan.py`) is flagged as such.
- **BETA Sizing 9** — every S/M/L is tied to named, opened files (the 63-line
  `scripts/port_preflight.py` read behind the M; the gate spec's §C3 parsing routine and
  five-plus touched files behind the L; a one-line fence close behind the S), with model
  tier matched to size (haiku for the fence fix, fable for the judgment-heavy K22).
- **BETA Convention 9** — id allocation computed from a full series scan and correct;
  epic/module/phase follow the named siblings (J41, U18, K21); model tiering matches
  the repo's actual distribution (sonnet/fable/haiku all in live use); acceptance
  sentences are testable and carry the J26 injected-defect discipline.

## Spot-checks — ALPHA (3)

**A1. `tests/unit/test_port_reconcile_guards.py` exists and imports exactly
`drydocs_core/__init__.py` + `drydocs_core/yaml_fragments.py` — VERIFIED.**
The file exists; line 49 reads `from drydocs_core import yaml_fragments`, which is
precisely the two-module import surface the plan's graph query reported (the package
`__init__` plus the fragment helper). No other project-internal imports.

**A2. `drydocs/loaders/manual_loads.py` fan-in 5 / fan-out 6 — VERIFIED, and
non-trivially.** Fan-in: grep for `manual_loads` matches six files, but the sixth
(`tests/unit/test_provenance_migration.py`) references the file by *path* in a
`read_text` call (line 50), not an import — so the graph's five importers
(`drydocs/cli.py` + 4 test files) is exactly right where a naive grep over-counts.
Fan-out: the six imports include two *function-local* ones —
`drydocs_core.mapping_store` at line 65 and `.folder_attribution` at line 120 — which
the graph caught. This is the strongest single verification in either plan.

**A3. `scripts/port_preflight.py` is a thin importer of `drydocs/port_preflight.py`
— VERIFIED.** Line 21: `from drydocs.port_preflight import REPO_ROOT, next_base_tag,
run_checks`. The plan's "one IMPORTS query answered it" claim holds. (Bonus checks
that also verified: the `test_markdown_fences.py` docstring quote is verbatim at
lines 19–22; the trailing fence in `SDLC-Docs/extracted/issue-driven-capture-loop.md`
reports `(181, 3)` when run through the guard's own parser; U18 sits at backlog.yaml
line 15480, matching the plan's "offset ~15480".)

**ALPHA's material error (found during verification, counted against Accuracy):**
Idea-99's draft J43 acceptance — "`docs/port-prompt.md` gains a relay line naming the
`dpl` and `snowflake` product rows, the `in-house` vendor row, and the `DPL` acronym"
— is *already satisfied*. `docs/port-prompt.md` line 743 carries **RELAY-5 (was R5) —
DPL + Snowflake registry entries**, naming all of those, dated "new 2026-08-09, gate
`software-version-context` / C25", with a company-side correction stamped 2026-08-09 pm
at PORT-REPORT-6f03264 ruling it a clean add; RELAY-4 at line 732 is struck through,
so even the idea's "striking R4" rider is done. The idea's own precondition ("add it
once that port merges") had resolved, and the plan confirmed the file's *node* existed
in the graph without ever reading its *content*. Promoting J43 would hand the SME a
no-op item.

## Spot-checks — BETA (3)

**B1. `docs/reviews/code-graph-review-plan.md` line 64 says eight roots, lines 181–184
still say six with stale counts — VERIFIED to the line.** Line ~64: "Metrics scoped to
`$packages` (U14; **eight roots since U18, 2026-08-09**)". Line 181: "Six scan roots ×
DesignDoc coverage … (baseline: tests 85, drydocs 41, drydocs_core 35, lineage 12,
remediation 7, deepdoc 3)". Every count matches the plan's citation exactly. The
mismatch Idea-97 alleges is independently confirmed, not just trusted.

**B2. `config/gate-prompts/software-version-context.yaml` is signed-off, §B2 keys on
`{source, install_path}`, §Q3 is deferred with its consequence stated — VERIFIED.**
`status: signed-off` at line 237; B2 confirmation text "MERGE KEY is {source,
install_path} — NOT {source}, and NOT {source, version}" at ~line 135; "Q3 DEFERRED
with its consequence stated: … identity moves to (fid, version) - a re-key" at lines
~228–231. The plan's claim that §Q3-before-MERGE-key is a real precondition, not idea
color, is grounded.

**B3. RELAY-5 already satisfies Idea-99, including the dating and the Idea-100
cross-reference — VERIFIED.** The block at lines 743–~804 carries the `dpl` row
(`vendor: in-house`, `type: internal`, `role: tool`), the `snowflake` row
(`role: data-platform`), the `in-house` vendor with no `publisher_url`, the
`DPL: "Data Pipeline Library"` acronym, the publisher-url rider, and — at lines
785–786 — "A DEFECT IN THAT GUARD WAS FOUND AND FIXED … it is the Idea-100 class",
exactly as the plan quoted. The merge→satisfied disposition is the single most
consequential correct call in either plan. (Bonus: `drydocs/loaders/software_registry.py`
exists; `config/gate-log.md`, both `knowledge/upgrade-plans/servicenow-*.md` files,
and `.claude/skills/reconcile-port/SKILL.md` all exist; the max-id scan C30/J41/K21/U19
matches my independent scan.)

## Compliance — VALID / INVALID

**The judgment call, reasoned out loud.** RULE SET 1 forbids Grep but says the two task
inputs "may be read directly." ALPHA's metrics show seven Grep calls, every one scoped
to `IDEAS.md` or `backlog.yaml` — the exempt files — and no Glob, no directory listing,
no tree-wide search of any kind. I read a *scoped* Grep against an exempt file as
permitted reading, not forbidden search, for two reasons. First, mechanism: a Grep
pinned to one named file can only surface content that a licensed full `Read` of that
same file would surface — it discovers no *paths*, no *files*, nothing outside the
exemption; it is an indexed read, not a sweep. Second, purpose: the rule's forbidden
list (Glob, Grep, listings, `git grep`, "any tree sweep") is plainly aimed at
*discovery of code context outside the graph*, and grepping inside a ~16,000-line
backlog file you are entitled to read end-to-end serves reading efficiency, not
discovery. The contrary strict-literal reading ("Forbidden: Grep", full stop) is
defensible, and under it ALPHA would flip to INVALID — but I find it the weaker
reading because it would make the exemption self-defeating (licensed to read a 16k-line
file, forbidden to find anything in it). Ruling on my stated reading:

- **ALPHA: VALID.** files_read: 4 — two exempt task inputs plus two files whose paths
  Idea-103's own text names (verified: IDEAS.md lines 119 and 125 name
  `tests/unit/test_markdown_fences.py` and `SDLC-Docs/extracted/issue-driven-capture-loop.md`),
  which the rule's "named by the task input" clause licenses. All searches are either
  Cypher or exempt-file-scoped Grep. No forbidden discovery.
- **BETA: VALID.** The metrics block shows Read/Grep/Glob only — no Neo4j, no Cypher,
  no graph access anywhere. Clean under RULE SET 2.

## Which plan goes to the SME

**BETA, without hesitation.** The groom's product is a set of decisions and paste-ready
items, and BETA is better at both ends of that: its drafts are schema-complete YAML
blocks that would pass `test_backlog.py`'s twelve required fields as written, and it
got right the one call that actually changes what lands in front of the SME — Idea-99
is already satisfied by RELAY-5, which BETA proved by reading the named file and ALPHA
missed by confirming the file's existence without opening it, drafting a no-op item
with an already-true acceptance test. BETA's sizes are also the ones I would trust to
schedule against, because each is anchored in an opened file (the gate spec's §C3
routine behind the L, the 63-line preflight script behind the M) rather than in
structural coupling counts. What ALPHA has that BETA lacks is worth naming: its
dependency-structure claims were the most precisely verified statements in either
document (the function-local imports in `manual_loads.py`, the path-reference-vs-import
distinction a grep would blur), and its epistemic honesty about what it could not see
is exemplary — but honest uncertainty plus one confident wrong disposition is a worse
SME hand-off than BETA's quiet, line-cited correctness. If the two were merged, ALPHA's
fan-in/fan-out evidence would strengthen BETA's C31 and J42 write-ups; as submitted,
BETA is the plan to hand over.
