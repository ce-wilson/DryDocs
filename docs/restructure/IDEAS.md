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

- 2026-07-22 — [idea] **Email DLs need an ontology mapping (user, chat pm).** DL = the
  contact/notification channel for an app/team; only configured in Outlook (no feed,
  can't fix), witnessed in runbooks, extractable from emails; membership/usage are
  context-graph (layer 4) material. DRAFTED STRAIGHT TO GATE same session: gate prompt
  `config/gate-prompts/email-dl-contact-point.yaml` (class options vcard:Group vs
  prov:Agent; HAS_CONTACT_POINT dcat:contactPoint edge; store-as-source per the O24
  pattern; extraction-proposes-steward-disposes; layer-4 membership boundary) + map
  entry `dl-contact-point` (proposed). Grooming disposition: tracked at the gate —
  build items groomed on sign-off (§E1); nothing further parked here.

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
  app-code→SEAL mapping. Declared examples: ARA=111027 (CMH Advice R&A), SRV=110865
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
  HERE: only the property-diet rider above (folder node prop retirement — gate names it
  a separate decision) and the tier-2 platform-code enumeration (SME to supply).

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

- 2026-07-21 — [question] **Gate rider (from G17 build): MAC subType → kind-enum
  semantics.** pipeline.json `subType=provisioning` (DB load, no transform — runtime
  trace) is wrong-by-signal as `kind='etl'`, but the fix is an enum decision the
  build must not make: EXTEND the gate-log 2026-07-16 §a enum
  (etl|utility|notification → +provisioning?) or MAP provisioning to `utility`?
  Until ruled, the dpl_mac extractor takes the rider path (no `mac_kind`; stamps
  `mac_kind_rider`, counts `kind_riders`; writer default stands). Any OTHER
  unmapped subType value rides the same path — the derivation table
  (`dpl_mac._KIND_BY_SUBTYPE`) only carries enum-safe entries. Decide at the next
  lineage gate session (the live-load flips / G22 sits closest).

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

- 2026-07-19 — [question] **m3_invokes `to_node: Script` may need broadening to
  `Script | ETLProcess`** in relationship_vocabulary.yaml: the abioncloud wrapper-payload
  expansion (`runScript.sh -g <pset>` → the ABINITIO invocation replaces the wrapper's)
  means INVOKES sometimes lands directly on an :ETLProcess endpoint with no Script hop —
  G12 implements exactly that (fixture job 25 → trust.pset). Vocabulary-shape decision →
  next gate session, not an auto-edit. (G12 subagent finding.)
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
