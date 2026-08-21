# The two cautionary tales in context-graph — expanded

> Companion to [`ui-architecture-analysis.md`](ui-architecture-analysis.md) (2026-07-23).
> That doc's verdict included one compressed line — *"their dual-ingestion and docs drift
> are the cautionary tales"* — this note unpacks it. Internal (derived from company
> material); never in a public mirror.

These two are worth a standalone write-up because they are the only findings in the
analysis that are about **engineering discipline rather than features** — and because
DryDocs, as a one-person project moving fast toward a prod decision, is exposed to both
failure modes in miniature. context-graph is a *good* system built by a resourced team;
these diseases still got in. That is the warning.

---

## Tale 1 — Dual ingestion: two implementations of the same job, one real

### What they actually have

context-graph carries **two complete ingestion implementations side by side**:

| | Python path | Java "connector framework" |
|---|---|---|
| Where | `scripts/` (~130 scripts, `discover.py` 7-step orchestrator) | `context-graph-connectors/` (13 connector modules) |
| Invoked by | `Jenkinsfile.pipeline`, daily 02:00 UTC — **the production data path** | only `POST /api/v1/sync/*` — **no cron or schedule invokes it in prod** |
| Design maturity | pragmatic scripts, idempotent MERGE on business keys | *more* formal: `GraphConnector` interface, `syncIncremental(SyncState)`, checkpoint state, `GraphMutation` batch upsert, `ConnectorScheduler`, retry/backoff |
| Edge vocabulary | `HAS_AREA_PRODUCT, HAS_TEAM, OWNED_BY, CONTAINS_REPO, IMPLEMENTS, DECIDES, EXPOSES…` | a **different, more formal** vocabulary: `DEPENDS_ON, BELONGS_TO, GROUPED_IN, IMPLEMENTS, DECIDES…` |

And the pattern repeats at two more layers:

- **Graph backend:** Neo4j is live; **TigerGraph adapters are scaffolded on BOTH sides**
  (Java `GRAPH_PROVIDER`, Python `GRAPH_BACKEND` factory) — stubs only. The root
  `pom.xml` *description* even calls the system "TigerGraph-backed." Aspirational, not
  actual.
- **MCP server:** an in-repo prototype (`mcp_server/`, flat 12 tools, hardcoded
  localhost creds) AND the standalone production repo (`context-graph-mcp`, dual-mode
  transport, OIDC C2C, circuit breaker, audit logging). Same 12 tool names on both.
  Their own Session-3 analysis had to spend a section on "reconciling the two MCP
  servers" — i.e., even *they* need documentation to answer "which one is real."

### Why this is a disease and not just untidiness

1. **The better-designed path is the dead one.** The connector framework is the more
   engineered artifact — interfaces, checkpoints, scheduling — and it is exactly the
   part that doesn't run. Design effort went where production truth isn't. Anyone
   assessing the system by reading code quality would rank the paths backwards.
2. **Two vocabularies, one graph.** The Java and Python sides disagree on edge names
   for the same relationships. If the refactor path ever *were* switched on, it would
   write a second dialect into the same database. Until then, every consumer (human,
   query, agent) must know which vocabulary is real.
3. **"Which is real" tax on everyone forever.** New teammate, auditor, LLM agent, or —
   concretely — us doing this analysis: everyone pays a discovery cost that a
   single-path system never charges. The 12-tool MCP duplication is the worst case:
   identical names, different auth, different resilience, one of them insecure-by-
   default (hardcoded creds).
4. **Optionality rots.** The TigerGraph stubs and the connector framework are "kept
   just in case." Unexercised code drifts from the schema, the deps, and the truth —
   the option's value silently goes to zero while its confusion cost stays.

### The root cause, honestly stated

This isn't incompetence — it's a **refactor aspiration built alongside production
without a kill-or-migrate decision**. The team wrote the future (connector framework,
pluggable backends) next to the present (Python scripts) and never scheduled the
verdict. Both survived. A resourced team can carry that; it still cost them coherence.

### DryDocs exposure — where we could catch the same disease

- **Fixture vs live data in the web console** is a sanctioned dual path. It is safe
  *only because* of the discipline attached: fixtures always render with a visible
  SYNTHESIZED/notice banner, and fallback triggers are explicit (API absent / 0 rows).
  The moment a fixture renders unbannered, we have their disease.
- **`benchmarkData.ts` is hand-carried** from the P0 verdict — a second copy of truth.
  Tracked as **O31** (regenerate from the docmeta eval harness when it lands). That is
  the correct pattern: a known duplication with a named sunset.
