# Issue-Driven Capture Loop — Grounded Graph + Supplements, Documented by Production Issues

> Companion to `feasibility-memo-context-sufficiency.md` and `adopt-bdd-sdd-howto.md`.
> Aligns with the existing `data-context-extractor` skill: machine-first
> `§META §DATAASSETS §JOBS §UC §CYPHER §OQ` format, existing node/edge vocabulary only.
> All examples illustrative/synthetic — no real SIDs/servers/rosters (CLAUDE.md §3).

---

## 0. The grounding principle (your intent, made the law of this loop)

```
KNOWLEDGE GRAPH = actual relationships = GROUND TRUTH    (USED/GENERATED/ORCHESTRATES/HAS_DATA_FLOW)
        ↑ never overwritten by prose
SUPPLEMENT LAYER = Jira / Confluence / email / RCA       (fills gaps, LINKED to nodes, classified)
        ↑ promoted to a graph edge only via HITL gate
FORCING FUNCTION = production issues                      ("why is this value different?")
        → each issue documents exactly the slice reality just exercised
```

Three rules that keep DryDocs grounded to your intent:
1. **Supplements link, they don't rewrite.** Unstructured content attaches as evidence to existing
   `:DataAsset` / `:ControlMJob` / `:Application` nodes. It never silently creates a relationship —
   that stays an ontology decision through the gate (`ontology-mapper` + HITL, `status: proposed`).
2. **Provenance or it didn't happen.** Every supplement fact carries its source span + trust axis
   (VERBATIM / GROUNDED / SYNTHESIZED) and `classification`.
3. **Issues drive coverage, not a documentation campaign.** We document where production breaks,
   not everywhere — the cheapest path to the context that actually matters.

## 1. Capture what we already have (does C+D content exist? — ingest to find out)

Before authoring anything, harvest existing answers. Each source maps to proposition classes and a
default sensitivity:

| Source | Connector | Yields (proposition class) | Default classification |
|---|---|---|---|
| **Jira** | REST API (stories, acceptance criteria, comments, linked issues) | intent (thin), use-case, some acceptance | Internal |
| **Confluence** | REST API (design pages, runbooks, data dictionaries) | requirements, tech-design, runbook fragments | Internal |
| **Email/chat** | Graph/Gmail API export *(highest risk — defer; R5)* | SLA, decisions, requirement discussions | **Internal-Confidential** |
| **RCA repo / incident tool** | export (postmortems) | root cause, fix, prevention → answers `§OQ` | Internal |

Ingestion writes **supplement records**, not graph edges:
```
§SUPPLEMENTS
- ref:        urn:drydocs:supplement:jira:KAN-123
  about:      urn:drydocs:dataasset:oracle:positions:POSITIONS   # links to a real node
  yields:     [use-case, acceptance]
  trust:      GROUNDED            # quoted from the ticket, not inferred
  classification: Internal
  span:       "KAN-123 §acceptance"
```
If the harvest already contains a usable use-case or acceptance, it **pre-fills `§UC`** and closes an
`§OQ` item with no new authoring. That is the "capture what we have if it exists" step.

## 2. The loop (what happens when an issue occurs)

```
ISSUE raised ("why is POSITIONS value different today?")
  1. SCOPE      → resolve to graph nodes: which DataAsset/Job/Application?         (cypher discovery)
  2. ANSWER     → retrieve grounded graph + linked §SUPPLEMENTS; answer OR abstain
  3. DRAFT DOC  → generate/refresh the Tech-Design-Doc / Runbook from what exists  (§3 template)
  4. EMIT GAPS  → unanswered pieces become §OQ items TAGGED BY METHOD             (§4)
  5. RESOLVE    → SME / RCA answers the §OQ; RCA doc ingested as §SUPPLEMENT       (§5)
  6. CONFIRM    → any new relationship promoted via HITL gate (status: proposed→done)
  7. LEDGER     → record the outcome for graceful-degradation tracking            (§6)
```

Every pass leaves the app/dataset/issue **more documented than before**, and only where it mattered.

## 3. Issue prompt template (reusable — the "why is this value different?" case)

```
ISSUE-PROMPT v1  (data-quality / value-discrepancy)
INPUT:   asset = <DataAsset URN>, symptom = "<observed vs expected>", date = <when>
CONTEXT: grounded graph (lineage USED/GENERATED), linked §SUPPLEMENTS for this asset

DO:
1. Trace upstream: list the jobs that GENERATED this asset and the assets they USED.   [graph = truth]
2. For each hop, state what we KNOW (grounded) vs what is UNKNOWN.
3. Propose the most likely cause ONLY IF grounded; else say "insufficient context — escalate".
4. Emit a Tech-Design-Doc / Runbook section for this asset from what exists (§DOC below).
5. List every gap as an §OQ item, each tagged with the METHOD that should answer it.

OUTPUT (machine-first):
§DOC   (runbook: purpose, inputs, outputs, schedule/SLA, known failure modes, checks)
§OQ    (open questions, method-tagged — see §4)
§LEDGER (one row — see §6)

GUARDRAIL: never assert a cause that isn't grounded. Abstention is a correct answer.
```

