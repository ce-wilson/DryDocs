# §XWALK — vendor model → company psgmgr replica

Maps the BMC 6.4.01 poster entities to the `dtsremgr` runtime objects and the
`psgmgr` `CM_` replica the company actually queries. Provenance tier
**SYNTHESIZED** (this mapping is DryDocs inference reconciling the poster against
the committed loaders; verify object names against
`drydocs/loaders/sql/controlm_*.sql` before relying on any row).

## §OBJ — object crosswalk

| Concept | Vendor (poster, 6.4.01) | Control-M runtime (`dtsremgr`, 9.0.21.300) | Company replica (`psgmgr`) | Replicated? |
|---------|-------------------------|--------------------------------------------|----------------------------|-------------|
| Job definition | `CMS_JOBDEF` | `DEF_VJOB` | `CM_DEF_VJOB` | ✅ |
| Folder / schedule table | `CMS_SCHEDT` | `DEF_VTAB` | `CM_DEF_VTAB` | ✅ |
| Job variables (SETVAR) | `CMS_SETVAR` | `DEF_SETVAR` | `CM_DEF_SETVAR_VW` | ✅ (name confirmed 2026-07-10) |
| In-conditions (consumed) | `CMS_CON_J` (in rows) | `DEF_LNKI_P` | `CM_DEF_LNKI_P_VW` | ✅ |
| Out-conditions (emitted) | `CMS_CON_J` (out rows) | `DEF_LNKO_P` | `CM_DEF_LNKO_P_VW` | ✅ |
| Run history / active | `CMR_AJF`, `CMR_RUNINF`, `CMR_IOALOG` | (runtime) | `CM_HIST_VW` | ✅ (expensive) |
| Action audit (who ran) | — | (audit) | `CM_AUD_ACTS` | ✅ (future extract) |
| Escalation / SCIM routing | — | (custom) | `CM_ESCALATION_DB` | ✅ (governance) |
| On-Do (ON/DO) | `CMS_ONSTMT` + `CMS_DO` | `DEF_ONSTMT`/`DEF_DO` | — | ❌ not yet |
| Quant/control resources | `CMS_QR_J` / `CMS_CTL_J` | `DEF_QR_J`/`DEF_CTL_J` | — | ❌ not yet |
| Shout/mail/remedy actions | `CMS_SHOUT`/`CMS_MAIL`/`CMS_REMEDY` | `DEF_*` | — | ❌ not yet |
| Security | `CMS_USERS`/`CMS_ACTAUT`/… | `DEF_*` | — | ❌ not replicated |
| Agents/hosts | `CMS_MACHINE_MAP`/`CMR_NODES` | — | — | ❌ not replicated |

**Naming rule:** company object = `CM_` + the `dtsremgr` object, with `_VW`
appended when the replica is exposed as a **view** over the copied table (the
condition links `CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW`; the `_P` = prerequisite).
`CM_RO_USER` is the read-only grantee. Confirm any object with the data-dictionary
probe in `ingest.md` — the replica is a **subset**. The variable object
`CM_DEF_SETVAR_VW` (the last name that carried a `VERIFY`) was confirmed against
live `psgmgr` 2026-07-10: it is a view (hence the `_VW`) with its own
`IS_CURRENT_VERSION` / `VERSION_SERIAL`.

## §COL — column crosswalk (the renames that bite)

6.4.01 uses terse flat names; the 9.0.x `DEF_V*` views use `_ID`/`_NAME` and add
versioning. Same concept, different column:

