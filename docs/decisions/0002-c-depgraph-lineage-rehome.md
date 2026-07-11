# ADR 0002-C — `depgraph@feat/controlm-lineage` → `drydocs-lineage` re-home plan

```yaml
status: IN_PROGRESS     # PLANNED | IN_PROGRESS | DONE — G9 pulled 2026-07-10; asset re-home underway (branch port/depgraph-lineage-rehome)
date: 2026-06-29
companion_to: docs/decisions/0002-component-database-topology.md   # ADR 0002, D2 (drydocs-lineage)
depends_on: docs/decisions/0002-a-drydocs-core-extraction-plan.md  # core must exist first
gated_by: ADR 0002 ACCEPTED (2026-06-26)        # topology is settled; this is execution
source_repo: ce-wilson/depgraph @ feat/controlm-lineage (PR #2, OPEN)   # prototype, pre-monorepo
target_package: lineage/  (drydocs-lineage)
skill: reconcile-port   # disjoint-history re-home flow
sibling_of: docs/decisions/0002-b-spinoff-rebase-checklist.md   # same move, different component
```

> Realizes ADR 0002 **D2 (`drydocs-lineage`)** and answers "how do we handle the depgraph
> Control-M lineage work." The decision is **Option A — absorb**: `depgraph@feat/controlm-lineage`
> is the **prototype** of `drydocs-lineage`, built outside the repo because the component did not
> exist yet. We **re-home its lineage assets onto `drydocs-core`** — we do **not** merge the
> depgraph repo, and we do **not** create separate branches/packages per fork. This is the exact
> sibling of 0002-B (`controlm-spinoff → drydocs-remediation`): same re-home move, different
> component.

---

## 0. What depgraph actually is (from its own `CONTINUATION.md` + `README.md`)

A **stdlib-only companion prototype** to DryDocs, not an independent tool. Its Control-M lineage
work, on the `feat/controlm-lineage` branch (PR #2), self-identifies as a DryDocs port:

1. `depgraph/controlm/commands.py` is *"a faithful stdlib-only **port** of DryDocs'
   `drydocs_core/controlm/commands.py`"* with deltas marked `# depgraph:` and a standing note —
   **"Keep in sync with DryDocs when that parser changes."** (This dual-maintenance tax is the
   thing the re-home eliminates.)
2. It consumes a **CSV export of DryDocs'** `controlm_jobs.sql` projection (psgmgr.CM_DEF_VJOB).
3. It emits `examples/drydocs.graph.json` and its final planned step (`profiles/drydocs.py`,
   "Fork 3") **MERGEs into the DryDocs DB**.

So the traversal it built — *parse a job's CMD_LINE → the next-lower dependency (script/spark/
sql artifact) → recurse for read/write lineage, bounded by what Control-M triggers* — **is**
`drydocs-lineage` (ADR 0002 D2: proactive/curated cmd-line lineage → `drydocs`).

**Critical invariant (inherited from D2):** `drydocs-lineage` writes **curated ground truth** to
the `drydocs` DB. It is the *reliable* dependency-graph component; the *uncertain* on-failure
variant is `drydocs-deepdoc` (→ `drydocs_context`). They share the **core** parser and nothing
else (D2: "neither imports the other").

## 1. Decision — absorb, don't fork (Option A)

| Considered | Verdict |
|---|---|
| **A. Absorb** — re-home depgraph's lineage assets into `lineage/` on `drydocs-core`; one parser in core; retire the depgraph branch to source-material. | **Chosen** — matches ADR 0002 D2/D3; kills the dual-parser sync tax. |
| B. Keep depgraph as an external companion that feeds DryDocs via `profiles/drydocs.py`. | Rejected — the parser stays **forked in two repos forever** (the sync tax depgraph itself flags), and `drydocs-lineage` (G4) would either not exist or duplicate it. |
| C. Merge the depgraph repo wholesale into the monorepo. | Rejected — pulls in a divergent copy of the parser already destined for core, re-creating the duplication 0002-A §7 names as the top risk; also drags depgraph's base/python-import layer in with no home in the topology. |

**The boundary, restated:** depgraph's parser → **core** (it is the literal C2/C3 overlap, already
routed to core by 0002-A §2). depgraph's lineage logic → **`lineage/`** (component). Nothing
depgraph-side stays a fork.

## 2. Preconditions (do not start the asset re-home until all true)

- [x] ADR 0002 **ACCEPTED** (2026-06-26 SME gate).
- [x] `drydocs-core` extraction (0002-A / backlog **G2**) is **DONE** — the core parser surface
      (`resolve_job`, `extract_container_command`, `Invocation`/`FileOp`, models, adapters) is
      importable as `drydocs_core.*`. *(Physical relocate merged `0546e21` 2026-07-10, thin
      variant per 0002-A-1; G4 scaffolded `drydocs_lineage/` the same day; G8's parser deltas
      were verified present in core during the G3 archive diff.)*
