# Runbook — operate `drydocs-agents`: the ADK service behind Ask

<!-- anchor: front-matter -->
- **Module:** drydocs-agents — this runbook IS the module runbook for drydocs-agents
  (V1 coverage rule). It covers the whole operate surface: the module's own venv, the
  service, the console wiring, the read-only contract, and a smoke check per registered
  app.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-09-08**,
  authored at commit `adecd387`. Every version, command and output below was RUN on the
  **laptop** (`NewThinkpad`, `agents/.venv`, Neo4j `neo4jtest`) and is transcribed from
  what came back, not read off the source. Where a step was NOT run here, it says so and
  says why (J18: a live claim names its venue, because the two machines hold independent
  graphs and independent venvs).
- **Classification:** Internal-Public (mechanism only — every credential below is named
  and none is quoted; no graph content, no model output, no real identity)
- **Audience:** anyone asked to start, check or debug the agent service behind the
  console's **Ask** page — including the person who has just been told "Ask says failed
  to fetch" and does not yet know which of four processes is down
- **Companion:** [`agents/README.md`](../../agents/README.md) (the module's own orientation
  and app table), [`agents/graph_qa/README.md`](../../agents/graph_qa/README.md) (**the
  answer-envelope contract, and it wins on conflict** — this page is procedure, not a
  second specification), [ADR 0007](../decisions/0007-agentic-qa-architecture.md) (the
  tiering, the read-only ruling and the telemetry sinks), and
  [`docs/design/drydocs-web-console-runbook.md`](drydocs-web-console-runbook.md) (the
  console this service sits behind).

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the ADK service that answers questions on the console's Ask page —
and, more often, work out which of the four processes in that chain is actually down.

### The chain, because most of this runbook is about locating a failure in it

```
browser  ->  console (Vite / the deployed page)
             |  /api/*    -> drydocs-api        (port 8001)  -> Neo4j
             |  /agent/*  -> THIS service       (port 8000)  -> Neo4j
                                                             -> the LLM provider
```

Four processes, one page. The Ask surface can fail because any of them is down, and three
of those failures used to print the same red line. That is the reason the console has a
staged failure ladder rather than an error string, and the reason this runbook leads with
*verify* rather than *startup*.

**In scope.** The `agents/` module: its own virtualenv, the four registered ADK apps, the
service launcher, the console wiring, the read-only contract the agent's Cypher runs
under, and the smoke checks that separate "the service is up" from "the service can
answer".

**Out of scope.** Neo4j provisioning and the load chain (that is
[`drydocs-startup-refresh-runbook.md`](drydocs-startup-refresh-runbook.md) and
[`drydocs-load-runbook.md`](drydocs-load-runbook.md)); the console itself
([`drydocs-web-console-runbook.md`](drydocs-web-console-runbook.md)); `drydocs-api`
([`drydocs-api-runbook.md`](drydocs-api-runbook.md)). **The provider account and its
spend** — this runbook names the environment variables and never a value, and it does not
tell you which model to buy. And the ANSWER: whether a given reply is *correct* is not an
operational question, and nothing here grades one.

<!-- anchor: prerequisites -->
## Prerequisites

**1. The module has its OWN virtualenv, and that is a design decision rather than an
accident.** `agents/` is not part of the poetry package: it has its own interpreter so the
agent runtime can be profiled and leak-tested in isolation, and so the ADK's dependency
tree never constrains the loaders'. Two consequences bite in practice — `poetry run`
cannot start this service, and a `pip list` in the repo venv tells you nothing about it.

