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

## Vendor reference held here: the DataHub Airflow plugin

`datahub-airflow-plugin/` is DataHub's Airflow lineage plugin, copied unmodified from the
`datahub-project/datahub` repository (Apache-2.0; provenance, commit and what was left behind
in [`SOURCE-MANIFEST.md`](SOURCE-MANIFEST.md)). It is here as the worked example of how a
running Airflow's metadata gets captured — read, never imported or run. Two things in it are
the reason it is worth holding:

**Its concept mapping, which is the same kind of table as the crosswalk above** — Airflow
native object to the capturing platform's concept, with the run axis the crosswalk does not
yet have (`src/datahub_airflow_plugin/client/airflow_generator.py`):

| Airflow native | DataHub concept | Where | The baseline concept it lands on here |
|----------------|-----------------|-------|----------------------------------------|
| DAG | `DataFlow` | `generate_dataflow` | Folder (`ControlMFolder`) |
| Task | `DataJob` | `generate_datajob` | Job (`ControlMJob`) |
| Task upstream ids | `DataJob.upstream_urns` | `_get_dependencies` | OUT->IN dependency (`WAS_INFORMED_BY`) |
| DAG run / task instance | `DataProcessInstance`, with `run_*` / `complete_*` status events | `run_dataflow`, `run_datajob`, `complete_*` | run history — the `cm_hist_vw` shape, not yet modelled for Airflow |
| `owner` (default_args) | ownership aspect | `_extract_owners` | run-as user (`AppUser`) |
| Operator inlets / outlets | `DataJob.inlets` / `outlets` (dataset URNs) | `airflow3/datahub_listener.py` `_extract_lineage` | dataset READS / WRITES (the DPL `dataset_flow` seam) |

**Its option set, which is finite and declared** (`src/datahub_airflow_plugin/_config.py`,
`DatahubLineageConfig`): `enabled`, `datahub_conn_id`, `cluster`, `platform_instance`,
`capture_ownership_info`, `capture_tags_info`, `capture_executions`, `materialize_iolets`,
`enable_extractors`, `patch_sql_parser`, `dag_filter_pattern`, `emit_mode`, and a handful
more — every knob a capture needs, as typed fields with defaults, not prose. That is the shape
the source registry's per-dataset descriptor is being held to (N18, `registry-wiring-readiness`).

What it does **not** answer: how *our* MWAA environment exports DAG metadata. The plugin emits
from inside the scheduler to a DataHub instance; it is not a file drop. Step 1 below still
needs the internal implementation docs for that.

## To activate
1. Complete `SOURCE-MANIFEST.md` for the **deployment** (MWAA environment, Airflow version,
   how DAG metadata is exported) — the manifest here covers only the vendor plugin. Start
   from the internal implementation docs referenced above; they are the only source that
   can answer the environment and the deployed version.
2. Complete `crosswalk.md`; run through the HITL gate.
3. Register in `config/source-registry.yaml` with `orchestrator: airflow`.
4. Implement loader emitting baseline node/edge types only.

> A DAG is a Folder and a Task is a Job — map, don't invent. Dataset-aware scheduling maps to
> `Condition`. The graph stays orchestrator-agnostic.
