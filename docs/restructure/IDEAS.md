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

- 2026-07-15 — [bug] **`Neo4jClient.run_script` inherits APOC's comment-`;` split.**
  `apoc.cypher.runMany` splits on every end-of-line `;`, including inside `//` comments;
  Neo4j 2026.x/Cypher 25 then rejects the comment-only fragment as an empty statement
  (5.x tolerated it). Seen live 2026-07-15: `apply-ontology-supplement` failed against the
  EE container until the one comment was reworded. The loaders are already protected
  (`base.py::_code_semicolons`); harden `run_script` the same way — split client-side with
  the comment/string-aware scanner and run per-statement — so supplement files can't
  re-trip this.

- 2026-07-15 — [chore] **`m3-verify` "active folders contain at least one job" fails on the
  bundled samples** — folders 161020 / 160501 are active (`user_daily=Y`) in
  `controlm_folders__sample.csv` but have no rows in `controlm_jobs__sample.csv`
  (empty=2 total=7, exit 1). Either give each a sample job or downgrade that invariant to
  a warning for the CSV adapter, so the README quick start verifies clean.

- 2026-07-14 — [doc] **`drydocs-project-review.md` has no canonical outline** — the new
  whole-project review (docs/design/) renders through the Epic L pipeline but is free-form:
  `doc_outline.py` only validates `docs/design/*-tdd.md`. When L8 introduces the second doc
  type (runbook), consider a `review.outline.yaml` third type so the review gets the same
  completeness validation + traceability treatment; it also needs a refresh cadence (facts
  pinned to a commit go stale quietly — maybe a Rev bump per epic close).

- 2026-07-14 — [source] **K2 FID / ALIAS reconciliation tables are company-side unblocks.**
  The attribution loader's TierReconcilers seam ships empty for FID and ALIAS (facts stay
  unresolved, counted in coverage) — tier 2 needs a FID -> seal_id source and tier 4 an
  alias table before those tiers resolve anything. APP_NAME reconciles today from the
  loaded SEAL reference (exact normalized match; ambiguous names excluded).

- 2026-07-14 — [idea] **internal psgmgr now derives `ctlm_id` = `folder_id.job_id`** (e.g.
  `161015.7`; recorded at the P2 avg-run gate sign-off as the §B join upgrade). Ripple beyond
  CM_AVG_RUN to check: (1) which other CM_ views/extracts carry it — could replace weak joins
  elsewhere; (2) K2 manual-CSV template `source_key` could accept `ctlm_id=<id>` as shorthand
  for the composite (folder_id, job_id) key; (3) company-side port alignment — the derived
  column lives internal-side, keep producer mechanism generic.

- 2026-07-12 — [idea] **dry-docs.com site visual language**: seed from the whitepaper's
  "overnight ledger" identity (greenbar/banner-page/mono-display; canonical source stays
  docs/whitepaper/drydocs-whitepaper.md). Parked until website work starts — the site is
  not started and the domain's availability is unresolved. (Re-inboxed slim at the
  2026-07-13 groom from the artifact-design-review line, sub-item 3.)

- 2026-07-12 — [doc] **/documentation skill has NO white-paper guideline** (types: README, API,
  runbook, architecture, onboarding). Wrote docs/whitepaper/drydocs-whitepaper.md deriving
  structure from the architecture-doc type + white-paper conventions; if white papers recur,
  add a "White paper" type to the skill (exec summary → problem → approach → architecture →
  governance → roadmap) and consider an Epic L outline for it (whitepaper.outline.yaml).

