# DataHub Airflow plugin — Source Manifest

**Purpose:** the vendor reference for how an Airflow deployment's DAG/task metadata and run
status are *captured* — held here as the placeholder's worked example of an Airflow export
path, while no DryDocs loader for Airflow is active.
**Classification:** `External` — publishable. Apache-2.0 source code; see
`config/classification.yaml` and `PUBLISH-BOUNDARY.md`.
**Added:** 2026-09-09 (Lane A, desktop; alongside the N18 `registry-wiring-readiness` sitting,
which used DataHub's ingestion model as the comparison shape).

---

## What is here

| Path | What it is |
|---|---|
| `datahub-airflow-plugin/README.md` | The plugin's own README: supported Airflow versions (3.0+; 2.x via plugin <= 1.6.0), the `airflow.cfg` `[datahub]` block, the REST / Kafka / file emitters, the `enable_extractors` / `patch_sql_parser` options. |
| `datahub-airflow-plugin/src/datahub_airflow_plugin/` | The package, whole: `client/airflow_generator.py` (DAG -> DataFlow, Task -> DataJob, run -> DataProcessInstance), `_config.py` (the finite option set), `datahub_listener.py` (run-status capture), `airflow3/` (Airflow 3 listener and OpenLineage adapters), `hooks/`, `operators/`, `example_dags/`. |
| `datahub-airflow-plugin/pyproject.toml`, `setup.py`, `setup.cfg` | Package metadata; `setup.py:120` declares `license="Apache-2.0"`. The version file reads `1!0.0.0.dev0` because the clone is a development tree, not a release. |
| `datahub-airflow-plugin/LICENSE` | The Apache License 2.0 text from the DataHub repository root, copied unmodified. |

**Source URL:** https://github.com/datahub-project/datahub/tree/master/metadata-ingestion-modules/airflow-plugin
(published as https://pypi.org/project/acryl-datahub-airflow-plugin/; docs at
https://docs.datahub.com/docs/lineage/airflow)
**Captured:** 2026-09-09, from a local clone of `datahub-project/datahub` at commit
`dea0f9c184b8d413696b6f1992e49528fb30dd76` (2026-08-30). `src/`, the README and the three
package-metadata files copied unmodified; `__pycache__` directories dropped.

**Left behind, on purpose:** `tests/`, `build.gradle`, `tox.ini`, `run-tests.sh`, `scripts/`,
and the Docker test harness (`Dockerfile.test`, `docker-compose.test.yml`, `README.docker.md`,
`DOCKER_TEST_GUIDE.md`). They are the vendor's build and test infrastructure; the module — the
importable package and its declared metadata — is what the placeholder needs.

## Licensing — why this is committed rather than gitignored

DataHub is **Apache-2.0**, which permits copying and redistribution provided the license text
and notices travel with the code. `LICENSE` beside the package is that text, and no file in the
copy was altered, so no modification notice is owed. This is the world-atlas precedent
(`external/geo/world-atlas/SOURCE-MANIFEST.md`): permissively licensed material may live in a
private-but-sometimes-published repo. The vendor PDFs elsewhere under
`external/orchestration/**` are the contrast — copyrighted binaries, gitignored.

## How it is consumed — read, never run

Nothing imports this package. It sits outside every `[tool.poetry] packages` root and
`MODULE_MAP.md` row, it is excluded from ruff (`pyproject.toml` `extend-exclude`, with the
other vendored code), and no test reads it. It is reference: the concept mapping in
`client/airflow_generator.py` and the option set in `_config.py` are what the placeholder
README's crosswalk cites. If a DryDocs Airflow loader is ever built it will be a DryDocs
component that reads an export, not a dependency on this plugin.

## Trust

**VERBATIM** as captured — byte-identical to the clone at the commit above. The placeholder
README's crosswalk rows that cite it are **GROUNDED** to these files; the rows that map
Airflow objects onto the BMC baseline are DryDocs' own draft and stay unconfirmed until the
HITL gate rules them (`docs/restructure/03-hitl-sme-flow.md`).

## Caveats

- **This is DataHub's model of Airflow, not Airflow's export format.** The plugin runs inside
  the Airflow scheduler and emits to a DataHub instance; it is not a file the MWAA environment
  writes. The internal implementation docs (`internal/airflow-reference/mwaa-internal-docs.md`,
  by path only) still own the question of how *our* DAG metadata is exported — step 1 of the
  placeholder README is only partly answered here.
- **Development snapshot.** The captured tree is between releases (`1!0.0.0.dev0`); a released
  version may differ in the option set. Re-capture at a tagged release before building on a
  specific option.
