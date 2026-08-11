---
standard: control-m-greenfield-job
domain: technology
taxonomy_path: technology/orchestration/control-m/job
governs: ControlMFolder.variables · ControlMJob.variables · ControlMJob.description
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: planned
trust_tier: internal / SME-asserted / planned
---

# Control-M Greenfield Job Standard — variables and description across FileWatcher, Placement and Trust

**Corpus:** INTERNAL-PUBLIC (mechanism half). **Status:** 🔵 **PROPOSED — 2026-08-11 (C30).**
**Role:** the target state for a four-job ingestion flow — what each job declares, where each
declaration lives, and what the description carries. Written to be **published as the revised
standards page**; the values twin at
[`internal/standards/technology/controlm-greenfield-job-standard.md`](../../../internal/standards/technology/controlm-greenfield-job-standard.md)
holds the real folder, accounts and ids.

> 🔒 **Split twin (J14).** This file is the publishable MECHANISM half. Real folder and job names,
> service accounts, SEALs, FIDs, GUIDs, DL addresses and author ids live ONLY in the values twin.
> Examples below use the synthetic SEAL block **70001–70099** and `example.invalid` addresses.

> 📄 **This is the RATIONALE half.** The normative page a job author follows is
> [**Control-M Guidelines & Standards**](controlm-guidelines-and-standards.md) (C31) — the same
> decisions in MUST/SHOULD voice, with the scope diagram and a worked resolution trace, and no
> argument. Three documents, three jobs: **normative there, rationale here, enforcement in the
> rules registry.** Keep it that way; two pages arguing the same point is how a standards corpus
> becomes five contradictory ones.

**Machine-checked.** Every rule here has a detector:
`drydocs_remediation.detect.detect_conformance` (rules R2, R30–R40, registered in the internal
rules registry). The test suite pins the pair that matters — a flow built to violate the standard
raises every rule, and the same flow rebuilt to this page raises **none**. A standard nobody can
reach is a wish.

---

## 0. Why this exists — the defect is the contract, not the jobs

Three sources describe the same four job types and disagree: the requirements pages, the DPL
generator, and what is deployed. Reading the generator **before** the deployed folder reverses the
obvious reading.

The generator emits a **partial job**. Each builder's command line references tokens it does not
declare, and expects the rest from a **folder-level `AUTOEDIT` / `SET VAR` block**. The two builders
do not even agree with each other about which side of that line four common variables sit on. When
the folder block is missing, or its contents are simply unknown to whoever is editing, people
hand-add the missing variables **job by job** — and the copies drift.

Every deployed defect traces to that: a launcher variable hand-added twice under two spellings, one
of them not matching the command that references it; a dataset id and a dataset version holding each
other's values; a canonical name spelled with an extra underscore so it produces no lineage row at
all. The generator had these right.

**So the fix is the contract, not the instances.** Declare which scope owns each variable, once, and
the whole class disappears.

---

## 1. The scope ladder

Three scopes, and the rule for choosing between them is a question about the VALUE, not the job:

> **Declare a value at the widest scope where it is still true.** A value true for the whole flow
> belongs to the folder. A value true for one dataset belongs to that dataset's sub-folder. Only a
> value that differs between two jobs of the same dataset belongs to a job.

| Scope | Holds | Example members |
|---|---|---|
| **SMART folder** | flow invariants — the runtime contract, the artifact, the operational contacts | `ENV` `FID` `SEAL` `CONF_PATH` `LAUNCHER_SCRIPT_PATH` `ETL_PLATFORM` `ETL_ARTIFACT_URI` `ETL_ARTIFACT_KIND` `ETL_PLATFORM_FLAGS` `TIMEOUT` `POLLING_INTERVAL` `FILE_BKP_DIR` `DEVX_KEY` `EMAIL_DL_L2` `EMAIL_DL_L3` `EMAIL_DL_PDN` |
| **Sub-folder, one per dataset** | dataset identity and the file it names | `DATAFLOW` `DS_ID` `DS_VER` `FILE_DIR` `FILE_PREFIX` `FILE_BUSINESS_DATE` + the derived handles |
| **Job** | only what genuinely differs between the four | `FILE_EXTENSION` (`.txt` on the DAT watcher, `.tok` on the TOK watcher) |

