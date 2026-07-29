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

- 2026-07-28 — [chore] **PARKED UNTIL AFTER THE PORT REVIEW: verify the `neo4j-drydocs` MCP
  server actually works now.** It requires APOC, and APOC was silently ABSENT from the
  `neo4jtest` container for weeks (`NEO4J_PLUGINS=[apoc]` set, `/plugins` empty — fixed
  `33cfc68`, plugins now a mounted volume, apoc 174 procs + gds 471). So the server cannot
  have functioned in that window and **has never been verified since the fix**. Check: the
  server is `~/.claude.json` local scope, stdio, `mcp/neo4j:latest`, `NEO4J_DATABASE=drydocs`,
  re-pointed to 7687 — confirm it connects and returns a query against the freshly reloaded
  graph (210 `:CodeModule` is a convenient marker). Note the container was RECREATED, so also
  re-confirm the port with `docker port neo4jtest` rather than trusting the config. Second,
  smaller thing worth doing in the same pass: **GDS is new here** (471 procs) — nothing in
  DryDocs calls it yet, so decide whether it earns a place (Epic R / graph-retrieval
  benchmark) or is just available. Deliberately deferred so it does not interleave with the
  port review.
- 2026-07-28 — [question] **Retire the `depgraph` sibling repo entirely by bringing the SCANNER
  in-house?** The user's reaction to the fork merge was *"I didn't realize it was still used
  after we made it a module"* — and that instinct was half right in a way worth acting on. ADR
  0002-C absorbed depgraph's **lineage** assets into drydocs-core, but the **scanner** never
  moved: `snapshot.ps1` shells out to `../depgraph` every session, which is precisely why a
  months-old sibling checkout could write a 105-edge undercount (→ U7). The whole *class* of
  defect — instrument revision decided by a checkout nobody looks at, capability split across
  branches, `dirty:true` in every meta block — exists only because the tool lives outside this
  repo's history. In-housing it (`drydocs_core/codegraph/`, or a thin vendored package) would
  delete that class outright: one `poetry run` invocation, pinned by `poetry.lock`, versioned
  with the code it measures, no probe needed because the tool and the caller ship together.
  Against: depgraph is deliberately stdlib-only and general-purpose (it scans any project, not
  just this one), it has its own Control-M/RUA/html-review surfaces DryDocs does not use, and
  0002-C consciously chose absorb-the-assets-not-the-tool. So this is a real trade, not a
  cleanup — size it before committing. Precondition now satisfied either way: the fork is
  consolidated (depgraph `5006567`, one branch), so there is a single revision to vendor from.
- 2026-07-28 — [question] **`config/dev-environment.yaml` under a `canonical-producer` row —
  decide the disposition producer-side too, not just company-side.** Step 48 raises this for the
  consumer, but the asymmetry is ours: `config/**` is `canonical-producer`, and U7 has just made
  that file *producer-local infrastructure* (sibling repo path, expected instrument commit, on
  top of the pre-existing container name + host ports). A port applies it wholesale, and the L16
  runbook's Appendix A is a **render** of it — so a producer value propagates into consumer
  documentation, which is exactly the drift Appendix A was restated to prevent. Options: a
  per-entry row (which keys? the file has no id-keyed grain — probably section-level: `neo4j:`
  and `depgraph:` are environment-specific, `services:` ports arguably shared), a
  canonical-company row, or split the file into a portable contract + a local overlay. The last
  is the cleanest and the most work. Left deliberately un-made by the 2026-07-28 session, per
  J16's own rule that a disposition is a decision, not a default. ~~Fork merge~~ — **RESOLVED
  2026-07-28**: both branches merged into depgraph `main` (`5006567`) and DELETED, local and
  remote; `main` now carries every capability (probe reports `multi_root` AND `tree` true for
  the first time, `-Tree` works). Semantic merge details in DryDocs `8a82e3b` and the depgraph
  merge commit; the `add_rel` signature/shape collision and three regions git auto-merged that
  should have conflicted are the parts worth re-reading if that code is touched again.
- 2026-07-28 — [chore] **react-router high advisory (GHSA-qwww-vcr4-c8h2, RSC-mode CSRF) cannot
  clear without the v7→v8 major migration** — v8 absorbs `react-router-dom` (its latest is
  still 7.18.1, inside the vulnerable 7.12.0–8.2.0 range), so `npm audit fix` is a no-op and
  the fix means rewriting the router imports against `react-router@8.3.0`. Escalated from O34
  per its stop clause (postcss/nanoid patches applied there); a UI-workstream decision, and
  likely moot in practice — the console is a Vite SPA, no RSC actions — but the audit stays
  red until ruled. Pairs with the code-splitting design call O34 also parked.

- 2026-07-27 — [idea] **The SME orchestrator-mapping act: what actually flips a batch port on.**
  SME direction, this session. CONFIRMED first, since the design rests on it: both ports are
  created `active = false` (`seal_applications.cypher:97,101`, `ON CREATE SET`) — and the
  stronger finding is that **nothing in the repo ever sets a Port's `active` to true, and
  nothing reads it.** It is a write-once dead flag today; the mapping act below is its missing
  writer. The direction: `(:BusinessApplication)-[:USES_SOFTWARE]->(:SoftwareProduct)` for
  ORCHESTRATION is **SME-mapped, established when the folder/entity mapping is confirmed** —
  not derived. The mapping table is a UI screen: cascading pickers **Product Line → Product →
  Business Application → [decision point: Control-M | AutoSys (once built)]** — that choice is
  what creates the orchestrator relationship — then a **filter of available folders** → the
  Control-M folder (matched on the internal folder naming-convention pattern) → an **SME
  check/approval + notes field capturing SME user, date** — and that completes the mapping.
  Four things this needs, all verified against what exists:
  1. **Home:** a new domain on the existing steward screen (`UI-WIP/wf-mapping-01.md`, backlog
     O13 done; O24 is the precedent for adding a domain). Its governing rule already fits this
     exactly — *the loader stays the ONLY graph writer*: the screen drafts a mapping-table row,
     which travels change artifact → gate → merge → next load run. The approval/notes/user/date
     fields ARE that screen's mandatory-rationale + lifecycle chips, already specified.
  2. **DONE 2026-07-27 — folded into the open gate as a companion section.**
     `config/gate-prompts/seal-app-ref-edge-reshape.yaml` **v3** now carries **§G** (7
     confirmations: orchestrator-first authorship, the C14 prefill demotion, 1:N cardinality,
     port activation, the §G5 consistency tie to §C1, the cascade, the unchanged write path);
     sign-off moved G→H, every existing id A1–F2 is unchanged so the external citations of
     §B/§C1/§E2 still resolve. SME rulings recorded as direction-to-confirm, not as decided.
  3. **What it re-frames in C14:** `batch_port_orchestrator` today writes the USES_SOFTWARE edge
     straight from the SEAL-declared string via the platforms.yaml crosswalk, with no SME
     confirmation anywhere in the path. Under this direction that declared string is a
     **prefill/proposal** and the confirmed folder mapping is the authority. Gate question, not
     a build decision — the loader was left as-is (§G2).
  4. ~~Missing edge behind dropdown 3.~~ **CORRECTED 2026-07-27 by the company-side review** —
     it is a **back-flow, not a build**. Producer-side `catalog_has_application` is `planned`
     with `loader: ~`, held there by the C9 note *"stays planned until a product-scoped extract
     is onboarded"*. **Company-side that precondition is already met**: a product-scoped extract
     feeds a dedicated loader (`pat_app_links.cypher`) and the edge is ACTIVE in the schema
     graph. Two riders now in §G6: the two sides **word the semantics differently** — producer
     "Product owns a set of SEAL-registered applications" vs company "a structural SUPPORT link,
     a Product is supported by 2+ apps (front-end/back-end)", which makes the picker mean
     different things — and the edge is **1:many by design** on both sides (the source extract's
     application-id column is multi-valued), so the picker returns a LIST.

  Also confirmed by that review: the company flagged its OWN stale artifact — a gate page still
  listing `catalog_has_application` as `planned` while its schema graph says `active`. Same
  root as the producer's staleness, opposite direction. **Divergence-ledger candidate**, and a
  reminder that "which surface is authoritative" needs an answer per repo, not once.

  Open questions carried into §G: the Event port's confirming evidence (no Control-M analogue —
  declared-only until an event source exists?); whether the planned `:Batch` intermediate
  collapses into the BatchProcessing `:Port` (§C2 already proposes retiring it); and what makes
  a folder "available" in the filter — unmapped only, naming-pattern match, or both.

- 2026-07-27 — [idea] **Company catalog gate (`internal/org/catalog/`, page dated 2026-06-25) has
  drifted ahead of the producer catalog ontology — back-flow / divergence-ledger candidate.**
  Screenshot review of `_catalog_gate_page.html` ("SME Gate Prompt — PAT Catalog Loader", step 1
  of 3; sibling `_product_application_gate_page.html` likely steps 2–3): introduces `:SubLOB` +
  `HAS_SUB_LOB` (LOB→SubLOB, "only CIB and AWM have them"), widens HAS_PRODUCT_LINE to
  `(:SubLOB|:LOB)`, uses label `:LOB {lob_id, name}` vs our `:CatalogLOB {lob_id, code, name}`,
  expects map ids `sub-lob-org-unit` + `catalog-lob-reconciles-segment` (ours:
  `lob-has-product-line` / `lob-reconciles-to-segment`, confirmed 2026-06-21), and ingests a
  5-field `pat_lob_sublob_productline.csv` (164 rows; Sub-LoB Name column our
  `lob-product-team.yaml` capture lacks). None of it exists here, even as `status: planned`.
  Gate MECHANICS all match the gate_pages.py design (localStorage ticks, no-write-until-confirmed,
  `{confidence, authority, aliases}` on RECONCILES_TO, skos:closeMatch aliases, precedence winner
  `lob-product-team`) — content drifted, mechanism didn't. Page date 2026-06-25 PRE-DATES the G2
  Phase-B relocate (2026-07-10), so its `drydocs/schema/ontology.cypher` path was period-correct,
  not a bug — refresh it if the prompt is revised. Real page bug to fix before signoff:
  functional-org target "Corporate" is ambiguous vs our seeded `:BusinessSegment {code:"Corp",
  name:"Corporate"}` — written as a code it MERGEs a phantom segment. Useful real-data signal:
  CIB + AWM appear as SEPARATE LoBs with 1.0 exact matches → resolves the LOB002 AWMCIB (legacy,
  0.5) open question in `lob-product-team.yaml`. If the company gate signs off: mechanism-only
  back-port (vocab entries as `planned`, map entries, 5-field taxonomy capture, LOB-vs-CatalogLOB
  label ruling) or an explicit port-prompt divergence-ledger entry. ~~COORDINATE FIRST: a laptop
  session (unpushed as of 2026-07-27) is re-working BusinessApplication mapping — don't touch
  catalog/SEAL map entries until it lands.~~
  KEPT-UPDATED 2026-07-27 groom: the laptop session LANDED same day (business-application-identity
  gate SIGNED OFF `fc15191`; the build = S3, `seal_id` → `app_id` on the canonical node) — the
  coordinate-first constraint is lifted. New wrinkle for the eventual back-port: the comparison
  now also crosses the app_id rename (the company page pre-dates it), so the label ruling
  (LOB vs CatalogLOB) and the key ruling (app_id) should be settled in the same pass. Still
  parked on its original trigger: the COMPANY gate's own sign-off.

- 2026-07-27 — [question] **Internal platform vocabulary in the sample corpus — ruling
  needed.** Residual from the groomed J14/J15 publish-boundary pair: the samples still carry
  real-looking internal platform tokens (`HLDM`, `PRARAG`, `svc.hldm`, `/opt/scripts/hldm/`,
  `host-hldm-01`, datacenter codes) — a different value class from SEALIDs, deliberately left
  untouched by the 2026-07-27 sweep and not ruled on. Is platform vocabulary publishable
  mechanism (like the naming grammar) or a value class to synthesize? User/SME call; once
  ruled, J15's value-shape guard test can grow a rule for it.
  KEPT-UPDATED 2026-07-27 (J14 close): two more members of the same identifier class found at
  the build — (a) the escalation-table schema identifiers (`psgmgr` / `cm_escalation_db` /
  `EJOBNAME` / `ECOMPONENT`) generalized out of the two J14 files but still present in 6+
  tracked files (controlm-db skill, gate prompts, taxonomy-ontology map, remediation TDD);
  (b) `knowledge/standards/technology/data-center-naming-convention.md` carries real DC codes
  and a real app code — same class, same sibling directory, untouched by J14 by scope. The
  ruling should cover: platform tokens, DC codes, schema/table/column identifiers, and
  synthetic-sample product NAMES that echo real ones ("Home Lending Servicing" in
  lob-product-team.yaml, paired only with synthetic ids).

- 2026-07-25 — [question] **How much depgraph audit history do we keep?** (review finding
  F11, `docs/reviews/architecture-structure-review-2026-07-25.md`). `knowledge/depgraph-snapshots/`
  holds 66 JSON files / 4.2 MB, several per day, unbounded — some 2026-07-20/21 timestamps are
  minutes apart. The review proposed "run `drydocs prune-snapshots`" and that was **wrong**:
  that command prunes snapshot nodes INSIDE Neo4j via `SnapshotWriter` and needs a live
  connection; it never touches these files. So there is no existing mechanism, and the real
  question is a retention POLICY: the files are a deliberate per-push structural-drift record
  with a documented A/B compare workflow (`knowledge/depgraph-snapshots/README.md`), so thinning
  them trades audit history for repo size. Candidate rules if we want one: keep one per day
  beyond N days; keep every snapshot whose `meta.commit` is a tagged release; keep all, and
  stop worrying (4.2 MB is not a problem yet). **User call — not groomed until it is made**;
  the ritual keeps writing one per session meanwhile.
- 2026-07-25 — [idea] **Supplement shape C — registration-vs-instance-seed re-slice** (the
  parked sibling of shape A, now groomed as **G29**). Re-sliced so that registering an
  ontology term and seeding an instance of it are separate operations rather than two halves
  of one supplement file. Explicitly **gate-worthy, not a refactor** — it changes what a
  supplement MEANS, so it routes through the HITL gate rather than a build item. Groom when
  the SME convenes it; G29 deliberately does not touch it.
