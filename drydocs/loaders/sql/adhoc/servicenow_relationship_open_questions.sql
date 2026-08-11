-- =============================================================================
-- servicenow_relationship_open_questions.sql
--   — run in DBeaver against the ServiceNow replica (carrier: Snowflake)
--
-- Answers the OPEN relationship-mapping questions in
-- knowledge/upgrade-plans/servicenow-replica-evidence.md (K21 §6), which feed
-- gates `tom-roles-enumeration-and-cardinality` (G35) and
-- `seal-tom-attribution-reshape`. Read-only probes — every statement is a
-- SELECT; nothing here writes, and no source is activated by running it.
--
-- ANNOTATE IN PLACE. Add `[ANSWERED <date>]` + the conclusion above each block
-- as it resolves, exactly as preflight_open_questions.sql does for psgmgr.
-- Do NOT commit result ROWS — they are Internal (CI names, SEAL ids, company
-- values, sys_id GUIDs). Commit conclusions and counts only.
--
-- RUN ORDER MATTERS. §A gates everything: if the replica is an incomplete
-- projection, every other answer here is measured against a partial copy.
-- =============================================================================
-- DIALECT: Snowflake, because the CARRIER is Snowflake. This is a property of
-- the carrier, never of ServiceNow — the same way psgmgr extraction SQL is
-- Oracle-shaped (K21 §1.5(3)).
--
-- IDENTIFIER CASE — THE RULE THAT DECIDES WHETHER ANY OF THIS RUNS.
-- Snowflake folds UNQUOTED identifiers to UPPERCASE and matches quoted ones
-- literally. This replica is MIXED, and the two halves go opposite ways:
--
--     VIEW names are stored UPPERCASE  -> write them unquoted:  V_CMDB_REL_CI
--     COLUMN names are stored lowercase -> write them QUOTED:   r."sys_id"
--
-- Evidence, from the SME's own working query and the DBeaver navigator: the
-- query writes tables unquoted and lowercase (<cmdb_schema>.v_cmdb_ci, which
-- folds up and matches) while quoting EVERY column in lowercase
-- (tom_main."number", resp."active", cmdbci."sys_class_name"). Those two
-- choices only coexist if views are uppercase and columns are not. The
-- navigator agrees: it lists V_CMDB_REL_CI in caps with parent / u_hash /
-- sys_updated_on beneath it in lower.
--
-- WHY IT MATTERS MORE THAN IT LOOKS. An unquoted column reference fails LOUDLY
-- (invalid identifier) and is easy to fix at the keyboard. But the same mistake
-- inside an INFORMATION_SCHEMA predicate fails SILENTLY: comparing column_name
-- against an UPPERCASE literal simply matches nothing, so §B1 would report that
-- the replica has no parent_descriptor — the exact false negative that triggers
-- K21 §3.3's fallback rule and would send the crosswalk off to split `name` on
-- '::' for no reason. Every INFORMATION_SCHEMA comparison below is therefore
-- wrapped in UPPER(), which is correct whichever way the identifiers are stored.
-- =============================================================================
-- HAND-EDIT BLOCK — the ONLY lines carrying Internal values. Fill these three,
-- run, and never commit the filled file (K21 §0; the values are Internal —
-- replica host, database, schema names and the company scope string).
--
-- Everything downstream reads these variables, so the scope string is written
-- ONCE here rather than in each of the five TOM references it used to appear in.
-- =============================================================================

SET replica_db  = '<DB>';            -- the replica database
SET cmdb_schema = '<CMDB_SCHEMA>';   -- the common/CMDB DW_*_DATA_VIEW schema (§2.2)
SET tom_scope   = '<SCOPE>';         -- the company string filling ServiceNow's x_<scope>_ prefix

-- Derived — do not edit. View naming rule (§2.1): V_ + the ServiceNow table
-- name, uppercased; scoped-app tables keep their x_<scope>_ prefix INSIDE the
-- view name.
SET v_tom_main  = 'V_X_' || UPPER($tom_scope) || '_CMDB_TOM_MAIN';
SET v_tom_roles = 'V_X_' || UPPER($tom_scope) || '_CMDB_TOM_ROLES';

USE DATABASE IDENTIFIER($replica_db);
USE SCHEMA   IDENTIFIER($cmdb_schema);

-- Sanity check before anything else — confirms the three variables resolved and
-- that the session is pointed where you think it is.
SELECT CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS schema,
       $v_tom_main        AS tom_main_view, $v_tom_roles AS tom_roles_view;

-- FALLBACK: if IDENTIFIER($var) is rejected in a FROM clause on this account,
-- drop the SET block and hand-substitute the literal view names instead — the
-- affected lines are §D1, §E1, §E2, §E3 and §E4, and they are the only ones.


