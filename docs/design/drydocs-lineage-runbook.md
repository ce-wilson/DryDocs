# Runbook — operate `drydocs-lineage`: extract, review, curate, load

<!-- anchor: front-matter -->
- **Module:** drydocs-lineage — this runbook IS the module runbook for drydocs-lineage
  (V1 coverage rule; authored at V6). It covers the module's whole operate surface: the
  three registered verbs, the read zones each hop resolves, the curation gate, the write
  boundary, and the library-only seams that no verb reaches.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-09-09**,
  authored at commit `62589a41`. Every command, every count and every refusal message
  below was RUN on this tree — laptop, bundled samples, no Neo4j and no company data —
  not transcribed from the source (J18: the venue is named because a lineage claim that
  does not name one reads as a defect from the other machine).
- **Classification:** Internal-Public (mechanism only — the counts below come from the
  tracked synthetic samples. Real jobs CSVs, MAC sets, registry exports and Glue
  inventories are Internal and live out of the repo tree under `DRYDOCS_DATA_ROOT`,
  never in this document)
- **Audience:** whoever runs the lineage chain — producer-side against the bundled
  samples, company-side against real `psgmgr` extracts and DPL Metadata-As-Code sets
- **Companion:** the two CHAIN runbooks this page routes to, each of which keeps its own
  depth and is not restated here —
  `docs/design/drydocs-lineage-mac-runbook.md` (the jobs-CSV + DPL MAC input chain and
  the MAC field contract) and
  `docs/design/drydocs-cmdline-resolution-runbook.md` (the G39→G48→G40 `CMD_LINE`
  staging/resolve/parse chain, whose output is a SQLite evidence store, not this
  module's graph). Also `docs/design/drydocs-startup-refresh-runbook.md` (container and
  schema bootstrap — a prerequisite for the `--write` step only) and
  `docs/restructure/03-hitl-sme-flow.md` (the gate that unlocks a planned label).

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the module that turns Control-M job definitions into *candidate*
lineage — what a job invokes, what it reads, what it writes — and drives those candidates
through the chain **extract → review → curate → (gated) load**. The module is
*proactive/curated* (ADR 0002 D2): it proposes, a person decides, and only what a person
confirmed may be written.

### The one rule to know before running anything

> **Nothing reaches ground truth uncurated.** With no decisions file the confirmed set is
> EMPTY, and the load says so rather than defaulting to "write everything".

This is structure, not convention. `drydocs lineage-load` with no `--confirmed` prints:

```
no --confirmed decisions file: the confirmed set is EMPTY - nothing reaches ground truth
uncurated. Export decisions from the lineage-review page.
```

...and plans zero statements. Curation is the gate, not a flag you may omit.

### Where to go — this page, or one of the two chain runbooks

An SME landing on the module starts here. Two procedures have their own pages because
they have depth this one deliberately does not restate:

| If you are… | Read |
|---|---|
| running the chain end to end; asking what the module operates at all | **this page** |
| preparing the jobs CSV or a DPL MAC root, or you need the MAC field contract and the promotion-repo clone layout | `docs/design/drydocs-lineage-mac-runbook.md` |
| turning verbatim `CMD_LINE`s into resolved, parseable text (stage → resolve → parse) | `docs/design/drydocs-cmdline-resolution-runbook.md` |

The cmdline chain is a **neighbour, not a hop**: it borrows one extractor from this
module (`drydocs_lineage/extractors/controlm_xml.py`, the G47 XML seam) and writes a
SQLite store, never this module's staged artifact. Running it is not a prerequisite for
anything below.

### The awkward fact, stated rather than hidden

**Three registered verbs reach four of the module's twelve extractors.** The other eight
files — and the G58 archival report — are library seams with no CLI verb: reachable from
Python, exercised by their unit tests, and not part of the chain. Appendix A is the
census, because a runbook that implied a verb for each of them would be the easier
document and the wrong one.