- 2026-07-25 — [source] **Databricks Unity Catalog researched — full notes at
  [`reference/research/databricks-unity-catalog.md`](../../reference/research/databricks-unity-catalog.md)
  (SME saw "Unity Catalog works so well in Databricks" and asked what it captures).** Public
  vendor build of the layer `docs/patterns/data-catalog/` models. Headline: its four semantic
  features land almost exactly on node types we already define — Domains → `CatalogDataDomain`,
  Glossary → `CatalogBusinessTerm`, governed tags → `CatalogTag` / `CatalogClassifier`, data
  classification → `config/classification.yaml`. Independent convergence, worth citing rather
  than re-deriving. **Three things to actually use:** (1) *lineage derived from Spark execution
  plans, never declared* — a clean public demonstration of the GROUNDED-over-SYNTHESIZED
  principle, and the argument for deriving Control-M dependencies from definitions rather than
  documentation; (2) *a controlled vocabulary needs an enforcement point or it rots* — their
  governed tags only work because a **tag policy** is attached, which is our classification-test
  rule generalized to any glossary we build; (3) their glossary ships "terms that link to each
  other," i.e. a concept scheme, which is external evidence for the acronym-catalog idea below.
  **Don't over-borrow:** "Genie Ontology" is a learned context layer, **not** an ontology in the
  PROV-O/ORG sense — cite as *catalog* precedent only, same tool-pattern-not-standard verdict as
  NeoCarta. It also has no orchestration model, so it answers a different question than we do.
  **Latent option (not proposed):** if the company runs Databricks, `system.access.table_lineage`
  and per-catalog `information_schema` are privilege-filtered and SQL-queryable — a legitimate
  future ingest source, necessarily Internal-classified. Groom: probably no backlog item of its
  own; fold the citations into the acronym-catalog item and any data-catalog ADR that revisits
  glossary/tag enforcement.
  KEPT-UPDATED 2026-07-25 groom — **the first citation has been consumed**: ADR 0010 §4.2
  (`app_id` + `id_authority`, groomed as **S3**) applies the governed-namespace lesson inward —
  the value of a governed namespace is that *the identifier itself carries its authority*, which
  is exactly what `id_authority: "SEAL"` encodes. Still parked: the *tag-policy-as-enforcement*
  and *glossary-as-concept-scheme* citations, which wait on the acronym-catalog line below and
  on a data-catalog ADR that neither exists nor is scheduled. No item of its own — confirmed.
  (Correction 2026-07-27: `id_authority` was WITHDRAWN at the identity gate's §B0 sign-off —
  SEAL stays the single issuing registry, so the property encoded a fact that cannot vary. The
  governed-namespace citation stands; its worked example moved to the source-field ledger shape
  instead.)
- 2026-07-25 — [idea] **Acronym catalog scoped by domain — so agents and humans stop colliding
  on the same three letters (SME, chat).** Direct fallout of the Q6 reopen below: `Ais` cost
  real time because two readings are both plausible — "as-is" (the standard architecture
  modeling idiom) and "Application Integration Streaming" (an org platform family) — and
  nothing in the repo adjudicated between them. Today
  `config/taxonomy/software-registry.yaml#acronyms` is a one-key section with no scope
  dimension, so it can record *expansions* but not **collisions**, and collisions are the
  failure mode that actually bites. **Shape:** key by acronym, carry *many* senses, tag each
  sense with its domain scope — `area` (which part of the org/platform), `business-domain`,
  `technical-domain`, `industry` (what an outsider would assume it means) — plus, wherever a
  misreading is known to have happened, an explicit **does-NOT-mean** note. AIS is the worked
  example: industry/modeling sense "as-is", org sense "Application Integration Streaming", and
  the note that our `:AisTool` label meant neither. **Modeling hook:** this is a SKOS job
  (`prefLabel` / `altLabel` / `definition` / `scopeNote`, senses as concepts in a scheme) —
  SKOS is already registered in `reference/standards/README.md` (namespace + "concept
  reconciliation") but has **no fetched local copy** yet, unlike prov-o/w3c-org/dprod-ekgf/
  sosa-ssn; fetching it would be part of this. **Boundary caveat (decide at grooming):**
  industry acronyms are External and publishable, org-internal ones are not automatically —
  needs per-entry `classification` or an `internal/` split, same rule as any other source.
  **Consumers:** agents reading CLAUDE.md and gate prompts; L5/L6 SME review, where an
  unglossed acronym stalls a page; a whitepaper/website glossary. Groom **after** the Q6
  ruling — Q6 decides whether `#acronyms` survives at all, and this is the shape it would grow
  into if it does. (Note: "Q6" here is the **gate-log** question, not the backlog item Q6,
  which is the unrelated docmeta Port A.)
  KEPT-UPDATED 2026-07-25 groom — **independent corroboration from the pre-UI structure
  review**: its §4.2 arrives at the same home from a different direction, ruling that where
  "SEAL", "PAT" and "AIS" need to be *defined* rather than *encoded*, the carrier is a
  `CatalogBusinessTerm`-shaped glossary (`docs/patterns/data-catalog/enterprise-data-catalog-ontology.md`)
  — not a property, not a label. That is this line's shape, reached by the identity question
  instead of the collision question. Still parked on the same trigger (the gate-log Q6 ruling);
  what changed is that two threads now converge on it, so it is likelier to be worth building.
  KEPT-UPDATED 2026-07-27 groom: the landing zone now EXISTS as a backlog item — **G34**
  (raised at the identity-gate sign-off) reserves `CatalogBusinessTerm` + its three edges as
  `planned`, schema public / definitions internal, deliberately defining NO terms. When Q6 is
  ruled and this line grooms, it becomes content INSIDE G34's scaffold (senses, scopes,
  does-NOT-mean notes as SKOS), not a new home.
