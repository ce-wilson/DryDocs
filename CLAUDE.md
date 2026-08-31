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
- [`docs/restructure/backlog/`](docs/restructure/backlog/) — machine-readable source of truth,
  **one item per file** (`items/<id>.yaml`; schema `drydocs.backlog.v3`, ADR 0013, guarded by
  `tests/unit/test_backlog.py`). Read it through `drydocs_core.backlog_store`; roll-ups (counts,
  `next_ready`) are DERIVED by the board and never stored. The human view is the rendered board
  [`docs/plan/board.html`](docs/plan/board.html) — its **Ready to pull** strip is `next_ready`;
  `IDEAS.md` is the inbox, groomed into item files via the **`groom-backlog` skill**.
  `backlog.yaml` is a tombstone.
- **Pull rule (give this to a sub-agent verbatim):** *"Take the next `status: todo` item in
  `docs/restructure/backlog/items/` whose every `depends_on` is `done` (the board's Ready-to-pull
  strip lists them); **commit and push** `status: in_progress` in that one item file
  **before starting work** — a claim ships NO render (Y5: the roadmap guard tolerates
  status-only drift, so the claim sha stays green; renders catch up at session close); do exactly that item, staying inside your layer; meet its
  `acceptance`; set it `done`."* Anything ambiguous → the HITL
  gate ([`docs/restructure/03-hitl-sme-flow.md`](docs/restructure/03-hitl-sme-flow.md)), never auto-decided.
  **Pushed, not merely committed — why:** the item file's `status` is the only claim channel between
  concurrent sessions on the two machines, and git is the only sync layer, so a local-only claim is
  invisible to the other machine. This is not hypothetical: on **2026-07-28 two sessions independently
  built C19 about ten minutes apart.** Same at the close — push `done`, don't sit on it.
  **Work visibility (J31) — the claim is visible, the WORK is not, until it is pushed.** Mechanism,
  not intention: (1) WHEN — push your in-flight work at the **first substantive edit** and again at
  the **end of any session that did not close its item**; (2) WHERE — a branch named
  **`wip/<id>-<machine>`** (the shape the K9 recovery used, `wip/k9-laptop`), never `main`;
  (3) BEFORE RELEASING someone else's `in_progress` claim back to `todo`, run
  **`git branch -r --list "wip/<id>-*"`** — a claim with a wip branch behind it is not dead, it is
  someone's unmerged work. Evidence, twice: K9 was fully built on the laptop and never pushed, so
  the desktop read claim commit `3608ae5` as a dead tip and rebuilt it (`17d9e08` on main,
  `bfb2f0b` stranded on a branch); and the C19 double-build above. What this does NOT fix: a session
  that dies before its first push stays invisible, and no convention changes that.

**Mint rule (the claim protocol's other half; I6).** A pull is claimed by pushing `status: in_progress`. An id is claimed the same way, and for the same reason: an id that exists only in your tree is an id the other machine will mint too. **Never read the next free number off your own tree** — ask the allocator, which unions the local items, every remote ref's tree listing, and every id ever added in history, and returns max+1 (a gap is usually a BURNED id — `config/gate-log.md` cites ids inside SIGNED records, so re-issuing one silently re-points a signed gate):
```
python .claude/skills/groom-backlog/validate.py --next-id G      # a backlog series
python .claude/skills/groom-backlog/validate.py --next-id Idea   # the idea inbox
```
Then **mint, push the stub, and only then write the body** — the mechanism that already works for ADR numbering, where a committed, pushed index line reserves a number for a draft that does not exist yet. **The stub carries the FINAL title**, because the collision guard compares titles and not bodies: refine a title between the stub push and the body push and the guard reads local-vs-trunk as two machines minting one number, and goes red until the body lands (observed on J66, 2026-08-30). Settle the title before the stub; everything else can follow. **And the stub commit carries the refreshed board and roadmap** (`poetry run python scripts/render_board.py`), because the Y5 tolerance that lets a CLAIM ship no render is for STATUS-ONLY drift and a new item is beyond it: without the render, `test_committed_roadmap_page_matches_its_sources` fails and the trunk is red for the whole window between the two pushes (observed on G132/G133, 2026-08-30). Rendering in the stub commit costs nothing and keeps the guard doing its job. This has failed six times without the protocol, most recently O69 on 2026-08-29: one machine's id was already pushed on a feature branch and the other never looked past its own working tree. The allocator BANDS (producer 1–9999, company 10000+) are a different rule and unchanged — they separate the two repos, never the two machines.

**Session ritual (keeps every platform aligned):**
1. **Start:** `git pull` → read this file → open the board's Ready-to-pull strip (or run
   `python .claude/skills/groom-backlog/validate.py` for the derived list), pick the next ready item.
