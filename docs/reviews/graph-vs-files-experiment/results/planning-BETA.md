# GROOM PLAN: Ideas 96–103

**Run date:** 2026-08-10  
**Snapshot:** Neo4j `drydocs` database loaded from commit `bd051ab`  
**Method:** Neo4j code-graph queries + backlog schema analysis

---

## Executive Summary

All eight ideas are actionable. Five promote to backlog items; two are gate-rider candidates
(merge into existing gate items); one is a parked decision question. No blocked dependencies.

---

## Per-Idea Analysis

### **Idea-96** · 2026-08-09 · `[chore]` · **prio High**

**Title:** The backlog union rule has no guard

**Disposition:** **PROMOTE** → `J43` (Epic J: release-infrastructure, phase 8)

**Justification:**  
Idea-96 identifies a defect in the port machinery: `PORT-MANIFEST.yaml` unconditionally states
"Union the items; NEVER regress…or drop an entry" for `docs/restructure/backlog.yaml`, but
`tests/unit/test_backlog.py` validates EACH copy in isolation. A port that silently
under-delivers items leaves both sides internally consistent and passing (J26 pattern: a
promise written in prose and enforced by nobody). The fix is a port-time check — not a unit
test, since the producer cannot see the consumer's tree — that diffs id sets at the recorded
port base and fails the port report on `producer-minus-consumer` difference, with an allow-list
for deliberately-not-carried ids.

**Code context** (via Neo4j, discovered at):
- `PORT-MANIFEST.yaml` — queried by file_id, found at line 1 of manifest (project root)
- `tests/unit/test_port_manifest.py` — CodeModule found; IMPORTS `PORT-MANIFEST.yaml` behavior
- `tests/unit/test_backlog.py` — CodeModule found; validates backlog schema in isolation
- `drydocs/port_preflight.py` — preflight machinery; new check will attach here
- `scripts/port_preflight.py` — CLI wrapper for preflight checks

**Sizing:** **M** (medium)  
- Requires: new preflight check (~50–100 lines), test proof case, port-report integration
- Touch points: 3 files (preflight.py, test_port_preflight.py, port-prompt.md runbook)

**Draft Item:**
```yaml
- id: J43
  epic: release-infrastructure
  title: "Port preflight check: backlog item union — producer's id set is a superset of consumer's at port base"
  type: chore
  module: drydocs-load
  phase: 8
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: [J41]  # port opening/closing sequences already done
  inputs:
    - PORT-MANIFEST.yaml
    - docs/port-prompt.md
    - scripts/port_preflight.py
    - tests/unit/test_port_preflight.py
  acceptance: >
    A new preflight check `backlog_union_rule()` diffs backlog item id sets
    (producer at recorded port base vs consumer at HEAD). Non-empty
    producer-minus-consumer fails the port report unless ids are in a named
    allow-list. The check is invoked by `port_preflight.py --tag` and
    decorates the port-report artifact with counts (dropped / allowed / kept).
  notes: >
    Idea-96 gives the defect class and the fix shape; near-miss precedent
    from 2026-08-04 reconcile where the gap was invisible until manual
    read (J26 family: prose promise, nobody enforces). Mechanism only —
    the occurrence's numbers and ids stay in the port report.
```

**Notes on parked decisions:** None; all path choices are mechanism-only.

---

### **Idea-97** · 2026-08-09 · `[bug]` · **prio Low**

**Title:** The review plan's doc-coverage baseline is two package generations stale

**Disposition:** **PROMOTE** → `U19` (Epic U: self-documentation, phase 16)

**Justification:**  
`docs/reviews/code-graph-review-plan.md` Phase 3 unit 3 still cites six package roots
(counts pre-dating both `drydocs_api` and `drydocs_docmeta`). U18 already guarded the
scoped package list in `pyproject.toml` and widened the metric, but this unit hard-codes
its own list in prose — outside the guard's reach. The fix is to restate the unit on
eight roots and re-measure per-root doc coverage. A secondary design question: whether
hand-typed root lists should be derived, given three already exist in the same doc.