- [x] Read access to `ce-wilson/depgraph@feat/controlm-lineage` confirmed; treat it as
      **source material**, not a merge base (histories are disjoint; this is a re-home, not a
      cherry-pick). *(Cloned read-only to the session scratchpad, 2026-07-10.)*

## 3. Parser-delta fold (depgraph → `drydocs-core`) — backlog **G8**

depgraph's port found and fixed real gaps the **current** DryDocs parser
(`drydocs_core/controlm/commands.py`, re-exported by `drydocs_core`) still has. Fold these **into
core**, then depgraph's parser ceases to exist (the component imports `drydocs_core.controlm`).
Verified against both trees on 2026-06-29:

| # | Delta | DryDocs parser today | Fold into core |
|---|---|---|---|
| 1 | `.pset` (Ab Initio parameter set) launcher | `LAUNCHER_REGISTRY` has `.m`→ABINITIO but **no `.pset`** | add `(re.compile(r"\.pset$"), "ABINITIO", "abinitio.pset")` after the `.m` rule |
| 2 | **`spark-submit --master yarn x.py` resolves to `yarn`** (a live correctness bug) | PYTHON/PYSPARK branch takes `next((a for a in args if not a.startswith("-")), None)` → the option *value* `yarn` | add `_looks_script()` (has path-sep or file-ext, not a flag); prefer a script-looking token, fall back to first bare non-flag |
| 3 | `.pset` in the direct-script extension regex | `re.search(r"\.(sh\|ksh\|bash\|pl\|m\|py)$", ...)` | `+pset` → `r"\.(sh\|ksh\|bash\|pl\|m\|py\|pset)$"` |

- **#2 is a real bug**, not a style delta — it is the concrete proof of the D3 thesis (one parser
  in core, not two drifting copies). Land it with a regression test
  (`spark-submit --master yarn /path/job.py` → `script_path == "/path/job.py"`).
- Folding is a **core** change (PR to core surface), never a component-side fork of the parser
  (0002-A §4 boundary rule).
- **Equivalence check:** depgraph's `tests/test_controlm.py` (stdlib `unittest`) is the apples-to-
  apples oracle — after the fold, the core parser must produce the same `Invocation`/`FileOp`
  output depgraph's tests assert. *(COUNT CORRECTION at G9 execution, 2026-07-10: the "25
  processes / 13 INVOKES on the 13-job sample" figures above were stale — the branch's actual
  oracle at tip `5b09a0d` asserts 4 current jobs / 7 processes / 4 INVOKES on a 5-row synthetic
  fixture, plus stale-version skip, field mapping, and shared-script collapse. Ported verbatim
  as `tests/unit/test_lineage_inventory.py`; GREEN against the core parser.)*
- **Fold delta #4 (found at G9, same rule — core change, never a component fork):** depgraph's
  `Invocation.target` property (script > executable > raw statement — what lineage keys child
  nodes on) was fork-only. Folded into `drydocs_core.controlm.commands.Invocation` 2026-07-10
  with a core regression test; shared C2/C3 need.

## 4. Asset re-home (depgraph → `lineage/`) — backlog **G9**

Re-home **only the lineage assets**; the parser is already in core (§3). Old → new home map
(fill dispositions during execution):

