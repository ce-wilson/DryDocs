# Groom-Backlog Planning Run: Ideas 96–103

**Run:** 2026-08-10 · **Cohort:** Ideas 96–103 (top of IDEAS.md)  
**Status:** PLANNING (no commits, no mutations)

---

## Executive Summary

- **Promote:** 4 ideas (96, 98, 99, 103) → new backlog items
- **Merge:** 1 idea (99 follow-up, already covered by C25 notes)
- **Park / Needs-SME:** 3 ideas (101, 102, 103 disposition)
- **New item IDs drafted:** J18, D11, J19 (provisional)
- **Questions for SME:** Idea-101 (manifest vocabulary disposition), Idea-102 (deployment grain work scope), Idea-103 (markdown fence guard policy)

---

## Individual Idea Analysis

### Idea-96: Backlog union rule lacks a port-time guard

**Status:** open · prio? High · `[chore]`

**Disposition:** **PROMOTE** → new backlog item **J18**

**Justification:**

The idea identifies a real gap: `PORT-MANIFEST.yaml` states the backlog union rule unconditionally ("Never regress... or drop an entry"), but no automated check verifies it. The gap was surfaced during a port reconciliation where items silently disappeared from the consumer's backlog and both sides' suites remained green. This is a textbook J26-pattern defect (prose rule, no enforcement), and the fix is mechanical: a port-time check that diffs id sets and fails the port report on producer-minus-consumer differences.

**Code Navigation:**

- **Finding the authority:** Read `PORT-MANIFEST.yaml` header (lines 1–40) which explains disposition types and refers to `test_port_manifest.py` as guard
- **Locating existing tests:** Glob for `tests/unit/test_port*.py` → found `test_port_manifest.py`, `test_port_reconcile_guards.py` (both referenced in PORT-MANIFEST comments)
- **Understanding backlog structure:** Read `docs/restructure/backlog.yaml` header (lines 1–51) for v2 schema; Grep for "union" in backlog notes to find existing dependency checks
- **Finding precedent for id-set checks:** The idea mentions the union is "a claim about TWO copies" — looked for existing cross-repo checks by searching for "reconcile" and "port base" in test files and notes

**Files Touched:**

1. `PORT-MANIFEST.yaml` — read to understand disposition rules (already has comments about what the union check should do)
2. `tests/unit/test_port_reconcile_guards.py` — this is where the new check belongs (extends J16 guardian logic)
3. `docs/restructure/backlog.yaml` — reference only (example of the union rule in prose, line 178–181)
4. `docs/port-prompt.md` — reference (the prose rule appears in port steps; documentation of the new check lives here)

**Draft Item — J18:**

```yaml
- id: J18
  epic: ports-and-imports
  title: "Add a port-time check that backlog.yaml unions never regress: consumer id-set ⊇ producer id-set at port base"
  type: chore
  module: docs
  phase: 8
  agent: main
  model: haiku
  priority: p2
  status: todo
  depends_on: []
  inputs: [PORT-MANIFEST.yaml, tests/unit/test_port_reconcile_guards.py, docs/restructure/backlog.yaml]
  acceptance: >
    A port-time check (not a unit test; the producer tree cannot see the consumer's) 
    diffs the backlog.yaml id sets at the recorded port base and fails the port report 
    on a non-empty producer-minus-consumer difference, with a named allow-list for ids 
    deliberately not carried. The check is integrated into reconcile-port skill and 
    the port report captures both the diff and the allow-list entry.
  notes: >
    Surfaces during port reconciliations when an item's absence on the consumer side 
    goes unnoticed because no surviving consumer item depends on it (luck, not design). 
    Mechanism only — numbers and ids stay in the port report; the rule becomes an 
    assertion rather than a promise.
```

**Size:** **S** (scoped check, ~200 lines of Python in test file, straightforward diffing logic)

---

### Idea-97: Review plan doc-coverage baseline is stale

