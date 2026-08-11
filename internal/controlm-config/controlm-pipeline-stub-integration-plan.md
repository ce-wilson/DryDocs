# controlm-pipeline-stub → DryDocs integration — backlog plan

**Classification: Internal.** **Written:** 2026-08-04 (producer session, Fable).
**Executor:** the internal-repo Opus 4.8 agent — this plan is your work order.
**Capture this plan argues from:**
[`reference/controlm-pipeline-stub-capture.md`](reference/controlm-pipeline-stub-capture.md)
(verbatim; read it first). The stub package itself lives in the internal repo as
a standalone project with 14/14 tests green.
**Sibling capture — what the generator is being asked to emit:**
[`reference/controlm-job-metadata-standards-capture.md`](reference/controlm-job-metadata-standards-capture.md)
(2026-08-11, C29 — REQ-1…REQ-4 plus four standards pages). Read it alongside this
plan: it is the *target* side of the same lifecycle, and it collides with **item E1
below**. E1 uses the two literal `DESCRIPTION` strings the stub emits as a
machine-generated provenance discriminator; the standard fills the same 4000-char
field with pipe-delimited tokens. Add a token block and E1's exact-literal match
breaks; require the literal and the token block has nowhere to go. Ruling needed
before either lands — the exits are in that capture's Conflicts §4. The standard
also **retires** part of what the stub emits (REQ-2 deletes `<SHOUT>`/`<DOSHOUT>`,
which the stub already omits) and adds two ordered file-watcher variables (REQ-3)
whose declaration order is load-bearing.

## Framing (the user's rulings, 2026-08-04)

1. **Oracle psgmgr stays the primary ingestion pipeline** — its dependencies
   are mapped. XML import is a **supplement**, not a replacement.
2. **The stub's components are candidates to import the `.xml`** definition
   exports alongside what `drydocs_lineage/extractors/controlm_xml.py` (G47)
   already stages.
3. **The stub's `model/` + `generator/` will create the "Greenfield .xml"**
   handed to dev by the Control-M fix module (`drydocs_remediation`) — the
   SoD holds: we generate and prove, dev deploys.
4. Beyond those two, this plan names every other DryDocs module the package
   plausibly serves (§Items, phase 4+), each as its own item.

## Why this package matters (what it settles)

- **It IS the vendor-schema acquisition** the remediation TDD parked XML I/O
  on ("gated on the vendor schema acquisition — company-side .dtd /
  exportdeftable"). `schema/Folder.xsd` is validated against a real 17,312-line
  export; the capture's §B1–B3 is a complete attribute/element/child-order
  reference for DEFTABLE/SMART_FOLDER/JOB and all six child element types.
- **It closes the job-naming-standard gap** for the DPL family:
  `get_job_name() = {APP[:4]}{FREQ}{JOB_NUM}_{SOR}_{DATASET}_AWS_{SUFFIX}` is
  generator-side truth, not inference. (The folder grammar
  `{application}G-HLDM-{seal}-{sor}_ONF` independently corroborates the PRAOCG
  positional-code + SEAL-in-folder-name findings.)
- **The two verbatim DESCRIPTION literals** ("Generated Control-M Folder";
  "Generated job to trigger DPL transformation in AWS for dataset: ") are a
  machine-generated-vs-hand-authored **provenance discriminator** usable
  against the live graph today.
- **The CR### validation registry** (CR015a ctmag, CR041 folder naming, CR042
  job naming, CR050 app-code prefix, CR060 NODEID known, CR070 failure DOMAIL
  present) is the company's own conformance vocabulary, in code, with
  reference lists.

## Standing constraints (apply to every item)

- **Branch discipline:** all of this is "bringing external work IN" — do it on
  `feat/`/`port/` branches, `--no-ff` merge, per CLAUDE.md §0. Run
  `git branch --show-current` before every commit.
- **Taxonomy first, ontology through the gate.** New STAGED data (conditions,
  quantitative resources, ON/DOMAIL blocks) is pure staging/taxonomy. Any new
  MEANING edge (e.g. job-NOTIFIES-DL, job-CONSTRAINED_BY-resource) routes
  through `relationship_vocabulary.yaml` as `status: planned` + the HITL gate.
  No exceptions; the gate items are flagged below.