```powershell
cd agents
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

> **Install gotcha (Windows).** Recent `litellm` sdists want a Rust toolchain. Install
> wheels only: `.venv\Scripts\pip install --only-binary :all: litellm`.

**2. What is actually installed here.** Measured on the laptop venv, 2026-09-08 — these
are transcribed from `importlib.metadata.version`, not from `requirements.txt`:

| Package | Declared in `requirements.txt` | Measured here |
|---|---|---|
| python | — | 3.12.10 |
| `google-adk` | `>=2,<3` | **2.3.0** |
| `neo4j` | `>=6.2,<7` | 6.2.0 |
| `python-dotenv` | `>=1.2,<2` | 1.2.2 |
| `litellm` | `>=1.97,<2` | **1.91.4** |
| `pyyaml` | `>=6.0,<7` | 6.0.3 |

Two rows disagree with the declaration and both are worth knowing before you debug
anything. `litellm` is BELOW its declared floor, because the Windows install gotcha above
pins the known-good wheel; and `google-adk` 2.3.0 is what a bare resolve produces today,
which is **the version the launcher does not start on** — see *Troubleshooting*, first
entry, before you conclude your install is broken.

**3. Credentials, by NAME only.** Two files are read, `agents/.env` first and the repo
root `.env` as fallback (that precedence is G131's, and it is why a probe that reads only
one of them can report a key unset on a machine where a real turn succeeds):

| Variable | Read by | Needed for |
|---|---|---|
| `GRAPHQA_PROVIDER` | `agents/graph_qa/providers.py` | `anthropic` (local/producer) or `azure` (company) — the R1 ruling, and the adapter refuses anything else |
| `GRAPHQA_MODEL` | `agents/graph_qa/providers.py` | the model id. **No default, on purpose** — model ids live in config, never code |
| `ANTHROPIC_API_KEY` | provider adapter | the `anthropic` provider |
| `AZURE_API_KEY` / `AZURE_API_BASE` | provider adapter | the `azure` provider |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | `agents/common/neo4j_tool.py` | every app that reads the graph |
| `DRYDOCS_AGENT_REG_KEY`, `DRYDOCS_API_URL` | `agents/common/ephemeral_client.py` | registering executed Cypher as an ephemeral spec (R4) — without them an answer still works and its steps simply carry no `explore_ref` |
| `DRYDOCS_LOGDIR` | `drydocs_core.run_log` | where the telemetry lands. Optional: it keeps a default, unlike `DRYDOCS_DATA_ROOT` |

**4. Neo4j reachable from THIS interpreter.** Not from the poetry env — the agents venv
has its own driver major (6.x against the repo's 5.x). The one-line check is in *Verify*.

<!-- anchor: startup -->
## Startup

**Step 1 — start the service.**

```powershell
cd agents
.venv\Scripts\python serve.py            # defaults: --host 127.0.0.1 --port 8000
```

`serve.py` is the ruled entry point rather than `adk api_server`, and it is not a
convenience wrapper. It does two things the vendor command does not:

- **R14 app discovery.** `adk api_server` lists every non-hidden subdirectory of
  `agents/` as an app, so the shared-tools package `common/` appears beside the four real
  ones. `serve.py` hands the app factory a loader that lists a directory only when it
  holds an `agent.py`.
- **R23 control redaction.** ADK persists every part of a user message to its session
  store as given. `serve.py` wraps the session service so the control part is redacted on
  the way to disk, and it **refuses to start** if that seam is missing rather than
  serving unredacted.

*Success looks like:* uvicorn logging `Uvicorn running on http://127.0.0.1:8000`.
**If it exits with a `ModuleNotFoundError` instead, go to Troubleshooting — that is a
known break on `google-adk` 2.3.0 and not a mistake you made.**

**Step 2 — wire the console.** Nothing to set. The console reaches this service as
`/agent/*` **on its own origin**, through the same reverse proxy that serves the page —
Vite's in dev, the Compose stack's in deployment. The prefix comes from
[`web/delivery.json`](../../web/delivery.json):

```json
{ "api": { "prefix": "/api" }, "agent": { "prefix": "/agent" } }
```