2. **During:** the in-session Task list is *ephemeral* working memory for the one item — distinct
   from the durable item file.
3. **End:** update the item's `status`, **regenerate the board** (`poetry run python scripts/render_board.py`)
   **and the design docs** (`poetry run python scripts/render_design_doc.py docs/design/*.md` — `.md` is the
   source of truth, the single `.html` (screen + `@media print`; L13) is a deterministic render; Epic L) — `snapshot.ps1` does
   both — then commit + `git push`, then **check CI on what you just pushed** —
   `gh run list --branch main --limit 5` — and only then **run
   `knowledge/depgraph-snapshots/snapshot.ps1`** (writes
   `<project>-<date>.json` with a git-commit `meta` header for drift comparison — see
   [`knowledge/depgraph-snapshots/README.md`](knowledge/depgraph-snapshots/README.md); view with
   `viewer.html`). Anything unfinished or newly noticed → `IDEAS.md`.
   *CI check — why it is a step and not a habit (Idea-111):* CI **blocks** on `ruff check`
   and `ruff format --check` (J10 stage 5), and it ran **RED from 2026-08-05 to 08-12 —
   100+ consecutive failing runs** — while sessions kept pushing past it. It stayed
   invisible because the unit suite passed the whole time, so nothing *local* ever looked
   wrong; only the last two CI steps were failing. `snapshot.ps1` now performs this check
   itself, immediately before it writes, and it matches on **HEAD's sha** — so "green"
   means green at *what you pushed*, never green at somebody else's older commit. It is
   **warn-only** and never blocks the snapshot: recording repo structure and passing a lint
   gate are unrelated jobs, and the failure being fixed here is nobody *looking*.
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
> The plugin ships 29 skills (~9.6k always-on tokens); we run 10 (~3.3k — measured with
> `claude plugin details neo4j-skills`, which prints the projected always-on cost). Trimming takes **two** steps, both
> required, in the plugin cache (`~/.claude/plugins/cache/neo4j-skills-marketplace/neo4j-skills/<ver>/`):
> **(1)** delete the unwanted `neo4j-*-skill/` directories, **(2)** remove their entries from that
> directory's `.claude-plugin/plugin.json` `skills` array. Step 1 without step 2 leaves the manifest
> pointing at paths that no longer exist. On Claude Code 1.x that made the *entire* plugin fail on the
> missing paths — every skill vanished with no error at the prompt, which is exactly what happened: the
> `aura-*` deletion (Aura ruled out for the Docker EE container, 2026-07-06) silently took **all** Neo4j
> reference offline until 2026-07-31, while this table still routed work to it. On **2.1.241 that symptom
> did not reproduce** — the three dangling `aura-*` entries sat in the manifest and the plugin still loaded
> its remaining skills — so treat step 2 as required for correctness, not as a guaranteed tripwire.
> `skillOverrides` is **not** an alternative — it gates filesystem skills (`.claude/skills/`) only, never
> plugin skills; verified inert in both project and local scope. Any `claude plugin install`/`update`
> re-fetches all 29 and reverts both steps — redo them, then confirm with `claude plugin details neo4j-skills`
> (expect `Skills (10)` and `✔ enabled` in `claude plugin list`). This HAS recurred: a re-fetch put all 29
> back and the trim was re-applied 2026-08-23.
>
> The 10 we run: cypher, modeling, import, document-import, graphrag, vector-index, gds, driver-python,
> query-tuning, security. (`document-import` joined the set 2026-08-23 — it was in active use.) Note that
> five of the vendor's skills — `cli-tools`, `driver-javascript`, `mcp`, `migration`, `spring-data` — ship
> with malformed YAML frontmatter (an unquoted multi-line `description` containing `: `) and never load at
> all; they are outside the keep set, so this costs us nothing.

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
units from `docs/restructure/backlog/items/`. Each backlog item names its agent + acceptance test.

---

## 6. Working agreements

