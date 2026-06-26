# Feasibility Memo — Which Development Method Captures Enough Context for a Non-Hallucinating Agent?

**Prepared for:** DryDocs direction decision
**Author persona:** SDLC + data-warehouse + AI/LLM
**Supersedes:** the §FEASIBILITY section of `plan-incrementalContextLoop.prompt.md` (rescoped per request)
**Date:** 2026-06-26

---

## 1. The question, stated precisely

DryDocs captures application data well at the **structural/operational** layer (Control-M lineage,
SEAL ownership, Oracle schema, scripts). What it is **missing now** is the *human-intent* layer:

> **intent · requirements · use cases · test cases**

The decision is not "Agile vs waterfall." It is: **which software-development method's documentation
discipline should we adopt (or mine) so that its natural byproducts supply those missing
propositions — enough for an agent to answer support/SDLC questions without hallucinating?**

Four methods are in scope, on a spectrum of how much *grounded, machine-readable intent* each emits
as a byproduct:

- **Waterfall** — heavy upfront documents (BRD, requirements, test design, traceability matrix).
- **Agile** — "just enough": the canonical user story `As a <role>, I want <X>, so that <Y>`.
- **BDD / Cucumber** — discovery → formulation (Gherkin `Given/When/Then`) → automation; *living
  documentation* that is "automatically checked against the system's behaviour."
  (https://cucumber.io/docs/bdd/)
- **Spec-Driven Development (SDD)** — specification as the "single, evolving source of truth," an
  "executable blueprint that AI agents use to generate and validate code"; six phases
  Constitution → Specify → Clarify → Plan → Tasks → Implement. (https://specdriven.ai/)

## 2. The reframe that makes it answerable

Hallucination tracks **proposition coverage, not documentation volume.** An agent hallucinates when a
question's answer-propositions are **absent or unretrievable** and it answers anyway instead of
abstaining. So judge each method by a single test: **does its byproduct deposit the missing
propositions (intent / requirements / use cases / test cases) in a form an agent can retrieve and
ground a citation against?** A calibrated *"not enough context — escalate to SME"* is a correct
outcome, not a failure.

## 3. Finding: the canonical Agile user story does NOT add context

Your opinion, made precise and adopted as a finding:

> `As a developer, I want to do this, because of this` — **adds no context.**

It is **syntactically** structured but **semantically empty** for grounding. The "so that / because"
clause is a *benefit rationale*, not a verifiable proposition. The bare story carries **no acceptance
criteria, no concrete example, no data condition, no link to the code or test that satisfies it.** An
agent given only user stories can restate the wish but cannot answer "what is correct behaviour
here," "what proves it," or "what is the SLA" — so it abstains (best case) or hallucinates (worst).
**Agile's documentation byproduct is therefore necessary-but-insufficient context.** This is the
crux: the problem was never "not enough documents," it was "the Agile byproduct doesn't encode
answerable propositions."

## 4. The propositions each method actually deposits

| Missing proposition | Waterfall | Agile (user story) | **BDD / Cucumber** | **Spec-Driven (SDD)** |
|---|---|---|---|---|
| **Intent / rationale** | ✅ BRD prose (stale, costly) | ⚠️ thin "so that" clause | ✅ discovery conversations + examples | ✅ Specify + Constitution |
| **Requirements** | ✅ enumerated | ❌ implied only | ✅ formulated as scenarios | ✅ spec + acceptance criteria |
| **Use cases** | ✅ use-case docs | ⚠️ one wish per story | ✅ scenarios = concrete examples | ✅ Clarify surfaces edge cases |
| **Test cases / acceptance** | ✅ test-design spec (separate, drifts) | ❌ absent | ✅✅ Gherkin **is** the test (living) | ✅ Tasks = "atomic, testable chunks" |
| **Machine-readable / AI-checkable** | ❌ prose, drifts from code | ❌ prose | ✅ executable, checked vs behaviour | ✅ executable blueprint for agents |
| **Low authoring friction (no "document more")** | ❌ heavy upfront | ✅ light but empty | ✅ written as part of building | ✅ written as part of specifying |

Reading the table: **BDD and SDD are the only two methods that deposit the missing propositions *and*
do so as a natural, machine-checkable byproduct of building the software** — i.e. without asking
humans to "document more" after the fact. Waterfall has the propositions but pays for them in stale
upfront prose; Agile has the low friction but not the propositions.

## 5. Recommendation — adopt the *discipline*, not the *paperwork*

The synthesis answers your question directly:

1. **Use the waterfall SDLC templates in this folder as a context-coverage *checklist*** — they
   enumerate *which* propositions a question class needs (BRD → intent/requirement fields;
   Traceability Matrix + Test Design → the requirement↔test edges). Schema, not deliverable.
2. **Adopt BDD/Gherkin as the capture mechanism for use cases + test cases + acceptance.** Gherkin
   is already the proposition *and* the test, machine-readable, and "checked against the system's
   behaviour" — so the requirement↔verification edges FCD always wanted come for free, and stay
   honest because they execute.
3. **Adopt SDD's spec-as-source-of-truth for intent + requirements + edge cases**, and lean on its
   Clarify phase to surface the ambiguities that otherwise hide in email. Specs are "executable
   blueprints AI agents use to generate and validate code" — the same blueprint is the agent's
   grounding context.
4. **Keep Agile as the cadence, but stop treating the user story as the documentation.** The story
   is the *intent trigger*; BDD scenarios + the spec are the *context*. AI agents fill the gap
   between them as work happens (the "document as they go" thesis), each fact landing as a
   SYNTHESIZED candidate an SME confirms.

Net: **Agile alone is insufficient; full waterfall is too costly; BDD + SDD are the adoption targets**
because their byproducts *are* the missing context, machine-readable and self-checking. Mine the
waterfall templates for the schema; capture with BDD/SDD; keep Agile's pace.

## 6. The experiment that proves it — designed to stay neutral

One DryDocs loop on **one pilot scope** (recommend one Control-M job/change). The danger is a rigged
result: pristine BDD/SDD artifacts no real team would write, compared to sloppy Agile, "proving" the
favorite. The controls below remove that bias — and explicitly model that **developers take shortcuts
regardless of method.**

### 6.1 Neutrality controls (decide all of this BEFORE running)
- **Pre-register** the hypothesis, the per-class accuracy bar, and the decision rule (§6.4) in writing
  before any condition is run. No post-hoc bar-moving.
- **Ground truth is built independently** of the conditions: the SME writes the answer key + the
  proving source *without seeing* the agent's outputs or which method supplied what.
- **Isolate one variable.** Same agent, same system prompt, same question set, same retrieval settings
  across A/B/C/D. *Only the supplied context differs.* No per-condition prompt tuning.
- **Blind, randomized grading.** Strip the condition label off each answer; shuffle order; the grader
  does not know which method produced it, nor the hypothesis.
- **Two authors, separated.** Whoever *roots for* C+D does not author the C/D artifacts. Better: the
  **agent authors all artifacts** for every condition (incl. the waterfall/Agile ones) so artifact
  quality is held constant and human bias can't sneak in.

### 6.2 Model the shortcuts (this is the neutrality you asked for)
Each method gets a **realistic** and a **shortcut** variant, so we measure the method *as practiced*,
not idealized:
- **C-full / C-cut:** Gherkin with edge-case scenarios vs only the happy-path scenario (the shortcut
  every team takes under deadline).
- **D-full / D-cut:** spec with `Clarify` edge-cases filled vs spec with `UNKNOWN`s left blank or
  guessed.
- **Confirmation quality:** add a variant where the SME **rubber-stamps** drafts vs genuinely
  confirms. Because the agent authors the docs, the real-world shortcut shifts from "dev skips it" to
  "SME approves without reading" — test that failure mode directly.

A method that **only wins when executed perfectly is a weak result.** The honest question is which
method **degrades gracefully** — i.e. when shortcut, does accuracy fall *and abstention rise* (safe),
or does *hallucination* rise (dangerous)?

### 6.3 Conditions & questions
- **Conditions:** A Agile-only · B +Waterfall · C +BDD · D +SDD — each in full and shortcut variants.
- **Question set (~30–50)** tagged by class (structural / intent / requirement / use-case /
  test-acceptance / temporal), and seeded with **unanswerable / adversarial questions** whose answer
  is genuinely absent — to catch fabrication and reward abstention.
- **Anti-guessing:** use scope-specific facts that cannot be inferred from general knowledge (e.g. the
  synthetic SLA = 02:00), so a "correct" answer must be *grounded*, not lucky.

### 6.4 Scoring & decision rule
- **Score each answer:** Coverage · Groundedness (cites a real span?) · **Calibrated-abstention** (said
  "not enough context" when it should) · **Accuracy** (correct ∧ grounded). **Hallucination =
  confident-and-wrong** — tracked separately and weighted worst.
- **Predicted result:** A≈baseline (empty on intent/use-case/test). B lifts all classes at authoring
  cost + drift risk. C lifts use-case/test sharply; D lifts intent/requirement sharply. **The decisive
  test is the shortcut variants:** C+D should *degrade into abstention, not hallucination* — that
  graceful failure, more than peak accuracy, is the real argument for adopting them.
- **Decision rule (pre-registered):** adopt, per question class, the cheapest method whose
  **shortcut** variant still clears the accuracy bar *and* keeps hallucination below threshold. Judge
  methods by their floor, not their ceiling.

## 7. Guardrails (unchanged, load-bearing here)

- Missing-context **abstention is a correct outcome** — escalate to the HITL gate, never fabricate.
  (`docs/restructure/03-hitl-sme-flow.md`)
- AI-extracted propositions are **SYNTHESIZED** until SME-confirmed; provenance span mandatory.
- Intent/requirement/SLA content is likely **Internal / Internal-Confidential** → `internal/`,
  excluded from public push; set `classification` at ingestion. (`CLAUDE.md` §3)
- New meaning edges (e.g. requirement→test `VERIFIES`, scenario→code `SPECIFIES`) go through the
  relationship vocabulary + HITL gate, `status: planned` first. (`CLAUDE.md` §6)

## 8. Next action

Approve the §6 experiment on one Control-M pilot scope, and I will (a) draft the tagged question set +
scoring rubric and (b) seed it as a `backlog.yaml` entry feeding loops L2–L6 of
`plan-incrementalContextLoop.prompt.md`. The experiment is the answer — and it doubles as a reusable
context-sufficiency regression test as the graph grows.

## §REFS
- Spec-Driven Development — https://specdriven.ai/ (spec as single source of truth; Constitution→
  Specify→Clarify→Plan→Tasks→Implement; "executable blueprint AI agents use to generate and validate code")
- BDD / Cucumber — https://cucumber.io/docs/bdd/ (discovery → formulation (Gherkin) → automation; living
  documentation "automatically checked against the system's behaviour")
- Intent source: `SDLC-Docs/extracted/FCD-Requirements.doc.txt` · Layers: `docs/restructure/00-conceptual-model.md`
