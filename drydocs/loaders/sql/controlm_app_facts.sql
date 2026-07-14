-- =============================================================================
-- controlm_app_facts.sql — STG_APP_FACT extract for the K2 SEAL attribution
-- loader (drydocs/loaders/seal_attribution.py).
--
-- Source: DRYDOCS_STG.STG_APP_FACT (the C3/C4 variable-normalization stream's
-- semantic facts) joined to STG_RUN for run recency. Run with current_schema
-- set to the staging owner (or qualify the table names for your environment).
--
-- ORDER BY r.started_at, f.app_fact_sk IS the tie-break contract: run_id is a
-- UUID and carries no order, so "most-recent STG_APP_FACT.run_id" (gate
-- seal-attribution-match-policy §C) is operationalized as feed order — the
-- resolver uses app_fact_sk (falling back to feed ordinal) as the row-recency
-- key. Do not remove the ORDER BY.
--
-- Mechanism only: no literal SEAL ids / app names / job names belong in this
-- file. Scope binds are not needed — the attribution loader consumes the whole
-- fact table and reconciles coverage against it (§B).
-- =============================================================================

SELECT
    f.app_fact_sk,
    f.run_id,
    f.data_center,
    TO_CHAR(f.folder_id)  AS folder_id,
    TO_CHAR(f.job_id)     AS job_id,
    f.fact_type,
    f.fact_value,
    f.environment,
    f.source_var
FROM stg_app_fact f
JOIN stg_run r
  ON r.run_id = f.run_id
ORDER BY r.started_at, f.app_fact_sk
