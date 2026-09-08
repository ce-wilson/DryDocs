# Runbook — operate `drydocs-remediation`: detect, propose, prove, hand off

<!-- anchor: front-matter -->
- **Module:** drydocs-remediation — this runbook IS the module runbook for
  drydocs-remediation (V1 coverage rule). It covers the whole operate surface: the
  detectors, the Tier-1 transform engine, corroboration, and the Jira handoff.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-09-07**,
  authored at commit `d0de5cd9`. Every command and every number below was RUN on this
  tree against the tracked synthetic fixture, not transcribed from the source.
- **Classification:** Internal-Public (mechanism only — the rule *values*, the real name
  maps, the real registry ids and their ratification state are company-side and injected
  by the caller. This runbook names rule ids and mechanism; it quotes no real definition,
  no real job name and no registry content)
- **Audience:** anyone asked to look at a Control-M folder export and say what is wrong
  with it, what may be corrected, and what a developer is being asked to implement
- **Companion:** `docs/design/drydocs-remediation-tdd.md` — **the contract, and it wins on
  conflict**; this page is procedure, not a second specification, so every design claim
  below is one sentence and a pointer into it. Also
  `drydocs_remediation/overview_readme.md` (the governance walk-through),
  `drydocs_remediation/module-requirements.md` (what is installed, what is not acquired,
  and why), and `.claude/skills/controlm-runbook-automation/references/fix-package.md`
  (the fix-package shape this module produces).

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the module that answers *"may we change this?"* about a Control-M
definition — and the answer is never the detector's to give.

### The one rule to know before running anything

> **Only ✅-ratified rules may change a definition. Everything else is WARN-only.**

This is enforced in code, not by convention: `transform.propose_greenfield` skips an
unratified rule and reports it in `skipped_unratified`. An unratified rule is not "a rule
nobody got around to" — it is structurally incapable of touching a job.

Each rule carries a status in the rules registry: **❓ open** (needs an SME decision),
**🟡 provisional** (observed and believed, not signed off), **✅ ratified** (signed off at
the HITL gate, and only now may it drive a change). **Status is independent of severity** —
a rule can be must-fix and provisional at once, because *how bad is it* and *may we act
unilaterally* are different questions. Collapsing them is how a linter starts editing
production (`overview_readme.md`, "The status ladder").

### The separation of duties, in one line

**We analyze and package; developers implement.** Nothing in this module applies a change
to a live Control-M environment. Its terminal artifact is a handoff a developer acts on,
and the handoff says so on its face — the rendered package's "Requested by" line reads
*"Production Support (analysis pre-validated; implementation only)"*.

**In scope.** Reading an export into a `DefinitionSet`; running the detectors; proposing a
Tier-1 greenfield; proving the proposal equivalent; corroborating against a second source;
assembling and rendering the handoff; the census verb `profile-folder-set`.

**Out of scope.** The graph — this module **writes none**, by construction (TDD §4,
NFR-REM-1), and the one read path refuses a write clause at runtime. The rule VALUES and
the registry's ratification state (company-side). What a finding MEANS for a specific
application — that is the SME's, at the gate. Applying anything to a live environment.

<!-- anchor: prerequisites -->
## Prerequisites

- **`poetry install`** — the default group is enough for everything in Startup, Refresh
  and Verify below. The module's own dependency page is
  `drydocs_remediation/module-requirements.md`.
- **`poetry install --with remediation`** — ONLY for the optional `lxml`, and `lxml` is a
  **validator, never the emitter**. Emission is byte-splicing in `xml_io.write`, because
  every DOM serializer rebuilds a start tag from an attribute dict and collapses the
  multi-line attribute wrapping a real `exportdeftable` JOB element carries — producing
  the 100%-diff file no developer can review, which `fix-package.md` §XML rule 1 forbids.
  A guard keeps it out of the emitter (`test_xml_io_edits.py`).
- **An export, if you are working on real definitions**: a directory of Control-M
  definition XML from `exportdeftable`. Real exports are Internal and live under
  `DRYDOCS_DATA_ROOT`, never in this repo.
- **Not required, and deliberately so**: a Neo4j graph (nothing here writes one, and the
  procedures below need none), Oracle credentials, and the Control-M `.dtd`/`.xsd`
  schema artifacts. Those last are **NOT ACQUIRED** and are **not a blocker for
  emission** — `xml_io` splices the vendor's own bytes and never authors XML. Their only
  role is the optional validation in Verify (`module-requirements.md` §2).
