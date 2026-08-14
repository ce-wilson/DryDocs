# Design comparison — GitNexus vs the DryDocs code-graph approach (depgraph)

**Status:** Evaluation (no decision taken here; adoption items are grooming candidates for
`IDEAS.md` / the backlog, gate-bound where they touch ontology).
**Date:** 2026-08-14.
**Classification:** Internal-Public (analysis of a public external repo; no internal data).
**Subject:** [GitNexus](https://github.com/abhigyanpatwari/GitNexus) @ `28187bb`
(2026-08-14), cloned to `C:\coding\projects\sandbox\GitNexus` for this review.
**Our side:** [`depgraph`](../../../depgraph) v0.1.0 (sibling repo, stdlib-only) + the
`knowledge/depgraph-snapshots/` drift ritual + the DryDocs estate KG it feeds.
**Method:** `/architecture` evaluation — read GitNexus `ARCHITECTURE.md`, `CLAUDE.md`,
repo layout; read depgraph `README.md`, `CONTINUATION.md`, snapshot README. No code
executed from the cloned repo.

---

## 1. Context — these are different tools that happen to share a noun

Both build "a code knowledge graph," but their primary jobs differ, and the comparison
is only honest with that stated first:

| | **GitNexus** | **depgraph (ours)** |
|---|---|---|
| Primary job | Symbol-level code intelligence for agent-assisted development (impact-before-edit, graph-backed review) | (1) Control-M-seeded **ETL lineage inventory**; (2) post-push **structural drift snapshots** of DryDocs |
| Grain | Symbol (function/method/class), optionally statement (`--pdg` basic blocks) | File (import edges) + directory tree; ProcessNode/DataAssetNode at the lineage layer |
| Languages | 16 via tree-sitter + unified capture tags | Python (`ast`) for imports; any-language file tree; Control-M `cmd_line` parsing |
| Store | LadybugDB embedded per-repo (`.gitnexus/`), Cypher-queryable, no server | Machine-first JSON → *profiles* → idempotent Cypher for a target Neo4j **or** self-contained offline HTML |
| Stack / footprint | TypeScript monorepo, npm, worker pools; ~2,300 TS files | Python stdlib-only, zero dependencies, runs on a locked-down offline server |
| Query surface | 17 MCP tools + HTTP API + CLI + web UI | CLI + generated Cypher + static HTML review page |
| Scale proof | Self-indexed: ~249k symbols / 565k relationships; Linux-kernel-sized repos via disk-backed worker streaming | DryDocs scan: 37 files / 70 edges; 13-job Control-M sample → 25 processes |
| Governance | Confidence scores on edges; no human gate | HITL gate, trust axis, classification, SME curation — the whole DryDocs discipline |

GitNexus is roughly two orders of magnitude more machinery, aimed at a problem DryDocs
does **not** have (understanding arbitrary application code at symbol grain so agents can
edit it safely). depgraph's constraints — stdlib-only, offline, SME-consumable static
HTML, Neo4j-optional — exist because of where it must run; GitNexus assumes npm and an
embedded native DB. **Neither replaces the other.** The value here is pattern transfer,
plus one direct-use question (§4).

## 2. Where GitNexus is genuinely ahead (and whether it matters to us)

1. **Typed phase DAG with declared deps.** 19 phases, Kahn-validated, each phase
   receiving *only* its declared upstream outputs (the runner filters the results map to
   prevent hidden coupling), per-phase timing, cycle diagnosis with the concrete path.
   depgraph's extractor/profile registries are flat; DryDocs' `CANONICAL_LOAD_SEQUENCE`
   is an ordered list. *Matters:* yes, as the loaders multiply — declared-deps is cheap
   discipline that makes hidden coupling a type error instead of a code review catch.
2. **Epistemic honesty as a first-class output.** Unresolved call receivers are censused,
   not dropped: `impact`/`context` publish `epistemic: 'exact' | 'lower-bound'` with a
   machine-readable `causes` split, and the agent rules hammer that `UNKNOWN ≠ low risk`
   ("an empty caller set is not evidence the symbol is unused"). Their route extractor is
   precision-weighted by doctrine: *"A missing route is a coverage limit; an invented one
   is a lie."* *Matters:* strongly — this is the same philosophy as the DryDocs trust
   axis, taken one step further: our query answers (runbook fields, lineage walks,
   `impact`-style blast radius over job chains) do not yet declare whether they are
   exact or a lower bound. That is directly adoptable and ontology-cheap (a property on
   the *answer*, not the graph).
3. **Purpose-built agent tools over the graph.** Not just `cypher`: `impact`, `context`,
   `trace`, `detect_changes`, `route_map` — verbs an agent can hold. Their skills make
   the graph the *mandatory* first step of every edit. *Matters:* yes — our
   `neo4j-drydocs` MCP exposes generic Cypher, and `drydocs_api` QuerySpecs already
   encode the reviewed queries; the missing piece is exposing those specs as named MCP
   tools so agents (and the support workflow) call `impact`-shaped verbs instead of
   composing Cypher.
4. **Process/community layer.** Leiden communities + synthesized `Process` nodes
   ("execution flows," 918 in their self-index) give agents a navigable mid-scale between
   file and symbol. *Matters:* moderately — DryDocs' analog (job chains / data series via
   Control-M conditions) is *declared* by the orchestrator rather than mined, which is
   better data than they have. The transferable bit is the packaging: named, enumerable
   process resources (`.../processes`, `.../process/{name}`) as a first-class query
   surface, which is what the runbook work already circles.