**Code context** (via Neo4j):
- `docs/reviews/code-graph-review-plan.md` — found as CodeModule; prose document
- `scripts/render_design_doc.py` — CodeModule found; design doc rendering infrastructure
- `pyproject.toml` — referenced by U18 for package list; source of truth for scope
- `drydocs/design_doc.py` — CodeModule found; doc validation and outline handling

**Sizing:** **S** (small)  
- Requires: count update (~5 package lines), per-root measurement (~20 lines of change)
- Touch points: 1 file (the review plan .md); optional: derivation framework (follow-up)

**Draft Item:**
```yaml
- id: U19
  epic: self-documentation
  title: "Update code-graph-review-plan Phase 3 unit 3: eight package roots, re-measured per-root doc coverage"
  type: bug
  module: docs
  phase: 16
  agent: main
  model: haiku
  priority: p3
  status: todo
  depends_on: [U18]  # U18 established the eight-package scope
  inputs:
    - docs/reviews/code-graph-review-plan.md
    - pyproject.toml
  acceptance: >
    Phase 3 unit 3 lists eight package roots (drydocs, drydocs_core, tests,
    drydocs_load, drydocs_lineage, drydocs_remediation, drydocs_docmeta,
    drydocs_api) with live per-root DesignDoc coverage counts. A design
    decision is recorded (prose list, derived list, or split) for the three
    hand-typed root lists in the document.
  notes: >
    Found during the U18 metric-scope widening. Same defect class as Idea-93:
    stale prose counts when the tooling moved to sourced scope. Derivation
    question is optional follow-up (out of scope for this fix).
```

**Notes:** No gate decisions needed; purely internal documentation hygiene.

---

### **Idea-98** · 2026-08-09 · `[chore]` · **prio Med**

**Title:** The adhoc Ab Initio version loader

**Disposition:** **PROMOTE** → `C29` (Epic C: ontology-mapping; phase 2)

**Justification:**  
C25 (the software-version-context HITL gate, signed 2026-08-09) explicitly deferred the
loader build as a follow-up. The gate signed off on the vocabulary entry
`reg_appuser_uses_software` (status: planned) and the MERGE key `{source, install_path}`;
the loader build is now unblocked. The build must: (1) respect §Q3 (settle install-path
identity before writing the key — deferred at C25 with stated consequence); (2) NOT write
the §F application-level rollup (blocked on K17); (3) NOT auto-append observed versions
to the curated list. Edge properties per §B3; `as_of` from email sent date.

**Code context** (via Neo4j):
- `drydocs/loaders/software_registry.py` — CodeModule found; related loader
- `drydocs/loaders/base.py` — CodeModule found; base loader class; imported by software_registry.py
- `config/taxonomy/software-registry.yaml` — registry config; touched by C25
- `config/manual-loads/manifest.yaml` — loader registration (§E4 references)
- `drydocs/loaders/cypher/` — Cypher templates for loaders; software loader will need a cypher file

**Sizing:** **M** (medium)  
- Requires: loader class (~150–200 lines), cypher merge template (~30–50 lines), test cases, integration
- Touch points: 5–6 files (loader, cypher, manifest, test, possibly invocation patterns)

**Draft Item:**
```yaml
- id: C29
  epic: ontology-mapping
  title: "Build the adhoc Ab Initio version loader (reg_appuser_uses_software): email evidence citations, gate-ruled MERGE key"
  type: task
  module: drydocs-load
  phase: 2
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: [C25]  # gate sign-off required first
  inputs:
    - drydocs/loaders/base.py
    - drydocs/loaders/software_registry.py
    - config/taxonomy/software-registry.yaml
    - config/manual-loads/manifest.yaml
    - config/gate-prompts/software-version-context.yaml
    - drydocs_core/ontology/relationship_vocabulary/
  acceptance: >
    The adhoc loader (drydocs/loaders/adhoc_abinitio_versions.py) implements
    the gate C25's signed shape: MERGE key {source, install_path}, edge
    properties per §B3, `as_of` from email sent date. Evidence block added
    to abinitio product row. Registered status: planned in manifest.
    §Q3 identity-gate settled BEFORE MERGE key written (via notes or gate rider).
    §F rollup NOT written. Observed versions NOT appended to curated list.
    Unit tests + integration proof.
  notes: >
    Gate C25 (signed 2026-08-09) explicitly reserves this build as follow-up;
    the two prerequisite product rows (dpl, snowflake) are now in taxonomy.
    §Q3 caveat: if the estate re-points installs via symlink, install_path
    becomes a poor key and identity moves to (fid, version), a re-key decision
    deferred at gate time with stated consequence — settle it via notes or
    gate rider before writing MERGE key. Two paths NOT taken: application-level
    rollup (F blocked on K17), auto-append to versions list (manual curation stays).
```

