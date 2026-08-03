# DryDocs — A Governed Knowledge Graph for Batch Production Support

**White paper · Rev 1 · 2026-07-12 · Classification: Internal-Public (mechanism only — no
customer names, hosts, schedules, or identifiers appear in this document).**

---

## Executive summary

Large enterprises run their overnight business on batch estates: hundreds of thousands of
scheduled jobs, millions of configuration variables, spread across multiple data centers and
owned by dozens of teams. When a job fails at 3 a.m., the questions are always the same —
*what does this job do, what depends on it, who owns it, and when will the data be late?* —
and the answers are always scattered: in the scheduler's database, in a wiki that trailed off
two years ago, in a spreadsheet, and in the head of the one engineer who remembers.

**DryDocs turns the scheduler's own metadata into a governed knowledge graph that answers
those questions on demand** — and, where the metadata itself is wrong or missing, turns the
failures into fix packages routed to the owning team. It is built on three commitments that
distinguish it from both wiki-style documentation and generic CMDB tooling:

1. **The graph is derived, not authored.** Runbooks and dependency maps generated from the
   orchestrator's live definitions cannot go stale the way hand-written pages do.
2. **No meaning enters the graph without a human decision.** Every relationship type is
   proposed against public ontology standards and confirmed by a subject-matter expert
   through a recorded gate before a single edge loads.
3. **Every governance rule is a machine-readable ledger with a test.** Classification tiers,
   source registries, column dispositions, ontology mappings, even the cross-repo porting
   rules — each is a config file guarded by CI, not a convention in prose.

The first customer is the application-support team; the architecture is deliberately shaped
so the same graph later serves data-governance and lineage programs without rework.

## The problem

Batch production support fails in a specific, repeatable way:

- **Documentation debt.** Runbooks are written once, at go-live, by people who then move on.
  The scheduler's definitions keep changing; the pages do not.
- **Tribal ownership.** Job-naming conventions encode team, application, and schedule — but
  only veterans can read them, and the conventions drift.
- **Invisible blast radius.** Job-to-job dependencies exist as prerequisite conditions
  inside the scheduler, legible to it but not to the human deciding whether a 3 a.m. failure
  can wait until 9.
- **Metadata drift compounds.** Escalation routing keyed to stale ownership, description
  fields left empty, hard-coded hosts nobody remembers — each defect makes the next incident
  slower, and there is no loop that repairs them.

Conventional responses — more wiki pages, a CMDB import, a one-off lineage project — share a
flaw: they create a *second* copy of the truth that immediately begins to diverge from the
scheduler that actually runs the business.

## The approach: four layers, standards-grounded

DryDocs models the estate in four deliberately separated layers:

| Layer | Question it answers | What lives there |
|---|---|---|
| **1 — Taxonomy** | *What category is this?* | Pure classification imported from sources: servers, folders, jobs, applications, org hierarchy. No meaning-bearing edges. |
| **2 — Ontology** | *What do connections mean?* | A relationship vocabulary bound to public standards — W3C PROV-O for provenance and activity, W3C ORG for organizations, DPROD/DCAT for data products, SKOS for concept schemes, SOSA/SSN (experimental) for runtime observations. |
| **3 — Knowledge graph** | *What is connected, and what does it mean?* | The populated property graph: folders contain jobs; jobs require and emit conditions; derived job-to-job dependency edges; jobs attributed to registered applications and owning teams. |
| **4 — Context graph** | *What matters right now?* | Task-scoped projections under design: runtime health observations, timing statistics, maintenance windows. |

The separation is enforced, not aspirational: importers may only classify; a relationship
type must exist in the vocabulary, map to a decision-matrix row, and pass the human gate
before any loader may write it. Standards-grounding is what keeps the graph legible to
future consumers — a provenance edge means what PROV-O says it means, so a governance tool
written years from now can read the graph without archaeology.

## Architecture

```
 orchestrator DB      org / app        vendor & standards
 (read-only replica)  registries       documentation
        │                 │                  │
        ▼                 ▼                  ▼
 ┌─────────────────────────────────────────────────┐
 │ CONFIG LAYER (ledgers + tests)                  │
 │  source registry · sensitivity classification  │
 │  column dispositions · precedence · crosswalks │
 └────────────────────┬────────────────────────────┘
                      ▼
        taxonomy capture ──► ontology mapping ──► HITL GATE (SME sign-off,
                      │        (PROV/ORG/DPROD)      append-only gate log)
                      ▼
              loaders (delta provenance, audit envelope)
                      ▼
              Neo4j knowledge graph
                      ▼
 ┌──────────┬───────────┬──────────┬──────────────┐
 │ review & │ generated │ lineage  │ remediation  │
 │ verify   │ documents │ & deep-  │ (fix packages│
 │ (SME     │ (runbooks,│ doc      │  → ticketing;│
 │ toolkit) │ TDDs)     │ passes   │  no writes)  │
 └──────────┴───────────┴──────────┴──────────────┘
```

