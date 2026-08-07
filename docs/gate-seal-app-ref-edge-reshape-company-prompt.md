# Company-side prompt — the `seal-app-ref-edge-reshape` ratification gate

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> This is the gate your own vocabulary hold names: `m3_belongs_to_application` is
> "PLANNED/inert pending a company gate that supersedes-or-reconciles" your signed
> K5/K2 job-grain position. **This session IS that gate.** Producer facts were
> verified against `cewilson/main` (gate-log entry 2026-08-03; vocab + loader state
> as of the K8 build `2026-08-04`).

Venue: company `<org>/DryDocs`. Run on `drydocs-port-20260806` (7 commits, unmerged)
or on `main` if the SME merged first — name which in every claim (J18). Durable note:
`/memories/repo/port-a14a8028-owed-failures.md` — the WP2 ×6 deferrals close here.

## What this session is (and is not)

The producer gate `seal-app-ref-edge-reshape` was **SIGNED OFF 2026-08-03, 24/24**
(SME chad.wilson; producer `config/gate-log.md`; spec v3
`config/gate-prompts/seal-app-ref-edge-reshape.yaml`). Under the two-tier doctrine
that is NOT your sign-off. This session runs the **company ratification**: walk the
producer's per-item outcomes, ratify / edit / refuse each, union-append the entry to
YOUR `config/gate-log.md`, and — on ratification — execute the held WP2 build unit.
The same person signs both sides; the two gate-logs are still separate records.

An edit that changes meaning is a **registered divergence**, not a silent fork.

## The producer ruling you are ratifying (summary — the gate-log entry is authority)

Grain and shape:
- **A1** — attribution grain is FOLDER; jobs inherit via `CONTAINS_JOB`; no per-job
  application edge authored going forward.
- **C1(b)** — tier-1 target is the application's **BatchProcessing `:Port`**, not
  `:BusinessApplication` (supernode avoidance: the app node already hubs TOM roles,
  contacts, product links, orchestrator edges).
- **D1(a)** — LOCAL edge **`BELONGS_TO_APPLICATION`**, `prov_maps_to: ~` (no natural
  PROV verb for Entity→Entity containment); props kept: `role=seal_app_ref`,
  `first_seen_at`, `source`, `match_method`, `last_seen_at`. **D2** — ONE shape
  everywhere: loader, manual tier-5 writer, migration target.
- **C2** — the `:Batch` bridge (`arch_contains_batch`/`arch_contains_folder`) RETIRED
  (`planned` → `deprecated`; an authorized downgrade — do not let no-downgrade guards
  red it; the gate entry is the authority, producer guard-scope note precedent).

Authoring:
- **B1** — ONE mechanism: steward-defined rows per Control-M app code; the loader
  fans out to folders via `CONTAINS_FOLDER`. New folders inherit at appearance.
- **B2 (amended in session)** — **THREE row kinds**, not two: tier 1 seal-born (1:1
  code→application), tier 2 shared platform (per-folder resolution, surfaced never
  auto-picked), **tier 3 dual-coded/migrating** (declared WITH an explicit end state
  so a stalled migration cannot become permanent ambiguity).
- **B3** — your K5/K2 fuzzy match policy DEMOTES to fallback for codes with no
  defined row; its internals are NOT re-opened; every fallback value is DISCLOSED
  via the origin flag (`defined` | `matched-fallback` | `override` | `manual-pin`).
- In-session rulings: **OWNER-NOT-USER** (a folder belongs to whoever OWNS it — a
  platform team's all-tenants utility folder attributes to the platform team's
  application); **folder→application is 1:1**, a second edge is a DEFECT, enforced
  as a graph-test; **`:AreaProduct` is a ROUTING step, never an edge target**.

Overrides and write path:
- **E1/E3** — O24 origin-flagged store verbatim; the loader stays the only graph
  writer. **E2** — defined rows ARE graph-loadable source of record, and overrides
  **may be PERMANENT in this domain** (permanence is domain-dependent; the general
  override-vs-precedence question stays open elsewhere).

Companion §G (the mapping act):
- **G1** — orchestrator-first: the confirmed mapping AUTHORS
  `USES_SOFTWARE {role: orchestrator}`. **G2** — the SEAL-declared string demotes to
  prefill; existing declared edges KEPT with `origin=declared` until superseded —
  no cleanup sweep. **G3** — orchestrator cardinality 1:N, graph-test never a
  constraint; mid-migration is normal, not drift. **G4(b)** — `active_state`
  per PORT (`declared`|`confirmed`) replaces the boolean, with
  `declared_by/at` + `confirmed_by/at/run_id`. **G5** — under C1(b) port
  confirmation is derivable from the folder edge; EVENT port stays declared-only.
  **G7** — approval notes/user/date ARE the O13 rationale chips and become edge
  provenance; folder filter = unmapped-only, naming-pattern optional;
  `run_as_user` as a sort option.