For a folder of three datasets × four jobs that is roughly **45 declarations instead of 180**, and —
the point — **one** copy of each value to maintain.

**Vendor warrant.** BMC resolution order is local → SMART folder → global → the reserved word
`CTMERR`. Folder scope resolving into a job is documented behaviour, not a trick.

⚠️ **One caveat that matters.** Folder-scope resolution is documented for **job processing
parameters** — command line, watch path, post-execution command. Resolving a folder variable inside
a job's **script** additionally requires `VARIABLE_INC_SEC = Global` on the Control-M/Server. Every
reference in this standard is a processing parameter, so the ladder does not depend on that setting;
confirm it before moving a script's references.

**Sub-folder per dataset is required, not stylistic.** One folder cannot hold three values for
`FILE_PREFIX`. Without the sub-folder layer the dataset identity falls back to job scope and the
copy-paste class returns.

---

## 2. Naming — one name per concept, one hop to SQL

> **The variable name, the `STG_APP_FACT.fact_type`, the SQL column and the ontology property stem
> are the SAME token. `UPPER_SNAKE`. The launcher *flag* is a binding recorded in the per-framework
> command template — never the variable's name.**

That is why the payload artifact is `ETL_ARTIFACT_URI` and not `IMG`: the concept names the
variable, the `-img` flag is just how one launcher spells it. One hop, no translation table.

**Lookup is exact.** Control-M variables are case-sensitive at execution, so the registry does not
case-fold — normalising would silently merge bindings someone meant to keep distinct. The cost of
that correct decision is that `DATA_FLOW` is not `DATAFLOW`: it misses the registry, writes no fact
row, and the dataset simply has no lineage. **Drift is silent, which is why it survives.**

Non-canonical names still materialise through the alias map with a rename WARN — legacy is never
broken — but WARN-free is the target.

### Vendor legality (R38)

BMC **forbids** these in user-defined variable names, plus blanks:
`< > [ ] { } ( ) = ; ` ~ | : ? . + - * / & ^ # @ ! , " '` — and caps user-defined names at 38
characters. The hyphen being forbidden settles two names outright:

| Requirements page | Standard | Why |
|---|---|---|
| `DevX-project` | **`DEVX_KEY`** | hyphen illegal; the live spelling is also shorter and the only one that satisfies `UPPER_SNAKE` |
| `%%FileWatch-FILE_PATH` | **`FILE_PATH`** | hyphen illegal, AND `FileWatch-` is a vendor **plugin namespace** (the `%%SAPR3-` application-prefix form). A hand-declared user variable may not sit inside one |
| `L2_EMAIL_DL_NM` / `L3_EMAIL_DL_NM` | **`EMAIL_DL_L2` / `EMAIL_DL_L3`** | one prefix, sortable, extensible — and it already has a third member |

In all three the deployed build is right and the page is wrong. **The page changes, not the jobs.**

---

## 3. The file name — broken out for SQL, short in the command

Two requirements pull opposite ways. The file name must be **decomposed**, because that is how
watchers are built and how the SQL parse populates `CM_JOB_FILE_NAME_STANDARD`. But a command line
that repeats a four-part composition is unreadable and — as the deployed folder shows — gets edited
in one place and not the other.

**Declaring the components and DERIVING one handle from them dissolves the conflict.** The
components stay decomposed for SQL; the commands reference a single token.

```
# sub-folder scope — components, each one an SQL column
FILE_DIR           = /data/<tenant>/dropbox/UPD/
FILE_PREFIX        = SAMPLE_LKP_
FILE_BUSINESS_DATE = %%$ODATE

# sub-folder scope — derived once, referenced everywhere
F_NM_DAT   = %%FILE_PREFIX.%%FILE_BUSINESS_DATE..txt
F_NM_TOK   = %%FILE_PREFIX.%%FILE_BUSINESS_DATE..tok
F_FQN_DAT  = %%FILE_DIR.%%F_NM_DAT
F_FQN_TOK  = %%FILE_DIR.%%F_NM_TOK

# job scope — the one thing that differs
FILE_EXTENSION = .txt          (DAT watcher)   |   .tok   (TOK watcher)
```

