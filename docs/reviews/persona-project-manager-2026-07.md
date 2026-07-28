# Persona review — Project manager (code-graph Phase 2, U2)

> **Run: 2026-07-28** against the live `drydocs` code graph (snapshot
> `drydocs-20260728-0754.json`, commit `36866f9`, 194 modules) and
> `backlog.yaml` at the same commit (todo 50 / done 153 at probe time).
> Plan: [`code-graph-review-plan.md`](code-graph-review-plan.md).
> ZERO backlog edits — mismatches route through IDEAS.

## Verdict up front

The backlog is telling the truth. 80 recently-closed items carrying 91
concrete path claims audited: **zero false done-claims**. All 30
`next_ready` items have live `inputs:` paths. The one structural gap is in
the *instrument*, not the ledger: **`drydocs_api` is a real Python package
that is not a scan root**, so a whole component is invisible to the code
graph (unit 2). That joins Phase 1's scanner finding as the second half of
one fix.

## Unit 1 — done-claims spot check (drift table)

Method: every `done` item whose notes/acceptance carry a 2026-07-15..29
date, every `path/like.ext` claim extracted, verified against the graph
(`.py` → `:CodeModule.file_id`) and the filesystem (everything else).
80 items, 91 claims; 8 flagged by the mechanical pass, each then
human-read:

| Item | Claim | Graph/disk verdict | Disposition |
|---|---|---|---|
| D4 | `models/controlm.py` | full path `drydocs_core/models/controlm.py` IS in graph | matcher artifact (relative prose) — claim TRUE |
| G28 | `provisioning/01_databases.cypher` | full path `drydocs_core/schema/provisioning/01_databases.cypher` on disk | matcher artifact — claim TRUE |
| O8 | `components/Shell.tsx` | lives at `web/src/layout/Shell.tsx` | benign rename in a historical close note (layout move post-dates the note) — no action, close notes are append-only history |
| O14 | `docs/runbook-mapping-demo.md` | relocated by **L14** (done) to `docs/design/drydocs-mapping-demo-runbook.md` | relocation is itself a recorded done item — self-consistent |
| L14 | input `docs/runbook-mapping-demo.md` | gone — L14 consumed and relocated it | stale input on a DONE item = historical, fine (the U2.3 rule only bites on todo items) |
| J11 | `docs/controlm-loader-flow.md` | now `docs/history/controlm-loader-flow.md` | J11 WAS the git-mv item — self-verifying |
| C18 | `drydocs_core/models/catalog.py` | absent everywhere | C18's title is "DELETE the stale shadow catalog models" — absence IS the acceptance. TRUE |
| C19 | `ontology/reference/swo_sdlc_ontology.cypher` | never existed in this tree | the savepoint path C19 documented as never-ported — quoted deliberately. TRUE |

**Zero real drift.** The two renames (O8, O14/L14) are historical notes
describing then-current paths; the ledger's discipline of recording moves
as their own items (J11, L14) is what makes them auditable.

## Unit 2 — module-registry census

Graph projects (6): `drydocs, drydocs_core, drydocs_deepdoc,
drydocs_lineage, drydocs_remediation, tests` — top-level `file_id`
prefixes match exactly (no unclaimed graph region; D7
`removed_from_source_at` count = 0, no zombie files).

Registry (18 modules) → graph mapping:

- **Code-claiming and present**: drydocs-core→`drydocs_core`,
  drydocs-lineage→`drydocs_lineage`, drydocs-remediation→
  `drydocs_remediation`, drydocs-deepdoc→`drydocs_deepdoc`;
  drydocs-load / drydocs-docgen / drydocs-review / drydocs-plan /
  drydocs-agents all live inside the `drydocs` root (MODULE_MAP's
  per-file split — finer than the graph's per-root `project`).
- **Code-claiming and ABSENT from the graph**: **drydocs-api** —
  `drydocs_api/` holds ~10 Python modules (app, handlers, query_specs,
  routing, mappings, guard, …) and is not a scan root. Every Phase-1
  metric silently excluded it. → IDEAS line (add scan root #7; pairs
  with the U1 cross-root-edges fix).
  Also **drydocs-web** → `web/` (TypeScript — out of a *Python* scanner's
  scope by design; census notes it, no action).
- **Work-area modules with no code claim by design**: config, docs,
  ontology, reference, taxonomy, graph-infra, drydocs-docmeta,
  drydocs-plan(board rendering scripts live under scripts/, also
  unscanned — same bucket as the U1 scripts-entry note).

## Unit 3 — todo reality check

All 30 `next_ready` items: every `inputs:` path exists (graph or
filesystem). **0 stale — no item needs a re-groom before an agent burns a
session on it.**

## Unit 4 — per-epic code footprint (recent done items × named roots)

| Epic | Roots touched (recent closes) | Charter drift? |
|---|---|---|
| component-topology (G) | drydocs, drydocs_core, drydocs_api, drydocs_lineage, drydocs_deepdoc, config, tests | no — the topology epic is SUPPOSED to span roots |
| ontology-mapping (C) | drydocs_core, drydocs, docs, external, knowledge, scripts, tests | no |
| web-console (O) | web, drydocs_api, drydocs, config, docs, scripts, tests | no |
| release-infrastructure (J) | config, docs, scripts, tests | no |
| doc-infrastructure (L) | config, docs (+ drydocs loaders via L17, closed after probe) | no |
| config-loaders (D) | drydocs_core, internal-local, tests | no |
| seal-attribution (K/M) | config, docs | consistent with the phase being at gates |
| docmeta (Q) | docs, drydocs, knowledge, reference | no |

No epic's footprint contradicts its charter. The visible pattern worth one
sentence: web-console and component-topology both write into
`drydocs_api` — the same package the graph can't see (unit 2), so the two
most active epics are the ones most under-measured.

## IDEAS lines filed

- `[bug]` scan roots exclude `drydocs_api` (folded into the Phase-1
  scanner line — one fix, two symptoms).

Nothing else was actionable: the ledger, its roll-ups, and its inputs all
verified true.