- **G6 — YOUR reading won**: `(:Product)-[:HAS_APPLICATION]->` is the structural
  SUPPORT link (a Product supported by 2+ applications), chosen over the producer's
  "owns a set of SEAL-registered applications" because yours is backed by a live
  extract and loader. Picker returns a LIST. Producer reconciles as back-flow.

Producer reference implementations (diff, don't re-derive):
`drydocs_core/manual_mappings.py` (K8 `SUPPORTED_SHAPE` + error wording),
`drydocs_core/ontology/relationship_vocabulary/40-local-controlm.yaml`
(`m3_seal_app_ref` → **deprecated**, `m3_belongs_to_application` → **active**, full
ruling in its note), `drydocs/loaders/.../folder_attribution.cypher`, `K2_SHAPE` in
`drydocs_api/mappings.py`, `graph-tests/folder-attribution-coverage.yaml` (the 1:1
test).

## What the producer could NOT decide for you — rule these yourself

1. **G4-RIDER premise check.** The grandfather ruling ("ports active by derivation
   → `confirmed`, provenance = the app-code link, NO disambiguation pass") rests on
   the premise that the deriving orchestrator is unambiguous because the initial
   series loads Control-M only. Your graph has **TWO** active-writers
   (`controlm_app_codes.cypher` + the AutoSys twin). Verify on your live graph
   whether any port is active by the AutoSys writer. If yes, the no-disambiguation
   clause fails on your side: rule a disambiguation pass (which writer flipped it →
   which orchestrator's confirmation it grandfathers as) instead of inheriting the
   clause. Venue the check.
2. **Your real tier rows.** Enumerate your tier-1 / tier-2 / tier-3 app-code rows
   (Internal; they never flow back to the producer — mechanism-only in any report).
   The defined-mapping LOADER cannot run before this enumeration exists; landing it
   held/absent until then is a legitimate staged adoption — say which you chose.
3. **E2 permanence and tier-3 end states** — confirm they match your operational
   reality; both were decided on producer-side SME facts.
4. **The F1/T23 migration is YOURS** (producer-side it was moot under
   wipe-and-rebuild). The recorded sequence: partial-doubling check (the 2026-08-04
   crash) → DROP `port_unique` FIRST → backfill `app_id = seal_id` on pre-cutover
   nodes → the S10 guard (all five of your `:BusinessApplication` MERGE sites,
   including `PatAppLinksLoader`) refuses until nulls clear → migrate live K2 job
   edges to folder grain **preserving every property including manual pins** → all
   8 key-bearing sites in ONE apply → re-run T1. This MAY stay its own later
   session — if so the durable note says "deferred" in those words (rule 6); a
   green suite is not a performed migration.

## The build unit (only after §H ratifies — one tight commit series)

a. **Vocabulary flip**: `m3_belongs_to_application` `planned` → `active`, the
   COMPANY HOLD note replaced by a citation of your ratification entry;
   `m3_seal_app_ref` demoted per your ruling (authorized downgrade — cite the entry
   so no-downgrade guards don't red it). This is what discharges the hold's
   "supersedes-or-reconciles" language — your entry should say it supersedes the
   K5/K2 job-grain position explicitly.
b. **Writer reshape**: diff your EXTENDED `manual_mappings` writer against the
   producer reference; flip `SUPPORTED_SHAPE` + `ManualMappingRow` to K8
   folder-grain, preserving your company extensions.
c. **K18 rider in the same unit**: `tier` → `row_kind` on CSV header, store column,
   and edge property; tier-authored rows re-author; platform code-level rows now
   require the platform's own `app_id` + rationale.
d. **Tier-5 CSV key cells**: convert per the composite-key serialization standard
   (producer step 62) in the SAME commit as the parse flip.
e. **Tests**: the WP2 ×6 (`test_mapping_store` ×5 + `test_mapping_api`) green on
   fixtures. Expected suite **7 → 1 failed** (~1871 / 1 / 31 — the remaining 1 is
   the WP1.4 infra-blocked deferral, unchanged). Quote real numbers with venue.

## Rules in force

1. Per-item outcomes in your gate-log entry (A1–H, including the in-session
   rulings) — ratified / edited / refused, with edits registered as divergences.
2. Fix data/code, never test-edit; the producer guards are the contract.
3. Real code→SEAL rows, SIDs, server names stay Internal on your side; anything
   reported back to the producer is mechanism-only.
4. Venue every claim (J18).
5. One commit per concern; quote the suite delta in each report-back message.
6. A green suite is not a performed migration — deferred means the word "deferred"
   in the durable note.

## Close-out

- Gate-log entry appended; vocabulary flipped; WP2 ×6 FIXED-with-commit in the
  durable note; the T23 live-graph migration either RUN (venued evidence) or
  DEFERRED in words.
- Report back: per-item edits/divergences, the G4-RIDER premise-check result, the
  loader staging choice, tier-row enumeration status (count only), and anything the
  producer should ledger — the G6 semantics reconciliation is already queued as a
  producer back-flow item.
- Then stop. The `--no-ff` merge (if still pending) and the T23 migration scheduling
  are the SME's decisions, not yours.
