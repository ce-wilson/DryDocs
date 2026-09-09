---
name: controlm-runbook-automation-SDLC
description: "COMPANY-SPECIFIC: generate the LONG-FORM SDLC Application Run Book — the Tier 2/Tier 3 markdown/Word reference for one Control-M folder — from the DryDocs graph or from the bundled samples. Use when: (1) producing an outline-conformant SDLC-Runbook document for a folder/application, (2) asking which sections of that run book the graph can answer and which need SME capture, (3) changing that answer (section-spec.yaml -> generate_runbook.py), or (4) auditing an existing long-form run book against what the graph knows. Sibling of controlm-runbook-automation-excel, which owns the SHORT form (the 2-tab folder-grain workbook), and of controlm-runbook-automation, the parent pipeline/fix-package skill. Mechanism-only in committed files; a FILLED run book is Internal and lives in internal-local/ or internal/."
---

# Control-M runbook automation — SDLC (the long-form run book)

**What this is.** The `-excel` sibling emits the *minimum viable* runbook: a
2-tab, folder-grain Excel workbook support teams exchange. This skill emits the
*long form* — the SDLC Application Run Book, the Tier 2/Tier 3 reference that
documents an application's whole batch estate in prose and tables. Same folder,
same graph, two audiences and two formats.

The document's shape is not this skill's to invent. It is
`docs/design/templates/sdlc-app-runbook.outline.yaml` (doc type `SDLC-Runbook`,
Epic L), transcribed structure-verbatim from a reviewed 56-page enterprise run
book, with `docs/design/templates/sdlc-app-runbook.example.md` as the worked
exemplar. This skill fills that shape.

## Files here

| File | Role |
|---|---|
| `section-spec.yaml` | **Source of truth for provenance**: one entry per outline section — can the graph supply it (`graph`), partly (`graph-partial`), or not at all (`manual`) — plus the exact table columns the outline mandates, and the citation for every graph-backed claim |
| `generate_runbook.py` | The renderer: fact bundle + spec + outline → one conformant markdown document |

There is no committed generated document. `tests/unit/test_sdlc_runbook_generator.py`
regenerates one for **every** bundled sample folder on each run and validates it,
which is a stronger claim than a committed sample would make and adds no
un-guarded render to the tree.

## How to run it

```bash
# the clone-reproducible path — bundled sample CSVs, no Neo4j, no data root
poetry run python .claude/skills/controlm-runbook-automation-SDLC/generate_runbook.py \
    --folder PRARAG-HLDM-70002-PEX-RFND-DLY --out /tmp/runbook.md

# the real path — the DryDocs graph
poetry run python .claude/skills/controlm-runbook-automation-SDLC/generate_runbook.py \
    --folder PRARAG-HLDM-70002-PEX-RFND-DLY --source graph --database <db> --out /tmp/runbook.md

# what the bundle holds, without rendering
... --folder <name> --coverage-only
```

Both sources build the same `FolderFacts`, so the renderer cannot tell them
apart and every document names on its cover which one produced it.

## The provenance vocabulary — the `-excel` sibling's, on purpose

`section-spec.yaml` labels every section with one of three values, and they are
the sibling's values, not new ones:

| `source:` | means | the long-form wording |
|---|---|---|
| `graph` | the graph (or its staging stores) already holds it | GRAPH-DERIVED |
| `graph-partial` | partly derivable; a named seam exists but needs enrichment | GRAPH-DERIVED in part, SME-RESIDUE for the rest |
| `manual` | SME capture; no system of record we ingest today | SME-RESIDUE |

Two skills with two names for one concept is the failure the anti-duplication
rule exists to prevent, so the three values are shared and the mapping to the
long-form wording is stated once, in the spec's header.

**The label is a claim about the spec, not about a run.** `architecture-contacts`
is marked `graph` because the graph *can* answer it; a folder whose attribution
edge was never confirmed still renders an empty ownership table. Every generated
document carries a **Generation coverage** block on its cover saying what *that*
folder's bundle actually held. Read the coverage block, not the label, when
asking whether a given run book is complete.

