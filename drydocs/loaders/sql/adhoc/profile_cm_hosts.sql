-- =============================================================================
-- profile_cm_hosts.sql  —  run internally in SQL Developer against psgmgr
--
-- Profiles psgmgr.CM_HOSTS — the company replica of the BMC node-group /
-- host-group membership structure (vendor 6.4.01 poster: CMS_NODGRP; agent
-- identity CMS_NODID / CMR_NODES is NOT replicated). Shape (column view):
--   CAPTURE_DATE DATE · DATA_CENTER VARCHAR2(20) · GRPNAME VARCHAR2(512)
--   · NODEID VARCHAR2(512) · PARTICIPATION_TYPE VARCHAR2(1)
--
-- INITIAL PASS ALREADY RUN (internal, 2026-07-09):
--   22 distinct DATA_CENTERs · 5,396 distinct GRPNAMEs · 8,161 distinct NODEIDs
--
-- Remaining probes below feed the controlm-hosts-topology gate
-- (config/gate-prompts/controlm-hosts-topology.yaml). Read-only. Do NOT
-- commit result rows (group/host names are Internal-Confidential) — record
-- conclusions only. Probe order follows the oracle-db skill schema-discovery
-- sequence: object → grain → value domains → cross-object join coverage.
-- =============================================================================

-- P0. Object type (table vs view vs synonym) + authoritative column census.
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'PSGMGR' AND object_name = 'CM_HOSTS';

SELECT column_id, column_name,
       data_type ||
         CASE WHEN data_type IN ('VARCHAR2','NVARCHAR2','CHAR')
              THEN '(' || data_length || ')' END AS full_type,
       nullable
FROM   all_tab_columns
WHERE  owner = 'PSGMGR' AND table_name = 'CM_HOSTS'
ORDER  BY column_id;

-- P1. GRAIN CHECK — is (DATA_CENTER, GRPNAME, NODEID) unique? The vendor PK
--     (CMS_NODGRP) is (GRPNAME, NODEID, TIMESTMP); the replica dropped
--     TIMESTMP. Rows back = history/dup rows survived the copy and the
--     loader must dedupe (see P5 CAPTURE_DATE).
SELECT DATA_CENTER, GRPNAME, NODEID, COUNT(*) AS dup_count
FROM   psgmgr.CM_HOSTS
GROUP  BY DATA_CENTER, GRPNAME, NODEID
HAVING COUNT(*) > 1
FETCH  FIRST 20 ROWS ONLY;

-- P2. Value domains.
-- P2a. PARTICIPATION_TYPE (observed 'P' so far — confirm the full domain;
--      BMC semantics per code = reference-librarian follow-up).
SELECT PARTICIPATION_TYPE, COUNT(*) AS cnt
FROM   psgmgr.CM_HOSTS
GROUP  BY PARTICIPATION_TYPE
ORDER  BY cnt DESC;

-- P2b. Group fan-out (how much the 2-hop model carries) + how many group
--      names are DNS aliases (load-balancer-URL-as-group-name pattern) vs
--      logical codes.
SELECT MIN(members) AS min_members, MEDIAN(members) AS median_members,
       MAX(members) AS max_members
FROM  (SELECT DATA_CENTER, GRPNAME, COUNT(DISTINCT NODEID) AS members
       FROM   psgmgr.CM_HOSTS
       GROUP  BY DATA_CENTER, GRPNAME);

SELECT CASE WHEN INSTR(GRPNAME, '.') > 0 THEN 'DNS_ALIAS' ELSE 'LOGICAL' END AS group_kind,
       COUNT(DISTINCT GRPNAME) AS groups
FROM   psgmgr.CM_HOSTS
GROUP  BY CASE WHEN INSTR(GRPNAME, '.') > 0 THEN 'DNS_ALIAS' ELSE 'LOGICAL' END;

-- P2c. Hosts serving more than one group (decides whether ExecutionHost
--      keyed on NODEID alone is safe — expected for shared/DR agents).
SELECT COUNT(*) AS multi_group_hosts
FROM  (SELECT NODEID
       FROM   psgmgr.CM_HOSTS
       GROUP  BY NODEID
       HAVING COUNT(DISTINCT DATA_CENTER || '|' || GRPNAME) > 1);

