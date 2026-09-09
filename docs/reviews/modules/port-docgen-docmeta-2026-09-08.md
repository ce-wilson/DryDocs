# drydocs-port + drydocs-docgen + drydocs-docmeta — module review, 2026-09-08

reviewed_commit: b7fb5f54
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 6, carrying tests/unit/test_never_port_citations.py and tests/unit/test_port_drops.py, both in this slot's subject area)
reviewed_port_base: port-base-20260908 — producer-side review
slot: 7 of 10 (slug `port-docgen-docmeta`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['port']`, `['docgen']` and `['docmeta']`, read from
  `drydocs_core/component_map.py` (J37, the importable object) at this firing — 10 prefixes:
  `drydocs.design_doc`, `drydocs.doc_outline`, `drydocs.doc_pdf`, `drydocs.docgen`,
  `drydocs.plan_ideas`, `drydocs.port`, `drydocs.port_backlog_union`, `drydocs.port_preflight`,
  `drydocs.port_rename_detect`, `drydocs_docmeta`
prior report: first pass

- **Reviewed at:** commit `b7fb5f54` on `review/module-sweep`, port base `port-base-20260908`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**Three modules, and the port half is the repo's highest-consequence surface.** The port
component decides what crosses from this producer repo to the company one. A false
positive there is not a wrong number on a page — it is internal material leaving the
publish boundary, or a never-port document crossing it. `PUBLISH-BOUNDARY.md` and
CLAUDE.md §3 are the standard this half is measured against, and the sweep's own recurring
question ("does a result state the limits of its method") is unusually sharp for a
preflight that answers "safe to port".

**Known inheritance from slot 6, not to be re-reported here.** Ten of the eighteen ADR
0018 D4 re-export shims live in this slot's prefixes (`design_doc`, `doc_outline`,
`doc_pdf`, `plan_ideas`, `port_backlog_union`, `port_preflight`, `port_rename_detect` and
siblings). Slot 6 found that their stated removal trigger fired today and that no item was
minted, and recommended grooming it ONCE across all four components. This report counts
them and does not re-derive the finding.

## Measurements

Taken before any module code was read.

| module | lines | shape |
|---|---|---|
| `drydocs/port/` | **2,786** | 9 files — `port_rename_detect` 638, `port_preflight` 544, `port_completeness` 463, `port_drops` 317, `reconcile_before` 308, `port_backlog_union` 250, `gate_log_redactions` 178, `dispositions` 82 |
| `drydocs/docgen/` | **1,189** | 5 files |
| `drydocs_docmeta/` | **1,105** | package |
| ADR 0018 shims in scope | **84** | 7 files × 12 lines |
| **combined** | **5,164** | against the plan table's 3,770 — **+37%** |

| both halves | |
|---|---|
| tests naming any of the three | **26** files |
| scoped suite | **485 passed, 9 skipped**, 43s |
| `ruff check drydocs/port/ drydocs/docgen/ drydocs_docmeta/` | clean |

**Correction to this report's own skeleton.** The skeleton said ten of slot 6's eighteen
shims live in this slot's prefixes. The real count is **seven** — `design_doc`,
`doc_outline`, `doc_pdf`, `plan_ideas`, `port_backlog_union`, `port_preflight`,
`port_rename_detect`. The remaining eleven are slot 6's eight, slot 8's `plan_board` and
`plan_roadmap`, and one package `__init__`. Recorded rather than silently edited, because
a later reader comparing the two numbers should see which one was checked.

**Five of seven slots have now come in over the plan table** (+37% here, after +49%, +36%,
+16%, one exactly on). The pattern is stable enough to stop being a per-slot note; slot 6
already raised it as a candidate for slot 10.

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
