# Runbook — operate `drydocs-review`: gate pages, graph acceptance, review pages, publishing

<!-- anchor: front-matter -->
- **Module:** drydocs-review — this runbook IS the module runbook for drydocs-review
  (V1 coverage rule; authored at V4). It covers the module's whole operate surface: the
  gate-page renderer, the graph acceptance suites, the SME review page, the review
  backbone and column ledgers, the FID/run-as measurements, and the docs-publish chain.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-09-09**,
  authored at commit `4ba761be`. Every command, count, error message and suite result
  below was RUN on this tree, and the live half names its venue (J18): **laptop,
  `neo4jtest` container, database `drydocs`**. The four suite failures reported in
  Verify are that graph's, not the code's, and the section says how to tell.
- **Classification:** Internal-Public (mechanism only — every example value is
  synthetic and every app id comes from the reserved 70001–70099 block. Real gate
  rulings live in `config/gate-log.md`; real FID measurements and the Confluence
  coordinates are company-side and appear nowhere here)
- **Audience:** whoever runs an SME gate, proves a graph invariant, renders a review
  page for an SME to mark up, or publishes a review document
- **Companion:** `docs/restructure/03-hitl-sme-flow.md` (**the process this module is
  the tooling for** — read it first if you have not run a gate before);
  `docs/design/drydocs-core-runbook.md` (the vocabulary registry and run logs the
  enforcement points below read); `config/README.md` (what each `config/` surface is);
  `graph-tests/README.md` (the acceptance suites' own notes).

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the tooling that puts a **person** between derived data and the
graph. Four surfaces, one job: render what an SME must decide (gate pages), prove what
the graph already claims (acceptance suites), show an SME the rows themselves (review
pages), and publish the result (the docs-publish chain).

### The one rule to know before running anything

> **No graph write happens until the mapping is confirmed.** The gate page *says* it;
> four separate places in the code *enforce* it, each by raising.

The distinction matters, because a sentence on a page is a claim and only code refuses:

| Enforcement point | Refuses when | Raises |
|---|---|---|
| `drydocs_core/manual_mappings.py` | `config/manual-loads/manifest.yaml` is not `status: confirmed` | `ManualLoadError` |
| `drydocs_core/orchestration/crosswalk.py` | a `status: proposed` crosswalk is used at runtime (`require_confirmed`) | `CrosswalkError` |
| `drydocs_core/registry_view.py` | — classifies a dataset only from entries in a RULED status (`applied` / `confirmed`); `proposed` leaves it UNCLASSIFIED and counted | *(reports, does not raise)* |
| `drydocs_lineage/writer.py` | a relationship label's vocabulary entry is not `active` | `GateBoundVocabularyError` |

If you are looking for where a refusal came from, look there — not at the gate page.

### The awkward fact, stated rather than hidden

**This module has twelve modules and exactly one registered CLI verb.** `fid-census` is
the only `drydocs …` command that reaches any of it, and the CLI still imports it
through the ADR 0018 D4 re-export shim rather than its real path. Everything else —
rendering a gate page, running the acceptance suites, rendering a review page,
assembling and publishing a document — is a **library call**, so the procedures below
are written as Python.

The sharpest case is the acceptance suites. `graph-tests/` is mapped to this module in
`drydocs_core/component_map.py`, holds six suites and thirty cases, and has **no
runner**: no verb, no `main()`, no script. Appendix B carries the loop that produced
this page's numbers, because there was nothing to cite.

**In scope.** Rendering a gate page from a `config/gate-prompts/*.yaml` spec and
drafting its log entry; loading and running the `graph-tests/` suites and reading a
failure correctly; rendering the SME review page; the review backbone
(`review_labels`) and the per-source column ledgers (`source_mappings`); the FID and
run-as measurements; the assemble → validate → preview → publish chain.

**Out of scope.** Deciding a gate — that is the SME's, through
`docs/restructure/03-hitl-sme-flow.md`, and the ruling is recorded in
`config/gate-log.md` by a person. Loading anything into the graph (no module here
writes one). The real Confluence push, which is not in this repo at all — see Refresh
step 4. And the `m1-verify` / `m3-verify` / `verify-reference` commands, which read
like this module's job and are not: they are hand-written Cypher in the CLI root and
never touch `graph_verify`.

<!-- anchor: prerequisites -->
## Prerequisites

1. **The toolchain.** `poetry install`. Every command below runs as `poetry run …`.
2. **Nothing else, for three of the four surfaces.** Gate pages, the review page and
   the publish chain are pure and offline: no database, no network, no data root, no
   credentials.
3. **A loaded graph — for the acceptance suites only.** The suites run Cypher, so they
   need a live Neo4j and a populated database. Bring the container up per the
   startup/refresh procedure in `docs/design/drydocs-startup-refresh-runbook.md`, and
   have `.env` at the repo root carrying the `NEO4J_*` names (names only — no secret
   appears in this document).
4. **Know which graph you are about to assert against.** A suite result is a statement
   about ONE database on ONE machine. Write it down before you run, and quote it with
   any number you report.

<!-- anchor: startup -->
## Startup

**There is no service to start.** This module is libraries and one verb; "startup" is
proving that the pieces load and that you know which graph you are pointed at.

1. **The module imports.**

   ```powershell
   poetry run python -c "from drydocs.review import gate_pages, graph_verify, graph_review, review_labels; print('ok')"
   ```

   *Success:* `ok`. Import the `drydocs.review.*` paths, never the flat ones — the old
   module paths are one-cycle re-export shims scheduled for removal at the roll after
   next, and new code that uses them will break then.
2. **The specs and suites are discoverable.**

   ```powershell
   poetry run python -c "from drydocs.review.graph_verify import load_suites; s=load_suites('graph-tests'); print(len(s), sum(len(x.cases) for x in s))"
   ```

   *Success:* measured on this tree, `6 30` — six suites, thirty cases. The count is
   the tree's, not a constant: a new suite file changes it.
3. **For the suites only — confirm the graph.** Note the container, the database name
   and roughly what is loaded, because Verify reads every failure against it.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

Four procedures. Only step 2 needs a database.

### Step 1 — render a gate page from its prompt spec

```python
from drydocs.review.gate_pages import load_gate_spec, render_gate_page, draft_gate_log_entry

spec = load_gate_spec("config/gate-prompts/<slug>.yaml")
page = render_gate_page(spec, page_path="<where you will save it>")
open("<out>.html", "w", encoding="utf-8", newline="\n").write(page)
```

Measured on this tree: 60 prompt specs on disk; rendering `airflow-crosswalk.yaml`
produced a 26,023-byte self-contained page. `page_path` is a **label the footer
prints**, not a destination — the renderer returns a string and writes nothing, so you
choose where it lands, and no directory convention exists for it in this repo.

The page is the SME's working surface: they tick confirmations, the browser saves
progress in `localStorage` and restores it on return, and the page states in its own
text that no graph write happens until the mapping is confirmed. **The repo is the
system of record and the browser is not** — a page whose ticks were never carried into
a written decision has recorded nothing.

`draft_gate_log_entry(spec, answers)` returns a **string draft** of the log entry (4,035
characters for the spec above, with an empty answer set). It is a draft for a person to
edit and paste; nothing in this module appends to `config/gate-log.md`, and nothing
should — the log is a signed record and a tool that writes it unattended would be
forging a signature.

### Step 2 — run the graph acceptance suites

There is no verb. The loop is in Appendix B; run it against a named database and keep
the output. What it does: `load_suites("graph-tests")` reads the YAML, each case's
Cypher runs against the live graph, and `evaluate(case.assertion, rows, case.expected)`
returns `(passed, detail)` for one of three assertions — `empty`, `nonempty`, `equals`.

Two notes for whoever runs it:

- **`evaluate` is pure and takes the assertion, not the case.** `evaluate(case, rows)`
  raises `GraphVerifyError: unhandled assertion` — the signature is
  `evaluate(assertion, rows, expected=None)`.
- **The driver prints `UnknownPropertyKeyWarning` on a partial graph, to stderr.** A
  property the graph has never seen produces a warning per query. That is Neo4j telling
  you the graph is thin, not a failure; keep stdout and stderr separate or the results
  are lost in it.

### Step 3 — render the SME review page

```python
from drydocs.review.graph_review import group_rows, render_review

rows = [ ... ]                                   # node-property dicts, each with a `_label` key
html = render_review(group_rows(rows), title="…", review_labels=None)
```

Pure — **no Neo4j in this module**: the caller fetches the rows and hands them in.
`group_rows` keys on `_label` (not `label`); a row without it lands under `Unlabeled`,
which is how a page silently comes out with one section. Passing a `ReviewLabels`
orders the sections by the review backbone and puts each source's provenance on the
section header; `hidden_props` strips the plumbing columns from every card.

Measured: three synthetic rows across two labels rendered a 1,483-byte page.

### Step 4 — assemble, validate, preview, publish

```python
from drydocs.review.publishing import assembler, validator, preview, publisher

body = assembler.assemble([fragment, ...])          # wraps in DEFAULT_TEMPLATE's {body}
validator.validate(body, raise_on_error=True)       # SEE THE WARNING BELOW
preview.write_preview(body, "<out>.html")
result = publisher.LocalPublisher(out_dir="<dir>").publish(title="…", body=body)
```

> **`validate()` RETURNS its errors and raises only when you ask it to.** The default
> call returns a list — `[]` when clean — so `validator.validate(body)` on its own line
> is a no-op that reads like a check. Pass `raise_on_error=True`, or test the return
> value. This is the one trap in the module.

Measured: the allow-list is `code, expand, info, note, panel, status, tip, toc,
warning`; a disallowed macro returns `macro 'html' not in allow-list [...]`; malformed
XHTML returns `not well-formed XML: mismatched tag: line 3, column 2`.

**About the real Confluence push — it is not in this repo.** The producer ships two
offline publishers only: `NoopPublisher` (records what *would* go, `published=False`)
and `LocalPublisher` (writes the page to a directory). The Confluence implementation —
space coordinates, auth, the internal wrapper — is a company-side gitignored twin
implementing the `Publisher` protocol. **There is therefore no base-URL configuration
key producer-side**, and looking for one is looking for something that does not exist:
the coordinates live in that implementation, not in this repo's config.

<!-- anchor: verify -->
## Verify

1. **A suite result is a statement about the graph it ran on.** This is the section's
   whole teaching point, so here is a real run rather than an idealized one — the same
   loop from Appendix B, on **laptop / `neo4jtest` / database `drydocs`**, a partial
   development graph (2,802 nodes; 28 Documents, 417 Chunks, 17 jobs, 8 folders, 4
   applications, 36 job runs, 0 people):

   ```
   bmc-docs-lexical                   5/5 passed
   bmc-docs-smoke                     2/3 passed      FAIL TC-03: expected 0 rows, got 8
   business-application-identity      4/5 passed      FAIL TC-01: expected 0 rows, got 4
   folder-attribution-coverage      12/12 passed
   provenance-diet                    1/2 passed      FAIL TC-02: expected 0 rows, got 3
   tom-required-contacts              2/3 passed      FAIL TC-01: expected >=1 row, got 0
   TOTAL 26/30
   ```

   **26/30 here is not 26/30 anywhere else, and the four failures are four different
   things.** Reading each one is the skill this section is teaching:

   | Failure | What it found | Reading |
   |---|---|---|
   | `business-application-identity` TC-01, 4 rows | four `:BusinessApplication` with a null `app_id` — 3 from `source: pat`, 1 from `source: registry` | **Venue artifact.** Pre-cutover loaders created them behind the uniqueness constraint's back, because uniqueness ignores nulls. The case description says so. Expected on this machine |
   | `tom-required-contacts` TC-01, 0 rows | no required-and-active `:TOMRole`, though 7 `:TOMRole` nodes exist | **Venue artifact — and the guard working.** This case is an explicit VACUITY guard: without it, TC-03 would pass on an unseeded graph and mean nothing. It is reporting a stale seed, exactly as designed |
   | `provenance-diet` TC-02, 3 rows | `bmc_docs.v1` recorded 374 rows changed with 0 `WAS_GENERATED_BY` edges; `essential_graphrag.v1` twice recorded 43 with 0 | **Not a venue artifact.** Every mismatch has `actual = 0` and both are loader-wide, so this is a consistent statement about two loaders, not drift. Worth a look; not a runbook's call |
   | `bmc-docs-smoke` TC-03, 8 rows | all 8 `:ControlMFolder` are nameless — and they carry no `name` property at all | **Not a venue artifact either.** Every folder here came from `controlm_folders.v1`, which writes the folder name as `sched_table`. The case asserts on `f.name`, a property that loader never writes, so it cannot pass against this loader's output. Whether the case or the loader is wrong is an SME/backlog question |

   The rule to carry away: **before calling a suite failure a defect, ask what is
   loaded.** Two of these four are the graph being partial and two are real
   disagreements — and no total tells you which is which.

2. **The offline surfaces verify without a graph.** Each returns something checkable:
   `load_suites` returns 6 suites / 30 cases; `render_gate_page` returns a non-empty
   self-contained page; `validator.validate` returns `[]` on a clean body and a
   populated list on a bad one; `write_preview` returns the path it wrote.
3. **The unit contract.** These pass on a clean tree with no database:

   ```powershell
   poetry run pytest -q tests/unit/test_gate_pages.py tests/unit/test_graph_verify.py tests/unit/test_graph_review.py tests/unit/test_review_labels.py tests/unit/test_publishing.py tests/unit/test_sme_notes.py tests/unit/test_source_mappings.py tests/unit/test_fid_census.py tests/unit/test_run_as_detect.py
   ```

<!-- anchor: rollback -->
## Rollback

**Nothing in this module writes the graph, so there is nothing to roll back from one.**
That is the module's defining property, not a happy accident, and the four enforcement
points in Purpose & scope are what keep it true elsewhere.

What each surface does write, and how to undo it:

- **Gate page** — `render_gate_page` returns a string and writes nothing. You wrote the
  file; delete it and re-render. The SME's ticks live in that browser's `localStorage`
  and are lost with the file, which is why a decision is not final until a person has
  written it into `config/gate-log.md`.
- **Acceptance suites** — read-only Cypher. A suite that ran is a measurement; there is
  no state to undo. (A suite is not *guaranteed* read-only by the runner — it runs the
  Cypher the YAML carries — so review a new suite's statements like any other.)
- **Review page** — one HTML file at the path you chose.
- **Publishing** — `NoopPublisher` sends nothing by construction. `LocalPublisher`
  writes one file per page into a directory you name; delete it. A real Confluence
  publisher is the company's, and its undo is Confluence's page history, not this
  repo's.
- **`config/gate-log.md`** — the one thing here that must never be rolled back
  automatically. It is a signed record; a wrong entry is corrected by a new entry that
  says so, the way the log already does.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `GraphVerifyError: unhandled assertion: Case(...)` | `evaluate` was passed the CASE; it takes the ASSERTION | `evaluate(case.assertion, rows, case.expected)` |
| The suite output is buried in `UnknownPropertyKeyWarning` text | The driver warns per query about properties this graph has never seen — a thin graph, not a failure | Keep stderr separate (`… 2>$null` in PowerShell); read the warnings once, then ignore them |
| A review page renders one section called `Unlabeled` | `group_rows` keys on `_label`; the rows carry `label` or nothing | Add `_label` to each row |
| A page with a forbidden macro publishes anyway | `validate()` RETURNS errors; the default call does not raise | Pass `raise_on_error=True`, or check the returned list |
| `Missing option '--application'` from `fid-census` | The verb has no default headers or scope, deliberately — the producer has never seen a functional-id directory export | Supply the real options; the column names are the caller's to name |
| `ManualLoadError: … is not status: confirmed` | The manual-loads manifest is gate-bound and has not been confirmed | Take it to the gate; do not edit the status to get past the refusal |
| `CrosswalkError: … is status 'proposed'` | A proposed crosswalk is a gate's INPUT, not a runtime mapping | Confirm it at the gate, or pass `require_confirmed=False` only for gate tooling reviewing it |
| An import of `drydocs.gate_pages` (or any flat name) works today and you are unsure it will tomorrow | Those are one-cycle re-export shims from ADR 0018 D4, due for removal at the roll after next | Import `drydocs.review.<name>` |
| A suite fails and you cannot tell whether it is the code or the graph | The question Verify step 1 exists for | Read what is loaded first; then read the case's Cypher and description |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Procedure owner:** the DryDocs producer (repo owner). Company-side runs against the
  real graph and the real Confluence space are the company session's, in its own repo.
- **Every decision this module surfaces routes to the HITL gate**
  (`docs/restructure/03-hitl-sme-flow.md`), and the ruling is recorded by a person in
  `config/gate-log.md`. This module renders the question and drafts the entry; it never
  answers and never signs.
- **A suite failure is escalated with its venue attached** — the machine, the container
  and the database — or the next reader cannot tell a defect from a partial load. Two
  of the four failures above would be misread as defects without it.
- **A disagreement between this page and the code:** the code wins, and the fix is this
  page. Appendix B re-derives every count here.

<!-- anchor: appendices -->
## Appendices

### A. The module census — twelve modules, one verb

| File | Reached by | What it does |
|---|---|---|
| `drydocs/review/gate_pages.py` | library only | renders a `config/gate-prompts/*.yaml` spec into a self-contained interactive gate page; drafts its log entry |
| `drydocs/review/graph_verify.py` | library only — **no runner exists** | loads the `graph-tests/` TC suites and evaluates their results; the loader and evaluator are pure |
| `drydocs/review/graph_review.py` | library only | renders grouped node rows into the SME review page; no Neo4j in the module |
| `drydocs/review/review_labels.py` | library only | typed accessor over `config/review-labels.yaml` — the review backbone that orders sections and supplies provenance |
| `drydocs/review/source_mappings.py` | library only | typed accessor over `config/source-mappings/<id>.yaml` — the per-source column ledger (project / filter-only / excluded / deferred) |
| `drydocs/review/sme_notes.py` | library only | harvests owner-attributed inline notes from the source into requirement buckets |
| `drydocs/review/fid_census.py` | **`drydocs fid-census`** (through the flat shim) | the K16 phase-0 FID directory census the `fid-identity-and-scope` gate needed |
| `drydocs/review/run_as_detect.py` | library only | K25, `fid_census`'s sibling: cross-application run-as detection |
| `drydocs/review/publishing/assembler.py` | library only | joins XHTML fragments into one body via `DEFAULT_TEMPLATE` |
| `drydocs/review/publishing/validator.py` | library only | well-formedness plus a macro allow-list; returns errors unless `raise_on_error=True` |
| `drydocs/review/publishing/preview.py` | library only | writes an assembled body to a local file, LF endings |
| `drydocs/review/publishing/publisher.py` | library only | the `Publisher` protocol plus `NoopPublisher` and `LocalPublisher`; the Confluence implementation is company-side |

`graph-tests/` belongs to this module too — `drydocs_core/component_map.py` maps it to
`drydocs-review`, because the suites are review's acceptance data.

### B. Re-derive one-liners — the code wins on disagreement

```powershell
# the suites and their case counts
poetry run python -c "from drydocs.review.graph_verify import load_suites; s=load_suites('graph-tests'); print(len(s), sum(len(x.cases) for x in s))"

# the publish macro allow-list
poetry run python -c "from drydocs.review.publishing.validator import DEFAULT_ALLOWED_MACROS; print(sorted(DEFAULT_ALLOWED_MACROS))"

# which registered verbs reach this module (read from Typer, never --help; J37)
poetry run python -c "import drydocs.cli as c; print(sorted(i.name for i in c.app.registered_commands if i.name))"
```

And the suite runner this page used, since the module ships none. Save it outside the
repo, point it at ONE named database, and quote that name with every number it prints:

```python
import os
from drydocs.cli import _client
from drydocs.review.graph_verify import evaluate, load_suites

db = os.environ.get("DRYDOCS_VERIFY_DB", "drydocs")
with _client(db) as client:
    print(f"venue: <machine>, <container>, database {db!r}")
    for suite in load_suites("graph-tests"):
        for case in suite.cases:
            rows = client.run(case.cypher, **(case.params or {}))
            passed, detail = evaluate(case.assertion, rows, case.expected)
            if not passed:
                print(f"FAIL {suite.name} {case.id}: {detail}")
```