- 2026-07-25 — [question] **Q6 REOPENED: is the AIS acronym entry worth keeping at all?**
  (SME, chat). C12/Q6 ruled the expansion "Application Integration Streaming" survives as
  `config/taxonomy/software-registry.yaml#acronyms` — the durable "what did that name mean"
  home. The SME now reports the premise was wrong: they read `Ais` as **"as-is"**, never as
  an acronym, so the label was never a considered modeling choice on our side. The record
  corroborates — `761a201` (2026-07-09) introduced it as `:AiTool` (**no "s"**), attributed
  to in-chat direction and flagged "not yet defined in the ontology"; it stayed spelled two
  ways for twelve days across backlog/IDEAS/port-archive; the 2026-07-21 "correction" to
  `AisTool` matched the C11 screenshot rather than decoding it; the expansion landed only at
  Q6 that afternoon. **Counterweight (don't skip it):** their docs portal root
  `/docs/ais/{orchestration,etl,file-transfer}/` is independent corroboration that AIS is a
  real org term — two separate questions (is the acronym real? = yes / was `:AisTool` a
  considered choice? = no), and Q6 answered the first as if it settled the second.
  **Options:** (a) drop `#acronyms` entirely — `config/gate-log.md` already carries the
  expansion verbatim, append-only, so nothing is lost and a one-key config section created
  to hold a dead string goes away; (b) keep it but rewrite as a **disambiguation** —
  "does NOT mean 'as-is'" is the protective sentence, not the expansion, since as-is/to-be
  is a standard modeling idiom and that misreading imports a false meaning (and "Streaming"
  was already ruled a misnomer at Q6). Producer-side recommendation: (b), worded as
  disambiguation. **Hold DISCHARGED 2026-07-27:** the hold was that
  `docs/port-T12-ais-excision-company-prompt.md` step 2b deferred the acronym rather than
  sweeping it, so no company session could harden a ruling still under review. T12 has since
  ruled (SUPERSEDE, 2026-07-21) and the excision is applied company-side, so that prompt is
  spent and was retired from the tree — the acronym question is now free-standing and no
  longer gated by a pending session. Still open, still the SME's: groom when they rule — a
  Q6 amendment entry in `gate-log.md`, not a new gate.
- 2026-07-24 — [bug] **Unlocated user-reported typo: "apply-catalog … at the bottom says
  apply ontology" (chat).** Searched cli.py docstrings/messages, runbook .md/.html both revs,
  run-drydocs skill, RELATIONSHIP_GUIDE, repo-README, feedback html, gate docs — no such
  string exists. Best guess: startup-refresh runbook step 3 says "the three domain
  supplements" and Appendix B omits `apply-registry-supplement` while running
  `load-software-registry` — a genuine Rev 3 gap that should ride the L5/L6 SME feedback
  loop (doc is mid-review; do not hot-edit). Re-check with the user for the exact spot.
  KEPT-UPDATED 2026-07-25 groom: **G29** (the `apply-supplements` consolidation) rewrites the
  exact verb set Appendix B lists, so its acceptance carries a rider to fold this check into
  the runbook update — which resolves the best-guess half without hot-editing a doc that is
  mid-SME-review. The *unlocated* half still needs the user to point at the exact spot.
  KEPT-UPDATED 2026-07-26 (G29 done): the rider was executed and turned up a NEW, closer
  candidate — not in the runbook at all, but in `.claude/skills/run-drydocs/SKILL.md`, whose
  chain block annotated `apply-catalog-supplement` with `# Catalog **ontology**` (and listed
  catalog BEFORE seal, which is the wrong order). "apply-catalog … says … ontology" is a
  fair description of that line. Both are now fixed — the block is one `apply-supplements`
  call and the order is enforced in code. Offered as the likely origin, NOT declared closed:
  if the user meant somewhere else, the report is still open. The runbook itself stays
  untouched and its three owed edits are the separate 2026-07-26 [doc] entry above.
- 2026-07-24 — [chore] **T11 L7-ratification paste-ready snippet still owed producer-side**
  (noted while confirming PORT-REPORT-73ee97a; the company gate pack references it).
- 2026-07-23 — [idea] **Oracle connection for the lineage/remediation path (user note,
  chat pm).** The lineage jobs step still stages a CSV by hand through a JDBC client;
  the Oracle connection is planned — and the user's note ties it to the REMEDIATION
  context ("switch to the remediation since this last update was related"). Candidate
  shape: a direct pull of the `controlm_jobs.sql` projection (the same file
  `ingest-controlm --use-oracle` runs — runbook Rev 2 records the equivalence) plus
  the remediation-side staging reads (STG_APP_FACT-family fact tables per the
  company-side greenfield docs). Clarify scope with the SME before building.
- 2026-07-23 — [source] **Company-side greenfield remediation standards not yet
  producer-modeled.** Two docs live in the company `drydocs_remediation` path (seen in
  review 2026-07-23): (1) the Control-M file-name component standard — FileName
  decomposed into FilePrefix / FileBusinessDate / FileSequence / FileExtension /
  FileCompression / FileSuffix + the FilePattern FileWatcher glob, DistributionRole
  derived from extension, a `CM_JOB_FILE_NAME_STANDARD` Oracle column standard, and
  dcat:Distribution ontology mappings; (2) the cmd-job ontology variable mapping
  (`%%ETL_PLATFORM`, `%%LAUNCHER_SCRIPT_PATH`, `%%ETL_ARTIFACT_URI`… →
  STG_APP_FACT fact_type → :Script nodes / INVOKES / USES_ARTIFACT). Producer-side
  `drydocs_remediation` models FileWatcher (`job_type`, `watch_template`, resolved-watch
  equivalence) and job variables (ordered defs, scope chain, canonical rename,
  dot-smuggling detect, corroborate) GENERICALLY — but has no filename-component
  standard and `transform.py` still notes the canonical variable map is "a company-side
  ratified value". Candidate: bring both docs in as the ratified maps when the
  remediation M2 generalization opens (FR-REM-5's schedule/command/conditions slice).
- 2026-07-23 — [chore] **Delete the rollback container** `neo4j-drydocs-ee` (stopped,
  restart=no) + its two anonymous volumes once `neo4jtest` has survived a week of normal
  use (week is up ~2026-07-30); also prune orphan volumes neo4j_data/neo4j_logs/
  neo4j2_data/neo4j2_logs (attached to nothing; likely relics of pre-2026-07-02
  containers — verify before pruning). The first-attempt community container `DryDocs`
  was deleted 2026-07-23 (user-confirmed). MERGED IN 2026-07-28: the 2026-07-03 chore
  about this same container's password being the literal string `<password>` — deleting
  the container retires that too (the live `neo4jtest` has a real password), so no
  separate action.
- 2026-07-22 — [idea] **PDN trigger design: milestone/SLA grain + graph-computed slack,
  not per-job failure mail (SME, chat pm).** Current state: dev teams default ON/DO-MAIL
  + SHOUT to L2-on-failure → hundreds of ignored mails daily (alert fatigue — the
  motivating stat for the notification model). SME ruling direction: a failure must NOT
  trigger a PDN (potential delay notification) by itself; the trigger belongs at the END
  of the work stream with remaining recovery time calculated. Options mapped: (1)
  vendor-native = Control-M SLA Management / BIM job type at stream end — deadline-aware,
  projects completion from averages, alerts only on projected breach [MODEL KNOWLEDGE,
  not in corpus; licensed add-on — add "is BIM installed?" to the OQ-1-style company
  probe list]; (2) no-license fallback = terminal Dummy milestone job + time-based SHOUT
  WHEN-lateness variants instead of ON-NOTOK [SHOUT corpus-grounded via ctmdefine; the
  WHEN variants need verification]; (3) Confirm attribute = manual-approval GATE
  (corpus-grounded), not a notifier — usable as a HITL pause at recovery-decision
  points, wrong tool at stream end; (4) fatigue fix independent of all: demote
  failure-mail to MAXRERUN-exhausted only. DryDocs' role: the TRUE trigger condition is
  deadline − (now + remaining critical-path runtime) < 0 — the CPM-not-path-sum ruling
  from the cm_avg_run gate + calendar-projection plan; graph decides, milestone job
  delivers, DL from the email-dl-contact-point NOTIFIES mapping receives. Feeds: the DL
  gate B2 grain question (stream/milestone grain confirms folder-preference), the
  runbook module ETA logic, and the company-side probe list.
  KEPT-UPDATED 2026-07-23 (SME, chat): the BIM install probe is ANSWERED — one
  production SLA/BIM job exists (SEAL 90489) — but it fires near-DAILY and is ignored:
  mechanism right, calibration wrong. Cause candidates (distinguishable): (1) deadline
  tighter than the stream's actual completion distribution [most common]; (2) stale/
  unrepresentative averages after the chain changed shape; (3) alert scope includes
  per-job failures, re-inheriting the noise it was meant to replace; (4) stream is
  genuinely chronically at-risk but the alert carries no slack/recovery content, so
  it's untriageable. DryDocs diagnostic play (once cm_avg_run + calendar projection
  land): take the 90489 BIM service's job membership, compute observed critical-path
  completion distribution, compare to the configured deadline → move deadline /
  refresh scope / re-engineer. Same slack computation that gates a PDN also VALIDATES
  whether a deadline is honest — deadline-calibration audit = a runbook/notification
  module feature, and the worked example for it. Principle for the notification model
  (gate-worthy): an alert channel earns attention only with a low base rate AND
  actionable content (remaining slack + recovery action) — any mechanism without
  calibrated thresholds degrades to ignored noise.
- 2026-07-22 — [idea] *(KEPT-UPDATED 2026-07-26: distinct from **Q10**, the email BODY as a
  document corpus. This entry is about DL MEMBERSHIP as an ontology mapping — the two touch
  the same source and must not be merged.)* **Email DLs need an ontology mapping (user, chat pm).** DL = the
  contact/notification channel for an app/team; only configured in Outlook (no feed,
  can't fix), witnessed in runbooks, extractable from emails; membership/usage are
  context-graph (layer 4) material. DRAFTED STRAIGHT TO GATE same session: gate prompt
  `config/gate-prompts/email-dl-contact-point.yaml` (class options vcard:Group vs
  prov:Agent; HAS_CONTACT_POINT dcat:contactPoint edge; store-as-source per the O24
  pattern; extraction-proposes-steward-disposes; layer-4 membership boundary) + map
  entry `dl-contact-point` (proposed). Grooming disposition: tracked at the gate —
  build items groomed on sign-off; nothing further parked here.
  AMENDED same day (SME follow-up, chat): the downstream-notification AUTHORING
  landscape added as gate section C — greenfield intent was the job Description
  field; better candidate = escalation DB special-instructions VARCHAR2(4000) in
  psgmgr (EJOBNAME/ECOMPONENT joins, support-editable = fixable source →
  override-until-fixed, not store-as-source, for the NOTIFIES leg); de facto truth =
  runbooks / Jira sign-offs / email threads (brownfield bootstrap, rejected as end
  state). C2 keyed convention must SHARE the description-metadata plan's template
  phase (two 4000-char conventions must not fork).
- 2026-07-22 — [idea] **The tie we need now: Control-M → SEAL batch :Port attribution as a
  DEFINED mapping, keyed by the Control-M APP CODE (:ControlMApplication), persisted via
  the mapping store (steward persona — NOT new UI).** SME model (2026-07-22, refined in
  session):
  (a) Grain correction — attribution was NEVER meant to be job-level; the graph grain is
  **folder → batch :Port** (jobs inherit via CONTAINS_JOB). Corrects the active
  `m3_seal_app_ref` (ControlMJob → :BusinessApplication, seal_attribution.py live).
  (b) The mapping should have been DEFINED, not matched: the authoring key is the
  **Control-M app code** — the :ControlMApplication folder-header grouping (which
  CONTAINS_FOLDER already ties to folders, so folder edges derive from the app-code row).
  Two tiers:
  **Tier 1 — seal-born app code (1:1):** the code was created FOR a SEAL → direct
  app-code→SEAL mapping. Declared examples: ARA=70002 (CMH Advice R&A), SRV=70003
  (HL Servicing R&A). Easy to define; enumerate these first.
  **Tier 2 — platform app code (1:many):** the code is a shared platform, mapping to
  MANY AreaProducts, not one SEAL — e.g. DPL= ?? (enumeration OPEN, SME to supply).
  Note: AreaProduct has ZERO rows in the sample taxonomy (lob-product-team.yaml OQ
  `area-product-missing`) — tier 2 makes that layer load-bearing; the OQs converge.
  Gate impact: the still-open K4 edge-shape follow-up gate owns target (app node vs
  BatchProcessing :Port), from_node (job → folder, derived from app-code), the
  defined-mapping tiers (seal-born vs platform), and migration of K2-written job edges.
  The K2 fuzzy match policy (SEAL > FID > APP_NAME > ALIAS) demotes to fallback for
  codes with no defined row; tier-5 manual pins unchanged. Conflict rule: a folder whose
  app code is tier-2/unresolved surfaces to the steward — never auto-picked.
  Mechanism after the gate: register the app-code→SEAL(:Port) and app-code→AreaProduct
  edges (matrix rows for Collection→Entity — Activity→Agent WAS_ASSOCIATED_WITH no
  longer fits), new mapping-store domain (app-code-keyed table replacing/demoting
  `job-application`; update K2_SHAPE in drydocs_api/mappings.py), rekey the
  manual-loads template, migrate live edges. Bonus once this + `batch_orchestrator`
  (C14) both exist: folder-mapped-to-ControlM vs app-declared Autosys becomes a
  conformance check.
  **Property-diet rider (SME, same session):** the naming-convention decode must come
  OFF :ControlMFolder node properties. Convention (folder_name.py, confirmed):
  pos1=env, pos2=lob, pos3-5=app_code, pos6=folder_type — so job application=PRSRV =
  P(rod)+R(etail)+SRV, the prefixed form of the folder's bare app_code=SRV. SME:
  `lob=Retail` / `lob_code=R` are artifacts of the Control-M app-code naming convention
  and as node properties they CONFUSE users — f.lob='Retail' collides with the org-
  taxonomy LOB (business-application.yaml `lob: CCB`), same word, different taxonomy.
  Today controlm_folders.cypher:66-72 stamps environment*/lob*/app_code/folder_type* on
  every folder. SME 2026-07-22: the docstring rationale "filter by environment, LOB, or
  appcode without re-parsing" was likely UNINTENTIONAL, not a decision — and it fails on
  all three counts: (1) ENV truth is the **data_center prefix** (:ControlMServer name),
  NOT folder-name pos-1 — this rule is in NO document yet (verified: all data_center doc
  hits are staging-key mechanics) → gate must land it in the concept-mapping doc;
  (2) LOB decode has ONE real value (LOB_CODE_MAP: R=Retail; Y/K/B are provisional
  placeholders per the code comments) — a name wildcard gives the same filter, and users
  don't know the codes anyway; (3) the real access pattern is a **ROLLUP** (inventory
  aggregated up folder → app-code → SEAL/AreaProduct via containment + defined mapping),
  not a property filter. Direction: decode lives ONCE in the app-code registry /
  defined-mapping rows; the node keeps sched_table raw (+ likely app_code as the join
  key — confirm at gate; with the filter rationale dead, environment/folder_type decode
  props presumably go too, env prop being actively misleading vs the data_center rule).
  Mechanics: loader + cypher edit, property-retirement migration per the M2 doc-06
  Phase 3 raw-prop pattern; parsed fields are inside row_checksum, so expect a one-time
  delta-churn on the next run (M2 precedent handled the same).
  KEPT-UPDATED 2026-07-22 pm (user: "close out the mapping"): the gate this item names
  is now REVISED to carry it — `config/gate-prompts/seal-app-ref-edge-reshape.yaml` v2
  (sections A grain / B app-code tiers / C target incl. :Batch-bridge retirement /
  D shape / E steward-override-until-fixed / F migration) + map entry
  `app-code-defined-mapping` (proposed, taxonomy-ontology-map.yaml). What stays parked
  HERE: only the tier-2 platform-code enumeration (SME to supply).
  **RESOLVED 2026-07-23 (property-diet rider):** SME ruled in-session — the naming
  convention is the internal Control-M app-code definition; do NOT expand it onto nodes.
  environment*/lob*/folder_type* retired from controlm_folders loader+cypher; app_code
  KEPT (join key for app-code → BusinessApplication mapping). No migration —
  wipe-and-rebuild. Ruling recorded in config/gate-log.md (2026-07-23 folder property
  diet); the app-code → SEAL mapping itself still belongs to the open
  seal-app-ref-edge-reshape v2 gate.

- 2026-07-22 — [idea] **Env toggle = one canonical node identity, never per-env node
  identities.** When the header env toggle [Prod|UAT|Dev] gets built, it must re-scope
  DATA under one canonical node, not split identities (`job-dev`/`job-prod`
  anti-pattern). (Backstage assessment T8, UI-WIP/backstage-catalog-assessment.md §3;
  design constraint for the shell — attach to the env-toggle item when one exists.)

- 2026-07-22 — [chore] **Company adoption: route the XML run's WARN flood through the new
  loader run logs (next port).** Producer BUILT the generalized run-log family same day
  (user directive after the first company XML run flooded the console with per-row
  `description_tokens` WARNINGs): `drydocs_core/run_log.py` + `BaseLoader` wiring —
  configurable path (`DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` fallback → `~/logs/DryDocs`),
  shared naming (`load.<loader>.<stamp>.log`), header/meta from the process, WARN-stream
  tee + uncapped reject detail, summary footer, best-effort contract. When ported,
  company-side should ALSO (a) attach the tee in the XML *extractor* stage (the
  description_tokens flood happens pre-loader, in the adapter), and (b) consider raising
  the console handler to WARNING-summary-only once the stream lands in the file — the
  file is the review surface, the console shows counts.

- 2026-07-22 — [idea] **Control-M compact-timestamp normalization (mechanism, from the
  company XML-loader's second timestamp bug).** Control-M XML exports carry compact
  timestamps `yyyyMMddHHmmss` + literal `UTC` suffix (invented example: `20250101093000UTC`);
  fed raw into Cypher `datetime()` they throw `CypherSyntaxError` — not ISO 8601, and
  `UTC` is not a valid zone designator (`Z`/`+00:00`). Fix mechanism when the XML loader
  back-flows (and for any future producer temporal field): (1) normalize in PYTHON at the
  row-model layer (the C3 "Python owns normalization" precedent) — one canonical
  `parse_controlm_timestamp()` pydantic validator emitting tz-aware `datetime`, driver
  converts natively, `datetime()` string-parsing never appears in Cypher; (2) two bugs in
  the same family = scattered parsing, consolidate + unit-test the compact-UTC, date-only,
  and empty forms; (3) unparseable value → row to `rows_rejected` + WARN (G16
  values-decide pattern), never a batch abort at `_flush`. **FIXED company-side same day
  (as-built mechanism, supersedes the proposal above for back-flow):** a `_ts()`
  normalizer in the XML extractor emits the ISO *string* the loaders' existing Cypher
  `datetime(replace(x, ' ', 'T'))` contract expects (one temporal contract shared with
  the Oracle path — better than forking to native datetimes); zone token `UTC`/`Z` → `Z`,
  numeric offsets kept; 8-digit date-only → midnight; empty/None → None so the null-guard
  drops the row (fixes the batch abort). Residual gaps flagged to the company agent:
  unknown non-compact forms pass through to `datetime()` (docstring claims None) and 14
  valid digits aren't validated as a real date (`strptime` beats `isdigit`+len) — carry
  both hardenings into the back-flowed version.

- 2026-07-21 — [chore] **Next cross-repo port: carry the AIS acronym expansion across
  files.** Producer's authoritative home is `software-registry.yaml#acronyms`; the company's
  PROVISIONAL gloss sits on their `source-registry.yaml` docs-source entry with a
  PORT-MANIFEST canonical-producer row expecting the producer expansion at next cherrypick —
  different files, so the port must transplant the value, not same-file overwrite. Also
  still open company-side: no 06-29 gate-log entry (their audit gap; backfill offered).

- 2026-07-21 — [idea] **ControlMApplication code → BusinessApplication mapping: the
  two-pattern model (SME, chat)**. SME states the code layer maps two ways: (1) some
  BusinessApplications own a DEDICATED Control-M app code → can map DIRECTLY
  (code→app 1:1); (2) some share a PLATFORM code (e.g. the DPL pipeline-launcher
  spine; cloud-ETL platform codes) → one code carries many apps, resolvable only
  per-folder/job or via the manual mapping table. Shipped today READ-ONLY as
  `explorer.controlm-app-codes.v1` (pattern DERIVED from observed cardinality over the
  gated seal_app_ref edges — no new edge invented). The GATE DECISION still open: an
  authoritative `(:ControlMApplication)-[:?]->(:BusinessApplication)` mapping edge for
  the dedicated-code pattern + a platform-code marker for shared codes — routes through
  relationship_vocabulary + HITL; feeds and is fed by the K2 tier model (a confirmed
  dedicated code is evidence ABOVE manual tier 5) and the O13 "code->application joins
  the domain strip when that mapping table exists as a reconciler input" hook (this is
  that table). Also touches plan-07 P3 invocation-pattern rows (AT GATE). SME also
  flagged: the Folders/App-codes frames are the power-user/SME mapping surface needed
  SOONEST → prioritize O13's /mappings React screen accordingly. KEPT-UPDATED at the
  2026-07-21 pm groom: O13 shipped same day (0dc2831) — the prioritization ask is
  satisfied; what stays parked here is the GATE DECISION core (the authoritative
  code→app mapping edge + platform-code marker), trigger = the SME convening that
  mapping gate / the K2 tier model's next touch.

- 2026-07-21 — [idea] **m7 build follow-up** (from gate `cmdline-nfr-vetting`): migrate
  payload invocations out of the m3_invokes 1..n fold onto the registered `USES_ARTIFACT`
  edge + stamp `script_role` {launcher, payload} and the artifact_* properties on :Script.
  Feed now EXISTS (G16 value-contract facts + G15 launcher properties); groom once the
  writer's ETLProcess endpoint work makes the edge landable — the vocab entry
  `m7_uses_artifact` stays `planned` until that build's own flip.

- 2026-07-21 — [idea] **Public marketing-site brand kit** captured in
  `UI-WIP/WEBSITE-IDEAS.MD` (3 logo directions incl. the core+orbit modernization, secondary
  palette, hero/feature/architecture landing structure). This is the PUBLIC SITE
  (website-and-backstory workstream, 'overnight ledger' editorial identity — site not
  started, domain unresolved), NOT the console — deliberately left out of the 2026-07-21
  Epic O extension groom. Groom when the public site starts; the icon/logo direction
  should stay consistent with the O22 console glyph set.

- 2026-07-21 — [idea] **FW-really-API confirmed live** — the greenfield-provenance use case
  for the fix module: a file-watcher-shaped job's `.tok` is produced by an UPSTREAM API-call
  job writing the file locally, no external push exists — the name/type lies. Already
  codified as the `_FW`-really-API anti-pattern + design principle 8 (intent from resolved
  flow, flag name-token disagreement) in
  `internal/remediation/governance/nfr-consistency-and-greenfield.md`; the description-field
  metadata plan is the declared-provenance carrier. Two NEW provenance gap classes from the
  live case: (a) payload script deployed on the exec host but ABSENT from SCM (code search
  finds only the XML variable reference) → *artifact-not-in-SCM* flag on :Script; (b)
  pipeline-id-keyed code discovery has NO key for non-DPL python jobs → PATH-keyed Script
  identity is the fallback, and the GUID-vs-path boundary is the kind discriminator.
- 2026-07-21 — [source] **DPL ingestion leg + AWS zone model traced** (company ingestion
  template; mechanism-only — values stay company-side). Upstream of the launcher spine:
  FM drop of a `.dat` + `.tok` landing pair → Control-M file-watcher condition grammar
  (`TOK-IN-COND…` / `FW_DAT#DAT-IN-COND…`, FW-OK-on-FAIL) → a **separate
  `ingestion-launcher` jar** publishes to S3 RAW via HTTP-PUT publish API (dataset
  identity = GUID + version, zone-scoped publish role) → **each zone hop
  RAW→TRUSTED→REFINED is its own DPL pipeline** (own `--pipeline-id`) → PROVISIONING
  DB-load lands the consumption target (Provisioned ≠ an S3 prefix). One bucket with
  zone prefixes; per-zone Glue databases + tables (partition keys at onboarding,
  `--odate` = partition value). Legacy `dataset_flow.json` FILE→CONFORMED ≈ the
  RAW→TRUSTED hop. UPDATE same day (prod CMD_LINE samples): the ingestion TRIGGER jobs
  use the SAME dt-launcher.sh (`-i` mode) — that grammar merged into G15. Still open
  here: (a) the template's `ingestion-launcher*.jar` was NOT observed in any sampled
  CMD_LINE (placement jobs?) — classifier entry waits on a real sample; (b) ~~DataAsset
  zone/glue-table shapes for the MAC enrichment feed~~ RESOLVED at the G17 build
  (same day): candidate shape = `dpl_dataset` DataAsset keyed by dataset GUID
  alone, version/zone/name as PROPERTIES (glue db/table can join later as more
  properties); version-as-identity deferred to G22 clause f; (c) Pre/Post-execution command fields carry mv/backup file ops
  (parquet + .tok → backup) — a G14-shaped surface G14 doesn't read (it parses
  CMD_LINE only); (d) cross-job `%%\\JOB\VAR` runtime threading (run GUIDs, record
  counts passed between jobs) — context-graph flavored, definition-level no-op.

