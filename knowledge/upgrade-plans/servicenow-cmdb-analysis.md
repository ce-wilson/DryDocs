# ServiceNow CMDB/CSDM doc-set analysis (C10)

**Classification:** Internal-Public (GROUNDED summaries of the vendor doc set +
SYNTHESIZED DryDocs dispositions; the vendor material itself stays local — see
`external/ServiceNow/README.md`, the source manifest).
**Analyzed:** 2026-07-20. **Feeds:** `generic-terminology-research.md` (the SaaS-naming
idea) and the gate-bound candidate list at the bottom.

**This file is the BASELINE half of a pair (K21, 2026-08-09).** It reads the vendor doc set —
the canonical CMDB/CSDM model. [`servicenow-replica-evidence.md`](servicenow-replica-evidence.md)
reads our **replica** — the instance — and names where the two differ (company `u_` columns, a
company `x_<scope>_` scoped app with no vendor baseline at all, and data-lake carrier columns that
exist in ServiceNow nowhere). Read them together; neither is sufficient alone. Note candidate #1
below is **re-opened** by that evidence.

Disposition vocabulary: **INCORPORATE** (act on it — target named), **PARK** (real but
no current use case), **REJECT** (out of scope for DryDocs). Nothing here changes the
graph or vocabulary — meaning-bearing candidates route through the HITL gate.

## Per-file findings

### 1. What are services and service offerings.pdf (asset 0003948)

Key concepts: service = "a means of delivering value to customers by facilitating
outcomes… without owning the costs and risks"; service offering = service commitments
stratifying one service by SLA/availability/pricing; THREE service types — business /
application / technical (extensible); **an application service is a logical
representation of a deployed application stack and is NOT the application — no 1:1
relationship**; categorization questions (outcomes, standalone?, owner, payer, users).

- INCORPORATE → terminology research: the Business Application vs Application Service
  (deployed instance) split — DryDocs has no "deployed instance of an app" concept; the
  batch estate (folders/jobs per app) plays that role implicitly. Gate-bound candidate #1.
- PARK: service offerings/SLA stratification (no catalog/consumption use case yet).

### 2. CMDB - Product Architecture.pptx (asset 0002024)

Key concepts: "The CMDB is the database — CSDM is the data model. It tells us where to
record the items" (a crisp statement of DryDocs' own layer 3 vs layer 2 split); CI class
= a table, parent/child specialization (`cmdb` → `cmdb_ci` → children); the IRE flow —
identify by serial → name → IP+MAC, then the **reconciliation rule checks whether the
current data source is ALLOWED to update that CI's attributes**; relationships = two CIs
+ a typed relationship with inverse-pair names ("Runs on::Runs"); foundation data
(users/groups/locations) deliberately NOT in the CMDB; every CI references a Product
Model; logical CIs are "tribal knowledge" (wizard-entered) vs discoverable CIs.

- INCORPORATE → docs prose: the CMDB/CSDM one-liner as external validation of the
  four-layer model (knowledge graph vs ontology); cite in 00-conceptual-model at next touch.
- INCORPORATE (validated, no change): source-allowed-to-update reconciliation ≈
  `config/precedence.yaml` + `PrecedenceResolver`.
- PARK: inverse-pair relationship naming (Runs on::Runs) as a vocabulary presentation idea.

### 3. CMDB Data Manager.pptx (asset 0003551)

