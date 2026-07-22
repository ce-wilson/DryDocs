# Next internal session — live-data confirmation checklist

> Generated 2026-07-16 from a backlog + gate-ledger sweep: every pending item whose
> blocker is **internal confirmation against live data** (live psgmgr, real extracts, or
> a live graph). Tick items here as they land, then groom outcomes back into
> `docs/restructure/backlog.yaml` / `config/gate-log.md` per the session ritual.
> Mechanism-only file: record conclusions, never paste real SIDs/hosts/data values here
> (real outputs go to `internal/` or `internal-local/`).

## The one-login batch (all five run in a single psgmgr session)

- [x] **1. P1 — profiling probes + DC scope call** (backlog p1, ready)
      Run `drydocs/loaders/sql/adhoc/profile_cm_hosts.sql` and `profile_cm_avg_run.sql`
      against live psgmgr. Record conclusions per the P1 acceptance + make the DC scope
      call (all 4 production DCs vs pilot). While in CM_AVG_RUN: verify the extract
      exposes the derived `ctlm_id` column (P2 gate §B; probes P0/P4).
      → unblocks **P3** (hosts loader), **P4** (avg-run supplement), then **P5**
      (maintenance-window query); twins company tracker **T5**.
      *LANDED 2026-07-17:* company commit `422534f` (pushed) — a surgical partial commit:
      P1→`done` + new item K6 only, exactly 3 files (`backlog.yaml`, board, IDEAS);
      `controlm_avg_run*` loader files and the P4/P2/P3/P5 flips deliberately stay as
      Epic P working-tree WIP (P4 commits alongside the avg-run loader when it lands).
      ~~STILL OWED producer-side: the probe conclusions + the **DC scope call outcome**
      have not been relayed here — grab them next internal session; item 5
      (DC-collision check) inherits whatever that scope call decided.~~
      *RELAYED 2026-07-22 (screenshot channel, 26 captures — PARTIAL):* the
      **preflight open questions** (Q0.1/Q0.2/Q2/Q3/Q4 — all answered, annotated in
      `preflight_open_questions.sql`) and the **CM_AVG_RUN set end to end**
      (pilot Q0–Q5 + estate P0–P8, incl. an ORA-01722 fix to P3a now back-ported)
      — conclusions transcribed into `profile_cm_avg_run.sql`, the avg-run gate
      spec's additive provenance block, and the CM_AVG_RUN ledger census
      (26 columns; **no ctlm_id column on CM_AVG_RUN** — the P2-gate §B verify
      came back NEGATIVE for this table). STILL OWED: the **CM_HOSTS
      definition-side probes** (`profile_cm_hosts.sql` P1–P5 — only the runtime
      census landed, via avg-run P5) **+ the DC scope call** (now three
      datapoints: 22 DCs in CM_HOSTS, 14 in CM_AVG_RUN, 4 production) — both
      remain HITL/next-internal items; item 5 still inherits the scope call.
      NEW HITL residuals for the P4-loader build: grain dedupe rule (dups 2–49;
      STAT_PERIOD candidate), run-time sanity cap (outliers to ~2.65 y),
      ctlm_id-absence join consequence.

- [ ] **2. E1 re-arm — CM_HIST run-history source** (backlog in_progress, gate deferred 07-14)
      Confirm CM_HIST shape/retention on live psgmgr (JOB_MEM_NAME = JOB_NAME;
      MEMNAME is junk; DTSREMGR retired) as the jobrun-observation run-history source,
      then re-present the `sosa-jobrun-observation` gate.
      → unblocks **E2** (first context-graph query, phase 4).
      *Internal readout 2026-07-17:* unchanged — `in_progress`, gate-bound (terms stay
      `planned` until the SME confirms).