-- #############################################################################
-- [ANSWERED 2026-08-11] §A VERDICT: NOT A CLEAN COPY — BUT NOT A FILTERED ONE
-- EITHER, AND THE DIFFERENCE DECIDES WHAT IT MEANS.
--   A1  843 dangling type refs.
--   A2  970 dangling parent CIs, 9,093 dangling child CIs, 4,431,314 edges.
--   A3  V_CMDB_REL_CI    4,431,328 rows, authorship lag 2 days.
--       V_CMDB_REL_TYPE         54 rows, last AUTHORED 2022-05-26, last CARRIER
--                                  LOAD 2026-04-15 -> lag 1,420 days.
--       V_CMDB_CI      21,601,633 rows, authorship lag 0 days.
--   A4  delete_flag = 'N' on all 54 type rows.
-- READ IT THIS WAY. The dangling counts are 0.02% of edges (843 and 970) and
-- 0.2% (9,093). A FILTERED view does not come out 99.98% complete — that is the
-- signature of SOURCE-SIDE ORPHANS, which ServiceNow is independently known for
-- (deleted CIs leaving cmdb_rel_ci rows behind). So the replica is faithful and
-- the CMDB itself carries referential drift.
-- THE ONE REAL STALENESS IS THE TYPE VIEW: its carrier load is FOUR MONTHS
-- behind the edge view's. Upstream it has not been authored since 2022, so a
-- stable vocabulary explains the old authorship date — but not the old LOAD
-- date, which is the carrier refreshing that view on a different cadence.
-- CONSEQUENCES, both of which hold whatever the cause: (1) a loader MUST handle
-- an unresolvable parent/child/type — skip or tombstone, never assume. (2) Row
-- counts DRIFT WITHIN A SESSION (4,431,314 / 4,431,328 / 4,431,668 across three
-- runs minutes apart), so never compare two counts taken at different moments
-- as though they were stable.
-- #############################################################################
-- §A — Q9. IS THE REPLICA A COMPLETE COPY, OR A FILTERED / STALE PROJECTION?
--          Outranks everything else here (§6 Q9). Run first; if A1/A2 return
--          non-zero, stop and raise it before ruling any pull scope.
-- #############################################################################

-- A1. Dangling edge -> type. Proves incompleteness FROM THE INSIDE, with no
--     external baseline: any row here is a live edge whose relationship type
--     is missing from the type view.
--     EXPECT 0. Non-zero => the type view does not carry every row.
SELECT COUNT(*) AS dangling_type_refs
FROM       V_CMDB_REL_CI   r
LEFT JOIN  V_CMDB_REL_TYPE t ON r."type" = t."sys_id"
WHERE t."sys_id" IS NULL;

-- A2. The same test on the NODE side, which K21 §6 Q9 did not cover and which
--     is the more serious half: an edge whose parent or child CI is absent
--     from the CI view. A missing type mislabels an edge; a missing CI means
--     the node view is short rows.
--     EXPECT 0 / 0.
SELECT COUNT_IF(pc."sys_id" IS NULL) AS dangling_parent_cis,
       COUNT_IF(cc."sys_id" IS NULL) AS dangling_child_cis,
       COUNT(*)                      AS total_edges
FROM       V_CMDB_REL_CI r
LEFT JOIN  V_CMDB_CI     pc ON r."parent" = pc."sys_id"
LEFT JOIN  V_CMDB_CI     cc ON r."child"  = cc."sys_id";

-- A3. Filtered or stale? Authorship high-water vs carrier-load high-water.
--     A recent load timestamp with an old authorship max reads STALE UPSTREAM;
--     both recent with A1/A2 non-zero reads FILTERED. Note the two column
--     families are different in kind (K21 §3.5): sys_* is authorship,
--     dwintel_dl_* is capture.
SELECT 'V_CMDB_REL_CI'                AS view_name,
       COUNT(*)                       AS row_count,
       MAX("sys_created_on")          AS max_created,
       MAX("sys_updated_on")          AS max_updated,
       MAX("dwintel_dl_ld_ts")        AS max_carrier_load,
       DATEDIFF('day', MAX("sys_updated_on"), MAX("dwintel_dl_ld_ts")) AS authorship_lag_days
FROM V_CMDB_REL_CI
UNION ALL
SELECT 'V_CMDB_REL_TYPE', COUNT(*), MAX("sys_created_on"), MAX("sys_updated_on"),
       MAX("dwintel_dl_ld_ts"),
       DATEDIFF('day', MAX("sys_updated_on"), MAX("dwintel_dl_ld_ts"))