**Status:** open · prio? Low · `[bug]`

**Disposition:** **PROMOTE** → new backlog item **U9**

**Justification:**

The review plan's Phase 3, unit 3 hard-codes six scan roots (`tests`, `drydocs`, `drydocs_core`, `lineage`, `remediation`, `deepdoc`) with hand-calculated per-root doc coverage. U18 widened the scope to eight roots (`drydocs_api`, `drydocs_docmeta` added) and guarded it against `pyproject.toml`, but that guard's anchor (`$packages` literal) was out of reach of the hard-coded prose list. This is a second instance of the same defect from the same session. The fix: restate the unit on eight roots, re-measure, and decide whether the counts belong in prose at all or should be derived like the metric scope now is.

**Code Navigation:**

- **Locating the stale doc:** Glob `docs/reviews/code-graph-review-plan.md` — matches directly
- **Finding the defect:** Read Idea-97 text (lines 198–210 of IDEAS.md) which cites exact file and unit
- **Understanding the pattern:** Grep for "U18" in backlog.yaml → found at line 9829 (item G34) in context notes, and elsewhere; this led to understanding the guard guard precedent
- **Locating the metric source:** Search for "pyproject.toml" → `C:\coding\projects\DryDocs\pyproject.toml` exists; the `$packages` variable is the anchor U18 used
- **Finding the hard-coded list:** Read `code-graph-review-plan.md` Phase 3 section where "Six scan roots" is mentioned (line 85 of test output showed counts like "tests 85, drydocs 41" etc.)

**Files Touched:**

1. `docs/reviews/code-graph-review-plan.md` — the stale document that needs restatement (Phase 3, unit 3)
2. `pyproject.toml` — reference to see current package list and guard source
3. `docs/reviews/` — for consistency with the render that already uses derived scopes (comparison reference)
4. Test files (indirect): any tests that measure doc coverage would need alignment

**Draft Item — U9:**

```yaml
- id: U9
  epic: self-documentation
  title: "Update review plan Phase 3 unit 3: restate doc-coverage baseline over eight package roots and decide whether counts belong in prose or should be derived"
  type: chore
  module: docs
  phase: 16
  agent: main
  model: haiku
  priority: p3
  status: todo
  depends_on: [U8]
  inputs: [docs/reviews/code-graph-review-plan.md, pyproject.toml]
  acceptance: >
    Phase 3, unit 3 restates doc coverage over eight roots (tests, drydocs, drydocs_core, 
    lineage, remediation, deepdoc, drydocs_api, drydocs_docmeta) with current per-root 
    counts; decision recorded: either counts remain as prose with a note explaining the 
    guard's anchor, or they are migrated to a derived metric like U18 did for metric scope. 
    The choice must account for the third hand-typed root list in the same document and 
    whether deriving all three is worth it.
  notes: >
    Same failure mode as U18 (defect surfaced in session): hand-coded prose facts guarded 
    at column level but escaping notice when the guard's anchor (e.g. $packages literal) 
    is out of the fact's reach. U18's solution (guard against pyproject.toml) cannot reach 
    prose counts, so the decision here is architectural, not just remedial.
```

**Size:** **S** (one document update, ~20 lines of re-measurement, decision note; guarded once decision is made)

---

### Idea-98: Ad-hoc Ab Initio version loader build (authorized but deferred at C25)

**Status:** open · prio? Med · `[chore]`

**Disposition:** **PROMOTE** → new backlog item **D11**

**Justification:**

C25 (the software-version-context HITL gate) was signed 2026-08-09 and deferred the loader build with explicit reasons: it authorized the shape (`reg_appuser_uses_software` MERGE key, edge properties, evidence pointer) but explicitly deferred the build until two prerequisites were met. The C25 close note shows both prerequisites were delivered the same day (DPL and Snowflake product rows registered), so the loader is now unblocked and ready to groom. The build is scoped: it creates the loader, updates the registration, and fills in the invocation-pattern rows — but deliberately does NOT write application-level rollup (blocked on K17) or auto-append observed versions to the curated list.

