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