**In scope.** The three verbs (`lineage-extract`, `lineage-review`, `lineage-load`); the
read/write zones each hop resolves and the refusal when a path sits outside one; the
staged artifact and its provenance header; the decisions file; the plan; the gated write
and how to read its refusals; retention; the library-only seams and how to reach them.

**Out of scope.** Container startup and schema provisioning (the startup/refresh
companion). The `CMD_LINE` staging chain (its own runbook, above). Attribution edges —
Epic K owns those; this module records SEAL *facts* only. Deciding whether a candidate is
TRUE: that is the SME's, at the review page.

<!-- anchor: prerequisites -->
## Prerequisites

1. **The toolchain.** `poetry install`. *Success:* `poetry run drydocs --help` prints
   without a traceback.
2. **`DRYDOCS_DATA_ROOT` is MANDATORY** — G81 removed the old `~/data/DryDocs` fallback,
   so an unset variable is a refusal and not a silent default. Set it in the shell
   before any command on this page.
3. **The zones each hop reads.** Every lineage input resolves inside a *declared* read
   zone or the run refuses — there is no override flag, because a side door is exactly
   the undeclared acquisition route G81/G121 closed. `drydocs landing-zones` prints where
   each one is on this machine; `config/data-zones.yaml` is the declaration.

   | Hop | Zone under `DRYDOCS_DATA_ROOT` | Required? | Helper in `drydocs_core/data_root.py` |
   |---|---|---|---|
   | 1 — Control-M inventory (jobs CSV, + variables CSV for PRECMD/POSTCMD) | `controlm-exports/` | **required** | `controlm_exports_dir` |
   | 2a — DPL Metadata-As-Code root | `dpl-mac/` | optional | `dpl_mac_dir` |
   | 2a — DPL registry Swagger exports, per SEAL | `dpl-registry/` | optional | `dpl_registry_dir` |
   | 3 — AWS Glue base-table inventory | `glue-inventory/` | optional | `glue_inventory_dir` |
   | *output* — the staged artifact | `lineage/staged/` | write zone | `lineage_staged_dir` |

   Note the registry path is `dpl-registry/`, not `dpl/`: the source registry declared
   the wrong one from N12 until G81 corrected it, and an operator who followed the
   registry had files nothing read.
4. **Neo4j — for the `--write` step only.** Everything up to and including the plan runs
   with no database. Bring the container up per the startup/refresh companion when you
   reach step 4, not before.

<!-- anchor: startup -->
## Startup

**This module has no service to start.** There is no daemon, no port and no long-running
process — "startup" here means proving that the data root and the zones resolve, which is
the only state a run depends on.

1. **Declare the data root.**

   ```powershell
   $env:DRYDOCS_DATA_ROOT = "<your data root>"
   ```

   *Success:* the next step prints zones instead of a refusal.
2. **Read the zones back.**

   ```powershell
   poetry run drydocs landing-zones
   ```

   *Success:* every zone in the prerequisites table is listed with an absolute path. A
   zone directory that does not exist yet is fine — an absent optional source is skipped
   and counted, never silently dropped.
3. **Check the environment.**

   ```powershell
   poetry run drydocs env-doctor
   ```

   *Success:* no refusal about `DRYDOCS_DATA_ROOT`.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

The chain is four steps. Steps 1–3 need no database.

### Step 1 — extract: run the chain into one staged artifact

```powershell
poetry run drydocs lineage-extract
```

With no options this is a **dev run against the bundled package samples**, and it works
in any clone. Measured on this tree:

```
controlm           present   …\drydocs\data\samples\controlm_jobs__sample.csv
controlm_variables absent - skipped   …\controlm_variables__sample.csv
dpl_mac            absent - skipped   …\dataroot\dpl-mac
dpl_registry       absent - skipped   …\dataroot\dpl-registry
glue               absent - skipped   …\dataroot\glue-inventory
graph: 33 processes, 0 data assets, 17 rels
wrote …\lineage\staged\lineage-20260909T133705Z-<run-id>.json (run <run-id>)
```

Two things that output is telling you, and both are deliberate:

