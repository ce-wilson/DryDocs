# drydocs-review + drydocs-agents — module review, 2026-09-08

reviewed_commit: 191a71ab
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 5, carrying docs/reviews/company-owed-path-review-2026-09-08.md and a re-stamped depgraph snapshot)
reviewed_port_base: port-base-20260908 — producer-side review. NOTE: this moved during today's sweep; slots 1-5 were stamped `port-base-20260905`.
slot: 6 of 10 (slug `review-agents`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['review']` and `COMPONENT_GROUPS['agents']`, read from
  `drydocs_core/component_map.py` (J37, the importable object) at this firing — 11 prefixes:
  `agents`, `drydocs.fid_census`, `drydocs.gate_pages`, `drydocs.graph_review`,
  `drydocs.graph_verify`, `drydocs.publishing`, `drydocs.review`, `drydocs.review_labels`,
  `drydocs.run_as_detect`, `drydocs.sme_notes`, `drydocs.source_mappings`
prior report: first pass

- **Reviewed at:** commit `191a71ab` on `review/module-sweep`, port base `port-base-20260908`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**This is the first slot holding TWO modules, and they are unlike each other.**
`drydocs-review` is ten dotted prefixes under `drydocs.` — the HITL surface: graph review
and verify, SME notes, review labels, gate pages, publishing. `drydocs-agents` is the
single prefix `agents`, which is not a `drydocs_*` package at all but the ADK app tree
with its own venv (`agents/.venv`, the one that leaks into this shell as `VIRTUAL_ENV`).
The plan sized them together at 4,851 lines. Where the two halves differ, this report says
which half it is talking about rather than averaging them.

## Measurements

Taken before any module code was read. The two halves are counted separately.

| measure | `drydocs-review` | `drydocs-agents` |
|---|---|---|
| first-party Python | **2,317 lines** | **4,901 lines**, 33 files (excludes `agents/.venv`) |
| shape | `drydocs/review/` package 2,197 + `publishing/` 24 + **8 re-export shims at 12 lines each** | the ADK app tree, own venv |
| largest unit | `review/gate_pages.py` 431 · `source_mappings.py` 382 · `fid_census.py` 366 | — |
| combined | **7,218 lines** against the plan table's 4,851 on 2026-09-05 — **+49%**, the largest gap yet | |

| both halves | |
|---|---|
| tests naming either | **40** files |
| scoped suite | **602 passed, 12 skipped**, 30s |
| `ruff check drydocs/review/ agents/` | clean |
| committed acceptance suites | **6** in `graph-tests/`, **30 assertions**: 28 `empty`, 2 `nonempty` |

**+49% is the widest divergence from the plan table so far** (slot 4 was +36%, slot 3
+16%, slot 5 exactly on). Four of the six slots measured have come in over. That is now a
pattern rather than a slot fact, and belongs to slot 10 rather than to any module: either
the table is stale by design and should say so, or the rotation is being sized against
numbers that no longer hold.

**One skip is a venue fact worth naming (J18):** `test_session_redaction.py:261` skips
because *"google-adk lives in agents/.venv, not this interpreter"*. The `agents` half is
therefore only partly exercised by this worktree's suite by construction — its own venv
is where its dependencies live. That is the same split that made the `api` group matter in
slot 4, and unlike that one it cannot be fixed by installing a group here: the ADK tree is
deliberately a separate environment.

## Lens 1 — system design

**The recurring pattern of this sweep reaches its highest-stakes instance here: the tool
whose job is to certify the graph reports PASS against a graph that is not there.**

### L1-1 — four of six acceptance suites cannot fail on an empty graph

`drydocs/review/graph_verify.py` is the *"data-driven Cypher acceptance runner"*: it loads
`TC-*` YAML suites from `graph-tests/`, runs each case's Cypher against a live graph, and
asserts a result shape — `empty`, `nonempty`, or `equals`. *"A suite fails (non-zero exit)
if any case fails."*

`evaluate` (`:136-148`) is pure and does exactly what it says:

```python
if assertion is Assertion.EMPTY:
    return (len(rows) == 0, ...)
```

There is **no precondition anywhere** — no anchor case, no row-count floor, no "is
anything loaded" check before the assertions are evaluated. So an `empty` case passes
whenever the query returns nothing, including when it returns nothing because the graph
holds nothing.

That would be harmless if suites mixed positive and negative assertions. **They do not.**
Counted across the six committed suites — 30 assertions, **28 `empty` and 2 `nonempty`**:

| suite | `empty` | `nonempty` | |
|---|---|---|---|
| `folder-attribution-coverage.yaml` | **12** | **0** | cannot fail on an empty graph |
| `bmc-docs-lexical.yaml` | **5** | **0** | cannot fail on an empty graph |
| `business-application-identity.yaml` | **5** | **0** | cannot fail on an empty graph |
| `provenance-diet.yaml` | **2** | **0** | cannot fail on an empty graph |
| `bmc-docs-smoke.yaml` | 2 | 1 | anchored |
| `tom-required-contacts.yaml` | 2 | 1 | anchored |

**Four of six suites, and 24 of 30 assertions, are unfalsifiable against an unloaded
graph.** The shape is inherent to what these suites are for — a negative assertion
("no folder lacks attribution", "no document is orphaned") is the natural way to express
a standard — and that is exactly why the runner has to supply the anchor the suite cannot.

**Consequence, and it is the sharpest version of this sweep's recurring finding.** A green
`graph-verify` run means *either* "the estate conforms to every rule in this suite" *or*
"the database was empty and every rule was vacuously satisfied", and the runner cannot
tell the reader which. `folder-attribution-coverage.yaml` is the clearest case: a
**coverage** suite, 12 negative assertions, no anchor — it cannot detect the absence of
the very thing whose coverage it measures. Because this is the acceptance gate, a false
green does not merely mislead; it ends the check.

**Cheapest correction:** a per-suite precondition, asserted by the runner before any case
is evaluated. The suite declares an anchor — a `nonempty` case, or a minimum row count on
a named label — and the runner reports `NOT RUN` rather than `PASS` when it fails. The
loader and evaluator are already pure and offline, so this is testable without Neo4j, and
the vocabulary already exists in the component: slot 3's `equivalence.py` calls the third
state **not proven** and rules that *"no evidence is never evidence."* This is that rule,
applied to the tool that certifies everything else.

### L1-2 — what this slot already gets right, recorded so no later firing re-audits it

- **The verifier writes nothing and says why it needs no gate.** *"The graph is only READ —
  this component writes no meaning edges, so it needs no HITL gate to run"*
  (`graph_verify.py:9-11`). The permission argument is made from the behaviour rather
  than asserted.
- **The classification boundary is stated at the file that would breach it.** The
  committed suite is a vendor-BMC smoke test, Internal-Public; *"real acceptance suites
  (internal counts/IDs) live in a gitignored twin"* (`:13-14`). Which also means the
  `empty`/`nonempty` ratio measured above is of the PUBLIC suites — the twin may be
  anchored differently, and this report cannot see it. **Recorded as a limit on the
  finding, not a hedge:** the four unanchored suites named are the ones that ship.
- **`unknown_targets` ties the suites to the review backbone** (`:151-158`) — a suite
  targeting a label the `review_labels` backbone does not know is reported, and the
  cross-check is kept pure by passing the backbone in rather than importing it.

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
