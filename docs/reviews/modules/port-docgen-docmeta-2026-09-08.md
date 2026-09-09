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

*(step 3 — tests, guards, linter, counts; raw numbers recorded as they arrive)*

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