- 2026-07-11 — [idea] **Lineage live-load gate session** (captured at the G9 close). The Fork-3
  writer is built and REFUSES by design: the four vocabulary entries (m3_invokes / m3_triggers /
  m3_reads_from / m3_writes_to) are `status: planned`, so `write_curated` raises
  GateBoundVocabularyError until the HITL gate flips them active. When the SME schedules that
  gate: review a `plan_curated` output + the lineage-review page for a real extract, confirm
  the vocabulary (and the writer's Script.path key + DataAsset URN mapping), flip statuses,
  first live curated write. HITL-dependent — groom into an item when the gate is scheduled.
  Refs: 0002-C §4/§7, drydocs_lineage/writer.py, tests/unit/test_lineage_writer.py (the gate
  test flips deliberately at activation).

- 2026-07-10 — [idea] **Remediation next slices — tracked in the TDD, not itemized here**
  (captured at the G3 close, same day). What remains after G3/0002-B closed: the Tier-2
  agentic lane (FR-REM-4 — gated on OQ-2 registry shape + OQ-4 agent runtime, both open
  HITL questions), XML I/O (gated on the vendor schema acquisition — company-side .dtd /
  exportdeftable, corpus stub has the fetch list), and the A3 ground-truth watched filename
  + B1 var.text rule (company-side; adjudicates the real M0 unit's equivalence verdict —
  the resolver stays untouched until then). Groom into items only when their gates open;
  `docs/design/drydocs-remediation-tdd.md` §6/§7 is the tracking surface.
- 2026-07-10 — [idea] **Phase C packaging (deferred by ADR 0002-A-1 at the G2 relocate)**: the
  pieces deliberately NOT executed in Phase B — (a) make `drydocs-core` independently
  installable (packaging-only commit: per-package pyprojects + path deps, NO file moves),
  (b) the remainder's 4-way component split (load/review/plan/docgen as real packages) and
  load's final name. UPDATED at the G3 close (same day): G3 completed IN-MONOREPO, so
  trigger (a) expired unfired — no early promotion needed; the whole line now waits for
  Phase C proper. Refs: ADR 0002-A-1 §Consequences, PORT-MANIFEST header sequencing note.
- 2026-07-09 — [idea] **Control-M Workbench as the remediation greenfield test bed — PARKED**
  (user call, 2026-07-09). The Workbench Docker image (dev Control-M, plain `docker run`, no
  Kubernetes/Helm) would let fix packages be DEPLOYED + EXECUTED against a disposable env
  before the Jira handoff — stronger than the offline equivalence proof, still SoD-safe.
  Blocked here: image lives on distribution.bmc.com (not Docker Hub; pull attempt 401) and
  needs an EPD-entitled account + identity token — an entitlement/machine-boundary question,
  not a technical one. Ports 8443/7005 verified free on this box. Revisit when OQ-1 closes
  company-side or entitlement is resolved. Refs: `controlm-api-installation.md` (corpus,
  §Workbench + SYNTHESIZED notes), `drydocs-remediation-tdd.md` §HITL OQ-1. (Control-M for
  Kubernetes / Helm-chart offering deliberately SKIPPED — different product, agents-in-K8s,
  no current use case.)
- 2026-07-09 — [idea] `:SchedulerKind` slated for **DEPRECATION → `:AisCapability` + `:AiTool`**
  (user 2026-07-09). Today SchedulerKind is a small placeholder vocab (ControlM/Autosys/Airflow,
  seeded `ontology.cypher` + the `scheduler_kind` constraint) with no `node_classifications` entry.
  The replacement classes are **not yet defined** — needs the SME to specify what `:AisCapability`
  and `:AiTool` represent and how the app batch port's `REQUIRES_SCHEDULER` re-targets them (one
  edge or two). Touches: the C6 `requires-scheduler` map entry (target provisional), F1/F2
  orchestrator crosswalks, `ontology.cypher` seeds + the `scheduler_kind` constraint, README.
  Ontology/node-meaning ⇒ HITL gate; groom into an item once the two classes are defined.
  Reconciliation placeholder created: `config/taxonomy/platforms.yaml` (status: placeholder).

- 2026-07-08 — [doc] **BRD outline (Epic L, deferred)** — the third canonical doc type after
  TDD (L1) and Runbook (L8). Parked, not promoted: the BRD is a work-in-progress upstream and
  the user flagged it as "definitely a later phase", so there is no stable outline to write an
  acceptance test against yet. When the BRD shape settles, promote as `docs/design/templates/
  brd.outline.yaml` (reuse the `drydocs.doc-outline.v1` schema + traceability spine) into Epic L.
  Seed from the corpus: `SDLC-Docs/BRD - Table of Contents.docx`, `business requirements document
  template 31.docx`, `Business Requirements Template - FULL CDI Version.docx`.