**Notes on parked decisions:** §Q3 identity question is named but deferred to build time
via notes or gate rider — the gate accepted that deferral.

---

### **Idea-99** · 2026-08-09 · `[chore]` · **prio Med**

**Title:** Port relay owed: the producer is now canonical for the DPL and Snowflake registry entries

**Disposition:** **MERGE → C25** (amend acceptance notes)

**Justification:**  
This is not a new item but a RELAY TASK that rides on C25's close. C25's notes already
document the situation: "the SME began the same expansion company-side on 2026-08-07 and
**stopped so the two would match**" — deliberate producer-first divergence with a waiting
consumer. The two product rows (`dpl`, `snowflake`) and the acronym expansion
(`DPL: "Data Pipeline Library"`) are now canonical here. C25's notes explicitly defer this
to "Add it once that port merges, together with the other post-port items." This is not
actionable NOW (port is in flight); it is a PORT-PROMPT checklist item, not a backlog item.

**Code context** (via Neo4j):
- `config/taxonomy/software-registry.yaml` — registry; already carries the dpl and snowflake rows as of C25
- `docs/port-prompt.md` — port relay checklist; WHERE this lands (not a backlog item)
- `PORT-MANIFEST.yaml` — disposition rules; no change needed

**Disposition:** **PARKED → port merge completion**

**Alternative:** If the user wants to track this explicitly in the backlog rather than
leave it as a port-prompt note, make it a `prio: p3` `status: blocked` item `depends_on: [<current-port-item>]`
— but C25's notes argue against splitting the relay from the port workflow, which is correct.

**Decision question for user:** Should relay tasks ride docs/port-prompt.md checklist items
(current model) or backlog items? This planning run assumes port-prompt routing is correct.

---

### **Idea-100** · 2026-08-09 · `[bug]` · **prio High**

**Title:** The manifest has no way to say "gate-bound" — and that gap nearly shipped an unsigned gate's ontology

**Disposition:** **PROMOTE** → `J44` (Epic J: release-infrastructure, phase 8)

**Justification:**  
Port-time reconcile caught the defect: G55 (rua-load-shapes) is unsigned company-side,
but G23's code ported inert because it is "gate-bound" — existing guards caught what the
MANIFEST did not. The rule from the company's re-check: "identical to base" and "per-entry
equivalent" are BOTH insufficient; a producer file can be byte-identical and still assume
an active gate the consumer has not signed. Fix: a `gate_bound:` key on manifest rows
naming the gate id, and a reconcile-time check that refuses to activate an entry whose
gate is unsigned on the RECEIVING side. Status/id-set parity is not field-and-gate parity.

**Code context** (via Neo4j):
- `PORT-MANIFEST.yaml` — CodeModule found; manifest schema
- `drydocs_core/ontology/relationship_vocabulary/` — gate-bound files; directory found via Neo4j
- `tests/unit/test_port_manifest.py` — CodeModule found; manifest guard tests
- `.claude/skills/reconcile-port/SKILL.md` — CodeModule found; reconcile-port skill logic

**Sizing:** **M** (medium)  
- Requires: manifest schema extension (gate_bound key), reconcile-time check (~50–100 lines),
  test proof cases (fixture rows with active/inactive gates)
- Touch points: 4 files (manifest schema, test, reconcile-port skill, port-prompt docs)

