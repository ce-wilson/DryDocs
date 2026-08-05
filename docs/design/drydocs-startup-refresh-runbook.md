# Runbook — DryDocs local startup & refresh (EE container + sample ingest)

<!-- anchor: front-matter -->
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 10, 2026-08-04**
  (Appendix B is now a PROFILE of the one declared load sequence, not a copy of it —
  it gains the standing `docs-verify` step it had been missing and a guard now fails
  if it drifts again (N6); on top of
  Rev 9, same day, where `ddlineage` retired — ADR 0002 X1 amendment: the topology enumerations drop to four
  names (drydocs, ddcontext, ddschema, ddall) and a host still carrying the fifth
  drops it per Epic X; on top of Rev 8, same day, where
  the rollback promise retires on the laptop — the copy it pointed at no longer
  exists, so Appendix A stops offering a recovery path that isn't there; on top of
  Rev 7, where the topology enumerations catch up with the verb — Appendix A, Startup step 4, and
  the one-shot script now all count five databases; on top of Rev 6, where
  the schema meta-graph joined the chain: `bootstrap-schema-graph` after `bootstrap`,
  targeting `ddschema`, which provisioning now creates — G51; on top of Rev 5, where
  the per-file supplement verbs collapse to the one `apply-supplements` chain, which
  also closes Appendix B's long-missing registry supplement; `load-doc-traceability`
  named in the ingest step; on top of Rev 4's plugin correction — plugins are a mounted
  volume, not `NEO4J_PLUGINS`, APOC was silently absent, GDS
  added; on top of Rev 3's container-fact re-point onto the `neo4jtest` recreation,
  sourced from
  `config/dev-environment.yaml`; on top of Rev 2's rev1-SME-feedback pass, which
  reflected commit `a135a6d`: post-D6 quick-start with step 3b, post-D7 sweep,
  post-K6 supplements)
- **Classification:** Internal (operational metadata — local host-port mapping and
  container names, the same class as `internal/helpmeloginlocalneo4j.md`; NO
  credentials — the password lives only in the repo-root `.env`, never here)
- **Audience:** anyone bringing a local DryDocs graph up from nothing, or refreshing
  one that exists
- **Companion:** `internal/repo-README.md` (the runnable pipeline + CLI reference),
  `internal/helpmeloginlocalneo4j.md` (login/port troubleshooting evidence),
  `.claude/skills/run-drydocs/SKILL.md` (agent-facing run notes)

