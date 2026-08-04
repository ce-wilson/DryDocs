# DryDocs — agent operating guide

**DryDocs is a production-support / development-support knowledge graph for D&A batch
processing.** It answers: *what runs, what it depends on, who owns it, which application
it belongs to* — and increasingly, *what matters right now for this support decision.*

This file is the routing brain. Read it first. It tells you **which layer you are working
in**, **which external reference to call**, and **which sub-agent owns the task**.

---

## 0. How to work — surfaces, backlog, session ritual

**The git repo is the single source of truth. Surfaces (Claude Code, Cowork, Projects, remote)
are lenses onto it, not separate workspaces.** Git is the cross-platform sync layer — pull at
the start, push at the end, and every machine stays identical.

**Git model (branch discipline; the two meanings of "port").** `main` is the trunk. Two unrelated
things share the word *port* — never conflate them:
- **Cross-repo port** — producer `ce-wilson/DryDocs` → company `<org>/DryDocs` ([`git-readme.md`](git-readme.md)):
  apply commit ranges onto the other repo's *disjoint* `main`. This is **not** a branch operation here.
- **Within-repo branch → `--no-ff` merge → delete.** Branch (`feat/`, `fix/`, `port/`) when: you are
  **bringing external work IN** (scraper re-home, reconcile-port, any "repoint" — *always* branch these);
  a multi-commit stream / epic slice you want to review or revert as a unit; risky / experimental /
  parallel work; anything an agent does in a worktree/fork; or anything you want as a PR.