- **The rules registry** for anything beyond mechanism: `internal/remediation/`
  `standards-rules-registry.md`. It is the single source for both gates — validate reads
  the rules, design reads each rule's greenfield action — so a rule tightens on both
  sides at once and they cannot disagree.

<!-- anchor: startup -->
## Startup

**This module has no service.** "Startup" is reading an export and finding out what you
are holding.

1. **Confirm the module imports and the graph boundary is intact** (cheap, and it is the
   check that proves the invariant this module rests on):
   ```powershell
   poetry run python -c "import drydocs_remediation.detect, drydocs_remediation.jira; print('ok')"
   ```
   Success: `ok`.

2. **Census the folder set** — what the export SAYS, and what only a human can supply:
   ```powershell
   poetry run drydocs profile-folder-set <export-dir> --out folder-set-profile.json
   ```
   Success: a summary, then `wrote folder-set-profile.json`. The artifact has two halves
   and the division is the point — five censuses of what the export carries (shape,
   identity, variables, contacts, invocation fan-out), then a **substitution-slot** list
   naming the facts the export does NOT carry. A slot with no value reports
   `not-supplied` with a null and **never a default**: inventing one is how a proposal
   becomes a wrong fact nobody re-checks. The verb prints those slots in yellow.

   This is the module's only CLI verb. It asserts nothing about meaning, and it writes no
   graph.

3. **If you have no export**, use the tracked synthetic fixture — the whole procedure
   below runs on it in any clone, with no company data and no graph:
   ```powershell
   poetry run python -c "from drydocs_remediation.formats import TranscriptDefinitionFormat; d = TranscriptDefinitionFormat().load('tests/fixtures/remediation/synthetic-legacy-transcript.yaml'); print(len(d.folders), 'folder(s),', len(d.jobs), 'job(s)')"
   ```
   Success: `1 folder(s), 1 job(s)`.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

**The recurring procedure is a BATCH, and it is driven from Python rather than from the
CLI.** Say that plainly rather than implying a verb exists: `profile-folder-set` is the
only registered command, and the detect → transform → prove → hand off sequence is a
library API. The batch entry point wraps itself in a run log (`run_remediation_batch`,
G107), so a batch is recorded whether it succeeds or fails.

The sequence, with the exact calls, in the order the TDD's stages run (§3, Stages A–E):

1. **Acquire** (Stage A) — an export through the `DefinitionFormat` seam:
   ```python
   from drydocs_lineage.extractors import ControlMXmlDefsExtractor
   from drydocs_remediation.xml_bridge import to_definition_set
   definitions = to_definition_set(ControlMXmlDefsExtractor().extract(export_dir))
   ```
   The fixture path is `TranscriptDefinitionFormat().load(...)` instead; everything after
   this step is identical, which is what makes the procedure rehearsable.

2. **Detect** (Stage B) — `detect_all(definitions)` runs the dot-smuggling detector
   (**registry R1**) and the conformance rules, de-duplicated:
   ```python
   from drydocs_remediation.detect import detect_all
   findings = detect_all(definitions)
   ```
   On the fixture: **5 findings — registry R1 ×1, registry R32 ×4.**

3. **Classify and propose** (Stages C–D) — the governance gate, and the step to read
   carefully:
   ```python
   from drydocs_remediation.transform import propose_greenfield
   result = propose_greenfield(definitions, rules)   # rules: Sequence[Tier1Rule]
   ```
   Every `Tier1Rule` carries `ratified: bool`. The unratified ones do not run and are
   named in `result.skipped_unratified`. On a two-rule demonstration (one ratified, one
   not) the fixture gives `applied: ['R-demo-ratified']`,
   `skipped_unratified: ['R-demo-unratified']` — the governance rule visible in the
   output rather than asserted in prose.

4. **Emit, if a definition actually changed** — `xml_io.write` splices bytes into the
   vendor's own file, and `changedoc.render_change_doc` produces the before/after excerpt
   a reviewer reads. The reviewable diff IS the deliverable; see the `lxml` note in
   Prerequisites for why no DOM serializer may take this step.

5. **Prove** (Stage D) — offline equivalence between the legacy and greenfield sets:
   ```python
   from drydocs_remediation.equivalence import prove_equivalence
   proof = prove_equivalence(definitions, result.greenfield)
   ```