> **What changed in Rev 10 (2026-08-04) — Appendix B stops being a second load
> sequence.** This runbook and `scripts/ingest.sh` each carried their own copy of the
> load order, and the two disagreed: the script ran seven steps, Appendix B ran twelve,
> and nothing anywhere said whether that gap was a decision or an oversight. That
> ambiguity was the real defect — a deliberate subset and a forgotten step look identical
> from the outside — so N6 ruled it rather than just reconciling the counts.
>
> The ruling: the script's shorter list is **deliberate**. A scheduled Control-M ingest is
> not a full refresh, and the four steps it skips each have a reason now recorded in code
> (`cli.SCHEDULED_INGEST_EXCLUSIONS`) — `refresh-reference` is a weekly chain on a
> different cadence, `load-software-registry` and `load-bmc-docs` are repo-triggered
> corpora that change when the repo does rather than when the estate does, and
> `docs-verify` would fail that path by design, since it loads no doc corpora.
>
> Appendix B's omission was **not** deliberate: `docs-verify` is a standing step and a cold
> start is exactly when the doc corpora get loaded, so it is now the last line of the
> block. Mechanically, both surfaces became *profiles* of the single declaration in
> `drydocs/cli.py`. `ingest.sh` reads its profile at run time and has no list left to
> drift; Appendix B is prose and cannot read anything, so
> `tests/unit/test_load_sequence_surfaces.py` holds it to the same answer and fails on the
> next divergence — including the one that started this, a step present in both operator
> surfaces and missing from the declaration.
>
> One consequence worth stating for the reader of the block itself: Appendix B is no longer
> free-form. Editing it now means editing the declaration, and a step added here alone will
> fail the suite.
>
> **What changed in Rev 8 (2026-08-04) — the rollback copy the doc promised no longer
> exists on the laptop.** Appendix A told every reader that `neo4j-drydocs-ee` was "kept
> stopped as a rollback copy." On the laptop the container had already been removed, and
> a Docker cleanup on 2026-08-04 (G52) deleted the anonymous data volume that had outlived
> it — 1.35GB still holding a 2026-07-02 `drydocs`/`ddlineage`/`ddcontext`. Appendix A now
> says so plainly, because the failure mode of a stale rollback line is the worst kind:
> it is read at exactly the moment someone needs the fallback, and it costs them the time
> to go looking before they discover it is not there.
>
> Worth separating from the fact itself: this is a **machine-local** correction (J18). The
> desktop may still have its stopped copy — G50 is open there — so the doc names the venue
> rather than declaring the rollback dead everywhere. The general lesson is that container
> facts in a shared doc need a venue when the two machines can diverge, which is the same
> reason Appendix A is a *render* of `config/dev-environment.yaml` rather than prose.
>
> **What changed in Rev 7 (2026-08-03) — Rev 6 added the verb and left the counts at
> four.** `ddschema` reached the procedure but not the places that enumerate the topology:
> Appendix A still listed four databases, Startup step 4 still named four, and
> `config/dev-environment.yaml` — the single source of truth Appendix A *renders* — had
> never been told about it at all. `scripts/ingest.sh`, the documented one-shot
> alternative, likewise ran a five-step chain the cold-start block no longer matched. All
> four now agree, and the one-shot gained the step so Appendix B and `ingest.sh` are the
> same sequence rather than two that drift.
>
> The reason it survived a green suite is worth recording, because it is the second
> instance in one day: `test_databases_match_provisioning_script` promised in its docstring
> that the config names are "exactly what `01_databases.cypher` creates" while asserting
> only that each configured name is provisioned — a subset check. A database added to the
> DDL and not the config passed. It is now bidirectional, and it fails loudly in the
> direction that actually drifted. Same defect class as the code-side guard G51 itself
> widened, and the same family as J26.
>
> **What changed in Rev 6 (2026-08-03) — the meta-graph verb was in shipped code and in
> no procedure.** `drydocs bootstrap-schema-graph` (C21) writes the schema meta-graph to
> its own database, `ddschema` — which, until G51, `01_databases.cypher` did not create:
> the verb worked only on a machine where someone had made the database by hand, and
> failed loudly everywhere else. Provisioning now creates `ddschema`, and step 3 +
> Appendix B run the verb right after `bootstrap`. It is chain-independent of the
> supplement/ingest sequence (a different database), but it lives in the cold-start
> block because a wiped DBMS is exactly when it is forgotten.
>
> **What changed in Rev 5 (2026-07-31) — one supplement command, and Appendix B was
> quietly one supplement short.** The cold-start step listed three per-file verbs
> (`apply-ontology-supplement` / `-seal-` / `-catalog-`) and Appendix B copied the same
> three. Since **G29** the chain is DATA — `drydocs_core.schema.supplements.SUPPLEMENTS`
> — and it has FOUR members: `base -> seal -> catalog -> registry`. So every reader who
> followed this runbook literally skipped the **registry** supplement, and
> `load-software-registry` (which is in the ingest step, and which MATCHes the terms that
> supplement seeds) was running against a graph that had never been given them. That is
> the G29 failure class the chain was built to end, sitting in the runbook that teaches
> the procedure. Both blocks now run the single verified `poetry run drydocs
> apply-supplements`, which applies each file in the load-bearing order and then CHECKS
> that every `:OntologyTerm` IRI it declares is actually present — a supplement that runs
> and seeds nothing now fails the command instead of surfacing later as an empty loader
> MATCH. The per-file verbs still work as thin aliases; they are simply no longer how the
> procedure is written. The Refresh/ingest demonstrable-content step also names
> `drydocs load-doc-traceability` (shipped by L7 after Rev 2 was signed, never added
> here). Procedure-only; no container or environment fact changed.
>
> *Numbering note:* the backlog item that asked for this says "Rev 4" — it was groomed
> before Rev 4 (plugins) landed on the same day. This is that revision, one number on.
>
> **What changed in Rev 4 (2026-07-28) — the plugins were never actually installed.**
> `NEO4J_PLUGINS=[apoc]` was set on the container for weeks while `/plugins` held only
> `README.txt`, so APOC was ABSENT: `drydocs bootstrap` refused with "APOC required"
> and the `neo4j-drydocs` MCP server could not function. That env var asks the
> entrypoint to *download* each plugin at startup and **fails open** — the container
> starts healthy and the plugin is simply missing, so nothing surfaces it until a
> loader refuses. Both jars ship INSIDE the image, version-matched to the server, so
> plugins are now a **named volume (`neo4j-testplugins`) populated from the image** and
> mounted at `/plugins` — which is also what makes them survive `docker rm` + `docker
> run` (a jar copied into a running container dies with its writable layer).
> **graph-data-science added alongside APOC** (471 procedures). The provisioning
> header's `docker run` — which still said `neo4j:5-enterprise` with no volume mounts —
> is corrected and now guarded by `tests/unit/test_dev_environment.py`.
>
> **What changed in Rev 3 (2026-07-28) — container facts follow the `neo4jtest`
> recreation.** The runbook still told you to start `neo4j-drydocs-ee` on host ports
> 7476/7689. That container was retired 2026-07-23: the graph moved into the named volume
> `neo4j-testdata` and the canonical container was recreated as `neo4jtest` on the
> 7474/7687 defaults (the old one is kept stopped as a rollback copy). Every container
> name, port, and `NEO4J_URI` example below now matches, and Appendix A is restated as a
> *render* of `config/dev-environment.yaml` — the single source of truth the
> `.env.example` templates and the `run-drydocs` skill already defer to — so the next
> container change is one edit, not five. Documentation-only; no procedure changed.
>
> **What changed in Rev 2 (2026-07-20).** Applied the rev1 SME feedback
> (`docs/design/feedback/drydocs-startup-refresh-runbook-rev1.yaml`): front-matter items
> are now one per line, and the out-of-scope list drops the company-side Track-2 item.

