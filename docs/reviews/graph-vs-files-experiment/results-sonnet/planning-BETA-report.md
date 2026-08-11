# Groom Plan — Idea-96 through Idea-103 (Track BETA / files-only navigation)

Planning run only. Nothing committed, nothing edited in the repo except this
report and its duplicate. No git-mutating commands were run. No Neo4j/Cypher
access was used (forbidden by track rules) — every finding below comes from
`Read`/`Grep`/`Glob` over the working tree.

Ids allocated below were computed by scanning `backlog.yaml` for the highest
existing id in each epic-letter series (`Grep -o "^  - id: ([A-Z]+)(\d+)"`,
full file). Max-per-letter found relevant to this cohort: `C30`, `J41`,
`K21`, `U19`. Next-free ids used: `C31`, `J42`, `J43`, `J44`, `K22`, `U20`.

---

## Idea-96 — port-time guard for the backlog union rule

**Disposition: PROMOTE.**

`PORT-MANIFEST.yaml` asserts (prose only) that a port must never let the
consumer's `backlog.yaml` item-id set regress below the producer's at the
port base, but nothing checks it — `tests/unit/test_backlog.py` only
validates one copy at a time (schema, roll-up arithmetic, `next_ready`,
`depends_on`). This is a real gap, not a maybe: a port that silently drops
items leaves both trees internally consistent and green.

**Draft item:**
```
id: J42
epic: release-infrastructure
title: "backlog.yaml union rule has no guard: assert producer-minus-consumer id diff is empty (or allow-listed) at each port"
type: chore
module: docs
phase: 8
agent: main
model: sonnet
priority: p1
status: todo
depends_on: []
inputs: [PORT-MANIFEST.yaml, .claude/skills/reconcile-port/SKILL.md, docs/restructure/backlog.yaml, scripts/port_preflight.py]
acceptance: >
  A reconcile-time check (added to .claude/skills/reconcile-port/SKILL.md's
  step sequence, backed by a script) diffs backlog.yaml item-id sets between
  the fetched producer tree at the recorded port base and the local
  (consumer) tree, and FAILS the port report on any producer-minus-consumer
  id that is not in an explicit named allow-list (for ids deliberately not
  carried). This is NOT a unit test — the producer tree cannot see the
  consumer's — so it must run reconcile-side, not in tests/unit/.
notes: >
  From Idea-96 (2026-08-09). Cannot live in tests/unit/test_backlog.py by the
  idea's own reasoning (single-tree visibility). Natural home is beside
  scripts/port_preflight.py (J41's opening-sequence certifier, producer-side)
  but this check is a CLOSING/reconcile-side check — it needs both trees, so
  it likely belongs as a new reconcile-port SKILL.md step rather than an
  extension of port_preflight.py's run_checks(). Confirm that split at build
  time rather than assuming it.
```

**Code-context navigation.** Found via `Grep -n "next_ready:|summary:"` and a
directory read of `.claude/skills/reconcile-port/SKILL.md` (grepped for
`backlog\.yaml|id set|superset|union`) plus `PORT-MANIFEST.yaml` (grepped for
`gate_bound|disposition:` and separately `gate_bound|allow.?list|precondition`
— zero matches for `gate_bound`, confirming Idea-100 below is also unbuilt).
Read `scripts/port_preflight.py` in full (63 lines) to see the existing
opening-sequence-check shape (`run_checks()` in `drydocs/port_preflight.py`,
report-only vs `--tag`) as the closest structural precedent.

**Size: M.** Touches a skill doc (`SKILL.md`), likely a new or extended
Python module (id-diff logic + allow-list schema), and the manifest schema.
No large refactor, but the diff logic itself (fetch producer tree at a named
base, extract ids, allow-list) is new mechanism, not a one-line change.

---

## Idea-97 — code-graph-review-plan.md Phase 3 unit 3 doc-coverage baseline is stale