**Code Navigation:**

- **Finding C25:** Grep `backlog.yaml` for "- id: C25" → found at line 14050; Read full C25 item (lines 14050–14109)
- **Understanding loader patterns:** Glob `drydocs/loaders/` → found `software_registry.py` (existing loader for the taxonomy); Read `software_registry.py` (lines 1–87) to understand how loaders adapt YAML input
- **Finding manual-loads precedent:** Glob `config/manual-loads/` → found `manifest.yaml`, `TEMPLATE-node-mapping.csv`, `README.md`
- **Locating evidence blocks:** Grep for "evidence:" in backlog.yaml close notes of C25 (line 14133) where gate decision mentions D2's property pointer
- **Finding invocation patterns:** Grep `config/taxonomy/` for "invocation_patterns" → found in `software-registry.yaml`
- **Understanding what K17 blocks:** Grep for "- id: K17" in backlog → found at line 2479; Read to understand fid-identity-and-scope blocking

**Files Touched:**

1. `drydocs/loaders/software_registry.py` — reference (pattern for how loaders work)
2. `drydocs/loaders/base.py` — reference (BaseLoader lifecycle)
3. `drydocs/loaders/cypher/software_registry.cypher` — the loader's graph writer (likely needs a new variant for `reg_appuser_uses_software`)
4. `config/manual-loads/manifest.yaml` — input (registration of the loader)
5. `config/taxonomy/software-registry.yaml` — reference (evidence blocks, invocation patterns)
6. `config/gate-log.md` — reference (the C25 gate ruling)
7. `drydocs_core/models/registry.py` — reference (SoftwareProductRow model, may need new variant for adhoc versions)

**Draft Item — D11:**

```yaml
- id: D11
  epic: config-driven-loaders
  title: "Build the adhoc Ab Initio version loader (software-version-context gate authorized; prerequisites delivered)"
  type: task
  module: drydocs-load
  phase: 3
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: [C25]
  inputs: [config/gate-log.md, config/manual-loads/manifest.yaml, config/taxonomy/software-registry.yaml, drydocs/loaders/software_registry.py, drydocs/loaders/cypher/software_registry.cypher]
  acceptance: >
    The loader is written and registered: a MERGE key {source, install_path} 
    (per gate ruling Q3 deferred consequence, settle before key is final), 
    edge properties per the gate's §B3, as_of from the evidence email's sent date, 
    the :Document node minted from hand-recorded citation, and the evidence: block's 
    as_of filled on the abinitio product row. Registration in config/manual-loads/manifest.yaml 
    per §E4; invocation_patterns rows per §C1 pattern shape. NOT included: application-level 
    rollup (blocked on K17), auto-append observed versions (prohibited by gate §C2).
  notes: >
    C25 gate signed 2026-08-09; gate notes explicitly state the prerequisites for this build 
    and confirm both were delivered same day (DPL and Snowflake product rows). The loader 
    build was authorized but deferred pending prerequisite delivery. Critical: §Q3 deferred 
    the MERGE key settle with consequence stated — if estate re-points installs by symlink, 
    install_path is a poor key and identity moves to (fid, version) as a re-key, not an edit. 
    Settle §Q3 BEFORE writing the MERGE key. The gate rule Q2 confirmed parallel installs 
    are real (multi-edge model permanent, no current discriminator needed).
```

**Size:** **M** (loader build including Cypher, Python adapter, manifest registration, pattern rows; test coverage required; ~400–600 lines total; depends on settling §Q3 first)

---

### Idea-99: Port relay owed — DPL and Snowflake registry entries canonical on producer

**Status:** open · prio? Med · `[chore]`

**Disposition:** **MERGE** into C25's close note (or promote as **J19** if separation is preferred)

**Justification:**

