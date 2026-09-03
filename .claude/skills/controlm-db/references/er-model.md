# §ER — BMC Control-M/Server 6.4.01 physical data model

Ground truth transcribed from `BMC_ControlM_SVR_v6.4.01_DB_Poster.pdf`. Provenance
tier **GROUNDED** (table names, PKs, and column lists are read directly off the
BMC poster; groupings are BMC's). Column *semantics* beyond the name are
SYNTHESIZED where noted.

Naming: **`CMS_`** = Control-M **Server / static definitions** (what is scheduled).
**`CMR_`** = Control-M **Runtime / active** (what actually ran). Key legend on the
poster: `PK` primary key, `I#` indexed field, `U` unique constraint.

The company replicates only a slice of this model (mostly the `CMS_` definition
side + history) — see `schema-crosswalk.md` for which. This file is the full
vendor map so you can locate any concept.

---

## §HUBS — the two backbone tables

Everything hangs off two entities:

- **`CMS_JOBDEF`** (PK `JOBNO`) — the job **definition**. The static "what should
  run" record. ~90 columns. All `CMS_*` child tables foreign-key on `JOBNO`.
- **`CMR_AJF`** (PK `ORDERNO`) — the **Active Jobs File**: a runtime **instance**
  of a job (one per order/run). Carries `JOBNO` back to `CMS_JOBDEF`. All `CMR_*`
  child tables foreign-key on `ORDERNO`.

The relationship `CMR_AJF.JOBNO → CMS_JOBDEF.JOBNO` is the definition↔runtime join.

### On-Do nesting (the child-row key pattern)
Job child rows model Control-M's **On-Do** logic (ON <condition/status> DO <action>)
via a composite key: `(JOBNO, IF_NO, DO_NO, ROWORDER)`.
- `IF_NO` = which ON block, `DO_NO` = which DO action within it, `ROWORDER` =
  ordering within a multi-row element. The same pattern repeats on the runtime
  side keyed by `ORDERNO`.

---

## §GRP-JOBDEF — Job Definitions (CMS_)

| Table | PK | Purpose | Notable columns |
|-------|----|---------|-----------------|
| `CMS_JOBDEF` | `JOBNO` | master job definition | `JOBNAME`, `APPLIC`, `APPLGROUP`, `SCHEDTAB` (folder), `AUTHOR`, `OWNER`, `TASKTYPE`, `CYCLIC`, `CYCLIC_TYPE`, `NODEID`/`NODEGRP` (target), `CMDLINE`, `MEMLIB`/`MEMNAME`, `OVERLIB`, `MAXRERUN`, `MAXWAIT`, `FROMTIME`/`UNTIL`, `DAYSTR`/`WDAYSTR`/`MONTHSTR`, `DAYSCAL`/`WEEKCAL`/`CONFCAL` (calendars), `CREATIONUSERID`/`CHANGEUSERID` + datetimes, `GROUPID`, `INSTREAM_SCRIPT`, `RUN_TIMES`, `INTERVAL_SEQUENCE` |
| `CMS_SCHEDT` | schedule-table (folder) def | folder / SMART table header | `SCHEDTAB` name; folder-level scheduling |
| `CMS_APPGRP` | app group | application-group def | groups jobs under `APPLGROUP` |
| `CMS_SETVAR` | `(JOBNO, ROWORDER, DO_NO, IF_NO)` | job **variable** assignments | `SETVARTYPE`, `GLOBALIND` (global vs local), `VAR`, `VAREXPR`, `VARSCOPE` |
| `CMS_CON_J` | `(JOBNO, ROWTYPE, ROWORDER, DO_NO, IF_NO)` | **conditions** in+out (combined) | `CONDNAME`, `DATEREF`, `OP`, `PARENTHESES`; `ROWTYPE` discriminates in vs out (**split in 9.0.x** → LNKI/LNKO) |
| `CMS_ONSTMT` | `(JOBNO, IF_NO, ROWORDER)` | **ON** statements of On-Do | `STMT`, `CODE` |
| `CMS_DO` | `(JOBNO, IF_NO, DO_NO)` | **DO** actions of On-Do | `ACTION`, `ROWORDER` |
| `CMS_SHOUT` | `(JOBNO, ROWORDER, DO_NO, IF_NO)` | shout / alert actions | `SHOUTYPE`, `URGENCY`, `MESSAGE`, `WHENCOND`, `SHOUTIME`, `EXECTYPE`, `LOGIC_DEST` |
| `CMS_CTL_J` | `(CONTROL, ROWORDER, JOBNO)` | **control resource** requests | `CMODE` (shared/exclusive) |
| `CMS_QR_J` | `(QRESNAME, ROWORDER, JOBNO)` | **quantitative resource** requests | `QNUMBER` (qty needed) |
| `CMS_SYSOUT` | `(JOBNO, ROWORDER, DO_NO, IF_NO)` | sysout handling | `SYSTYPE`, `SYSOPT`, `SYSPRM` |
| `CMS_DATES` | `(JOBNO, JOBDATE, TAGNAME)` | explicit run dates | — |
| `CMS_TAG` | `(TAGNAME, GROUPID)` | scheduling **tag** (rule-based calendar) | `MAXWAIT`, `CAL_ANDOR`, `MONTHSTR`, `DAYSCAL`/`WEEKCAL`/`CONFCAL`, `DAYSTR`/`WDAYSTR`, `TAGFROM`/`TAGTILL` |
| `CMS_TAGLINK` | `(TAGNAME, JOBNO)` | tag ↔ job link | `GROUPID` |
| `CMS_FORCEJ` | `(JOBNO, DO_NO, IF_NO)` | DO FORCEJOB action | `JOBNAME`, `SDATE`, `SCHEDTAB` |
| `CMS_CON_J` (DO side) | — | DO COND (add/remove condition) | see conditions |
| `CMS_MAIL` | `(JOBNO, DO_NO, IF_NO)` | DO MAIL action | `SUBJECT`, `URGENCY`, `MESSAGE`, `LOGIC_DEST`, `CC_DEST`, `ATTACH_SYSOUT` |
| `CMS_REMEDY` | `(JOBNO, DO_NO, IF_NO)` | DO REMEDY ticket action | `URGENCY`, `SUMMARY`, `DESCRIPTION` |
| `CMS_SHDEST` | `(GRPNAME, APPLTYPE, ACT_SH_TAB, LOGIC_DEST)` | shout destination table | `ADDRTYP`, `NODEID`, `DESTYPE`, `DESTARGET` |
| `CMS_DATEMM` | date-member | named date-list member | — |
| `CMS_NODGRP` | node-group | host/agent grouping | — |
| `CMS_NODID` | node-id | node/agent identity | — |
| `CMS_SYSPRM` | `(JOBNO, ROWORDER, DO_NO, IF_NO)` | system / step parameters | `SYSTYPE`, `SYSOPT`, `SYSPRM` |
| `CMS_CMNPRM` | `(COMPUTER, OPSYS, VERSION, CMVERSION)` | **common/config parameters** (see Config group) | server-wide config |

**`CYCLIC` vs `CYCLIC_TYPE` — two columns, one trap (2026-09-02).** `CYCLIC` (`Y`/`N`) says WHETHER a
job is cyclic. `CYCLIC_TYPE` says HOW a cyclic run repeats — `INTERVAL` / `INTERVAL_SEQUENCE` /
`SPECIFIC_TIMES` per `external/orchestration/bmc-controlm/controlm-ctmdeffolder-utility.md` (Parameter
Reference, GROUNDED); its companions are `RUN_TIMES` and `INTERVAL_SEQUENCE`. In the replica the
column carries single letters (`C`, `S`), and a company-side census found `C` concentrated on the
`*_DLY` folders and `S` on the `*_CYC` folders — the opposite of what "C for cyclic" predicts. Read
the letter as a cycle type, never as a job type; the letter-to-enum map is unverified. The case:
`.claude/skills/research-probe-discipline/evals/files/cyclic-type-trap.md`.

---

## §GRP-SECURITY — Security Definitions (CMS_)

| Table | PK | Purpose |
|-------|----|---------|
| `CMS_USERS` | `(USERNAME, NODEID)` | user; `USERDESCR`, `USERGROUP` |
| `CMS_ACTAUT` | `(USERNAME, NODEID, OWNER)` | per-action authorizations: `HOLD`, `FORCE`, `DELETEACT`, `RERUN`, `LOG`, `MAYORDER`, `KILLJOB`, … (all CHAR(2) Y/N) |
| `CMS_SCHAUT` | `(USERNAME, NODEID, SCHEDTAB)` | schedule-table authorizations: `ADDACT`, `DELETEACT`, `READACT`, `UPDATEACT`, `MAYORDER` |
| `CMS_IOAAUT` | `(USERNAME, NODEID, RESTYPE)` | resource authorizations: `ADDACT`, `DELETEACT`, `CHANGEACT` |
| `CMS_IOACHK` | `(RESTYPE, RESNAME)` | resource checksum |
| `CMS_SECURITY_MAP` | `(OWNER, TARGET_MACHINE)` | owner→machine credential map: `PASSWORD_KEY_FLAG`, `PASS_AUTH_KEY_NAME` |
| `CMS_SECURITY_KEYS` | `AUTHENTICATION_KEY_NAME` | key material: `PASSWORD_KEYPHRASE`, `TYPE`, `FORMAT`, `BITS`, `OWNER_KEY` — **never replicate/expose** |

---

## §GRP-ACTIVE — Active Jobs (CMR_)

Runtime instances, keyed on `ORDERNO`. Mirrors of the definition children.

| Table | PK | Purpose |
|-------|----|---------|
| `CMR_AJF` | `ORDERNO` | active-jobs-file: `JOBNO`, `STATUS`, `STATE`, `ODATE`, `PROCID`, `RERUN_NO`, `OSCOMPSTAT`/`OSCOMPMSG`, `STARTRUN`/`ENDRUN`, `NEXTDATE`, `JOBNAME`, `SCHEDTAB`, `OWNER`, `APPLIC`, `RUNCOUNT`, `DAILYNAME`, `HOLDFLAG`, `CONFIRMED` |
| `CMR_CON_J` | `(ORDERNO, ROWTYPE, ROWORDER, DO_NO, IF_NO)` | active conditions in/out |
| `CMR_SETVAR` | `(ORDERNO, ROWORDER, DO_NO, IF_NO)` | active SETVAR |
| `CMR_DO` / `CMR_ONSTMT` | On-Do at runtime | `ACTION` / `STMT`,`CODE` |
| `CMR_SHOUT` / `CMR_MAIL` / `CMR_REMEDY` | runtime action instances |
| `CMR_CTL_J` / `CMR_QR_J` | resource use at runtime |
| `CMR_SYSOUT` | runtime sysout |
| `CMR_FORCEJ` | runtime forcejob (`JOBNAME`, `SDATE`, `SCHEDTAB`) |
| `CMR_RUNINF` | `(TIMESTMP, ORDERNO, RUNCOUNT)` | per-run info: `NODEID`, `MEMNAME`, `CPUTIME`, `ELAPTIME`, `STATUS`, `OSCOMPSTAT`, `STARTRUN`/`ENDRUN` |
| `CMR_JOBINF` / `CMR_JOBINF_<N>` | job info (partitioned by `<N>`) |
| `CMR_IOALOG` / `CMR_IOALOG_<N>` | `(LOGDATE, LOGTIME, KEYSTMP)` | the **IOA log** — run/event messages: `JOBNAME`, `JOBNO`, `ORDERNO`, `USERNAME`, `NODEID`, `ODATE`, `MSGID`, `MESSAGE`, `TASKTYPE` |
| `CMR_STATIS` | `KEYSTMP` | run statistics: `ELAPSED`, `CPUTIME`, `LIBRARY`, `MEMNAME`, `JOBNAME`, `SCHEDTAB` (+ `_SD` std-dev variants) |
| `CMR_ECSMSG` | `(ECSMSG_ISN, USERNAME)` | ECS messages |
| `CMR_DBLOG` | `KEYSTMP` | DB log: `DBULVL`, `DBMESSAGE`, `MSGSIZE` |
| `CMR_UDLAST` | `DAILYNAME` | user-daily last run/end |
| `CMR_QRUSE` | `(QRESNAME, QR_REQ, ORDERNO)` | live QR usage: `JOBUSED`, `RESERVE` |
| `CMR_CTLUSE` | `(CONTROL, ORDERNO)` | live control-resource usage: `CMODE`, `RESERVE` |
| `CMR_LASTNO` | `TABLENAME` | last-ISN counters |

---

## §GRP-POOL — Pool Resources (CMR_)

The live resource + condition pools the scheduler evaluates.

| Table | PK | Purpose |
|-------|----|---------|
| `CMR_CONTAB` | `(CONDNAME, CONDDATE)` | **prerequisite conditions table** — the live pool of conditions that exist right now. In/out condition rows reference conditions here by `CONDNAME` + date. |
| `CMR_QRTAB` | `QRESNAME` | quantitative-resource pool: `QTYPE`, `QRTOTAL`, `RSRVNO`, `QRUSED` |
| `CMR_CTLTAB` | `CONTROL` | control-resource pool: `CMODE`, `RESCOUNT`, `USECOUNT` |
| `CMR_RESOURCELOCK` | `(RESOURCE_NAME, RESOURCE_TYPE)` | resource lock: `LASTEND` |

---

## §GRP-CONFIG — Configuration Parameters

| Table | PK | Purpose |
|-------|----|---------|
| `CMS_CMNPRM` | `(COMPUTER, OPSYS, VERSION, CMVERSION)` | server-wide config: `DBVERSION`, `DATETYPE`, `LOGDIR`, `PROCLIB`, `CM_DATE`, `SWEEK`, and the `MAX*` limits (`MAXJOBLOG`, `MAXAJFREC`, `MAXTRY`, …), `NEWDAY`/`DAYTIME`, retention (`IOALOGLM`, `SYSOUTRETN`) |

---

## §GRP-DIAG — Diagnostics (CMR_)

| Table | PK | Purpose |
|-------|----|---------|
| `CMR_SP_DIAG_MESSAGES` | `(SPNAME, TIMESTMP, KEYCNT)` | diagnostic messages: `MESSAGE` |
| `CMR_SP_DIAG_REQUEST` | `SPNAME` | diagnostic request flag: `DIAGREQ` |

---

## §GRP-AGENTS — Agents & Remote Hosts

| Table | PK | Purpose |
|-------|----|---------|
| `CMS_AGPRM` | `NODEID` | agent parameters: `PHYSNODEID`, timeouts, `PORTNUM`, `POLLTIME`, `COMVERSION`, `SSL_SYNC`, `PERSISTENT_CONNECTION` |
| `CMS_MACHINE_MAP` | `NODEID` | logical→physical machine map: `PHYS_NODEID`, `AGSTAT`, `HOSTNAME`, `DOMAIN_NAME`, `OS_NAME`, `PLATFORM`, `IS_DEFAULT` |
| `CMS_WMI_DETAILS` | `TARGET_MACHINE` | Windows WMI: `SYSOUT_DIRECTORY` |
| `CMS_SSH_DETAILS` | `TARGET_MACHINE` | SSH: `PORT_NUMBER`, `ENCRYPTION_METHOD`, `COMPRESSION` |
| `CMS_RJX_NAMES` | `(TARGET_MACHINE, RJX_NAME)` | remote-job-execution names |
| `CMR_NODES` | `NODEID` (+`AGENTID`) | live agent status: `PHYS_NODEID`, `AGSTAT`, `FIRST_SET`, `LAST_UPD`, `NODETYPE`, `HOSTNAME`, `OS_NAME`, `PLATFORM` |
| `CMR_NODES_RJX_STATUS` | `(NODEID, APPLTYPE)` | per-application-type agent version: `APPLVER`, `CMVER` |

---

## §REL — Relationships worth remembering

- `CMS_JOBDEF (JOBNO)` ⟵ every `CMS_*` child (SETVAR, CON_J, ONSTMT, DO, SHOUT,
  CTL_J, QR_J, SYSOUT, DATES, TAGLINK, FORCEJ, MAIL, REMEDY).
- `CMR_AJF (ORDERNO)` ⟵ every `CMR_*` child (same shape, runtime).
- `CMR_AJF.JOBNO → CMS_JOBDEF.JOBNO` — runtime instance → its definition.
- `CMS_JOBDEF.SCHEDTAB` groups jobs into a **folder / schedule table**
  (`CMS_SCHEDT`); `APPLGROUP`/`APPLIC` are the business app grouping.
- Conditions are the dependency fabric: a job **emits** out-conditions and
  **consumes** in-conditions; the live set lives in `CMR_CONTAB`. Job B depends
  on Job A when B's in-condition name = A's out-condition name (same `ODATE`
  reference). This is the edge the DryDocs dependency graph is built from.
- Resources gate concurrency: `CMS_QR_J`/`CMS_CTL_J` (requests) vs
  `CMR_QRTAB`/`CMR_CTLTAB` (pools).