- **Default:** small, verified, sequential work commits **directly on `main`** (the repo's linear norm).
- **Branch guardrail (this is what prevents the main-vs-branch mix-ups):** ALWAYS run
  `git branch --show-current` immediately before committing and name the target branch — HEAD can change
  between turns, agents, worktrees, or forks, so never assume it persisted. Wrong branch → stop and confirm.

**Where to work, by output type:**
- output is a **commit** → **Claude Code** (CLI/desktop/IDE). All repo work, running the
  pipeline, the HITL gate, and **dispatching the sub-agents** happen here (the `.claude/agents/`
  only exist here).
- output is an **artifact/document** (SME interview, deck, diagram, research) → **Cowork**;
  the result comes back as a commit.
- output is a **captured thought** → append to [`docs/restructure/IDEAS.md`](docs/restructure/IDEAS.md)
  (the idea inbox). Use **Projects** for this when away from the repo.

**The backlog (what agents pull from):**
- [`docs/restructure/backlog.yaml`](docs/restructure/backlog.yaml) — machine-readable source of
  truth (schema `drydocs.backlog.v2`, guarded by `tests/unit/test_backlog.py`). The human view is
  the rendered board [`docs/plan/board.html`](docs/plan/board.html) (`02-backlog.md` is the legacy
  text view); `IDEAS.md` is the inbox, groomed into the yaml via the **`groom-backlog` skill**.
- **Pull rule (give this to a sub-agent verbatim):** *"Take the next `status: todo` item in
  `backlog.yaml` whose every `depends_on` is `done`; **commit and push** `status: in_progress`
  **before starting work**; do exactly that item, staying inside your layer; meet its
  `acceptance`; set it `done`."* Anything ambiguous → the HITL
  gate ([`docs/restructure/03-hitl-sme-flow.md`](docs/restructure/03-hitl-sme-flow.md)), never auto-decided.
  **Pushed, not merely committed — why:** `backlog.yaml` status is the only claim channel between
  concurrent sessions on the two machines, and git is the only sync layer, so a local-only claim is
  invisible to the other machine. This is not hypothetical: on **2026-07-28 two sessions independently
  built C19 about ten minutes apart.** Same at the close — push `done`, don't sit on it.

**Session ritual (keeps every platform aligned):**
1. **Start:** `git pull` → read this file → read `backlog.yaml`, pick the next ready item.
2. **During:** the in-session Task list is *ephemeral* working memory for the one item — distinct
   from the durable `backlog.yaml`.
3. **End:** update the item's `status`, **regenerate the board** (`poetry run python scripts/render_board.py`)
   **and the design docs** (`poetry run python scripts/render_design_doc.py docs/design/*.md` — `.md` is the
   source of truth, the single `.html` (screen + `@media print`; L13) is a deterministic render; Epic L) — `snapshot.ps1` does
   both — then commit + `git push`, then **run `knowledge/depgraph-snapshots/snapshot.ps1`** (writes
   `<project>-<date>.json` with a git-commit `meta` header for drift comparison — see
   [`knowledge/depgraph-snapshots/README.md`](knowledge/depgraph-snapshots/README.md); view with
   `viewer.html`). Anything unfinished or newly noticed → `IDEAS.md`.
   *Stale-render check (renders are deterministic):* re-render, then `git diff --quiet docs/plan/board.html`
   (and the `docs/design/*.html`, `web/src/generated/gates.json`, `web/src/generated/enforcement-matrix.json`,
   `web/src/generated/load-map.json`, and `docs/plan/load-map.html` — a default-paths `render_board.py` run
   refreshes gates.json, the matrix, and both load-map surfaces too; J17/J20/N4/N5) — any diff means
   a committed render didn't match its source; commit the refresh.

---

## 1. The four layers (read this before modeling anything)

DryDocs is built in four conceptual layers. Most past confusion came from collapsing them.
Keep them distinct. (Grounded in the Neo4j taxonomy/ontology/knowledge-graph/context-graph
series — see `docs/restructure/00-conceptual-model.md`.)

| Layer | Answers | Where it lives | Owner agent |
|-------|---------|----------------|-------------|
| **1. Taxonomy** | "What *category* is this?" | `config/taxonomy/`, imported hierarchies (apps, products, Oracle schemas, scripts, Control-M variables, LOB→Product→Team) | `taxonomy-importer` |
| **2. Ontology** | "What do the connections *mean*?" | `drydocs_core/schema/*.cypher`, `drydocs_core/ontology/`, `knowledge/ontology/` | `ontology-mapper` |
| **3. Knowledge graph** | "What is connected *and* what does it mean?" | the populated Neo4j graph | (loaders) |
| **4. Context graph** | "What matters *right now* for this task?" | task-scoped projections: temporal state, ownership, permissions, current health | (future) |

**Rule of thumb:** import as **taxonomy first** (pure classification, no edges that imply
meaning), then **apply ontology** (the PROV-O / ORG / DPROD rules that give edges meaning),
*then* load. Never invent a relationship type during import — that is an ontology decision
and goes through the `ontology-mapper` + the HITL gate (`docs/restructure/03-hitl-sme-flow.md`).

---

## 2. External reference — call ALL of these, not just BMC

> **Known failure mode:** agents used to "see" only BMC because it was the only vendor with
> files in the repo. Neo4j, Oracle, and the ontology standards lived only as plugin skills,
> so a repo survey missed them. They are now **all** first-class. When a task touches a
> platform, **consult its reference before writing code.**

External reference is split into two tiers by *role*:

### Tier 1 — Reference source *platforms* (you build WITH these)
Index: [`reference/REGISTRY.yaml`](reference/REGISTRY.yaml)

| Platform | What it is | How to call it |
|----------|-----------|----------------|
| **Neo4j** | the graph platform itself | `neo4j-skills` plugin — trimmed locally to 9 skills: cypher, modeling, import, graphrag, vector-index, gds, driver-python, query-tuning, security (see the trim note below) + [`reference/platforms/neo4j/`](reference/platforms/neo4j/README.md) |
| **Ontology standards** | PROV-O, W3C ORG, DPROD/EKGF, **SOSA/SSN**, DCAT, SKOS | [`reference/standards/`](reference/standards/README.md) |
| **Academic research** | papers backing modeling choices | [`reference/research/`](reference/research/README.md) |

> **Trimming `neo4j-skills` — delete the directory AND prune the manifest, or the whole plugin dies.**
> The plugin ships 29 skills (~8k always-on tokens); we run 9 (~3k). Trimming takes **two** steps, both
> required, in the plugin cache (`~/.claude/plugins/cache/neo4j-skills-marketplace/neo4j-skills/<ver>/`):
> **(1)** delete the unwanted `neo4j-*-skill/` directories, **(2)** remove their entries from that
> directory's `.claude-plugin/plugin.json` `skills` array. Step 1 without step 2 makes Claude Code fail
> the *entire* plugin on the missing paths — every skill vanishes with no error at the prompt. That is
> exactly what happened: the `aura-*` deletion (Aura ruled out for the Docker EE container, 2026-07-06)
> silently took **all** Neo4j reference offline until 2026-07-31, while this table still routed work to it.
> `skillOverrides` is **not** an alternative — it gates filesystem skills (`.claude/skills/`) only, never
> plugin skills; verified inert in both project and local scope. Any `claude plugin install`/`update`
> re-fetches all 29 and reverts both steps — redo them, then confirm with `claude plugin details neo4j-skills`
> (expect `Skills (9)` and `✔ enabled` in `claude plugin list`).

### Tier 2 — Orchestration *vendors* (you ingest FROM these — one level lower)
Index: [`external/orchestration/README.md`](external/orchestration/README.md)

| Vendor | Status | Reference |
|--------|--------|-----------|
| **BMC Control-M** | **BASELINE** (the canonical orchestrator; truth for folder/job/condition semantics) | [`external/orchestration/bmc-controlm/`](external/orchestration/bmc-controlm/) |
| **AutoSys (CA/Broadcom)** | placeholder — map to baseline | [`external/orchestration/autosys/`](external/orchestration/autosys/README.md) |
| **AWS Airflow / MWAA** | placeholder — map to baseline | [`external/orchestration/airflow/`](external/orchestration/airflow/README.md) |

Oracle (source DB) and Snowflake (future) are **data platforms**, referenced via the Oracle
`db` skill and [`reference/platforms/`](reference/platforms/README.md).

---

## 3. Sensitivity classification — the publish boundary

This repo is **private but sometimes published**. Every ingested source carries a **sensitivity
classification** ([`config/classification.yaml`](config/classification.yaml)), decided at
ingestion and required on every source (enforced by `tests/unit/test_classification.py`). It
drives the GitHub publish boundary like a `.gitignore`:

| Classification | Publishable? | Typical home |
|----------------|--------------|--------------|
| **External** | **Yes** | `reference/`, `external/` (public vendor/standards; cite `source_url`) |
| **Internal-Public** | **Yes** | `knowledge/` (internal design prose, no secrets) |
| **Internal** | **NO — excluded from public push** | `internal/` (operational metadata AND confidential material — rosters, SIDs, SEAL ids, schemas; the former Internal-Confidential tier collapsed into this level 2026-07-31, J23 — mark confidential handling in a note on the entry) |

**Never** commit real SIDs, credentials, server addresses, GHE org names, or production data
values outside `internal/`. When registering a source, **set its `classification`** — there is no
unlabeled default. See [`PUBLISH-BOUNDARY.md`](PUBLISH-BOUNDARY.md). (This is *sensitivity*; the
*trust* axis — VERBATIM/GROUNDED/SYNTHESIZED — lives in each `SOURCE-MANIFEST`.)

---

## 4. Source-of-truth precedence (the config layer)

When sources disagree about what something *is*, resolve in this order (configurable in
[`config/precedence.yaml`](config/precedence.yaml)):

1. **BMC baseline** — orchestration vendor's canonical object semantics.
2. **Internal standards** — `knowledge/standards/` naming/normalization conventions that
   refine the baseline for our environment.
3. **LOB → Product → Team** — the org taxonomy that assigns ownership & context.

The configuration layer (`config/`) is where taxonomy meets ontology: it records, per source,
*which orchestrator it uses* and *which ontology rule applies* — confirmed by the SME through
the guided gate before any graph write.

---

## 5. Sub-agents (delegate; they run on cheaper models)

Defined in [`.claude/agents/`](.claude/agents/) — each agent's frontmatter carries its
description, tools, and model; the layer table in §1 names the owner agent. Dispatch by layer.

**Orchestration stays with the main (Opus) session.** Sub-agents do scoped, well-specified
units from `docs/restructure/backlog.yaml`. Each backlog item names its agent + acceptance test.

---

## 6. Working agreements

- **Verify before asserting.** A recalled fact or stale doc that names a file/flag/column may
  be wrong — confirm it exists before relying on it.
- **Live-verification claims name their venue (J18).** A "verified live" claim names the
  machine/container/database it ran on (e.g. "desktop, `neo4jtest`, `drydocs` DB") — the two
  machines hold independent graphs, so an untagged claim reads as a defect from the other
  machine. Prefer sample-reproducible evidence ("`ingest-controlm` on the bundled samples
  reproduces X") over machine-pinned claims.
- **Governed renders publish VERBATIM.** Two surface classes, two rules. *Governed surfaces*
  — `docs/design/*` renders, gate pages, `docs/plan/board.html` — are deterministic renderer
  output that the HITL loop keys anchors on (L5 digital / L6 paper feedback re-attachment):
  share them exactly as rendered, never restyled, summarized, or editorially reworked (a
  "prettier" copy silently breaks feedback re-attachment). *Non-governed outward-facing docs*
  — the whitepaper, the website — are the ONLY place editorial/design treatment
  (artifact-design pass, visual identity) applies.
- **Prose style: U.S. business-technical English.** All new prose follows
  [`docs/style/us-business-english.md`](docs/style/us-business-english.md) — plain, concrete,
  direct; "backbone"/"core"/"source of truth", not "spine"/"planes"/"decays"; lead with the
  core claim. Two boundaries ride with the guide: mechanism names (HITL status `confirmed`,
  port-prompt guardrails, identifiers) are never renamed by a style pass, and "crosswalk(s)"
  is an SME-approved exception (2026-08-03).
- **Taxonomy imports are reversible; ontology edges are not casual.** New relationship types
  go through `docs/RELATIONSHIP_GUIDE.md` + the `relationship_vocabulary.yaml` registry +
  the HITL gate. Set `status: planned` first.
- **Tests gate every change:** `poetry run pytest -q`, `python -c "import drydocs.cli"`,
  `drydocs --help`.
- **Secrets discipline:** architecture-level only. No real data values in commits.

See `internal/repo-README.md` for the runnable pipeline and `docs/restructure/01-project-plan.md` for the plan.