Then every consumer is one token:

```
DAT watcher   Path      : %%F_FQN_DAT          (no post-command — see §5)
TOK watcher   Path      : %%F_FQN_TOK
              Post-exec : cat %%F_FQN_TOK
TRUST         Post-exec : mv %%FILE_DIR/%%F_NM_DAT %%FILE_BKP_DIR/%%F_NM_DAT
```

**This is the corpus's own idiom, generalised.** REQ-3 already defines `%%POSTCMD` as *"cats the
value from the previous variable"* and states **"Order matters"** — document order is the
sequential-assignment contract. Deriving `F_FQN` from `F_NM` from the components is the same move,
one step further.

Three things fall out of it:

- **One place to change.** The deployed TOK watcher has a path referencing two names it never
  declares while its declared names go unused — a rename finished on one field and not the other.
  With a derived handle there is one reference per field, and the derivation is the only edit.
- **The token-cat rule becomes checkable.** "Post-command references the watch-path variable
  expression" is nearly impossible to assert. `post_command == "cat " + watch_path` is string
  equality.
- **The naming tension disappears rather than being traded off.** Components keep the long,
  SQL-aligned names; the command sees `%%F_FQN_TOK`.

> ⚠️ The `..` before the extension is correct, not a typo: Control-M **consumes** the first dot as
> the concatenation delimiter, so the second is the literal separator. The alternative — storing
> `.txt` with its leading dot — also works and is what the file-name component standard's controlled
> vocabulary does. Pick one per estate; do not mix. What is forbidden either way is R1's
> dot-smuggling: a variable whose value is a **bare** `.`.

---

## 4. Variables by job type

Names are canonical; **Scope** is where the declaration lives, not where it is used.

### 4.1 FileWatcher (`_DAT_ONPM_FW`, `_TOK_ONPM_FW`)

| Variable | Scope | Purpose | SQL column |
|---|---|---|---|
| `FILE_DIR` | sub-folder | watched directory, trailing `/` | `FILE_DIR` |
| `FILE_PREFIX` | sub-folder | static business identifier | `FILE_PREFIX` |
| `FILE_BUSINESS_DATE` | sub-folder | the date the DATA represents | `FILE_BUSINESS_DATE` |
| `FILE_EXTENSION` | **job** | `.txt` \| `.tok` — drives DistributionRole | `FILE_EXTENSION` |
| `F_NM_*` / `F_FQN_*` | sub-folder | derived handles | *(derived — never parsed)* |

`FILE_EXTENSION` is referenced by nothing at runtime and that is correct: it is declared **for the
record**, so the SQL parse can read it. The orphan rule (R31) exempts registered facts and standard
metadata fields for exactly this reason.

### 4.2 Placement (`_AWS_PLCT`) and Trust (`_AWS_TRUST`)

Under the ladder these jobs declare **nothing of their own**. Everything resolves from the folder
and the sub-folder.

| Variable | Scope | Notes |
|---|---|---|
| `LAUNCHER_SCRIPT_PATH` | folder | the deployed folder declared it twice under two spellings and referenced a third — the single clearest argument for the ladder |
| `ETL_PLATFORM` · `ETL_ARTIFACT_URI` · `ETL_ARTIFACT_KIND` | folder | required on every command job (REQ-4); absent from the deployed folder entirely |
| `ETL_PLATFORM_FLAGS` | folder | optional per REQ-4 |
| `ENV` · `FID` · `SEAL` · `CONF_PATH` · `TIMEOUT` · `POLLING_INTERVAL` | folder | flow invariants |
| `DATAFLOW` · `DS_ID` · `DS_VER` | sub-folder | dataset identity |
| `APP_NAME` · `ALIAS` | folder | launcher arguments |