FROM V_CMDB_REL_TYPE
UNION ALL
SELECT 'V_CMDB_CI', COUNT(*), MAX("sys_created_on"), MAX("sys_updated_on"),
       MAX("dwintel_dl_ld_ts"),
       DATEDIFF('day', MAX("sys_updated_on"), MAX("dwintel_dl_ld_ts"))
FROM V_CMDB_CI;

-- A4. Does the type view HIDE soft-deleted rows or carry them? This is half of
--     why the count came in under the older extract (§3.3 reading (c)).
--     delete_flag is a VARCHAR, not a boolean (§3.1) — read the raw values.
SELECT "delete_flag", COUNT(*) AS row_ct
FROM   V_CMDB_REL_TYPE
GROUP  BY "delete_flag"
ORDER  BY row_ct DESC;


-- #############################################################################
-- §B — THE RELATIONSHIP VOCABULARY. Q4, Q6, and the §3.3 crosswalk input.
--      cmdb_rel_type -> relationship_vocabulary is a finite 54-row mapping
--      job (SME count 2026-08-10: 48 standard + 6 custom). These queries
--      produce the rows that job consumes.
-- #############################################################################

-- B1. Q4 — DOES THE REPLICA VIEW CARRY parent_descriptor? It was not visible in
--     the screenshot's cut-off column list, and it decides §3.3: with both
--     descriptor columns the crosswalk is two columns -> two labels; without
--     parent_descriptor the fallback is to ASK FOR THE COLUMN, never to start
--     splitting `name` on '::'.
--     EXPECT: has_parent_descriptor = TRUE.
--     UPPER() on both sides: see the identifier-case note in the header — an
--     uppercase literal compared against a lowercase stored name matches
--     nothing and would report the column ABSENT rather than erroring.
SELECT COUNT_IF(UPPER(column_name) = 'PARENT_DESCRIPTOR') > 0 AS has_parent_descriptor,
       COUNT_IF(UPPER(column_name) = 'CHILD_DESCRIPTOR')  > 0 AS has_child_descriptor,
       COUNT_IF(UPPER(column_name) = 'END_POINT')         > 0 AS has_end_point,
       COUNT_IF(UPPER(column_name) = 'SYS_SCOPE')         > 0 AS has_sys_scope
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  UPPER(table_schema) = UPPER($cmdb_schema)
  AND  UPPER(table_name)   = 'V_CMDB_REL_TYPE';

-- B2. The full column list, so a missing column is legible as a REPLICA
--     PROJECTION GAP rather than as an absent ServiceNow field. Compare
--     against the vendor baseline in servicenow-cmdb-analysis.md (C10).
--     Also read this for the CASE the columns are stored in — it is the
--     authoritative answer to the header's identifier rule.
SELECT column_name, data_type, is_nullable, ordinal_position
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  UPPER(table_schema) = UPPER($cmdb_schema)
  AND  UPPER(table_name)   = 'V_CMDB_REL_TYPE'
ORDER  BY ordinal_position;

-- B3. THE CROSSWALK INPUT — the whole vocabulary, one row per type, with the
--     provenance split machine-read rather than judged. sys_scope separates
--     global (stock) from scoped (company) rows, so §3.1's vendor-baseline vs
--     company-extension boundary needs no case-by-case decision here.
--     Maps directly onto relationship_vocabulary: parent_descriptor ->
--     neo4j_label, child_descriptor -> inverse_label.
SELECT t."sys_id",
       t."name"                                        AS concatenated_name,
       t."parent_descriptor",
       t."child_descriptor",
       t."sys_scope",
       IFF(t."sys_scope" ILIKE '%global%', 'standard', 'custom') AS provenance,
       t."end_point",
       t."delete_flag"
FROM   V_CMDB_REL_TYPE t
ORDER  BY provenance, t."parent_descriptor";

-- B4. The count the SME reported (48 standard + 6 custom = 54), reproduced
--     from the data rather than from memory — and split by delete_flag so a
--     soft-deleted row cannot silently pad or shrink the total.
SELECT IFF("sys_scope" ILIKE '%global%', 'standard', 'custom') AS provenance,
       "delete_flag",
       COUNT(*) AS row_ct
FROM   V_CMDB_REL_TYPE
GROUP  BY provenance, "delete_flag"
ORDER  BY provenance, "delete_flag";

