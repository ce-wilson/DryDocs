# Changelog

All notable changes to DryDocs are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/) (see [VERSIONING.md](VERSIONING.md)).
Bracketed ids reference `docs/restructure/backlog.yaml`.

## [Unreleased]

Everything since `v0.3.0` (2026-07-09). Not yet cut as a release; the version in
`pyproject.toml` still reads `0.3.0` until the release ritual runs.

### Added

- **Web console + thin read API (Epic O, phases 1–12 complete; O20 gate signed off).**
  Launchable React site (`web/`) on a shared module template — Explorer, lineage DAG,
  mappings stewardship, ownership rollup, loads timeline, runbooks/remediation, docs corpus
  map, gates record, and an admin config-traceability lens with a generated enforcement
  matrix. QuerySpec registry with two-path export + provenance manifests [O11]; persona
  sign-in with role-gated views [O2]; GraphAccess seam — API adapter primary, bolt dev-only
  per ADR 0005 [O4–O6]; `drydocs_api` read-only FastAPI component [O5]. Write-shaped
  surfaces stay HITL: SEAL-contacts override list as an origin-flagged store [O24] and gate
  pages that draft their own gate-log entry client-side [O25].
- **Mapping store** — SQLite materialization of the mapping layer (M0–M4 of the 07-17 plan),
  steward endpoints, changeset artifacts, and the O13 live demo.
- **Component split executed** — `drydocs_core` physical extraction [G2]; scaffolds for
  `drydocs_lineage` + `drydocs_deepdoc` [G4]; `drydocs_remediation` built in-monorepo
  (M0 PoC, R1 detector, Tier-1 transform engine, Jira handoff, corroboration) [G3, ADR 0002-B];
  depgraph lineage re-home [G9, ADR 0002-C] with extractor coverage accounting [G11].
- **Lineage seams** — live CMDLINE pattern closure, DPL launcher argument contract [G15],
  FACT_REGISTRY ETL canonicals + value contracts [G16], DPL MAC ingest seam (dataset-flow
  candidates, kind discriminator, SEAL facts) [G17]; rua-extract ingest phase groomed behind
  a gate [G18–G25].
- **SEAL attribution live** — K2 match-policy gate + loader (`m3_seal_app_ref` ACTIVE,
  `WAS_ASSOCIATED_WITH` edges); BusinessApplication entity reshape executed via K3/K4
  (qualified attribution, TOMRole scheme, `:Application` → `:BusinessApplication`);
  K5 Product Cabinet attribution; manual-CSV tier-5 final option.
- **Platforms taxonomy resolved** — C11 company-confirmed capture, C12 gate signed off
  (SchedulerKind retires into the software-registry model), C13/C14 builds executed.
- **Provenance diet executed** — M2 migration HITL-confirmed and run live (blanket-edge
  cleanup, raw-prop retirements, renames; m3-verify green) [doc 06 Phase 3].
- **Source gates + probes** — CM_HOSTS host-topology and CM_AVG_RUN runtime-supplement gates
  signed; `add-source-object` skill; P1 probe readout transcribed (preflight + CM_AVG_RUN
  answered end to end; CM_HOSTS definition probes + DC scope call still owed).
- **Doc system completed (Epic L)** — SME-feedback panels + per-subsection annotation
  [L10–L11], single screen+print render surface [L13], review outline as the third doc type
  with exemplar-pin tests [L15]; runbooks for startup/refresh, web console, mapping demo,
  and lineage MAC ingest.
- **Infrastructure** — CI [J5] + testcontainers e2e [J9]; `config/dev-environment.yaml`
  drift-guarded dev topology; PORT-MANIFEST.yaml as the machine-readable port authority;
  Essential GraphRAG lexical load + traversal experiment [Q1–Q2].

### Fixed