**Disposition: PROMOTE.** This is the exact gap U18's own close note named and
deliberately left open ("Related gap NOT fixed here and inboxed instead:
Phase 3 unit 3's doc-coverage baseline still reads 'six scan roots'…same
disease, different table"). Confirmed by reading `U18` in `backlog.yaml`
(`Grep -o` id scan located it at line 15480) and by reading
`docs/reviews/code-graph-review-plan.md` lines 55–190 directly: line 64 shows
`$packages` is now **eight** roots (U18, 2026-08-09) while line 181–184 still
says "Six scan roots × DesignDoc coverage" with the old six-root counts
(`tests` 85, `drydocs` 41, `drydocs_core` 35, `lineage` 12, `remediation` 7,
`deepdoc` 3) — predating both `drydocs_api` and `drydocs_docmeta`.

**Draft item:**
```
id: U20
epic: self-documentation
title: "Phase 3 unit 3's doc-coverage baseline is stale — six scan roots, predates drydocs_api and drydocs_docmeta"
type: bug
module: docs
phase: 16
agent: main
model: sonnet
priority: p3
status: todo
depends_on: []
inputs: [docs/reviews/code-graph-review-plan.md, tests/unit/test_code_graph_review_plan.py, pyproject.toml]
acceptance: >
  Phase 3 unit 3 restates its baseline on the eight $packages roots (matching
  U18's widening) with per-root doc-coverage counts re-measured, and either
  derives the root list the same way U18 derived the metrics scope (from
  pyproject.toml [tool.poetry] packages + tests) or states in prose why this
  third instance stays hand-typed. tests/unit/test_code_graph_review_plan.py
  gains (or extends) a guard so the Phase-3 root list and the metrics
  $packages list cannot diverge again — proven to fail on an injected
  six-root regression before being trusted (J26 discipline).
notes: "From Idea-97 (2026-08-09), which is U18's own named residue."
```

**Code-context navigation.** `Grep` for `Six scan roots|DesignDoc coverage` in
`code-graph-review-plan.md` located line 181; a second `Grep` for
`packages|\$packages|eight package roots` in the same file located line 64's
"eight roots since U18" note, confirming the mismatch directly rather than
trusting the idea's prose. `test_code_graph_review_plan.py` was named but not
opened in this pass — flagged as the file the build session must read first.

**Size: S.** One doc section rewrite + re-measurement, one test-guard
extension. Contained to two files.

---

## Idea-98 — the adhoc Ab Initio version loader (build C25 authorized)

**Disposition: PROMOTE.** Verified against `config/gate-prompts/software-version-context.yaml`,
which is `status: signed-off` (read lines 1–40 and 120–239): §B2 confirms the
MERGE key is exactly `{source, install_path}` (line 136), §B3 the edge
properties (line 137), §B4 that `as_of` is the email's sent date (line 138),
§C1 that the path→product pattern rows follow
`config/taxonomy/software-registry.yaml#invocation_patterns`'s existing shape
(confirmed by a second file, `config/gate-prompts/software-usage-patterns.yaml`,
which already uses that exact table for a sibling gate — `id, product, field,
match_type, pattern, example, status`). §Q3 (install-path stability as a MERGE
key) is explicitly **deferred, not answered** (lines 198, 228–231) — the idea
text's instruction to "settle §Q3 before writing the MERGE key" is therefore a
real precondition, not idea color, and belongs in the acceptance test.

**Draft item:**
```
id: C31
epic: ontology-mapping
title: "Build the adhoc Ab Initio version loader the software-version-context gate (C25) authorized"
type: task
module: drydocs-load
phase: 2
agent: main
model: sonnet
priority: p2
status: todo
depends_on: [C25]
inputs:
  - drydocs/loaders/manual_loads.py
  - drydocs/loaders/software_registry.py
  - config/gate-prompts/software-version-context.yaml
  - config/taxonomy/software-registry.yaml
  - config/manual-loads/manifest.yaml
  - config/doc-source-registry.yaml
acceptance: >
  Before the loader is written, §Q3 (is install_path a stable MERGE key, or
  does the estate symlink installs?) is confirmed with the SME and the
  consequence recorded — a "yes" proceeds as drafted, a "no" re-keys to
  (fid, version) instead. Then: the loader MERGEs
  (:AppUser)-[:USES_SOFTWARE {version, version_raw, install_path, source,
  origin, status, as_of, evidence_doc_id}]->(:SoftwareProduct) keyed on
  {source, install_path} (§B2/§B3); the §C1 install-path pattern rows land in
  config/taxonomy/software-registry.yaml#invocation_patterns; the
  adhoc-sme-email :Document corpus is registered/used per §D1-D5; the
  abinitio product row gains the §C5 evidence: pointer block; the load is
  registered in config/manual-loads/manifest.yaml per §E4. The loader does
  NOT write the §F application-level rollup (blocked on K17) and does NOT
  auto-append observed versions to the curated versions: list (§C2).
notes: "From Idea-98 (2026-08-09), the build follow-up C25's own close note named as owed."
```

**Code-context navigation.** Located the two candidate loader files with
`Glob("drydocs/loaders/*.py")` (24 files) and confirmed the manual-load
convention with `Grep("manual-loads|manual_load", path="drydocs/")`, which
returned `drydocs/loaders/manual_loads.py`, `drydocs/loaders/README.md`,
`drydocs/loaders/cypher/manual_seal_attribution.cypher`, `drydocs.cli`, and
`drydocs/loaders/seal_attribution.py` — a real precedent for a manual/adhoc
load pattern to follow. Read `config/manual-loads/manifest.yaml` in full (46
lines) for the registration schema (`file`, `scope`, `status`,
`replaces_with`, `authored_by`, `notes`) referenced in §E4.

**Size: L.** New loader logic (CSV/path parsing + version normalization per
§C3), a new pattern-table entry, a new document corpus registration, a
manifest entry, and a product-row edit — five-plus files, one genuinely new
parsing routine, and one open SME question that gates the MERGE key shape.

---

## Idea-99 — port relay owed: DPL + Snowflake registry entries

**Disposition: MERGE → already satisfied, no new item.** Verified this is
**done**, not owed. `Grep("DPL|Snowflake|snowflake|in-house",
"docs/port-prompt.md")` found `RELAY-5 (was R5) — DPL + Snowflake registry
entries`, and reading lines 743–804 in full shows the relay already carries
everything Idea-98's text asks for: the `dpl`/`snowflake` product rows, the
`in-house` vendor with no `publisher_url`, the `DPL` acronym, the three
riders (value-across-files, `versions: []` deliberate, the publish-boundary
asymmetry), and a correction dated **2026-08-09 pm at PORT-REPORT-6f03264**
showing the company side already reconciled it as a clean add. The relay
even cross-references Idea-100 by name ("A DEFECT IN THAT GUARD WAS FOUND…
it is worth knowing because it is the Idea-100 class"), which places this
entry's writing at or after 2026-08-09 — the same date Idea-99 was captured.

**Recommendation:** mark Idea-99 `groomed → satisfied by RELAY-5 in
docs/port-prompt.md (no new item)` in IDEAS.md rather than promoting or
merging into a live backlog item — the artifact it asked for already exists
and is dated.

**Code-context navigation.** One `Grep` across `docs/port-prompt.md` for the
product names, one full read of the ~60-line relay block. No backlog.yaml
lookup was needed since the relay is a doc-only mechanism (hand-merge
surface per its own text), not a tracked item.

**Size: n/a (no build).**

---

## Idea-100 — PORT-MANIFEST.yaml has no `gate_bound:` precondition key

**Disposition: PROMOTE.** Confirmed genuinely unbuilt: `Grep("gate_bound",
"PORT-MANIFEST.yaml")` returns zero matches (checked twice, with two
different surrounding patterns). The near-miss it describes (G55
`rua-load-shapes` activated on a signed-elsewhere gate, K8) is real and
already referenced from `docs/port-prompt.md`'s RELAY-5 as "the Idea-100
class" of defect, which corroborates the idea's own framing rather than just
restating it.

**Draft item:**
```
id: J43
epic: release-infrastructure
title: "PORT-MANIFEST.yaml rows need a gate_bound precondition key — status/id-set parity is not gate parity"
type: chore
module: docs
phase: 8
agent: main
model: sonnet
priority: p1
status: todo
depends_on: []
inputs: [PORT-MANIFEST.yaml, .claude/skills/reconcile-port/SKILL.md, config/gate-log.md]
acceptance: >
  Rows in PORT-MANIFEST.yaml that assume an active gate (starting with
  drydocs_core/ontology/relationship_vocabulary/**) gain an optional
  gate_bound: <gate-id> key, and the reconcile-port activation logic refuses
  to flip a gate_bound entry active unless the RECEIVING side's
  config/gate-log.md shows that gate id signed-off — "identical to base" and
  "per-entry equivalent" are no longer treated as sufficient on their own for
  a gate_bound row.
notes: "From Idea-100 (2026-08-09), the manifest-side companion to the code-side guard that already caught the near-miss (G23/rua gate-bound refusal)."
```

**Code-context navigation.** Reused the `PORT-MANIFEST.yaml` reads from
Idea-96's investigation (`Grep("gate_bound|disposition:")` and
`Grep("gate_bound|allow.?list|precondition")`) — both zero-result on
`gate_bound`, confirming this is a distinct, still-open gap from Idea-96's
(union superset vs. gate precondition are different failure classes sharing
the same file).

**Size: S.** A manifest schema addition (one new optional key) plus a
refusal check in the reconcile flow. Smaller than J42 because it does not
need a two-tree diff — it only reads the local `gate-log.md`.

---

## Idea-101 — does the manifest vocabulary need a `derived` disposition?

**Disposition: NEEDS-SME. Park as a question**, unchanged from its current
`[question]` tag. The entry itself says it was "deliberately not settled
unilaterally" by the company's send-back, and it is a real either/or with
different consequences: `canonical-company` (keep-what-you-have) vs. a new
`derived`/regenerate disposition changes how EVERY rendered artifact
(`board.html`, `roadmap.html`, design-doc `.html`) is treated on every future
port, and the entry explicitly notes that fixing only the `roadmap.yaml` row
in isolation would create a worse inconsistency than leaving it. This is a
manifest-semantics decision with repo-wide blast radius — not something to
guess into `backlog.yaml`.

**Code-context navigation.** No additional files read beyond the IDEAS.md
entry itself — the entry already cites the precedent it needs
(`roadmap.yaml`'s `evaluate` → `per-entry` fix) and the question is
self-contained.

**Size: n/a (question, not a build).**

---

## Idea-102 — deployment grain: mostly SME-resolved; one residual thread

**Disposition: split.**

**(a) The CI-topology finding (points 1–3 of the entry) — MERGE, no new
item.** Read `G35` in `backlog.yaml` (`epic: seal-attribution`,
`status: in_progress`, claimed on the LAPTOP 2026-08-10) and its gate-prompt
spec, `config/gate-prompts/tom-roles-enumeration-and-cardinality.yaml`. A
`Grep("Deployment Module|deployment_module", ...)` against that file returns
9 hits, including lines 15 and 320–341, which state — in the SAME terms as
Idea-102 — that "the Deployment Module carries its own unique CI id," that
"Business Application [Instantiates] Deployment Module," and that "the
DEPLOYMENT MODULE CI IS REAL." G35's own close note (§G0d–§G0f) already gives
G13/G14/G15 "a named subject — the Deployment Module." Idea-102's points 1–3
are therefore **already captured**, in the same file, on the same date
(2026-08-10), as the gate G35 is drafting. No new item is needed; the correct
action is to mark Idea-102 `merged → G35` for this portion.

**(b) The KB-article thread (point 4) — PROMOTE, genuinely new.** A `Grep`
for `kb_|KB article|knowledge base|deployment module` against BOTH
`config/gate-prompts/seal-tom-attribution-reshape.yaml` (0 hits) and
`config/gate-prompts/tom-roles-enumeration-and-cardinality.yaml` (0 hits on
the KB terms, despite 9 hits on "Deployment Module") confirms this half is
not captured anywhere. It is also the one the idea author explicitly flagged
as "worth its own item."

```
id: K22
epic: seal-attribution
title: "Determine whether KB-article-to-Deployment-Module links are asserted or a defaulted transactional foreign key"
type: task
module: taxonomy
phase: 9
agent: main
model: fable
priority: p2
status: todo
depends_on: [K21]
inputs:
  - knowledge/upgrade-plans/servicenow-replica-evidence.md
  - knowledge/upgrade-plans/servicenow-cmdb-analysis.md
  - config/gate-prompts/tom-roles-enumeration-and-cardinality.yaml
acceptance: >
  An analysis note (paired with K21's servicenow-replica-evidence.md) states,
  from replica evidence, whether a kb_knowledge article's link to a
  Deployment Module CI is an ASSERTED edge or a DEFAULTED foreign key
  inherited from the same transactional-record default Idea-102 documents for
  Changes/Incidents — mechanism only, no real CI/KB ids committed. Nothing
  activated: no source row, no loader, no gate signed inside this item.
notes: >
  From Idea-102 point 4 (2026-08-10 update). Likely a LAPTOP item like K21,
  since it needs the same DBeaver replica evidence (Internal, gitignored,
  laptop-only) — confirm machine assignment at pull time.
```

**Code-context navigation.** Located `C10` and `K21` first by scanning the
`Grep -o "^  - id: ..."` id map, then read both in full (C10: 60 lines, K21:
90 lines) to trace the "gate-bound candidate #1... deferred" language K21's
own close note re-opens and that Idea-102 references. Read `G35` (85 lines)
next because K21's close note says the deployment finding feeds G35/
seal-tom-attribution-reshape. A `Grep` inside
`seal-tom-attribution-reshape.yaml` for Deployment Module terms returned
**zero** hits, which is what sent the search to
`tom-roles-enumeration-and-cardinality.yaml` instead (`Glob("config/gate-prompts/*tom*")`)
— the acceptance text in `backlog.yaml` for G35 names this second file as its
actual output, which the first grep's zero-result made necessary to check.

**Size: (a) n/a — no build. (b) S** — one analysis document, mechanism-only,
no code, but gated on replica access that may only exist on one machine.

---

## Idea-103 — five more unclosed markdown fences outside the docs/** guard

**Disposition: split.**

**(a) The "DECIDE" ask — ALREADY RESOLVED, no SME question needed.** Read
`tests/unit/test_markdown_fences.py` in full (50 lines shown). Its own
docstring (lines 19–22) already states the exact resolution option (b) the
idea proposes: *"Scope is `docs/**` — what this repo authors. `internal/`
holds captured transcripts and `.claude/skills/**` holds vendored reference
material; both have the same defect, and in both cases editing the file to
satisfy a guard would edit somebody else's capture. They are inboxed
instead."* This is option (b) from the idea, already implemented and
rationale-documented in the guard's own file. No new decision is needed —
the "DECIDE" ask is stale; recommend closing this half of Idea-103 with a
pointer to the existing docstring rather than parking it as an open question.

**(b) The one safe trailing-fence fix — PROMOTE (small).** Verified
`SDLC-Docs/extracted/issue-driven-capture-loop.md` is repo-authored planning
content (opens with "Companion to `feasibility-memo-context-sufficiency.md`…
CLAUDE.md §3" — our own cross-references, not a third-party transcript),
unlike the CONFLUENCE-TRANSCRIPT/vendored-skill files the idea correctly
excludes. Read the file head and tail (15 lines each end) to confirm it ends
mid-fence at line 181 of 181.

```
id: J44
epic: release-infrastructure
title: "Close the trailing orphan fence in SDLC-Docs/extracted/issue-driven-capture-loop.md"
type: bug
module: docs
phase: 8
agent: main
model: haiku
priority: p3
status: todo
depends_on: []
inputs: [SDLC-Docs/extracted/issue-driven-capture-loop.md, tests/unit/test_markdown_fences.py]
acceptance: >
  The file's trailing fence is closed (matching CommonMark 4.5, the same rule
  test_markdown_fences.py enforces under docs/**); no other content changes.
  test_markdown_fences.py's scope stays docs/** only — this fix is cosmetic
  correctness on a file the repo authored, not a guard-scope change.
notes: "From Idea-103 (2026-08-10), the one file the idea itself called 'probably safe' — repo-authored, not a vendored/captured transcript."
```

**Code-context navigation.** Read `tests/unit/test_markdown_fences.py` in
full first (it was already open from the Idea-100/PORT-MANIFEST search
chain's file list) via `Grep("84ed7e3|unclosed markdown fence|
test_markdown_fences", "backlog.yaml")` (0 hits — confirmed no existing
backlog item owns this guard) then `Read` on the test file directly. Then
read `SDLC-Docs/extracted/issue-driven-capture-loop.md` head and tail to
confirm authorship and the orphan-fence claim without needing to fix it.

**Size: (a) n/a. (b) S** — one-line fence close in one file.

---

## Summary table

| Idea | Disposition | New id(s) | Size |
|---|---|---|---|
| 96 | promote | J42 | M |
| 97 | promote | U20 | S |
| 98 | promote | C31 | L |
| 99 | merge → already satisfied (RELAY-5) | — | n/a |
| 100 | promote | J43 | S |
| 101 | needs-SME (park, unchanged) | — | n/a |
| 102 | merge → G35 (a) + promote (b) | K22 | n/a / S |
| 103 | already-resolved (a) + promote (b) | J44 | n/a / S |

**Parked as a question for the user:** Idea-101 (derived-disposition
manifest semantics — repo-wide blast radius, company explicitly deferred it).

**Flagged as resolved-in-place, not requiring a groom decision:** Idea-99
(port-prompt.md RELAY-5 already carries it) and Idea-103's guard-scope half
(test_markdown_fences.py's own docstring already documents the boundary the
idea asks the groom to decide).

---

## METRICS

files_read: 9  [docs/restructure/IDEAS.md; docs/restructure/backlog.yaml; config/gate-prompts/software-version-context.yaml; config/manual-loads/manifest.yaml; docs/port-prompt.md; scripts/port_preflight.py; docs/reviews/code-graph-review-plan.md; tests/unit/test_markdown_fences.py; SDLC-Docs/extracted/issue-driven-capture-loop.md]

searches_or_queries: 24
1. Grep `^  - id: T\d+|^  - id: U\d+|^  - id: N\d+` (backlog.yaml)
2. Grep `next_ready:|summary:` (backlog.yaml)
3. Grep `^  - id: [A-Z]+\d+$` (backlog.yaml) — no matches, bad pattern
4. Grep `^  - id: ([A-Z]+)(\d+)` -o (backlog.yaml, full scan, paginated in 2 calls)
5. Grep `install_path|MERGE key|reg_appuser_uses_software|as_of` (software-version-context.yaml)
6. Grep `invocation_patterns` (software-usage-patterns.yaml)
7. Grep `manual-loads/manifest.yaml|invocation_patterns` (backlog.yaml)
8. Glob `config/manual-loads/*.yaml`
9. Glob `**/*invocation_pattern*`
10. Grep `invocation_patterns` (files_with_matches, config/)
11. Glob `drydocs/loaders/*.py`
12. Grep `manual-loads|manual_load` (drydocs/)
13. Grep `DPL|Snowflake|snowflake|in-house` (docs/port-prompt.md)
14. Grep `gate_bound|disposition:` (PORT-MANIFEST.yaml)
15. Grep `def check_|CHECKS|checks =` (scripts/port_preflight.py)
16. Grep `gate_bound|allow.?list|precondition` (PORT-MANIFEST.yaml)
17. Grep `backlog\.yaml|id set|superset|union` (.claude/skills/reconcile-port/SKILL.md)
18. Grep `Six scan roots|DesignDoc coverage|Phase 3 unit 3|tests.*85|drydocs_core.*35` (code-graph-review-plan.md)
19. Grep `packages|\$packages|eight package roots` (code-graph-review-plan.md)
20. Grep `deployment|Deployment Module|G13|G14|G15` (config/gate-prompts/seal-tom-attribution-reshape.yaml)
21. Grep `kb_|KB article|knowledge base|deployment module|Deployment Module` (seal-tom-attribution-reshape.yaml)
22. Glob `config/gate-prompts/*tom*`
23. Grep `Deployment Module|deployment_module|deployment module` (tom-roles-enumeration-and-cardinality.yaml)
24. Grep `84ed7e3|unclosed markdown fence|test_markdown_fences` (backlog.yaml)

tool_calls_total: 43
blocked_on: nothing