| depgraph artifact (`feat/controlm-lineage`) | Disposition | New home |
|---|---|---|
| `controlm/commands.py` (the port) | **drop — DONE 2026-07-10** (§3 fold verified; `.target` folded as delta #4) | `drydocs_core.controlm` |
| `model.py` v2 — `ProcessNode`/`DataAssetNode`/typed rels (`INVOKES/TRIGGERS/READS/WRITES`) | **PORTED 2026-07-10** — lineage layer only; identity = ControlMJob NODE-KEY composite; rels normalized to the REGISTERED planned vocabulary (m3_invokes/m3_triggers/m3_reads_from/m3_writes_to; READS/WRITES aliases); code layer left behind | `drydocs_lineage/model.py` |
| `extractors/controlm_inventory.py` (CSV export → ProcessNodes + INVOKES) | **PORTED 2026-07-10** — parses via the shared core parser | `drydocs_lineage/extractors/controlm_inventory.py` |
| `tests/test_controlm.py` + `tests/fixtures/controlm/jobs.csv` (synthetic twin) | **PORTED 2026-07-10** — the §5 oracle, pytest-style, green against core | `tests/unit/test_lineage_inventory.py` + `tests/fixtures/lineage/jobs.csv` |
| `profiles/html_review.py` (self-contained SME review page) | port — NEXT SLICE | `drydocs_lineage/review.py` — the lineage SME surface |
| `profiles/drydocs.py` ("Fork 3", planned — MERGE into `drydocs`) | **build here — NEXT SLICE** (rel vocabulary is gate-bound; no live load before the HITL gate) | `drydocs_lineage/writer.py` — the curated write to `drydocs` |
| `examples/drydocs.load.cypher` | leave behind — inspected 2026-07-10: it is the Fork-1 (CodeFile) base profile, not lineage | stays in depgraph |
| `collect/rua_inventory.sh` (+ `.conf`, README) — RHEL run-as-user collector | port — NEXT SLICE | `drydocs_lineage/collect/` |
| depgraph base layer (`python_imports.py`, `profiles/base.py`) | **leave behind** | stays in depgraph; out of the topology |

**Re-home rules (per 0002-A §4 + D3):**
- `lineage/` imports **only `drydocs_core.*`** — never `drydocs-deepdoc`, never depgraph.
- It is **stdlib-only no longer** required — inside the monorepo it leans on core's deps (the
  "drops in unchanged / nobody installs anything" constraint was a *depgraph* concern, not a
  component one). Treat that as a simplification, not a regression.
- The `ProcessNode`/`DataAssetNode` shapes must **reconcile to DryDocs identity** — DCAT/PROV/SWO
  entities on canonical URNs (`assetId`, `ControlMJob(folder_id,job_id)`), not invented ids.
  Validate the mapping with **neo4j-modeling** before authoring the load Cypher with
  **neo4j-cypher** (constraint-on-key, MERGE, UNWIND; **no `CYPHER 25`** — match the load profile).
- The CSV-export division of labor is preserved: the Oracle pull + pydantic row models stay in
  **core/load**; lineage consumes the `controlm_jobs` projection.

## 5. Verification gates (the invariants, as tests)

- [x] **Shared-parser test:** `drydocs-lineage` imports `drydocs_core.controlm` and contains **no**
      Control-M parse code of its own (grep/AST: no `LAUNCHER_REGISTRY`, no `parse_command` defined
      in `lineage/`). *(test_lineage_inventory.py::test_no_parse_code_of_its_own, 2026-07-10)*
- [x] **Core boundary holds:** `test_module_boundary.py` (0002-A §4) extended to `lineage/` —
      imports only `drydocs_core.*`; no `lineage→deepdoc` / `deepdoc→lineage` import.
      *(`lineage` COMPONENT_GROUP since G4; default-deny green over the ported modules.)*
- [ ] **Writes ground truth only:** `drydocs-lineage` opens write transactions **only** against
      `drydocs` (not `drydocs_context`) — the D2 trust boundary, asserted structurally.
      *(Lands with the Fork-3 writer, next slice.)*
- [x] **Parser equivalence (§3):** core parser reproduces depgraph's `test_controlm.py` outputs,
      incl. the new `spark-submit --master yarn` regression. *(GREEN 2026-07-10; see the §3
      count correction — the real oracle figures are 4 jobs / 7 processes / 4 INVOKES.)*
- [x] Existing gates green: `poetry run pytest -q`, `python -c "import drydocs.cli"`, `drydocs --help`.
      *(532 passed / 3 skipped at slice 1.)*

## 6. Sequencing (where this sits in Epic G)

```
G2 (core extraction)  ──blocks──►  G8 (parser-delta fold)  ──►  one parser in core
        │                                                          │
        └──────────────►  G4 (scaffold lineage/ + deepdoc/)  ──────┴──►  G9 (re-home depgraph
                                  depends [G1,G2]                          lineage assets → lineage/)
                                                                           depends [G4, G8]
```

- **G8** (parser fold) can land as soon as the core parser is the edit target; it fixes a live bug
  and is independently valuable. Do it early.
- **G9** (asset re-home) needs the **scaffolded `lineage/` package (G4)** and the **unified parser
  (G8)**. Until both, depgraph's branch stays the prototype of record.
- On **G9 done:** depgraph PR #2 is **superseded** for the lineage assets — record it here and in
  ADR 0002's rollout note; stop maintaining `feat/controlm-lineage` as a lineage source. depgraph
  may continue to exist for its base/python-import layer only (or be retired).

## 7. Done criteria

`drydocs-lineage` runs its inventory → parse → recurse → curated-write loop using **only**
`drydocs_core` for parsing and identity; the shared-parser, boundary, ground-truth-only, and
parser-equivalence tests pass; gates green. depgraph's Control-M parser no longer exists as a
second copy (folded into core, §3). The depgraph `feat/controlm-lineage` branch is recorded as
**superseded source material**.