- **The variables sample is absent in a fresh clone.** Only the *named* samples are
  force-tracked and that one is not, so hop 1 runs without PRECMD/POSTCMD text. The
  artifact records the absence rather than pretending the file was never asked for.
- **Every optional hop is skipped AND COUNTED.** The artifact's `sources` block names
  each hop with `present`/`absent` and the path it resolved to, so a reader can tell
  *"nothing to read"* from *"never asked"*. That is G11's house rule one level up.

For a real run, name the sources — each must already sit inside its declared zone:

```powershell
poetry run drydocs lineage-extract --jobs <zone>\jobs.csv --variables <zone>\variables.csv --mac-root <zone> --registry-root <zone> --glue <zone>
```

`--out-dir` moves the artifact; `--keep N` (default 10) prunes the staged zone to the
newest N after a successful write, and `--keep 0` keeps everything.

**An input outside its zone is refused, with the fix in the message.** Measured:

```
REFUSED: --jobs drydocs\data\samples\controlm_jobs__sample.csv is outside every declared
read zone. An acquisition route is declared or it does not run (G121): --jobs reads from
controlm-exports (`drydocs landing-zones` shows where that is on this machine). Land the
file there, or declare a zone in config/data-zones.yaml.
```

Note that the *bundled sample path itself* is refused when passed explicitly. That is
correct and not a bug: the default path is a dev convenience the command grants itself,
while an explicit path is an acquisition claim and has to be declared.

### Step 2 — review: render the SME page and export decisions

```powershell
poetry run drydocs lineage-review <jobs.csv> -o lineage-review.html
```

One self-contained HTML file — no server, no Neo4j, no external resources: a section per
Control-M folder, a card per job, its INVOKES dependencies, and per-folder SME notes.
The SME marks each candidate and the page's **Export** writes a decisions file
(`drydocs.lineage-decisions.v1`). Measured on the bundled sample: a 24 KB page, coverage
`rows=17 jobs=17 invocations=17 (unresolved=0)`.

The decision grain is one yes/no per rel, keyed by the graph's own triple
(`from`, `type`, `to`) — so a decision joins to a candidate by equality and nothing is
re-derived. A rel the SME never touched is simply absent and stays `proposed`.

### Step 3 — plan: what a live load would do, without a database

```powershell
poetry run drydocs lineage-load --confirmed <decisions.json>
```

With no `--artifact` it reads the **newest** staged artifact — the UTC stamp leads the
file name, so no file is opened to find it. It then prints, in order: the artifact and
the extract run it names; the code commit (flagged `DIRTY TREE` if that extract was
staged from uncommitted code); each source's state; the graph's counts; the decisions
tally; and the plan. Measured with all 17 candidates confirmed:

```
decisions …\decisions-all-confirmed.json: 17 confirmed, 0 rejected, 0 undecided;
          0 candidate(s) never decided
plan      nodes: 6 Script, 10 ETLProcess, 0 DataAsset; rels: 17 confirmed, 17 INVOKES
          8 statement(s) (load run <load-run-id>)
plan only - pass --write to load against drydocs.
```

The plan is the review surface: it is the exact statement set a live load would run, and
it is printed before anything can happen.

### Step 4 — the gated write

```powershell
poetry run drydocs lineage-load --confirmed <decisions.json> --write
```

This is the module's **only** database write, and `drydocs_lineage/writer.py` is the only
file in the module that performs one. It writes exactly one database — `drydocs`, the
ground truth — via constraint-on-key MERGE, so a re-run of the same plan converges rather
than duplicating. Every node and rel written carries the artifact's run id and code
commit, so a row in the graph names the extract it came from.

A label whose vocabulary entry is not `active` is **refused by the writer**, not filtered
by the caller. See Verify for how to read that refusal.

<!-- anchor: verify -->
## Verify

1. **The extract asked for everything it should have.** Open the artifact's `sources`
   block, or re-read it from the plan print in step 3: five hops, each `present` or
   `absent` with the path it resolved to. A hop missing from that list is a defect;
   a hop `absent` is information.