Companion templates (same shape, different `ISSUE-PROMPT` head): `late-data`, `job-failure`,
`schema-drift`, `ownership-unknown`. Each produces `§DOC + §OQ + §LEDGER`.

## 4. Gaps become §OQ items, tagged by method (the heart of your ask)

The agent doesn't just say "I don't know" — it says **which method must supply the missing
proposition**, turning a gap into routable work:

```
§OQ
- id:      OQ-POSITIONS-002
  question: "What is the acceptance condition that defines a 'correct' POSITIONS value?"
  missing:  acceptance            # proposition class
  method:   BDD                   # → author a Gherkin scenario  (C)
  route_to: SME / domain expert
  status:   open

- id:      OQ-POSITIONS-003
  question: "What is the SLA freshness window for POSITIONS?"
  missing:  sla
  method:   SDD                   # → fill spec.sla              (D)
  classification: Internal-Confidential
  status:   open

- id:      OQ-POSITIONS-004
  question: "Why does upstream EXTRACT sometimes deliver partial files?"
  missing:  root-cause
  method:   RCA                   # → awaiting postmortem
  status:   open
```

`method ∈ {BDD, SDD, Requirement, RCA, Runbook}` — each tag tells the agent *how* to close it and
ties straight back to the C+D adoption (BDD scenario / SDD spec) from the memo.

## 5. RCA capture closes the loop

When the issue is resolved, the RCA postmortem is ingested as a `§SUPPLEMENT` (trust: GROUNDED,
classification: Internal) and **resolves the matching `§OQ`**:
```
§SUPPLEMENTS
- ref: urn:drydocs:supplement:rca:INC-456
  about: urn:drydocs:dataasset:oracle:positions:POSITIONS
  resolves: [OQ-POSITIONS-004]
  yields: [root-cause, prevention]
  trust: GROUNDED
```
If the RCA establishes a durable relationship (e.g. POSITIONS *depends on* a newly-found upstream
feed), that edge is proposed to the gate — `status: proposed` → SME confirm → loader writes it. Now
the app/dataset/quality-issue **is documented**: runbook + answered UCs + RCA, all grounded.

## 6. Capture, track, and gauge graceful degradation (the KPI)

A per-asset ledger turns "graceful degradation" from a slogan into a tracked metric. One row per
issue-answer:
```
§LEDGER
- asset: POSITIONS  | date: 2026-06-26 | issue: value-discrepancy
  outcome: ABSTAINED            # GROUNDED_ANSWER | ABSTAINED | HALLUCINATION(caught)
  oq_opened: 3  | oq_closed_this_pass: 1
  coverage_by_class: {intent: y, requirement: y, use-case: n, acceptance: n, sla: n}
```
Gauges derived from the ledger:
- **Gracefulness ratio** = `ABSTAINED : HALLUCINATION` when context is insufficient — **want high**.
  A method/asset that abstains instead of fabricating is degrading gracefully (ties to memo §6).
- **§OQ burn-down** per asset — open questions should trend ↓ as issues drive documentation.
- **Coverage heatmap** per asset × proposition class — shows *which* method each gap needs next.
- **MTTD** (mean time to document) — issue raised → matching `§OQ` closed/confirmed.

This is also the running, real-world version of the memo's §6 experiment: production issues
continuously test context sufficiency, and the ledger records whether the system fails safe.

## 7. What's new vs reused (keep it grounded; don't over-build)

| Need | Status |
|---|---|
| `§DATAASSETS §JOBS §UC §CYPHER §OQ` format, USED/GENERATED edges | **reuse** — `data-context-extractor` |
| `§SUPPLEMENTS`, `§DOC` (runbook), `§LEDGER` sections | **new format sections** (machine-first, additive) |
| `:Supplement` / `:Incident` / `:RCA` / `:OpenQuestion` nodes, `:EVIDENCE_FOR` / `:RESOLVES` edges | **ontology decision** → `RELATIONSHIP_GUIDE.md` + vocab, **`status: planned`**, through HITL gate — do NOT auto-create |
| Jira / Confluence / email / RCA connectors | **new ingestion**, classification-gated; email deferred (R5) |
| Graceful-degradation gauges | **derived from `§LEDGER`** — no new infra |

## 8. Next action (pick one)
- **(a) Spec the supplement model:** draft the `§SUPPLEMENTS/§DOC/§LEDGER` template + propose the
  `:Supplement/:RCA/:OpenQuestion` nodes & edges as `status: planned` for the gate.
- **(b) Wire one ingest:** Jira (lowest risk, highest gap-fill) — harvest one app's stories into
  `§SUPPLEMENTS` + pre-filled `§UC`, no graph writes.
- **(c) Run one issue end-to-end:** take one synthetic value-discrepancy on one DataAsset through
  §2's loop → produce `§DOC + §OQ(method-tagged) + §LEDGER`, as the first graceful-degradation row.
- **Recommended order:** (a) → (b) → (c).
```
