# Human-in-the-loop SME flow — guided per-decision gate

The defined flow that guides you (the SME) when an imported taxonomy is mapped to an ontology
rule. Goal: **maximum control while the model stabilizes** — every ambiguous mapping pauses for
your decision; only the trivially obvious are batched.

## When the gate runs
- After `taxonomy-importer` captures a taxonomy and `ontology-mapper` drafts mappings
  (`status: proposed`).
- When onboarding an orchestrator crosswalk (AutoSys/Airflow native → BMC baseline).
- When a `precedence.yaml` conflict must be resolved (two authorities disagree).

## The decision the agent presents (one mapping at a time)

```
┌─ MAPPING #<n>  (source: <taxonomy source>, authority: <bmc-baseline|internal-standards|lob-product-team>)
│
│  Taxonomy element : <e.g. "Folder contains Job">
│  Proposed meaning : (<FromNode>:<PROVtype>) -[:<LABEL>]-> (<ToNode>:<PROVtype>)
│  Standard term    : <prov:hadMember | org:member | sosa:... | dcat:... | none>
│  Matrix row       : <e.g. "Collection → any = prov:hadMember">
│  Confidence       : <high|medium|low>
│  Open questions   : <...>
│
└─ Your call:  [C]onfirm   [E]dit (change label/term/direction)   [R]eject   [S]kip for now
```

## Routing rules (what pauses vs what batches)

| Situation | Action |
|-----------|--------|
| Matrix row is unambiguous AND reuses an existing confirmed node classification | **batch** — show in a confirm-all list |
| New node type, new label, or new standard term | **pause** — individual decision |
| Two precedence authorities disagree | **pause** — show both, you pick the winner; loser → alias |
| Confidence `low`, or any `open_questions` | **pause** |
| Touches confidential data (real names/SIDs) | **pause + redirect** to `internal/` by id |

## What happens on each call
- **Confirm** → `status: confirmed`, `confirmed_by` + `confirmed_on` set. Eligible for load.
- **Edit** → agent revises the entry; re-presents the changed mapping for confirm.
- **Reject** → `status: rejected` (kept for audit; never loaded). Agent records your reason.
- **Skip** → left `proposed`; revisited next pass.

## Invariants the gate enforces (so the POC drift can't recur)
1. No taxonomy element becomes a graph edge while any of its mappings is `proposed`/`rejected`.
2. Every `confirmed` label maps to a matrix term or a recorded standard term — never a
   freestanding label.
3. A new label must have a `relationship_vocabulary.yaml` entry (`status: planned`) + a
   supplement block (per `docs/RELATIONSHIP_GUIDE.md`) before it can reach `applied`.
4. Precedence is applied, not improvised: the higher authority wins and the decision is logged.

## Your fast path
Most runs you will: confirm a short batch of obvious matrix mappings, then make 2–5 real
decisions on the new/ambiguous ones. The agent always tells you the count up front:
*"3 to confirm in batch, 2 need your decision."*

## Audit trail
Every gate run appends a short log (date, items confirmed/edited/rejected, your reasons for
rejections) to the mapping file's history or a sibling `config/gate-log.md`, so the evolution of
the model is reviewable later.

## Gate-page format (STANDARD — all gate reviews follow this)

Every gate review page is rendered by `drydocs/gate_pages.py` from a spec in
`config/gate-prompts/` and follows the same four-part structure (established by
`controlm-q1q3-phase1`, SME-accepted 2026-07-07; enforced by `tests/unit/test_gate_pages.py`):

1. **Meta header card** — the review's coordinates, always including: `Module`, `Source`
   (system/path, no vendor prose — cite `config/taxonomy/software-registry.yaml` ids per
   ADR 0004), `Registry ref` (the `config/source-registry.yaml` id + confirmation state),
   and `Classification`. Add `Taxonomy` / `Ontology map` / `Source of record` refs when the
   gate binds a mapping.
2. **Mini-ER overview** — source element → graph target → edge, one row per mapping;
   anything not yet gated/loaded is tagged `[PROPOSED]`.
3. **Property provenance** — per label, every property badged **SOURCE** (straight column)
   or **DERIVED** (with the derivation rule), so the SME always sees what came from the
   source versus what DryDocs inferred. Scope filters and proposed normalizations are
   DERIVED rows with notes.
4. **Confirmations** — the tick-through sections; the last confirmation is always "safe to
   transcribe into `config/gate-log.md`".

Committed specs are **mechanism-only** (column names and rules — never real folder names,
SIDs, or data values); pages for real PAT/SEAL steps render from a gitignored twin. Rendered
HTML goes to a gitignored dir (`internal-local/gate-pages/`), never the repo.

## Promotion: `drydocs_context` → `drydocs` (trust axis = DB boundary)

The multi-DB topology (ADR 0002) keeps **uncertain** context (`drydocs-deepdoc` output, stamped
`reliability`/`trust`) in `drydocs_context`, structurally isolated from the **curated ground
truth** in `drydocs`. Moving a node across that boundary is a *trust promotion*, and it runs
through this gate like any other meaning decision:

- **Promotion is ONLY ever a gate-confirmed WRITE to `drydocs`** — the item is presented as
  `status: proposed`, and on **Confirm** a *loader* writes the ground-truth shape into `drydocs`
  (constraint-on-key MERGE on the canonical URN / business key).
- **Never an in-place cross-DB edit.** There is no "move", no relabel-in-place, no direct
  `drydocs_context` → `drydocs` copy outside a loader. The original `drydocs_context` record is
  left intact (it is the provenance of the promotion) — the composite (`drydocs_all`) continues
  to join both on the shared business key.
- **Per-item decision presentation** — each candidate promotion is shown in the same frame as
  §"The decision the agent presents": the uncertain node, its `reliability`/`trust` stamps, the
  evidence that matured it (verified against source, SME attestation, corroborating extract),
  and the exact ground-truth write it would become. Routing rules apply unchanged: low
  confidence or open questions **pause**; nothing batches unless it reuses an already-confirmed
  classification.
- **Gate-log audit requirement** — every promotion (and every rejection) lands in the §"Audit
  trail" log with the evidence cited, so `drydocs` can always answer *why* a once-uncertain
  fact is now ground truth.
- **Timing caveat (ADR 0002 rollout):** promotion is **paused until core stabilizes** — the
  destroy-and-rebuild development loop makes `drydocs` disposable right now; `drydocs_context`
  records survive rebuilds and re-link through the URN key, so nothing is lost by waiting.