- **A render run from a git worktree no longer writes into the main checkout
  [Idea-109].** `drydocs` is installed editable — a `drydocs.pth` pinned at the main tree
  — so modules that anchored their default paths on `Path(__file__)` named the main tree
  from anywhere, and `python scripts/render_board.py` puts `scripts/` on `sys.path[0]`
  without the cwd, so a worktree's own `drydocs/` was never shadowed in. The damage was
  *partial*, which is what made it silent: the five sibling scripts `render_board.py`
  invokes anchor on their own `__file__` and wrote to the worktree correctly, while
  `board.html`, `ideas.html` and `roadmap.html` routed through the installed package and
  landed in main — one command, one torn render, two trees, and the worktree left clean.
  Two agents hit this independently on 2026-08-11. New `drydocs_core/repo_paths.py`
  resolves the checkout containing the cwd (nearest enclosing `.git`, validated as a
  DryDocs tree so a sibling or parent repo can never capture the paths) and falls back to
  the old `__file__` anchor whenever the cwd is outside a checkout, so installed-package
  consumers are unaffected. Adopted by `plan_board`, `plan_ideas` and `plan_roadmap`;
  package-internal resources such as `drydocs_core/schema/*.cypher` deliberately keep the
  `__file__` anchor, since those travel with the package. `tests/unit/test_repo_paths.py`
  drives a real `git worktree` through a real render and asserts the main tree comes back
  byte-identical — verified to fail without the fix. The remaining `_REPO_ROOT` sites
  outside the render ritual are catalogued in `Idea-109` and not yet converted.

### Changed

- **One verified `apply-supplements` verb replaces the five per-file supplement verbs
  [G29].** The chain is now data — `drydocs_core/schema/supplements.py` holds the single
  ordered registry (base → seal → catalog → registry, SOSA opt-in behind `--with-sosa`) —
  so the load-bearing order (**seal before catalog**: catalog reuses seal's `:Attribution`
  class and `#hasAgent` term) can no longer be typed wrong; the `run-drydocs` skill had in
  fact listed it backwards. Each file is applied *and verified*: every `:OntologyTerm` IRI
  the `.cypher` declares must be present afterwards, so a truncated or renamed supplement
  fails at the apply instead of surfacing later as a loader MATCH quietly matching zero
  `:Role` nodes. The run writes a `load.supplement.<stamp>.log` envelope — the first
  supplement/bootstrap verb to write a run log at all. All five legacy verbs remain as
  delegating aliases and inherit both the verification and the log.
- `drydocs_core.cypher_split` gained `strip_comments()`, so the supplement IRI parser reads
  code only — a commented-out MERGE (how a term is retired) is not mistaken for a term the
  graph is then required to hold.
- **Curated lineage residency ruled: it lands in `drydocs` [G30].** Four `drydocs_api` query
  specs read `ddlineage` while `drydocs_lineage.writer` pinned `drydocs` and refused anything
  else — the specs had followed G1 provisioning, the writer had followed ADR 0002 D1/D2, and
  the ADR was never amended when G1 added a fourth database two days after it was accepted.
  Ruled for the ADR (written up as its "Residency clarification"; not an amendment): the
  curated writer MATCHes `:ControlMJob` nodes the M3 load owns in `drydocs` and deliberately
  never MERGEs them, and a transaction cannot span databases — so writing lineage into
  `ddlineage` would silently drop every job-endpoint edge. The specs repoint to `drydocs`;
  `ddlineage` stays provisioned and composite-aliased, documented as provisioned-for-later,
  with a named trigger to revisit through the gate. `tests/unit/test_database_names.py` now
  asserts no spec reads a database nothing writes.
- Main history squashed to a fresh "Initial import" root (2026-07-20); pre-squash history
  preserved locally under the `archive/old-history-2026-07-20` tag.
- Port prompt rolled to the v2 rolling format (steps 1–42 frozen in the archive doc).

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
- Multi-database Neo4j topology (`drydocs` + `ddcontext` + a composite) with proxy-node
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
