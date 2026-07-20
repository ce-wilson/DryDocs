# Runbook — DryDocs local startup & refresh (EE container + sample ingest)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-07-20**
(authored at L8; content reflects commit `0acc0f8`: post-D6 quick-start with step 3b,
post-D7 sweep, post-K6 supplements) ·
**Classification:** Internal (operational metadata — local host-port mapping and
container names, the same class as `internal/helpmeloginlocalneo4j.md`; NO credentials —
the password lives only in the repo-root `.env`, never here) ·
**Audience:** anyone bringing a local DryDocs graph up from nothing, or refreshing one
that exists ·
**Companion:** `internal/repo-README.md` (the runnable pipeline + CLI reference),
`internal/helpmeloginlocalneo4j.md` (login/port troubleshooting evidence),
`.claude/skills/run-drydocs/SKILL.md` (agent-facing run notes).

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

**Out of scope.** Company-side production ingest (Track-2 — the port-prompt and the
company Control-M ingestion TDD own that), the web console (Epic O), and the multi-DB
provisioning topology beyond a first-time pointer (G1's `provision.ps1` README owns it).

<!-- anchor: prerequisites -->
## Prerequisites

1. **Docker Desktop** running, with the Neo4j **Enterprise** container present —
   locally `neo4j-drydocs-ee` (Neo4j 2026.05.0 EE, host ports **7476** HTTP / **7689**
   Bolt as of 2026-07-03). Any EE container works; the *actual* host ports are whatever
   `docker port <container>` says — never assume the 7474/7687 defaults.
2. **Toolchain:** pipx-installed Poetry with the in-project `.venv` synced
   (`poetry install`). Run everything through `poetry run` — the bare `drydocs.cmd`
   Store-venv wrapper mis-reports exit codes (a known wrapper artifact, not a CLI bug).
3. **`.env` at the repo root** with the connection settings the CLI and
   `scripts/ingest.sh` read: `NEO4J_URI` (e.g. `bolt://localhost:7689`), `NEO4J_USER`,
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
   docker start neo4j-drydocs-ee
   docker port neo4j-drydocs-ee        # confirm the real host ports
   ```
   *Success:* `docker ps` shows the container up; `docker logs` ends with
   `INFO  Started.`; the port mapping matches what `.env`'s `NEO4J_URI` expects.
2. **Connectivity + APOC:**
   ```powershell
   poetry run drydocs check
   ```
   *Success:* exit 0 — server version and APOC reported.
3. **Schema backbone, then the three domain supplements** (order matters —
   `catalog_ontology_supplement.cypher` owns the canonical `:Role` seeds the SEAL/PAT
   loaders MATCH at runtime, and since K6 also the `product_roles` ProductRole scheme):
   ```powershell
   poetry run drydocs bootstrap                   # constraints.cypher + ontology.cypher
   poetry run drydocs apply-ontology-supplement   # Control-M anchor terms
   poetry run drydocs apply-seal-supplement       # SEAL domain terms (TOM scheme)
   poetry run drydocs apply-catalog-supplement    # Catalog/PAT terms + Role seeds + Product Cabinet
   ```
   *Success:* each command exits 0; all four are idempotent — re-running is safe.
4. **First-time only — multi-DB topology** (drydocs + ddlineage + ddcontext + the
   ddall composite): run the G1 provisioning per
   `drydocs_core/schema/provisioning/README.md` (`provision.ps1`). Skip on an
   already-provisioned container.

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
   poetry run drydocs load-essential-graphrag     # optional (-> ddcontext)
   ```
4. **One-shot alternative:** `scripts/ingest.sh [args…]` runs check → bootstrap →
   supplements → ingest-controlm → m1/m3-verify in order and fails fast; arguments are
   forwarded to the `ingest-controlm` step.
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
   volume and survives restarts. Recreating the *container* can remap host ports
   (re-check `docker port`, update `.env`); deleting the *volume* loses the graph — the
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

**A. Current local environment (2026-07-20; verify with `docker port`, never assume):**

| Item | Value |
|---|---|
| Container | `neo4j-drydocs-ee` (Neo4j 2026.05.0 Enterprise) |
| HTTP / Browser | container 7474 → host **7476** (`http://localhost:7476/browser/`) |
| Bolt | container 7687 → host **7689** (`bolt://localhost:7689`) |
| Databases | `drydocs`, `ddlineage`, `ddcontext` + composite `ddall` (G1/G7) |
| Credentials | `.env` only (`NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`) |

**B. The full cold-start command sequence,** in one block (each step's success check is
in the sections above):

```powershell
docker start neo4j-drydocs-ee
poetry run drydocs check
poetry run drydocs bootstrap
poetry run drydocs apply-ontology-supplement
poetry run drydocs apply-seal-supplement
poetry run drydocs apply-catalog-supplement
poetry run drydocs refresh-reference
poetry run drydocs ingest-controlm
poetry run drydocs load-software-registry
poetry run drydocs load-bmc-docs
poetry run drydocs m1-verify
poetry run drydocs m3-verify
```