**Value contracts.** `DS_ID` is a UUID and `DS_VER` is dotted-numeric. This is not pedantry: in the
deployed folder the two hold each other's values on one job. Both names resolve, so **both write a
fact row and one of them is false** — a wrong row, not a missing one, and the worse of the two
failure classes.

`ETL_ARTIFACT_URI` must be a **registry-qualified URI**, not a bare image name. The security
boundary (NF-SEC-2) restricts artifact sources to approved repositories, and a bare name names no
repository. `ETL_ARTIFACT_KIND` gains `container` alongside `wheel` / `jar` / `pset` / `other`.

### 4.3 `pipelineId` — the literal is the carrier

The generator declares **no** `PIPELINE_ID` variable and its command line does not reference one:
the GUID is baked in at generation time from the pipeline configuration. That is the right call —
the id is generator-owned and immutable per pipeline, and a variable makes it hand-editable, which
is the drift class this whole standard exists to close.

**Ruling: the command literal is the carrier. Any `PIPELINE_ID` variable is removed, and
NFR-CTM-001 §6.1/§6.2 are corrected to drop `%%PIPELINE_ID` from the templates.** Where both exist —
as they do in the deployed folder — they can disagree silently, the command wins, and the variable
lies.

> **One consequence, paid for rather than assumed away.** The pipeline GUID is the join key into the
> DPL dataset-flow lineage, and NFR §10 refuses to parse `CMDLINE`. Under this ruling the id would
> never reach `STG_APP_FACT`. The standard therefore grants **one anchored extractor** —
> `-pipeline <uuid>`, matched on the flag and validated as a UUID, nothing else. This is a named
> exception to §10, not a reopening of it.

### 4.4 Ab Initio

Same pattern. Its `-p %%JOBNAME-%%ODATE-%%ORDERID-%%RUNCOUNT` order prefix is a composed handle
built inline; it becomes a derived `AI_ORDER_PREFIX` for the same reason `F_FQN` exists.

---

## 5. The description — only what has no other home

> **The description carries facts with no runtime role and no other carrier. Anything already in a
> variable, or derivable from the job name, does not go in the description.**

The field is 1–4000 characters and is **not** runtime-accessible as a `%%` variable, which is what
makes it safe to restructure and also what makes it unable to drive anything. It is a graph feed.

### 5.1 FileWatcher

```
DELIVERY_MECHANISM: MFTS_AGENT | USER: <transfer-account> | FTS_ID: FTS2 |
REC_ID: <id>,<id> | SOURCE_CONTACT: <origin-owner-DL>
```

These are transfer facts: how the file arrived, over which instance, on whose account, referenced by
what at the source. None has a runtime role and none has another carrier. Four rulings:

- **`ENV` → `FTS_ID`.** On a watcher description `ENV` named an MFTS File Transfer instance; on the
  command jobs `ENV` is the deployment environment (`prod`). One key, two concepts, landing in the
  same SQL and the same graph. The transfer instance moves; `ENV` keeps the meaning it already has
  everywhere else.
- **The value is the bare transfer id.** A version fragment is dropped: `ST 6.0 - FTS2` → `FTS2`.
  Known members `FTS1`, `FTS2`, `FTS6`, `FTS7`, `FTSCAT1`; the check is a **shape**
  (`^FTS[A-Z]*[0-9]+$`), not a closed enum, because new instances appear — and `FTSCAT1` already
  breaks a naive `FTS<digit>` pattern.
- **A file watcher is inherently INBOUND.** Direction is carried by the job type and is not
  re-encoded in a token. That retires the `INBOUND_ROUTE` / `OUTBOUND_ROUTE` pair and
  `ex:mftsRouteDirection`: from the watcher's side there is no outbound leg to describe.
- **`REC_ID` is a source-system reference, not a route pair.** It is multi-valued, comma-separated.

**The outbound leg is not lost — it is a variable.** The watched directory *is* the landing zone, so
`FILE_DIR` feeds `dprod:outputPort` (the deposit path the DPROD model already has), while `REC_ID`,
`USER`, `FTS_ID` and `DELIVERY_MECHANISM` feed `dprod:inputPort`. Description carries the source
side, variables carry the target side, nothing is stated twice.