Measured over the current spec: 4 sections `graph`, 11 `graph-partial`, 26
`manual`, of which 10 are N/A for a pure-batch module. That ratio is the honest
one and it is *worse* than the workbook's — the `-excel` job tab is ~90%
graph-derivable because it is all orchestration metadata, while the long form
adds recovery procedures, escalation scenarios, vault safes and directory maps,
none of which any system we ingest holds.

## Section → system of record (cited, never restated)

Every graph-backed section resolves through a citation in the spec's
`sor_citations:` block rather than a query written here. The authority for each
is the file named, not this skill:

| Section family | Cited authority |
|---|---|
| Folder, jobs, descriptions, owners, command lines | the `-excel` SKILL.md column map + the `ingest-controlm` graph |
| Folder → application attribution | the `-excel` map's SEAL row; the edge lands on the application's **batch port**, folder grain, never job grain |
| Ownership and escalation contacts | the SEAL role-attribution chain (the `-excel` map's escalation row covers the queue/DL half, which this skill does **not** re-derive) |
| Conditions and job-to-job dependencies | the BMC baseline's condition grammar |
| Hosts and servers | the `-excel` map's Control-M row |
| Average run time, SLA/SLO on ODATE | the `-excel` map's two graph-partial rows — this skill claims no more than the sibling does |
| Per-job definition detail | the `-excel` workbook itself; section 6.7 points at it rather than reproducing ~35 columns in markdown |

Where a fact would need a query the sibling already owns, the run book **points
at the workbook**. Two renderings of one fact are two things that can disagree,
and a support engineer reading two disagreeing runbooks at 03:00 is the outcome
both skills exist to avoid.

## What it refuses to invent

- A `manual` section gets its heading, its exact mandated columns and a capture
  marker — never a plausible-looking filled row.
- A `graph-partial` section fills what the graph answers and writes an explicit
  `_not captured_` in what it does not. That token is different from an empty
  cell: empty means the section does not ask, `_not captured_` means it asked
  and got nothing.
- A required section that does not apply to a batch module renders
  `N/A — <reason>`, keeping its anchor and its number. The outline requires the
  anchor; a reason turns an omission into an answer.
- **Condition names are not trigger-file paths.** The schedule section lists the
  conditions a job waits on and says so; the literal `.done` paths, the alert
  cadence and the restart-after-window rule stay SME capture. Presenting one as
  the other would be a quietly wrong run book, which is worse than a blank one.
- Nothing reads a clock. The cover's date is the newest capture date in the
  folder's own data, so two runs over one bundle are byte-identical.

## Boundaries

- **Committed files are mechanism-only.** Every value that reaches this
  directory is synthesized — application ids inside the reserved block
  70001-70099, `example.invalid` addresses, `host-*` node names. A FILLED run
  book for a real application is **Internal**: write it to `internal-local/`
  (machine-local) or `internal/` (repo-internal), never here. The generator says
  so on every document it produces.
- Generation is **read-only** on the graph. Where a graph value disagrees with
  what a team's existing run book says, that is a metadata finding — route it to
  the parent skill's failure-driven fix loop, never silently overwrite either
  side.
- **The two SEAL sample files are not tracked.** `.gitignore` ignores
  `drydocs/data/` and the sample files that ship are force-added exceptions,
  which `seal_application_data__sample.csv` and `seal_contact_data__sample.csv`
  are not — they are rebuilt per machine. So on a fresh clone the sample path
  produces a run book with full orchestration content and no ownership at all,
  and the coverage block says which files were missing. That is deliberate: the
  alternative is a generator that works on the machine that built it.
- Section numbering, heading text and the N/A wording are **conventions with no
  guard**. The one committed contract is the outline's 41 anchors, which
  `drydocs.docgen.doc_outline` checks. Conformance therefore proves STRUCTURE,
  not content — a document can pass with every table empty. The coverage block
  is what says whether it is any good.

## Related

- `controlm-runbook-automation-excel` — the SHORT form (2-tab workbook) for the
  same folder, and the owner of the column → system-of-record map this skill
  cites.
- `controlm-runbook-automation` — the parent workflow skill: pipeline phases,
  fix packages, the SoR map.
- `controlm-db` — the CM_ replica schema map behind every graph-backed row.
- `docs/design/templates/sdlc-app-runbook.outline.yaml` — the doc-type contract.
- `docs/design/templates/sdlc-app-runbook.example.md` — the worked exemplar.