-- [ANSWERED 2026-08-11] ZERO ROWS. `name` = parent || '::' || child holds for
--     all 54, no descriptor contains '::', none is empty. The trap has NOT fired
--     on this instance. K21's rule stands unchanged, but note WHY it stands: not
--     because the concatenation is currently broken, but because nothing
--     GUARANTEES it — and B6 found a different way for a name-based crosswalk to
--     go wrong that this test would never have caught.
-- B5. THE '::' TRAP, tested rather than assumed (§3.3). K21 rules: read the two
--     descriptor columns, do NOT split `name`. These rows are the proof —
--     a literal '::' inside a descriptor, an empty descriptor, or a `name`
--     that is not exactly parent || '::' || child. Each one breaks a split and
--     not the columns.
--     ANY ROW HERE justifies the rule. Zero rows does NOT overturn it — it
--     means the trap has not fired YET on this instance.
SELECT "sys_id",
       "name",
       "parent_descriptor",
       "child_descriptor",
       CASE
         WHEN "parent_descriptor" LIKE '%::%'
           OR "child_descriptor"  LIKE '%::%'              THEN 'descriptor contains ::'
         WHEN COALESCE(TRIM("parent_descriptor"), '') = '' THEN 'parent_descriptor empty'
         WHEN COALESCE(TRIM("child_descriptor"),  '') = '' THEN 'child_descriptor empty'
         ELSE 'name != parent::child'
       END AS trap
FROM   V_CMDB_REL_TYPE
WHERE  "parent_descriptor" LIKE '%::%'
   OR  "child_descriptor"  LIKE '%::%'
   OR  COALESCE(TRIM("parent_descriptor"), '') = ''
   OR  COALESCE(TRIM("child_descriptor"),  '') = ''
   OR  "name" <> "parent_descriptor" || '::' || "child_descriptor";

-- [ANSWERED 2026-08-11] THREE ROWS, AND THEY CORRECT K21 §1.4/§3.3:
--     Contains::Contained by, Instantiates::Instantiated by, Instantiates::Instance of.
--     BOTH Instantiates rows exist, BOTH are global/standard. So this is NOT
--     "the vendor says one label, the instance says another" — the instance
--     carries TWO DISTINCT RELATIONSHIP TYPES that share a parent_descriptor and
--     differ only in the inverse. THE CROSSWALK CONSEQUENCE IS THE POINT:
--     parent_descriptor does NOT identify a type, so a crosswalk keyed on the
--     forward label alone MERGES two types. Key on sys_id, or on the PAIR.
--     B7 then shows only ONE of the two is used (Instance of, 23,753 edges;
--     Instantiated by, 0).
-- B6. The §1.4 label trap, checked directly: public material writes the pair as
--     'Instantiates::Instantiated by', this instance uses 'Instance of' as the
--     inverse. Same relation, different label — the concrete reason to read the
--     instance's descriptors rather than a vendor label set.
SELECT "sys_id", "name", "parent_descriptor", "child_descriptor"
FROM   V_CMDB_REL_TYPE
WHERE  "parent_descriptor" ILIKE '%instantiat%'
   OR  "child_descriptor"  ILIKE '%instantiat%'
   OR  "child_descriptor"  ILIKE '%instance of%'
   OR  "parent_descriptor" ILIKE '%contains%'
   OR  "child_descriptor"  ILIKE '%contained by%';

-- [ANSWERED 2026-08-11] 21 OF 54 CARRY EDGES; 33 CARRY NONE. The live set is
--     dominated by infrastructure: IP Connection::IP Connection 1,969,277,
--     Hosted on::Hosts 1,186,735, Member of::Members 491,786, Located in::Houses
--     301,509, In Rack::Rack contains 226,706, Contains::Contained by 115,113,
--     Depends on::Used by 78,301, Instantiates::Instance of 23,753, then a tail
--     down to single digits.
--     ALL SIX CUSTOM TYPES CARRY ZERO EDGES. The company defined six and uses
--     none, so the crosswalk's real input is 21 standard rows, not 54 — and the
--     custom/standard split, while machine-readable, turns out to be moot.
-- B7. WHICH OF THE 54 ARE LIVE. §3.2's rule applied to the vocabulary: only
--     types that carry edges need a DryDocs decision. The sampled rows all
--     showed ONE type value, so the live subset may be far smaller than 54.
SELECT t."parent_descriptor",
       t."child_descriptor",
       IFF(t."sys_scope" ILIKE '%global%', 'standard', 'custom') AS provenance,
       COUNT(r."sys_id") AS edge_count
FROM       V_CMDB_REL_TYPE t
LEFT JOIN  V_CMDB_REL_CI   r ON r."type" = t."sys_id"
GROUP  BY t."parent_descriptor", t."child_descriptor", provenance
ORDER  BY edge_count DESC, t."parent_descriptor";

