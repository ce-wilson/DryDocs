# Changelog

All notable changes to DryDocs are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/) (see [VERSIONING.md](VERSIONING.md)).
Bracketed ids reference `docs/restructure/backlog.yaml`.

## [Unreleased]

_Nothing yet._

## [0.3.0] - 2026-07-09

First tagged release. Back-filled from the restructure plan (phases 0–11); `0.1.0` was the
project-init stub and `0.2.0` was skipped, so this entry covers all work to date.

### Added

- Four-layer conceptual model (taxonomy → ontology → knowledge graph → context graph), the
  external/internal split, the config layer, the publish boundary, and the layer-owner
  sub-agents. [phase 0]
- Taxonomy capture as pure classification: Control-M folders/jobs/conditions, SEAL business
  applications, the LOB→Product→Team hierarchy, and the Oracle schema shape template. [B1–B4]
- Ontology mapping through the HITL gate: Control-M edge semantics, SEAL DPROD/ORG terms, the
  catalog hierarchy, and a reconciled relationship vocabulary with a drift guard. [C1–C4]
- Config-driven loaders: `precedence.yaml`-resolved reconciliation and a fail-fast gate that
  refuses unconfirmed sources. [D1–D3]
- Multi-database Neo4j topology (`drydocs` + `drydocs_context` + a composite) with proxy-node
  constraints, deployed live on the Docker Enterprise container; core-package extraction behind a
  boundary shim; the depgraph Control-M parser deltas folded into the core parser (including a
  `spark-submit` script-resolution fix). [G1, G2, G5–G8]
- Offline reproduction of the SME-review / HITL toolkit: `graph_verify`, `review_labels`,
  `graph_review`, `sme_notes`, the gate-page generator, and a publishing pipeline with a pluggable
  publisher — all behind a default-deny module boundary. [H1–H7]
- Repo-native planning infrastructure: backlog schema v2 with a validator, the rendered HTML
  project board, the `groom-backlog` skill, and a session-ritual regen hook. [I1–I4]
- Documentation infrastructure: a canonical TDD outline + completeness/traceability validator, a
  deterministic Markdown→HTML/PDF renderer (the `.md` is the single source), and both HITL markup
  loops — digital (per-anchor save button) and paper (print-margin anchors + a scan→transcribe
  skill). [L1, L3–L6]
- SEAL application-attribution edge registered (`planned`) with a mapping proposal. [K1]
- Provenance-edge diet: `WAS_GENERATED_BY` written only on record create/change, plus the
  Control-M source audit envelope. [M1]
- Source column-mapping ledger: schema, typed accessor, and the Control-M ledger. [N1]
- BMC Control-M docs lexical loader (Document→Chunk, `llm-graph-builder` pattern), gate-accepted
  and loaded live — the P0 spike of the doc-ingestion track.

### Changed

- Renamed `:JobFolder` → `:ControlMFolder` repo-wide (ADR 0003) with a migration.
- Retired the derived job→job `:DEPENDS_ON` edge in favor of `:WAS_INFORMED_BY`
  (vocab `m3_was_informed_by`).

### Infrastructure

- Adopted Semantic Versioning ([VERSIONING.md](VERSIONING.md)); this is the first annotated git
  tag. [J3]
- Swept iteration-era naming drift and superseded-doc banners. [J1]

### In progress (not complete at this tag)

- Context-graph pilot (Epic E), orchestrator expansion (Epic F), remaining component-topology work
  (G3–G4, G9), SEAL attribution loader + reshape gate (K2–K3), doc-context ingest + runbook
  capstone (L7–L9), provenance / column ledgers (M2–M4, N2), and the ontology same-row-derived rule
  (C5) + `REQUIRES_SCHEDULER` registration (C6).

[Unreleased]: https://github.com/ce-wilson/DryDocs/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/ce-wilson/DryDocs/releases/tag/v0.3.0