This is the Epic L capstone exemplar: the second doc type rendered and validated by the
same outline system as the TDDs (`docs/design/templates/runbook.outline.yaml`).

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Bring a local DryDocs knowledge graph from OFF to VERIFIED — Docker
container up, schema bootstrapped, sample data ingested, invariants green — and run the
recurring refresh on a graph that already exists.

**In scope.** The local Neo4j Enterprise Docker container; the bundled-sample ingest
chain (no Oracle needed); the Oracle-scoped variant as a pointer; the derived artifacts
that refresh alongside the graph (board, design renders, depgraph snapshot).

**Out of scope.** The web console (Epic O), and the multi-DB provisioning topology
beyond a first-time pointer (G1's `provision.ps1` README owns it).

<!-- anchor: prerequisites -->
## Prerequisites

1. **Docker Desktop** running, with the Neo4j **Enterprise** container present —
   locally `neo4jtest` (Neo4j 2026.05.0 EE, host ports **7474** HTTP / **7687** Bolt
   since the 2026-07-23 recreation). Names and ports are declared once in
   `config/dev-environment.yaml`; Appendix A renders them. Any EE container works, and
   the *actual* host ports are still whatever `docker port <container>` says — Docker
   remaps them on recreation, so confirm rather than assume, defaults included.
2. **Toolchain:** pipx-installed Poetry with the in-project `.venv` synced
   (`poetry install`). Run everything through `poetry run` — the bare `drydocs.cmd`
   Store-venv wrapper mis-reports exit codes (a known wrapper artifact, not a CLI bug).
3. **`.env` at the repo root** with the connection settings the CLI and
   `scripts/ingest.sh` read: `NEO4J_URI` (e.g. `bolt://localhost:7687`), `NEO4J_USER`,
   `NEO4J_PASSWORD`. Secrets live ONLY here — `.env` is gitignored; nothing in this
   runbook or any committed file carries the password.
4. **Reference docs at hand:** `internal/repo-README.md` §Quick start (the canonical
   command chain this runbook operationalizes) and
   `internal/helpmeloginlocalneo4j.md` (if login misbehaves).

<!-- anchor: startup -->
## Startup

From OFF to READY. Each step states its success check — do not proceed past a failed
check; go to Troubleshooting.

1. **Start the container:**
   ```powershell
   docker start neo4jtest
   docker port neo4jtest               # confirm the real host ports
   ```
   *Success:* `docker ps` shows the container up; `docker logs` ends with
   `INFO  Started.`; the port mapping matches what `.env`'s `NEO4J_URI` expects.
2. **Connectivity + APOC:**
   ```powershell
   poetry run drydocs check
   ```
   *Success:* exit 0 — server version and APOC reported.
3. **Schema backbone, then the supplement chain:**
   ```powershell
   poetry run drydocs bootstrap                   # constraints.cypher + ontology.cypher
   poetry run drydocs bootstrap-schema-graph      # meta-graph -> ddschema (G51 provisions it)
   poetry run drydocs apply-supplements           # base -> seal -> catalog -> registry
   ```
   One command, not four. The order is load-bearing — `catalog` reuses the
   `:Attribution` class and `#hasAgent` term that `seal` declares, and `catalog` owns
   the canonical `:Role` seeds the SEAL/PAT loaders MATCH at runtime (since K6 also the
   `product_roles` ProductRole scheme) — so the order lives in ONE place,
   `drydocs_core.schema.supplements.SUPPLEMENTS`, rather than in whatever sequence a
   runbook happened to list (G29). Do not hand-run the per-file verbs to "save a step":
   that is exactly how `registry` went missing from this runbook for months.

   *Success:* exit 0, and the printed table shows every supplement with
   `Verified == Declared terms` and `OK = yes`. The command FAILS if a supplement
   applies but seeds nothing, so a green run is evidence the terms are in the graph —
   not just that a file executed. Idempotent; re-running is safe. A run log lands in
   `DRYDOCS_LOGDIR`.

   *Opt-in:* `--with-sosa` appends the EXPERIMENTAL SOSA/SSN supplement. It is not a
   declared company standard and is never in the default chain — leave it off unless
   you are deliberately working layer-4.
4. **First-time only — multi-DB topology** (drydocs + ddcontext + ddschema
   + the ddall composite): run the G1 provisioning per
   `drydocs_core/schema/provisioning/README.md` (`provision.ps1`). Skip on an
   already-provisioned container.

   Note the ordering trap on an EXISTING container: `CREATE DATABASE … IF NOT EXISTS`
   is a no-op where the database already exists, so re-running provisioning proves
   nothing about a newly added name. `ddschema` was created by hand during C21 and only
   provisioned by DDL at G51 — on any machine that predates G51, confirm with
   `SHOW DATABASES` rather than inferring it from a successful `provision.ps1` run.
   The same asymmetry runs the other way for a RETIRED name: provisioning never drops
   anything, so a container that predates the 2026-08-04 `ddlineage` retirement (ADR
   0002 X1) still carries it after a green `provision.ps1` — dropping it is the manual
   Epic X step (alias out of `ddall`, zero-node probe, then `DROP DATABASE ddlineage`).

<!-- anchor: refresh-ingest -->
## Refresh / ingest

The recurring load on a READY system. Everything below runs against the bundled CSV
samples; the Oracle variant is the same chain with scope binds.

1. **Reference data (M1 chain):**
   ```powershell
   poetry run drydocs refresh-reference           # catalog + SEAL + dev teams (+ snapshots)
   ```
2. **Control-M (M3 chain):**
   ```powershell
   poetry run drydocs ingest-controlm             # folders -> jobs -> conditions -> derived deps
   ```
   Oracle-scoped variant: `poetry run drydocs ingest-controlm --use-oracle
   --folder '<pattern>%'` (the `--folder` value is a bind variable, injection-safe).
3. **Demonstrable content — after ANY container rebuild** (a fresh container has none
   of these corpora; the loaders are idempotent, re-running on a live container is safe):
   ```powershell
   poetry run drydocs load-software-registry
   poetry run drydocs load-bmc-docs
   poetry run drydocs load-doc-traceability       # L7 — DryDocs documenting itself
   poetry run drydocs load-essential-graphrag     # optional (-> ddcontext)
   ```
   `load-doc-traceability` is the L7 self-documentation chain: `docs/design/*.md` →
   `:DesignDoc`/`:DocSection`, the traceability-matrix rows → `:Requirement`/
   `:Component`/`:TestCase`, and `docs/design/feedback/*.yaml` → `:FeedbackNote`. It
   shipped after Rev 2 was signed and was never added here, so a rebuilt container had
   no doc graph until someone remembered the verb.
4. **One-shot alternative:** `scripts/ingest.sh [args…]` runs the **`scheduled-ingest`
   profile** and fails fast; arguments are forwarded to the `ingest-controlm` step. That
   profile is a deliberate SUBSET of Appendix B's `cold-start` profile — it skips the
   weekly reference chain, the two repo-triggered corpora, and `docs-verify`, each for a
   reason recorded in `cli.SCHEDULED_INGEST_EXCLUSIONS` (N6). The script reads the
   declaration at run time rather than listing steps, so it cannot drift; to see what it
   will do without running it:
   ```powershell
   poetry run python -c "from drydocs.cli import load_profile; print(*[s.command for s in load_profile('scheduled-ingest')], sep='\n')"
   ```
5. **Derived artifacts** (the session ritual — renders are deterministic, so a clean
   tree stays clean):
   ```powershell
   knowledge\depgraph-snapshots\snapshot.ps1      # board + design-doc renders + dated depgraph JSON
   ```

<!-- anchor: verify -->
## Verify

1. **Graph invariants:**
   ```powershell
   poetry run drydocs m1-verify
   poetry run drydocs m3-verify
   ```
   *Success:* both exit 0, every invariant `yes` — including "active folders contain at
   least one job" (`empty=0` since D6). The canonical expected `m3-verify` output for the
   bundled samples (17 jobs, 8 distinct `WAS_INFORMED_BY` edges, `apps=0` sample-mode
   note) lives in `internal/repo-README.md` — reconcile there, not from memory.
2. **Unit suite** (no Neo4j needed):
   ```powershell
   poetry run pytest -q
   ```
   *Success:* 0 failures (skips for gitignored production CSVs are expected).
3. **Stale-render check:** after `snapshot.ps1`,
   `git diff --quiet docs/plan/board.html docs/design/*.html` — any diff means a
   committed render didn't match its source; commit the refresh.

<!-- anchor: rollback -->
## Rollback

Known-good is cheap here because every loader MERGEs idempotently.

1. **A failed or partial ingest:** just re-run the chain — loaders converge on source
   state; no manual cleanup of duplicates is ever needed.
2. **Jobs/folders that vanished from the source:** the load only soft-MARKS them
   (`removed_from_source_at`, D7). Inspect before deleting:
   ```powershell
   poetry run drydocs sweep-removed --days 30 --dry-run
   poetry run drydocs sweep-removed --days 30 --yes    # hard-delete past retention
   ```
3. **Container-level:** `docker stop` is always safe — graph data lives in the named
   volume `neo4j-testdata` and survives restarts. Recreating the *container* can remap
   host ports (re-check `docker port`, update `.env` — that is exactly what the
   2026-07-23 recreation did, Appendix A); deleting the *volume* loses the graph — the
   recovery is this runbook from Startup step 3, including Refresh step 3 (the document
   corpora live only in the DB).
4. **Destructive last resort:** `poetry run drydocs reset --yes` DETACH-DELETEs every
   node and relationship in the default DB. Blast radius: the whole graph, including
   gate-accepted corpora loads. Recovery: Startup steps 3–4 + the full Refresh section.

<!-- anchor: troubleshooting -->
## Troubleshooting

Symptom → diagnosis → fix. Deep evidence lives in `internal/helpmeloginlocalneo4j.md`;
don't duplicate it here.

| Symptom | Diagnosis | Fix |
|---|---|---|
| Browser URL returns raw JSON (`{"auth_config":…}`) | You browsed to the **Bolt** host port | `docker port <container>` → use the 7474-mapped port for the Browser, the 7687-mapped one in `NEO4J_URI` (2026-07-02 incident) |
| Login fails, container log clean | Wrong host port or stale password | `docker inspect <container> --format '{{.Config.Env}}'` → compare `NEO4J_AUTH` with `.env` |
| `drydocs check` fails | Container down, or `.env` points at old ports | `docker ps` / `docker port`; update `.env` |
| `m1-verify`/`m3-verify` errors immediately | They need a LIVE Neo4j + APOC | Run Startup steps 1–3 first; the unit suite is the no-DB check |
| A supplement fails on a comment `;` | Pre-D5 splitter on an old checkout | Update — `run_script` splits client-side since D5 (`drydocs_core/cypher_split.py`); comment semicolons can't shear |
| Corpus queries return nothing after a rebuild | Fresh container: document corpora live only in the DB | Refresh step 3 (the D6 step-3b reloads) |
| `drydocs` exits −1 outside `poetry run` | Store-venv `drydocs.cmd` wrapper artifact | Always `poetry run drydocs …` (G2 finding) |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Owner / SME:** the repo owner (sign-offs recorded in `config/gate-log.md`); this is
  a single-operator sandbox — there is no on-call rotation to page.
- **Ambiguity rule:** anything touching relationship/edge meaning is NEVER decided from
  a runbook — it routes through the HITL gate
  (`docs/restructure/03-hitl-sme-flow.md`); everything else ambiguous goes to
  `docs/restructure/IDEAS.md` for the next groom.
- **Company-side escalation:** N/A here — SCIM/escalation-queue routing belongs to the
  company runbook-automation workflow (`.claude/skills/controlm-runbook-automation`),
  not to this local procedure.

<!-- anchor: appendices -->
## Appendices

**A. Current local environment** — a render of `config/dev-environment.yaml` (2026-08-03).
Change it *there* first, then here; verify against `docker port`, never assume:

| Item | Value |
|---|---|
| Container | `neo4jtest` (Neo4j 2026.05.0 Enterprise) |
| Volume (data) | `neo4j-testdata` → `/data` (the graph survives container recreation) |
| Volume (plugins) | `neo4j-testplugins` → `/plugins` — APOC + graph-data-science, populated from the image; survives recreation for the same reason |
| Plugins | `apoc` (174 procs) + `gds` (471 procs), both 2026.05.0. Needs `apoc.*,gds.*` in BOTH `dbms.security.procedures.unrestricted` and `..._allowlist`. NOT `NEO4J_PLUGINS` — see Rev 4 |
| HTTP / Browser | container 7474 → host **7474** (`http://localhost:7474/browser/`) |
| Bolt | container 7687 → host **7687** (`bolt://localhost:7687`) |
| Databases | `drydocs`, `ddcontext` + composite `ddall` (G1/G7), and `ddschema` for the schema meta-graph (G51) — deliberately NOT a `ddall` constituent, since it describes the schema rather than the estate. (`ddlineage` retired 2026-08-04, ADR 0002 X1 — a container provisioned earlier still shows it until the Epic X drop) |
| Credentials | `.env` only (`NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`) |

**No rollback copy exists on the laptop.** The retired `neo4j-drydocs-ee` (7476/7689) container
is long gone there, and the orphaned data volume that outlived it — still holding a 2026-07-02
`drydocs`/`ddlineage`/`ddcontext` — was deleted 2026-08-04 (G52). A laptop recovery therefore
restores from `neo4j-testdata` or a re-ingest, never from a second container. The desktop may
still hold its own stopped copy; G50 is open there. Wherever two Neo4j containers are up,
`docker port` is the only way to tell which one `.env` is talking to.

**B. The full cold-start command sequence,** in one block (each step's success check is
in the sections above). This is the **`cold-start` profile** of
`cli.CANONICAL_LOAD_SEQUENCE` — not an independent list. `tests/unit/test_load_sequence_surfaces.py`
compares this block against the declaration and fails on any difference, so a step added
or removed here alone breaks the suite (N6, Rev 10):

```powershell
docker start neo4jtest
poetry run drydocs check
poetry run drydocs bootstrap
poetry run drydocs bootstrap-schema-graph
poetry run drydocs apply-supplements
poetry run drydocs refresh-reference
poetry run drydocs ingest-controlm
poetry run drydocs load-software-registry
poetry run drydocs load-bmc-docs
poetry run drydocs load-doc-traceability
poetry run drydocs m1-verify
poetry run drydocs m3-verify
poetry run drydocs docs-verify
```

Re-derive it rather than trusting this copy — the declaration wins on any disagreement:

```powershell
poetry run python -c "from drydocs.cli import load_profile; print(*[s.command for s in load_profile('cold-start')], sep='\n')"
```

Two absences here are decisions, not gaps. The three per-file supplement verbs this block
used to list are gone on purpose: they covered `base`/`seal`/`catalog` and silently omitted
`registry`, so `load-software-registry` two lines down was MATCHing terms nothing had
seeded — `apply-supplements` is the whole chain and verifies it landed (Rev 5). And the
`optional`/`gated` steps of the sequence (`load-batch-orchestrators`, `load-vendor-docs`,
`load-essential-graphrag`, `load-code-snapshot`, `load-folder-attribution`) are not part of
a cold start; run them from the Refresh section when you want them. `load-doc-traceability`
is the one `optional` step that IS here, because a cold start is precisely when the doc
graph is empty.