- **Mechanism producer-side, values internal-side.** Where an item says
  "producer twin", the generic mechanism belongs in the producer repo (or is
  already there); the HLDM/QR/server values stay in `internal/` or config.
- **The stub stays a sibling, not a vendored blob.** Import the *pieces* named
  per item (model/, Folder.xsd, rules.py patterns). Do NOT absorb deploy/
  (ITPAM upload) into remediation — SoD: DryDocs never deploys. Stage-5
  runtime/ is reference-only.
- **The unscrubbed sample XML** (`PRSRVG-HLDM-25638.xml`) never enters DryDocs.
  Fixtures for DryDocs tests are stub-GENERATED synthetic folders (item F1).
- **Suite + guards green** after every item; renders regenerated per the
  session ritual; claims pushed before work (the pull rule).

---

## Phase 1 — READ side: XML supplement to the psgmgr pipeline

**X1 — Vendor `Folder.xsd` + XSD preflight in the XML seam** · module:
drydocs-lineage · model: opus · depends: none
Bring `schema/Folder.xsd` in (internal config or `drydocs_lineage` resource —
decide and record; it is lenient by design, see capture gotcha 4) and add an
optional XSD-validation preflight to `ControlMXmlDefsExtractor` (G47):
report-only (counts into `XmlDefsCoverage`, per-file pass/fail + failure
detail), never a batch abort. *Acceptance:* extractor run over (a) a stub-
generated folder XML and (b) a real export both report `xsd: pass`; a
deliberately malformed file reports `xsd: fail` with the lxml reason and still
stages what it can; coverage `.summary()` carries the new counts; suite green.
*Note:* do NOT tighten the XSD (gotcha 4 — the real export has nested
SMART_FOLDERs without DESCRIPTION).

**X2 — Widen the XML staging contract: INCOND/OUTCOND/QUANTITATIVE/ON+DOMAIL**
· module: drydocs-lineage · model: opus · depends: X1
G47 stages folders, jobs, ordered variables. The capture §B3 gives the exact
attribute sets for the remaining child elements. Extend `XmlJobRecord` (or
sibling records) to stage them VERBATIM (taxonomy-first: no meaning edges, no
resolution): conditions with NAME/ODATE/AND_OR|SIGN, quantitatives with
NAME/QUANT/ONFAIL/ONOK, ON/DOMAIL with STMT/CODE + the six DOMAIL attrs.
*Acceptance:* extractor on a stub-generated folder containing all six child
types round-trips every attribute into staging records; `scope_layers()`
unchanged; coverage counts each child type; suite green.
*Why it matters:* the psgmgr replica carries conditions already — the XML
supplement's marginal value is exactly the definition-level blocks the replica
views flatten (ON/DOMAIL, quantitative resources) plus a second witness for
conditions. Keep the psgmgr-primary precedence ruling OPEN (the 2026-07-29
inbox question owns it — do not decide it in this item).

**X3 — Attribute-reference conformance test between capture and extractor** ·
module: drydocs-lineage · model: sonnet · depends: X2
A pinned test that the extractor's staged field set covers the capture §B1/§B3
attribute inventory (constants may be recorded as constants). Guards future
drift when the stub evolves. *Acceptance:* test enumerates the capture's
attribute names from a checked-in fixture list; extractor omissions fail with
the missing names.

## Phase 2 — WRITE side: the Greenfield XML emitter for the fix module

**W1 — XML object model into the fix path** · module: drydocs-remediation ·
model: opus · depends: none (parallel with X1)
Adapt the stub's `model/` (DefTable/SmartFolder/Job/Variable/InCond/OutCond/
Quantitative/OnStatement+DoMail + `make_element`, fixed child order) as the
emitting half of `drydocs_remediation.formats.XmlDefinitionFormat.dump()`.
Placement call to make consciously: remediation-local vs
`drydocs_core.orchestration.controlm` (the S2 seam) — recommend
**remediation-local first** (only consumer today), promote to core when a
second consumer appears; record the decision in the item close.
*Acceptance:* `DefinitionSet → dump()` emits schema-valid XML (validates
against Folder.xsd), fixed child order asserted, `<?xml?>` + `Exported at`
preamble present; round-trip `load(dump(x)) == x` on the M0 unit; suite green.