> **A stale instruction you may still find:** older notes (and V9's own acceptance text)
> say to set `VITE_ADK_URL` and to start the server with
> `--allow_origins http://localhost:5173`. **Both are retired** (ADR 0020, WEB10). A
> production bundle carries no deployment coordinate at all, and because no browser
> request is cross-origin there is no allowlist to configure — a cross-origin caller is a
> deployment defect, not a case to configure for. `agents/README.md`'s Run block still
> shows the old flag; the flag is inert, not harmful.

**Step 3 — confirm the page can reach it.** Start the console and drydocs-api per
[`drydocs-web-console-runbook.md`](drydocs-web-console-runbook.md), then open Ask.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

**N/A for the service — this module ingests nothing.** It is a read path over a graph
other modules load, and it holds no state of its own that a refresh would rebuild. What
follows is the maintenance that *does* recur here, because "nothing to ingest" is not the
same as "nothing to keep current".

**The session store grows.** ADK persists sessions to `agents/graph_qa/.adk/session.db`.
It is not swept, and it is the file R13 is about; it is also where the R23 redaction
proves itself, so do not delete it to "clean up" without knowing that a redaction check
reads it.

**The telemetry files are the durable record.** In `DRYDOCS_LOGDIR`:

| File | Kind | Retention | What it is |
|---|---|---|---|
| `qa.graph_qa.<YYYYmmdd>.jsonl` | `qa` | 90 days | one line per LLM call, one per answered question. **The only place a question's full text lands** — the `:AgentRun` graph node carries sha256 + length |
| `qa-debug.graph_qa.<YYYYmmdd>.jsonl` | `qa-debug` | 7 days | the R18 decision trace. **Written only when `config/log-kinds.yaml` declares the kind at `level: DEBUG`**, which the shipped declaration does not |

Sweeping the `qa` file destroys the only record that turns a question hash back into
words. That consequence is deliberate and stated in the kind's declaration; it is not an
oversight to be tidied.

**After a graph reload,** nothing here needs regenerating — the agent reads the live
schema on every text2cypher call. What DOES change is the answer: a spec that returned
rows yesterday returns zero today if the load did not land, and the console reports that
honestly rather than hiding it. Diagnose it as a LOAD problem, in the load runbook.

<!-- anchor: verify -->
## Verify

Four checks, in the order that isolates a failure fastest — each answers a question the
one before it cannot.

**V1 — can this interpreter reach Neo4j?** (No service needed.)

```powershell
cd agents
.venv\Scripts\python -c "import sys; sys.path.insert(0,'.'); from common.neo4j_tool import graph_schema_detailed as g; s=g(); print(len(s['labels']), len(s['relationshipTypes']), len(s['propertyKeys']))"
```

Expected: three counts. Run here 2026-09-08 (laptop, `neo4jtest`): `76 35 232`. **Those
numbers are this machine's graph and are not a target** — what passes is *three numbers
instead of an exception*. A `ServiceUnavailable` or `AuthError` here is a Neo4j or `.env`
problem and no amount of agent debugging will move it.

**V2 — is the server up and serving the right apps?**

```powershell
curl http://127.0.0.1:8000/list-apps
```

Expected, exactly four names:

```json
["controlm_fix","core_ingest","graph_qa","graph_query"]
```

**A fifth entry, `common`, means R14's loader is not in effect** — you are on the vendor
path (see Troubleshooting). Harmless to answering, and a reliable signal that `serve.py`
did not start.

**V3 — can the agent reach a model?** This is the second failure, and it is a different
one from V2:

```powershell
curl http://127.0.0.1:8000/drydocs-health
```

Expected when configured: `{"configured": true, "detail": null}`. When not:
`{"configured": false, "detail": "GRAPHQA_MODEL is not set (agents/.env) — model ids live in config, never code"}`.
The `detail` names a KEY and a FILE and never a value — a probe that leaked one would be
worse than no probe. This endpoint is deliberately not `/health`: that one is ADK's own
and answers for the SERVER, which is the question V2 already asked.

**V4 — a smoke check per app.** `graph_query` is the one that needs no key and is
therefore the honest first target: it proves browser → ADK → Neo4j with nothing else in
the chain.

```powershell
# create a session, then run one turn
curl -X POST http://127.0.0.1:8000/apps/graph_query/users/u1/sessions/s1 -H "Content-Type: application/json" -d "{}"
curl -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" ^
  -d "{\"appName\":\"graph_query\",\"userId\":\"u1\",\"sessionId\":\"s1\",\"newMessage\":{\"role\":\"user\",\"parts\":[{\"text\":\"MATCH (n:BusinessApplication) RETURN count(n) AS apps\"}]},\"streaming\":false}"
```

Expected output SHAPE — run here 2026-09-08 (laptop, `neo4jtest`), transcribed from the
last event's text part:

```json
{
  "query": "MATCH (n:BusinessApplication) RETURN count(n) AS apps",
  "status": "success",
  "rowCount": 1,
  "keys": ["apps"],
  "records": [{ "apps": 4 }]
}
```

The `4` is this machine's graph. **The shape is the check**: `status`, `rowCount`, `keys`,
`records`. A `status` of anything but `success` carries the reason.

| App | Key needed | Smoke input | Expected shape |
|---|---|---|---|
| `graph_query` | no | a read-only Cypher string (empty = the default component query) | the envelope above |
| `graph_qa` | **yes** | a free-text question | the ADR 0007 answer envelope: `status`, `run_id`, `tier`, `answer`, `steps[]` with per-step Cypher, `sources[]`, `metrics` — the contract is `agents/graph_qa/README.md` and it is the authority |
| `core_ingest` | yes (Gemini, legacy demo) | free text | an LLM reply; these two are demo agents and are not on the Ask path |
| `controlm_fix` | yes (Gemini, legacy demo) | free text | an LLM reply |

**Only `graph_query` was executed here.** The other three spend a provider call, and
running someone's key to produce a runbook example is not a decision this document makes
for you. Their shapes above are the declared contracts, and `graph_qa`'s is the one under
test in the repo suite.

**V5 — the read-only contract, and why you do not have to take it on trust.** The agent's
Cypher runs in **READ access mode server-side**, so Neo4j itself rejects a write; the
string guard in the pre-flight is a fast fail, explicitly *not* the boundary (it cannot
see `CALL apoc.*` writes). Row caps and a transaction timeout apply.
`tests/integration/test_graph_qa_read_mode.py` proves it against a live database. The one
component in this module that opens a WRITE session is the `:AgentRun` telemetry writer,
which is a dedicated boundary that refuses any database but the ruled one.

<!-- anchor: rollback -->
## Rollback

**Nothing this service does needs undoing, and that is a property rather than a
convenience.** It writes no ground truth (ADR 0007 decision 2, O20). Three things it
*does* write, and what "back to known-good" means for each:

| What | Where | Reverting it |
|---|---|---|
| `:AgentRun` telemetry | the `drydocs` database, carrying `:Uncertain` | One node per answered question, MERGEd on `run_id`. Deleting them is safe and affects no ground truth; nothing reads them but the admin frame |
| Ephemeral specs (R4) | drydocs-api, session-scoped | TTL-bounded and session-owned; they expire. Restarting drydocs-api drops them |
| The session store | `agents/graph_qa/.adk/session.db` | Deleting it loses conversation history and nothing else. See the note in *Refresh* first |

**To roll the SERVICE back:** stop it. There is no drain, no queue and no half-written
state — a turn either completed and returned an envelope or it did not.

**To roll the VENV back:** delete `agents/.venv` and rebuild it from
`requirements.txt`. That is the destructive last resort and its blast radius is exactly
one directory; nothing outside `agents/` depends on it.

<!-- anchor: troubleshooting -->
## Troubleshooting

**Symptom — `serve.py` exits immediately with
`ModuleNotFoundError: No module named 'google.adk.cli.utils._nested_agent_loader'`.**

*Diagnosis.* Measured on this laptop, 2026-09-08, `google-adk` **2.3.0**: that module is
gone. `google.adk.cli.utils.agent_loader` now offers `AgentLoader` and `BaseAgentLoader`
only, and the nested loader R14 uses to hide `common/` is not among them. The declaration
is `google-adk>=2,<3`, so a fresh resolve lands on 2.3.0 and the launcher does not start.
The R23 redaction seam is a separate question and is **fine** — `fast_api.create_session_service_from_options`
is still present at 2.3.0, so this is an app-discovery break and not a redaction break.

*Fix.* Not one this runbook can hand you: re-pointing R14 at whatever 2.3.0 offers is a
code change with a design question inside it, and it is filed as a handback on V9. What
you can do meanwhile is start the server on the vendor loader, accepting the cosmetic
regression:

```powershell
cd agents
.venv\Scripts\python -c "import sys; sys.path.insert(0,'.'); import uvicorn; from google.adk.cli.fast_api import get_fast_api_app; from google.adk.cli.utils.agent_loader import AgentLoader; uvicorn.run(get_fast_api_app(agents_dir='.', agent_loader=AgentLoader('.'), web=False, host='127.0.0.1', port=8000), host='127.0.0.1', port=8000)"
```

`/list-apps` then answers `["common","controlm_fix","core_ingest","graph_qa","graph_query"]`
— verified here, and `common` in that list is precisely the defect R14 exists to prevent.
**This workaround also skips the R23 redaction**, so do not run it against a console
session whose token you care about.

**Symptom — Ask says "Failed to fetch" and the console is otherwise green.**

*Diagnosis.* This is the incident the console's failure ladder was built for: everything
looked green because the fourth process was never started. Do not read the red line —
read the ladder underneath it, which probes the services and then reinterprets the
original error against what it found.

*Fix.* Work V2 then V3. The two states the ladder separates are "the agent server is not
running" and "the agent server is running and cannot reach a model", and they have
different fixes.

> **What the console does NOT do, corrected here because V9's own acceptance says
> otherwise.** The acceptance (written 2026-07-29) describes an ADK-unreachable fallback
> as a "SYNTHESIZED demo trace + banner". **That is not the behaviour today.** An
> unreachable agent renders the O63 **failure ladder**; there is no demo trace and no
> fallback answer. The SYNTHESIZED banner is a real surface but a different one — it
> fires when an ANSWER's sources are watermarked, and says so about the data rather than
> about the transport. Read as of commit `adecd387`; the acceptance predates O63.

**Symptom — an answer arrives but every step's `explore_ref` is null.**

*Diagnosis.* The R4 registration surface is not configured — `DRYDOCS_AGENT_REG_KEY` or
`DRYDOCS_API_URL` is unset, or drydocs-api is down. This is honest degradation by design:
a registration failure never kills an answer.

*Fix.* Set both, and confirm drydocs-api answers. Open-in-Explorer and Export need them;
the answer does not.

**Symptom — `ProviderConfigError: GRAPHQA_MODEL is not set (agents/.env)` on a machine
where the file plainly sets it.**

*Diagnosis.* Import order. `providers.py` merges only the repo-root `.env` at import;
`agents/.env` is merged by `common/neo4j_tool` at ITS import. Anything that reaches the
provider without going through the agent's own import path reads a half-loaded
environment. `serve.py`'s probe imports `common.neo4j_tool` first for exactly this
reason.

*Fix.* If it is your own script, import `common.neo4j_tool` before `graph_qa.providers`.
If it is the probe, it already does.

**Symptom — the answer says a document is not ingested when you can see it in the graph.**

*Diagnosis.* A routing problem, not a load problem, and R18's evidence is three live runs
of exactly this: two of them read the same subject as an operational question and
generated a valid traversal against the wrong domain, while a third routed correctly and
found the document. Nothing in the ordinary telemetry says WHY.

*Fix.* Turn on the decision trace — declare `qa-debug` at `level: DEBUG` in
`config/log-kinds.yaml`, restart the service (enablement is read once at import, and is
settings-level on purpose: an HTTP request has no `--verbose`), reproduce, then read
`qa-debug.graph_qa.<day>.jsonl` or fetch it by run id from `/admin/qa-trace`. It records
the router's candidates and its stated reason, the schema prompt, every generated Cypher
and its fix attempts. Turn it back off afterwards: it carries prompt text at 7-day
retention.

<!-- anchor: contacts-escalation -->
## Contacts & escalation

**Owner.** The DryDocs producer session that holds the `code:drydocs-agents` pen. The
module has no separate on-call.

**Decide-vs-escalate, the line that matters here.** Everything in this runbook is
operational and reversible. What is NOT this runbook's to decide:

- **Anything that changes what an edge MEANS.** The agent reads the ontology vocabulary
  and never extends it. A new relationship type goes through
  [`docs/RELATIONSHIP_GUIDE.md`](../RELATIONSHIP_GUIDE.md) and the HITL gate
  ([`docs/restructure/03-hitl-sme-flow.md`](../restructure/03-hitl-sme-flow.md)) as
  `status: planned` first.
- **Binding a console term to a graph concept.** If a question makes you want to declare
  that Tower *is* some label, that is the gate's ruling and not a fix.
- **The provider and the model id.** The R1 gate ruled environment-split providers
  (local/producer anthropic, company azure). Changing that is an ADR 0007 amendment.
- **Turning the debug trace on in a shared deployment.** It captures prompt text. The
  retention is short by design; the decision to capture at all is the operator's to make
  deliberately.

**Escalation route.** A defect goes to the backlog
([`docs/restructure/backlog/items/`](../restructure/backlog/)) as an item naming its
module; anything ambiguous goes to the HITL gate rather than being auto-decided. A
gate-bound question never ships from a runbook.

<!-- anchor: appendices -->
## Appendices

### A — the four apps, and the convention that makes them apps

One directory = one ADK app, and **a directory is an app exactly when it holds an
`agent.py`**. `common/` has none and is therefore a shared package rather than an app —
which is the whole of R14, and the reason `/list-apps` returning five names is a signal
rather than a curiosity.

### B — what a `graph_qa` answer carries

Not restated here on purpose. The envelope is specified in
[`agents/graph_qa/README.md`](../../agents/graph_qa/README.md) and a second copy would
drift from it. What an operator needs from it is three fields: `tier` (which tier
answered), `steps[].cypher` (what actually ran), and `metrics.response_ms` (where the time
went).

### C — the three telemetry sinks, and which question each answers

| Sink | Answers |
|---|---|
| `qa` JSONL ledger | what did this run cost, and what were the words of the question |
| `:AgentRun` node | how does this run compare to the others, queryable next to load telemetry |
| `qa-debug` trace (off by default) | **why** did the router choose what it chose |

The third exists because the first two cannot answer it: the router's reply was reduced to
a spec id and discarded, so there was nothing to read.
