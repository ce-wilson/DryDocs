# IDEAS — the idea board (inbox)

Low-friction capture. Jot anything here from any surface — a "what if", a bug you spotted,
a doc that needs writing, a future source to ingest. **No schema required.** Messy is fine.

This is the **inbox**, not the backlog. Nothing here is committed to until it is *groomed*
into an item file under [`backlog/`](backlog/) (`items/<id>.yaml`; the old `backlog.yaml` is a
tombstone) with an id, owner agent, inputs, and an acceptance test.

## How this feeds the backlog

```
capture here (any surface)  ──groom──▶  backlog/items/<id>.yaml  ──▶  agent pulls it
```

**Grooming ritual** (you, or an Opus `main` session, ~weekly): read this list top to bottom;
for each idea either (a) promote it to a backlog item file (`backlog/items/<id>.yaml`), (b) merge it into an existing
item, or (c) drop it. Strike through or delete what's been groomed so the inbox stays short.

## Capture format (loose)

`- [tag] one line. (optional: why / where you saw it)`

Tags help grooming: `idea` · `bug` · `doc` · `source` (new data source) · `question` · `chore`.

### Entry header (added 2026-08-05, user direction — the inbox needed identity, state and priority)

Every inbox entry carries a one-line header, then its body:

```
- **`Idea-N`** · 2026-07-22 · `[idea]` · **open** · prio? **Med** —
  <the entry text>
```

The header and the body render as ONE line (the Epic L markdown renderer has no hard
break), which is why the header ends in `—`: it reads as a prefix, the same shape the
file already used (`2026-08-05 — [bug] **Title**`), just carrying identity and state.

| Field | Rule |
|---|---|
| **id** | `Idea-<n>`, assigned in CAPTURE order — oldest is `Idea-1`. Ids are **stable references**: never renumber, never reuse. **Ask the allocator for the next one** (I6): `python .claude/skills/groom-backlog/validate.py --next-id Idea` — it reads this file, every remote ref's copy of it, and every revision in history, because a branch that appended an entry is invisible to a local read. New entries still go at the TOP; position is chronology, the id is identity. **This side allocates 1–9999** — see the allocator bands below. |
| **split** | A big entry whose parts have DIFFERENT dispositions splits into `Idea-Na`, `Idea-Nb`, … Split only when the parts would carry different **status or priority or target item** — not merely because an entry is long. |
| **date** | Capture date. Unchanged by later edits; a later finding is a `KEPT-UPDATED <date>` line in the body. |
| **tag** | `idea` · `bug` · `doc` · `source` · `question` · `chore` — as before. |
| **status** | `open` (needs a decision or a groom) · `parked → <trigger>` (deliberately waiting on a NAMED trigger) · `groomed → <ids>` (produced backlog items) · `merged → <id>` (folded into an existing item's acceptance or notes) · `closed` (resolved, kept for the record). |
| **prio** | **the user's** call: `High` · `Med` · `Low` · `Deferred`. Written `prio?` while the value is **proposed by the agent and not yet confirmed**; written `prio` once the user has ruled it. Confirming is a one-character delete, which is the point. |

### Allocator bands — which side minted this id (added 2026-08-18)

**Producer allocates `1–9999`. Company allocates `10000+`.** Same rule in every series — here and
in the backlog's letter series (`backlog/items/<id>.yaml`). The grammar does not change, so `Idea-10012` and `G10604` parse
with every existing regex and no historical id moves.

**Read it by length:** *five digits or more → company; four or fewer → producer.* There is no
boundary number to remember, which is the point — `G604` and `G60` differ by one glyph and sit in
the same visual class, while `G10604` cannot be mistaken for anything producer-side.

**Why the bands exist.** Three allocators mint from one counter with no lock — producer-desktop,
producer-laptop, company. Git serializes the first two only *after* both have pushed, which is
exactly when it is too late, and never serializes the third. This file is `union-append` at port
time (`PORT-MANIFEST.yaml`), so two sides' entries merge and a shared number becomes two different
ideas. It has already happened at every level: `backlog.yaml` carried **two different G70 and two
different G71** after a concurrent push, and the desktop pair had to be renumbered to G75/G76
because `config/gate-log.md` cited G73/G74 inside a SIGNED-OFF record and *a sign-off citation must
not be falsified to settle a numbering clash* (`docs/port-prompt.md`). `PORT-MANIFEST.yaml` records
the same hazard for `backlog.yaml` ("both sides run their own plan against OVERLAPPING ids") and
again for ADRs ("both sides may hold the same ADR number for different decisions").

**Forward-only.** The bands govern the NEXT id each side allocates; nothing historical is
renumbered, because ids are join keys and renaming one in place re-points every citation of it
(the G87 ruling). So a low number means "allocated before the partition", NOT "producer" — that
residual ambiguity is frozen on the day this rule landed and shrinks in relevance from there.

Enforced by `tests/unit/test_plan_ideas.py::test_new_idea_ids_stay_in_this_sides_band` and the
matching backlog guard. The grandfather line is a committed constant, never "the current max" —
a computed floor rises with every new id and silently re-legalizes the band.

**Why `merged` exists, and why it is the most useful status.** Most inbox entries are not
new work — they are a fact that belongs INSIDE work already scheduled. Filing those as new
items inflates the backlog and splits one change across two owners; leaving them in the inbox
loses them. `merged → C25` says the finding now rides that item's acceptance, so whoever
picks it up gets the finding for free.

**Why marked rather than moved.** The groom ritual says a groomed line moves to the audit
trail at the bottom of this file. That works when an entry maps 1:1 to an item. It does not
when one entry carries several findings and only part of it is actionable — moving the whole
line files the open findings under "recently groomed", where nobody looks for open work.
So: **fully consumed → move to the audit trail; partially consumed → mark in place and say
what stays open.** Either way the inbox itself answers "was this groomed?", which is the
question a 1,000-line file with the trail at the bottom could not answer.

## Inbox

- **`Idea-241`** · 2026-09-02 · `[idea]` · **open** · prio? **High** —
  **The S8 composition root should DISCOVER a consumer command module by convention, so
  `drydocs/cli.py` stops being an `evaluate` collision — the company never adopted the split
  and its monolith carries stale inline copies of every verb S8 moved.** Source: the
  company's PORT-REPORT for `port-base-20260826..20260901`, defect 6 (2026-09-02, relayed
  session record): `test_env_doctor::test_the_command_is_registered` failed at their G slice
  because `env-doctor` is defined in `drydocs/cli_schema.py` — byte-identical to producer,
  taken in D — and **nothing imports it**. Their `drydocs/cli.py` is a **4,079-line pre-S8
  monolith with zero references to any `cli_*` module** (4,112 after D's one hunk); the six
  per-domain modules sit beside it unwired. Attribution checked, not assumed: the orphaning
  predates the port — it was already so at their base `294b9cec`.
  **MEASURED HERE (J63: `main`, `port-base-20260901`).** Producer `cli.py` is 669 lines and
  registers 51 commands (`app.registered_commands`, J37); the six `cli_*.py` modules total
  4,017 lines. The S8 split landed **2026-08-21** (`f5e7229d`, 3,184 lines → thin root + six
  modules) and S13 hoisted shared state on 08-27 (`5ab0c1d2`) — so `cli.py` was 1,356 lines at
  `port-base-20260826` and 669 at `20260901`. **S8 was in the PREVIOUS port's range.** A
  prior port already faced the split and did not adopt it.
  **WHY — a manifest row that cannot express a refactor.** `drydocs/cli.py` is `evaluate`
  with the note *"composition root; both sides add commands — merge per collision ledger
  (keep consumer verbs, add producer verbs)"* (`PORT-MANIFEST.yaml:870`). That rule is
  correct for VERB ADDITIONS and wrong for a STRUCTURAL change: followed literally it merges
  producer verbs INTO the monolith, so the monolith grows every port (3,184 → 4,079 → 4,112)
  and the split never arrives. Worse than one missing verb: every verb S8 moved into a
  module and that has CHANGED since — G79's `refresh-reference` split into three subject
  commands, `verify-reference`/`verify-controlm` with the m1/m3 deprecated aliases — exists
  company-side only as a **stale inline copy from before the split**. Their 67 registered
  commands include those copies. `env-doctor` is the first one a guard caught, not the only
  one that is wrong.
  **TWO CHANGES, one theirs and one ours.**
  THEIRS (the port action, raised in their report as "owed, for a ruling") — adopt the split:
  take the 669-line root wholesale; move the company-only verbs (their count: 26) into a
  company-owned `drydocs/cli_company.py` (or per-domain) with its `MODULE_MAP.md` row in the
  same commit (`load` group; the S13 subprocess-per-import guard covers it for free); DROP,
  not move, every inline verb whose name is in producer's `registered_commands` — the module
  version is current, the inline one is stale (name-set diff, read the importable object on
  both sides); add `cli_company` to `COMMAND_MODULES` at `cli.py:663`.
  OURS (this idea) — remove the residual collision permanently. After adoption the only
  company edit to `cli.py` is one tuple element. Replace it with DISCOVERY: the composition
  root imports `drydocs.cli_local` (name to be settled; one name, documented in
  `MODULE_MAP.md`) **if and only if `importlib.util.find_spec` finds it**, and registers its
  verbs after `COMMAND_MODULES`. Producer ships no such module; the company owns one; the
  manifest row for `drydocs/cli.py` can then move from `evaluate` to `canonical-producer`,
  because both sides never again edit the same file. Guards: `test_cli_import_order.py` gains
  the optional module (subprocess-per-import — an in-process import proves nothing about
  order, S13); `test_cli_registry.py` asserts a fixture `cli_local` registers and a missing
  one is silent; `test_module_boundary.py` classifies the name (default-deny). The
  composition-root-plus-discovered-extension shape is ADR 0002-A's — core imports nothing
  from a component; a consumer module is the outermost layer and may import anything.
  **THE GENERAL LESSON, for the J68/J69 machinery:** `evaluate` notes say how to merge
  CONTENT. None of them can say "the producer changed the SHAPE of this file — take the
  shape, re-home your content." A structural refactor of an `evaluate` path needs its own
  RELAY at the roll that carries it, naming the new shape and where consumer content goes;
  S8 shipped without one, and two ports walked past it. Candidate rule for
  `docs/port/port-prompt.md`: a commit whose subject starts `refactor(` and touches an
  `evaluate` path is a mandatory relay. Related: S8, S13, ADR 0002-A, J68, J69, [[Idea-239]]
  (same report, same day), [[Idea-240]].

- **`Idea-240`** · 2026-09-02 · `[idea]` · **open** · prio? **Med** —
  **The publish boundary is defined on the tracked tree and says nothing about git HISTORY —
  34 commit messages on main carry the retired org acronym, and whether the public push is
  tip-only or carries history is undocumented.** Source: the company's own flag during the
  D/F apply (2026-09-02, relayed session record) — a commit TITLE on their `main` carries the
  retired token, and their `git rm --cached` of the deepdoc scrape removed the blob from the
  tip while it stays reachable in history; they named it *a history-rewrite decision, not a
  tip-level one*, and left it to the SME. The same decision exists here and has never been
  written down. **Measured producer-side:** `git log main --grep` for the retired token (read
  from `internal/cdo-reference/README.md`, the guard's own mapping file, never spelled here)
  matches **34 of 1,816** commits on `main`. `tests/unit/
  test_publish_boundary_retired_org_acronym.py` (J55) scopes history OUT deliberately — its
  docstring cites commit `3c2bfcdd` naming history as an *expected transient survivor* — and
  that is the right scope for a tree guard. But `PUBLISH-BOUNDARY.md` defines the boundary
  as *the git-tracked working tree outside `internal/`* and does not contain the word
  "history," so the document that governs the public push is silent on the one thing a
  public push carries that a tree guard cannot see. This repo has a public twin
  ([[project-public-side-publish-boundary]]), so the question is live, not hypothetical.
  **THE RULING NEEDED, one of three:** (a) the public push is TIP-ONLY (squash or orphan
  commit) — history never leaves, and `PUBLISH-BOUNDARY.md` says so in one sentence; (b) the
  public push carries history and the 34 messages are ACCEPTED (the acronym in a commit
  subject identifies an org unit, not a person, host or credential — arguably below the
  §3 line) — recorded as an allowlisted class with the count and the reason; (c) history is
  rewritten (`filter-repo` on messages only) — the option the company named, and the one
  that breaks every `reviewed_commit` stamp, gate-log sha, port-base tag and PORT-REPORT
  pin in the repo, so it is listed to be REJECTED with the reason, not to be chosen.
  Recommendation is (a) if the publish mechanism already is tip-only (verify against the
  public twin's `git rev-list --count`), otherwise (b). **Either way the mechanism gains one
  test:** a guard that reads `git log --format=%s%b` for the retired token and asserts the
  count against the recorded ceiling (34 today) — a NEW occurrence in a commit message is
  the leak J55 cannot see, and it is the failure the company just had. Not a sweep; a
  ceiling. Related: J55, J23, [[Idea-239]] (same day, same port).

- **`Idea-239`** · 2026-09-02 · `[idea]` · **open** · prio? **Med** —
  **A config surface, its renderer's SURFACES row and the derived artifact it feeds are ONE
  coupling — a port slice carries all three or none, and the manifest should name the triple
  the way J68 names declaration/guard pairs.** Source: the company's D-slice apply of
  `port-base-20260826..20260901` (2026-09-02; relayed session record, `port-updat-d-10..13`
  transcribed in the relay's reading, not cited as images). What happened, in order:
  `config/source-bindings.yaml` (G125) had reached the company in an earlier slice WITHOUT the
  matching row in `scripts/render_enforcement_matrix.py` `SURFACES`; producer's guard
  `tests/unit/test_enforcement_matrix.py` asserts every top-level `config/` entry is in
  `SURFACES` or `CONFIG_EXEMPT`, so on OUR tree the pair can never separate — but a port slice
  is not a tree, and the guard only fires after the take. `render_board.py` then exited 1, so
  `enforcement-matrix.json` and `load-map.json` could not be regenerated; the freshly applied
  `web/src/generated/**` → `derived` manifest row (febdf3ba) says *regenerate, never carry*;
  and the J55 acronym guard failed on the stale carried copies. **A row we wrote to stop a
  file being carried made the file unproducible instead**, because its inputs had crossed in
  different slices. Clearing it exposed a SECOND stacked failure (`render_software_registry.py`
  on `datetime.date`, fixed producer-side at O68 `6b43c850`, inside this range, not yet
  applied) that the first had hidden. The company's own words: *the same dependency-closure
  failure a fourth time, in a new place: renders → renderers → config surfaces.*
  **WHY THE EXISTING MACHINERY DOES NOT COVER IT.** J68's `DECLARATION_GUARD_PAIRS` names
  two-way couplings whose members must share a DISPOSITION. This is a three-way coupling
  whose members legitimately hold DIFFERENT dispositions — the config file is `per-entry`
  (company rows stay), the renderer is `canonical-producer`, the artifact is `derived` — and
  the invariant is not "same disposition" but "same SLICE": if any one crosses, the other two
  must be applied (or regenerated) in the same apply, and the `derived` member must be
  regenerated LAST, after both inputs. The APPLY BY DISPOSITION section already orders
  `derived` last; what it lacks is the statement that `derived`'s inputs are a closure, and
  which files are in it.
  **THE PROPOSAL, smallest form.** (1) A `closure:` field on each `derived` manifest row
  naming its renderer(s) and the config surfaces they read — for `web/src/generated/**` that
  is `scripts/render_board.py`, `render_enforcement_matrix.py`, `render_software_registry.py`,
  `render_load_map.py` and every `config/*.yaml` in `SURFACES`; (2) a guard in
  `test_port_manifest.py` that the closure is TOTAL against the importable object (J37: read
  `SURFACES`, never the render) — a config file registered in `SURFACES` but absent from the
  closure fails; (3) `scripts/render_port_dispositions.py` prints the closure under each
  `derived` row so the apply sees "regenerate this — which needs THESE applied first" instead
  of a bare "regenerate." Nothing in the port-prompt's ledger changes; this is manifest
  structure and a guard, the J68 pattern. **What it is NOT:** a reason to allowlist a carried
  artifact — the company considered that and rejected it, correctly: it would have shipped a
  `derived` row for files that could not be produced.
  **A NOTE ON COUNT.** "Fourth time" is the company's tally and it is the right one to keep:
  `dev-environment.yaml` by omission (2026-07-28), `source-registry.yaml` (J68),
  `source-bindings.yaml` missing from the 08-30 slice (found 2026-09-01), and now the
  closure behind it. Each was fixed at the file; this is the first framing at the shape.
  Related: J68, J71, J72, G125, O68, N4/N5 (the load-map surfaces), [[Idea-235]].

- **`Idea-238`** · 2026-09-02 · `[idea]` · **open** · prio? **Med** —
  **Load the mind-map research logs into a throwaway Neo4j database (`mindmap`), apply the
  current ontology, and run the Knowledge-Graph-of-Thoughts retry loop over it — to see how a
  mind map traverses.** User ask, 2026-09-02 (laptop session, branch
  `feat/mm-deepdoc-investigate`): "ingest all of the research-mindmap files, test loading into
  a new Neo4j db `mindmap`, applying the current ontology, and the retry logic of knowledge
  graphs of thoughts, just to see how it can be traversed." An experiment, not a feature.
  - **THE SOURCE FAMILY.** `internal/research/<SUBJECT>-MM-research.md` — one so far, the
    JOB→MFTS log (`internal/research/JOB-MFTS-MM-research.md`, 2,183 lines, transcribed
    producer-side 2026-09-02 from its company venue; Idea-236 files its five gaps). It is
    already graph-shaped prose: YAML front matter (`central_question`, `subject`, `venue`),
    a **Brain-map** section (the tree), a **Trace ledger** of ~120 hops (H-n), **CORRECTION**
    blocks that retract earlier hops, **Gotchas** (G-n), **Predictions** resolved against
    evidence, **Open questions** (OQ-n, the SME's to rule), **Acronyms & terms**, and a dated
    **Notes log**. The sibling family is the deepdoc session's eight `*-capture.md`
    transcripts (machine-local, never tracked). Both are `classification: Internal` — the
    loaded graph carries real values, so the database lives only on a machine that has
    `internal/`, is never published, and every claim about it names its venue (J18).
  - **"NEW DB" — read it the KGoT way or it fights the fold.** G102 (2026-08-18) folded the
    content topology to ONE database, `drydocs`, with `:Uncertain` as the boundary; ADR 0011
    is the contingency; `test_database_names.py` pins the deployed names. A fourth content
    database reopens that ruling. What does NOT: KGoT's own pattern — a **task-scoped,
    throwaway graph per question** (`reference/research/knowledge-graph-of-thoughts.md`,
    the iterative controller). So `mindmap` is a scratch database created for the run and
    dropped after, the way KGoT builds one per task — a test bench, never a home. If the
    experiment shows the graph is worth KEEPING, that is a gate question (which labels,
    which database), not a default.
  - **"APPLY THE CURRENT ONTOLOGY."** The relationship-vocabulary registry
    (`drydocs_core/ontology/relationship_vocabulary/`, per-domain fragments) plus what MM
    has already registered `planned` — MM2's `:DataFlow` edges (`arch_has_data_flow`,
    `arch_orchestrates`, `arch_fed_by`, `arch_lands_in`, `docs_evidenced_by`). The log's
    sections map onto things the epic already has names for: hops → `ContextFinding`-shaped
    rows (subject / predicate / object / evidence breadcrumb / `phase: build|run`);
    CORRECTION blocks → retractions with an `as_of` (a KGoT graph edit, and the temporal
    axis C40 wants); Open questions → **open slots** in the MM3 state file
    (`drydocs.deepdoc.mindmap.v1`); the Brain-map → its branches; Acronyms & terms → MM12's
    candidate class; the MM3 entity extractor pulls the ids out of every hop. Every write
    is corpus-derived, so it carries `:Uncertain` + reliability/trust (ADR 0011 clause 1)
    even in a scratch database — the discipline is cheap and the guards
    (`test_uncertain_boundary.py`) only watch `drydocs_deepdoc`, so a scratch writer under
    `scripts/` or `internal-local/` must carry it by choice, and say so.
  - **"THE RETRY LOGIC OF KNOWLEDGE GRAPHS OF THOUGHTS."** As the reference file maps it onto
    ADR 0007: bounded escalation INTO an iterative loop (Tier 2, reached only when Tier-1
    context is insufficient), the **fix-Cypher repair loop capped at ≤2 retries**, the
    **forced-solve fallback** so a stalled loop still returns something inspectable, and
    **per-iteration snapshots** (rendered by the console's `TaskGraphPane`). The experiment:
    seed the loop with the log's own `central_question`, let it traverse the `mindmap`
    graph, and record — hops taken vs the ~120 the analyst took by hand, which retries
    fired and why, whether forced-solve was reached, what each iteration's snapshot shows,
    and whether the traversal arrives at the same "understanding" section the log states
    plainly. That is the whole question: **can the loop walk a mind map, and where does it
    stall.**
  - **WHERE IT SITS.** Downstream of MM3 (done: the state file and the extractor are the
    parse target and the parser); a live rehearsal for MM6 (ontology proposals — the
    experiment will surface which labels the log needs) and MM10 (`investigate()` v1 is
    this loop made procedural, graph-seeded); adjacent to R16 (named agent verbs over the
    reviewed QuerySpecs — the loop's tools) and L28 (the KGoT citation). Module for a groom:
    `drydocs-deepdoc` for the parse and the state-file writer; the scratch-database loader
    and the loop harness under `scripts/` (or `agents/`, if it rides the Tier-2 ADK loop)
    so nothing in a component learns a database name the pin does not allow.
  - **What to expect, stated before the run:** the CORRECTION blocks are the interesting
    part — a hop the log later retracted is exactly the edge a naive traversal will happily
    walk, and whether the loop notices the retraction is the first thing to look at.
  - **KEPT-UPDATED 2026-09-02 (same day) — the family is two files, not one, and the second
    brings the traversal's negative space.** `internal/research/mm-aar-research.md` landed on
    `main` (fd3aa92b; provenance corrected 2c184a79): the after-action review of the JOB→MFTS
    search, transcribed from seven company artifacts that live on an UNMERGED research branch
    — not company main, not port candidates, cited by path only. Two of those artifacts are
    graph-loadable beside the log and belong in this experiment: the **probe log**
    (`internal/research/_probes/<subject>-probes.jsonl`, one object per probe — `source / tool /
    query / scope / result_count / outcome`, `outcome ∈ empty | irrelevant | blocked | stale |
    exhausted | exhausted_in_scope`, with a positive `control_query` that must pass before
    `exhausted` is admissible) and the **source whitelist**
    (`internal/research/_registry/source-whitelist.yaml`: confirmed-good sources AND
    controlled dead ends, `decay` mandatory, graduates to the ingestion registries only through
    the gate). Loaded, the probe log is the set of edges the analyst tried and ruled out, each
    with its control — exactly what a KGoT loop needs so it does not re-walk a dead end — and
    the whitelist is the `known` half of MM3's novelty score. The probe log's row is the MM3
    search log's sibling (`tool / query / outcome` beside `tool / search / theme / novelty`);
    whether the two converge into one row shape is a groom question this experiment answers
    with data rather than by ruling. Three AAR §3 rules go into the loop's retry logic as
    written: a negative probe without a passing positive control is INVALID, not negative
    (3.1); a census over an artifact needs a schema control before "the platform does not hold
    X" is a finding (3.2); the artifact and the reading are cited separately — the image is
    VERBATIM, a model's reading of it is GROUNDED (3.6).

- **`Idea-237`** · 2026-09-02 · `[doc]` · **open** · prio? **Med** —
  **The data-flow-overview gate prompt calls "MM3" the Output-tab / log-substrate extractor —
  that is MM7's work, and MM3 is something else.** Found while closing MM3 (2026-09-02, laptop).
  `config/gate-prompts/data-flow-overview.yaml` names MM3 nine times (lines 10, 40, 65, 112, 134,
  137, 260, 269, 390) as the item that reads the Output-tab log verbatim, enriches the members and
  fills the SOURCE-badged log fields (`launcher_kinds`, `compute_target`, `placement_handoff`,
  `landing_prefix`) — "absent until MM3 lands and the field says so". In the backlog as it stands,
  that is **MM7** (`Control-M Output-tab log extractor … joined onto :ETLProcess`, drydocs-lineage,
  in_progress); **MM3** is the mind-map state file + the shared entity/ID extractor + the search
  log's theme/novelty columns (drydocs-deepdoc, done). Line 65 even files the consumer as
  "drydocs-lineage (MM3)", which is MM7's module. The numbers shifted at a groom after the prompt
  was drafted (2026-08-21), and nothing re-pointed the prompt. Why it is an inbox line and not a
  fix: `config/gate-prompts/**` is canonical-company (J72 notes), so a producer-side edit to a
  drafted, unsigned prompt is a cross-repo reconciliation, not an edit — and a reader who takes
  the prompt at its word will look for MM3 to close the Output-tab fields and find a state file.
  Smallest fix: s/MM3/MM7/ at the nine sites, with the consumer line's module corrected; the
  `gates: [data-flow-overview]` edge on MM3 itself stays, because the evidence-ref grammar MM3
  built IS gate territory (§E).

- **`Idea-236`** · 2026-09-02 · `[idea]` · **open** · prio? **High** —
  **The JOB→MFTS research landed (120 hops, 19 open questions) and it answers Idea-104's
  evidence half — five gaps against the backlog, one of which blocks the file-transfer
  lineage strategy outright.** Source: `internal/research/JOB-MFTS-MM-research.md` (the
  company-side mind-map research log, transcribed producer-side 2026-09-02 at its stated venue
  `feat/dd_lineage @ b6ca9422`; 2,183 lines, 6 self-corrections, 21 gotchas). The strategy under
  test: MFTS/SFTP/API transfer metadata as an inventory matched to jobs, confirmed, then written
  into the Control-M FileWatcher description so the Control-M database becomes the source of
  record for the job→route binding — completing source→target lineage for file transfers and
  feeding the runbook.
  **WHAT THE RESEARCH SETTLES.** Idea-104's evidence half: 89 of 89 real MFTS routes carry a
  6-digit NUMERIC route id (production capture `372399` inside the sampled range); the
  `MFTS_RT_IN_*`/`MFTS_RT_OUT_*` string pair appears in **zero** real routes and reads as a
  documentation placeholder; the UUID key belongs to OneMFT, a **different product**; and
  `NEP4824` — the runbook's "Inbound MFTS Route ID" column — is the partner/account stem, not a
  route id at all. Four namespaces, at least two homonyms. **MFTS is Axway SecureTransport 6.0.3,
  SEAL 89830, distinct from FileMover/OneMFT** (CORRECTIONS H93 + "three platforms"). The
  ruling stays the SME's; the log's own words: *a confirmation rather than a coin-flip*.
  **THE PREMISE CORRECTION.** "We don't have loaders planned for MFTS routes" is true of producer
  `main` and false of the company's `feat/dd_lineage`: `:MftsRoute {route_id}`,
  `USES_INBOUND_ROUTE`/`USES_OUTBOUND_ROUTE`, `DELIVERED_VIA`→`:DeliveryMechanism` and
  `controlm_filewatcher_metadata.cypher` are **built and active there**, with `route_id`
  UNIQUE-constrained. Producer holds only the parser (`description_tokens.py`). The research's
  G-1 names the consequence: *the key was committed before the shape was ruled*. So the loader is
  not missing — it is a back-flow candidate that must WAIT for the ruling, or it imports the
  question.
  **THE FIVE GAPS, each with where it lands:**
  1. **[BLOCKER — item, p1] No conformant way to record a route id on a watcher today (G-8).**
     C30 (`done`) retired `INBOUND_ROUTE`/`OUTBOUND_ROUTE` on watchers — a watcher is inherently
     inbound — and pointed them at `FTS_ID` + `REC_ID`. Both retired tokens were also
     `MFTS_AGENT only; literal NULL otherwise`, and **every one of the 89 sampled routes is
     SFTP**. So the strategy's write-back step has no token to write into, and under the prior
     standard it would have been NULL for 100% of the real population. The research calls this
     *a defect, not a convention*. Amending a `done` standard that carries a ruling routes through
     **C40** (revisit a signed ruling); the item is the amendment, not the sweep.
  2. **[item, registry] The transfer platforms are not registered (OQ-4).** No `systems[]` row, no
     classification, no owner for MFTS, FileMover or OneMFT — producer `source-registry.yaml`
     confirms it. MFTS has a SEAL (89830) and a named support group (`IP_CFP_ISUP_MFTS`), so it
     is at minimum a `:BusinessApplication`. Control-M cannot be the source of record for a
     relationship whose other end is unregistered. Same class as the registration gaps this
     session already named; the row is the smallest change.
  3. **[item, small] `software-registry.yaml` does not know `mfts` or `axway` (OQ-15, U-1).**
     The vendor was **erased by internal branding** — absent from the UI, portal, API-store entry
     and docs; it surfaced only in a mandatory `User-Agent: Axway/EndPoint` header. Recording
     `mfts` with `vendor: axway`, the way `controlm` carries `vendor: bmc`, is the change that
     stops the vendor being lost again. Whether Axway becomes a **vendor baseline** (a new
     `external/file-transfer/` category and a second baseline rank in `precedence.yaml`) is a
     separate, larger call — a gate question, not this item.
  4. **[rider on G64, or its own item] `:MftsRoute` identity needs the environment (OQ-18).** A
     prod route can be disabled while its CAT twin stays enabled, so `route_id` alone cannot
     express identity; `(route_id, fts_id)` can, and `MFT System Environment` is already a column
     in the search export. **Same shape as G64's `(guid, connectorName)` finding** — the research
     says *worth ruling together*. And OQ-11 adds that a re-provisioned route may not keep its
     id, in which case `route_id` fails ADR 0001's business-key test outright.
  5. **[groom Idea-104 → item] Convene the ruling.** Idea-104 was left ungroomed for three weeks
     because *a groom cannot pick between the readings*. The groom no longer has to pick — the
     evidence is assembled and the gate page exists (`email-dl-contact-point` §G5 stages MFTS
     routes as DPROD ports; OPEN/UNSIGNED). The item is to convene it with this research as the
     evidence base. Two inputs the gate needs that the idea never had: OQ-8's **third reading**
     (the two shapes belong to two platforms), and OQ-5's **H68** (a route is two SFTP legs
     through FTS2 under one request id, which favours the `dprod:inputPort`/`outputPort` pair
     over a single node — *C29 was not inventing a pair, it was reading one*).
  **ONE SME RULING ALREADY MADE THAT SHARPENS THE STRATEGY (OQ-12):** *no daily capture.* DryDocs
  documents **the routes** — the durable framework — and nothing more; transfer history is pulled
  manually and periodically as research needs it. So the inventory is a ROUTE inventory, and the
  loader question collapses to routes only. What survives for the gate is whether a transfer ever
  becomes a graph node at all or stays research evidence (P8).
  **THE ASSESSMENT, stated plainly.** The direction is right and the research is what makes it
  buildable: the operational walk is *watched file → landing directory → MFTS route → sender →
  sender's owner → owning application*, MFTS holds the last four links (H17–H22), and Control-M
  can hand over only the second (G-9) — so an inventory that grounds the description field in
  MFTS's truth before anything is written is the correct sequencing, not a nicety. **Where the
  framing needs one refinement:** Control-M becomes the source of record for the **job→route
  binding**; MFTS stays the source of record for the **route itself**. Two records, one join key
  in the description field — never the route's facts. The description field is typed prose, and
  the "standard" placeholder value appeared in 0 of 89 real routes; a record is only as good as
  what got typed, so the write-back needs a validation guard against the MFTS inventory, not just
  a confirm step.
  **RESEARCH METHOD FINDINGS WORTH KEEPING PRODUCER-SIDE (U-1..U-6):** an internally branded
  platform hides its vendor on every documentation surface and leaks it through implementation
  surfaces — user-agent, cookie names, default ports, path conventions, id shapes — so check
  those FIRST, ahead of asking a team; naming the vendor is what moves a subject from
  entitlement-bound Internal to a publishable External reference; "there is an API" is not
  "there is a source" until the operation list says it DESCRIBES rather than MOVES; and a
  contract observed on one export is not the platform's contract — the log over-generalised that
  way three times in one day and corrected itself each time. These belong in
  `internal/research/_templates/source-probe.md` when that template is back-flowed (it is
  company-side today and the research owes it a correction).
  **KEPT-UPDATED 2026-09-02 (laptop, `feat/research-skills`):** the U-1..U-6 method landed
  producer-side as SKILLS, not as the `source-probe.md` template — `research-general` §2.1 /
  §2.3 / §2.4 carries U-1..U-6 in mechanism, on the `research-probe-discipline` backbone,
  with `research-job-failure` and `research-job-lineage` beside it; all four rebuilt from the
  transcription `internal/research/mm-aar-research.md` (Parts 4–7, reviewed at `2c184a79`).
  The company originals sit on an unmerged research branch, so this is a rebuild from the
  transcription, not a port. The template correction the research owed is moot producer-side:
  the skills supersede the template, and the whitelist schema ships as
  `.claude/skills/research-probe-discipline/references/source-whitelist.template.yaml` with
  the AAR's OQ-a..OQ-e flagged OPEN for the user. One substantive correction at the review:
  the lineage skill's "compare max ids and renumber" step is rewritten to the allocator mint
  rule.
  **TWO HOUSEKEEPING NOTES FROM THE COMPANY'S OWN PASS:** `G64.yaml` is `status: todo` on both
  sides while its research log describes the gate as convened and §B run — worth checking which is
  stale. And the log's hop ids (`H1–H7`, `P1–P6`, `S3`, `G5`) collide with real backlog ids; a
  future grep will conflate them. Cosmetic, but it will bite a reader.
  Not groomed here: items 1–3 are buildable now and should be; 4 is a rider unless G64 has moved;
  5 is the SME's convening. F-1 (a Control-M QR for jobs using MFTS 6) is company-band
  `Idea-10021` and stays theirs. Related: [[Idea-104]], C16, C29, C30, G83, G64, MM7, MM8, MM9.

- **`Idea-235`** · 2026-09-01 · `[idea]` · **open** · prio? **Med** —
  **The measurement apparatus corrupts the measurement, and it fails toward a REASSURING answer
  rather than an alarming one.** Three instances in one session (2026-09-01), across two machines
  and two people, all during the same port:
  1. **cp1252 decoding.** A comparison script read `git show` with `subprocess(text=True)`, which
     decodes with the platform locale on Windows. It mojibaked every em-dash and **fabricated 18 of
     25 reported "differences"**. The file on disk was clean the whole time.
  2. **A truncated pipeline's exit code.** A sweep captured results as
     `... | Select-Object -First N; $LASTEXITCODE`. `-First` terminates a native-command pipeline
     early, so `$LASTEXITCODE` reflected something other than the command — **reporting exit 0 where
     the raw code was 1**. Five prefixes had been declared clean on that basis, and a slice was about
     to be started on it.
  3. **A fixture written to match a hypothesis.** A guard was validated against test data authored to
     make its author's theory true, so it passed and the theory was wrong. The real pair, measured on
     the other tree, scored 0.08 where the fixture said it cleared the floor.
  **THE COMMON SHAPE, and it is what makes this worth a rule rather than three fixes:** in every case
  the instrument was the thing that was broken, the artifact under test was fine, and **the corrupted
  measurement said everything was OK**. A tool that fails loudly gets fixed in minutes. A tool that
  fails into "clean", "18 differences found", or "the test passes" gets ACTED ON. Both of this
  session's failures that reached a commit came from tooling that quietly reported success.
  **WHY IT IS NOT AN ACCIDENT that they all fail reassuringly.** Each is a default that optimises for
  not-interrupting: a locale decoder that substitutes rather than raises, a pipeline that stops
  reading when it has enough, a fixture that the author wrote and therefore believes. Defaults are
  chosen to keep going, and "keep going" reads as "fine".
  **DISPOSITION — the candidate rule, not yet ruled:** when a measurement contradicts an expectation,
  **check the instrument before the subject**, and prefer the check that can fail loudly — read the
  raw exit code before parsing, decode explicitly, reconstruct a fixture from the incident at its
  real values rather than authoring one. Cheap in every case. The counter-argument is that it is a
  discipline rather than a mechanism, and this repo's own history says a discipline nobody is forced
  to follow rots — so the real question is whether any of the three admits a guard. Related:
  [[feedback-verify-before-asserting]], and J72's own notes carry all three as worked examples.

- **`Idea-234`** · 2026-09-01 · `[idea]` · **open** · prio? **Low** —
  **A branch tip can be green while commits inside it are red, and nothing records which — so a
  bisect through the range fails on the guard rather than the defect.** Observed on
  `feat/ui-web`, 2026-09-01, and reported by the session that made it rather than found by
  anything: `e7e95f07` and `f44fb40d` shipped two console components without their
  `config/taxonomy/ui-components.yaml` ledger rows and were RED on `test_ui_components` when
  pushed; `e0c12d10` added the rows and the tip went green. The tip is the state anyone looks
  at, so the range reads as healthy.
  WHY IT IS WORTH A LINE RATHER THAN A SHRUG. The session ritual's CI check matches on HEAD's
  sha precisely so that "green" means green at what you pushed — `snapshot.ps1` performs it
  immediately before writing, warn-only. That check is per-push, and it does exactly what it
  claims; nothing aggregates the answers, so a branch accumulates red commits and reports the
  colour of its last one. The cost is not correctness — the tip is genuinely green — it is that
  `git bisect` over such a range returns the commit where a LEDGER row was missing, not the
  commit where behaviour changed, and the bisector cannot tell those apart without re-running
  the suite by hand at each step.
  WHAT MOSTLY NEUTRALIZES IT, and why this is Low rather than Med: CLAUDE.md already mandates
  `--no-ff` for branch merges, so once `feat/ui-web` lands on `main` the red commits leave
  main's FIRST-PARENT line entirely and `git bisect --first-parent` never visits them. The
  hazard is real only while bisecting the branch itself, or a range that crosses the merge
  boundary — which a port range does, since a port reads the full range and not the
  first-parent walk.
  DISPOSITION, if it is ever worth acting on: not a guard. A pre-push hook running the full
  suite would cost minutes on every push to buy a property nobody has needed yet, and a red
  intermediate commit is a normal, legitimate way to work (J68's own guard was written red
  first on purpose — the difference is that it went green in the SAME commit). The cheap
  version is a note: when a ledger roll describes a range, say which commits inside it were
  red at push, the way step 272 says which ids were re-minted. That is one sentence per roll
  and it is written by the session that already knows.

- **`Idea-233`** · 2026-08-31 · `[idea]` · **open** · prio? **Med** —
  **Record HOW a source was captured, not only how much its content is trusted: a capture-rung
  alongside the VERBATIM/GROUNDED/SYNTHESIZED axis.** Every `SOURCE-MANIFEST` today carries a
  trust axis, which says how much interpretation sits between the source and the claim. It does
  not say how the bytes were obtained, and those are different questions: a fact read out of a
  served OpenAPI document and the same fact read off a printed rendering of that document can
  both be labelled VERBATIM, while one is reproducible with a single request and the other is
  a parsing project that silently drops whatever did not render.
  THE LADDER, five rungs, worth capturing as a declared vocabulary rather than prose: (1) a
  machine-readable spec or bulk export - the served document itself, byte-for-byte; (2) an
  authenticated API call you make yourself - same data, one object at a time; (3) saved HTML or
  a rendered DOM - structure survives as markup, often incomplete for a single-page app; (4)
  print-to-PDF plus layout-mode text extraction - position survives, semantics do not, and it
  is expensive and bug-prone; (5) copy/paste as text - loses indentation, required markers, and
  anything held in glyph position. The operating rule is to work DOWN only until something
  answers, and never to start below rung 3 without checking above it.
  WHY IT PAYS FOR ITSELF: the failure it prevents is scraping a rendering when the source was
  one request away, and that failure is invisible after the fact - the transcript of a rung-4
  capture looks exactly as authoritative as a rung-1 one. Recording the rung per evidence slot
  makes a finding's cost legible without re-deriving its provenance, and makes "nobody has
  probed this source yet" a task rather than a silent gap.
  THE COROLLARY THAT IS NOT OBVIOUS: the ladder is TYPICAL fidelity, not a guarantee - a lower
  rung can beat a higher one. Observed case: a print-to-PDF came back text-bearing and looked
  like the better capture, but the page's central table had rendered as an image, so its rows
  were simply absent from the extracted text, while the copy/paste of the same page preserved
  every row. So a rung is a prior, not a verdict: check what a capture actually CONTAINS before
  ranking it, because the loss is silent when the rest of the page extracts cleanly.
  RELATED, and the reason this is not just method prose: it generalises the rule this repo
  already holds about images - a rendering may inform a reading, it may not be the citation. The
  ladder says the same thing with a gradient instead of a boundary, and it adds the exception
  that boundary lacks: a rendering is worth capturing when it shows RELATIONSHIPS a flat export
  only shows as columns (which row is a definition and which an execution, which value is an
  alias and which resolved from it). Capture it to understand the export; assert only from the
  export.
  SHAPE IF BUILT: a declared `capture_rung` on the source registry entry and on a research log's
  evidence slots, with the same default-deny discipline the classification label has - no
  unlabeled default. Cheapest first step is the vocabulary plus the manifest field; the probe
  procedure can stay prose until something needs to enforce it.
  PROVENANCE: surfaced 2026-08-31 from a company-side research-template review; the transcription
  is machine-local and Internal. The ladder itself is mechanism and carries nothing company-specific.


- **`Idea-232`** · 2026-08-31 · `[bug]` · **open** · prio? **High** —
  **A backlog item can be HELD by an annotation while the ready list still calls it ready,
  because `next_ready` is computed from `depends_on` alone.** Found the expensive way: O26
  was pulled and claimed during a p2 task run because both its dependencies were `done`.
  It carries `annotations.status: 'SME HOLD 2026-07-22: runbook template shape goes through
  a HITL template session BEFORE this view is built — deps are done but do NOT pull this
  item until that session rules'`. The claim was released the same session with nothing
  built, but the pull commit and its release are both on the trunk, and a session with less
  slack would have built it.
  WHY THE READY LIST CANNOT SEE IT. `next_ready` is derived — status `todo` plus every
  `depends_on` `done`. That is the right rule for DEPENDENCIES and it is the whole rule
  today, so a hold expressed anywhere else is invisible to it. The board's Ready-to-pull
  strip, `validate.py`'s derived list, and the pull rule in CLAUDE.md all inherit the same
  blindness — the pull rule tells an agent to take the next ready item and says nothing
  about reading annotations first.
  WHAT MAKES IT WORSE THAN A ONE-OFF: the hold is on the item precisely BECAUSE the deps
  are done. An item blocked by dependencies needs no annotation; the annotation exists for
  exactly the case the ready list gets wrong. So the two mechanisms are most likely to
  disagree in the situation the annotation was written for.
  CHEAPEST HONEST SHAPE, and it is small: teach the derivation to exclude an item whose
  `annotations.status` (or any annotation the schema blesses for this) reads as a hold, and
  render it on the board as HELD with the annotation text rather than dropping it silently
  — an item that vanishes with no reason is its own defect. If the schema has no blessed
  field for this, minting one is the first step and is a `drydocs.backlog.v3` change, so it
  is a schema decision rather than a validator tweak.
  SCOPE CAUTION: do NOT let this become a general "block on any annotation" rule. Most
  annotations are notes, not holds. The distinction has to be a declared field or a declared
  vocabulary, or the guard starts refusing items nobody meant to hold — which would be worse
  than today, because a false hold is invisible in the other direction.
  RELATED: [[Idea-230]] is the same family seen from the other side — there, an item's
  acceptance went stale against its dependency; here, an item's PULLABILITY goes stale
  against a ruling. Both are "the backlog knows something the derived view does not".


- **`Idea-231`** · 2026-08-31 · `[bug]` · **open** · prio? **Med** —
  **`canAccessModule` decides who sees which console module and has no test, and no guard
  pins which modules are designated `sme`.** Noticed at O59, which set `access: 'sme'` on
  `/remediation` — a one-word edit that changed the module from visible-to-every-role to
  steward+admin. The change was intended and the reason is recorded inline, but nothing
  outside the diff would have caught it either way.
  TWO SEPARATE HOLES, and the second is the larger one. (1) `canAccessModule` in
  `web/src/modules/registry.ts` is a pure three-line function with three call sites
  (`layout/Aside.tsx`, `lib/auth.ts`, `routes/OverviewRoute.tsx`) and no test — exactly the
  shape the O80 vitest runner exists for, and cheaper to guard than to argue about. (2) No
  guard pins the DESIGNATIONS. Which modules are `sme` is a visibility decision made
  deliberately, module by module, with a reason written beside each (FB-03 for `/software`
  and `/gates`, the delta argument for `/remediation`); a designation added or removed by
  accident reads as an ordinary registry edit, and the failure is silent in BOTH directions —
  a module wrongly opened shows an end user numbers they will misread, and a module wrongly
  closed simply disappears for them with no error.
  WHAT THIS IS NOT: not an authorization defect. The server re-resolves the real role from
  the token on every call and the API is the enforcement point, so nothing here is a data
  exposure — this is about the console's own audience decisions staying deliberate. Say that
  in the item so nobody prices it as a security fix.
  CHEAPEST HONEST SHAPE: a vitest file over `canAccessModule` (the three roles against the
  three designations, including the `undefined`/`'all'` default), plus a pinned list of which
  module ids carry a non-default `access` — the same "state the number so it cannot drift up
  quietly" pattern `ui-tests.yaml`'s coverage pins already use. A pin is right here precisely
  because the list SHOULD change rarely and always on purpose.

- **`Idea-230`** · 2026-08-31 · `[chore]` · **open** · prio? **Med** —
  **An item's acceptance can be overtaken by its own dependency's growth, and nothing
  notices.** Found while building O59, whose acceptance says "PROFILE frames render G68's
  four censuses". G68 has five: census (e) INVOCATIONS was merged into it from `Idea-140` on
  2026-08-19, eight days after O59 was raised on 2026-08-11. Nothing connected the two.
  WHY IT IS WORTH A MECHANISM RATHER THAN CARE. The builder is left with two bad options and
  no third: follow the LETTER and ship four censuses when five exist, or follow the PURPOSE
  and silently deviate from a written acceptance. O59 took the second and recorded the
  deviation in the code and the close note, which is the best available answer and still
  relies on somebody happening to read the dependency's notes closely enough to spot it. The
  information was not missing — G68's own notes say "MERGED 2026-08-19 (groom)" in plain
  words — it just had no route to the item that depends on it.
  WHERE THE HOLE IS, precisely. `depends_on` is a SCHEDULING edge: it decides what enters
  `next_ready` and nothing else. It carries no currency claim, so an amended dependency and
  an untouched dependent are indistinguishable from a dependency that never changed. The
  groom amends items, but a groom is triggered by inbox entries, not by another item's
  amendment. Y5 and the render guards catch STALE RENDERS; nothing catches stale cross-item
  PROSE, and no validator ever could by diffing text.
  CHEAPEST HONEST SHAPE: not a prose diff. For each item still `todo` or `in_progress`, ask
  git whether any file in its `depends_on` set was modified more recently than the item's own
  file, and report that as a currency WARNING in `validate.py` — mechanical, one `git log -1`
  per file, no judgement. It must be WARN-ONLY and it must be said out loud why: most
  dependency edits are irrelevant to the dependent, so a failing check would be noise inside
  a week and would train people to ignore it. The value is a list somebody scans at groom
  time, not a gate.
  SCOPE CAUTION for whoever picks this up: `done` items are deliberately excluded. A closed
  item's acceptance describing an older dependency is a HISTORICAL RECORD and correct as
  written — re-opening those would make verified records retrospectively false, which is the
  same argument the 2026-08-28 groom used when it filed O77 fresh rather than reopening O66.

- **`Idea-229`** · 2026-08-31 · `[chore]` · **open** · prio? **High** —
  **A cancelled CI run is neither green nor red, and nothing reads it as unverified — so a
  commit can reach main having never been checked, and its failure surfaces on somebody
  else's next push.** Both of this session's first two pushes were cancelled by the newer
  push; the guard failure they carried appeared on the OTHER machine's commit, where it read
  as that commit's fault until the log was opened.
  WHAT ALREADY COVERS THIS AND WHERE THE HOLE IS: snapshot.ps1's CI check matches on HEAD's
  sha, which is what makes "green" mean green AT WHAT YOU PUSHED rather than at somebody
  else's older commit (Idea-111). That catches STALE GREEN. It does not catch NO VERDICT — a
  cancelled run has a matching sha and no result, so the check has nothing to disagree with.
  The producer-side half is one sentence of logic: treat `cancelled` as UNVERIFIED and say so,
  the same warn-only way the existing check reports.
  WHY IT MATTERS MORE THAN IT LOOKS: two machines pushing minutes apart is the normal case
  here, not the edge case — the same concurrency the I6 mint rule and the J31 wip-branch rule
  exist for. Every one of those rules makes work VISIBLE across machines; this is the same
  gap in the verification channel.
  SEPARATE AND ALREADY RESOLVED, recorded so the run ids in this entry still read correctly:
  on 2026-08-31 run 33401557831 failed all three jobs in 2-3 seconds on a GitHub billing block
  ("recent account payments have failed or your spending limit needs to be increased"),
  executing nothing. The user raised the spending limit the same day and the re-run started
  normally. Account-side, no repo change, closed.

- **`Idea-187`** · 2026-08-29 · `[task]` · **groomed → N22 (2026-08-30)** · prio? **Med** —
  **Producer has no registry row for the PAT Product Application Report, so two loaders the
  company runs have no producer-side source.** The 2026-08-28 manual-load PoC established the
  three PAT reports and which loaders each feeds: Team Details Report (`pat:people-report`),
  Product Catalog People Report (`pat:product-catalog`), and the **Product Application Report**
  — which feeds `pat_product_owners` and `pat_area_products` company-side under the id
  `pat:catalog-app`, and which producer's registry does not carry at all. The gate prompt
  `manual-download-provenance.yaml` (company, drafted 2026-08-28) records the wider form: a
  2026-08-27 PAT pull landed thirteen reports in the `pat/` drop zone and four in active
  analytical use resolve to no dataset id.
  **Why this was not just added at the 2026-08-29 census close.** Adding `locator.report` to
  EXISTING rows is a field edit and was done. Minting a NEW dataset id is T19 territory — T19
  ruled `pat:product-catalog` precisely so neither repo's legacy string survived, and inventing
  a third id unilaterally producer-side would re-open exactly that. The company id
  (`pat:catalog-app`, replacing `pat-catalog-app`) is a candidate, not a default.
  **Also unresolved and riding the same gate:** `pat:people-report` is bound to the Team Details
  Report while the report actually named "…People Report" is `pat:product-catalog`'s — the two
  ids read crossed (D1). The mismatch is now recorded in the registry row's own comment and the
  new `test_manually_downloaded_reports_name_the_report_they_come_from` guard makes the report
  name declared rather than tribal, but the RENAME is the gate's call, not a build's.

- **`Idea-186`** · 2026-08-28 · `[task]` · **groomed → G127 (2026-08-30)** · prio? **Med** —
  **The superseded-database line-scan, applied to the five operator docs the 2026-08-24 fold
  touched, finds 18 un-escaped historical mentions across four of the five files — G114's
  clause (e) declined to bundle the fix and this is the recorded follow-up.** At G114's build
  the guard's exact SUPERSEDED_NAMES / allowed-line logic was dry-run against
  `drydocs_core/schema/provisioning/README.md`, `docs/design/drydocs-startup-refresh-runbook.md`,
  `docs/design/drydocs-project-review.md`, `docs/design/drydocs-core-runbook.md`, and
  `internal/repo-README.md` (the last is clean). The offenders are flowing narrative prose
  naming retired databases without the escape wording on the same line — six lines in
  project-review, five in the startup runbook. The reason it was not swept in G114: three of
  the four files are GOVERNED design-doc renders (verbatim-publish rule, feedback anchors key
  on the rendered text), so the fix is a prose pass plus a design-doc re-render and review,
  not a mechanical reword. The follow-up item should: reword the 18 lines to carry the escape
  wording, re-render with render_design_doc.py, and extend the guard's scan to a small
  DECLARED operator-doc list (the extra-docs idiom test_runbook_currency.py uses) so the
  surface stays guarded after the sweep — that last part is the piece that stops the drift
  from recurring, per the G114 close note's general form (guarded surfaces followed the fold,
  nine unguarded ones did not).

- **`Idea-185`** · 2026-08-28 · `[question]` · **open — the MECHANICAL half is groomed → J61 (2026-08-28); the POLICY half below is the user's, because it is a choice about how two live sessions share one working tree** · prio? **Med** —
  **Twice on 2026-08-28, hours apart, a session could not sync the shared desktop checkout
  because the other live session was holding an uncommitted edit to a file the incoming merge
  also touched.** Commit `2946de82` records the first in its own message body (the port-ledger
  session committed from a temp worktree, ff-blocked by the uncommitted ADR 0015 draft); the
  weekly groom hit the identical abort on the identical file and independently invented the
  identical workaround. J61 writes the recovery recipe down and gives the branch guardrail an
  answer for the detached case, where the show-current command returns an EMPTY string.
  **The sharp part is WHICH file blocks, and it is not the draft.** The uncommitted ADR 0015
  body (`docs/decisions/0015-team-edition-template.md`) is UNTRACKED and blocks nothing at all;
  what blocks is its one-line index row in `docs/decisions/README.md`, because Lane B's ADR 0016
  appended a row to that same file. The ADR index is a shared APPEND surface, so any draft that
  has touched the index blocks every incoming ADR for as long as the draft is held. The same
  shape applies to every append-only index in the tree, not just this one.
  **The question, four readings, and they lead different places.** (1) Commit the index row
  immediately and separately, keeping the draft body uncommitted — the row is one line, it is
  append-only, and it is the only part that collides; the cost is an index that points at a file
  nobody else has. (2) Commit the whole draft at once as an explicit draft-status ADR, accepting
  that a half-formed decision then sits in the governance index, which the repo treats as a
  governed surface. (3) Hold the draft outside the tracked tree until it is ready, accepting that
  it is then invisible to the other machine and unbacked by git — the exact failure the J31
  work-visibility rule exists to prevent. (4) Change nothing and expect the second session to use
  a worktree, accepting today's cost as the price of the current setup, which is what both
  sessions did by default. A groom cannot pick between these: (1) and (2) trade governance
  cleanliness against unblocking, (3) trades it against visibility, and (4) is a decision to
  keep paying.
  **Not urgent, and worth saying so.** The workaround works, J61 makes it cheap, and the block
  clears the moment the ADR lands. This is captured because it recurred within one day and
  because the index-is-the-hot-spot finding generalizes past this one draft.

- **`Idea-184`** · 2026-08-27 · `[idea]` · **groomed → O71 (2026-08-28)** · prio? **High** —
  THE ADR 0015 REGISTER ROW'S NAMED TRIGGER HAS FIRED: the fastapi/full-stack-fastapi-
  template row says 'nothing adopted... only re-opens if a shared estate console is
  chartered (the one legitimate use identified)' — and the internal ui-workstream branch
  is now building the user/login implementation, which is that use. Per the register
  discipline stated in the ADR itself: a watched source firing its trigger does not
  auto-change anything — it opens a backlog item, and AUTH IS A TRUST BOUNDARY, so the
  adoption routes through a gate. Candidate shape: cherry-pick the template's auth
  PRACTICES (OAuth2 password flow + JWT + hashed credentials + user model + recovery
  flow — the survey already characterized it: 'users-in-a-workspace rows behind JWT'),
  cited in the register row, never the scaffold (the ADR's survey rejection stands —
  clone-and-diverge, no update lifecycle, Stripe/orgs baggage). Producer-side the seam is
  the O-epic's ?as= headless sign-in pattern (a stub exactly where real auth lands);
  company-side it is their ui-workstream call. Groom: one item to draft the auth-boundary
  gate question + the register-row amendment; the ADR file itself is the other session's
  draft — coordinate, never sweep.
  **GROOMED 2026-08-28 → O71.** One item, exactly as this entry asked: draft the gate
  prompt for the console auth boundary and draft the register-row amendment. It adopts
  nothing — the scaffold rejection stands, the practices are what go to the SME, and each
  practice is a separately tickable confirmation so declining any subset is a valid
  sign-off. Filed under epic O rather than a Team Edition epic because this entry names
  the `?as=` headless sign-in as the producer-side seam and no TE epic exists yet (see
  [[Idea-179]]). The coordination instruction is written INTO the item rather than left
  here: `docs/decisions/0015-team-edition-template.md` was an uncommitted working file in
  the shared tree at groom time, so O71 clause (d) lets the item close whether or not the
  draft has landed and forbids a session from resolving the gap by authoring the ADR
  itself.
- **`Idea-183`** · 2026-08-27 · `[chore]` · **groomed → J57 (2026-08-28)** · prio? **Med** —
  SET-NOT-COUNT acceptance, adopted from the company session's measured trap (2026-08-27,
  their memory note): two sessions independently measured the same failing-test TOTAL and
  treated agreement as confirmation — but one of the failures was new and self-inflicted;
  agreeing on a total is not agreeing on its contents. Producer surfaces that compare
  totals today: the port acceptance (suite counts, Track-1 tallies, '55 of 55 are the
  documented clusters'), snapshot.ps1's green-at-HEAD check, and any 'this is clean'
  claim after a targeted fix. Candidate shape: (1) port/reconcile acceptance records the
  failing-test ID SET (sorted node ids) and diffs sets between baseline and result — a
  swap that keeps the total visible; (2) a 'clean claim' convention: targeted-file
  verification is never sufficient — run the repo-wide guard family (module boundary,
  render determinism, no-render-parsing, repo paths) whose failures no targeted file
  catches — the company side recorded the same rule with their guard names the same day.
  Groom into the reconcile-port skill + snapshot ritual when picked up.
  **GROOMED 2026-08-28 → J57.** Both halves ride one item: the set-not-count swap on the
  port/reconcile acceptance (sorted failing-test node ids, diffed as sets, with the total
  still printed) and the clean-claim convention naming the repo-wide guard family by test
  path so it is executable rather than an exhortation. Two clauses were added at grooming
  that this entry did not state: the snapshot script's green-at-HEAD verdict is a third
  surface that must be examined and either changed or explicitly ruled already
  identity-based, and the surface list must be exhaustive rather than sampled — a partial
  sweep here reproduces the exact class of miss the rule exists to prevent. The item edits
  procedure only and ships no test change.
- **`Idea-182`** · 2026-08-27 · `[bug]` · **groomed → K30 (2026-08-28); the two producer-verifiable halves are startable now, the header RE-PIN waits on the landed header list per that item's clause (g)** · prio? **High** —
  PRODUCER pat_projection.py SHARES THE G82 DEFECT CLASS the company just measured and
  fixed on their side (their G82 close-out session 2026-08-27; the header facts land as a
  citable file with that cluster's SME review status — do the edits from the FILE, not
  from relay). Verified producer-side at drydocs/pat_projection.py: (a) the seal_ids
  header is marked PINNED from the pat-evidence README at one spelling while the live
  export uses a case-different one — and seal_ids is NOT in REQUIRED_FIELDS, so on a real
  run the mismatch degrades to an empty column and a run that prints success writes zero
  dev-team→application edges (exactly the company's finding); (b) test_pat_projection
  writes its synthetic fixture header in the SAME believed spelling, so code and test
  agree and are both wrong against reality — 'built and tested' and 'never run' true at
  once, one layer down; (c) jira_board_id maps a header this report does not carry (it
  lives in a sibling export); (d) KNOWN_DROPPED holds 12 believed spellings where the
  company's landed census corrected and extended the set. FIX CLASS (Lane B item at
  groom, after the PAT-cluster review status arrives): re-pin the header map + dropped
  set from the LANDED header list; make EVERY mapped field's absence loud, not only
  required ones (the company's adopted rule); re-pin fixtures against the recorded
  header list from the review status §3.2 — the packet's schema-of-record section is
  exactly what fixtures should assert against, which closes the fixture-agrees-with-code
  trap structurally. Header names are mechanism (03-hitl-sme-flow: column names commit;
  values never); estate row counts stay out per the volumetrics fence.
  **GROOMED 2026-08-28 → K30.** Every claim was re-verified against this tree before the
  item was written, not carried across from the relay: `REQUIRED_FIELDS` holds three fields
  and `seal_ids` is not among them; `missing_optional` is computed but reaches only the
  report object and never an exit code; `KNOWN_DROPPED` holds 12 entries; the test fixture
  writes the same believed SEAL-id spelling the module looks for. K30 splits by what is
  verifiable TODAY — make every mapped field's absence loud, and resolve `jira_board_id`,
  which maps a header this report does not carry — from what needs the landed header list,
  and its clause (g) makes `blocked` a legitimate outcome for the latter so no session
  re-pins from memory. Its clause (d) links the fixture to the RECORDED header list rather
  than to the module's own constant, which is what closes the agrees-with-itself trap
  structurally instead of moving it. The wider question — which OTHER loaders make a
  believed header authoritative and test it against itself — is deliberately left out of
  scope and stays available for a sweep once this worked example is fixed.
- **`Idea-181`** · 2026-08-27 · `[chore]` · **groomed → J58, J59, J60 (2026-08-28)** · prio? **Med** —
  YAML/PY HEADER STANDARD + a freshness guard (user review request 2026-08-27; ties to the
  port protocol and TE). The exemplar exists and is already in use — the source-mapping
  four-key block (schema: / source: / classification: / updated:, see
  config/source-mappings/design-docs.yaml) — but coverage is thin and the one freshness key
  we have LIES: of 138 non-backlog tracked YAMLs, 104 have no updated: key, 32 no schema:
  key, and of 24 files WITH updated: checked against git last-touch, 16 are stale
  (PORT-MANIFEST itself: updated 2026-08-20, git 2026-08-27) — a hand date that drifts is
  worse than none. Gate prompts are the governed exception (Module/Source/Registry
  ref/Classification enforced by test_gate_pages) but carry NO date key at all; files
  without updated: bury their freshness in per-section notes (20-mappings-seal: 34 body
  dates, none in the header). Py side is healthier informally: 214/446 module docstrings
  cite an ADR/gate/item, 132 carry dates, 31 have no docstring — standardize lightly there.
  Candidate shape: (1) the four-key header REQUIRED on governed config YAML (+ optional
  layer:/domain: where the vocabulary domain applies), guarded like test_doc_registry;
  (2) the guard must solve the LYING problem, not just presence — producer-side, compare
  updated: against git -1 --format=%as per file; note git dates DO NOT survive the port
  (disjoint histories stamp port day), which is exactly why the in-file date is the
  cross-repo mechanism and why updated: is a PER-SIDE field at the manifest (the
  doc-source-registry field-split precedent); (3) TE inherits the block — a copier-updated
  instance needs in-file vintage because template refreshes rewrite files wholesale.
  Groom with Idea-180 (gate status keys) — same disease, same guard family.
  KEPT-UPDATED 2026-08-27: python-architect persona review
  (docs/reviews/persona-python-architect-idea-181.md) against copier / copier-pdm /
  ss-python / full-stack-fastapi-template — two prescriptions corrected before grooming:
  (F1/F2) copier updates are three-way MERGES keyed on .copier-answers.yml _commit, not
  wholesale rewrites — so the header standard scopes BY FILE CLASS (required on governed
  DATA files, FORBIDDEN in template-class files where a hand date guarantees update
  conflicts; the ADR 0015 D4 seam); (F3) the git-compare guard is blind in CI (shallow
  checkout, no fetch-depth override — verified) — presence/schema guard in pytest now,
  freshness as a producer-side pre-commit hook later (no .pre-commit-config exists yet);
  (F4) enable ruff D100/D104 instead of a bespoke docstring guard (select has no D rules);
  (F5) one JSON Schema for the header, not N bespoke tests; (F6) schema: is the
  TE-load-bearing key (copier migrations key on it) — sequence schema-coverage first,
  updated:-coverage second.
  **GROOMED 2026-08-28 → J58, J59, J60.** Split three ways, and the split comes from this
  entry's own persona review rather than from convenience. J58 is the header standard: one
  JSON Schema (F5) under `config/schemas/`, scoped BY FILE CLASS with template-class files
  FORBIDDEN from carrying a hand date (F1/F2 — copier updates are three-way merges keyed on
  `.copier-answers.yml` `_commit`), `schema:` coverage sequenced ahead of `updated:` (F6),
  and the 53 gate prompts gaining the date key they lack under the guard they already have.
  J59 is the freshness half and it left J58 for a mechanical reason (F3): comparing
  `updated:` to `git log -1 --format=%as` is blind under CI's shallow checkout — confirmed,
  `.github/workflows/ci.yml` uses `actions/checkout@v4` with no `fetch-depth` — so it ships
  as the repo's first pre-commit hook, and it carries the per-side `updated:` declaration at
  the port manifest, because disjoint histories stamp every ported file with port day. J60
  is the Python half: `select` carries no `D` rules today, so F4's D100/D104 plus the ~31
  missing module docstrings, and no bespoke guard. The two measured baselines (32 files with
  no `schema:`, 104 with no `updated:`; 16 of 24 dated headers stale) are recorded in the
  items as figures to RE-MEASURE at pull time, not as facts to trust.
- **`Idea-180`** · 2026-08-27 · `[chore]` · **open** · prio? **Med** —
  Gate state is not machine-readable: only 4 of 52 gate-prompt YAMLs carry a status key;
  everything else resolves only by prose-parsing the 4,191-line gate-log — and the log is
  already stale against the tree once (line ~1125 says the snowflake-data-catalog prompt is
  not drafted; the file exists — G119 owns the dated correction). Surfaced by the 2026-08-27
  gate survey that found 13 of 20 unsigned gates unowned. Candidate shape: a required
  status key on every spec (drafted | signed-off | deferred) guarded by test_gate_pages,
  derived FROM the gate-log at migration and drift-checked against it after — the log stays
  the authority, the key becomes the queryable index (J37: read the importable object,
  never parse a render — this is the same disease one layer up). Groom AFTER the 13
  run-the-gate items land so the migration sweeps a stable queue.
  **RE-READ AT THE 2026-08-28 GROOM — deliberately NOT groomed, on this entry's own
  instruction.** The last line asks for the migration to run after the 13 run-the-gate items
  land so it sweeps a stable queue, and none of them has. Grooming it now would mint an item
  whose first act is to wait, and whose derived-from-the-log migration would then have to be
  re-run against a queue that moved underneath it. Nothing else changed: the gate-log is
  still the authority and the status key is still proposed as a queryable index derived from
  it, which is J37's rule one layer up. Re-check when the run-the-gate queue drains — it is
  the trigger, and it is visible on the board rather than needing a reminder here.
- **`Idea-179`** · 2026-08-27 · `[idea]` · **open** · prio? **Med** —
  ADR 0015 (Team Edition, rev 7 draft) application, from the Chase leadership-page scrape
  (docs/reviews/chase-leadership-scrape-2026-08-27.md): TE should ship a NEWCOMER'S
  OPERATING-STRUCTURE OVERVIEW page — "who runs what around here" for the instance's org:
  the team's unit inside its LOB, the leadership roster one level up, the function seats
  that matter to support (CIO / data & analytics / risk / control), and the escalation
  attachment the instance already models. Built from membership evidence the graph already
  holds (SEAL contacts + escalation DB internally; public leadership pages as the External
  twin), rendered with the HAS_MEMBERSHIP-not-REPORTS_TO discipline and a per-source as-of
  stamp on every fact — the scrape's D1-D7 drift record is the proof the stamp is needed
  (even the publisher's own page carried one fact in three concurrent vintages), so the
  page teaches a newcomer to read org facts with dates attached instead of trusting them
  flat. Fits ADR 0015 D1 (a completeness-ledger surface: derivable entirely from data the
  instance already ingests, so its gaps are measurable) and D6 (ships in the template as a
  GENERATED surface, never authored prose that would rot exactly the way the scraped bios
  did). Groom into the ADR 0015 epic when that epic lands; until the ADR is accepted this
  stays an inbox idea, not a commitment.
  **RE-READ AT THE 2026-08-28 GROOM — not groomed, on this entry's own terms.** It closes by
  saying it stays an inbox idea until ADR 0015 is accepted, and the ADR is still a draft:
  `docs/decisions/` on `main` runs 0014 then 0016, with the Team Edition file an uncommitted
  working copy in the shared tree. There is consequently no TE epic to file it into — the
  same absence that pushed [[Idea-184]]'s item onto epic O instead. The idea itself is
  unchanged and its two disciplines (HAS_MEMBERSHIP not REPORTS_TO; a per-source as-of stamp
  on every fact) now have a nearer anchor than when it was captured, since the `:Employee`
  backbone with its REPORTS_TO creation policy landed on `main` in the interim. Trigger: the
  ADR is accepted and its epic is chartered.
- **`Idea-178`** · 2026-08-26 · `[chore]` · **groomed → J55 (2026-08-27) — the ENFORCEMENT half only (nothing stops the retired string coming back); the cross-repo doc-corpus id migration stays STANDING → the next port session, which is the only place it can be settled** · prio? **Med** —
  **The org-acronym sanitization renamed the doc corpus id the two repos JOIN on.** Gate-log
  RECORD 2026-08-26; the old-to-new mapping is written once, in `internal/cdo-reference/README.md`.
  The company registry row still carries the pre-rename id, and their 2026-08-19 Confluence
  capture ran under it. The next port session treats this as a deliberate id migration, per-entry
  per the port-review F-table (producer fields cross, company fields never do), and checks whether
  their load ran — i.e. whether graph doc ids carry the retired string (the `essential-graphrag`
  retired entry is the string-lives-on-in-the-graph precedent). Also: the `hr-bootstrap-loads-config`
  worktree predates the sweep — whoever merges it re-runs the done-gate grep (`git grep -i` for
  the retired string outside `internal/`).
  **RELOCATED AND GROOMED 2026-08-27.** This entry was captured below the audit-trail heading in an
  ad-hoc shape and was invisible to both `test_plan_ideas.py` guards; it is re-filed here with a
  conforming header, and the guard gap that hid it is [[I5]]. The manual "re-run the done-gate grep"
  step is what became **J55** — a boundary guard on J15's pattern, reading the retired token from
  the internal mapping file so the test embeds no literal of it. What J55 explicitly does NOT touch
  is the cross-repo half above: producer-side enforcement rules nothing about their registry row or
  their loaded graph, so that stays open on the port trigger.

<!-- add new ideas at the top -->

- **`Idea-228`** · 2026-08-31 · `[bug]` · **open — found while verifying O78, desktop** · prio? **Low** —
  **Relationship chips dodge NODES but not each other, so two names whose edges pass near the same
  point still overlap — now visible on /docs, where DESCRIBES lands on top of NEXT_CHUNK.** O66
  moved the label out of the SVG edge layer into an HTML chip; O77 taught the chip to walk along
  the edge's perpendicular until it clears every NODE rect; O78 brought MiniDag onto that same
  component, which is what made this visible — before it, DESCRIBES rendered as the two letters
  "ES" behind a node, so there was nothing to collide WITH. The obstacle set in
  `placeClearOfNodes` is `nodeRects` from the store and nothing else. NOT FIXED AT O78 by a
  deliberate call: chip-vs-chip placement is order-dependent in a way node-dodging is not — each
  chip's final position depends on the others', so a naive registry of placed rects invites a
  render loop or an order-dependent layout, and the three canvases O77 tuned are currently
  correct. A safe approximation exists if this is ever worth doing: treat other edges'
  MIDPOINTS (computable from endpoint node centres, so no feedback) as small obstacles. Cheap
  mitigations that do NOT work: raising z-index only chooses which of the two names is destroyed,
  which is the trade O77 already rejected once.
  · **AMENDED 2026-08-31 (user question: would the NVL canvas fix this, and how does mermaid
  handle it?) — THE RECOMMENDATION ABOVE IS THE LESSER ANSWER. Better dodging shrinks this class;
  it does not retire it. There are three strategies and we have been climbing them one rung at a
  time.** (1) PAINT ORDER — the SVG label in the edge layer, which is what O78 removed: the label
  loses to nodes. (2) POST-HOC DODGING — O66/O77/O78: the label is placed after the layout and
  then walked clear, which cannot see other labels without an ordering problem, and that IS this
  entry. (3) LAYOUT-TIME RESERVATION — the label is a first-class layout participant with
  dimensions, so space is allocated for it rather than negotiated afterwards; no dodging code
  exists because none is needed. **MERMAID IS (3):** its flowcharts lay out through dagre, which
  inserts a dummy node carrying the edge label's size into the ranking pass — our own
  `docs/design/drydocs-remediation-tdd.md` diagram is exactly this shape (`C -->|"rule codeable"|
  D1`). Caveat, stated because it was not verified in-repo: mermaid is not a dependency here (the
  fences are rendered by whatever displays the markdown), so that is dagre's documented behaviour
  rather than something read from source this session; it also reserves RANK space rather than
  guaranteeing zero overlap. **NVL IS NOT A FIX, verified against the installed package rather
  than assumed:** `@neo4j-nvl/base` 1.2.1 exposes NO overlap, collision or label-avoidance option
  at all — `captionAlign` is only top/bottom/center within an element, and neither
  ForceDirectedOptions nor the other layout options mention label space. What NVL changes is the
  ODDS, two ways: node captions render INSIDE the node, so O78's defect class cannot recur there
  at all, and a force layout makes edges long relative to their labels, unlike MiniDag's tight
  hand-authored positions. Two edge captions near the same point still collide, and O81's canvas
  carries the same exposure today. **WHY MINIDAG CANNOT SIMPLY DO (3):** its node positions are
  hand-authored constants in the demo data, so there is no layout engine to hand the label to —
  dodging was chosen because it is the only option inside that architecture. So the real fork is
  not "better geometry": it is whether these surfaces move onto a layout engine (dagre, or NVL's
  force layout) at all, which retires the whole class, versus another rung of dodging, which does
  not.

- **`Idea-227`** · 2026-08-31 · `[bug]` · **open — found by O80's new unit runner, desktop** · prio? **Med** —
  **A synthetic city's country reports that it HAS a drawable outline when it does not, because
  `resolve.ts` reads `country_id` and ignores `country_alias` — the same family as the Z5 index bug
  the file was written to catch.** `PlacedSite.countryHasNoShape` is computed as
  `COUNTRY_NO_SHAPE.has(city.country_id ?? '')`, but a synthetic city carries no numeric
  `country_id` — only `country_alias: 'SYN'` — so the lookup asks for the empty string and misses
  `SYN`, which the gazetteer declares `no_shape: true`. The UI therefore offers an outline to tint
  and drill into for a country that has none. `countryId` is null for the same reason, so synthetic
  countries never reach `countryIds` and never appear in the drill-down list either. Both follow
  from one missing `?? city.country_alias`. NOT FIXED AT O80 by that item's scope guard — it buys
  the test capability and proves it, and changing what the map draws is Z-series work with its own
  review. The correct expectation is already written down as a deliberately failing
  `it.fails` case in `web/src/components/map/resolve.test.ts`, so fixing the code turns that test
  red and tells whoever fixed it to flip `it.fails` back to `it`. Worth noting as evidence rather
  than coincidence: the runner found this on its FIRST run, in the one module the item named.

- **`Idea-225`** · 2026-08-30 · `[idea]` · **open — found by G129's doctor, desktop** · prio? **Med** —
  **A variable set in `.env` alone is visible to every loader and invisible to every binding check,
  and the two surfaces will disagree out loud the first time an Oracle account lands here.** The
  settings classes declare `env_file=.env` (`drydocs_core/config.py`), so pydantic reads the
  machine-local file; `drydocs_core.env_refs.expand()` reads `os.environ` and nothing else, which is
  what `config/source-bindings.yaml` resolves through. Live on this desktop today: every `NEO4J_*`
  variable answers from the file, not the process. It is harmless there because no profile
  references them — but put `ORACLE_DSN` in `.env` and a loader connects while
  `drydocs landing-zones --check` calls `oracle-psgmgr` not-configured-on-this-machine. G129 REPORTS
  the divergence (`drydocs env-doctor` flags `invisible_to_bindings` and names the affected
  profiles) rather than resolving it, because the obvious fix is wrong: making `expand()` read the
  file would mean every test that monkeypatches a variable to empty silently picks up the author's
  own `.env`, trading a visible disagreement for a machine-dependent suite. The real options are (i)
  a documented "export it" instruction, which is what the doctor prints today, (ii) an explicit
  opt-in file read on the binding path only, guarded so tests never see it, or (iii) moving the
  settings classes off `env_file` so there is one channel. That is a ruling, not a build. Related
  [[G125]], [[G129]], [[Idea-223]].


- **`Idea-223`** · 2026-08-30 · `[idea]` · **groomed → G128 (2026-08-30)** · prio? **Med** —
  **G125 built the ONE expansion function but did not migrate the seven resolvers onto it — the
  list is enforced, the resolvers still disagree.** What shipped: `drydocs_core/env_refs.py` with
  `expand()` (bare `${NAME}` only, bash defaults REFUSED, secret registered at expansion),
  `DECLARED_VARIABLES` (24 entries) and process-local masking. What did NOT: `resolve_data_root()`
  still treats an empty string as unset and raises its own `DataRootNotSetError`;
  `resolve_log_dir()` still walks `DRYDOCS_LOGDIR` then the `SPIDERP_LOGDIR` alias then a default;
  `credentials_path()` still takes any non-empty override verbatim; `MappingStore.__init__` still
  imports `os` inside the constructor to read one variable. WHY DEFERRED, and it was a risk call
  rather than an oversight: each resolver raises a type other tests catch by name, so migrating
  them is a behavior change disguised as a refactor, and G125 had eight other acceptance clauses
  to land. WHAT HOLDS THE LINE MEANWHILE:
  `test_every_variable_first_party_code_reads_is_declared` reads the IMPORTABLE objects — the
  env-name constants plus each pydantic settings class's `env_prefix` + fields (J37, because no
  grep can see `NEO4J_URI` when the prefix composes it) — so a NEW undeclared variable fails even
  though the old resolvers are untouched. That is the property clause (c) actually wanted; this
  item is the rest of it. THE ONE DESIGN DECISION TO MAKE FIRST, so the migration does not become
  a bisect: whether the resolver-specific errors become subclasses of `UnsetVariableError` (callers
  and tests keep working, one exception hierarchy) or whether the callers move to the new type (a
  wider diff, a cleaner end state). `EnvVar.aliases` already covers the `SPIDERP_*` legacy chain,
  so the log-dir case needs no new mechanism. Related [[G125]], [[Idea-222]].

- **`Idea-224`** · 2026-08-30 · `[idea]` · **open — re-read at the 2026-08-30 groom and deliberately not groomed: the trigger is a Snowflake account existing on a machine, not a decision anyone can take here** · prio? **Low** —
  **The `snowflake-catalog` binding profile is declared with NO variables, and is the one row
  waiting on something outside the repo.** State at main: `config/source-bindings.yaml` declares
  it with `env: {}` and `status: declared-unconfigured`, serving three datasets
  (`catalog@[db].[schema].datasets_v`, `...distributions_v`, `snowflake:schema-inventory` — all
  three `confirmed: false`, all three `adapter: ~`). No Snowflake account exists on either
  machine, so there is nothing for a variable to hold. DECLARING IT EMPTY IS DELIBERATE and should
  not be "tidied away": the check reports `declared-no-variables` instead of the carrier being
  absent from the report altogether, which is exactly the coverage lie G125 exists to end. WHEN AN
  ACCOUNT APPEARS, three things move together and none of them is an id change: (1) the profile
  grows an `env:` block of `${NAME}` references; (2) those names are added to
  `DECLARED_VARIABLES` in `drydocs_core/env_refs.py`, or `expand()` refuses them — a variable
  cannot enter by being used; (3) `status: declared-unconfigured` is dropped. ADJACENT AND
  SEPARATE: the two `catalog@...` rows are the flagship `[schema]`-redacted ids, so they also sit
  in the id-grammar gate ([[Idea-215]], [[Idea-218]]) — that work pairs the un-redaction with
  `SourceEntry.urn` and rides its own SME gate, and NOTHING here waits on it. A binding is how a
  carrier is reached; the id is what the dataset is called. Related [[G125]], [[Idea-218]].

- **`Idea-222`** · 2026-08-30 · `[idea]` · **groomed → N24 (2026-08-30)** · prio? **Med** —
  **ACCESS PATHS to one datapoint are already documented THREE times, each per-source, and never
  generalized: a row can name one path, never a choice among several, and nothing ranks them.**
  User capture, 2026-08-30 ("it may have been documented -- manual reports, database, API; code
  from the repo versus a copy from the server; the user path versus functional-id access points").
  Checked before writing, and the user is right: WHAT EXISTS ALREADY — (1) the `acquisition:`
  block, N12 clause (c), declares the enum `via: api | db` with the G96 Control-M adapter
  (`drydocs_core/adapters/controlm/api.py`, which exists) as the worked example, and clause (b)
  covers the manual-report path with `format: csv | ascii | json` plus `drop_dir`. So all THREE
  paths the user names are in the vocabulary. Measured at main: mode manual 15 / automated 15;
  `via` = `db` on all 15 automated rows and `api` on ZERO. (2) The repo-versus-server case is
  documented in full in `docs/design/drydocs-lineage-mac-runbook.md` — promotion-repo clone
  (Bitbucket, `<name>#<guid>` folders) versus the per-pipeline Swagger export tool, WITH the
  ruling: the SME caveat (2026-07-23) that the clone main may LAG because feature branches are not
  reliably merged, so "the folder listing is a floor on the inventory, never the authority", and
  "dataflow is per-pipeline swagger regardless of which source discovered the pipeline".
  (3) `config/gate-prompts/dpl-dataset-registry-contract.yaml` already treats per-SEAL API versus
  bulk export as two paths to one datapoint and gates the choice: clause C4 rules discovery
  precedence "in config/precedence.yaml terms", backed by clause B4's measured api-versus-bulk diff
  for the same SEAL/day (GUIDs in one and not the other, field-level divergence counts).
  WHAT IS MISSING, and it is three things, not one: (a) `via` is a SCALAR, so a row records the
  path taken, never that the datapoint HAS two — the three cases above each had to write prose
  instead; (b) nothing ranks paths — `config/precedence.yaml` exists with the right conflict policy
  (winner highest-authority, loser_disposition alias, require_sme_confirmation, never silent-drop)
  but its `order:` entries rank SOURCES OF TRUTH ABOUT A FACT (bmc-baseline, internal-standards,
  seal-pat-source-of-record, lob-product-team, hand-verified-crosswalk, servicenow-tom,
  seal-contact-extract), which is a different question from WHICH PATH TO THE SAME SOURCE WINS —
  so the DPL gate points at a mechanism whose shape does not fit yet; (c) THE USER-PATH VERSUS
  FUNCTIONAL-ID DISTINCTION IS A FOURTH DIMENSION not in the vocabulary at all — a human at a
  Swagger web page and a service account at a programmatic endpoint are the same `via: api` and
  the same object, but differ in PRINCIPAL, in what each can see, and in auditability. That is
  closer to the K2 FID/ALIAS tiers than to a format. WHY IT MATTERS beyond tidiness: paths
  DISAGREE (the clone-lag measurement is exactly that), so an unrecorded path choice makes a
  divergence unattributable — you cannot tell a stale copy from a real change. And an MCP server
  ([[Idea-221]]) would be one more path, so this is the axis that idea plugs into rather than a
  competing one. NOT PROPOSED: widening `via` to a list, or adding a path-precedence section to
  precedence.yaml, are schema changes fenced by the unsigned N10 clause D2 and would ride its
  gate. Related [[Idea-221]], [[N12]], [[G25]].

- **`Idea-221`** · 2026-08-30 · `[idea]` · **groomed → N24 clause (e) (2026-08-30), the READER-GRAIN half only; the MCP-server build stays open, downstream of that ruling and of a separate HITL question about whether such a tool may write a committed file** · prio? **Med** —
  **The missing surface may be an MCP SERVER, not a UI — for Jira, for Confluence, or for data
  registrations themselves.** User capture, 2026-08-30, against [[Idea-220]]: DataHub's UI turned
  out to have no model of its own (it stores the recipe as an opaque string), so the honest cost of
  the no-UI posture is only a scheduler and a validating form. An MCP server is a third option that
  was not in that comparison — it is not a UI and not raw YAML editing, but a typed tool surface an
  agent drives, which fits a repo where the operator is already working through an agent in the
  editor. THREE CANDIDATES, and they are not the same kind of thing: (a) DATA REGISTRATIONS — tools
  to register/validate/inspect a source-registry row, which is the one that fills the [[Idea-220]]
  gap directly, and the validating-form half of it is `test_connection`-shaped (a typed report,
  reachability plus per-capability verdicts); (b) JIRA — a seam already exists,
  `drydocs_remediation/jira.py` (the remediation handoff, G3); (c) CONFLUENCE — the publisher is
  machine-local at `internal-local/confluence/`, smoke-validated 2026-07-07 against the personal
  instance. PRECEDENT IN-REPO: the graph is already reached this way (`neo4j-drydocs` MCP server),
  so the pattern is established rather than new. THINGS THAT WOULD HAVE TO BE RULED before any of
  this is built, none of them decided here: whether an MCP tool may WRITE a committed config file
  or only propose a diff (the HITL gate question, and G126's read-zone ruling is the nearest
  precedent); whether registration tools bypass the gate that `confirmed` exists to hold; and where
  such a server would live under MODULE_MAP (a component, never core). Related [[Idea-220]],
  [[Idea-218]].
  AMENDED 2026-08-30 (user), and it corrects the emphasis above: **the MCP server is a READ
  surface used AFTER configuration, to read the source's metadata -- and the SME identifies WHICH
  server and WHICH configuration, for a given DATAPOINT/PURPOSE.** So it sits on the ingestion
  side, not the curation side: it is a way to REACH a source, not a way to edit our registry. That
  makes it an ADAPTER, and the field already exists at the right grain -- `adapter:` is
  dataset-grained and already names the read mechanism (measured at main: `oracle` 10, `csv` 4,
  `json`/`markdown`/`yaml` 1 each, `~` 13). An MCP server is a new adapter kind; what a row cannot
  say today is WHICH server and with what configuration, and that is precisely the ADR 0017
  binding. Note the 10 `oracle` rows are the same 10 that share one global connection triple
  ([[Idea-220]]), so both gaps sit on the same rows. EVIDENCE FOR THE CLAUSE-2 DEBATE, and it is
  the useful part: selection is per DATAPOINT and per PURPOSE -- finer than per-origin (the ADR's
  proposal) and finer than per-carrier ([[Idea-215]]'s correction). Both of those are about the
  CONNECTION and neither covers the READER, so the binding is two things at two grains: a
  connection per carrier, and a reader per datapoint. DataHub's shape agrees -- a recipe is
  `source.type` plus `source.config`, one per source, and one platform can carry many recipes.
  THE PURPOSE AXIS IS THE GENUINELY NEW PART and does not fit a single static `adapter:` value:
  the same datapoint read for two purposes may want two servers or two configurations, which is
  layer-4 (context graph) shaped rather than layer-1. Flagged, not assumed. AND THE SME CHOICE IS
  A GATE DECISION -- "which server, which configuration, for this datapoint" is the kind of thing
  the HITL flow says is never auto-decided, so it is recorded on the row with its ruling, never
  inferred from the platform.

- **`Idea-220`** · 2026-08-30 · `[bug]` · **closed — ADR 0017 Rev 2 (accepted 2026-08-30) folded these findings into its clauses and G125 shipped the three mechanisms; the only residue is the ADR's stale per-origin TITLE, which rides N23 clause (g)** · prio? **High** —
  **Source-side database configuration is a SINGLETON and ADR 0017 never says so; and the
  editor-first posture it assumes is DataHub's own canonical path, which the ADR also never says.**
  Fifth pass, evidence in `docs/design/datahub-substrate-review.md` Rev 2 (findings 7 and 8);
  venue = this desktop, DataHub clone HEAD `dea0f9c1`. MEASURED at main: the DESTINATION is
  configured well (`Neo4jSettings` + committed `config/dev-environment.yaml`, 8 consumer modules);
  the SOURCE side is one Oracle triple (`ORACLE_USER`/`ORACLE_PASSWORD`/`ORACLE_DSN`) with exactly
  ONE consumer, `_oracle_adapter` at `drydocs/cli_shared.py:769-782`, which takes a query and no
  source id — so there is no seam where a second Oracle connection could enter, and everything
  else is `locator:` prose no guard reads. Consequence the ADR's closing trigger paragraph misses:
  a second Oracle service behind `psgmgr` breaks the CONNECTION layer before it breaks the id
  layer. WHAT DATAHUB DOES: a datasource is registered by writing a YAML recipe in an editor —
  `source.type` plus a pydantic-validated `source.config` carrying host_port/database/username/
  password/service_name — and the UI has NO model of its own: `DataHubIngestionSourceInfo` stores
  `recipe: string`, an opaque blob plus a schedule and an executor id. So the file path is MORE
  structured than the UI path, and DryDocs's no-UI posture is canonical rather than degraded; what
  it gives up is a scheduler and a validating form, which is worth naming so the choice is real.
  THREE MECHANISMS TO TAKE: (1) `${VAR}` expansion is also where the secret is REGISTERED for
  masking (`datahub/masking/bootstrap.py` states it: config loaders register during expansion,
  pydantic models register `SecretStr` at validation) — that is what clause 3's "one expansion
  function" is FOR; (2) the reference-vs-value rule, `if value.startswith("$"): return value` else
  mask, over a credential key allow-list — a committed-YAML WRITE GUARD in about twenty lines, and
  the enforcement [[Idea-218]] (f) says DryDocs lacks; (3) `TestableSource.test_connection` returns
  a TYPED report (`basic_connectivity` + per-capability `capable`/`failure_reason`/
  `mitigation_message`), which is the shape the automated half of `landing-zones --check` should
  return instead of a boolean. ALSO: `config/dev-environment.yaml` — not `config/data-zones.yaml`
  — is the closer precedent for ADR 0017's committed-map/machine-local-value split, because it is
  that split already carrying a live database. NOTE a narrowing of the research report: `C-36`
  says no shared framework-level sanitizer in either language; at HEAD there is no DSN *sanitizer*
  but there IS a shared Python masking layer (`datahub/masking/`) the report's sweep terms would
  not have matched. Related [[Idea-218]], [[G125]].

- **`Idea-218`** · 2026-08-30 · `[bug]` · **merged → N23 (2026-08-30), the id-and-URN half; the ADR-text corrections landed in ADR 0017 Rev 2** · prio? **High** —
  **ADR 0017 clause 1 cites DataHub for a deferral DataHub did not make, and the ceiling it records
  is in the wrong artifact.** Fourth-pass review, evidence in
  `docs/design/datahub-substrate-review.md` (Rev 1); venue = this desktop, DataHub clone HEAD
  `dea0f9c1` 2026-08-30, seven decisive claims re-derived. (a) THE MECHANISM: clause 1 says the
  three-part-key ceiling was fixed with a `dataPlatformInstance` aspect, and concludes the eventual
  DryDocs fix is therefore "a configuration change rather than an id migration". `platform_instance`
  is NOT a fourth key component — `DatasetUrn.createFromUrn` still throws on `key.size() != 3`, and
  the instance is concatenated into the URN name (`avro_codegen.py:516`), so adding one CHANGES the
  dataset's identity. DataHub's fix WAS an id migration, and its connection-shaped object
  (`dataHubConnection`) could not absorb the instance because identity is not resolvable through
  configuration. The ruling may still stand; the reason given does not — the migration is
  DEFERRED, not AVOIDED. (b) THE REAL CEILING: clause 1 points at `[db]` in the committed id string,
  but `[db]` is a redaction in a string no code keys on. `SourceEntry.urn` derives
  `({carrier},{artifact},prod)` — dropping the database AND the schema. Measured at main: 30 rows,
  30 distinct URNs, so nothing is broken yet, but the key is (carrier, bare table name, prod) and
  `psgmgr` already carries three origins, `snowflake` two. DataHub's URN name was always the FULLY
  QUALIFIED native name (verified in the Snowflake connector), so DataHub was one axis short;
  DryDocs is three. Consequence for the pending grammar work: un-redacting `[db]`/`[schema]` in ids
  does nothing for the URN unless `SourceEntry.urn` changes in the same commit. (c) CLAUSE 3 RIDER:
  DataHub's `${VAR}` expander is bash-style and supports `${VAR:-default}` — adopting the syntax as
  cited puts G81 (d)'s silent-default behavior back at the SYNTAX level, where the one expansion
  function cannot see it; the expander must substitute and REFUSE defaults. Also three backends with
  a stated precedence (DataHub > File > Environment), so a second backend needs one stated
  precedence added to clause 3's list. (d) CLAUSE 4 CORROBORATED + a cost: `dataHubConnection` IS
  the Purview shape shipped, standalone by construction — and NOTHING links it to the datasets it
  serves, which is the same un-enumerable defect ADR 0017 opens with. Clause 4 should declare the
  reference direction and its guard. (e) CLAUSE 5: better example available — the encryption key
  falls back to the literal string `ENCRYPTION_KEY` (`application.yaml:173`), so setting it
  correctly later is what breaks decryption; sharper than the demo account. (f) NEW PROPERTY WORTH
  RECORDING: neither peer has a normative prohibition on credentials in an identifier, and DataHub
  has no sanitizer in either language (zero-hit Java sweep re-derived) — DryDocs HAS the stated rule
  and no enforcement, the one substrate property where the peers are behind. Related [[Idea-215]],
  [[G125]], [[N10]].

- **`Idea-219`** · 2026-08-30 · `[idea]` · **groomed → C38 (2026-08-30) — registered `planned` only; the edge meaning stays the gate's** · prio? **Med** —
  **Replica-ness is recorded three times in the registry and as no EDGE — DataHub rules that the
  typed derivation edge is the answer and the aliasing mechanism is an anti-pattern.** Today
  `origin != system` (the id shape), `authority: ADS`, and prose in `notes` all say "this is a
  copy"; all three are attributes and none is traversable, so no query can walk replica -> origin.
  DataHub's ruling (research report `D-04`): use `Upstream{type=COPY}` (released 2020-05-21,
  patchable one edge at a time), never `Siblings` — because `Siblings` asserts "these are the same
  thing" and `SiblingGraphService` ACTIVELY DELETES any lineage relationship between two siblings
  from the default merged read path, destroying the very fact being recorded. Second half of their
  ruling worth carrying: record the HOW redundantly, because the lineage TYPE does not survive graph
  traversal on any of their four read paths. Minting a derivation relationship type here is an
  ontology decision — `docs/RELATIONSHIP_GUIDE.md` plus the relationship-vocabulary registry plus
  the HITL gate, `status: planned` first — so this is inboxed, not proposed. Evidence:
  `docs/design/datahub-substrate-review.md` anchor `replica-note`. Related [[Idea-218]].

- **`Idea-216`** · 2026-08-30 · `[bug]` · **groomed → N25 (2026-08-30)** · prio? **High** —
  **The BDAT `layer` is a property of the SYSTEM, so it records where an extract came FROM, not
  what it is ABOUT — which is why `human` is structurally unreachable rather than merely unused.**
  MEASURED at main: no dataset row carries `layer`; all 16 system rows do (gate source-registry-v2,
  2026-07-31, put it on the v2 system row). Every dataset therefore INHERITS its layer from its
  carrier. Consequences, all live rows: `hr@[db].psgmgr.hr_phone_exp` is `taxonomy_category:
  People & Org` and inherits **data** from psgmgr; `seal@[db].psgmgr.cm_escalation_db` — the
  ServiceNow/HPSM technician routing — also inherits **data**, and would inherit **technology** if
  it came from the `snow` system instead; `pat:people-report` is also `People & Org` and inherits
  **business** from pat. So THE TWO `People & Org` DATASETS ALREADY SIT IN TWO DIFFERENT LAYERS,
  same subject, different label, purely because they were pulled from different carriers. That is
  the axis measuring the wrong thing, demonstrated without needing a new row. AND IT EXPLAINS THE
  ZERO: `human` is empty not because we hold no human data (we hold at least three such datasets)
  but because a SYSTEM is a place you connect to and no place is a person — the label can only be
  reached by inventing a fake "HR system" to carry it, which is the same category error one level
  up. [[Idea-210]]'s note that `technology` is the default bucket (9 of 16) is true but secondary;
  this is the structural half. SHAPE OF THE FIX (a ruling, not applied): `layer` describes the
  dataset's SUBJECT, so either it moves to the dataset or it is DERIVED from `taxonomy_category`,
  which is already dataset-grained, already has the right values (People & Org 2, Software/Apps 4,
  Product 1, Pipelines 11, Data Asset 5, Infrastructure 3, Architecture 2, ITSM/Gov 2) and has
  ZERO consumers today. Deriving costs no new field, which matters because gate clause D2
  (`registry-wiring-readiness`, N10, UNSIGNED) fences the schema until the SME signs. NEEDED WITH
  IT — the subject-vs-reference test, or it gets re-litigated per row the way "established public
  vocabulary" was: **is a person the SUBJECT of a row, or an ATTRIBUTE of one?** An application
  contacts extract is one row per person-role -> human; an application list with an owner column is
  one row per application -> business. The test is countable (ask what the grain is) and it also
  decides the functional-account case in [[Idea-217]]. Related [[Idea-215]], [[N10]].

- **`Idea-217`** · 2026-08-30 · `[idea]` · **groomed → N23 clause (d) (2026-08-30) — the same grammar gate this entry asks to ride** · prio? **Med** —
  **RULED 2026-08-30 (user): two filtered extracts from one table are distinguished by a SUBSET
  QUALIFIER NAMING THE PREDICATE — `hr@spiderdb.psgmgr.hr_phone_exp#employees` and
  `...#functional-accounts` — not by a `[taxonomy].` prefix on the id.** The remaining work is the
  gate that changes the grammar and the shape of the declared predicate; the discriminator itself
  is decided. Original finding: User proposal, 2026-08-30: functional account IDs live in
  an HR table alongside human owners, so take two extracts from the same table on a filter. AGREED,
  and the strongest reason is not convenience — applying [[Idea-216]]'s grain test, the two land in
  DIFFERENT LAYERS: an employee row has a person as its subject (human), while a functional-account
  row has an ACCOUNT as its subject and the human is an owner attribute (a non-human principal —
  technology or business, not human). Two subjects, two layers, two ontology classes, two
  `confirmed` states, two gates, and plausibly two classifications (a named-human roster is more
  sensitive than a list of account ids). They cannot be one dataset row. TWO OBSTACLES, both real:
  (1) THE ID GRAMMAR IS TABLE-GRAINED — `{origin}@{db}.{schema}.{table}` derives the SAME id for
  both extracts, and `SourceEntry.urn` collides too since it builds from `system` + `artifact`. A
  subset qualifier in the grammar, or an `artifact` that is not the table name (which breaks the
  grammar's own rule that the segment after `@` is "the ACTUAL qualified carrier locator"). Either
  way it is a grammar change and therefore an SME gate — the SAME gate the `[db]` un-redaction in
  [[Idea-215]] needs, so they should ride together. (2) THE FILTER MUST BE DECLARED AS DATA, NOT
  PROSE. A predicate in a `notes:` block recreates ADR 0017's own opening complaint that "prose in
  a locator block is not a declaration" — nothing could then check that the two extracts are
  disjoint, or that together they cover the table. Ready-made shape: OpenLineage's
  `BaseSubsetDatasetFacet` condition grammar (`spec/facets/BaseSubsetDatasetFacet.json` — field vs
  literal expressions, `compare` with EQUAL/GREATER_THAN/..., `binary` with AND/OR, plus partition
  and location variants). HONEST COUNTERPOINT, since it is the one place the precedent points the
  other way: OpenLineage itself would NOT split — its subset facet is an input/output facet, so it
  is run-scoped, and OL keeps ONE dataset identity while recording the filter on the read. That is
  right for observed pipeline lineage and wrong here, because a DryDocs dataset row is a GOVERNED
  REGISTRATION carrying `confirmed`, a gate, a classification and a loader binding — all of which
  must differ between the two extracts. Take OL's predicate grammar; leave its identity decision.
  CANDIDATE CONSIDERED AND RULED OUT (user proposal, then user agreement on the alternative, 2026-08-30):
  `[taxonomy].{origin}@{db}.{schema}.{table}`. It does disambiguate THIS case and it makes the
  subject visible in the id, which is a real merit against [[Idea-216]]. Four arguments against.
  (a) It disambiguates by accident, not by construction — it works only because employees and
  functional accounts happen to fall in different categories; two extracts from one table in the
  SAME category (active vs terminated employees, per-LOB splits) collide again, so it solves the
  instance and not the class, and it encodes a CONSEQUENCE of the filter rather than the filter.
  (b) It puts a mutable judgement in an immutable identifier: `taxonomy_category` is a ruling that
  changes (the mis-layered `dpl` row is live, and [[Idea-216]] proposes re-deriving the whole
  axis), so every re-classification becomes an id migration through `retired:`/`replaced_by` —
  the cost ADR 0017 clause 1 explicitly declined for the INSTANCE axis, and worse here, because
  instance coordinates change rarely while classifications change whenever an SME rules. (c) It
  duplicates a field that already exists on the row and creates a way for the two to disagree; a
  guard asserting prefix == field would prove the segment carries no information (derivable =
  redundant, divergent = defect, no third option). (d) Every precedent puts LOCATION in identity
  and MEANING in metadata — OpenLineage's (namespace, name) are both pure location with
  classification in facets, DataHub's URN is platform+name+env, and ours is origin @ qualified
  locator; a taxonomy prefix would be the first semantic segment in any of them. Cost if adopted:
  all 30 ids change, plus 83 `source_id` references, the overlay, the retired list, the derived
  URNs, every gate citing an id, and the company port. ADOPTED SHAPE instead (user, 2026-08-30) — a subset
  qualifier naming the PREDICATE rather than its classification, e.g.
  `hr@spiderdb.psgmgr.hr_phone_exp#employees` and `...#functional-accounts`: it keeps the
  grammar's own rule intact (the locator is still exactly `spiderdb.psgmgr.hr_phone_exp` and the
  fragment is visibly not part of it), it is stable under re-classification, and it names what
  actually differs. Verified there is NO charset/regex validation on dataset ids — they are free
  strings checked only for membership and retirement — so the separator choice is a design
  question, not a code constraint. Migration precedent exists: `retired.replaced_by` is a LIST and
  `controlm-psgmgr` -> 7 ids is the standing 1->many case. STILL OPEN, and all of it is gate work
  rather than shape work: the separator character (`#` reads as a URI fragment and nothing in the
  code constrains it, but it has to be checked against the URN derivation and the id-bearing
  surfaces); whether the qualifier also appears in the derived URN or only in the dataset id;
  the structured form of the predicate itself (OpenLineage's condition grammar is the shape to
  copy — field vs literal expressions, `compare`, `binary` AND/OR); and whether the guard should
  assert that the subsets of one table are mutually exclusive, and separately whether they are
  required to cover it. This rides the SAME grammar gate as the `[db]` un-redaction in
  [[Idea-215]]. Related [[Idea-216]], [[Idea-215]].

- **`Idea-215`** · 2026-08-30 · `[bug]` · **groomed → N23 (2026-08-30)** · prio? **High** —
  **ADR 0017 clause 2 keys the source binding per `origin`, and for the registry's largest origin
  that row cannot exist.** The clause argues from OpenLineage — "`{origin}@{db}.{schema}.{table}`
  puts the origin where OpenLineage puts the namespace" — and concludes the binding table needs a
  row per origin. Read at the source (clone at `C:\coding\projects\OpenLineage`, HEAD `b995ee00`,
  Apache-2.0), the OpenLineage namespace is a CONNECTION: `oracle://{host}:{port}`, one shape
  across forty-odd platforms. DryDocs's `origin` is a PROVENANCE label — who produced the data —
  and the registry field at the right LEVEL is `system`. The row the ADR describes says
  so itself: `controlm@[db].psgmgr.cm_def_vtab` carries `system: psgmgr`, `origin: controlm`.
  AND `system` IS THE RIGHT LEVEL CARRYING THE WRONG VALUE (user ruling, 2026-08-30): `psgmgr` is
  a SCHEMA, not a system and not a system of record; the database connection behind it is
  `spiderdb`, which the registry names nowhere — it is the token `[db]` redacts in all ten ids and
  `locator.service: ~` on the system row. The registry already half-knows this (the same row is
  identified `psgmgr` AND declares `locator.schema: psgmgr`) and fully knows the carrier half (its
  note reads "the Control-M replica database — CARRIER, not origin"; all ten datasets are
  `authority: ADS`, never SOR). Two consequences: the binding row keys on the connection carrier
  `spiderdb`, since keying on `system` works only while one schema happens to equal one database;
  and `SourceEntry.urn` builds the carrier slot from `system`
  (`drydocs_core/source_registry.py:127-135`), so the ten rows currently derive
  `urn:drydocs:dataset:(psgmgr,cm_def_vtab,prod)` — a schema in the carrier position, and
  correcting the id would change ten derived URNs.
  MEASURED over `config/source-registry.yaml` at main, 15 automated datasets: keyed by `system`
  = 4 rows (psgmgr 10, snowflake 3, oracle 1, drydocs-stg 1); keyed by `origin` = 6 rows
  (controlm 9, hr 1, seal 1, catalog 2, oracle 1, snowflake 1) — so the ADR's "roughly six
  origins" counted right and keyed wrong. TWO FACTS DECIDE IT AND THE SECOND IS FATAL: `system:
  psgmgr` carries three origins (`controlm`, `hr`, `seal`), so a per-origin key mints three
  binding rows for ONE Oracle database, re-fragmenting the connection that clause 4 chose Purview's
  named-profile shape to share — the ADR contradicts itself across two clauses; and `origin:
  controlm` spans THREE systems (`controlm`, `drydocs-stg`, `psgmgr`), so the largest origin has
  no single connection to bind to and a per-origin row is unsatisfiable, not merely redundant.
  `origin: seal` spans two and fails the same way. The fix is one field name — the rest of clause
  2 (inheritance by dataset, the "one mechanism, not two" fence with landing zones, the
  connection/object split itself) all survives, and the counts stay 4/3/1/1 because the grouping
  was never in doubt. This is a RULING and goes to the user;
  nothing is applied. The standing plan already reached the same answer for [[G125]] by a
  different route, and the ADR text is the piece that was never updated to match.
  ALSO: `spiderdb` is the exact test case for the plan's §0, and it is RULED (user, 2026-08-30):
  it is the NAME — the leading, pronounceable segment of the TNS alias. The alias itself is a
  connection coordinate (it resolves through `tnsnames.ora` to host/port/service, which is why the
  port notes warn an alias "resolves only via tnsnames and won't work thin"); its pronounceable
  head is what the database is CALLED. Standing test: nobody connects with `spiderdb` alone —
  that needs the rest of the alias, a tnsnames entry, and a Kerberos principal. So it is an
  identifier, it PUBLISHES, and that is where OpenLineage puts it too (the
  `{serviceName}.{schema}.{table}` name half). Consequences: the `[db]` placeholder in the ten
  psgmgr ids has a known correct value, so un-redacting is a concrete edit — still an id change,
  so still the `retired:`/`replaced_by` re-key plus the SME gate §0 describes; and the grammar
  header's rule ("real db/schema values are connection coordinates -> internal twin only") is now
  wrong on its own flagship case in BOTH halves — `psgmgr` publishes by a hand-waved "established
  public vocabulary" exemption and `spiderdb` publishes on the test. The rule is not merely too
  cautious, it misclassifies the thing it names. Full evidence,
  the scaffolding assessment and a re-derivation checklist:
  `docs/design/openlineage-substrate-review.md`. Related [[Idea-207]].

- **`Idea-211`** · 2026-08-30 · `[bug]` · **closed — fixed same day, 2026-08-30** · prio? **High** —
  **The supplement chain is documented as FOUR members in nine live places and has been FIVE
  since Z3 (2026-08-19); the guard that should have caught it asserts a PREFIX.** `default_chain()`
  returns `base -> seal -> catalog -> registry -> infrastructure`. Nine first-party surfaces on
  main said four: the run-drydocs skill, `drydocs/cli.py`'s module header, the
  `apply-supplements` DOCSTRING, `supplements.py`'s own registry comment, `MODULE_MAP.md`, the
  startup-refresh runbook in three places, `RELATIONSHIP_GUIDE.md`, the SME checklist and
  `internal/repo-README.md` twice. THE SHARPEST ONE IS THE RUNBOOK AT `:146` — it is a CORRECTION
  NOTE, written because an earlier version of that runbook left readers "quietly one supplement
  short", and it states "it has FOUR members". The note that fixed the defect became the next
  instance of it. WHY NO GUARD FIRED: `test_supplements.py` pinned the run-log envelope with
  `assert "chain      : base -> seal -> catalog -> registry" in text` — a substring assertion
  against a `" -> ".join(...)` of the live chain, so the four-name string is a PREFIX of the
  five-name string and the test passes green on exactly the drift it exists to catch. A
  prefix assertion over an ordered join can never detect growth at the end. The correct
  behavioural guards were right all along (`test_registry_order_is_the_documented_chain` and
  `test_sosa_is_opt_in_and_never_in_the_default_chain` both list five) — the code was never wrong,
  only every sentence describing it. Found by transcribing the company-side 2026-08-28 triage
  (`internal/research/triage-bootstrap-2026-08-28.md`, their F-4 claim 1, which named only the
  skill file and missed the other eight). FIXED 2026-08-30: nine strings corrected, the prefix
  assertion made exact, and a NEW GUARD added that scans first-party prose for any arrow-joined
  run of supplement names and asserts it equals `default_chain()` — so the tenth site cannot be
  written wrong. Dated records (CHANGELOG, `G29.yaml`, [[Idea-52]]) deliberately left alone: the
  chain WAS four when they were written. Related [[Idea-212]].

- **`Idea-212`** · 2026-08-30 · `[idea]` · **groomed → G130 (2026-08-30)** · prio? **Med** —
  **`bootstrap` verifies declared-present and never reports live-but-undeclared, and that
  asymmetry is how retired-label constraints survive a wipe.** The command already asserts
  "58/58 declared present". It cannot see the other direction: a constraint alive in the database
  that no `drydocs_core/schema/**/*.cypher` declares. The company-side 2026-08-28 triage found
  three of them on their instance — `ais_capability_id` on `:AisCapability` and `ais_tool_id` on
  `:AisTool` (both typo leftovers, dropped there after a zero-node safety check) and
  `membership_id` on `:Membership`. THE MECHANISM THAT MAKES THIS BITE: constraints outlive data
  wipes. Their census recorded 62 constraints at a TRUE-ZERO node baseline, because the SME's
  wipe was a data delete, not a database drop — so a clean graph is not a clean schema, and a
  retired-label constraint silently enforces an old identity rule against any future load that
  reuses the label. On producer main all three are already resolved (`membership_id` DROPPED at
  G99, 2026-08-18; the two `Ais*` labels appear nowhere in `drydocs_core/schema/`), so this is
  NOT a producer defect today — it is a missing DETECTOR, and the next retirement will recreate
  the condition on any long-lived instance. Shape: `SHOW CONSTRAINTS` minus the parsed
  declarations, reported as a drift WARNING, never an automatic drop — the safety check before
  each of their two drops was a zero-node count, which is a human decision. Needs a live graph,
  so it is not a pure-unit item. Related [[Idea-211]], [[G99]].

- **`Idea-213`** · 2026-08-30 · `[research]` · **groomed → H8 (2026-08-30) — the disposition table; which of the seventeen to reproduce stays the user's ruling** · prio? **Med** —
  **The company tree registers 67 CLI commands to producer main's 50 — the first MEASURED
  back-flow inventory the epic has had.** Both counts read from
  `drydocs.cli.app.registered_commands`, not from `--help` or prose. Theirs and not ours: the
  whole `docs-*` family (`docs-diff`, `docs-fetch`, `docs-preview`, `docs-publish`,
  `docs-register`, `docs-status`), `graph-review`, `graph-verify`, `sme-notes`,
  `new-doc-section`, `ingest-controlm-xml`, `m6-verify`, five `load-snow-*` verbs,
  `load-employee-roster`, `load-dev-teams`, `load-seal-attribution`, and the
  `apply-contacts/locations/platforms/resource-pools/seal-deployments-supplement` verbs. Ours and
  not theirs: `load-essential-graphrag`, `profile-folder-set`. THE FIRST GROUP IS PRECISELY THE
  SME-REVIEW / HITL TOOLKIT already named as the top back-flow candidate — `graph-review`,
  `graph-verify` and `sme-notes` are the generic mechanism this repo has only as docs. Two of the
  five `apply-*-supplement` verbs were already known company-local from [[Idea-52]] (resource-pools
  and platforms, verified 2026-08-04), which corroborates the census rather than duplicating it.
  ALSO UNPORTED: the `devx` system row and its two `devx:bitbucket-repo` / `devx:githubrepo`
  datasets exist in their `config/source-registry.yaml` and nowhere in ours. Detail and the
  per-finding comparison: `internal/research/triage-bootstrap-2026-08-28.md`. Grooming note: this
  is an INVENTORY, not a work item — the deliverable is deciding which of the 17 to reproduce
  mechanism-only, which is [[project_drydocs_review_backflow]]'s standing question, now with
  numbers.

- **`Idea-214`** · 2026-08-30 · `[question]` · **groomed → J63 (2026-08-30)** · prio? **High** —
  **A review run against an un-ported checkout manufactures defects, and it has now happened
  three times.** The company-side 2026-08-28 triage reported the `refresh-*` verbs as "exactly
  backwards" and an exploration pass listed eight commands as unregistered. On producer main all
  three refresh verbs ARE registered with `refresh-reference` as the deprecated alias delegating
  to them (that is G79, shipped 2026-08-23), and SEVEN of the eight commands they called
  unregistered exist here. Their observations were correct for their tree; the DEFECT FRAMING was
  not. This is the third instance: [[Idea-210]] recorded six wrong facts from a checkout predating
  S8/S13/G78/G79, and the same class produced their F-4 claim 2 and most of F-5. So it is a
  pattern with a cause, not a coincidence — and the reviewer has NO WAY to tell a real gap from a
  missing port, because nothing in a review's output states which tree it ran against. Note the
  irony worth keeping: their own adopted method correction ("command names come from
  `registered_commands`, never from prose") is right, is our J37, and would NOT have prevented
  this — reading the importable object faithfully still reports a stale tree faithfully. THE
  MISSING PIECE IS PROVENANCE, NOT METHOD: a review surface that names its own commit and its
  port base, so "absent here" can be read as "not yet ported" rather than "broken". Rides
  [[Idea-210]]'s registry-surface argument (a surface should report the tree it is run against)
  but the justification is cross-repo, which is why it is captured separately. Related
  [[project_port_workflow_topology]].

- **`Idea-207`** · 2026-08-29 · `[bug]` · **groomed → N23 (2026-08-30)** · prio? **High** —
  **The id grammar calls identifiers "connection coordinates" and redacts them, so a registered id
  cannot always identify anything.** SME hit this registering downloaded AWS/Glue metadata as a
  replica: source-to-target mapping over registered ids is the core function, and an id that
  resolves to nothing cannot be mapped. A db or schema NAME is an identifier, not a connection
  coordinate — nobody connects with a schema name. **J13 class 3 already ruled schema publishable**
  ("redacts the database and publishes schema.table", 2026-08-11) and TWO LIVE ROWS VIOLATE IT:
  `catalog@[db].[schema].datasets_v` and `.distributions_v` — the flagship replica rows, whose only
  real token is the view name — plus a `snow@[db].[schema].<table>` TEMPLATE that teaches the shape
  to the next row. It recurs because the carve-out is a judgement ("established public vocabulary")
  with no test behind it, so redact wins by default. THE TEST THAT WOULD SETTLE IT: could someone
  connect with this string alone? A schema name fails; a host, port, service or credential passes.
  THE DB HALF RESOLVES THROUGH ADR 0017, not through redaction — the placeholder is conflating the
  logical database name (identity) with which deployment (the instance coordinate), and 0017 clause
  1 already puts the instance in the binding table. THIRD INSTANCE, same category error: the
  application-id field is a standing placeholder on all 16 system rows (D1 amendment), so the
  identifier a governance product maps ownership through is absent everywhere. Full argument and
  measurements: [[source-registry-identity-review]] I1–I3. NEEDS AN SME GATE — it changes committed
  ids (retired-id mint, `replaced_by`, test pins), so a rider, not an edit. Related [[Idea-208]],
  [[Idea-209]].

- **`Idea-208`** · 2026-08-29 · `[bug]` · **groomed → N26 (2026-08-30), with Idea-210** · prio? **High** —
  **Nothing can see what the registry holds, so a wrong registration is invisible for as long as
  nobody trips over it.** `dpl` is registered `layer: technology` and is wrong — it is a
  pipeline/dataset taxonomy registry, a DATA-layer asset. The distribution shows how: **technology
  9, data 5, business 2, human 0.** Technology is the default bucket, `human` is declared and never
  used, and NO SURFACE ANYWHERE ASKS ANYONE TO CONFIRM A LAYER. The load map renders `layer` as one
  column of a flat systems table — never grouped, never counted, never flagged as unconfirmed.
  THE VIEW MUST BE ORGANIZED BY CLASS, NOT BY NAME: BDAT layer → business application → application
  id → ontology class, with loader and module names demoted to detail. `asset_type` CANNOT be the
  ontology heading — it reads `dcat:Dataset` on 30 of 30 rows, and a constant rendered as a column
  reads as an answer when it is a default; the real class comes from
  `config/taxonomy-ontology-map/`, which the generator already joins, and a row still on the bare
  default is UNCLASSIFIED and should say so. THREE AXES HAVE NO CONSUMER: `taxonomy_category` has a
  full vocabulary (Pipelines 11, Data Asset 5, Software/Apps 4, Infrastructure 3, Architecture 2,
  ITSM/Gov 2, People and Org 2, Product 1) and ZERO readers outside `config/`; `acquisition` reaches
  only `landing-zones` and only its manual half; and replica is COMPUTABLE (`origin != system`,
  corroborated by `authority: ADS`) and computed nowhere. Gate `registry-wiring-readiness` clause D3
  says surfacing this "is a separate item — say so and it gets one"; the SME said so. NO NEW FIELD
  IS NEEDED — every indicator derives from fields that exist, which is what keeps it clear of that
  gate's clause D2. Detail: [[source-registry-identity-review]] V1–V3. Related [[Idea-207]],
  [[Idea-209]], [[N18]].

- **`Idea-209`** · 2026-08-29 · `[bug]` · **groomed → G129 (2026-08-30)** · prio? **Med** —
  **The internal twin is a black hole: the registry names no variable, points at no twin file, and
  cannot say what is unset.** It says the real value lives in the twin and stops — never WHICH
  file, WHICH variables, or WHETHER they are set. `internal/` holds ~20 directories with no index of
  which one carries which system's settings. MEASURED: `.env.example` declares 17 keys; first-party
  code reads **8 more declared nowhere** (console-credentials path, Control-M API config pointer,
  both mapping-store variables, agent registration key, caller variable, a Neo4j container name,
  plus the legacy log/caller aliases). So a null service locator with a comment is an empty slot
  with no way to discover it is empty. THREE VERBS, each reusing a precedent: FIND (a set/unset
  doctor that never prints a value — ADR 0017 clause 3's "one enumerable list" made real), DOCUMENT
  (`.env.example` GENERATED from the declarations so it cannot drift 8 behind again), UPDATE (a
  no-echo writer to the machine-local file, the `set_console_credential.py` pattern — consistent
  with G126's ruling that `internal-local/` is read-mode because the SYSTEM may never write there
  and the operator's hand is not the system). THE TRAP: the enumeration CANNOT BE A GREP —
  `config.py` uses prefixed pydantic-settings, so the Neo4j URI never appears as a literal and a
  text search sees the prefix and misses the field. J37 one layer over: read the importable object,
  never the text that happens to spell it. Detail: [[source-registry-identity-review]] T1–T2.
  Related [[Idea-207]], [[G125]].

- **`Idea-210`** · 2026-08-29 · `[idea]` · **groomed → N26 (2026-08-30), with Idea-208 — one generator, two surfaces** · prio? **Med** —
  **A generic loader question cost ~40 searches and produced a review wrong in six places — the
  wrongness is the finding, not the slowness.** Asked to review a loader and report its registry
  mapping, an agent searched roughly forty times and returned: `cli_ingest.py` is orphaned (it is
  registered, and `CHAINS` comes from `cli_shared` since S13); the samples dir is missing so the run
  skips and exits 0 (it exists, the flag has no default since G78, and a missing input exits 2 —
  that "skipping" string is the CLOSED defect quoted from `chain_inputs.py` as if it were live); the
  SEAL row has no `locator.report` (it does); `AliasChoices` is on the row model (it is not — the
  lowercasing is in the CSV adapter); and MODULE_MAP calls the S8 split deferred (it says it
  shipped). It also MISSED that a third loader binds the same dataset id. EVERY ONE OF THOSE FACTS
  IS IN AN IMPORTABLE OBJECT — `LOADER_REGISTRY`, `LOADER_SOURCE`, `effective_source_id()`, the
  `BaseLoader` ClassVars — and `render_load_map.py` already inverts them. The facts were reachable;
  the surface that hands them over in one call does not exist, so the search filled the gap with
  plausible wrongness. A `drydocs registry --loader <name>` verb removes the room in which that
  answer gets assembled. NOTE the miss pattern: four of the six are STALENESS (a checkout predating
  S8/S13/G78/G79), which is its own argument for a surface that reports the tree it is run against.
  Rides [[Idea-208]] as the same generator; called out separately because the justification is
  different. Detail: [[source-registry-identity-review]].

- **`Idea-206`** · 2026-08-29 · `[idea]` · **groomed → J64 (2026-08-30), the SCAN-ORDERING half only; the CADENCE ruling stays open with its four named directions and is the user's** · prio? **Med** —
  **The depgraph snapshot rolls at every session close, and 30 of the last 33 rolls carried no
  debt signal at all.** Measured on `knowledge/depgraph-snapshots/debt-metrics.jsonl`, 34 rows
  spanning 2026-08-21 to 2026-08-29: 15 consecutive pairs are flat on every metric, another 15
  move only `snapshot_imports` — which says the tree grew, not that anything got worse — and
  **three** move a real debt metric (`4176c12`, `5a0383e`, `55536e6`, each an `a3_fan_in` plus
  `a4_first_party_orphans` shift). That is 9 percent signal. The cadence is roughly five rolls a
  day and peaked at nine on 2026-08-24. WHAT IS ACTUALLY VALUABLE HERE IS NOT THE SNAPSHOT: the
  JSON is under a newest-only retention ruling, so each roll DELETES its predecessor and the
  in-tree file carries no history whatsoever — the durable time series is `debt-metrics.jsonl`,
  which is append-only and costs one line. The two are currently welded together by
  `snapshot.ps1`, so the cheap thing that has lasting value can only be produced by also doing
  the expensive thing that does not. Splitting them is the idea. NOT A PROPOSAL TO DROP IT:
  `tests/unit/test_depgraph_snapshots.py` requires exactly one committed snapshot and
  `tests/unit/test_code_snapshot_loader.py` loads it, so zero snapshots is not a reachable state.
  This is about CADENCE. Directions for the groom to pick between, deliberately not chosen here:
  (a) decouple — append the metrics row every close, roll the snapshot JSON only when the scan
  shows a structural change; (b) skip the roll when every debt metric is unchanged, which makes
  the commit itself the signal; (c) cap it at one roll per day; (d) leave it, on the argument
  that a cheap ritual nobody has to think about beats a conditional one they do. A SECOND CLAUSE
  THAT IS INDEPENDENT OF THE CADENCE RULING, because it cost real work on 2026-08-29: a snapshot
  must be scanned AFTER the commit it stamps exists, never before. A snapshot taken from the
  pre-merge tree that day recorded a directory main had renamed on 2026-08-26, tripped the
  [[J55]] publish-boundary guard, and had to be deleted and regenerated against the merge commit.
  The script stamps `meta.git` (`commit`, `full`, `branch`, `describe`, `subject`, `dirty`), so
  scanning first and committing second makes that stamp a claim about a tree that was never
  scanned. Sibling entries in the same script, both about
  correctness rather than cadence and neither superseded by this: [[Idea-170]] (the board refresh
  skips silently on this desktop) and the item behind the CI verdict asking about `main` from a
  branch.

- **`Idea-205b`** · 2026-08-29 · `[idea]` · **groomed → I7 (2026-08-30)** · prio? **Med** —
  **Any fan-out orchestration has to allocate ids in the coordinator, because N parallel workers are
  N more allocators inside one machine.** Split from [[Idea-205a]] because the disposition differs:
  205a is a tool to build, this is a working agreement to write. No skill in this repo spawns
  parallel workers today, so the whole concurrency model is cross-machine sessions and the rules in
  CLAUDE.md section 0 are written for exactly that. An external fan-out command (the `/batch`
  orchestration, invoked here on 2026-08-29) breaks the assumption in two ways at once. FIRST, ids:
  if any worker grooms or mints, several allocators now run concurrently inside one checkout with no
  counter between them, which is the same failure as [[Idea-205a]] with the rate raised. SECOND,
  renders: every worker that touches the backlog or the inbox regenerates `docs/plan/board.html`,
  `web/src/generated/gates.json`, `load-map.json` and the design HTML, so N units produce N
  conflicting versions of files that are DERIVED and were never meant to have more than one writer
  per cycle. Proposed rule, one sentence: the coordinator allocates every id up front and hands each
  worker a pre-assigned id, workers never mint and never re-render, and fan-out is restricted to
  units touching disjoint source files. Worth stating in CLAUDE.md section 0 beside the pull rule
  rather than left for the next session to rediscover, since the orchestration command is not part
  of this repo and cannot carry the rule itself.

- **`Idea-205a`** · 2026-08-29 · `[idea]` · **groomed → I6 (2026-08-30)** · prio? **High** —
  **There is no allocator. "Next free id" is a sentence in a skill file, and it has now failed six
  times.** The rule lives at `.claude/skills/groom-backlog/SKILL.md` line 51 and at the entry-header
  table in this file, and both amount to: an agent reads its OWN working tree and picks the next
  number. No counter, no reservation, and nothing anywhere runs `git fetch` before minting.
  `drydocs_core/backlog_store.py` is a reader by design and has no allocate path. The guards are all
  local and after the fact: the duplicate-id check in `validate.py` only fires once both files sit in
  one checkout, which is to say once the collision has already happened and the work is renumbering.
  The band tests assert producer stays at or below 9999; nothing compares against a remote at all.
  THE RECORD, because the count is the argument: C19 built twice (2026-07-28, produced [[J19]]), K9
  built twice (produced [[J30]] and [[J31]]), a duplicate Idea-101 ([[J41]]), a duplicate Idea-86
  ([[J47]], recorded at the time as "the second two-session id collision"), two different G70 AND two
  different G71 renumbered to G75/G76 (the incident that produced the allocator bands), and on
  2026-08-29 nineteen ids at once - O69, O70, and Idea-157 through Idea-173. Six incidents, six
  conventions, zero enforcement points. THE CONTROL CASE IS THE INTERESTING PART: ADR numbering
  survived the same day on the same two machines, because `docs/decisions/README.md` carried the line
  "(0015 is an in-flight draft on the desktop.)" - a committed, pushed reservation on an id that did
  not exist yet. Main took 0016, the desktop kept 0015, nothing collided. The mechanism that worked
  was writing the claim down and pushing it at MINT time. PROPOSED, three parts. (a) Make "next free"
  mean free across every remote ref rather than free in my tree: a `--next-id <letter>` mode on
  `validate.py` that fetches, then reads `git ls-tree` over `refs/remotes/**` - tree listing only, no
  checkout, cheap. This alone would have stopped 2026-08-29, because the laptop's O69 was already
  pushed on `origin/feat/ui-workstream` when the desktop minted its own; the desktop never looked
  past its own tree because the rule never said to. (b) Extend the claim protocol from PULLING to
  MINTING - mint the id, push the stub, then write the body - which generalizes the ADR pattern and
  closes the asymmetry [[Y6]] already identified. (c) A guard that compares local item ids against
  `origin/main` and fails when one id carries two different titles, skipping with a named message
  where no remote is reachable (the U26 precedent). NOT A RESTATEMENT OF THE BAND NOTE: the allocator
  bands section of this file already says bands separate producer from company and do not cover two
  producer machines, and commit `430025c5` says it again. The diagnosis has six descriptions and no
  mechanism; this entry is only about the mechanism. Adjacent and deliberately not folded in:
  [[Idea-185]]'s policy half (how two live sessions share one checkout, explicitly the user's call)
  and [[Idea-170]]'s still-unbuilt company-side mirror guard, which leaves the partition one-sided.

- **`Idea-173`** · 2026-08-25 · `[bug]` · **open — the two ACTIONABLE halves LANDED 2026-08-25 (database-inventory.md at ede62d44; the alias-in-prose sweep + SME ruling at f22da676). What stays open is the GENERALIZATION: a canonical-producer file has no company-writable surface, so a company-side fact about a company-side system still has nowhere to live** · prio? **High** —
  **A company session recorded a census on `config/source-registry.yaml`, which is
  `canonical-producer` — so the next port deletes it.** Not hypothetical and not a
  criticism of that session: it asked the right question, got the right answer for
  where a loaderless object's census belongs, wrote it in the right FILE, and the
  file is one the port overwrites wholesale. `PORT-MANIFEST.yaml` has NO row for
  `source-registry.yaml` (only `doc-source-registry.yaml` has its own), so it falls
  to the `config/**` default, which is `canonical-producer`. The census landed
  producer-side in this same commit so the port carries it TO them, which is the
  direction that survives.
  **N10 ALREADY NAMED THIS EXACT FAILURE and it has now happened twice.** Its gate
  prompt (`registry-wiring-readiness`, drafted 2026-08-19) argues from the port
  asymmetry: *"the company's cm_hosts wiring hold is OVERWRITTEN by the producer's
  `confirmed: true` at every port and survives only because a human pinned it and
  armed a re-arm trigger."* That was one field on one row; this is a whole census
  paragraph. **The generalization worth capturing: a canonical-producer file has no
  company-writable surface at all, so "where does a company-side FACT about a
  company-side system live?" has no answer today** — and the answer keeps being
  discovered per-file, at the cost of the work already written.
  **THE SECOND HALF — the census-only ledger class.** `test_source_mapping_drift.py`
  requires every `psgmgr.yaml` object to be exercised by at least one loader SQL, so
  a registered-not-loaded object cannot go in the column ledger. That guard is RIGHT
  and must not be loosened for this. But it leaves column inventory for a loaderless
  object with nowhere structured to live — it went into a `notes:` prose block, which
  no `census_failures()` can reconcile and no drift check can read. If the ledger
  should ever hold it, that is a deliberate schema change (an object class the drift
  guard SKIPS *because* it is registered-not-loaded, with the skip stated rather than
  implied), not a quiet guard edit. Capture-only until something actually needs to
  query a loaderless census.
  **Third, smaller, and the reason to check the id at the next port:** the company's
  row substitutes the REAL DATABASE NAME into the `{db}` slot of the id. The
  producer's is `seal@[db].psgmgr.cm_escalation_db`, and that placeholder is the
  SIGNED N9 grammar (J13 class 3: redact the db, publish schema.table), pinned in
  `tests/unit/test_source_registry.py`. Either that is a local divergence or a
  transcription slip, but the producer row cannot adopt it and the guards would
  refuse it. The value is not repeated here, which is the rule doing its job: an
  id-shaped string is exactly where a database name stops looking like one.
  **KEPT-UPDATED 2026-08-25 (user correction, and it found a real gap).** The value is
  the DATABASE NAME, not an instance SID — the assistant's first framing was wrong. The
  correction is not the useful part; the gap it exposed is. **Ten shipped ids write
  `[db]` and nothing recorded what `[db]` IS**, in this repo or the internal twin, from
  the N9 build on 2026-07-31 until now. A redaction whose real value lives only in a
  shell profile is not a boundary control, it is a gap shaped like one — and the
  precedent for closing it already existed:
  `internal/standards/technology/data-center-inventory.md` is exactly the same artifact
  for the `P`->`T` swap. Written as
  `internal/standards/technology/database-inventory.md`, with the grammar, the ten ids
  it keys, and the two `catalog@[db].[schema].*` rows marked UNRESOLVED rather than
  redacted (their gate prompt is undrafted, so nobody has hidden anything — nobody
  knows yet).
  **AND ONE OPEN RULING IT SURFACED, left for the SME:** the same token is PUBLISHED as
  an env-var prefix (`SPIDERP_LOGDIR` in `.env.example`, ADR 0014, the `run-drydocs`
  skill) and named directly in the `reconcile-port` skill's tnsnames caution, while the
  id grammar redacts it. Either the redaction does less than it looks like, or those
  four sites want the J13 class-2 treatment. Not swept: ADR 0014 already deprecates
  `SPIDERP_*` for one cycle so the env prefix has a scheduled death, and the skill
  mention is a connection mechanism that loses its point if generalized. Same shape as
  the four J13 classes — the assistant proposes, the SME rules.

- **`Idea-172`** · 2026-08-25 · `[idea]` · **groomed → O68 (2026-08-26); the debug-tier Cypher DISPLAY question stays an SME review and is top of the review list — O68 may report that kind's size and retention and may not render its contents** · prio? **High** —
  **The console admin page should surface the log estate: directory, path, size and capacity per
  kind.** SME direction, 2026-08-25, given alongside the ADR 0014 retention rulings. Epic O already
  owns the console and an admin config-traceability lens, and the SME placed this there rather than
  in a new epic — so this is a PANEL on that surface, not a new one.
  **THE DATA ALREADY EXISTS, which is why this is small.** G109 shipped
  `drydocs_core.data_zones.inventory()`, which returns present/absent plus a file count per declared
  zone, and `drydocs landing-zones --json` already emits both halves as one document
  (`manual_zones` + `declared_zones`) with `path`, `mode`, `base`, `inside_repo`, `exists`,
  `file_count`, `empty`. The panel needs a read endpoint over that, not new collection. Capacity is
  the one genuinely missing field — `inventory()` counts files, it does not sum bytes — so a
  `total_bytes` per zone is the one core addition, and it belongs beside the count rather than in
  the API.
  **WHY IT IS WORTH BUILDING RATHER THAN JUST RUNNING THE CLI:** the whole reason
  `drydocs landing-zones` exists is that "my extracts are gone" should be a one-command answer, and
  the person most likely to ask it is the SME on a machine where the CLI is not the habitual
  surface. Post-G105 the panel also answers the retention question the same way — 90 days declared
  against N days actually on disk.
  **ONE THING IT MUST NOT DO WITHOUT A RULING, and the SME asked for this to go to the top of the
  review list: display debug-tier Cypher text.** ADR 0014 clause 6 as ruled splits `api` (lean,
  90-day, no Cypher) from `api-debug` (verbose, short, carries Cypher and request detail).
  CAPTURING that text is ruled; SURFACING it in the console is NOT, and the two are different risks
  — a short-lived file on an operator's disk versus a rendered page. So this panel may report the
  debug kind's SIZE and RETENTION like any other kind, and must not render its contents until that
  review happens. Anything that would display it is blocked on the review, not on this item.
  **Also worth carrying in:** the panel is the natural place to show the `data_zones._resolve()`
  defect while it is live (Idea-171's residue) — the `run-logs` zone resolves to the default
  whenever `DRYDOCS_LOGDIR` is set, so a panel built today would confidently show the wrong
  directory for exactly the kind the SME most wants to see. Fix that first or the panel ships a
  known-wrong row.

- **`Idea-170`** · 2026-08-24 · `[bug]` · **parked → the next company port relays it (re-read 2026-08-27: the entry's own finding is that producer-side action is NONE — all four guards are green here and the id this entry carries was minted by them, so there is nothing to groom and nothing to fix until the relay goes out)** · prio? **Med** —
  **The one-sided allocator partition bit: a company inbox capture landed with NO id at
  all, and its number was minted only after the user asked where it was.** Port step 160
  predicted this in as many words — *"Until that lands the partition is one-sided and the
  next Idea-59-class collision is a matter of time"* — and its company half
  (`n >= 10000` mirror assertion + a committed grandfather constant) is still unexecuted.
  This is the first recorded instance of it actually costing something.
  **WHAT THIS SIDE ACTUALLY HAS — checked, because the company session reported the
  opposite:** `tests/unit/test_plan_ideas.py` exists here with 12 tests, four of them
  load-bearing for exactly this failure. `test_every_inbox_entry_carries_the_header`
  matches ``- **`Idea-<n>`** ·`` per entry, so an unheadered capture fails immediately —
  it is precisely the guard the missing number would have tripped, and its docstring says
  why it exists ("the entry simply does not appear in the scan, which reads as 'nothing to
  review here' rather than as a formatting slip"). `test_idea_ids_are_unique` scans the
  WHOLE file, not just the inbox, *because* union-append is when a duplicate arrives.
  `test_producer_allocates_below_the_company_band` pins `PRODUCER_BAND_CEILING = 9999`
  with a deliberately hand-maintained `PORTED_COMPANY_IDS`. And
  `test_the_bands_are_documented_where_a_capturer_will_read_them` requires `IDEAS.md`
  itself to contain `9999`, `10000+` and `union-append` — the **Allocator bands** section
  has been in this file since 2026-08-18.
  **THE CLAIM TO CORRECT, or it gets re-derived next port:** the company session reported
  (a) "no allocator-bands documentation section in IDEAS.md — the rule lives only in
  `test_backlog.py`'s comments" and (b) "no idea-side band guard: `test_plan_ideas.py` is
  absent **on both sides**, recorded in the port ledger." (a) is true company-side only.
  (b)'s "both sides" half is wrong, and so is its reading of the ledger:
  `PORT-MANIFEST.yaml`'s `test_plan_ideas.py` row is `disposition: per-entry` and reads
  **"The render/header guards are producer-canonical and port whole. The ALLOCATOR-BAND
  block does NOT"** — the ledger tells the company to TAKE the file and invert one block,
  not that the file is absent by design.
  **THE CHEAP HALF IS AVAILABLE TODAY, independently of the band work:** the header and
  uniqueness guards carry no band assumption whatsoever, so porting just those two ends the
  "capture with no id" failure mode outright. Only `PRODUCER_BAND_CEILING` /
  `PORTED_COMPANY_IDS` need the mirror treatment described in port step 160.
  **Producer-side action: none** — all four guards are green here, and the id this entry
  carries was minted by them. Captured so the next port relays a finding instead of
  rebuilding it.

- **`Idea-168`** · 2026-08-24 · `[chore]` · **parked → next internal session** · prio? **Med** —
  **The Control-M profiling numbers are company-estate figures, and every threshold derived
  from them needs re-tuning on the internal side.** Two different things are called
  "profiling" here and both statements about them are true at once. (1) The **cardinality
  volumetrics already given ARE captured**: CM_HOSTS 2026-07-09 (22 distinct DATA_CENTERs /
  5,396 GRPNAMEs / 8,161 NODEIDs) in `drydocs/loaders/sql/adhoc/profile_cm_hosts.sql`,
  `drydocs/loaders/sql/controlm_hosts.sql`, the `controlm-hosts-topology` gate spec and the
  CM_HOSTS `profile.via:` string; CM_AVG_RUN 2026-07-22 (169,639 rows / 14 DCs / 12,639
  folders / 779 node groups / 26 columns) in `profile_cm_avg_run.sql` and the
  `controlm-avg-run-supplement` gate spec. (2) The ledger's `census:` field means the
  **column inventory** (types, nullability, `column_count`), which has only ever run for
  CM_AVG_RUN — **6 of the 7 objects in `config/source-mappings/psgmgr.yaml` still read
  `census: pending`**, so a tool reading the ledger correctly reports them unprofiled.
  Volumetrics are not a census and neither backfills the other: stamping the counts into
  `profiled_on`/`census` would falsify `census_failures()`, where a *recorded* census must
  balance explicit rows against the frozen sweep `count:`.
  **WHERE it runs — internal only, by design.** Backlog P1 carries the rule in its own record
  ("User-run on the internal network (no producer-side psgmgr access); agent transcribes" /
  "Producer never runs these probes (internal-only by design); status mirrors the company
  SoR"). The producer side has no psgmgr, transcribes conclusions only, and consumes none of
  the numbers mechanically — `census: pending` means there is nothing to reconcile, so no
  producer-side ingest, guard or suite is waiting on this. doc 08 Phase 2 (the real column
  census, via the controlm-db skill against the live views) is an internal-session job for the
  same reason.
  **WHAT needs tuning internally:** every number calibrated against the company estate rather
  than derived — the avg-run supplement's ≈30% join-coverage expectation (145,454/169,639
  stats→jobs, 144,827/489,096 jobs→stats), the grain-dedupe discriminator (dups 2–49,
  STAT_PERIOD the leading candidate), the run-time sanity cap (outliers to ~2.65 y), and P1's
  own performance flag (scoped smoke test before the estate-wide join). They ride with the
  probes still owed: `docs/next-internal-session.md` item 1 — the CM_HOSTS **definition-side**
  probes P1–P5 and the **DC scope call** (three datapoints: 22 DCs in CM_HOSTS, 14 in
  CM_AVG_RUN, 4 production) are open even though backlog P1 reads `done`, because only the
  avg-run set actually ran.
  **KEPT-UPDATED 2026-08-24 — the census half LANDED, the tuning half did not.** An internal
  session ran the doc 08 Phase 2 catalog census read-only against live psgmgr (column
  inventory + row counts, no data values) and the conclusions are transcribed into
  `config/source-mappings/psgmgr.yaml`: **7/7 objects now read `census: complete`** (was 1/7),
  every sweep carries its frozen `count:`, `census_failures()` is empty, and **CM_DEF_VJOB's
  `kind` was wrong — recorded `view`, it is a TABLE** (corrected in the same pass; no other
  file asserted the wrong kind). Column counts / rows: VTAB 26 / 76,364 · VJOB 121 /
  1,089,358 · LNKI 12 / 1,293,560 · LNKO 10 / 1,318,968 · SETVAR 11 / 4,716,529 · CM_HOSTS 5 /
  13,745 · AVG_RUN 26 (2026-07-22). STILL OPEN, and why this entry stays parked: per-column
  DATA profiling (null rates, distinct counts, value domains) is a separate heavier pass; the
  CM_HOSTS **definition-side** probes P1–P5 still have not run — a catalog census is not those,
  and the remaining probes return real host/group names, which is why the census used a
  catalog-only path; and the DC scope call is still the SME's. The per-DC extraction
  requirement those row counts drive is [[Idea-169]].

- **`Idea-167`** · 2026-08-24 · `[question]` · **parked → the company names the two extra catalog IRIs (re-read 2026-08-27: the entry says in terms that producer does nothing until the two ids are known, so the trigger is an answer, not a decision this side can take)** · prio? **Low** —
  **The company's `catalog` supplement declares two more terms than ours, and the gap is
  theirs, not producer staleness.** A company `apply-supplements` run reports
  base 47 / seal 15 / **catalog 24** / registry 4 / infrastructure 6; producer declares
  base 47 / seal 15 / **catalog 22** / registry 4 / infrastructure 6 — four of five match
  exactly, and `sosa` is correctly absent on both (opt-in). Producer has never held 24:
  `catalog_ontology_supplement.cypher` went 18 -> 22 at K6 (Product Cabinet, the ProductRole
  scheme) and has been 22 at every commit touching it since. Ports run one way, so the two
  extra terms are company-local catalog modelling. **Why it is worth a look rather than a
  shrug:** the whole point of G29's declared chain is that a term nobody declared is a
  loader MATCHing nothing — two undeclared-here terms are the mirror case, a real modelling
  addition that only one side has. **Ask:** name the two IRIs. If they are a genuine
  addition they are a `drydocs-review` BACK-FLOW candidate, alongside the two company-local
  supplements already tracked at `Idea-52` -> `G59`. If they are leftovers from a
  superseded shape, they want retiring on their side. Producer does nothing until the two
  ids are known — this is a question, not a defect.

- **`Idea-163`** · 2026-08-24 · `[chore]` · **open — NARROWED 2026-08-31 to the release call alone; the durability and doc-drift halves are DONE (see below), so what is left is one decision and no discovery** · prio? **Med** —
  **Has `[Unreleased]` earned a `v0.4.0`?** `pyproject.toml` still reads `0.3.0` while CHANGELOG
  `[Unreleased]` has accumulated everything since 2026-07-09 — the whole of Epics J/K/L/N/O/Q and
  the S-series module split among it. Cutting it means deciding the bump against VERSIONING.md's
  public surface (CLI contract, config schemas, active vocabulary terms), then running its ritual,
  whose step 5 is `git push origin main --follow-tags` — the step that never completed for
  `v0.3.0` and produced the orphan problem now closed. **This is a judgment call, not a task:**
  nothing is broken while it waits, and no agent should cut a release unasked.
  **What was resolved 2026-08-31, so nobody re-opens it:** (a) `v0.3.0` was pushed **as-is**, still
  pointing at `8645f81e`, on the user's ruling that the tag should record what actually shipped
  rather than be re-cut against post-squash history; (b) its target is reachable on `origin`
  because `archive/old-history-2026-07-20` (411 commits) was pushed alongside it, so the release
  record is no longer one disk failure from gone; (c) the third sub-item — VERSIONING.md citing
  `drydocs.backlog.v2` and the `backlog.yaml` tombstone — was fixed in `e0134168`, which also
  caught a pointer this entry never recorded: the graph-model surface named
  `relationship_vocabulary.yaml` as a file after S5 split it into per-domain fragments.
  **Ruled separately:** the third orphan line, `pre-scrub-20260804`, was NOT pushable as it stood —
  it carried `drydocs-20260804-1338.json` (blob `50b2dd6d`) with real Internal workbook values that
  the U9 off-by-one had leaked. Its fix commit had ruled that acceptable while the leak stayed in
  LOCAL history; pushing to a remote was held to be a different question. The line was rewritten
  without the file and pushed as `archive/prescrub-20260804-scrubbed`, verified at 0 matching
  blobs, and the unscrubbed original deleted on the user's instruction.
  **Not a port defect** — `git-readme.md` step 24 rules that the annotated tag does not cherry-pick
  and that the company keeps its own version string, so the company repo correctly has no `v0.3.0`.
  Surfaced while verifying a company-side port-close review, which correctly flagged the tag's
  absence on their main.

- **`Idea-162`** · 2026-08-24 · `[chore]` · **parked → a producer `DD` letter series is actually proposed (re-read 2026-08-27: nothing to do until then; the disposition is already recorded in the body so the choice cannot be made by accident, which is the only way it would be)** · prio? **Low** —
  **The company occupies `DD1`–`DD10` in the PRODUCER band, in a letter series this repo
  cannot see.** `DD1`–`DD9` predate the 2026-08-18 allocator partition and are
  grandfathered by the forward-only clause; `DD10` was minted 2026-08-24 — groomed from
  their correctly-banded `Idea-10000` — and landed at numeric 10, inside `1–9999`. Ports
  are one-way, so none of those ids ever reaches this tree and the only producer-side
  record of them is machine-local. **The hazard is ours, not theirs:** if this repo ever
  opens a `DD` series — `drydocs_deepdoc` is producer code and `DD` is the obvious slug —
  then `DD1` is a perfectly LEGAL producer-band mint that collides at the company's next
  `union-append`, which is the G70/G71 shape that already forced one renumber (and could
  not be settled by renaming, because `config/gate-log.md` cited the ids inside a
  SIGNED-OFF record). Renumbering their `DD10` does not close this — `DD1`–`DD9` stay.
  **Disposition when it arises:** open any producer `DD` series at a number no company id
  can reach, or pick another prefix. Nothing to do until such a series is proposed;
  captured so that decision is not made by accident, which is the only way it would be.
  **KEPT-UPDATED 2026-08-24:** a company session now describes their `Idea-10000` as "the one
  that groomed into **DD10001**", while this entry recorded that mint as **DD10** — numeric 10,
  inside the producer band — on the same day. Either the out-of-band id was renumbered after
  this was written, or the two numbers are being used interchangeably in conversation.
  **Unresolved from here:** ports are one-way, so this side cannot read their letter series.
  What does not change either way is the hazard above — `DD1`–`DD9` stay in the producer band
  regardless, so renumbering `DD10` would not close this entry. See [[Idea-170]] for the
  guard half of the same partition.

- **`Idea-154`** · 2026-08-21 · `[bug]` · **open — partially groomed → J52 (2026-08-22, the consequence half: the verify skill gains the session-launched-browser rule + recipe); the two-browser diagnostic that would prove the mechanism needs both machines in hand and stays the user's step** · prio? **Med** —
- **`Idea-204`** · 2026-08-29 · `[bug]` · **groomed → O83 (2026-08-30)** · prio? **Low** —
  **The console's bolt panel defaults its database to `neo4j`, so a fresh clone runs correct
  Cypher against the wrong database and gets zero rows.** `CypherConsole.tsx` reads
  `env.VITE_NEO4J_DATABASE ?? 'neo4j'`; every depgraph and Control-M surface lives in `drydocs`,
  and the home database is explicitly NOT part of the topology (the same drift that put stray
  sample loads in it until 2026-07-27). A machine whose `web/.env.local` sets the variable never
  sees this, which is why it has survived — the failure only reaches someone who copied
  `.env.example` and did not fill it, and it presents as an empty result rather than an error.
  Candidate fix is to default to `drydocs` rather than the driver's home database, since no
  surface this panel serves reads from `neo4j`.

- **`Idea-203`** · 2026-08-29 · `[chore]` · **groomed → G131 (2026-08-30)** · prio? **Low** —
  **`agents/.env` carries an empty `NEO4J_PASSWORD`, and only a falsy-check keeps the agent tier
  working.** The file is a filled-in copy of `.env.example` whose password line was left blank,
  per the agents README step. It works today because `common/neo4j_tool.py` merges the root
  `.env` with `if _value and not os.getenv(_name)`, and an empty string is falsy, so the root
  value fills the gap. The fragility is that the guard reads like a normal precedence rule while
  actually depending on that emptiness: rewrite it as a membership test and the blank line
  silently wins, giving the whole agent tier an empty password. Either clear the line so the
  merge has nothing to override, or make the guard's intent explicit in a comment.

- **`Idea-202`** · 2026-08-29 · `[idea]` · **groomed → O84 (2026-08-30)** · prio? **Med** —
  **A demo query that names a label the graph does not have returns `status: success, rowCount:
  0`, and nothing anywhere notices.** Found 2026-08-29 (desktop, `neo4jtest`, `drydocs`): the
  console's `C4 components (depgraph)` preset and the matching `DEFAULT_QUERY` in
  `agents/graph_query/agent.py` both queried `:CodeFile` / `DEPENDS_ON` / `relPath`, while the
  self-documentation-code-graph gate ruled `:CodeModule` (rejecting option (b) `:CodeFile`) and
  `IMPORTS`, and the loader writes snake_case `rel_path`. Both were fixed the same day, but the
  interesting part is the detection gap: the two call sites drifted from a SIGNED gate ruling,
  the unit suite stayed green, and the surface reported success. Worth deciding whether the
  gate-ruled labels should be generated or guarded rather than hand-copied into demo queries —
  the same generated-artifact-plus-drift-test shape already used elsewhere in the UI work.

- **`Idea-201`** · 2026-08-28 · `[bug]` · **groomed → J65 (2026-08-30)** · prio? **Med** —
  **snapshot.ps1's board refresh has been silently skipping on this desktop, and the warn-only
  catch is what hides it.** Observed at the O77 close, 2026-08-28: the step reports "board
  refresh skipped" followed by the first line of a traceback, which reads like noise; run the
  same command from PowerShell and the real error is ModuleNotFoundError for typer, raised from
  render_load_map.py. Cause is the known desktop VIRTUAL_ENV leak — the Claude Code shell
  pre-sets VIRTUAL_ENV to the agents venv, so poetry resolves the wrong environment; a Bash
  caller that unsets it succeeds and PowerShell inherits it and fails. Consequence is narrow but
  exactly the class the ritual exists to catch: the load-map surfaces never refresh from the
  snapshot on this machine, so a stale render there would not be noticed by the step meant to
  notice it. Two candidate fixes, and the second matters more than the first: have the script
  clear VIRTUAL_ENV before it calls poetry, and print the LAST line of a failed traceback rather
  than the first, so the warning names the module instead of the word Traceback.

- **`Idea-200`** · 2026-08-28 · `[bug]` · **groomed → O85 (2026-08-30)** · prio? **Med** —
  **The verify convention serves the console on port 5199, which has not been able to sign in
  since O69.** The API's CORS allowlist (`drydocs_api/app.py`, `create_app`) is
  `http://localhost:5173` and `http://localhost:4173` only, so a console served anywhere else
  gets a browser-blocked `/login` and the page falls back to the sign-in screen. The symptom
  names the wrong cause: the client reports "drydocs-api unreachable", because a CORS-blocked
  fetch and a dead server are the same rejection to `fetch`. Found while verifying [[O77]] on
  2026-08-28 — 5199 is the port the ui-tests ledger's own O65/O66 sources cite, and 5173 was
  already taken by another dev server, so verification ran on 4173. Worth deciding as one
  question rather than two: whether the allowlist should carry the verification port, and
  whether that error message should distinguish a refused connection from a blocked origin.

- **`Idea-199`** · 2026-08-28 · `[question]` · **open — user ruling, blocks the second half of the acronym stream** · prio? **Med** —
  **Where does a harvested acronym LAND — the graph, or the config glossary?** Split out of
  [[Idea-190]] at the 2026-08-28 groom so it is visible as a decision rather than buried in a
  promoted note. MM11 takes the extractor half (acronym candidates, with the sentence they were
  found in, into the mind-map state file), which is useful under either answer. This is the half
  that is not.
  - **Option A — graph nodes.** It becomes a real loader with a `LOADER_REGISTRY` row, and
    "loader" means what it means everywhere else in the repo. It also means minting a node label
    and an attaching edge, which is an ontology decision and goes through
    `docs/RELATIONSHIP_GUIDE.md`, the relationship-vocabulary registry and the HITL gate, with the
    mapping `planned` until confirmed.
  - **Option B — propose into the registry.** It lands in
    `config/taxonomy/software-registry.yaml` — today's durable home for the three committed
    entries — as a change artifact riding the path O68 clause (c) already describes. No new
    edge meaning, no gate; but "loader" would be the wrong word for it, and the graph never learns
    the acronym.
  - **The two answers have different modules, different guards and different gate exposure**, which
    is exactly why the groom would not pick. Whichever way it goes, it should settle the same
    provenance question O68 clause (d) forces from the other direction — two surfaces disagreeing
    about what makes an acronym trustworthy is worse than either gap — and a corpus-harvested
    acronym stays SYNTHESIZED and `:Uncertain` under both.

- **`Idea-198`** · 2026-08-28 · `[bug]` · **groomed → Y6 (2026-08-28)** · prio? **Med** —
  **"A claim ships NO render" is true for PULLING an item and false for MINTING one, and CLAUDE.md
  states it without the distinction — it turned CI red today.** The O75 claim commit
  (`49356d9a`) followed the pull rule as written, shipped no render, and failed the roadmap
  staleness guard: `test_committed_roadmap_page_matches_its_sources`, "stale beyond a status-only
  change".
  - **Why the rule holds in its intended case.** Y5's tolerance is for a STATUS-ONLY diff. Flipping
    an existing item `todo → in_progress` moves a value inside a row the roadmap already renders,
    the guard forgives it, and the claim sha stays green. That is the case the rule was written
    for and it still works.
  - **Why it does not hold here.** A claim that MINTS a new item adds a row that did not exist, so
    the roadmap's source fingerprint moves for a structural reason, not a status one, and the
    tolerance correctly does not cover it. The guard is right; the instruction is incomplete.
  - **The fix is one clause in CLAUDE.md §0**, not a code change: a claim on an EXISTING item ships
    no render; a claim that mints a NEW item ships the board and roadmap render with it. Worth
    stating because the failure is silent in the normal ritual — the item gets built, the next
    push carries the render anyway, and the red claim sha is only visible to somebody reading
    `gh run list` afterwards, which is precisely the "nobody was looking" failure Idea-111 already
    made a session step for.
  - **Not hypothetical.** `33214406376`, 2026-08-28, one failing test in a 2,388-test run.

- **`Idea-197`** · 2026-08-28 · `[idea]` · **merged → G81 (f)(g)(h) · G104 (the ADR's second requirement) · G109 (f) — all four proposals folded 2026-08-28, same day, same session** · prio? **Med** —
  **The catalog/lineage second pass proposes amendments to G81, G104 and G109 — they need a groom
  or they die in a design doc.** `docs/design/catalog-substrate-review.md` (Rev 1) read DataHub,
  OpenMetadata, Amundsen and OpenLineage/Marquez in depth plus Microsoft Purview for concepts,
  against the two questions the SaaS-scaffold pass could not answer. It produced six proposals, all
  landing on items that already exist, none applied.
  - **G104 (ADR 0014).** Record the three-part-key ceiling: DryDocs derives
    `urn:drydocs:dataset:(carrier,artifact,prod)` and DataHub's identical key could not hold two
    deployments of one platform, forcing the `platform_instance` retrofit across every source. The
    `[db]` redaction placeholder in our committed ids IS that instance coordinate. The ask is a
    paragraph naming the ceiling, not the axis itself.
  - **G104 again.** Bind per ORIGIN, not per dataset — OpenLineage's namespace/name split maps
    exactly onto `origin@db.schema.table`, so fifteen automated datasets reduce to about six
    origins. And reference env vars from committed YAML rather than reading them in Python, the
    DataHub recipe pattern.
  - **G81.** Widen clause (b) beyond the three named path families to the full origin set, and
    implement clause (d)'s no-silent-default-root as ONE expansion function rather than per module.
  - **G109.** Clause (a) names six undeclared code zones; the real gap also includes all fifteen
    `acquisition.mode: automated` datasets, which resolve through nothing and which
    `drydocs landing-zones --check` cannot see. Widen, or record why the automated half is out.
  - **Why it was stated as a proposal first.** Each is an amendment to a `todo` item's ruled
    acceptance, which is a change of scope on work this session was not pulling. The review stated
    them so the user could rule rather than a design doc silently rewriting three items. **The user
    ruled the same day: fold them in.** Done — G81 gains clauses (f), (g) and (h); G104 gains a
    second stated requirement on the ADR rather than acceptance clauses of its own, because a
    survey can change what a decision must ADDRESS and never what it concludes; G109 gains clause
    (f). No existing clause was rewritten in any of the three.

- **`Idea-196`** · 2026-08-28 · `[idea]` · **groomed → O76, BUILT same day** · prio? **Med** —
  **The credential store cannot tell a generated demo secret from a chosen operator one, so no
  surface can say "rotate this."** `admin_demo_login.py --generate` invents a secret and prints it
  once — defensible for a synthetic account on localhost, and the docstring argues it correctly.
  But nothing records that it happened. `--list` and `--status` show only which ids have a
  credential, so an account carrying a secret that was printed to a terminal weeks ago looks
  identical to one set by hand at a no-echo prompt.
  - **The fix is small and the format already anticipates it.** The credential entry gains
    non-secret metadata, `origin: generated|prompted` plus `set_at`, and `FORMAT_VERSION` goes to
    2 — the file already refuses a version it does not know, so the migration path exists.
  - **Where it came from.** DataHub's documentation spends a page warning that its shipped
    `datahub:datahub` account survives deleting the user in the UI. DryDocs ships no credential at
    all, which is the stronger default, but `--generate` reintroduces a small piece of the same
    problem: a credential nobody chose deliberately and nobody is tracking.

- **`Idea-195`** · 2026-08-28 · `[bug]` · **groomed → O75, BUILT same day (`36a7422a`); rotation stays out of scope by O75 clause (f) and needs a per-identity generation stamp the credential file does not carry** · prio? **High** —
  **Removing a console credential does not end that account's live sessions — access continues for
  up to eight hours.** `InMemorySessionStore.revoke(token)` is token-scoped and driven by logout.
  `resolve(token)` checks the token and its expiry and never consults the credential store again,
  and `ReloadingCredentialStore` is read only by `handlers.login`.
  - **The sequence.** `morpheus` signs in and gets an 8h session. The operator runs
    `set_console_credential.py --remove morpheus`, or rotates the secret because it leaked. The
    file changes, the API picks it up on the next login attempt, and the already-issued admin token
    keeps resolving until its TTL runs out. The operator has every reason to believe access was
    withdrawn.
  - **The shape of the fix, which O73 already established.** `resolve` compares the session's
    `persona_id` against the credential store's current identities, so a removed account's token
    stops resolving on the next request through the same stat-based reload that already runs. The
    bootstrap script cannot revoke directly — it does not share a process with the API, and giving
    it one would violate the guard that keeps writes out of `drydocs_api`.
  - **Rotation is the harder half and can be deferred with a reason.** A rotated secret leaves the
    identity present, so identity comparison does not catch it; that needs a credential generation
    counter or a per-identity stamp. Removal is the case an operator will actually rely on.
  - Found by the second-pass review, `docs/design/catalog-substrate-review.md` finding L3.

- **`Idea-194`** · 2026-08-27 · `[idea]` · **open — re-read at the 2026-08-28 groom and NOT promoted: which layer is templatable at all is a user ruling, and the entry says so itself** · prio? **Med** —
  **Copier is the mechanism the standalone-template goal has been missing — a template that can be
  UPDATED in place after generation, not just generated once.** Noticed while reviewing
  `serious-scaffold/ss-python` for web scaffolding (`docs/design/web-scaffolding-review.md`); it is
  the one piece of that project worth more than the tooling it ships.
  - **The goal it serves.** A standing long-term aim is to turn DryDocs into a sanitized standalone
    template another organization can implement. Every sanitization decision, every placeholder,
    every `[seal-id]` and `[db]` in the registry already pays into it. What has never been decided
    is HOW a downstream copy would be created, or what happens to it afterwards.
  - **Why the update property is the whole point.** A one-shot generator (cookiecutter) hands
    someone a copy that diverges from the day it is made — which is exactly the producer-to-company
    divergence this project already manages by hand, with port prompts, a manifest, and a ledger.
    Copier can re-apply template changes to an already-generated project, so downstream copies could
    pull improvements instead of drifting. That is a different relationship than the one the
    cross-repo port models, and it is worth knowing whether it is the better one.
  - **The honest counter-argument, so it is not discovered later.** Most of what makes DryDocs
    useful is CONTENT, not scaffolding — the ontology, the registries, the gate corpus, the
    vocabularies. A template can carry the shapes and the guards; it cannot carry another
    organization's Control-M estate. So the question is not "should we be a Copier template" but
    "which layer is templatable at all", and that is a ruling, not a task.
  - **Not an item on purpose.** This is a direction to decide, not work to schedule. If the answer
    is yes, it reshapes how the repo is laid out; if no, the sanitization work stands unchanged and
    loses nothing.

- **`Idea-193`** · 2026-08-27 · `[bug]` · **groomed → Z8 (2026-08-28)** · prio? **Med** —
  **The Z1/Z3 and Z5 fixtures were each built correctly and do not interlock, so the bundled
  demo can only ever fill one of the map's three dimensions.** Found by running the whole Z3
  chain on the desktop for the first time (`neo4jtest`, `drydocs` DB, 2026-08-27) to see why the
  Locations tab drew nothing. The chain itself is fine — constraints applied, the infrastructure
  supplement verified 6/6, the loader took 5 rows / 0 rejected first try, and its coverage
  counters reported every gap honestly rather than hiding one. The gaps are all in how the three
  sample files reference each other, and each one silences a different dimension:
  - **Servers dimension — 2 of 5 rows cannot be placed.** The Z3 export fixture uses the
    synthetic cities Sampleville and *Modelton*; the Z5 gazetteer seeded Sampleville and
    *Otherton*. Two items independently invented a second synthetic city and picked different
    names, so the DR rows resolve to nothing. Fix is one gazetteer row — pure classification,
    guarded, no gate.
  - **Jobs dimension — permanently empty.** The Control-M sample hosts are host-hldm-02/03 and
    host-auto-01/02; the server export names are srv-synth-01..03 and srv-synth-51/52. The signed
    T1/T2 tiers are exact and normalized-short-name, so those two sets can never join, and the
    resolution pass correctly reported 4 of 4 hosts UNMATCHED. Nothing is wrong with the tiers —
    the fixtures were simply never written to meet.
  - **Teams dimension — permanently empty.** The export names business application 70055; the
    graph carries 70051-70053. The technology-port leg is MATCH-only by gate ruling, so it minted
    nothing and counted apps_unmatched 1, exactly as designed.
  - **Why this matters beyond the demo:** every one of these is the shape of a real coverage gap,
    so the bundled samples, run together, exercise the reporting path and never the success path.
    CORRECTED same day: the T1 tier IS proven — tests/integration/test_server_inventory_e2e.py
    seeds its own :ExecutionHost matching a fixture server and asserts the exact match, so the
    claim that no test proves the tiers fire was wrong. What no sample proves is the DEMO path,
    where the Control-M sample's hosts meet the server export without a test seeding the join for
    them. Cheapest order: gazetteer row, then align the export's host names and app id with the
    Control-M sample (and update the e2e's seeded host with them).
  - **Related:** the Z5 index defect fixed the same day (`ae740be5`) was load-bearing here — with
    it unfixed, all five servers would have been unplaceable and a successful load would still
    have drawn an empty world.

- **`Idea-192`** · 2026-08-27 · `[question]` · **open — the mandate question is ANSWERED (not mandated, preferred); the residue is conditional on Salt ever being costed, so nothing was promoted at the 2026-08-28 groom** · prio? **Low** —
  **Salt DS as a SECOND UI track: the standing open question is answered, and the only substantive
  assessment we ever wrote is not in the working tree.** Raised at a 2026-08-27 review of what the
  repo documents about the company design system (`@salt-ds/core`, Apache-2.0, public).
  - **USER RULING 2026-08-27 — Salt is NOT mandated company-side. "Preferred" is the accurate
    word.** This closes the make-or-break input that a cost estimate was blocked on: a preference
    is a design argument, a mandate would have been a schedule constraint. Any future Salt work is
    therefore an OPTION to be costed on its merits, not an obligation to be planned around. Record
    it here because the question was previously unrecorded and a later session would re-ask it.
  - **Do not repeat the counterexample.** An earlier draft of this review argued Salt is "not
    demonstrably universal internally" from `internal/context-graph-analysis/ui-architecture-analysis.md`
    section 3.4, which records one internal application using no component library at all. The user
    ruled that a badly chosen example: one incubator application's stack says nothing about the
    estate, and the inference does not follow. The ruling above stands on its own; the 3.4
    observation is a fact about that one application and nothing more.
  - **The evidence problem.** Every Salt mention now on disk is a one-line "dropped" note —
    `IDEAS.md` (the 2026-07-17 decision line), `site-plan.md` sections 1 and 6,
    `claude-design-ui-prompt.md` (listed under *superseded, do not follow*),
    `backlog/epics/web-console.yaml`, `items/O8.yaml`, and a comment on the ReUI row in
    `config/taxonomy/software-registry.yaml`. The ONLY substantive assessment ever written —
    version and license, density modes, the AG-Grid pairing, the not-Tailwind and
    aesthetically-opposite findings, the library-agnostic-shell mitigation — lives in git history at
    commit `f9d0b2d0` (2026-07-17), consumed at groom `ea1a4554` and compressed to a one-liner.
    This is the second time a Salt fact has had to be recovered from history rather than read from a
    doc. If Salt is ever costed, that content is the starting point and it should be lifted back
    onto disk first.
  - **What a cost estimate still needs, if this is ever picked up** (the seam itself is sound —
    `web/src/layout/shellConfig.ts` is the one typed layout config, and `layout-anatomy-checklist.md`
    holds the zone decomposition, so a skin swaps components, not structure): a structure-only Salt
    crosswalk in the same shape as `layout-anatomy-checklist.md`, covering (a) our seven
    `components/ui/` primitives plus the five shell zones mapped to Salt equivalents and gaps,
    (b) a ruling on whether a Salt track keeps Tailwind for layout or drops it — the coupling is
    1,167 `className=` sites across 65 files and this single decision is the largest term in the
    estimate, (c) a token-mapping test against the `ui-conventions.md` status table, and (d) an
    offline/internal-registry install check against site-plan section 1's "no external requests of
    any kind" intranet constraint, since Salt is a versioned npm dependency. The Kept Orbit brand
    constraint is the open design risk: Salt's aesthetic was called opposite to the dark-schematic
    spec and nobody has tested whether Salt theming can carry the brand.

- **`Idea-191`** · 2026-08-26 · `[idea]` · **open — NOT groomable: both readings mint ontology, so the first step is the three-clause gate question the entry states, not a build item (re-read 2026-08-28)** · prio? **Low** —
  **A per-column checkbox on a grid that promotes that column into a label node and lands it in the
  unstructured context graph.** Raised by the user 2026-08-26 alongside [[Idea-190]]. The appeal is
  clear and it is the right instinct for **layer 4** (CLAUDE.md's context graph — the layer that
  answers *what matters right now for this task*, and the one still marked future): a grid column IS
  a dimension a reader has just decided is meaningful, and ticking it is the cheapest possible way to
  say so. The obvious home is the column header of the grids that already exist —
  `routes/DomainGridTable.tsx` and `explorer/SpecGrid.tsx`, which now share a header-button idiom.
  - **IT COLLIDES WITH TWO STANDING RULINGS, and that is the whole reason to write it down rather
    than build it.** (1) **The UI may not write the graph.** Gate `ui-write-surface` (O20, signed
    off 2026-07-21) ruled M3 direct write **REFUSED STANDING** and C4 admin edits **NEVER**; every
    console drafting surface produces a change ARTIFACT that travels git to gate to loader, and the
    loader stays the only graph writer. (2) **The uncertain realm has a closed writer list.**
    `tests/unit/test_uncertain_boundary.py` pins `UNCERTAIN_WRITERS` to exactly
    `drydocs_deepdoc` and `agents/common/agent_run_writer.py`, with the comment stating outright
    that adding an entry there *is a ruling, not a convenience* (gate `document-content-topology`
    §F / ADR 0011 clause 1). A checkbox that writes into the context graph asks to become the third
    entry on that list, from the browser.
  - **So the viable shape is almost certainly PROPOSE, not CREATE:** the checkbox drafts a
    proposal — column, its distinct values, the spec or domain it came from, and a rationale — into
    a tray, and that becomes an artifact a loader applies after review. Same mechanism as the
    /mappings changeset and the acronym add path backlog O68 describes. Worth checking whether one
    drafting mechanism can serve all three rather than growing a third.
  - **"LABEL NODE" NEEDS DISAMBIGUATING BEFORE ANY BUILD.** A *tag node* is a node that exists to
    group things, attached by an edge; a new *node label* is a schema-level addition. **KEPT-UPDATED
    2026-08-26 (user ruling): EITHER reading needs an ONTOLOGY REVIEW — the tag/label distinction
    does not buy a cheap path, and this entry originally said it did.** The correction matters
    because the earlier framing (a tag node "is data, and rides the normal proposal path") is
    exactly the sentence that would license someone to build it without a gate. It does not hold: a
    tag node still has to answer *what label does this node carry* and *what edge attaches it to
    anything*, and a new relationship type goes through `docs/RELATIONSHIP_GUIDE.md`, the
    relationship-vocabulary registry (`drydocs_core/ontology/relationship_vocabulary/`) and the HITL
    gate — never invented during import (CLAUDE.md §6). So there is no "just data" branch here;
    both readings mint ontology, one at the instance grain and one at the schema grain, and both go
    through review with `status: planned` set first.
  - **FILED Low, and the reason is readiness rather than merit:** nothing depends on it, and it
    cannot be built at all without at least one ruling — possibly two. It should not sit in the
    ready-to-pull strip competing with work that has no such precondition. The honest first step is
    not a build item but a gate question, and it is now THREE clauses in a deliberate order:
    *(a) what label and what attaching edge would this mint, and does the ontology admit them?*
    then *(b) may a console surface DRAFT a context-graph node proposal?* then *(c) does the
    uncertain writer list extend to whatever applies it?* (a) comes first because if the ontology
    does not admit the label and the edge, there is nothing for (b) and (c) to be about.

  Mechanism-only; no real column values or company data land in a tracked file.

- **`Idea-190`** · 2026-08-26 · `[idea]` · **groomed → MM11 (2026-08-28) — the EXTRACTOR half only; the destination fork (graph nodes vs config-glossary proposal) is re-filed as [[Idea-199]] and stays the user's** · prio? **Med** —
  **Deepdoc meets acronyms all over the corpus and has nowhere to put them — expand that capture
  into an acronym LOADER that feeds the surface backlog O68 specifies.** Raised by the user
  2026-08-26, right after O68 was filed: O68 gives acronyms a readable surface and a MANUAL add
  path, and this is the automated feeder for it. The investigation the deepdoc design doc records
  is exactly the situation that produces acronyms — one evening crossing email, the Control-M
  client, Jira, Bitbucket and Confluence, every one of them dense with internal shorthand — and the
  analyst's mind map is where those meanings currently get written down and then lost with the
  session. **Checked before filing, and it is the sharp end of this entry: `acronym` appears
  NOWHERE in `docs/design/deepdoc-data-flow-overview.md` or `drydocs_deepdoc/`.** The capture is
  informal today; there is no field, no slot and no output that holds one. **MM3 is the natural
  seam** — it builds the mind-map state file (`drydocs.deepdoc.mindmap.v1`) AND the shared entity/ID
  extractor in `drydocs_core`, and that extractor's enumerated token classes (application-id tokens,
  issue keys, folder-name positional tokens via the PRAOCG decode, table names, distribution-list
  names, GUIDs) do NOT include acronyms. So the concrete ask splits in two: add acronyms as an
  extracted class, then give the result somewhere to land.
  - **THE FORK TO DECIDE, not to default:** where does a loaded acronym go? Today the durable home
    is `config/taxonomy/software-registry.yaml` — a CONFIG glossary, not the graph — so "loader" in
    the repo's usual sense (the only graph writers) may be the wrong word for it. Either it lands as
    graph nodes and becomes a real loader with a `LOADER_REGISTRY` row, or it proposes into the
    registry and rides the change-artifact path O68 clause (c) already describes. Both are
    defensible; picking silently is not.
  - **TRUST IS NOT OPTIONAL HERE.** Deepdoc output is corpus-derived, so a harvested acronym is
    SYNTHESIZED and carries the `:Uncertain` discipline (ADR 0006 corpus-consumer ruling, ADR 0011,
    `tests/unit/test_uncertain_boundary.py`). It must never become indistinguishable from the three
    SME-supplied entries committed today. That is the SAME fork O68 clause (d) already forces about
    provenance, reached from the other direction — whichever item lands first should settle it for
    both, because two surfaces disagreeing about what makes an acronym trustworthy is worse than
    either gap.
  - **An acronym also has a shape the other extracted classes do not:** it needs the SENTENCE it was
    found in, not just the token. `SNOW` is only useful because someone wrote down that it means
    ServiceNow and explicitly NOT Snowflake, and that distinction lives in prose, not in the token.
    Expect the candidate record to carry the surrounding evidence span, which the extractor's typed
    matches-with-spans design already supports.

  Sibling of backlog O68 (the surface and the manual add), and depends on MM3 for the extractor.
  Mechanism-only; no real acronym values from any company corpus land in a tracked file.

- **`Idea-189`** · 2026-08-26 · `[bug]` · **groomed → O78 (2026-08-28, depends on O77)** · prio? **Med** —
  **`MiniDag` never adopted the O66 `RelEdge` overlay, so relationship names still render BEHIND
  the nodes on FIVE routes.** O66's acceptance says the fix is one component so that "one future
  change fixes all three", and `components/RelEdge.tsx` says the same in its header comment — but
  the three canvases that adopted it are explorer, lineage and ownership. `components/MiniDag.tsx`
  was never migrated and still uses React Flow's built-in SVG `label` / `labelStyle` /
  `labelBgStyle` props (`MiniDag.tsx:108-111`), which paint in the EDGE layer and therefore stack
  below nodes — the exact treatment `RelEdge`'s comment names as the defect. Observed live
  2026-08-26 on `/docs` (desktop, Vite :5173, this branch): the `DESCRIBES` edge into
  `BMC Control-M` renders as the two letters `ES`, the rest hidden behind the `#1 What is a job?`
  node. **Blast radius is five routes, not one** — `MiniDag` is rendered by `DocsRoute`,
  `GatesRoute`, `RemediationRoute`, `RunbooksRoute` and `SoftwareRoute`, so every one of them
  carries the defect O66 rated p1 on a single page. Filed Med rather than High only because each
  MiniDag map loses SOME names rather than all of them, unlike [[Idea-188]]; raise it if the
  console is about to be demonstrated. Migrating `MiniDag` to `RelEdge` is the obvious move and
  makes the "one component" clause true for the first time — but do it AFTER 157, or it inherits
  157's inverted occlusion on all five routes at once. Rendering only; no edge meaning moves.

- **`Idea-188`** · 2026-08-26 · `[bug]` · **groomed → O77 (2026-08-28) — filed as a NEW item, not a reopen of O66; the missing acceptance clause travels in O77 clause (b)** · prio? **High** —
  **O66 is `done` but the defect came back inverted: `/ownership` now paints the relationship
  chips ON TOP of the node boxes, so the NODE names are the unreadable half.** O66 fixed
  "labels behind nodes" by moving the label into the `EdgeLabelRenderer` portal with an explicit
  `zIndex: 10` (`RelEdge.tsx`), which does put relationship names above the node layer — its
  acceptance genuinely holds. What the acceptance never said is that node names had to stay
  readable too, so trading one occlusion for the other passed it. Observed live 2026-08-26
  (desktop, Vite :5173, this branch, both the `Rollup (K4 shape)` view and after `fitView`):
  every node in the chain is clipped by the chip of the edge leaving it — `LOB-R (synthetic`,
  `edger Services (line)`, `Ledger An...`, `...Platforms (ToT)`, `Team N...`, and the
  `BusinessApplication` kind line reduced to `inessApplication`. Cause is geometric, not a
  z-order mistake: `demoOwnership.ts` places the chain at fixed x/y close enough that each
  straight edge's MIDPOINT lands inside the neighbouring node box, and `RelEdge` puts the chip at
  that midpoint. **So the fix is not another z-index pass — whichever layer wins, the other is
  unreadable.** Remove the collision instead: offset the chip off the midpoint where it would
  intersect a node rect, or space the chain so midpoints fall in the gaps. **Reopening O66 rather
  than filing fresh is the groomer's call**, but note its acceptance needs the missing clause
  (node names readable too, in both themes) or the next attempt can pass it the same way.
  **RULED OUT at capture, so nobody re-derives it:** wiring the greyed-out `Layout` / `Fit` /
  `Refresh` / `Export` toolbar buttons does NOT fix this. They are not disabled React Flow
  controls — `ToolbarButton` (`routes/ModuleTemplate.tsx:83-90`) takes only `label` and
  `disabled` and has no `onClick` and no handler anywhere, so enabling them yields four buttons
  that do nothing. And none of the four acts on paint order even if implemented: `Fit` is
  pan/zoom and scales nodes and labels together so relative overlap is unchanged (proven live by
  clicking React Flow's own fit control on `/docs` — the clipped `DESCRIBES` stayed clipped, and
  both panes already call `fitView` on mount), `Refresh` re-fetches the same positions, `Export`
  does not touch the screen, and only `Layout` could even mitigate, by spacing nodes rather than
  by changing the stacking rule. Sibling of [[Idea-189]], which is the same defect uninverted on
  five other routes. Rendering only; K4's attribution shape is gate-confirmed and does not move.

- **`Idea-153`** · 2026-08-21 · `[idea]` · **groomed → MM1–MM10** · prio **High** —
  **Deepdoc leaves the placeholder: the per-data-flow overview record, grounded in one
  production deep-dive.** A support thread (daily pre-processor failing on an API pull) was run to
  ground by hand across the Control-M client, Jira, Bitbucket, Confluence and a chat assistant; the
  48-frame session is transcribed verbatim machine-local
  (`internal-local/deepdoc/2026-08-20-session-1/transcripts/*-capture.md`) and synthesized
  mechanism-only in `docs/design/deepdoc-data-flow-overview.md`. Findings: the job name token
  cannot tell an API pull from a pushed file (the FileWatchers watch files the predecessor wrote on
  the same host — R13's second consequence); the Control-M Output tab carries what CMDLINE cannot
  (launcher job KIND, provenance GUID chain, landing prefix, compute target) = iteration 2 of the
  launcher contract; collaboration-type Jira projects have no application binding, so Jira is a
  signpost and Bitbucket commit-inspect is the code anchor; the owning team's Confluence space held
  nothing while the producer's space held the feed register — which documents the LEGACY file feed.
  Three grains already exist unreconciled (`%%DATAFLOW`, `:AppDataFlow`, the runbook "data series"
  traversal); the record keys on `%%DATAFLOW`. Groomed same day into the new epic MM (mind-map).

- **`Idea-142`** · 2026-08-20 · `[bug]` · **closed → J51 DONE 2026-08-20 (six rows landed, same day it was groomed (2026-08-20, desktop, at the port review — the caa0406 report named five more paths; F4 status-direction ruled same day into the entry_rule + ADR 0013)** · prio? **High** —
- **`Idea-141`** · 2026-08-20 · `[idea]` · **open — architect review DONE 2026-08-20, verdict: do-not-recommend as framed; the “worth doing regardless” residue groomed → G110 (2026-08-21); the four open questions stay the user’s** · prio? **Low** —
  **Should `agents/` stop carrying its own venv + `requirements.txt` and become an optional
  poetry group (`poetry install --with agents`), matching `[tool.poetry.group.api]` and
  `[tool.poetry.group.remediation]`?** Raised 2026-08-20 when the Ask spoke would not answer and
  the documented launch path turned out to be `pip install -r agents/requirements.txt` rather
  than poetry. **Reviewed the same day; the answer is leave it alone** — recorded here rather
  than groomed into an item, because the reasons are worth keeping even though nothing is owed.
  - **No ADR rules the split.** `docs/decisions/` contains nothing on venvs or poetry groups;
    ADR 0007 names `agents/` as the Q&A app's home and is silent on packaging. The authority is
    prose only — `agents/README.md:5-7`, `agents/requirements.txt:1`, `MODULE_MAP.md:100,158`.
    So this needs no ADR to reverse: it is a lighter change than it looks, which is exactly why
    the reason NOT to make it should be written down.
  - **The README's stated reason does not hold as written.** "its own venv so the agent runtime
    can be profiled/leak-tested in isolation" describes PROCESS isolation, and `adk api_server`
    is a separate OS process under either scheme (`agents/README.md:43-46` — memray on the ADK
    process, DevTools on the React page, `docker stats` on Neo4j). Installed-but-unimported
    packages cost a memray profile nothing. The rationale is real but mislabelled as a
    dependency concern.
  - **The reason to leave it alone is the PORT, not the venv.** `pyproject.toml` merges
    per-entry as a union of dependencies keeping the consumer's version string
    (`PORT-MANIFEST.yaml:151-155`), so the group itself would land cleanly — but `poetry.lock`
    carries "re-lock after the merge instead" (`:679-681`), which would oblige the company side
    to resolve `google-adk` and `litellm` on its internal index at every port. Today that choice
    is quarantined inside `agents/**`. ADK is only "the OSS base of the company-internal Fusion
    SmartSDK" (`agents/README.md:4`) — the consumer may not install `google-adk` at all, and
    whether it can reach it is unanswerable from this repo.
  - **Three resolver hazards, if anyone revisits.** Optional groups are not separate resolution
    universes — `poetry lock` solves all groups into one lock. (1) `click = ">=8.0,<8.2"`
    (`pyproject.toml:18`, held down by `typer ^0.12`) against whatever click the ADK/litellm
    tree wants. (2) `python = "^3.11"` spans up to 3.14 while litellm's tokenizers/tiktoken tree
    commonly caps below it. (3) `neo4j = "^5.20"` would silently DOWNGRADE the agent runtime,
    which today resolves driver 6.x from the bare `neo4j` line in `agents/requirements.txt:5` —
    the sleeper, since that runtime is the one being leak-tested. Poetry also has no
    `--only-binary` equivalent, so the documented Windows litellm wheel-only workaround
    (`agents/README.md:25-27`) cannot be expressed; a hard pin is the only substitute.
  - **MEASURED 2026-08-20 — two of those three hazards are now confirmed, not predicted.**
    The agents venv was built the same session (Python 3.14.6, `pip install --only-binary :all:
    -r requirements.txt`, clean) and what it resolved settles two open questions without a
    `poetry lock --dry-run`: **`click 8.4.2`**, against `pyproject.toml:18`'s
    `click = ">=8.0,<8.2"` — so hazard (1) is a HARD CONFLICT, not a maybe, and it cannot be
    resolved without moving `typer ^0.12` too; and **`neo4j 6.2.0`**, confirming the agent
    runtime genuinely runs driver 6.x today, so hazard (3)'s silent downgrade to `^5.20` is
    real. Hazard (2) did NOT materialise: `litellm 1.97.0`, `tokenizers 0.23.1` and
    `google-adk 2.7.1` all had cp314 wheels, so `python = "^3.11"` reaching 3.14 is currently
    survivable — with the caveat that pip picked those versions freely, which is exactly the
    freedom a shared lock removes. Net: the verdict is unchanged but better founded — the
    click pin alone blocks the group as framed.
  - **Worth doing regardless of the verdict.** (a) `MODULE_MAP.md:158` is WRONG today: it says
    `agents/` is absent from the boundary test, which `tests/unit/test_module_boundary.py:38`
    (agents in `PKG_ROOTS`) and `MODULE_MAP.md:100` both contradict. (b)
    `agents/requirements.txt:5` is a bare `neo4j`, so the agent runtime's driver version is
    unpinned and unreproducible — pin it where it already lives, no group needed; same for
    `litellm`, whose known-good version is recorded in README prose but nowhere a tool reads.
  - **Open questions that would flip this to recommend:** does the company side install
    `google-adk` or SmartSDK, and can it reach those distributions? Is the agent runtime meant
    to stay on neo4j driver 6.x (if yes, the group is impossible without loosening
    `neo4j = "^5.20"` repo-wide)? Is "one machine holds the only agents venv" permanent, or is
    broad agent-dev access the goal?

- **`Idea-140`** · 2026-08-19 · `[source]` · **merged → G68 census (e) (2026-08-19, the measurement half: wrapper fan-out + per-wrapper varying parameters); the informatica-kind RULING stays parked → the lineage gate (G12's inboxed m3_invokes to_node broadening)** · prio? **Med** —
  **Informatica invocations are the same generic few `.ksh` wrappers for ALL business
  applications on that platform — script-path identity is non-distinguishing, which is
  the G12 wrapper-payload problem arriving on a third platform.** SME direction
  2026-08-19 at the K16 two-source session. G12 already ruled this shape for two kinds:
  Ab Initio and DPL invocations land on `:ETLProcess` keyed on a kind-scoped stable
  token (pset/graph basename; pipeline GUID) with the path kept as a property, never
  identity — because the invoked path is a wrapper and the real identity is in the
  parameters. Informatica is the same family: every business application's Control-M
  jobs invoke the same handful of generic shell wrappers, so `m3_invokes` targets
  would converge on a few shared `:Script` nodes that distinguish NOTHING — while the
  actual identity (interface name, source-system code, package id) rides the folder
  variables (worked example in doc 09's two-source section, captures in the data
  root). Candidate ruling for the next lineage gate/groom: an `informatica` kind in
  the G12 classification with its own kind-scoped token derived from the invocation
  parameters — and the open question of WHICH parameter(s) are identity-grade is
  exactly the kind of thing the G68 folder profile can measure before anyone rules.
  G12's own close note already inboxed the `m3_invokes` to_node broadening question;
  this entry adds the third kind and its evidence.

- **`Idea-139`** · 2026-08-19 · `[idea]` · **groomed → J50 (2026-08-19, same session)** · prio? **Low** —
  **`gates.json`'s `unblocks` edge is a MENTION SCAN, and this repo already knows that is
  not good enough — it fixed the same class one edge over.** `scripts/render_gates.py`'s
  `unblocks()` serialises each backlog item to JSON and matches the gate slug anywhere in
  it, so **any prose citation of a gate becomes a dependency edge**. Found by causing it:
  writing K23's runbook-baseline note, which HANDS INFORMATION TO the
  `document-supersession` gate, made that gate read as though it *unblocks* K23. In this
  one case the edge happens to be defensible (the runbook replacement really does need the
  `SUPERSEDES` edge signed), which is exactly what makes the pattern worth recording rather
  than the instance — a heuristic that is right by luck is still a heuristic. **The repo
  has already ruled this distinction for the other direction:** the same function's caller
  carries `# J28: only an entry ABOUT the gate closes it -- a citation never does`, and
  `section_accounts_for()` implements it. So "about vs citation" is a solved problem here
  for gate-log sections and an unsolved one for backlog items, in adjacent lines of the
  same file. **The cheap fix is probably a declared field rather than better matching** —
  an item that genuinely waits on a gate could say so (`gates: [document-supersession]`)
  and the scan could stop guessing; that also makes the edge visible in `backlog.yaml`
  where a reader is, instead of only in a generated surface. Worth checking how many
  current `unblocks` edges are citations before spending anything: if it is one or two, a
  note is enough.

- **`Idea-132`** · 2026-08-18 · `[source]` · **groomed → N16 (2026-08-19) — the `source_label` enum question ONLY; the re-sourcing record itself STAYS STANDING, because nothing is owed producer-side today and it is what a future build must read** · prio? **Med** —
  **The ServiceNow extracts are being re-sourced INTERNALLY: hand-pulled CSV/YAML → SQL
  against the Snowflake replica views. SME note 2026-08-18.** Today every ServiceNow-derived
  load is a hand pull exported to CSV/YAML and then loaded; nothing queries the replica
  directly. That is changing company-side — each hand-built extract becomes a SQL file, the
  loader's `source_label` flips `csv`/`yaml` → `snowflake`, and an overlay rebinds each
  dataset onto the replica.
  **NOTHING IS OWED PRODUCER-SIDE TODAY** — there are no `snow_*` loaders here and the only
  registered ServiceNow datasets are `snow:cmdb-ci-classes` and the `snowflake:` placeholder.
  This is recorded because it changes what a FUTURE producer-side build should target, and
  because two of the pieces are already scheduled: [[G100]] (the ITSM technician-group gate)
  must build its lookup against the sourced feed, not against a CSV shape that is being
  retired underneath it.
  **THE GRAMMAR IS ALREADY RULED AND SHOULD NOT BE RE-DERIVED.** `config/source-registry.yaml`
  (the `snow` system row) states it: ServiceNow → Snowflake replica → `snow@[db].[schema].<table>`,
  origin stays `snow` with Snowflake as the CARRIER — the same shape as Control-M read from the
  Oracle replica. And the naming rule is explicit: **name the dataset for the ServiceNow TABLE,
  never for the `V_`-prefixed view wrapper.** The replica host, database and schema are Internal
  and stay company-side.
  **WHAT IS AND IS NOT A MODEL CHANGE:** the row models are unchanged — the SQL aliases columns
  onto the existing field names — so this is a SOURCE swap, not a re-shape. Two areas ARE
  net-new and have never been built: per-CI TOM responsibilities (a scoped-app extension table
  resolved to application/deployment) and incidents. Each is a new graph shape and needs its own
  HITL gate before any load, not a loader bolted onto this swap.
  **ONE KNOCK-ON WORTH DECIDING WITH IT:** `source_label: snowflake` would be another value
  outside the declared `'csv' | 'oracle' | 'agent' | 'human'` enum in `drydocs/loaders/base.py`
  — 12 of 28 loaders are already outside it and nothing enforces it. Re-sourcing is the natural
  moment to rule what that field means rather than adding a thirteenth exception.
  **KEPT-UPDATED 2026-08-18:** the ACQUISITION half of this entry now has an owner — Idea-133 groomed to [[N12]] (a declared `acquisition:` block per registry dataset row, so this swap becomes a `mode: manual` → `automated` flip rather than prose in `notes:`) and [[N13]] (the gate prompt ruling that flip once, with O24/K9's override→source-corrected flip). The `source_label` enum question is UNTOUCHED and stays open here.

- **`Idea-129`** · 2026-08-17 · `[bug]` · **closed 2026-08-17** · prio? **Low** —
  **The depgraph snapshot JSON was written CRLF — the surface Idea-121 did not reach.
  FIXED, and the guard Idea-121 asked for now exists.** Measured before:
  **31,505 CRLF / 0 bare LF**; after: **0 / 31,505**.
  **THE FIRST DIAGNOSIS WAS WRONG AND THE EVIDENCE CORRECTED IT.** This entry
  originally blamed `snapshot.ps1:391`. The real culprit on the ritual path is
  `filter_ignored.py:100` — `write_text(...)` with no `newline=`, the *exact*
  Idea-121 defect in a file that sweep never looked at. The tell was in the original
  measurement: **0 bare LF** means one uniform writer produced every line, and
  `snapshot.ps1` injects its meta line with a bare `` `n `` — so had the PowerShell
  been last, the file would have held at least one. `filter_ignored.py` rewrites the
  file after it and decides the committed bytes.
  **BOTH sites are fixed, and that is not belt-and-braces:** `filter_ignored.py`
  early-returns without rewriting when nothing is dropped, and a `-CodeOnly` run never
  calls it at all, so `snapshot.ps1` normalizing `$new` to `\n` is the only guarantee
  on those two paths. Safe as a byte replace — JSON forbids unescaped control
  characters in strings, so every CRLF there is structural.
  **The guard is the durable half.** Idea-121 recorded "nothing guards this yet, so it
  can regress", and Idea-129 IS that regression, found by a stray `git add` warning
  rather than a test. `tests/unit/test_render_determinism.py` now carries two:
  a STATIC check that every declared committed-surface writer passes `newline="\n"`
  (fails on CI, on any platform, the moment a writer is added without it) and a byte
  check that no committed surface holds a CR. Verified RED on
  `drydocs-20260817.json` before the fix, green after. The writer list is DECLARED,
  not swept, because Idea-121 fenced eight non-render writers out on purpose —
  adding a committed surface means adding its writer to that tuple.
  **Left open deliberately:** whether the sibling depgraph repo should emit LF at
  source (Idea-126 territory) — we normalize on arrival either way.

- **`Idea-126`** · 2026-08-14 · `[idea]` · **parked → sibling-repo work resumes in `../depgraph` — it lands there, not in this repo, so it is deliberately not a backlog item here (re-checked 2026-08-19)** · prio? **Med** —
  **Declared-deps extractor DAG in depgraph (sibling-repo item).** R3 of the GitNexus
  comparison: before the lineage forks multiply extractors, adopt the GitNexus runner
  pattern — extractors/profiles declare `deps`, Kahn-validated, runner passes each one
  only its declared upstream outputs (hidden coupling becomes an error, cycle diagnosis
  prints the concrete path), per-phase timing. Lands in `../depgraph`, not DryDocs;
  captured here because grooming happens here.

- **`Idea-111`** · 2026-08-12 · `[bug]` · **closed — both CI ruff gates exit 0 again; only the process question is left, and it is the user's** · prio? **High** —
  **SWEPT AND GREEN 2026-08-12 (this desktop).** `ruff check .` and `ruff format --check .`
  both exit **0** — the first time since 2026-08-05. 35 findings and 31 unformatted files
  to zero. The user's deferral was only ever about not racing the concurrent remediation
  session; that session closed (G60/G83/G84 `done`), so the sweep ran the same evening.
  **Fixed, not ignored (the default):** 10 auto-fixable; a 31-file `ruff format`; the 6
  **N818** exception renames in `xml_io.py` at the user's explicit call —
  `UnsupportedEncoding`→`…Error` and its five siblings, **54 references across 5 files**,
  every name verified standalone first so a word-boundary rename could not clobber a longer
  one; **RUF007** ×2 → `itertools.pairwise` (clearer and equivalent); **N802** ×1, a test
  name of this session's own.
  **Two things RULED as keepers rather than fixed, because ruff's suggestion was wrong —
  not merely unnecessary.** This is the half worth reading:
  - **RUF002/RUF003** (14, prose only) now ignored globally with the reason inline.
    `defect A′` / `defect B′` are established identifiers carried in commit subjects
    (`3ebb66d`, `d40c9cb`) and throughout `drydocs_remediation`; ruff proposes a BACKTICK,
    which yields ``defect A` `` — nonsense, and CLAUDE.md is explicit that a style pass
    never renames identifiers. `⊆`/`∪` are set notation in a comment *about* set semantics
    ("emitted tokens ⊆ before ∪ introduced"); ruff proposes capital `U`, which reads as a
    word. **RUF001 stays ENFORCED** and is the one that matters — ambiguous characters in
    IDENTIFIERS are a hazard, in prose they are typography. Same split
    `docs/ruff-format-convergence.md` already drew for RUF001/2/3.
  - **RUF009** ×2 per-file-ignored on `xml_io.py`: the rule catches a shared MUTABLE
    default, and `Span` is `@dataclass(frozen=True)`, so one shared immutable instance is
    correct. Ruff does not special-case frozen dataclasses.
  Suite 2110 passed / 8 skipped; renders verified non-drifting.
  **STILL OPEN, and the only thing left here: the process question below.** A blocking gate
  that nobody read for a week is the actual defect; the lint was just its symptom.
  <!-- original entry, kept for the trail: -->

  **CI has been RED on `main` since 2026-08-05 and nobody noticed for a week.** Last green
  run `2026-08-05T06:10` (`test(currency): bring port-prompt under the currency guard`);
  every one of the 100+ runs since has failed, including four pushed today before this was
  checked. The failure is narrow and always the same: `ruff check` fails, so `ruff format
  --check` never even runs. **Everything else is green** — unit suite, CLI imports, CLI
  help, publish-boundary guard, schema/vocabulary guard. That is why it was survivable and
  also why it was invisible: the job that matters most passes, and only the last two steps
  red out.
  **This is J10 stage 5 working as designed and then being ignored.** Stage 5 (`1fcbf63`,
  2026-08-01) made both ruff gates blocking on purpose, after stages 1-4 cleared 362
  findings and formatted the whole tree at the pinned ruff **0.5.7**
  (`docs/ruff-format-convergence.md`). The debt then re-accumulated over eleven days of
  agent-authored code that never went through the pinned formatter: **48 findings / 44
  unformatted files** as measured 2026-08-12.
  **A hypothesis worth killing before someone re-derives it:** the drift is NOT two ruff
  versions disagreeing. There is exactly one ruff here — 0.5.7 in `pyproject.toml`,
  `poetry.lock` and the installed binary, with no ruff on PATH, no pipx ruff and no
  VS Code/Cursor bundled extension. New code is simply hand-written in the modern
  `assert x, (msg)` shape that 0.5.7 rewrites to its own older style. One formatter, an
  unformatted tail.
  **FIXED TODAY — the gate's SCOPE, not the code.** `pyproject.toml` `extend-exclude` now
  carries the two graph-vs-files capture directories (13 `.py` files, nothing imports them,
  verified before excluding). They are agent scratch scripts kept verbatim as the record of
  each track, and the repo already ruled this class once: *"fixing somebody else's capture
  to satisfy a guard is a provenance call, not a formatting one"* (ledger step 123, which
  inboxed the question as `Idea-103` rather than editing them). Same reasoning as the
  vendored `.claude/skills` block. **48 -> 35 findings, 44 -> 32 files.**
  **STILL OPEN — the sweep, deliberately deferred by the user.** ~1 hour: 10 auto-fixable
  plus a 32-file mechanical format (+452/-320), then ~25 needing judgement — 14
  `RUF002/003` (one character each, ambiguous Unicode in prose), 6 `N818`, 2 `RUF009`, 2
  `RUF007`, 1 `N802`. **Sequencing matters: 22 of the 35 are in `drydocs_remediation`,
  where a concurrent session is working right now** — including all 6 `N818`, which are
  exception-class renames in `xml_io.py` (`MalformedXml`, `LocatorNotFound`,
  `SelfCheckFailed`…) and therefore an API change, not a lint tidy. That session is already
  fixing its own ruff findings, so the sweep should follow their work, not race it. Outside
  their module only **13** remain: 8 `tests`, 2 `scripts`, 2 `drydocs`, 1 `drydocs_lineage`.
  **The process question is the durable half, and it is the user's:** a blocking gate that
  goes unwatched for a week is worth less than an advisory one that gets read. Options are
  a notification on red, a session-ritual step that checks `gh run list` before pushing, or
  accepting red-until-swept as a known state with an owner and a date.

- **`Idea-110`** · 2026-08-12 · `[doc]` · **closed — reclassified as a dated record, same day** · prio? **Low** —
  **CLOSED 2026-08-12.** User ruled option (c): the file is a dated RECORD of the
  2026-07-21 issue, not a usable starting prompt. Its header now says exactly that — a
  `status: DATED RECORD` block with the capture and landing dates, an explicit "do not
  paste as-is", and the reason it is kept anyway (it is the clearest single statement of
  the approved design direction: Kept Orbit brand rules, locked stack, token palette,
  layout anatomy — all of which still hold). The known drift is named in the header rather
  than left for the next reader to chase: the two marks are gone, the final mark is
  UNSETTLED, and mark references in the body are to be read as intent, not as pointers to
  assets. The body is deliberately NOT rewritten — annotating a record beats editing one,
  and the §2/§6 wording is part of what the record records. Two caveats added while there:
  the 33-path check is stamped point-in-time rather than offered as a guarantee, and §7
  ("what actually needs design work") is flagged as the most likely stale section, being a
  2026-07-21 to-do list. `kept-orbit-brand-sheet.png` + `kept-orbit-philosophy.md` remain
  the brand authority and are present. The general hazard below stands and is the residue
  worth keeping.
  **THE RESIDUE IS NOW MECHANISED, same day.** The "cheap standing check" below is a
  seventh port-preflight check, `cited paths resolve`: `drydocs.port_preflight` resolves
  every backticked repo-relative path cited by each document the range **ADDS**, and
  refuses to certify the base on any that resolve nowhere. Run against
  `UI-WIP/claude-design-ui-prompt.md` **as it stood at its merge `429d829`** it returns
  exactly `UI-WIP/drydocs-mark.svg` — the miss, reproduced. Two filters keep it actionable
  and both were measured rather than guessed: a citation with no directory is a filename
  mention (so `drydocs-mark-mini.svg` is deliberately NOT caught — the same line
  `test_runbook_currency` draws), and a citation whose first segment is not a top-level
  entry of this repo is relative to its own document or to a foreign codebase. ADDED-only
  is the other half: added-or-modified reports **59** paths on `ae21ee4..HEAD`, nearly all
  gate-log history and IDEAS entries naming an absence on purpose, while added-only reports
  **1** — this one. Exemptions follow the existing idiom: `RECORD_PREFIXES`
  (`docs/reviews/`, `internal/controlm-config/reference/`) each with its reason, plus
  self-declaration — a header carrying `status: DATED RECORD` exempts its own document,
  which is why the (c) ruling above ALSO closed the check's only live finding. Guards in
  `tests/unit/test_port_preflight.py`, each of the six mechanisms proven to fail on an
  injected defect before being trusted (J26). Documents already covered by
  `test_runbook_currency` are skipped — not to save work, but so that one defect is not
  reported under two check names.
  **`UI-WIP/claude-design-ui-prompt.md` cites two canonical brand assets that main deleted
  as REJECTED two and a half weeks before the doc was merged.** The doc names
  `UI-WIP/drydocs-mark.svg` + `drydocs-mark-mini.svg` as "final vector marks" under
  *Approved / canonical*; `d6022c3` (2026-07-28, "drop three rejected marks") removed both
  from main, and nothing on any branch has replaced them — they resolve nowhere in the tree
  and are not gitignored. A designer following the doc's own reference list is sent to two
  files that do not exist, listed under the heading that says they are approved.
  **How it got here, which is the part worth keeping:** the doc was authored 2026-07-21
  (`d9a2eac`) on a local branch, the marks were dropped from main 2026-07-28, and the branch
  was merged 2026-08-12 (`429d829`). The merge was textually conflict-free — one new file,
  no collision — so nothing flagged that its CONTENT referenced files main had since
  removed. That is the general hazard: merging a long-idle branch validates text overlap,
  never whether the prose still describes the tree. Cheap standing check before landing an
  idle doc branch — resolve the paths it cites.
  **Scope check done, so this is not vaguer than it is:** 33 of the doc's referenced paths
  resolve fine, including `kept-orbit-brand-sheet.png`, `kept-orbit-philosophy.md`,
  `web/src/layout/shellConfig.ts`, `components/ui/EmptyState.tsx`,
  `routes/ModuleTemplate.tsx` and the `drydocs-icons/` registry. The mark pair is the only
  genuine miss. The rest of the doc is a 2026-07-21 snapshot of the console and reads as
  accurate.
  **Decide:** (a) re-point the two lines at whatever the current mark is, if one exists
  outside the tree; (b) mark the brand-asset bullet superseded and say the mark is unsettled;
  or (c) leave it and reclassify the whole file as a dated record rather than a usable
  starting prompt — in which case its header should say so, since it currently reads as
  live instructions ("Copy everything below the line into Claude Design UI").

- **`Idea-109`** · 2026-08-12 · `[bug]` · **closed — fix landed at 841dc6e5, residue swept as J48 the same day** · prio? **Low** —
  **RESIDUE SWEPT 2026-08-12 (this desktop) — J48 `done`, and this entry closes.** 27
  sites judged: 24 modules now route through `repo_root()`, and three were RULED and left
  as written, which is the judgement this entry said each one needed — recorded at the
  site, because "skipping a site is not a disposition": `ontology/schema_graph.py`
  (vocabulary fragments + generated `.cypher` are package resources),
  `scripts/external_vendor_scrape.py` (not an installed package, so `__file__` already
  names the caller's tree — and it *cannot* adopt: those two lines put the root on
  `sys.path` **before** `drydocs_core` is importable), and `drydocs_core/config.py`, the
  one place where following the caller would be a **regression** — `.env` is untracked
  machine-local credentials that a worktree never receives, so a worktree run would find
  no `.env` at all. The mixed case came out repo-content: `var/mapping.db` is derived FROM
  the committed YAML/CSV beside it, so a worktree reading its own `config/` and writing
  main's `var/` is exactly the torn split this entry describes. Gitignored ≠ shared.
  **This entry's own list was short by four**, all the same defect in the same editable
  install: `drydocs_docmeta/registry.py`, `drydocs_docmeta/policy.py`,
  `drydocs_api/intake.py`, and a `_repo_relative()` helper buried INSIDE a function body in
  `drydocs_api/mappings.py` — found by the new derived guard *after* every listed file had
  already been read by hand, which is the case for deriving rather than enumerating in one
  incident.
  **One mechanism finding worth keeping.** The worktree proof's first draft ran its probe
  with `python -c`, which puts the CWD on `sys.path` — so the worktree's own `drydocs/`
  shadowed the editable install, every import came back worktree-relative, and the control
  passed for the wrong reason. The test now runs a probe FILE outside the worktree,
  reproducing the incident's real condition (`sys.path[0]` is the script's directory, never
  the cwd). That is the same asymmetry the original bug turned on, met from the other side.
  **Verified live** (desktop, no database, no company data — re-runs anywhere): a real
  `git worktree`, nine constants across four packages resolving inside it, and
  `cli.DEFAULT_SAMPLES_DIR` correctly staying pinned at the install. A blanket
  search-and-replace of every `__file__` anchor FAILS that test, so it checks the judgement
  and not just the edit. Suite 2092 passed / 8 skipped.
  **FIX 2026-08-12 (this desktop).** New `drydocs_core/repo_paths.py` — `repo_root(fallback)`
  climbs from the cwd to the nearest enclosing `.git` (an `.exists()` test, because a
  worktree root carries a `.git` *file*, not a directory), validates it as a DryDocs
  checkout via `drydocs/__init__.py` + `pyproject.toml`, and otherwise returns the caller's
  old `__file__` anchor. It stops at the first `.git` whether or not that repo validates,
  so neither the `depgraph` sibling nor an unrelated parent repo can capture the paths, and
  installed-package consumers outside any checkout behave exactly as before. Adopted in
  `plan_board`, `plan_ideas`, `plan_roadmap` — the three that route through the installed
  package. Guard: `tests/unit/test_repo_paths.py`, 13 tests, including one that drives a
  **real** `git worktree` through a **real** `scripts/render_board.py` and asserts main
  comes back byte-identical; **verified to fail without the fix** with exactly the original
  symptom (`wrote C:\coding\projects\DryDocs\docs\plan\board.html` from a worktree cwd).
  Suite 1961 passed / 5 skipped. **What the fix also corrected in the diagnosis below:** the
  damage was never "everything goes to main", it was a **torn render** — the five sibling
  scripts `render_board.py` invokes (`render_gates`, `render_enforcement_matrix`,
  `render_load_map`, `render_software_registry`, `render_context_types`) resolve out of the
  worktree's own `scripts/` and anchor on their own `__file__`, so *those* were always
  correct; only the three package-routed outputs went to main. Half the render in each tree
  is why nobody noticed. **RESIDUE, still open:** ~17 other `_REPO_ROOT`/`REPO_ROOT` sites
  share the raw `Path(__file__)` pattern (`gate_pages`, `graph_verify`, `review_labels`,
  `source_mappings`, `seal_samples`, `port_preflight`, the four `drydocs/loaders/*`,
  `drydocs_core` `precedence`/`source_registry`/`manual_mappings`/`mapping_store`,
  `orchestration/crosswalk`+`shell`, `ontology/schema_graph`). They are NOT all bugs — the
  rule is that repo-*content* paths follow the caller while package-*internal* resources
  (e.g. `drydocs_core/schema/*.cypher`) rightly follow `__file__` — so each needs that
  one-line judgement, which is why this was scoped to the ritual rather than swept.
  *(Swept as J48 later the same day — see the top of this entry. The real count was 27, not
  17, and the rule held: 24 adopted, 3 ruled package-internal or install-anchored.)*

  <!-- original diagnosis, kept for the trail: -->

  **A worktree-isolated agent that runs the session-end render ritual writes its output
  into the MAIN repo, not its own worktree.** Both `results-sonnet` tracks hit this
  independently within the same half hour on 2026-08-11 and both recovered, which is why
  the sonnet `RUN-LOG.md` calls it out as adoptable "independent of the graph-vs-files
  question". Mechanism, re-verified on this desktop 2026-08-12: `drydocs` is installed
  **editable** into `.venv` via a `drydocs.pth` pinned at the main tree, and
  `drydocs/plan_board.py:34` sets `_REPO_ROOT = Path(__file__).resolve().parent.parent` —
  so the defaults are anchored to *where the package file lives*, never to the cwd or to
  the worktree the caller is standing in. Running `python scripts/render_board.py` puts
  `scripts/` on `sys.path[0]` and does **not** put the cwd on the path, so the worktree's
  own `drydocs/` is never shadowed in: the import falls through to the editable install.
  Reproduced with cwd set to `.claude/worktrees/agent-a6fcf6daf8af92ce7` — `p.__file__`
  and `DEFAULT_BOARD_PATH` both resolve under `C:\coding\projects\DryDocs\`, the main
  tree. No database and no company data, so it re-runs anywhere (J18). It is silent: the
  render succeeds, the worktree stays clean, and the main tree acquires an uncommitted
  board/design-doc render nobody in that session wrote. `DEFAULT_BACKLOG_PATH` has the
  same anchor, so the agent also *reads* main's backlog, not its own. Blast radius is
  every `scripts/render_*.py` plus `snapshot.ps1`, which drives them — i.e. the whole
  CLAUDE.md §0 session-end ritual, exactly the step an agent is most likely to run
  unprompted. Candidate fixes, not yet ruled: derive `_REPO_ROOT` from `git rev-parse
  --show-toplevel` at call time; or have the render scripts pass explicit paths resolved
  from their own `__file__`; or refuse to write outside the caller's worktree. Related to
  `Idea-108`, which is the wreckage this behaviour left behind.

- **`Idea-108`** · 2026-08-12 · `[chore]` · **closed — salvaged, then pruned under user ruling, same day** · prio? **Low** —
  **CLOSED 2026-08-12.** User ruled "prune worktrees + branches" once the salvage below
  made it safe. Executed on this desktop after a final re-verification that all four
  untracked files were byte-identical to their committed captures and all four branches
  were ancestors of `main`: both `.claude/worktrees/agent-*` trees removed,
  `git worktree prune` run, and all four `worktree-agent-*` branches deleted
  (`6c24963` ×2, `23e14bb` ×2). `git worktree list` now reports only the main checkout and
  no `worktree-agent-*` branch remains. Nothing unique was lost — the content lives in
  `o31-ALPHA.diff` / `o31-BETA.diff`, committed and pushed first.
  **UPDATE 2026-08-12 (this desktop): the "both directions are destructive" dilemma is
  resolved, because there was a third, non-destructive direction — finish the capture.**
  The two worktrees are the ALPHA/BETA tracks of the `results-sonnet` O31 coding
  comparison (`docs/reviews/graph-vs-files-experiment/`), whose protocol told each agent
  to write a `<run>.diff` back to the main tree and **commit nothing**. Checking the two
  captures against their live worktrees showed they were **not captured to the same
  standard**: `agent-aa168e5039f906d30` = ALPHA, whose `o31-ALPHA.diff` is a structured
  file (`=== git diff (tracked files) ===` / `=== NEW FILE: … ===` / `=== git status
  --porcelain ===`) that **embeds both untracked files in full** — that worktree was
  already 100% redundant. `agent-a6fcf6daf8af92ce7` = BETA, whose `o31-BETA.diff` was a
  plain `git diff` plus a porcelain listing: it **named** `scripts/render_underhood_benchmark.py`
  and `tests/unit/test_underhood_benchmark.py` as `??` but carried **none of their
  content**, and BETA's report only describes the script. So 737 lines — the *core
  deliverable* of half the comparison — existed nowhere but that dirty worktree, and the
  prune this entry was raised to authorize would have destroyed it while the diff on disk
  looked complete. **Done:** `o31-BETA.diff` rewritten into ALPHA's format with both files
  embedded verbatim — **744 insertions, 0 deletions**, every pre-existing byte verified
  byte-identical in place and both embedded files verified exact against the worktree.
  **What is left is only the prune**, and it is now genuinely safe: both worktrees are
  fully represented in tracked files, and all four `worktree-agent-*` branches are already
  ancestors of `main`. Still the user's call because `git worktree prune` / branch deletion
  is irreversible and touches another stream's trees. The separate render-path finding
  these two runs surfaced is now filed as `Idea-109`. Sibling of `Idea-17` (post-squash
  relic cleanup).

  <!-- superseded framing, kept for the trail: -->
  **Two abandoned agent worktrees are holding UNCOMMITTED work that no branch and no
  `git log` will ever show.** Found at the 2026-08-12 groom, verified on this desktop:
  `git worktree list` reports `.claude/worktrees/agent-a6fcf6daf8af92ce7` and
  `.claude/worktrees/agent-aa168e5039f906d30`, both pinned at `6c24963` (2026-08-11)
  while `main` is at `887a0e7`, and BOTH TREES ARE DIRTY — 6 and 8 changed paths
  respectively, including an untracked new file `scripts/render_underhood_benchmark.py`
  and modifications to `docs/restructure/backlog.yaml`, `docs/plan/board.html`,
  `docs/plan/roadmap.html`, `tests/unit/test_render_determinism.py`, `CHANGELOG.md`
  and two `web/src/underhood/` sources. All four `worktree-agent-*` branches are
  ancestors of `main` (`git branch --merged main` lists every one), so the BRANCHES
  carry no unique commits: the only unique content in the repo is that uncommitted
  working-tree state. Two of the four branches have no worktree directory left at all.
  Why it is worth a decision rather than a sweep: a `git worktree prune` or a routine
  branch cleanup erases the untracked script silently, and the standing concurrent-sessions
  rule is that no session touches another stream's uncommitted work — which is exactly why
  the groom looked and did NOT act. What the user rules: is this a superseded
  `render_underhood_benchmark.py` experiment that can go, or unlanded work to commit onto
  a branch first? Sibling of `Idea-17` (post-squash relic cleanup), which this groom
  narrowed the same day.

- **`Idea-104`** · 2026-08-11 · `[question]` · **open** · prio? **Med** —
  **The MFT route id changed shape between the field observation and the standard, and
  nobody has said which is real.** The 2026-06-11 production capture
  (`internal/standards/technology/description-field-metadata-plan.md`) records one
  numeric key, `ROUTE_ID: 372399`. The 2026-08-11 standards capture records a
  *directional pair* of *string* ids, `INBOUND_ROUTE: MFTS_RT_IN_…` /
  `OUTBOUND_ROUTE: MFTS_RT_OUT_…`, each modeled as a `dprod:DataProductPort`. Three
  readings and they lead different places: the strings are documentation placeholders
  and the real ids are numeric; the route-id format genuinely changed; or the numeric id
  was only ever one leg of a pair nobody had split yet. It matters because C16's prefix
  governance assigns a SINGLE target (`mfts.routeId`) that a directional pair does not
  fit, and because a `dprod` port needs a stable key. Same capture, same class of
  problem, worth ruling together: `SourceSnowQueue` (the *source system's* queue,
  populated in production) and `PDN_SNOW_QUEUE` (the *downstream consumer's* queue,
  `NULL` in the standard) are DIFFERENT SUBJECTS that a naive key mapping would merge.
  **CHECKED AT THE 2026-08-11 GROOM — still open, and now half-answered.** C30 (done, 2026-08-11) retires the INBOUND/OUTBOUND route pair ON WATCHERS, because a watcher is inherently inbound, and drops `PDN_SNOW_QUEUE` from the job token set — so the directional-pair half and the two-queues half both narrow. What C30 did NOT rule, and what still needs the SME, is the one this entry was raised for: whether the real route id is the numeric `372399` or the `MFTS_RT_*` string, which decides both what C16's single `mfts.routeId` prefix target points at and what a `dprod:DataProductPort` is keyed on. NOT groomed into an item, deliberately: the two readings lead to different prefix governance and a different port key, and a groom cannot pick between them.
  **RE-CHECKED AT THE 2026-08-12 GROOM — still the SME's, and now explicitly PROTECTED in an item rather than only in this file.** G83 applies C30's ruling to the parse contract, which means it touches exactly the two entries that carry this question. Its acceptance therefore says in writing that marking the route pair retired is NOT an answer to which route-id shape is real, and that whichever entry survives must keep the note recording the two unreconciled forms — so the evidence cannot be tidied away with the tokens. The question itself is unchanged and unowned.
  **RE-CHECKED AT THE 2026-08-22 GROOM — unchanged and still the SME's.** No new evidence since the
  2026-08-12 re-check: G83 still carries the protection clause, and nothing in the interim touched which
  route-id shape is real. Not groomed, deliberately — the two readings lead to different C16 prefix
  governance and a different `dprod:DataProductPort` key, and a groom cannot pick between them.
  **RE-CHECKED 2026-09-02 — THE EVIDENCE HALF HAS ARRIVED, and the blocker changed shape.** The
  company-side research log `internal/research/JOB-MFTS-MM-research.md` (transcribed producer-side
  the same day) measured it: **89 of 89 real MFTS routes carry a 6-digit numeric id**, the string
  pair appears in **zero**, the UUID belongs to a different product (OneMFT), and the runbook's
  `NEP4824` is a partner stem, not a route id. It also adds a THIRD reading this entry never had:
  the two shapes may belong to two different PLATFORMS (MFTS is Axway, SEAL 89830, distinct from
  FileMover/OneMFT). The ruling is still the SME's — but "a groom cannot pick" is no longer the
  reason to hold: the groom does not need to pick, it needs to CONVENE, and the gate page exists
  (`email-dl-contact-point` §G5, OPEN/UNSIGNED). Two things the ruling must now also cover, both
  from the research: whether identity needs the environment — `(route_id, fts_id)`, the G64
  composite-key shape (OQ-18) — and whether a re-provisioned route keeps its id, because if not
  `route_id` fails ADR 0001's business-key test (OQ-11). See [[Idea-236]] for the full gap list.

- **`Idea-93`** · 2026-08-08 · `[chore]` · **groomed → executed IN PLACE at the 2026-08-09 groom (14 stale `inputs:` fixed in backlog.yaml) + merged → L19 (the design-doc half); the E1 status question STAYS OPEN — user call** · prio? **High** —
  **next_ready needs a re-groom: 9 of 62 items carry stale `inputs:`** (persona Run 2,
  U-pm: `docs/reviews/persona-project-manager-2026-08.md`). Six causes: (1) the S5
  2026-08-06 split of `config/taxonomy-ontology-map.yaml` and
  `drydocs_core/ontology/relationship_vocabulary.yaml` into fragment DIRECTORIES —
  stales Q14, G34, U10, U11 (and one traceability-matrix Component ref, per U-tw —
  re-point it in the same pass); (2) `web/src/routes/ask/` never existed — the ask
  module is `web/src/ask/` + `routes/AskRoute.tsx` (Q15, R11, R12); (3) U10 cites the
  retention-deleted `drydocs-20260802.json` — rule of thumb: cite the snapshot
  DIRECTORY, never a dated file, retention makes dated cites self-staling; (4) R9 has a
  filename typo (`persona-architect-…` → `persona-python-architect-…`); (5) V4 cites
  `drydocs/review/`, which is flat files not a directory; (6) status hygiene — E1 has
  worn `in_progress` since 2026-06-22 while actually waiting on gate scheduling;
  consider `blocked`. Done-claims audit itself: 271 claims, ZERO false — the ledger
  holds.
  **GROOM 2026-08-09 — what was executed, and what is left.** Fourteen (not nine)
  non-`done` items carried a stale `inputs:` path, and all fourteen were corrected in
  `backlog.yaml` at this groom rather than promoted, because `backlog.yaml` is the file a
  groom owns: `E1`, `Q10`, `Q11`, `Q14`, `G34`, `G44`, `U10`, `U11` re-pointed at the S5
  fragment DIRECTORIES (`drydocs_core/ontology/relationship_vocabulary/`,
  `config/taxonomy-ontology-map/`); `E2` likewise; `Q15`, `R11`, `R12` re-pointed at
  `web/src/ask/` + `web/src/routes/AskRoute.tsx`; `U10` also dropped the retention-deleted
  dated snapshot for the snapshot DIRECTORY (the rule of thumb this entry proposed, now
  applied); `R9` fixed to `persona-python-architect-2026-07.md`; `V4` re-pointed at the five
  flat drydocs-review files plus `drydocs/publishing/`. `done` items were deliberately NOT
  touched — their `inputs:` were true when the work ran, and rewriting them edits the record
  rather than the work queue. STILL OPEN, and the reason this entry stays in the inbox: the
  **E1 status question** (in_progress since 2026-06-22, actually waiting on gate scheduling —
  `blocked` may be the honest value). A groom does not move an item's status: status is the
  claim channel between the two machines, so that one is the user's call. The design-doc and
  traceability-matrix half of this entry rides L19 clause (f).
  **RE-AUDITED 2026-08-12 (groom) — the 08-09 sweep has held, and the two new stale paths
  found were fixed in place.** The check re-run across all 112 non-`done` items (leading path
  token of every `inputs:` entry, existence-tested against the tree) returns THREE refs, down
  from fourteen: `G63` and `G64` both cite `config/audit-fields/` as a DIRECTORY when the
  ledger is the file `config/audit-fields.yaml` — every one of the other twelve references in
  `backlog.yaml` spells it correctly, so this is a typo and not a planned split; both corrected
  at this groom with the reason in a trailing comment. The third, `Y4`'s `backlog/items/`, is
  NOT stale: it is the sharded directory `Y2`/`Y3` create, and an input that names a
  deliberate future output is the one legitimate form of a non-existent path. Worth keeping as
  a standing groom check — it is cheap, it caught two, and `L27`'s enforcement mechanism does
  not cover `backlog.yaml` inputs. The E1 status question is untouched and still the user's.
  **RE-AUDITED 2026-08-19 (groom, desktop) — the standing check ran a third time and found THREE refs, of which TWO were false positives of the check itself.** The real staleness: `K17`, `G70` and `G73` all cite `drydocs_core/ontology/relationship_vocabulary/41-local-seal.yaml`, and that fragment was RENAMED to `41-local-business-application.yaml` when gate vocabulary-domains-and-id-policy §A2 renamed the domain `seal` → `business_application` — the same rename G101 exists to finish on the ids. All three corrected in place at this groom with the reason in a trailing comment, the 08-12 precedent. The two NON-findings are worth recording so the next run does not re-raise them: `Y4`'s `backlog/items/` is the sharded directory Y2/Y3 CREATE (an input naming a deliberate future output, ruled legitimate on 2026-08-12), and `O59`'s entry carries a parenthetical after the path, which the leading-token test reads as part of it. Three runs, three different causes, fourteen → two → three refs: the check keeps earning its place. The E1 status question is untouched and still the user's.

- **`Idea-89`** · 2026-08-07 · `[bug]` · **closed → fixed in place 2026-08-07 (SME ruling); no item minted** · prio **Med** —
  **`OverviewRoute` renders ALL modules unfiltered — the Overview pick-list offers
  routes the persona will bounce off.** `OverviewRoute.tsx:94` maps `MODULES` with no
  `canAccessModule` filter, while `Aside.tsx:50` does filter
  (`MODULES.filter((m) => canAccessModule(m.access, persona.role))`). So for the `user`
  persona the Overview "What do you want to look at?" list shows `gates`,
  `underhood` and now `software` — all `access: 'sme'` — and clicking any of them
  hits the App.tsx role guard and redirects to `/`. The fix is one `.filter(...)`,
  but it CHANGES BEHAVIOUR for modules that predate `/software`, so it wants its own
  item with a test rather than a drive-by edit inside another item's commit. Worth
  deciding at the same time: whether an inaccessible module should vanish or render
  disabled-with-a-reason (vanishing is what the aside already does, so consistency
  argues for the filter). (Found at the /software build, 2026-08-07, laptop —
  `/software` inherited the defect rather than causing it.)
  **RULED 2026-08-07 (SME): VANISH, matching what the aside already does.** The
  disabled-with-a-reason alternative is DECLINED — *"I don't want to overcomplicate
  the UI; we are still in proof-of-concept early stages, authentication will be
  added later if needed."* That reason is the durable half: a second access idiom
  is complexity bought against a decision NOT YET MADE, and the moment real
  authentication lands the whole affordance gets re-decided anyway. One idiom, one
  place. FIXED IN PLACE rather than promoted: with the behaviour question ruled,
  what remained was a one-line `.filter(...)` making the pick-list agree with the
  aside — minting an item to close it the same minute is ceremony, not audit. The
  groom was right to flag the disagreement; the ruling is what dissolved it.

- **`Idea-74`** · 2026-08-05 · `[source]` · **open — user decision, blocks O44 column 3** · prio? **Med** —
  **Does DryDocs ingest the ServiceNow queue/assignment-group export, and
  producer-side or company-side?** O44's third column wants the SNOW queues that
  match an application and the technician roles inside them. `snow:cmdb-ci-classes`
  is registered (Q4 ruling, 2026-07-31) but `confirmed: false`, `adapter: ~`, and
  it captures CMDB **classes** — not queues, not assignment groups, not people.
  The concept is real and evidenced in prose only: the runbook skill's
  template-spec cites AO (L3) and RE/RRT (L2) Snow queues with a `Technician`
  role, and `internal/remediation/governance/critical-batch-and-self-heal.md`
  names a SNOW technician group plus a CTASK peer-review task. So the shape is
  known and no dataset carries it. Decide (a) register a second SNOW dataset for
  the queue/group export and build it here, (b) company-side only, in which case
  O44 column 3 is permanently empty and its acceptance should say so, or (c) defer.
  Note this is ALSO the other half of G35 §D — the ServiceNow TOM Accountable view
  is the surface whose counts disagree with SEAL's, and neither is ingested today.

- **`Idea-70`** · 2026-08-05 · `[decision]` · **closed — RULED same day, no item** · prio? **Med** —
  **`cdo-frameworks` corpus activation — SME "under consideration" at the
  cdo-crosswalk sign-off (gate-log 2026-08-05).** RULED in-chat the same
  session ("flip to activate. I want to settle our ontology with what they
  published"): (a) `confirmed: true` flipped in
  `config/doc-source-registry.yaml` with a gate-log RECORD entry; (b) the
  flip proceeds INDEPENDENTLY of the row-5 recapture — activation is the
  path that produces the recapture evidence. Test moved with the flip.
  No backlog item needed; the executed-pre-groom pattern.
  ORIGINAL ENTRY: the gate confirmed the vocabulary crosswalk (rows 1-4/6-8)
  and the SME remarked on §A that activating the corpus is under
  consideration, since the alignment check it was waiting on has passed.
  Sub-decisions: (a) the activation flip itself (producer-side registry
  state; the actual Confluence scrape stays company-side/on-network), and
  (b) wait for the row-5 recapture or proceed independently.

- **`Idea-63a`** · 2026-08-05 · `[question]` · **closed — answered; the cardinality question is settled** · prio? **Med** —
  **Control-M app code → SEAL cardinality — CORRECTED 2026-08-05: `uniq -d`
  tests the registry key, NOT the tier, and is necessary but NOT sufficient.** `AOC` and `DCL` are each
  a UNIQUE row in the file and still 1:many in reality (see the tier-1-shaped-CSV entry above). K8
  authors one steward row per app code and fans it out to folders (§B1), while
  `graph-tests/folder-attribution-coverage.yaml` enforces folder→application **1:1**. **Many codes →
  one SEAL is SAFE and already exercised** — SEAL 35806 (a reporting engine) registered ONE CODE PER
  SCHEMA, and two distinct codes carry SEAL 111809. **One code → many CONSUMERS is real and is tier 2**,
  handled by K7's surfacing rule rather than by the cardinality of the file. Still worth running
  `awk -F, 'NR>1{print $1}' <file> | sort | uniq -d` — a duplicated code would ALSO make the K9 manual
  tier-5 pins ambiguous (they were rekeyed to `app_code=<CODE>` and are hand-authored) — but an empty
  result proves only that the registry is a function, not that any code is tier 1. *(Split 2026-08-05:
  the `descr` half became `Idea-63b` — different disposition, since the cardinality question has an
  answer and the review queue is unbuilt work.)*

- **`Idea-61`** · 2026-08-05 · `[source]` · **parked → AutoSys ingestion work resumes (row 12 is a crosswalk amendment gate; checked at the 2026-08-07 groom — no active AutoSys stream to hang it on)** · prio? **Med** —
  **AutoSys attributes at a NAME-PREFIX grain, not a folder grain — crosswalk
  row 12, needs a gate amendment.** Placeholder captured in
  [`external/orchestration/autosys/README.md`](../../external/orchestration/autosys/README.md); the
  `autosys-crosswalk` gate is SIGNED (11 rows, 2026-07-14) so this cannot be appended to
  `config/crosswalks/autosys-to-bmc.yaml` silently. Observed: the AutoSys code registry maps a code to
  a LIST of instance-qualified name prefixes (`t08.x; u08.x; l08.x`), and a job name is a dotted
  namespace `<instance>.<lob>.<app>.<name>.<type>` — so attribution is a prefix MATCH, not a container
  lookup, and the environment lives in the instance prefix (the FID-name env-triplet convention one
  level up). Two load traps to handle before, not during, a load: a SENTINEL SEAL id whose row says
  the code must not be used (needs an explicit reject list — a lookup miss is not the same thing), and
  lifecycle state ("SEAL Decommissioned NO New EDIT ACCESS Permitted") trapped in a free-text info
  column beside a date.

- **`Idea-60`** · 2026-08-04 · `[source]` · **groomed → C25** · prio? **Med** —
  *(the gate SESSION is now a backlog item; the rest of this entry
  stays open — the sub-application USES_SOFTWARE source and the two missing product rows are not
  in C25)* —
  2026-08-04 — [source] **Software VERSION as graph context, from an adhoc evidence email — two gates
  drafted, both awaiting SME.** An SME email compiled for a version-readiness review lists install
  paths per functional id for one ETL product. Opening proposal was
  `(:BusinessApplication)-[:USES_SOFTWARE {version}]->(:SoftwareProduct)-[:documented_by]->(email)`;
  two defects named in the draft: (1) Neo4j cannot hang a relationship off a relationship, so the
  evidence attaches by property pointer / node-grain edge / reified assertion — not as drawn; (2) the
  rows are **(fid-name, install-path)** rows, not (application, product) rows — the same app appears
  many times with different versions and is reached only through a MUTABLE ownership join, so writing
  the app-level edge directly bakes a time-varying derivation into a fact. Gate
  `software-version-context` proposes: load at the AppUser grain (new vocab entry
  `reg_appuser_uses_software`, same label, C8-clean), MERGE keyed `{source, install_path}` (NOT
  `{source}` — C14's key assumes one fact per pair and this source asserts several), version parsed
  from the path via a pattern table shaped like `invocation_patterns`, observed versions NEVER
  auto-appended to the curated `software-registry.yaml` product row, evidence attached by
  `evidence_doc_id` pointer with reification as the named upgrade path. Corpus `adhoc-sme-email`
  registered (`confirmed: false`, citation-only, connector `email`). App-level rollup deliberately
  BLOCKED on the FID gate. **Groom both gates + the doc-09 phases into backlog items once signed.**

- **`Idea-57`** · 2026-08-05 · `[bug]` · **merged → J35 (2026-08-07, the SHA-citation half); the company-side credential fix stays open, company's hand** · prio? **High** —
  **The company side cannot fetch the producer, and has been answering
  from a cached ref without knowing it was one.** A company session reported "producer repo
  not reachable — private or removed" and fell back to `cewilson/main @ 5f79d145`. The repo
  is neither private-to-them-by-design nor removed: `gh repo view ce-wilson/DryDocs` from
  the producer returns `PRIVATE` and healthy with a current `pushedAt`. So it is an ACCESS
  failure — expired PAT, lapsed SSO authorization on the token, or a proxy — and all three
  are indistinguishable from `git fetch`. Blocks guardrail 1 outright ("read at producer
  HEAD, not the ref you last fetched"). Warning added at the top of `port-prompt.md`
  §"Last completed port", but the fix is company-side credential work. **The design question
  worth grooming:** a cached-ref read is currently indistinguishable from a live one to the
  reader of the answer — should the port prompt require every producer-tree citation to
  quote the SHA it was read at, so a stale read announces itself?

- **`Idea-50`** · 2026-08-04 · `[source]` · **parked → the internal DPL build starts landing** · prio? **Med** —
  **`controlm-pipeline-stub` captured + integration plan written (internal).**
  The internal DPL Control-M XML builder/validator package (config → generate → validate →
  upload → runtime, 14/14 green) is captured VERBATIM at
  `internal/controlm-config/reference/controlm-pipeline-stub-capture.md`, and the
  work order for the internal Opus 4.8 agent is
  `internal/controlm-config/controlm-pipeline-stub-integration-plan.md` (items X1-X3 XML-seam
  supplement, W1-W4 greenfield emitter for the fix module, V1-V2 CR### rules, E1-E4
  classifier/gate enrichment, F1 fixture factory). Producer-side grooming trigger: the
  producer-TWIN items (E2 job-name grammar mechanism, F1 sanitized fixtures, W1 if promoted
  to drydocs_core) groom into backlog.yaml when the internal build starts landing — epic
  placement (G-series vs new) is a user call at that groom. Notables the capture settles:
  the stub IS the vendor-schema acquisition remediation XML I/O was parked on
  (Folder.xsd + full attribute reference), and the DPL job-name grammar closes half the
  "job naming standard = outstanding gap" memory (folder grammar corroborates PRAOCG).
  TRIGGER CHECKED 2026-08-04 (weekly groom) — **NOT fired, stays parked.** Both capture
  files verified present (`internal/controlm-config/reference/controlm-pipeline-stub-capture.md`
  and `internal/controlm-config/controlm-pipeline-stub-integration-plan.md`), but the stated
  trigger is the INTERNAL build starting to land, and nothing from X1-X3 / W1-W4 / V1-V2 /
  E1-E4 / F1 has landed yet. The entry's own terms also make this un-groomable today even if
  it had: epic placement for the producer twins (G-series vs a new epic) is explicitly a user
  call at that groom, so promoting now would be inventing the answer.

- **`Idea-49`** · 2026-08-04 · `[question]` · **parked → user ruling: recreate the desktop container, or re-point the version fact** · prio? **Med** —
  venue divergence (J18): the DESKTOP `neo4jtest` reports server
  5.26.27, while `config/dev-environment.yaml` + runbook Appendix A say 2026.05.0 EE —
  and its `ddschema` was missing today despite G51 (provisioned 2026-08-03, desktop),
  i.e. the topology state postdating the wipe did not survive to today. Likely the
  desktop container predates/rolled back from the 2026-07-28 plugin-volume recreation.
  Ties into G50 (desktop rollback-copy question, open). Re-provisioned + fully reloaded
  today; decide whether to recreate the desktop container on the pinned image or re-point
  the config's version fact with a venue note. (desktop)
  KEPT-UPDATED 2026-08-04 (weekly groom) — **still the user's decision, and now confirmed
  DESKTOP-ONLY.** Verified at this groom from the laptop (J18 venue: laptop, `neo4jtest`,
  `drydocs` DB): this machine runs the pinned 2026.05.0 Enterprise with `ddschema` present
  and six user databases online, so the config's version fact matches reality here and the
  divergence is not a repo-wide drift. That narrows the choice rather than making it — the
  question is unchanged (recreate the desktop container on the pinned image, or re-point the
  config's version fact with a venue note), and it stays parked because either answer is a
  ruling, not a default. Worth noting for whoever rules it: nothing currently DETECTS this.
  `tests/unit/test_dev_environment.py` pins the provisioning command to the config file, but
  no check compares a RUNNING server's reported version against the pinned one, which is why
  the desktop drifted silently. If the ruling is "re-point with a venue note", that gap is
  the thing worth an item.

- **`Idea-44`** · 2026-07-31 · `[source]` · **parked → company network access** · prio? **Med** —
  **cdo-frameworks live Confluence scrape (company-side).**
  Registered on-demand in `config/doc-source-registry.yaml` (connector: confluence, T4,
  ddcontext); page-ID target list in `internal/cdo-reference/README.md`. Priority
  recapture: Descriptive Metadata, Data Quality, Data Contracts (DPROD), Taxonomy
  Framework property tables — the capture holes that block crosswalk sign-off. Needs the
  docmeta confluence connector (or an interim company-side capture) — company network only.

- **`Idea-41`** · 2026-07-28 · `[question]` · **merged → J34 (2026-08-07 pm — the overlay grammar must be able to express a producer-LOCAL file); the disposition ruling itself stays the user's** · prio? **Med** —
  **`config/dev-environment.yaml` under a `canonical-producer` row —
  decide the disposition producer-side too, not just company-side.** Step 48 raises this for the
  consumer, but the asymmetry is ours: `config/**` is `canonical-producer`, and U7 has just made
  that file *producer-local infrastructure* (sibling repo path, expected instrument commit, on
  top of the pre-existing container name + host ports). A port applies it wholesale, and the L16
  runbook's Appendix A is a **render** of it — so a producer value propagates into consumer
  documentation, which is exactly the drift Appendix A was restated to prevent. Options: a
  per-entry row (which keys? the file has no id-keyed grain — probably section-level: `neo4j:`
  and `depgraph:` are environment-specific, `services:` ports arguably shared), a
  canonical-company row, or split the file into a portable contract + a local overlay. The last
  is the cleanest and the most work. Left deliberately un-made by the 2026-07-28 session, per
  J16's own rule that a disposition is a decision, not a default. ~~Fork merge~~ — **RESOLVED
  2026-07-28**: both branches merged into depgraph `main` (`5006567`) and DELETED, local and
  remote; `main` now carries every capability (probe reports `multi_root` AND `tree` true for
  the first time, `-Tree` works). Semantic merge details in DryDocs `8a82e3b` and the depgraph
  merge commit; the `add_rel` signature/shape collision and three regions git auto-merged that
  should have conflicted are the parts worth re-reading if that code is touched again.

- **`Idea-37`** · 2026-07-25 · `[idea]` · **parked → the SME convenes the supplement-shape gate** · prio? **Low** —
  **Supplement shape C — registration-vs-instance-seed re-slice** (the
  parked sibling of shape A, now groomed as **G29**). Re-sliced so that registering an
  ontology term and seeding an instance of it are separate operations rather than two halves
  of one supplement file. Explicitly **gate-worthy, not a refactor** — it changes what a
  supplement MEANS, so it routes through the HITL gate rather than a build item. Groom when
  the SME convenes it; G29 deliberately does not touch it.

- **`Idea-36`** · 2026-07-25 · `[source]` · **closed — cited, no item of its own (confirmed at the 2026-07-25 groom)** · prio? **Low** —
  **Databricks Unity Catalog researched — full notes at
  [`reference/research/databricks-unity-catalog.md`](../../reference/research/databricks-unity-catalog.md)
  (SME saw "Unity Catalog works so well in Databricks" and asked what it captures).** Public
  vendor build of the layer `docs/patterns/data-catalog/` models. Headline: its four semantic
  features land almost exactly on node types we already define — Domains → `CatalogDataDomain`,
  Glossary → `CatalogBusinessTerm`, governed tags → `CatalogTag` / `CatalogClassifier`, data
  classification → `config/classification.yaml`. Independent convergence, worth citing rather
  than re-deriving. **Three things to actually use:** (1) *lineage derived from Spark execution
  plans, never declared* — a clean public demonstration of the GROUNDED-over-SYNTHESIZED
  principle, and the argument for deriving Control-M dependencies from definitions rather than
  documentation; (2) *a controlled vocabulary needs an enforcement point or it rots* — their
  governed tags only work because a **tag policy** is attached, which is our classification-test
  rule generalized to any glossary we build; (3) their glossary ships "terms that link to each
  other," i.e. a concept scheme, which is external evidence for the acronym-catalog idea below.
  **Don't over-borrow:** "Genie Ontology" is a learned context layer, **not** an ontology in the
  PROV-O/ORG sense — cite as *catalog* precedent only, same tool-pattern-not-standard verdict as
  NeoCarta. It also has no orchestration model, so it answers a different question than we do.
  **Latent option (not proposed):** if the company runs Databricks, `system.access.table_lineage`
  and per-catalog `information_schema` are privilege-filtered and SQL-queryable — a legitimate
  future ingest source, necessarily Internal-classified. Groom: probably no backlog item of its
  own; fold the citations into the acronym-catalog item and any data-catalog ADR that revisits
  glossary/tag enforcement.
  KEPT-UPDATED 2026-07-25 groom — **the first citation has been consumed**: ADR 0010 §4.2
  (`app_id` + `id_authority`, groomed as **S3**) applies the governed-namespace lesson inward —
  the value of a governed namespace is that *the identifier itself carries its authority*, which
  is exactly what `id_authority: "SEAL"` encodes. Still parked: the *tag-policy-as-enforcement*
  and *glossary-as-concept-scheme* citations, which wait on the acronym-catalog line below and
  on a data-catalog ADR that neither exists nor is scheduled. No item of its own — confirmed.
  (Correction 2026-07-27: `id_authority` was WITHDRAWN at the identity gate's §B0 sign-off —
  SEAL stays the single issuing registry, so the property encoded a fact that cannot vary. The
  governed-namespace citation stands; its worked example moved to the source-field ledger shape
  instead.)

- **`Idea-35`** · 2026-07-25 · `[idea]` · **merged → G34 (content inside its scaffold); parked → the gate-log Q6 ruling** · prio? **Med** —
  **Acronym catalog scoped by domain — so agents and humans stop colliding
  on the same three letters (SME, chat).** Direct fallout of the Q6 reopen below: `Ais` cost
  real time because two readings are both plausible — "as-is" (the standard architecture
  modeling idiom) and "Application Integration Streaming" (an org platform family) — and
  nothing in the repo adjudicated between them. Today
  `config/taxonomy/software-registry.yaml#acronyms` is a one-key section with no scope
  dimension, so it can record *expansions* but not **collisions**, and collisions are the
  failure mode that actually bites. **Shape:** key by acronym, carry *many* senses, tag each
  sense with its domain scope — `area` (which part of the org/platform), `business-domain`,
  `technical-domain`, `industry` (what an outsider would assume it means) — plus, wherever a
  misreading is known to have happened, an explicit **does-NOT-mean** note. AIS is the worked
  example: industry/modeling sense "as-is", org sense "Application Integration Streaming", and
  the note that our `:AisTool` label meant neither. **Modeling hook:** this is a SKOS job
  (`prefLabel` / `altLabel` / `definition` / `scopeNote`, senses as concepts in a scheme) —
  SKOS is already registered in `reference/standards/README.md` (namespace + "concept
  reconciliation") but has **no fetched local copy** yet, unlike prov-o/w3c-org/dprod-ekgf/
  sosa-ssn; fetching it would be part of this. **Boundary caveat (decide at grooming):**
  industry acronyms are External and publishable, org-internal ones are not automatically —
  needs per-entry `classification` or an `internal/` split, same rule as any other source.
  **Consumers:** agents reading CLAUDE.md and gate prompts; L5/L6 SME review, where an
  unglossed acronym stalls a page; a whitepaper/website glossary. Groom **after** the Q6
  ruling — Q6 decides whether `#acronyms` survives at all, and this is the shape it would grow
  into if it does. (Note: "Q6" here is the **gate-log** question, not the backlog item Q6,
  which is the unrelated docmeta Port A.)
  KEPT-UPDATED 2026-07-25 groom — **independent corroboration from the pre-UI structure
  review**: its §4.2 arrives at the same home from a different direction, ruling that where
  "SEAL", "PAT" and "AIS" need to be *defined* rather than *encoded*, the carrier is a
  `CatalogBusinessTerm`-shaped glossary (`docs/patterns/data-catalog/enterprise-data-catalog-ontology.md`)
  — not a property, not a label. That is this line's shape, reached by the identity question
  instead of the collision question. Still parked on the same trigger (the gate-log Q6 ruling);
  what changed is that two threads now converge on it, so it is likelier to be worth building.
  KEPT-UPDATED 2026-07-27 groom: the landing zone now EXISTS as a backlog item — **G34**
  (raised at the identity-gate sign-off) reserves `CatalogBusinessTerm` + its three edges as
  `planned`, schema public / definitions internal, deliberately defining NO terms. When Q6 is
  ruled and this line grooms, it becomes content INSIDE G34's scaffold (senses, scopes,
  does-NOT-mean notes as SKOS), not a new home.

- **`Idea-34`** · 2026-07-25 · `[question]` · **open — SME rules** · prio? **Low** —
  **Q6 REOPENED: is the AIS acronym entry worth keeping at all?**
  (SME, chat). C12/Q6 ruled the expansion "Application Integration Streaming" survives as
  `config/taxonomy/software-registry.yaml#acronyms` — the durable "what did that name mean"
  home. The SME now reports the premise was wrong: they read `Ais` as **"as-is"**, never as
  an acronym, so the label was never a considered modeling choice on our side. The record
  corroborates — `761a201` (2026-07-09) introduced it as `:AiTool` (**no "s"**), attributed
  to in-chat direction and flagged "not yet defined in the ontology"; it stayed spelled two
  ways for twelve days across backlog/IDEAS/port-archive; the 2026-07-21 "correction" to
  `AisTool` matched the C11 screenshot rather than decoding it; the expansion landed only at
  Q6 that afternoon. **Counterweight (don't skip it):** their docs portal root
  `/docs/ais/{orchestration,etl,file-transfer}/` is independent corroboration that AIS is a
  real org term — two separate questions (is the acronym real? = yes / was `:AisTool` a
  considered choice? = no), and Q6 answered the first as if it settled the second.
  **Options:** (a) drop `#acronyms` entirely — `config/gate-log.md` already carries the
  expansion verbatim, append-only, so nothing is lost and a one-key config section created
  to hold a dead string goes away; (b) keep it but rewrite as a **disambiguation** —
  "does NOT mean 'as-is'" is the protective sentence, not the expansion, since as-is/to-be
  is a standard modeling idiom and that misreading imports a false meaning (and "Streaming"
  was already ruled a misnomer at Q6). Producer-side recommendation: (b), worded as
  disambiguation. **Hold DISCHARGED 2026-07-27:** the hold was that
  `docs/port-T12-ais-excision-company-prompt.md` step 2b deferred the acronym rather than
  sweeping it, so no company session could harden a ruling still under review. T12 has since
  ruled (SUPERSEDE, 2026-07-21) and the excision is applied company-side, so that prompt is
  spent and was retired from the tree — the acronym question is now free-standing and no
  longer gated by a pending session. Still open, still the SME's: groom when they rule — a
  Q6 amendment entry in `gate-log.md`, not a new gate.

- **`Idea-33`** · 2026-07-24 · `[bug]` · **open — needs the user to point at the exact spot** · prio? **Low** —
  **Unlocated user-reported typo: "apply-catalog … at the bottom says
  apply ontology" (chat).** Searched cli.py docstrings/messages, runbook .md/.html both revs,
  run-drydocs skill, RELATIONSHIP_GUIDE, repo-README, feedback html, gate docs — no such
  string exists. Best guess: startup-refresh runbook step 3 says "the three domain
  supplements" and Appendix B omits `apply-registry-supplement` while running
  `load-software-registry` — a genuine Rev 3 gap that should ride the L5/L6 SME feedback
  loop (doc is mid-review; do not hot-edit). Re-check with the user for the exact spot.
  KEPT-UPDATED 2026-07-25 groom: **G29** (the `apply-supplements` consolidation) rewrites the
  exact verb set Appendix B lists, so its acceptance carries a rider to fold this check into
  the runbook update — which resolves the best-guess half without hot-editing a doc that is
  mid-SME-review. The *unlocated* half still needs the user to point at the exact spot.
  KEPT-UPDATED 2026-07-26 (G29 done): the rider was executed and turned up a NEW, closer
  candidate — not in the runbook at all, but in `.claude/skills/run-drydocs/SKILL.md`, whose
  chain block annotated `apply-catalog-supplement` with `# Catalog **ontology**` (and listed
  catalog BEFORE seal, which is the wrong order). "apply-catalog … says … ontology" is a
  fair description of that line. Both are now fixed — the block is one `apply-supplements`
  call and the order is enforced in code. Offered as the likely origin, NOT declared closed:
  if the user meant somewhere else, the report is still open. The runbook itself stays
  untouched and its three owed edits are the separate 2026-07-26 [doc] entry above.

- **`Idea-32`** · 2026-07-23 · `[idea]` · **open — user/SME ruling: which scope (the controlm_jobs.sql direct pull vs the remediation staging reads); re-checked at the 2026-08-07 pm groom** · prio? **Med** —
  **Oracle connection for the lineage/remediation path (user note,
  chat pm).** The lineage jobs step still stages a CSV by hand through a JDBC client;
  the Oracle connection is planned — and the user's note ties it to the REMEDIATION
  context ("switch to the remediation since this last update was related"). Candidate
  shape: a direct pull of the `controlm_jobs.sql` projection (the same file
  `ingest-controlm --use-oracle` runs — runbook Rev 2 records the equivalence) plus
  the remediation-side staging reads (STG_APP_FACT-family fact tables per the
  company-side greenfield docs). Clarify scope with the SME before building.

- **`Idea-31`** · 2026-07-23 · `[source]` · **parked → the remediation M2 generalization opens** · prio? **Med** —
  **Company-side greenfield remediation standards not yet
  producer-modeled.** Two docs live in the company `drydocs_remediation` path (seen in
  review 2026-07-23): (1) the Control-M file-name component standard — FileName
  decomposed into FilePrefix / FileBusinessDate / FileSequence / FileExtension /
  FileCompression / FileSuffix + the FilePattern FileWatcher glob, DistributionRole
  derived from extension, a `CM_JOB_FILE_NAME_STANDARD` Oracle column standard, and
  dcat:Distribution ontology mappings; (2) the cmd-job ontology variable mapping
  (`%%ETL_PLATFORM`, `%%LAUNCHER_SCRIPT_PATH`, `%%ETL_ARTIFACT_URI`… →
  STG_APP_FACT fact_type → :Script nodes / INVOKES / USES_ARTIFACT). Producer-side
  `drydocs_remediation` models FileWatcher (`job_type`, `watch_template`, resolved-watch
  equivalence) and job variables (ordered defs, scope chain, canonical rename,
  dot-smuggling detect, corroborate) GENERICALLY — but has no filename-component
  standard and `transform.py` still notes the canonical variable map is "a company-side
  ratified value". Candidate: bring both docs in as the ratified maps when the
  remediation M2 generalization opens (FR-REM-5's schedule/command/conditions slice).

- **`Idea-30a`** · 2026-07-22 · `[idea]` · **parked → cm_avg_run + calendar projection land** · prio? **Med** —
  **PDN trigger design: milestone/SLA grain + graph-computed slack,
  not per-job failure mail (SME, chat pm).** Current state: dev teams default ON/DO-MAIL
  + SHOUT to L2-on-failure → hundreds of ignored mails daily (alert fatigue — the
  motivating stat for the notification model). SME ruling direction: a failure must NOT
  trigger a PDN (potential delay notification) by itself; the trigger belongs at the END
  of the work stream with remaining recovery time calculated. Options mapped: (1)
  vendor-native = Control-M SLA Management / BIM job type at stream end — deadline-aware,
  projects completion from averages, alerts only on projected breach [MODEL KNOWLEDGE,
  not in corpus; licensed add-on — add "is BIM installed?" to the OQ-1-style company
  probe list]; (2) no-license fallback = terminal Dummy milestone job + time-based SHOUT
  WHEN-lateness variants instead of ON-NOTOK [SHOUT corpus-grounded via ctmdefine; the
  WHEN variants need verification]; (3) Confirm attribute = manual-approval GATE
  (corpus-grounded), not a notifier — usable as a HITL pause at recovery-decision
  points, wrong tool at stream end; (4) fatigue fix independent of all: demote
  failure-mail to MAXRERUN-exhausted only. DryDocs' role: the TRUE trigger condition is
  deadline − (now + remaining critical-path runtime) < 0 — the CPM-not-path-sum ruling
  from the cm_avg_run gate + calendar-projection plan; graph decides, milestone job
  delivers, DL from the email-dl-contact-point NOTIFIES mapping receives. Feeds: the DL
  gate B2 grain question (stream/milestone grain confirms folder-preference), the
  runbook module ETA logic, and the company-side probe list.

- **`Idea-30b`** · 2026-07-23 · `[idea]` · **parked → cm_avg_run + calendar projection land** · prio? **Med** —
  **Deadline-calibration audit — the SAME slack computation that gates a PDN also tells you
  whether a deadline is honest.** *(Split from `Idea-30a` 2026-08-05: 30a designs the trigger,
  30b audits the one that already exists — different deliverables, same feed.)*
  KEPT-UPDATED 2026-07-23 (SME, chat): the BIM install probe is ANSWERED — one
  production SLA/BIM job exists (SEAL 90489) — but it fires near-DAILY and is ignored:
  mechanism right, calibration wrong. Cause candidates (distinguishable): (1) deadline
  tighter than the stream's actual completion distribution [most common]; (2) stale/
  unrepresentative averages after the chain changed shape; (3) alert scope includes
  per-job failures, re-inheriting the noise it was meant to replace; (4) stream is
  genuinely chronically at-risk but the alert carries no slack/recovery content, so
  it's untriageable. DryDocs diagnostic play (once cm_avg_run + calendar projection
  land): take the 90489 BIM service's job membership, compute observed critical-path
  completion distribution, compare to the configured deadline → move deadline /
  refresh scope / re-engineer. Same slack computation that gates a PDN also VALIDATES
  whether a deadline is honest — deadline-calibration audit = a runbook/notification
  module feature, and the worked example for it. Principle for the notification model
  (gate-worthy): an alert channel earns attention only with a low base rate AND
  actionable content (remaining slack + recovery action) — any mechanism without
  calibrated thresholds degrades to ignored noise.

- **`Idea-29`** · 2026-07-22 · `[idea]` · **parked → gate email-dl-contact-point signs** · prio? **Med** —
  *(KEPT-UPDATED 2026-07-26: distinct from **Q10**, the email BODY as a
  document corpus. This entry is about DL MEMBERSHIP as an ontology mapping — the two touch
  the same source and must not be merged.)* **Email DLs need an ontology mapping (user, chat pm).** DL = the
  contact/notification channel for an app/team; only configured in Outlook (no feed,
  can't fix), witnessed in runbooks, extractable from emails; membership/usage are
  context-graph (layer 4) material. DRAFTED STRAIGHT TO GATE same session: gate prompt
  `config/gate-prompts/email-dl-contact-point.yaml` (class options vcard:Group vs
  prov:Agent; HAS_CONTACT_POINT dcat:contactPoint edge; store-as-source per the O24
  pattern; extraction-proposes-steward-disposes; layer-4 membership boundary) + map
  entry `dl-contact-point` (proposed). Grooming disposition: tracked at the gate —
  build items groomed on sign-off; nothing further parked here.
  AMENDED same day (SME follow-up, chat): the downstream-notification AUTHORING
  landscape added as gate section C — greenfield intent was the job Description
  field; better candidate = escalation DB special-instructions VARCHAR2(4000) in
  psgmgr (EJOBNAME/ECOMPONENT joins, support-editable = fixable source →
  override-until-fixed, not store-as-source, for the NOTIFIES leg); de facto truth =
  runbooks / Jira sign-offs / email threads (brownfield bootstrap, rejected as end
  state). C2 keyed convention must SHARE the description-metadata plan's template
  phase (two 4000-char conventions must not fork).
  TRIGGER RE-CHECKED 2026-08-22 (groom) — **NOT fired.** `config/gate-log.md` carries a 2026-08-12 `RECORD:`
  for §G5 (the downstream consumer contact attaches to a `:Port`, not to job/folder) — a logged SME direction,
  NOT a sign-off. The gate itself is still unsigned, so the entry's own disposition stands: tracked at the gate,
  build items groomed on sign-off, nothing parked here.

- **`Idea-28`** · 2026-07-22 · `[source]` · **open — SME data entry, not a backlog item** · prio? **High** —
  **Tier-1/tier-2 app-code rows: the SME still owes the enumeration.**
  (Re-inboxed slim 2026-08-04 from the groomed defined-mapping mega-entry — everything else
  in it was resolved by the K7 sign-off 2026-08-03 and the K9 build; see the audit trail.)
  Declared tier-1 examples so far: ARA=70002 (CMH Advice R&A), SRV=70003 (HL Servicing R&A).
  Tier-2 platform codes (e.g. DPL) map to MANY AreaProducts and the enumeration is OPEN.
  The landing zone now EXISTS: rows in `config/overrides/app-code-mappings.csv`, authored
  either directly or via the K11 steward screen once built — this is DATA ENTRY awaiting the
  SME, not a backlog item. Reminder riding with it: AreaProduct has ZERO rows in the sample
  taxonomy (lob-product-team.yaml OQ `area-product-missing`) — tier 2 makes that layer
  load-bearing, so the two OQs converge when the SME supplies the list.

- **`Idea-27`** · 2026-07-22 · `[idea]` · **parked → an env-toggle item exists to attach to** · prio? **Low** —
  **Env toggle = one canonical node identity, never per-env node
  identities.** When the header env toggle [Prod|UAT|Dev] gets built, it must re-scope
  DATA under one canonical node, not split identities (`job-dev`/`job-prod`
  anti-pattern). (Backstage assessment T8, UI-WIP/backstage-catalog-assessment.md §3;
  design constraint for the shell — attach to the env-toggle item when one exists.)
  TRIGGER RE-CHECKED 2026-08-12 (groom) — **NOT fired, and the check is worth recording because
  the toggle superficially looks built.** `O2` (done) shipped a **cosmetic** Prod|UAT|Dev toggle
  in the console shell; it re-scopes nothing, so there is still no item that would decide node
  identity, which is the only thing this entry constrains. Attaching the constraint to O2 now
  would file it against a done item where no one implementing the real re-scope will read it.
  TRIGGER RE-CHECKED 2026-08-22 (groom) — **NOT fired, unchanged from 2026-08-12.** `O2` (done) is still the
  only env-toggle item and it is still cosmetic: it re-scopes no data, so no item yet decides node identity,
  which is the only thing this entry constrains.

- **`Idea-25`** · 2026-07-22 · `[idea]` · **parked → a producer extractor starts consuming a temporal field** · prio? **Low** —
  **Control-M compact-timestamp normalization (mechanism, from the
  company XML-loader's second timestamp bug).** Control-M XML exports carry compact
  timestamps `yyyyMMddHHmmss` + literal `UTC` suffix (invented example: `20250101093000UTC`);
  fed raw into Cypher `datetime()` they throw `CypherSyntaxError` — not ISO 8601, and
  `UTC` is not a valid zone designator (`Z`/`+00:00`). Fix mechanism when the XML loader
  back-flows (and for any future producer temporal field): (1) normalize in PYTHON at the
  row-model layer (the C3 "Python owns normalization" precedent) — one canonical
  `parse_controlm_timestamp()` pydantic validator emitting tz-aware `datetime`, driver
  converts natively, `datetime()` string-parsing never appears in Cypher; (2) two bugs in
  the same family = scattered parsing, consolidate + unit-test the compact-UTC, date-only,
  and empty forms; (3) unparseable value → row to `rows_rejected` + WARN (G16
  values-decide pattern), never a batch abort at `_flush`. **FIXED company-side same day
  (as-built mechanism, supersedes the proposal above for back-flow):** a `_ts()`
  normalizer in the XML extractor emits the ISO *string* the loaders' existing Cypher
  `datetime(replace(x, ' ', 'T'))` contract expects (one temporal contract shared with
  the Oracle path — better than forking to native datetimes); zone token `UTC`/`Z` → `Z`,
  numeric offsets kept; 8-digit date-only → midnight; empty/None → None so the null-guard
  drops the row (fixes the batch abort). Residual gaps flagged to the company agent:
  unknown non-compact forms pass through to `datetime()` (docstring claims None) and 14
  valid digits aren't validated as a real date (`strptime` beats `isdigit`+len) — carry
  both hardenings into the back-flowed version.
  KEPT-UPDATED 2026-07-31 (weekly groom) — **trigger CHECKED and NOT fired, but the
  landing site now has a name.** A producer-side XML seam DOES exist as of 2026-07-29
  (**G47**, `drydocs_lineage/extractors/controlm_xml.py`), which looked like the
  back-flow trigger — but the file consumes **no temporal fields at all**: its declared
  contract is folders, jobs, and ordered variables only, and a search of it for
  timestamp/datetime handling returns nothing. So there is still no producer surface
  where a compact `yyyyMMddHHmmssUTC` value could arrive, and nothing to normalize. Stays
  parked, with the trigger sharpened: this grooms when the XML seam (or any producer
  extractor) starts consuming a temporal field — at which point the normalizer belongs in
  the EXTRACTOR emitting the ISO string the loaders' existing
  `datetime(replace(x, ' ', 'T'))` Cypher contract expects (the as-built company `_ts()`
  shape, which deliberately shares one temporal contract with the Oracle path rather than
  forking to native datetimes), plus the two hardenings above.
  Trigger re-checked 2026-08-04 (Control-M inbox groom): `controlm_xml.py` still consumes
  no temporal fields — stays parked.
  Trigger re-checked 2026-08-12 (groom): still NOT fired, and this check covers new ground —
  the extractor was rewritten at **G66** (2026-08-11) to stage folder and job DESCRIPTIONS, so
  it is no longer the same file that was checked in August. A search of it for timestamp /
  datetime handling still returns nothing: the fields it consumes are folders, jobs, ordered
  variables and now descriptions. Stays parked on the unchanged trigger.

- **`Idea-22`** · 2026-07-21 · `[idea]` · **parked → the public site starts** · prio? **Low** —
  **Public marketing-site brand kit** captured in
  `UI-WIP/WEBSITE-IDEAS.MD` (3 logo directions incl. the core+orbit modernization, secondary
  palette, hero/feature/architecture landing structure). This is the PUBLIC SITE
  (website-and-backstory workstream, 'overnight ledger' editorial identity — site not
  started, domain unresolved), NOT the console — deliberately left out of the 2026-07-21
  Epic O extension groom. Groom when the public site starts; the icon/logo direction
  should stay consistent with the O22 console glyph set.

- **`Idea-20`** · 2026-07-21 · `[source]` · **groomed → G60 (2026-08-07 pm) — clause (c) ONLY; clauses (a) and (d) re-read 2026-08-12 as PARKED, not open: (a) parked → a real CMD_LINE sample containing the `ingestion-launcher` jar, (d) parked → layer-4 context-graph work starts** · prio? **Med** —
  **DPL ingestion leg + AWS zone model traced** (company ingestion
  template; mechanism-only — values stay company-side). Upstream of the launcher backbone:
  FM drop of a `.dat` + `.tok` landing pair → Control-M file-watcher condition grammar
  (`TOK-IN-COND…` / `FW_DAT#DAT-IN-COND…`, FW-OK-on-FAIL) → a **separate
  `ingestion-launcher` jar** publishes to S3 RAW via HTTP-PUT publish API (dataset
  identity = GUID + version, zone-scoped publish role) → **each zone hop
  RAW→TRUSTED→REFINED is its own DPL pipeline** (own `--pipeline-id`) → PROVISIONING
  DB-load lands the consumption target (Provisioned ≠ an S3 prefix). One bucket with
  zone prefixes; per-zone Glue databases + tables (partition keys at onboarding,
  `--odate` = partition value). Legacy `dataset_flow.json` FILE→CONFORMED ≈ the
  RAW→TRUSTED hop. UPDATE same day (prod CMD_LINE samples): the ingestion TRIGGER jobs
  use the SAME dt-launcher.sh (`-i` mode) — that grammar merged into G15. Still open
  here: (a) the template's `ingestion-launcher*.jar` was NOT observed in any sampled
  CMD_LINE (placement jobs?) — classifier entry waits on a real sample; (b) ~~DataAsset
  zone/glue-table shapes for the MAC enrichment feed~~ RESOLVED at the G17 build
  (same day): candidate shape = `dpl_dataset` DataAsset keyed by dataset GUID
  alone, version/zone/name as PROPERTIES (glue db/table can join later as more
  properties); version-as-identity deferred to G22 clause f; (c) Pre/Post-execution command fields carry mv/backup file ops
  (parquet + .tok → backup) — a G14-shaped surface G14 doesn't read (it parses
  CMD_LINE only); (d) cross-job `%%\\JOB\VAR` runtime threading (run GUIDs, record
  counts passed between jobs) — context-graph flavored, definition-level no-op.
  RE-READ 2026-08-12 (groom) — **neither remaining clause is an open question; both are
  waits, and saying so is the whole edit.** Clause (a) cannot be groomed into an item
  because the item would have no input: a repo-wide search finds `ingestion-launcher`
  ONLY in this entry and in the backlog text quoting it — no sample, no classifier row, no
  fixture. It is parked on evidence arriving (a real `CMD_LINE` sample carrying that jar),
  and the classifier entry is a ten-minute edit the day one does. Clause (d) is parked on
  SCOPE, not evidence: cross-job runtime threading is layer-4 context-graph material by the
  CLAUDE.md §1 split, and layer 4 has no owner agent and no phase work started, so an item
  raised now would sit unstartable and distort `next_ready`. Marked so a future reader stops
  re-litigating two lines that are each waiting on something nameable.

- **`Idea-17`** · 2026-07-20 · `[chore]` · **open — NARROWED 2026-08-12: the REMOTE half is discharged (both branches are already gone from origin) and the stash is gone; only two this-machine-local relics remain, still the user's destructive call** · prio? **Low** —
  **Post-squash ref cleanup (user decision, destructive)**: origin still
  carries two pre-squash-history branches — `feat/mapping-store` (SUPERSEDED: the Initial-import
  squash absorbed its content and main then evolved past it; its only unique file was the
  regenerable web-console `.print.html`, since retired by L13) and
  `feature/provenance-audit-fields-plan` (status unreviewed). Local relics on the producer
  machine: branch `backup/ui-dark-local-3`, the stale stash noted at the 07-20 groom, and the
  new safety tag `archive/old-history-2026-07-20` (this machine's pre-squash history; the other
  machine has `archive/full-history`). Deleting the remote branches is the user's call.
  RE-CHECKED 2026-08-12 (groom, desktop) — **most of this entry has already been executed,
  and nobody recorded it.** `git ls-remote --heads origin` returns exactly two refs, `main`
  and `feat/external-vendor-scraper`: BOTH pre-squash-history branches (`feat/mapping-store`,
  `feature/provenance-audit-fields-plan`) are already gone from origin, so the destructive
  remote decision this entry was raised for no longer exists. `git stash list` is EMPTY, so
  the stale stash is gone too. What actually remains is two local relics on this desktop and
  nothing else: the branch `backup/ui-dark-local-3` and the safety tag
  `archive/old-history-2026-07-20`. Both are still the user's call — deleting the tag drops
  this machine's only pointer to pre-squash history (the other machine holds
  `archive/full-history`), which is precisely the kind of thing a groom must not decide.
  Related finding from the same check, filed separately because it is live rather than
  historical: `Idea-108`, four merged `worktree-agent-*` branches and two dirty worktrees.

- **`Idea-16`** · 2026-07-20 · `[chore]` · **open — USER MANUAL STEP** · prio? **Med** —
  **USER MANUAL STEP: add the SNYK_TOKEN repo secret** so the new CI
  snyk job (44523ab) runs for real — token from app.snyk.io (Account settings → API
  token) → repo Settings → Secrets and variables → Actions. Until then every scan step
  skips cleanly by design. After the first green scan: triage `snyk code` advisory
  findings and decide whether to gate it (the ruff-idiom follow-up).
  RE-VERIFIED 2026-08-12 (groom) — **the entry still stands exactly as written, and it is
  still the user's hand.** `.github/workflows/ci.yml` still carries the `snyk` job (the
  `snyk/actions/setup` step, `snyk test --all-projects --severity-threshold=high`, and the
  advisory `snyk code test`), and the file's own comment still names the missing repo secret
  as a USER MANUAL STEP. Nothing in the repo can discharge this: no agent can set a GitHub
  repo secret, so it neither grooms into an item nor closes itself. Checked because an open
  entry that has quietly become obsolete is worse than one that is merely waiting.

- **`Idea-15`** · 2026-07-20 · `[idea]` · **parked → ONE user decision (display-label scope); the placement blocker is DISCHARGED — epic `generic-naming` now exists** · prio? **Med** —
  **Replace SEAL/PAT naming with industry-standard, SaaS-configurable
  terminology** (user request; web research DONE same day →
  `knowledge/upgrade-plans/generic-terminology-research.md`). Candidates validated:
  SEAL → **Application Portfolio** holding **Business Application**s (ServiceNow
  CSDM/APM — our K4 node label independently confirmed); PAT → **Product Taxonomy** /
  **Product Portfolio** (product-operating-model literature; AreaProduct is the least
  standard term). Mechanism = the Salesforce "Rename Tabs and Labels" pattern: canonical
  concept ids stay generic and stable, tenant display/source names become config
  (source-registry `display_name` fields; O12/O13 console surfaces render them).
  PARKED pending user decisions recorded in the note's §Decision surface: (1) scope —
  display-label config only vs also renaming `seal_*` vocab ids/domains (ADR-scale, the
  ADR 0004 precedent); (2) placement — productization has NO epic/phase, so promoting
  this is a PLAN CHANGE (new epic proposal → user); (3) `SEALID` → generic identity
  property (gate discipline). Related: [[SaaS scaffold research line — the
  template-play/whitespace finding, 2026-07-17]].
  KEPT-UPDATED 2026-07-20 groom: **C10 landed same day** (ServiceNow CMDB/CSDM doc-set
  mined, 54ccf63) — the CSDM service/service-offering layer this line called its missing
  piece is now in reference/. The decision surface is fully fed; still PARKED on the three
  §Decision user calls above (scope / placement-as-plan-change / SEALID property).
  KEPT-UPDATED 2026-07-27 groom: **§Decision item 3 is RESOLVED** — the
  business-application-identity gate (SIGNED OFF 2026-07-27) ruled `SEALID` → generic
  `app_id` on the canonical node, with the per-source field-name ledger
  (`config/source-mappings/seal-extract.yaml`) carrying what each source CALLS it; build = S3.
  Decisions 1 (display-label scope) and 2 (placement/plan-change) remain the parked user calls.
  KEPT-UPDATED 2026-08-12 (groom): **§Decision item 2 is DISCHARGED — this entry now has ONE
  open question, not two.** Promoting it was blocked because "productization has NO epic/phase",
  so any promotion was a plan change only the user could make. That is no longer true: epic
  **`generic-naming`** was created 2026-08-11 on SME direction and **GN1 is DONE** — ADR 0012
  names loaders, commands and sources by the DATA rather than the tool, on exactly this
  entry's warrant ("company jargon entered a repo that was meant to be generic from the start —
  seal, pat, m1/m3 — this is the standalone-generalization goal, not cosmetics"). So the
  landing zone exists and the plan-change question is answered. What ADR 0012 does NOT cover is
  this entry's subject: the DISPLAY layer (tenant-configurable labels over stable concept ids,
  the Salesforce rename-tabs pattern) and the node-label/vocab-id question. Decision 1 — display
  labels only, or also renaming `seal_*` vocabulary ids and domains, which is ADR-scale — is the
  single remaining user call, and it is a genuine fork: one is config, the other rewrites the
  ontology's identifiers. ADR 0012 §(f) is the warning worth reading before ruling it: source
  registry ids are COMPANY-CANONICAL, so renaming `pat:*` is a cross-repo reconciliation minting
  retired-id entries, not an edit.

- **`Idea-14`** · 2026-07-19 · `[idea]` · **parked → depgraph work resumes** · prio? **Low** —
  **depgraph metric extensions (codeflow takeaways — ideas, not code)**:
  compute codeflow's three genuinely useful metrics ON TOP of our existing ast-accurate
  graph, in the depgraph sibling repo (stdlib, deterministic, rides the snapshot JSON,
  flows into Neo4j at Fork 3): (1) **blast radius** — reverse transitive reachability per
  file ("what breaks if this changes"; the same what-depends-on-it question DryDocs asks
  of batch jobs, turned inward); (2) **dead-file candidates** — zero inbound edges and not
  an entrypoint; (3) **coupling/health trend** — fan-in/fan-out per file plus a metric-delta
  summary across the committed snapshot series (codeflow's card-history pattern, free from
  our existing time series). Deep-dive verdict 2026-07-19: codeflow itself REJECTED as a
  ritual component (browser-only app, regex-heuristic edges vs our ast, Node-vm headless
  hack, no Neo4j path) — take the ideas only.

- **`Idea-13`** · 2026-07-18 · `[idea]` · **parked → a catalog/domain owner asks for it** · prio? **Low** —
  **ETL-tooling inventory as a DryDocs domain** (re-inboxed slim from the
  groomed mapping-store line): a gap no catalog covers — DataHub/OpenMetadata inventory data
  assets, not the tooling estate. DryDocs should own it. Context in the mapping-store plan §5
  (internal DataHub adoption).

- **`Idea-11`** · 2026-07-17 · `[idea]` · **closed — research; whitespace confirmed, no item** · prio? **Low** —
  **SaaS knowledge-graph scaffold research (chat)**: no drop-in template exists
  for what DryDocs is. Candidates assessed: Neo4j Labs `create-context-graph` (Apache-2.0 scaffolder,
  FastAPI+Next.js+Chakra — stack mismatch vs ReUI decision, auto-extract-by-default = anti-HITL, no
  lineage/batch-job domains → pattern quarry only: its "one domain YAML drives the whole generated
  app" validates our registry-driven module/QuerySpec design); OpenMetadata (real HITL prior art —
  draft→reviewer→approve glossary/governance workflows — but deliberately NO graph DB, would replace
  the Neo4j core, no Control-M connector); DataHub (Neo4j-backed graph layer architecturally closest,
  but Kafka+ES+MySQL+Neo4j footprint, approval flows largely Cloud-tier, no Control-M). Whitespace
  confirmed: Control-M/batch-orchestration knowledge graph + HITL-gated ontology is uncovered — keep
  building; future options = "publish to catalog" export target (OpenMetadata/DataHub ingestion APIs,
  fits QuerySpec export) and DryDocs-as-template play à la create-context-graph ("pick your
  orchestrator, get a scaffolded support graph") for the standalone-generalization goal.

- **`Idea-10`** · 2026-07-14 · `[source]` · **merged → K16, K17 (the FID half); the ALIAS tier re-read 2026-08-12 as PARKED → a company-side alias table (or a producer-side substitute) actually exists** · prio? **Med** —
  **K2 FID / ALIAS reconciliation tables are company-side unblocks.**
  The attribution loader's TierReconcilers seam ships empty for FID and ALIAS (facts stay
  unresolved, counted in coverage) — tier 2 needs a FID -> seal_id source and tier 4 an
  alias table before those tiers resolve anything. APP_NAME reconciles today from the
  loaded SEAL reference (exact normalized match; ambiguous names excluded).
  CANDIDATE SOURCE added 2026-07-16 (cmdline-lineage-review side finding): FID + SEAL
  are co-located in Control-M FOLDER VARIABLES (env-suffixed FID_D/Q/P alongside a SEAL
  value; the SEAL is also embedded in folder names) — a FID→seal_id pairing may be
  derivable from the already-ingested variables, not only from company tables.
  RE-READ 2026-08-12 (groom) — **the ALIAS half is a wait, not an open question, and the
  FID half has moved a long way since this was written.** Tier 4 resolves nothing until an
  alias table exists to reconcile against; no such source is registered, so there is no item
  to write and nothing for a groom to decide — parked on the source existing. The FID half
  is live and has narrowed twice this week: `K16` (census) and `K17` (the gate) own it, and
  the 2026-08-12 SME answers moved the join off the functional id entirely
  (`UPPER(HR_PHONE_EXP.EMP_LAST_NAME) = CM_DEF_VJOB.OWNER`, directory side normalized only),
  which is a stronger result than the "candidate source" note above anticipated.

- **`Idea-9`** · 2026-07-12 · `[idea]` · **parked → website work starts** · prio? **Low** —
  **dry-docs.com site visual language**: seed from the whitepaper's
  "overnight ledger" identity (greenbar/banner-page/mono-display; canonical source stays
  docs/whitepaper/drydocs-whitepaper.md). Parked until website work starts — the site is
  not started and the domain's availability is unresolved. (Re-inboxed slim at the
  2026-07-13 groom from the artifact-design-review line, sub-item 3.)

- **`Idea-7`** · 2026-07-11 · `[idea]` · **parked → the SME schedules the lineage gate** · prio? **Med** —
  **Lineage live-load gate session** (captured at the G9 close). The Fork-3
  writer is built and REFUSES by design: the four vocabulary entries (m3_invokes / m3_triggers /
  m3_reads_from / m3_writes_to) are `status: planned`, so `write_curated` raises
  GateBoundVocabularyError until the HITL gate flips them active. When the SME schedules that
  gate: review a `plan_curated` output + the lineage-review page for a real extract, confirm
  the vocabulary (and the writer's Script.path key + DataAsset URN mapping), flip statuses,
  first live curated write. HITL-dependent — groom into an item when the gate is scheduled.
  Refs: 0002-C §4/§7, drydocs_lineage/writer.py, tests/unit/test_lineage_writer.py (the gate
  test flips deliberately at activation).

- **`Idea-6`** · 2026-07-10 · `[idea]` · **parked → the remediation gates open (TDD §6/§7 is the tracking surface)** · prio? **Low** —
  **Remediation next slices — tracked in the TDD, not itemized here**
  (captured at the G3 close, same day). What remains after G3/0002-B closed: the Tier-2
  agentic lane (FR-REM-4 — gated on OQ-2 registry shape + OQ-4 agent runtime, both open
  HITL questions), XML I/O (gated on the vendor schema acquisition — company-side .dtd /
  exportdeftable, corpus stub has the fetch list), and the A3 ground-truth watched filename
  + B1 var.text rule (company-side; adjudicates the real M0 unit's equivalence verdict —
  the resolver stays untouched until then). Groom into items only when their gates open;
  `docs/design/drydocs-remediation-tdd.md` §6/§7 is the tracking surface.

- **`Idea-5`** · 2026-07-10 · `[idea]` · **parked → Phase C proper** · prio? **Low** —
  **Phase C packaging (deferred by ADR 0002-A-1 at the G2 relocate)**: the
  pieces deliberately NOT executed in Phase B — (a) make `drydocs-core` independently
  installable (packaging-only commit: per-package pyprojects + path deps, NO file moves),
  (b) the remainder's 4-way component split (load/review/plan/docgen as real packages) and
  load's final name. UPDATED at the G3 close (same day): G3 completed IN-MONOREPO, so
  trigger (a) expired unfired — no early promotion needed; the whole line now waits for
  Phase C proper. Refs: ADR 0002-A-1 §Consequences, PORT-MANIFEST header sequencing note.

- **`Idea-4`** · 2026-07-09 · `[idea]` · **parked → BMC EPD entitlement, or OQ-1 closes company-side** · prio? **Low** —
  **Control-M Workbench as the remediation greenfield test bed — PARKED**
  (user call, 2026-07-09). The Workbench Docker image (dev Control-M, plain `docker run`, no
  Kubernetes/Helm) would let fix packages be DEPLOYED + EXECUTED against a disposable env
  before the Jira handoff — stronger than the offline equivalence proof, still SoD-safe.
  Blocked here: image lives on distribution.bmc.com (not Docker Hub; pull attempt 401) and
  needs an EPD-entitled account + identity token — an entitlement/machine-boundary question,
  not a technical one. Ports 8443/7005 verified free on this box. Revisit when OQ-1 closes
  company-side or entitlement is resolved. Refs: `controlm-api-installation.md` (corpus,
  §Workbench + SYNTHESIZED notes), `drydocs-remediation-tdd.md` §HITL OQ-1. (Control-M for
  Kubernetes / Helm-chart offering deliberately SKIPPED — different product, agents-in-K8s,
  no current use case.)

- **`Idea-3`** · 2026-07-08 · `[doc]` · **parked → the BRD shape settles upstream** · prio? **Low** —
  **BRD outline (Epic L, deferred)** — the third canonical doc type after
  TDD (L1) and Runbook (L8). Parked, not promoted: the BRD is a work-in-progress upstream and
  the user flagged it as "definitely a later phase", so there is no stable outline to write an
  acceptance test against yet. When the BRD shape settles, promote as `docs/design/templates/
  brd.outline.yaml` (reuse the `drydocs.doc-outline.v1` schema + traceability backbone) into Epic L.
  Seed from the corpus: `SDLC-Docs/BRD - Table of Contents.docx`, `business requirements document
  template 31.docx`, `Business Requirements Template - FULL CDI Version.docx`.

## Recently groomed (audit trail)

- **`Idea-226`** · 2026-08-30 · `[chore]` · **groomed → J66 (2026-08-30)** · prio? **Med** —
  **Source-reading guards keep failing on their own prose, and every author invents the fix again.**
  A guard that greps its own source tree for a forbidden pattern also matches the COMMENT that
  explains why the pattern is forbidden. It happened three times on 2026-08-30 alone: G128's
  declared-list guards matched `os.environ` and `${VAR:-default}` in their own docstrings (fixed
  with a local `_code_only()` helper using `tokenize`); G129's no-import guard matched the *text*
  `set_env_var` in three modules that merely name the script in prose (fixed with an AST import
  walk); and G130's purity guard matched `session` and `run(` in its own docstring (fixed with an
  AST call walk). Each fix was correct and each was written from scratch. The consequence is the
  one worth naming: **a guard that fails on the explanation teaches people to stop writing
  explanations**, which in this repo would cost more than the guard is worth. Proposal: one shared
  test helper — `tests/unit/_source_scan.py` or similar — offering `code_only(source)` (tokenize,
  strip COMMENT and STRING) plus `imported_modules(source)` and `called_attributes(source)` over
  the AST, and a note in the testing conventions that a source-reading guard uses it rather than
  a bare `in`. Small, and it removes a recurring authoring trap rather than a bug. Related
  [[G128]], [[G129]], [[G130]], [[J37]].
  **GROOMED 2026-08-30 → J66.** One item, and the count changed at grooming: this entry
  names three instances and a fourth same-named function exists in the vocabulary endpoints
  guard — but that one strips CYPHER comments and literals with regular expressions, a
  different grammar the Python tokenizer cannot parse, so J66 clause (c) fences it out
  explicitly rather than letting a build fold two unrelated things together on a name match.
  All three real call sites were re-verified in the tree before the item was written. Two
  clauses were added that this entry did not state: the location decision is made once against
  the existing shared-suite-module precedent at the tests root (with pytest-does-not-collect
  and both-suites-can-import confirmed at build), and the tempting meta-guard — a test that
  hunts for bare substring tests over source — must be written over the abstract syntax tree
  or declined in the close note, because a text-scanning version of it would match this very
  explanation. The rule itself lands in the root guide's working agreements beside J37.

- **`Idea-177`** · 2026-08-26 · `[doc]` · **groomed → K28 (2026-08-27)** · prio? **Low** —
  `drydocs/fid_census.py`'s module docstring still opens with "Gate ``fid-identity-and-scope`` is
  DRAFTED AND UNSIGNED" — the gate SIGNED 33/33 on 2026-08-19 (recorded in the K16 company
  prompt's rider and the gate log). The docstring's *reasoning* (the census runs before the gate)
  is now history, same as the prompt's rider says of itself. One-line docstring correction;
  noticed during K25 (its sibling module cites the signed state) and left out of that commit
  because it is K16's surface, not K25's.
  **RELOCATED AND GROOMED 2026-08-27.** Captured below the audit-trail heading in an ad-hoc shape
  and invisible to both `test_plan_ideas.py` guards; re-filed with a conforming header. K28 carries
  the correction AND the instruction to keep the ordering rationale as history rather than delete
  it with the stale state. The guard gap that hid this entry is [[I5]].

- **`Idea-176`** · 2026-08-25 · `[idea]` · **groomed → G112 (2026-08-26); the INVOCATION half is recorded inside G112 as a gate question and deliberately not built** · prio? **Med** —
  **G92 put a resolved scope chain in the Control-M extractor, and exactly one
  consumer uses it.** The chain is now built once per run (`_build_scope_chains`) and
  `_resolve_shell` runs shell text through the one core resolver before the file-op
  parse. Two other places in the SAME extractor still read RAW values and would be
  strictly better with it:
  **(1) THE G97 ARTIFACT PASS.** `_artifact_pass` skips any `ETL_ARTIFACT_URI` whose
  value still holds a `%%ref` and counts it as `artifact_values_unresolved`. Many of
  those are resolvable right now — the chain is already in hand two methods away. This
  was NOT folded into G92 because G92's acceptance is explicit about file-op operands
  and its counters are file-op counters; widening it would have silently changed G97's
  tested numbers in the same commit that established them.
  **(2) INVOCATION TARGETS.** The CMD_LINE pass deliberately still parses the VERBATIM
  command for invocations (G92 resolves only the file-op half). That was the right call
  and should stay a decision rather than drift: invocation identity is already
  env-stabilised by `_stable_invocation_key` (DPL pipeline GUID, Ab Initio basename),
  and re-keying it on resolved text would move a signed ruling (cmdline-lineage-review
  2026-07-16). If this is ever revisited it is a GATE question, not a build.
  **WHAT IS ALREADY TRUE AND NEEDS NOTHING:** the resolve counters
  (`resolve_resolved` / `residue` / `unresolved` / `nothing_to_substitute` /
  `no_scope_chain`) ride the existing `ExtractCoverage` summary line, so the yield of
  any widening is measurable in the place the other counters already land.

- **`Idea-175`** · 2026-08-25 · `[idea]` · **groomed → G113 (2026-08-26) — the three-way rule (shared AND the same mount source = confirmed) is the item's acceptance** · prio? **Med** —
  **G56 now DERIVES `storage_scope`, but the two places that act on multi-host
  identity still behave as if it were always `unknown`.** Left out of G56 on purpose:
  that item's acceptance and inputs are the collector and the extractor, and this is a
  CLAIM-LAYER change with its own judgment in it.
  **(1) THE STALE FLAG.** `drydocs_lineage/writer.py` computes
  `unconfirmed = len(node_hosts) > 1` and stamps `identity_unconfirmed_across_hosts`
  without reading scope at all. Under the D1 ruling + the D-amendment that is right for
  `local` and `unknown` and WRONG for `shared`: one NFS export seen on twenty hosts is
  one file, and flagging it queues twenty non-findings for SME review. The two comments
  that say "until G56 lands" (writer.py, at the `storage_scope` setdefault and at the
  `unconfirmed` line) were re-pointed here at the G56 build rather than left reading
  false; the LOGIC is untouched, so nothing changed behaviour.
  **(2) THE CAVEAT THAT MAKES IT MORE THAN A ONE-LINER, and the reason it is not a
  trivial fix.** `storage_scope: shared` does NOT by itself prove two hosts see the SAME
  file — two hosts can both mount nfs4 at `/home/svc` from DIFFERENT exports. Confirming
  identity needs MOUNT SOURCE equality (`synthfiler01:/export/apps` on both), and the
  source is captured in `mounts.tsv` and stamped as `mount_source` on every record
  precisely so this is cheap when it is picked up. So the rule is three-way, not two:
  shared AND same mount_source → confirmed · shared but DIFFERENT source → still
  unconfirmed (and worth its own count, since it is a real finding) · local or unknown →
  unconfirmed, unchanged.
  **(3) DOWNSTREAM ALREADY WORKS AND NEEDS NOTHING.** `drydocs_lineage/archival.py`
  reads `storage_scope` off the occurrence records and gates the misdeployment bucket on
  `local` (G58 §c) — it was written against this shape and goes live on real values with
  no edit. Named here so a groom does not re-open it.

- **`Idea-174`** · 2026-08-25 · `[task]` · **groomed → P6 (the data-center collision probe, internal-only, any-rows routes to the gate) + N17 (the ripple sweep, now desk work)** · prio? **High** —
  **Two live-psgmgr probes lost their only home when `docs/next-internal-session.md`
  retired, and one of them BLOCKS any multi-DC load.** The checklist was the recorded
  owner (its own audit trail says the DC-collision check was "ALREADY ROUTED to the
  internal-session checklist"), so deleting it without this capture would have dropped
  them silently.
  **(1) DC-COLLISION IDENTITY CHECK — HIGH (advisor-confirmation §2a).** One query:
  `SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) FROM psgmgr.CM_DEF_VTAB GROUP BY TABLE_ID
  HAVING COUNT(DISTINCT DATA_CENTER) > 1;` Staging keys by `(data_center, folder_id,
  job_id)` but graph identity is `(folder_id, job_id)` — zero rows means document the
  uniqueness invariant in `controlm_folders.cypher`; ANY rows mean cross-DC nodes
  silently merge and the fix is an IDENTITY change (data_center into the folder + job
  keys) → HITL gate + constraint migration. The single-DC pilot structurally cannot
  expose this, and it has become MORE urgent, not less: the 2026-08-24 SME direction
  (Idea-169/170) commits to per-DC extraction over THREE DCs, which is exactly the
  regime where a TABLE_ID reused across DCs merges two different folders into one node.
  Run it BEFORE the first multi-DC load, not after.
  **(2) ctlm_id RIPPLE SWEEP — now DESK WORK, no login needed.** Which other CM_ views
  carry the derived `ctlm_id` (folder_id.job_id), as join-upgrade candidates over the
  weak SCHED_TABLE / JOB_MEM_NAME joins? When this parked (2026-07-14) it needed live
  queries; doc 08 Phase 2 (step 220, 2026-08-25) has since censused all seven psgmgr
  objects with complete column inventories, so the answer now reads off
  `config/source-mappings/psgmgr.yaml` — with the one known negative already recorded
  (CM_AVG_RUN carries NO ctlm_id; the 2026-07-22 relay proved it). Fold the outcome into
  the column ledger rather than a new doc.
  Checklist disposition for the record: items 1/6 were ticked done; 2 (E1), 8
  (software-usage-patterns) stay owned by their live item and the pending-gates list; 3
  superseded by K6/K16/K17; 7 by G12/G13/G22/G23; 9 by M3's signed gates.

- **`Idea-171`** · 2026-08-24 · `[idea]` · **groomed → G111 (2026-08-26, the residue only); clauses 1/3/4 were RULED into ADR 0014 on 2026-08-25 and built by G105** · prio? **Med** —
  **Logging is configurable globally or not at all; it needs to be configurable BY KIND, and
  `kind` is not yet a thing the code knows about.** User direction, 2026-08-24, taken while
  reviewing ADR 0014 clause 3. MEASURED FIRST (desktop, `C:\coding\projects\logs\DryDocs`,
  J18): 86 files / 396 KB in one flat directory — 84 loader run logs plus a 2-file graph-QA
  ledger (54 entries, 18.9 KB, 40 `llm_call` + 14 `run` lines over 14 run ids). One directory,
  one level, no retention, and the level field is read by nothing.
  **WHY IT CANNOT BE CONFIGURED TODAY:** `kind` is a filename convention, not a code concept.
  Three independent sites mint it and none of them agree to anything —
  `run_log.py:147` hardcodes the literal `load.` prefix, `llm_ledger.py` hardcodes
  `qa.graph_qa`, and `sql_run_log` accepts a caller-supplied `base_name` with no prefix
  enforcement at all, so that family can currently write any kind it likes. Nothing can be
  configured per kind while no declaration says what the kinds ARE.
  **TWO FINDINGS THAT CAME OUT OF THE SAME MEASUREMENT, both worth carrying into the build.**
  (1) ADR 0014 clause 3's naming rule `<kind>.<name>.<YYYYmmdd-HHMMSS>` matches **5 of 86
  files**. The other 79 read `load.<name>.v1.<ts>.log` — and the `v1` is INSIDE `loader_name`,
  not a fourth field, so the rule is not wrong by one segment, it is describing the wrong
  shape. The ledger is therefore not "the one exception" the clause calls it; the clause was
  drafted without counting.
  (2) The `run-logs` zone in `config/data-zones.yaml` declares `env: DRYDOCS_LOGDIR` and
  `data_zones._resolve()` ignores the field entirely, handling only `base: home` and
  `base: data_root`. With the variable set, the zone resolves to the untouched default
  (`~/logs/DryDocs`, 11 stale files) while every real log lands elsewhere — and G81's
  declared-equals-resolved guard misses it because that guard only walks zones with a
  `helper`, which `run-logs` has as null. G109 made this WORSE by widening
  `drydocs landing-zones` to report the zone: it was invisible before and is now reported
  confidently and wrongly, which is the exact failure that command exists to prevent. The
  root-resolution half of this proposal fixes it by construction, and the guard gap needs
  closing whether or not the rest lands.
  **PROPOSED SHAPE — `config/log-kinds.yaml`, schema `drydocs.log-kinds.v1`,** following the
  `config/data-zones.yaml` idiom this repo already uses (declare in YAML, resolvers derive,
  a guard asserts they agree). One `root` block carrying base/path/env — one place resolves
  the variable, so finding (2) cannot recur. A `defaults` block (level, retention_days,
  rotation `per-run|per-day`, format `log|jsonl`, dir). Then one entry per kind naming its
  `writer`, overriding only what differs: `load` inherits everything; `qa` takes
  `rotation: per-day`, `format: jsonl` and a longer retention, because it is an append-only
  ledger whose `run` line is the ONLY place full question text lands (`:AgentRun` carries
  sha256 + length), so its value is that one file reads end to end; `sql` is declared so the
  family that accepts any `base_name` becomes checkable; `api` is declared
  `status: planned` for ADR 0014 clause 6, so the kind exists before its writer does.
  Optional per-kind `dir:` and a `DRYDOCS_LOGDIR_<KIND>` override generalize the sister
  project's `<INTEGRATION>_LOG_DIR` pattern that Idea-152 captured.
  **THE GRAMMAR THEN DERIVES INSTEAD OF BEING ASSERTED:** `<kind>.<name>.<stamp>.<ext>`,
  where stamp granularity comes from `rotation` and `ext` from `format`. Under that,
  `qa.graph_qa.20260820.jsonl` is CONFORMING rather than excepted — which dissolves ADR 0014
  clause 3's self-flagged weakness ("one exception in a naming rule is how naming rules die")
  without needing the exception at all. `<name>` stays free-form, which is what makes the 79
  `.v1` files conforming too.
  **Relationship to the ADR chain, so this is not groomed as a duplicate:** ADR 0014 clause 1
  gives ONE `RuntimeSettings` group with a single `log_dir`/`log_level`/`log_retention_days`.
  This is that clause widened from one global set to a per-kind declaration, and it should be
  ruled ON the ADR rather than after it — G105 implements clause 1 and would otherwise build
  the global shape first and have it widened immediately. Clause 3 is superseded by the
  derived grammar above. Not started; no code written.
  **OUTCOME 2026-08-25:** ruled into ADR 0014 as amendments to clauses 1 (per-kind
  declaration), 3 (derived grammar, ledger exception withdrawn) and 4 (retention read from
  the declaration), with G105's acceptance given a rider so it builds the amended shape.
  **WHAT STAYS OPEN, and it is not covered by any of those:** `data_zones._resolve()`
  ignores a zone's `env:` field, and G81's declared-equals-resolved guard only walks zones
  carrying a `helper`, so `run-logs` (helper null) is unguarded and resolves to the wrong
  directory whenever DRYDOCS_LOGDIR is set. The ADR's clause 1 fixes the class by giving
  the log root ONE resolution site, but that is a forward fix: the guard gap and the
  currently-wrong zone need closing on their own, and `drydocs landing-zones` reports that
  zone confidently and wrongly until they are. Groom as a separate item.

- **`Idea-169`** · 2026-08-24 · `[task]` · **groomed → G115 (2026-08-26); the first multi-data-center LOAD is gated on P6, which G115's acceptance names** · prio? **High** —
  **The Control-M extracts have no data-center dimension, and the estate is too big to pull
  in one go — they need to run individually, per DC, in stages.** *(User direction
  2026-08-24.)* **MEASURED, not recalled:** neither `controlm_folders.sql` nor
  `controlm_jobs.sql` filters on `DATA_CENTER`. The scope binds are `:folder_filter`,
  `:run_as` (jobs only), `:developer_sid` and `:row_cap` — built by `_scope_binds()`
  (`drydocs/cli.py`) and exposed as `--folder` / `--run-as` / `--developer-sid` /
  `--row-cap`. The siblings are the same: variables share those four,
  `controlm_hosts.sql` has `:grpname_filter` + `:row_cap`, `controlm_avg_run.sql` has
  `:folder_filter` + `:row_cap`. So a run today pulls **every** DC present in
  actively-scheduled folders, and `controlm_folders.cypher` mints one `:ControlMServer`
  per distinct `DATA_CENTER` — non-production included. `--folder` is the only lever and
  it filters the wrong axis.
  **THE SCOPE:** three production data centers, run one at a time — `T012-E0700-IB`,
  `T014-E0700-ANY`, `T032-E0700-DMA` in the publishable spelling (the J13 environment-letter
  swap; real values live in `internal/standards/technology/data-center-inventory.md`).
  **WHY STAGING IS NOT OPTIONAL, with the numbers the 2026-08-24 census produced:** raw
  object sizes are CM_DEF_VJOB 1,089,358 rows · CM_DEF_LNKI_P_VW 1,293,560 ·
  CM_DEF_LNKO_P_VW 1,318,968 · CM_DEF_SETVAR_VW **4,716,529** · CM_DEF_VTAB 76,364. The
  extract scope (`IS_CURRENT_VERSION = 'Y'` + `USER_DAILY IS NOT NULL`) already cuts jobs to
  ~240,600 across four DCs, and the per-DC split (internal twin, capture 2026-06) runs
  2,230–7,914 folders and 42,688–85,202 jobs per DC — so **per-DC is a fraction of the
  estate, and variables is the object that actually forces staging**, not jobs.
  **THE DBA ASK IS ALREADY WRITTEN, AND IT IS ALREADY DC-SHAPED:**
  `drydocs/loaders/sql/ddl/controlm_staging_ddl.sql` is a DBA implementation script —
  Section 0 pre-flight (is `TABLE_ID` unique across DCs? the design assumes the composite
  key defensively), Section 1 base read views, `stg_run.data_centers` ("comma list processed
  this run"), every staging table carrying `(run_id, data_center, folder_id, job_id)` with a
  `(data_center, folder_id, job_id)` index, Section 6 grants, full-refresh load pattern,
  sizing < 3M rows / < 2 GB with no partitioning needed. **"Dictate what we need" = hand
  them that file.** What it does NOT yet carry is a per-DC RUN RECIPE (one run per DC vs one
  run listing three), and `stg_run.data_centers` is a comma list, so either shape is
  expressible — the choice needs writing down before the first load.
  **NOT BUILT, deliberately:** no `:data_center` bind was added. The mechanism is cheap and
  changes no projection (one NULL-tolerant bind per extract + `_scope_binds()` +
  `--data-center`; the ledger and the SQL drift guard are untouched because the column set
  does not move), but **which** DCs load is the SME's scope call, and the 22-vs-4 residual
  under gate `controlm-hosts-topology` is still open.
  **THE FOURTH DC — ANSWERED 2026-08-24 (user):** `T021-E0800-ANY`, the largest by folder
  count, is a **deliberate scope cut, not an omission** — the graph and the UI get exercised
  against the three-DC load before more is ingested. So the order is test-then-widen, and the
  three DCs are a first cut rather than the final estate; nothing here rules the DC scope
  call (`controlm-hosts-topology`), which stays the SME's.

- **`Idea-166`** · 2026-08-24 · `[bug]` · **groomed → L29 (2026-08-26)** · prio? **Med** —
  **The load runbook's `--csv` example points at a path that exists nowhere in this repo.**
  `docs/design/drydocs-load-runbook.md` step 3 reads
  `poetry run drydocs load catalog_lobs --csv internal/org/catalog/catalog_lobs.csv`, but
  `internal/org/` holds exactly one file here (`product-overview.md`, from `36ae3828`) and
  `internal/org/catalog/` has never existed producer-side. Every other producer mention of
  that directory is a reference to the COMPANY's copy, not ours — `C26`'s divergence
  ledger, `reconcile-port/SKILL.md`, `30-mappings-catalog.yaml`, and the 2026-07-27 inbox
  line — all citing their 2026-06-25 catalog gate page. So the runbook teaches a
  company-shaped path as if it were a local one, in a doc classified Internal-Public on the
  grounds that it carries bundled sample data only. **Found the honest way:** a company
  session hit the same line, could not find the file, and spent a session tracing why its
  catalog folder kept reverting — the answer had nothing to do with the runbook, but the
  runbook is where the hunt started. **Disposition, not decided:** either repoint the
  example at a bundled sample under `drydocs/data/samples/` so a reader can actually run
  it, or mark it explicitly as a company-side illustration. Do NOT invent an
  `internal/org/catalog/` here to make the line true — real data never lands in this repo,
  which is the whole asymmetry. Note the line was touched at load-runbook Rev 3 (annotation
  only); the path was not examined then.

- **`Idea-164`** · 2026-08-24 · `[task]` · **groomed → G114 (2026-08-26) — written RED first, per the entry's own rule** · prio? **Med** —
  **The superseded-database guard does not scan the two packages where the stale names
  actually were.** `tests/unit/test_database_names.py` has scanned six packages since G28
  (`SCANNED_PACKAGES`), and `agents/` and `drydocs_docmeta/` are not among them — which is
  precisely where the 2026-08-24 sweep found live-code docstrings naming `ddcontext` and
  `dddocs`, including one (`agents/common/agent_run_writer.py`) whose module docstring said
  *"targeting the ruled database — `ddcontext`, NEVER `drydocs`"* twenty lines above a
  constant reading `drydocs`. The guard could not see either. Separately `SUPERSEDED_NAMES`
  carries `drydocs_docs` (the docmeta plan's WORKING name) but not **`dddocs`**, the real one
  that ADR 0006 §1 rejected — so the one name the fold's §C found declared-but-never-provisioned
  is the one the guard does not blocklist. **Measured before proposing:** running the guard's
  own line-scan logic over `agents/`, `drydocs_docmeta/`, `scripts/`, `libs/` and `web/` with
  `dddocs` added returns exactly **four** hits, all four real, no false positives — so the
  widening is a two-element tuple edit plus one frozenset entry, not a new instrument.
  **The general form is the part worth keeping:** at the fold, every GUARDED surface followed
  and nine unguarded ones did not, and the same runbook proves it both ways — Appendix B stayed
  correct because `test_load_sequence_surfaces.py` derives it, Appendix A drifted because its
  only stated source is a sentence. A third clause could extend the same scan to a small
  DECLARED list of operator docs (the `EXTRA_DOCS` idiom in `test_runbook_currency.py`), which
  would have caught all five doc sites. Deliberately scoped OUT of the sweep commit on the
  user's call — raised here so the choice is visible rather than lost. Whoever takes it should
  write the widening RED first and confirm it names the sites before any fix: a guard that is
  green the moment it is written has proven nothing, which is the same rule N11 already applies
  to an empty census.

- **`Idea-160`** · 2026-08-23 · `[task]` · **groomed → K27 (2026-08-26) — the item must pick ONE disposition and say why** · prio? **Med** —
  **A SOURCE-mode `refresh-teams` now needs an input file nothing produces.** G79 wired
  `pat_team_roles` into the team chain (it was gate-confirmed at C9 and had never run),
  and it binds to `pat:people-report` — so a REAL run,
  `drydocs refresh-teams --source pat:people-report`, resolves THREE files from that
  source's landing zone: `dev_teams.csv`, `pat_product_mapping.csv` and now
  `pat_team_roles.csv`. `scripts/project_pat_team_report.py` (G82) emits only the first
  two, so the third has no documented way to exist. **Not silent** — G78's resolver
  fails before the first write, naming the file and the directory searched, which is
  the whole reason this is a task and not a bug. But the first company-side real run
  will stop there with no instruction on what to do next, which is a poor place to
  learn it. Two candidate dispositions, and the item should pick ONE with a reason:
  extend `pat_projection.py` to emit `pat_team_roles.csv` from the same PAT team report
  (its ledger, `config/source-mappings/pat-team-report.yaml`, would need the role
  columns pinned — G82's `--header-map` discipline, spellings fixed at the first real
  run, never guessed), or declare the file a hand-drop and say so where the operator
  will look. Scope note: this is G82-adjacent (the projection's coverage), deliberately
  NOT G79 — the split's job was to wire the loader and it did, fixture mode included
  (verified live: 6 rows, 0 rejected). FIXTURE mode is unaffected; the bundled
  `pat_team_roles__sample.csv` ships with the package.

- **`Idea-159`** · 2026-08-23 · `[bug]` · **groomed → S15 (2026-08-26); reproduced at that groom on the desktop, 4 failed / 45 passed** · prio? **Low** —
  **Four tests pass in the full suite and FAIL when their file runs alone**, which
  means the suite's green does not mean what a reader assumes it means.
  `pytest -q tests/unit/test_repo_paths.py` alone gives 4 failures, all
  `AttributeError: partially initialized module 'drydocs.cli_docs' has no attribute
  'app' (most likely due to a circular import)` — the parametrized
  `test_content_defaults_live_under_the_resolved_root[drydocs.cli_docs-*]` cases.
  In the full suite something imports `drydocs.cli` first and the cycle resolves, so
  the failure is invisible. **Verified PRE-EXISTING at `origin/main`, not introduced
  by G79** — found while checking whether the G79 split had broken it, and confirmed
  by running the same file alone on main (same 4 failures). Why it is worth fixing
  rather than tolerating: a developer narrowing to one file to iterate gets four red
  tests that have nothing to do with their change, which trains people to ignore red;
  and the cycle it exposes is real (`cli_docs` <-> the composition root), so the
  import graph is telling the truth about a coupling the boundary test permits by
  the `ENTRYPOINT_MODULES` exemption. Likely fix is an import-order-independent
  accessor in the test rather than loosening the module boundary. Whoever takes it
  should check the other `cli_*` domain modules (S8 split them out) for the same
  shape rather than fixing only the two that happen to be parametrized here.

- **`Idea-158`** · 2026-08-23 · `[bug]` · **groomed → J53 (2026-08-26)** · prio? **Med** —
  **`snapshot.ps1`'s board refresh half-failed and reported a traceback with no traceback in it.**
  At this session's close the ritual printed
  `WARNING: board refresh skipped: Traceback (most recent call last):` and nothing more, after
  writing only three of `render_board.py`'s nine outputs (board.html, gates.json,
  enforcement-matrix.json — then stopping before load-map, software-registry, context-types,
  remediation-diff, ideas.html and roadmap.html). Run directly in the same tree seconds later the
  same script completed all nine. **Two separable defects.**
  **(1) The message is useless by construction.** The catch block
  (`knowledge/depgraph-snapshots/snapshot.ps1:97`) prints `$_.Exception.Message`, which for a
  failing NATIVE command is the first line of stderr — and the first line of a Python failure is
  always the literal `Traceback (most recent call last):`. So the warning can never name a cause:
  it reports the banner and discards the exception. Capture the command's full stderr and print
  the LAST line (the exception type and message) or the whole block.
  **(2) The refresh is "best-effort" and a PARTIAL run is indistinguishable from a skipped one.**
  The step is wrapped so it never blocks the snapshot, which is right, but a half-written render
  set is worse than none: the surfaces it did write are current and the six it did not are stale,
  and the stale-render `git diff --quiet` check in the ritual runs against whatever it produced.
  Nothing says which outputs landed. This is the Idea-111 shape again — an instrument whose
  failure mode is silence, inside the ritual step added to stop exactly that.
  **Root cause on this machine, for the reproduction:** the Claude Code shell pre-sets
  `VIRTUAL_ENV` to `agents\.venv`, and `poetry run` inside the script inherits it, so the import
  resolves against the wrong environment partway through. A user's own terminal is unaffected,
  which is why this has never been seen interactively — and is a second reason the message needs
  to name the cause rather than the banner. Mechanism-only, no gate.

- **`Idea-165`** · 2026-08-24 · `[bug]` · **done (2026-08-24)** · prio? **Med** —
  **A SKILL still routes agents into two databases that do not exist**, which is worse
  than the stale prose swept at `703c2019` because a skill is executable guidance rather
  than description. `.claude/skills/data-context-extractor/` carries **18 sites** across
  five files instructing an agent to give document DataAssets `trust: SYNTHESIZED` and
  **target `ddcontext`** (`SKILL.md` x8 — including the `description:` frontmatter that
  decides when the skill is invoked at all — `references/platforms.md` x4,
  `cypher-patterns.md` x3, `nodes.md` x2, `use-cases.md` x1). `cypher-patterns.md` goes
  further and emits `CALL { USE ddall.ddcontext ... }` — a cross-database query against a
  composite retired 2026-08-18 for federating one database. Both names died at the G32/G102
  fold. **Why this was left out of the sweep rather than fixed with it:** the sweep replaced
  descriptions of where content LIVES, which is mechanical. This skill encodes a RULING about
  where SYNTHESIZED content goes, and the fold's answer — one database, `:Uncertain` as the
  LABEL, trust as a property of the row rather than of the storage location — is the gate's
  §B, so re-pointing it is a decision to make deliberately and not inside a prose pass.
  `.claude/**` is canonical-producer, so it ports as-is. Whoever takes it should re-point
  the two `USE ddall.ddcontext` blocks first: those are not just wrong, they cannot run.
  **DONE 2026-08-24.** All 18 sites re-pointed, and the substitution is the fold's own
  ruling rather than a rename: SYNTHESIZED content is written to `drydocs` carrying the
  **`:Uncertain` LABEL**, so separation is the label and not the location. The trust axis
  itself (VERBATIM / GROUNDED / SYNTHESIZED) did not move and is untouched. The
  `CALL { USE ddall.ddcontext ... }` subquery became an ordinary
  `MATCH (seg:BusinessSegment&Uncertain)` — worth keeping because it is the clearest
  statement of what the fold bought: the federated hop was not replaced, it stopped being
  needed. The gate's §B reason now sits in `references/platforms.md` where an agent reading
  the skill meets it — keying trust on where a row was stored is the root cause, because a
  query that has to cross databases cannot rank what it finds. Two mentions of the dead
  names survive on purpose, both inside a comment that says they retired.

- **`Idea-161`** · 2026-08-24 · `[task]` · **done (2026-08-24, laptop `NewThinkpad`)** · prio? **Med** —
  **The wave-2 base is CERTIFIED: `port-base-20260824` @ `68b53716`, preflight 7/7.**
  All three named blockers cleared plus the relay defect. **(1) Ledger coverage** —
  the estimate in the original entry was wrong and the correction is the useful part:
  **136 uncited commits, not ~45**, across a 179-commit range. The gap is not a
  miscount, it is a rule: `is_ritual()` matches the subject `chore(backlog): claim`
  and NOT `chore(<item-id>): claim`, so 27 claim commits in this range read as
  substantive to the checker. Deliberate narrowness — matching `chore(*): claim` at
  large would let real work hide behind the word — so the cost is a footnote list,
  now written down in the footnote itself rather than left for the next roll to
  rediscover. Steps **178-213** were written, 36 of them; five are called out in the
  roll note as behaviour-changing or delete-something-you-hold (195 the cli split,
  209 `refresh-reference` gone by name, 210 the mandatory data root, 188 the
  vocabulary-id migrations, 212 the untracked review). **(2) Cited paths** — the
  `internal-local/` transcript took the `status: DATED RECORD` treatment exactly as
  the entry predicted; the two `drydocs_lineage/extractors/controlm_output.py`
  citations were reworded to name the planned module without claiming a file (MM7
  writes it; writing it here would have been scope). **(3) The relay defect** — the
  G81 block became **RELAY-12** inside the parsed section; verified the parser now
  enumerates 1-12. **(4) The tag.**
  **ONE THING THIS ENTRY DID NOT PREDICT, and it is the reason the ritual has a CI
  step:** the roll went RED on CI while the same suite passed locally. Step 212 cites
  `docs/reviews/port-review-7c18ff4b-20260820.md`, which `103f240c` untracked but
  which is still **present on this laptop's disk** — the currency guard asks the
  filesystem, not git, so it resolved here and nowhere else. Any machine that ever
  held the file gets the same false pass. Fixed as a `HISTORICAL_PATHS` entry
  (`3b4d8e76`) whose reason carries the trap, and **verified by moving the file aside
  and re-running**, not by trusting the local green. Related: [[Idea-111]] is the same
  class — an instrument whose failure mode is silence.

- **FILED 2026-08-23 (laptop, dispatched groom — the run that followed 2026-08-22's)** — **Promoted 1, inboxed 0, merged 1. The inbox was empty of ungroomed notes** — the earlier fork of this same session had swept it hours before (commit `81f1eb08`, the FILED entry below), and `feat/ui-workstream` was checked too: its only inbox difference is that it sits BEHIND `main`, so no branch-side note is owed. **No new `[question]` was parked**, and no inbox entry was re-annotated: the open ones are the same user/SME calls the run below already named, and a second "re-checked" line a day later is noise, not an audit trail. **Both durable changes came from checking which Ready-to-pull items were safely dispatchable, which is where a groom with no notes earns its keep.** **PROMOTED — S13:** all SIX per-domain command modules the S8 split created on 2026-08-21 (`cli_schema`, `cli_ingest`, `cli_verify`, `cli_variables`, `cli_docs`, `cli_plan`) **fail to import as the first import of a fresh interpreter** — `python -c "import drydocs.cli_docs"` raises `AttributeError: partially initialized module ... has no attribute 'app'` at `drydocs/cli.py:955`. Each module opens with `from drydocs import cli as _root`, so the root's body runs to its closing merge loop and reaches back for an `app` the still-importing module has not defined yet. `import drydocs.cli` succeeds — and that is the ONE import CLAUDE.md's smoke test names, so nothing ever went red. The visible symptom is a **false red**: `pytest tests/unit/test_repo_paths.py` alone is 4 failed / 45 passed while the same tests inside the full suite pass (2328 passed, 9 skipped). p2 — the shipped CLI is unaffected because the real entry point imports the root first; every other way in is not. The item requires the guard to run each import **in its own subprocess**, since an in-process check cannot fail once `sys.modules` is primed — the very mechanism that hid it. Reproducible from the repo in any checkout, so no venue pin is owed (J18). **MERGED — J42** — the port-time backlog-union guard, p1 and sitting in the Ready-to-pull strip — was written 2026-08-11, nine days before **Y2** sharded the backlog, and its acceptance still aimed at `docs/restructure/backlog.yaml` and its `items[]` key. That file is a **TOMBSTONE**, so the guard as specified would have read two empty id sets, reported "no difference" and **passed for being wrong** — the exact J26 failure the item exists to close, reproduced inside the item itself. Repointed at the sharded grain (the entry IS the file, ADR 0013 Clause 6, so the id set is the directory listing or `backlog_store.load_backlog_document()`), with two tightenings so it cannot go vacuously green again: an **absent or empty items directory must FAIL** rather than read as agreement, and a **filename-vs-inner-id mismatch** is now in scope. The never-regress-a-status half was fenced out to **J16**, which already owns it. Scope unchanged otherwise, and no ruling was needed — `PORT-MANIFEST.yaml` already carries the same promise at file grain ("Never drop a file; never regress a status", F4 ruling 2026-08-20). **A sweep of every other citation of the tombstone** across the 504 item files found them all inside **done** items, where naming the old path is correct history; J42 was the only live one. A parallel check of every open item's `inputs:` for paths that do not exist returned only legitimate forward references (G105-G109 → the ADR G104 will write) and machine-local `internal-local/` transcripts.

- **FILED 2026-08-22 (laptop, groom of the open inbox)** — **Promoted 5, inboxed 0 new, merged 0, marked-in-place 1.** New items: **Q26** — G32 §A rests blast-radius on `corpus_id` scoping and the loaded graph has none (all 28 live `:Document` rows group under null, because only the Q13 loader stamps it); the item makes the SIGNED claim true as written (stamp + reload, per machine) and says in writing that narrowing the claim instead would be an ESCALATION to the gate, never an item's decision. **Q27** — Idea-86 **UNPARKED: its named trigger fired.** The entry waited on "G32 rules `target_db`"; the gate signed 32/32 on 2026-08-18 and G102 applied the fold, so `target_db` has exactly one legal value and the internal MWAA docs can register (registration only — `confirmed: false`, no loader may write). **U27** — snapshot.ps1's CI check asks `gh run list --branch main` and matches LOCAL HEAD against it, so from any branch HEAD can never appear and the verdict degrades to no-run-yet permanently; five fixtures for a verdict function its own design note calls pure and which has no tests. **R23** — the R5 in-band handshake writes the drydocs-api session token into `agents/graph_qa/.adk/session.db` in cleartext once per turn, no expiry, never pruned (p1; `.adk/` is gitignored, so no commit-boundary leak). **J52** — Idea-154's consequence half: verification evidence about a local dev server counts only when the session launched the browser itself. **One marked in place, not moved:** Idea-154 — the two-browser diagnostic needs both machines in hand and stays the user's step. **Trigger sweep:** all parked entries re-read; ONE had fired (Idea-86 → Q27). Idea-29 (gate `email-dl-contact-point` — a 2026-08-12 `RECORD:` is not a sign-off) and Idea-27 (still only the cosmetic O2 toggle) re-checked and NOT fired, noted on the entries; the rest wait on external triggers (SME scheduling, company network, sibling-repo work). **No note was parked as a new `[question]`** — every open entry was either actionable or already the user's. **No plan change**: every item lands in an existing epic and phase. **Left for the user or the SME, unchanged and named so they are not mistaken for oversights:** Idea-104 (which MFT route-id shape is real — re-checked, still unowned), Idea-93 (E1's status), Idea-74, Idea-34, Idea-33, Idea-32, Idea-28, Idea-17, Idea-16, Idea-141's four packaging questions, and Idea-154's two-browser check. **One citation corrected outside the inbox:** R18's notes cited "Idea-151" for the cleartext credential, which is the BRANCH-side number — repointed at R23/Idea-155. **And one stale roadmap row exposed:** retiring Idea-86's `roadmap.yaml` estimate turned `test_real_roadmap_cites_only_live_inbox_ideas` red on **Idea-88** as well — that row should have been retired on 2026-08-13 when the entry became Q18, and survived nine days only because the guard matches a SUBSTRING and Idea-86's body happened to cite `` `Idea-88` ``. Both rows are retired in this commit.

- **`Idea-157`** · 2026-08-22 · `[bug]` · **groomed → Q26 (2026-08-22)** · prio? **Med** —
  **The 28 live Documents carry NO corpus_id — G32 §A's blast-radius story leans on a property
  the pre-fold loads never wrote.** Found at the Q14 evidence pass (laptop, `neo4jtest`,
  `drydocs` DB — J18): `MATCH (d:Document) RETURN d.corpus_id, count(*)` → all 28 rows
  (27 bmc-docs + 1 essential-graphrag) group under `corpus_id: null`. G32 §A ruled that
  load-separation and blast-radius in the one database "are satisfied by corpus_id scoping",
  and `docs-verify`'s graph_locator matches on `corpus_id` — but only the Q13 vendor-docs
  loader stamps it; `bmc_docs.cypher`'s R3 reload evidently does not (or the laptop's reload
  predates the stamp). Either the bmc-docs/essential-graphrag loaders gain the corpus_id
  stamp + a backfill, or the fold's scoping claim is narrower than the gate-log reads.
  Not chased inside Q14 (drydocs-load layer, not ontology). Sibling context: [[Idea-154]]'s
  venue discipline is why the machine is named.

- **`Idea-156`** · 2026-08-21 · `[bug]` · **groomed → U27 (2026-08-22)** · prio? **Med** —
  **The snapshot CI check can never see a branch, and the verdict still has no tests.** Filed on
  `feat/ui-workstream` as its Idea-152 and re-filed here at 156 because both 151 and 152 were
  taken on `main` by unrelated entries while the branch sat unmerged. **Half of the original
  report is already fixed and is recorded here only so the fix is not re-done:** the report's
  defect (1), `Get-CiVerdict` never enumerating the runs array so `$mine[0]` was the whole
  ten-run array and `conclusion -eq "success"` was true if ANY recent run passed, was fixed on
  `main` by `22b8ad7` and then properly by `5c0308e` (`knowledge/depgraph-snapshots/snapshot.ps1`
  now assigns the parse and unrolls it explicitly, with the PS 5.1 trap written down at the
  line). **What is still open is defect (2):** the caller runs
  `gh run list --branch main --limit 10` and matches the LOCAL HEAD against it, so from any
  branch — which is what CLAUDE.md instructs for worktree, epic-slice and agent work — HEAD can
  never appear until merge and the check degrades to the yellow no-run-yet path permanently. The
  branch this was filed from is the worked example: CI was green on `feat/ui-workstream` and
  invisible to a query pinned to `main`. Fix: pass the current branch via
  `git rev-parse --abbrev-ref HEAD` instead of the literal `main`. **Also still open, and the
  reason the first defect shipped at all:** the verdict is a pure function of (runs, head) by its
  own design note and has NO tests — add fixtures for green-at-head,
  failed-at-head-with-older-success, in-progress, no-run-yet and empty. The empty case is the one
  that would have caught it. Sibling of [[Idea-150]] in the same script: that one loses the JSON
  write from a worktree, this one mis-reports the step before it. Mechanism-only, no gate.

- **`Idea-155`** · 2026-08-21 · `[bug]` · **groomed → R23 (2026-08-22)** · prio? **High** —
  The Ask control token is persisted in cleartext in the ADK session store. `web/src/ask/askApi.ts`
  sends the drydocs-api session token as an in-band message part
  (`{"drydocs_control": {"api_token": ..., "api_url": ...}}`, the R5 handshake in
  `agents/graph_qa/control.py`), and ADK writes every message part verbatim into
  `agents/graph_qa/.adk/session.db`, so the raw bearer token lands on disk in the `events` table
  once per turn. Observed 2026-08-21 on this desktop in session `ask-jdoe4821-wjtacr8x` — the same
  token appears in all three user events. Two things make it worse than a stray log line: the token
  has no expiry (`InMemorySessionStore.issue` mints `secrets.token_urlsafe(24)` and only `revoke`
  or an API restart ends it), so a copy taken from the file is replayable for the life of the API
  process; and the store is never pruned, so tokens accumulate. It also contradicts the envelope's
  own privacy stance one row over — `Envelope` deliberately reduces question text and caller
  identity to sha256 plus length so neither is persisted, while the credential beside them is
  written raw. `control.py` states that control parts never reach the LLM, which holds, but says
  nothing about persistence; that is the gap. Not a commit-boundary leak: `.adk/` is gitignored
  (`.gitignore:25`), so nothing reached the repo. Fix direction — strip the control part from the
  event before ADK persists it, or redact the value on write and keep the token only in process
  memory for the turn; add a regression test asserting no `api_token` value appears in
  `session.db` after a run, and purge the existing file since its tokens are live until the API
  restarts.

- **`Idea-86`** · 2026-08-07 · `[source]` · **groomed → Q27 (2026-08-22, UNPARKED — the named trigger fired: G32 signed 2026-08-18, G102 applied)** · prio? **Med** —
  **Register the internal MWAA documentation as a doc corpus — blocked on `target_db`,
  which G32 owns.** The internal MWAA implementation-docs locator saved this session
  (`internal/airflow-reference/mwaa-internal-docs.md`, hung off the `airflow` system
  row's `locator.internal_docs` in `config/source-registry.yaml`, id
  `airflow:internal-implementation-docs`) has NO entry in
  `config/doc-source-registry.yaml`, so `drydocs docs-coverage` reports Airflow as
  `no-corpus` — a true statement, and the exact row the Q16 report exists to print.
  Registering one requires `target_db`, and `tests/unit/test_doc_registry.py` admits
  only `{dddocs, ddcontext}` with no "pending" value — a field G32 is actively
  deciding. **User ruling 2026-08-07: WAIT for G32** rather than declare a value that
  the ruling may reverse. When it unparks, the entry is tier **T2** (internal
  platform), connector **web**, curation **sme-confirm** (fixed per tier), and
  classification **Internal**.
  TRIGGER RE-CHECKED 2026-08-12 (groom) — **NOT fired.** G32 is still `in_progress` (a drafted,
  unsigned gate awaiting the SME), so `target_db` has no ruled value and the user's WAIT ruling
  stands. Worth noting for whoever schedules that gate: the residency question now has a THIRD
  waiting consumer — C34 §(b1) blocks its cross-corpus half on the same constraint (a Neo4j
  relationship cannot span databases), alongside this entry and `Idea-88`. Three parked items on
  one unsigned gate is the argument for scheduling it, not for pre-empting it.
- **FILED 2026-08-28 (ui-workstream worktree, groom of the open inbox)** — **Promoted 7, inboxed 1 new, merged 0, marked-in-place 4.** New items: **O77** — O66 traded one occlusion for the other, so /ownership now paints the relationship chips ON TOP of the node boxes (Idea-188). The note left the reopen-or-refile call to the groomer and it was **filed fresh**: O66 is done and its acceptance genuinely holds, so reopening it would make a verified record retrospectively false; the clause O66 was missing (node names readable too, both themes) travels in O77 clause (b), and clause (a) states that the cause is GEOMETRY, not z-order, so the next attempt cannot pass by flipping the layers again. **O78** MiniDag never adopted RelEdge, so five routes still draw labels behind the nodes (Idea-189) — `depends_on: [O77]` deliberately, or it inherits the inverted occlusion on five routes at once. **U27** the snapshot CI verdict queries `main` by literal and matches the LOCAL head against it, so from any branch it degrades to the no-run-yet path permanently, and `Get-CiVerdict` still has no tests (Idea-156). **R23** the Ask control token is written to the ADK session database in cleartext once per turn and never expires (Idea-155) — p1, filed **drydocs-agents** because the write to disk happens where the control part meets ADK, though the token is minted in `drydocs_api`; the module fork is recorded in the item. **Y6** the pull rule's "a claim ships NO render" is true for claiming an EXISTING item and false for one that MINTS a new one (Idea-198) — documentation only, and Y5's status-only tolerance is explicitly NOT widened, because widening it would forgive the stale render the guard exists to catch. **Z8** the Z1/Z3 and Z5 sample files each built correctly and never meet, so the bundled demo fills none of the map's three dimensions (Idea-193) — fixtures move, the signed T1/T2 tiers and the MATCH-only technology-port ruling do not. **MM11** acronym candidates as a new class on the MM3 extractor, carrying the sentence they were found in (Idea-190) — **the extractor half only**. **One parked as a new `[question]`:** **Idea-199**, where a harvested acronym LANDS — graph nodes with a `LOADER_REGISTRY` row (which mints a label and an attaching edge, so it routes through the HITL gate) or a proposal into the config glossary. The two answers have different modules, different guards and different gate exposure, so the groom would not pick; MM11 was written to be useful under either. **Four marked in place, not promoted, with the reason recorded on each:** Idea-194 (Copier — which layer is templatable at all is a ruling, and the entry says so itself), Idea-192 (Salt — the mandate question is answered; the residue is conditional on Salt ever being costed), Idea-191 (the grid-column checkbox — both readings mint ontology, so the first step is a gate question, not a build item), Idea-154 (the extension-browser locality defect — a standing verification caution; closing it needs both machines in hand). **No plan change:** every item lands in an existing epic and phase, no epic or phase was minted. **Left for the user or the SME, unchanged and named so they are not mistaken for oversights:** Idea-199 (new, above), Idea-104, Idea-93 (E1's status), Idea-74, Idea-34, Idea-33, Idea-32, Idea-28, Idea-17, Idea-16.

- **FILED 2026-08-21 (laptop, groom of the open inbox)** — **Promoted 17, inboxed 0 new, merged 0, marked-in-place 1.** New items: **G104–G109**, the six-item runtime-substrate chain Idea-152 asked for in writing (G104 ADR 0014 DRAFTED-Proposed only — acceptance is the user’s and must reconcile with ADR 0009; G105 the `RuntimeSettings` group + `dictConfig`; G106 `drydocs prune-logs`; G107 per-component `LoaderRunLog`; G108 the API audit line; G109 the data-zone declaration) — filed under **component-topology / phase 6 for want of a runtime-substrate epic, which a groom cannot mint; a dedicated epic is PROPOSED TO THE USER** and taking it moves `epic:`, not ids. **G110** the Idea-141 residue (MODULE_MAP contradicts the boundary test; four agent-runtime dependencies unpinned). **O64–O67** the four console defects (Ask loses the last completed turn; dark mode never reaches the shared controls; /ownership labels render behind the nodes; `ModuleIcon` has no exhaustiveness guard). **R20–R22**, one Ask incident split into three separable defects — stale spec vocabulary, discarded Neo4j notifications, and the synthesized UI term *Tower* proxied onto `:TOMRole`; **module drydocs-api on all three, verified at the groom (the QuerySpec registry is `drydocs_api/query_specs.py`, not `agents/`)**, and R22 carries the gate boundary in its acceptance. **Q23** the scrape-run ↔ registry-row join, bounded by J51’s per-entry FIELD split. **U26** snapshot.ps1’s three-hop sibling resolution, which dies in every worktree — and its test’s skip path resolves it the same wrong way, so the two agree while both are wrong. **Y5** the claim-commit-vs-stale-render contradiction: Idea-151 asked the groom to decide and it did — **option (b), the guards tolerate status-only drift**, because option (a) puts generated files into every claim commit and recreates the shared-line conflict Y2’s sharding removed. **One marked in place, not moved:** Idea-141 — the poetry-group verdict and its four open questions stand; only the residue was groomed. **No note was parked as a new `[question]`:** every open entry was either actionable or already the user’s. **No plan change** — every item lands in an existing epic and phase, with the runtime-substrate epic proposed rather than created. **Left for the user or the SME, unchanged and named so they are not mistaken for oversights:** Idea-104 (which MFT route-id shape is real), Idea-93 (E1’s status), Idea-74 (does DryDocs ingest the SNOW queue/group export, and which side), Idea-34 (the AIS acronym entry), Idea-33 (the unlocated typo), Idea-32 (the Oracle-connection scope), Idea-28 (the tier-1/tier-2 app-code enumeration — SME data entry), Idea-17 (two local relics, destructive), Idea-16 (the SNYK_TOKEN repo secret — no agent can set one), and Idea-141’s four packaging questions.

- **`Idea-152`** · 2026-08-20 · `[idea]` · **groomed → G104–G109 (2026-08-21; the ADR is DRAFTED-only, acceptance is the user’s)** · prio **High** —
  **Log/config substrate: the log directory is env-var-only, two run-log families plus a
  JSONL ledger share one directory under two naming rules with no rotation, and
  `AppSettings.log_level` is wired to nothing.** Captured from a 2026-08-20 survey of this
  repo beside a sister internal project's logging layer (mechanism only; no names or paths
  carried). What the survey found here: (a) `drydocs_core/run_log.py` resolves
  `DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` → `~/logs/DryDocs`; `adapters/sql_run_log.py` honors
  only the legacy var; `agents/common/llm_ledger.py` writes a per-DAY `qa.graph_qa.<YYYYmmdd>
  .jsonl` beside per-RUN `<kind>.<name>.<ts>.log` files; none rotate, cap, or sweep.
  (b) `cli.py:715` is the sole `basicConfig` — level comes from `--verbose` only; stderr
  only; `DRYDOCS_LOGDIR` never receives console output. (c) `drydocs_api` (incl.
  `/raw-cypher`, `/specs/{id}/run`) logs nothing; `drydocs_remediation` (G93), `_lineage`,
  `_docmeta`, `_deepdoc` have no logger; `scripts/external_vendor_scrape.py` prints only;
  `agents/graph_qa/agent.py:70-77` swallows telemetry failures bare. (d) `.env.example`
  documents neither `DRYDOCS_LOGDIR` nor `DRYDOCS_DATA_ROOT`. (e) Data-root drift: registry
  `dpl/` vs code `dpl-registry/`; six code zones (`email-extracts`, `context-intake`,
  `vendor-docs`, `remediation/*`, `cmdline-staging`, `catalog`) have no `source-registry`
  row so `drydocs landing-zones --check` is blind to them; the Confluence capture lands
  in-tree, against `landing_zones.py`'s tracked-only rule. **The pattern worth adopting
  from the sister project**, as a sample: one factory module owning `get_logger(app)`;
  per-key resolution *env var → config-file key → fallback arg → error* over a small
  key file —
  `LOG_ROOT=<base>/log_files`, `CONSOLE_LOG_DIR=<base>/log_files/console`,
  `<INTEGRATION>_LOG_DIR=<base>/log_files/<integration>` (relative = repo-root-anchored,
  env overrides); files `<app>/<stream>_<YYYYMMDD>_<HHMMSS>.log` under a per-app rotating
  handler with a size quota, N-day retention, and a background sweeper. Its recorded
  gotchas are the anti-checklist: level hardcoded with no env override; Linux-absolute
  default that breaks on Windows; silent fallback to the local profile on a misconfigured
  box; process-start timestamp in local time so all files share one stamp; sweeper
  registry growing unbounded when `get_logger` is called with per-incident names.
  **Proposed ADR 0014 "runtime substrate: logs, settings, data zones"** (next free number;
  must reconcile with ADR 0009, which already makes git YAML the settings source of truth):
  (1) one `RuntimeSettings` group (`DRYDOCS_` prefix, pydantic-settings like `config.py`)
  carrying `log_dir`, `log_level`, `log_retention_days`, `data_root` — `.env`-readable,
  env-overridable, defaults unchanged; `SPIDERP_*` kept one cycle as deprecated aliases,
  then `DRYDOCS_*` only on both families (symmetry with the data root, which has no
  legacy var). (2) stdlib `logging.config.dictConfig` from that group, no new runtime dep:
  console + a JSON-lines file sink in `log_dir`, level from settings, `--verbose` still
  wins; `run_log.py`'s header/summary contract unchanged. (3) ONE naming rule for the
  directory — `<kind>.<name>.<YYYYmmdd-HHMMSS>.{log|jsonl}` — and the ledger moves to it
  (or the exception is documented). (4) `drydocs prune-logs` mirroring `prune-snapshots`
  (age + size, dry-run default) instead of a daemon sweeper. (5) every component opens a
  `LoaderRunLog` per batch (G93 generalized to lineage/docmeta/deepdoc/scrape). (6) an API
  request/audit line for every Cypher-executing route, actor hashed like `AgentRun`.
  (7) the data-zone map gets a single declaration — `source-registry.yaml` rows for the six
  undeclared zones, `dpl-registry` reconciled, `data_root.py` resolvers derived from the
  rows — and `.env.example` gains both roots. Groom into: the ADR; a core item (1-3);
  a load item (4); per-component items (5); an api item (6); a config item (7). The
  ask-search logging request (executed Cypher never persisted server-side; only counted
  on `:AgentRun`) is a separate idea once its owner surface is known.

- **`Idea-151`** · 2026-08-20 · `[bug]` · **groomed → Y5 (2026-08-21; RULED at the groom as option (b) — the stale-render guards tolerate status-only drift)** · prio? **Med** —
  **A bare one-key claim commit goes RED in CI: the pushed-claim protocol and the roadmap
  stale-render guard contradict each other.** First hit 2026-08-20 (laptop), the first
  post-shard claim: flipping `items/D10.yaml` to `in_progress` and pushing — exactly what
  the Y2 claim ritual prescribes — failed `test_plan_roadmap.py::
  test_committed_roadmap_page_matches_its_sources` on CI (run 32440366508), because
  `roadmap.html` derives item statuses and the claim commit ships no regen. The close-out
  commit went green, so the failure window is precisely the work interval the claim exists
  to cover — every correctly-claimed item now spends its whole in-flight life with CI red
  at the claim sha, which trains sessions to read red as noise (the exact habit Idea-111
  fought). Either the claim ritual gains "run `render_board.py` in the claim commit" (cheap,
  but no longer one-key) or the stale-render guards learn to tolerate status-only drift
  (scoping question). Groom decides; don't leave both rules standing as written.

- **`Idea-150`** · 2026-08-20 · `[bug]` · **groomed → U26 (2026-08-21)** · prio? **Med** —
  **`snapshot.ps1` cannot find the depgraph sibling when run from a git worktree, so the
  session ritual's last step is unavailable to exactly the sessions CLAUDE.md tells to use
  worktrees.** Line 172 resolves the instrument as `"$here\..\..\..\depgraph"`, three hops up
  from `knowledge/depgraph-snapshots`. From the main checkout that lands on
  `C:\coding\projects\depgraph` and is correct; from
  `.claude/worktrees/<name>` the same three hops land on
  `.claude/worktrees/depgraph`, which does not exist, and the script dies with
  `Resolve-Path : Cannot find path`. Hit at the O57 session close 2026-08-20: everything
  before it succeeded — all renders written, `ci: GREEN at HEAD c583b76` reported by the
  script's own check — and only the JSON write was lost, so the session produced no drift
  record. `tests/unit/test_probe_instrument.py:252` SKIPS for the same reason and with the
  same wrong path in its message (`depgraph sibling checkout absent at
  ...\worktrees\depgraph`), so the two agree with each other while both being wrong about
  where the sibling is. The fix is to resolve the repo's MAIN working tree rather than count
  directory hops — `git rev-parse --path-format=absolute --git-common-dir` gives the shared
  `.git`, whose parent is the main checkout, and it returns the same answer from a worktree
  and from the checkout itself. Worth doing in the same pass for the test's skip path.
  Mechanism-only, no gate. Not fixed inside the O57 session deliberately: this is a shared
  instrument, the ritual step that records repo structure, and it cannot be honestly verified
  from a worktree without also exercising it from the main checkout.

- **`Idea-149`** · 2026-08-20 · `[bug]` · **groomed → O67 (2026-08-21)** · prio? **Med** —
  **`ModuleIcon`'s switch has no `default` and no exhaustiveness check, so a new console
  module renders in the nav as bare text with no error anywhere.** Hit at the O57 build:
  `loadmap` was added to `ModuleId` and to `MODULES`, the page worked, the build and oxlint
  were clean, and the Aside entry simply had no glyph — noticed only because a screenshot was
  being read. The file ALREADY documents the hazard in a comment on the `software` case
  ("this switch has no `default`, so a missing case returns undefined and the glyph silently
  vanishes from both the aside and the Overview hub with no compiler error"), which makes this
  a known trap that keeps being paid for rather than a discovery. The cheap fix is the standard
  TS exhaustiveness guard — a `default` branch assigning the parameter to `never`, so the NEXT
  missing case is a compile error at the point of omission instead of a silent gap on two
  surfaces. Deliberately NOT done inside O57: that item's acceptance is the load-map surface,
  and changing a shared component's return contract is its own change with its own blast
  radius (12 modules + the Overview hub). Mechanism-only, no gate — nothing here touches edge
  semantics.

- **`Idea-148`** · 2026-08-20 · `[idea]` · **groomed → Q23 (2026-08-21)** · prio? **Med** —
  **A scrape run and the registry row it fulfils are not joined — `drydocs-scrape` should
  stamp the `doc-source-registry` id in its run manifest, and the row should carry
  `captured_at` + `manifest` the way `bmc-docs-controlm-utilities` already does.** Found at
  the 7c18ff4b port review: the `cdo-frameworks` row was upgraded to VERBATIM producer-side
  on 2026-08-19 on the strength of a company run that was keyed by SPACE + a free-text
  `--purpose` string, neither of which is a registry id — the SME chose the space by hand
  because the tie-in to the row was not expressible. The join precedent EXISTS one row over:
  `bmc-docs-controlm-utilities` carries `captured_at`, a `manifest:` path to its
  `capture-manifest.json` (capture id stamped by `external_vendor_scrape.py`), and a
  `graph_locator` by `corpus_id`. The fix is mechanism-only: (a) the scrape tool takes a
  `--registry-id` (or resolves `--purpose` to one) and writes it into the run manifest;
  (b) the registry row gains `captured_at` + `manifest` at capture and `graph_locator` at
  load, so a VERBATIM claim traces to a run id instead of to prose ("the 2026-08-19 fetch").
  Numbered 148 at the ui-workstream merge: that branch had already minted Idea-143..147, so the 147 this entry first carried collided and was re-issued here. Sibling of
  the J51 doc-source-registry finding (same review): the fields (b) adds are COMPANY-owned
  facts, which is why that file needs a per-entry row before they exist.

- **`Idea-147`** · 2026-08-20 · `[bug]` · **groomed → O66 (2026-08-21)** · prio? **High** —
  Ownership graph relationship labels are occluded by nodes in the left-to-right K4 qualified-
  attribution layout. `/ownership` shows `EXAMPLE DATA · ILLUSTRATIVE — K4 qualified-attribution
  shape`, but relationship names render behind nodes and are unreadable. Explorer's
  `Tower / app drill-down graph · backs onto drydocs` and Lineage's `Source → target DAG · backs
  onto drydocs` keep relationship names readable as overlays. Ownership should use the same
  readable overlay treatment while preserving dark/light theme tokens, arrows, and the existing
  left-to-right relationship direction.

- **`Idea-146`** · 2026-08-20 · `[bug]` · **groomed → R22 (2026-08-21; the item may declare Tower’s source is NOT the graph, but any BINDING to graph vocabulary routes through the HITL gate)** · prio? **High** —
  Ask question `how many towers are there` returned `0` from generated Cypher
  `MATCH (t:TOMRole) WHERE t.name CONTAINS 'Tower' OR t.name CONTAINS 'tower' RETURN count(DISTINCT t) AS tower_count`,
  while `/explorer` defines Tower as a synthesized UI concept (`Tower / app drill-down graph · backs onto drydocs`)
  backed by the in-repo `TOWERS` definitions. No registered QuerySpec matched, so the router correctly
  escalated to Tier 1; the text2cypher model then selected the real `TOMRole` graph label as a proxy for
  the UI term, but TOMRole is not the Explorer Tower definition. The answer therefore reports 0 towers
  without explaining the semantic mismatch. The UI exposes the safe execution trace (router, generated
  Cypher, rows, timings, source) but not model prompts or chain-of-thought. Add an explicit Tower
  definition/source contract and a registered count spec or semantic mapping so this question cannot
  silently cross from synthesized UI taxonomy to TOM ontology.

- **`Idea-145`** · 2026-08-20 · `[bug]` · **groomed → O65 (2026-08-21; filed p2 against this entry’s proposed High — presentation, not correctness)** · prio? **High** —
  Dark-mode UI contrast defect: the shared React controls on the left vertical rail and the Source
  panel at the bottom right retain the same light-surface styling as light mode. The off-white
  control box is stark against the dark page and does not provide an intentional dark-mode surface.
  Audit the shared control/source styles and theme tokens; dark mode should use the page's dark
  panel/background tokens while preserving readable text, borders, focus states, and source
  affordances. Verify both light and dark screenshots after the fix.

- **`Idea-144`** · 2026-08-20 · `[bug]` · **groomed → R20 + R21 (2026-08-21; the spec/vocabulary half and the discarded-warnings half land in different code)** · prio? **High** —
  Ask test question `how many folders and jobs does each tower support?` routes to
  `explorer.folder-applications.v1`, gets 0 rows, then falls back to schema-grounded Cypher that
  references stale graph vocabulary: `BELONGS_TO_APPLICATION`, `HAS_PORT`, `:Port`,
  `:SchemaMeta`, and `active_state`. Neo4j emits four non-fatal warnings, so the answer presents
  an empty result while Explorer can show synthesized data. Admins cannot currently see those
  warnings: Ask renders only rows/errors, the API runner discards Neo4j notifications, and
  `AgentRun` telemetry stores no warning payload. Fix the registered spec against the current
  graph schema, add a live vocabulary/spec smoke check, and surface warning diagnostics to the
  admin review path without exposing them as an end-user error.

- **`Idea-143`** · 2026-08-20 · `[bug]` · **groomed → O64 (2026-08-21)** · prio? **High** —
  Ask loses the last completed question and answer when navigating to Explorer and back because
  `AskRoute` keeps turns only in component state. Persist the last completed turn per persona in
  browser-local storage for this phase; do not persist in-progress or failed turns, and keep the
  existing TTL-bound explore-ref behavior explicit.

- **FILED 2026-08-19 (desktop, weekly groom of the whole `## Inbox`)** — **Promoted 10, inboxed 0 new, merged 3, closed 1, parked 1.** New items: **Q21** (the `docs_email_concerns` writer — the build the SIGNED `email-folder-assignment` gate authorized and did not build) and **Q22** (the SME assignment surface, the slice the gate named at §B2); **U24** (snapshot.ps1's RED warn prints `System.Object[]`) and **U25** (the debt-metrics ledger); **J49** (the non-render `write_text` sites); **G103** (the rua script-copy convention); **R15/R16/R17** (the gitnexus review's R1/R2/R4 — epistemic labeling, named agent verbs, read-time staleness); **N16** (rule what `source_label` means). **Three merges, deliberately riders rather than new items:** Idea-130 → **Q17** (jpmc-reports as the External-PUBLIC P4 end-to-end candidate — Q17 already owns that corpus's shape decision); Idea-137's union-report half → **N14** (gate §B3 named that report as the home for the unassigned email count, and N14 is still `todo`, so this is a rider and NOT a `depends_on` that would strand Q21); Idea-127's viewer half → **U22** (`viewer.html` already renders the commit; the missing AGE belongs with the detection). **One closed:** Idea-131 was consumed by **G98** the same day it was captured — the gate signed 19/19, `:Company` is registered, both `HAS_BUSINESS_SEGMENT*` edges are entered `status: planned`, and the §D3 endpoint guard the entry called "the reusable half" is built (`tests/unit/test_vocabulary_endpoints.py::test_every_declared_edge_endpoint_is_a_registered_label`); all four verified at this groom rather than taken from the close note. **One parked:** Idea-126 lands in `../depgraph`, not this repo. **Two marked in place, not moved:** Idea-132 (only the `source_label` question groomed out; the ServiceNow re-sourcing record stays standing because nothing is owed producer-side today) and Idea-93 (a third run of its standing stale-`inputs:` check — three refs, two of them false positives of the check; the E1 status question is still the user's). **Nine of the ten enter `next_ready`;** Q22 does not, because it depends on Q21 — the surface has no second write path. **No plan change:** every item lands in an existing epic and phase. **Left for the user or the SME, unchanged and named so they are not mistaken for oversights:** Idea-104 (which MFT route-id shape is real), Idea-74 (does DryDocs ingest the SNOW queue/group export, and which side), Idea-34 (the AIS acronym entry), Idea-33 (the unlocated typo), Idea-32 (the Oracle-connection scope), Idea-28 (the tier-1/tier-2 app-code enumeration — SME data entry), Idea-17 and Idea-16 (both destructive or manual by nature), and E1's status from Idea-93.

- **`Idea-138`** · 2026-08-19 · `[idea]` · **groomed → Q22 (2026-08-19)** · prio? **Med** —
  **The SME email-assignment surface — the later slice whose CONTRACT gate
  `email-folder-assignment` just ruled (§B2, signed 8/8 2026-08-19).** The build presents:
  the email (subject, sent_at, the msg/extract CITATIONS — never the content), the
  propose-only candidates WITH their evidence (prose hits are candidates, never edges —
  §B1), and the unassigned state as first-class (never a nag, never a default). An SME
  action here is one of only two hands that may perform the CONCERNS write (the other:
  a structured-field source signal, which today's assumed contract doesn't have). Grooming
  note: this is company-side-facing (real extracts live there); the producer side owns the
  contract shape and any shared surface plumbing.

- **`Idea-137`** · 2026-08-19 · `[idea]` · **groomed → Q21 (2026-08-19)** · prio? **Med** —
  **The `docs_email_concerns` writer build — the commit that flips the vocab entry
  `planned -> active` (N13 §B1: the build lands the flip; intent never flips anything).**
  Gate `email-folder-assignment` SIGNED 8/8 (2026-08-19): CONCERNS spelling, endpoints
  ControlMFolder | ETLProcess with the class recorded on the edge (rua §B2), required
  `assigned_by` (sme | source-signal) + evidence pointer (O24), and the §B1 bar —
  structured field only performs; prose/subject mentions are propose-only. Since the
  assumed extract contract has NO structured folder/process field, in practice every
  assignment starts SME-performed via the Idea-138 surface. The writer also owns wiring
  the unassigned count into the N13 union report (mechanics = Idea-134's build), and it
  must remove the forbidden-token fence in `test_email_extracts.py` ONLY for its own new
  cypher file — `email_extracts.cypher` itself stays fenced forever (the lexical loader
  never gains the write).

- **`Idea-136`** · 2026-08-19 · `[bug]` · **groomed → U24 (2026-08-19)** · prio? **Low** —
  **`snapshot.ps1`'s RED warn line prints `System.Object[]` where the conclusion belongs.**
  Observed at the 2026-08-19 snapshot: `ci: System.Object[] AT HEAD e0ae9ba - main is RED...`
  — the `-f` arg `$mine[0].conclusion.ToUpper()` (line ~136) stringified as an array, so the
  warn names no conclusion. Cosmetic only (warn-only by design, the RED itself was the known
  billing block: jobs "fail" in 3-5s with no logs), but the line exists so a human reads WHY
  main is red, and right now it can't say. Likely PS 5.1 member-enumeration on `$mine[0]`
  when `gh run list --json` yields nested arrays — pin with `@($mine)[0]` or select the
  property explicitly, then re-run the snapshot to confirm the text.

- **`Idea-131`** · 2026-08-17 · `[bug]` · **closed — consumed by G98 before this entry was ever groomed: gate corporate-backbone-vocabulary SIGNED 19/19 (2026-08-17), :Company registered, both edges entered status: planned, and the §D3 endpoint guard BUILT — verified at the 2026-08-19 groom** · prio? **Med** —
  **`:Company` and both `HAS_BUSINESS_SEGMENT*` edges execute but were NEVER
  registered in the relationship vocabulary — and no guard can see it.** The
  corporate backbone `(:Company {name:"JPMC"})-[:HAS_BUSINESS_SEGMENT]->(:BusinessSegment)`
  is MERGEd by `drydocs_core/schema/ontology.cypher:205-232`, constrained by
  `constraints.cypher:29` (`company_name` uniqueness), documented as *the* corporate
  hierarchy across four `.claude/skills/data-context-extractor/` files, and live in the
  graph (verified: laptop, `neo4jtest`, `drydocs` DB — 4 current + 4 historical edges).
  But `10-node-classifications.yaml` registers `BusinessSegment` and `CatalogLOB` and
  **not `Company`** (57 labels, absent), and no fragment registers either
  `HAS_BUSINESS_SEGMENT` or `HAS_BUSINESS_SEGMENT_HISTORICAL` — only `RECONCILES_TO`
  (`42-local-catalog.yaml`). **NOT a regression:** `git log -S "Company"` over the
  vocabulary returns nothing, so it was never there and there is no ruling to find —
  it is an M0 seed that predates the registry and never got back-registered.
  **WHY NOTHING CAUGHT IT, which is the reusable half:**
  `test_taxonomy_ontology_map.py:134` checks label UNIQUENESS and
  `test_yaml_fragments.py:83` checks fragment KEYS — **nothing cross-checks an edge's
  `from_node`/`to_node` against the registered label set**, so a wholly absent endpoint
  raises no guard. `RECONCILES_TO` passes only because its endpoint happens to be
  registered. That endpoint cross-check is a cheap guard and is the part worth building
  first; it generalizes past this one backbone. This is the exact shape closed for
  `ControlMApplication` (2026-07-09) and deliberately avoided for the `:Port` →
  `:DistributionList` edge, where the node class shipped WITH the edge for this reason.
  **Registering the label + two edges is gate territory** per `docs/RELATIONSHIP_GUIDE.md`
  (`status: planned` first), not a quiet add — but the guard is not.

- **`Idea-130`** · 2026-08-17 · `[idea]` · **merged → Q17 (2026-08-19, as the P4 end-to-end-candidacy rider)** · prio? **Med** —
  **`jpmc-reports` is an External-PUBLIC corpus, so it is the safest first docmeta
  ingestion — SME direction 2026-08-17.** The annual-report / 10-K MD&A source is
  already registered and classified: `config/doc-source-registry.yaml#jpmc-reports`,
  `classification: External` ("public SEC filings / investor-relations PDFs"),
  `source_url` present, `trust_default: VERBATIM`. **Why it is a good candidate
  specifically:** an External corpus carries no publish-boundary risk, so the P4 load
  path can be exercised end-to-end — chunker, embeddings, trust provenance, the
  `:Uncertain` routing — without any of the redaction care an Internal corpus forces.
  The P4 revision (`knowledge/upgrade-plans/docmeta-p4-revision-single-db.md`)
  currently names only the BMC corpus for the end-to-end local load; this is a second
  External candidate for that slot, and it is gate-bound like the rest of P4.
  **Three facts that change the work, all in the registry entry:** (1) it is
  `confirmed: false`, which is the flag N9 says a future loader gates on; (2) its
  current shape is `:DataAsset` slices, **NOT** the lexical `Document→Chunk` shape —
  reshaping is the P4+ decision, not a load; (3) **the ingest path is gone** —
  `scripts/ingest_jpmc_reports.py` was REMOVED 2026-07-22 (recover via git history)
  and the two PDFs were never committed (root `/*.pdf` gitignore precedent), so
  "publishable" describes the DATA, not a runnable pipeline. Re-running it means
  re-fetching the PDFs and writing a loader against the current module shape.
  Related: this corpus seeded the effective-dated `Company`/`BusinessSegment` context
  whose vocabulary registration is the gap in [[Idea-131]].

- **`Idea-127`** · 2026-08-14 · `[idea]` · **groomed → R17 (2026-08-19) + merged → U22 (the viewer half, as a rider)** · prio? **Low** —
  **Read-time staleness hint on estate queries and snapshot HTML.** R4 of the GitNexus
  comparison: surface "indexed at commit X / loaded at T; HEAD is Y / now is T+n" in
  query answers and the depgraph html view — the GitNexus `staleness.ts` contract. Our
  snapshot meta header already pins provenance harder (U7/U15); this is the missing
  *read-time* half. Small; depgraph html profile + `drydocs_api`.

- **`Idea-125`** · 2026-08-14 · `[idea]` · **groomed → R16 (2026-08-19)** · prio? **Med** —
  **Named agent verbs over QuerySpecs (impact/context/trace analogs).** R2 of the
  GitNexus comparison: expose reviewed `drydocs_api` QuerySpecs as purpose-built MCP
  tools — `impact` (blast radius over job chains/conditions), `context` (one
  job/asset/series: owners, schedule, upstream/downstream), `trace` (path between two
  estate nodes) — so agents call named verbs instead of composing raw Cypher against
  the generic neo4j-drydocs server. GitNexus evidence: the verb surface, not the graph,
  is what makes agents actually use it. Pairs with Idea-124 (the verbs carry the
  epistemic field).

- **`Idea-124`** · 2026-08-14 · `[idea]` · **groomed → R15 (2026-08-19; filed p2 against this entry's proposed High — the reason is in the item's notes and is reversible)** · prio? **High** —
  **Epistemic labeling on query answers: `exact` vs `lower-bound` + causes.** R1 of
  [`docs/reviews/gitnexus-depgraph-comparison.md`](../reviews/gitnexus-depgraph-comparison.md):
  lineage/impact-style QuerySpec responses (and depgraph's JSON assertions) declare
  whether the answer is complete — `epistemic: exact|lower-bound` plus a
  machine-readable `causes` split (unparsed `cmd_line`s, unresolved invocations,
  gate-pending edges). Extends the trust axis from the *graph* to the *answer*;
  GitNexus doctrine: an empty result set is not evidence of absence when the causes
  say the walk couldn't see. Ontology-cheap — a property on responses, not the graph.

- **`Idea-121`** · 2026-08-13 · `[bug]` · **groomed → J49 (2026-08-19) — the remaining write_text sites, re-censused at the groom as TEN not eight; the render half landed 2026-08-13 and the guard this entry asked for now exists** · prio? **Med** —
  **RENDER HALF FIXED 2026-08-13; the remaining writers stay open, so this entry stays
  open too.** all 11 `write_text(` sites in
  `plan_board` / `plan_ideas` / `plan_roadmap` / `design_doc` and the six
  `scripts/render_*.py` now pass `newline="\n"`. Verified by re-rendering EVERY surface
  — board, the six generated JSON, roadmap, ideas, load-map and all 16 design docs —
  and getting a clean tree: **25 dirtied files down to 0**. Suite 2150 passed; both
  ruff gates exit 0 (the added argument pushed five lines over the limit, so
  `ruff format` rewrapped them in the same commit). **What stays open:** the other
  eight `write_text(` sites — `vendor_docs` (2), `publishing/publisher`,
  `publishing/preview`, `schema_graph`, `extract_office_text`,
  `external_vendor_scrape` — which this entry deliberately fenced OUT of the sweep.
  They write non-render outputs and each needs its own call, not a blanket change.
  Also still open: whether a guard should pin this (a test asserting no committed
  render surface contains a CR byte would stop it regressing; nothing enforces it
  today). The original finding follows.
  **The renderers write CRLF on Windows, so every render run dirties the committed
  renders with line-ending-only churn.** Found the same day the LF policy landed
  (`fcc8afa` .editorconfig, `b348b0c` `* text=auto eol=lf`): running
  `render_board.py` + `render_ideas.py` left TEN files modified in `git status`, of
  which exactly ONE — `ideas.html` — had a content change. The other nine
  (`board.html`, `roadmap.html`, `load-map.html`, and six `web/src/generated/*.json`)
  differed only in line endings. Mechanism: the writers call
  `Path.write_text(..., encoding="utf-8")` with no `newline=`, so Python text mode
  translates `\n` to `\r\n` on Windows; git normalizes it straight back to LF on
  commit, which is why no blob ever changed and nobody noticed. **Correctness is not
  at stake — legibility is.** The session ritual's stale-render check reads
  `git status` / `git diff --quiet` after a re-render, and a step that reports ten
  changed files when one changed is a step whose signal is buried in noise. That is
  the Idea-111 failure shape (a gate nobody reads) arriving by a different route, and
  it is exactly the "phantom CRLF-vs-LF noise in tools that read the working tree"
  the `.editorconfig` commit named the same morning. Fix: pass `newline="\n"` —
  available since Python 3.10, and the project is `^3.11` (verified present on
  3.12.10). Nineteen `write_text(` sites repo-wide lack it; roughly ten produce
  committed render surfaces (`plan_board` / `plan_ideas` / `plan_roadmap` /
  `design_doc` plus the six `scripts/render_*.py` JSON generators). Sweep the
  render/generated-surface writers as one unit; the remaining writers
  (`vendor_docs`, `publishing/*`, `schema_graph`, the `scripts/` scrapers) are a
  separate call, not automatic. Idea-120's proposed metrics JSONL writer should be
  born with `newline="\n"` rather than added to the queue.
  **KEPT-UPDATED 2026-08-13 — it is not cosmetic after all: it poisons a committed
  provenance field, and the LF refresh is what started it.** The session-end
  `snapshot.ps1` renders the board and the design docs BEFORE it scans, so those
  renders dirty 25 tracked files and the scan then records `meta.git.dirty: true`.
  That field has one job, stated in the script's own comment: *"does the commit in
  this header actually describe the code that was measured?"* Here the answer is yes
  and the header says no — a reader is told the opposite of the truth, which is the
  exact failure U15 split the field to prevent (the 20260805 snapshot, where the
  "dirt" was three untracked paths). Same false alarm, new cause. The two snapshots
  taken either side of the refresh prove the causation: `bb9788b6` at 02:20 recorded
  `dirty: false`, `7d885c9` at 13:45 recorded `dirty: true`, same script and a clean
  tree both times. Before the refresh the working tree held CRLF and the renderers
  wrote CRLF, so a render changed nothing; afterwards the tree is LF and every render
  dirties its output. So **every snapshot taken on Windows from now on carries a false
  `dirty: true`** until the writers pass `newline="\n"`, and `drydocs-20260813-1344.json`
  is the first one — committed knowingly, recorded here rather than silently. This
  raises the priority question: the fix is ten call sites, and the thing it protects
  is the provenance header of the whole snapshot series.

- **`Idea-120`** · 2026-08-13 · `[chore]` · **groomed → U25 (2026-08-19)** · prio? **Med** —
  **Debt metrics have no machine-readable history, so "is it getting better" is
  unanswerable.** Newest-only snapshot retention (U12) is right for snapshots, but it
  leaves the tech-debt skill's hand-typed prose as the ONLY trend record for A3/A4/A5.
  That prose has been wrong twice in the direction that hides work — `drydocs_api` at
  the U2 census, then `drydocs_docmeta` invisible to A3/A4/A5 for five days after
  `d647171` — and on 2026-08-13 it blocked attribution of an A5 move from 29 to 31,
  because there is no prior snapshot on disk to diff against. Proposed: `snapshot.ps1`
  appends one row per run to a metrics JSONL beside the snapshot it just wrote (date,
  commit, A3 top module + count, A4 package + first-party counts, A5 count, live
  `IMPORTS` edge count). Append-only and cheap, and it turns every future `/tech-debt`
  run into a diff instead of a re-derivation. U12 stays intact — a metrics ledger is
  not a retained snapshot. Pairs with Idea-119, whose +2 this would have explained.

- **`Idea-115`** · 2026-08-12 · `[chore]` · **groomed → G103 (2026-08-19)** · prio? **Med** —
  **The rua bundle's script-copy path is a CONVENTION the extractor re-derives, not a
  column the collector declares — so if the two ever disagree, the pipeline reports an
  empty bundle rather than a broken contract.** `drydocs_lineage/extractors/rua_inventory.py:384`
  builds it by hand — `copy_rel = f"scripts{row['path']}"  # the collector mirrors the abs tree` —
  and `scripts.tsv` carries no copy-path column to check it against: the collector writes
  the header `path owner group perms size mtime sha256`
  (`drydocs_lineage/collect/rua_inventory.sh:296`) and mirrors matched files under
  `scripts/` separately. Both downstream consumers then read that derived path —
  G21 `rua_code_ops.py:236` (`read_text` → parse code operations) and G24
  `code_repo.py:235` (`read_bytes` → git blob sha1 → server-vs-repo corroboration).
  **Why it is worth a line rather than a shrug:** the failure is SILENT and reads as the
  wrong thing. Both extractors already handle a missing copy gracefully and correctly —
  `scripts_unreadable` / `scripts_no_copy` in G21, `server_uncomputable` in G24 — because
  an over-cap file is *listed but not copied* by design (`SCRIPT_COPY_MAX_BYTES`, default
  1 MiB). That is the right behavior for the case it was built for, and it is exactly what
  absorbs a layout change: every counter lands in the "too big to copy" bucket, the run
  succeeds, and "the collector's mirror layout changed" is indistinguishable from "this
  estate has large scripts". Nothing errors. Found 2026-08-12 tracing G24 end to end at the
  user's ask; **nothing is wrong today** — the chain is correctly wired and this is a latent
  coupling, not a live defect.
  **The fix is not free, and the tension is the interesting part.** The obvious move — add a
  `copy_path` column to `scripts.tsv` so the location is declared rather than guessed — is a
  **bundle schema change**, and the collector stamps `COLLECTOR_VERSION=rua-inventory/v2`
  precisely so consumers can version-detect. The script's own header already rules that an
  extractor "must treat `scripts.tsv` and the `sha256` columns as OPTIONAL" so v1 bundles
  stay ingestible; a new column means v3 and the same optional-column discipline again, for
  a field every current bundle can already derive. **The cheaper candidate:** leave the wire
  format alone and pin the CONVENTION with a guard — one test that builds a small bundle
  (or uses a fixture) and asserts a `-n`-captured file is readable at
  `scripts{path}` from the extractor's side, so a collector-side layout change reds a test
  instead of quietly zeroing the counters. That is the S10/derived-coverage idiom the repo
  already uses elsewhere. **Decide which**, or rule it accepted-as-is with the reason
  recorded — all three are legitimate; what is not legitimate is the current state, where
  the contract exists only as a comment on one line.

- **FILED 2026-08-18 (desktop, second pass — the whole consumed tail, per the user's “clear the rest”)** — **Promoted 0, inboxed 0, merged 0, parked 0. Twenty-two entries moved, seven deliberately left behind.** After the morning's seven-entry filing the inbox still held **79 entries, 29 of them already marked `groomed →` or `merged →`** — dispositioned work that a reader scanning for open items had to re-read and re-dismiss on every pass. This clears that tail. **Moved (22):** `Idea-113` (→ G93), `Idea-83` (→ J33), `Idea-81` (→ N10), `Idea-77` (→ O53), `Idea-75` (→ K20), `Idea-72` (→ L25), `Idea-71` (→ O52), `Idea-69` (→ K18), `Idea-68` (→ K18), `Idea-64` (→ D9), `Idea-63b` (→ K18), `Idea-62` (→ J32), `Idea-135` (→ K16+K17, filed as `Idea-59` and renumbered later the same day), `Idea-58` (→ U15), `Idea-56` (→ J35), `Idea-53` (→ S10), `Idea-46` (→ C22+C26), `Idea-45` (→ C26+C27), `Idea-39` (→ C26+C27), `Idea-38` (→ J13), `Idea-12` (→ the provenance-audit-fields plan, docs 06/06a), `Idea-2` (→ Q4+Q5+Q6). **THE SEVEN THAT STAY, and why — this is the half worth reading.** The ritual says *fully consumed → move; partially consumed → mark in place and say what stays open*, so a `groomed →` header is NOT by itself a licence to file. Each of these carries a live remainder in its own header: `Idea-93` (L19 took the design-doc half; **the E1 status question stays open — user call**), `Idea-60` (**C25 took the gate SESSION only**; the sub-application USES_SOFTWARE source and the two missing product rows are explicitly not in it), `Idea-57` (J35 took the SHA-citation half; **the company-side credential fix is the company's hand**), `Idea-41` (J34 took the overlay-grammar requirement; **the disposition ruling itself stays the user's**), `Idea-35` (G34 took the content; **the rest parks on the gate-log Q6 ruling**), `Idea-20` (**clause (c) ONLY** to G60 — (a) and (d) re-read 2026-08-12 as parked, not open), `Idea-10` (K16/K17 took the FID half; **the ALIAS tier parks until a company-side alias table exists**). Filing any of those seven would bury an open user decision under a heading nobody reads for open work — the precise failure the mark-in-place rule exists to prevent. **Four judgement calls made explicit so they can be reversed.** `Idea-69`'s body says “WHAT SURVIVES” and reads like residue; it is not — the survivor is the narrow code-level platform declaration, and that is exactly what K18 (done) was groomed to carry. `Idea-135` (`Idea-59` when filed) carries “six open questions [that] need the directory owner”; they ride K16 (blocked) and K17 (todo), which is tracking, not inbox work. `Idea-45` and `Idea-39` both contain the word *parked* about a DIFFERENT entry's trigger — the company catalog gate — and `Idea-39` states in its own header that nothing stays open as inbox work. `Idea-12` merged into a PLAN document rather than a backlog item, and `Idea-2` left P4–P7 plan-tracked; both are dispositioned elsewhere, which is consumption, not residue. **Result: the inbox drops 79 → 57 and now holds open work, parked work and closed-for-the-record only — no entry whose disposition is already complete.** Verified by census rather than assertion: 57 inbox + 79 trail = 136 entries, the same 136 as before the pass, with zero duplicated and zero lost.

- **`Idea-113`** · 2026-08-12 · `[idea]` · **groomed → G93 (2026-08-12)** · prio? **Med** —
  **Coverage counts belong in the Jira fix-package explanation.** User direction
  2026-08-12: the per-run counters the extractors already emit (`ExtractCoverage.summary()`
  with the new `prepost_*` source split, `XmlDefsCoverage`, the conformance finding counts
  by rule) are the model for what a remediation batch should LOG when it is done — the
  counts go into the Jira explanation of the fix package (the runbook-automation support→dev
  handoff), carried through the run-log contract (`drydocs_core/run_log.py`) rather than
  console output, so the explanation is generated from the same numbers the run recorded.

- **`Idea-83`** · 2026-08-07 · `[bug]` · **groomed → J33 (2026-08-07)** · prio? **Low** —
  **Three standing rich-ANSI test failures on this desktop, pre-existing (not
  G55).** `test_supplements.py::test_chain_applies_in_registry_order` +
  `::test_unknown_only_name_exits_2_without_touching_the_graph` and
  `test_bootstrap_guard.py::test_bootstrap_reports_the_declared_count_on_success`
  all assert plain substrings against CLI output that arrives with ANSI color
  codes interleaved on this machine (`\x1b[1;31m` inside the matched phrase) —
  fails under both `python -m pytest` and `poetry run pytest`, fails identically
  on a stashed clean tree, `NO_COLOR=1` does not help (rich force-colors the
  captured stream). Likely a rich/typer version or console-detection difference
  on this desktop. Fix direction: strip ANSI in the assertions or force
  `Console(force_terminal=False)` under pytest — do NOT loosen the messages.
  (Found during the G55 close, 2026-08-07.)

- **`Idea-81`** · 2026-08-07 · `[idea]` · **groomed → N10 (2026-08-07, the gate-prompt draft; schema change waits on the gate)** · prio? **Med** —
  **Split wiring readiness out of the registry `confirmed` flag.** The a14a8028
  fix session (company, 2026-08-06) surfaced a semantics drift: producer uses
  `confirmed` for SEMANTIC confirmation (gate-signed; the class that transfers per
  Q6), while the company additionally encodes PIPELINE-WIRING readiness in the same
  flag (`cm_hosts` stays `false` because their P3 host stage isn't wired, despite the
  transferable gate). Company suggestion, endorsed at the fix session's Q1-B ruling:
  a separate `wired`/`ready` field on registry entries rather than overloading
  `confirmed` — then a divergence like T15/P3 is expressible as
  `confirmed: true, wired: false` instead of a pinned-guard standing divergence.
  Registry schema change → gate territory; groom toward the config layer.
  (Source: company `gate-log.md` standing-divergence entry + PORT-REPORT-a14a8028
  fix close-out, ledgered in docs/port-prompt.md.)

- **`Idea-77`** · 2026-08-06 · `[chore]` · **groomed → O53 (2026-08-07, default remove)** · prio? **Low** —
  **`web/src/components/HeroArt.tsx` is an orphan — the code graph's first
  front-end finding.** The O42 TS import edges went live (226 edges, depgraph
  `a56d2fc`) and the very first orphan query returned exactly one component:
  nothing imports HeroArt and it imports nothing first-party. The repo's own
  comments corroborate — `OverviewRoute.tsx:16` says the radial hub was
  "DEMOTED to a small decorative mark", and only a css comment still cites the
  file. Decide: delete it (with the index.css hero block that styles it), or
  re-wire it in. Either way, remove-or-use — a knowingly dead component defeats
  the inventory drift guard's purpose. *(Found at the O42 close, desktop; the
  query is `MATCH (m:CodeModule) WHERE m.extension IN ['.ts','.tsx'] AND NOT
  (m)-[:IMPORTS]-() ...` — vite.config.ts is the other hit and is legitimately
  edge-less.)*

- **`Idea-75`** · 2026-08-06 · `[bug]` · **groomed → K20 (2026-08-07, the amendment-gate DRAFT — K5 stays signed until sign-off)** · prio? **High** —
  **`tech_partner` is scoped to a node class that has no rows and no loader, and
  the SME says it belongs one level up.** SME, in-chat 2026-08-06: *"in the catalog
  there is a role hierarchy ProductCatalog-Product with role 'Tech Partner'"* — i.e.
  Tech Partner attaches at the **Product** level. The signed K5 gate
  (product-cabinet-attribution, 2026-07-20) ruled the opposite: §B118 records
  *"tech_partner ALSO attaches ONLY to :AreaProduct"*, and
  `catalog_ontology_supplement.cypher:373-374` seeds it `scope = "AreaProduct"`.
  **The repo's own company role doc agrees with the SME, not with the gate.**
  `docs/Product/technology_roles_and_responsibilities.md` defines Tech Partner as
  *"accountable technology leader **for a product**"* and lists **Area Tech
  Partner** as a SEPARATE role (*"owns the technical strategy for the domain"*),
  noting a Tech Partner *"may also assume Area Tech Partner responsibilities based
  on product size"* — which is exactly the kind of overlap that makes two roles look
  like one. K5's stated basis for the AreaProduct scope was *"the rename history
  naming it the area-product role"*, so the likeliest reading is that the two roles
  were conflated at the gate.
  **Two consequences, both measurable now.** (1) `area_products: 0` in
  `config/taxonomy/lob-product-team.yaml` and `catalog_has_area_product` is still
  `status: planned` — so `tech_partner` is scoped exclusively to a node class with
  zero instances and no loader, making it **a signed concept nothing can write**.
  That is precisely the `technology_risk_controls` failure mode (G35 §A2) reproduced
  on the catalog side, and it went unnoticed for the same reason: nothing tests that
  a seeded concept is reachable. (2) If Tech Partner is product-level, then **Area
  Tech Partner has no concept at all** in a scheme K5 fixed at exactly 7 — the first
  worked example on this side of what a FIXED scheme costs.
  **Do NOT fix by editing the supplement.** K5 is signed; per CLAUDE.md a signed
  ruling is re-opened through a gate. Needs a K5-amendment gate on the G35 model
  (G35 amends the 2026-07-10 §B the same way). Note G35's scope fence explicitly
  declines to reopen K5, so this cannot be folded into that walk.
  *Adjacent but separate:* the SME also ruled 2026-08-06 that the SEAL-side
  `"tech partner" -> "CTO"` alias STAYS (G35 §A6). That is about a contact-extract
  NAME; this is about which catalog node the ProductRole attaches to. Both true at
  once — but if Tech Partner is product-level, K5's change_note (*"this area-product
  role was formerly named 'CTO' in SEAL; SEAL's CTO now denotes the product-level
  role"*) needs re-reading at the same gate, because its two halves may have been
  describing the same level.

- **`Idea-72`** · 2026-08-05 · `[doc]` · **groomed → L25 (2026-08-07, rider default per the step-83 precedent)** · prio? **Low** —
  **A SIGNED gate page cites line numbers that have since moved.** The
  business-application-identity gate's §D2 (signed 2026-07-27) names its four
  `attribution_id` sites as `seal_applications.cypher:124,147,170` and
  `seal_contacts.cypher:53`. They are now `152,175,198` and `55`. The FILES and
  the FACT are still right — only the line numbers drifted — but §D2's whole
  point was that the site count had been wrong once already, so it is the one
  clause where a reader is most likely to check the citation and conclude the
  page is stale. Found while drafting the G35 gate prompt, which cites the same
  four sites. Question this raises beyond the fix: gate pages are governed
  surfaces and a signed one is a historical record — is a line number ever
  correctable in place, or does a drifted citation get a rider (the step-83
  precedent) rather than an edit? Cheap either way; the RULE is the valuable part,
  because L19's doc-drift sweep will hit the same question at scale.

- **`Idea-71`** · 2026-08-05 · `[bug]` · **groomed → O52 (2026-08-07; the J26-class question rides the item's notes)** · prio? **Med** —
  **`ownership.attributions.v1` returns a column that is always null.** The
  QuerySpec ends `... e.sid AS holder_sid` (`drydocs_api/query_specs.py:451`),
  but `:Employee` is keyed and written as `employee_id` at every site
  (`seal_contacts.cypher:31`, `seal_applications.cypher:145,169,192`) and nothing
  in the repo ever sets `.sid`. So the Holder SID column of the K4 attribution
  review surface is empty for every row. Its sibling spec
  `mappings.seal-contact-roles.v1` gets it right (`e.employee_id AS holder_sid`,
  line 258), which is what makes this a typo rather than a design difference.
  One-word fix; the reason it is worth an entry is the CLASS — a QuerySpec that
  names a property no loader writes is green in every unit test, because the
  guards check spec shape and not whether the property exists in the schema. That
  is the same promise-vs-assertion family as J26. Found while reading the
  attribution surfaces for the G35 gate prompt; not fixed there because G35 is an
  `ontology`-layer item and this is `drydocs-api`.

- **`Idea-69`** · 2026-08-05 · `[bug]` · **groomed → K18** · prio? **High** —
  **CORRECTED SAME DAY — the claim below was WRONG in its headline and is kept
  only for the narrow residue.** I reported that "every code authored through the K11 steward screen
  is tier-1 by construction". It is not.
  [`AppCodeCascadePane.tsx:288`](../../web/src/routes/AppCodeCascadePane.tsx) has a three-value tier
  selector — `seal-born | platform | dual-coded` — and `tier === 'platform'` authors **per-folder**
  rows (`app_code + folder_id + app_id`), which the loader indexes into `by_folder` and resolves per
  folder. That IS K7 §B2's "resolves per folder", built and wired end to end. The screen handles
  platform codes correctly. WHAT SURVIVES, and it is much smaller: the **code-level platform
  DECLARATION** — the empty-app_id row whose only job is to mark a code so its *unresolved* folders
  surface as `platform-unresolved` instead of falling through to the K2 fuzzy fallback — cannot be
  authored through the store. Consequence is bounded to folders under a platform code that the
  steward has not yet resolved per-folder: they get a fuzzy match instead of surfacing to a human.
  Worth closing, not urgent, and NOT the silent fan-out I described. ALSO REVISED (user,
  2026-08-05): platform app codes DO carry a SEAL — the platform's own — so "declare by absence of
  app_id" was always the wrong encoding; an explicit row kind is the fix, and the store's
  app_id-required check is correct as it stands.
  ORIGINAL ENTRY, for the record: **K9/K11 cannot author a tier-2 platform declaration — the store
  requires the exact field the loader requires to be empty.** Found reviewing the K series (user request).
  [`drydocs_api/mappings.py:413`](../../drydocs_api/mappings.py) refuses a changeset entry unless
  BOTH `app_code` and `app_id` are present ("app_code and app_id are both required — authoring is per
  app code (K7 §B1)"), and the same requirement repeats in the second validator (~:541). But
  [`folder_attribution.py:216-224`](../../drydocs/loaders/folder_attribution.py) uses an **empty
  `app_id`** as the SOLE mechanism to mark a code as a declared platform code — a populated app_id is
  read as a tier-1 code-level attribution and fans out to every folder under the code. **Consequence:
  every code authored through the K11 steward screen is tier-1 BY CONSTRUCTION**, and a platform code
  can only be declared by hand-writing an authored row that bypasses the store. This is the same
  silent fan-out logged against the app-code CSV, reached by a second independent route — so the fix
  cannot be "sanitize the CSV". FIX SHAPE: the store needs an explicit platform-declaration entry kind
  (app_code + no target + rationale), not a relaxation of the app_id check — the check is right for
  tier-1 rows and dropping it would let a blank target through as an ordinary attribution. Severity:
  the loader is correct, the gate is correct, the WRITE PATH is the gap; nothing is mis-written today
  because no producer-side platform code has been authored yet.

- **`Idea-68`** · 2026-08-05 · `[question]` · **merged → K18** · prio? **Low** —
  **"tier" names three different things — but the VALUE SPACES do not
  collide, so this is naming hygiene, not the ambiguity I first claimed (corrected same day).** The
  K7 row-kind tier is a STRING enum (`seal-born | platform | dual-coded`, `AppCodeCascadePane.tsx`);
  the K2 match-precedence tier is an INT (1 SEAL … 5 manual); `drydocs_api/mappings.py` stamps the
  int form on SUPPORTED_SHAPE definitions. `folder_attribution.py` writes the STRING onto the
  BELONGS_TO_APPLICATION edge, so a `tier` edge property is not ambiguous in practice — I said a
  `tier=2` edge could mean "platform" or "matched by FID"; it cannot, because the edge carries the
  string. Still worth a rename (`row_kind` vs `match_tier`) for readers, and worth doing before
  either surfaces in a QuerySpec, but it is cosmetic rather than a correctness risk.

- **`Idea-64`** · 2026-08-05 · `[chore]` · **groomed → D9 (2026-08-07; the ordering decision routes through the gate)** · prio? **High** —
  **`refines:` in the standards frontmatter is a CHAIN, not a flag — and
  `config/precedence.yaml` cannot express two internal tiers.** SME framing: Vendor → Company/Platform
  team → Lower support group. Concretely: BMC baseline ← DAT SRE standard (platform team,
  framework-coded) ← HLT standard (support group, application-coded). Both internal levels sit at
  precedence tier 2 today, so where the two internal standards DIFFER — and they do, in folder
  grammar, in what position 6 means, and in whether the app code carries the SEAL — nothing records
  which wins. Also corrected a real defect in the publishable standard: "frequency at position 6 =
  legacy" is true only of the DAT standard; under HLT a frequency letter at position 6 is CURRENT.

- **`Idea-63b`** · 2026-08-05 · `[question]` · **merged → K18** · prio? **Med** —
  **The app-code CSV's `descr` column is a corroboration signal, never a validity
  test (user, 2026-08-05).**
  `descr` leads with the seal id on MOST rows but not all, so column 2 vs the head of column 3 is a
  CORROBORATION signal with a known-imperfect base rate — never a pass/fail check and never a
  derivation source. `seal_id` is the field; `descr` is prose about it. A majority-correct column is
  the dangerous kind: it survives spot-checks and fails silently in the tail. Use the comparison only
  to produce a REVIEW QUEUE of disagreeing rows (candidate stale renames / decommissioned SEALs /
  copy-paste), each ruled by a human — same disposition as the §G5 disagreement classes.

- **`Idea-62`** · 2026-08-05 · `[idea]` · **groomed → J32** · prio? **High** —
  **Generalize the registration/routing/attribution rule — three instances in two
  days.** (1) A FID is REGISTERED to the platform app while its jobs are ATTRIBUTED elsewhere
  (`fid-identity-and-scope` §G). (2) An AutoSys failure alert carries TWO SEAL ids as escalation
  ROUTING (`SEAL=<a>_<b>` in the incident payload) — ingested naively that manufactures a job
  belonging to two applications. (3) The Control-M escalation DB routes by SEAL for the same reason.
  Candidate standing rule for `docs/RELATIONSHIP_GUIDE.md` or a knowledge/standards note: **a SEAL id
  appearing in a field is not an attribution claim unless that field's job is to attribute** —
  ownership, routing, and attribution are three different facts that all serialize as a SEAL id, and
  the graph has exactly one place (the confirmed app-code mapping) where the third is authored.

- **`Idea-135`** · 2026-08-04 · `[source]` · **groomed → K16, K17** · prio? **High** — *(RENUMBERED 2026-08-18 from `Idea-59` at the allocator-band change: the company side holds a DIFFERENT `Idea-59` (snow_tom_responsibilities), this file is `union-append`, and a port would have merged both into one number. Producer's was the uncited side — no hit in backlog.yaml, config/gate-log.md, docs/ or any tracker row at the time of the grep — so per the G75/G76 precedent producer's moved. One citation appeared later the same day: `docs/port-prompt.md` RELAY-11, an outbound relay telling the company how to repair their lost `Idea-50..75` block. That is a live relay, not an append-only signed record, so it was amended in the same change (RELAY-11 RIDER 2) rather than pinning the id — the G75/G76 constraint is that a SIGN-OFF citation must not be falsified, and this is not one. Keeps its 2026-08-04 capture date: the id is identity, the date is chronology.)* —
  *(census then gate session; the §G registration-vs-attribution
  finding and the six directory-owner questions ride the gate page, not this entry)* —
  2026-08-04 — [source] **The FID directory is the K2 tier-2 unblock — it was never a side quest.**
  `TierReconcilers.fid` has been an empty dict since the K2 build ("no producer-side reconciliation
  source yet"), while the signed match policy orders SEAL > **FID** > APP_NAME > ALIAS. The firm's ID
  directory is that table, and it is ingestible (UI, export, audit columns, application assignment) —
  unlike the outlook-dl case. Gate `fid-identity-and-scope` + [doc 09](09-fid-identity-and-scope.md)
  drafted: `:AppUser` keyed on the directory **id** (not the name — a renameable key silently splits a
  node) with `fid_name` + an explicit crosswalk on the hot path, since every source we hold joins by
  NAME; `BELONGS_TO_APPLICATION {role:'service_account', as_of}` to `:BusinessApplication`; ownership
  is an **as-of assertion**, transfers are normal not drift, and **transfer detection requires
  snapshot diffing** — a single extract can never reveal one, so dated retained snapshots or the
  `as_of` stamp is decoration. Scope answered by MEASUREMENT not judgment: demand-driven pull list
  (run-as owners ∪ unresolved FID facts ∪ evidence rows), preceded by a one-application census that
  turns "about 200 accounts" into "N of ~200, and here is what the rest are". Retired accounts stay in
  scope (historical jobs reference them); contact columns defer to `email-dl-contact-point`.
  Six open questions need the directory owner — name reuse after retirement is the one that decides
  whether every historical join by name is ambiguous.

- **`Idea-58`** · 2026-08-05 · `[bug]` · **groomed → U15 (2026-08-07; the whole-meta-header pass stays a candidate in its notes)** · prio? **Med** —
  **`meta.depgraph.dirty` conflates "untracked files present" with "the
  instrument differs from its pin".** The 20260805 snapshot records `depgraph.commit:
  773fb1e, dirty: true` — but the sibling is at EXACTLY the pin, and the dirt is three
  untracked paths (`.claude/`, two screenshots), no modified tracked source. A reader of
  that header reasonably concludes the snapshot was produced by modified instrument code,
  which would make it unusable for comparison. Fix is small: compute the flag from tracked
  changes only (`git status --porcelain --untracked-files=no`), or split it into
  `dirty_tracked` / `untracked_present`. Third finding in the instrument-provenance class
  (see the two inboxed 2026-08-04), which is starting to argue for one grooming pass over
  the whole `meta` header rather than another point fix.

- **`Idea-56`** · 2026-08-05 · `[chore]` · **merged → J35 (2026-08-07, with Idea-76)** · prio? **High** —
  **The port ledger is being reconstructed after the fact, not rolled
  at the port.** Rolling it today found TWO unrecorded ports (`6713c142`, `5f79d145`) while
  the section still named `40c35724`; the `40c35724` entry itself admits the same thing
  happened to `f71967db`. Three in a row. Consequence: range, port commit, backup tag and
  acceptance numbers are simply unknown for both new entries and cannot be recovered
  retroactively. Worth a real fix rather than more diligence — either the company report
  lands in the producer repo as an artifact, or the roll becomes a step in the port prompt's
  own closing sequence.

- **`Idea-53`** · 2026-08-04 · `[bug]` · **groomed → S10 (BUILT 2026-08-05)** · prio? **High** —
  *(the missing loader guard is now an item and was BUILT the same
  day; the tracker-row half was not groomed — it was DONE in the same commit, T23's row now carries
  the firing as direct evidence. Nothing here stays open.)* —
  2026-08-04 — [bug] **T23 FIRED company-side, exactly as its own row predicted — the tracker
  status should stop saying "pending (producer belief)".** The company ran
  `drydocs load seal_applications` against a graph that took the S3 CODE but never the S3
  re-key, and got `Neo.ClientError.Schema.ConstraintValidationFailed: Node(97) already exists
  with label 'BusinessApplication'`. Mechanism confirmed against producer source: pre-S3 nodes
  carry `seal_id` and NO `app_id`; `MERGE (a:BusinessApplication {app_id: row.app_id})` cannot
  match them because a uniqueness constraint IGNORES NULLS, so it mints a second node, and the
  next line `SET a.seal_id = row.app_id` then collides with the original's `seal_id` (both
  properties are separately unique-constrained, constraints.cypher:43-44). T23's row already
  says "all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance
  silently doubles canonical nodes" — this is that sentence happening. Fix relayed: backfill
  `app_id = seal_id` on pre-S3 nodes BEFORE re-running, after checking whether the partial run
  (batches commit per flush) already doubled any. Producer action: T23's status cell reads
  "pending (producer belief, as of 2026-08-03)" and there is now direct evidence — update it
  at the next port roll, and consider whether the loader should FAIL LOUDLY on a
  `:BusinessApplication` with a null app_id rather than silently creating its twin, which is
  the guard the null-tolerance argument implies but nothing implements.

- **`Idea-46`** · 2026-08-01 · `[source]` · **merged → C22 (bug half) + C26 (back-flow half)** · prio? **Med** —
  **Company catalog-loader review (screenshots, same day as C17) — three
  back-flow candidates and one confirmation.** CONFIRMS C17 §a from the other side: the company's
  `product_lines.cypher` takes `product_line_id` + `parent_lob_id` + `parent_sub_lob_id` and keys
  on ids throughout, i.e. the id-carrying extract the ruling assumed is not hypothetical — it is
  what they load. NEW producer-side gaps, none of which exist here: (a) `pat_app_links.cypher` —
  the product-scoped Product→BusinessApplication loader C9 §c said `catalog_has_application` was
  waiting for, complete with STUB GOVERNANCE worth copying (`is_stub: true`, `source: 'pat-stub'`,
  placeholder attrs filled ONLY while stub, cleared once the real SEAL load lands); (b)
  `pat_product_owners.cypher` — `:Product` ownership enrichment (`product_owner_*`,
  `tech_partner_*`, sids as join keys for a later employee-hierarchy load), MATCH-only so it never
  mints products; (c) `products.cypher` step-2a supplement fields (`description`, `alias`,
  `product_orientation`, `references[]`), each coalesced so a sparse refresh cannot blank an
  enrichment. Also a straight producer BUG the comparison exposed: our `product_lines.cypher` and
  `area_products.cypher` do `SET name = row.name` unconditionally, so a sparse refresh BLANKS the
  name — the company's `coalesce(row.name, p.name)` is the right idiom and we should adopt it
  (their `product_lines` has our bug, their `products` does not; the inconsistency is theirs,
  the bug is ours in both). Company-side findings recorded as tracker T20 in `docs/port-prompt.md`.
  KEPT-UPDATED 2026-08-02 (weekly groom) — **the bug half is groomed, the back-flow half stays
  parked.** The `SET name = row.name` finding went to **C22** together with the [bug] parent-join
  line (same three files, one sweep); the groom verified it and found the blanking SET in
  `products.cypher` too, so C22 covers three loaders rather than the two named here. What remains
  parked HERE are the three producer-side GAPS — `pat_app_links` with its stub governance,
  `pat_product_owners`, and the `products` step-2a supplement fields — because those are back-flow
  and ride the same trigger as the 2026-07-27 company-catalog line below: the COMPANY gate's own
  sign-off. Do not open a second back-flow item for them.
  **GROOMED 2026-08-05 → C26** *(the parked half only)*: those three gaps are now named in C26's
  notes as absorbed, so they ride C26/C27's trigger inside the backlog rather than in this file.
  Nothing about this entry stays open — the bug half went to C22 in the 2026-08-02 groom.

- **`Idea-45`** · 2026-08-01 · `[question]` · **groomed → C26, C27** · prio? **Med** —
  *(absorbed into the company-catalog pair exactly as this
  entry's own last line instructed — the Sub-LoB grain and the `:LOB`-vs-`:CatalogLOB` label
  ruling are C27's §(a) and §(b), settled in ONE pass; the invisible-flattening argument is
  recorded in C27's notes as the reason it is gate-worthy rather than shruggable.)* —
  2026-08-01 — [question] **We model no Sub-LoB, and the SME fact that closed C17 says it is a
  real grain with its own numeric id. CONFIRMED BUILT company-side the same day** — their
  `product_lines.cypher` carries `parent_sub_lob_id` and anchors the line under
  `MERGE (sl:SubLOB {sub_lob_id: …})` when it is populated, falling back to `:LOB {lob_id}`
  otherwise, both via `HAS_PRODUCT_LINE`. So this is no longer "should we model it" but "adopt
  which shape" — and the label ruling (`:LOB` vs our `:CatalogLOB`) has to be settled in the same
  pass, since their fallback branch and our `catalog_lobs.cypher` write DIFFERENT labels for the
  same thing. Original note follows. The catalog hierarchy runs
  `BusinessSegment → CatalogLOB → ProductLine → Product → AreaProduct`; the source runs
  `LoB → Sub-LoB → Product Line → …`, so our chain silently flattens one level. Corroborated
  three ways: the SME statement (2026-08-01), the CDO capture's "5-level hierarchy … native
  IDs at each level", and the company's own catalog gate page which already introduces
  `:SubLOB` + `HAS_SUB_LOB` ("only CIB and AWM have them") and widens `HAS_PRODUCT_LINE` to
  `(:SubLOB|:LOB)`. NOT built at C17 on purpose — a new node label + relationship is an
  ontology decision, and this is the same divergence the parked 2026-07-27 company-catalog
  back-flow note already owns (its trigger is the COMPANY gate's sign-off). Worth noting the
  flattening is currently INVISIBLE rather than merely absent: `parent_lob_id` on a product
  line will carry whatever the extract puts there, so a sub-LoB id would land in a
  `:CatalogLOB`-keyed field and MERGE a phantom LOB. Fold into that back-flow item when its
  trigger fires; do not open a second one.

- **`Idea-39`** · 2026-07-27 · `[idea]` · **groomed → C26, C27** · prio? **Med** —
  *(the whole entry is now covered: C26 writes the divergence
  down and reserves the four shapes as `planned` — actionable NOW, no trigger; C27 is the
  adoption gate that still waits on the COMPANY gate's sign-off. The two sibling entries that
  said "fold into that back-flow item; do not open a second one" — the 2026-08-01 Sub-LoB line
  and the parked half of the 2026-08-02 catalog-comparison line — are absorbed into the same
  pair. Nothing here stays open as inbox work.)* —
  2026-07-27 — [idea] **Company catalog gate (`internal/org/catalog/`, page dated 2026-06-25) has
  drifted ahead of the producer catalog ontology — back-flow / divergence-ledger candidate.**
  Screenshot review of `_catalog_gate_page.html` ("SME Gate Prompt — PAT Catalog Loader", step 1
  of 3; sibling `_product_application_gate_page.html` likely steps 2–3): introduces `:SubLOB` +
  `HAS_SUB_LOB` (LOB→SubLOB, "only CIB and AWM have them"), widens HAS_PRODUCT_LINE to
  `(:SubLOB|:LOB)`, uses label `:LOB {lob_id, name}` vs our `:CatalogLOB {lob_id, code, name}`,
  expects map ids `sub-lob-org-unit` + `catalog-lob-reconciles-segment` (ours:
  `lob-has-product-line` / `lob-reconciles-to-segment`, confirmed 2026-06-21), and ingests a
  5-field `pat_lob_sublob_productline.csv` (164 rows; Sub-LoB Name column our
  `lob-product-team.yaml` capture lacks). None of it exists here, even as `status: planned`.
  Gate MECHANICS all match the gate_pages.py design (localStorage ticks, no-write-until-confirmed,
  `{confidence, authority, aliases}` on RECONCILES_TO, skos:closeMatch aliases, precedence winner
  `lob-product-team`) — content drifted, mechanism didn't. Page date 2026-06-25 PRE-DATES the G2
  Phase-B relocate (2026-07-10), so its `drydocs/schema/ontology.cypher` path was period-correct,
  not a bug — refresh it if the prompt is revised. Real page bug to fix before signoff:
  functional-org target "Corporate" is ambiguous vs our seeded `:BusinessSegment {code:"Corp",
  name:"Corporate"}` — written as a code it MERGEs a phantom segment. Useful real-data signal:
  CIB + AWM appear as SEPARATE LoBs with 1.0 exact matches → resolves the LOB002 AWMCIB (legacy,
  0.5) open question in `lob-product-team.yaml`. If the company gate signs off: mechanism-only
  back-port (vocab entries as `planned`, map entries, 5-field taxonomy capture, LOB-vs-CatalogLOB
  label ruling) or an explicit port-prompt divergence-ledger entry. ~~COORDINATE FIRST: a laptop
  session (unpushed as of 2026-07-27) is re-working BusinessApplication mapping — don't touch
  catalog/SEAL map entries until it lands.~~
  KEPT-UPDATED 2026-07-27 groom: the laptop session LANDED same day (business-application-identity
  gate SIGNED OFF `fc15191`; the build = S3, `seal_id` → `app_id` on the canonical node) — the
  coordinate-first constraint is lifted. New wrinkle for the eventual back-port: the comparison
  now also crosses the app_id rename (the company page pre-dates it), so the label ruling
  (LOB vs CatalogLOB) and the key ruling (app_id) should be settled in the same pass. Still
  parked on its original trigger: the COMPANY gate's own sign-off.

- **`Idea-38`** · 2026-07-27 · `[question]` · **merged → J13** · prio? **High** —
  **Internal platform vocabulary in the sample corpus — ruling
  needed.** Residual from the groomed J14/J15 publish-boundary pair: the samples still carry
  real-looking internal platform tokens (`HLDM`, `PRARAG`, `svc.hldm`, `/opt/scripts/hldm/`,
  `host-hldm-01`, datacenter codes) — a different value class from SEALIDs, deliberately left
  untouched by the 2026-07-27 sweep and not ruled on. Is platform vocabulary publishable
  mechanism (like the naming grammar) or a value class to synthesize? User/SME call; once
  ruled, J15's value-shape guard test can grow a rule for it.
  KEPT-UPDATED 2026-07-27 (J14 close): two more members of the same identifier class found at
  the build — (a) the escalation-table schema identifiers (`psgmgr` / `cm_escalation_db` /
  `EJOBNAME` / `ECOMPONENT`) generalized out of the two J14 files but still present in 6+
  tracked files (controlm-db skill, gate prompts, taxonomy-ontology map, remediation TDD);
  (b) `knowledge/standards/technology/data-center-naming-convention.md` carries real DC codes
  and a real app code — same class, same sibling directory, untouched by J14 by scope. The
  ruling should cover: platform tokens, DC codes, schema/table/column identifiers, and
  synthetic-sample product NAMES that echo real ones ("Home Lending Servicing" in
  lob-product-team.yaml, paired only with synthetic ids).
  KEPT-UPDATED 2026-08-12 (groom) — **ONE OF THE FOUR CLASSES IS NOW CLOSED, three remain.**
  Class (1), the platform tokens this entry led with, was RULED by the SME on 2026-08-11:
  `PRARAG`/`HLDM` are AUTHORED FIXTURE NAMES, not captured values, so no sweep is owed and the
  proposed one was stopped (`PRARAG` sits in ~36 files including the bundled sample corpus, the
  lineage fixtures and five tests that assert on it literally, so removing an authored name
  would have rewritten the corpus and broken the parser's own pins). The ruling is recorded
  where realness decisions live — beside the J15 realness table in
  `internal/standards/technology/folder-naming-convention.md` — because that table replaced the
  NUMERIC segments inside those folder names, and reading it alone makes the surviving tokens
  look like an oversight. J13's notes already carry the closure. Classes (2) DC codes,
  (3) schema/table/column identifiers and (4) the echoing product names are UNCHANGED and still
  user-gated; the ruling deliberately did not dispose of them, and the DC-codes file is the live
  one (it carries real DC codes AND a real app code, out of J14's scope by accident of scoping).

- **`Idea-12`** · 2026-07-18 · `[idea]` · **merged → the provenance-audit-fields plan (docs 06/06a), at its next touch** · prio? **Low** —
  JobRun.started_at/status indexes (GraphAcademy advisor residual) — fold
  into the provenance-audit-fields plan (docs 06/06a) at its next touch, not standalone.

- **`Idea-2`** · 2026-07-06 · `[idea]` · **groomed → Q4, Q5, Q6 (P1–P3); P4–P7 stay plan-tracked** · prio? **Med** —
  **`drydocs-docmeta` component plan written** — full plan in
  `knowledge/upgrade-plans/docmeta-component.md`: component boundary (new `docmeta`
  COMPONENT_GROUP, imports core only, CLI via entrypoint exemption), config
  `doc-source-registry.yaml` + test guard, `drydocs_docs` DB + composite delta, phases
  P0 (benchmark) → P7 (T4 connectors), Port A inventory (bkup scraper → producer:
  carry cleaner/tokenizer/manifest, adapt registry/confluence-interface, drop migrate),
  Port B git-readme §6 (clean-adds / Canonical-COMPANY connector wiring / company
  supplements: blocked vendor fetches, Graph-API creds, Enterprise multi-DB target).
  Heads-up bullet added to git-readme.md. Groom phases P1–P3 to backlog after the P0
  benchmark verdict (**landing zone since 2026-07-16: phase 14 / Epic Q** — created at the
  Essential-GraphRAG groom). **TRIGGER FIRED 2026-07-16 pm: the P0 WRITTEN verdict landed**
  (knowledge/upgrade-plans/docmeta-p0-verdict.md, Q3 — recommendation: BUILD) → **P1–P3 are
  now groomable into Epic Q at the next groom**; the docmeta ADR is the P1 gate output — **number correction 2026-07-16**:
  the plan reserved "ADR 0004" (2026-07-06) but 0004 was minted the next day for the
  software-registry terminology ADR (accepted 2026-07-07); the docmeta ADR takes the next
  free number at authoring (plan doc's 3 refs annotated same day). The four T1–T4 tier lines were folded
  INTO this sequenced plan (P0→P7) and moved to the audit trail (2026-07-09). P0's corpus
  load is already substantially executed: the bmc-docs lexical loader (Document→Chunk,
  llm-graph-builder pattern) shipped and gate `bmc-docs-lexical-load` was ACCEPTED 13/13,
  LOADED LIVE (commits 12423f4/24d6a4b) — the WRITTEN benchmark verdict (traversal vs
  manifest-routed markdown vs vector RAG) + the docmeta ADR still remain before P1–P3 promote.
  **GROOMED 2026-07-18: P1–P3 promoted → Q4 (gate + ADR) / Q5 (registry ledger) / Q6 (Port A;
  module drydocs-docmeta registered as working name — final at the Q4 gate).** P4–P7 stay
  plan-tracked until Q4–Q6 land. NEW RIDER (GraphAcademy advisor, 2026-07-17): when the docmeta
  loaders land, add existence constraints on `Document.trust_default` / `Chunk.tier_rule`
  (silent null = provenance undercount).

- **FILED 2026-08-18 (desktop — `Idea-114` + `Idea-112`, the 2026-08-12 pair whose lines never moved)** — **Promoted 0, inboxed 0, merged 0, parked 0: this run dispositions nothing.** Both entries were already groomed on 2026-08-12 and the trail already carries that run (**GROOM 2026-08-12, targeted — `Idea-112`, `Idea-113`, `Idea-114`**, below); what never happened is the second half of the ritual, the MOVE. They sat in the inbox marked `groomed →` for six days, which is exactly the state the “fully consumed → move to the audit trail” rule exists to prevent — a reader scanning the inbox for open work had to read and dismiss them each pass. Filed together at the user's grouping because they came out of ONE session (working through the G60 result) and split into work that still has to agree: `Idea-112` → **G92** (p2, `drydocs-lineage`, phase 6) resolves `%%` variables BEFORE the file-op parse so a variable path and its resolved twin stop planning two `DataAsset` nodes for one file; `Idea-114` → **G94** (p2, `drydocs-core`, phase 6, deps G84) the standard-selection decision tree **+ G95** (p3, `config`, dependency-free) the gate prompt for standard identity and its carrier. **All three items are still `todo`, so nothing here is retrospective** — the filing is bookkeeping, and the open work is in the backlog where it belongs. Guardrail restated because it survives the move: §7.5/G84 rule the DD digit a grammar VERSION that must never select a template or standard, so a standard id needs its own carrier and never the sentinel digit.

- **`Idea-114`** · 2026-08-12 · `[idea]` · **groomed → G94 (the selection decision tree, buildable now) + G95 (the gate prompt for standard identity + per-team carrier — the contract change goes to the SME first, 2026-08-12)** · prio? **Med** —
  **DD1 standard selection is a decision tree, and standards need identity.** User
  direction at the 2026-08-12 session: under the `DD1|` tag, a FileWatcher job validates
  against the FW standard; a CMD job selects by ETL engine FIRST (DPL, Ab Initio,
  Informatica — the launcher classification already names these), then falls back to a
  generic standard that carries SOME shared tokens (DevX key, the EMAIL_DL contacts) but
  not all. The standard itself then needs identity and storage: a config table (SQLite?)
  keyed by a standard id, so a validation profile can be stored BY TEAM, with a
  platform/product hierarchy later. Guardrail to carry into the groom: §7.5/G84 rule the
  DD digit a grammar VERSION that MUST NOT select a template or standard — selection rides
  TASKTYPE + JOB_ROLE + the launcher classification, so a standard id needs its OWN
  carrier (the config table keyed by team/engine, or a registered token), never the
  sentinel digit. Today the per-job-type sets live in code-as-data (`TOKEN_REGISTRY`, the
  parse contract, guarded by the registry-vs-standard agreement test) — externalizing
  them into a per-team registry is a contract change and gate-relevant. Relates: G77
  (THEME token inside the DD1 block), the etlprocess-kind-enum rider (engine vocabulary).

- **`Idea-112`** · 2026-08-12 · `[idea]` · **groomed → G92 (2026-08-12)** · prio? **Med** —
  **Resolve `%%` variables in PRECMD/POSTCMD (and CMD_LINE) before the G14 file-op
  parse.** The G60 feed stages operands verbatim, so candidates carry unresolved names
  (`%%R_PATH/...`, `%%$ODATE`) that cannot merge with their resolved twins. The one
  resolver (`drydocs_core/orchestration/controlm/resolver.py` — "no caller may
  re-implement substitution") already does everything needed: PRECMD/POSTCMD are
  themselves SETVAR definitions, so `resolve_layers()` over the folder→job scope chain
  returns each row's `resolved_value` in place — parse THAT instead of the raw value, keep
  raw verbatim beside it (the G46 derived-fact shape), and `{ODATE}`-class canonical
  tokens remain as expected symbolic residue in the operand. The SAME variables CSV
  carries both the shell text and its bindings (`var_scope` splits FOLDER from JOB in the
  aliased shape; the raw export's folder rows are the header row where JOB_NAME equals the
  folder name). Count resolution quality per the `ResolveCoverage` precedent
  (`drydocs/cmdline_staging.py`). Raised working through the G60 result with the user.

- **FILED 2026-08-18 (desktop — `Idea-79` + `Idea-76`, the port-mechanics pair; both items shipped)** — **Promoted 0, inboxed 0, merged 0, parked 0.** Neither entry had a trail record at all: they were dispositioned on 2026-08-07 in a session that filed no groom entry (the only 2026-08-07 entry below is the laptop's Q16-session gaps run, which covers different ids), so this filing is also the retro-record. Grouped because they are one subject seen from two ends — what the port CARRIES and what the port has REACHED. `Idea-79` → **J34** (p2, `docs`, phase 8, **done**): the `PORT-MANIFEST.yaml` company-row overlay seam, raised after a clobber audit quantified **89 company-only paths** falling through `default:` and out of their own J16 guard. `Idea-76` → **J35** (p2, `docs`, phase 8, **done**, merged with `Idea-56`): the port ledger stopping at step 101 / `a14a802` with ten commits behind it, which J35 turned from a catch-up into a structural roll. **Both done, so the entries are fully consumed with no residue** — the reason they move rather than getting marked in place.

- **`Idea-79`** · 2026-08-06 · `[idea]` · **groomed → J34 (2026-08-07)** · prio? **Med** —
  **`PORT-MANIFEST.yaml` needs a company-row overlay seam — ports keep clobbering
  company-only tracked-path rows.** PORT-REPORT-a14a8028's clobber audit found the take
  dropped the company's `default_ok` section — quantified at the 2026-08-06 root-cause
  run as **89 company-only paths** falling through `default:` (canonical-producer
  disposition means the producer file wins verbatim), so company-only tracked paths fell
  through their own J16 guard (`test_no_tracked_path_falls_through_silently`, the one
  conscious deferral in that report). The company session re-adds the rows by
  hand this time; the structural fix is a D2-registry-style overlay: producer manifest
  stays canonical, company rows live in a separate company-side include the guard unions,
  and a port can no longer delete them. Needs a small grammar decision (include file vs.
  marked section), then a manifest + guard change on both sides.

- **`Idea-76`** · 2026-08-06 · `[chore]` · **merged → J35 (2026-08-07, with Idea-56)** · prio? **Med** —
  **The port ledger stops at step 101 / `a14a802`, and ten commits have landed
  since — including the whole G22 gate session.** The internal port that started
  2026-08-06 classified the range ending at `a14a802`, so everything after it is
  outside what the company side has seen: `180f4ae` (the SEAL sample generator —
  already flagged as owed step 102), the five G22 gate commits, the desktop's two
  code-graph asset-skip rulings, and the `.ksh` → SWO binding in
  `code_snapshot.py`. Two of those are code changes, not just gate prose. Roll the
  ledger before the next port so the company side is classifying a range that ends
  somewhere deliberate. *(Noticed at the G22 session close, laptop.)*

- **FILED 2026-08-18 (desktop — `Idea-67` + `Idea-66` + `Idea-65`, the Control-M app-code cluster; all three items shipped)** — **Promoted 0, inboxed 0, merged 0, parked 0.** All three were dispositioned on 2026-08-05, before this trail's earliest entry, so they have never had a record here; this filing supplies it. Grouped because they are three readings of ONE identifier problem — a 3-character Control-M app code asked to carry more meaning than it can hold. **`Idea-66` → K18** (p1, `drydocs-load`, phase 9, **done**): the app-code CSV is tier-1-shaped, so a straight conversion would fan a PLATFORM code's own SEAL onto every consumer folder beneath it — silent, and it looks correct, because `AOC→110777` is a true statement about the platform and a false one about the folders. Unblocked the same day when the SME supplied the closed six-code platform list, turning a steward capture exercise into a name parse. **`Idea-67` → K19** (p2, `drydocs-load`, phase 9, **done**, deps K18): the same code is not DURABLE — a scarce 3-char namespace gets retired and reissued (`DDC` is the documented case), so a code→application mapping is an as-of assertion, not a fact, and a reused code can silently inherit its predecessor's mapping. **`Idea-65` → merged into C25** (p2, `ontology`, phase 2, **done**): the SUB-APPLICATION field is a standards-backed at-scale statement of app→platform — and the entry is worth keeping for its own CORRECTION, which the user made the same day: it was first overclaimed as a better USES_SOFTWARE source than the version email, and it answers no versioning question at all. PRODUCT and VERSION are two facts, not two sources for one. **All three items done; no residue, so all three move.**

- **`Idea-67`** · 2026-08-05 · `[question]` · **groomed → K19** · prio? **Med** —
  **A Control-M app code is NOT a durable identifier — the 3-char limit
  forces reuse (user, 2026-08-05).** Codes are a scarce namespace, so they get retired and reissued
  with a different meaning; `DDC` is the documented case (created for the PySpark conversion,
  repurposed, nothing PySpark now). CONSEQUENCE for the K9 store, which is about to be hand-keyed:
  a code→application mapping is an **as-of assertion**, not a fact — the same shape as the FID→SEAL
  registration ruled in `fid-identity-and-scope` §B1, and the third current-state-only identifier
  found this week. `authored_on` already gives the store an as_of; what nothing prevents is a REUSED
  code silently inheriting its predecessor's mapping, and folders authored under the old meaning
  keeping an attribution that is now wrong. Wants: effective dating on the mapping, or at minimum a
  reuse detection that surfaces "this code's mapping predates folders that appeared under it".

- **`Idea-66`** · 2026-08-05 · `[bug]` · **groomed → K18** · prio? **High** —
  **The app-code CSV is TIER-1-SHAPED, and loading it as authored rows would
  silently fan a platform code's own SEAL onto every consumer folder under it.** THE MECHANISM (built,
  [`folder_attribution.py:216-224`](../../drydocs/loaders/folder_attribution.py)): the ONLY way to
  declare a tier-2 platform code is an authored row with **`app_id` EMPTY** — a populated app_id is
  read as a code-level tier-1 attribution and fans out. `internal/orchestration/controlm-app-codes-with-seal.csv`
  (company-side) populates `seal_id` on every row, including the platform codes, so a straight
  CSV→authored-rows conversion can NEVER produce a platform declaration. Confirmed real by the user
  2026-08-05: `AOC` (registered to the CCB Cloud Data Processing Platform SEAL, the datalake seal for
  Ab Initio) and `DCL` (the DPL launcher backbone, registered to a consumer app) are both shared platform
  codes whose folders serve many consuming applications. K7 ALREADY RULED THIS — tier 2, "e.g. the DPL
  launcher spine", folders SURFACE for steward completion, never auto-picked
  ([`k7-folder-mapping-decisions.md:14`](k7-folder-mapping-decisions.md)) — so the 1:1 graph-test does
  NOT red; the defect is upstream, at tier assignment. FIX SHAPE: an explicit platform-code list
  applied BEFORE conversion, dropping `seal_id` for those codes rather than carrying it. The failure is
  silent and looks correct — `AOC→110777` is a true statement about the PLATFORM, just not about the
  consumer folders it would be stamped on. The only in-file hint of platform-ness is the word
  "Platform" in `descr`, which is the untrustworthy column (below). **UNBLOCKED SAME DAY:** the SME
  supplied the DAT SRE standard's Framework → APPCODE table — the platform list is CLOSED AT SIX
  codes (values in `internal/standards/technology/folder-naming-convention.md`), and tier is
  MECHANICALLY DERIVABLE from the folder name: prefix positions 3–5 ∈ platform list → tier 2, else
  tier 1. So the fix is a six-row list plus a name parse, NOT a steward capture exercise — and the
  tier-2 resolving SEAL is a token inside the folder name, so per-folder resolution is derivable for
  the common case too. Mechanism written up in
  [`knowledge/standards/technology/folder-naming-convention.md`](../../knowledge/standards/technology/folder-naming-convention.md).

- **`Idea-65`** · 2026-08-05 · `[source]` · **merged → C25** · prio? **Med** —
  **The Control-M SUB-APPLICATION field declares WHICH PLATFORM an application
  runs on — a first-pass C1 source, NOT a replacement for the version email.** ~~a far better
  USES_SOFTWARE source than the adhoc version email~~ — **CORRECTED SAME DAY (user):** that
  overclaimed it on both axes. Under the HLT standard the framework does not vanish when the app code
  is application-tied; it moves to a sub-application `PR<Appcode>-<Platform App Code>`. **Documenting
  the platform IS the intent of the naming standard** — so the field is a faithful, standards-backed,
  at-scale statement of *app → platform*, and that is genuinely useful. What it is not:
  - **It answers no versioning question.** `ABI` says Ab Initio, never `v4-3-2-2`. The version email
    and this field are not two sources for one fact; they are two different facts (PRODUCT vs
    VERSION), and only the email carries the one the readiness review actually asked for. Treating
    this as "the better source" would have left the gate's whole subject unsourced.
  - **Mapping it at sub-application grain manufactures a super node.** An app has MANY
    sub-applications, all naming the same platform — fan every one into `:SoftwareProduct {abinitio}`
    and that single node collects an edge per sub-application per app across the estate, which is a
    traversal hazard, not just noise. If this is loaded, the edge is **one per (application, product),
    deduped at app grain**, with the sub-application rows as supporting evidence rather than as edges.
  Standing use: **fine for a first-pass C1 (container) diagram** — which apps sit on which ETL
  platform, at estate scale, for free. Anything finer waits for a real source.
  PREREQUISITE either way: two of the six framework codes have no
  `config/taxonomy/software-registry.yaml` product row — DPL (the standing gap `invocation_patterns`
  already records, now with a name and a framework table behind it) and Snowflake ETL. Register those
  products first. *[Corrected 2026-08-05 (user): AWS Snowflake is a TARGET DB platform (S3/Glue/
  Iceberg family), not an ETL product — the second row registers `snowflake` the data platform, not
  a "Snowflake ETL" tool. Recorded in C25's notes and both folder-naming twins.]*

- **GROOM 2026-08-18 (targeted — Idea-134 only, the mechanics the signed gate authorized; SME context supplied at dispatch)** — **Promoted 2: `Idea-134` → `N14` + `N15`** (both epic N / phase 11 / **p1** — SME-confirmed at dispatch, not proposed — agent `main`, sonnet, todo, `depends_on: [N12, N13, O24]`, all three done, so **both enter `next_ready` on arrival**). **Inboxed 0, merged 0, parked-as-question 0.** **TWO items rather than one because the gate's two authorized builds land in different modules:** N14 is a report/export surface (`drydocs-api`, the O24 report family) and N15 is loader-side detection (`drydocs-load`, which owns a run cadence — the MODULE_MAP placement test). They are independent; neither blocks the other. **N14 — the UNION REPORT:** one report class over BOTH domains (§A1's single `pending_source_correction` vocabulary — active `seal_contact_override` rows plus every registry dataset row still at `acquisition.mode: manual`), ordered by AGE with the age BASIS made explicit because it is asymmetric (override rows carry `authored_on`; a manual registry row carries no dated field today, so the build picks and documents one basis). The gate's fences are written into the ACCEPTANCE, not the notes: no deadline, SLA, alerting or per-row `review_by` (§C2 — per-row clocks were offered and declined); it never gates a load, blocks CI or fails a test (§C3); and per N12 clause (f) no column, wording or styling may present `manual` as a defect. The K7 §E2 exemption is ENFORCED rather than documented — a test asserts an `app_code_mapping` row can never appear (§D1), and the report reads each store's DECLARED pending-vs-permanent property (§D2) instead of hardcoding the one exemption. **N15 — AGREEMENT-CANDIDATE DETECTION:** `seal_contacts` + the O24 override store named as the first concrete surface; when a loaded SEAL holder equals the override's corrected holder the override becomes a retirement CANDIDATE. **Two hands made structural, not aspirational:** it rides the EXISTING draft mechanism (`add_draft` / the commit-by-replace override draft path), so an unattended run can only leave an open draft — a test asserts a detection run leaves every `seal_contact_override.status` untouched (§B2/§B3; auto-retire was offered at the gate and declined). Confirming archives the row dated with its agreement evidence, history kept (§B4) — which is what extends today's `('active','corrected-in-seal')` CHECK. **Nothing graph-side in either item (§A3):** pending-ness lives in config and stores only; a graph-side flag would be a new RELATIONSHIP_GUIDE proposal and its own gate. **No new gate is created and none is needed** — the lifecycle was SIGNED 12/12 the same day and these two implement it. Sonnet on both, recorded deliberately in N15's notes: it does change a store schema, but the gate already made that decision, so the schema-touch alone must not re-tier it to fable. Verified at the groom rather than recalled: the gate clause anchors come from `config/gate-log.md`, and the `v_source_corrections` view, the `app_code_mapping` DDL comment, the status CHECK and the thin `seal_contacts` loader were read out of the tree.

- **`Idea-134`** · 2026-08-18 · `[idea]` · **groomed → N14 + N15 (2026-08-18)** · prio **High** —
  **The pending-source-correction MECHANICS — the two builds the signed gate authorized
  but did not build.** Gate `pending-source-correction` SIGNED 12/12 (2026-08-18, N13).
  Ruled, now buildable: (1) the UNION REPORT — one report class listing every live
  placeholder across both domains (override rows awaiting source correction + manual
  acquisition rows awaiting automation), ordered by AGE, no deadline, never gating
  anything (§C1-§C3); (2) AGREEMENT-CANDIDATE DETECTION — the load that consumes a
  source carrying an overridden value surfaces override == source as a retirement
  CANDIDATE for steward confirmation (§B2, two hands; an unattended job may propose,
  never perform, §B3). Both flips keep history per §B4. The K7 §E2 permanent-by-nature
  domains are exempt and must not appear in the report (§D1); new stores declare
  pending-vs-permanent at creation (§D2).

- **GROOM 2026-08-18 (targeted — Idea-133 only, with SME context supplied in-session)** — **Promoted 2: `Idea-133` → `N12` + `N13`** (both epic N / module `config` / phase 11 / p2 / todo, dependency-free, so both enter `next_ready` on arrival). **Inboxed 0, merged 0, parked-as-question 0.** N12 is the BUILD: a first-class `acquisition:` block on every dataset row of `config/source-registry.yaml` (`mode: manual | automated`; manual names `format: csv | ascii | json` + a landing-zone-relative `drop_dir`, automated names `via: api | db` with the pull's coordinates by reference), declared in the JSON Schema and ENFORCED in `tests/unit/test_source_registry.py` — the schema is shape-only (S6, no `additionalProperties: false`), so a block added to the YAML alone would validate silently. **The SME's exploratory-phase framing is written into the ACCEPTANCE, not just the notes:** `mode: manual` is the EXPECTED FIRST STATE of every source (profiling → ontology → mapping → trial loads, with a .csv/.json file as the natural manual Neo4j loader), never a defect — no test or render may present it as a violation. Fences kept from the entry: no watcher/mover is built, no real path is committed, and the doc-corpus ledger is out of scope. **N13 is the SIBLING the SME's second half asked for:** the acquisition manual→automated flip and the O24 override→source-corrected flip are ONE lifecycle shape, and K9 §E2 deferred that flip to "the domains where permanence is temporary" with NO item owning it — so N13 drafts one gate prompt covering both (drafting decides nothing; G27/W1/U11/N10 precedent) and nothing changes until the gate signs. Raised as a sibling rather than folded into N12 as a clause on purpose: folding it would make a buildable config item undeliverable without an SME session. Coordination recorded, not invented: N10's proposed wired/ready flag and `acquisition.mode` are DIFFERENT axes that compose on the same row, and Idea-132's `source_label` enum question stays open in the inbox.

- **`Idea-133`** · 2026-08-18 · `[idea]` · **groomed → N12 + N13 (2026-08-18)** · prio? **Med** —
  **Give every registry source a declared ACQUISITION PATH: manual sources name their
  drop directory (CSV/ASCII, real path in the internal twin), automated sources name
  their API/db pull.** SME ask 2026-08-18. Today the acquisition mode is smeared across
  three half-fields that do not compose into an answer: `adapter` (csv/oracle/yaml/
  markdown/json — 8 sources carry `~`), `connector` (only the doc corpora use it), and
  `locator` (free-shape: `extract: ~`, `data_root:`, `mapping:` — each source invents
  its own key). Nothing states the split the SME names: is this source a MANUAL drop
  (someone exports a file into a directory) or AUTOMATED (an API call or a db pull the
  pipeline runs)?
  **THE SHAPE TO CONSIDER:** a first-class `acquisition:` block per dataset —
  `mode: manual | automated`; for manual, `format: csv | ascii` plus `drop_dir:` where
  the COMMITTED value is the landing-zone convention (`DRYDOCS_DATA_ROOT`-relative, the
  `controlm-xml/` precedent, resolver in `drydocs_core/data_root.py`) and the REAL
  internal path lives only in the internal twin (the `locator.extract: ~` discipline,
  unchanged); for automated, `via: api | db` plus the pull's coordinates by reference
  (the source's own dataset id already names the db object; the API case names the
  call surface, e.g. the G96 framework for Control-M).
  **WHY IT EARNS A FIELD RATHER THAN A CONVENTION:** Idea-115 already caught this class
  once — the rua copy path existed only as a derived expression, and the fix was to
  make both ends name each other. Idea-132 is the live driver: the ServiceNow extracts
  are moving manual→automated (hand-pulled CSV → SQL over the replica), and TODAY that
  transition has no field to flip — it shows up only as prose in `notes:`. A declared
  `acquisition.mode` makes "what is still hand-fed?" a query instead of an audit, gives
  the load-map/console an honest manual-vs-automated lens, and gives the
  `source_label` enum question (Idea-132's knock-on) the axis it is actually trying to
  encode — acquisition mode is a SOURCE fact and belongs on the registry row, not on
  the loader class.
  **FENCES:** schema change to `drydocs.source-registry.v2` rows + its JSON Schema +
  `test_source_registry.py`, so it is a groomable item, not a quick edit; no real paths
  ever committed (Scan D/J27 class); and it RECORDS mode per source — it does not build
  any mover/watcher for the drop directories.

- **GROOM 2026-08-17 (desktop, targeted — the UI / UI-WIP inbox entries only, per the run's focus: console work that does not touch what other sessions hold)** — the three entries the 2026-08-13 groom explicitly left for a console-epic run ("UI-view work and belong with the console epic") are that run's whole scope, and all three promoted. **Promoted 3: `Idea-116` → `O60`, `Idea-122` → `O61`, `Idea-123` → `O62`** (all p2 task, `drydocs-web`, phase 12, epic web-console, sonnet) — all three dependency-free, so all three enter `next_ready` on arrival. **Inboxed 0, merged 0, parked-as-question 0, closed 0.** Verified against the tree at the groom rather than taken from the entries: `web/src/lineage/` + `routes/LineageRoute.tsx` exist (O60's landing), `UI-WIP/wireframes/wireframes.json` carries WF-DFL-01..17 + the `FB-2026-08-13-01` feedback record and `out/dataflow.svg` is present, `web/src/ownership/` + `MiniDag.tsx` exist and the module registry's own tagline for /ownership is "SEAL → PAT → team rollup" — the exact chain Idea-122 draws (O61's landing), and `web/src/ask/` + `routes/AskRoute.tsx` + `drydocs_api/query_specs.py` exist (O62's landing). **The O60/O62 pairing is kept explicit in both items** — one job → pipeline → asset chain, swimlane form vs report form. **Nothing here decides an ontology question, and two caveats are written into acceptances rather than left in this file:** O60 renders READS/WRITES dashed-and-labelled-planned for as long as `m3_reads_from`/`m3_writes_to` stay `status: planned` (drawing skips no gate), and O61's dotted "aligns to platform" cross-branch edge renders as a visually distinct annotation because no confirmed graph relationship backs it. **The sensitivity boundary is in every acceptance:** all three SME-supplied examples live machine-local under `internal-local/` with real SEAL ids/hosts/org values; the committed fixtures are SYNTHESIZED twins of shape only. Ties recorded as ties, not dependencies: O61 ↔ G94 (renders the roll-up, does not consume the selector), O62 ↔ Idea-125 (whether the report also becomes an Ask-agent named-verb answer stays open in the inbox). No existing item's status, id, or text was touched — additive only, by the run's own no-impact constraint.

- **`Idea-123`** · 2026-08-13 · `[idea]` · **groomed → O62 (2026-08-17)** · prio? **Med** —
  **Web UI example output: the "Ask the knowledge graph" file-name search report.**
  SME supplied a real captured example (screenshot machine-local at
  `internal-local/ui-examples/dd-ui-wip-user-query-for-file-name-result.png`,
  transcribed — real SEAL ids/hosts/repo URLs — at
  `internal-local/ui-examples/dd-ui-ask-graph-file-search-transcription-20260813.md`).
  The use case: user searches a FILE NAME (or table) to find the business
  application and process associated with it; the result points to a
  file-transfer process fed by an event-based application, and the generated
  "report" shows the code repos and development teams for BOTH processes so
  support can escalate. Mechanism: a shortest-path traversal from an
  Application anchor filtered on a fileName property (~22-node result spanning
  application / product / dev-team / scheduler folder+job / file-transfer
  route / pipeline / repo labels), plus a source→node-label legend table the
  report view would carry. This is the concrete output target for the Ask
  route — pairs with the Idea-116 swimlane view (same job→pipeline→asset
  chain, report form instead of diagram form).

- **`Idea-122`** · 2026-08-13 · `[idea]` · **groomed → O61 (2026-08-17)** · prio? **Med** —
  **Web UI example view: the product roll-up flow — which area a job/folder
  supports and how it rolls up through the product catalog.** SME supplied a
  rendered mermaid example (screenshot machine-local at
  `internal-local/ui-examples/dd-ui-wip-user-view-product-mermaid.png`,
  transcribed — real org-taxonomy values — at
  `internal-local/ui-examples/dd-ui-product-rollup-mermaid-transcription-20260813.md`).
  The view: folder token = PAT AreaProduct, rolling up AreaProduct → Product →
  ProductLine → LOB, with the TWO roll-up shapes side by side — framework
  applications (no direct SEAL; the AreaProduct token is the join) vs app-tied
  applications (carry SEAL; the Control-M sub-application is the join) — the
  folder-name grammar as the leaf, data classification beneath, and a dotted
  cross-branch "aligns to platform" edge. Candidate UI shape: a mermaid/MiniDag
  flow on the product page; ties to the PRAOCG folder grammar and the G94
  standard-selection decision tree.

- **`Idea-116`** · 2026-08-13 · `[idea]` · **groomed → O60 (2026-08-17)** · prio? **Med** —
  **Web UI: a swimlane data-flow layout for the lineage module — lanes Control-M |
  Data Layer | File Server / Database.** Captured from SME chat while testing the
  wireframe feedback loop (recorded as `FB-2026-08-13-01` in
  `UI-WIP/wireframes/wireframes.json`); the idea traces to the user's original Full
  Circle Docs document-portal concept, §7 Business Flow Diagrams (transcribed
  machine-local at `internal-local/fullcircle-docs-scan-20260813.md`). The wireframe
  half is DONE at capture time: `UI-WIP/wireframes/out/dataflow.svg` (keys
  WF-DFL-01..17; the renderer gained `lane` + `arrow` primitives, spec v2). What
  remains is the React build: a swimlane layout for `/lineage` (proposed
  `lineage/SwimlaneView.tsx`) rendering job → pipeline → asset per data series —
  FW job "detected by" join, launcher→pipeline token join (G15 contract),
  condition edges per the BMC baseline — with READS/WRITES rendered dashed while
  `m3_reads_from`/`m3_writes_to` stay `status: planned` (no gate is skipped by
  drawing them). Wireframe-first is the point: SME feedback cites WF-DFL keys
  before any component exists.

- **GROOM 2026-08-14 (desktop, targeted — `Idea-128` only)** — closed `Idea-128` as **evaluated**: the producer-side GitNexus trial it proposed RAN on 2026-08-14 (desktop) and the entry's own body carries the full verdict, so the groom's whole job was the disposition. Mechanics all passed (clean global install, Windows worker pool fine, ~30s index of the DryDocs repo, working tree untouched so the publish boundary held, `.gitnexus/` a local cache) — but method-grain impact returned `epistemic: "exact"` while missing real receiver-annotated production call sites that plain grep finds, and a tool whose `exact` can be false cannot gate edits; **verdict: do NOT adopt as edit discipline.** **Promoted 0, inboxed 0, merged 0, closed 1.** No backlog item minted — module-boundary tests + grep remain the edit discipline on this codebase, and the entry's cleanup residue (disposable `.gitnexus/` caches, optional `npm uninstall -g gitnexus`) is delete-at-will hygiene, not an item. `Idea-124` (epistemic labeling as a CONCEPT) is explicitly unaffected by this close and stays open — ours must census its blind spots better than this implementation did. `backlog.yaml` is untouched, so `summary:` and `next_ready:` are unchanged by construction; the validator was still run. Nothing here decides an ontology question — the trial never touched the estate graph.

- **`Idea-128`** · 2026-08-14 · `[idea]` · **closed — evaluated at the 2026-08-14 groom: trial ran, verdict recorded in the body, do NOT adopt, no item minted** · prio? **Low** —
  **Producer-side GitNexus trial on the DryDocs repo itself (dev tooling only).**
  R5 of [`docs/reviews/gitnexus-depgraph-comparison.md`](../reviews/gitnexus-depgraph-comparison.md):
  index the DryDocs repo with GitNexus (supports Python; clone at `sandbox/GitNexus`),
  wire its MCP server, and evaluate `impact`/`detect_changes` before `drydocs_core`
  refactors — symbol-grain impact analysis beside (not replacing) the depgraph drift
  ritual. Check in the trial: Windows worker-pool behavior, index time, and that
  `.gitnexus/` stays out of git (their analyzer edits `.gitignore` itself — publish
  boundary). Never touches the estate graph or ontology.
  **TRIAL RUN 2026-08-14 (desktop) — verdict: do NOT adopt as edit discipline; grooming
  should close this as evaluated.** Mechanics all passed: global install clean (gitnexus
  1.6.9; npm 11 allow-scripts gate skipped postinstalls but prebuilt binaries cover it),
  Windows worker pool fine, DryDocs indexed in ~30s via `analyze --index-only` (16,737
  nodes / 27,077 edges), working tree untouched (publish boundary safe), `.gitnexus/`
  ~240 MB local cache. Quality on OUR Python is where it failed: class-grain
  `impact Neo4jClient` was reasonable (48 impacted, import-grain), and the
  ambiguous-name handling (`run_script` → 10 candidates, risk UNKNOWN until
  disambiguated) is genuinely good design — but method-grain impact on the
  disambiguated `Neo4jClient.run_script` returned impactedCount=1 labeled
  `epistemic: "exact"` while missing real receiver-annotated production call sites
  (`drydocs/loaders/base.py:442` `self.client.run_script(...)`, client: Neo4jClient;
  ditto `runs_on_resolution.py`) that plain grep finds. The honesty mechanism we most
  wanted (Idea-124's model) under-reports on Python receiver typing — "exact" was
  false. `trace main → Neo4jClient` found no path (breaks at CLI dispatch, our
  dominant pattern); `detect-changes` mixes markdown Section "symbols" into a
  risk=high verdict (noisy); FTS/BM25 unavailable offline (LadybugDB extension wants
  network). Net: for this codebase, module-boundary tests + grep remain stronger than
  its method-grain graph, and a tool whose `exact` can be wrong cannot gate edits.
  Idea-124 (epistemic labeling as a CONCEPT) is unaffected — ours must census its
  blind spots better than this implementation did. Cleanup: `.gitnexus/` dirs in
  DryDocs (~240 MB) and sandbox/GitNexus (~358 MB) are disposable caches; delete at
  will, plus `npm uninstall -g gitnexus` if not wanted.

- **GROOM 2026-08-13 (desktop, targeted — "the open inbox entries that would impact or change the established node labels and the Cypher loaders")** — the filter was applied to the WHOLE open and parked tail, not only the new captures, and every claim below was re-verified against the tree at the groom rather than taken from the entry. **Promoted 5: `U21`, `U22`, `U23`, `G97`, `Q18`. Merged 1. Inboxed 0. Parked as a question 0.** Four of the five are dependency-free and enter `next_ready` on arrival; `Q18` deliberately does not. **`Idea-118` → `U21`** (p1 bug, `drydocs-load`, phase 16): the code-snapshot load sweeps NODES and never EDGES, so `IMPORTS` only grows — `seal_attribution.py` still carries an edge to `loaders/base.py` that survived a full re-load, against a file with zero occurrences of the string and a snapshot that records no such edge (985 live vs 982 in the snapshot; fan-in 32 where the tree says 31). Written as a PER-SOURCE retraction with the over-reach guard as its own test, because the graph holds edges other loaders wrote; the mark-vs-delete call is left to the item but must be RECORDED, and if edges are marked then the read paths filter them the way U13 made node queries filter. Verified at the groom: `stale_edge_cleanup.cypher` is the repo's only edge-retraction precedent and has NO live caller in the tracked tree, so the pattern exists as a file rather than as a mechanism. **`Idea-117` → `U22`** (p2 bug, `graph-infra`, phase 16): every `:CodeModule` carried one Aug-2 `last_seen_at` for eleven days and the session read A3's fan-in as the Aug-2 value believing it current — the G78 class, a read that SUCCEEDED with the wrong data. The entry explicitly handed the warn-vs-fail call to the groom: **RULED WARN**, on the same argument CLAUDE.md already makes for `snapshot.ps1`'s CI check (recording structure and passing a gate are unrelated jobs, and the check must not red a suite on a machine with no container). What is unit-testable is the COMPARISON over fixtures — fresh / stale / no snapshot / empty graph / database-unreachable, that last one a DISTINCT verdict and never "fresh" — so the mechanism is guarded with no database. Priority dropped to p2 from the entry's High with the reason in the notes: one existing command repairs it and did, so what is missing is detection. `module: graph-infra` chosen on SUBJECT (the loaded graph's currency, U15/U19's family) over `docs` (the review-plan file, U13/U20's) and the choice is recorded in the item, because both were plausible. **`Idea-47` → `U23`** (p3 task, `ontology`, phase 16, `fable`, `ontology-mapper`): the `.cypher` files are `:CodeModule` nodes with zero edges while each loader names its Cypher as a literal path — promoted as a **gate-rider DRAFT and only a draft**, on the G27 / N10 / G95 precedent, because a new relationship type is an ontology decision. Its clause (c) is what stops a signed rider with no path to a first row: the depgraph scanner does not emit the edge, so the prompt must say where it would come from and what an instrument change costs. Clause (d) fences it against gate `self-documentation-code-graph` §H5 — a loader→cypher edge is the FIRST half of the "which module loads this job" join and not the join. **`Idea-23` → `G97`** (p2 task, `drydocs-lineage`, phase 6): the parked trigger has FIRED and the entry was out of date — `m7_uses_artifact` has been `status: active` since 2026-08-07 (gate `rua-load-shapes` §A4, applied at G55), not `planned`, and `writer.py` MERGEs `:ETLProcess` on its token. G16's own notes name this item by description. NO gate is opened: `cmdline-nfr-vetting` ruled the distinct label and the `:Script` refinements, `rua-load-shapes` activated both entries together precisely so the launcher/payload split is right from first load. Verified ABSENT at the groom so this is a real build — the writer emits no `USES_ARTIFACT` edge and stamps `script_role` only for the rua profile case. **`Idea-88` → `Q18`** (p2 task, `drydocs-load`, phase 14) — **the parking is PRESERVED, not overridden**: the entry was parked behind two open rulings, and the item reproduces that as `depends_on: [G32, Q14]`, so it stays out of `next_ready` until both rule while the work becomes visible in the database instead of living only in this file. Its acceptance says in writing that the edge TERM is Q14's and residency is G32's, and it carries Q16's unshipped clause (b). **Merged 1: `Idea-119` → `G78` clause (d) + a rider note on `G79`** — the five loaders with no direct test import (`business_segments`, `controlm`, `controlm_dependencies_derived`, `controlm_hosts`, `seal_contacts`) ride the fix that touches them, which is the entry's own proposed disposition; A5 is named in the clause as a DIRECT-IMPORT proxy so the ask is an import-bearing test, not proof of total absence. `G79`'s note names the two the split re-homes, verified at the groom (`seal_contacts` is a `REFRESH_REFERENCE_CHAIN` member and `business_segments` is refreshed inside the same command, ahead of the chain tuple). **Deliberately NOT promoted, each for a stated reason:** `Idea-86` and the residency half of `Idea-88` stay behind `G32`, which is still `in_progress` (an unsigned drafted gate) — three parked consumers on one gate is an argument for scheduling it, not for pre-empting it; `Idea-7` (flipping the four `m3_*` lineage entries active) and `Idea-37` are HITL-scheduled by their own terms; `Idea-104` (which MFT route-id shape is real) and `Idea-34` (whether the AIS acronym entry survives, and what `:AisTool` ever meant) are label/identifier questions that only the SME can answer; `Idea-15`'s remaining call — display labels only, or renaming the `seal_*` vocabulary ids and domains — is ADR-scale and the user's; `Idea-25`, `Idea-27`, `Idea-31` and `Idea-61` were re-read and their triggers are still unfired. `Idea-122` and `Idea-123`, both captured the same day, DESCRIBE label chains rather than change them — they are UI-view work and belong with the console epic, so this run left them. **Nothing here decides an ontology question:** `U23` is a prompt that registers nothing, `G97` builds inside two signed gates and flips no entry, and `Q18` routes both of its open questions back to `Q14` and `G32` by dependency.

- **GROOM 2026-08-12 (desktop, targeted — `Idea-112`, `Idea-113`, `Idea-114` only, not the open tail)** — three entries captured the same day from live work, all three actionable, so this run promoted rather than parked. **Promoted 4: `G92`, `G93`, `G94`, `G95`** — all four dependency-satisfied and in `next_ready` on arrival. **Inboxed 0, merged 0, parked-as-question 0.** Every claim below was re-verified against the tree at the groom rather than taken from the entry, and all of it is sample-reproducible with no database and no company data (J18). **`Idea-112` → `G92`** (p2 task, `drydocs-lineage`, phase 6, deps G14/G46/G60 all done): the entry's premise holds exactly — `_prepost_pass` in `drydocs_lineage/extractors/controlm_inventory.py` calls `parse_command(value)` on the RAW variables-CSV `var_value`, and `_file_op` keys the asset off that verbatim operand, so `%%R_PATH/out.dat` and `/data/r/out.dat` plan edges to two `DataAsset` nodes for one file; the CMD_LINE pass shares the defect, pre/post merely concentrates it. Written as a FEED change, not a new parser and not a new resolver: `resolve_layers` / `resolve_command_line` (G46, done) already return each definition's `resolved_value` with substitution provenance, and PRECMD/POSTCMD are themselves SETVAR definitions, so the chain that resolves the rest of the job resolves them in place. The acceptance carries the four things that make it reviewable — raw stays beside resolved (the G46 derived-fact shape), `{ODATE}`-class residue counted as EXPECTED and kept distinct from an unresolved user variable, `ResolveCoverage`-style per-run counters on the existing `ExtractCoverage` summary line, and both variables-CSV shapes feeding the scope chain (`var_scope` in the aliased projection; the `JOB_NAME == folder name` header rule in the raw export, per `drydocs/staging.py`). Endpoints unchanged, no new relationship type, `m3_reads_from` / `m3_writes_to` stay planned — no gate. `module: drydocs-lineage` recorded in the item: the change point is the extractor's pass, core's resolver is CALLED not modified. **`Idea-113` → `G93`** (p2 task, `drydocs-remediation`, phase 6, dependency-free): `render_handoff()` in `drydocs_remediation/jira.py` emits Findings / Scope / Change / Equivalence / Acceptance / Rollback and not one count of what the run processed, so the ticket carries no denominator — while the extractors already model exactly this (`ExtractCoverage.summary()` with the G60 `prepost_*` split, `XmlDefsCoverage`, findings by rule). Also verified: NOTHING under `drydocs_remediation/` imports `run_log` today (`drydocs/cli.py` is the only `LoaderRunLog` caller), so the batch-side run log is IN the item rather than assumed. Acceptance pins the five things that keep it honest — counts ride the run log not the console, they are recorded not recomputed at render time (proven by a test where the renderer gets a filtered finding list), skips counted with reasons, absence rendered as *not recorded* rather than omitted, and the equivalence proof NOT restated so a big denominator cannot read as evidence. **`Idea-114` → `G94` + `G95`, split on buildability.** `G94` (p2 task, `drydocs-core`, phase 6, deps G84 done) is the decision tree, and it is buildable now because the repo already has both inputs: `config/launcher-registry.yaml` classifies DPL / ABINITIO / INFORMATICA through `classify_executable()`, and `JOB_ROLES` is already the C30 discriminator set — the gap is that `required_tokens()` keys on `JobType` alone. Its most durable clause is the guardrail-as-test: §7.5 and G84(c) rule the DD digit a grammar VERSION that must not select a standard, so a test asserts the same job under `DD1|` and a hypothetical `DD2|` selects the SAME standard, and the per-engine token CONTENT is explicitly out of scope (an unruled engine inherits the generic set and REPORTS that it did). `G95` (p3 task, `config`, phase 6, `fable`, dependency-free) is the other half as a DRAFTED GATE PROMPT on the G27 / W1 / N10 / G61 precedent — drafting decides nothing — because standard identity and its carrier are a contract change to `TOKEN_REGISTRY`, whose docstring calls itself the single source parser and register both read from, guarded by the registry-vs-standard agreement test. The prompt puts four questions and pre-picks none: identity shape, carrier (versioned YAML under `config/` on the launcher-registry precedent vs. the SQLite table the user floated), ratifying the DD-digit fence explicitly *because a per-team registry is the exact pressure that would break it*, and whether a team profile may RELAX a company-required token or only add. `module: config` recorded in the item — the artifact under discussion is a registry/profile store and `config/` is the declared home for registries; the prompt DESCRIBES a change to a `drydocs-core` module without making one. **Nothing was parked as a question** — no `module` or `phase` was genuinely two-way, and the one decision the user has not made (where a standard lives) is routed to the SME as `G95` rather than guessed. **Left for the user/SME: unchanged from the third pass**, plus the `G95` gate itself.

- **GROOM 2026-08-12 (desktop, third pass — the two entries captured after the second pass)** — the inbox gained exactly two entries since the morning runs, `Idea-110` and `Idea-109`, and they needed opposite dispositions. **Promoted 1: `J48`** (p2 chore, `drydocs-core`, phase 8, dependency-free) from `Idea-109`'s RESIDUE. The reported bug — a worktree-isolated agent running the session-end render ritual writes `board.html` / `ideas.html` / `roadmap.html` into the MAIN tree — was already FIXED the same day at `841dc6e5` (`drydocs_core/repo_paths.py`, adopted in `plan_board`/`plan_ideas`/`plan_roadmap`, 13 tests including one that drives a real `git worktree` through a real `render_board.py`), so what was left was never groomed into anything: **seventeen** other modules still anchor a default path on a raw `Path(__file__)` repo root. Re-counted at this groom rather than taken from the entry — a `grep` for `REPO_ROOT =` across `drydocs/`, `drydocs_core/` and `scripts/` returns 21 sites, of which 3 have adopted `repo_root()` and 1 is the docstring example in `repo_paths.py` itself, leaving 17 (plus `ontology/schema_graph.py`, which uses `Path(__file__)` without a `REPO_ROOT` name and is in the item's inputs for that reason). Evidence is re-runnable with no database and no company data (J18). The item is written as a **sweep with a judgement, not a mechanical replace**, because the entry is explicit that these are not all bugs: repo-*content* defaults follow the caller's checkout, package-*internal* resources rightly keep `__file__`, and each site gets that one-line ruling — with "correct as written" recorded as a package-internal disposition rather than a skip, plus a derived coverage test (the S10 precedent) so a NEW un-ruled site reds instead of passing by omission. Likely dispositions are written into the notes as NON-binding, so the sweep is not re-derived from scratch. `module: drydocs-core` chosen and recorded in the item: the convention, its one implementation and its guard all live in `drydocs_core/`, even though the sites span three trees. **Inboxed 0, merged 0.** `Idea-110` needed nothing — it was captured AND closed the same day (`b268cd36` reclassified `UI-WIP/claude-design-ui-prompt.md` as a dated record), and its residue is a standing habit ("resolve the paths a doc cites before landing an idle branch"), not an item. **Left for the user/SME: 9, unchanged from the second pass** — `Idea-104`, `Idea-74`, `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17` (the two machine-local relics), `Idea-16` (the SNYK repo secret), and the `E1` status question inside `Idea-93`; all were re-verified against the tree hours earlier at the second pass, so this run did not re-walk them. Nothing here touches edge semantics: J48 is path resolution only — no graph write, no vocabulary entry, no gate.

- **GROOM 2026-08-12 (desktop, second pass — "finish any non-HITL open items")** — the inbox had NO new captures (the 08-11 weekly pass consumed Idea-96..Idea-107 and the earlier 08-12 pass worked the tail), so this run did the one thing left that is not the user's: walk every OPEN and residual-clause entry, verify its state against the tree, and either finish it or say precisely what it waits on. **Promoted 1, and it did not come from the inbox:** **K24** (p2 bug) — the `fid-identity-and-scope` gate page carries TWO questions numbered **Q6**, the SME answer landed 2026-08-12 by `887a0e7` and an older, still-open application-roll-up question that was never renumbered when the new one was appended, while FOUR other files cite "Q6" by number (`config/source-mappings/psgmgr.yaml`, `config/source-registry.yaml`, `docs/k16-fid-census-company-prompt.md`, and K16's own "RUN Q6 FIRST" line). Reproduced at the groom with a scan of every file in `config/gate-prompts/` — exactly one collision in the whole tree — so the evidence is re-runnable with no database and no company data (J18). It renumbers only the entry nobody cites and adds the duplicate-id guard to `tests/unit/test_gates_json.py`; it answers nothing, which matters because K17 is the next gate walked on that page. **Fixed in place, 2 stale `inputs:` paths** (the `Idea-93` class, re-audited across all 112 non-`done` items): `G63` and `G64` cited `config/audit-fields/` as a directory when the ledger is the file `config/audit-fields.yaml`. Three refs flagged, two were typos, one (`Y4`'s `backlog/items/`) is a legitimate future output — down from fourteen at the 08-09 sweep. **Two open entries narrowed by verification rather than by a ruling:** `Idea-17` — both pre-squash branches are ALREADY GONE from origin and the stash is empty, so the destructive REMOTE decision it was raised for no longer exists; two this-machine-local relics remain. `Idea-16` — re-verified the `snyk` job is still in `ci.yml` and still gated on the missing repo secret, so it is unchanged and undischargeable by any agent. **Three residual clauses re-read as PARKED with named triggers, not open:** `Idea-20`(a) → a real `CMD_LINE` sample carrying the `ingestion-launcher` jar (a repo-wide search finds that string only in this file and the backlog text quoting it, so an item today would have no input), `Idea-20`(d) → layer-4 context-graph work starting, `Idea-10`'s ALIAS tier → an alias source existing at all. **Inboxed 1:** `Idea-108` — two abandoned agent worktrees pinned at `6c24963` are holding UNCOMMITTED work (6 and 8 changed paths, including the untracked `scripts/render_underhood_benchmark.py`), while all four `worktree-agent-*` branches are already ancestors of `main`; parked rather than swept because the standing rule is that no session touches another stream's uncommitted work, and both salvage and prune are irreversible in one direction. **Left for the user/SME: 9, unchanged** — `Idea-104`, `Idea-74`, `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17` (local half), `Idea-16`, the `E1` status question in `Idea-93` — plus `Idea-108` new. Nothing here decides an ontology question: K24 is identifier hygiene on a gate page and explicitly rules nothing the gate owns.

- **GROOM 2026-08-12 (desktop)** — a SMALL groom by design: the 2026-08-11 weekly pass consumed every new capture (Idea-96..Idea-107), and nothing has been captured since, so this pass worked the OPEN and PARKED tail plus one cross-check the inbox could not have produced. **Promoted 2:** both from the Control-M `DESCRIPTION` seam, both reproduced at the groom with a sample and no database (J18) so anyone can re-run the evidence. **G83** (p1 bug) — C30 ruled the description token set on 2026-08-11 and only the standards page moved: parsing a fully C30-conformant watcher description returns SEVEN findings (`FTS_ID` and `REC_ID` as unknown keys, `ENV` + both route ids + both `EMAIL_DL`s reported missing), and `G67`'s own conformance fixtures already emit `FTS_ID: FTS2`. The judgment call is written into the acceptance rather than left open: retired tokens are MARKED, never deleted, because the deployed estate still carries them and a greenfield standard cannot retroactively unwrite ~240K descriptions. **G84** — the `DD1|` sentinel from `Idea-105`'s SME resolution: today the parser reports the compliant marker itself as an `unparseable_segment`, and legacy prose containing a colon manufactures pseudo-tokens indistinguishable from a C16 team-local annotation. Fenced: a READ gate only, ratifying nothing, with the marker in ONE constant because gate `email-dl-contact-point` §G6 still rules it. **Merged 1:** `Idea-73` (the employee hierarchy) → **G74**, which was raised 2026-08-11 asking the same question from the other end; three findings ride across — O44 column 1 is a second waiting consumer, `pat:people-report` carries teams not reporting lines so it is NOT the source, and the 2026-07-23 HR-hierarchy direction was written for the COMPANY gate, which is why nothing landed here. **One dependency added:** `G77` now depends on `G84` as well as `C34` — its clause (a) registers a THEME token *inside* the `DD1|` block, and without the link two sessions implement the same sentinel differently in one file. **Left for the user/SME: 9** — `Idea-104` (which MFT route-id shape is real; G83 was written NOT to answer it), `Idea-74` (does DryDocs ingest the ServiceNow queue export, and on which side), `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17`, `Idea-16`, and the `E1` status question inside `Idea-93`. **Four parked entries re-checked, none fired,** and two of them narrowed: `Idea-15`'s placement blocker is DISCHARGED (the `generic-naming` epic now exists), leaving one open user call instead of two; `Idea-38`'s class (1) is CLOSED by the 2026-08-11 authored-fixture ruling, leaving three; `Idea-25` and `Idea-27` re-verified unfired against the current tree. Nothing raised here decides an ontology question: both new items are pure-parse, zero graph writes, every token stays `proposed`.

- **`Idea-119`** · 2026-08-13 · `[chore]` · **merged → G78 clause (d) + a rider note on G79 (2026-08-13) — the five untested loaders ride the fix that touches them, exactly as this entry proposed** · prio? **Med** —
  **31 package modules have no direct test import, and five of them are loaders G78 is
  about to change.** A5 measured 2026-08-13 at `bb9788b6`: 31, against the skill's 29
  baseline at `2d104ef` (08-09). By package: `drydocs_core` 14, `drydocs` 10,
  `drydocs_lineage` 4, `drydocs_docmeta` 2, `drydocs_api` 1. The pointed five are
  `business_segments.py`, `controlm.py`, `controlm_dependencies_derived.py`,
  `controlm_hosts.py` and `seal_contacts.py` — untested loaders, while G78 (p0) fixes a
  chain step that silently skips a missing input and reports success. Highest
  single-leverage gap: `drydocs_lineage/extractors/rua_inventory.py`, fan-in 5, no test
  import. Two caveats ride with the number: A5 is a DIRECT-IMPORT proxy, so fixtures and
  subprocess coverage do not show; and the +2 could not be attributed (see Idea-120).
  Proposed disposition on groom: **merge the five loaders into G78/G79's acceptance**
  rather than filing a coverage sweep — the tests belong with the fix that touches them.

- **`Idea-118`** · 2026-08-13 · `[bug]` · **groomed → U21 (2026-08-13)** · prio? **High** —
  **`IMPORTS` edges are never retracted, so fan-in inflates permanently and test debt
  under-reports.** Found while cross-checking the freshly reloaded graph against the
  snapshot it was loaded from. `drydocs/loaders/seal_attribution.py` still carries an
  `IMPORTS` edge to `drydocs/loaders/base.py`; the file contains ZERO occurrences of the
  string "base" (K8 removed it at `4df4df2`), and today's snapshot records no such edge.
  **The edge survived a full `load-code-snapshot` re-run** — so this is not the staleness
  in Idea-117 and a refresh does not fix it. The D7 sweep tombstones removed MODULES;
  nothing sweeps removed EDGES, so the import graph only grows. Size today: 985 live
  `IMPORTS` edges in the graph vs 982 in the snapshot — 3 ghosts, one of which put
  `loaders/base.py` at fan_in 32 where the tree says 31, distorting the repo's #1
  change-risk metric. **A5 is affected in the dangerous direction**: a module whose test
  import was DELETED keeps the ghost edge and still counts as tested, so test debt reads
  better than it is. Fix shape: retract edges absent from the loaded snapshot for any
  module that snapshot DID include — a per-source sweep, never a global delete, since the
  graph holds edges other loaders wrote.

- **`Idea-117`** · 2026-08-13 · `[bug]` · **groomed → U22 (2026-08-13; the warn-vs-fail call this entry left to the groom is RULED WARN in the item's clause (b))** · prio? **High** —
  **The code graph can go stale for weeks and nothing says so.** Found by `/tech-debt`
  2026-08-13 (desktop, `neo4jtest`, `drydocs` DB): every `:CodeModule` carried
  `last_seen_at = 2026-08-02T23:06:42Z` from ONE run id — loaded once on Aug 2 and never
  refreshed, 11 days. The session first read A3's top fan-in as 28, which is the Aug-2
  value (the skill's own baselines run 28 → 29 on 08-04 → 31 on 08-09); it looked current
  and would have been reported as current. Same class as G78 — not a failed read, a read
  that SUCCEEDED with the wrong data, and it sits underneath every architecture and debt
  decision. `drydocs load-code-snapshot` repairs it in one command (run 2026-08-13; graph
  now 1697 modules, 164 tombstones), but nothing compares `max(m.last_seen_at)` against
  the newest snapshot's `meta.captured_at`. Proposed: a freshness assertion in
  `tests/unit/test_code_graph_review_plan.py`, which already fails when the typed package
  allow-list and `pyproject.toml` disagree — the shape exists, this is one more check in
  it. Warn-vs-fail is a real call for the groom: the snapshot ritual's CI check is
  warn-only on the argument that recording structure and passing a gate are different
  jobs, and the same argument applies here.

- **`Idea-88`** · 2026-08-07 · `[idea]` · **groomed → Q18 (2026-08-13), with the parking PRESERVED as `depends_on: [G32, Q14]` rather than overridden** · prio? **Med** —
  **The only loaded software↔docs edge has NO registry declaration behind it — close
  the gap with a `describes_product:` field.** The 27 live
  `(:Document)-[:DESCRIBES]->(:SoftwareProduct)` edges for `controlm` are asserted by a
  hardcoded Python constant — `drydocs/loaders/bmc_docs.py`
  `SUBJECT_PRODUCT_ID = "controlm"` — and the corpus's `doc-source-registry.yaml` entry
  carries only `taxonomy_path`, which NO file maps to a product id. So the one working
  traversal in the estate is unreproducible from the ledger, and a report cannot
  honestly infer the declaration (the /software page refuses to, deliberately — O56
  honesty rule 4). Fix direction: a `describes_product:` field on doc-source-registry
  entries, with the loader READING the registry instead of carrying the constant, plus
  a guard that the id resolves to a real software-registry product. Parked rather than
  groomed because it touches a loader AND a gated corpus behind two open rulings — G32
  (which database corpora live in) and Q14 (which term carries the edge) — and this is
  also where Q16's unshipped clause (b) will land. (Found at the Q16 close, 2026-08-07.)

- **`Idea-47`** · 2026-08-02 · `[idea]` · **groomed → U23 (2026-08-13) — the gate-rider DRAFT only; the edge stays unregistered until the SME signs, and the emitter question rides the prompt** · prio? **Low** —
  **The 45 `.cypher` files are now nodes with zero edges — nothing joins a
  loader to the Cypher it executes**, even though the path is a literal in the `.py`
  (`CYPHER_DIR / "code_snapshot.cypher"`). `drydocs/loaders/` holds 32 `.cypher` + 24 `.py` +
  15 `.sql` side by side, unconnected. depgraph does not emit the edge and the loader could not
  load it if it did (new edge type → gate). This is gate §H5's named future item, now with the
  nodes already in place — the remaining work is the edge, not the corpus.

- **`Idea-23`** · 2026-07-21 · `[idea]` · **groomed → G97 (2026-08-13) — TRIGGER FIRED: `m7_uses_artifact` has been `status: active` since 2026-08-07 (gate rua-load-shapes §A4, applied at G55), not `planned` as this entry recorded, and the writer MERGEs :ETLProcess on its token** · prio? **Med** —
  **m7 build follow-up** (from gate `cmdline-nfr-vetting`): migrate
  payload invocations out of the m3_invokes 1..n fold onto the registered `USES_ARTIFACT`
  edge + stamp `script_role` {launcher, payload} and the artifact_* properties on :Script.
  Feed now EXISTS (G16 value-contract facts + G15 launcher properties); groom once the
  writer's ETLProcess endpoint work makes the edge landable — the vocab entry
  `m7_uses_artifact` stays `planned` until that build's own flip.

- **`Idea-105`** · 2026-08-11 · `[question]` · **groomed → G84 (2026-08-12, the READ gate only — the ruling itself stays the gate's, rider §G6)** · prio? **High** —
  **Two things claim the same 4000-char Control-M `DESCRIPTION` field on generated
  objects, and they cannot both hold.** The DPL generator stamps two literal strings
  (`Generated Control-M Folder`, `Generated job to trigger DPL …`), and
  `internal/controlm-config/controlm-pipeline-stub-integration-plan.md` item **E1** keys
  machine-generated provenance on an EXACT match of those literals. The company
  description-metadata standard captured at C29
  (`internal/controlm-config/reference/controlm-job-metadata-standards-capture.md`)
  fills the same field with pipe-delimited `key: value` tokens. Add a token block and
  E1's literal match breaks; require the literal and the token block has nowhere to go.
  Neither document mentions the other. Three exits: (a) exempt generated objects from
  the token standard — cheapest, but generated objects are the majority of the estate
  and the metadata is most valuable exactly where nobody hand-authored anything;
  (b) fold the literal in as one token (`GENERATED_BY: <generator>`) — keeps both, but
  changes E1 from a string compare to a parse and invalidates the discriminator on every
  object already generated; (c) move the discriminator off `DESCRIPTION` to something
  else the generator also stamps. DECIDE with whichever item lands E1; raised as gate
  rider `email-dl-contact-point` §G6 so a section-C ruling cannot presume an exit
  silently. Sibling finding: REQ-3 in the same capture reintroduces the dot-smuggling
  pattern (`…%%$NEXT..tok`) that the description-metadata plan §3 lists as hazard #1 —
  so the practice is not extinct in the *standards*, not just in the legacy estate.
  **CHECKED AT THE 2026-08-11 GROOM — still open, and already carried in two places, which is why no item was minted.** C29's notes record the collision verbatim, and it rides `config/gate-prompts/email-dl-contact-point.yaml` as rider §G6 so a section-C ruling cannot presume an exit silently. There is still NO backlog item landing the stub plan's E1, so there is nothing to merge into; the three exits (exempt generated objects, fold the literal in as a `GENERATED_BY:` token, or move the discriminator off `DESCRIPTION`) have materially different costs on an estate that is mostly generated objects, so this is a user/SME ruling at that gate rather than a groom decision.
  **RESOLVED 2026-08-11 (SME design session) — EXIT (d), which none of the three recorded
  exits describes: a VERSIONED SENTINEL PREFIX partitions the field, so both claims hold
  unchanged and nothing already deployed migrates.** A description that begins `DD1|` is
  authored to the token standard; one that does not is either the generator's literal or
  legacy filler. E1 keeps its exact-match discriminator because generated descriptions
  never carry the tag; the token parser never sees a generated object it would choke on;
  and legacy waterfall prose becomes a third, correctly-ignored class. Cheaper than all
  three recorded exits: (a) loses the metadata where the estate is densest, (b)
  invalidates E1 on every object already generated, (c) needs a new carrier the generator
  stamps — (d) costs one prefix and zero migrations. It also RETIRES C29's proposed
  `GENERATED_BY` token: absence of the tag on a literal-match description already is the
  provenance signal, so a token asserting it is a second carrier for one fact.
  THE DESIGN THAT RIDES WITH IT, all SME-ruled the same session:
  (1) the digit is a VERSION, not a template id — `DD1|` / `DD2|` parse side by side
  through a grammar migration, and template selection is `TASKTYPE` (derived) plus the
  already-registered `JOB_ROLE` token (declared), never the sentinel;
  (2) anchored at position 0, so the check is `startswith` — the cheapest possible SQL
  predicate at ~240K jobs, and prose that quotes the convention cannot false-positive;
  (3) FOLDER SCOPE is preferred, because `get_description()` is generator-owned and a
  tagged block on a generated JOB is overwritten at the next regeneration;
  (4) the compliance objection dissolves rather than being solved — untagged means
  unread, so multi-team inconsistency costs COVERAGE (a number that grows) instead of
  corrupting data (a number that never closes). Under 10 folders carry the standard
  today, which is a sample size, not a weakness: what is being proven is that the round
  trip is lossless and the vocabulary holds WHEN the field is filled, never that teams
  will comply.
  Recorded at the gate as rider §G6 exit (d) and specified in
  `knowledge/standards/technology/controlm-guidelines-and-standards.md` §7.5. The gate
  still RULES it — this entry stops being an open question and becomes a recommendation
  with a written warrant. NOTE for the company side: their copy of the gate prompt is
  canonical-company and did not take the producer edits, so RELAY-7 carries this across.


- **`Idea-73`** · 2026-08-05 · `[source]` · **merged → G74 (2026-08-12) — the item that owns the :Employee backbone now carries the source question, the O44 column-1 consumer and the company-side reading** · prio? **High** —
  **Where does the employee hierarchy come from, and does it live producer-side at
  all?** Established while drafting G35: `:Employee` is a node class (`prov:Agent`)
  with **no Employee-to-Employee edge anywhere** in the relationship vocabulary —
  no `REPORTS_TO`, no manager edge, no source feeding one, no backlog item that
  would create one. Two separate SME directions now depend on it: G35 §B7 ("if a
  person is in the role, create the relationship to the employee hierarchy in a
  later pass") and O44's first column, whose manager filter is its whole point.
  The 2026-07-23 producer-session HR-hierarchy direction — single `:Employee`
  backbone, two-scope HR supplement, two-pass loader, `REPORTS_TO` current-state
  sweep — was written for the **company** `hr-emp-hierarchy` gate, which is
  probably why nothing landed here. Decide whether the producer repo gets a
  hierarchy at all (with what source — `pat:people-report` carries teams, not
  reporting lines), or whether both directions are company-side and the producer
  records that explicitly. Marked High because two committed directions currently
  defer to something that does not exist, and a deferral pointing at nothing is an
  omission with better wording.


- **GROOM 2026-08-11 (desktop, weekly)** — worked the eleven ungroomed 2026-08-09..08-11 captures plus one misfiled entry found at the bottom of this file. **Promoted 10:** `Idea-96`→**J42** (the backlog union rule has no guard — a port-time id-set diff), `Idea-100`→**J43** (a `gate_bound:` precondition key on PORT-MANIFEST rows), `Idea-103`→**J44** (where the unclosed-fence guard's boundary sits for captured and vendored markdown), `Idea-99`→**J45** (the owed DPL/Snowflake port relay), `Idea-106`→**J46** (the clock-racing run-log collision test), `Idea-107`→**J47** (no guard asserts a PORT-MANIFEST path exists; the ordering check is hardcoded), `Idea-98`→**C33** (the adhoc Ab Initio version loader C25 authorized), `Idea-97`→**U20** (the review plan's six-scan-roots baseline, two package generations stale), `Idea-102`→**K22** + **K23** (the Deployment Module CI class via the gate, and the KB-article grain check). **Merged 2:** `Idea-101` into **J43** as clause (b) — same file, same vocabulary, same reviewer, so the derived-render disposition is decided in the same pass; `Idea-102`'s register-line finding into **G70**'s notes rather than its acceptance, because that acceptance mirrors a SIGNED gate register and a groom does not edit one. **Left open as questions for the user/SME: 2** — `Idea-104` (which MFT route-id shape is real, updated with what C30 did and did not settle) and `Idea-105` (the two claimants on the 4000-char `DESCRIPTION` field; three exits, already carried as gate rider §G6 and in C29's notes, with no item landing E1 to merge into). **One id repaired:** the 2026-08-11 manifest-guard capture had been filed as a second `Idea-86` and appended BELOW this audit trail — renumbered `Idea-107`, tagged `[bug]` instead of the non-vocabulary `[guard]`, and groomed. Every item raised here is dependency-free, so all ten enter `next_ready` on arrival; nothing raised decides an ontology question — K22 and K23 both register `planned` and route via the gate.

- **`Idea-96`** · 2026-08-09 · `[chore]` · **groomed → J42** · prio? **High** —
  **The backlog union rule has no guard: nothing asserts that after a port the consumer's
  item-id set is a superset of the producer's at the port base.** `PORT-MANIFEST.yaml`
  states the rule unconditionally for `docs/restructure/backlog.yaml` — *"Union the items;
  NEVER regress a status … or drop an entry"* — and `tests/unit/test_backlog.py` enforces
  plenty about the file (schema, roll-up arithmetic, `next_ready`, unknown `depends_on`),
  but every one of those checks looks at ONE copy in isolation. The union is a claim about
  TWO copies, and no check ever compares them, so a port that quietly under-delivers items
  leaves both sides internally consistent and passing. Textbook J26: a rule written in
  prose and enforced by nobody, which is exactly the shape that survives unnoticed —
  surfaced during a reconcile, where items present in the producer at the port base turned
  out to be absent downstream and neither side's suite had anything to say about it. Note
  the near-miss that makes this worse than it sounds: the dependency guard would have
  caught it *if* any surviving item had depended on a missing one, so whether the gap is
  visible at all is luck, not design. Shape of the fix: a port-time check (not a unit test
  — the producer tree cannot see the consumer's) that diffs the two id sets at the recorded
  port base and fails the port report on a non-empty producer-minus-consumer difference,
  with a named allow-list for ids deliberately not carried. Cheap, and it converts the
  union rule from a promise into an assertion. Mechanism only — the numbers and ids from
  the occurrence stay in the port report, not here.

- **`Idea-97`** · 2026-08-09 · `[bug]` · **groomed → U20** · prio? **Low** —
  **The review plan's doc-coverage baseline is two package generations stale — same disease
  U18 just fixed one table over.** `docs/reviews/code-graph-review-plan.md` Phase 3 unit 3
  still reads *"Six scan roots × DesignDoc coverage"* with per-root counts (`tests` 85,
  `drydocs` 41, `drydocs_core` 35, `lineage` 12, `remediation` 7, `deepdoc` 3) that predate
  BOTH `drydocs_api` and `drydocs_docmeta`. U18 widened the A1–A6 metric scope to eight
  package roots and guarded the typed list against `pyproject.toml`, but that guard is
  anchored on the `$packages` literal and this unit hard-codes its own root list in prose,
  so it was out of the guard's reach and out of U18's stated surface. Left deliberately
  rather than swept in. Fix is small: restate the unit on eight roots, re-measure the
  per-root doc coverage, and decide whether the count belongs in prose at all or should be
  derived like the metric scope now is — the third hand-typed root list in the same
  document is the argument for deriving.

- **`Idea-98`** · 2026-08-09 · `[chore]` · **groomed → C33** · prio? **Med** —
  **The adhoc Ab Initio version loader — the build C25 authorized and deliberately did not do.**
  Gate `software-version-context` signed the shape and nothing else:
  `reg_appuser_uses_software` is registered `status: planned`, no loader exists, and the
  `adhoc-sme-email` corpus stays `confirmed: false` for that reason alone. The build is:
  the loader itself (MERGE key `{source, install_path}`, edge properties per §B3, `as_of`
  from the email's sent date), the `:Document` minted from a hand-recorded citation, the
  `evidence:` block's `as_of` filled in on the `abinitio` product row, registration in
  `config/manual-loads/manifest.yaml` per §E4, and the §C1 install-path pattern rows in the
  `invocation_patterns` shape. **Settle §Q3 before writing the MERGE key, not after** —
  the gate deferred it with the consequence stated: if the estate re-points installs by
  symlink, `install_path` is a poor key and identity moves to `(fid, version)`, which is a
  re-key rather than an edit. Two things this build must NOT do: write the §F
  application-level rollup (blocked on K17, and not behind a flag), and auto-append observed
  versions to the curated `versions:` list (§C2).

- **`Idea-99`** · 2026-08-09 · `[chore]` · **groomed → J45** · prio? **Med** —
  **Port relay owed: the producer is now canonical for the DPL and Snowflake registry
  entries.** C25 registered the `dpl` and `snowflake` product rows, the `in-house` vendor
  (no `publisher_url`, guard narrowed to third-party vendors), and the acronym
  `DPL: "Data Pipeline Library"`. The SME began the same expansion company-side on
  2026-08-07 and **stopped so the two copies would match** — so this is a deliberate
  producer-first divergence with a waiting consumer, exactly the shape of the standing AIS
  acronym relay (R1), whose lesson applies here too: that expansion had to be carried
  ACROSS FILES rather than same-file overwritten, and this one may as well. Deliberately
  NOT written into `docs/port-prompt.md` at the time it arose, because a port was in flight
  against a fetched head and that file is a hand-merge surface — a relay added mid-port
  lands in someone's conflict resolution instead of their checklist. **Add it once that
  port merges**, together with the other post-port items (the staged clean-add rows, the
  ledger roll, striking R4).

- **`Idea-100`** · 2026-08-09 · `[bug]` · **groomed → J43** · prio? **High** —
  **The manifest has no way to say "gate-bound" — and that gap nearly shipped an unsigned
  gate's ontology.** The best finding in PORT-REPORT-0d3761a9, caught company-side by their
  own re-check rather than by any guard: their initial vocabulary reconcile ACTIVATED the
  G55 `rua-load-shapes` lineage flips, because K8 (`seal-app-ref-edge-reshape`) *is* signed
  company-side and the files looked takeable. `rua-load-shapes` is a DIFFERENT gate and is
  still unsigned there. They reverted all three vocab fragments; the G23/rua code ported
  inert because it is gate-bound and refuses `planned` labels — so the code's own guard
  caught what the manifest did not. **The rule they wrote down is the one this repo should
  encode: "identical to base" and "per-entry equivalent" are BOTH insufficient tests for a
  gate-bound file.** A producer vocabulary or test file can be byte-identical to the port
  base and still assume an active gate the consumer has not signed — status/id-set parity is
  not field-and-gate parity. Today `PORT-MANIFEST.yaml` expresses disposition (who wins) but
  nothing about PRECONDITION (what must be signed first), so
  `drydocs_core/ontology/relationship_vocabulary/**` carries a disposition that is right
  whenever the gates agree and dangerous exactly when they do not. Shape of the fix: a
  `gate_bound:` key on those rows naming the gate id, and a reconcile-time check that
  refuses to activate an entry whose gate is unsigned on the RECEIVING side. Note the near
  miss honestly — this was caught by a human re-reading their own work, which is not a
  control.

- **`Idea-101`** · 2026-08-09 · `[question]` · **merged → J43 (clause b — the derived-render disposition, decided across every derived row in one pass)** · prio? **Low** —
  **Does the manifest vocabulary need a `derived` disposition?** Raised by the company's
  send-back on the two roadmap rows and deliberately not settled unilaterally. Derived
  renders — `docs/plan/board.html`, `docs/plan/roadmap.html`, the design-doc `.html` — all
  carry `disposition: canonical-company`, which is a poor fit: there is no authored consumer
  content to be canonical about, and the actual instruction in every one of their notes is
  REGENERATE from the reconciled tree. `canonical-company` and "regenerate" differ in a way
  that matters — the first says *keep what you have*, and keeping a stale render is as wrong
  as taking the producer's. The `roadmap.yaml` row had the same class of defect and was a
  clear enough case to fix outright (`evaluate` → `per-entry`, since its note already
  prescribed a deterministic rule); this one is not, because splitting a single row away
  from the board.html precedent would create a worse inconsistency than the imprecision.
  Decide it across all the derived rows at once, or leave it and say why in the manifest.

- **`Idea-102`** · 2026-08-09 · `[question]` · **groomed → K22 (the CI class, via the gate) + K23 (the KB-article thread); merged → G70 (the shared-subject finding for §G13/G14/G15)** · prio? **High** —
  **The deployment grain has an SME-confirmed cardinality and no home — DryDocs has one
  concept where the source has two.** K21 found `u_seal_deployment_id` sitting beside
  `u_seal_application_id` on the CSDM Application Service row (`cmdb_ci_service_discovered`),
  never on `cmdb_ci_business_app`. The SME then confirmed it directly: **one application,
  multiple deployments is correct**, with the identifier reading as
  `app_id(seal_id):deployment_id`. That closes the condition C10's gate-bound candidate #1 was
  deferred on ("only when an environment-level use case lands"). **THE SAME SESSION ALSO SUPPLIED
  THE CAVEAT THAT SHRINKS IT, and the caveat is the more valuable half:** *everything we map is
  off the **application**; modules are referenced by default for changes but in practice are not
  used as intended.* So the grain is ruled — attribution stays on the application,
  `seal-tom-attribution-reshape`'s subject does NOT move, and `:BusinessApplication` is correct
  as-is. What survives is much smaller than it first looked: **capture an identifier the source
  carries and we discard**, not re-home attribution. Worth writing down precisely because the
  expensive reading was the plausible one — this repo's grain corrections (K1/K2, and the
  2026-07-22 move of SEAL attribution from job level to the folder→batch `:Port`) are exactly the
  shape this looked like for about an hour. **What is left.** (1) **The key, and it still
  blocks.** If the deployment id is scoped under the application id, a bare `deployment_id` is
  NOT a business key and a loader keying on it alone MERGEs distinct deployments together — the
  identity-gate §D2 / §C3 failure on a new axis. **UPDATED 2026-08-10 — the SME supplied the CI
  topology and it answers the key question and renames the thing.** The CI class is the
  **Deployment Module**: `Business Application [Instantiates] Deployment Module`, inverse
  `[Instance of]`, and above it `[Contained by] area product`. Each Deployment Module carries its
  OWN unique CI id, so the CI id is the key and `app_id:deployment_id` is the human-readable name
  — which is itself the proof the deployment id is scoped, since a globally unique id would not
  need the application in its name. **"Deployment" and "module" are ONE thing**, which means G35's
  G13 (Deployment Owner), G14 (Deployment Information Owner) and G15 (Application Module Owner)
  plausibly share ONE subject and could resolve together rather than one register line at a time.
  **A CORRECTION THIS ENTRY MUST CARRY, because its first version had it backwards:** the module
  reference being a form default applies to TRANSACTIONAL records — a Change, an Incident or a KB
  article must name a deployment module, ServiceNow defaults it, and people accept the default. The
  Deployment Module CI ITSELF is real, with its own id, its own place in the chain, and KB articles
  attached. So the grain is sound and only the *counting of transactions per module* is not; the
  earlier conclusion that §G15 needed no grain would have discarded a real CI class on the strength
  of a defaulted foreign key. (2) **The label**, if we capture it: C10's standing advice holds —
  adopt the CONCEPT, pick our own stable name, since the vendor's own label moved (Application
  Service → Service Instance at Yokohama), and this instance's own inverse label (`Instance of`)
  already differs from the one public material uses (`Instantiated by`). (3) **A rider on an
  existing gate, not its own gate** — nothing changes an attribution subject. **AND A SEPARATE
  THREAD WORTH ITS OWN ITEM:** KB articles link at Deployment Module grain and the SME called them
  "more meaningful." A documented fix attached to the deployment that has the incident is squarely
  what a production-support knowledge graph is for; it would promote the `kb_*` family from ring 3
  to a real candidate. Check first whether the KB→module link is asserted or defaulted, since the
  defect above would hit it identically. Evidence, and open questions 8 + 9:
  `knowledge/upgrade-plans/servicenow-replica-evidence.md`.

- **`Idea-103`** · 2026-08-10 · `[bug]` · **groomed → J44** · prio? **Low** —
  **Five more unclosed markdown fences live outside the `docs/**` guard, in files this
  repo did not author.** The J41 sweep that found the `port-prompt.md` defect
  (`84ed7e3`, live five days and four ports) scanned all 507 tracked `.md` files and
  found six. One was ours and is fixed (`docs/decisions/0002` carried an orphan trailing
  fence). `tests/unit/test_markdown_fences.py` now guards `docs/**`. The rest were left
  DELIBERATELY, and the reason is the interesting part: `internal/cdo-reference/`
  CONFLUENCE-TRANSCRIPT.md (opens 5140 of 5355) and TRANSCRIPT-1-ONTOLOGY.md (419 of
  568) are CAPTURED transcripts, and `.claude/skills/data-context-extractor/references/`
  is vendored skill material — editing either to satisfy a guard means editing somebody
  else's capture, which is a provenance decision rather than a formatting one.
  `SDLC-Docs/extracted/issue-driven-capture-loop.md` (181 of 181) is a trailing orphan
  and probably safe. DECIDE: widen the guard with an explicit capture carve-out, or
  leave captures unguarded and say so where the boundary lives.

- **`Idea-106`** · 2026-08-11 · `[bug]` · **groomed → J46** · prio? **Low** —
  **`test_loader_run_log.py::test_naming_convention_and_collision_suffix` is clock-flaky.**
  It calls `claim_log_path()` twice and asserts the second gets the `-2` collision
  suffix — but the suffix only appears when both calls land in the SAME second, since
  the name is stamped `YYYYMMDD-HHMMSS`. If the clock ticks between the two statements
  the second call gets a fresh timestamp and no suffix, and the assertion fails.
  Observed failing once and passing on the immediately following identical run
  (2026-08-11, desktop, during the C30/G67 close-out). Fix: freeze the clock for the
  two calls rather than racing it — the collision behaviour is what is under test, not
  the timestamp.

- **`Idea-107`** · 2026-08-11 · `[bug]` · **groomed → J47** · prio? **Med** —
  **No guard asserts that a `PORT-MANIFEST.yaml` path still exists.**
  Found at G75: the row `drydocs_core/controlm/**` pointed at a path that has not
  existed since the S2 / ADR 0008 relocate under `orchestration/`, so every module in
  the Control-M package was silently falling through to the generic
  `drydocs_core/**` evaluate-on-collision row instead of the canonical-producer row it
  was written for. Nothing failed, because `tests/unit/test_port_manifest.py` checks
  uniqueness, dispositions, notes and pins — never existence.
  `test_runbook_currency.py::test_every_path_a_document_names_exists` already does
  exactly this job for DOCUMENTS, and its FOREIGN_PATHS / HISTORICAL_PATHS escape
  hatches are the right shape here too: a manifest legitimately names company-only
  paths (`drydocs/docmeta/**`, `drydocs/scrapers/**`) and glob rows that match nothing
  producer-side. So the guard is "every non-glob row resolves, every glob row matches
  at least one path, unless allowlisted with a reason".
  Second half, same family: `test_overrides_precede_their_broader_glob` only checks a
  HARDCODED list of four overrides against `config/**`. A new specific row placed after
  its broader glob passes today — verified at G75, where the ordering had to be fixed by
  hand. Derive the pairs instead: any row whose path is a strict prefix-match of a later
  glob row is an ordering defect.
  RENUMBERED AT THE 2026-08-11 GROOM: captured as `Idea-86`, an id the 2026-08-07
  `[source]` entry already held — the second two-session id collision in this file after
  the duplicate `Idea-101` that J41 records. The older entry keeps the id; commit
  `d05811a`'s message is the only surface carrying the short-lived spelling. It also
  landed BELOW the audit trail rather than at the top of the inbox, and its `[guard]`
  tag is not one of the six — both corrected here.


- **GROOM 2026-08-09 (desktop, weekly)** — worked the six 2026-08-08 persona Run-2 captures plus the two `open` chores the 2026-08-07 pm groom left standing. **Promoted 11:** `Idea-91`→U18, `Idea-92`→U19, `Idea-94`(mechanism half)→L27, `Idea-95`(c)→V11, `Idea-85`→**G62/G63/G64/G65** (one item per gate session — the four post-G22 data-profile prompts were drafted 2026-08-07 and had no id, so the pull loop could not see them), `Idea-87`→J40, `Idea-90`→C28 + Q17. **Merged 3:** `Idea-94` and `Idea-95`(a,b) into **L19** (second filing — the sweep never ran and the drift got worse, so L19 was raised p3→p2 and re-stated with Run-2 numbers, and clause (f) now covers the S5 fragment-split re-cites); `Idea-90`’s location findings into **Z2** (mixed grain + the enumerable-site-vs-aggregate-claim line, as required confirmations). **Executed in place 1:** `Idea-93` — fourteen stale `inputs:` corrected directly in `backlog.yaml`; its E1 status question stays open and the entry stays in the inbox, marked. **Parked as a question: 0.** Two HITL-safe drafts, deciding nothing: C28 (business-layer ORG prompt, `status: planned` terms only, sign-off a separate session) and Q17 (a PROPOSED decision record the user rules) — the G27/W1/U16 precedent.

- **`Idea-95`** · 2026-08-08 · `[doc]` · **merged → L19 (clauses a+b, the second filing) + groomed → V11 (clause c, 2026-08-09)** · prio? **Med** —
  **Doc-drift second filings + one new gap** (persona Run 2, U-tw). (a)
  `drydocs_lineage/model.py` still cited by no traceability component — fan-in has
  grown 9 → 24 and it is the G22-reshape fan-out surface (`base.py` DID get its cite,
  so the Run-1 line half-landed). (b) `sdlc-neo4j-schema.md` §DEP: all three Run-1 rows
  still stale, and the vocabulary row is now TWO moves behind (G2 re-home, then the S5
  fragment split); the file gets additive edits (a C23 note landed 08-03) but no
  verification sweeps — regenerate §DEP from the tree. (c) NEW: `drydocs_docmeta`
  (10 modules) has no design doc or runbook — the same growth stage that produced the
  core-runbook after Run 1 flagged drydocs_core.

- **`Idea-94`** · 2026-08-08 · `[doc]` · **merged → L19 (the sweep) + groomed → L27 (the enforcement mechanism, 2026-08-09)** · prio? **High** —
  **Design-doc re-cite sweep, SECOND filing — now with a mechanism ask** (persona Run 2,
  U-tw: `docs/reviews/persona-tech-writer-2026-08.md`). The Run-1 sweep never ran: all
  five pre-squash cites unchanged (`807e050`, `ac2ea2e`, `97ee81c`, `24d6a4b`,
  `0e036ff`); `drydocs-startup-refresh-runbook` reached Rev 10 (seven bumps since
  Run 1) still citing squash-day `a135a6d`; `drydocs-mapping-store-runbook` took two
  bumps on `22d1a39`; `drydocs-mapping-demo-runbook` still has no `commit:` at all;
  `drydocs-project-tdd` was edited 08-06 on a dangling cite. The pattern is behavioral —
  rev bumps happen, cite refreshes don't — so beyond the one-time sweep, add
  enforcement: the design-doc renderer or a unit test should fail on a `commit:` that
  is unreachable from HEAD.

- **`Idea-92`** · 2026-08-08 · `[bug]` · **groomed → U19 (2026-08-09)** · prio? **Med** —
  **Depgraph scanner blind spot: imports rooted off the repo root never resolve**
  (persona Run 2, U-arch F1). `scripts/render_board.py:56-62` imports seven sibling
  scripts by bare name — zero `scripts→scripts` edges in the graph; `agents/` modules
  import `common.*`/`graph_qa.*` against the `agents/` sys.path root — zero
  `agents→agents` edges. Absolute imports from the same files DO resolve, so the U6 fix
  is fine; what is missing is per-directory sys.path roots (or an alias map) in the
  extractor. Until fixed, the 23-item first-party orphan queue is mostly false positives
  and only the package-scope metrics are trustworthy.

- **`Idea-91`** · 2026-08-08 · `[bug]` · **groomed → U18 (2026-08-09)** · prio? **Med** —
  **U14 `$packages` allow-list is missing `drydocs_docmeta`** (persona Run 2, U-arch F4:
  `docs/reviews/persona-python-architect-2026-08.md`). The package was born 2026-08-04
  (`d647171`) — the same day the U14 baselines were measured — and has a MODULE_MAP row
  and a `test_module_boundary.py` entry, but the tech-debt skill's A1–A6 pack and the
  review plan still scope metrics to seven roots, so all 10 docmeta modules are invisible
  to A3/A4/A5. Fix: add the eighth root in both places, re-baseline A3/A5, and note the
  two untested connectors (`connectors/filedrop.py`, `connectors/web.py`) while there.
  Same failure shape as Run 1's `drydocs_api` census miss, one package generation later.

- **`Idea-90`** · 2026-08-08 · `[idea]` · **groomed → Q17 (corpus reshape) + C28 (org-structure gate DRAFT); merged → Z2 (the location grain + claim-vs-site findings) — 2026-08-09** · prio? **Med** —
  **Business-layer location experiment ran (annual report + ORG/location ontology) —
  three decisions queued.** Full write-up:
  `internal/context-graph-analysis/business-layer-location-experiment.md`. The GraphRAG
  search verdict: the `jpmc-reports` corpus is registered (External, `target_db:
  ddcontext`, `:DataAsset`-slice shape, `confirmed: false`) but `ddcontext` is EMPTY on
  the desktop (`neo4jtest`, probed 2026-08-08) and the registered shape is not the
  lexical backbone, so no vector retrieval is possible either way. The hand-applied ORG +
  location pass over the public sources produced a coherent business layer regardless:
  org units = the LOB layer verbatim ("managed on an LOB basis"), an effective-dated
  `org:ChangeEvent` (the 2Q2024 segment merge), sites at MIXED grain (street → city →
  country), and a hard epistemic line between an enumerable `org:Site` and an aggregate
  presence claim ("177 locations") that must never be exploded into fake site nodes.
  Queued: (1) the corpus's named P4+ reshape decision now has a real consumer — lexical
  backbone vs slice shape, and the newer 2025/2026 editions at the repo root should ride the
  re-ingest; (2) the §3 ORG mappings are gate material (`status: planned` proposals) —
  grain + claim-vs-site findings feed Z2, the org-structure shapes want a business-layer
  gate or E-epic item; (3) any re-ingest gates on the desktop ddcontext provisioning
  check (`Idea-49`). Also proves the Z5 map contract is satisfiable from the business
  layer alone — a located-nodes world map needs no technical layer.

- **`Idea-87`** · 2026-08-07 · `[chore]` · **groomed → J40 (2026-08-09)** · prio? **High** —
  **Company docmeta has diverged and is AHEAD — exactly the class a port silently
  clobbers.** Port A landed on the company side and then moved: their ADR is
  `0005-docmeta-document-ingestion.md` where the producer has docmeta at **ADR 0006**
  (`0006-docmeta-component-and-doc-graph.md`, and producer 0005 is the browser↔Neo4j
  access path — so the numbers COLLIDE with different subjects); their package is
  `drydocs.docmeta` (`drydocs/docmeta/`) where the producer has top-level
  `drydocs_docmeta/`; and they carry `prompts.py` and `pipeline.py`, which the producer
  does not have at all. A straight producer→company port take would overwrite the
  package path, renumber-or-duplicate the ADR, and drop two files that only exist over
  there. Needs a deliberate reconcile decision before the next docmeta port — at
  minimum: which ADR number is canonical on each side, whether the package paths
  converge or stay deliberately divergent with a recorded reason, and whether
  `prompts.py`/`pipeline.py` back-flow to the producer. Relates to `Idea-79`/J34
  (the PORT-MANIFEST company-overlay seam) — same failure mode, different artifact.

- **`Idea-85`** · 2026-08-07 · `[chore]` · **groomed → G62, G63, G64, G65 (2026-08-09 — one item per gate session, as the entry asked)** · prio? **Med** —
  **Backlog ids + scheduling for the four post-G22 data-profile gate prompts**
  (drafted 2026-08-07, unsigned): `rua-bundle-data-profile`,
  `repo-manifest-data-profile`, `dpl-pipeline-registry-contract`,
  `dpl-dataset-registry-contract` in `config/gate-prompts/`. Each has the same
  two-step shape per SME direction: §A HITL identify-the-source-data (Internal)
  → §B agent profiles the existing data → §C rulings. The dpl pair discharges
  T13; repo-manifest is the trusted_ref blessing venue; rua-bundle gates any
  load population beyond the G22-walked bundles. Promote with ids + agent/model
  at next groom; sessions are company-side (real data lives there).


- **GROOM 2026-08-07 (laptop, Q16-session gaps)** — source was the session, not this file, so no inbox line moved; recorded here because the ids are new. **Closed:** `Q16` → `done` as an explicit PARTIAL close (clause (a) shipped at b297268 / 9b4cf59 / 0ddf880; clause (b), the pointer reaching the graph, is NOT done and stays blocked behind Q14, which is behind G32 — said in the close note rather than implied by the status). **Promoted 3, all epic web-console:** `O56` (the `/software` page, groomed `done` — it was BUILT at 9b4cf59 before any item claimed it, so the ledger was carrying an invisible surface), `O57` (a console page for the load-map content no web/ code reads — 28 pipeline sources, 15 systems, 17 retired ids, 17 sequence steps; N5 chose the print surface, so the JSON's console consumer was never scoped), `O58` (a docs-verify surface, `fable` because its transport choice can change the drydocs_api read-path boundary — the sweep is multi-database and a QuerySpec carries exactly one `database:`). **Inboxed 4, none promoted:** `Idea-86` (MWAA corpus, parked on G32 per the user's ruling), `Idea-87` (company docmeta divergence — ADR number AND package path, port-clobber class), `Idea-88` (the undeclared bmc-docs→controlm link; also where Q16's clause (b) lands), `Idea-89` (OverviewRoute renders all modules unfiltered). **Merged 0.**

- **GROOMED TOGETHER 2026-08-07 (pm)** — the OLD OPEN TAIL. The morning groom cleared the fresh Idea-56..84 cohort; this run worked the entries that had been sitting `open` since 2026-07-03 through 2026-08-04, and promoted 15 of them: `Idea-84`→J36, `Idea-54`→J37, `Idea-18`+`Idea-24`+`Idea-26`→**J38** (one item, because the three share a defect rather than content — the inbox is not a channel the other repo reads), `Idea-19`→J39, `Idea-52`→G59, `Idea-20`(c)→G60, `Idea-21`→G61, `Idea-51`→N11, `Idea-43`→D10, `Idea-42`→U16, `Idea-48`→U17, `Idea-55`→O54, `Idea-40`→O55, `Idea-8`→L26, `Idea-1`→R14. Two HITL-safe drafts, not decisions: D10 (the XML-vs-replica precedence prompt) and G61 (the two provenance gap classes) both DRAFT and rule nothing, per the standing G27/W1/N10 precedent. `Idea-41` merged into J34 and `Idea-20` marked partial — both stay in the inbox. Left open on purpose, and named in the groom report: `Idea-73`/`Idea-74` (user decisions blocking O44), `Idea-32` (SME scope call), `Idea-34`/`Idea-33`/`Idea-28`/`Idea-16`/`Idea-17` (SME rulings, user manual steps, destructive ref deletion — none of them a groom's to make).

- **`Idea-84`** · 2026-08-07 · `[bug]` · **groomed → J36 (2026-08-07 pm)** · prio? **Low** —
  **Testcontainers integration tests on this desktop need
  `TESTCONTAINERS_RYUK_DISABLED=true`.** At the G23 e2e build, container startup
  failed with "Port mapping ... port 8080 is not available" for the ryuk reaper —
  reproduced identically on an existing J9 test, so pre-existing environment
  trouble, not the new test. Workaround (remove stale ryuk containers, then set
  the env var) ran the new e2e green in 22s. Decide: pin the env var for this
  machine class (integration-test docs or conftest), or fix the underlying port
  conflict. (Found at the G23 close, desktop, 2026-08-07.)


- **`Idea-55`** · 2026-08-04 · `[idea]` · **groomed → O54 (2026-08-07 pm; the "registry must accept a module path" blocker was checked at the groom and is NOT the blocker)** · prio? **Low** —
  **The load sequence is config-living-in-code and now guarded — it may
  deserve an enforcement-matrix row.** `render_enforcement_matrix.py`'s own docstring calls
  `code_resident` "config living in code, the page's KPI example", and `cli.CANONICAL_LOAD_SEQUENCE`
  (with `LOAD_PROFILES` / `SCHEDULED_INGEST_EXCLUSIONS`) is exactly that — except it now has
  guards, so it would land `enforced` rather than `unguarded`. Blocked on a small design
  question rather than effort: every SURFACES row today has a `file:` under `config/`, so a
  code-resident row needs the registry to accept a module path. (Noticed at N6; deliberately
  NOT done there — the matrix is an O12/admin surface, not N6's scope.)

- **`Idea-54`** · 2026-08-04 · `[bug]` · **groomed → J37 (2026-08-07 pm)** · prio? **Med** —
  **A guard written on one machine had never actually executed on the
  other, and passed by accident when it did.** `test_runbook_currency.py::_cli_verbs` shelled
  out to `drydocs --help` and parsed it. On the laptop that failed twice at once: `text=True`
  decodes with cp1252, which cannot decode the `┐` in Typer's rich box (`0x90`), so `stdout`
  came back `None`; and the rows start with `│`, not `|`, so the pattern would have matched
  nothing anyway — which makes EVERY documented verb look unregistered. Fixed at N6 by
  reading `app.registered_commands` instead of parsing a rendered table. The general question
  worth grooming: how many other guards shell out and parse human-facing output, and is
  "never parse a render when the object is importable" worth writing down as a standard?

- **`Idea-52`** · 2026-08-04 · `[question]` · **groomed → G59 (2026-08-07 pm; the company-side relay was already made)** · prio? **Med** —
  **`apply-supplements` would silently skip the company's two local
  supplements — the exact defect G29 was built to remove.** Producer's chain is the ONE ordered
  list `base -> seal -> catalog -> registry` (+ opt-in sosa) in
  `drydocs_core/schema/supplements.py`. The company additionally runs
  `apply-resource-pools-supplement` (Control-M QUANTITATIVE resource pools, feeds
  `controlm_quantitatives.py`) and `apply-platforms-supplement` (now a documented SUPERSEDED
  no-op, T12) — verified 2026-08-04 that NEITHER verb nor supplement file exists producer-side,
  so they are genuinely company-local, not producer staleness. Consequence: if the company
  adopts `apply-supplements` as its one chain, resource-pools is omitted and whatever MATCHes
  its terms goes quiet — which is precisely how the pre-G29 three-verb block omitted `registry`
  and left `load-software-registry` MATCHing terms nothing had seeded. Relayed as "add your two
  to your own SUPPLEMENTS list before switching". Open producer-side question: should
  `apply-supplements` VERIFY that every supplement file present on disk is in the chain, so a
  local addition cannot be silently skipped? That guard would be portable and would have caught
  this class on either side.

- **`Idea-51`** · 2026-08-04 · `[bug]` · **groomed → N11 (2026-08-07 pm; the divergence half closed with N6 on 2026-08-04)** · prio? **Med** —
  **N6 is now the only thing keeping three load sequences honest, and it is
  ready.** Asked to confirm the load sequence, a check of all three surfaces found them agreeing
  on the shape and disagreeing on membership. `bootstrap-schema-graph` was in BOTH operator
  surfaces (`scripts/ingest.sh` step 3/6, the startup runbook's Appendix B) and missing ONLY from
  `cli.CANONICAL_LOAD_SEQUENCE`, so the generated load-map published 15 steps while both real
  paths ran 16 — FIXED same session (declaration corrected, load-map regenerated at 17). What is
  NOT fixed is why nothing caught it: `test_load_map_declarations.py` checks that every declared
  step is a real command and that every LOADER-backed command is sequenced, but
  `bootstrap-schema-graph` is a schema command, so the completeness check never reaches it — the
  guard is one-directional for non-loader verbs. ingest.sh's own comment already says this block
  and Appendix B "are meant to be the same sequence, not two sequences that drift", which is
  exactly N6's acceptance ("a guard proves they agree"). Remaining divergence for N6 to absorb:
  ingest.sh omits refresh-reference, load-software-registry, load-bmc-docs, load-doc-traceability
  and docs-verify that the runbook and the declaration carry — deliberate for a scheduled
  Control-M ingest, but nothing records that it is deliberate, so it reads identically to drift.

- **`Idea-48`** · 2026-08-02 · `[question]` · **groomed → U17 (2026-08-07 pm)** · prio? **Low** —
  **`DesignDoc.commit` is an author's claim, not a git fact — decide
  whether the writer persona's staleness ranking should use it.** `drydocs-startup-refresh-runbook`
  carries `a135a6d` (2026-07-20, from the doc's own "reflected commit" prose) while the file's
  last touch is `554a4e8` (2026-07-31, Rev 5). Both readings are defensible — "what the author says
  it reflects" vs "when it was edited" — but the plan doesn't say which, so the ranking is undefined.

- **`Idea-43`** · 2026-07-29 · `[question]` · **groomed → D10 (2026-08-07 pm, the gate-prompt DRAFT — the ruling stays the SME's)** · prio? **High** —
  **psgmgr replica vs Control-M XML export: which source wins per
  object when they disagree?** (Guardrail 3 of the XML-fed cmd-line resolution idea → G46/
  G47/G48; the build fills a nullable derived column and decides NO source-of-truth
  question.) Needs a config/precedence.yaml ruling + a named owner-and-sunset for the dual
  definition path (the context-graph dual-ingestion tale's rule of thumb) — e.g. "XML
  export is the definition SoR; the Oracle replica remains the runtime/stats feed", or
  whatever is actually intended. Also touches T16: if XML becomes the standing feed, the
  CM_DEF_VJOB_DETAIL retirement note gains a second path. HITL — user/SME rules this,
  never a groom.

- **`Idea-42`** · 2026-07-28 · `[question]` · **groomed → U16 (2026-08-07 pm, the sizing record — the call stays the user's)** · prio? **Med** —
  **Retire the `depgraph` sibling repo entirely by bringing the SCANNER
  in-house?** The user's reaction to the fork merge was *"I didn't realize it was still used
  after we made it a module"* — and that instinct was half right in a way worth acting on. ADR
  0002-C absorbed depgraph's **lineage** assets into drydocs-core, but the **scanner** never
  moved: `snapshot.ps1` shells out to `../depgraph` every session, which is precisely why a
  months-old sibling checkout could write a 105-edge undercount (→ U7). The whole *class* of
  defect — instrument revision decided by a checkout nobody looks at, capability split across
  branches, `dirty:true` in every meta block — exists only because the tool lives outside this
  repo's history. In-housing it (`drydocs_core/codegraph/`, or a thin vendored package) would
  delete that class outright: one `poetry run` invocation, pinned by `poetry.lock`, versioned
  with the code it measures, no probe needed because the tool and the caller ship together.
  Against: depgraph is deliberately stdlib-only and general-purpose (it scans any project, not
  just this one), it has its own Control-M/RUA/html-review surfaces DryDocs does not use, and
  0002-C consciously chose absorb-the-assets-not-the-tool. So this is a real trade, not a
  cleanup — size it before committing. Precondition now satisfied either way: the fork is
  consolidated (depgraph `5006567`, one branch), so there is a single revision to vendor from.
  KEPT-UPDATED 2026-08-02 (weekly groom) — still the user's call, but the argument moved: **U9
  added a THIRD producer-side post-processing step wrapped around the sibling tool** (git-ignore
  filtering, after U7's capability probe and U8's abs_path strip). None of the three could live
  in depgraph, because each encodes something about THIS repo rather than about scanning — which
  is a point for the fork ("the general instrument stays general") and against it at the same
  time ("the wrapper is now bigger than the seam it wraps"). Worth deciding before a fourth step
  appears. What has NOT changed: no scan capability was missing this time — `main` already
  reported `tree: true`, so the sibling checkout was not the constraint.
- **`Idea-40`** · 2026-07-28 · `[chore]` · **groomed → O55 (2026-08-07 pm; migrate OR record a waiver, both allowed)** · prio? **Med** —
  **react-router high advisory (GHSA-qwww-vcr4-c8h2, RSC-mode CSRF) cannot
  clear without the v7→v8 major migration** — v8 absorbs `react-router-dom` (its latest is
  still 7.18.1, inside the vulnerable 7.12.0–8.2.0 range), so `npm audit fix` is a no-op and
  the fix means rewriting the router imports against `react-router@8.3.0`. Escalated from O34
  per its stop clause (postcss/nanoid patches applied there); a UI-workstream decision, and
  likely moot in practice — the console is a Vite SPA, no RSC actions — but the audit stays
  red until ruled. Pairs with the code-splitting design call O34 also parked.

- **`Idea-26`** · 2026-07-22 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-18 and Idea-24)** · prio? **Low** —
  **Company adoption: route the XML run's WARN flood through the new
  loader run logs (next port).** Producer BUILT the generalized run-log family same day
  (user directive after the first company XML run flooded the console with per-row
  `description_tokens` WARNINGs): `drydocs_core/run_log.py` + `BaseLoader` wiring —
  configurable path (`DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` fallback → `~/logs/DryDocs`),
  shared naming (`load.<loader>.<stamp>.log`), header/meta from the process, WARN-stream
  tee + uncapped reject detail, summary footer, best-effort contract. When ported,
  company-side should ALSO (a) attach the tee in the XML *extractor* stage (the
  description_tokens flood happens pre-loader, in the adapter), and (b) consider raising
  the console handler to WARNING-summary-only once the stream lands in the file — the
  file is the review surface, the console shows counts.

- **`Idea-24`** · 2026-07-21 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-18 and Idea-26)** · prio? **Low** —
  **Next cross-repo port: carry the AIS acronym expansion across
  files.** Producer's authoritative home is `software-registry.yaml#acronyms`; the company's
  PROVISIONAL gloss sits on their `source-registry.yaml` docs-source entry with a
  PORT-MANIFEST canonical-producer row expecting the producer expansion at next cherrypick —
  different files, so the port must transplant the value, not same-file overwrite. Also
  still open company-side: no 06-29 gate-log entry (their audit gap; backfill offered).

- **`Idea-21`** · 2026-07-21 · `[idea]` · **groomed → G61 (2026-08-07 pm, the provenance gate DRAFT)** · prio? **Med** —
  **FW-really-API confirmed live** — the greenfield-provenance use case
  for the fix module: a file-watcher-shaped job's `.tok` is produced by an UPSTREAM API-call
  job writing the file locally, no external push exists — the name/type lies. Already
  codified as the `_FW`-really-API anti-pattern + design principle 8 (intent from resolved
  flow, flag name-token disagreement) in
  `internal/remediation/governance/nfr-consistency-and-greenfield.md`; the description-field
  metadata plan is the declared-provenance carrier. Two NEW provenance gap classes from the
  live case: (a) payload script deployed on the exec host but ABSENT from SCM (code search
  finds only the XML variable reference) → *artifact-not-in-SCM* flag on :Script; (b)
  pipeline-id-keyed code discovery has NO key for non-DPL python jobs → PATH-keyed Script
  identity is the fallback, and the GUID-vs-path boundary is the kind discriminator.
- **`Idea-19`** · 2026-07-21 · `[idea]` · **groomed → J39 (2026-08-07 pm)** · prio? **Med** —
  **Back-flow the company's un-back-flowed advances (bd7952f follow-up 3).**
  The 2026-07-20 bundle port went bidirectional (+288 producer / +148 company) precisely
  because these never came back; reproduce mechanism-only via the screenshot/describe
  channel: snow-support schema supplements (`hpsm_queue_key`/`sn_group_name` constraint
  pair + a `snow-snowflake-itsm` source stub), the `drydocs_remediation` DPL-watch-drift
  rule + tests (pairs with the DPL runtime-trace inbox entry below), the `graph_verify`
  Assertion refactor, the docgen deviations vs the finalized company TDD, the
  `CONFLUENCE_BASE_URL` config seam (mechanism: base-URL as config; the value stays
  company-side), and the `controlm_folders.sql` `J` table alias. Ties into the
  drydocs-review back-flow epic. Until these land, every future port repeats the
  squash-reconcile instead of a clean linear apply.

- **`Idea-18`** · 2026-07-21 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-24 and Idea-26; every relay is RE-VERIFIED before it is written down)** · prio? **Low** —
  **Company-side heads-ups from the port-report gap review** (their
  tracker — recorded here so they aren't lost; relay next company session): (a) the
  `test_schema_graph.py` drift-guard sequencing conflict — see the new reconcile-port
  skill ledger note (re-add only after their doc-vocab gate); (b) confirm
  `docs/restructure/internal-backlog.yaml` was deleted after the DD-series merge
  (bd7952f follow-up 2 — 388a30d shows the merge happened, not the deletion); (c) the
  company is producer commits behind past `7e8df54` (L7 gate sign-off + live loader,
  G14 lineage file-ops pass, the hermetic oracle-kerberos test fix that retires the
  standing known-failure note, DPL inbox, port-gap fixes) — **and their tooling can't
  see it**: the 07-21 company-side "identify unported commits" search concluded "fully
  ported, nothing outstanding" from a FROZEN `cewilson/main` ref (`git fetch cewilson`
  404s company-side; likely the stale pre-rename remote URL — the live repo is
  `https://github.com/ce-wilson/DryDocs.git`, pushed 07-21). First company action:
  `git remote set-url` + re-auth, re-fetch, then re-run their own re-verify
  (`git log <last-ported>..cewilson/main`). Silver lining from that search: the L7
  port branch IS merged to company main (`373e993`→`c8cf9f0`), closing the
  "NOT merged" state in 5eba0c3, and the historical port reports (0eb1a8d, aa049d3,
  e6f8cca, e418258, eeaffa2, f7970e5) all exist as files company-side.

- **`Idea-8`** · 2026-07-12 · `[doc]` · **groomed → L26 (2026-08-07 pm; the Epic L outline half deliberately excluded)** · prio? **Low** —
  **/documentation skill has NO white-paper guideline** (types: README, API,
  runbook, architecture, onboarding). Wrote docs/whitepaper/drydocs-whitepaper.md deriving
  structure from the architecture-doc type + white-paper conventions; if white papers recur,
  add a "White paper" type to the skill (exec summary → problem → approach → architecture →
  governance → roadmap) and consider an Epic L outline for it (whitepaper.outline.yaml).

- **`Idea-1`** · 2026-07-03 · `[chore]` · **groomed → R14 (2026-08-07 pm)** · prio? **Low** —
  `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.

- **GROOMED TOGETHER 2026-08-07** (user instruction): `Idea-80` + `Idea-82` produced **G58** (the dead-script archival report — three dispositions, a stated coverage precondition, the already-archived count) and **L24** (state the target state as a goal in the executive overview). One report item rather than two because both entries turn on the SAME argument: an absence observed by one feed is not an absence in the world. The one fragment NOT made an item — what to CALL the estate-level end state — rides G58's notes as a question the build surfaces, because nothing needs a formal term yet.

- **`Idea-82`** · 2026-08-07 · `[idea]` · **groomed → G58 + L24 (2026-08-07, same day as capture)** · prio? **Med** —
  **Name the estate-level TARGET STATE: "the production server holds only actively
  used code" — and carry it into the executive overview as a stated goal.** User
  direction, 2026-08-07, in the question that closed the G22 sign-off session.
  **THE GAP:** DryDocs can already name every ARTIFACT-level state involved, but has
  no name for the ESTATE-level condition they add up to. Artifact side is covered:
  a tombstone (`removed_from_source_at`, the D7 sweep ruled at U13) is the existing
  word for *was here, isn't now, history kept*, and after G22 §D2 the `:Script` case
  needs no new flag at all — it falls out of the occurrence shape (code-repo
  occurrence + no current server-extract occurrence = archived; server occurrence +
  no repo occurrence = G24's existing `never_committed` bucket). That keeps
  "archived" DERIVED FROM EVIDENCE rather than declared, the same move §G1 made when
  it put identity in the business key and made the URN a render. What has no name is
  the goal: an estate where the two sets have converged.
  **WHY IT IS NOT A LABEL CHOICE:** the state is a property of the ESTATE, not of any
  node, so it is a real vocabulary decision and rides the HITL gate rather than being
  picked at a groom. Do NOT reach for the `00-header.yaml` lifecycle
  (`planned|active|deprecated|removed`) — that enum governs relationship-vocabulary
  ENTRIES (edge meanings, i.e. schema), and a script on a server is an INSTANCE.
  Reusing the four words for both would put `removed` = "we deleted an edge
  definition" and `removed` = "we deleted a file off a server" in one repo: the exact
  two-things-one-spelling collision §A2 caught on `group` and J32 made a standing rule.
  **THE PRECONDITION THAT MUST RIDE ANY WORK HERE (§H1):** absence of a server
  occurrence is NOT proof of removal. All three usage axes are positive-only, and
  present-on-server is bounded by `scan_roots`, so "not in the bundle" only ever means
  "not observed by that feed". A tombstone must therefore be set from a SWEEP-SCOPED
  absence — within roots actually scanned, on a bundle that actually parsed — or a
  collector that skipped a mount tombstones live code. Since §E3's use case is
  DELETION, that false positive deletes something running. §E3's three dispositions
  stay distinct for the same reason: genuinely dead (archive and remove), misdeployed
  (relocate, never delete), unreferenced-but-dynamically-called (keep).
  **THE SECOND HALF OF THE ASK — the executive overview.** The user asked for this to
  appear in `docs/overview/drydocs-executive-overview.html` as a stated **target-state
  goal**, not only as a backlog item. Two things a groomer needs to know before
  touching it: (1) that file is **hand-authored HTML and its own SINGLE SOURCE** —
  there is NO `.md` twin (unlike `docs/whitepaper/`), it is not renderer output, and
  `render_design_doc.py` does not cover `docs/overview/`, so it is edited directly;
  (2) it is a **non-governed outward-facing doc** (CLAUDE.md §6), so editorial and
  design treatment DO apply there — the publish-VERBATIM rule binds the design
  renders, gate pages and the board, not this file. Nearest existing homes are "The
  loop that makes it a system, not an inventory" (the operational-outcome section) and
  "Honest about the gaps"; there is no target-state section today.
  **RELATED:** §E3 (the archival/removal use case and its three dispositions), G23
  (curated rua load), Idea-80 (dead-script report coverage precondition — same
  coverage argument, and these two should probably groom together).

- **`Idea-80`** · 2026-08-06 · `[idea]` · **groomed → G58 (2026-08-07, once G22 signed as its own status line required)** · prio? **High** —
  **The dead-script report drives DELETION, so it needs a coverage precondition and
  three dispositions, not two.** G22 §E3 named the use case: identifying unused,
  deprecated code for archival and removal. That raises the bar on the report the
  usage axis feeds. (a) **Body-copy coverage is a precondition, not a footnote** —
  script-to-script invocation is visible only where the bundle carried the script
  BODY, and the metadata-only listings ship none, so on those bundles
  "unreferenced" means "no CMD_LINE reference", never "nothing calls it"; a report
  that omits its coverage will propose deleting leaf scripts it was structurally
  unable to see callers for. (b) **Three dispositions** — genuinely dead (remove),
  MISDEPLOYED (relocate; §E1's caveat that a script may have been deployed to the
  wrong server), and unreferenced-but-dynamically-called (keep). (c) The
  misdeployment case is only valid where `storage_scope` is local — under shared
  storage every host sees one file. *(From the G22 §E session, laptop.)*

- **`Idea-78`** · 2026-08-06 · `[feature]` · **groomed → O45–O51 (2026-08-06, same day as capture)** · prio? **High** —
  **SME Context-Intake page: the front door for the unstructured email corpus
  (the Q10 "SME assignment surface"), planned end-to-end.** User direction
  in-session; full plan at `UI-WIP/sme-intake-page-plan.md`. Seven sections top
  to bottom: PAT + SEAL area cascade (hint channel, "unknown" first-class) →
  context-type dropdown from a NEW `config/taxonomy/context-types.yaml`
  (job-failure, missed-data-load, missed-file, data-issue — growing, taxonomy
  layer so growth is not a gate) → drag-drop upload for .msg + Copilot .json
  pairs (.txt TBD; data-root staging, Internal stamp, sha256, never the repo) →
  CDO-style "review for ontology" pass (proposed bindings, SME confirms) →
  read-only related-nodes QuerySpec over the structured graph → ADK agent
  first-pass correlation (accept / modify / stay-unassigned) → confirm into the
  O24 origin-flagged store (`origin: sme-intake`) and an ADMIN review queue.
  Nothing writes the graph: corpus load waits on Q10←G31←G32, the assignment
  edge is gate-registered `planned` per Q10's own acceptance; admin-accepted
  records park on a "waiting on gate" chip. Seven proposed build slices
  (O45–O51 indicative) + open questions are in the plan. *(Grooming: the
  console slices join Epic O; Q10 keeps the corpus/load half.)* AMENDED
  same day (user): §8 **reviewer-quality signal + admin block** — per-SME
  auto-accept rate / too-fast rate / admin-return rate over a rolling window,
  limits in `config/review-quality.yaml`; crossing a limit FLAGS the SME on
  the admin queue's quality rail, and the admin (never the machine) can block
  the persona from submitting — reversible, recorded who/when/why. The user
  recalled a backlog item ranking auto-acceptance to flag poor-quality work;
  searched 2026-08-06 — no such item exists in backlog/IDEAS/gates/history
  (possibly company-side drydocs-review), so this entry is now that
  requirement's home.

- 2026-08-05 (desktop, user directive: number the inbox, add status + priority, and
  "extend or supplement existing backlog items with the ideas… I don't want every idea
  moved, but they do need to be reviewed again") — **all 69 inbox entries reviewed and
  headered.** Ids assigned in CAPTURE order (`Idea-1` oldest, `Idea-69` newest), so a new
  capture at the top never renumbers anything below it. Three entries SPLIT because their
  halves had different dispositions, which is the only reason to split: `Idea-63a` (the
  cardinality question — answered, closed) vs `63b` (the `descr` review queue — unbuilt,
  merged into K18); `Idea-30a` (design the PDN trigger) vs `30b` (audit the deadline of the
  BIM job that already exists).
  **Outcome of the review — the point of it was NOT to promote everything.** 3 promoted
  (**K18** derive the tier from the folder name + give the store a platform-declaration row
  kind; **K19** app-code mapping as an as-of assertion, reuse detection; **J32** write down
  the registration/routing/attribution rule). 5 MERGED into items that already exist, which
  is the disposition this pass was really for — **J13** absorbed the platform-vocabulary
  ruling (`Idea-38`: it is the same user-gated decision J13 already waits on, now with four
  value classes named), **C25** absorbed the two missing software-registry product rows
  (`Idea-65`) as a prerequisite, **G34** absorbed the acronym-catalog CONTENT shape
  (`Idea-35`) into its scaffold, and `Idea-68`/`Idea-63b` ride K18 as clauses. The rest
  carry a status and a proposed priority and STAY here: 22 `parked` with a named trigger,
  28 `open`, 3 `closed`. (71 headers over 69 ids — the two splits account for the difference.)
  Every priority carries a trailing `*` — proposed by the agent, not confirmed by the user.
  Clearing the star is the review pass this file now supports and could not before.

- 2026-08-05 (desktop, user directive "groom them into backlog items") — the two HITL gates
  drafted the same day → **C25** (run the `software-version-context` gate — epic
  ontology-mapping, phase 2, beside its C12/C14 USES_SOFTWARE siblings) and **K17** (run the
  `fid-identity-and-scope` gate — epic seal-attribution, phase 9, the K2 tier-2 unblock),
  plus **K16** (the doc-09 Phase-0 FID census). K17 depends on K16 BY DESIGN: the census
  produces the §Q0 disagreement breakdown the gate cannot sign without, so grooming the gate
  alone would have scheduled a session that cannot reach a ruling. Both gates were already
  documented as artifacts — committed prompts, `status: open` rows in `gates.json`, format
  guard passing — but had NO backlog item, so `unblocks: []` and nothing would ever pull
  them. That gap is what this groom closes. The IDEAS entries themselves STAY in the inbox
  (they carry findings wider than the gates: the app-code cardinality question, the
  registration/routing/attribution rule, the sub-application USES_SOFTWARE source, the
  tier-naming split) — only the gate-session work was promoted.
- 2026-08-04 (desktop, user directive) — [idea] the backlog-sharding EPIC entry (2026-08-03;
  kept-parked at the same day's weekly groom) → **UN-PARKED and groomed as Epic Y: Y1 the
  sharding ADR ruling session, Y2 the shard build, Y3 the :BacklogItem/DEPENDS_ON vocabulary
  via the gate, Y4 the query surface.** Phase 1's guard had already shipped (`c5b689e`, port
  step 55) and stays outside the epic. The park condition travels with Y2 as a prose
  precondition (in-flight port PORT-REPORT review first). Fresh exhibit recorded at the groom:
  the three same-afternoon roll-up rebase conflicts of 2026-08-04 (X1-claim/V8, X2-close/V2,
  X3-close/V3), all in the stored summary/next_ready block Y2 derives away.

- 2026-08-04 (session close, laptop) — [question] "nothing compares the checkout against
  `expected_commit`" → **RULED AND BUILT SAME SESSION (user: "warn in snapshot.ps1"), no
  backlog id.** `snapshot.ps1` now reads the pin, compares against the revision it records
  (`$depFull`, not a fresh HEAD), and warns with a drift classification that says what to do:
  *ahead* → the pin is the stale side, bump it; *behind* → this scan is stale and not
  comparable, `pull --ff-only`; *diverged* → the fork shape behind the 105-edge undercount,
  resolve first; *unknown* → the pinned commit is absent, fetch. An explicit "currency
  UNCHECKED" warning fires when the pin cannot be read, so a silent no-op is never mistaken
  for a clean check. WARN and not refuse was the ruled point: a sibling ahead of the pin is
  how a bump starts, so refusing would block the fix. All six paths exercised by executing
  the block extracted from the real file against synthetic states.
  Two defects found while building it, both worth remembering. (1) The classifier first
  compared against a fresh `HEAD` rather than the captured `$depFull` — identical in a normal
  run, so only the test matrix caught it, and it misreported *behind* as *ahead*, the one
  direction that matters. (2) The advice strings were first written with em dashes and BROKE
  THE SCRIPT: the file is UTF-8 without a BOM, PS 5.1 therefore decodes it as CP1252, and a
  UTF-8 em dash arrives ending in a smart quote that PowerShell honours as a string
  delimiter — the string closed early and the whole file failed to parse (confirmed with
  `Parser::ParseFile` on the real file). Em dashes in comments and here-strings are harmless
  and stay. A repo-wide guard now reds on non-ASCII inside a single-line quoted string in any
  BOM-less `.ps1`, proven red on a probe before being kept. Note J29's encoding standard
  covers `.cypher`/`.sql`/`.csv` and deliberately not `.ps1`, so this is a neighbouring rule,
  not a J29 gap. Also removed: the capability refusal's hardcoded `depgraph 5006567`, stale
  since the morning's bump — it quotes the configured pin now.

- 2026-08-04 (session close, laptop) — [bug]×2 the instrument-drift pair → **BOTH RESOLVED
  SAME SESSION on user direction ("pull the depgraph sibling and bump the pin"), no backlog
  id.** (a) Sibling fast-forwarded 5006567 → 773fb1e (clean descendant: `9c663ca` RUA
  inventory ingestion + script-op analyzer, then the merge), `expected_commit` bumped, probe
  re-run the way `snapshot.ps1` runs it (PYTHONPATH=. inside the sibling — a bare run from
  the DryDocs venv reports everything false and is NOT a valid probe) → importable,
  multi_root, tree all true. (b) The dead-SHA snapshot header is gone: the re-run replaced
  `drydocs-20260804.json` (which cited the rewritten-away `63adc2b`) with
  `drydocs-20260804-1548.json` at the live `299af39`.
  **One claim in the original entry was WRONG and the correction is worth keeping:** it said
  scanning from the stale revision "would emit a snapshot missing three relationship types".
  Measured after the bump, that is false for this repo — DryDocs scans emit exactly ONE
  relationship type, CONTAINS (1772), with TRANSFERS and RUNS_ON at zero in both the old and
  new snapshots and an identical 526 edges. Those types come from depgraph's Control-M / RUA
  lineage extractors, which a Python-tree scan never exercises. The bump was still right —
  two machines on different instruments cannot be compared, and the pin named a revision main
  had moved past — but the justification was comparability and currency, not lost output. The
  inferred consequence had been stated as fact without measuring it. Lesson recorded in the
  config comment: treat a REL_TYPES change as a reason to re-measure, not as proof of an
  undercount. Residual (the missing DETECTION) re-inboxed as a [question].

- 2026-08-04 (weekly groom, laptop) — [bug] `provision.ps1` shells out to host-PATH
  `cypher-shell` → **G54**. Verified at the groom: the REQUIRES block (`:6`) presents host
  cypher-shell as satisfied by "bundled in the Neo4j Docker image", but the runner (`:57`)
  invokes the bare binary, which a Docker-only host does not have. Acceptance forces one of
  two resolutions (exec-aware script preferred over a header-only fix) and carries the J29
  PS 5.1 trap into the header, since the workaround shape and the encoding standard are one
  lesson. The BOM half of the report was already resolved by J29 and is recorded as wrong.
- 2026-08-04 (weekly groom, laptop) — [bug] the two catalog loaders C22's file set excluded
  → **C24**. Verified statically: `catalog_lobs.cypher:28-29` blanks TODAY (CatalogLOBRow's
  code/name are already Optional), while `dev_teams.cypher:16` is the latent whole-row-reject
  case (DevTeamRow.name is required) — so they fail differently and C22's row-model half has
  to move with the Cypher half. Depends on C22 (done), so it enters next_ready.
- 2026-08-04 (weekly groom, laptop) — [chore] branch `wip/k9-laptop` → **J30 + J31**, split
  deliberately. J30 is the one-off disposition (per-file comparison, lift what is worth
  keeping, then delete local and remote with the tip SHA in the close note); J31 is the rule
  the collision exposed — the pull rule makes the CLAIM visible but not the WORK, so a
  session that dies looks identical to one that never started. J31 extends J19's pushed-claim
  discipline rather than proposing a new direction, which is why it is a chore and not a gate
  item; its wording is confirmed with the user at build. Second occurrence of the C19 class,
  and the two failed differently — C19 was two unclaimed sessions, K9 was a pushed claim that
  went dark while the work existed locally.
- 2026-08-04 (weekly groom, laptop) — [chore] `reference/REGISTRY.yaml`'s dcat `docs:` path
  resolves to nothing → **A4**. Verified: no `reference/standards/dcat/` directory exists.
  Two allowed resolutions (write the dcmi-terms-pattern stub, or re-point at the standards
  README like skos), the choice recorded in the close note; rides A1's registry-path audit if
  that is picked up first.
- 2026-08-04 (weekly groom, laptop) — [idea] the `controlm-runbook-automation-SDLC` skill →
  **L23**. Promoted rather than parked because it is not a speculative shape: the shipped
  `-excel` skill's own frontmatter already names "a future -SDLC sibling", and the doc type,
  worked example and outline tests all landed at `995eb9a`. Acceptance keys on the validation
  that already exists (a generated doc validates against the outline unedited) and forbids
  re-writing queries the `-excel` skill owns — two skills disagreeing about the same runbook
  fact is the failure it exists to prevent. Filed under Epic L: the outline system lives
  there, and this is a doc GENERATOR, distinct from drydocs-docmeta which ingests.
- 2026-08-04 (weekly groom, laptop) — [doc] `sdlc-neo4j-schema.md`'s stale HAS_APPLICATION
  loader-inventory row → **MERGED into L19** as clause (e), no new item. The line's own
  instruction was "fix it in the stream that owns that doc, not piecemeal", and L19 is
  already the doc-drift sweep over `docs/reviews/sdlc-*.md`. Verified both halves: `:553`
  still carries the claim, `pat_product_mapping.cypher:39` says C9 removed the write in
  2026-07-18. Restated to the K13 support reading so the correction lands once.
- 2026-08-04 (weekly groom, laptop) — two entries KEPT PARKED with triggers re-checked and
  NOT fired: the **controlm-pipeline-stub** twins (capture files present, but no internal
  build has landed, and epic placement is explicitly a user call at that groom) and the
  **desktop venue divergence** (a user ruling either way; the laptop was verified on the
  pinned 2026.05.0 with `ddschema` present, so the drift is desktop-only — and the groom
  noted that nothing currently detects a running server's version against the pinned one).

- 2026-08-04 (Control-M groom) — [chore] the legacy /mappings job-application pane (coverage
  grid + assign flow still on the retired job-grain edge, found at K11) → **K15** (type bug —
  the surface actively misreports; retire-or-re-bind, direction confirmed with the user at
  build).
- 2026-08-04 (Control-M groom) — [idea] the 2026-07-14 ctlm_id ripple → **CONSUMED**: (1) the
  which-other-CM_-views census is internal-side (docs/next-internal-session.md item 4, needs
  Oracle — K14's notes keep it separate on purpose); (2) the K2 manual-CSV `ctlm_id=` shorthand
  is moot — K9 rekeyed the template to app_code; (3) company-side alignment rides port step 62
  (the composite-key-serialization standard, ctlm_id dot form ruled 2026-08-03).
- 2026-08-04 (weekly groom) — [bug] review-plan seed queries missing the D7 tombstone filter
  → **U13** (the A3 dead-`__init__.py` ranking is the proof case; fix the query pack, not the
  sweep).
- 2026-08-04 (weekly groom) — [bug] 63 vendored `.claude/skills` scripts polluting the
  architect-persona metrics → **U14**. Fix placed in the QUERIES (region allow-list), not the
  scan — the U9 whole-tree shape is the ruled intent; the metrics mis-scope it.
- 2026-08-04 (weekly groom) — [chore] the G51-tail retrospective close → **MERGED into J26** as
  the second family instance (promise-vs-assertion: `test_databases_match_provisioning_script`
  docstring promised equality, asserted subset; made bidirectional at `aa0a0eb` and failed on
  `['ddschema']` before the config fix). Both company consequences were ALREADY ledgered before
  this groom: port-prompt step 59 carries the schema_meta caution verbatim, and the standing
  divergences carry the Rev 5 rev-pin note — no tracker row owed.
- 2026-08-04 (weekly groom) — [question] composite-key grammar → **RESOLVED + BUILT 2026-08-03**
  (two SME rulings: ctlm_id dot composite is THE value form; key-cell pairs join with `:` not
  `;`). Standard = `knowledge/standards/technology/composite-key-serialization.md`; `_parse_key`
  flipped in the free migration window; the value-form sweep is **K14**; port step 62 carries
  the company T4 caution.
- 2026-08-04 (weekly groom) — [idea] the 2026-07-27 SME orchestrator-mapping act → **RESOLVED by
  the K7 sign-off (24/24, 2026-08-03)**: §G ruled all seven confirmations; the cascade screen is
  **K11**, the `catalog_has_application` back-flow (§G6's company SUPPORT reading) is **K13**,
  the C14 prefill demotion is §G2, and the folder-availability question is answered in K11's
  acceptance (unmapped-only, naming-pattern optional). The `:Batch` bridge RETIRED at the gate.
- 2026-08-04 (weekly groom) — [idea] the 2026-07-22 defined-mapping mega-entry (grain correction,
  two-tier app-code model, K2 demotion, property-diet rider) → **RESOLVED by the K7 sign-off +
  the K9 build**: folder grain (§A), tiers seal-born/platform/dual-coded (§B2), origin flags
  (§B3), store = source of record (§E2); the loader half is **K8**, the taxonomy capture **K12**.
  Residue re-inboxed slim: the tier-2 platform-code enumeration (SME data entry, no item).
- 2026-08-04 (weekly groom) — [idea] the 2026-07-21 two-pattern code→app model → **RESOLVED by
  the K7 sign-off**: the "GATE DECISION core" it parked (authoritative code→app edge +
  platform-code marker) IS the ruled `BELONGS_TO_APPLICATION` folder-grain edge authored per
  app code with the tier column as the marker. The read-only explorer spec stands unchanged.
- 2026-08-04 (weekly groom) — [idea] the backlog-sharding EPIC proposal → **KEPT PARKED by user
  ruling at this groom** (phases 2–3 are a cross-repo plan change; re-time after the in-flight
  port's PORT-REPORT lands). Entry stays in the inbox with the ruling annotated.

- 2026-08-03 — [feedback] U.S. business-English instruction set (user, in-chat, after "spine"
  in the exec overview failed with its own audience) → guide committed as
  `docs/style/us-business-english.md` + **L22** (wire it in, rewrite the overview, inventory
  idioms, mechanism-name fence).

- 2026-08-03 — [question] "what's upstream of :Metric?" (user, in-chat, minutes after the
  manual graph wipe — the DQV seed's IN_DIMENSION query was the one thing worth asking about
  what was just deleted) → **C23**: the quality seed floats — no measurement writer, no
  vocabulary entries; rule build/defer/prune via the gate.

- 2026-08-02 (weekly groom) — [source→Q6] the company-side fetcher shape → **MERGED into Q6's
  acceptance**, not a new item: acquisition-only connectors over a `Connector` protocol, `web`
  with an INJECTABLE TRANSPORT and an SSRF scheme allow-list, `filedrop` over pathlib. Both
  guarantees written in as non-negotiable — the transport injection is what makes Q6's Track-1
  offline tests real, and the allow-list is the guardrail Q12 exists to enforce. Unblocks Q6, R7
  (released unbuilt 2026-08-01 for exactly this missing fetcher) and Q12 behind it. The line's
  own caution was honoured: the realm is described, never named.
- 2026-08-02 (weekly groom) — [chore→L19] two governed design docs falsified by the S3 identity
  cutover → **MERGED into L19 as acceptance clause (d)** (web-console-tdd's "columns verbatim",
  controlm-ingestion-tdd's `Application.seal_id` stale on both halves), with the
  deliberately-untouched mapping-store COLUMNS named so a later sweep does not "fix" them.
- 2026-08-02 (weekly groom) — [chore] guards that read committed text with a bare substring match
  → **J26**. The instance (test_constraint_count counting `CREATE CONSTRAINT` inside a comment)
  was already fixed in S3; the item owns the CLASS, and the groom found a live second member —
  see G51.
- 2026-08-02 (weekly groom) — [chore] `.gitignore` names the real org and internal domain in two
  comments → **J27**. Promoted rather than parked as a decision: CLAUDE.md §3 already bans real
  org names outside `internal/`, so the default branch is REWORD and the item applies an existing
  rule; the "record the exception in PUBLISH-BOUNDARY.md" branch stays available because the
  boundary is the user's to set.
- 2026-08-02 (weekly groom) — [bug] silent parent joins in the catalog loaders + the [source]
  line's unconditional `SET name = row.name` → **C22**, two lines into one sweep because they
  land on the same files (the L19 precedent). Verified at the groom: the blanking SET is in
  `products.cypher` as well, so C22 covers three loaders, not the two the inbox named. The
  [source] line's three back-flow candidates stay parked on the company gate's sign-off.
- 2026-08-02 (weekly groom) — [question] "How much depgraph audit history do we keep?" (review
  finding F11, open since 2026-07-25) → **RESOLVED by the SME and already executed; no item.**
  Direction 2026-08-02: "the old dep snapshots can be removed this was the intent", retention =
  newest all-files snapshot only. Applied at `e3f65af`: 105 files removed (101 dated, 2
  `drydocs1-*`, 2 tree one-offs), one kept, all recoverable from history. Nothing in code
  referenced a snapshot by name (checked before deleting). Two halves of the question stay open
  as **U12**: the README still documents a prune-to-ten rule and cites two of the deleted files,
  and `snapshot.ps1` still writes `<project>-<date>-<HHmm>.json` when a snapshot already exists
  for today — so the ruling holds only until the next double-run. A rule enforced by whoever
  remembers it is the shape U9 just deleted.
- 2026-08-02 (weekly groom) — **raised AT the groom, not from the inbox** (the skill's optional
  graph/code cross-check, run as a code cross-check): three follow-ons from the self-doc session
  plus one defect it left behind. **U9** + **C21** groomed RETROSPECTIVELY as done — that work
  landed at `e3f65af` before any item existed, and three committed files already cite "U9" as an
  id nothing defined. **U10** = the code-graph package-layer GATE SESSION (drafted 2026-08-02,
  unsigned; its own §I is what opens the build item, so none was groomed ahead of it). **U11** =
  draft the second gate prompt, the `.py → .cypher → :Label` chain the parent gate deferred at
  §H5 — possible only now, because .cypher files became graph nodes for the first time at U9.
  **G51** = the defect: `drydocs bootstrap-schema-graph` targets a database that
  `01_databases.cypher` does not create, so it works only on the machine where it was made by
  hand — and `test_database_names.py`, the guard written for exactly this drift, missed it
  because it keys on the identifier `DATABASE` and the constant is called
  `SCHEMA_GRAPH_DATABASE`. Same family as J26.

- 2026-07-31 (pm, weekly groom — run AFTER the N7 gate + N9 build closed the registry-v2
  work) — [chore] T11 L7-ratification paste-ready snippet still owed producer-side →
  **J25**. Verified genuinely owed before promoting: `docs/port-prompt.md` §6 states the
  four elements a Tier-A ratification entry must carry and records that the snippet was
  "provided in the producer session 2026-07-21", but a repo-wide search for `0252d29` /
  `PORT-REPORT-6fd3270` finds prose references only — the block itself was never
  committed, so the company gate pack cites an artifact no company session can open, and
  tracker T11 has read `pending` since. J25 is producer-side AUTHORING only; the entry
  lands in the company gate-log at their next port and their sign-off stays theirs.
- 2026-07-31 (pm, weekly groom) — [doc] Runbook Rev 3 candidate: mention
  `drydocs load-doc-traceability` in the Refresh/ingest step → **MERGED into L21**
  (Runbook Rev 4) as an acceptance clause. The line parked itself explicitly to "ride the
  next feedback loop rather than bump a fresh Rev for one line", and L21 IS that revision
  — so it became a clause, not an item.
- 2026-07-31 (pm, weekly groom) — [new, raised AT the groom] **J23's own residual: the
  retired `Internal-Confidential` tier survives in FORWARD-LOOKING specs** → **J24**.
  J23 collapsed the vocabulary to three levels the same morning and correctly scoped
  itself to config + the boundary docs + the two tests, leaving history alone. The sweep
  found the token still live in surfaces that are neither config nor history but
  *instructions for assigning a tier*: `UI-WIP/site-plan.md`'s classification union type
  (a TypeScript enum in waiting) and its banner rule, `wf-admin-config-01.md`, two skill
  reference tables that ROUTE material by tier (`data-context-extractor/references/
  platforms.md`, `controlm-runbook-automation/references/fix-package.md`), and the
  `bmc-docs-example.yaml` gate-prompt template. Left as history and named so in J24:
  `config/gate-log.md`, signed-off gate prompts, `done` backlog close-notes,
  `SDLC-Docs/extracted/`, this audit trail. J24 also adds a regression guard to
  `test_classification.py` scoped by an explicit file list, so history can never be swept
  in by accident.
- 2026-07-31 (pm, weekly groom) — [database fix, no item] **M3's acceptance still failed
  its own vocabulary**: it required column mappings "authored in the internal twin —
  Internal-Confidential never lands producer-side", naming a tier retired hours earlier.
  Fixed inline at the groom (now: "Internal, and confidential-handling, so never
  producer-side") rather than deferred into J24 — a `todo` item whose pass/fail test
  cites a dead enum value is exactly what grooming exists to prevent. Deliberately kept
  OUT of J24's scope so each surface has one owner.

- 2026-07-31 — [chore] classification collapse to 3 levels (registry-plan Phase 1; user
  ruling same day, pre-decided) → **J23** (may land ahead of the N7 gate — removes
  machinery, adds none).
- 2026-07-31 — [idea] registry-plan directive captured → **MERGED into N7** same day
  (`2d6f705`: inputs + notes point at `internal/registry-redesign/REGISTRY-PLAN.md`;
  samples re-homed, J22 guard failure cleared). No new item.
- 2026-07-31 — [idea] CDO ontology crosswalk Phases 1–3 → new **Epic W**
  (cdo-alignment, phase 2): **W1** crosswalk + gate spec (mechanism-only rows,
  capture-hole rows blocked-on-recapture), **W2** planned property/enum registration
  (Run props + event enum, SKOS attrs on enum gates incl. G27, ColumnShape names),
  **W3** ontology-builder as optional add-source-object aid. Skip list binding; the
  companion [source] live-scrape line stays parked (company-side connector).
- 2026-07-30 — [idea] Source-registry id-field redesign (user directive: flat id conflates
  source SYSTEM with extracted DATASET) + the 2026-07-29 per-side loader→source overlay
  candidate (which had reserved the id) → **N7**, ONE fable/HITL-gated design session
  bundling two-level identity, the overlay, the URN handle, and the reconcile
  same-id/changed-meaning guard; feeds the company T19 gate review. Nothing decided at
  groom — everything routes through the gate.
- 2026-07-30 — [chore] 4 taxonomy-ontology-map entries citing unregistered source ids
  (N4 render day-one finding) → **N8** (per-entry ruling: register / re-point / exempt;
  outlook-dl expected exemption per the DL gate's store-as-source design).
- 2026-07-30 — [bug] J16 manifest-coverage guard tracked-only blind spot (new file passes
  pre-commit, fails post-commit — live N5 incident) → **J22** (widen the walk to
  `git ls-files --others --exclude-standard`, false-positive check on scratch files).
- 2026-07-30 — [chore/question/idea] the R5 follow-up trio → **R11** (Ask-spoke
  LLM-in-the-loop smoke on the agents-venv machine), **R13** (ADK 2.x partial/
  non-persisted event mode check vs the session-growth tripwire), **R12** (promote the
  stub-ADK harness into a committed fixture).
- 2026-07-30 — [chore] verify the neo4j-drydocs MCP server post-APOC-fix + GDS
  disposition (parked-until-port-review; the review completed with PORT-REPORT-e60822fc)
  → **G49**.
- 2026-07-30 — [chore] delete rollback container neo4j-drydocs-ee + verify-then-prune the
  orphan volumes (the neo4jtest probation week ended ~today; user pre-decided 2026-07-23)
  → **G50**.
- 2026-07-30 — [idea] SME feedback FB-03/FB-04 (page-role designations + agent-test
  harness) — retro-recorded, NO item: both were executed and SME-re-ruled same day
  (standalone `web/public/agent-test.html`; FB-03 designations stand); the "early seat
  for R5" note was superseded by R5 building `/ask` directly. V10's audit covers the
  runbook side.
- 2026-07-29 — [doc] "create a SME-Runbook for each module" (user directive, chat) → new
  **Epic V** (sme-runbooks, phase 10): **V1** coverage rule — every modules-registry entry
  maps to a governed runbook, an explicit EXEMPT reason, or a frozen shrink-only
  RUNBOOK_PENDING list (N2's LEDGER_PENDING idiom) — then **V2–V10** per-module runbooks
  (core, load, review, docgen, lineage, remediation, api, agents, web-audit), each gated
  on V1's extend-vs-author dispositions for the five runbooks that already exist.
- 2026-07-29 — [question] "one view of all of the taxonomy by source, ontology, extract and
  loads in one place — is it done?" (user, restating the 2026-07-28 ask) → confirmed **NOT
  built yet**: N3–N6 are the build and all four are still `todo` (N3 is next_ready). The
  restated ask is WIDER than the 07-28 scope (taxonomy + ontology weren't in it), so the
  taxonomy-capture and taxonomy-ontology-map joins were MERGED into **N4**'s acceptance
  rather than opened as a new item.
- 2026-07-29 — [idea] XML-fed CMD_LINE resolution (Control-M XML ingestion parses folder/job
  variables → shared resolver populates the G39 store's cmd_line_resolved; three guardrails:
  one-resolver-in-core, derived-beside-verbatim-with-provenance, precedence-before-first-
  disagreement) → **G46** (resolver cmd-line API), **G47** (controlm-xml-export seam),
  **G48** (resolve-cmdline-staging, v3 store); guardrail 3 stays in the inbox as the
  precedence [question].
- 2026-07-28 evening — [bug] rua_inventory silent scripts drop on metadata-only scripts.csv
  bundles (company fixed theirs same day; producer parity, mechanism-only) → **G45**.
- 2026-07-28 evening — [question] constraints.cypher "deprecated by K4 — kept for old graphs"
  comment under-scoped (role/membership keys are live catalog writes) → **C20**.
- 2026-07-28 evening — [chore] enforcement-matrix render must ride the one entry point (the
  stale-render check caught the 49667dd drift live; the J17 defect shape, second surface) → **J20**.
- 2026-07-28 evening — [idea] agent-runtime target-state follow-ups (ADR 0007 revisit check
  PASSED; detail in internal/agent-platform/) → **R10** (google-adk pin + ADR date-stamp);
  caller-identity slot MERGED into **R3**'s acceptance. The target-state prose itself lives in
  the internal review + the R-item acceptances now.
- 2026-07-28 pm — [question] "do we have ONE document with the loaders and order, commands,
  source→target mapping?" → answered NO, then scoped and groomed as **N3–N6** (Epic N,
  phase 11). It is split today across `internal/repo-README.md` (CLI reference + Control-M
  run order), the startup/refresh runbook (operational chain),
  `04-sme-checklist-and-load-plan.md` (sequential plan) and `config/source-mappings/*.yaml`
  (column ledgers). Built as a RENDER, not a fourth hand-written doc — hand-authoring it
  would create exactly the drift this session fixed twice (the depgraph README's stale scan
  roots, `provision.ps1`'s stale `docker run`). The blocker found while scoping: loaders
  declare `name` and `source_label` but NO source-registry id, so loader→source→column-ledger
  cannot be traversed at all — that is N3, and it has value even if N4–N6 never ship.
  No inbox line preceded this; the question arrived in chat and is recorded here for the trail.
- 2026-07-28 pm (post-UI-merge pass) — [bug] snapshot instrument unpinned (fd2834d) → **U7**
  (revision pin + capability probe); the sibling-repo depgraph fork merge stays inboxed as a
  [question] — user's call, different repo.
- 2026-07-28 pm — [bug] snapshot abs_path machine/worktree-dependent (twice ritual-blocking) → **U8**.
- 2026-07-28 pm — [idea] SME landing feedback FB-01/FB-02 + WF-LND wireframes → **O35** (p2 —
  direct SME feedback).
- 2026-07-28 pm — [bug] loads timeline rail dot clips first character → **O36**.
- 2026-07-28 pm — [idea] DataLens continuity DL-5/6/8 → **O37** (radius tokens), **O38**
  (IdChip convention), **O39** (deep-link slot, depends O38). DL-1/2/3/4/9 shipped pre-groom
  on `feat/datalens-quickwins`; DL-7 was a groom-MERGE into O32's notes, executed on-branch
  (`bc61408`) — counted as this pass's 1 merge.
- 2026-07-28 pm — [idea] DSI review DL-10/11/12 → **O40** (StatTiles click-to-filter), DL-11(a)
  folded into **O38**, DL-11(b) → **B5** (stage taxonomy capture, SME gate for the canonical
  set), **O41** (status-vocabulary map). The Epic R precedent note stays with the R1/ADR-0007
  gate materials in `continuity.md` — gate-session input, not a backlog item.
- 2026-07-28 pm — [idea] agent graph-navigation surface (live-benchmarked) → **R9** (read-only
  query command over the O33-guarded specs; MCP recorded as the later option).
- 2026-07-28 pm — [idea] VERIFIED-LIVE claims don't name their machine → **J18**.
- 2026-07-28 pm — [idea] two sessions built C19 concurrently; pushed-claim wording → **J19**.
- 2026-07-28 pm — [chore] misnamed Copy-feedback export (RESOLVED same day — deleted, user's
  call; it was rev1 YAML content under an .html name, both notes already applied in Rev 2;
  the deletion produced no diff and this trail line is the record it existed) → latent gap
  promoted as **L20** (feedback/ stray-file findings guard).
- 2026-07-28 pm — [doc] startup-runbook three held edits (2026-07-26 line): hold lifted (the
  SME review closed); edit 3 (container facts) landed via **L16** Rev 3; edits 1+2 (supplement
  verb collapse + Appendix B registry gap) → **L21** as one Rev 4.
- 2026-07-28 — [source] Snowflake data-catalog (dataset/distribution) loader plan → **G42**
  (source registration + taxonomy-first extractor), **G43** (cross-check reports),
  **G44** (gate prompt + proposed ontology entries; the dcat one-node-or-two ruling
  rides the gate). Epic-close-out groom run; the plan doc is the mapping ledger.
- 2026-07-28 — [bug] Component-cell comma-split shears parenthetical refs (U3) → **L18**.
- 2026-07-28 — [doc]×3 U3-census doc-drift lines (pre-squash citation sweep + sdlc §DEP
  tables + fan-in hotspot citation gap) consolidated → **L19** (one sweep, one review).
- 2026-07-28 — [bug] bootstrap "Constraints applied." with zero constraints (runMany
  no-ops DDL; pre-D5 window) → **D8** (the missing SHOW CONSTRAINTS count guard — the
  history is already fixed by D5, the item is the structural check).
- 2026-07-28 — [chore] render_gates.py missing from the stale-render ritual → **J17**.
- 2026-07-28 — U5 executed INSIDE the groom run (graph cross-check subsection added to
  this very skill) — **Epic U closed 6/6**, the run's close-out target.
- 2026-07-28 — [bug] depgraph scanner blind spots — one fix, three symptoms (cross-root
  IMPORTS, function-level imports, missing drydocs_api scan root; U1 F1 + U2 census,
  confirmed live by the graph-navigation benchmark 0-vs-24) → **U6** (p2, graph-infra;
  work spans the external depgraph repo + snapshot.ps1 target list); **U4 re-sequenced**
  to depend on U6, encoding the U1 wait-verdict. Companion agent-graph-navigation
  [idea] line stays inboxed (mechanism decision = `drydocs query` CLI vs MCP, user call).
- 2026-07-28 — [bug] ontology.cypher:109 dangling SDLC-subset load reference → **C19**
  (comment fix; the build-the-subset-at-all question recorded IN the item as an open
  user/SME call, not silently dropped).
- 2026-07-28 — [bug] PORT-MANIFEST `default: clean-add` fall-through gap → **J16** (the
  inverse-question guard: no tracked path resolves to default without an allowlisted
  reason; the git-readme.md deliberately-uncovered DECISION gets written into the
  allowlist rather than living only in this inbox).
- 2026-07-28 — [bug] doc_traceability/doc_feedback silent-prereq sweep leftovers → **L17**
  (Q8-pattern loud refusal; doc_feedback is the L5/L6 re-attachment loop, so it headlines).
  The batch_port_orchestrator half of that line was already FIXED 2026-07-27 in-session.
- 2026-07-28 — [chore] web/ 3 high-severity npm advisories → **O34** (audit-fix + verify;
  the 1,485 kB bundle/code-splitting design call recorded as explicitly OUT of O34's scope,
  parked in its notes).
- 2026-07-28 — [idea] Script→SWO rider (`:Script -IS_ENCODED_IN-> SwoClass` by extension,
  G33 §E1(b) precedent; run_as = Agent territory boundary; dead-script detection framing)
  → **MERGED into G22 notes as rider R1** for the gate session's agenda.
- 2026-07-28 — [question] m3_invokes `to_node` broadening (Script → Script|ETLProcess, the
  abioncloud wrapper-payload finding) → **MERGED into G22 notes as rider R2** — same gate
  session, vocabulary-shape decision.
- 2026-07-28 — [bug] SchemaMeta contamination defeats WRITE-side guards too (the Q8 build
  finding) → **MERGED into O33**: acceptance now covers loader prereq/guard queries, and
  the keyless-exemplar root-fix option is recorded in its notes.
- 2026-07-28 — [chore] neo4j-drydocs-ee literal `<password>` (2026-07-03 line) → **MERGED
  into the 2026-07-23 delete-rollback-container line** — deleting the container retires it.
- 2026-07-28 — trail moves, no new ids: the C17 PAT-keying and C18 shadow-model lines
  (both said "Groomed as …" since 2026-07-27, C18 since closed) and the fully-RESOLVED
  p0/boundary J14-residual line (its surviving question is the standalone
  platform-vocabulary line; the 6-digit-table-keys SME ruling is recorded in J15's
  close_note) moved out of the inbox.
- 2026-07-27 — [chat notes] G18→G22 premise correction: the psgmgr CM_DEF_VJOB_DETAIL-style
  table (split by job type) was never built → **G39** (temporary cmd-line staging store,
  graph-sourced — j.cmd_line already loads; next_ready) + **G40** (Python cmd-line parse into
  detail columns via the G26 registry + G15 arg contract; depends G39) + the correction merged
  into **G22**'s notes (gate stays the graph terminus; folder/job VARIABLES stay deferred as
  originally sequenced). Company-side "load into the real detail table when built" recorded in
  G40's notes for their tracker. G37 left unallocated (sequence gap beside G38 — possibly the
  concurrent session's; not risked).
- 2026-07-27 — [chore] EE home db `neo4j` pre-existing strays → **RESOLVED same day, no item**:
  user ruled "wipe it, it can be rebuilt" — 288 nodes deleted, 0 remain; topology DBs verified
  untouched (drydocs 834). The .env comment + dev-environment.yaml home_db_warning guard recurrence.
- 2026-07-27 — [idea] code-graph multi-persona review plan (docs/reviews/code-graph-review-plan.md)
  → **U1** (python-architect, opus), **U2** (PM backlog-truth audit), **U3** (tech-writer
  doc-status board) — all next_ready; optional skill-edit follow-ups → **U4** (tech-debt,
  gated on U1) + **U5** (groom-backlog, gated on U2). Epic U gains its first U-lettered ids.
- 2026-07-27 — [p0/boundary] knowledge/standards real-SEALID relocate-vs-sanitize → **J14**
  (option-b split, mechanism public / values internal); [lesson] field-vs-VALUE sweep failure
  → **J15** (value-shape boundary guard test, 70001-70099 block). Residual platform-vocabulary
  question re-inboxed as its own line.
- 2026-07-27 — [chore] :BusinessApplication index diet → **G36** (rides S3's bootstrap
  re-run); [bug] SchemaMeta exemplar contamination → **O33**; [bug] nothing-reads-ddall →
  **G38** (after G32's ruling); [question] deepdoc charter drift → **MERGED into G32** as
  acceptance clause (e).
- 2026-07-27 — [question] "BusinessApplication identity gate — deferred, resume leaner"
  RESOLVED without an item: the gate resumed on exactly the four-question surface and SIGNED
  OFF 2026-07-27 (22/22, `fc15191`). Build = S3 (acceptance rewritten at sign-off); ADR 0010
  amendment = S1; TOM-roles reopen = G35; glossary reservation = G34.

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-26 groom run (docs-residency design session, straight after G28/G29/G30)
  — **8 promoted / 2 inboxed** (todo 39 → 47). Source was a chat, not inbox lines, so
  nothing was moved out of the inbox except the notes below.
  - **Epic Q (docmeta):** **Q7** registry-vs-loaded reconciliation (user-requested — the
    registry declares corpora and `test_doc_registry.py` enforces the declaration's shape,
    but nothing checks a corpus was ever loaded or landed in the database it declared);
    **Q8** the DESCRIBES silent-drop bug; **Q9** re-file Essential GraphRAG as Neo4j vendor
    docs; **Q10** the failure/activity email corpus; **Q11** document supersession/currency.
  - **Epic G (component-topology):** **G32** the document/content topology ruling +
    ddcontext charter (the decision everything waits on); **G31** the proxy-node backbone extension
    (prerequisite for every corpus move).
  - **New phase 16 + Epic U — `self-documentation`:** **G33** the code snapshot under a
    Project root. Groomed into phase 6 with the marginal fit flagged, then **re-phased the
    same day on the user's ratification** — *"similar to a major version change of the
    snapshot ritual"*, i.e. a new capability rather than an ADR 0002 follow-up. The framing
    that earned the phase: the depgraph ritual's output stops being a JSON file a human
    reads and becomes a queryable `:Project` subgraph — a different KIND of thing, not a
    bigger version of the same one. Id kept as G33 (ids are stable references and it is
    already named in commit a37043a); new items here take U1, U2, … — **T is not free**, it
    is the port-turn series (`docs/port-T12-*.md`).
  - **The session's through-line, worth keeping:** ONE failure pattern found three times —
    *succeeds loudly, does nothing*. G29 (a supplement that runs and seeds no terms), G30
    (a spec that reads a database nothing writes), Q8 (an `OPTIONAL MATCH` whose target
    class is in another database). All three pass their loads green. Worth treating as a
    review lens rather than three unrelated fixes: **any MATCH that can legitimately find
    nothing needs to distinguish "this row missed" from "the whole class is absent".**
  - **Two decisions recorded that overturn signed-off records**, both routed through the
    gate rather than edited (the discipline G30 set): Q9 amends ADR 0006 §2 (the Q2 book's
    `ddcontext` placement) and G32 amends ADR 0002 D1 + ADR 0006 §2.
  - **One assumption I got wrong and corrected in-session:** I proposed *capture fidelity*
    as the database boundary (faithfully-captured vs inferred) and the user rejected it —
    a faithfully-captured stale Confluence page is MORE dangerous than a lossy capture of a
    good page, because it looks authoritative. The property that earns a boundary is
    **content authority**, not capture fidelity. Recorded because the wrong version is the
    intuitive one and will be re-proposed otherwise.
  - **A prediction that did not survive contact:** I named email retention as the fact that
    would decide 2 databases vs 3. It did not — the extracts are deliberately preserved past
    Outlook's 6–18 months until process/project retirement, so purge is property-scoped, not
    a database drop. The 3-DB decision rests on load separation and wipe blast-radius
    instead. Kept here so the retention argument is not re-run.
  - **Inboxed, not promoted:** the deepdoc scope drift (ADR 0002 vs ADR 0006 vs stated
    intent — a ruling, likely a G32 §) and "nothing reads `ddall`" (both at the top of the
    inbox).

- 2026-07-25 groom run (bare `/groom-backlog`, same session as the pre-UI structure review)
  — **11 promoted / 2 inboxed / 1 merged / 1 resolved-in-groom** (todo 30 → 41):
  - **New Epic S — `structure-remediation` (S1–S9)** from
    `docs/reviews/architecture-structure-review-2026-07-25.md` (15 findings, scored
    `(Impact+Risk)×(6−Effort)` plus a pre-UI cost-of-delay flag the formula cannot encode).
    Given its own epic rather than folded into G because the items share one review
    document, one phased plan, and three ADRs whose acceptance gates them — the board
    should show that sequencing as a unit. Each item keeps its correct existing plan
    phase, so the roadmap strip is unchanged.
    - **S1** — rule on ADRs 0008 / 0009 / 0010 (the decision item; the R1 precedent, so
      nothing is groomed into a done deal). Not a HITL gate: no edge semantics.
    - **S2** — ADR 0008: `drydocs_core/orchestration/` parent over `controlm/`, with the
      neutral `shell.py` / `paths.py` / `crosswalk.py` surface beside it. The review
      measured before recommending: ~1,100 of `controlm/`'s 1,725 lines are irreducibly
      Control-M, so the answer to *"should controlm/ become orchestration/"* is **no
      rename — add a parent**. Graph labels untouched (ADR 0003 rule 4).
    - **S3** — ADR 0010: `app_id` + `id_authority` beside `seal_id`, API and web emitting
      only the neutral pair. **GATE-BOUND** — a property-term binding on the canonical
      `:BusinessApplication` node; the map entry stays `proposed` until sign-off.
    - **S4** — ADR 0009: a `draft` table in `mapping.db` as the console's write-ahead
      buffer, promoted by emitting a YAML/CSV diff. Git stays the commit target.
    - **S5** (split the two monolith YAMLs by domain) · **S6** (JSON Schema per config
      family) · **S7** (record the folder-vs-module naming rule once).
    - **S8** — cli.py regroup. **MERGE**: the review's F6 and the long-parked
      `[idea] cli.py regroup` inbox line are the same work; that line's file was 937 lines
      when written and is 1,519 now, which is the argument for doing it. Its deprecation-alias
      condition carried into the acceptance. No dependency on S1 — reorganizing a CLI needs
      no ADR.
    - **S9** — `UI-WIP/` → `docs/design/ui-exploration/` + loose `docs/*.md` grouped.
      Effort was scored 1 and **corrected to 3–4 the same day** when the attempt measured
      31 tracked references (backlog.yaml 45 hits, the generated board, `PORT-MANIFEST.yaml`,
      two gate prompts, two governed renders, `drydocs_api/app.py`) — branch + port-sequenced,
      never a tidy-up commit.
  - **G28** — the multi-database naming drift, found while writing the executive overview
    against the live gated convention. `drydocs_deepdoc.DATABASE = "drydocs_context"`, a
    database `provisioning/01_databases.cypher` never creates (it creates `ddcontext`), and
    `test_lineage_deepdoc_scaffold.py` **pins that value** — so the suite currently protects
    the wrong name. Also unanswered: `ddlineage` is provisioned and read by four query specs,
    but `drydocs_lineage/writer.py` pins `DATABASE = "drydocs"`, so those specs read an empty
    database. Not a trust-boundary hole — the writer refuses on an allowlist.
    RESOLVED 2026-07-26: that second half was split out of G28 as **G30** (a data-residency
    decision, not a naming fix — bundling them was a grooming error) and is now DONE. Ruled
    for ADR 0002 D1/D2: curated lineage lands in `drydocs`; the four specs repoint there and
    `ddlineage` is documented as provisioned-for-later. Ruling written up as ADR 0002's
    "Residency clarification", with the named trigger to revisit through the gate.
  - **G29** — [idea] supplement consolidation shape A (2026-07-24, designed + user-reviewed)
    → the single `apply-supplements` verb with legacy verbs as delegating aliases, all four
    agreed riders in the acceptance. Its sibling **shape C** re-inboxed slim above: it changes
    what a supplement *means*, so it is gate-worthy, not a refactor.
  - **inboxed:** F11 depgraph-snapshot retention (a user call about audit history — and the
    review's proposed mechanism was wrong: `drydocs prune-snapshots` prunes snapshots inside
    Neo4j, not the JSON files); supplement shape C (above).
  - **resolved in the groom, no promotion:** [doc] reconcile-port skill's stale Track-1 floor
    — measured this session at **114 passed / 3 skipped** (the line said 90/3; the inbox note's
    own 113/3 was already stale, since the 2026-07-25 boundary-guard fix added a fifth
    `test_module_boundary.py` test). Skill updated in place, with the number reframed as a
    FLOOR to re-measure rather than a constant, since this is the second time it has drifted.
  - **kept-updated:** the Databricks Unity Catalog line (its governed-namespace citation was
    consumed by ADR 0010 / S3; the tag-policy and glossary-as-concept-scheme citations stay
    parked) · the acronym-catalog line (the review's §4.2 independently reaches the same
    `CatalogBusinessTerm` home from the identity question rather than the collision question;
    still parked on the gate-log Q6 ruling) · the unlocated-typo bug (G29 rewrites the very
    verb list Appendix B carries, so its rider resolves the best-guess half).
  - **findings deliberately given NO item**, recorded so a future reviewer does not rediscover
    them: F4 / F9 / F10-part (done same day — `432ea43` boundary-guard fix, `bbf29cf` gitignore);
    F5 (the `drydocs/` 4-component flat namespace — deferred to Phase C by ADR 0002-a-1, and
    the review's §6 says explicitly not to reopen it mid-UI-build); F15 (two test roots — `tests/`
    pytest and `graph-tests/` YAML acceptance are two mechanisms, not duplication).
  - **kept parked, unchanged** (trigger checked this pass): gate-log Q6 reopen (SME ruling),
    T11 L7-ratification snippet (owed at the next company session), Oracle connection for
    lineage/remediation, company-side greenfield remediation standards, rollback-container
    deletion, PDN/BIM milestone-grain design, email-DL contact point (gate-tracked), the
    Control-M app-code → SEAL `:Port` block (gate `seal-app-ref-edge-reshape` v2 — note S3
    touches the same node, so run them together if timing allows), env-toggle canonical
    identity, XML WARN-flood port note, compact-timestamp back-flow, AIS acronym port-carry,
    ControlMApplication two-pattern mapping, m7 build follow-up, marketing-site brand kit,
    FW-really-API gap classes, DPL ingestion-leg residuals, company back-flow batch,
    company-side heads-ups, post-squash ref cleanup, Runbook Rev 3 rider, SNYK_TOKEN,
    SEAL/PAT generic terminology (three §Decision calls — **note S3 now overlaps its
    `SEALID`→generic-identity-property call and may close it**), m3_invokes `to_node`
    broadening, depgraph metric extensions, ETL-tooling inventory, JobRun indexes, SaaS
    scaffold research, K2 FID/ALIAS tables, `ctlm_id` ripple, dry-docs.com seed,
    /documentation whitepaper type, lineage live-load gate, remediation slices, Phase C
    packaging, Control-M Workbench, BRD outline, docmeta P4–P7, EE container password,
    `common/` in /list-apps.

- 2026-07-23 groom run (full inbox sweep + the misfiled "UI acceleration session"
  block folded in from the bottom of this file) — 5 promoted / 2 resolved-in-build
  (no promotion) / rest kept parked (todo 25 → 30):
  - [chore] Neo4j-container-recreation residual (the container migration itself
    — `neo4jtest` on named volume `neo4j-testdata`, default ports 7474/7687 — is
    already done; only the doc is stale) → **L16**: refresh
    `docs/design/drydocs-startup-refresh-runbook.md`'s container table + start
    commands (still say `neo4j-drydocs-ee`/7476/7689) via the governed render
    pipeline. The sibling "delete the rollback container after a week + prune
    orphan volumes" chore stays INBOXED (time-gated manual Docker op with no
    repo-testable acceptance — the SNYK_TOKEN / post-squash-cleanup precedent:
    manual user steps don't get a backlog.yaml pull id).
  - Misfiled "## 2026-07-23 — UI acceleration session" block (context-graph
    analysis + underhood build) folded into this trail entry — its groom
    candidates from `UI-WIP/two-track-ui-plan.md` (Track 1 table) promoted:
    **O29** (T1-5 trust-tier/edge-provenance legend live on the /lineage and
    /docs graph-pane canvases, adopting context-graph's declared/observed
    legend pattern); **O30** (T1-7 retire `App.css` legacy-mockup classes into
    the token idiom across SignIn/MyApps/GraphExplorer/TowerDrill/
    CypherConsole); **O31** (T1-8 regenerate `web/src/underhood/
    benchmarkData.ts` from the docmeta evaluation-harness output — no
    standalone eval-harness backlog item exists yet, so the dependency is
    recorded as prose in the item's notes per the groom instruction and
    `depends_on` is left `[]`); **O32** (T1-6 light-mode design pass — not
    previously tracked; dark stays canonical). The "intended-bypass build
    landed on main" record and the context-graph adopt/avoid headlines are
    DONE-work notes only, not backlog-actionable — no item, preserved here and
    in `UI-WIP/two-track-ui-plan.md` / `internal/context-graph-analysis/
    ui-architecture-analysis.md`.
  - [source] By-SEAL bulk MAC inventory line → RESOLVED IN BUILD, no
    promotion: G25 (done 2026-07-23) already carries both the taxonomy-first
    per-SEAL staging and the clone-lag `cross_check()` column the line asked
    for; the assumed-field-contract residual rides the dpl_mac discipline, not
    a separate item.
  - [question] Gate rider (G17 build): MAC subType → kind-enum semantics →
    MERGED into **G27** (done 2026-07-22): the gate BRIEF
    (`config/gate-prompts/etlprocess-kind-enum.yaml`) already carries this
    exact question with a recommendation; the SME sign-off itself stays a
    HITL session, not a fresh backlog item.
  - kept parked, unchanged (checked against backlog.yaml this pass — no
    matching item to merge into, or the recorded trigger/gate hasn't fired):
    Oracle connection for the lineage/remediation path (needs SME scope
    clarification first — a question, not yet scoped work), company-side
    greenfield remediation standards (no FR-REM-5/M2 item exists yet),
    PDN trigger/BIM-90489 milestone-grain design, email-DL contact-point
    ontology mapping (already gate-tracked, nothing further to promote), the
    Control-M app-code → SEAL :Port attribution block (owned by gate
    `seal-app-ref-edge-reshape` v2; the property-diet rider sub-part already
    resolved in-line 2026-07-23), env-toggle canonical-identity constraint,
    XML-run WARN-flood next-port note, compact-timestamp normalization
    back-flow note, AIS acronym port-carry, ControlMApplication two-pattern
    mapping (gate-decision core), m7 build follow-up (lineage live-load
    gate), public marketing-site brand kit, FW-really-API provenance gap
    classes, DPL ingestion-leg residuals, back-flow of un-back-flowed company
    advances, company-side heads-ups (their tracker), post-squash ref cleanup
    (destructive, user-gated), Runbook Rev 3 rider, SNYK_TOKEN manual step,
    SEAL/PAT generic terminology (three §Decision user calls), m3_invokes
    to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance
    plan's next touch), SaaS scaffold research (triggers unfired), K2
    FID/ALIAS tables (company-side), ctlm_id ripple (internal-side),
    dry-docs.com seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Control-M Workbench
    (entitlement), BRD outline (later phase), docmeta plan P4–P7 (Q6 still
    todo), EE container password (user deferred), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-23 R1 gate SIGNED OFF (same session as the groom below) — **ADR 0007 ACCEPTED
  as written**; rulings (full text in config/gate-log.md): (a) Tier-2 task-graph residency
  = in-process only (ddcontext persistence deferred; new gate if ever proposed);
  (b) :AgentRun envelope → ddcontext, dedicated writer boundary, question sha256+length
  only in-graph; (c) LLM keys = **environment-split: local/producer Anthropic API key,
  company Azure OpenAI** — Gemini NOT the runtime default, closing the 2026-07-03
  question with a ruling that supersedes its Gemini-shaped assumption. R2 next_ready.
- 2026-07-23 groom run (agentic-Q&A architecture session) — **new phase 15 "Agentic Q&A
  console" + Epic R (R1–R8)** from the llm-graph-builder vs knowledge-graph-of-thoughts
  comparative analysis; **ADR 0007 drafted (PROPOSED)** — SME gate = R1, which also rules
  context-graph escalation residency, :AgentRun target DB, and the LLM key strategy.
  Moved from inbox: the 2026-07-03 [question] LLM key strategy (Gemini vs Anthropic via
  LiteLLM) → decided at **R1**. New module registered: drydocs-agents (agents/ ADK
  service). Analysis dossier (both workflow diagrams) linked from ADR 0007's footnote.
- 2026-07-22 — [source] **Backstage catalog-model assessment T1–T8 groomed**
  (UI-WIP/backstage-catalog-assessment.md; shallow clone surveyed + deleted same day):
  T1 kind-enum gate precedent brief → **G27** (in_progress, pulled at groom); T2+T3
  QuerySpec conventions (derived-edge rule + external ref grammar + no element ids) →
  **O27**; T4 inverse_label display field → **C15**; T5 status.items node-status
  envelope → **O28**; T7 metadata key-prefix governance → **C16**; T8 env-toggle
  canonical-identity constraint → inboxed above (no env-toggle item exists yet); T6
  schema-as-contract on DataAsset = design CONFIRMATION only — already covered by the
  O10 schema-definition frame + the G17 MAC dataset feed chain, no new item.

- 2026-07-21 pm — [task] **C12 platforms-taxonomy gate RUN + SIGNED OFF in-chat** (same
  session, ~an hour after C12 was groomed; the K5 precedent): rendered page presented,
  3/3 as recommended — A+B1–B3 confirmed as written (registry model; Ais* removed;
  USES_SOFTWARE {source: 'batch-port'} landing), B4 existing local no-PROV typing covers
  the migrated fact, B5 airflow row stays as the F2 crosswalk placeholder. Gate-log
  entry appended; platforms.yaml confirmed: true; build follow-ups groomed → **C13**
  (SchedulerKind retirement + vocab/map closure + Ais* straggler sweep) and **C14**
  (batch-port USES_SOFTWARE loader migration). C12 done (todo 22 / done 122).

- 2026-07-21 pm groom run (bare /groom-backlog, same session as the platforms-taxonomy
  pre-rulings) — 3 promoted / 0 inboxed / 1 kept-updated (todo 18 → 21):
  - [idea] SchedulerKind → AisCapability/AiTool deprecation (parked since 2026-07-09;
    groom-condition FULLY FIRED today — C11 captured the company shape am, the SME ruled
    the reshape in-chat pm: Ais* removed both sides, registry model wins, gate prompt
    reshaped to confirm-as-written) → **C12** (run the platforms gate, USER-GATED START;
    build follow-ups groom at sign-off — the K5 gate-RUN precedent).
  - [idea] app-to-app path runbook view wireframe (2026-07-21) → **O26** (Runbooks-page
    App-path tab + QuerySpec runbooks.app-path.v1; lane partition from label sets only —
    the layer/c4_level vocabulary stays a gate question; trigger fired: O17 + O11 done).
  - [idea] launcher-registry config-file migration (2026-07-16, the remaining inboxed
    half) → **G26** (config/ pattern + schema guard; classifier_rule ids pinned by
    invocation_patterns must keep resolving; trigger fired: O12 done — its matrix renders
    this registry as the unguarded-config example G26 retires).
  - kept-updated: the ControlMApplication two-pattern mapping line — O13 shipped same
    day (0dc2831), satisfying its prioritization flag; the gate-decision core stays
    parked on the SME convening the mapping gate / K2's next touch.
  - kept parked, unchanged (trigger checks this pass): AIS acronym port-carry (next
    cross-repo port), MAC subType kind-enum rider (next lineage gate; G22 closest), m7
    build follow-up (lineage live-load / m7 flip), marketing-site brand kit (site not
    started), FW-really-API gap classes (next Script-refinement gate), DPL ingestion-leg
    residuals, company back-flow batch (needs screenshot channel), company-side heads-ups
    (relay next company session), post-squash ref cleanup (user, destructive), Runbook
    Rev 3 rider, SNYK_TOKEN manual step, SEAL/PAT terminology (three §Decision calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metrics (sibling repo),
    ETL-tooling inventory, JobRun indexes, SaaS scaffold research, K2 FID/ALIAS
    (company-side), ctlm_id ripple (internal-side), dry-docs.com seed, /documentation
    whitepaper type, lineage live-load gate (HITL scheduling), remediation slices (TDD
    §6/§7), Phase C packaging, Workbench (entitlement), BRD outline (later phase),
    docmeta P4–P7 (Q6 still todo), EE container password, LLM key strategy, common/
    cosmetic, cli.py regroup (v1.0 window).

- 2026-07-21 groom run (bare /groom-backlog, same day as cmdline-nfr-vetting/G15/G16 and the
  Epic O landings) — 2 promoted / 1 retired-merged / 1 kept-updated (todo 22 → 24):
  - [source] DPL runtime traced end-to-end (2026-07-21) + [idea] ETLProcess kind
    discriminator (2026-07-19; its trigger FIRED — pipeline.json subType is exactly the
    discriminating signal G12 lacked) → **G17** (MAC ingest seam: dataset-flow
    READS_FROM/WRITES_TO candidates + kind-derivation rule + SEAL attribution facts;
    synthetic fixtures, gate-confirmed endpoints, all m3_* statuses untouched;
    depends_on G15 — ready now).
  - [idea] AIS taxonomy back-flow for the platforms gate (flagged 2026-07-10 in the
    66acea8 port report, unactioned since) → **C11** (USER-GATED START: capture the
    company-confirmed AisCapability/AiTool shape into config/taxonomy/platforms.yaml
    as the gate's PROPOSED seed; pull loop skips it until the user supplies the
    screenshot/describe material; the sibling SchedulerKind-deprecation line stays
    parked on that same gate).
  - [source] variable gap analysis (2,384 names vs the alias map) → RETIRED MERGED —
    fully consumed at build time: G15's acceptance (a)/(c) cites it as evidence and
    G16 built its alias rollups, value contracts, and the ETL_ARTIFACT_SHA canonical
    from it. Nothing left to carry.
  - kept-updated: the DPL ingestion-leg line — its open item (b) (DataAsset
    zone/glue-table shapes for the MAC enrichment feed) now rides G17 instead of the
    retired sibling line; its other open items (ingestion-launcher jar sample,
    Pre/Post-exec file-op surface, cross-job %%\\JOB\VAR threading) stay inboxed.
  - kept parked, unchanged (each on its recorded trigger): m7 build follow-up
    (deliberately inboxed at the gate — lands at the lineage live-load / m7 flip),
    public marketing-site brand kit (site not started), FW-really-API provenance gap
    classes (:Script property proposals = gate rider for the next Script-refinement/
    lineage gate session), back-flow of un-back-flowed company advances (needs the
    screenshot/describe channel; spans six modules — batch shape decided when the
    material arrives), company-side heads-ups (their tracker; relay next company
    session), post-squash ref cleanup (user, destructive), Runbook Rev 3 rider,
    SNYK_TOKEN manual step, SEAL/PAT generic terminology (three §Decision user calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance plan's
    next touch), SaaS scaffold research (triggers unfired), launcher-registry
    config-file migration (O12 todo), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling —
    unchanged by G15/G16), remediation slices (TDD §6/§7), Phase C packaging (plan
    gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool (gate; C11
    now feeds it), BRD outline (later phase), docmeta P4–P7 (plan-tracked while Q6
    todo), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-21 — [question] Company draft CMD_LINE/variable NFR ontology vetted vs m3 vocab →
  **RULED same day at gate `cmdline-nfr-vetting`** (config/gate-log.md; guided SME session,
  4/4 as recommended): TRIGGERS from-node stays the LAUNCHER (payload variant rejected);
  `USES_ARTIFACT` registered as vocab entry `m7_uses_artifact` (status: planned); :Script
  refinements adopted (script_role + artifact_* props); all 7 variable-standard deltas
  adopted (ETL_* prefix, ETL_ARTIFACT_SHA, aliases-suggest-values-decide, alias-map
  completion, two platform axes, FACT_REGISTRY migration, mode flags stay literals) →
  engine-alignment work groomed as **G16**.

- 2026-07-21 — [chat] UI extension groom ("extend the UI open items until HITL"): the new
  UI-WIP corpus (DryDocs_UI_Development_Specs.md, gemini-wire-frame.md, icons.md,
  layout-anatomy-checklist.md, new mocks) + site-plan §5 P3 → **O15–O22** (Ownership /
  Loads / Runbooks+Remediation / Docs / Gates-read-only pages, the O20 write-surface HITL
  gate as the chain terminus, UI-WIP commit chore w/ LFS, icon SVG export); demo-content +
  expanded-landing specs **merged into O9** inputs/notes; WEBSITE-IDEAS.MD parked to Inbox
  (public site, separate workstream).

- 2026-07-21 — [source] Real prod DPL CMD_LINE samples (folder/job screenshots +
  variables-simulation views) → **merged into G15** (acceptance upgraded from
  placeholders to observed grammar: single-dash `-pipeline` GUID as the only literal,
  variable-held launcher fallback, -i/-t/-py mode flags, -seal/-fid/-img/-conf/-compute
  property set; one dt-launcher.sh backbone across ingest/transform/provision). Remainder
  re-inboxed on the ingestion-leg line: template ingestion-launcher jar unobserved,
  Pre/Post-exec file-op surface, zone/glue DataAsset shapes, cross-job %%\\JOB\VAR.

- 2026-07-21 — [chat] DPL launcher key-parameter capture (--pipeline-id spelling +
  shell-launcher variants + -py route + dataset-id/aws/jar/queue params as properties)
  → **G15**. The sibling 2026-07-21 inbox line (MAC dataset-flow enrichment feed +
  G12 kind discriminator) stays in the inbox — G15's explicit non-goal.

- 2026-07-20 groom run (evening; second machine re-based post-squash, then /groom-backlog) —
  2 promoted / 1 inboxed / 1 kept-updated (todo 17 → 19):
  - session preamble (recorded here — ref state, not backlog): this machine adopted the
    squashed main (reset to 4540bbc), local `feat/mapping-store` DELETED as superseded
    (its content was inside the Initial-import squash and main evolved past it; old
    history kept at local tag `archive/old-history-2026-07-20`).
  - [doc] runbook-mapping-demo free-form pre-L8 (2026-07-18) → **L14** (refit to
    runbook.outline.yaml, 2nd runbook exemplar; trigger = L8 done, e6bcb24).
  - [doc] project-review canonical outline (2026-07-14) → **L15** (review.outline.yaml
    3rd doc type + recorded refresh cadence; same L8 trigger; p3).
  - inboxed: post-squash ref cleanup (stale origin branches feat/mapping-store +
    feature/provenance-audit-fields-plan; local backup branch/stash/tags) — destructive,
    user-gated.
  - kept-updated: SEAL/PAT generic-terminology line — C10's CSDM mining landed (its
    named missing piece); decision surface fully fed, still parked on the three
    §Decision user calls (scope / new-epic plan change / SEALID property).
  - trigger checks this pass: Q6 todo → docmeta P4–P7 stay plan-tracked; O12 todo →
    launcher-registry config-file migration stays; E1 deferred both sides; Runbook Rev 3
    rider + SNYK_TOKEN manual step stay inboxed (new today, correctly parked). All other
    lines kept parked, unchanged on their recorded gates.

- 2026-07-20 — [doc] apply the runbook rev1 SME feedback → EXECUTED SAME-DAY (user-directed,
  no backlog id): both notes applied to the .md (front-matter one item per line; out-of-scope
  drops the company-side Track-2 item), Rev 1→2 with a change note, re-rendered (footer
  "Rev 2 · commit a135a6d"), validator + doc tests green. The rev1.yaml stays as the
  feedback record; the stray -sme.html working copy remains the user's to delete.

- 2026-07-20 — [chore] USER MANUAL STEP: port-bundle transfer → **RETIRED, FULLY COMPLETE**
  (the 07-19 line, end to end): bundle created @ 3ae9b08 (447 commits, full pre-squash
  history) → base64 3-way split → emailed → company side rejoined, hash-verified,
  `git bundle verify` passed, full bundle-port reconciliation ran (their
  PORT-REPORT-bd7952f.md, 2026-07-20) → ALL FIVE local transfer files deleted
  (3 parts post-email; the bundle + .b64.txt deleted 2026-07-20 pm after far-side verify,
  user-directed). Full private history now exists only in local `archive/full-history` +
  the company repo. Recipe reference: `docs/ruff-format-convergence.md` §"Transfer
  without visibility change".

- 2026-07-20 — [question] cross-repo backlog id collision → **DECIDED SAME-DAY (user):
  the DD-series** (`DD1`, `DD2`, …) is reserved for company-side-only items; the producer
  never allocates it, the company never allocates epic-letter ids. Recorded in
  git-readme.md (§backlog id allocation), the backlog.yaml header, and the groom-backlog
  skill id rule. REMAINING (company-side, next session there): renumber their colliding
  C10/K6/N3 → DD1–DD3 before the next port range applies.

- 2026-07-20 pm — bundle-port readout review (company-side photo; their
  PORT-REPORT-bd7952f.md) — 2 mirrored done / 1 line resolved / 1 question inboxed:
  - **P1 + P4 → done** (company completion wins for company-side work — their probes +
    CM_AVG_RUN supplement loader shipped; resolves the 07-18 "concurrent Epic P session"
    observation). P3 becomes next_ready; P5 still waits on P3.
  - port-bundle USER MANUAL STEP line → RESOLVED to its last step (delete the 2 remaining
    local transfer files; far side verified).
  - inboxed: the C10/K6/N3 cross-repo id-collision question (convention needed before the
    next port).
  - noted, no producer change: the company deferred 3 HITL deltas to their own gates
    (docs_*/:DocSource union-add; catalog_supports re-activation; jobrun-observation —
    E1's gate is now deferred BOTH sides); their 4 port commits await review + push.

- 2026-07-20 — [chore] Snyk scanning in CI → EXECUTED SAME-DAY (no backlog id, direct user
  request — the PAT-semicolon precedent): ci.yml gains a `snyk` job — SCA over the Poetry
  manifest (blocking at high severity) + advisory `snyk code` SAST (the ruff idiom).
  Token-gated: every scan step skips cleanly until the SNYK_TOKEN repo secret exists.
  REMAINING USER MANUAL STEP: add SNYK_TOKEN (Settings → Secrets → Actions; token from
  app.snyk.io) — first green scan confirms; consider gating `snyk code` after triage.

- 2026-07-20 — [source] **external/ServiceNow doc set** (6 files downloaded same day: CMDB
  Process Guide .docx, CMDB Product Architecture / Data Manager / Governance Workshop
  .pptx, ITAM-SAM Integration Options .pptx, "What are services and service offerings"
  .pdf) → **C10** (promoted directly from chat, the C9 precedent): housing + SOURCE-MANIFEST
  + classification decision, readable-text conversion (the SDLC-Docs/extracted idiom),
  and per-file concept mining dispositioned incorporate/park/reject — feeds the parked
  generic-terminology idea (the CSDM service/service-offering layer is its missing
  piece). User context in the item notes: the full-circle-docs-era ServiceNow Marketplace
  consideration (research only) and the CMDB-for-taxonomy→ontology reference. Files stay
  untracked until C10's classification step.

- 2026-07-20 — [task] **K5 Product Cabinet gate RUN + SIGNED OFF in-chat** (same session as
  the groom below, later in the day; page rendered via gate_pages.py from the in-flight
  2026-07-19 gate-prep, sections A–E answered in-session, §F signed off — gate-log
  2026-07-20): map entry confirmed; families INDEPENDENT (shared-cto dropped, rename
  history recorded — supersedes 2026-07-10 §B); tech_partner :AreaProduct-only; BOTH
  attribution forms (collapsed catalog_cabinet_attributed_to added); reporting edges
  DEFERRED (internal-side); DevTeam↔BusinessApplication M:N confirmed. Supplement
  follow-up promoted directly → **K6** (the C9 direct-promotion precedent); K5 done
  (todo 22 / done 91). The 07-20 groom entry's "K5 in flight uncommitted" observation is
  RESOLVED — this session took ownership, committed the stream (K5(1)/K5(2) + this
  close-out), and the m3_invokes to_node rider stays parked (this gate was
  Product-Cabinet-scoped; next lineage-vocab gate remains its trigger).

- 2026-07-20 groom run (bare /groom-backlog, day after the weekly run; post history-squash) —
  0 promoted / 0 merged / 1 kept-updated; backlog database untouched (todo 22 / in_progress 1 /
  done 90 stand as of the 07-19 groom):
  - kept-updated: the USER MANUAL STEP port-bundle line gains the SQUASH RIDER — today's
    history squash (main = single commit c5a84c3; full history only in local
    archive/full-history) makes "email the existing 3ae9b08 full-history parts vs re-cut
    from the squashed main" a user decision that must precede the email step.
  - noted closed by the squash: the 07-19 seal-sample residual ("git HISTORY retains both
    seal twins until a rewrite, user-gated") is CLOSED on main/origin — pre-squash history
    survives only in local archive/full-history + the five transfer files (whose deletion
    is the port-bundle line's remaining step).
  - observation (no groom action): **K5 gate-prep is IN FLIGHT, UNCOMMITTED** in the working
    tree — config/gate-prompts/product-cabinet-attribution.yaml (new) + map/vocab/
    schema_graph edits, proposed_at 2026-07-19, all correctly gate-bound (everything
    planned/proposed, nothing applied). Left untouched per the 07-18 P1 precedent: the
    owning session commits and flips K5 todo→in_progress itself; this groom's commit
    excludes those files.
  - observation (user decision, destructive): stash@{0} "On feat/k4-businessapplication-
    reshape: gate-review IDEAS entries" is STALE — its two 2026-07-15 lines reached the
    inbox via another path and were groomed to G12/G13 at the 07-16 pm run (G12 since
    executed). Candidate `git stash drop`; not dropped by the groom.
  - trigger checks this pass: Q4/Q5 done but Q6 still todo → docmeta P4–P7 stay
    plan-tracked; L8 todo → runbook-mapping-demo refit + project-review outline stay;
    O12 todo → launcher-registry config-file migration stays; no other recorded gate moved
    since yesterday's run. All other lines kept parked, unchanged (m3_invokes to_node
    broadening noted as a candidate agenda rider for whichever gate session runs next —
    the in-flight K5 gate is Product-Cabinet-scoped, so adding it is the SME's call).

- 2026-07-19 groom run (weekly inbox groom) — 2 promoted / 2 merged-or-folded / 1 kept-updated:
  - [bug] publish-ceiling drift (real identifiers in publishable-tier files; found by the
    2026-07-19 aborted-mirror pre-publish grep) → **J13** (p1, fable, USER-GATED START — the
    user confirms the real-vs-synthetic term list before execution; the term list is recorded
    internal/-side only, never in publishable tiers; the backlog pull loop skips J13 until then).
  - [idea] file-ops READS_FROM/WRITES_TO extractor pass (G13's missing feed) → **G14**; the
    sibling [idea] surface-`WritePlan.unresolved_file_ops` line FOLDED into G14's acceptance
    (one item — the feed is what makes the counter worth reading).
  - [source] codeflow UI screenshot → MERGED into **O9** (inputs + notes). File already tracked
    at `UI-WIP/codeflow-ui-reference.png`; classification External, captured 2026-07-19 from
    https://github.com/braedonsaunders/codeflow/blob/main/screenshot.png (MIT-licensed repo) —
    cite, don't imitate branding.
  - kept-updated: the USER MANUAL STEP port-bundle line — the create half is done (bundle @
    3ae9b08 encoded + 3-way split); remaining: email the parts, far-side hash confirm, delete
    the five local transfer files.
  - kept parked, unchanged (each on its recorded gate): m3_invokes to_node broadening (next
    vocab gate session), ETLProcess kind discriminator (needs a discriminating signal),
    depgraph metric extensions (sibling-repo work), runbook-mapping-demo refit (L8),
    ETL-tooling inventory domain (direction), JobRun-index fold (provenance plan's next
    touch), SaaS scaffold research (triggers unfired), launcher-registry config-file
    migration, project-review outline (L8), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind
    → AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P4–P7
    (plan-tracked until Q4–Q6 land), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-19 — [bug] PAT seal_ids semicolon-delimiter mismatch → FIXED SAME-DAY (no backlog id,
  user call — pulled ahead of the catalog-pat team-report onboarding it was parked for):
  `PatProductMappingRow.seal_ids` now normalizes `;` → `,` before the cypher's comma split;
  synthetic sample row T0042 made semicolon-delimited to exercise the path; drift guard
  `test_row_model_normalizes_semicolon_seal_ids`; `internal/pat-evidence/README.md` note updated.

- 2026-07-19 — [chore] seal-sample standing exception → RETIRED EXECUTED SAME-DAY (no backlog id):
  user call — DELETE both `seal_*__sample.csv` twins from the tip rather than synthesize
  replacements (names were fictional; the seal_ids were real). App file e7f8f20 (user, web UI) +
  contacts twin this commit; classification.yaml carve-out removed; `drydocs/data/samples/**` is
  synthetic-only again. Residual: git HISTORY retains both files until a rewrite (user-gated).
  A future SEAL sample, if ever needed, gets synthetic ids (the pat_product_mapping pattern).

- 2026-07-18 — [task] C5-gate follow-up (promoted directly from the gate session):
  pat_product_mapping.cypher still writes the 2026-06-21-deprecated catalog_supports
  edge every load; SME supplied PAT screenshots in-session (Internal-Confidential,
  held out of the repo) showing teams map to 1..n business applications via the PAT
  team report while area-product alignment is volatile + relationship-typed — the
  deprecated edge may be independently asserted (the C5 exception path), so it re-gates
  rather than gets deleted blind → **C9** (p1, fable).

- 2026-07-18 — [bug] design-doc DUAL-HTML render (chat capture + screenshot, promoted
  directly): `.print.html` misrenders in-browser while the screen `.html` already
  print-adapts (white-on-black on screen, black-on-white at print) — SME call: one file
  suffices, retire the `.print.html` series (fold the L6 print-margin anchors into
  @media print) → **L13**. Evidence PNG at repo root, local-only (root-images
  gitignore). Related-not-merged: L9 (Chrome partial render of the screen html).

- 2026-07-18 groom run (weekly inbox groom, on `feat/mapping-store` — the 07-15 K4-branch
  precedent) — 5 promoted / 1 merged / 2 retired-executed / 2 re-inboxed slim / 1 kept-updated:
  - [idea] mapping-store research line → RETIRED EXECUTED-PRE-GROOM (the TechStack plan-07
    precedent — plan-tracked, not epic-itemized): M0–M4 + the wf-mapping-01 live demo BUILT on
    `feat/mapping-store` (807e050), deltas recorded in the plan doc header (store moved to
    drydocs_core; artifact-download submit; no new gates). Groom-touches: **O13** gains a
    progress record + the plan-§6 acceptance rider ("dropdowns read mapping.db via
    drydocs-api"); the plan's unwired M2 rebuild residual promoted → **O14** (staleness
    guard — a stale var/mapping.db serves stale grids until deleted). ETL-tooling inventory
    re-inboxed as its own slim line.
  - docmeta plan line (trigger fired 2026-07-16: P0 verdict = BUILD, Q3 done) → P1–P3
    promoted: **Q4** (gate session + docmeta ADR + planned vocab entries, reconciled against
    active docs_*; fable), **Q5** (doc-source registry ledger + guard test + stray-PDF
    sweep), **Q6** (Port A bkup→producer; module `drydocs-docmeta` REGISTERED as working
    name — final at the Q4 gate, the drydocs-api precedent). Line kept-updated: P4–P7 stay
    plan-tracked; GraphAcademy existence-constraints rider attached.
  - [question/idea/chore] GraphAcademy advisor line → dispositioned per sub-item:
    incremental delete-sweep → **D7**; BaseLoader index preflight EXECUTED PRE-GROOM
    (66049a0); DC-collision check ALREADY ROUTED to the internal-session checklist
    (66049a0/d21d4e5) — **P1 deliberately untouched this groom: its status flip is
    uncommitted in a concurrent Epic P session** (c12ab43 readout); graphrag-llm-navigation
    annotation + the save_data_model save were already done in-line; JobRun-index fold
    re-inboxed slim (provenance plan's next touch).
  - [idea] EE re-bootstrap demonstrable-content loads → MERGED into **D6** (the line's own
    suggestion): the quick-start/bootstrap sequence gains load-software-registry +
    load-bmc-docs (+ optional load-essential-graphrag); Q3's P0 spike already re-ran both
    loads once, proving the gap.
  - inboxed new: runbook-mapping-demo authored free-form pre-L8 (refit when L8 lands; the
    web-console TDD from the same session is auto-swept, nothing to do).
  - kept parked, unchanged (each on its recorded gate): SaaS scaffold research (direction;
    export-target/template-play triggers unfired), launcher-registry config-file migration,
    project-review outline (L8), K2 FID/ALIAS tables (company-side; fid-seal/alias-seal
    mapping domains now visibly registered-but-unavailable in the O13 demo), ctlm_id ripple,
    dry-docs.com seed, /documentation whitepaper type, lineage live-load gate (HITL),
    remediation slices (TDD §6/§7), Phase C packaging, Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME), BRD outline, EE container password,
    LLM key strategy, common/ cosmetic, cli.py regroup (v1.0 window).

- 2026-07-17 admin/steward surfaces groom — 2 promoted (chat captures + the fired
  launcher-line trigger): admin configuration page w/ generated enforcement matrix →
  **O12** (user decisions: CI last-run metadata; secrets .env-only so config renders
  verbatim); power-user manual-mapping stewardship screen (job→application, FID, ALIAS;
  gate-bound manual-loads changesets, zero graph writes; new steward persona) → **O13**.
  Wireframes wf-admin-config-01.* + wf-mapping-01.*; launcher-registry config-file
  migration still inboxed.

- 2026-07-17 site-plan groom — 4 promoted (O8–O11, Epic O phase 12), 2 inbox lines closed:
  - [idea] **UI DECISION: single-track ReUI, Salt DROPPED** (user call) + site plan
    (`UI-WIP/site-plan.md`: system-default 3-state theming dark-first, radial-hub landing,
    one module-subpage template × 9 modules, QuerySpec registry + two-path Neo4j
    data-frame export with provenance manifest/classification banners) → **O8** (shell +
    theme + routes), **O9** (landing + Explorer template), **O10** (Lineage canvas),
    **O11** (QuerySpec + export, module drydocs-api). Existing modules used — the plan's
    `drydocs-ui` module suggestion superseded (registry already names drydocs-web).
  - [idea] UI-stack proposal 2026-07-17 (ReUI free + React Flow + ADK 2.0 compat; Salt
    two-track addendum) → subsumed: stack table = site-plan §1; Salt track dropped by the
    same-day decision; ADK enablers (mcp.reui.io, @reui/skills-claude, AG-UI notes)
    preserved in site-plan §1 + memory. Site-plan §4 backend caveat corrected at groom:
    ADR 0005 ratified + drydocs-api shipped (O5), export endpoints land there.
- 2026-07-16 evening groom, part 2 (user decisions on the same-day [source] line) —
  2 promoted / 1 plan change (user-approved) / housing executed in-session:
  - PLAN CHANGE: new **phase 14 "Document ingestion & doc-graph benchmarks"** + **Epic Q**
    — the docmeta landing zone (AskUserQuestion-approved; the phase-12/13 idiom). The
    docmeta plan's P1+ phases groom here once the P0 verdict + docmeta ADR land.
  - [source] Essential GraphRAG (Manning / Neo4j-sponsored ebook, Bratanič & Hane,
    179 pp) → **Q1** (mine for applicable patterns at chapter level → docmeta P0 verdict
    input; answers "are there more examples of how to do it properly?") + **Q2**
    (Document→Chunk lexical-graph load + >=5-question agent-traversal experiment —
    vocabulary-reusing per the 07-08 bmc-docs gate, no new gate; target DB drydocs-vs-
    ddcontext decided at execution). HOUSING EXECUTED with the groom (user decisions:
    gitignore, publicly available): root-level `/*.pdf` blanket rule (root-images
    precedent; tracked UI-WIP/*.pdf unaffected) + reference/research/README.md seed-table
    row (Manning link verified 2026-07-16).
  - kept-updated: the docmeta plan line — phase 14 / Epic Q recorded as the landing zone
    for its P1–P3 promotions.

- 2026-07-16 evening groom (third run today; bare /groom-backlog, no new notes) —
  0 promoted / 1 inboxed / 0 merged; backlog database untouched (todo 23 / done 71 stand
  as of acf0bfe):
  - inboxed: `Essential-GraphRAG.pdf` found untracked at repo root (Manning / Neo4j-sponsored
    ebook, 179 pp, file dated 07-14) → new [source] line above — registration + housing
    (commit vs cite+gitignore) is a user decision; joins the JPMC annual-report PDFs in the
    untracked-root-PDF class noted at the 07-16 am groom.
  - all other lines kept parked, unchanged — every recorded gate was checked twice earlier
    today (am weekly run, pm post-merge run at acf0bfe); nothing has landed on main since.

- 2026-07-16 pm groom (second run today, post cmdline-lineage-review + the K4-branch merge) —
  2 promoted / 2 retired-executed / 1 line-update:
  - [idea] 2026-07-15 ETLProcess writer endpoint class (lineage vocab gate residual; the
    business-key half decided + implemented extractor-side at cmdline-lineage-review) →
    **G12**. [idea] 2026-07-15 writer file-ops resolution (same gate's second residual;
    endpoints per the gate EDIT: ETLProcess|ControlMJob → DataAsset) → **G13**. Both are
    the pre-flip curated-load-build blockers; shapes gate-confirmed so no HITL surface
    remains — sonnet items with written acceptance.
  - retired to this trail (fully executed/decided in-session, gate-log
    cmdline-lineage-review): the 07-16 [bug] CMDLINE parser gaps line (all four gaps
    closed same day: control-keyword stripping, runScript.sh -g pset payload expansion +
    case-fix, java/.jar + DPL rules, air rule; sanitized twins pinned) and the 07-16
    [question] gate-agenda line ((a)–(d) all decided; cross-machine reconcile with the
    07-15 vocab gate recorded at the b3c455f merge).
  - line-update: the K2 FID/ALIAS company-side line gains the folder-variable FID+SEAL
    co-location as a candidate FID→seal_id source (side finding from the live captures).
  - kept parked, unchanged: launcher-registry human-configurable (new today — trigger =
    web-console admin surfaces or Phase-E urgency); all other lines on their recorded
    gates (verified this morning, unchanged since).

- 2026-07-16 groom run (weekly inbox groom) — 0 promoted / 0 merged / 1 kept-updated;
  backlog database untouched (summary/next_ready stand as of 2026-07-15):
  - kept-updated: the docmeta plan line — **ADR number collision found + corrected**: the
    plan (2026-07-06) reserved "ADR 0004" for its P1 gate output, but 0004 was minted the
    next day as `0004-software-registry-vendor-terminology.md` (accepted 2026-07-07). The
    docmeta ADR now takes the next free number at authoring; the plan doc's 3 stale refs
    (`knowledge/upgrade-plans/docmeta-component.md` §1.1, P1 phase row, port table)
    annotated in the same commit.
  - gate checks run against the repo this pass: L8 still `todo` → project-review outline
    stays parked; docmeta P0 WRITTEN verdict still absent (only the ADR number changed);
    ADR 0005 ratified + O1/O3/O6 done ≠ any parked trigger.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (L8), K2 FID/ALIAS reconciliation tables (company-side sources), ctlm_id ripple checks
    (internal-side), dry-docs.com visual seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling),
    remediation next slices (TDD §6/§7), Phase C packaging (plan gate), Workbench
    (entitlement), SchedulerKind → AisCapability/AiTool (SME class definitions), BRD
    outline (later phase), docmeta P1–P3 (P0 verdict + the renumbered ADR), EE container
    password (user deferred), LLM key strategy (open question), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).
  - observation (no action): untracked UI-WIP/ website material (WEBSITE-IDEAS.MD,
    gemini-wire-frame.md, landing PNGs, icons.md) predates the 07-13 re-inbox of the
    dry-docs.com line and is its seed corpus when that gate fires; console-side UI-WIP
    files are O-epic surfaces. Root-level JPMC annual-report PDFs also untracked
    (data-context-extractor inputs — house them or gitignore at next touch).

- 2026-07-15 pm groom (on feat/k4-businessapplication-reshape) — 2 promoted, both
  same-day findings from the O6 session's first live EE bootstrap:
  - [bug] `Neo4jClient.run_script` inherits APOC's comment-`;` split (Cypher 25 rejects
    the empty fragment; loaders already guarded by `base.py::_code_semicolons`) → **D5**.
  - [chore] m3-verify fails on bundled samples — active folders 161020/160501 have no
    sample jobs → **D6** (add-jobs vs downgrade-to-warning left either/or, decided at
    execution).
  - groom-touch on **K4**: the branch feat/k4-businessapplication-reshape is reserved for
    it; the remote stub (40fe038, zero own commits, pre-K2) was re-based onto main a683384.

- 2026-07-15 groom run (weekly inbox groom) — 3 promoted / 1 retired (resolved in place):
  - [chore] `controlm-loader-flow.md` → `docs/history/` move (captured same day at the
    controlm docs status-refresh sweep, e3e7bec) → **J11**. Inbound-linker correction made
    during grooming: grep says README.md + the internal governance doc reference it, NOT
    CHECKPOINT/reviews as the inbox line guessed.
  - [chore] schema_graph.cypher stale (generated 2026-06-09, no drift guard; found at the
    K2 build) → **C8** — regenerate-with-guard vs mark-point-in-time deliberately left as
    an either/or in the acceptance, decided at execution (derived view, no gate needed).
  - [chore] session-ritual `python scripts/...` fails outside the venv → **J12**
    (CLAUDE.md ritual lines + snapshot.ps1's two `& python` calls; re-verified live this
    session — render_design_doc.py failed bare, succeeded under `poetry run`). Execution
    caution recorded: CLAUDE.md carried uncommitted user edits at groom time.
  - retired: the 2026-07-13 UI-branch reconcile line — fully RESOLVED in place by its own
    2026-07-14 updates (all UI branches reconciled; the web stream lives entirely on main);
    no item needed, the resolution narrative is preserved in this trail's 2026-07-14 entries.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (trigger = L8 landing the 2nd doc type), K2 FID/ALIAS reconciliation tables
    (company-side sources), ctlm_id ripple checks (internal-side investigation),
    dry-docs.com visual seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL), remediation next slices (TDD §6/§7
    tracks), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind →
    AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P1–P3
    (P0 verdict + ADR 0004), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-15 — [bug] psgmgr version filter domain is `'Y'` not `'1'` — resolved by the
  FINALIZED company Control-M ingestion TDD (captured local-only in
  `internal-local/company-backflow/controlm-ingestion-tdd.md`; their live extracts filter `'Y'`
  and returned the worked-example population). Closes staging-ingestion-flow preflight 0.3 → **D4**.
- 2026-07-14 — [idea] Two support queries proven live on the internal graph (dependency-chain
  finder via undirected `shortestPath` over `WAS_INFORMED_BY`; folder-scoped dependency census,
  ~69% cross-folder stat) — groomed to drydocs-api named endpoints → **O7** (closed same day:
  already shipped by O5's `queries.py`; the note was stale — O5 built them in directly).

- 2026-07-14 groom run (ADR 0005 Action items → Epic O; not an inbox groom) — 4 promoted:
  **O3** ratify ADR 0005 (in_progress — awaiting the SME flip, the E1/P2 idiom; gates the
  rest); **O4** GraphAccess seam refit + dev-flag-gated raw Cypher + credential-rule doc
  (ADR items 2/4/5); **O5** thin-API component scaffold (ADR item 3 — the ADR explicitly
  deferred it to this flow; NEW module `drydocs-api`; fable per the component-boundary
  precedent); **O6** live C4/graph view through the seam (the remaining O1 build; O1
  closes on O3+O6). Ran at the feat/web-login-mock --no-ff merge (design pass onto main).

- 2026-07-13 groom run (weekly inbox groom) — 2 promoted / 1 merged / 1 re-inboxed:
  - [chore] ruff cleanup → CI lint gate (2026-07-11, found executing J5) → **J10** (Epic J,
    phase 8; ready — J5 done and live on main). The user's timing flag preserved in the item
    notes: execute during a port lull, the diff touches every Python file.
  - [idea] artifact-design review sub-item 1 (governed-render-fidelity rule: governed
    surfaces — design-doc renders, gate pages, board — publish VERBATIM; editorial treatment
    only for outward-facing docs) → **L12** (Epic L, phase 10).
  - [idea] artifact-design review sub-item 2 (artifact-design skill's "UI, not a document"
    checklist + AI-default-looks list as the UI-WIP/ review lens) → **MERGED into O1** notes;
    O1 re-tiered opus → fable on the groom touch (G3 policy — the bolt-vs-thin-API call is a
    boundary decision).
  - [idea] artifact-design review sub-item 3 (whitepaper "overnight ledger" identity as the
    dry-docs.com visual seed) → re-inboxed as its own slim line, parked until website work starts.
  - kept parked, unchanged (each on its recorded gate): /documentation whitepaper doc-type
    (trigger "white papers recur" hasn't fired), lineage live-load gate session (HITL —
    groom when the SME schedules it), remediation next slices (TDD §6/§7 tracks), Phase C
    packaging (plan gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool
    (SME class definitions), BRD outline (later phase), docmeta P1–P3 (P0 written verdict +
    ADR 0004), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 rename window).
  - hygiene: deleted the stray empty docs/restructure/IDEAS.md.tmp (interrupted-write leftover,
    0 bytes, untracked).

- 2026-07-11 — /tech-debt documentation audit (docs/reviews/tech-debt-documentation.md) —
  0 promoted / 1 merged / 5 executed with the review / 3 deduped:
  merged: README feature-currency gap → **J2** (title broadened; one README pass).
  executed (D-numbers per the report): D2 login tribal-knowledge doc committed under
  internal/ with classification; D5 MODULE_MAP drift (future-markers on shipped H2/H5
  modules; sme_notes/gate_pages rows added; lineage row = populated); D6 stale cron prompt
  → docs/history/ + banner; D7 root console dump → gitignored internal-local/; D8 tracking
  headers on the two 2026-07-09 tech-debt reports.
  deduped: skill staleness → J4; missing runbook → L8; UI-WIP → O1. Structural verdict:
  clean — all point-in-time reviews banner'd, living docs came through the relocate clean.

- 2026-07-11 groom run (G9-close session; directive: groom the remaining NON-HITL items) —
  2 promoted / 1 merged / 1 inboxed:
  - [idea] G9 tech-debt finding #3 (extractor coverage accounting — stale/nameless/no-target
    skips are silent) → **G11** (drydocs-lineage, phase 6; ready — G9 done). Report, never
    drop: the STG_PARSE_QUALITY / UNMATCHED house rule applied to the candidate side.
  - [idea] G9 tech-debt finding #2 (extractor CSV column contract duplicates controlm_jobs.sql
    aliases as strings, silent-drop on alias rename) → **MERGED into N2** (the SQL SELECT-list
    drift guard gains the extractor as a second consumer of the same list). The 2026-07-10
    tech-debt line is fully dispositioned (#1/#4 fixed same day, #2→N2, #3→G11) and retires.
  - [idea] testcontainers end-to-end CSV→Neo4j load test (parked since 2026-07-01) → **J9**
    (drydocs-load, phase 8; ready — no deps, no HITL surface). Covers the never-executed
    Cypher path; opt-in + Docker-gated so the unit suite is untouched.
  - inboxed: the lineage live-load gate session (HITL-dependent by definition — the Fork-3
    writer's refusal IS the gate; groom when the SME schedules it).
  - kept parked, unchanged (each on its recorded non-HITL-groomable gate): remediation next
    slices (OQ-2/OQ-4 + company-side), Phase C packaging (plan gate), Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME class definitions = HITL), BRD outline (later
    phase, user call), docmeta P1–P3 (P0 written verdict + ADR 0004), EE container password
    (user deferred), LLM key strategy (open user question), common/ in /list-apps (cosmetic),
    cli.py regroup (v1.0 rename window).

- 2026-07-10 groom run (G3-close session) — 0 promoted / 1 inboxed / 1 kept-updated / 0 merged:
  - inboxed: remediation next slices (Tier-2 FR-REM-4 gated on OQ-2/OQ-4; XML I/O on schema
    acquisition; A3/B1 company-side) — deliberately NOT itemized; the TDD §6/§7 tracks them,
    groom when their gates open.
  - kept-updated: the Phase-C packaging line — G3 closed IN-MONOREPO so its early-promotion
    trigger (a) expired unfired; the line waits for Phase C proper.
  - all other inbox lines remain parked on their recorded gates (no change today: Workbench/
    entitlement, SchedulerKind/SME classes, BRD, docmeta/P0-verdict+ADR-0004, container
    password, LLM keys, common/ cosmetic, cli regroup/v1.0 window, testcontainers).
  - backlog database untouched this run (G3/G10 changes landed in-session pre-groom:
    G3 done 46, G10 ready — see commits ca9f165..ef57602).

- 2026-07-09 — [idea] design-doc feedback: per-subsection annotate controls when a section
  has >2 subsections (1.a/1.b/1.c… or steps 1/2/3) so feedback keys to the exact subsection
  → **L11**. (chat note, same review pass as L10; design core = stable derived sub-anchors)
- 2026-07-09 — [idea] design-doc feedback widget: appendix "SME - Feedback" panel (divider +
  static HITL how-to: annotate, Copy feedback, create docs/design/feedback/<doc>-rev<N>.yaml,
  paste, save) → **L10** (amended same day: instruction block, not a free-text notes field).
  (chat note after reviewing docs/design/feedback/scans/; answered the open question — the
  export is .yaml per feedback_yaml, not markdown)
- 2026-07-09 groom run (Opus session) — 4 promoted / 1 retired; web/ became a plan change:
  - [chore] repo `.venv` has no pytest / poetry not on PATH → **RETIRED (resolved this session)**:
    pipx + Poetry 2.4.1 installed, in-project `.venv`, dev deps synced; `poetry run pytest -q`
    → 453 passed / 3 skipped. The documented gate now runs. (See memory `drydocs-python-toolchain`.)
  - [doc] `run-drydocs/SKILL.md` stale Gotchas → **J4** (Epic J, phase 8). Verified 2026-07-09:
    still claims "PyYAML not installed" (×2), "159 pass", Aura, and `apply-m3-supplement` — all stale.
  - [chore] CI (GitHub Actions gates + classification publish-boundary guard) → **J5** (user
    confirmed promote 2026-07-09).
  - [chore] unused deps → **J6** (Epic J), **scoped after verification**: only `streamlit` +
    `streamlit-agraph` are dead; `pandas` is intentional (`csv_adapter.py`) and `pypdf` is now used
    (`scripts/ingest_jpmc_reports.py`) — the original note's "imported nowhere" claim corrected.
  - [idea] web/ front end → **O1** + NEW module `drydocs-web` + NEW **phase 12 "Web console /
    graph visualization"** (plan change, user-approved). Marked in_progress — design pass in flight
    (branches `feature/ui-dark-landing-myapps` + `feat/web-console-design-pass`, untracked `UI-WIP/`).
  - Kept parked: BRD outline (later phase), `drydocs-docmeta` plan (gated on the P0 benchmark verdict
    + ADR 0004), the `<password>` EE container (deferred), LLM-key strategy (open question), `common/`
    in `/list-apps` (cosmetic), cli.py regroup (gated on the v1.0 rename window), and the testcontainers
    integration test (testcontainers[neo4j] confirmed unused; not selected this run).

- 2026-07-09 — [chore] Versioning reset (parked since 2026-07-01) → **J3** (Epic J, phase 8),
  executed same day: adopted SemVer (VERSIONING.md), bumped pyproject 0.1.0 → 0.3.0, back-filled
  CHANGELOG.md from the completed epics, cut annotated tag **v0.3.0** (user decision over v0.2.0 —
  matches plan phase 8's `release:` field). Sibling parked lines (CI, cli.py regroup, unused-dep
  removal, integration tests) stay in the inbox.

- 2026-07-09 groom run (this session) — weekly inbox groom, 2 promoted / 5 retired / 2 kept-updated:
  - [doc] README still says `:DEPENDS_ON` for the derived job→job edge → **J2** (Epic J, phase 8).
    VERIFIED 2026-07-09: the loader `controlm_dependencies_derived.cypher` MERGEs `:WAS_INFORMED_BY`
    and vocab `m3_was_informed_by` is active ("Replaces DEPENDS_ON") — README is the stale side
    (4 refs: README.md:16,139,152,231). Naming-drift doc hygiene, same class as J1.
  - [idea] `REQUIRES_SCHEDULER` (:BatchProcessing → :SchedulerKind) unregistered → **C6** (Epic C,
    phase 2 — re-opened). VERIFIED 2026-07-09 still absent from `relationship_vocabulary.yaml`;
    register `status: planned` + HITL gate before wiring the post-load step (edge-meaning ⇒ gate).
  - [idea] **T1** vendor-doc KG traversal benchmark → SUPERSEDED by the `drydocs-docmeta` plan (its
    P0 spike) AND substantially executed: the bmc-docs lexical loader (Document→Chunk,
    llm-graph-builder) shipped + gate `bmc-docs-lexical-load` ACCEPTED 13/13, LOADED LIVE (commits
    `12423f4`/`24d6a4b`). Written benchmark verdict + ADR 0004 still pending before P1–P3 promote.
  - [source] **T2/T3/T4** internal-platform / product-process / SME-context ingestion → ABSORBED into
    the `drydocs-docmeta` sequenced plan (`knowledge/upgrade-plans/docmeta-component.md`, phases
    P0→P7); tracked there until the P0 verdict + ADR 0004 gate, per the docmeta note's own instruction.
  - [bug] `node_classifications` ControlMFolder-vs-`:JobFolder` drift → CLOSED (already RESOLVED
    2026-07-05, ADR 0003 + rename migration); the struck line is retired from the inbox.
  - kept + updated in-inbox: the `drydocs-docmeta` plan note (records the bmc-docs load; T1–T4 folded)
    and the web/ front-end note (flagged the now-active design-pass branches). Parked pending user
    decisions (semver start, CI, cli.py regroup, unused-dep removal, integration tests), open
    questions (LLM key strategy), and piggyback chores stay in the inbox.


- 2026-07-08 groom run (this session) — **new phase 11 "Source governance ledgers"** + 9 items:
  - [question] SEAL ontology reshape + scraped-docs source-of-record → **K3** (gate session;
    K2 gains `depends_on: K3` — the wasAssociatedWith/Entity type conflict means the reshape
    gate runs before the match-policy gate is ticked). Prep was already on main (`0986d6d`).
  - [bug] design-doc HTML Chrome-vs-Brave render discrepancy → **L9**.
  - [idea] provenance diet + source audit fields (2026-07-05) → **M1–M3** (doc-06 Phases 2–5;
    Phases 0–1 shipped 2026-07-07 pre-groom via gate `controlm-q1q3-phase1` + commit `62673ed`).
  - [idea] property-level ontology terms for the audit envelope (2026-07-07) → **M4**.
  - [question] same-row-derived node relationships (city/state/country, 2026-07-07) → **C5**
    (re-opens phase 2 — methodology gap).
  - [idea] source column mappings (doc 08, 2026-07-07) → **N1–N2** (Phases 0–1 per the plan's
    own groom note; later phases stay in the plan doc).
  - [idea] TechStack software registry (2026-07-07) → CLOSED, executed directly as plan-07
    (Phases 0–2 done `caa1e79`/`eb0fe56`; Phase 3 at the software-usage-patterns gate; Phase 4
    deferred). Not backlog-itemized — the plan doc tracks it; itemize the P3 build when its
    gate passes.
  - [idea] "Application contains folders" support view (2026-07-01 review) → SUPERSEDED by the
    gate-confirmed header-row design (`controlm-q1q3-phase1` + `107581d`): ControlMApplication
    + CONTAINS_FOLDER now load in the folder pass from CM_DEF_VJOB JOB_ID=1 — NOT derived from
    per-job APPLICATION reconciliation as the line proposed (that column stays informational).

- 2026-07-08 — Epic L (**documentation infrastructure**, new phase 10) groomed into `backlog.yaml`
  from the deterministic-documentation design conversation. Canonical per-doc-type outlines (stable
  anchors = the render/traceability/HITL id namespace), md-as-source deterministic render, and the
  digital + pen/paper markup loop. `tdd.outline.yaml` drafted same day (L1 in_progress). New module
  `drydocs-docgen`. Sequence (user-set): TDD (L1) → render/feedback (L3–L7) → Runbook (L8, capstone);
  runbook resequenced from L2 → L8. BRD parked above (later phase). Distinct from the
  `drydocs-docmeta` ingestion idea (2026-07-06).
- 2026-07-01 — [source] seal_app_ref attribution → **K1 + K2** (Epic K, phase 9). CORRECTED
  during grooming by the company reconciliation answers: the edge is spec-level on BOTH sides
  (their FR-NS-013/UC-NS-005 docs read ACTIVE with no loader/vocab/gate behind them); the feed
  is STG_APP_FACT semantic facts, NOT job.APPLICATION (explicitly unreliable for SEAL identity).
  Promoted as build items with the company's write shape, gate sequence, and verify shapes.
- 2026-07-01 — [chore] fragment cleanup (naming drift, banners, SDLC-Docs README) → **J1**
  (Epic J, release-infrastructure) via the groom-backlog skill's demonstration run. Sibling
  lines (versioning reset, CI, cli regroup, unused deps, integration tests) stay in the inbox
  pending user decisions (semver start version, rename window).
- 2026-07-01 — Epic I (I1–I4, project board & planning infrastructure) groomed into `backlog.yaml`
  from the architecture-review plan; schema upgraded to `drydocs.backlog.v2` (I1 done same day).
- 2026-06-20 — initial backlog A1–F2 seeded directly into `backlog.yaml` from `02-backlog.md`.
- 2026-07-09 groom run (remote session) — 8 promoted / 0 inboxed; PLAN CHANGE: new phase 13
  "Runtime topology & maintenance windows" + Epic P (ratify — the phase-12/O1 precedent):
  - CM_HOSTS + CM_AVG_RUN onboarding (add-source-object walkthrough ×2; hosts gate SIGNED OFF
    18/18, avg-run gate awaiting SME) → **P1** (internal probes + DC scope call), **P2**
    (avg-run gate session, in_progress awaiting HITL), **P3** (hosts loader + RUNS_ON
    resolution pass), **P4** (avg-run property-supplement loader + job-name index),
    **P5** (the maintenance-window query — the driving use case).
  - Port-boundary tech-debt audit (docs/reviews/tech-debt-port-boundary.md) → **J7** (per-entry
    reconciler guards) + **J8** (skip-guard policy test); Phase-1 PORT-MANIFEST.yaml + guard
    EXECUTED pre-groom (5cfcfa7) — no item, the doc-06 precedent.
  - Taxonomy-ontology-map audit (docs/reviews/tech-debt-taxonomy-ontology-map.md) → **C7**
    (vocab_id + capture fields at the next gate); F1–F4 fixes EXECUTED pre-groom
    (c396d75, ede0b94).