| Concept | 6.4.01 poster | psgmgr `CM_DEF_V*` |
|---------|---------------|--------------------|
| Job surrogate key | `JOBNO` | `JOB_ID` |
| Folder surrogate key | (schedtab id) | `TABLE_ID` |
| Folder name | `SCHEDTAB` | `SCHED_TABLE` |
| Job name | `JOBNAME` | `JOB_NAME` |
| Business app | `APPLIC` | `APPLICATION` |
| App group | `APPLGROUP` | `GROUP_NAME` |
| Task type | `TASKTYPE` | `TASK_TYPE` |
| Command line | `CMDLINE` | `CMD_LINE` |
| Target node | `NODEID` | `NODE_ID` |
| Author | `AUTHOR` | `AUTHOR` (+ `CREATION_USER`, `CHANGE_USERID`) |
| Owner (run-as) | `OWNER` | `OWNER` |
| Variable name / value | `VAR` / `VAREXPR` | `NAME` / `VALUE` |
| Condition name | `CONDNAME` | `CONDITION` |
| Date reference | `DATEREF` | `ODATE` |
| In/out boolean glue | `OP` + `PARENTHESES` (+`ROWTYPE`) | in: `AND_OR`,`PARENTHESES`,`ORDER_`,`ISN_`; out: `SIGN`,`ISN_` |
| Data center / server | (server instance) | `DATA_CENTER` (P12/P14/P32/P33) |
| — (new in 9.0.x) | — | `IS_CURRENT_VERSION`, `VERSION_SERIAL`, `VERSION_OPCODE`, `VERSION_TIMESTAMP`, `VERSION_USER`, `CAPTURE_DATE` |
| Active-schedule gate | (n/a) | `USER_DAILY` (on `CM_DEF_VTAB`; NULL = not scheduled) |

### Structural deltas 6.4.01 → 9.0.21.300 (do not skip)
1. **Conditions split.** One `CMS_CON_J` (discriminated by `ROWTYPE` in/out)
   becomes two views: `CM_DEF_LNKI_P_VW` (in, 12 cols) and `CM_DEF_LNKO_P_VW`
   (out, 10 cols). Out rows carry `SIGN` (`+` add / `-` remove); in rows carry the
   boolean-expression glue (`AND_OR`, `PARENTHESES`, `ORDER_`).
2. **Versioned views.** Every definition object is a current-version view. **Always**
   `WHERE IS_CURRENT_VERSION = '1'` (string literal — the column is VARCHAR2(1)).
   Omitting it returns every historical edit of every job.
3. **Denormalized folder on the job row.** `CM_DEF_VJOB.PARENT_TABLE` carries the
   folder name redundantly; the authoritative folder name is
   `CM_DEF_VTAB.SCHED_TABLE`. Join on `TABLE_ID`, don't trust `PARENT_TABLE` alone.
4. **No versioning on folders.** `CM_DEF_VTAB` has **no** `IS_CURRENT_VERSION` /
   `VERSION_SERIAL` — versioning applies to jobs and conditions only. Filter
   folders by `USER_DAILY IS NOT NULL` instead.

## §KEYS — join keys in the replica

- Job ↔ folder: `CM_DEF_VJOB.TABLE_ID = CM_DEF_VTAB.TABLE_ID`.
- Variable ↔ job: `CM_DEF_SETVAR_VW.(TABLE_ID, JOB_ID) = CM_DEF_VJOB.(TABLE_ID, JOB_ID)`.
- Condition ↔ job/folder: `CM_DEF_LNK{I,O}_P_VW.(TABLE_ID, JOB_ID)` → job; join
  folder via `TABLE_ID`.
- **Dependency edge** (derived, not stored): job B **depends on** job A when
  `LNKI(B).CONDITION = LNKO(A).CONDITION` with matching `ODATE` semantics. This is
  the core edge `controlm_dependencies_recursive.sql` builds.
- Composite-key caveat (open question `Q0.1`): `TABLE_ID` may collide across
  `DATA_CENTER`s — treat `(DATA_CENTER, TABLE_ID, JOB_ID)` as the true grain in
  staging until confirmed.
- **Folder-scope variables:** a SETVAR row whose `JOB_NAME = SCHED_TABLE` (the
  smart-folder header row) is a **folder-scoped** variable inherited by all jobs
  in the folder — the `var_scope = 'FOLDER'` case in `controlm_variables.sql`.