-- [ANSWERED 2026-08-11, IN THE NEGATIVE] end_point is FALSE on all 54 rows —
--     one distinct value across the whole vocabulary. A single-valued column
--     carries no information, so there is nothing to model and nothing to ask
--     the SME about. Q6 closes: not "we don't know what it means" but "it does
--     not discriminate anything here."
-- B8. Q6 — WHAT IS end_point? No public vendor definition was found, so it is
--     left unassigned rather than guessed. Its distribution against edge usage
--     is the cheapest evidence available: a flag that is TRUE only for types
--     with no outbound edges means something different from one spread evenly.
SELECT t."end_point",
       COUNT(DISTINCT t."sys_id") AS type_count,
       COUNT(r."sys_id")          AS edge_count
FROM       V_CMDB_REL_TYPE t
LEFT JOIN  V_CMDB_REL_CI   r ON r."type" = t."sys_id"
GROUP  BY t."end_point"
ORDER  BY type_count DESC;


-- #############################################################################
-- §C — EDGE POPULATION AND SOFT DELETES. Q5 and §3.2.
--      "The schema is not the contract; the populated schema is."
-- #############################################################################

-- [ANSWERED 2026-08-11 — AND IT CORRECTS K21 §3.2, which is the point of the
--     block] 4,431,668 edges. u_hash POPULATED ON 2,151,933 (48.6%), NOT null
--     throughout as the 200-row sample suggested. percent_outage populated 0.
--     connection_strength 1 distinct value.
--     §3.2 argued "the schema is not the contract; the populated schema is" and
--     then drew its own example from 200 visible rows — which is the same error
--     one level up. The rule survives; the illustration was wrong. u_hash is a
--     real half-populated column and needs a meaning before anything reads it.
-- C1. §3.2 at full-table scale, not the 200 visible rows. u_hash read as null
--     throughout, percent_outage null throughout, connection_strength the
--     constant 'always'. A schema-driven pull would ingest all three as
--     meaningful. This decides whether DryDocs needs an impact-weight concept
--     on edges at all (§6, closing paragraph) — do not conclude "we don't need
--     one" from a sample.
SELECT COUNT(*)                                 AS total_edges,
       COUNT("u_hash")                          AS u_hash_populated,
       COUNT("percent_outage")                  AS percent_outage_populated,
       COUNT(DISTINCT "percent_outage")         AS percent_outage_distinct,
       COUNT("connection_strength")             AS conn_strength_populated,
       COUNT(DISTINCT "connection_strength")    AS conn_strength_distinct
FROM   V_CMDB_REL_CI;

-- C2. If C1 shows connection_strength has more than one value, this names them.
SELECT "connection_strength", "percent_outage", COUNT(*) AS row_ct
FROM   V_CMDB_REL_CI
GROUP  BY "connection_strength", "percent_outage"
ORDER  BY row_ct DESC;

-- [ANSWERED 2026-08-11] delete_flag TAKES ONLY 'N' OR NULL. There is no 'Y'
--     anywhere: V_CMDB_CI 21,475,298 N / 126,337 NULL; V_CMDB_REL_CI 4,170,886 N
--     / 260,831 NULL; V_CMDB_REL_TYPE 54 N.
--     So NO soft-deleted row is visible in the replica at all — deletes are
--     either hard-removed upstream or the flag is never set. That makes §3.4's
--     worry (ingesting dead edges as live) NOT CURRENTLY REAL, and C5's guessed
--     predicate moot. What replaces it is a smaller, sharper question: NULL is a
--     second state on 0.6% of CIs and 5.9% of edges, and nobody knows what it
--     means. Rule NULL before relying on the flag, and do not assume N = live.
-- C3. Q5 — delete_flag semantics across the three ring-1 views. What values it
--     takes, and whether deleted rows are retained. Decides §3.4: a pull that
--     ignores this ingests dead edges as live ones, and a dead edge makes two
--     live nodes look connected. The D7 tombstone idiom
--     (removed_from_source_at) is the existing shape to reuse — do not invent
--     a second one.
SELECT 'V_CMDB_CI' AS view_name, "delete_flag", COUNT(*) AS row_ct FROM V_CMDB_CI       GROUP BY "delete_flag"
UNION ALL
SELECT 'V_CMDB_REL_CI',          "delete_flag", COUNT(*)          FROM V_CMDB_REL_CI    GROUP BY "delete_flag"
UNION ALL
SELECT 'V_CMDB_REL_TYPE',        "delete_flag", COUNT(*)          FROM V_CMDB_REL_TYPE  GROUP BY "delete_flag"
ORDER  BY view_name, row_ct DESC;