- **Where new code goes is dictated — read [`MODULE_MAP.md`](MODULE_MAP.md) before creating a
  file.** §1's four layers are the *conceptual* routing; `MODULE_MAP.md` is the *physical* one,
  and they answer different questions. It holds the per-module table, the invariant (**core
  imports nothing from any component; components import only core, never each other**), and the
  S7 rule for when a directory name must match its module name. The placement test, from ADR
  0002-A §2: *pure parse / resolve / typed-model / driver / config → `drydocs_core/`; anything
  that writes the graph or owns a run cadence → a component.* When unsure, leave it in the
  component — over-extracting "to share early" recreates the tangle the split removed (0002-A §7).
  Enforcement is [`tests/unit/test_module_boundary.py`](tests/unit/test_module_boundary.py), and it
  is **default-deny**: a module classified into no bucket fails as UNCLASSIFIED, so new code means
  adding its `MODULE_MAP.md` row and its prefix to `CORE_PREFIXES` or a `COMPONENT_GROUP` in the
  same commit. A backlog item's `module:` field names the target component; the map says which
  directory that is.
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
- **A review names the tree it ran against (J63).** Every review, triage or research
  artifact states its `reviewed_commit`, `reviewed_branch` and `reviewed_port_base`
  ([`docs/style/review-provenance.md`](docs/style/review-provenance.md);
  `python scripts/review_stamp.py` prints the block). Without it, *absent here* reads as
  **broken** when it means **not yet ported** — which has now manufactured findings three
  times, most recently the 2026-08-28 triage that called three registered refresh verbs
  backwards and seven existing commands unregistered. Note what this is NOT: J37 (read the
  importable object) was followed correctly every time. Reading faithfully still reports a
  STALE tree faithfully, so this is provenance and no method rule can substitute for it.
- **Prose style: U.S. business-technical English.** All new prose follows
  [`docs/style/us-business-english.md`](docs/style/us-business-english.md) — plain, concrete,
  direct; "backbone"/"core"/"source of truth", not "spine"/"planes"/"decays"; lead with the
  core claim. Two boundaries ride with the guide: mechanism names (HITL status `confirmed`,
  port-prompt guardrails, identifiers) are never renamed by a style pass, and "crosswalk(s)"
  is an SME-approved exception (2026-08-03).
- **Taxonomy imports are reversible; ontology edges are not casual.** New relationship types
  go through `docs/RELATIONSHIP_GUIDE.md` + the relationship-vocabulary registry (`drydocs_core/ontology/relationship_vocabulary/`, per-domain fragments; S5) +
  the HITL gate. Set `status: planned` first.
- **Never parse a render when the object is importable (J37).** A guard that enumerates commands,
  loaders, specs or options reads the importable object (`app.registered_commands`, `LOADER_REGISTRY`,
  `QUERY_SPECS`) — never `drydocs --help` or any other human-facing render, which reflows, colours and
  wraps (J33). A test may assert against CLI output only when that output IS the contract under test
  (exit code + message), and it strips ANSI / relies on the unit conftest's non-terminal console.
  Guarded by `tests/unit/test_no_render_parsing.py`.
- **A guard reads CODE, not the prose around it (J66).** A source-reading guard goes
  through [`tests/source_scan.py`](tests/source_scan.py) — `code_only` (comments and string
  literals stripped), `imported_modules`, `called_names` — never a bare substring test over
  raw source. The reason ships with the rule because the reason IS the rule: a guard that
  greps for a forbidden pattern also matches the **comment explaining why it is forbidden**,
  so it fails on the explanation and teaches people to stop writing explanations — which, in
  a repo whose comments carry its rulings, costs more than the guard is worth. It happened
  three times on 2026-08-30 alone (G128, G129, G130), each fixed from scratch. This is J37's
  disease at the other end: J37 says read the importable object rather than a render; this
  says read the code rather than the prose around it. Guarded by
  `tests/unit/test_source_scan.py`. The one exception is a guard whose subject IS the prose —
  asserting an error message or an operator-facing string — which reads raw source on purpose
  and says so.
- **Tests gate every change:** `poetry run pytest -q`, `python -c "import drydocs.cli"`,
  `drydocs --help`. The root import is ONE of eight CLI entry points — the other seven
  (`cli_shared` + the six S8 command modules) are guarded by
  `tests/unit/test_cli_import_order.py`, subprocess-per-import, because an in-process
  import proves nothing about import order (S13: exactly that gap shipped a cycle).
- **Secrets discipline:** architecture-level only. No real data values in commits.

See `internal/repo-README.md` for the runnable pipeline and `docs/restructure/01-project-plan.md` for the plan.
