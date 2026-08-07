# AWS Airflow / MWAA (Apache Airflow) — PLACEHOLDER

Status: **placeholder.** No loader is active. Reserves Airflow as a future orchestration source
and records how it will crosswalk to the **BMC Control-M baseline**.

## Crosswalk to baseline (draft — SME must confirm before activation)

| Airflow native | BMC baseline concept | DryDocs node | Confidence |
|----------------|----------------------|--------------|------------|
| DAG | Folder | `ControlMFolder` (Collection) | high |
| Task | Job | `ControlMJob` | high |
| `task >> task` (dependency) | OUT→IN dependency | `WAS_INFORMED_BY` | high |
| `ExternalTaskSensor` / dataset | IN condition | `REQUIRES_IN_CONDITION` → `Condition` | medium |
| Operator (e.g. `SparkSubmitOperator`) | invoked script/ETL | `INVOKES` → `Script` / `ETLProcess` | medium |
| Connection / pool | execution host / engine | `ExecutionHost` | medium |
| `owner` (default_args) | run-as user | `AppUser` | high |
| Schedule (cron / timetable) | scheduling | job schedule properties | high |

> **Internal implementation docs exist**, and step 1 below is where they get used. This file is
> public vendor material, so the location is referenced **by path, never by value**:
> `internal/airflow-reference/mwaa-internal-docs.md` (id `airflow:internal-implementation-docs`),
> also pointed at from the `airflow` system row's `locator.internal_docs` in
> `config/source-registry.yaml`. That is a different fact from the `apache.org` publisher URL on
> the `apache` vendor row — who publishes Airflow, versus where our own deployment is documented.

## To activate
1. Add `SOURCE-MANIFEST.md` (MWAA environment, Airflow version, how DAG metadata is exported)
   — start from the internal implementation docs referenced above; they are the only source
   that can answer the environment and the deployed version.
2. Complete `crosswalk.md`; run through the HITL gate.
3. Register in `config/source-registry.yaml` with `orchestrator: airflow`.
4. Implement loader emitting baseline node/edge types only.

> A DAG is a Folder and a Task is a Job — map, don't invent. Dataset-aware scheduling maps to
> `Condition`. The graph stays orchestrator-agnostic.