-- P3. DATA_CENTER VALUE-DOMAIN MATCH vs CM_DEF_VTAB — the join-key question.
--     CM_HOSTS shows long-form DC names (<Pnnn>-E<hhmm>-<suffix>); 22 distinct
--     (incl. non-production). If the two sets differ, the ControlMServer
--     node key needs a normalization rule (e.g. leading segment) — gate item.
SELECT DATA_CENTER FROM psgmgr.CM_HOSTS
MINUS
SELECT DATA_CENTER FROM psgmgr.CM_DEF_VTAB;

SELECT DATA_CENTER FROM psgmgr.CM_DEF_VTAB
MINUS
SELECT DATA_CENTER FROM psgmgr.CM_HOSTS;

-- P4. THE ONTOLOGY-VALIDATING PROBE — CM_DEF_VJOB.NODE_ID resolution census.
--     Classifies every current-version job's NODE_ID:
--       GROUP     → matches a GRPNAME           (2-hop: job → host group → hosts)
--       DIRECT    → matches a member NODEID only (1-hop: hard-coded host)
--       BOTH      → group/host name collision (should be zero; if not, the
--                   'group match wins' precedence needs explicit SME sign-off)
--       UNMATCHED → in neither (agent in no group, or a normalization gap)
--       NULL      → job has no NODE_ID
--     DC predicate intentionally omitted until P3 resolves the value domains;
--     re-run with it once the normalization rule is known.
SELECT CASE
         WHEN J.NODE_ID IS NULL THEN 'NULL'
         WHEN G.GRPNAME IS NOT NULL AND N.NODEID IS NOT NULL THEN 'BOTH'
         WHEN G.GRPNAME IS NOT NULL THEN 'GROUP'
         WHEN N.NODEID  IS NOT NULL THEN 'DIRECT'
         ELSE 'UNMATCHED'
       END      AS node_id_resolution,
       COUNT(*) AS jobs
FROM   psgmgr.CM_DEF_VJOB J
LEFT JOIN (SELECT DISTINCT GRPNAME FROM psgmgr.CM_HOSTS) G ON G.GRPNAME = J.NODE_ID
LEFT JOIN (SELECT DISTINCT NODEID  FROM psgmgr.CM_HOSTS) N ON N.NODEID  = J.NODE_ID
WHERE  J.IS_CURRENT_VERSION = 'Y'
GROUP  BY CASE
            WHEN J.NODE_ID IS NULL THEN 'NULL'
            WHEN G.GRPNAME IS NOT NULL AND N.NODEID IS NOT NULL THEN 'BOTH'
            WHEN G.GRPNAME IS NOT NULL THEN 'GROUP'
            WHEN N.NODEID  IS NOT NULL THEN 'DIRECT'
            ELSE 'UNMATCHED'
          END
ORDER  BY jobs DESC;

-- P4b. Eyeball the UNMATCHED long tail (case/whitespace variants, retired
--      agents, z/OS-style targets). Conclusions only — never commit values.
SELECT J.NODE_ID, COUNT(*) AS jobs
FROM   psgmgr.CM_DEF_VJOB J
WHERE  J.IS_CURRENT_VERSION = 'Y'
  AND  J.NODE_ID IS NOT NULL
  AND  NOT EXISTS (SELECT 1 FROM psgmgr.CM_HOSTS H
                   WHERE H.GRPNAME = J.NODE_ID OR H.NODEID = J.NODE_ID)
GROUP  BY J.NODE_ID
ORDER  BY jobs DESC
FETCH  FIRST 30 ROWS ONLY;

-- P4c. Case-fold check: if upper_matches > exact_matches the resolution pass
--      needs a case-normalization rule.
SELECT COUNT(CASE WHEN H.GRPNAME = J.NODE_ID THEN 1 END)               AS exact_matches,
       COUNT(CASE WHEN UPPER(H.GRPNAME) = UPPER(J.NODE_ID) THEN 1 END) AS upper_matches
FROM   psgmgr.CM_DEF_VJOB J
JOIN   psgmgr.CM_HOSTS H ON UPPER(H.GRPNAME) = UPPER(J.NODE_ID)
WHERE  J.IS_CURRENT_VERSION = 'Y';

-- P5. Is CAPTURE_DATE uniform per snapshot (same question as jobs-extract Q2)?
--     distinct_caps = 1 → snapshot stamp, not a change signal.
SELECT COUNT(DISTINCT CAPTURE_DATE) AS distinct_caps,
       MIN(CAPTURE_DATE) AS min_cap, MAX(CAPTURE_DATE) AS max_cap
FROM   psgmgr.CM_HOSTS;