- 2026-07-06 — [idea] **`drydocs-docmeta` component plan written** — full plan in
  `knowledge/upgrade-plans/docmeta-component.md`: component boundary (new `docmeta`
  COMPONENT_GROUP, imports core only, CLI via entrypoint exemption), config
  `doc-source-registry.yaml` + test guard, `drydocs_docs` DB + composite delta, phases
  P0 (benchmark) → P7 (T4 connectors), Port A inventory (bkup scraper → producer:
  carry cleaner/tokenizer/manifest, adapt registry/confluence-interface, drop migrate),
  Port B git-readme §6 (clean-adds / Canonical-COMPANY connector wiring / company
  supplements: blocked vendor fetches, Graph-API creds, Enterprise multi-DB target).
  Heads-up bullet added to git-readme.md. Groom phases P1–P3 to backlog after the P0
  benchmark verdict; ADR 0004 is the P1 gate output. The four T1–T4 tier lines were folded
  INTO this sequenced plan (P0→P7) and moved to the audit trail (2026-07-09). P0's corpus
  load is already substantially executed: the bmc-docs lexical loader (Document→Chunk,
  llm-graph-builder pattern) shipped and gate `bmc-docs-lexical-load` was ACCEPTED 13/13,
  LOADED LIVE (commits 12423f4/24d6a4b) — the WRITTEN benchmark verdict (traversal vs
  manifest-routed markdown vs vector RAG) + ADR 0004 still remain before P1–P3 promote.
- 2026-07-03 — [chore] the local `neo4j-drydocs-ee` Docker container's password is literally the
  string `<password>` (copy-paste artifact at creation). Fine for sandbox; change it before
  anything less throwaway. (Found while wiring web/ + agents/ to it.)- 2026-07-03 — [question] LLM key strategy for the ADK agents (core_ingest, controlm_fix):
  GOOGLE_API_KEY (Gemini) vs routing to Anthropic via LiteLLM; company side is Fusion SmartSDK
  on ADK, so Gemini-shaped is the safer default.