Key concepts: policy-driven BULK CI lifecycle — Retire / Archive / Delete / Attestation
policy types; **attestation = verifying that recorded infrastructure/applications still
physically exist**, on a cadence, task-assigned to the "Managed by Group" (the SMEs);
approvals gate destructive actions ("Careful! Delete CIs without approval may have
unintended consequences!"); exclusion lists; orphan dependent-CI cleanup + cascade
retire; tasks stale at 90 days; retention driven by regulatory questions.

- INCORPORATE → D7's family: the retire/archive/delete ladder maps onto our
  mark (`removed_from_source_at`) → sweep design; "retire = keep inactive for audit" is
  exactly our soft-delete mark. The NEW idea is **attestation** — a periodic SME
  re-confirmation pass over gate-accepted, non-discoverable facts. Gate-bound candidate #2.
- PARK: the policy-framework UI (a far-future Epic O surface).

### 4. CMDB Governance Workshop.pptx (April 2025)

Key concepts: the full CSDM glossary + **table map** (Business Capability =
`cmdb_ci_business_capability`, Business Application = `cmdb_ci_business_app`,
Information Object = `cmdb_ci_information_object`, Service Instance —
**renamed from "Application Service" at Yokohama** — = `cmdb_ci_service_auto`, …);
schema-change governance is a formal committee gate — CCB steering board + RACI, class
create/reclassify/delete owned by named roles, changes justified by a named use case;
CMDB health KPIs — **completeness / correctness / compliance / relationships** — as
configurable per-class rules; the maturity scorecard (Initial→Managed) and the CSDM
Crawl/Walk/Run/Fly ladder (Business App + App Service + relationships FIRST, Information
Object data-flow edges LAST); "once a CI, always a CI"; remediation playbooks =
Analysis play / Fix play / Data Governance play.

- INCORPORATE → terminology research: the table map is the crosswalk spine; ALSO the
  Yokohama rename warning — "Application Service" is already unstable vendor naming
  (now "Service Instance"), so DryDocs should adopt the CONCEPT (deployed instance),
  not the label. Candidate #1 refined.
- INCORPORATE (validated, no change): CCB + RACI + use-case-justified class changes is
  the industry form of our HITL gate + ontology-mapper discipline — citable validation.
- INCORPORATE → verify framing: completeness/correctness/compliance is a better public
  vocabulary for what m1/m3-verify invariants already check — candidate naming
  alignment in verify OUTPUT/docs only (no invariant changes). Chore-scale.
- PARK: maturity scorecard (a future SaaS-positioning surface); playbook triple (ops
  pattern for a future runbook).

### 5. CMDB - Process Guide.docx (asset 0001261, Dec 2025)

Key concepts: the five-activity CM process (Identify/Control/Record/Status/Audit);
IRE reconciliation is **per-attribute** — "only designated authoritative data sources
[may] write to the CMDB at the CI table AND attribute level," real-time, no staging;
**references vs relationships** — one-to-many reference ATTRIBUTES (reporting/filtering)
are deliberately distinct from graphical CI RELATIONSHIPS (topology/impact); CSDM 5.0
six domains (Foundation outside the CMDB; Build & Integration non-operational; Service
Delivery = deployed instances; a Business App MAY relate directly to an Application
Service — the SDLC layer is optional); standard **Lifecycle Status/Stage** fields;
staleness thresholds (60-day signal, 90-day manual remediation); **CMDB 360** keeps
per-source proposed-value history per attribute; separation of duties; custom-attribute
restraint ("avoid mandatory fields that provoke junk entries").

- INCORPORATE → the provenance/audit-fields plan (docs 06/06a) at its next touch (the
  JobRun-index fold idiom): per-attribute source lineage (CMDB 360 pattern) as an
  audit-envelope extension candidate. Candidate #3.
- INCORPORATE (validated, no change): references-vs-relationships = our C5-family
  property-vs-edge discipline; Lifecycle Status/Stage ≈ `active` +
  `removed_from_source_at` (D7); 60/90-day staleness thresholds are a benchmark for
  sweep-retention defaults.
- REJECT: real-time no-staging ingestion — DryDocs deliberately stages and gates.

### 6. ITAM - SAM - Product Integration Options - Yokohama.pptx (asset 0001397)

Key concepts: a Now Create partner-delivery TEMPLATE deck (its FAQ grants ecosystem
reuse for delivery); integration types — bidirectional vs **unidirectional ("one system
is considered as the Source of Record")**, live vs batch; SAM tables
(`cmdb_sam_sw_install`, `cmdb_software_product_model`, discovery-model); Software Asset
Connection feeds external discovery through the IRE (de-dup + reconciliation); the
Content Service (shared normalization); SaaS publisher packs + Okta usage.

- INCORPORATE → docs prose: the unidirectional/source-of-record integration vocabulary
  where DryDocs docs describe feeds (SoR language we already use — now citable).
- PARK: software-model normalization parallel to our software-registry (plan-07 /
  ADR 0004) — note the correspondence, no action.
- REJECT: license/entitlement management — out of DryDocs scope.

## CSDM ↔ DryDocs correspondence (the terminology-research payload)

| CSDM concept (table) | DryDocs today | Verdict |
|---|---|---|
| Business Application (`cmdb_ci_business_app`) | `:BusinessApplication` (K4) | **ALIGNED** — independently validated |
| Application Service / **Service Instance** (Yokohama) | — (implicitly: an app's batch estate) | **Gate-bound candidate** — adopt the concept, not the unstable vendor label |
| Business Capability (`cmdb_ci_business_capability`) | — | PARK (LOB ≠ capability; future) |
| Information Object (`cmdb_ci_information_object`) — "type of data interchanged between the business application and the database serving it" | `:DataAsset` + READS_FROM/WRITES_TO | **NEAR-MATCH** — annotation candidate on node_classifications (note edit at a future gate) |
| Business/Technical Service + Offerings | — | PARK (no catalog/consumption use case) |
| Product Model | `:SoftwareProduct` (ADR 0004) | Partial correspondence — note only |
| Foundation data (outside the CMDB) | Employee/Role/DevTeam reference layer | Analogous pattern, validated |
| CMDB Group / Dynamic CI Group (saved queries) | QuerySpec registry (O11) | Nice parallel — cite in O11 design |
| Lifecycle Status/Stage | `active` + `removed_from_source_at` (D7) | Partial — vocabulary comparison only |
| IRE + reconciliation rules (per-attribute) | precedence.yaml + loaders (per-source) | Aligned; per-ATTRIBUTE granularity = audit-envelope candidate |
| CMDB 360 multi-source history | provenance plan (docs 06/06a) | Enhancement candidate at next plan touch |
| Health KPIs (completeness/correctness/compliance) | m1/m3-verify invariants | Naming-alignment candidate (output/docs only) |
| CCB + RACI class governance | HITL gate + ontology-mapper | **VALIDATED** — the industry form of our gate |
| Attestation / Data Certification | — | **Gate-bound candidate** — periodic SME re-confirmation practice |

## Gate-bound / follow-up candidates (nothing adopted here)

1. **Deployed-application-instance concept** (CSDM Application Service/Service Instance)
   — node-meaning decision → its own gate, only when an environment-level use case
   lands (dev/test/prod estates). Adopt the concept; pick our own stable label.
   **RE-OPENED 2026-08-09 (K21): the trigger condition is met.** The replica carries
   `u_seal_deployment_id` beside `u_seal_application_id`, and both sit on the Application
   Service row (`cmdb_ci_service_discovered`) rather than on `cmdb_ci_business_app` — so the
   source distinguishes application from deployment and keys each, while DryDocs has one
   concept for both. See `servicenow-replica-evidence.md` §1.3(c) and §4. Still gate-bound;
   this records that the deferral's own condition has arrived, nothing more.
2. **Attestation practice** — a recurring SME re-confirmation pass over gate-accepted,
   non-discoverable facts (the Data Manager attestation model; extends D7's family).
   Process-level; groom when a cadence owner exists.
3. **Per-attribute source lineage** (CMDB 360) — fold into the provenance/audit-fields
   plan (docs 06/06a) at its next touch, alongside the parked JobRun-index idea.
4. **Verify-vocabulary alignment** — present m1/m3-verify results under
   completeness/correctness/compliance headings (docs/output only; no invariant change).
5. **Information Object ↔ DataAsset annotation** — a note edit on node_classifications
   riding a future gate session (C7 idiom).

Items 1–2 imply meaning → the gate. Items 3–5 are plan/docs-level; groom on their
recorded triggers.