6. **Corroborate** — reconcile the definitions against a second source (the `psgmgr`
   staging extract, or a graph fetch through `ReadOnlyGraph`):
   ```python
   from drydocs_remediation.corroborate import reconcile_variables
   report = reconcile_variables(definitions, extract)   # extract: {job_name: VariableDefs}
   ```

7. **Package and hand off** (Stage E):
   ```python
   from drydocs_remediation.jira import run_remediation_batch, render_handoff, emit_handoff
   package = run_remediation_batch(definitions, findings, proof, title=..., transform=result)
   text = render_handoff(package)          # review this before anything leaves
   ref = emit_handoff(package, submitter)  # submitter: your JiraSubmitter implementation
   ```
   `run_remediation_batch` RECORDS the batch's counts once, at the seam, and
   `render_handoff` reads them from the package rather than recomputing them — so the
   rendered numbers and the run log's numbers cannot drift apart.

<!-- anchor: verify -->
## Verify

**The proof surface is the run's own output.** Every value below was produced by running
the sequence above against `tests/fixtures/remediation/synthetic-legacy-transcript.yaml`
on this tree, so it is reproducible in any clone (no graph, no company data):

| Check | Where | Expected on the fixture |
|---|---|---|
| The export parsed | `len(d.folders)`, `len(d.jobs)` | `1`, `1` |
| Detectors ran | `len(detect_all(d))` | `5` (registry R1 ×1, registry R32 ×4) |
| Governance held | `result.skipped_unratified` | the unratified rule id, present |
| Equivalence proven | `proof.equivalent` / `compared_jobs` / `proven_jobs` / `not_proven` | `True` / `1` / `1` / `0` |
| Corroboration | `report.consistent` / `checked_jobs` | `True` / `1` |
| Batch coverage | `package.coverage` | `objects_examined 2`, `objects_changed 0`, `findings_ratified 0`, `findings_unratified 5`, `skipped {'unratified (governance skip)': 1}` |

**Read `equivalent` correctly.** It is True only when every paired job is PROVEN — at
least one surface compared and all compared surfaces equal. A job with nothing to compare
lands in `not_proven` and BLOCKS the claim; it never passes by silence. *"We did not prove
this"* is a different statement from *"this is equivalent"*, and the report keeps them
apart on purpose.

**Read the coverage counts as a governance readout, not a scorecard.** On the fixture
`findings_ratified` is 0 and `findings_unratified` is 5: five real findings, none of them
authorized to change anything, which is the correct state for a registry whose rules are
still provisional. `objects_changed: 0` follows from that, not from the detectors failing
to find anything.

**Validate the emitted XML, if you have the schema.** With `--with remediation` installed
and a `.dtd`/`.xsd` acquired, validate `<folder>.updated.xml` against it. This upgrades
the honest residual claim — *"the file differs from a Control-M-produced file by exactly
the approved bytes"* — to a schema-checked one. Without the schema, the byte-level
self-check in `changedoc` is the available proof, and it is the reason the residual claim
is phrased that way.

<!-- anchor: rollback -->
## Rollback

**There is nothing to roll back in this repo's data, by construction.** The module writes
no graph (the boundary is enforced, not merely intended — see Troubleshooting) and no
change reaches a live Control-M environment from here. The artifacts a batch produces —
the profile JSON, the change doc, the updated XML, the rendered handoff — are files you
may delete and regenerate; the sequence is deterministic over the same input.

**Rolling back an APPLIED change is the developer's procedure, not this module's**, and
the handoff says which one: `run_remediation_batch` carries the rollback line into every
package, defaulting to *"Restore prior version via Control-M Changes History."* Override
it with the `rollback=` argument when a batch needs something more specific, so the
instruction travels attached to the change rather than living in somebody's memory.

**If a proposal was wrong, the fix is upstream of the artifacts.** Correct the rule in the
registry (which is a gate decision, not an edit), re-run the batch, and let the new
package supersede the old one. Editing an emitted artifact by hand breaks the one property
the whole design rests on: that the file differs from the vendor's by exactly the bytes a
rule proposed.

<!-- anchor: troubleshooting -->
## Troubleshooting