2. **The load's gate-bound refusals — read them, do not carry a copy.** The plan prints
   one line per label whose vocabulary entry is not active:

   ```
   GATE-BOUND: <LABEL> (<vocab id>) is <status>, not active - a live load refuses this
   label until the HITL gate flips it
   ```

   **The command is the authority on which labels those are**, because it computes them
   from the vocabulary registry on every run. Measured at Rev 1 on this tree: of the five
   labels — `INVOKES`, `USES_ARTIFACT`, `READS_FROM`, `WRITES_TO`, `TRIGGERS` — four are
   active and only `TRIGGERS` (`scheduler_triggers`) is still `planned`. That state moves
   when a gate signs; **re-run the plan rather than trusting this sentence**, which is
   why the check is written as *run it and read the output* and not as an asserted list.
3. **Determinism.** Two extracts over the same inputs produce byte-identical artifacts —
   sorted keys, `newline="\n"`, no clock in the body. If two runs on two machines differ,
   the inputs differed.
4. **The unit contract.** These pass on a clean tree with no database and no data root:

   ```powershell
   poetry run pytest -q tests/unit/test_lineage_staging.py tests/unit/test_lineage_writer.py tests/unit/test_lineage_curation.py tests/unit/test_cli_lineage_extract.py tests/unit/test_cli_lineage_load.py
   ```

<!-- anchor: rollback -->
## Rollback

- **Extract** — nothing to roll back. Each run writes a NEW artifact and mutates
  nothing; the previous artifacts stay until `--keep` prunes them, and the load never
  deletes. To undo a bad extract, run a good one: the load reads the newest.
- **Review** — writes one HTML file at the path you gave and touches nothing else.
  Delete it and re-render.
- **Plan** — reads only. This is the rollback-free step by design: it exists so the
  irreversible one can be inspected first.
- **Load (`--write`)** — re-running the same plan is safe: MERGE on the node key
  converges. To *withdraw* what a load wrote, the handle is the load run id printed with
  the plan — every node and rel written carries it, so the blast radius of a targeted
  cleanup is exactly one run. **The destructive last resort** is the module's own
  database (`drydocs`) being reset per the startup/refresh companion, which discards
  every loader's work, not just this one's — never reach for it to undo a lineage load.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| A command refuses naming `DRYDOCS_DATA_ROOT` | Unset. G81 removed the old `~/data/DryDocs` default, so there is nothing to fall back to | Set it in the shell (Prerequisites 2) |
| `REFUSED: --<opt> … is outside every declared read zone` | The path is real but its acquisition route is not declared (G121). There is no override flag, deliberately | Land the file in the zone the message names, or declare a zone in `config/data-zones.yaml` |
| `no staged lineage artifact in <dir>` | Step 3 ran before step 1, or `--out-dir` sent the artifact somewhere the load does not look | Run `lineage-extract`, or pass `--artifact <path>` |
| The plan says `0 confirmed` and plans nothing | No `--confirmed` file, or a file in which nothing is marked `confirmed`. This is the gate working | Export decisions from the review page and pass the file |
| `N decision(s) name a rel this artifact does not carry` | The review page was rendered from a DIFFERENT extract than the artifact being loaded | Re-render `lineage-review` from this artifact's sources and decide again |
| `code … DIRTY TREE - staged from uncommitted code` | The extract ran against uncommitted changes, so its provenance cannot be reproduced from a commit | Commit, re-extract. Acceptable for a dev run; never for evidence |
| `GATE-BOUND: <LABEL> … not active` | The vocabulary entry is `planned`. The writer refuses it — the SME gate has not flipped it | Take it to the HITL gate (`docs/restructure/03-hitl-sme-flow.md`); the ruling lands in `config/gate-log.md`. Do not edit the registry to get past a refusal |
| `N confirmed rel(s) not written` after a successful load | A `ControlMJob` endpoint is not in the graph (the M3 load owns those), or a file-op candidate had no owning job | Run the M3 load first, then re-run this one; check the plan's unresolved file-op count |
| Hop 1 runs but no PRECMD/POSTCMD lineage appears | The variables CSV is absent — in a fresh clone the sample is untracked | Pass `--variables`, or land one in the `controlm-exports/` zone |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Procedure owner:** the DryDocs producer (repo owner). Company-side runs against real
  extracts are the company session's, in its own repo.