- 2026-07-03 — [chore] `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.- [idea] cli.py regroup: split the 937-line flat command list into domain subcommand groups
  (schema/ingest/verify/variables) — NOT milestone names; rename m1-verify/m3-verify →
  verify-reference/verify-controlm with deprecation aliases at the v1.0 window. (same review)

## Recently groomed (audit trail)

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-15 groom run (weekly inbox groom) — 3 promoted / 1 retired (resolved in place):
  - [chore] `controlm-loader-flow.md` → `docs/history/` move (captured same day at the
    controlm docs status-refresh sweep, e3e7bec) → **J11**. Inbound-linker correction made
    during grooming: grep says README.md + the internal governance doc reference it, NOT
    CHECKPOINT/reviews as the inbox line guessed.
  - [chore] schema_graph.cypher stale (generated 2026-06-09, no drift guard; found at the
    K2 build) → **C8** — regenerate-with-guard vs mark-point-in-time deliberately left as
    an either/or in the acceptance, decided at execution (derived view, no gate needed).
  - [chore] session-ritual `python scripts/...` fails outside the venv → **J12**
    (CLAUDE.md ritual lines + snapshot.ps1's two `& python` calls; re-verified live this
    session — render_design_doc.py failed bare, succeeded under `poetry run`). Execution
    caution recorded: CLAUDE.md carried uncommitted user edits at groom time.
  - retired: the 2026-07-13 UI-branch reconcile line — fully RESOLVED in place by its own
    2026-07-14 updates (all UI branches reconciled; the web stream lives entirely on main);
    no item needed, the resolution narrative is preserved in this trail's 2026-07-14 entries.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (trigger = L8 landing the 2nd doc type), K2 FID/ALIAS reconciliation tables
    (company-side sources), ctlm_id ripple checks (internal-side investigation),
    dry-docs.com visual seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL), remediation next slices (TDD §6/§7
    tracks), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind →
    AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P1–P3
    (P0 verdict + ADR 0004), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-15 — [bug] psgmgr version filter domain is `'Y'` not `'1'` — resolved by the
  FINALIZED company Control-M ingestion TDD (captured local-only in
  `internal-local/company-backflow/controlm-ingestion-tdd.md`; their live extracts filter `'Y'`
  and returned the worked-example population). Closes staging-ingestion-flow preflight 0.3 → **D4**.
- 2026-07-14 — [idea] Two support queries proven live on the internal graph (dependency-chain
  finder via undirected `shortestPath` over `WAS_INFORMED_BY`; folder-scoped dependency census,
  ~69% cross-folder stat) — groomed to drydocs-api named endpoints → **O7** (closed same day:
  already shipped by O5's `queries.py`; the note was stale — O5 built them in directly).

- 2026-07-14 groom run (ADR 0005 Action items → Epic O; not an inbox groom) — 4 promoted:
  **O3** ratify ADR 0005 (in_progress — awaiting the SME flip, the E1/P2 idiom; gates the
  rest); **O4** GraphAccess seam refit + dev-flag-gated raw Cypher + credential-rule doc
  (ADR items 2/4/5); **O5** thin-API component scaffold (ADR item 3 — the ADR explicitly
  deferred it to this flow; NEW module `drydocs-api`; fable per the component-boundary
  precedent); **O6** live C4/graph view through the seam (the remaining O1 build; O1
  closes on O3+O6). Ran at the feat/web-login-mock --no-ff merge (design pass onto main).

- 2026-07-13 groom run (weekly inbox groom) — 2 promoted / 1 merged / 1 re-inboxed:
  - [chore] ruff cleanup → CI lint gate (2026-07-11, found executing J5) → **J10** (Epic J,
    phase 8; ready — J5 done and live on main). The user's timing flag preserved in the item
    notes: execute during a port lull, the diff touches every Python file.
  - [idea] artifact-design review sub-item 1 (governed-render-fidelity rule: governed
    surfaces — design-doc renders, gate pages, board — publish VERBATIM; editorial treatment
    only for outward-facing docs) → **L12** (Epic L, phase 10).
  - [idea] artifact-design review sub-item 2 (artifact-design skill's "UI, not a document"
    checklist + AI-default-looks list as the UI-WIP/ review lens) → **MERGED into O1** notes;
    O1 re-tiered opus → fable on the groom touch (G3 policy — the bolt-vs-thin-API call is a
    boundary decision).
  - [idea] artifact-design review sub-item 3 (whitepaper "overnight ledger" identity as the
    dry-docs.com visual seed) → re-inboxed as its own slim line, parked until website work starts.
  - kept parked, unchanged (each on its recorded gate): /documentation whitepaper doc-type
    (trigger "white papers recur" hasn't fired), lineage live-load gate session (HITL —
    groom when the SME schedules it), remediation next slices (TDD §6/§7 tracks), Phase C
    packaging (plan gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool
    (SME class definitions), BRD outline (later phase), docmeta P1–P3 (P0 written verdict +
    ADR 0004), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 rename window).
  - hygiene: deleted the stray empty docs/restructure/IDEAS.md.tmp (interrupted-write leftover,
    0 bytes, untracked).

- 2026-07-11 — /tech-debt documentation audit (docs/reviews/tech-debt-documentation.md) —
  0 promoted / 1 merged / 5 executed with the review / 3 deduped:
  merged: README feature-currency gap → **J2** (title broadened; one README pass).
  executed (D-numbers per the report): D2 login tribal-knowledge doc committed under
  internal/ with classification; D5 MODULE_MAP drift (future-markers on shipped H2/H5
  modules; sme_notes/gate_pages rows added; lineage row = populated); D6 stale cron prompt
  → docs/history/ + banner; D7 root console dump → gitignored internal-local/; D8 tracking
  headers on the two 2026-07-09 tech-debt reports.
  deduped: skill staleness → J4; missing runbook → L8; UI-WIP → O1. Structural verdict:
  clean — all point-in-time reviews banner'd, living docs came through the relocate clean.

- 2026-07-11 groom run (G9-close session; directive: groom the remaining NON-HITL items) —
  2 promoted / 1 merged / 1 inboxed:
  - [idea] G9 tech-debt finding #3 (extractor coverage accounting — stale/nameless/no-target
    skips are silent) → **G11** (drydocs-lineage, phase 6; ready — G9 done). Report, never
    drop: the STG_PARSE_QUALITY / UNMATCHED house rule applied to the candidate side.
  - [idea] G9 tech-debt finding #2 (extractor CSV column contract duplicates controlm_jobs.sql
    aliases as strings, silent-drop on alias rename) → **MERGED into N2** (the SQL SELECT-list
    drift guard gains the extractor as a second consumer of the same list). The 2026-07-10
    tech-debt line is fully dispositioned (#1/#4 fixed same day, #2→N2, #3→G11) and retires.
  - [idea] testcontainers end-to-end CSV→Neo4j load test (parked since 2026-07-01) → **J9**
    (drydocs-load, phase 8; ready — no deps, no HITL surface). Covers the never-executed
    Cypher path; opt-in + Docker-gated so the unit suite is untouched.
  - inboxed: the lineage live-load gate session (HITL-dependent by definition — the Fork-3
    writer's refusal IS the gate; groom when the SME schedules it).
  - kept parked, unchanged (each on its recorded non-HITL-groomable gate): remediation next
    slices (OQ-2/OQ-4 + company-side), Phase C packaging (plan gate), Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME class definitions = HITL), BRD outline (later
    phase, user call), docmeta P1–P3 (P0 written verdict + ADR 0004), EE container password
    (user deferred), LLM key strategy (open user question), common/ in /list-apps (cosmetic),
    cli.py regroup (v1.0 rename window).

- 2026-07-10 groom run (G3-close session) — 0 promoted / 1 inboxed / 1 kept-updated / 0 merged:
  - inboxed: remediation next slices (Tier-2 FR-REM-4 gated on OQ-2/OQ-4; XML I/O on schema
    acquisition; A3/B1 company-side) — deliberately NOT itemized; the TDD §6/§7 tracks them,
    groom when their gates open.
  - kept-updated: the Phase-C packaging line — G3 closed IN-MONOREPO so its early-promotion
    trigger (a) expired unfired; the line waits for Phase C proper.
  - all other inbox lines remain parked on their recorded gates (no change today: Workbench/
    entitlement, SchedulerKind/SME classes, BRD, docmeta/P0-verdict+ADR-0004, container
    password, LLM keys, common/ cosmetic, cli regroup/v1.0 window, testcontainers).
  - backlog database untouched this run (G3/G10 changes landed in-session pre-groom:
    G3 done 46, G10 ready — see commits ca9f165..ef57602).

- 2026-07-09 — [idea] design-doc feedback: per-subsection annotate controls when a section
  has >2 subsections (1.a/1.b/1.c… or steps 1/2/3) so feedback keys to the exact subsection
  → **L11**. (chat note, same review pass as L10; design core = stable derived sub-anchors)
- 2026-07-09 — [idea] design-doc feedback widget: appendix "SME - Feedback" panel (divider +
  static HITL how-to: annotate, Copy feedback, create docs/design/feedback/<doc>-rev<N>.yaml,
  paste, save) → **L10** (amended same day: instruction block, not a free-text notes field).
  (chat note after reviewing docs/design/feedback/scans/; answered the open question — the
  export is .yaml per feedback_yaml, not markdown)
- 2026-07-09 groom run (Opus session) — 4 promoted / 1 retired; web/ became a plan change:
  - [chore] repo `.venv` has no pytest / poetry not on PATH → **RETIRED (resolved this session)**:
    pipx + Poetry 2.4.1 installed, in-project `.venv`, dev deps synced; `poetry run pytest -q`
    → 453 passed / 3 skipped. The documented gate now runs. (See memory `drydocs-python-toolchain`.)
  - [doc] `run-drydocs/SKILL.md` stale Gotchas → **J4** (Epic J, phase 8). Verified 2026-07-09:
    still claims "PyYAML not installed" (×2), "159 pass", Aura, and `apply-m3-supplement` — all stale.
  - [chore] CI (GitHub Actions gates + classification publish-boundary guard) → **J5** (user
    confirmed promote 2026-07-09).
  - [chore] unused deps → **J6** (Epic J), **scoped after verification**: only `streamlit` +
    `streamlit-agraph` are dead; `pandas` is intentional (`csv_adapter.py`) and `pypdf` is now used
    (`scripts/ingest_jpmc_reports.py`) — the original note's "imported nowhere" claim corrected.
  - [idea] web/ front end → **O1** + NEW module `drydocs-web` + NEW **phase 12 "Web console /
    graph visualization"** (plan change, user-approved). Marked in_progress — design pass in flight
    (branches `feature/ui-dark-landing-myapps` + `feat/web-console-design-pass`, untracked `UI-WIP/`).
  - Kept parked: BRD outline (later phase), `drydocs-docmeta` plan (gated on the P0 benchmark verdict
    + ADR 0004), the `<password>` EE container (deferred), LLM-key strategy (open question), `common/`
    in `/list-apps` (cosmetic), cli.py regroup (gated on the v1.0 rename window), and the testcontainers
    integration test (testcontainers[neo4j] confirmed unused; not selected this run).

- 2026-07-09 — [chore] Versioning reset (parked since 2026-07-01) → **J3** (Epic J, phase 8),
  executed same day: adopted SemVer (VERSIONING.md), bumped pyproject 0.1.0 → 0.3.0, back-filled
  CHANGELOG.md from the completed epics, cut annotated tag **v0.3.0** (user decision over v0.2.0 —
  matches plan phase 8's `release:` field). Sibling parked lines (CI, cli.py regroup, unused-dep
  removal, integration tests) stay in the inbox.

- 2026-07-09 groom run (this session) — weekly inbox groom, 2 promoted / 5 retired / 2 kept-updated:
  - [doc] README still says `:DEPENDS_ON` for the derived job→job edge → **J2** (Epic J, phase 8).
    VERIFIED 2026-07-09: the loader `controlm_dependencies_derived.cypher` MERGEs `:WAS_INFORMED_BY`
    and vocab `m3_was_informed_by` is active ("Replaces DEPENDS_ON") — README is the stale side
    (4 refs: README.md:16,139,152,231). Naming-drift doc hygiene, same class as J1.
  - [idea] `REQUIRES_SCHEDULER` (:BatchProcessing → :SchedulerKind) unregistered → **C6** (Epic C,
    phase 2 — re-opened). VERIFIED 2026-07-09 still absent from `relationship_vocabulary.yaml`;
    register `status: planned` + HITL gate before wiring the post-load step (edge-meaning ⇒ gate).
  - [idea] **T1** vendor-doc KG traversal benchmark → SUPERSEDED by the `drydocs-docmeta` plan (its
    P0 spike) AND substantially executed: the bmc-docs lexical loader (Document→Chunk,
    llm-graph-builder) shipped + gate `bmc-docs-lexical-load` ACCEPTED 13/13, LOADED LIVE (commits
    `12423f4`/`24d6a4b`). Written benchmark verdict + ADR 0004 still pending before P1–P3 promote.
  - [source] **T2/T3/T4** internal-platform / product-process / SME-context ingestion → ABSORBED into
    the `drydocs-docmeta` sequenced plan (`knowledge/upgrade-plans/docmeta-component.md`, phases
    P0→P7); tracked there until the P0 verdict + ADR 0004 gate, per the docmeta note's own instruction.
  - [bug] `node_classifications` ControlMFolder-vs-`:JobFolder` drift → CLOSED (already RESOLVED
    2026-07-05, ADR 0003 + rename migration); the struck line is retired from the inbox.
  - kept + updated in-inbox: the `drydocs-docmeta` plan note (records the bmc-docs load; T1–T4 folded)
    and the web/ front-end note (flagged the now-active design-pass branches). Parked pending user
    decisions (semver start, CI, cli.py regroup, unused-dep removal, integration tests), open
    questions (LLM key strategy), and piggyback chores stay in the inbox.


- 2026-07-08 groom run (this session) — **new phase 11 "Source governance ledgers"** + 9 items:
  - [question] SEAL ontology reshape + scraped-docs source-of-record → **K3** (gate session;
    K2 gains `depends_on: K3` — the wasAssociatedWith/Entity type conflict means the reshape
    gate runs before the match-policy gate is ticked). Prep was already on main (`0986d6d`).
  - [bug] design-doc HTML Chrome-vs-Brave render discrepancy → **L9**.
  - [idea] provenance diet + source audit fields (2026-07-05) → **M1–M3** (doc-06 Phases 2–5;
    Phases 0–1 shipped 2026-07-07 pre-groom via gate `controlm-q1q3-phase1` + commit `62673ed`).
  - [idea] property-level ontology terms for the audit envelope (2026-07-07) → **M4**.
  - [question] same-row-derived node relationships (city/state/country, 2026-07-07) → **C5**
    (re-opens phase 2 — methodology gap).
  - [idea] source column mappings (doc 08, 2026-07-07) → **N1–N2** (Phases 0–1 per the plan's
    own groom note; later phases stay in the plan doc).
  - [idea] TechStack software registry (2026-07-07) → CLOSED, executed directly as plan-07
    (Phases 0–2 done `caa1e79`/`eb0fe56`; Phase 3 at the software-usage-patterns gate; Phase 4
    deferred). Not backlog-itemized — the plan doc tracks it; itemize the P3 build when its
    gate passes.
  - [idea] "Application contains folders" support view (2026-07-01 review) → SUPERSEDED by the
    gate-confirmed header-row design (`controlm-q1q3-phase1` + `107581d`): ControlMApplication
    + CONTAINS_FOLDER now load in the folder pass from CM_DEF_VJOB JOB_ID=1 — NOT derived from
    per-job APPLICATION reconciliation as the line proposed (that column stays informational).

- 2026-07-08 — Epic L (**documentation infrastructure**, new phase 10) groomed into `backlog.yaml`
  from the deterministic-documentation design conversation. Canonical per-doc-type outlines (stable
  anchors = the render/traceability/HITL id namespace), md-as-source deterministic render, and the
  digital + pen/paper markup loop. `tdd.outline.yaml` drafted same day (L1 in_progress). New module
  `drydocs-docgen`. Sequence (user-set): TDD (L1) → render/feedback (L3–L7) → Runbook (L8, capstone);
  runbook resequenced from L2 → L8. BRD parked above (later phase). Distinct from the
  `drydocs-docmeta` ingestion idea (2026-07-06).
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
- 2026-07-09 groom run (remote session) — 8 promoted / 0 inboxed; PLAN CHANGE: new phase 13
  "Runtime topology & maintenance windows" + Epic P (ratify — the phase-12/O1 precedent):
  - CM_HOSTS + CM_AVG_RUN onboarding (add-source-object walkthrough ×2; hosts gate SIGNED OFF
    18/18, avg-run gate awaiting SME) → **P1** (internal probes + DC scope call), **P2**
    (avg-run gate session, in_progress awaiting HITL), **P3** (hosts loader + RUNS_ON
    resolution pass), **P4** (avg-run property-supplement loader + job-name index),
    **P5** (the maintenance-window query — the driving use case).
  - Port-boundary tech-debt audit (docs/reviews/tech-debt-port-boundary.md) → **J7** (per-entry
    reconciler guards) + **J8** (skip-guard policy test); Phase-1 PORT-MANIFEST.yaml + guard
    EXECUTED pre-groom (5cfcfa7) — no item, the doc-06 precedent.
  - Taxonomy-ontology-map audit (docs/reviews/tech-debt-taxonomy-ontology-map.md) → **C7**
    (vocab_id + capture fields at the next gate); F1–F4 fixes EXECUTED pre-groom
    (c396d75, ede0b94).