**`skipped_unratified` is non-empty and nothing changed.**
*Diagnosis:* the rule is not ✅-ratified. This is the design working, not a defect —
`propose_greenfield` is structurally incapable of applying it.
*Fix:* nothing in the code. The rule's status is a registry entry and moving it is a HITL
gate decision. If the rule has no registry entry at all, that is the real problem: a
detector with no entry emits findings nothing can rank, nothing can turn into a fix, and
nothing can sign off on — **the entry is the thing that gets ratified**
(`overview_readme.md`).

**`UnprovenHandoffError` when emitting.**
*Diagnosis:* the package is being sent without a proof that covers it. The equivalence
report is not decoration on the handoff; it is a precondition of it.
*Fix:* run `prove_equivalence` and inspect `not_proven` before re-emitting. If jobs sit in
`not_proven`, the honest answer is to say so — the claim narrows to the jobs actually
proven, or the batch narrows to them.

**`GraphWriteAttemptError` from corroboration.**
*Diagnosis:* a write clause reached `ReadOnlyGraph.fetch`. This is a **code bug, not a
configuration problem** — the component never writes a graph (NFR-REM-1), and the
read-only wrapper is where that invariant is enforced at runtime.
*Fix:* remove the write clause from the query. Do not route around the wrapper; it is the
enforcement, and the exception names the clause it caught.

**Substitution slots report `not-supplied`.**
*Diagnosis:* the export does not carry that fact — DEVX_KEY, the MFTS set and the contact
DLs are the standing examples. The census is telling you the truth about the export.
*Fix:* an SME supplies the value. Never a default: the whole point of the `not-supplied`
sentinel is that a plausible invented value is indistinguishable from a real one three
steps later.

**The handoff's owner reads `UNRESOLVED`.**
*Diagnosis:* ownership could not be resolved. The renderer surfaces this rather than
guessing, and labels it as *itself a defect*.
*Fix:* resolve ownership before the package goes out. An unowned change request is one
nobody will act on, and a guessed owner is worse.

**A reviewer says the diff is unreadable.**
*Diagnosis:* almost certainly a DOM serializer got into the emission path, collapsing
multi-line attribute wrapping and producing a whole-file diff.
*Fix:* emission is `xml_io.write` byte-splicing, always. `lxml` validates and inspects; it
never serializes. The guard that keeps this true is
`test_xml_io_edits.py::test_xml_io_imports_are_stdlib_core_and_formats_only`.

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Rule ratification — the SME, at the HITL gate.** Moving a rule ❓ → 🟡 → ✅ is a gate
  decision recorded in the rules registry, never a code change and never a runbook
  decision. The registry is `internal/remediation/standards-rules-registry.md`; this page
  cites it and quotes nothing from it.
- **Anything about what a finding MEANS for a specific application** — the SME, through
  `docs/restructure/03-hitl-sme-flow.md`. A detector reports a shape; whether that shape
  matters here is an ownership question.
- **Implementation of an approved change** — the developer or team who owns the folder.
  The separation of duties is not advisory: this module produces analysis and a package,
  and stops there.
- **The contract, on any conflict with this page** — `docs/design/drydocs-remediation-tdd.md`
  wins, and a disagreement between the two is a defect in this runbook to be fixed here.

<!-- anchor: appendices -->
## Appendices

### A. What the handoff looks like

`render_handoff(package)` produces a plain-text package whose first lines carry the title,
the owner, and the requester line that states the separation of duties. Then a findings
block, one line per finding, each carrying its rule id, severity, **ratification state**
and target; then a coverage block. On the fixture every finding renders as
`UNRATIFIED (warn-only)`, which is what makes the governance state legible to a reader who
never opens the registry.

### B. Where each stage lives

| Stage (TDD §3) | Module |
|---|---|
| A — Acquire | `formats.py` (the `DefinitionFormat` seam), `xml_bridge.py`, `xml_io.py` |
| B — Detect | `detect.py` (`detect_all`, registry R1 + the conformance rules) |
| C — Classify | the registry's status ladder, read by `transform.py` |
| D — Transform + prove | `transform.py`, `equivalence.py`, `changedoc.py` |
| E — Package + handoff | `jira.py` (`run_remediation_batch`, `render_handoff`, `emit_handoff`) |
| (census) | `profile.py`, reached by `drydocs profile-folder-set` |
| (corroboration) | `corroborate.py` (`ReadOnlyGraph`, `reconcile_variables`) |
