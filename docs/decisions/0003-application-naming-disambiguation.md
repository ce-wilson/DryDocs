# ADR 0003 — "Application" naming disambiguation: source terms stay verbatim, one canonical label, reconcile by relationship

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-07-05        # revised same day after the company-side root-cause fix landed
deciders: [chad.wilson, ontology-mapper, SME-gate]
layer: 2-ontology
affects:
  - docs/RELATIONSHIP_GUIDE.md
  - config/taxonomy-ontology-map.yaml
  - docs/port-prompt.md            # company-side adapter fix + ControlMFolder rename
```

## Context

"Application" is the single most overloaded term in the estate and it collides
across three distinct meanings:

1. **Control-M `APPLICATION`** — a free-form BMC job-grouping field. Teams use
   it inconsistently (some put a Platform name, some a 3-char appcode). It is
   **not** a reliable business-app identifier.
2. **`:Application` (SEAL)** — the canonical business-application node, keyed
   by `seal_id`, carrying governance metadata from `DECO_SEAL_APP_INFO`. Used
   in 80+ places across schema, snapshot writer, README, and standards docs.
3. **Colloquial "application"** — installed software / a running system.

The trigger was a *mechanical* failure on the company side: the ingest died
with "SQL references bind :Application but no value was provided."

### Root cause (as diagnosed and fixed company-side)

The company bind renderer (`jdbc_oracle_adapter.py`, `_BIND_RE =
(?<![\w]):([A-Za-z_]\w*)`) scanned the **entire SQL text** and treated every
`:word` token as a required bind — including tokens inside `--` comments and
string literals. Folder-scoped runs supply only `folder_filter / run_as /
developer_sid / row_cap`, so `:Application` in the `controlm_jobs.sql` line-34
comment raised a KeyError. The next chain stage would have failed identically:
`controlm_dependencies_recursive.sql` has `:DEPENDS_ON` in a comment **and**
the string literal `':depends_on'` (lines 62/124) — a colon that is *emitted
data* and cannot be fixed by editing text.

**The fix (company-side, correct):** `_render_sql` was hardened to substitute
binds **only in code regions** — `--` line comments, `/* */` block comments,
`'single-quoted strings'`, and `"quoted identifiers"` are copied verbatim.
This matches how the Oracle server itself parses statements. The `.sql` files
were left untouched; `:Application` / `:DEPENDS_ON` in comments is *valid
graph-label notation* and is preserved. Verified against all six chain SQL
files (no KeyError; `':depends_on'` literal intact). An earlier producer-side
attempt to de-colonize the comments was reverted — the SQL loaders are
Canonical-here on port, and edited comments would have clobbered company
originals.

Known edge (documented, not fixed): Oracle alternative quoting `q'[...]'`
is not recognized by the region scanner. No chain SQL uses it; if one ever
does, extend `_render_sql` first.

The taxonomy question raised alongside the bug: should the software
`:Application` concept be renamed (e.g. to `BusApp`) so Control-M loads and
taxonomy mapping stop colliding?

## Decision

**Keep `:Application` as the single canonical business-app label. Keep source
fields verbatim on source-labeled nodes. Reconcile only by explicit
relationship, never by string-matching the Control-M field. Disambiguate
source-system labels with the `ControlM` prefix, not by renaming the canon.**

Four rules this ADR codifies (into `docs/RELATIONSHIP_GUIDE.md`):

1. **Source-system fields stay verbatim on source-labeled nodes.**
   `(:ControlMJob).application` keeps its source name — the node label *is*
   the namespace. Its documented meaning is "Control-M app code", never the
   SEAL name (see controlm_jobs.cypher header).
2. **One canonical graph concept for business application: `:Application`,
   keyed by `seal_id`.** Loaders other than the SEAL loader never MERGE
   `:Application` nodes. Source-side labels take the source prefix instead:
   `ControlMJob`, `ControlMServer`, and (company-side rename, 2026-07)
   **`ControlMFolder` — formerly `JobFolder`** — so every BMC-sourced label
   is self-namespacing.
3. **Reconciliation is a relationship, not a string.** Control-M → SEAL
   linkage goes through the folder-name 3-char appcode mechanism (positions
   3-5, per docs/m3_controlm_concept_mapping.md), materialized as an explicit
   edge — never inferred from `J.APPLICATION` equality.
4. **Bind renderers substitute only in code regions.** Colon-prefixed
   graph-label notation (`:Application`, `:DEPENDS_ON`) in SQL comments and
   string literals is legitimate and must survive rendering verbatim. Never
   "fix" a renderer bug by editing the SQL.

## Options considered

**A. Rename `:Application` → `BusApp` (rejected).** Abbreviations read poorly
in Cypher and to future readers; `BusApp` trades one ambiguity for another.

**B. Rename `:Application` → `:BusinessApplication` (rejected *for now*).**
The spelled-out label is the better name in isolation — if a rename ever
happens, this is the target, not `BusApp`. Rejected today for a structural
reason: `:Application` appears in 80+ locations plus the live graph, so the
rename is a migration with constraint churn — while the collision was a
renderer bug, now fixed mechanically. Revisit only via a dedicated migration
ADR (this one would be SUPERSEDED).

**C. De-colonize SQL comments (attempted producer-side, reverted).** Treats
the symptom in text the renderer should never have scanned, cannot fix the
`':depends_on'` data literal at all, and diverges Canonical-here files from
company originals. The renderer fix supersedes it.

**D. Keep the name, fix the renderer, prefix source labels (accepted).**

## Consequences

- Zero `:Application` migration; `seal_id`-keyed identity untouched.
- The failure class is fixed once in the adapter, for every present and
  future `.sql` file, instead of policed file-by-file in comments.
- `ControlMFolder` completes the source-prefix pattern for BMC labels.
  **Producer-side rename `JobFolder` → `ControlMFolder` is required before
  the next port** — the cypher loaders are Canonical-here, and porting them
  unrenamed would clobber the company rename (see docs/port-prompt.md).
- `:Application` remains colloquially ambiguous in conversation; readers
  learn "in the graph, `:Application` = SEAL."

## Follow-up (small, bounded)

1. ~~Producer-side label rename `JobFolder` → `ControlMFolder` (cypher loaders,
   constraints, README, docs) + migration cypher for existing local graphs.~~
   **DONE 2026-07-05** — repo-wide rename; migration at
   `drydocs/migrations/20260705_rename_jobfolder_to_controlmfolder.cypher`
   (constraint `folder_id` → `controlmfolder_id`).
2. Add rules 1–4 to `docs/RELATIONSHIP_GUIDE.md` ("naming collisions").
3. Route through the SME gate (`docs/restructure/03-hitl-sme-flow.md`) to move
   this ADR `PROPOSED → ACCEPTED`.
