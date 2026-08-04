# ADR 0006 — docmeta is its own component: proactive doc ingestion, the docs database, and the doc-graph vocabulary

```yaml
status: ACCEPTED        # gate-confirmed 2026-07-18, SME accepted as written (config/gate-log.md, Q4)
date: 2026-07-18
deciders: [chad.wilson, SME-gate]
layer: component-boundary + 2-ontology
affects:
  - knowledge/upgrade-plans/docmeta-component.md   # the plan this ADR ungates (P2+)
  - drydocs_core/ontology/relationship_vocabulary.yaml
  - MODULE_MAP.md + tests/unit/test_module_boundary.py   # Q6: new COMPONENT_GROUP
  - drydocs_core/schema/provisioning/               # the new docs database
  - docs/restructure/backlog.yaml                   # Q4 (this gate) -> Q5/Q6
```

## Context

The docmeta P0 benchmark verdict (2026-07-16,
`knowledge/upgrade-plans/docmeta-p0-verdict.md`) recommends **BUILD**: graph
traversal over the lexical Document→Chunk corpus beat manifest-routed markdown
~27× on retrieved-context cost at equal-or-better recall (12 fixed questions,
3 live arms). The component plan (2026-07-06,
`knowledge/upgrade-plans/docmeta-component.md`) deliberately reserved four
decisions for this gate: component identity, database target, the doc-graph
relationship entries, and the curation-ladder→gate mapping.

Two facts changed since the plan was written:

1. **The lexical chunk shape is already gated and ACTIVE.** The
   bmc-docs-lexical-load gate (2026-07-08) activated `docs_chunk_part_of`
   (`(:Chunk)-[:PART_OF]->(:Document)` — the llm-graph-builder direction),
   `docs_first_chunk`, `docs_next_chunk`, and `docs_describes`
   (`(:Document)-[:DESCRIBES]->(:SoftwareProduct)`), proven twice (bmc-docs
   2026-07-08; the Q2 Essential-GraphRAG load). The plan's provisional
   `HAS_CHUNK` list predates this.
2. **The live database naming convention is `dd*`.** The deployed multi-DB
   topology (G6/G7) runs `drydocs`, `ddlineage`, `ddcontext`, `ddall` — the
   plan's working name `drydocs_docs` predates the deploy.

## Decision

1. **docmeta is its own component (`drydocs-docmeta`), NOT a deepdoc fold-in.**
   Different duty cycles: docmeta is a proactive, registry-driven,
   refresh-cadence corpus pipeline; `drydocs-deepdoc` (reserved by ADR 0002 C3)
   is a reactive on-failure investigator. Different write targets: docmeta
   writes the docs DB for confirmed content (T4 → `ddcontext` only); deepdoc
   writes `ddcontext` only. Deepdoc becomes a *consumer* of docmeta's corpus
   (its deep dives cite Document/Chunk nodes). The `drydocs-docmeta` module
   registry entry drops its "working name" caveat.

2. **The docs corpus gets its own database: `dddocs`** (the plan's
   `drydocs_docs`, renamed to the live `dd*` convention). Provisioned via the
   G1 pattern (`CREATE DATABASE` + composite membership + uniqueness on
   `Document.doc_id`, `Chunk.chunk_id`), keeping docs out of the structural DB
   so core destroy/rebuild freedom survives. The bmc-docs + software-registry
   corpus currently demonstrated in `drydocs` re-targets to `dddocs` at the P4
   loader build (a reload, not a migration — the loaders are idempotent); the
   Q2 book corpus stays in `ddcontext` (experiment/reference content, per its
   recorded decision).

3. **Doc-graph vocabulary, reconciled — no double registration.**
   - `HAS_CHUNK`: **superseded** by the ACTIVE `PART_OF`/`FIRST_CHUNK`/
     `NEXT_CHUNK` shape — not registered; the plan's model diagram is updated
     by this ADR rather than re-shaping a gated, twice-proven model.
   - `DESCRIBES` (Document→SoftwareProduct): **already ACTIVE** — unchanged.
   - **NEW, `status: planned`** (gate-bound until the P4+ builds wire them):
     `docs_has_document` — `(:DocSource)-[:HAS_DOCUMENT]->(:Document)`, with a
     new `DocSource` node classification (`dd:DocSource`, prov Entity; the
     registry entry materialized as a node, DCAT-catalog-shaped);
     `docs_governed_by` — `(:Document)-[:GOVERNED_BY]->(:OntologyTerm)` where
     the registry's `taxonomy_path` is declared.
   - Chunk-level `DESCRIBES` to proxy nodes (`ControlMJob`, `DataAsset`) is
     **deferred to its own gate** when content-extraction is designed (P4+) —
     extracting edges from doc content is exactly the ontology decision the
     layer rules route through a gate, and its shape is unknowable before the
     extractor exists.

4. **Curation ladder → HITL gate mapping** (bkup's `curation_status` onto the
   restructure's gate): `unapproved` → pre-gate; `ai_generated_review_needed`
   → gate-queued; `approved_by_sme` → confirmed. Registry `curation:` field
   drives it: `none` (T1 vendor docs), `sme-confirm` (T2/T3),
   `sme-confirm+confidential` (T4). Freshness is gate-preserving: a sha256
   change on refetch RE-QUEUES curation — a changed page never silently
   overwrites confirmed content.

5. **Adopted from the P0 verdict** (its "what the ADR should adopt" list):
   the lexical graph is the spine (active `docs_*` vocabulary + navigation
   properties); ch.8's evaluation harness (RAGAS-style, Cypher-as-ground-truth,
   per-stage failure attribution) becomes the component's own gate; a fulltext
   index is standing infrastructure; embeddings/vector is a **pluggable arm
   gated on the open LLM-key-strategy decision** (parent-document shape +
   out-of-scope threshold test when built); query-time hygiene (front/back
   matter down-ranked, abstention scored); the manifest stays the provenance
   source of truth and fallback retrieval path.

## Consequences

- Q5 builds `config/doc-source-registry.yaml` against this ADR's field
  semantics (`target_db: dddocs | ddcontext`, `curation:` ladder).
- Q6 builds the `drydocs/docmeta/` package under the confirmed name with its
  own COMPONENT_GROUP; the modules-registry comment updates from "working
  name" to final.
  > **Amendment, 2026-08-04 (Q6, path only — the decision stands):** the package
  > landed at **`drydocs_docmeta/`**. The `drydocs/docmeta/` path was inherited
  > from the plan, which predates the Phase B relocate; every component created
  > after it is a top-level package. The confirmed NAME (`drydocs-docmeta`), the
  > separate-component ruling and the COMPONENT_GROUP requirement are unchanged,
  > so this is recorded as a note rather than a body edit (the ADR 0002 banner
  > precedent).
- The two planned vocabulary entries sit gate-bound until their loaders exist
  (the K2 flips-are-follow-ups pattern); nothing flips active in this ADR.
- The docmeta plan's §1.1/§2 provisional names (`drydocs_docs`, `HAS_CHUNK`)
  are superseded by this ADR; annotate, don't rewrite history.

## Gate record

Gate session 2026-07-18, in-session (config/gate-log.md "docmeta component +
doc-graph gate"). SME (chad.wilson) accepted all four decisions AS WRITTEN on
the recommended options: separate component / `dddocs` / reconciled vocabulary
set / curation ladder + P0 adoptions.
