-- =============================================================================
-- controlm_hosts.sql
--
-- Source table : psgmgr.CM_HOSTS  (replicated copy of the BMC node-group /
--                                  host-group membership structure — vendor
--                                  6.4.01 poster: CMS_NODGRP; governed access
--                                  via CM_RO_USER)
-- Projection   : all five columns (small object — full projection is the
--                stated use case, not speculation).
--
-- GATE-BOUND: the graph landing (ControlMHostGroup / ExecutionHost /
-- CONTAINS_HOST / RUNS_ON resolution) is proposed only — see
-- config/gate-prompts/controlm-hosts-topology.yaml. Until the SME confirms,
-- rows are staging-only (the CM_DEF_SETVAR_VW precedent).
--
-- Key schema findings (internal profile 2026-07-09 + column view):
--   * No IS_CURRENT_VERSION / VERSION_SERIAL — the object is NOT versioned;
--     no USER_DAILY either (grain is independent of folders/jobs).
--   * Volumes: 22 distinct DATA_CENTERs (incl. non-production) · 5,396
--     distinct GRPNAMEs · 8,161 distinct NODEIDs.
--   * DATA_CENTER carries LONG-FORM names (<Pnnn>-E<hhmm>-<suffix>, the
--     default-time encoding) — the value-domain match against
--     CM_DEF_VTAB.DATA_CENTER is an OPEN QUESTION (adhoc/profile_cm_hosts.sql
--     P3) gating the ControlMServer join.
--   * Grain assumed (DATA_CENTER, GRPNAME, NODEID) pending the P1 dup probe;
--     PARTICIPATION_TYPE domain pending P2a (observed 'P' only).
--
-- Load order: this extract is independent of folders/jobs. The job wiring —
-- RUNS_ON {role: host_group | agent_host} from CM_DEF_VJOB.NODE_ID, group
-- match wins — is a DERIVED resolution pass that runs only after BOTH the
-- jobs pass and this pass have loaded (the WAS_INFORMED_BY derived-pass
-- pattern). Use case: server-patching / maintenance-window planning.
--
-- Scope binds (optional, NULL = no filter): :grpname_filter (H.GRPNAME LIKE),
-- :row_cap (ROWNUM sample cap), :data_center_filter (H.DATA_CENTER LIKE —
-- G115; this column is long-form, so the family-shared long-form pattern
-- applies directly). :folder_filter / :run_as / :developer_sid do
-- not apply at this grain (no folder, owner, or author on CM_HOSTS).
-- =============================================================================

SELECT
    H.DATA_CENTER        AS data_center,        -- long-form DC name (22 distinct)
    H.GRPNAME            AS grpname,            -- host-group name; may itself be a DNS/LB alias
    H.NODEID             AS nodeid,             -- member agent host (FQDN)
    H.PARTICIPATION_TYPE AS participation_type, -- VARCHAR2(1); domain probe pending
    H.CAPTURE_DATE       AS capture_date        -- replication timestamp — never authorship
FROM   psgmgr.CM_HOSTS H
WHERE  (:grpname_filter     IS NULL OR H.GRPNAME     LIKE :grpname_filter)
  AND  (:data_center_filter IS NULL OR H.DATA_CENTER LIKE :data_center_filter)
  AND  (:row_cap            IS NULL OR ROWNUM         <=  :row_cap)
;
