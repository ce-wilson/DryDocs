# IDEAS — the idea board (inbox)

Low-friction capture. Jot anything here from any surface — a "what if", a bug you spotted,
a doc that needs writing, a future source to ingest. **No schema required.** Messy is fine.

This is the **inbox**, not the backlog. Nothing here is committed to until it is *groomed*
into [`backlog.yaml`](backlog.yaml) with an id, owner agent, inputs, and an acceptance test.

## How this feeds the backlog

```
capture here (any surface)  ──groom──▶  backlog.yaml item  ──▶  agent pulls it
```

**Grooming ritual** (you, or an Opus `main` session, ~weekly): read this list top to bottom;
for each idea either (a) promote it to a `backlog.yaml` item, (b) merge it into an existing
item, or (c) drop it. Strike through or delete what's been groomed so the inbox stays short.

## Capture format (loose)

`- [tag] one line. (optional: why / where you saw it)`

Tags help grooming: `idea` · `bug` · `doc` · `source` (new data source) · `question` · `chore`.

## Inbox

<!-- add new ideas at the top -->

- 2026-07-03 — [chore] the local `neo4j-drydocs-ee` Docker container's password is literally the
  string `<password>` (copy-paste artifact at creation). Fine for sandbox; change it before
  anything less throwaway. (Found while wiring web/ + agents/ to it.)
- 2026-07-03 — [idea] web/ front end shipped as a throwaway test page (no design pass). Needs:
  plan/wireframes, a real C4 rendering (NVL?), and a decision on whether the basic Cypher flow
  keeps talking bolt-from-browser or goes through a thin API.
- 2026-07-03 — [question] LLM key strategy for the ADK agents (core_ingest, controlm_fix):
  GOOGLE_API_KEY (Gemini) vs routing to Anthropic via LiteLLM; company side is Fusion SmartSDK
  on ADK, so Gemini-shaped is the safer default.
- 2026-07-03 — [chore] `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.
- 2026-07-03 — [chore] repo `.venv` has no pytest (and poetry isn't on PATH in plain PowerShell)
  — the `poetry run pytest -q` gate can't run as documented on this machine; reinstall dev deps.

- [bug] node_classifications says label ControlMFolder but every loader/edge writes :JobFolder
  (controlm_folders.cypher MERGEs JobFolder:Collection; edge entries say from_node: JobFolder) —
  same drift visible in the company copy. Decide the winning name via the gate, then fix the
  losing side everywhere. (same screenshots)
- [doc] README.md still says :DEPENDS_ON for the derived job->job edge; the loader + m3-verify
  write :WAS_INFORMED_BY (vocab m3_was_informed_by; DEPENDS_ON retired). Reconcile the README.
  (2026-07-01 Control-M naming review with SME)
- [idea] REQUIRES_SCHEDULER (:BatchProcessing -> :SchedulerKind) appears in README/plans but is
  NOT registered in relationship_vocabulary.yaml — register status: planned + gate before wiring
  the post-load step. (same review)
- [idea] "Application contains folders" support view (SME's mental model): derive
  Folder -> :BatchProcessing from job.APPLICATION reconciliation + the folder-naming resolver;
  SME-gated DERIVED edge, never base ingest (BMC puts APPLICATION on the job; folders can hold
  mixed applications). (same review)
- [chore] Versioning reset: adopt semver policy (VERSIONING.md), cut first tag (v0.2.0 or v0.3.0
  with the board), start CHANGELOG.md back-filled from completed epics. (2026-07-01 architecture review)
- [chore] CI: GitHub Actions running the CLAUDE.md gates (pytest -q, import drydocs.cli,
  drydocs --help, ruff) on every push; classification test as publish-boundary guard. (same review)
- [doc] .claude/skills/run-drydocs/SKILL.md Gotchas are stale: PyYAML IS a runtime dep since D2
  (the "4 skipped tests / PyYAML not installed" notes are outdated), and test counts have moved.
  Refresh next time the skill is touched. (noticed 2026-07-01 while authoring groom-backlog)
- [idea] cli.py regroup: split the 937-line flat command list into domain subcommand groups
  (schema/ingest/verify/variables) — NOT milestone names; rename m1-verify/m3-verify →
  verify-reference/verify-controlm with deprecation aliases at the v1.0 window. (same review)
- [chore] Remove unused deps: pandas, streamlit, streamlit-agraph (runtime), pypdf (dev) — declared
  in pyproject.toml, imported nowhere; ~100MB install weight. (same review)
- [idea] Integration tests: testcontainers[neo4j] is already a dev dep but unused — one end-to-end
  CSV→Neo4j load test would cover the untested Cypher-execution path. (same review)

## Recently groomed (audit trail)

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-01 — [source] seal_app_ref attribution → **K1 + K2** (Epic K, phase 9). CORRECTED
  during grooming by the company reconciliation answers: the edge is spec-level on BOTH sides
  (their FR-NS-013/UC-NS-005 docs read ACTIVE with no loader/vocab/gate behind them); the feed
  is STG_APP_FACT semantic facts, NOT job.APPLICATION (explicitly unreliable for SEAL identity).
  Promoted as build items with the company's write shape, gate sequence, and verify shapes.
- 2026-07-01 — [chore] fragment cleanup (naming drift, banners, SDLC-Docs README) → **J1**
  (Epic J, release-infrastructure) via the groom-backlog skill's demonstration run. Sibling
  lines (versioning reset, CI, cli regroup, unused deps, integration tests) stay in the inbox
  pending user decisions (semver start version, rename window).
- 2026-07-01 — Epic I (I1–I4, project board & planning infrastructure) groomed into `backlog.yaml`
  from the architecture-review plan; schema upgraded to `drydocs.backlog.v2` (I1 done same day).
- 2026-06-20 — initial backlog A1–F2 seeded directly into `backlog.yaml` from `02-backlog.md`.