### 5.2 Placement and Trust

```
JOB_ROLE: PLACEMENT          JOB_ROLE: TRUST_INGEST
```

That is the whole set. Everything a reader might want is a variable (`DATAFLOW`, `DS_ID`,
`ETL_ARTIFACT_URI`) or derivable from the job-name suffix. Padding these for symmetry would create a
second copy of facts that already have a home.

`JOB_ROLE` earns its place as the **discriminator** that tells the SQL parse which table a row lands
in.

> **This also resolves the generated-description collision.** The generator stamps a fixed literal
> per builder via `get_description()`, and a provenance check keys on matching that literal exactly.
> A token block in the same field would break the match. Because both the literal and the tokens
> come from the same function, the exit is clean: the discriminator becomes a **token**
> (`GENERATED_BY`), not an exact-string match.

### 5.3 Contacts are documentation, and they stay at folder scope

Notification is being **removed** as a mechanism. Control-M shouts are deleted (REQ-2); generated
mail adds noise; **the failure raises a ServiceNow incident, and the incident is the call to
action.**

So `EMAIL_DL_L2`, `EMAIL_DL_L3` and `EMAIL_DL_PDN` are **folder-scope documentation**, extracted
later for runbooks. They are deliberately not wired to anything.

**Do not "fix" the unset mail destination by pointing it at a support DL.** Every generated job
emits `<DOMAIL DEST="%%NOTIFY">` and nothing assigns `%%NOTIFY`. Under this standard that is an
ordinary unresolvable reference to report (R30) — never an invitation to re-wire the mechanism being
removed.

**Two different kinds of contact, despite the shared prefix.** `EMAIL_DL_L2` / `EMAIL_DL_L3` are
internal **support tiers** (`ex:supportContact`). `EMAIL_DL_PDN` is **Production Delay
Notification** — downstream *business* users told that a delay affects them (`ex:consumerContact`).
Same carrier, different audience, different ontology role; the register must never collapse them.

**No ServiceNow queue belongs in a Control-M variable.** Technician routing lives in the escalation
DB, joined on the job name with SEAL via the component column, and the HPSM-queue → SNOW-technician
mapping is a later step. `PDN_SNOW_QUEUE` is therefore **dropped** from the standard rather than
relocated: it paired a downstream *business* notification with a ServiceNow *technician* queue,
which are different audiences.

### 5.3.1 `<DOMAIL>` goes too — SME ruling, 2026-08-11

REQ-2 removed `<SHOUT>`/`<DOSHOUT>` and left `<DOMAIL>` *"out of scope for this requirement and
remains"*. The SME has now ruled that mail goes with the shouts: the whole `ON … NOTOK` → `DOMAIL`
block is deleted, and the destination reference goes with it. R40 is widened accordingly.

Two things make this cheaper than it looks, and both are worth recording because they are the
argument, not the decision:

**The destination has more than one spelling.** The generator emits `%%NOTIFY`; a deployed on-prem
load job carries an On-Do action reading *"When Job ended Not OK — Send mail notification to
`%%EMAIL_GRP`"*; a hand-built Ab Initio folder declares a third, `%%EMAIL_GRP_S`.

**CORRECTED 2026-08-11 (C32).** This section first argued that none of them is declared, so the
block already resolves to `CTMERR`, mails nothing, and deletion costs nothing. That is true of the
DPL-**generated** folders and **false** of the hand-built ones, which declare all three to a real L2
support address — there the block sends. The ruling stands; the argument does not, and the honest
version is: on generated folders this is cleanup, on hand-built ones it is a deliberate removal of
a working mail path, made because the ServiceNow incident is the call to action. Carrying the easier
argument would tell a reader who meets a hand-built folder that the rule does not apply to them.

**A second spelling is itself the R33 argument in miniature.** Two names for one concept, neither
declared, is exactly the drift the one-name-per-concept rule exists to stop. Repairing the block
would mean first ruling which name is canonical — paying the naming cost for a mechanism being
retired.