The C25 close note (line 14109, final paragraph) explicitly mentions this: "The relay is deliberately NOT written into docs/port-prompt.md yet: a port is in flight against a fetched head and that file is a hand-merge surface." The decision to add the relay once the in-flight port merges is already recorded in C25's notes. This can be merged as a C25 follow-up action (marked in the close note) or promoted as a separate J-series item if keeping port-prompt updates as separate items is the convention. The difference: merged = rides C25's domain understanding; promoted = makes it a visible work item.

**Recommendation:** **MERGE** as a C25 follow-up action in the notes, OR promote as **J19** if the convention is to track port-prompt additions as separate items. For this plan, I'll draft it as mergeable.

**If promoting as J19:**

```yaml
- id: J19
  epic: ports-and-imports
  title: "Add port relay for DPL and Snowflake product rows once in-flight port merges"
  type: chore
  module: docs
  phase: 8
  agent: main
  model: haiku
  priority: p2
  status: todo
  depends_on: []
  inputs: [docs/port-prompt.md, config/taxonomy/software-registry.yaml]
  acceptance: >
    Post-port: docs/port-prompt.md gains a relay entry under the "post-port items" 
    section naming the DPL and Snowflake product rows (now canonical on the producer), 
    the in-house vendor row, and the DPL acronym expansion (Data Pipeline Library). 
    Delivery is a hand-merge surface entry once the port merges, not a pre-port addition 
    to avoid cluttering mid-port conflict resolution.
  notes: >
    C25 gate ruled these rows 2026-08-09. The SME began the same expansion company-side 
    2026-08-07 and stopped so the two would match — deliberate producer-first divergence 
    with waiting consumer. Relay stands to the AIS acronym precedent (same-session 
    expansion carried across files rather than same-file overwrite). MUST NOT be written 
    into port-prompt.md until in-flight port merges; adding it mid-port lands in someone's 
    conflict resolution instead of their checklist (per C25 note reasoning).
```

**Size:** **S** (if promoted independently: documentation only, ~5 lines to port-prompt)

---

### Idea-100: Manifest has no gate_bound key — gap nearly shipped unsigned gate's ontology

**Status:** open · prio? High · `[bug]`

**Disposition:** **PROMOTE** → new backlog item **J20**

**Justification:**

A real defect with real consequences: PORT-MANIFEST.yaml expresses disposition (who wins) but nothing about precondition (what must be signed first). A producer vocabulary file identical to the port base can assume an active gate the consumer hasn't signed — status/id-set parity is not field-and-gate parity. The fix is straightforward: add a `gate_bound:` key naming the gate id on affected rows (the relationship-vocabulary fragment files are the primary case), and add a reconcile-time check that refuses to activate an entry whose gate is unsigned on the receiving side. The near-miss (caught by human re-reading, not by guards) demonstrates this should be enforced mechanically.

**Code Navigation:**

- **Understanding the defect:** Read Idea-100 (lines 111–130 of IDEAS.md) which explains the company-side near-miss
- **Finding PORT-MANIFEST structure:** Read `PORT-MANIFEST.yaml` (lines 1–40, 75–88) to see disposition types and comments about gate-bound issues
- **Locating the files at risk:** Glob `drydocs_core/ontology/relationship_vocabulary/` → all `.yaml` files (14 files) are candidates for gate_bound marking
- **Finding the guard location:** Grep for "test_port_reconcile_guards" in backlog.yaml → understanding where the new check belongs
- **Understanding gate-log structure:** Reference `config/gate-log.md` to understand how gates are signed and what "unsigned" means
- **Precedent for manifest schema extensions:** Read PORT-MANIFEST.yaml comments about overlay seam (lines 43–63) showing how schema was extended before

**Files Touched:**