-- C4. Does delete_flag interact with the carrier's snapshot trim? If deleted
--     rows only ever appear in trimmed snapshots, retention is the answer to
--     "are they kept indefinitely" and the pull needs a snapshot predicate,
--     not just a flag predicate.
SELECT "delete_flag",
       "dwintel_dl_snapshot_trim",
       COUNT(*)                        AS row_ct,
       MIN("dwintel_dl_snapshot_dt")   AS first_snapshot,
       MAX("dwintel_dl_snapshot_dt")   AS last_snapshot
FROM   V_CMDB_REL_CI
GROUP  BY "delete_flag", "dwintel_dl_snapshot_trim"
ORDER  BY row_ct DESC;

-- C5. Are soft-deleted edges pointing at live CIs? This is the concrete harm in
--     §3.4 — the row that would make two live nodes look connected. Non-zero
--     means the flag MUST be in the pull predicate, not a later cleanup.
SELECT COUNT(*) AS deleted_edges_between_live_cis
FROM       V_CMDB_REL_CI r
INNER JOIN V_CMDB_CI     pc ON r."parent" = pc."sys_id"
INNER JOIN V_CMDB_CI     cc ON r."child"  = cc."sys_id"
WHERE  r."delete_flag"  IS NOT NULL AND TRIM(r."delete_flag")  NOT IN ('', 'N', 'false', 'FALSE', '0')
  AND (pc."delete_flag" IS NULL     OR  TRIM(pc."delete_flag")     IN ('', 'N', 'false', 'FALSE', '0'))
  AND (cc."delete_flag" IS NULL     OR  TRIM(cc."delete_flag")     IN ('', 'N', 'false', 'FALSE', '0'));
--     NOTE: the value lists above are a GUESS pending C3. Re-write this
--     predicate from C3's actual values before trusting the number.


-- #############################################################################
-- §D — THE GRAIN AND CLASS QUESTIONS. Q8, §1.3(b), §1.4.
--      These decide what a loader reads, and they are the ones that would be
--      expensive to get wrong (the K1/K2 job-vs-folder precedent).
-- #############################################################################

-- D1. Q8 — IS THE TOM ROW'S SUBJECT A BUSINESS APPLICATION CI OR A DEPLOYMENT
--     MODULE CI? K21 calls this "the sharpest of the remainder" and says one
--     query settles it. The SEAL ids come off cmdb_ci_service_discovered
--     (§1.3(c)), which would put the assignment at DEPLOYMENT grain in the
--     SOURCE, while practice maps off the APPLICATION. Both can be true — the
--     source may record finer than the operating model uses it.
--     THIS IS THE ONE TO RUN BEFORE WALKING G35: §G0e's fork turns on it.
SELECT ci."sys_class_name",
       COUNT(*)                             AS tom_rows,
       COUNT(DISTINCT tom_main."parent_id") AS distinct_subject_cis
FROM       IDENTIFIER($v_tom_main) tom_main
LEFT JOIN  V_CMDB_CI               ci ON ci."sys_id" = tom_main."parent_id"
GROUP  BY ci."sys_class_name"
ORDER  BY tom_rows DESC;

-- [ANSWERED 2026-08-11] 21,601,635 CIs in base. 14,683 also in
--     cmdb_ci_business_app. 24,169 also in cmdb_ci_service_discovered. IN BOTH:
--     ZERO. So a CI sits in exactly one class table, the multiplication trap is
--     real but bounded, and no CI is both a business application and an
--     application service — which rules out a reading §1.3(c) left open.
--     THE SCALE IS THE HEADLINE: business applications are 0.07% of the CI
--     table. That is the number behind the SME's 2026-08-11 scope ruling and the
--     reason §3.6's ring model was rewritten — see §7.
-- D2. §1.3(b) — THE CLASS-TABLE MULTIPLICATION TRAP, quantified. cmdb_ci,
--     cmdb_ci_service_discovered and cmdb_ci_business_app share sys_id: one CI
--     with class-specific attribute sets, NOT three entities. A pull that
--     treats each view as a dataset and each row as a node multiplies every CI
--     by its class depth. This is the single most likely way to get the pull
--     wrong, and it is invisible from the view list.
--     Read: in_base should equal the class counts' union, never their sum.
SELECT COUNT(DISTINCT ci."sys_id")    AS cis_in_base,
       COUNT(DISTINCT bap."sys_id")   AS also_in_business_app,
       COUNT(DISTINCT disco."sys_id") AS also_in_service_discovered,
       COUNT(DISTINCT IFF(bap."sys_id" IS NOT NULL AND disco."sys_id" IS NOT NULL,
                          ci."sys_id", NULL)) AS in_both_class_tables