**Draft Item:**
```yaml
- id: J44
  epic: release-infrastructure
  title: "PORT-MANIFEST.yaml gate_bound check: refuse to activate vocabulary rows whose gate is unsigned on the consumer"
  type: bug
  module: docs
  phase: 8
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: []
  inputs:
    - PORT-MANIFEST.yaml
    - tests/unit/test_port_manifest.py
    - .claude/skills/reconcile-port/SKILL.md
    - drydocs_core/ontology/relationship_vocabulary/
  acceptance: >
    PORT-MANIFEST.yaml rows for drydocs_core/ontology/relationship_vocabulary/**
    carry a `gate_bound: <gate-id>` field naming the gate(s) that must be signed
    before the row may be activated. reconcile-port's entry-activation step checks
    that each row's gate is SIGNED on the consumer side; unsigned gates fail the
    reconcile with a named hold-list and message. Two proof fixtures: a signed gate
    (allows), an unsigned gate (blocks). Field is optional (null = not gate-bound).
  notes: >
    Idea-100 gives the defect: PORT-REPORT-0d3761a9 caught by company re-check.
    The near-miss: G23 code ported inert because its gate is unsigned company-side,
    and existing guards against hard-deletes caught what the manifest did not.
    Shape: a `gate_bound:` key (single gate id or list — reconcile interprets both)
    and a reconcile check that the gate's sign-off line exists in the consumer's
    gate-log.md. Mechanism only; manifests entries are user/SME decisions.
```

**Notes:** No gate decisions needed; this is a guard/check addition.

---

### **Idea-101** · 2026-08-09 · `[question]` · **prio Low**

**Title:** Does the manifest vocabulary need a `derived` disposition?

**Disposition:** **PARKED → HITL user decision; NOT promoted**

**Justification:**  
Idea-101 raises a manifest design question: derived renders (`docs/plan/board.html`,
`docs/plan/roadmap.html`, design-doc `.html`) all carry `disposition: canonical-company`,
but the notes in every one say REGENERATE, not "keep what you have." The two dispositions
differ in consequence — keeping a stale render is as wrong as taking the producer's.
`roadmap.yaml` row was fixed (`evaluate` → `per-entry`), but splitting board.html away
from its precedent would create worse inconsistency. Decide it across all derived rows
at once, or leave it and document why in the manifest.

This is NOT an item for the backlog: it is a DESIGN DECISION for the user/SME to rule,
via the HITL gate or a design session. The backlog cannot hold unruled questions (only
`status: todo/in_progress/blocked/done`). Parked here with the decision question named.

**User decision:** (1) rule derived disposition across board/roadmap/design-docs at once,
then groom as manifest schema change → new `J*` item; (2) leave canonical-company as-is and
document why in PORT-MANIFEST.yaml header (no backlog item).

---

### **Idea-102** · 2026-08-09 · `[question]` · **prio High**

**Title:** The deployment grain has an SME-confirmed cardinality and no home

**Disposition:** **MERGE → K21** (gate rider, NOT a new item)

**Justification:**  
Idea-102 is the OUTPUT of a K21 gate session (2026-08-09 SME work), not a NEW REQUIREMENT.
The SME confirmed: (1) one application, multiple deployments is correct; (2) everything we
map is off the **application**; modules are referenced by default but not used; (3) grain
is ruled — attribution stays on the application, `seal-tom-attribution-reshape` subject
does NOT move, `:BusinessApplication` is correct as-is. What survives are THREE SMALL ITEMS,
all gate riders, NOT new work:

1. **The key** (identity-gate §D2/§C3): bare `deployment_id` is NOT a business key. Test:
   count distinct ids vs distinct (app_id, deployment_id) pairs. → **Rider on identity gate**

2. **The label**: adopt the CONCEPT, pick stable name. Vendor label moved in Yokohama.
   → **Rider on existing vocabulary gate** (C10 standing advice)

3. **Evidence§G15**: Application Module Owner's subject is a module DryDocs has no grain for.
   Practice: module reference is a FORM DEFAULT, populated and not meaningful. Building a
   grain to hold it models the default, not the operating model. So §G15 can be ruled without
   inventing one. → **Rider on existing G-gate** (probably G35)