- 2026-07-21 — [idea] **Back-flow the company's un-back-flowed advances (bd7952f follow-up 3).**
  The 2026-07-20 bundle port went bidirectional (+288 producer / +148 company) precisely
  because these never came back; reproduce mechanism-only via the screenshot/describe
  channel: snow-support schema supplements (`hpsm_queue_key`/`sn_group_name` constraint
  pair + a `snow-snowflake-itsm` source stub), the `drydocs_remediation` DPL-watch-drift
  rule + tests (pairs with the DPL runtime-trace inbox entry below), the `graph_verify`
  Assertion refactor, the docgen deviations vs the finalized company TDD, the
  `CONFLUENCE_BASE_URL` config seam (mechanism: base-URL as config; the value stays
  company-side), and the `controlm_folders.sql` `J` table alias. Ties into the
  drydocs-review back-flow epic. Until these land, every future port repeats the
  squash-reconcile instead of a clean linear apply.

- 2026-07-21 — [chore] **Company-side heads-ups from the port-report gap review** (their
  tracker — recorded here so they aren't lost; relay next company session): (a) the
  `test_schema_graph.py` drift-guard sequencing conflict — see the new reconcile-port
  skill ledger note (re-add only after their doc-vocab gate); (b) confirm
  `docs/restructure/internal-backlog.yaml` was deleted after the DD-series merge
  (bd7952f follow-up 2 — 388a30d shows the merge happened, not the deletion); (c) the
  company is producer commits behind past `7e8df54` (L7 gate sign-off + live loader,
  G14 lineage file-ops pass, the hermetic oracle-kerberos test fix that retires the
  standing known-failure note, DPL inbox, port-gap fixes) — **and their tooling can't
  see it**: the 07-21 company-side "identify unported commits" search concluded "fully
  ported, nothing outstanding" from a FROZEN `cewilson/main` ref (`git fetch cewilson`
  404s company-side; likely the stale pre-rename remote URL — the live repo is
  `https://github.com/ce-wilson/DryDocs.git`, pushed 07-21). First company action:
  `git remote set-url` + re-auth, re-fetch, then re-run their own re-verify
  (`git log <last-ported>..cewilson/main`). Silver lining from that search: the L7
  port branch IS merged to company main (`373e993`→`c8cf9f0`), closing the
  "NOT merged" state in 5eba0c3, and the historical port reports (0eb1a8d, aa049d3,
  e6f8cca, e418258, eeaffa2, f7970e5) all exist as files company-side.

- 2026-07-20 — [chore] **Post-squash ref cleanup (user decision, destructive)**: origin still
  carries two pre-squash-history branches — `feat/mapping-store` (SUPERSEDED: the Initial-import
  squash absorbed its content and main then evolved past it; its only unique file was the
  regenerable web-console `.print.html`, since retired by L13) and
  `feature/provenance-audit-fields-plan` (status unreviewed). Local relics on the producer
  machine: branch `backup/ui-dark-local-3`, the stale stash noted at the 07-20 groom, and the
  new safety tag `archive/old-history-2026-07-20` (this machine's pre-squash history; the other
  machine has `archive/full-history`). Deleting the remote branches is the user's call.

- 2026-07-20 — [doc] Runbook Rev 3 candidate: mention `drydocs load-doc-traceability` in the
  Refresh/ingest demonstrable-content step (L7 shipped the loader after Rev 2 was signed —
  ride the next feedback loop rather than bumping a fresh Rev for one line).
- 2026-07-20 — [chore] **USER MANUAL STEP: add the SNYK_TOKEN repo secret** so the new CI
  snyk job (44523ab) runs for real — token from app.snyk.io (Account settings → API
  token) → repo Settings → Secrets and variables → Actions. Until then every scan step
  skips cleanly by design. After the first green scan: triage `snyk code` advisory
  findings and decide whether to gate it (the ruff-idiom follow-up).

- 2026-07-20 — [idea] **Replace SEAL/PAT naming with industry-standard, SaaS-configurable
  terminology** (user request; web research DONE same day →
  `knowledge/upgrade-plans/generic-terminology-research.md`). Candidates validated:
  SEAL → **Application Portfolio** holding **Business Application**s (ServiceNow
  CSDM/APM — our K4 node label independently confirmed); PAT → **Product Taxonomy** /
  **Product Portfolio** (product-operating-model literature; AreaProduct is the least
  standard term). Mechanism = the Salesforce "Rename Tabs and Labels" pattern: canonical
  concept ids stay generic and stable, tenant display/source names become config
  (source-registry `display_name` fields; O12/O13 console surfaces render them).
  PARKED pending user decisions recorded in the note's §Decision surface: (1) scope —
  display-label config only vs also renaming `seal_*` vocab ids/domains (ADR-scale, the
  ADR 0004 precedent); (2) placement — productization has NO epic/phase, so promoting
  this is a PLAN CHANGE (new epic proposal → user); (3) `SEALID` → generic identity
  property (gate discipline). Related: [[SaaS scaffold research line — the
  template-play/whitespace finding, 2026-07-17]].
  KEPT-UPDATED 2026-07-20 groom: **C10 landed same day** (ServiceNow CMDB/CSDM doc-set
  mined, 54ccf63) — the CSDM service/service-offering layer this line called its missing
  piece is now in reference/. The decision surface is fully fed; still PARKED on the three
  §Decision user calls above (scope / placement-as-plan-change / SEALID property).
  KEPT-UPDATED 2026-07-27 groom: **§Decision item 3 is RESOLVED** — the
  business-application-identity gate (SIGNED OFF 2026-07-27) ruled `SEALID` → generic
  `app_id` on the canonical node, with the per-source field-name ledger
  (`config/source-mappings/seal-extract.yaml`) carrying what each source CALLS it; build = S3.
  Decisions 1 (display-label scope) and 2 (placement/plan-change) remain the parked user calls.

- 2026-07-19 — [idea] **depgraph metric extensions (codeflow takeaways — ideas, not code)**:
  compute codeflow's three genuinely useful metrics ON TOP of our existing ast-accurate
  graph, in the depgraph sibling repo (stdlib, deterministic, rides the snapshot JSON,
  flows into Neo4j at Fork 3): (1) **blast radius** — reverse transitive reachability per
  file ("what breaks if this changes"; the same what-depends-on-it question DryDocs asks
  of batch jobs, turned inward); (2) **dead-file candidates** — zero inbound edges and not
  an entrypoint; (3) **coupling/health trend** — fan-in/fan-out per file plus a metric-delta
  summary across the committed snapshot series (codeflow's card-history pattern, free from
  our existing time series). Deep-dive verdict 2026-07-19: codeflow itself REJECTED as a
  ritual component (browser-only app, regex-heuristic edges vs our ast, Node-vm headless
  hack, no Neo4j path) — take the ideas only.

- 2026-07-18 — [idea] **ETL-tooling inventory as a DryDocs domain** (re-inboxed slim from the
  groomed mapping-store line): a gap no catalog covers — DataHub/OpenMetadata inventory data
  assets, not the tooling estate. DryDocs should own it. Context in the mapping-store plan §5
  (internal DataHub adoption).

- 2026-07-18 — [idea] JobRun.started_at/status indexes (GraphAcademy advisor residual) — fold
  into the provenance-audit-fields plan (docs 06/06a) at its next touch, not standalone.