- **drydocs-api today vs the ADK agent layer later** (site-plan §4): one is the read
  path, the other is a future addition. Keep the site-plan's explicit ruling ("ADK is
  a LATER, separate addition, not the read path") — that sentence is exactly the
  kill-or-migrate decision context-graph never wrote down.
- **Rule of thumb to keep:** every parallel implementation must carry (a) a named
  owner-decision ("X is production, Y is spike"), (b) a banner/label at the surface,
  and (c) a backlog item that either promotes or deletes it. No third state.

---

## Tale 2 — Docs drift: the README describes a system that doesn't exist

### What they actually have

Verified discrepancies between context-graph's own documentation and its code:

| Doc claim | Source-of-truth reality |
|---|---|
| README: **Java 25** | root `pom.xml` pins **Java 21** |
| README: **"9 MCP tools"** | 12 tools registered (verified inventory) |
| README references `ui/api.py` dev server | removed in CCBETPINC-152; replaced by Vite proxy + Spring `UiApiController` |
| `pom.xml` description: "TigerGraph-backed" | Neo4j is the only live backend; TigerGraph is stubs |

Their own deep-analysis sessions had to adopt a standing rule: *"Treat docs as
aspirational; verify against source."* Read that sentence again — it means **their
documentation has negative value for factual questions**: it costs verification effort
AND plants wrong priors.

### Why this compounds worse than it looks

1. **Docs that are wrong once are distrusted everywhere.** After the first Java-25
   claim fails verification, a careful reader re-derives *everything* from source —
   the docs stop saving anyone time, which was their only job.
2. **Agents amplify it.** An LLM agent handed that README will confidently repeat
   "Java 25, 9 tools, TigerGraph-backed." Docs drift becomes hallucination-by-
   ingestion — the exact failure mode our own benchmark's OS1 question demonstrates
   (confident noise beats honest absence). A knowledge-graph product whose own docs
   poison agents is self-refuting.
3. **Drift is directional.** Notice the pattern: every drifted claim describes the
   *intended* system (newer Java, the TigerGraph future, the tool count of some
   earlier plan). Aspiration written in the indicative mood. Nobody decides to lie;
   the plan just gets written as fact and never demoted when reality diverges.

### DryDocs' structural defenses — and the gaps

We are unusually well-defended, mostly because the repo treats derived facts as
*renders*, not prose:

- **Generated artifacts with drift tests**: `enforcement-matrix.json`, `gates.json`,
  the board, the design-doc HTML renders — all deterministic renders of a source of
  truth, all guarded (`test_enforcement_matrix.py`, `test_gates_json.py`, stale-render
  check in the session ritual). A README can't drift about what a test regenerates.
- **Trust tiers apply to our own prose**: VERBATIM / GROUNDED / SYNTHESIZED is exactly
  the "indicative vs aspirational" distinction their README lacks. SYNTHESIZED chunks
  are *labeled* inference — the graph enforces the demotion their docs never got.
- **Gate/ADR discipline**: status fields (`planned/proposed/confirmed/active`) mean an
  intention has a place to live *without being stated as fact*.

Where we've already shown the same symptom, small-scale:

- **`docs/design/ui-exploration/site-plan.md` phasing went stale** — the console inventory (2026-07-23)
  found the plan's P0–P3 checklist describes work as future that is entirely built.
  Harmless today; it's the identical mechanism (plan written as roadmap, reality moved,
  doc didn't). Groomed follow-ups now live in the backlog, but the plan file itself
  still reads as if the console were unbuilt.
- **Env toggle + global search in the console** look functional but are cosmetic
  placeholders. In-UI honesty exists (mock-auth banner); keep the rule that anything
  non-functional must say so *at the surface*, not in a doc nobody reads.
- **Rule of thumb to keep:** any factual claim that CAN be derived (versions, counts,
  route lists, tool inventories) must be generated or test-pinned, never hand-written;
  any claim that can't be derived must carry its tier (GROUNDED vs SYNTHESIZED) —
  including in READMEs and whitepapers.

---

## The one-sentence versions, for reuse

- **Dual ingestion:** *If two implementations of the same job coexist, the better-
  documented one will be believed and the other one will be running — schedule the
  kill-or-migrate decision the day the second one is born.*
- **Docs drift:** *Prose describing derivable facts is a cache with no invalidation —
  generate it, test-pin it, or label it aspirational; otherwise your own docs become
  the first hallucination your agents ingest.*
