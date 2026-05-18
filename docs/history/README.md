# Historical milestone docs

Frozen documentation from prior DryDocs milestones. Kept for context — the
authoritative project README at the repo root reflects the current state
(M3 part 1 + part 2). Anything here can disagree with current code; trust
the root README and the source over these files when they conflict.

| File | Original milestone | What it covers |
| --- | --- | --- |
| [M0-README.md](M0-README.md) | M0 bootstrap | Poetry deps, Neo4j client, ontology backbone seed, constraint DDL, initial CLI |
| [M1-Fix-README.md](M1-Fix-README.md) | M1 hotfix | Restoration of `drydocs/models/seal.py` + schema upgrade after the M3 pack overwrote `models/__init__.py` |
| [LoadPlanV2.md](LoadPlanV2.md) | Planning v2 | Initial Neo4j loader plan (ontology stack, TDQ pipeline, KGoT seam) |
| [LoadPlanV3.md](LoadPlanV3.md) | Planning v3 | Delta on v2 — adds corporate scaffolding, two-port Application pattern, Control-M server mesh, BMC condition-event dependency model, Oracle refresh cadence |