**W2 — Greenfield generation wired to `propose_greenfield`** · module:
drydocs-remediation · model: opus · depends: W1
`transform.py::propose_greenfield` output + W1 emitter = the **before/after
.xml pair** in the fix package (`jira.py::render_handoff`/`emit_handoff`).
Emit both files, XSD-validate both, and refuse the handoff if the AFTER fails
validation (extends the existing `UnprovenHandoffError` discipline).
*Acceptance:* a fix package for the M0 unit contains `before.xml`/`after.xml`,
both schema-valid; equivalence proof still gates emission; a synthetic
schema-breaking transform is refused with the validation detail.

**W3 — The two DESCRIPTION literals as pinned constants** · module:
drydocs-remediation (constants in the shared seam) · model: haiku · depends: W1
`FOLDER_DESCRIPTION` and `AWS_TRANSFORM_JOB_DESCRIPTION_PREFIX` land once
(single source of truth, mirroring the stub's `__init__.py`) with a drift test,
so greenfield output and the provenance classifier (E1) share them.
*Acceptance:* constants exist in one module; two tests pin the exact strings.

**W4 — AUTOEDIT/SET VAR gap ruling (HITL-adjacent)** · module:
drydocs-remediation · model: opus · depends: W1, W2
The stub's known gap: generated jobs reference CMDLINE tokens resolved only by
folder-level AUTOEDIT/global vars it does not emit (capture §B4/§B7). The fix
module's greenfield MUST NOT ship that gap silently: either emit the folder
AUTOEDIT block (the real dplplugin behavior) or hard-fail generation listing
unresolved tokens — the resolver (`resolve_command_line`, G46) already knows
how to find them. *Acceptance:* generating a transform-family greenfield either
carries folder-level variable definitions for every CMDLINE token or refuses
with the unresolved-token list; the choice of emit-vs-refuse is recorded and,
if emit, the variable values route through the existing var-standard facts
(G16), not invented.

## Phase 3 — Validation registry: CR### rules into conformance

**V1 — CR### rule registry pattern + the six rules** · module:
drydocs-remediation · model: opus · depends: none
Reproduce the registry shape (`@register_rule("CRxxx")`, `RuleResult`,
report `.passed`/`.failures`/`to_html`/`to_json`) inside remediation's
detector family (it is the same shape as `detect.py::Finding` — reconcile,
don't duplicate: one registry, findings as rule results). Implement the six
known rules against DryDocs inputs: CR041 folder naming, CR042 job naming,
CR050 app-code prefix, CR060 NODEID known, CR070 failure DOMAIL present,
CR015a ctmag. Reference lists (folder prefixes, servers, high-priority) become
config under `internal/` or `config/` with source rows.
*Acceptance:* the six rules run against (a) a stub-generated folder (all pass)
and (b) mutated fixtures (each rule individually fails); report renders;
rules also run in the greenfield path (W2) so a fix package can never emit a
folder that fails the company's own checks.

**V2 — Rule parity backlog with `ba0.sh` (census, not build)** · module:
drydocs-remediation · model: sonnet · depends: V1
The stub implements ~6 of ~50 CR rules. Census the remaining rules from the
JGL DAL source, table them (id, intent, inputs needed, DryDocs feasibility),
and inbox the buildable tier. *Acceptance:* the census table exists in
`internal/remediation/` with a per-rule disposition; no code required.

## Phase 4 — Classifier & graph enrichment (the "other modules")

**E1 — Generated-by-dplplugin provenance discriminator** · module:
drydocs-load / ontology · model: opus · **GATE-TOUCHING** · depends: W3
Jobs/folders whose DESCRIPTION matches the two literals are machine-generated.
Stamp a derived PROPERTY (e.g. `authored_by_generator: dplplugin`) at ingest —
a property, not an edge (the O28 precedent keeps this gate-light), but take
the property naming through a config/vocabulary note and flag it in the gate
log. Feeds the FW-really-API/greenfield-provenance work (design principle 8).
*Acceptance:* ingest stamps the property on matching live rows; counts
reported; naming recorded; no relationship added.

**E2 — Job-name grammar into the classifier facts** · module: drydocs-core
(orchestration/controlm) · model: opus · depends: none
`{APP[:4]}{FREQ}{JOB_NUM}_{SOR}_{DATASET}_AWS_{SUFFIX}` + the JOB_NUM/SUFFIX
catalog (0001 FW / 0005 MOVE / 0020 PLCT / 0050 INGEST / 0051 TRUST / 0060
PROV) become a parse helper beside `parse_folder_name` (producer-twin
mechanism; the catalog values ride internal config). This is a definitive feed
for the G12/G27 ETLProcess **kind enum** (the MAC kind-enum rider gate:
`etlprocess-kind-enum.yaml` — this catalog is evidence FOR that gate, do not
flip it here) and for the K2 FID tier (fid appears in JobConfig; CREATED_BY =
`fid.lower()` is one more FID witness).
*Acceptance:* `parse_job_name()` decomposes the six families on stub-generated
names + real samples; unparsed names return a typed miss, never a guess;
the kind-enum gate page gains the catalog as evidence.

**E3 — Escalation/DOMAIL linkage evidence for the DL gate** · module: ontology
· model: sonnet · **GATE-EVIDENCE** · depends: X2
`%%NOTIFY` (dest of every failure DOMAIL) is set folder-side, "often the
escalation DL from the escalation Excel templates". Attach this + CR070 to the
open `email-dl-contact-point` gate as evidence; stage DOMAIL blocks (X2) so
the gate can argue from data. *Acceptance:* gate prompt's evidence section
cites the capture; no write.

**E4 — ingestion-config.yaml ↔ MAC/DPL registry crosswalk** · module:
config / drydocs-lineage · model: opus · depends: none
The stub's Stage-1 config "mirrors the DryDocs internal-twin shape" — its
`DatasetConfig` (dataset_name, sor, seal, pipeline_id, dataset_id, fid, env,
image, jobs[]) overlaps the G17 `dpl_mac` seam and the planned G25 DPL registry
DB. Write the field-level crosswalk (which fields agree, which exist only one
side, join keys) and register `ingestion-config.yaml` as a source (internal
classification) if it becomes an ingest. The Zilo `flow_definition.json` shape
is a new artifact fact for the MAC family ("Compute JSON File" in the Excel
runbook maps here). *Acceptance:* crosswalk doc committed; source registered
or explicitly declined with reason.

## Phase 5 — Fixture factory (producer-twin friendly)

**F1 — Stub-generated synthetic XML fixtures + round-trip proof** · module:
drydocs-lineage tests · model: sonnet · depends: X2, W1
Use the generate side to mint SANITIZED synthetic folder XML (generic app
codes, zeroed GUIDs) as committed fixtures, replacing any temptation to use
the unscrubbed sample. The flagship test: **generate → extract → compare** —
stub emitter output fed to `ControlMXmlDefsExtractor` reproduces the input
config's facts (names, variables in order, conditions, DOMAIL). This is the
scenario-fixture plan's XML leg. *Acceptance:* fixtures committed
(publish-boundary-clean — value-shape guards pass), round-trip test green,
G47's declared contract unchanged.

## Explicitly OUT of scope (recorded so nobody re-derives)

- **Stage 4 `deploy/` (ITPAM upload, folder delete, escalation-db write)** —
  DryDocs never deploys (SoD). Keep as reference for the fix-package handoff
  doc; `update_escalation_db` is noted as a future *read* target only.
- **Stage 5 `runtime/`** — the launcher arg contract corroborates G15; nothing
  to build. If a discrepancy with G15's grammar is found, that is an IDEAS
  entry, not silent edit.
- **Replacing psgmgr ingestion** — ruled out by the user; XML is supplement.
- **The precedence ruling** (psgmgr vs XML per object) — stays with its
  2026-07-29 inbox question; HITL, the user/SME rules it.

## Sequencing summary

```
X1 ─→ X2 ─→ X3
 │      └─→ E3 (gate evidence)
W1 ─→ W2 ─→ W4        (W1 ∥ X1)
 └─→ W3 ─→ E1 (gate-touching property)
V1 ─→ V2              (V1 after W1 if sharing the emitter in tests)
E2, E4                (independent)
F1                    (after X2 + W1 — the round-trip needs both sides)
```

Suggested first session for the Opus agent: **X1 + W1** (independent, both
unblock everything else), then W2/W3, then X2. Groom these into the internal
tracker with your own ids (producer DD-series convention: the producer never
allocates DD ids — allocate them internal-side); producer-twin items (E2
mechanism, F1 fixtures, W1 if promoted to core) flow back through the normal
port channel with PORT-MANIFEST rows.