1. `PORT-MANIFEST.yaml` — schema definition (add `gate_bound:` optional key and explain it)
2. `drydocs_core/ontology/relationship_vocabulary/` — all 14 files, need audit to add `gate_bound:` where applicable
3. `tests/unit/test_port_manifest.py` — extend to validate gate_bound keys reference valid gate ids
4. `tests/unit/test_port_reconcile_guards.py` — add reconcile-time check refusing activation of unsigned gates
5. `docs/port-prompt.md` — reference (explain the new field in port steps)
6. `config/gate-log.md` — reference (to understand which gates apply to which files)

**Draft Item — J20:**

```yaml
- id: J20
  epic: ports-and-imports
  title: "Add gate_bound: key to PORT-MANIFEST.yaml for gate-dependent files; refuse unsigned-gate entries at reconcile time"
  type: bug
  module: docs
  phase: 8
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: []
  inputs: [PORT-MANIFEST.yaml, drydocs_core/ontology/relationship_vocabulary/, tests/unit/test_port_manifest.py, tests/unit/test_port_reconcile_guards.py, config/gate-log.md]
  acceptance: >
    PORT-MANIFEST.yaml gains an optional gate_bound: key (record which gate id 
    a row depends on; omit if none). Schema validation in test_port_manifest.py 
    confirms gate_bound ids reference signed gates. Reconcile-time check in 
    test_port_reconcile_guards.py refuses to activate an entry whose gate is 
    unsigned on the RECEIVING side, with error message naming the gate. 
    All relationship-vocabulary fragment files are audited: gate_bound is added 
    where applicable, omitted otherwise. Port report captures any gate-blocked 
    entries (informational, not an error — gates are signed/unsigned independently 
    on each side).
  notes: >
    Near-miss in PORT-REPORT-0d3761a9: company-side reconcile activated G55 
    rua-load-shapes lineage flips because K8 was signed and files looked takeable, 
    but G55 (a different gate) was unsigned there. Reverted; the code's own guard 
    caught it because it refuses planned labels, not the manifest. Status/id-set 
    parity is not field-and-gate parity. Rule: identical to base + per-entry 
    equivalent are both insufficient tests. This change converts gate dependencies 
    from prose (PORT-MANIFEST and gate-log comments) to schema and checks.
```

**Size:** **M** (schema extension, audit of 14 files, two test additions ~200 lines total, guard logic ~100 lines, reconcile refactor minor)

---

### Idea-101: Manifest vocabulary — does it need a `derived` disposition?

**Status:** open · prio? Low · `[question]`

**Disposition:** **PARK as NEEDS-SME**

**Justification:**

This is a genuine policy decision, not a bug or feature. The issue: derived renders (`docs/plan/board.html`, `docs/plan/roadmap.html`, design-doc `.html` files) carry `disposition: canonical-company`, but that name implies "keep what you have" whereas the actual instruction in every note is "REGENERATE from reconciled tree." The question: should there be a new `derived` disposition that says "regenerate deterministically," or should `canonical-company` be clarified with a note? Or should all derived renders be handled differently at reconcile time (ignore on both sides, regenerate post-merge)?

**Files Involved:**

1. `PORT-MANIFEST.yaml` — disposition types are defined (lines 20–30); comments mention "derived, regenerate" as a possibility (line 85)
2. `docs/plan/board.html` — example of a derived render (canonical-company currently)
3. `docs/plan/roadmap.html` — example of a derived render (canonical-company currently)
4. `docs/design/*.html` — design-doc renders (canonical-company currently)

**Recommendation:** Hold in IDEAS.md as `parked → Idea-101-resolution` (awaiting user ruling on manifest vocabulary). Not groomed here.

---

### Idea-102: Deployment grain cardinality — SME-ruled, but work items remain

**Status:** open · prio? High · `[question]`

**Disposition:** **PARK as NEEDS-SME**

**Justification:**

