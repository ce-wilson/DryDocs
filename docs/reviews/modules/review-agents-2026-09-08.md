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

*(step 4)*

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