- **Anything that changes what an edge MEANS** — a new relationship label, a vocabulary
  status, whether a candidate is true — is not this procedure's to decide. It routes to
  the HITL gate (`docs/restructure/03-hitl-sme-flow.md`), and the signed ruling lands in
  `config/gate-log.md`. A refusal from the writer is that boundary holding, not a bug to
  work around.
- **A disagreement between this page and the code:** the code wins, and the fix is this
  page. Every claim above is re-derivable from the one-liners in Appendix B.

<!-- anchor: appendices -->
## Appendices

### A. The extractor census — what a verb reaches, and what only Python reaches

Twelve extractors plus the archival report. Four are in the `lineage-extract` chain; the
rest are library seams with no CLI verb, reached by importing them. Listing them is the
point: each one is a real, tested capability, and none of them is behind a command.

| File | Reached by | What it reads |
|---|---|---|
| `drydocs_lineage/extractors/controlm_inventory.py` | **hop 1** of `lineage-extract` | the jobs CSV (+ variables CSV); seeds every process node |
| `drydocs_lineage/extractors/dpl_mac.py` | **hop 2a** of `lineage-extract` | a DPL Metadata-As-Code root — per-pipeline JSON sets keyed by GUID |
| `drydocs_lineage/extractors/dpl_registry.py` | **hop 2a** of `lineage-extract` | per-SEAL registry Swagger exports, taxonomy-first |
| `drydocs_lineage/extractors/glue_tables.py` | **hop 3** of `lineage-extract` | AWS Glue base-table inventory exports |
| `drydocs_lineage/extractors/controlm_xml.py` | the **cmdline-resolution** chain (its own runbook) | Control-M XML definition exports — folders, jobs, ordered variables |
| `drydocs_lineage/extractors/rua_inventory.py` | library only | one `rua_*.tar.gz` collector bundle from the `rua/incoming/` zone |
| `drydocs_lineage/extractors/rua_code_ops.py` | library only | the script/profile CONTENT a rua bundle carried back |
| `drydocs_lineage/extractors/code_repo.py` | library only | the code-repo provenance origin (repo + ref + commit + path) |
| `drydocs_lineage/extractors/snowflake_catalog.py` | library only | the two Snowflake data-catalog views, from the `catalog/` zone |
| `drydocs_lineage/extractors/catalog_crosscheck.py` | library only | what the catalog and its neighbours disagree about — every bucket counted AND listed |
| `drydocs_lineage/extractors/lb_resolution.py` | library only | an `nslookup` transcript, for load-balancer alias → server evidence |
| `drydocs_lineage/archival.py` | library only | the G58 dead-script report — output drives DELETION, so its safety bar is structural |

The rest of the module: `drydocs_lineage/model.py` (the graph and its identity rules),
`drydocs_lineage/staging.py` (the chain and the artifact), `drydocs_lineage/review.py`
(the SME page), `drydocs_lineage/curation.py` (the decisions file and its states), and
`drydocs_lineage/writer.py` (the one write boundary).

### B. Re-derive one-liners — the code wins on disagreement

A pointer cannot go stale; only a copy can. Each of these answers a question this page
also answers in prose, and the command is the authority:

```powershell
# the registered verbs, read from Typer rather than from --help (J37)
poetry run python -c "import drydocs.cli as c; print(sorted(i.name for i in c.app.registered_commands if i.name and 'lineage' in i.name))"

# which labels a live load would refuse today, and why
poetry run python -c "from drydocs_lineage.writer import gate_bound_labels, VOCAB_IDS; print(gate_bound_labels(VOCAB_IDS))"

# the one database this module writes
poetry run python -c "from drydocs_lineage.writer import DATABASE; print(DATABASE)"

# where every zone resolves on this machine
poetry run drydocs landing-zones
```
