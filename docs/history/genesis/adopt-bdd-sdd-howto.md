# How to Adopt C+D (BDD + Spec-Driven) in DryDocs — Worked Example

> Companion to `feasibility-memo-context-sufficiency.md`. Answers "I don't know how to adopt C+D."
> All data below is **illustrative/synthetic** — no real SIDs, servers, or rosters (CLAUDE.md §3).

---

## 0. The one idea that makes this adoptable

**You do not change how teams work. The agent authors the spec + scenarios from existing
byproducts; the SME only confirms.**

```
existing byproducts                AI agent drafts            SME confirms        graph
(Control-M job, scripts,    →   SDD spec  (intent/reqs)   →   HITL gate     →   Requirement nodes
 schema, Jira story, PR)        BDD .feature (use/test)       (accept/reject)   TestCase nodes + edges
                                                                                 (status: proposed→done)
```

So "adopting BDD+SDD" = **two lightweight templates + one agent that fills them + the HITL gate you
already have.** Agile cadence is untouched; the story stays the *intent trigger*, not the document.

## 1. The two templates (the only new conventions)

### 1a. SDD spec — `spec.md` per job/change (intent + requirements)
Mirrors specdriven.ai's Specify/Clarify phases. Agent fills every field from byproducts; "UNKNOWN —
needs SME" is a *valid, required* value (it triggers abstention, not a guess).

```markdown
# Spec: <job or change name>
- intent:         <why this exists — the business reason>
- requirements:   <- enumerated, testable statements ->
- inputs/outputs: <data assets in / out>
- acceptance:     <- what "correct" means; becomes the BDD scenarios ->
- edge_cases:     <- Clarify: late data, empty file, partial load, SLA breach ->
- sla:            <freshness / completion window>            # likely Internal-Confidential
- owner:          <SEAL / team>
- provenance:     <source span each fact came from>          # mandatory
- open_questions: <- UNKNOWN items routed to SME ->
```

### 1b. BDD feature — `<job>.feature` (use cases + test cases, executable)
Gherkin from cucumber.io: each scenario is simultaneously a use case, an acceptance criterion, and a
runnable test — so the requirement↔verification edge FCD always wanted is *born linked and stays
honest because it executes.*

```gherkin
Feature: Nightly positions load completes and is fresh
  # use case + acceptance + test, all in one artifact

  Scenario: Upstream file arrives on time
    Given the source extract "POSITIONS_YYYYMMDD" landed before 02:00
    When the load job runs
    Then the target table is refreshed
    And downstream consumers see data dated today

  Scenario: Upstream file is late (edge case from spec.clarify)
    Given the source extract has not landed by 02:00
    When the SLA window is checked
    Then the job holds and an alert is raised to the owning team
    And no partial/stale data is published
```

## 2. Worked example — one Control-M job, end to end (illustrative)

**Byproducts the agent starts from (already exist):** a Control-M job `JOB_POSITIONS_LOAD`, its
condition `IN: EXTRACT_POSITIONS_OK`, a shell script `load_positions.sh`, the target table, and a
two-line Jira story *"As an analyst I want fresh positions so that I can report"* — the empty story
from the memo's §3.

**Step 1 — agent drafts the SDD spec** (extraction, SYNTHESIZED):
- intent: *positions must be fresh by start-of-day for downstream regulatory reporting* — **drawn
  from the script comment + consumer list; the Jira story alone could not supply this.**
- requirements: load completes by 02:00; no partial publish; alert on miss.
- acceptance: → the two scenarios above.
- sla: 02:00 completion *(UNKNOWN exact value → routed to SME)*.
- provenance: `load_positions.sh:1-12`, Control-M `JOB_POSITIONS_LOAD`, story KAN-123.

**Step 2 — agent drafts the `.feature`** (the Gherkin above).

**Step 3 — HITL gate.** SME confirms intent + scenarios, fills the one UNKNOWN (SLA = 02:00),
rejects nothing. Three minutes of human time.

**Step 4 — load to graph** (loaders, confirmed edges only):

## 3. How the propositions become graph (the §6 payoff)

```
(Requirement {text:"load completes by 02:00"})-[:VERIFIES]->(Scenario {name:"Upstream on time"})
(Scenario)-[:SPECIFIES]->(Job {name:"JOB_POSITIONS_LOAD"})
(Requirement)-[:DERIVED_FROM]->(Spec)-[:ABOUT]->(Job)
(Spec)-[:HAS_SLA]->(SLA {window:"02:00", classification:"Internal-Confidential"})
```

New edge types (`VERIFIES`, `SPECIFIES`, `DERIVED_FROM`) are **meaning edges** → register in
`relationship_vocabulary.yaml` + `RELATIONSHIP_GUIDE.md`, `status: planned` first, through the HITL
gate (CLAUDE.md §6). PROV-O typing: Spec `wasDerivedFrom` byproducts; Scenario `used` to validate Job.

**Now the agent can answer the questions World A couldn't:**
- "What is correct behaviour if the file is late?" → grounded in Scenario 2 (was: hallucination).
- "What proves the load requirement?" → the VERIFIES edge (was: no such link).
- "What's the SLA?" → the SLA node, SME-confirmed (was: absent/guessed).

## 4. Plugging into DryDocs (no new machinery)

| Need | Existing DryDocs piece |
|---|---|
| Capture job/script/schema as classification | `taxonomy-importer` |
| Propose spec→requirement, scenario→test edges | `ontology-mapper` (`status: proposed`) |
| SME confirm/reject | HITL gate `docs/restructure/03-hitl-sme-flow.md` |
| Register new edge types | `relationship_vocabulary.yaml` + `RELATIONSHIP_GUIDE.md` |
| Sensitivity on SLA/intent | `config/classification.yaml` → `internal/` |
| Run as resumable loop | `plan-incrementalContextLoop.prompt.md` L2–L6 |

The only genuinely new things are the **two templates (§1)** and **one agent operating prompt** that
says: *"read these byproducts, fill spec.md and <job>.feature, mark anything unsupported UNKNOWN, emit
edges as status: proposed."* Everything else is wiring you already have.

## 5. What "adopting" costs, concretely

- **Teams:** nothing new — keep writing stories/PRs/scripts.
- **Agent:** one prompt/skill (`spec-scenario-extractor`) + the two templates.
- **SME:** minutes per job to confirm drafts and answer UNKNOWNs at the gate.
- **You decide once:** the edge vocabulary (`VERIFIES`/`SPECIFIES`/`DERIVED_FROM`) — a one-time
  ontology decision through the gate.

## 6. Next action (pick one)
- **(a) Build the kit:** I create the two template files + the `spec-scenario-extractor` agent prompt,
  and register the three edge types as `status: planned`. *(produces real, reusable files)*
- **(b) Run the pilot:** point me at one real Control-M job (or let me use a synthetic one) and I
  produce its `spec.md` + `.feature` + proposed edges as the L2–L4 checkpoint.
- **(c) Both, in order** — recommended: build the kit, then run the pilot through it.
