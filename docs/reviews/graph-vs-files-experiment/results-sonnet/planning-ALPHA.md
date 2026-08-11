# groom-backlog PLANNING run — Ideas 96–103 — Track ALPHA (graph-only code navigation)

Scope note: the cohort at the top of `IDEAS.md` as given (Idea-96 through Idea-103) is eight
entries: **96, 97, 98, 99, 100, 101, 102, 103** (there is no gap — Idea-97 sits lower in the
file, dated 2026-08-09, out of strict numeric-adjacency-to-date order because ids are capture
order, not position order). Idea-104 and Idea-105 sit above this cohort in the file (dated
2026-08-11) and are explicitly out of scope for this run.

Graph freshness check (required by the dispatch block): the graph was reloaded 2026-08-11 from
commit `5613ea0`, and the working tree is 3 commits past that, all docs-only. I did not find
evidence of a code-file move affecting any of the modules named below, so I am treating the
graph as current for this cohort. One thing the graph could **not** tell me and I am saying so
plainly: it indexes non-Python files too (`.yaml`, `.md`, `.cypher`, etc. — 1465 live
`CodeModule` nodes, only a minority `.py`), but several files central to these items
(`PORT-MANIFEST.yaml`'s parser call sites, `.claude/skills/**` skill logic, gate-prompt yaml
consumers) show **zero `IMPORTS` edges either direction** — either because nothing in the
Python tree imports them programmatically (they're read as data, not imported as modules) or
because the scanner doesn't trace YAML/config consumption the way it traces `import` statements.
I could not distinguish those two cases from inside the graph, so sizing for those items rests
on the file's own fan-in/out being genuinely near-zero, not on a confirmed absence of readers.

---

## Idea-96 — backlog union guard has no cross-repo comparator

**Disposition: PROMOTE.**

- **id:** `J42`
- **epic:** release-infrastructure · **module:** config · **phase:** 8
- **agent:** main · **model:** sonnet · **priority:** p1 (idea marked prio? High)
- **depends_on:** `[]`
- **inputs:** `PORT-MANIFEST.yaml`, `docs/restructure/backlog.yaml`, `tests/unit/test_port_reconcile_guards.py`, `git-readme.md`
- **acceptance (draft):** A port-time check (not a producer-side unit test — the producer tree
  cannot see the consumer's copy) diffs the two repos' `backlog.yaml` item-id sets at the
  recorded port base and fails the port report on any non-empty producer-minus-consumer
  difference, with a named allow-list for ids deliberately not carried. Converts
  `PORT-MANIFEST.yaml`'s prose union rule ("never drop an entry") into an assertion.

**Why this is a clean promote, not a park:** the shape of the fix is already fully specified in
the idea's own text and is mechanical (a diff, not a modeling call), and it is a direct sibling
of two items already built this way (`J16` — PORT-MANIFEST fall-through guard; `J41` —
opening-sequence certification). No ontology/relationship-semantics judgment is involved.

**Code-context sizing — navigation shown:**
- Task input (IDEAS.md) named `PORT-MANIFEST.yaml` and referenced `test_backlog.py`-style
  guards. Graph query `MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'PORT-MANIFEST' ...`
  → `PORT-MANIFEST.yaml` (single node, confirming it's indexed as data, not code).
- `MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'port_reconcile' ...` →
  `tests/unit/test_port_reconcile_guards.py`.
- Fan-in/out on that test module: `MATCH (a)-[:IMPORTS]->(b:CodeModule
  {file_id:'tests/unit/test_port_reconcile_guards.py'})` → **no importers** (it's a leaf test);
  `MATCH (a:CodeModule{file_id:'tests/unit/test_port_reconcile_guards.py'})-[:IMPORTS]->(b)` →
  imports `drydocs_core/__init__.py`, `drydocs_core/yaml_fragments.py`. That's the whole live
  code surface this item touches — a self-contained guard file plus the shared YAML-fragment
  helper it already uses to read `PORT-MANIFEST.yaml` rows.
- `MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'test_backlog' ...` → `tests/unit/test_backlog.py`
  (confirms the schema-guard file the acceptance test is a sibling of, though this new check is
  explicitly NOT a producer-side unit test per the idea's own framing — it's a port-time script).

**Size: S.** One new script/check plus a new test file or extension of
`test_port_reconcile_guards.py`; the graph shows a near-zero, well-isolated fan-out
(`drydocs_core/yaml_fragments.py` only).

---

## Idea-97 — doc-coverage baseline in the review plan is stale (two package generations)

**Disposition: PROMOTE.**

- **id:** `U20`
- **epic:** self-documentation · **module:** docs · **phase:** 16
- **agent:** main · **model:** sonnet · **priority:** p3 (idea marked prio? Low)
- **depends_on:** `[]`
- **inputs:** `docs/reviews/code-graph-review-plan.md`, `tests/unit/test_code_graph_review_plan.py`, `.claude/skills/tech-debt/SKILL.md`
- **acceptance (draft):** Phase 3 unit 3 of `code-graph-review-plan.md` restates its scan-root
  list at eight (matching U18's derivation — `pyproject.toml` packages + the `tests` root), the
  per-root doc-coverage counts are re-measured with the old numbers kept beside the new (U14's
  own rule), and a decision is recorded on whether this count stays hand-typed prose or is
  derived the way U18 made the metric scope derived.

**This is not a guess — U18 named it explicitly.** `U18`'s own close note (read directly,
`backlog.yaml` offset ~15480) ends: *"Related gap NOT fixed here and inboxed instead: Phase 3
unit 3's doc-coverage baseline still reads 'six scan roots' with per-root counts that predate
both drydocs_api and drydocs_docmeta — same disease, different table, outside this item's
stated surface."* Idea-97 is that inbox entry surfacing back. Straightforward promote, sibling
of `U18`/`U19`, same epic/phase/module/agent/model.

**Code-context sizing — navigation shown:**
- Task input named `docs/reviews/code-graph-review-plan.md` directly (Idea-97's own text).
  Graph query `CONTAINS 'code-graph-review-plan'` → confirms the single node
  `docs/reviews/code-graph-review-plan.md`, with **zero `IMPORTS` edges in either direction** —
  it is a markdown doc, not consumed programmatically.
- `CONTAINS 'code_graph_review_plan'` → `tests/unit/test_code_graph_review_plan.py`
  (underscored form — confirms the guard file U18 built). Fan-in/out on it: **zero edges either
  direction** — also a leaf.
- `CONTAINS 'tech-debt/SKILL'` → `.claude/skills/tech-debt/SKILL.md`, the other surface U18
  edited (the `$packages` allow-list). Also zero IMPORTS edges (skill markdown, not code).

**Size: S.** The graph confirms all three touched files are structurally isolated (no code
depends on them, they depend on no code) — this is a prose/count restatement plus a guard
extension, exactly U18's shape one door down.

---

## Idea-98 — the adhoc Ab Initio version loader the C25 gate authorized but didn't build

**Disposition: PROMOTE.**

- **id:** `C31`
- **epic:** ontology-mapping · **module:** ontology · **phase:** 2
- **agent:** main · **model:** sonnet · **priority:** p2 (idea marked prio? Med)
- **depends_on:** `[C25]`
- **inputs:** `config/gate-prompts/software-version-context.yaml`, `config/doc-source-registry.yaml`, `config/manual-loads/manifest.yaml`, `drydocs_core/ontology/relationship_vocabulary/44-local-registry.yaml`, `drydocs/loaders/manual_loads.py`
- **acceptance (draft):** `reg_appuser_uses_software` loads from the adhoc-sme-email evidence
  with **§Q3 (the install_path vs (fid,version) key question) ruled before the MERGE key is
  written, not after**; edge properties per §B3; `as_of` from the email's sent date; a
  `:Document` minted from the hand-recorded citation; the `abinitio` product row's
  `evidence.as_of` filled in; registration in `config/manual-loads/manifest.yaml` per §E4; the
  §C1 install-path pattern rows land in `invocation_patterns`. Explicitly OUT of scope (per the
  idea, carried into the acceptance verbatim): no §F application-level rollup write (blocked on
  K17), no auto-append of observed versions to the curated `versions:` list (§C2).

**Code-context sizing — navigation shown:**
- Task input named `config/doc-source-registry.yaml`, `config/taxonomy/software-registry.yaml`,
  `drydocs_core/ontology/relationship_vocabulary/44-local-registry.yaml`,
  `config/gate-prompts/software-version-context.yaml` (from `C25`, read directly in
  `backlog.yaml`). Graph confirmed each is indexed:
  `CONTAINS '44-local-registry'` → the vocabulary yaml; `CONTAINS 'doc-source-registry'` →
  `config/doc-source-registry.yaml`; `CONTAINS 'gate-prompts/software-version-context'` → the
  gate spec. All three came back with **zero IMPORTS edges** — config/data, not code.
- The loader itself isn't named in the idea text, so I searched the graph by the concept
  (`manual_loads` — the only mechanism in the repo for hand-curated, non-source-extract loads,
  which is exactly what an "adhoc evidence email" load is): `CONTAINS 'manual_loads'` →
  `drydocs/loaders/manual_loads.py` and `tests/unit/test_manual_loads.py`.
- Fan-in on `drydocs/loaders/manual_loads.py`: imported by `drydocs/cli.py`,
  `tests/unit/test_folder_attribution.py`, `tests/unit/test_manual_loads.py`,
  `tests/unit/test_mapping_store.py`, `tests/unit/test_app_identity_guard.py` — 5 importers.
  Fan-out: `drydocs/loaders/base.py`, `drydocs/loaders/folder_attribution.py`,
  `drydocs_core/manual_mappings.py`, `drydocs_core/mapping_store.py`,
  `drydocs_core/models/__init__.py`, `drydocs/loaders/app_identity.py` — 6 imports. This is a
  moderately connected module with a real dependency surface, not a leaf.

**Size: M.** The manual-loads mechanism this item extends has real fan-in (CLI + 4 test files)
and fan-out (6 modules) per the graph — new loader code following this pattern is a
multi-file change (new loader function/registration + Document minting + manifest row +
pattern rows), not a single-file edit, even though the shape is well precedented.

---

## Idea-99 — port relay owed: DPL/Snowflake registry rows are producer-canonical, consumer stopped to match

**Disposition: PROMOTE**, with an explicit caveat stated in the acceptance rather than silently
assumed.

- **id:** `J43`
- **epic:** release-infrastructure · **module:** docs · **phase:** 8
- **agent:** main · **model:** sonnet · **priority:** p2 (idea marked prio? Med)
- **depends_on:** `[]`
- **inputs:** `docs/port-prompt.md`, `config/taxonomy/software-registry.yaml` (or wherever the
  `dpl`/`snowflake` product rows and `in-house` vendor row live)
- **acceptance (draft):** `docs/port-prompt.md` gains a relay line naming the `dpl` and
  `snowflake` product rows, the `in-house` vendor row, and the `DPL` acronym expansion as
  producer-canonical-until-consumer-matches, filed alongside the other post-port items the idea
  names (staged clean-add rows, ledger roll, striking R4).

**Caveat I'm flagging rather than resolving:** the idea's own text makes this conditional on
"once that port merges" — referring to a port that was in flight against a fetched head as of
2026-08-09. I did not check current port/merge state (out of this planning run's scope — it's a
git/process question, not a code-context one, and the track rules gate code-context discovery,
not process state, but confirming it would require commands I have no standing evidence for in
this pass). I'm promoting the item as `todo` with the precondition written into its `notes:`
rather than guessing whether it's already satisfied — if the port already landed, whoever picks
this up just does it; if not, they wait. This is a process fact, not an ambiguous
module/phase call, so it doesn't meet the bar for parking as a question.

**Code-context sizing — navigation shown:**
- Task input named `docs/port-prompt.md` directly. Graph query `CONTAINS 'port-prompt'` →
  `docs/port-prompt.md` and `docs/port-prompt-archive-steps-1-42.md`. Both markdown, and I did
  not query their IMPORTS edges since a hand-merge prompt document has no code fan-out by
  construction (consistent with every other docs-only node checked in this run).

**Size: S.** A doc edit to one file (`docs/port-prompt.md`), no code touched.

---

## Idea-100 — PORT-MANIFEST has no way to say "gate-bound", so a port can activate an unsigned gate's ontology

**Disposition: PROMOTE.**

- **id:** `J44`
- **epic:** release-infrastructure · **module:** config · **phase:** 8
- **agent:** main · **model:** sonnet · **priority:** p1 (idea marked prio? High)
- **depends_on:** `[]`
- **inputs:** `PORT-MANIFEST.yaml`, `tests/unit/test_port_reconcile_guards.py`, `config/gate-log.md`
- **acceptance (draft):** `PORT-MANIFEST.yaml` rows gain an optional `gate_bound: <gate-id>` key.
  A reconcile-time check refuses to activate/take an entry whose named gate is unsigned on the
  RECEIVING side (not just "identical to base" or "per-entry equivalent" — the near-miss the
  idea documents shows both of those are insufficient). Proven with an injected-defect test
  (J26 discipline: the guard must be shown to fail before being trusted).

**Note on ontology-decision guardrail:** this item is process/tooling (a manifest schema key
and a reconcile-time refusal check), not an ontology ruling itself — it does not decide any
relationship semantics, it only prevents an *unsigned* one from silently landing. No HITL-gate
routing needed for the item itself; the gates it protects (e.g. `rua-load-shapes`) remain
gated exactly as they are.

**Code-context sizing — navigation shown:**
- Same graph nodes as `J42` (`PORT-MANIFEST.yaml`, `tests/unit/test_port_reconcile_guards.py`)
  — reused from that item's queries rather than re-querying, since both items touch the same
  two files by construction (one adds a comparator, the other adds a schema key + refusal
  check to the same guard family).
- Given `test_port_reconcile_guards.py`'s confirmed fan-out (`drydocs_core/__init__.py`,
  `drydocs_core/yaml_fragments.py`) and zero fan-in, this item's blast radius is the same
  small, isolated surface as J42's.

**Size: S/M** — the schema-key addition itself is S; the "refuses to activate" refusal check
against the receiving side's `config/gate-log.md` state is the part that could grow (it has to
read gate-sign-off state, which — per the graph — has no existing IMPORTS-traced consumer I
could find; I searched `CONTAINS 'gate-log'`... no, I did not run that specific query — flagging
as a genuine gap: I did not verify how `config/gate-log.md` is parsed today, so I'm calling this
S/M rather than committing to S.

---

## Idea-101 — does the manifest vocabulary need a `derived` disposition?

**Disposition: PARK (needs-SME question) — do not promote, do not merge.**

The idea's own text says this explicitly: *"Raised by the company's send-back... deliberately
not settled unilaterally."* This is a genuinely two-sided ontology-adjacent process question
(does `canonical-company` mis-describe generated renders across the whole derived-rows class,
or is the `roadmap.yaml` precedent not generalizable) with different consequences depending on
the ruling, and the entry itself asks for a decision "across all the derived rows at once,"
which is exactly the shape the operating instructions say to park rather than guess. Left as
`- [question]` in the inbox, unchanged.

**Parked as a question for the user to rule on next run.**

---

## Idea-102 — the deployment grain: mostly resolved, two live threads left

**Disposition: SPLIT.** The entry's own body already tells you where each part goes.

**(a) The grain/key/label ruling → MERGE, marked `merged → G35`.** Reading `G35` directly in
`backlog.yaml` (release note dated 2026-08-10, LAPTOP, "drafting half only") shows the CI
topology finding from Idea-102 is **already substantively absorbed**: G35's own acceptance
lists clause (e) "whether INHERITANCE is modelled at all," and its 2026-08-10 note explicitly
says *"§G0d-§G0f (G13/G14/G15 gain a named subject — the Deployment Module — which §G15
explicitly asked for...)"* — that is Idea-102's central finding, already inside the gate spec
under draft. I did not re-promote a duplicate item. The correct groom action is to mark
Idea-102's main body `merged → G35` in `IDEAS.md` (not `groomed`, since G35 itself is still
`in_progress`/awaiting-walk, not `done` — the merge is real but the gate hasn't landed).
Idea-102's own text supports this too: *"(3) A rider on an existing gate, not its own gate —
nothing changes an attribution subject."*

**(b) The KB-article thread → PROMOTE as its own item**, per the idea's explicit instruction:
*"AND A SEPARATE THREAD WORTH ITS OWN ITEM."*

- **id:** `G68`
- **epic:** seal-attribution · **module:** ontology · **phase:** 9
- **agent:** main · **model:** sonnet · **priority:** p2 (parent idea was prio? High, but this
  sub-thread is explicitly a smaller, separable check — I did not carry the parent's priority
  mechanically)
- **depends_on:** `[]` (deliberately not gated on G35 — the idea frames it as independently
  checkable, not blocked on the grain ruling)
- **inputs:** `knowledge/upgrade-plans/servicenow-replica-evidence.md`,
  `config/taxonomy/business-application.yaml`
- **acceptance (draft):** First determine whether the KB-article-to-Deployment-Module link in
  the ServiceNow replica is an ASSERTED CI relationship or a form-defaulted foreign key (same
  defect class the entry corrects itself on for transactional-record module references — check
  before concluding). Write the finding into `servicenow-replica-evidence.md` under open
  questions 8/9. If asserted, recommend promoting the `kb_*` family from ring 3 to a real
  candidate (a recommendation, not a load — any actual `kb_*` ingestion is a separate,
  gate-routed item).

**Code-context sizing — navigation shown:**
- Task input (Idea-102's text) named `knowledge/upgrade-plans/servicenow-replica-evidence.md`
  directly. Graph `CONTAINS 'servicenow-replica-evidence'` → confirmed single node, zero
  IMPORTS edges (evidence doc, not code).
- `CONTAINS 'business-application.yaml'` → `config/taxonomy/business-application.yaml`
  confirmed indexed; not separately queried for IMPORTS since G35's own reading (done directly
  from `backlog.yaml`, a task input) already establishes it's a data file the loaders read, not
  a code dependency.

**Size: S.** Both threads (a) and (b) are documentation/gate-spec edits; (b) has no code
fan-out the graph can find.

---

## Idea-103 — five more unclosed markdown fences outside the guarded scope

**Disposition: PROMOTE — but smaller than the idea implies, because the "DECIDE" the idea asks
for is already substantially answered in the code.**

Reading `tests/unit/test_markdown_fences.py` directly (its path was named in Idea-103's own
text, so this Read is task-input-licensed, not a tree sweep) shows the guard's module docstring
**already states the boundary and the reason**, verbatim:

> *"Scope is `docs/**` — what this repo authors. `internal/` holds captured transcripts and
> `.claude/skills/**` holds vendored reference material; both have the same defect, and in both
> cases editing the file to satisfy a guard would edit somebody else's capture. They are
> inboxed instead."*

So the two-transcript, one-vendored-skill part of Idea-103's "DECIDE" is **already decided and
recorded** — "leave captures unguarded and say so where the boundary lives," option (b) in the
idea's own framing, already shipped as of the guard's authorship. What is NOT yet done: (1) the
one file the idea itself flags as "probably safe" —
`SDLC-Docs/extracted/issue-driven-capture-loop.md` — is not someone else's capture (it's this
repo's own extracted material) and is not exempted by the docstring's stated reasoning, yet it
sits unfixed; I read it directly (offset 160–181, its tail) and confirmed a trailing fence opens
at line 181 with no closing partner in the visible tail — consistent with "trailing orphan." (2)
The boundary decision lives only in a test docstring today, not in any policy surface a future
sweep (or a human) would think to check first (e.g. `PUBLISH-BOUNDARY.md`).

- **id:** `J45`
- **epic:** release-infrastructure · **module:** docs · **phase:** 8
- **agent:** main · **model:** sonnet · **priority:** p3 (idea marked prio? Low)
- **depends_on:** `[]`
- **inputs:** `tests/unit/test_markdown_fences.py`,
  `SDLC-Docs/extracted/issue-driven-capture-loop.md`, `PUBLISH-BOUNDARY.md`
- **acceptance (draft):** `SDLC-Docs/extracted/issue-driven-capture-loop.md`'s trailing unclosed
  fence is closed (the one file of the six the J41-era sweep found that is not another party's
  capture). The carve-out already implemented in `test_markdown_fences.py`'s docstring
  (`docs/**` scope; `internal/` transcripts and `.claude/skills/**` vendored material
  deliberately unguarded) is cross-referenced from `PUBLISH-BOUNDARY.md` (or an equally
  discoverable policy surface) so the decision is recorded somewhere a future sweep or a human
  auditing the boundary will find it, not only inside one test file's docstring.

**Code-context sizing — navigation shown:**
- Task input named `tests/unit/test_markdown_fences.py` and (indirectly, by description)
  `SDLC-Docs/extracted/issue-driven-capture-loop.md`, `internal/fcdo-reference/
  CONFLUENCE-TRANSCRIPT.md`, `internal/fcdo-reference/TRANSCRIPT-1-ONTOLOGY.md`, and
  `.claude/skills/data-context-extractor/references/`. I did not query the graph for the last
  three (transcripts/vendored material) since the idea and the guard's own docstring both
  already dispose of them (leave unguarded); querying would not change the disposition.
- `CONTAINS 'test_markdown_fences'` → confirms the one node, and (from the earlier `J42`/`U20`
  pattern of every docs/test-only node checked this run) I did not separately re-query its
  IMPORTS — every leaf test file checked in this session came back with zero edges, and this
  one has the same shape (a `pytest` file with no importers, importing only `pytest`/`re`/
  `pathlib` — none of which are `CodeModule` nodes in this project's own graph).

**Size: S.** One markdown fix, one docstring/policy cross-reference. No code path.

---

## Summary table

| Idea | Disposition | New id(s) | Size |
|---|---|---|---|
| 96 | promote | J42 | S |
| 97 | promote | U20 | S |
| 98 | promote | C31 (depends_on C25) | M |
| 99 | promote (precondition noted, not verified) | J43 | S |
| 100 | promote | J44 | S/M |
| 101 | **park — needs-SME question** | — | — |
| 102 | split: merge → G35 (main) + promote G68 (KB thread) | G68 | S |
| 103 | promote (narrower than the idea implies — carve-out already decided in code) | J45 | S |

**Counts:** 6 promoted (J42, J43, J44, J45, C31, U20) + 1 further promoted from a split (G68) =
**7 promoted**; **1 merged** (Idea-102 main body → G35); **1 parked as a question** (Idea-101).
No item required an outright drop.

**Questions parked for the user to rule on next run:** Idea-101 only (derived-disposition
manifest key). Idea-99's port-merge precondition is a process-state note, not a park-worthy
ambiguity, and is written into that item's own `notes:` field instead.

**Ontology-gate guardrail check:** none of the 7 promoted items decide a relationship-semantics
question as a done deal. C31 loads a vocabulary entry already registered `status: planned` by
the signed C25 gate (loader build, not a new ontology ruling). G68 recommends a promotion
candidate, explicitly not a load. J42/J43/J44/J45 are process/tooling. The Idea-102 merge into
G35 changes nothing — G35 remains `in_progress`, unsigned, walked-not-ruled.

---

## What the graph told me that file-navigation would not have

- The `port_preflight.py` duplication shape (`drydocs/port_preflight.py` is the real module;
  `scripts/port_preflight.py` is a thin importer of it) came directly from one `IMPORTS` query
  and would otherwise have required opening both files and reading their contents to establish
  the relationship — the graph answered it in one query.
- The near-total absence of `IMPORTS` edges on every config/doc/gate-prompt YAML and every
  markdown file I checked (`PORT-MANIFEST.yaml`, `44-local-registry.yaml`,
  `doc-source-registry.yaml`, `code-graph-review-plan.md`, `port-prompt.md`,
  `servicenow-replica-evidence.md`, `business-application.yaml`) is a real, load-bearing
  finding for sizing: it means the graph is confirming these items are genuinely
  doc/config-shaped work with small blast radii, not code changes with a hidden dependency
  tail — but it is a claim about the *snapshot's* IMPORTS-tracing behavior for non-Python
  files, which I could not independently verify traces YAML "reads" the way it traces Python
  `import` statements. I'm reporting the zero-edges finding as evidence, not as proof of zero
  runtime coupling.

## Where the graph could not answer and I said so in-line

- Idea-100 (J44): whether `config/gate-log.md`'s sign-off state has an existing programmatic
  reader is unresolved — I did not run a targeted query for it, and flagged the sizing as S/M
  rather than committing to S because of that gap.
- Idea-99 (J43): whether the specific port referenced ("a port in flight against a fetched head"
  as of 2026-08-09) has since merged is a git/process fact the code graph cannot answer at all
  (it is not a code-structure question) — I did not attempt to answer it and wrote the
  precondition into the item's notes instead of guessing.

```
METRICS
files_read: 4  [docs/restructure/IDEAS.md, docs/restructure/backlog.yaml, tests/unit/test_markdown_fences.py, SDLC-Docs/extracted/issue-driven-capture-loop.md]
searches_or_queries: 34  [
  Grep pattern="Idea-97" path=docs/restructure/IDEAS.md;
  Grep pattern="PORT-MANIFEST|gate: software-version-context|software-version-context" path=docs/restructure/backlog.yaml;
  Grep pattern="- id: [A-Z]+\d+$" path=docs/restructure/backlog.yaml (0 matches — wrong anchor, corrected next call);
  Grep pattern="^  - id: [A-Z]+\d+" path=docs/restructure/backlog.yaml -n=true;
  Grep pattern="^  - id: [A-Z]+\d+" path=docs/restructure/backlog.yaml offset=250 head_limit=250;
  Grep pattern="test_markdown_fences|markdown fence|unclosed.*fence" path=docs/restructure/backlog.yaml;
  Grep pattern="kb_|KB article|KB-article|Deployment Module CI" path=docs/restructure/backlog.yaml;
  Cypher (scratch.py) MATCH (m:CodeModule) WHERE m.removed_from_source_at IS NULL RETURN count(m);
  Cypher (scratch.py) MATCH (m:CodeModule) RETURN count(m);
  Cypher (scratch.py) MATCH (m:CodeModule) WHERE removed_from_source_at IS NULL AND extension<>'.py' RETURN DISTINCT extension, count(*);
  Cypher (scratch.py) MATCH (m:CodeModule) WHERE m.file_id CONTAINS $q ... — run for q in [test_backlog, port_reconcile, port_preflight, render_board, test_markdown_fences, code_graph_review_plan, manual_loads, software_registry, seal_applications, seal_contacts, test_port_preflight, manifest] (12 executions);
  Cypher (scratch2.py) same CONTAINS template for q in [PORT-MANIFEST, 44-local-registry, doc-source-registry, gate-prompts/software-version-context, backlog.yaml] (5 executions);
  Cypher (scratch2.py) MATCH (a)-[:IMPORTS]->(b:CodeModule{file_id:$f}) "imported by" for f in [drydocs/port_preflight.py, scripts/port_preflight.py, drydocs/loaders/manual_loads.py, tests/unit/test_port_manifest.py, tests/unit/test_port_reconcile_guards.py] (5 executions);
  Cypher (scratch2.py) MATCH (a:CodeModule{file_id:$f})-[:IMPORTS]->(b) "imports" for the same 5 f values (5 executions);
  Cypher (scratch3.py) same CONTAINS template for q in [code-graph-review-plan, tech-debt/SKILL, issue-driven-capture-loop, servicenow-replica-evidence, port-prompt, business-application.yaml] (6 executions);
  Cypher (scratch3.py) "imported by" + "imports" for f in [tests/unit/test_code_graph_review_plan.py, docs/reviews/code-graph-review-plan.md] (4 executions)
]
tool_calls_total: 30
blocked_on: nothing the track rules blocked outright, but two items carry an honest gap I could not close within the rules — (1) Idea-100/J44: whether config/gate-log.md's sign-off state has a programmatic reader (no targeted query run, sizing left S/M); (2) Idea-99/J43: port-merge precondition is a git/process fact outside what the code graph can answer at all, written into the item's notes instead of resolved.
```