- [ ] **3. K2 FID tier — folder-variable candidate probe** (new 2026-07-16)
      Count FID_D/FID_Q/FID_P + SEAL co-location across live folder variables (SEAL is
      also embedded in folder names): is a **FID → seal_id table derivable from
      Control-M itself**, instead of waiting on a company reference table?
      → potentially shortcuts company tracker **T2** (tier-2 reconciler wiring).
      *Internal readout 2026-07-17:* probe not yet run. Company side PROMOTED the
      follow-up in `422534f` as backlog **K6** ("SEAL attribution FID + ALIAS
      reconciliation tiers — source the tables, wire the TierReconcilers"; seal-attribution
      epic, `depends_on: [K2]`, `next_ready`, **no gate** — the m3_seal_app_ref match
      policy is already active from K2; tier precedence SEAL > FID > APP_NAME > ALIAS).
      The folder-variable candidate source moved from their IDEAS inbox into K6's audit
      trail — so THIS probe is now K6's "source the FID table" candidate path; tracker
      rows T2/T3 stay open until K6 ships.

- [ ] **4. ctlm_id ripple sweep** (parked 07-14)
      One query per CM_ view/extract: which others carry the derived `ctlm_id`
      (`folder_id.job_id`) — candidates to replace weak (SCHED_TABLE, JOB_MEM_NAME)
      joins beyond CM_AVG_RUN.

- [ ] **5. DC-collision identity check** (new 2026-07-17; advisor-confirmation §2a — HIGH,
      blocks any multi-DC load)
      `SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) FROM psgmgr.CM_DEF_VTAB GROUP BY
      TABLE_ID HAVING COUNT(DISTINCT DATA_CENTER) > 1;` — staging keys by
      `(data_center, folder_id, job_id)` but graph identity is `(folder_id, job_id)` /
      folder by `folder_id` alone. Zero rows → document the uniqueness invariant in
      `controlm_folders.cypher`; any rows → cross-DC nodes would silently merge, and the
      fix is an identity change (`data_center` into the folder + job keys) → **HITL gate**
      + constraint migration. The P012 single-DC pilot cannot expose this. Feeds item 1's
      DC scope call.

## Live-graph work (needs a running graph, not psgmgr)

- [x] **6. M2 — WAS_GENERATED_BY edge-diet migration** (backlog, ready)
      Destructive on an existing graph → HITL-confirm, then run the migration on the
      live/sandbox graph; backfill envelope props where recoverable; m3-verify updated.
      *Internal readout 2026-07-17:* still `todo` company-side (`depends_on: M1`).
      *DONE producer-side 2026-07-21:* migration HITL-confirmed + run live (0 blanket
      edges, 8 raw-prop retirements, 816 renames; m3-verify all green; idempotent
      re-run verified). Company-side twin remains open on their tracker.

- [ ] **7. Lineage live-load gate** (parked IDEAS line; the flips + first curated write)
      PRE-REQ (producer box, no live data): build **G12** (writer ETLProcess endpoint
      class) + **G13** (file-ops resolution) — both next_ready.
      THEN with a real extract: review `plan_curated` + the lineage-review page over
      real rows, flip the four `m3_*` entries planned → active with the supplement
      blocks, first curated write to `drydocs`.

## Desk work once live evidence is in hand

- [ ] **8. software-usage-patterns gate** (plan-07 P3, awaiting since 07-08)
      Confirm the 7 proposed invocation-pattern rows against live CMDLINE evidence
      (watch the `^m_` Informatica false-positive risk); fold in the decided
      DPL ≠ Ab Initio row from the 2026-07-16 `cmdline-lineage-review` gate.

- [ ] **9. M3 — SEAL + catalog audit envelopes** (backlog p3)
      Author the confidential source→column mappings internal-side from real extract
      headers; one per-source gate each (doc-06 pattern; public file gets stubs only).

## Company-machine tracker cross-reference (flip in THEIR port-prompt copy)

T1 live attribution load → T2/T3 FID/ALIAS tables (item 3 may shortcut T2) → T4 manual
CSVs as needed → T5 = item 1's twin → T6 docs Track-2 → T7 live multi-DB deploy →
T8 M0 equivalence ground truth (A3 watched filename + B1 dot rule).
