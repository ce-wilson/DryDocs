# Port prompt — apply DryDocs1 onto the original `<company-org>/DryDocs` base

Hand this prompt to an agent working in a clean checkout of the company
`<company-org>/DryDocs` `main` (GitHub Enterprise). It executes the one-way
producer→consumer port described in [`git-readme.md`](../git-readme.md), which stays the
source of truth for the per-path disposition tables. This prompt is the actionable
wrapper; `git-readme.md` is the authority.

```text
You are porting the DryDocs1 PRODUCER repo (ce-wilson/DryDocs1, github.com) onto the
original/superseded <company-org>/DryDocs base (GitHub Enterprise). This is a ONE-WAY
producer→consumer apply. Work in a clean checkout of company `main`.

AUTHORITATIVE INSTRUCTIONS: the producer carries its own port guide at `git-readme.md`
(repo root). Fetch it and follow it exactly — it holds the per-path disposition tables
(Canonical-here / Clean-adds / Collisions) and the acceptance oracle. If anything in this
prompt and git-readme.md disagree, git-readme.md wins. Do not duplicate or improvise around it.

CRITICAL CAVEAT — DISJOINT HISTORIES. The producer was `git init`-ed fresh; there is NO
common ancestor with company main, so there is no 3-way merge base. This is a CHERRY-PICK
/ `git am --3way`, NOT `git merge`/`git pull`. A `merge=ours` gitattributes rule does NOT
help (it keeps the wrong side). Every path is either a clean-add (applies untouched) or a
collision (reconcile by hand, every time).

PROCEDURE:
1. From the company main checkout:
     git remote add drydocs1 https://github.com/ce-wilson/DryDocs1.git
     git fetch drydocs1 main
2. READ THE GUIDE FIRST: `git show drydocs1/main:git-readme.md`. Internalize its three
   tables (Canonical-here, Clean-adds, Collisions) before touching anything.
3. git switch -c drydocs-port main
4. List the commit range (histories disjoint → all of it is new vs company main):
     git log --oneline --reverse drydocs1/main
   Identify commits by SUBJECT, not SHA (a rebase rewrites SHAs). The Control-M
   normalization stream is the three subjects "…variable taxonomy (Phase A)…" →
   "…variable resolver (Phase B)…" → "…Phase C command/script parser…", applied in that
   order; everything else is additive docs + ontology + the v1 restructure.
5. Cherry-pick the range: git cherry-pick <oldest>^..<newest>   (or format-patch +
   `git am --3way`). Clean-adds apply silently; cherry-pick stops on each collision.
6. RESOLVE EACH COLLISION per git-readme.md:
   - Canonical-here (take the producer version WHOLESALE, do not hand-merge): the entire
     v1 restructure — CLAUDE.md, PUBLISH-BOUNDARY.md, reference/, external/orchestration/,
     config/, internal/, .claude/agents/, docs/restructure/; plus drydocs/controlm/,
     knowledge/standards/, the Control-M SQL loaders, relationship_vocabulary.yaml,
     catalog_ontology_supplement.cypher.
   - Integration points (PRE-EXIST on company main → WILL conflict, hand-merge preserving
     exactly the "what to preserve" column): drydocs/cli.py (gains `analyze-variables` +
     `normalize-variables` commands and `.controlm` imports; existing command bodies
     unchanged), drydocs/models/controlm.py, drydocs/models/__init__.py.
   - Then `git add <path>` and `git cherry-pick --continue`.
7. ONE RENAME: vendor/bmc-controlm/ → external/orchestration/bmc-controlm/. If company main
   still has vendor/bmc-controlm/, delete it after taking the new path (across disjoint
   history git sees the move as delete+add); references were already repointed producer-side.
8. SCHEMA CONSOLIDATION (constraints.cypher key corrections, deleted m1/m3_* patch files,
   `apply-m3-supplement`→`apply-ontology-supplement` rename): the company baseline may have
   fixed these differently — EVALUATE each against company main before applying, per
   git-readme's "Schema consolidation" section. Authoritative bootstrap order:
   constraints → ontology → ontology_supplement → seal_ontology_supplement →
   catalog_ontology_supplement.
9. ARCHITECTURE-DECISIONS STREAM + MODULAR SPLIT (all clean-adds): docs/decisions/ (ADR 0001
   ontology base; ADR 0002 component & database topology + 0002-a/0002-b), MODULE_MAP.md, and
   tests/unit/test_module_boundary.py apply untouched — see git-readme.md's "Architecture decisions
   + modular split" section. It also flags the planned drydocs/ → drydocs-core package move
   (ADR 0002, Phase B), which is NOT yet executed; this port still targets the flat drydocs/ layout.

ACCEPTANCE GATE (behavior is the contract, not a byte-compare):
- Track 1 (portable, no production sample present):
    poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py \
                      tests/unit/test_variable_staging.py tests/unit/test_command_parser.py \
                      tests/unit/test_module_boundary.py -q
  Expect 88 passed, 3 skipped — the four variable-stream files give 86 passed / 3 skipped (the 3
  skips are sample-backed test_sample_*, which skip when the .gitignore'd production CSV is absent),
  plus 2 from the stdlib core/component boundary guard (test_module_boundary.py, ADR 0002-a Phase A;
  pure stdlib, no data, so it runs anywhere). A FileNotFoundError on controlm_variables__sample.csv
  means the skip guard was lost — fix it.
- Full `pytest tests/unit/` must be green (passes + sample-skips + the PyYAML test_schema.py
  skips). ZERO failures is the contract. Both CI guards must pass: test_schema.py (no `active`
  relationship without its supplement block) and test_classification.py (every source in
  source-registry.yaml has a valid sensitivity classification). New dep: PyYAML.

BOUNDARIES:
- One-way only. Never add company main as a remote on the producer; never push back to
  ce-wilson/DryDocs1.
- drydocs/data/ is .gitignore'd — sample CSVs stay local, never transfer.
- Never commit real SIDs, credentials, server addresses, GHE org names, or production data
  values; internal/ is the only home for confidential data and is stripped on publish
  (PUBLISH-BOUNDARY.md).
- When done, open drydocs-port as a PR onto company main; do not fast-forward main directly.
```