What survives is documentation: `EMAIL_DL_L2` / `EMAIL_DL_L3` / `EMAIL_DL_PDN` stay folder
variables, read by the runbook extractor, wired to nothing.

---

## 6. Post-execution commands — two clauses, and the forbidden one is the risk

| Watcher DistributionRole | Post-execution command |
|---|---|
| **TOK / CTL** | **MUST** be `cat ` + the watch path, the same expression |
| **DAT** (`.dat` `.csv` `.txt`) | **MUST NOT** cat |

The required clause gives upfront TDQ: the declared record count lands in the watcher's sysout at
detection time, before ingestion, so a short feed is caught at the transfer rather than blamed on
the load.

The forbidden clause is the operational risk, and it is currently violated: **data files can be
multi-GB, and echoing one into sysout floods the log and can breach sysout limits.** REQ-3 says "for
job type file_watcher" without qualification, which reads as *all* watchers. It needs this scope
correction.

---

## 7. Naming and numbering — three schemes are live

| Scheme | FW | Move | Placement | Ingest | Trust | Provision |
|---|---|---|---|---|---|---|
| Generator | 0001 | 0005 | 0020 | 0050 | 0051 | 0060 |
| HLT bands | 0010 | — | 0020 | — | 0050 | 0060 |
| Observed | dataset-grouped (`902x` / `903x` / `904x`) | | | | | |

**Recommend the HLT functional bands**, since R29 already governs them (fixed-width zero-padded, a
linear extension of the dependency DAG, gaps for insertion). Two corrections follow: the generator's
`FW=0001` collides with HLT's House Keeping slot and must move; and the generator's grammar hardcodes
`_AWS_`, so it cannot express an on-premises watcher at all. Add two slots:

```
{APP[:4]}{FREQ}{JOB_NUM}_{SOR}_{DATASET}_{PAYLOAD}_{CHANNEL}_{TYPE}
                                          DAT|TOK   AWS|ONPM
```

Sub-foldering per dataset makes the grouped-vs-banded argument moot — the GUI groups by sub-folder
and the band orders within it.

---

## 8. Use the tool's own guardrails

The observed folder has **Enforce Validations** unchecked and **Site Standard: `-- None --`**. A
Site Standard enforces a required declaration set **at author time**, in Control-M, instead of a SQL
check discovering the gap afterwards. Recommended — confirm what the environment licenses before
committing to it.

---

## 9. What this buys — the lineage join

Today the four jobs of one dataset **cannot be joined**. Each spells the file differently
(`FILE_PREFIX` + `FILE_EXTENSION` on the watchers, a full path on Placement, a basename on Trust),
and the dataset key misses the registry so there is no dataset identity at all.

Under this standard all four inherit `DATAFLOW` and `DS_ID` from one sub-folder, and the file
resolves to one derived handle whose components land verbatim in `CM_JOB_FILE_NAME_STANDARD`:

| Join | Key |
|---|---|
| the four jobs of a dataset | sub-folder = `DATAFLOW` = `DS_ID` |
| Control-M → the file | `FILE_PREFIX` + `FILE_BUSINESS_DATE` + `FILE_EXTENSION` |
| Control-M → DPL dataset-flow lineage | the `-pipeline` GUID, via the §4.3 anchored extractor |

**FW → PLCT → TRUST becomes a lineage chain instead of three unrelated rows.** That is the whole
return on the standard.

---

## 10. Open items

1. **`SOURCE_CONTACT`** — a DL rather than a named person? The observed value is an individual.
2. **The dot convention** — `..` before the extension, or the dot stored inside `FILE_EXTENSION`?
   Both are legal; the estate should pick one. (§3)
3. **Site Standards licensing** (§8).
4. **Job-number band collision** — the generator's `FW=0001` vs HLT's House Keeping. (§7)

*Closed 2026-08-11:* **REQ-2 and `<DOMAIL>`** — mail is removed alongside the shouts (§5.3.1).

Related: [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]],
[[project-runbook-automation-usecase]], [[project-folder-naming-praocg]]
