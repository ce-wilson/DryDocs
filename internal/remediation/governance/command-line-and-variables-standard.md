# Control-M Command-line & Canonical Variables Standard (v2)

**Corpus:** INTERNAL (governance, tier ④ HLT — formalized). **Status:** 🟠 DIGESTED — 2026-06-17.
**Source:** Confluence **`CBTHLTAUTO` / "Control-M Command line and variables v2"** (`confluence.prod.aws.jpmchase.net/.../pages/6088871957`). The most engine-relevant standards artifact found — it specifies the **canonical variable registry**, **per-framework command-line templates**, and the **ctm-remediate tooling behaviour** directly (requirement IDs `NF-VAL-*`, `NF-AUD-*`, `NF-SEC-*`).

> This is the **ratification source** for registry rules **R2** (variable-name canonicalization) and **R16** (single canonical metadata source), and the command-line half of **NFR-CTM-301**. Unlike the other governance docs (observed standards), this one is written *as* a spec for the tooling — treat it as the authoritative target for Gate-3 generation + Gate-2 validation of command lines and variables.

---

## 1. Canonical variables (the registry)

Variables are **canonical names + aliases**, **uppercase ASCII, lookup case-sensitive** (Control-M variables are case-sensitive at execution; normalizing case would silently merge intentionally-distinct bindings — so the tool **WARNs, never silently merges**).

Core canonical names (from the per-framework templates): `LAUNCHER_SCRIPT_PATH`, `ETL_PLATFORM`, `ETL_ARTIFACT_URI`, `ETL_ARTIFACT_KIND`, `ETL_PLATFORM_FLAGS`, `FID`, `ENV`, `PIPELINE_ID`, `BUS_DATE`, `ODATE`, `DATAFLOW`, `SEAL`, `CONF_PATH`, `COMPUTE`, `APPNAME`, `JOBNAME`, `ORDERID`, `RUNCOUNT`, `ABINITIO_GRAPH_FLAGS`, `START_DELAY`, `TIMEOUT`, `RESOURCE`; Informatica: `SRC_SYS_CD`, `INFA_INTERFACE_LOCAL`, `INFA_INTERFACE_GLOBAL`, `FREQUENCY`, `INFA_JOB`, `INFA_DATABASE`.

**Alias rollups (the canonicalization the resolver/registry enforces):**
- `img_path` (lowercase) / `IMG_PATH` / `IMAGE` → **`ETL_ARTIFACT_URI`**. The standalone `IMAGE → IMAGE` mapping is **removed**; `IMAGE` now rolls up to `ARTIFACT_URI` (clean break, no dual-write — see Decision Log).

This is exactly the **name-drift problem** R2 targets and the **single-canonical-source** principle R16 states — now with an authoritative target registry.

---

## 2. Per-framework command-line templates (the greenfield target)

Each framework has a fixed command line + a **required declaration set**. These are the Gate-3 generation templates (and the Gate-2 conformance shape):

**6.1 Python (dt-launcher, `-py`)** — `ETL_ARTIFACT_KIND=wheel`, `ETL_PLATFORM_FLAGS=-py`.

**6.2 Java (dt-launcher without `-py`):**
```
%%LAUNCHER_SCRIPT_PATH -fid %%FID -env %%ENV -pipeline %%PIPELINE_ID \
  -bd %%BUS_DATE -od %%ODATE -dataflow %%DATAFLOW -alias %%DATAFLOW \
  -img %%ETL_ARTIFACT_URI -seal %%SEAL -i \
  -conf %%CONF_PATH -compute %%COMPUTE
```
Decls: `LAUNCHER_SCRIPT_PATH=/apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh`, `ETL_PLATFORM=java`, `ETL_ARTIFACT_URI=…/artifactory/maven/.../bar-1.4.0.jar`, `ETL_ARTIFACT_KIND=jar`, `ETL_PLATFORM_FLAGS=(empty)`.

**6.3 Ab Initio (wrapper runner, embedded `.pset`):**
```
sh %%LAUNCHER_SCRIPT_PATH -c %%CONFIG_JSON_PATH -f %%FID -e %%ENV -a %%APPNAME \
  -p %%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT \
  -g "%%ETL_ARTIFACT_URI %%ABINITIO_GRAPH_FLAGS" \
  -s %%START_DELAY -t %%TIMEOUT -r %%RESOURCE
```
Decls: `LAUNCHER_SCRIPT_PATH=/apps/cds/abioncloud/script/runScript.sh`, `ETL_PLATFORM=abinitio`, `ETL_ARTIFACT_URI=…/hlsf_service_territory_ingestion_cdc.pset`, `ETL_ARTIFACT_KIND=pset`. (Note the **`-p` order-prefix** `%%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT` hardcoded in the command line — the same NFR-CTM-301 rule.)

**6.4 Informatica — variant 1 (interface identifiers only):**
```
%%LAUNCHER_SCRIPT_PATH -S %%SRC_SYS_CD -I %%INFA_INTERFACE_LOCAL \
  -G %%INFA_INTERFACE_GLOBAL -F %%FREQUENCY -J %%INFA_JOB
```
Decls: `LAUNCHER_SCRIPT_PATH=/etlapps/icdw/prod/ops/Scripts/ICDW_etl_run_interface.ksh`, `ETL_PLATFORM=informatica`, `ETL_ARTIFACT_KIND=other`, `INFA_INTERFACE_LOCAL=ICDW_OBE_FRW_EXT_BB`, `INFA_INTERFACE_GLOBAL=ICDW_OBE_FRW_GBL`, `INFA_JOB=PICDDXL31_FRW_BB_OB_EXTRACT_DLY`.

