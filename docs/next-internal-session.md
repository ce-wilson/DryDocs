# Next internal session — live-data confirmation checklist

> Generated 2026-07-16 from a backlog + gate-ledger sweep: every pending item whose
> blocker is **internal confirmation against live data** (live psgmgr, real extracts, or
> a live graph). Tick items here as they land, then groom outcomes back into
> `docs/restructure/backlog.yaml` / `config/gate-log.md` per the session ritual.
> Mechanism-only file: record conclusions, never paste real SIDs/hosts/data values here
> (real outputs go to `internal/` or `internal-local/`).

## The one-login batch (all four run in a single psgmgr session)

- [ ] **1. P1 — profiling probes + DC scope call** (backlog p1, ready)
      Run `drydocs/loaders/sql/adhoc/profile_cm_hosts.sql` and `profile_cm_avg_run.sql`
      against live psgmgr. Record conclusions per the P1 acceptance + make the DC scope
      call (all 4 production DCs vs pilot). While in CM_AVG_RUN: verify the extract
      exposes the derived `ctlm_id` column (P2 gate §B; probes P0/P4).
      → unblocks **P3** (hosts loader), **P4** (avg-run supplement), then **P5**
      (maintenance-window query); twins company tracker **T5**.

- [ ] **2. E1 re-arm — CM_HIST run-history source** (backlog in_progress, gate deferred 07-14)
      Confirm CM_HIST shape/retention on live psgmgr (JOB_MEM_NAME = JOB_NAME;
      MEMNAME is junk; DTSREMGR retired) as the jobrun-observation run-history source,
      then re-present the `sosa-jobrun-observation` gate.
      → unblocks **E2** (first context-graph query, phase 4).

- [ ] **3. K2 FID tier — folder-variable candidate probe** (new 2026-07-16)
      Count FID_D/FID_Q/FID_P + SEAL co-location across live folder variables (SEAL is
      also embedded in folder names): is a **FID → seal_id table derivable from
      Control-M itself**, instead of waiting on a company reference table?
      → potentially shortcuts company tracker **T2** (tier-2 reconciler wiring).

- [ ] **4. ctlm_id ripple sweep** (parked 07-14)
      One query per CM_ view/extract: which others carry the derived `ctlm_id`
      (`folder_id.job_id`) — candidates to replace weak (SCHED_TABLE, JOB_MEM_NAME)
      joins beyond CM_AVG_RUN.

## Live-graph work (needs a running graph, not psgmgr)

- [ ] **5. M2 — WAS_GENERATED_BY edge-diet migration** (backlog, ready)
      Destructive on an existing graph → HITL-confirm, then run the migration on the
      live/sandbox graph; backfill envelope props where recoverable; m3-verify updated.

- [ ] **6. Lineage live-load gate** (parked IDEAS line; the flips + first curated write)
      PRE-REQ (producer box, no live data): build **G12** (writer ETLProcess endpoint
      class) + **G13** (file-ops resolution) — both next_ready.
      THEN with a real extract: review `plan_curated` + the lineage-review page over
      real rows, flip the four `m3_*` entries planned → active with the supplement
      blocks, first curated write to `drydocs`.

## Desk work once live evidence is in hand

- [ ] **7. software-usage-patterns gate** (plan-07 P3, awaiting since 07-08)
      Confirm the 7 proposed invocation-pattern rows against live CMDLINE evidence
      (watch the `^m_` Informatica false-positive risk); fold in the decided
      DPL ≠ Ab Initio row from the 2026-07-16 `cmdline-lineage-review` gate.

- [ ] **8. M3 — SEAL + catalog audit envelopes** (backlog p3)
      Author the confidential source→column mappings internal-side from real extract
      headers; one per-source gate each (doc-06 pattern; public file gets stubs only).

## Company-machine tracker cross-reference (flip in THEIR port-prompt copy)

T1 live attribution load → T2/T3 FID/ALIAS tables (item 3 may shortcut T2) → T4 manual
CSVs as needed → T5 = item 1's twin → T6 docs Track-2 → T7 live multi-DB deploy →
T8 M0 equivalence ground truth (A3 watched filename + B1 dot rule).