5. **Hybrid retrieval, local-first.** BM25 + vector merged by Reciprocal Rank Fusion;
   embeddings are **Snowflake arctic-embed-xs, 384-D, local, incremental by content
   hash**, opt-in, and skipped above 50k nodes. *Matters:* as validation — this is an
   independent production system landing on the same shape our P4 revision just chose
   (local 384-D model, embeddings optional, fulltext as the always-on arm). RRF is worth
   noting for the eventual hybrid retriever; incremental-by-content-hash matches our
   `sha256` envelope design.
6. **Staleness as a surfaced contract.** Indexed `lastCommit` vs `HEAD` produces hints at
   query time. depgraph snapshots already pin provenance harder (the U7/U15
   subject-vs-instrument split GitNexus has no equivalent of — our meta header is the
   better design), but nothing *warns at read time* when a snapshot or the estate graph
   trails reality. *Matters:* small, cheap, real.

## 3. Where our approach is ahead (do not trade these away)

- **Governance.** GitNexus has confidence floats; DryDocs has a gate, a trust vocabulary,
  classification, precedence, and SME curation. For an estate KG that answers production
  support questions, that is the moat, not overhead.
- **Provenance of the measurement itself.** The snapshot meta header records what was
  measured *and what measured it* (instrument commit, dirty/untracked split, capability
  probe with refusal). GitNexus records `lastCommit` only.
- **Offline portability.** stdlib-only + static HTML + version-targeted Cypher runs where
  the company actually needs it. GitNexus cannot follow us there.
- **Declared orchestration beats mined communities** for our domain: Control-M is ground
  truth for what runs together; Leiden is a heuristic reconstruction GitNexus needs
  because application code declares no processes.

## 4. The direct-use question: GitNexus *on* the DryDocs repo (producer side)

Separate from the estate KG entirely: GitNexus supports Python, runs locally, and its
`impact` / `detect_changes` / `rename` discipline targets exactly the risk our working
agreements handle by convention (module-boundary tests, verify-before-assert). A
producer-side trial — index the DryDocs repo, wire the MCP server, use `impact` before
refactors of `drydocs_core` — is cheap to run and would answer whether symbol-grain
impact analysis earns a place beside the depgraph drift ritual. It does **not** replace
depgraph: different grain, different environment reach, and the snapshot series' value
is its committed history. Risks to check in the trial: Windows worker-pool behavior,
index time on our repo, and that `.gitnexus/` stays out of git (their analyzer edits
`.gitignore` itself — verify against our publish boundary).

## 5. Adoption recommendations (ranked; grooming candidates, not decisions)

| # | Recommendation | Effort | Where it lands |
|---|---|---|---|
| R1 | **Epistemic labeling on query answers** — `epistemic: exact\|lower-bound` + `causes` on lineage/impact-style QuerySpec responses (unparsed `cmd_line`s, unresolved invocations, gate-pending edges are our `causes`) | S–M | `drydocs_api` / depgraph JSON assertions |
| R2 | **Named agent verbs over QuerySpecs** — expose reviewed specs as purpose-built MCP tools (`impact`, `context`, `trace` analogs for jobs/series/assets) instead of generic Cypher only | M | `drydocs_api` + MCP config |
| R3 | **Declared-deps extractor DAG in depgraph** — extractors/profiles declare `deps`, runner validates and passes only declared outputs (Kahn + cycle path, per-phase timing), ahead of the lineage forks multiplying | S | `depgraph` |
| R4 | **Read-time staleness hint** — estate queries and snapshot HTML surface "indexed at commit X, HEAD is Y" | S | depgraph html profile / `drydocs_api` |
| R5 | **Producer-side GitNexus trial on the DryDocs repo** (§4) — evaluate `impact`/`detect_changes` for our own development loop | S trial | dev tooling only; no graph/ontology contact |
| R6 | **RRF noted for the eventual hybrid retriever**; local-384-D + content-hash-incremental embeddings stand confirmed by an independent implementation | — | note on the P4 revision / retrieval follow-on |

Explicitly **not** recommended: adopting LadybugDB or the TS pipeline (wrong environment,
wrong grain, duplicates Neo4j); mining communities (Control-M already declares our
processes); symbol-level parsing of estate application code (our unit of support is the
job/script/asset, and the SME gate could not absorb symbol-grain volume).

## 6. Consequences

- *Easier:* agent consumption of the estate graph (R2), honest partial answers (R1),
  safer growth of depgraph's extractor set (R3).
- *Harder:* nothing structural — every recommendation is additive at the API/tool layer;
  R1 touches answer shapes, so `drydocs_api` consumers re-read one field.
- *Revisit:* if the R5 trial succeeds, whether `detect_changes` supersedes any part of
  the snapshot ritual (unlikely — provenance history vs point-in-time diff — but check).

## 7. Action items

1. [ ] Groom R1–R5 into `IDEAS.md` → `backlog.yaml` (R1/R2 likely one epic; R3 is a
       depgraph-repo item, not DryDocs).
2. [ ] Decide keep/delete of the clone at `sandbox/GitNexus` (it is reference material,
       not a dependency; this doc records everything cited).
3. [ ] Add a one-line pointer to this review from `reference/research/README.md` if the
       R5 trial proceeds (external tool evaluation precedent).
