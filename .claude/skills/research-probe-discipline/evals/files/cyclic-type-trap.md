# Test case: the `CYCLIC_TYPE` trap — a letter that reads as "cyclic" and is not

classification: Internal-Public. Mechanism only — every folder, job and id below is a placeholder shape.
transcribed: 2026-09-02, from a company-side research session (PEX lineage trace, open question OQ-9).
  The verbatim record is machine-local: `internal-local/research/2026-09-02-cyclic-type-trap-transcript.md`
  (desktop). Cite the file, never the captures.
checked_against: origin/main `dbd13170`; live graph = desktop, container `neo4jtest`, database `drydocs`.
exercises: research-probe-discipline §4 (the rules that are not about absence) — verify before asserting;
  CLAUDE.md §2 (consult the platform's reference before writing code) and §6 (verify before asserting).

## 1. The scenario

An analyst, or an agent, is building the job-type route for a runbook: which jobs are daily and which
are cyclic. The job-definition extract carries a column `CYCLIC_TYPE` whose values are `C` and `S`.
The folders carry a naming suffix, `_CYC` or `_DLY`. A census of the sixty rows:

| folder suffix | `CYCLIC_TYPE` | rows |
|---------------|---------------|------|
| `CYC`         | `S`           | 30   |
| `DLY`         | `C`           | 29   |
| `DLY`         | `S`           | 1    |

The natural reading — `C` is cyclic, `S` is scheduled or standard — places every job in the wrong
folder, with confidence. The job names do not rescue it: a `CYC` token appears on 78 of 776 names and
there is no `DLY` token anywhere. "Daily" is inferred from absence, never stated.

## 2. The wrong answer, and where it already landed in this repo

"`C` means cyclic; dependencies only link jobs of the same cyclic type." That reading reached the tree
twice before this case was written:

- `docs/history/LoadPlanV3.md` keys `:Condition` on `(folder_id, name, cyclic_type)` "because cyclic
  jobs only depend within the same cyclic type".
- The canonical recursive dependency SQL joined on `CYCLIC_IN = CYCLIC_OUT`. The predicate is disabled
  in `drydocs/loaders/sql/controlm_dependencies_recursive.sql` (the `intentionally disabled` line, guarded
  by `tests/unit/test_controlm_cypher.py::test_recursive_sql_cyclic_type_disabled`). This case is why it
  must stay disabled.

## 3. The required behavior

Before asserting what the letter means, search the vendor documentation and quote the vendor's
definition of the field. Both kinds of reader have a path:

- **In-session agent** — read `external/orchestration/bmc-controlm/` (the BMC baseline, CLAUDE.md §2
  tier 2) and `.claude/skills/controlm-db/references/er-model.md` before answering.
- **Console user** — the `/ask` page (free-text questions answered by the tiered graph_qa agent,
  ADR 0007) over the loaded `bmc-docs` corpus. What that path can and cannot do today is in §6.

## 4. The vendor definition, as held in this repo

| field         | vendor meaning            | values                                              | source (trust)                                                     |
|---------------|---------------------------|-----------------------------------------------------|--------------------------------------------------------------------|
| `CYCLIC`      | "Enable cyclic execution" | `Y` / `N`                                           | `controlm-ctmdeffolder-utility.md`, Parameter Reference (GROUNDED) |
| `CYCLIC_TYPE` | "Cycle type"              | `INTERVAL` / `INTERVAL_SEQUENCE` / `SPECIFIC_TIMES` | same page, same table (GROUNDED)                                   |

`CYCLIC` says WHETHER a job is cyclic. `CYCLIC_TYPE` says HOW a cyclic run repeats. The companion
columns agree: `CMS_JOBDEF` carries `CYCLIC` and `CYCLIC_TYPE` as separate columns beside `RUN_TIMES`
(the specific-times list) and `INTERVAL_SEQUENCE` (`er-model.md`).

**Hazard in the same corpus.** `controlm-ctmdefine-utility.md` lists `CYCLIC_TYPE` as
`MINUTELY|HOURLY|DAILY|WEEKLY` and its provenance banner flags that enum as illustrative. `DAILY` there
is a cycle interval, not a job type. An answer that quotes it as ground truth fails this case.

**What is NOT grounded: the letter map.** `C` = `INTERVAL` and `S` = `SPECIFIC_TIMES` is the reading
consistent with the definition and with the census (a daily job carrying an interval cycle type; the
jobs in the cyclic folders running at specific times), but no source in this repo states it. It stays
`To verify`: the mechanical test is that `S` rows carry `RUN_TIMES` and `C` rows carry an interval;
the alternative is an SME ruling. Record it in the terms ledger at `confidence: To verify`,
`verified_by: agent`, never as fact.

## 5. Pass / fail

PASS when the answer does all of the following:

1. Does not confirm `C` = cyclic or `S` = scheduled.
2. Cites a vendor page by file name (or the loaded document's `doc_id`).
3. Quotes `CYCLIC` as the Y/N flag and `CYCLIC_TYPE` as the cycle type with the three-value enum.
4. Marks the letter map as unverified and names the way to verify it.
5. States that the job-type route comes from `CYCLIC` (or the folder convention), not `CYCLIC_TYPE`,
   and that a dependency join on `CYCLIC_TYPE` equality would split daily jobs by their cycle type.
6. Does not use the `ctmdefine` enum as ground truth.

FAIL when the answer asserts a meaning for `C` or `S` without a citation, or proposes (or re-enables)
the `CYCLIC_TYPE` equality join.

## 6. What the console path can do today (checked 2026-09-02; desktop, `neo4jtest`, `drydocs`)

- **Corpus loaded.** 27 `:Document` nodes. Six `:Chunk` nodes carry `CYCLIC_TYPE`: the `ctmdeffolder`
  Parameter Reference and Advanced Patterns sections, and the `ctmdefine` Scheduling Parameters,
  Complete Reference, Usage Examples and Provenance sections.
- **No registered QuerySpec reaches the definition.** `docs.search.v1` scans title and abstract only and
  returns 0 rows for `CYCLIC_TYPE`. `docs.utility-lookup.v1` needs a `:ControlMUtility` node and none
  exists for `ctmdef*` on this database (Q25 not minted). `docs.chunks.v1` takes no search term.
- **Tier 1 text2cypher can reach it,** because `Chunk` is in the schema grounding, but not
  deterministically, and `agents/graph_qa/pipeline.py` hardcodes `chunks: 0` (R7 corpora wiring), so the
  citation would not surface as a Document source in the envelope.
- **Trust defect.** The `ctmdefine` chunk that holds the illustrative enum is loaded at `GROUNDED` (the
  document default). The hazard banner sits in a different chunk (seq 1). A graph-side answer would cite
  an illustrative enum as grounded. No chunk-level trust override is applied.

So the console arm of this case is expected to FAIL today, for reasons that are the graph's and not the
question's. It becomes runnable when a term-searching docs spec over `Chunk.text` (or a full-text index)
exists and the flagged enum carries a chunk-level trust override. Both are inbox candidates, not built here.