**6.5 Informatica — variant 2 (+ `-D` database):** adds `-D %%INFA_DATABASE` (`INFA_DATABASE=ICTL_ERRAUD_T`).

---

## 3. Migration examples (how the tool treats legacy → canonical)

| Status | Job declares | Tooling result |
|---|---|---|
| Today | `%%img_path = …/foo.whl` (lowercase) | **No `STG_APP_FACT` row** (case miss); no `:Script` payload node |
| Migrate | rename → `%%IMG_PATH` | alias `IMG_PATH → ARTIFACT_URI`; **WARN logged**; node materializes |
| Final | rename → `%%ETL_ARTIFACT_URI` | canonical; **no WARN** |
| Pre-NFR | `%%IMAGE = …/foo.whl` | `fact_type=IMAGE` (prior schema) |
| Post-NFR | same job, no change | `fact_type=ARTIFACT_URI`; same row, new label; WARN suggests rename |

→ The tool is **non-destructive on legacy** (still materializes via alias + WARN), and **canonical = WARN-free**. That WARN stream is the conformance signal for R2.

---

## 4. Tooling behaviour (the spec maps onto the engine)

| Component | Behaviour |
|---|---|
| `variables.py` `FACT_REGISTRY` | canonical names + aliases; `IMAGE → IMAGE` removed, replaced with `IMAGE → ARTIFACT_URI` |
| `staging.py` | `build_app_fact_rows()` emits `STG_APP_FACT` for any classified variable with `fact_type ≠ None` **and** `is_fully_resolved` |
| `controlm_staging_ddl.sql` | `fact_type` enumeration comment updated; `IMAGE` removed; new types added |
| `m7_etl_artifact_supplement.cypher` | declares `:LocalRelationship` for `INVOKES`, `USES_ARTIFACT`; `:MAPS_TO → prov:used` |
| `controlm_etl_artifacts.py` (loader) | reads `STG_APP_FACT`, MERGEs `:Script` + edges |
| `m7-verify` | enforces **NF-VAL-1 … NF-VAL-7** |
| `audit-variable-aliases` CLI | implements **NF-AUD-2, NF-AUD-3** |

> The `is_fully_resolved` gate is the same resolver guarantee the [concat-dot fix](../../drydocs/controlm/resolver.py) provides — a variable must resolve cleanly before it becomes a fact. Ties the resolver work directly to this standard.

---

## 5. Decision log (accepted)

- **`%%IMAGE` rolls up to `ARTIFACT_URI`** (clean break, no dual-write): drop-and-recreate Neo4j workflow makes migration cost zero; the `STG_APP_FACT` writer is new, so no production consumer of the old `IMAGE` fact_type exists.
- **Canonical names are uppercase ASCII, lookup case-sensitive:** Control-M vars are case-sensitive at execution; case-normalizing would silently merge distinct bindings → **WARN preferred over silent merge.**
- **Distinct labels `INVOKES` vs `USES_ARTIFACT`** (not one label with a role property): *avoids the documented `RUNS_ON` overload risk in `relationship_vocabulary.yaml`* — **directly the same overload that the [loader-flow doc](../../../docs/history/controlm-loader-flow.md) flagged (`RUNS_ON` vs `SCHEDULED_ON`).** The standard chose label-splitting to avoid it.
- **Option A modeling** (one `:Script` label + role property): minimal ontology change; sub-label split (Option B) deferred until query-side pressure justifies it.
- **Security boundary on `ETL_ARTIFACT_URI` (NF-SEC-2):** restrict artifact sources to **JPMC-approved repositories** → prevents supply-chain risk, enforceable by the verifier.

---

## 6. Explicit out-of-scope (v2)

Tracked separately, **not** delivered by this NFR:
- Inferring canonical variable *values* by parsing `CMDLINE`, `MEMNAME`+`MEMLIB`, Task `JSON Path`, or `PARM1`–`PARMn` when the canonical variables are **absent**.
- Quoted-argument extraction (e.g. Ab Initio `-g "<pset> -CAIP_PROC_SIZE_LARGE 50"` token).
- `PRECMD`/`POSTCMD` shell-hook handling for launcher/payload derivation.
- Folder-name signal mining as a platform fallback.
- Container-image registry URI shape validation (e.g. enforcing `registry.jpmchase.net/<path>:<tag>`).

> These are the **known resolver/classifier gaps** — useful as the bounded backlog for the spin-off's variable/command engine, and they overlap the resolver's `var.text` open question (B1).

---

## 7. For the spin-off

- The **canonical registry + alias map** (§1) **ratifies R2/B4** — the spin-off no longer has to derive the canonical map from scratch; it's authored here.
- The **per-framework command-line templates** (§2) are the **Gate-3 generation target** for command lines (the greenfield command line is deterministic per framework + declarations).
- The **`NF-VAL-1..7` / `NF-AUD-2/3` / `NF-SEC-2`** IDs should be cross-walked into the [standards rules registry](../standards-rules-registry.md) as their own checks (verifier `m7-verify` already enforces them).
- The **out-of-scope list** (§6) bounds the engine honestly and overlaps **B1** (`var.text`) — keep them aligned.

Related: [[project-controlm-remediation-spinoff]], [[project-description-metadata-plan]], [[project-controlm-xml-not-json]]
