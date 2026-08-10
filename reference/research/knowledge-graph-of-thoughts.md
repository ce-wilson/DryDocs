# Knowledge Graph of Thoughts (KGoT) — the reference architecture behind the agent tier

**Classification:** External (public research + public source; cite the links, do not vendor the code)
**Researched:** 2026-07-23 · **Registered:** 2026-08-10 (backlog L28)
**Trigger:** the console needed to answer free-text questions. Two reference architectures were
compared side by side and neither was adopted wholesale — the result is
[ADR 0007](../../docs/decisions/0007-agentic-qa-architecture.md), ACCEPTED at the R1 gate
2026-07-23.

This note exists because KGoT was already **load-bearing and uncited**: the ADR analyzes it by
name, four `agents/` modules carry its design or name its traps in their docstrings, and nothing
pointed at a paper, a repo, or a license. Companion to the
[NeoCarta](README.md#neocarta--context-for-the-data-catalog-layer) and
[Unity Catalog](databricks-unity-catalog.md) notes — same verdict shape as both: a **pattern to
borrow from, not a standard to seed**.

---

## Citation

> Besta, Maciej; Paleari, Lorenzo; Jiang, Jia Hao Andrea; Gerstenberger, Robert; Wu, You;
> Hannesson, Jón Gunnar; Iff, Patrick; Kubicek, Ales; Nyczyk, Piotr; Khimey, Diana; Blach, Nils;
> Zhang, Haiqiang; Zhang, Tao; Ma, Peiran; Kwaśniewski, Grzegorz; Copik, Marcin;
> Niewiadomski, Hubert; Hoefler, Torsten.
> **"Affordable AI Assistants with Knowledge Graph of Thoughts."** 2025.
> arXiv:2504.02670 · doi:10.48550/arXiv.2504.02670

| | |
|---|---|
| **Paper** | https://arxiv.org/abs/2504.02670 |
| **Source** | https://github.com/spcl/knowledge-graph-of-thoughts |
| **Lab** | SPCL (Scalable Parallel Computing Lab), ETH Zurich |
| **License** | **BSD 3-Clause**, © 2025 ETH Zurich — the repo additionally carries code from Microsoft AutoGen (MIT), OpenAI simple-evals (MIT), and Hugging Face's Beating GAIA with Transformers Agents (Apache-2.0) |
| **Verified** | 2026-08-10 — citation, arXiv id and license read from the repo |

**No KGoT code is vendored into DryDocs.** What crossed over is design, restated in our own
modules; the BSD notice is recorded here because the debt is real and should be visible even
though no file carries their copyright.

---

## What it is

An iterative controller that builds a **task-scoped knowledge graph per question** — a throwaway
graph that *is* the agent's working memory, rather than a persistent graph the agent reads. Its
loop alternates two branches decided by majority vote: **INSERT** (run tools, let the LLM write
Cypher into the task graph) and **RETRIEVE** (query the task graph and parse an answer). Around
that sit a fix-Cypher repair loop on every execution failure, forced-solve fallbacks when the loop
stalls, and a per-LLM-call JSONL cost ledger recording function, model, prompt/completion tokens,
cost, and duration.

The paper's claim is economic, not merely architectural: a small, cheap model driving a structured
task graph beats a large model reasoning in flat text, at a fraction of the cost. That is the same
bet DryDocs makes at a different altitude — structure the context, then a modest model suffices.

## What DryDocs adopted

| KGoT mechanism | Where it landed here |
|---|---|
| The task-scoped graph as agent working memory (NetworkX shape) | `agents/graph_qa/task_graph.py` — closed node vocabulary (`question · subquestion · evidence · answer`), snapshots emitted in the shape the console's d3 pane already lays out |
| Per-LLM-call cost ledger (`collect_stats`) | `agents/common/llm_ledger.py` — one JSONL line per call in `DRYDOCS_LOGDIR`, plus a run-summary line; owns the model→price map and returns `None` rather than a guessed cost for an unpriced model |
| Bounded escalation *into* an iterative loop | ADR 0007 Tier 2 — reached only when Tier-1 context is insufficient |
| Fix-Cypher repair loop | Tiers 1 and 2, capped at ≤2 retries |
| Majority voting on the branch decision | Tier 2, vote ×3 |
| Forced-solve fallback | Tier 2, so a stalled loop still returns something inspectable |
| Per-iteration snapshots | rendered by the console's `TaskGraphPane` |

## What DryDocs rejected, and why

Both rejections are structural — they follow from standing rulings, not from taste.

1. **The INSERT branch collides head-on with the O20 zero-write ruling.** KGoT's loop assumes a
   graph it may freely write. DryDocs' graph is persistent ground truth and the UI path performs
   **no** graph writes; agent queries execute in READ access mode, enforced server-side.
2. **Whole-graph-state injection does not survive contact with a persistent KG.** KGoT injects the
   entire graph state into every prompt — workable on a task graph of a few dozen nodes, impossible
   against ours. `agents/graph_qa/schema_context.py` is the replacement: three bounded ingredients
   (the ACTIVE `relationship_vocabulary.yaml` rows, live `graph_schema()` output, a few registered
   QuerySpec cyphers as few-shot), every one of them character-capped so prompt cost per call is
   fixed and predictable.
3. **Unbounded cost and latency.** Dozens of LLM calls and minutes per question is not a console
   interaction. Hence tiering: most questions terminate at Tier 0 (a registered QuerySpec) or
   Tier 1 (schema-grounded text2cypher) in seconds, and the ledger exists so the caps get tuned
   from measured cost rather than guessed.

**Two traps named in our source, so they are not re-imported by a later contributor:**

- *Hardcoded model ids.* KGoT pins a tool model in code. `agents/graph_qa/providers.py` takes model
  ids and endpoints **only** from env/config — the R1 environment-split ruling (local Anthropic /
  company Azure OpenAI) is enforced by having one adapter and no literals.
- *Inject-everything prompting.* Recorded verbatim in `schema_context.py`'s docstring, next to the
  bounded alternative — the docstring is the control, and the caps are the mechanism.

## The layer-4 result

The most consequential borrowing is conceptual. CLAUDE.md §1 names the **context graph** ("what
matters right now for this task") as layer 4 and leaves it future. KGoT's task graph is exactly
that object, which is why its **residency had to be ruled rather than improvised**: R1 gate ruling
A (2026-07-23) fixed it as **in-process only** — it dies with the run, UI snapshots are ephemeral,
persistence to `ddcontext` was considered and **deferred**, and proposing it again is a new gate.
`tests/unit/test_tier2.py` reads `task_graph.py`'s source and fails if a driver, a session, a
database name, or Cypher ever appears in it. A module with nothing to persist with is the control;
a comment saying "do not persist this" is not.

## Takeaways

1. **Structure the context and a cheaper model suffices.** The paper's economic result is the one
   to keep. Our tiering is the same argument applied to a persistent graph: deterministic where
   possible, reasoning only where needed.
2. **An ephemeral-graph design does not port to a persistent-graph estate unchanged.** Every KGoT
   mechanism that assumes disposability — free writes, whole-state prompts — had to be dropped or
   bounded. That is the reusable lesson for the next agent architecture surveyed here.
3. **Cost telemetry belongs in the design, not bolted on after.** `collect_stats` is a small idea
   with outsized value: without a per-call ledger there is no evidence base for tuning caps, and
   the caps are what keep Tier 2 affordable.
4. **Cite the traps, not only the patterns.** Half of what this repo took from KGoT is a record of
   what not to do. Those belong in the source that would otherwise re-commit them.

## Sources

Links verified 2026-08-10.

| Topic | Link |
|---|---|
| Paper — *Affordable AI Assistants with Knowledge Graph of Thoughts* | https://arxiv.org/abs/2504.02670 |
| Implementation (BSD 3-Clause, ETH Zurich) | https://github.com/spcl/knowledge-graph-of-thoughts |
| The sibling architecture compared against it | https://github.com/neo4j-labs/llm-graph-builder |
| The decision it fed | [`docs/decisions/0007-agentic-qa-architecture.md`](../../docs/decisions/0007-agentic-qa-architecture.md) |
