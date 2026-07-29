# SME Runbook — Agent Test (standalone page)

> 2026-07-29 · companion to `UI-WIP/sme-ui-launch-guide.md`. How to run a live
> agent test and read every panel. Surface ruled by SME gate sign-off 2026-07-29
> (`config/gate-log.md`): standalone, dark-only, **no auth**, read-only (O20).
> Page: `web/public/agent-test.html` — ships verbatim inside `web/dist`.

## 1 · Launch

**Producer (local):**

```powershell
# terminal 1 — the ADK api_server (agents live in agents/)
adk api_server                        # default http://localhost:8000

# terminal 2 — any http server for the page (vite dev is fine)
cd C:\coding\projects\DryDocs\web
npm run dev                           # → http://localhost:5173/agent-test.html
```

**Company port:** open `https://<your-host>/agent-test.html` from the deployed
`web/dist` and type the company ADK endpoint into the **ADK URL** field — that
input is the whole binding; no code edits, no env vars.

Direct `file://` opening renders the page but the ADK fetch may hit CORS —
serve over http for live runs.

## 2 · Run a test

Pick a **Module** (only the non-deterministic, agent-interpreted modules are
listed — Explorer `graph-qa`, Docs `docmeta-qa`; the QuerySpec modules have
nothing to interpret), type your request in **SME request**, hit **Run** (or
Enter). Green `LIVE — ADK run` tag = a real run. Yellow banner +
`EXAMPLE DATA · SYNTHESIZED` = the ADK URL didn't answer and you are looking at
the canned demo shape — nothing on a SYNTHESIZED trace is evidence.

## 3 · Reading the six panels

| Panel | What it is | What to judge |
|---|---|---|
| 1 · Interpretation | the agent's first text event | did it read your intent right (route, entities, direction, depth)? |
| 2 · Cypher | first ` ```cypher ``` ` block found in the event stream | is the query the right shape — labels/edges per the confirmed vocabulary? |
| 3 · Return path | the agent/author chain the events walked | did it take the route the interpretation promised? |
| 4 · Agent timeline | per-stage rows: thinking, tool calls, texts + tokens | see below — this is the context-memory view |
| 5 · Answer | final event text | correct, cited, non-hallucinated? |
| 6 · Metrics | chars in/out, events, latency, ctx @ final, think tok | cost + speed at a glance |

## 4 · The timeline — thinking and context memory per stage

Each row is one step of the run:

- **kind = thought** (yellow, italic) — the model's reasoning text. Rows appear
  ONLY when the agent runs with thinking exposed (`include_thoughts` in the
  agent's planner/model config) on a thinking-capable model.
- **kind = tool** (teal) — a function call/response step (no model tokens).
- **ctx in (tok)** — `usageMetadata.promptTokenCount` for that model call: the
  **size of the context window at that stage**. Watch it grow row to row — that
  growth IS the context-memory story (the 27.4× token-efficiency claim from
  Under the Hood is exactly about keeping this small).
- **out / think (tok)** — output tokens and `thoughtsTokenCount` for the call.
- **context growth bar** — ctx-in relative to the run's largest call; a bar
  that jumps sharply is a stage stuffing the window (usually a fat tool result).

If the agent doesn't report `usageMetadata`, the token columns show `—` and the
note under the table says so — that's a fact about the agent config, not the
page. Fix in the agent (usage reporting on; thinking budget/include_thoughts
for thought rows), not here.

## 5 · What to look for (SME judgment calls)

- Interpretation names the wrong edge or direction → **vocabulary problem** —
  route to the HITL gate, never accept a creative edge name from a demo.
- Cypher right but rows wrong → data/load question (Loads view, `:JobRun`s).
- ctx-in ballooning after a tool step → the tool returns too much; note the
  stage number in your feedback.
- Thinking that contradicts the answer → capture verbatim; that's a routing/
  synthesis defect worth a line on its own.

## 6 · Recording feedback

Same loop as everything else: cite what you saw with its anchor — panel number
+ stage row ("timeline row 4: ctx jumped 812→2,140 on run_readonly_cypher") —
into `docs/restructure/IDEAS.md`, tagged FB-. Meaning-level findings (edge
semantics, vocabulary) go through `docs/restructure/03-hitl-sme-flow.md`.

## 7 · Troubleshooting

- **Banner: ADK unreachable** — check the URL field first (company host?
  port?); then whether `adk api_server` is up; then CORS (serve the page over
  http, not file://).
- **Apps list empty** ("ADK reachable but no apps registered") — the api_server
  started outside the agents directory; start it where the agent apps live.
- **No thought rows on a live run** — thinking isn't enabled for that agent, or
  the model doesn't expose thoughts. Expected, not a bug.
- **Token columns all —** — agent isn't returning `usageMetadata`; see §4.
- **Page renders but looks unstyled-ish** — you're in a very old browser; the
  page needs CSS variables + fetch (any evergreen browser is fine).