Key design decisions, and why:

- **Read-only ingestion from a replica.** DryDocs never touches the production scheduler;
  it reads a governed replica of the orchestrator's database. Vendor semantics are pinned to
  a baseline (the orchestrator's own physical model), with crosswalks planned for additional
  orchestrators so concepts normalize to one vocabulary.
- **Config-gated loads.** A source that is not registered, classified, and confirmed does
  not load — the pipeline fails closed. Each source carries a structured locator (owning
  application → platform → service → schema → object) whose sensitive halves live only in a
  private twin repository.
- **Provenance without supernodes.** Every load run is itself a graph activity; nodes link
  to the run that generated them **only when created or actually changed** (a per-row
  checksum diet), so provenance stays queryable at estate scale. Source authorship
  (who created/last changed each definition) rides a separate, gate-approved audit envelope.
- **Human-in-the-loop as an architectural element, not a review habit.** The gate is a
  rendered page with numbered confirmations; the decision is transcribed to an append-only
  log; statuses flip only then. AI agents prepare gates and apply outcomes — the SME
  decision itself is never automated.
- **Component topology with an enforced boundary.** A slim core (models, parsers, config,
  driver) is imported by independent components — loading, review, lineage, documentation
  generation, remediation — and a default-deny test fails the build if any module goes
  unclassified or components entangle.

## What the graph does on day one

- **Generated runbooks.** For a data series or application: the jobs involved, their
  schedule windows, upstream/downstream dependencies, ownership and escalation — assembled
  from live definitions, re-generated as they change.
- **Blast-radius and ETA questions.** *If this job fails, what is downstream?* is a graph
  traversal; *when will the data actually land?* is a critical-path computation over
  observed run statistics — deliberately not a naive path sum.
- **Maintenance-window planning.** Host and host-group topology plus normalized job timing
  yields the quiet window for patching a given server — with definition-time claims
  cross-validated against observed runtime placement, so disagreements surface as metadata
  findings instead of surprises.
- **Failure-driven metadata repair.** Where the graph exposes defects (empty descriptions,
  stale routing, hard-coded hosts), a remediation component builds corrected greenfield
  definitions, proves equivalence offline, and hands a package to the owning development
  team via ticketing. Separation of duties is structural: support authors, developers
  deploy, and the next ingest confirms closure. The component writes neither production nor
  the graph.

## Governance and trust model

Two independent axes govern every artifact:

- **Sensitivity** (publish boundary): External / Internal-Public / Internal /
  Internal-Confidential. The public repository carries *mechanism* — schemas, rules, code,
  sanitized examples; real identifiers exist only in internal twins. The boundary is
  enforced by tests and CI, not etiquette.
- **Trust** (epistemic provenance): every ingested corpus is tiered VERBATIM / GROUNDED /
  SYNTHESIZED, so AI-assisted inference is never silently promoted to vendor or source
  ground truth.

The same ledger-plus-test pattern governs process itself: the ontology mapping file, the
backlog, the column dispositions, and the cross-repository porting rules are each
machine-readable and each guarded by a test that fails on drift. The operating experience of
the project is that the guarded surfaces stay clean and the unguarded ones are where
incidents happen — so surfaces get guards.

## Operating model

DryDocs is developed in a two-repository pattern: a public **producer** carrying the
sanitized, generalizable platform, and a private **consumer** carrying real wiring and data.
Work ports one way through a machine-readable disposition manifest (which paths apply
wholesale, which are consumer-canonical, which merge entry-by-entry); the consumer's
enhancements return only as re-derived, sanitized mechanism. The end-state goal is a
standalone template another organization can adopt: bring your orchestrator replica and org
registries, keep your identifiers private, inherit the governance machinery intact.

AI agents (with scoped skills for the orchestrator's schema, the graph platform, ontology
standards, and document generation) do the preparation, porting, and drafting; humans make
the calls that change meaning. The gate log is the audit trail that the division held.

## Roadmap

Near-term: runtime-statistics supplement and the maintenance-window query; application
attribution end-to-end; document-ingestion (vendor + internal guidance corpora) behind the
same trust tiers; a web console over the graph. Forward positioning: the ontology's
standards-grounding (DPROD data products, qualified attributions, primary-source provenance)
is the bridge to enterprise data-governance alignment — optionality that costs nothing now
and avoids a remodel later.

## Conclusion

The scheduler already knows what runs, what depends on what, and who owns it. DryDocs makes
that knowledge legible, governed, and self-repairing: derived instead of authored, gated
instead of guessed, tested instead of trusted. Support teams get answers at incident speed;
the organization gets a graph it can defend.

---

*Prepared from the DryDocs producer repository at rev `40fe038` (2026-07-12). Structure
follows the project documentation skill's architecture-doc principles; a dedicated
white-paper guideline is a noted gap in that skill.*