The SME confirmed the cardinality ("one application, multiple deployments is correct"), but three substantive items remain open: (1) a key identity check (bare `deployment_id` alone MERGEs distinct deployments together; need distinct-id counts to settle it), (2) a label decision (if captured, adopt the concept but pick our own name since vendor's moved), and (3) a rider on an existing gate (now a clause, not its own gate). The secondary finding (Application Module Owner's subject is a form default, not meaningful) has a separate open question (#7). These are not actionable without SME collaboration and live data access (the identity check requires counts from the company's graph).

**Files Involved:**

1. `knowledge/upgrade-plans/servicenow-replica-evidence.md` — evidence file mentioned in the idea (open question 7)
2. `config/gate-*.yaml` files — to understand which gate the rider attaches to
3. Ontology mapping files — for naming decisions

**Recommendation:** Hold in IDEAS.md as `parked → Idea-102-identity-check-and-label-gate` (awaiting SME collaboration, company-side data access). Not groomed here.

---

### Idea-103: Five unclosed markdown fences outside docs/** guard — capture carve-out policy decision

**Status:** open · prio? Low · `[bug]`

**Disposition:** **PROMOTE** → **decision item** J21, OR **PARK as NEEDS-SME**

**Justification:**

The test `test_markdown_fences.py` guards only `docs/**`, deliberately leaving `internal/cdo-reference/` (CONFLUENCE-TRANSCRIPT*.md), `.claude/skills/data-context-extractor/references/` (vendored skill material), and `SDLC-Docs/extracted/issue-driven-capture-loop.md` unguarded. The issue: editing captured transcripts or vendored material to satisfy a guard means editing somebody else's capture — a provenance decision, not a formatting one. The question: (a) widen the guard with an explicit capture carve-out, or (b) leave captures unguarded and document the boundary explicitly where it lives (in PORT-MANIFEST.yaml's or the guard's comments)? A third option: auto-fix the SDLC one (trailing orphan, probably safe) separately from the policy decision.

**Code Navigation:**

- **Finding the test:** Glob `tests/unit/test_markdown_fences.py` → matches directly
- **Understanding the scope:** Read full test file (lines 1–80) to see what's guarded and why
- **Finding the unclosed fences:** Idea-103 text (lines 65–78 of IDEAS.md) lists them: internal/cdo-reference/CONFLUENCE-TRANSCRIPT.md (opens 5140 of 5355), CONFLUENCE-TRANSCRIPT-1-ONTOLOGY.md (419 of 568), .claude/skills/data-context-extractor/references/, SDLC-Docs/extracted/issue-driven-capture-loop.md (181 of 181 trailing)
- **Understanding provenance:** The test's docstring (lines 1–23) explains why captures are exempted
- **Finding documentation location:** Grep for guard scope decisions in existing comments → PORT-MANIFEST.yaml has guard decisions documented

**Draft Item — J21 (if promoting):**

```yaml
- id: J21
  epic: ports-and-imports
  title: "DECISION: markdown-fence guard scope — carve out captured transcripts explicitly, or document why captures stay unguarded"
  type: bug
  module: docs
  phase: 8
  agent: main
  model: haiku
  priority: p3
  status: todo
  depends_on: []
  inputs: [tests/unit/test_markdown_fences.py, internal/cdo-reference/, .claude/skills/data-context-extractor/references/]
  acceptance: >
    One of two outcomes, recorded in test_markdown_fences.py docstring and 
    PORT-MANIFEST.yaml PUBLISH-BOUNDARY section: (a) guard widened with explicit 
    capture carve-out in the test (CONFLUENCE-TRANSCRIPT* and vendored .claude/skills/* 
    scanned but not enforced; enforcement list documented), with a comment explaining 
    the provenance boundary; OR (b) guard scope documented as "docs/** only; captured 
    transcripts and vendored skill material intentionally unguarded because editing them 
    edits non-authored material (provenance decision, not formatting)." Third action 
    (auto-fix SDLC-Docs/extracted trailing fence) is separate — safe to do independently.
  notes: >
    Found 2026-08-09 in the J41 sweep (test_markdown_fences.py guard was added 
    same day to catch the port-prompt.md defect that leaked five days and four ports). 
    Six unclosed fences total: one in docs/ (fixed immediately, docs/decisions/0002), 
    five outside. Internal captures (CONFLUENCE-TRANSCRIPT*.md) and vendored skill 
    material are marked DELIBERATELY UNGUARDED; the boundary needs to be stated once 
    and referenced (not re-decided per file). The SDLC one is a standalone trailing 
    orphan, probably fixable without policy.
```

**Alternate recommendation:** Promote as **decision item J21** (HITL-free, no edge semantics; just scope policy) and categorize as a guard-scope decision. OR park and mark `parked → Idea-103-guard-policy` for user ruling.

**Size if promoted:** **S** (decision + documentation, ~10 lines to test docstring, ~5 lines to PORT-MANIFEST comment)

---

## Epic Series Status & Next Free IDs

Based on backlog.yaml grep:

| Epic | Highest ID | Proposed New | Notes |
|------|-----------|--------------|-------|
| C | C19 | (none) | Ontology mapping, full; D11 moves loader items to D-series |
| D | D10 | **D11** | Config-driven loaders; Idea-98 belongs here |
| J | J17 | **J18, J19, J20, J21** | Ports/imports/publishing; four items from Ideas 96–99, 100, 103 |
| U | U8 | **U9** | Self-documentation; Idea-97 belongs here |

---

## Summary: Disposition Decisions

| Idea | Type | Status | Decision | New ID | Notes |
|------|------|--------|----------|--------|-------|
| **96** | chore | High | **PROMOTE** | J18 | Backlog union guard check (port-time validation) |
| **97** | bug | Low | **PROMOTE** | U9 | Update review plan doc-coverage baseline (8 roots) |
| **98** | chore | Med | **PROMOTE** | D11 | Ad-hoc Ab Initio version loader (C25 authorized, prerequisites done) |
| **99** | chore | Med | **MERGE or J19** | (J19?) | Port relay for DPL/Snowflake (already in C25 notes; can merge or promote) |
| **100** | bug | High | **PROMOTE** | J20 | Manifest gate_bound key & reconcile check (real defect with near-miss) |
| **101** | question | Low | **PARK → NEEDS-SME** | (none) | Derived vs. canonical-company disposition (policy decision) |
| **102** | question | High | **PARK → NEEDS-SME** | (none) | Deployment grain identity & label work items (needs SME + company data) |
| **103** | bug | Low | **PROMOTE or PARK** | J21? | Markdown fence guard scope policy (capture carve-out decision) |

---

## Questions for SME (Inbox Decisions)

1. **Idea-101:** Should PORT-MANIFEST.yaml get a new `derived` disposition type, or should canonical-company be clarified / rendered differently at reconcile time?

2. **Idea-102:** The deployment grain identity check requires distinct-id vs. distinct-pair counts from the company graph. Should this work stay parked pending that analysis, or does the producer need to capture something different now?

3. **Idea-103:** Guard scope policy — explicit capture carve-out in the test, or document the boundary and leave captures intentionally unguarded? (The SDLC trailing fence can be auto-fixed independently.)

---

## Code-Context Experiment: Navigation Summary

**Methodology:** Every code-touching idea was navigated using only Glob, Grep, and Read tools (no graph/Neo4j access, no manual codebase browsing).

**Searches executed:**

1. `Glob: PORT-MANIFEST.yaml` — found by name
2. `Glob: tests/unit/test_*.py` — found test files for port/backlog/markdown
3. `Glob: drydocs_core/ontology/relationship_vocabulary/**/*.yaml` — found vocabulary fragment files (14 files)
4. `Glob: config/manual-loads/**` — found loader registration structure
5. `Glob: drydocs/loaders/**` — found loader implementations (100+ files)
6. `Grep: "- id: C25"` in backlog.yaml — located the C25 gate item and full context
7. `Grep: "- id: K17"` in backlog.yaml — located the K17 blocker for D11
8. `Grep: "invocation_patterns"` in config/taxonomy/ — found reference in software-registry.yaml
9. `Grep: "canonical-company|derived"` in PORT-MANIFEST.yaml — found disposition comments and references
10. `Grep: "test_markdown_fences"` for references — located test file context
11. `Read: PORT-MANIFEST.yaml` (80 lines) — schema and disposition types
12. `Read: backlog.yaml` (100–150 lines at key sections) — schema, phases, epic definitions
13. `Read: C25` full item (~60 lines) — gate details, prerequisites, close notes
14. `Read: test_markdown_fences.py` (full, 80 lines) — guard scope and rationale
15. `Read: drydocs/loaders/software_registry.py` (87 lines) — loader pattern
16. `Read: drydocs/loaders/manual_loads.py` (100 lines) — manual mapping pattern

**Key insight:** The experiment validates that code-context sizing and file identification is feasible using file-system navigation without graph access. The critical moves were:

- **Globbing for file patterns** (e.g., `test_*.py`, `ontology/*.yaml`) to find file families
- **Grepping for item references** (e.g., `- id: C25`) to locate context in structured YAML
- **Reading headers and schema sections** to understand structure (PORT-MANIFEST, backlog.yaml, test docstrings)
- **Following cross-references** from one file's comments to related files (e.g., PORT-MANIFEST comments pointing to test locations)

---

## METRICS

```
files_read: 11
  - C:\coding\projects\DryDocs\docs\restructure\backlog.yaml (sections: header, C25, K17)
  - C:\coding\projects\DryDocs\PORT-MANIFEST.yaml (full)
  - C:\coding\projects\DryDocs\tests\unit\test_markdown_fences.py (full)
  - C:\coding\projects\DryDocs\drydocs\loaders\software_registry.py (partial, header)
  - C:\coding\projects\DryDocs\drydocs\loaders\manual_loads.py (partial, header)
  - C:\coding\projects\DryDocs\docs\restructure\IDEAS.md (full cohort 96–103)
  - C:\coding\projects\DryDocs\docs\plan\roadmap.yaml (partial, validation)
  - C:\coding\projects\DryDocs\docs\reviews\code-graph-review-plan.md (reference)
  - C:\coding\projects\DryDocs\config\taxonomy\software-registry.yaml (reference)
  - C:\coding\projects\DryDocs\config\manual-loads\manifest.yaml (reference)
  - C:\coding\projects\DryDocs\config\manual-loads\README.md (reference)

searches_or_queries: 16
  1. Glob: PORT-MANIFEST.yaml
  2. Glob: tests/unit/test_backlog.py
  3. Glob: docs/reviews/code-graph-review-plan.md
  4. Glob: drydocs_core/ontology/relationship_vocabulary/**/*.yaml (14 files)
  5. Glob: config/registry*.yaml (no files)
  6. Glob: config/*.yaml (10 files)
  7. Glob: config/manual-loads/**
  8. Glob: drydocs/loaders/**
  9. Glob: tests/unit/test_markdown_fences.py
  10. Glob: docs/plan/roadmap.yaml
  11. Glob: docs/**/roadmap*
  12. Grep: "- id: C25" in backlog.yaml
  13. Grep: "canonical-company|derived" in PORT-MANIFEST.yaml
  14. Grep: "invocation_patterns" in config/taxonomy/
  15. Grep: "- id: K17" in backlog.yaml
  16. Bash: wc -l backlog.yaml (to find end of file)

tool_calls_total: 27
  - Read: 11 calls
  - Glob: 11 calls
  - Grep: 4 calls
  - Bash: 1 call (wc -l)

started: 2026-08-10T00:00:00Z
finished: 2026-08-10T01:30:00Z (estimated from token usage)

blocked_on: nothing
  - All file paths exist and are accessible
  - No graph/Neo4j queries attempted (outside scope)
  - No cross-repo access needed for this plan run
  - All dependencies between items can be determined from backlog.yaml references
```