- 2026-07-17 — [idea] **SaaS knowledge-graph scaffold research (chat)**: no drop-in template exists
  for what DryDocs is. Candidates assessed: Neo4j Labs `create-context-graph` (Apache-2.0 scaffolder,
  FastAPI+Next.js+Chakra — stack mismatch vs ReUI decision, auto-extract-by-default = anti-HITL, no
  lineage/batch-job domains → pattern quarry only: its "one domain YAML drives the whole generated
  app" validates our registry-driven module/QuerySpec design); OpenMetadata (real HITL prior art —
  draft→reviewer→approve glossary/governance workflows — but deliberately NO graph DB, would replace
  the Neo4j core, no Control-M connector); DataHub (Neo4j-backed graph layer architecturally closest,
  but Kafka+ES+MySQL+Neo4j footprint, approval flows largely Cloud-tier, no Control-M). Whitespace
  confirmed: Control-M/batch-orchestration knowledge graph + HITL-gated ontology is uncovered — keep
  building; future options = "publish to catalog" export target (OpenMetadata/DataHub ingestion APIs,
  fits QuerySpec export) and DryDocs-as-template play à la create-context-graph ("pick your
  orchestrator, get a scaffolded support graph") for the standalone-generalization goal.

- 2026-07-14 — [source] **K2 FID / ALIAS reconciliation tables are company-side unblocks.**
  The attribution loader's TierReconcilers seam ships empty for FID and ALIAS (facts stay
  unresolved, counted in coverage) — tier 2 needs a FID -> seal_id source and tier 4 an
  alias table before those tiers resolve anything. APP_NAME reconciles today from the
  loaded SEAL reference (exact normalized match; ambiguous names excluded).
  CANDIDATE SOURCE added 2026-07-16 (cmdline-lineage-review side finding): FID + SEAL
  are co-located in Control-M FOLDER VARIABLES (env-suffixed FID_D/Q/P alongside a SEAL
  value; the SEAL is also embedded in folder names) — a FID→seal_id pairing may be
  derivable from the already-ingested variables, not only from company tables.

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
  benchmark verdict (**landing zone since 2026-07-16: phase 14 / Epic Q** — created at the
  Essential-GraphRAG groom). **TRIGGER FIRED 2026-07-16 pm: the P0 WRITTEN verdict landed**
  (knowledge/upgrade-plans/docmeta-p0-verdict.md, Q3 — recommendation: BUILD) → **P1–P3 are
  now groomable into Epic Q at the next groom**; the docmeta ADR is the P1 gate output — **number correction 2026-07-16**:
  the plan reserved "ADR 0004" (2026-07-06) but 0004 was minted the next day for the
  software-registry terminology ADR (accepted 2026-07-07); the docmeta ADR takes the next
  free number at authoring (plan doc's 3 refs annotated same day). The four T1–T4 tier lines were folded
  INTO this sequenced plan (P0→P7) and moved to the audit trail (2026-07-09). P0's corpus
  load is already substantially executed: the bmc-docs lexical loader (Document→Chunk,
  llm-graph-builder pattern) shipped and gate `bmc-docs-lexical-load` was ACCEPTED 13/13,
  LOADED LIVE (commits 12423f4/24d6a4b) — the WRITTEN benchmark verdict (traversal vs
  manifest-routed markdown vs vector RAG) + the docmeta ADR still remain before P1–P3 promote.
  **GROOMED 2026-07-18: P1–P3 promoted → Q4 (gate + ADR) / Q5 (registry ledger) / Q6 (Port A;
  module drydocs-docmeta registered as working name — final at the Q4 gate).** P4–P7 stay
  plan-tracked until Q4–Q6 land. NEW RIDER (GraphAcademy advisor, 2026-07-17): when the docmeta
  loaders land, add existence constraints on `Document.trust_default` / `Chunk.tier_rule`
  (silent null = provenance undercount).
- 2026-07-03 — [chore] `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.

## Recently groomed (audit trail)

- 2026-07-28 evening — [bug] rua_inventory silent scripts drop on metadata-only scripts.csv
  bundles (company fixed theirs same day; producer parity, mechanism-only) → **G45**.
- 2026-07-28 evening — [question] constraints.cypher "deprecated by K4 — kept for old graphs"
  comment under-scoped (role/membership keys are live catalog writes) → **C20**.
- 2026-07-28 evening — [chore] enforcement-matrix render must ride the one entry point (the
  stale-render check caught the 49667dd drift live; the J17 defect shape, second surface) → **J20**.
- 2026-07-28 evening — [idea] agent-runtime target-state follow-ups (ADR 0007 revisit check
  PASSED; detail in internal/agent-platform/) → **R10** (google-adk pin + ADR date-stamp);
  caller-identity slot MERGED into **R3**'s acceptance. The target-state prose itself lives in
  the internal review + the R-item acceptances now.
- 2026-07-28 pm — [question] "do we have ONE document with the loaders and order, commands,
  source→target mapping?" → answered NO, then scoped and groomed as **N3–N6** (Epic N,
  phase 11). It is split today across `internal/repo-README.md` (CLI reference + Control-M
  run order), the startup/refresh runbook (operational chain),
  `04-sme-checklist-and-load-plan.md` (sequential plan) and `config/source-mappings/*.yaml`
  (column ledgers). Built as a RENDER, not a fourth hand-written doc — hand-authoring it
  would create exactly the drift this session fixed twice (the depgraph README's stale scan
  roots, `provision.ps1`'s stale `docker run`). The blocker found while scoping: loaders
  declare `name` and `source_label` but NO source-registry id, so loader→source→column-ledger
  cannot be traversed at all — that is N3, and it has value even if N4–N6 never ship.
  No inbox line preceded this; the question arrived in chat and is recorded here for the trail.
- 2026-07-28 pm (post-UI-merge pass) — [bug] snapshot instrument unpinned (fd2834d) → **U7**
  (revision pin + capability probe); the sibling-repo depgraph fork merge stays inboxed as a
  [question] — user's call, different repo.
- 2026-07-28 pm — [bug] snapshot abs_path machine/worktree-dependent (twice ritual-blocking) → **U8**.
- 2026-07-28 pm — [idea] SME landing feedback FB-01/FB-02 + WF-LND wireframes → **O35** (p2 —
  direct SME feedback).
- 2026-07-28 pm — [bug] loads timeline rail dot clips first character → **O36**.
- 2026-07-28 pm — [idea] DataLens continuity DL-5/6/8 → **O37** (radius tokens), **O38**
  (IdChip convention), **O39** (deep-link slot, depends O38). DL-1/2/3/4/9 shipped pre-groom
  on `feat/datalens-quickwins`; DL-7 was a groom-MERGE into O32's notes, executed on-branch
  (`bc61408`) — counted as this pass's 1 merge.
- 2026-07-28 pm — [idea] DSI review DL-10/11/12 → **O40** (StatTiles click-to-filter), DL-11(a)
  folded into **O38**, DL-11(b) → **B5** (stage taxonomy capture, SME gate for the canonical
  set), **O41** (status-vocabulary map). The Epic R precedent note stays with the R1/ADR-0007
  gate materials in `continuity.md` — gate-session input, not a backlog item.
- 2026-07-28 pm — [idea] agent graph-navigation surface (live-benchmarked) → **R9** (read-only
  query command over the O33-guarded specs; MCP recorded as the later option).
- 2026-07-28 pm — [idea] VERIFIED-LIVE claims don't name their machine → **J18**.
- 2026-07-28 pm — [idea] two sessions built C19 concurrently; pushed-claim wording → **J19**.
- 2026-07-28 pm — [chore] misnamed Copy-feedback export (RESOLVED same day — deleted, user's
  call; it was rev1 YAML content under an .html name, both notes already applied in Rev 2;
  the deletion produced no diff and this trail line is the record it existed) → latent gap
  promoted as **L20** (feedback/ stray-file findings guard).
- 2026-07-28 pm — [doc] startup-runbook three held edits (2026-07-26 line): hold lifted (the
  SME review closed); edit 3 (container facts) landed via **L16** Rev 3; edits 1+2 (supplement
  verb collapse + Appendix B registry gap) → **L21** as one Rev 4.
- 2026-07-28 — [source] Snowflake data-catalog (dataset/distribution) loader plan → **G42**
  (source registration + taxonomy-first extractor), **G43** (cross-check reports),
  **G44** (gate prompt + proposed ontology entries; the dcat one-node-or-two ruling
  rides the gate). Epic-close-out groom run; the plan doc is the mapping ledger.
- 2026-07-28 — [bug] Component-cell comma-split shears parenthetical refs (U3) → **L18**.
- 2026-07-28 — [doc]×3 U3-census doc-drift lines (pre-squash citation sweep + sdlc §DEP
  tables + fan-in hotspot citation gap) consolidated → **L19** (one sweep, one review).
- 2026-07-28 — [bug] bootstrap "Constraints applied." with zero constraints (runMany
  no-ops DDL; pre-D5 window) → **D8** (the missing SHOW CONSTRAINTS count guard — the
  history is already fixed by D5, the item is the structural check).
- 2026-07-28 — [chore] render_gates.py missing from the stale-render ritual → **J17**.
- 2026-07-28 — U5 executed INSIDE the groom run (graph cross-check subsection added to
  this very skill) — **Epic U closed 6/6**, the run's close-out target.
- 2026-07-28 — [bug] depgraph scanner blind spots — one fix, three symptoms (cross-root
  IMPORTS, function-level imports, missing drydocs_api scan root; U1 F1 + U2 census,
  confirmed live by the graph-navigation benchmark 0-vs-24) → **U6** (p2, graph-infra;
  work spans the external depgraph repo + snapshot.ps1 target list); **U4 re-sequenced**
  to depend on U6, encoding the U1 wait-verdict. Companion agent-graph-navigation
  [idea] line stays inboxed (mechanism decision = `drydocs query` CLI vs MCP, user call).
- 2026-07-28 — [bug] ontology.cypher:109 dangling SDLC-subset load reference → **C19**
  (comment fix; the build-the-subset-at-all question recorded IN the item as an open
  user/SME call, not silently dropped).
- 2026-07-28 — [bug] PORT-MANIFEST `default: clean-add` fall-through gap → **J16** (the
  inverse-question guard: no tracked path resolves to default without an allowlisted
  reason; the git-readme.md deliberately-uncovered DECISION gets written into the
  allowlist rather than living only in this inbox).
- 2026-07-28 — [bug] doc_traceability/doc_feedback silent-prereq sweep leftovers → **L17**
  (Q8-pattern loud refusal; doc_feedback is the L5/L6 re-attachment loop, so it headlines).
  The batch_port_orchestrator half of that line was already FIXED 2026-07-27 in-session.
- 2026-07-28 — [chore] web/ 3 high-severity npm advisories → **O34** (audit-fix + verify;
  the 1,485 kB bundle/code-splitting design call recorded as explicitly OUT of O34's scope,
  parked in its notes).
- 2026-07-28 — [idea] Script→SWO rider (`:Script -IS_ENCODED_IN-> SwoClass` by extension,
  G33 §E1(b) precedent; run_as = Agent territory boundary; dead-script detection framing)
  → **MERGED into G22 notes as rider R1** for the gate session's agenda.
- 2026-07-28 — [question] m3_invokes `to_node` broadening (Script → Script|ETLProcess, the
  abioncloud wrapper-payload finding) → **MERGED into G22 notes as rider R2** — same gate
  session, vocabulary-shape decision.
- 2026-07-28 — [bug] SchemaMeta contamination defeats WRITE-side guards too (the Q8 build
  finding) → **MERGED into O33**: acceptance now covers loader prereq/guard queries, and
  the keyless-exemplar root-fix option is recorded in its notes.
- 2026-07-28 — [chore] neo4j-drydocs-ee literal `<password>` (2026-07-03 line) → **MERGED
  into the 2026-07-23 delete-rollback-container line** — deleting the container retires it.
- 2026-07-28 — trail moves, no new ids: the C17 PAT-keying and C18 shadow-model lines
  (both said "Groomed as …" since 2026-07-27, C18 since closed) and the fully-RESOLVED
  p0/boundary J14-residual line (its surviving question is the standalone
  platform-vocabulary line; the 6-digit-table-keys SME ruling is recorded in J15's
  close_note) moved out of the inbox.
- 2026-07-27 — [chat notes] G18→G22 premise correction: the psgmgr CM_DEF_VJOB_DETAIL-style
  table (split by job type) was never built → **G39** (temporary cmd-line staging store,
  graph-sourced — j.cmd_line already loads; next_ready) + **G40** (Python cmd-line parse into
  detail columns via the G26 registry + G15 arg contract; depends G39) + the correction merged
  into **G22**'s notes (gate stays the graph terminus; folder/job VARIABLES stay deferred as
  originally sequenced). Company-side "load into the real detail table when built" recorded in
  G40's notes for their tracker. G37 left unallocated (sequence gap beside G38 — possibly the
  concurrent session's; not risked).
- 2026-07-27 — [chore] EE home db `neo4j` pre-existing strays → **RESOLVED same day, no item**:
  user ruled "wipe it, it can be rebuilt" — 288 nodes deleted, 0 remain; topology DBs verified
  untouched (drydocs 834). The .env comment + dev-environment.yaml home_db_warning guard recurrence.
- 2026-07-27 — [idea] code-graph multi-persona review plan (docs/reviews/code-graph-review-plan.md)
  → **U1** (python-architect, opus), **U2** (PM backlog-truth audit), **U3** (tech-writer
  doc-status board) — all next_ready; optional skill-edit follow-ups → **U4** (tech-debt,
  gated on U1) + **U5** (groom-backlog, gated on U2). Epic U gains its first U-lettered ids.
- 2026-07-27 — [p0/boundary] knowledge/standards real-SEALID relocate-vs-sanitize → **J14**
  (option-b split, mechanism public / values internal); [lesson] field-vs-VALUE sweep failure
  → **J15** (value-shape boundary guard test, 70001-70099 block). Residual platform-vocabulary
  question re-inboxed as its own line.
- 2026-07-27 — [chore] :BusinessApplication index diet → **G36** (rides S3's bootstrap
  re-run); [bug] SchemaMeta exemplar contamination → **O33**; [bug] nothing-reads-ddall →
  **G38** (after G32's ruling); [question] deepdoc charter drift → **MERGED into G32** as
  acceptance clause (e).
- 2026-07-27 — [question] "BusinessApplication identity gate — deferred, resume leaner"
  RESOLVED without an item: the gate resumed on exactly the four-question surface and SIGNED
  OFF 2026-07-27 (22/22, `fc15191`). Build = S3 (acceptance rewritten at sign-off); ADR 0010
  amendment = S1; TOM-roles reopen = G35; glossary reservation = G34.

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-26 groom run (docs-residency design session, straight after G28/G29/G30)
  — **8 promoted / 2 inboxed** (todo 39 → 47). Source was a chat, not inbox lines, so
  nothing was moved out of the inbox except the notes below.
  - **Epic Q (docmeta):** **Q7** registry-vs-loaded reconciliation (user-requested — the
    registry declares corpora and `test_doc_registry.py` enforces the declaration's shape,
    but nothing checks a corpus was ever loaded or landed in the database it declared);
    **Q8** the DESCRIBES silent-drop bug; **Q9** re-file Essential GraphRAG as Neo4j vendor
    docs; **Q10** the failure/activity email corpus; **Q11** document supersession/currency.
  - **Epic G (component-topology):** **G32** the document/content topology ruling +
    ddcontext charter (the decision everything waits on); **G31** the proxy-spine extension
    (prerequisite for every corpus move).
  - **New phase 16 + Epic U — `self-documentation`:** **G33** the code snapshot under a
    Project root. Groomed into phase 6 with the marginal fit flagged, then **re-phased the
    same day on the user's ratification** — *"similar to a major version change of the
    snapshot ritual"*, i.e. a new capability rather than an ADR 0002 follow-up. The framing
    that earned the phase: the depgraph ritual's output stops being a JSON file a human
    reads and becomes a queryable `:Project` subgraph — a different KIND of thing, not a
    bigger version of the same one. Id kept as G33 (ids are stable references and it is
    already named in commit a37043a); new items here take U1, U2, … — **T is not free**, it
    is the port-turn series (`docs/port-T12-*.md`).
  - **The session's through-line, worth keeping:** ONE failure pattern found three times —
    *succeeds loudly, does nothing*. G29 (a supplement that runs and seeds no terms), G30
    (a spec that reads a database nothing writes), Q8 (an `OPTIONAL MATCH` whose target
    class is in another database). All three pass their loads green. Worth treating as a
    review lens rather than three unrelated fixes: **any MATCH that can legitimately find
    nothing needs to distinguish "this row missed" from "the whole class is absent".**
  - **Two decisions recorded that overturn signed-off records**, both routed through the
    gate rather than edited (the discipline G30 set): Q9 amends ADR 0006 §2 (the Q2 book's
    `ddcontext` placement) and G32 amends ADR 0002 D1 + ADR 0006 §2.
  - **One assumption I got wrong and corrected in-session:** I proposed *capture fidelity*
    as the database boundary (faithfully-captured vs inferred) and the user rejected it —
    a faithfully-captured stale Confluence page is MORE dangerous than a lossy capture of a
    good page, because it looks authoritative. The property that earns a boundary is
    **content authority**, not capture fidelity. Recorded because the wrong version is the
    intuitive one and will be re-proposed otherwise.
  - **A prediction that did not survive contact:** I named email retention as the fact that
    would decide 2 databases vs 3. It did not — the extracts are deliberately preserved past
    Outlook's 6–18 months until process/project retirement, so purge is property-scoped, not
    a database drop. The 3-DB decision rests on load separation and wipe blast-radius
    instead. Kept here so the retention argument is not re-run.
  - **Inboxed, not promoted:** the deepdoc scope drift (ADR 0002 vs ADR 0006 vs stated
    intent — a ruling, likely a G32 §) and "nothing reads `ddall`" (both at the top of the
    inbox).

- 2026-07-25 groom run (bare `/groom-backlog`, same session as the pre-UI structure review)
  — **11 promoted / 2 inboxed / 1 merged / 1 resolved-in-groom** (todo 30 → 41):
  - **New Epic S — `structure-remediation` (S1–S9)** from
    `docs/reviews/architecture-structure-review-2026-07-25.md` (15 findings, scored
    `(Impact+Risk)×(6−Effort)` plus a pre-UI cost-of-delay flag the formula cannot encode).
    Given its own epic rather than folded into G because the items share one review
    document, one phased plan, and three ADRs whose acceptance gates them — the board
    should show that sequencing as a unit. Each item keeps its correct existing plan
    phase, so the roadmap strip is unchanged.
    - **S1** — rule on ADRs 0008 / 0009 / 0010 (the decision item; the R1 precedent, so
      nothing is groomed into a done deal). Not a HITL gate: no edge semantics.
    - **S2** — ADR 0008: `drydocs_core/orchestration/` parent over `controlm/`, with the
      neutral `shell.py` / `paths.py` / `crosswalk.py` surface beside it. The review
      measured before recommending: ~1,100 of `controlm/`'s 1,725 lines are irreducibly
      Control-M, so the answer to *"should controlm/ become orchestration/"* is **no
      rename — add a parent**. Graph labels untouched (ADR 0003 rule 4).
    - **S3** — ADR 0010: `app_id` + `id_authority` beside `seal_id`, API and web emitting
      only the neutral pair. **GATE-BOUND** — a property-term binding on the canonical
      `:BusinessApplication` node; the map entry stays `proposed` until sign-off.
    - **S4** — ADR 0009: a `draft` table in `mapping.db` as the console's write-ahead
      buffer, promoted by emitting a YAML/CSV diff. Git stays the commit target.
    - **S5** (split the two monolith YAMLs by domain) · **S6** (JSON Schema per config
      family) · **S7** (record the folder-vs-module naming rule once).
    - **S8** — cli.py regroup. **MERGE**: the review's F6 and the long-parked
      `[idea] cli.py regroup` inbox line are the same work; that line's file was 937 lines
      when written and is 1,519 now, which is the argument for doing it. Its deprecation-alias
      condition carried into the acceptance. No dependency on S1 — reorganizing a CLI needs
      no ADR.
    - **S9** — `UI-WIP/` → `docs/design/ui-exploration/` + loose `docs/*.md` grouped.
      Effort was scored 1 and **corrected to 3–4 the same day** when the attempt measured
      31 tracked references (backlog.yaml 45 hits, the generated board, `PORT-MANIFEST.yaml`,
      two gate prompts, two governed renders, `drydocs_api/app.py`) — branch + port-sequenced,
      never a tidy-up commit.
  - **G28** — the multi-database naming drift, found while writing the executive overview
    against the live gated convention. `drydocs_deepdoc.DATABASE = "drydocs_context"`, a
    database `provisioning/01_databases.cypher` never creates (it creates `ddcontext`), and
    `test_lineage_deepdoc_scaffold.py` **pins that value** — so the suite currently protects
    the wrong name. Also unanswered: `ddlineage` is provisioned and read by four query specs,
    but `drydocs_lineage/writer.py` pins `DATABASE = "drydocs"`, so those specs read an empty
    database. Not a trust-boundary hole — the writer refuses on an allowlist.
    RESOLVED 2026-07-26: that second half was split out of G28 as **G30** (a data-residency
    decision, not a naming fix — bundling them was a grooming error) and is now DONE. Ruled
    for ADR 0002 D1/D2: curated lineage lands in `drydocs`; the four specs repoint there and
    `ddlineage` is documented as provisioned-for-later. Ruling written up as ADR 0002's
    "Residency clarification", with the named trigger to revisit through the gate.
  - **G29** — [idea] supplement consolidation shape A (2026-07-24, designed + user-reviewed)
    → the single `apply-supplements` verb with legacy verbs as delegating aliases, all four
    agreed riders in the acceptance. Its sibling **shape C** re-inboxed slim above: it changes
    what a supplement *means*, so it is gate-worthy, not a refactor.
  - **inboxed:** F11 depgraph-snapshot retention (a user call about audit history — and the
    review's proposed mechanism was wrong: `drydocs prune-snapshots` prunes snapshots inside
    Neo4j, not the JSON files); supplement shape C (above).
  - **resolved in the groom, no promotion:** [doc] reconcile-port skill's stale Track-1 floor
    — measured this session at **114 passed / 3 skipped** (the line said 90/3; the inbox note's
    own 113/3 was already stale, since the 2026-07-25 boundary-guard fix added a fifth
    `test_module_boundary.py` test). Skill updated in place, with the number reframed as a
    FLOOR to re-measure rather than a constant, since this is the second time it has drifted.
  - **kept-updated:** the Databricks Unity Catalog line (its governed-namespace citation was
    consumed by ADR 0010 / S3; the tag-policy and glossary-as-concept-scheme citations stay
    parked) · the acronym-catalog line (the review's §4.2 independently reaches the same
    `CatalogBusinessTerm` home from the identity question rather than the collision question;
    still parked on the gate-log Q6 ruling) · the unlocated-typo bug (G29 rewrites the very
    verb list Appendix B carries, so its rider resolves the best-guess half).
  - **findings deliberately given NO item**, recorded so a future reviewer does not rediscover
    them: F4 / F9 / F10-part (done same day — `432ea43` boundary-guard fix, `bbf29cf` gitignore);
    F5 (the `drydocs/` 4-component flat namespace — deferred to Phase C by ADR 0002-a-1, and
    the review's §6 says explicitly not to reopen it mid-UI-build); F15 (two test roots — `tests/`
    pytest and `graph-tests/` YAML acceptance are two mechanisms, not duplication).
  - **kept parked, unchanged** (trigger checked this pass): gate-log Q6 reopen (SME ruling),
    T11 L7-ratification snippet (owed at the next company session), Oracle connection for
    lineage/remediation, company-side greenfield remediation standards, rollback-container
    deletion, PDN/BIM milestone-grain design, email-DL contact point (gate-tracked), the
    Control-M app-code → SEAL `:Port` block (gate `seal-app-ref-edge-reshape` v2 — note S3
    touches the same node, so run them together if timing allows), env-toggle canonical
    identity, XML WARN-flood port note, compact-timestamp back-flow, AIS acronym port-carry,
    ControlMApplication two-pattern mapping, m7 build follow-up, marketing-site brand kit,
    FW-really-API gap classes, DPL ingestion-leg residuals, company back-flow batch,
    company-side heads-ups, post-squash ref cleanup, Runbook Rev 3 rider, SNYK_TOKEN,
    SEAL/PAT generic terminology (three §Decision calls — **note S3 now overlaps its
    `SEALID`→generic-identity-property call and may close it**), m3_invokes `to_node`
    broadening, depgraph metric extensions, ETL-tooling inventory, JobRun indexes, SaaS
    scaffold research, K2 FID/ALIAS tables, `ctlm_id` ripple, dry-docs.com seed,
    /documentation whitepaper type, lineage live-load gate, remediation slices, Phase C
    packaging, Control-M Workbench, BRD outline, docmeta P4–P7, EE container password,
    `common/` in /list-apps.

- 2026-07-23 groom run (full inbox sweep + the misfiled "UI acceleration session"
  block folded in from the bottom of this file) — 5 promoted / 2 resolved-in-build
  (no promotion) / rest kept parked (todo 25 → 30):
  - [chore] Neo4j-container-recreation residual (the container migration itself
    — `neo4jtest` on named volume `neo4j-testdata`, default ports 7474/7687 — is
    already done; only the doc is stale) → **L16**: refresh
    `docs/design/drydocs-startup-refresh-runbook.md`'s container table + start
    commands (still say `neo4j-drydocs-ee`/7476/7689) via the governed render
    pipeline. The sibling "delete the rollback container after a week + prune
    orphan volumes" chore stays INBOXED (time-gated manual Docker op with no
    repo-testable acceptance — the SNYK_TOKEN / post-squash-cleanup precedent:
    manual user steps don't get a backlog.yaml pull id).
  - Misfiled "## 2026-07-23 — UI acceleration session" block (context-graph
    analysis + underhood build) folded into this trail entry — its groom
    candidates from `UI-WIP/two-track-ui-plan.md` (Track 1 table) promoted:
    **O29** (T1-5 trust-tier/edge-provenance legend live on the /lineage and
    /docs graph-pane canvases, adopting context-graph's declared/observed
    legend pattern); **O30** (T1-7 retire `App.css` legacy-mockup classes into
    the token idiom across SignIn/MyApps/GraphExplorer/TowerDrill/
    CypherConsole); **O31** (T1-8 regenerate `web/src/underhood/
    benchmarkData.ts` from the docmeta evaluation-harness output — no
    standalone eval-harness backlog item exists yet, so the dependency is
    recorded as prose in the item's notes per the groom instruction and
    `depends_on` is left `[]`); **O32** (T1-6 light-mode design pass — not
    previously tracked; dark stays canonical). The "intended-bypass build
    landed on main" record and the context-graph adopt/avoid headlines are
    DONE-work notes only, not backlog-actionable — no item, preserved here and
    in `UI-WIP/two-track-ui-plan.md` / `internal/context-graph-analysis/
    ui-architecture-analysis.md`.
  - [source] By-SEAL bulk MAC inventory line → RESOLVED IN BUILD, no
    promotion: G25 (done 2026-07-23) already carries both the taxonomy-first
    per-SEAL staging and the clone-lag `cross_check()` column the line asked
    for; the assumed-field-contract residual rides the dpl_mac discipline, not
    a separate item.
  - [question] Gate rider (G17 build): MAC subType → kind-enum semantics →
    MERGED into **G27** (done 2026-07-22): the gate BRIEF
    (`config/gate-prompts/etlprocess-kind-enum.yaml`) already carries this
    exact question with a recommendation; the SME sign-off itself stays a
    HITL session, not a fresh backlog item.
  - kept parked, unchanged (checked against backlog.yaml this pass — no
    matching item to merge into, or the recorded trigger/gate hasn't fired):
    Oracle connection for the lineage/remediation path (needs SME scope
    clarification first — a question, not yet scoped work), company-side
    greenfield remediation standards (no FR-REM-5/M2 item exists yet),
    PDN trigger/BIM-90489 milestone-grain design, email-DL contact-point
    ontology mapping (already gate-tracked, nothing further to promote), the
    Control-M app-code → SEAL :Port attribution block (owned by gate
    `seal-app-ref-edge-reshape` v2; the property-diet rider sub-part already
    resolved in-line 2026-07-23), env-toggle canonical-identity constraint,
    XML-run WARN-flood next-port note, compact-timestamp normalization
    back-flow note, AIS acronym port-carry, ControlMApplication two-pattern
    mapping (gate-decision core), m7 build follow-up (lineage live-load
    gate), public marketing-site brand kit, FW-really-API provenance gap
    classes, DPL ingestion-leg residuals, back-flow of un-back-flowed company
    advances, company-side heads-ups (their tracker), post-squash ref cleanup
    (destructive, user-gated), Runbook Rev 3 rider, SNYK_TOKEN manual step,
    SEAL/PAT generic terminology (three §Decision user calls), m3_invokes
    to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance
    plan's next touch), SaaS scaffold research (triggers unfired), K2
    FID/ALIAS tables (company-side), ctlm_id ripple (internal-side),
    dry-docs.com seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Control-M Workbench
    (entitlement), BRD outline (later phase), docmeta plan P4–P7 (Q6 still
    todo), EE container password (user deferred), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-23 R1 gate SIGNED OFF (same session as the groom below) — **ADR 0007 ACCEPTED
  as written**; rulings (full text in config/gate-log.md): (a) Tier-2 task-graph residency
  = in-process only (ddcontext persistence deferred; new gate if ever proposed);
  (b) :AgentRun envelope → ddcontext, dedicated writer boundary, question sha256+length
  only in-graph; (c) LLM keys = **environment-split: local/producer Anthropic API key,
  company Azure OpenAI** — Gemini NOT the runtime default, closing the 2026-07-03
  question with a ruling that supersedes its Gemini-shaped assumption. R2 next_ready.
- 2026-07-23 groom run (agentic-Q&A architecture session) — **new phase 15 "Agentic Q&A
  console" + Epic R (R1–R8)** from the llm-graph-builder vs knowledge-graph-of-thoughts
  comparative analysis; **ADR 0007 drafted (PROPOSED)** — SME gate = R1, which also rules
  context-graph escalation residency, :AgentRun target DB, and the LLM key strategy.
  Moved from inbox: the 2026-07-03 [question] LLM key strategy (Gemini vs Anthropic via
  LiteLLM) → decided at **R1**. New module registered: drydocs-agents (agents/ ADK
  service). Analysis dossier (both workflow diagrams) linked from ADR 0007's footnote.
- 2026-07-22 — [source] **Backstage catalog-model assessment T1–T8 groomed**
  (UI-WIP/backstage-catalog-assessment.md; shallow clone surveyed + deleted same day):
  T1 kind-enum gate precedent brief → **G27** (in_progress, pulled at groom); T2+T3
  QuerySpec conventions (derived-edge rule + external ref grammar + no element ids) →
  **O27**; T4 inverse_label display field → **C15**; T5 status.items node-status
  envelope → **O28**; T7 metadata key-prefix governance → **C16**; T8 env-toggle
  canonical-identity constraint → inboxed above (no env-toggle item exists yet); T6
  schema-as-contract on DataAsset = design CONFIRMATION only — already covered by the
  O10 schema-definition frame + the G17 MAC dataset feed chain, no new item.

- 2026-07-21 pm — [task] **C12 platforms-taxonomy gate RUN + SIGNED OFF in-chat** (same
  session, ~an hour after C12 was groomed; the K5 precedent): rendered page presented,
  3/3 as recommended — A+B1–B3 confirmed as written (registry model; Ais* removed;
  USES_SOFTWARE {source: 'batch-port'} landing), B4 existing local no-PROV typing covers
  the migrated fact, B5 airflow row stays as the F2 crosswalk placeholder. Gate-log
  entry appended; platforms.yaml confirmed: true; build follow-ups groomed → **C13**
  (SchedulerKind retirement + vocab/map closure + Ais* straggler sweep) and **C14**
  (batch-port USES_SOFTWARE loader migration). C12 done (todo 22 / done 122).

- 2026-07-21 pm groom run (bare /groom-backlog, same session as the platforms-taxonomy
  pre-rulings) — 3 promoted / 0 inboxed / 1 kept-updated (todo 18 → 21):
  - [idea] SchedulerKind → AisCapability/AiTool deprecation (parked since 2026-07-09;
    groom-condition FULLY FIRED today — C11 captured the company shape am, the SME ruled
    the reshape in-chat pm: Ais* removed both sides, registry model wins, gate prompt
    reshaped to confirm-as-written) → **C12** (run the platforms gate, USER-GATED START;
    build follow-ups groom at sign-off — the K5 gate-RUN precedent).
  - [idea] app-to-app path runbook view wireframe (2026-07-21) → **O26** (Runbooks-page
    App-path tab + QuerySpec runbooks.app-path.v1; lane partition from label sets only —
    the layer/c4_level vocabulary stays a gate question; trigger fired: O17 + O11 done).
  - [idea] launcher-registry config-file migration (2026-07-16, the remaining inboxed
    half) → **G26** (config/ pattern + schema guard; classifier_rule ids pinned by
    invocation_patterns must keep resolving; trigger fired: O12 done — its matrix renders
    this registry as the unguarded-config example G26 retires).
  - kept-updated: the ControlMApplication two-pattern mapping line — O13 shipped same
    day (0dc2831), satisfying its prioritization flag; the gate-decision core stays
    parked on the SME convening the mapping gate / K2's next touch.
  - kept parked, unchanged (trigger checks this pass): AIS acronym port-carry (next
    cross-repo port), MAC subType kind-enum rider (next lineage gate; G22 closest), m7
    build follow-up (lineage live-load / m7 flip), marketing-site brand kit (site not
    started), FW-really-API gap classes (next Script-refinement gate), DPL ingestion-leg
    residuals, company back-flow batch (needs screenshot channel), company-side heads-ups
    (relay next company session), post-squash ref cleanup (user, destructive), Runbook
    Rev 3 rider, SNYK_TOKEN manual step, SEAL/PAT terminology (three §Decision calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metrics (sibling repo),
    ETL-tooling inventory, JobRun indexes, SaaS scaffold research, K2 FID/ALIAS
    (company-side), ctlm_id ripple (internal-side), dry-docs.com seed, /documentation
    whitepaper type, lineage live-load gate (HITL scheduling), remediation slices (TDD
    §6/§7), Phase C packaging, Workbench (entitlement), BRD outline (later phase),
    docmeta P4–P7 (Q6 still todo), EE container password, LLM key strategy, common/
    cosmetic, cli.py regroup (v1.0 window).

- 2026-07-21 groom run (bare /groom-backlog, same day as cmdline-nfr-vetting/G15/G16 and the
  Epic O landings) — 2 promoted / 1 retired-merged / 1 kept-updated (todo 22 → 24):
  - [source] DPL runtime traced end-to-end (2026-07-21) + [idea] ETLProcess kind
    discriminator (2026-07-19; its trigger FIRED — pipeline.json subType is exactly the
    discriminating signal G12 lacked) → **G17** (MAC ingest seam: dataset-flow
    READS_FROM/WRITES_TO candidates + kind-derivation rule + SEAL attribution facts;
    synthetic fixtures, gate-confirmed endpoints, all m3_* statuses untouched;
    depends_on G15 — ready now).
  - [idea] AIS taxonomy back-flow for the platforms gate (flagged 2026-07-10 in the
    66acea8 port report, unactioned since) → **C11** (USER-GATED START: capture the
    company-confirmed AisCapability/AiTool shape into config/taxonomy/platforms.yaml
    as the gate's PROPOSED seed; pull loop skips it until the user supplies the
    screenshot/describe material; the sibling SchedulerKind-deprecation line stays
    parked on that same gate).
  - [source] variable gap analysis (2,384 names vs the alias map) → RETIRED MERGED —
    fully consumed at build time: G15's acceptance (a)/(c) cites it as evidence and
    G16 built its alias rollups, value contracts, and the ETL_ARTIFACT_SHA canonical
    from it. Nothing left to carry.
  - kept-updated: the DPL ingestion-leg line — its open item (b) (DataAsset
    zone/glue-table shapes for the MAC enrichment feed) now rides G17 instead of the
    retired sibling line; its other open items (ingestion-launcher jar sample,
    Pre/Post-exec file-op surface, cross-job %%\\JOB\VAR threading) stay inboxed.
  - kept parked, unchanged (each on its recorded trigger): m7 build follow-up
    (deliberately inboxed at the gate — lands at the lineage live-load / m7 flip),
    public marketing-site brand kit (site not started), FW-really-API provenance gap
    classes (:Script property proposals = gate rider for the next Script-refinement/
    lineage gate session), back-flow of un-back-flowed company advances (needs the
    screenshot/describe channel; spans six modules — batch shape decided when the
    material arrives), company-side heads-ups (their tracker; relay next company
    session), post-squash ref cleanup (user, destructive), Runbook Rev 3 rider,
    SNYK_TOKEN manual step, SEAL/PAT generic terminology (three §Decision user calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance plan's
    next touch), SaaS scaffold research (triggers unfired), launcher-registry
    config-file migration (O12 todo), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling —
    unchanged by G15/G16), remediation slices (TDD §6/§7), Phase C packaging (plan
    gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool (gate; C11
    now feeds it), BRD outline (later phase), docmeta P4–P7 (plan-tracked while Q6
    todo), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-21 — [question] Company draft CMD_LINE/variable NFR ontology vetted vs m3 vocab →
  **RULED same day at gate `cmdline-nfr-vetting`** (config/gate-log.md; guided SME session,
  4/4 as recommended): TRIGGERS from-node stays the LAUNCHER (payload variant rejected);
  `USES_ARTIFACT` registered as vocab entry `m7_uses_artifact` (status: planned); :Script
  refinements adopted (script_role + artifact_* props); all 7 variable-standard deltas
  adopted (ETL_* prefix, ETL_ARTIFACT_SHA, aliases-suggest-values-decide, alias-map
  completion, two platform axes, FACT_REGISTRY migration, mode flags stay literals) →
  engine-alignment work groomed as **G16**.

- 2026-07-21 — [chat] UI extension groom ("extend the UI open items until HITL"): the new
  UI-WIP corpus (DryDocs_UI_Development_Specs.md, gemini-wire-frame.md, icons.md,
  layout-anatomy-checklist.md, new mocks) + site-plan §5 P3 → **O15–O22** (Ownership /
  Loads / Runbooks+Remediation / Docs / Gates-read-only pages, the O20 write-surface HITL
  gate as the chain terminus, UI-WIP commit chore w/ LFS, icon SVG export); demo-content +
  expanded-landing specs **merged into O9** inputs/notes; WEBSITE-IDEAS.MD parked to Inbox
  (public site, separate workstream).

- 2026-07-21 — [source] Real prod DPL CMD_LINE samples (folder/job screenshots +
  variables-simulation views) → **merged into G15** (acceptance upgraded from
  placeholders to observed grammar: single-dash `-pipeline` GUID as the only literal,
  variable-held launcher fallback, -i/-t/-py mode flags, -seal/-fid/-img/-conf/-compute
  property set; one dt-launcher.sh spine across ingest/transform/provision). Remainder
  re-inboxed on the ingestion-leg line: template ingestion-launcher jar unobserved,
  Pre/Post-exec file-op surface, zone/glue DataAsset shapes, cross-job %%\\JOB\VAR.

- 2026-07-21 — [chat] DPL launcher key-parameter capture (--pipeline-id spelling +
  shell-launcher variants + -py route + dataset-id/aws/jar/queue params as properties)
  → **G15**. The sibling 2026-07-21 inbox line (MAC dataset-flow enrichment feed +
  G12 kind discriminator) stays in the inbox — G15's explicit non-goal.

- 2026-07-20 groom run (evening; second machine re-based post-squash, then /groom-backlog) —
  2 promoted / 1 inboxed / 1 kept-updated (todo 17 → 19):
  - session preamble (recorded here — ref state, not backlog): this machine adopted the
    squashed main (reset to 4540bbc), local `feat/mapping-store` DELETED as superseded
    (its content was inside the Initial-import squash and main evolved past it; old
    history kept at local tag `archive/old-history-2026-07-20`).
  - [doc] runbook-mapping-demo free-form pre-L8 (2026-07-18) → **L14** (refit to
    runbook.outline.yaml, 2nd runbook exemplar; trigger = L8 done, e6bcb24).
  - [doc] project-review canonical outline (2026-07-14) → **L15** (review.outline.yaml
    3rd doc type + recorded refresh cadence; same L8 trigger; p3).
  - inboxed: post-squash ref cleanup (stale origin branches feat/mapping-store +
    feature/provenance-audit-fields-plan; local backup branch/stash/tags) — destructive,
    user-gated.
  - kept-updated: SEAL/PAT generic-terminology line — C10's CSDM mining landed (its
    named missing piece); decision surface fully fed, still parked on the three
    §Decision user calls (scope / new-epic plan change / SEALID property).
  - trigger checks this pass: Q6 todo → docmeta P4–P7 stay plan-tracked; O12 todo →
    launcher-registry config-file migration stays; E1 deferred both sides; Runbook Rev 3
    rider + SNYK_TOKEN manual step stay inboxed (new today, correctly parked). All other
    lines kept parked, unchanged on their recorded gates.

- 2026-07-20 — [doc] apply the runbook rev1 SME feedback → EXECUTED SAME-DAY (user-directed,
  no backlog id): both notes applied to the .md (front-matter one item per line; out-of-scope
  drops the company-side Track-2 item), Rev 1→2 with a change note, re-rendered (footer
  "Rev 2 · commit a135a6d"), validator + doc tests green. The rev1.yaml stays as the
  feedback record; the stray -sme.html working copy remains the user's to delete.

- 2026-07-20 — [chore] USER MANUAL STEP: port-bundle transfer → **RETIRED, FULLY COMPLETE**
  (the 07-19 line, end to end): bundle created @ 3ae9b08 (447 commits, full pre-squash
  history) → base64 3-way split → emailed → company side rejoined, hash-verified,
  `git bundle verify` passed, full bundle-port reconciliation ran (their
  PORT-REPORT-bd7952f.md, 2026-07-20) → ALL FIVE local transfer files deleted
  (3 parts post-email; the bundle + .b64.txt deleted 2026-07-20 pm after far-side verify,
  user-directed). Full private history now exists only in local `archive/full-history` +
  the company repo. Recipe reference: `docs/ruff-format-convergence.md` §"Transfer
  without visibility change".

- 2026-07-20 — [question] cross-repo backlog id collision → **DECIDED SAME-DAY (user):
  the DD-series** (`DD1`, `DD2`, …) is reserved for company-side-only items; the producer
  never allocates it, the company never allocates epic-letter ids. Recorded in
  git-readme.md (§backlog id allocation), the backlog.yaml header, and the groom-backlog
  skill id rule. REMAINING (company-side, next session there): renumber their colliding
  C10/K6/N3 → DD1–DD3 before the next port range applies.

- 2026-07-20 pm — bundle-port readout review (company-side photo; their
  PORT-REPORT-bd7952f.md) — 2 mirrored done / 1 line resolved / 1 question inboxed:
  - **P1 + P4 → done** (company completion wins for company-side work — their probes +
    CM_AVG_RUN supplement loader shipped; resolves the 07-18 "concurrent Epic P session"
    observation). P3 becomes next_ready; P5 still waits on P3.
  - port-bundle USER MANUAL STEP line → RESOLVED to its last step (delete the 2 remaining
    local transfer files; far side verified).
  - inboxed: the C10/K6/N3 cross-repo id-collision question (convention needed before the
    next port).
  - noted, no producer change: the company deferred 3 HITL deltas to their own gates
    (docs_*/:DocSource union-add; catalog_supports re-activation; jobrun-observation —
    E1's gate is now deferred BOTH sides); their 4 port commits await review + push.

- 2026-07-20 — [chore] Snyk scanning in CI → EXECUTED SAME-DAY (no backlog id, direct user
  request — the PAT-semicolon precedent): ci.yml gains a `snyk` job — SCA over the Poetry
  manifest (blocking at high severity) + advisory `snyk code` SAST (the ruff idiom).
  Token-gated: every scan step skips cleanly until the SNYK_TOKEN repo secret exists.
  REMAINING USER MANUAL STEP: add SNYK_TOKEN (Settings → Secrets → Actions; token from
  app.snyk.io) — first green scan confirms; consider gating `snyk code` after triage.

- 2026-07-20 — [source] **external/ServiceNow doc set** (6 files downloaded same day: CMDB
  Process Guide .docx, CMDB Product Architecture / Data Manager / Governance Workshop
  .pptx, ITAM-SAM Integration Options .pptx, "What are services and service offerings"
  .pdf) → **C10** (promoted directly from chat, the C9 precedent): housing + SOURCE-MANIFEST
  + classification decision, readable-text conversion (the SDLC-Docs/extracted idiom),
  and per-file concept mining dispositioned incorporate/park/reject — feeds the parked
  generic-terminology idea (the CSDM service/service-offering layer is its missing
  piece). User context in the item notes: the full-circle-docs-era ServiceNow Marketplace
  consideration (research only) and the CMDB-for-taxonomy→ontology reference. Files stay
  untracked until C10's classification step.

- 2026-07-20 — [task] **K5 Product Cabinet gate RUN + SIGNED OFF in-chat** (same session as
  the groom below, later in the day; page rendered via gate_pages.py from the in-flight
  2026-07-19 gate-prep, sections A–E answered in-session, §F signed off — gate-log
  2026-07-20): map entry confirmed; families INDEPENDENT (shared-cto dropped, rename
  history recorded — supersedes 2026-07-10 §B); tech_partner :AreaProduct-only; BOTH
  attribution forms (collapsed catalog_cabinet_attributed_to added); reporting edges
  DEFERRED (internal-side); DevTeam↔BusinessApplication M:N confirmed. Supplement
  follow-up promoted directly → **K6** (the C9 direct-promotion precedent); K5 done
  (todo 22 / done 91). The 07-20 groom entry's "K5 in flight uncommitted" observation is
  RESOLVED — this session took ownership, committed the stream (K5(1)/K5(2) + this
  close-out), and the m3_invokes to_node rider stays parked (this gate was
  Product-Cabinet-scoped; next lineage-vocab gate remains its trigger).

- 2026-07-20 groom run (bare /groom-backlog, day after the weekly run; post history-squash) —
  0 promoted / 0 merged / 1 kept-updated; backlog database untouched (todo 22 / in_progress 1 /
  done 90 stand as of the 07-19 groom):
  - kept-updated: the USER MANUAL STEP port-bundle line gains the SQUASH RIDER — today's
    history squash (main = single commit c5a84c3; full history only in local
    archive/full-history) makes "email the existing 3ae9b08 full-history parts vs re-cut
    from the squashed main" a user decision that must precede the email step.
  - noted closed by the squash: the 07-19 seal-sample residual ("git HISTORY retains both
    seal twins until a rewrite, user-gated") is CLOSED on main/origin — pre-squash history
    survives only in local archive/full-history + the five transfer files (whose deletion
    is the port-bundle line's remaining step).
  - observation (no groom action): **K5 gate-prep is IN FLIGHT, UNCOMMITTED** in the working
    tree — config/gate-prompts/product-cabinet-attribution.yaml (new) + map/vocab/
    schema_graph edits, proposed_at 2026-07-19, all correctly gate-bound (everything
    planned/proposed, nothing applied). Left untouched per the 07-18 P1 precedent: the
    owning session commits and flips K5 todo→in_progress itself; this groom's commit
    excludes those files.
  - observation (user decision, destructive): stash@{0} "On feat/k4-businessapplication-
    reshape: gate-review IDEAS entries" is STALE — its two 2026-07-15 lines reached the
    inbox via another path and were groomed to G12/G13 at the 07-16 pm run (G12 since
    executed). Candidate `git stash drop`; not dropped by the groom.
  - trigger checks this pass: Q4/Q5 done but Q6 still todo → docmeta P4–P7 stay
    plan-tracked; L8 todo → runbook-mapping-demo refit + project-review outline stay;
    O12 todo → launcher-registry config-file migration stays; no other recorded gate moved
    since yesterday's run. All other lines kept parked, unchanged (m3_invokes to_node
    broadening noted as a candidate agenda rider for whichever gate session runs next —
    the in-flight K5 gate is Product-Cabinet-scoped, so adding it is the SME's call).

- 2026-07-19 groom run (weekly inbox groom) — 2 promoted / 2 merged-or-folded / 1 kept-updated:
  - [bug] publish-ceiling drift (real identifiers in publishable-tier files; found by the
    2026-07-19 aborted-mirror pre-publish grep) → **J13** (p1, fable, USER-GATED START — the
    user confirms the real-vs-synthetic term list before execution; the term list is recorded
    internal/-side only, never in publishable tiers; the backlog pull loop skips J13 until then).
  - [idea] file-ops READS_FROM/WRITES_TO extractor pass (G13's missing feed) → **G14**; the
    sibling [idea] surface-`WritePlan.unresolved_file_ops` line FOLDED into G14's acceptance
    (one item — the feed is what makes the counter worth reading).
  - [source] codeflow UI screenshot → MERGED into **O9** (inputs + notes). File already tracked
    at `UI-WIP/codeflow-ui-reference.png`; classification External, captured 2026-07-19 from
    https://github.com/braedonsaunders/codeflow/blob/main/screenshot.png (MIT-licensed repo) —
    cite, don't imitate branding.
  - kept-updated: the USER MANUAL STEP port-bundle line — the create half is done (bundle @
    3ae9b08 encoded + 3-way split); remaining: email the parts, far-side hash confirm, delete
    the five local transfer files.
  - kept parked, unchanged (each on its recorded gate): m3_invokes to_node broadening (next
    vocab gate session), ETLProcess kind discriminator (needs a discriminating signal),
    depgraph metric extensions (sibling-repo work), runbook-mapping-demo refit (L8),
    ETL-tooling inventory domain (direction), JobRun-index fold (provenance plan's next
    touch), SaaS scaffold research (triggers unfired), launcher-registry config-file
    migration, project-review outline (L8), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind
    → AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P4–P7
    (plan-tracked until Q4–Q6 land), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-19 — [bug] PAT seal_ids semicolon-delimiter mismatch → FIXED SAME-DAY (no backlog id,
  user call — pulled ahead of the catalog-pat team-report onboarding it was parked for):
  `PatProductMappingRow.seal_ids` now normalizes `;` → `,` before the cypher's comma split;
  synthetic sample row T0042 made semicolon-delimited to exercise the path; drift guard
  `test_row_model_normalizes_semicolon_seal_ids`; `internal/pat-evidence/README.md` note updated.

- 2026-07-19 — [chore] seal-sample standing exception → RETIRED EXECUTED SAME-DAY (no backlog id):
  user call — DELETE both `seal_*__sample.csv` twins from the tip rather than synthesize
  replacements (names were fictional; the seal_ids were real). App file e7f8f20 (user, web UI) +
  contacts twin this commit; classification.yaml carve-out removed; `drydocs/data/samples/**` is
  synthetic-only again. Residual: git HISTORY retains both files until a rewrite (user-gated).
  A future SEAL sample, if ever needed, gets synthetic ids (the pat_product_mapping pattern).

- 2026-07-18 — [task] C5-gate follow-up (promoted directly from the gate session):
  pat_product_mapping.cypher still writes the 2026-06-21-deprecated catalog_supports
  edge every load; SME supplied PAT screenshots in-session (Internal-Confidential,
  held out of the repo) showing teams map to 1..n business applications via the PAT
  team report while area-product alignment is volatile + relationship-typed — the
  deprecated edge may be independently asserted (the C5 exception path), so it re-gates
  rather than gets deleted blind → **C9** (p1, fable).

- 2026-07-18 — [bug] design-doc DUAL-HTML render (chat capture + screenshot, promoted
  directly): `.print.html` misrenders in-browser while the screen `.html` already
  print-adapts (white-on-black on screen, black-on-white at print) — SME call: one file
  suffices, retire the `.print.html` series (fold the L6 print-margin anchors into
  @media print) → **L13**. Evidence PNG at repo root, local-only (root-images
  gitignore). Related-not-merged: L9 (Chrome partial render of the screen html).

- 2026-07-18 groom run (weekly inbox groom, on `feat/mapping-store` — the 07-15 K4-branch
  precedent) — 5 promoted / 1 merged / 2 retired-executed / 2 re-inboxed slim / 1 kept-updated:
  - [idea] mapping-store research line → RETIRED EXECUTED-PRE-GROOM (the TechStack plan-07
    precedent — plan-tracked, not epic-itemized): M0–M4 + the wf-mapping-01 live demo BUILT on
    `feat/mapping-store` (807e050), deltas recorded in the plan doc header (store moved to
    drydocs_core; artifact-download submit; no new gates). Groom-touches: **O13** gains a
    progress record + the plan-§6 acceptance rider ("dropdowns read mapping.db via
    drydocs-api"); the plan's unwired M2 rebuild residual promoted → **O14** (staleness
    guard — a stale var/mapping.db serves stale grids until deleted). ETL-tooling inventory
    re-inboxed as its own slim line.
  - docmeta plan line (trigger fired 2026-07-16: P0 verdict = BUILD, Q3 done) → P1–P3
    promoted: **Q4** (gate session + docmeta ADR + planned vocab entries, reconciled against
    active docs_*; fable), **Q5** (doc-source registry ledger + guard test + stray-PDF
    sweep), **Q6** (Port A bkup→producer; module `drydocs-docmeta` REGISTERED as working
    name — final at the Q4 gate, the drydocs-api precedent). Line kept-updated: P4–P7 stay
    plan-tracked; GraphAcademy existence-constraints rider attached.
  - [question/idea/chore] GraphAcademy advisor line → dispositioned per sub-item:
    incremental delete-sweep → **D7**; BaseLoader index preflight EXECUTED PRE-GROOM
    (66049a0); DC-collision check ALREADY ROUTED to the internal-session checklist
    (66049a0/d21d4e5) — **P1 deliberately untouched this groom: its status flip is
    uncommitted in a concurrent Epic P session** (c12ab43 readout); graphrag-llm-navigation
    annotation + the save_data_model save were already done in-line; JobRun-index fold
    re-inboxed slim (provenance plan's next touch).
  - [idea] EE re-bootstrap demonstrable-content loads → MERGED into **D6** (the line's own
    suggestion): the quick-start/bootstrap sequence gains load-software-registry +
    load-bmc-docs (+ optional load-essential-graphrag); Q3's P0 spike already re-ran both
    loads once, proving the gap.
  - inboxed new: runbook-mapping-demo authored free-form pre-L8 (refit when L8 lands; the
    web-console TDD from the same session is auto-swept, nothing to do).
  - kept parked, unchanged (each on its recorded gate): SaaS scaffold research (direction;
    export-target/template-play triggers unfired), launcher-registry config-file migration,
    project-review outline (L8), K2 FID/ALIAS tables (company-side; fid-seal/alias-seal
    mapping domains now visibly registered-but-unavailable in the O13 demo), ctlm_id ripple,
    dry-docs.com seed, /documentation whitepaper type, lineage live-load gate (HITL),
    remediation slices (TDD §6/§7), Phase C packaging, Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME), BRD outline, EE container password,
    LLM key strategy, common/ cosmetic, cli.py regroup (v1.0 window).

- 2026-07-17 admin/steward surfaces groom — 2 promoted (chat captures + the fired
  launcher-line trigger): admin configuration page w/ generated enforcement matrix →
  **O12** (user decisions: CI last-run metadata; secrets .env-only so config renders
  verbatim); power-user manual-mapping stewardship screen (job→application, FID, ALIAS;
  gate-bound manual-loads changesets, zero graph writes; new steward persona) → **O13**.
  Wireframes wf-admin-config-01.* + wf-mapping-01.*; launcher-registry config-file
  migration still inboxed.

- 2026-07-17 site-plan groom — 4 promoted (O8–O11, Epic O phase 12), 2 inbox lines closed:
  - [idea] **UI DECISION: single-track ReUI, Salt DROPPED** (user call) + site plan
    (`UI-WIP/site-plan.md`: system-default 3-state theming dark-first, radial-hub landing,
    one module-subpage template × 9 modules, QuerySpec registry + two-path Neo4j
    data-frame export with provenance manifest/classification banners) → **O8** (shell +
    theme + routes), **O9** (landing + Explorer template), **O10** (Lineage canvas),
    **O11** (QuerySpec + export, module drydocs-api). Existing modules used — the plan's
    `drydocs-ui` module suggestion superseded (registry already names drydocs-web).
  - [idea] UI-stack proposal 2026-07-17 (ReUI free + React Flow + ADK 2.0 compat; Salt
    two-track addendum) → subsumed: stack table = site-plan §1; Salt track dropped by the
    same-day decision; ADK enablers (mcp.reui.io, @reui/skills-claude, AG-UI notes)
    preserved in site-plan §1 + memory. Site-plan §4 backend caveat corrected at groom:
    ADR 0005 ratified + drydocs-api shipped (O5), export endpoints land there.
- 2026-07-16 evening groom, part 2 (user decisions on the same-day [source] line) —
  2 promoted / 1 plan change (user-approved) / housing executed in-session:
  - PLAN CHANGE: new **phase 14 "Document ingestion & doc-graph benchmarks"** + **Epic Q**
    — the docmeta landing zone (AskUserQuestion-approved; the phase-12/13 idiom). The
    docmeta plan's P1+ phases groom here once the P0 verdict + docmeta ADR land.
  - [source] Essential GraphRAG (Manning / Neo4j-sponsored ebook, Bratanič & Hane,
    179 pp) → **Q1** (mine for applicable patterns at chapter level → docmeta P0 verdict
    input; answers "are there more examples of how to do it properly?") + **Q2**
    (Document→Chunk lexical-graph load + >=5-question agent-traversal experiment —
    vocabulary-reusing per the 07-08 bmc-docs gate, no new gate; target DB drydocs-vs-
    ddcontext decided at execution). HOUSING EXECUTED with the groom (user decisions:
    gitignore, publicly available): root-level `/*.pdf` blanket rule (root-images
    precedent; tracked UI-WIP/*.pdf unaffected) + reference/research/README.md seed-table
    row (Manning link verified 2026-07-16).
  - kept-updated: the docmeta plan line — phase 14 / Epic Q recorded as the landing zone
    for its P1–P3 promotions.

- 2026-07-16 evening groom (third run today; bare /groom-backlog, no new notes) —
  0 promoted / 1 inboxed / 0 merged; backlog database untouched (todo 23 / done 71 stand
  as of acf0bfe):
  - inboxed: `Essential-GraphRAG.pdf` found untracked at repo root (Manning / Neo4j-sponsored
    ebook, 179 pp, file dated 07-14) → new [source] line above — registration + housing
    (commit vs cite+gitignore) is a user decision; joins the JPMC annual-report PDFs in the
    untracked-root-PDF class noted at the 07-16 am groom.
  - all other lines kept parked, unchanged — every recorded gate was checked twice earlier
    today (am weekly run, pm post-merge run at acf0bfe); nothing has landed on main since.

- 2026-07-16 pm groom (second run today, post cmdline-lineage-review + the K4-branch merge) —
  2 promoted / 2 retired-executed / 1 line-update:
  - [idea] 2026-07-15 ETLProcess writer endpoint class (lineage vocab gate residual; the
    business-key half decided + implemented extractor-side at cmdline-lineage-review) →
    **G12**. [idea] 2026-07-15 writer file-ops resolution (same gate's second residual;
    endpoints per the gate EDIT: ETLProcess|ControlMJob → DataAsset) → **G13**. Both are
    the pre-flip curated-load-build blockers; shapes gate-confirmed so no HITL surface
    remains — sonnet items with written acceptance.
  - retired to this trail (fully executed/decided in-session, gate-log
    cmdline-lineage-review): the 07-16 [bug] CMDLINE parser gaps line (all four gaps
    closed same day: control-keyword stripping, runScript.sh -g pset payload expansion +
    case-fix, java/.jar + DPL rules, air rule; sanitized twins pinned) and the 07-16
    [question] gate-agenda line ((a)–(d) all decided; cross-machine reconcile with the
    07-15 vocab gate recorded at the b3c455f merge).
  - line-update: the K2 FID/ALIAS company-side line gains the folder-variable FID+SEAL
    co-location as a candidate FID→seal_id source (side finding from the live captures).
  - kept parked, unchanged: launcher-registry human-configurable (new today — trigger =
    web-console admin surfaces or Phase-E urgency); all other lines on their recorded
    gates (verified this morning, unchanged since).

- 2026-07-16 groom run (weekly inbox groom) — 0 promoted / 0 merged / 1 kept-updated;
  backlog database untouched (summary/next_ready stand as of 2026-07-15):
  - kept-updated: the docmeta plan line — **ADR number collision found + corrected**: the
    plan (2026-07-06) reserved "ADR 0004" for its P1 gate output, but 0004 was minted the
    next day as `0004-software-registry-vendor-terminology.md` (accepted 2026-07-07). The
    docmeta ADR now takes the next free number at authoring; the plan doc's 3 stale refs
    (`knowledge/upgrade-plans/docmeta-component.md` §1.1, P1 phase row, port table)
    annotated in the same commit.
  - gate checks run against the repo this pass: L8 still `todo` → project-review outline
    stays parked; docmeta P0 WRITTEN verdict still absent (only the ADR number changed);
    ADR 0005 ratified + O1/O3/O6 done ≠ any parked trigger.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (L8), K2 FID/ALIAS reconciliation tables (company-side sources), ctlm_id ripple checks
    (internal-side), dry-docs.com visual seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling),
    remediation next slices (TDD §6/§7), Phase C packaging (plan gate), Workbench
    (entitlement), SchedulerKind → AisCapability/AiTool (SME class definitions), BRD
    outline (later phase), docmeta P1–P3 (P0 verdict + the renumbered ADR), EE container
    password (user deferred), LLM key strategy (open question), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).
  - observation (no action): untracked UI-WIP/ website material (WEBSITE-IDEAS.MD,
    gemini-wire-frame.md, landing PNGs, icons.md) predates the 07-13 re-inbox of the
    dry-docs.com line and is its seed corpus when that gate fires; console-side UI-WIP
    files are O-epic surfaces. Root-level JPMC annual-report PDFs also untracked
    (data-context-extractor inputs — house them or gitignore at next touch).

- 2026-07-15 pm groom (on feat/k4-businessapplication-reshape) — 2 promoted, both
  same-day findings from the O6 session's first live EE bootstrap:
  - [bug] `Neo4jClient.run_script` inherits APOC's comment-`;` split (Cypher 25 rejects
    the empty fragment; loaders already guarded by `base.py::_code_semicolons`) → **D5**.
  - [chore] m3-verify fails on bundled samples — active folders 161020/160501 have no
    sample jobs → **D6** (add-jobs vs downgrade-to-warning left either/or, decided at
    execution).
  - groom-touch on **K4**: the branch feat/k4-businessapplication-reshape is reserved for
    it; the remote stub (40fe038, zero own commits, pre-K2) was re-based onto main a683384.

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