None of these are backlog items. All three are riders on existing gate sessions, with
findings already captured in the gate-log and evidence documents. **Merge into K21's notes
or K21's dependents (the gate riders).**

**No backlog item needed.** Record the decision (settled by K21 SME session) in backlog.yaml
somewhere K21's dependents will see it (their notes or inputs).

---

### **Idea-103** · 2026-08-10 · `[bug]` · **prio Low**

**Title:** Five more unclosed markdown fences live outside the `docs/**` guard, in files this repo did not author

**Disposition:** **PARKED → HITL user decision; merger candidate**

**Justification:**  
J41's sweep found six unclosed markdown fences in 507 tracked `.md` files. One was ours
(fixed). Now `tests/unit/test_markdown_fences.py` guards `docs/**` — but five remain
DELIBERATELY, outside the guard, in files we do not author:
- `internal/fcdo-reference/CONFLUENCE-TRANSCRIPT.md` (5140 of 5355 fences) — captured transcript
- `internal/fcdo-reference/TRANSCRIPT-1-ONTOLOGY.md` (419 of 568) — captured transcript
- `.claude/skills/data-context-extractor/references/` — vendored skill material
- `SDLC-Docs/extracted/issue-driven-capture-loop.md` (181 of 181) — trailing orphan, possibly safe

**Decision:** (1) widen the guard with an explicit CAPTURE carve-out (re-guard others; admit captures);
(2) leave captures unguarded and document the exception in PUBLISH-BOUNDARY.md or test-guard
conventions.

This is a MANIFEST/BOUNDARY DECISION, not a code item. The guard itself (test_markdown_fences.py)
is already done as part of J41. The decision is:

- **(A)** Promote → `J45`: "Widen test_markdown_fences to carve out CAPTURE corpus files"
  - Inputs: test_markdown_fences.py, docs/restructure/IDEAS.md
  - Acceptance: Guard scans all `docs/**` md files; SKIPS `internal/fcdo-reference/TRANSCRIPT*.md`
    with comment explaining CAPTURED-CORPUS exception; guard still catches `docs/decisions/*`

- **(B)** Document in PUBLISH-BOUNDARY.md that CAPTURE files are intentionally exempt
  - No backlog item; just clarify the boundary rule

**User call:** Deploy (A) + (B), or just (B)? This plan assumes the safer default is (A):
explicitly carve out captures and prove the guard works.

---

## Summary Table

| Idea | Disposition | Item ID | Epic | Status | Notes |
|------|---|---|---|---|---|
| 96 | Promote | J43 | release-infrastructure | todo | Port preflight backlog-union check |
| 97 | Promote | U19 | self-documentation | todo | Update review plan doc-coverage counts |
| 98 | Promote | C29 | ontology-mapping | todo | Build adhoc Ab Initio version loader |
| 99 | Merge → C25 | (port-prompt relay) | — | parked | Relay task; rode port workflow, not backlog |
| 100 | Promote | J44 | release-infrastructure | todo | Manifest gate_bound key + reconcile check |
| 101 | Parked | — | — | decision | User/SME to rule derived disposition scope |
| 102 | Merge → K21 | (gate riders, not items) | — | done | Three gate riders on K21 SME findings |
| 103 | Promote | J45 | release-infrastructure | todo | Carve out CAPTURE corpus from markdown guard |

---

## Proposed New Items (Ready to Groom)

