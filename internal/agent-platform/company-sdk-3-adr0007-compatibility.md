# SmartSDK 3.0 release notes vs ADR 0007 / Epic R — compatibility review

**Classification: Internal** — names the internal SDK, its package, feature names,
and install channel. Never crosses the publish boundary; the public-side record is
the target-state IDEAS entry (2026-07-28), which cites this file by path only.

**Reviewed:** 2026-07-28, from the Agent Builder Team release notes for
`cdaosmart-sdk` v3.0.0 ("SmartSDK 3.0 — a fundamental evolution of the platform
built on top of Google ADK 2.0"). Source: internal release-notes markdown
(`SmartSDK-Python-3.md`, untracked working file; docs at `go/smartsdk`).
**Verdict: COMPATIBLE — ADR 0007's revisit-if trigger ("company Fusion SmartSDK
diverges from OSS ADK in a way that breaks the app shape") fired and PASSED.**
SmartSDK 3.0 *converges* on OSS ADK rather than diverging.

## Release-notes digest (what matters to DryDocs)

Breaking changes:
- **Local Skills** — restructured to align with ADK's native skill API; loaded
  from directories via `load_skill_from_dir()` into a `SkillToolset` (replaces
  the 2.x skills approach).
- **Retry Logic** — automatic retries via `RetryConfig(max_attempts=...)` at the
  node/workflow level; tool exceptions trigger the retry mechanism.
- **Runner Semantics** — aligned closer to Google ADK: Runner takes the App and
  Agent at construction; `run_async()` takes `user_id`, `session_id`,
  `new_message` per call.
- **Graph (deprecated)** — SMARTGraph / SMARTNode / `smart_sdk.graph` deprecated
  (DeprecationWarning on import; removal planned). New code uses Workflow with
  Edge / FunctionNode / JoinNode.
- **Teams (removed)** — `smart_sdk.teams` root re-exports gone; SelectorTeam only
  as a deep import; Workflow is the multi-agent orchestration surface.
- **Adapters (removed)** — SmartSDK agents now subclass ADK agents directly via
  multiple inheritance instead of composition wrapping;
  `isinstance(smart_agent, google.adk.agents.LlmAgent)` is now True.
- **A2AServer requires IDAConfig** — all A2A servers must be authenticated
  (`ida_config` is a required parameter on `A2AServer.run()`).

New features: **Workflow** (ADK 2.0 graph-native: conditional routing, parallel
fan-out/fan-in, `RetryConfig`/`NodeTimeoutError`, human-in-the-loop via
`RequestInput`, nested composition — replaces shell agents); **A2UI** (agents
emit declarative UI components rendered natively by clients, no arbitrary code);
**OpenAI V1 API** (`use_v1_api=True` on the Model class routes Azure OpenAI
through the OpenAI-compatible V1 endpoint `{azure_endpoint}/openai/v1`);
**MCP Inject Args** (`InjectedArgsMcpTool` pins a subset of args — api_key,
tenant_id — at construction; stripped from the declaration the LLM sees);
**Guardrail Plugin** (runtime screening of LLM inputs/outputs via an external
guardrails gateway backed by purpose-built SLMs; registered once on the runner,
applies to every call); **A2A Proxy** (reverse proxy fronting multiple external
A2A agents under one Starlette app — IDA-protected ingress, per-upstream auth,
egress secret inspection, OTel trace propagation, feature flags); **Harness
Agent** (PRIVATE PREVIEW — long-running agent composing planner, evaluator,
error recovery, policy gateway, budget tracker, context manager, cognitive
memory, workspace backend; LOB assumes full responsibility in production);
**Voice Agents** (experimental; Nova Sonic / AWS Bedrock; Python >= 3.12).

Install: `uv pip install cdaosmart-sdk==3.0.0` from the internal Artifactory
PyPI index. Extras: a2a, a2ui, ag-ui, db, evals, harness, kerberos, memory,
sandbox, smartllm, tracing, voice-bedrock.

## Compatibility mapping against the plan

| Plan element | SmartSDK 3.0 fact | Verdict |
|---|---|---|
| ADR 0007 app shape: `graph_qa` as an OSS-ADK app in `agents/`, subclassing `BaseAgent`/`LlmAgent` with `_run_async_impl` | 3.0 agents subclass `google.adk` agents directly; `isinstance(..., LlmAgent)` True; the 2.x composition/adapter layer is gone | **Compatible — strengthened.** Producer agent ports company-side without wrapping. Under 2.x it would have needed the adapter layer. |
| ADR 0007 revisit-if: "company SDK diverges from OSS ADK" | 3.0 is "generally aligned closer to Google ADK" across skills, runner, orchestration | **Trigger fired, PASSED** — convergence, not divergence. Date-stamp owed in the ADR (inboxed). |
| R1 ruling: env-split providers — company runtime = Azure OpenAI | `use_v1_api=True` routes Azure OpenAI through the OpenAI-compatible V1 endpoint, first-class | **Compatible.** Company binding = the Model flag rather than LiteLLM; `agents/graph_qa/providers.py::extract_usage` already normalizes the openai token shape. |
| R6: Tier-2 bounded enhance/solve loop (iterations/vote/budget caps, forced-solve) | ADK 2.0 Workflow: Edge/FunctionNode/JoinNode, conditional routing, fan-out/fan-in, RetryConfig, NodeTimeoutError, RequestInput HITL, nested composition | **Compatible — build R6 ON Workflow primitives.** Never SMARTGraph (deprecated), Teams (removed), or a bespoke controller loop. |
| Gate discipline in agent flows | `RequestInput` human-in-the-loop node | **Native hook** for any SME-confirmation step (e.g., a future mapping-act flow). |
| R9: read-only agent query CLI; MCP = later option (config + write-risk concerns) | `InjectedArgsMcpTool` pins sensitive args at construction and strips them from the LLM's view | **CLI-first unchanged; the MCP-later option matured.** A CLI tool wraps trivially as an ADK function tool either way. |
| Server-side READ enforcement is THE security boundary (ADR 0007 §2) | Guardrail Plugin (global, runner-level) + A2A auth | **Complementary layers, no replacement.** Agent-side guardrails never substitute for READ access mode. |
| R3: per-LLM-call ledger + `:AgentRun` envelope | OTel trace propagation (A2A Proxy), `tracing` extra; `run_async` now takes explicit `user_id` | **Compatible.** Follow-up: envelope reserves a hashed caller-identity slot (hash like the question text — full identity never lands in the graph). |
| R5 Ask spoke (custom React panel, Cypher exposure via explore_ref) | A2UI declarative components | **No conflict.** A2UI can't obviously carry the Cypher-exposure/explore_ref contract; R5 stays a console spoke. A2UI/A2A exposure of graph_qa = company Track-2 / DD-series, with IDAConfig auth now mandatory (good). |
| Tier-2 self-built vs platform | Harness Agent = the same shape (planner/budget/memory), but PRIVATE PREVIEW, LOB-owns-risk | **Do not take a dependency.** R6 stays self-built and bounded; Harness is convergent validation only. |
| Python floor | Only the voice extra needs >= 3.12 | No action (repo is ^3.11; voice not planned). |
| `agents/requirements.txt` | `google-adk` UNPINNED while ADK 2.0 breaking changes land upstream | **Risk — follow-up inboxed:** pin `>=2,<3`. |

## Follow-ups (inboxed 2026-07-28, public-side in target-state wording)

1. [chore] Pin `google-adk` (`>=2,<3`) in `agents/requirements.txt`.
2. [idea] R3 `:AgentRun` envelope reserves a hashed caller-identity slot.
3. [doc] Date-stamp the passed revisit check in ADR 0007's Revisit-if section.

If this SDK's next major diverges from OSS ADK (or Harness leaves private
preview with a governance story), re-run this review — the ADR's revisit clause
stays live.