FROM       V_CMDB_CI                     ci
LEFT JOIN  V_CMDB_CI_BUSINESS_APP        bap   ON bap."sys_id"   = ci."sys_id"
LEFT JOIN  V_CMDB_CI_SERVICE_DISCOVERED  disco ON disco."sys_id" = ci."sys_id";

-- D3. Which CI classes actually exist, and how many of each. Ring 1 pulls
--     cmdb_ci and gets EVERY class in one table; whether DryDocs wants all of
--     them or only the classes it has node semantics for is a modeling
--     decision for the gate (§3.6). This is the list that decision needs.
SELECT "sys_class_name", COUNT(*) AS cis
FROM   V_CMDB_CI
GROUP  BY "sys_class_name"
ORDER  BY cis DESC;

-- D4. §1.4 — THE RELATIONSHIP CHAIN, validated as data rather than as a
--     drawing. The SME's chain is area product -[Contains]-> business
--     application -[Instantiates]-> deployment module. This returns the actual
--     class-to-class edge shapes, which is the real crosswalk unit: DryDocs
--     maps (parent class, descriptor, child class) triples, not bare labels.
SELECT pc."sys_class_name" AS parent_class,
       t."parent_descriptor",
       t."child_descriptor",
       cc."sys_class_name" AS child_class,
       COUNT(*)            AS edges
FROM       V_CMDB_REL_CI   r
LEFT JOIN  V_CMDB_REL_TYPE t  ON r."type"   = t."sys_id"
LEFT JOIN  V_CMDB_CI       pc ON r."parent" = pc."sys_id"
LEFT JOIN  V_CMDB_CI       cc ON r."child"  = cc."sys_id"
GROUP  BY parent_class, t."parent_descriptor", t."child_descriptor", child_class
ORDER  BY edges DESC;

-- D5. Is the application -> deployment relation really 1:N, as the SME
--     confirmed 2026-08-09? Anything with max_children = 1 estate-wide would
--     contradict it; a long tail of 1s with a few N is the expected shape.
--     Fill the descriptor predicate from B6's actual value — 'Instantiates' is
--     this instance's reading, not a vendor constant.
SELECT COUNT(DISTINCT inst.parent_ci)  AS parent_apps,
       COUNT(*)                        AS child_links,
       MAX(inst.child_count)           AS max_children_on_one_parent,
       AVG(inst.child_count)           AS avg_children_per_parent
FROM (
  SELECT r."parent" AS parent_ci,
         r."child"  AS child_ci,
         COUNT(*) OVER (PARTITION BY r."parent") AS child_count
  FROM       V_CMDB_REL_CI   r
  INNER JOIN V_CMDB_REL_TYPE t ON r."type" = t."sys_id"
  WHERE  t."parent_descriptor" ILIKE '%instantiat%'
) inst;


-- #############################################################################
-- §E — ADJACENT QUESTIONS THAT ARE CHEAP WHILE THE CONNECTION IS OPEN.
--      Not relationship-mapping proper, but each blocks a G35 clause and each
--      costs one query.
-- #############################################################################

-- E1. Q1 — DOES tom_main CARRY A USER/PERSON COLUMN AS WELL AS group? The
--     sample joins only sys_user_group and selects no person column. This
--     decides whether G35 §B6's "a role holding always names a person" is an
--     invariant the load may rely on, or a SEAL-side-only fact — and whether
--     HAS_AGENT must widen to admit an Organization (prov:agent already does).
--     Blocks §B6.
SELECT column_name, data_type, is_nullable
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  UPPER(table_schema) = UPPER($cmdb_schema)
  AND  UPPER(table_name)   = UPPER($v_tom_main)
ORDER  BY ordinal_position;

-- E2. If E1 shows a user column, this says whether it is POPULATED — §3.2's
--     rule applies to the TOM tables too. Replace <USER_COL> with its name,
--     quoted and lowercase exactly as E1 reports it.
--     Skip this block entirely if E1 returns no user column.
-- SELECT COUNT(*)                AS tom_rows,
--        COUNT("<USER_COL>")     AS user_populated,
--        COUNT("group")          AS group_populated,
--        COUNT_IF("<USER_COL>" IS NULL AND "group" IS NOT NULL) AS group_only_rows
-- FROM   IDENTIFIER($v_tom_main);
--     NOTE: `group` is a reserved word AND stored lowercase, so it needs the
--     quotes for both reasons — but lowercase inside them, not upper.