```yaml
# J43 — Port preflight backlog union check
- id: J43
  epic: release-infrastructure
  title: "Port preflight check: backlog item union"
  type: chore
  module: drydocs-load
  phase: 8
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: [J41]

# U19 — Code-graph-review-plan doc-coverage update
- id: U19
  epic: self-documentation
  title: "Update code-graph-review-plan Phase 3 unit 3: eight package roots"
  type: bug
  module: docs
  phase: 16
  agent: main
  model: haiku
  priority: p3
  status: todo
  depends_on: [U18]

# C29 — Adhoc Ab Initio version loader
- id: C29
  epic: ontology-mapping
  title: "Build the adhoc Ab Initio version loader (reg_appuser_uses_software)"
  type: task
  module: drydocs-load
  phase: 2
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: [C25]

# J44 — PORT-MANIFEST.yaml gate_bound check
- id: J44
  epic: release-infrastructure
  title: "PORT-MANIFEST.yaml gate_bound check: refuse unsigned gates"
  type: bug
  module: docs
  phase: 8
  agent: main
  model: sonnet
  priority: p2
  status: todo
  depends_on: []

# J45 — Markdown fence guard carve-out for captures
- id: J45
  epic: release-infrastructure
  title: "Widen markdown fence guard to carve out CAPTURE corpus files"
  type: chore
  module: docs
  phase: 8
  agent: main
  model: haiku
  priority: p3
  status: todo
  depends_on: []
```

---

## Parked Decisions (User Ruling Required)

1. **Idea-101 — Derived disposition scope**  
   Question: Should `canonical-company` disposition apply to renders (board.html, roadmap.html,
   design-docs .html) or adopt a new `derived` value meaning "REGENERATE from reconciled tree"?
   - Current: board.html uses canonical-company (says "keep"); docs say REGENERATE
   - Precedent: roadmap.yaml row was fixed to `evaluate` (deterministic rule)
   - Scope decision: rule across all derived rows at once, or leave canonical-company + document

2. **Idea-103 — Capture corpus guard exemption**  
   Question: Carve out CAPTURED-CORPUS exception in test_markdown_fences.py, or document
   the exemption in PUBLISH-BOUNDARY.md?
   - Proposed: **Both** — promote J45 (guard carve-out + proof) + document boundary rule
   - Alternative: Doc only; leave test unguarded with noted exception

---

## Cross-References & Dependencies

- **C25** (done): software-version-context gate; unblocks C29 loader build
- **J26** (done): Guard text-match sweep; provides J43/J44/J45 methodology
- **J35** (done): Port ledger roll; prerequisite for port machinery (J41–J44)
- **J41** (done): Port opening/closing sequences + port_preflight.py; prerequisite for J43
- **K21** (2026-08-09 SME session): Output is three gate riders (merged, no backlog items)
- **U18** (done): Code-graph metric scope widened; prerequisite for U19 update

---

## Navigation Notes

**How each idea was located in the code graph:**

1. **Idea-96** → Neo4j: searched `PORT-MANIFEST`, `test_backlog.py`, `port_preflight.py` modules
2. **Idea-97** → Neo4j: searched `review-plan`, `design_doc.py`, `render_design_doc.py`
3. **Idea-98** → Neo4j: searched `software_registry`, loaders/ directory, matched to C25 gate context
4. **Idea-99** → Backlog cross-reference: C25 notes name the DPL/Snowflake rows and relay
5. **Idea-100** → Neo4j: searched `PORT-MANIFEST`, `relationship_vocabulary` directory, `reconcile-port` skill
6. **Idea-101** → Backlog schema: searched `disposition` field values in existing manifest entries
7. **Idea-102** → Backlog cross-reference: K21 gate session findings; mapped to gate riders, not items
8. **Idea-103** → Neo4j: searched `markdown`, `test_markdown_fences`; matched to J41 sweep context

**Graph snapshot limitations:**  
The Neo4j snapshot is from 2026-08-10 at commit `bd051ab`. `test_markdown_fences.py` may have been
created after the snapshot (not found in CodeModule scan), but J41's notes confirm the guard exists
and is working. Backlog.yaml is authoritative for cross-references and gate context.

---

## Metrics

```
METRICS
files_read: 3  [docs/restructure/IDEAS.md, docs/restructure/backlog.yaml (sections)]
searches_or_queries: 7  [Neo4j queries for code graph exploration; 7 Python scripts written and executed]
tool_calls_total: 10  [8 Neo4j query script runs + Read tool calls + planning document write]
started: 2026-08-10T16:22:00Z
finished: 2026-08-10T16:35:00Z (estimated)
blocked_on: nothing — all ideas are actionable; two parked on user/SME decision only (not blocked)
```