-- E3. §1.3(e) — the inheritance columns, as distribution. SME 2026-08-10:
--     'Inherited' = the CI came from the area product; 'Overridden' = set by
--     hand. Neither value is a vendor concept. This is what turns G35 §E4 from
--     a blocked option into a modeling choice: if inherited_from_ci resolves to
--     CIs DryDocs already holds as :AreaProduct, the pointer can be a real edge
--     rather than a property.
--     Watch for a THIRD value: G35 §E1 lists an empty mode that the evidence
--     does not corroborate, and §E1b asks the walk to confirm or drop it. This
--     query answers that too.
SELECT tom_main."inheritance",
       COUNT(*)                                    AS row_ct,
       COUNT(tom_main."inherited_from_ci")         AS parent_pointer_populated,
       COUNT(DISTINCT parent_ci."sys_class_name")  AS distinct_parent_classes
FROM       IDENTIFIER($v_tom_main) tom_main
LEFT JOIN  V_CMDB_CI               parent_ci ON parent_ci."sys_id" = tom_main."inherited_from_ci"
GROUP  BY tom_main."inheritance"
ORDER  BY row_ct DESC;

-- E4. And WHICH classes the inherited-from parents are — the direct test of
--     "the parent is the area product". If one class dominates, G35 §E5's
--     modelled-node option has a named target.
SELECT parent_ci."sys_class_name" AS inherited_from_class, COUNT(*) AS row_ct
FROM       IDENTIFIER($v_tom_main) tom_main
INNER JOIN V_CMDB_CI               parent_ci ON parent_ci."sys_id" = tom_main."inherited_from_ci"
GROUP  BY inherited_from_class
ORDER  BY row_ct DESC;

-- E5. §2.2 — does any table appear in more than one DW_*_DATA_VIEW schema, and
--     which would be authoritative? Recorded as open so it is not
--     rediscovered. Runs across the whole database, not the current schema.
SELECT table_name,
       COUNT(DISTINCT table_schema) AS schema_count,
       LISTAGG(table_schema, ', ') WITHIN GROUP (ORDER BY table_schema) AS schemas
FROM   INFORMATION_SCHEMA.TABLES
WHERE  UPPER(table_schema) RLIKE 'DW_.*_DATA_VIEW'   -- RLIKE: avoids Snowflake's backslash string-escape trap in LIKE
GROUP  BY table_name
HAVING COUNT(DISTINCT table_schema) > 1
ORDER  BY schema_count DESC, table_name;

-- E6. Q10 — IS THE KB -> DEPLOYMENT MODULE LINK GENUINE, OR ANOTHER DEFAULTED
--     REFERENCE? The SME flagged KB articles on the module as "more
--     meaningful", which would promote the kb_* family from ring 3. But the
--     same defect that makes change counts per module untrustworthy (§1.3, the
--     2026-08-10 correction) would make KB attachment untrustworthy in exactly
--     the same way.
--     READ FOR SKEW: a healthy link spreads across many modules. One module
--     holding a large share is the signature of a form default, not an
--     assertion. Name the instance's actual KB->CI reference column first, with
--     an E1-style column inspection against V_KB_KNOWLEDGE.
-- SELECT ci."sys_class_name",
--        COUNT(*)                        AS kb_articles,
--        COUNT(DISTINCT kb."<CI_REF>")   AS distinct_cis,
--        MAX(per_ci.n)                   AS max_articles_on_one_ci
-- FROM       V_KB_KNOWLEDGE kb
-- LEFT JOIN  V_CMDB_CI      ci ON ci."sys_id" = kb."<CI_REF>"
-- LEFT JOIN (SELECT "<CI_REF>" AS ci_ref, COUNT(*) AS n
--            FROM V_KB_KNOWLEDGE GROUP BY "<CI_REF>") per_ci
--        ON per_ci.ci_ref = kb."<CI_REF>"
-- GROUP  BY ci."sys_class_name"
-- ORDER  BY kb_articles DESC;


-- =============================================================================
-- WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
--
-- It does not rule the pull scope, activate a source, or write a registry row.
-- K21 §5 is explicit that the ring-1 dataset rows stay a DRAFTED PROPOSAL until
-- a gate rules, because config/source-registry.yaml is an enforcement surface
-- and a proposal sitting where the enforcement matrix reads it forces the gate
-- to strike rows rather than approve a recommendation.
--
-- It also does not reproduce the SME's report query. That query is a hand-built
-- report and carries three defects that are harmless in a report and would be
-- bugs in a contract (K21 §1.5): a wrong-alias active filter, two ANDed LIKEs
-- reaching for one role family, and a WHERE clause referencing a SELECT alias.
-- Transcribing it would inherit all three.
--
-- WHAT IT DOES BORROW FROM THAT QUERY is its IDENTIFIER CONVENTION, which is
-- the one thing in it that is not a defect but a hard requirement of this
-- replica: tables unquoted, columns quoted and lowercase. See the header.
-- =============================================================================
