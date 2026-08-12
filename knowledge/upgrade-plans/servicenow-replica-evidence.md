# ServiceNow replica — the instance evidence (K21)

**Classification:** Internal-Public — **mechanism only** (see §0 for what is deliberately absent).
**Captured:** 2026-08-09, from an SME DBeaver session against the replica. **Analyzed:** same day.

**Companion to [`servicenow-cmdb-analysis.md`](servicenow-cmdb-analysis.md) (C10), and the split
between the two files is the point.** That file reads the **vendor doc set** — the canonical CMDB/CSDM
model, which is the **baseline**. This file reads the **replica** — what our instance actually
contains, which is the **instance**. Where they differ, the difference is a company extension or a
carrier artifact, and naming it is a deliverable rather than a footnote.

**Feeds:** `tom-roles-enumeration-and-cardinality` (G35, in progress) and
`seal-tom-attribution-reshape`. **Nothing here is adopted.** No source is activated, no loader is
built, no gate is signed. Findings feed those gates; they do not pre-empt them.

---

## 0. The boundary

The evidence is four screenshots held on the laptop and gitignored by the root `/*.png` rule. They
are Internal. **Never in this repo:** the replica host, the database name, the literal schema names,
the company string that fills `x_<scope>_`, SEAL application and deployment ids, configuration-item
names, company/LOB filter values, and any `sys_id` GUID.

**Here, because it is mechanism:** stock ServiceNow table and column names (public — the vendor
documents them), the join shape, the *classes* of local extension (`u_`, `x_<scope>_`), and the
replica's own carrier columns. A reader can rebuild the query; a reader cannot learn who or what it
returned.

---

## 1. The working query, as mechanism

### 1.1 The join spine

Nine table references, all `LEFT JOIN`, anchored on the TOM assignment row. Aliases are the SME's.

```
x_<scope>_cmdb_tom_main            tom_main    -- ANCHOR: one row per TOM assignment
  -> x_<scope>_cmdb_tom_roles      resp        ON tom_main.role       = resp.sys_id
                                                  AND resp.active = TRUE
  -> cmdb_ci                       cmdbci      ON tom_main.parent_id  = cmdbci.sys_id
  -> core_company                  cc_cmdb     ON cc_cmdb.sys_id      = cmdbci.company
  -> cmdb_ci_service_discovered    disco       ON disco.sys_id        = cmdbci.sys_id
  -> sys_user_group                sug         ON sug.sys_id          = tom_main.group
                                                  AND sug.active = TRUE
  -> cmdb_ci                       cmdbci_inh  ON cmdbci_inh.sys_id   = tom_main.inherited_from_ci
  -> cmdb_ci_business_app          bap         ON bap.sys_id          = cmdbci.sys_id
                                                  AND bap.u_external_service = FALSE
  -> sys_user_group                sug_2       ON sug_2.sys_id        = cmdbci.assignment_group
                                                  AND sug_2.name IS NOT NULL
```

Filters: one company; role name `LIKE '%change%'` **and** `LIKE '%approval%'`; application state in
a four-value set; one SEAL application id; one named configuration item.

### 1.2 The column map

| Source column | Table | DryDocs vocabulary | Standing |
|---|---|---|---|
| `tom_main.number` | TOM (scoped) | the assignment's own record id | **NEW** — no counterpart; TOM rows are records with identity, not derived pairs |
| `tom_main.role` → `tom_roles.sys_id` | TOM (scoped) | `TOMRole` concept | **NEW EVIDENCE** — the vocabulary is a *table*, see §4 |
| `tom_roles.name` | TOM (scoped) | role class name | assumed by G35 §A |
| `tom_roles.active` | TOM (scoped) | — | **NEW** — role classes retire; no DryDocs equivalent |
| `tom_main.parent_id` → `cmdb_ci.sys_id` | TOM (scoped) | the attribution subject | **NEW** — subject is a *CI*, see §1.3(c) |
| `tom_main.group` → `sys_user_group` | TOM (scoped) | attribution holder | **TENSION** with G35 §B6, see §4 |
| `tom_main.inheritance` | TOM (scoped) | assertion mode | assumed by G35 §E1 — **now confirmed as data** |
| `tom_main.inherited_from_ci` | TOM (scoped) | inherited-from pointer | assumed by G35 §E1 — **and E4's premise changes**, see §4 |
| `cmdb_ci.sys_class_name` | stock | the CI's actual class | **NEW** — the discriminator that makes §1.3(b) readable |
| `cmdb_ci.u_status` | local `u_` | lifecycle status | **NEW** |
| `cmdb_ci.company` → `core_company.name` | stock | LOB / company | partial — DryDocs has LOB→Product→Team |
| `cmdb_ci.assignment_group` → `sys_user_group` | stock | the support queue | **NEW** |
| `disco.u_seal_application_id` | local `u_` | the SEAL join key | assumed — **but not where assumed**, see §1.3(c) |
| `disco.u_seal_deployment_id` | local `u_` | *no counterpart* | **NEW — the sharpest finding**, see §4 |
| `disco.correlation_id` | stock | cross-system correlation | **NEW** |
| `disco.u_application_state` | local `u_` | lifecycle state (Build/Operate/Plan/Retired) | **NEW** |
| `bap.u_external_service` | local `u_` | in/out-of-scope flag | **NEW** — used as a filter, not selected |

### 1.3 Five observations that change how the query should be read

**(a) The anchor is the TOM row, not the application.** The query enumerates *assignments* and
resolves each one outward to its subject, its role, and its holder. An ingestion built by
"start at the application, collect its contacts" inverts this and will not reproduce it, because a
TOM row can point at a CI that is not a business application at all.

**(b) Three of the nine joins are the same configuration item seen through its class tables.**
`cmdb_ci`, `cmdb_ci_service_discovered` and `cmdb_ci_business_app` all join on **the same `sys_id`**.
That is ServiceNow's table-per-class inheritance: a CI has one row in the base table and one in each
class table it extends, sharing an identity. `cmdb_ci_service_discovered` extends `cmdb_ci_service`,
which extends `cmdb_ci`.

*Consequence for DryDocs:* these are **not three entities to ingest as three node classes.** They are
one CI with class-specific attribute sets, and `sys_class_name` says which class it actually is. An
ingestion that treats each view as a separate dataset and each row as a separate node will multiply
every CI by its class depth. This is the single most likely way to get the pull wrong, and it is
invisible from the view list — only the shared-`sys_id` join reveals it.

**(c) The SEAL identifiers live on the Application Service, not on the Business Application.**
`u_seal_application_id` and `u_seal_deployment_id` are read from `disco` —
`cmdb_ci_service_discovered`, which CSDM maps to **Application Service**. `cmdb_ci_business_app` is
joined but contributes **no selected column**; it appears only to supply the
`u_external_service = FALSE` filter.

This matters because DryDocs attributes to `:BusinessApplication`. The ServiceNow surface attributes
to the deployed-service layer *beneath* it. C10 already flagged this exact gap — "an application
service is a logical representation of a deployed application stack and is **not** the application" —
and parked it as gate-bound candidate #1, "only when an environment-level use case lands." §4 argues
the use case has now landed.

> **SME CONFIRMATION, 2026-08-09** (given on this finding, recorded verbatim in substance):
> **one application, multiple deployments is correct**, and the identifier shape reads as
> **`app_id(seal_id):deployment_id`**.
>
> Two things follow, and they are different in kind. **The cardinality is now a stated fact**, not
> an inference from column names: the application→deployment relation is 1:N, which is what gate-bound
> candidate #1 was waiting on. **The key shape is the SME's read of the data** ("looks like"), and it
> carries a consequence worth pinning before anyone builds on it: if the deployment identifier is
> *scoped under* the application id, then **a bare `deployment_id` is not a business key** — the key
> is the pair. Keying a future deployment node on `deployment_id` alone would collide across
> applications wherever the source restarts its numbering.
>
> This repo has been here before, which is why it is worth stating rather than assuming: identity
> gate §D2 pinned the 4-part `attribution_id` for exactly this reason, and §C3 refused the tempting
> narrower key because MERGE would have collapsed distinct rows. Same shape, new axis.
>
> **THE CAVEAT, same session — and it is the part that decides what to build.** SME: *everything
> we map is off the **application**. Modules are referenced by default for changes, but in practice
> are not used as intended.*
>
> So the grain question (§6 Q3) is answered for **practice**: mapping and accountability are done
> at the **application** level. The deployment id is real and the 1:N is real, but the deployment is
> **not** the attribution subject, and DryDocs attributing to `:BusinessApplication` is therefore
> *correct as-is* rather than one layer too high. That materially narrows what the re-opened C10
> candidate #1 is for: it is about **capturing an identifier the source carries and we discard**,
> not about re-homing attribution. Those are very different pieces of work, and the second one is
> the expensive one we are now not doing.
>
> **The module half is a second finding — and the first reading of it here was too strong.**
> Corrected by the SME on 2026-08-10, because the distinction decides real work:
>
> - **The Deployment Module CI is real.** It has its own unique CI id, a defined place in the
>   relationship chain (§1.4), and KB articles attached to it. It is a genuine grain, not an artifact.
> - **What is unreliable is the module reference on TRANSACTIONAL records.** In ServiceNow a Change,
>   an Incident and a KB article must each name a deployment module, the form defaults it, and people
>   generally accept the default. So the *link from a change to a module* is noisy; the *module* is
>   not.
>
> This document originally collapsed the two and concluded that a DryDocs module grain "would model
> the form default rather than the operating model," and that G35 §G15 could be ruled without
> inventing a grain. **That was wrong in the direction that matters** — it would have discarded a
> real CI class on the strength of a defaulted foreign key. The correct statement: the grain is
> sound, and any *counting* of changes or incidents per module is not.
>
> §3.2's lesson still applies, just to the right column: a populated field can be emptier than a null
> one, and here it is the transactional reference — the field most likely to be trusted, because it
> is never empty.
>
> **What is still open** (§6 Q7): whether `u_seal_deployment_id` is globally unique or unique only
> within its application. Still worth settling even though the deployment is not the attribution
> subject — the moment the id is captured at all, it needs to be captured under the right key.

**(d) As sampled, the TOM assignment names a GROUP, not a person.** `tom_main.group` resolves to
`sys_user_group`. There is no `sys_user` join anywhere in the query, and no person column is
selected. **Stated as a limit, not a conclusion:** this proves the SME's report attributes to a
group; it does not prove `tom_main` lacks a user column. §6 carries it as an open question. It is
raised because G35 §B6 records the SME direction that "a role holding always names a person" as an
*invariant the load may rely on*, and the one ServiceNow sample we have does not show one.

**(e) Inheritance is carried as data, on every row.** `inheritance` (the mode) and
`inherited_from_ci` (the parent pointer) are columns on the anchor table, and the query resolves the
pointer back through `cmdb_ci` to a name. G35 §E1 asserted this from description; it is now evidence.

> **SME, 2026-08-10 — what the two columns actually mean.** `inheritance` takes one of two values:
> **`Inherited`**, in which case the CI comes **from the area product**; or **`Overridden`**, meaning
> it was changed by hand. Not a vendor concept — neither value appears in the public ServiceNow
> documentation, which is consistent with §3.1: the TOM tables are a company scoped app with no
> vendor baseline.
>
> **This is the strongest correction in the document, because DryDocs already models the parent.**
> G35 §E4 reasons that "the inherited-from parent is a CI in another system's hierarchy, not a
> BusinessApplication DryDocs holds," and treats the modelled-node option as blocked on estate data
> we do not have. The parent is the **area product** — and `:AreaProduct` is an existing DryDocs node
> class, gated and signed at K6 (`product-cabinet-attribution`, 2026-07-20), carrying
> `area_product_owner` and `tech_partner`. So E4's blocked option is not blocked: the pointer can be
> a modelled edge to a node that already exists, not a foreign reference stored as a property.
>
> **One boundary, stated so this is not misread as reopening K6.** What inherits is the
> **assignment's CI**, not the role vocabulary. K6 ruled the two role families INDEPENDENT — Product
> Cabinet roles (`product_roles`, scoped to `:Product` / `:AreaProduct`) share no concepts with TOM
> roles (`tom_roles`, on `:BusinessApplication`), and "do not conflate" is explicit in the node
> classification. Nothing here merges them. It says only that a TOM assignment on an application may
> have been *set at* the area product and flowed down, which is a provenance fact about the
> assignment, not a shared concept scheme.

### 1.4 The CI relationship chain — the actual CMDB shape

**SME, 2026-08-10.** The CI relationship panes (the formatter's Downstream / Upstream split) give the
topology the TOM rows hang off:

```
  AREA PRODUCT
      |  [Contains]  /  [Contained by]
  BUSINESS APPLICATION            <-- everything DryDocs maps is off THIS node
      |  [Instantiates]  /  [Instance of]
  DEPLOYMENT MODULE               <-- named app_id:deployment_id; own unique CI id (e.g. CI123456789)
      |
      +-- KB articles link HERE
```

Four things this settles or sharpens:

**(i) "Deployment" and "module" are the same thing.** The CI class is the **Deployment Module**. The
document previously treated `u_seal_deployment_id` and ServiceNow's Application Module as two
separate findings; they are one. That matters for G35, where **G13 Deployment Owner, G14 Deployment
Information Owner and G15 Application Module Owner all plausibly share a single subject** — this CI
class. §G15 asks the gate to "confirm the subject before required-ness," and the candidate subject
now has a name, a key and a place in a hierarchy. Offered as the reading to confirm, not as a fact:
the SME named the CI class, not the three roles' subjects.

**(ii) The label pairs are the `cmdb_rel_type` inverse-pair mechanism, working.** `Instantiates` /
`Instance of` and `Contains` / `Contained by` are exactly the `parent_descriptor` /
`child_descriptor` shape of §3.3, which is the strongest argument yet that ring 1's `cmdb_rel_type`
pull maps mechanically onto `neo4j_label` + `inverse_label`.

**And a trap inside the confirmation:** the public material that mentions this family at all writes
the pair as **`Instantiates::Instantiated by`**, while this instance uses **`Instance of`** as the
inverse. Different label, same relation. That is the concrete reason §3.3 says to *read* the
descriptor columns rather than assume a vocabulary — a crosswalk built from the vendor's label set
would miss this instance's actual value.

> **MEASURED 2026-08-11 — right conclusion, wrong mechanism, and the real mechanism is worse.**
> The instance carries **both** rows, both `sys_scope = global`:
>
> | `name` | `parent_descriptor` | `child_descriptor` | edges |
> |---|---|---|---|
> | `Instantiates::Instantiated by` | Instantiates | Instantiated by | **0** |
> | `Instantiates::Instance of` | Instantiates | Instance of | **23,753** |
>
> So it is not "the vendor says one label, we say another." It is **two distinct relationship types
> that share a forward label and differ only in the inverse**, with the estate using one and leaving
> the other empty.
>
> **The crosswalk consequence is the finding: `parent_descriptor` does not identify a type.** A
> mapping keyed on the forward label alone silently MERGES these two — and merging them would map an
> unused type onto a live one, which is the quiet kind of wrong. Key the crosswalk on `sys_id`, or
> on the descriptor **pair**; never on the forward label. Note also that §3.3's `::` test would never
> have caught this: both names concatenate perfectly.

**(iii) The deployment key question (§6 Q7) is answered.** Each Deployment Module carries **its own
unique CI id**. So the CI `sys_id` is the technical key, and `app_id:deployment_id` is the
human-readable **name** — which incidentally confirms the deployment id is scoped under the
application, since a globally unique id would not need the application in its name. Any capture keys
on the CI id and treats the composite as a name, never the reverse.

**(iv) The Business Application really is the mapping node.** The chain shows the layer above (area
product) and the layer below (deployment module), with DryDocs' `:BusinessApplication` in the middle
— matching the 2026-08-09 direction that everything mapped is off the application. DryDocs already
holds both neighbours in some form: `:AreaProduct` exists (K6); the deployment module does not.

### 1.5 Three reasons this is a report, not an ingestion contract

The item raised the precision question in the abstract. The sample answers it concretely — it
carries defects that are harmless in a report and would be bugs in a contract.

1. **A wrong-alias filter.** The `sug_2` join reads `... AND sug.active = TRUE` — `sug`, the *first*
   group alias, already joined and already filtered. So the second group join does **not** filter on
   its own `active` flag. Transcribed verbatim into a loader, this silently admits inactive
   assignment groups while appearing to exclude them.
2. **Two `AND`ed `LIKE`s on one column.** `lower(resp.name) LIKE '%change%'` and
   `lower(resp.name) LIKE '%approval%'` select role names containing *both* words. That is a
   hand-built reach for one role family, not a definition of the TOM role set.
3. **A `WHERE` clause that references a `SELECT` alias.** Legal on the carrier, not portable. The
   Control-M precedent is instructive: `psgmgr` extraction SQL is Oracle-shaped because the carrier
   is Oracle. Any snow extraction SQL will be Snowflake-shaped for the same reason, and that is a
   property of the carrier, never of ServiceNow.

**One thing in the sample is NOT a defect and must be copied exactly — the identifier convention.**
The query writes **tables unquoted and lowercase** (`<cmdb_schema>.v_cmdb_ci`) while **quoting every
column in lowercase** (`tom_main."number"`, `resp."active"`, `cmdbci."sys_class_name"`). Those two
choices only coexist for one reason: Snowflake folds unquoted identifiers to UPPERCASE, so unquoted
table names match views stored in caps, while quoted lowercase column names mean the columns are
stored lowercase and an unquoted reference would not resolve. The DBeaver navigator corroborates —
`V_CMDB_REL_CI` in caps, `parent` / `u_hash` / `sys_updated_on` in lower beneath it.

> **VIEWS UPPERCASE, COLUMNS QUOTED LOWERCASE.** Any SQL written against this replica follows it or
> does not run.

**Why this is worth a callout rather than a footnote:** the failure is asymmetric. An unquoted column
in a `SELECT` fails LOUDLY — invalid identifier, fixed at the keyboard. The same mistake inside an
`INFORMATION_SCHEMA` predicate fails SILENTLY: comparing `column_name` against an uppercase literal
simply matches nothing, so a probe asking "does this view carry `parent_descriptor`?" answers **no**
for a column that is present. That is a confidently wrong answer, and in this case it would have
triggered §3.3's fallback and sent the crosswalk off splitting `name` on `::` for no reason. Wrap
`INFORMATION_SCHEMA` comparisons in `UPPER()` on both sides — correct whichever way the identifiers
turn out to be stored.

None of the three is a criticism of the SME's query, which did its job. They are the evidence for
why clause (3) of the item exists.

---

## 2. The view inventory, as taxonomy

### 2.1 The naming rule — now with evidence behind it

`config/source-registry.yaml` asserts the rule in a comment. The evidence supports it:

> **`V_` + the ServiceNow table name, uppercased.** Scoped-app tables keep ServiceNow's own
> `x_<scope>_` prefix *inside* the view name.

So `V_CMDB_CI` → `cmdb_ci`, `V_CMDB_REL_CI` → `cmdb_rel_ci`, and the TOM views →
`x_<scope>_cmdb_tom_main` / `x_<scope>_cmdb_tom_roles`. **This is what keeps `origin: snow`
unambiguous while the carrier is Snowflake:** the view name *is* the ServiceNow table name, so a
dataset id names the ServiceNow table and never the view wrapper. No exception was observed.

### 2.2 The schema split

Several `DW_*_DATA_VIEW` schemas sit in one database: a **common/CMDB** schema (which holds
everything the TOM query touches), an **ITSM** schema (the session's default connection), and at
least two others whose names indicate an APM area and a billing area. Every table in §1 resolves in
the common/CMDB schema.

**Open:** whether any table appears in more than one schema, and which is authoritative if so (§6).

### 2.3 What was observed

The inventory below is what was **visible** in two screenshots of a scrolled navigator tree, running
alphabetically from `V_ALM_LICENSE` to `V_RM_RELEASE`. **It is not the complete inventory** — the
tree is cut at both ends. Two views the query *proves* exist, `V_SYS_USER_GROUP` and `V_SYS_CHOICE`,
sit past the visible end and do not appear below. Recorded this way so the gap is legible rather than
mistaken for absence.

| Family | Views observed | Relevance |
|---|---|---|
| **CMDB core** | `cmdb_ci`, `cmdb_model`, `cmdb_model_lifecycle`, `cmdb_ot_entity`, `cmdb_related_entry`, `cmdb_hardware_product_model`, `cmdb_hardware_model_lifecycle`, `cmdb_software_product_model` | the node layer |
| **CI classes** | `cmdb_ci_business_app`, `cmdb_ci_business_capability`, `cmdb_ci_business_process`, `cmdb_ci_service`, `cmdb_ci_service_discovered`, `cmdb_ci_service_technical`, `cmdb_ci_service_group`, `cmdb_ci_query_based_service`, `cmdb_ci_sdlc_component`, `cmdb_ci_server`, `cmdb_ci_pc_hardware`, `cmdb_ci_computer_room`, `cmdb_ci_cloud_service_account`, `cmdb_ci_spkg`, `cmdb_ci_outage` | the class tables of §1.3(b) |
| **Relationship family** | `cmdb_rel_ci`, `cmdb_rel_type`, `cmdb_rel_filter`, `cmdb_rel_group_type`, `cmdb_rel_rollup`, `cmdb_rel_team`, `cmdb_rel_type_rule_definitions`, `cmdb_rel_type_suggest`, `cmdb_rel_user_type` | the edge layer + its governance machinery (§3.3) |
| **Foundation / org** | `core_company`, `core_country`, `business_unit`, `cmn_department`, `cmn_cost_center`, `cmn_location`, `cmn_building` | org taxonomy overlap |
| **On-call / scheduling** | `cmn_rota`, `cmn_rota_member`, `cmn_rota_roster`, `cmn_rota_escalation`, `cmn_schedule`, `cmn_schedule_span`, `cmn_skill` | production-support ownership — worth its own look later |
| **ITSM / knowledge / other** | `alm_license`, `ast_contract`, `contract_sla`, `asmt_assessment_instance`, `cab_definition`, `cab_meeting`, `chg_model`, `discovery_status`, `em_agg_group`, `em_alert_extra_data`, `em_alert_management_rule`, `expert_panel_knowledge`, `interaction`, `kb_knowledge`, `kb_knowledge_base`, `kb_category`, `kb_knowledge_keyword`, `kb_2_sc`, `kb_template_faq`, `kb_template_known_error_article`, `label`, `label_entry`, `label_table`, `life_cycle_stage`, `life_cycle_stage_status`, `m2m_connected_content`, `major_incident_trigger_rule`, `metric_definition`, `metric_instance`, `process_step`, `question_choice`, `rm_epic`, `rm_release` | out of scope for this pull |

Two names stand out against existing DryDocs work and are noted, not proposed:
`cmdb_software_product_model` sits beside the software registry (ADR 0004), and the `cmn_rota*`
family is the on-call roster — the closest thing in the estate to "who is accountable *right now*",
which is a layer-4 context-graph question rather than a taxonomy one.

---

## 3. The precision question — what we should actually pull

### 3.1 Vendor baseline vs. this instance: three classes of difference

The item's premise is that these are stock ServiceNow tables, so the vendor documents the canonical
schema and the vendor doc is the baseline. **That premise holds for the CMDB core and fails at the
center of what G35 needs** — which is the most important correction in this document.

| Class | What it is | Vendor documents it? |
|---|---|---|
| **Stock** | `cmdb_ci`, `cmdb_rel_ci`, `cmdb_rel_type`, `cmdb_ci_*`, `sys_user_group`, `core_company`, the `sys_*` audit columns | **Yes** — canonical, publicly documented |
| **`u_` local columns** | `u_seal_application_id`, `u_seal_deployment_id`, `u_application_state`, `u_status`, `u_external_service`, `u_hash`, `u_discovery_source` | **No** — company columns on stock tables |
| **`x_<scope>_` scoped app** | **the entire TOM model** — `x_<scope>_cmdb_tom_main`, `x_<scope>_cmdb_tom_roles` | **No** — a company-built scoped application |

**The TOM tables are not stock ServiceNow.** They are a company scoped app, so there is no vendor
baseline for them at all — no canonical column list, no documented semantics, no upgrade contract.
Every fact about `tom_main` and `tom_roles` must come from the instance or from the SME. G35 is
reasoning about role classes and cardinality against a surface the vendor has never described, and
that should be stated in the gate rather than assumed away.

**A fourth class, which is neither vendor nor company but *carrier*:** `dwintel_dl_snapshot_dt`,
`dwintel_dl_ld_ts`, `dwintel_dl_snapshot_trim` and `delete_flag` are artifacts of the data-lake
replication. They exist on the replica and nowhere in ServiceNow. `delete_flag` is a **VARCHAR**, not
a boolean — worth knowing before anything filters on it.

### 3.2 A worked caution: a `u_` column existing does not mean it carries data

On `cmdb_rel_ci`, across the 200 sampled rows, `u_hash` is **null on every visible row**,
`percent_outage` is null throughout, and `connection_strength` is the constant `'always'`. Three
columns that a schema-driven pull would ingest as meaningful and that carry, respectively, nothing,
nothing, and one value. This is the concrete form of what T10/T13 exist to prevent: **the schema is
not the contract; the populated schema is.** Any pull scope should be justified against observed
population, not against column existence.

> **THE RULE SURVIVED THE MEASUREMENT; THE ILLUSTRATION DID NOT (2026-08-11).** Run at full-table
> scale: `u_hash` is populated on **2,151,933 of 4,431,668 rows — 48.6%**, not null throughout.
> `percent_outage` is genuinely 0 populated and `connection_strength` genuinely has one distinct
> value (`'always'`, with a single null row), so two of the three examples held.
>
> The u_hash claim was drawn from 200 visible rows in a screenshot — **the same error this section
> exists to warn about, made one level up while making the warning.** Recorded rather than quietly
> corrected, because it is the most useful demonstration in the document that a sample is not a
> population, and because a half-populated column is a worse trap than an empty one: it looks
> meaningful from either end. `u_hash` now needs a *meaning* before anything reads it.

### 3.3 The relationship-family ruling

**Yes — `cmdb_rel_ci` and `cmdb_rel_type` belong in the pull.** A CMDB without its relationship rows
is a node list, not a graph, and this is the one place the replica gives us edges we cannot
reconstruct from anywhere else.

**No — the rest of the `cmdb_rel_*` family does not.** `cmdb_rel_filter`, `cmdb_rel_group_type`,
`cmdb_rel_rollup`, `cmdb_rel_team`, `cmdb_rel_type_rule_definitions`, `cmdb_rel_type_suggest` and
`cmdb_rel_user_type` are ServiceNow's own governance, suggestion and UI machinery for *maintaining*
relationships. They describe how ServiceNow curates its edges; they are not the edges.

**One refinement on the mapping, and it corrects the standing note.** The evidence note on K21 reads
`cmdb_rel_type` as carrying "a forward label plus an inverse label," mapping onto our
`neo4j_label` + `inverse_label`. The vendor baseline is more precise:

- `parent_descriptor` — the relationship from the parent's side ("Depends on")
- `child_descriptor` — the relationship from the child's side ("Used by")
- `name` — **the concatenation of both**, in `Parent descriptor::Child descriptor` form

So the mapping is *even more* mechanical than stated — two columns, two labels — but the
implementation note is the opposite of what the concatenated field invites. **Read the two descriptor
columns; do not split `name` on `::`.** A name containing a literal `::` in either descriptor, or a
descriptor left empty, breaks the split and not the columns.

**Unverified, and it decides the above:** `parent_descriptor` was **not visible** in the screenshot's
column list, which was cut off. `child_descriptor`, `name` and `end_point` were. If the replica view
genuinely omits `parent_descriptor`, that is a replica projection gap worth naming — and the fallback
is to ask for the column, not to start string-splitting.

`end_point` (boolean) has **no public vendor definition** that this analysis could find. It is left
unassigned rather than guessed.

**The vocabulary is small and bounded — SME count, 2026-08-10: 48 standard/global + 6 custom = 54.**
Two consequences, one good and one to check.

*The good one:* this makes the ring-1 crosswalk a **54-row mapping job**, not an open-ended modelling
problem. `cmdb_rel_type` → `relationship_vocabulary` is finite, enumerable and reviewable in one
sitting, which is a materially better position than the CI class hierarchy (§3.6) where the class
count is large and the useful subset unknown. And the *used* subset is smaller still: every sampled
`cmdb_rel_ci` row carried the same single `type` value, so §3.2's rule applies here too — a
`COUNT(*) … GROUP BY type` says which of the 54 are live, and only those need a DryDocs decision.

*The mechanism worth knowing:* the standard-vs-custom split **is a column**. `sys_scope` is present
on this view, and it is what separates global (stock) rows from scoped (company) ones. So §3.1's
vendor-baseline-versus-company-extension boundary — which for `u_` columns and the TOM tables takes
judgment — is **machine-readable on this table**. A crosswalk can label every row's provenance
without anyone deciding case by case.

*The thing to check:* the SME reports 54 is **fewer than an older extract** held from the same
estate. No public source states an out-of-box baseline count, so the number cannot be validated
externally, and three readings survive: **(a)** types were genuinely retired or consolidated over
time; **(b)** the replica view is FILTERED or STALE and does not carry every row — a carrier-fidelity
problem, and the same class of finding as §3.1's "the replica is not a pure mirror"; **(c)** the old
extract came from a different instance or scope, or counted rows this view excludes (deleted,
inactive). See §6 Q9 for the test that separates them, because (b) is much more serious than the
other two: it would mean row counts on the replica are not source truth anywhere, not just here.

### 3.4 Soft deletes are an ingestion contract question

If rows persist in the replica after deletion in ServiceNow, then any pull ignoring `delete_flag`
ingests dead CIs and dead edges as live ones — and edges are the worse half, because a dead edge
makes two live nodes look connected.

**The precedent already exists:** D7's tombstone idiom distinguishes *removed from source* from
*never existed*, via `removed_from_source_at`. This is the same problem arriving from a different
source, and it should reuse that shape rather than invent a second one. What is needed from the SME
is the semantics: what values `delete_flag` takes, whether deleted rows are retained indefinitely or
trimmed, and whether `dwintel_dl_snapshot_trim` interacts with it.

### 3.5 The audit envelope maps cleanly — the first source where it does

`sys_created_by`, `sys_created_on`, `sys_updated_by`, `sys_updated_on` are present on the sampled
view and map onto the four frozen envelope property names without adaptation. A
`config/audit-fields.yaml` entry for a snow dataset would be a **real mapping**, unlike most sources
ruled at `audit-envelope-phase4`.

**The split that matters:** the `sys_*` columns are *authorship* (who changed the record in
ServiceNow). The `dwintel_dl_*` columns are *capture* (when the lake copied it). Only the first is
envelope; `dwintel_dl_snapshot_dt` is excluded under the standing CAPTURE_DATE rule. Conflating them
would record the replication job as the author of every record in the CMDB.

### 3.6 Proposed pull scope — three rings

Offered as a **recommendation for the gate to rule**, not a decision.

> **SUPERSEDED 2026-08-11 by the SME's scope ruling and the measured row counts — see §7.4.** The
> three rings below were drafted before anyone knew the CI table holds **21.6 million rows**. Ring 1
> as written is a 21.6M-node, 4.4M-edge wholesale take, which is precisely what the SME ruled out:
> *"I'm not trying to ingest the company catalog for everything — that is WAY TOO MUCH data."* The
> ring *ordering* survives as a statement of priority; the ring *contents* do not. §7.4 carries the
> replacement, which is an **anchored** pull rather than a wholesale one. Kept here rather than
> deleted because the reasoning below is still the reasoning — it was applied to the wrong estimate
> of size, and a later reader should see that rather than meet a scope with no history.

**Ring 1 — the graph core.** `cmdb_ci`, `cmdb_rel_ci`, `cmdb_rel_type`. Nodes and edges. Defensible
on its own: it is the CMDB *as a graph*, it is stock and vendor-documented, and it stands up without
any TOM decision.

**Ring 2 — the attribution the gates need.** `x_<scope>_cmdb_tom_main`, `x_<scope>_cmdb_tom_roles`,
`sys_user_group`, `cmdb_ci_service_discovered`, `cmdb_ci_business_app`, `core_company`. This is what
G35 §D needs to compare the two rosters at all. It carries the §3.1 caveat: two of the six have no
vendor baseline.

**Ring 3 — deferred, named so the deferral is a decision.** `cmn_*` foundation and org tables,
`cmn_rota*` on-call, `cmdb_ci_outage`, `contract_sla`, `cmdb_software_product_model`, the `kb_*`
family. Each has a plausible DryDocs consumer; none has one *today*.

**What ring 1 does not settle:** which CI classes to *materialize*. Per §1.3(b), pulling `cmdb_ci`
gets every CI of every class in one table. Whether DryDocs wants all of them, or only the classes it
has node semantics for, is a modeling decision and belongs to the gate.

---

## 4. What this evidence changes for the two gates

Findings only. Every row is for the gate to rule.

| Gate clause | What the evidence says | Disposition |
|---|---|---|
| **G35 §E1** — inheritance mode + parent pointer exist | `tom_main.inheritance` and `tom_main.inherited_from_ci`, on every row | **CONFIRMS** — asserted from description, now evidenced |
| **G35 §E4** — "the inherited-from parent is a CI in another system's hierarchy… the modelled-node option is a dependency on estate data DryDocs does not have" | The parent CI is `cmdb_ci`, **in the same replica**, in the same schema as everything else in ring 1 | **CORRECTS THE PREMISE** — the estate data is available. E4's choice between "foreign reference as a property" and "modelled node" is no longer constrained by availability, so it becomes a modeling decision on its merits |
| **G35 §D1/§D3** — the ServiceNow TOM surface is not ingested; a discriminator is proposed | The ServiceNow side is now specified end to end: anchor, role table, holder, subject, inheritance | **ENABLES** — §D3 can be ruled against a real shape |
| **G35 §A8/§F1/§F3** — "the role vocabulary becomes DATA, config-declared or admitted at load" | ServiceNow's side **already is** data: `tom_roles` is a table with `sys_id`, `name`, `active` | **CONFIRMS THE TARGET** — and supplies a worked example. `active` also means role classes *retire*, which no DryDocs surface can currently express |
| **G35 §B6** — "a role holding always names a person… an Attribution with no HAS_AGENT is a defect" | As sampled, `tom_main.group` names a **group**; no person join appears | **TENSION** — see §6 Q1 before this becomes an invariant. If the ServiceNow surface attributes to groups, an invariant asserted from the SEAL surface does not hold across both |
| **`seal-tom-attribution-reshape` mapping #3** — `(:Attribution)-[:HAS_AGENT]->(:Employee)` | Same finding | **SCOPE** — `prov:agent` admits an Organization as readily as a Person, so the PROV shape survives; the *target node class* is what would need to widen |
| **C10 gate-bound candidate #1** — the deployed-instance concept, deferred "until an environment-level use case lands" | `u_seal_deployment_id` sits beside `u_seal_application_id` on the Application Service row; SME **confirmed 1:N** 2026-08-09, identifier reading as `app_id(seal_id):deployment_id` — **but also that everything mapped is off the APPLICATION** | **NARROWED, NOT RE-HOMED** — the candidate is now about capturing an identifier we discard, not about moving the attribution subject. Attributing to `:BusinessApplication` is confirmed correct. Q7 (key scope) still gates any capture |
| **G35 §G15** — Application Module Owner: "a module owner plausibly owns a PART of an application, and DryDocs has no module grain to attribute to. Confirm the subject before required-ness" | SME 2026-08-10: the subject is the **Deployment Module** CI — own unique id, named `app_id:deployment_id`, `[Instance of]` the application. What is defaulted is the module reference on Changes/Incidents/KB, not the CI | **NAMES THE SUBJECT** — §G15's missing grain exists and is identified. Supersedes this document's first reading, which wrongly concluded no grain was needed |
| **G35 §G13/§G14/§G15** — three role classes the SME's list added, with no concept, no crosswalk and no prior capture | All three plausibly share ONE subject: the Deployment Module | **CANDIDATE UNIFICATION** — offered for the gate to confirm. If it holds, three unruled register lines resolve together against one grain rather than one at a time |
| **G35 §E4** — "the inherited-from parent is a CI in another system's hierarchy… the modelled-node option is a dependency on estate data DryDocs does not have" | SME 2026-08-10: `Inherited` means the CI came **from the area product**; `Overridden` means set by hand. `:AreaProduct` is an existing, K6-signed DryDocs node class | **THE BLOCKED OPTION IS NOT BLOCKED** — the parent is already modelled here, so E4 can choose a real edge rather than a property. Supersedes the weaker "available in the replica" reading above |
| **K6 `product-cabinet-attribution`** — the two role families are INDEPENDENT, "do not conflate" | Inheritance moves the assignment's CI, not the role vocabulary | **UNTOUCHED** — recorded explicitly so the E4 finding is not misread as reopening K6 |

**The last row is the finding to carry forward.** DryDocs models `:BusinessApplication` and attributes
TOM roles to it. The evidence shows the company's own operating model attributing accountability at
the **Application Service / deployment** grain, one layer below. That is a grain question, and grain
questions in this repo have a history — K1/K2 (job vs. folder) and the 2026-07-22 correction that
moved SEAL attribution from job level to the folder→batch `:Port`. This is the same class of problem
on a different axis, and it is cheaper to rule now than to re-key attributions later.

---

## 5. Draft dataset rows — and why they are not in the registry

The item permits a draft row "if warranted." **Judgment: warranted as a drafted proposal, not as a
registry edit** — `config/source-registry.yaml` is an enforcement surface, and the pull scope is
explicitly a gate decision. Writing nine `confirmed: false` rows into the registry would put a
proposal where the enforcement matrix reads it, and the gate would then have to strike rows rather
than approve a recommendation. The ring-1 block is drafted here, ready to paste once ruled.

```yaml
# PROPOSED — not in config/source-registry.yaml. Ring 1 only (see §3.6).
# Grammar: snow@[db].[schema].<servicenow_table> — origin snow, carrier snowflake,
# exactly as controlm@[db].psgmgr.<table> is origin controlm, carrier psgmgr.
- id: "snow@[db].[schema].cmdb_ci"
  system: snowflake          # carrier
  origin: snow               # ServiceNow — see the disambiguation on both system entries
  artifact: cmdb_ci
  artifact_kind: table       # a ServiceNow TABLE, exposed by the replica as a V_-prefixed view
  asset_type: dcat:Dataset
  confirmed: false           # no gate has ruled the pull scope
  notes: >
    The CI base table. Table-per-class inheritance: a CI has one row here AND one in each
    class table it extends, sharing sys_id — so this is not disjoint from cmdb_ci_business_app
    or cmdb_ci_service_discovered. sys_class_name is the discriminator. K21 §1.3(b).

- id: "snow@[db].[schema].cmdb_rel_ci"
  system: snowflake
  origin: snow
  artifact: cmdb_rel_ci
  artifact_kind: table
  asset_type: dcat:Dataset
  confirmed: false
  notes: >
    The CI edge list: parent / child / type, all sys_id. Without it the CMDB pull is a node
    list. Carries carrier columns (dwintel_dl_*, delete_flag) that are NOT vendor schema —
    the soft-delete rule (K21 §3.4) must be ruled before this loads.

- id: "snow@[db].[schema].cmdb_rel_type"
  system: snowflake
  origin: snow
  artifact: cmdb_rel_type
  artifact_kind: table
  asset_type: dcat:Dataset
  confirmed: false
  notes: >
    The edge vocabulary. parent_descriptor + child_descriptor are the forward and inverse
    labels — the same shape as relationship_vocabulary's neo4j_label + inverse_label. Read the
    two columns; do NOT split `name` on '::' (K21 §3.3). end_point has no public vendor
    definition and is left unassigned.
```

`taxonomy_category`, `authority`, `feeds_taxonomy`, `adapter` and `locator` are deliberately omitted:
each encodes a decision (which taxonomy this feeds, whether ServiceNow or the lake is authoritative,
which adapter reads Snowflake) that no one has made.

---

## 6. What this evidence cannot settle

Ordered by how much they block. **Q3 and Q7 were answered by the SME on 2026-08-09/10 and are kept
struck through rather than deleted** — the alternatives were live and a later reader should see they
were ruled out rather than never considered. Q8 is the sharpest of the remainder: it reconciles the
source's grain with the operating model's, and one `GROUP BY sys_class_name` settles it.

> **The probes are written.** Every question below that a query can settle has one in
> [`drydocs/loaders/sql/adhoc/servicenow_relationship_open_questions.sql`](../../drydocs/loaders/sql/adhoc/servicenow_relationship_open_questions.sql)
> — Snowflake dialect (the carrier), read-only, placeholders for db/schema/scope, annotate-in-place
> on the `preflight_open_questions.sql` precedent. Q9 is §A and runs first because it gates the rest.
> Q1 → §E1, Q4 → §B1, Q5 → §C3, Q6 → §B8, Q8 → §D1, Q10 → §E6, §2.2 → §E5, §3.2 → §C1, §3.3 → §B3–B7.
> The script is authored here and **run on the laptop** — the replica connection lives there, and the
> result rows are Internal, so only conclusions come back.

1. **Does `tom_main` carry a user/person column as well as `group`?** The sample joins only
   `sys_user_group`. This decides whether G35 §B6's "always names a person" is an invariant or a
   SEAL-side-only fact, and whether `HAS_AGENT` must admit an Organization. **Blocks §B6.**
2. **Is the TOM scoped app the same surface as SEAL's Application Contacts, or the second surface?**
   G35 §D1 compares two rosters that disagree. If the TOM scoped app *is* the ServiceNow side of that
   comparison, §D3's discriminator has its two values. **Blocks §D3.**
3. ~~**What is the accountability grain — Application Service, or Business Application?**~~
   **ANSWERED 2026-08-09 by the SME: the APPLICATION.** Everything mapped is off the application;
   deployments and modules exist in the source but are not the mapping subject. So DryDocs
   attributing to `:BusinessApplication` is correct as-is, `seal-tom-attribution-reshape`'s
   attribution subject does not move, and the C10 candidate narrows from "re-home attribution" to
   "capture an identifier we discard." Kept struck-through rather than deleted because the question
   was the reason for the finding, and a later reader meeting only the answer would not know the
   alternative was considered and ruled out. **Residual CLOSED 2026-08-10:** the inheritance columns
   are explained — `Inherited` means the CI came from the area product, `Overridden` means set by
   hand. It is inheritance down the CI chain (area product → application), not between application
   and deployment. See §1.3(e).
4. **Does the replica's `cmdb_rel_type` view carry `parent_descriptor`?** Not visible; decides §3.3.
5. **What does `delete_flag` mean operationally** — values, retention, interaction with
   `dwintel_dl_snapshot_trim`? Decides §3.4.
6. **What is `end_point` on `cmdb_rel_type`?** No public definition found. Instance or SME only.
7. ~~**Is `u_seal_deployment_id` globally unique, or unique only within its application?**~~
   **ANSWERED 2026-08-10:** each Deployment Module carries **its own unique CI id**, so the CI
   `sys_id` is the key and `app_id:deployment_id` is the human-readable name. The composite name is
   itself the evidence that the deployment id is scoped under the application — a globally unique id
   would not need the application in its name. **Capture rule:** key on the CI id, treat the
   composite as a name, never the reverse.

8. **Is the TOM row's subject a Business Application CI or a Deployment Module CI?** *(NEW, and it is
   the one that reconciles the two SME statements.)* `tom_main.parent_id` resolves to `cmdb_ci`, and
   the query joins **both** `cmdb_ci_business_app` and `cmdb_ci_service_discovered` on that same
   `sys_id` — defensively, so only the CI's actual class returns non-null. The sample does not show
   which one hit, because `sys_class_name` was selected but its values are not in evidence.
   This matters: the SEAL ids come off `cmdb_ci_service_discovered` (§1.3(c)), which would put the
   TOM assignment at deployment grain in the **source**, while practice maps off the **application**.
   Both can be true — the source may record finer than the operating model uses it — but which is
   which decides what a loader reads. **One query settles it:** count TOM rows grouped by
   `cmdb_ci.sys_class_name`.
9. **Is the replica a COMPLETE copy, or a filtered/stale projection?** *(NEW — raised by the
   `cmdb_rel_type` count coming in below an older extract, §3.3, and it outranks everything else
   here.)* Every finding in this document assumes the views carry all the rows. If they do not, the
   assumption is wrong everywhere at once, and no amount of care about column meanings compensates.
   **The decisive test is cheap and needs no comparison to the old extract** — look for edges whose
   type does not resolve:

   ```sql
   -- any row > 0 means the type view is missing rows that LIVE EDGES depend on
   SELECT COUNT(*) FROM v_cmdb_rel_ci r
     LEFT JOIN v_cmdb_rel_type t ON r.type = t.sys_id
    WHERE t.sys_id IS NULL;
   ```

   A dangling foreign key inside the replica proves incompleteness from the inside, with no external
   baseline needed. If it returns zero, the type view is self-consistent with the edge view and
   reading (a) or (c) is the likely explanation. Two cheap follow-ups either way: group
   `v_cmdb_rel_type` by `delete_flag` (does the view carry soft-deleted rows, or hide them — §3.4),
   and check the maximum `sys_created_on` / `dwintel_dl_ld_ts` to distinguish *filtered* from
   *stale*. **This should be settled before any pull scope is ruled**, since it decides whether the
   replica can be a source of record at all or only a convenience copy.
10. **Are the KB articles linked to the Deployment Module worth pulling?** The SME flagged them as
   "more meaningful," and for a production-support knowledge graph that is squarely on-mission — a
   documented fix attached to the deployment that has the incident is exactly what DryDocs exists to
   answer. It would promote the `kb_*` family from ring 3 to a real candidate. **What to check
   first:** whether the KB→module link is a genuine assertion or another defaulted reference (§1.3's
   correction) — the same defect that makes change counts per module untrustworthy would make KB
   attachment untrustworthy in exactly the same way.

Two smaller ones, recorded so they are not rediscovered: whether any table appears in more than one
`DW_*_DATA_VIEW` schema and which would be authoritative (§2.2), and whether `connection_strength` /
`percent_outage` are populated anywhere beyond the constant-and-null sample (§3.2) — the CMDB models
impact weight on the edge, and DryDocs has no equivalent, so it is worth knowing whether there is
anything there before deciding we do not need one.

---

## 7. Measured — the 2026-08-11 probe run

The probes in
[`servicenow_relationship_open_questions.sql`](../../drydocs/loaders/sql/adhoc/servicenow_relationship_open_questions.sql)
were run against the replica. Counts and conclusions only; no result rows, per §0. Each block is
annotated `[ANSWERED 2026-08-11]` in the script itself.

**Read the counts as approximate.** Total-edge counts came back as 4,431,314 / 4,431,328 / 4,431,668
across three runs minutes apart — the replica reloads during a session. Never compare two counts
taken at different moments as though they were stable.

### 7.1 The estate, by size — the number that changes the plan

| View | Rows |
|---|---|
| `cmdb_ci` (all CI classes) | **21,601,633** |
| `cmdb_rel_ci` (all edges) | **4,431,328** |
| `cmdb_ci_service_discovered` (deployment modules) | 24,169 |
| `cmdb_ci_business_app` | **14,683** |
| `cmdb_rel_type` | 54 |

**Business applications are 0.07% of the CI table** — and **ours are ~1.4% of those** (§7.4: roughly
200 applications; the 14,683 span multiple LOBs). So the applications DryDocs models are on the order
of **one in a hundred thousand CI rows**. The class distribution explains the rest: the top classes
are all cloud and infrastructure — database snapshots, deployment targets, OS images, storage
volumes, endpoint blocks, ECS tasks — each in the hundreds of thousands. The estate is overwhelmingly
technical inventory that DryDocs has no use for.

**Zero CIs appear in both class tables.** A CI is in exactly one, so the §1.3(b) multiplication trap
is real but bounded — and no CI is both a business application and an application service, which
closes a reading §1.3(c) left open.

### 7.2 Replica completeness (Q9) — faithful copy, drifting source

| Probe | Result |
|---|---|
| Edges whose type is missing | 843 (0.019%) |
| Edges whose parent CI is missing | 970 (0.02%) |
| Edges whose child CI is missing | 9,093 (0.2%) |

**Not a filtered projection.** A filtered view does not come out 99.98% complete. These proportions
are the signature of **source-side orphans** — deleted CIs leaving `cmdb_rel_ci` rows behind, which
ServiceNow is independently known for. The replica is faithful; the CMDB carries referential drift.

**One genuine staleness, and it is the type view.** `cmdb_rel_type` was last *authored* 2022-05-26
(a stable vocabulary, unsurprising) but last *carrier-loaded* 2026-04-15 — **four months behind** the
edge view's daily load. The old authorship date is fine; the old load date means the carrier
refreshes that view on a different cadence, and it is the thing to watch if a type is ever added.

**The consequence holds whatever the cause:** a loader must handle an unresolvable parent, child or
type — skip or tombstone, never assume resolution.

### 7.3 The vocabulary, resolved

- **54 types: 48 standard (`sys_scope = global`) + 6 custom.** Confirmed against the data.
- **`name` = `parent_descriptor` || `'::'` || `child_descriptor` holds for all 54.** No descriptor
  contains `::`, none is empty. The trap has not fired here — the rule stands because nothing
  *guarantees* the concatenation, not because it is currently broken.
- **Only 21 of 54 carry any edges.** The crosswalk's real input is 21 rows, not 54.
- **All six custom types carry zero edges.** The company defined six and uses none — so the
  standard/custom split, though machine-readable off `sys_scope` (§3.3), turns out to be moot.
- **`end_point` is false on all 54.** Single-valued, so it discriminates nothing. Q6 closes not as
  "we don't know what it means" but as "it carries no information here."
- **`delete_flag` takes only `N` or NULL — there is no `Y` anywhere.** No soft-deleted row is visible
  in the replica at all, which makes §3.4's worry *not currently real* and C5's guessed predicate
  moot. It is replaced by a smaller question: NULL is a second state on 0.6% of CIs and 5.9% of
  edges, and nobody knows what it means. Rule NULL before relying on the flag; do not assume `N`
  means live.

### 7.4 The pull scope, rewritten — anchored, not wholesale

**SME ruling, 2026-08-11:** *not ingesting the company catalog — that is way too much data. Business
applications and the product catalog in full are small. Control-M is the largest pull for now. Only
a very small percentage of the technical hardware listed is in use.*

That supersedes §3.6, which took `cmdb_ci` and `cmdb_rel_ci` whole and would have pulled 21.6M nodes
and 4.4M edges. The replacement inverts the direction of travel: **seed from what we care about and
traverse out**, rather than take the tables and filter down.

**AND THE SEED IS SMALLER THAN "ALL BUSINESS APPLICATIONS" — SME, 2026-08-11:** *there are roughly
**200 applications** our teams support; the full list is for **multiple LOBs**.*

That is the single most scope-reducing fact in this document, and it also changes the seed's
*mechanism*. The 14,683 business applications are the whole company across every line of business.
Ours are **~1.4% of them**, and DryDocs **already knows which ones** — they are the SEAL applications
it holds today. So the seed is not a filter applied to ServiceNow's catalog; it is a **join from our
side**, on `u_seal_application_id`. That reframes the whole pull: this is **enrichment of an
application list we already have**, not ingestion of a CMDB.

| | Take | Rows | Why |
|---|---|---|---|
| **Vocabulary** | `cmdb_rel_type` **in full** | 54 | Trivial, and needed to read any edge. Take all 54 even though 21 are live — the unused ones cost nothing and their absence would look like a gap |
| **Seed** | `cmdb_ci_business_app` **for OUR SEAL applications only** | **~200** | Joined on `u_seal_application_id` from the app list DryDocs already holds. NOT all 14,683 — those span multiple LOBs and are not ours to model |
| **Seed** | the area products above those applications | small | The layer above in the §1.4 chain. Reached by traversal from the seed, not taken as a table |
| **One hop out** | `cmdb_ci_service_discovered` for seeded apps | ~200 × deployments each | The deployment modules `[Instance of]` a seeded application (§1.3(c): 1:N) |
| **Edges** | `cmdb_rel_ci` **restricted to both endpoints in the seeded set** | small | Never the whole edge table |
| **Attribution** | the TOM tables + `sys_user_group` + `core_company`, for seeded apps | — | What G35 needs; unchanged from §3.6 ring 2 except that it too is seed-scoped |
| **NOT taken** | `cmdb_ci` as a table; the other ~14,480 business applications; the cloud/infrastructure classes; the `kb_*`, `cmn_*`, rota and SLA families | 21.6M | Out by SME ruling. Individual classes can be added later against a named use case |

**The scope has now collapsed by roughly four orders of magnitude** from §3.6's ring 1 — 21.6M CI
rows to a low-thousands node set — and each step was a fact rather than a preference: the CI table's
size, then "everything mapped is off the application", then "~200 applications, multiple LOBs."

**Two consequences worth stating before anyone builds.** First, **the LOB boundary is a real
publishing and modelling boundary, not just a volume filter** — the other ~14,480 applications belong
to teams DryDocs does not support, and pulling them would be ingesting other people's ownership data
with no use case. Second, **a join-from-our-side seed inverts the failure mode**: instead of "did we
filter enough?", the question becomes "which of our ~200 are MISSING from the CMDB?" — and that
question is worth answering, because an application we support that has no CI is a finding in itself.

**Two things this shape gets right that the ring model did not.** It is bounded by *what we model*
rather than by *what the source holds*, so it does not grow when the estate does — the cloud classes
that dominate the CI table will keep growing and none of it reaches us. And it makes the edge pull a
consequence of the node pull rather than a separate decision, which is the only way to keep 4.4M
edges from arriving by default.

**What it still does not settle:** the traversal depth. One hop from the seeded applications is
defensible and cheap; two hops starts pulling infrastructure, which is exactly what is ruled out. If
a support question ever needs "which server does this run on", that is a use case for adding a class
by name, not a reason to widen the traversal.

**Control-M stays where it is.** It is the largest pull and it comes from the Oracle `psgmgr`
replica, not from here — nothing in this document changes that.

---

## 8. The API evidence (2026-08-11) — and why it rewrites the query plan

Before the SQL probes ran, the SME queried the **ServiceNow API** through an internal tool, against
one SEAL application and one of its deployments. It answers more than the SQL did, because it
followed references the SQL never traversed. Mechanism only — no names, SIDs, emails, group names,
SEAL ids, CI ids or GUIDs are reproduced here.

### 8.1 The five structural facts

**(a) `tom_roles` is a GLOBAL MASTER CATALOG, not a per-application list.** It holds **83 role-type
definitions** (exported 2026-08-11; the SME's initial estimate of 100+ is corrected in §10.7),
numbered `TR#######`, with **no application or SEAL column**. Applications instantiate
these types; the catalog itself is estate-wide. Every count this project has argued over — 7, 9, 10,
13, 14 — describes what the SEAL contact extract *surfaces*, not what the register *contains*.

**(b) Every role type carries two classifying attributes DryDocs has no equivalent for.**

| Attribute | Values seen |
|---|---|
| **Scope** | `Individual` or `Group` |
| **Type** | `Accountable`, `Operational`, `Approval`, `Assignment`, other |

**(c) `tom_main` has TWO holder columns, not one — `group` and `individual`.** Which one is populated
is determined by the role type's **Scope**. This resolves §1.3(d): the SME's report query joined only
`sys_user_group`, so the surface *looked* group-only; the table carries both.

**(d) Inheritance runs application to deployment, and it is nearly total.** On the sampled deployment,
**every** TOM assignment is `Inherited` from the parent business-application CI **except two** —
`Deployment Owner` and `Deployment Information Owner` — which are set **Direct** on the deployment.

**(e) The application-to-deployment link is a REFERENCE COLUMN, not an edge.**
`cmdb_ci_service_discovered.u_business_application` points at the business-application CI directly.
The deployment also carries `correlation_id` in `app_id:deployment_id` form, alongside
`u_seal_application_id` and `u_seal_deployment_id` — and a `CI` id distinct from `sys_id`. It further
carries `discovery_source` naming SEAL deployments, a `subcategory` of Deployment, and a
`used_for` field valued Production.

### 8.2 What this does to the query plan

**The edge table drops out of the core pull entirely.** §7.4 had `cmdb_rel_ci` restricted to seeded
endpoints. But the two hops that matter are both **reference columns**: application to deployment via
`u_business_application`, and CI to TOM assignment via `tom_main.parent_id`. Neither needs
`cmdb_rel_ci`. That removes a 4.4M-row table, its 843 dangling type refs and its 9,093 dangling child
refs from the critical path. `cmdb_rel_ci` becomes optional — wanted only for the area-product hop
and for infrastructure relationships, neither of which is in the first pull.

**The plan is now four joins from a list we already hold:**

```
our ~200 SEAL app ids  (DryDocs already has these)
  -> cmdb_ci_business_app          on u_seal_application_id
  -> cmdb_ci_service_discovered    on u_business_application        (1:N, the deployments)
  -> x_<scope>_cmdb_tom_main       on parent_id = CI sys_id         (the assignments)
  -> x_<scope>_cmdb_tom_roles      on role = sys_id                 (~100 rows, take in full)
       then EITHER sys_user_group  on group       (Scope = Group)
       OR         sys_user         on individual  (Scope = Individual)
```

**Four consequences for how it must be written.**

1. **Read BOTH holder columns, switched on the role's Scope.** A query that joins only `group`
   silently drops every Individual-scoped accountability — which is most of the ones DryDocs
   currently models. Joining only `individual` drops the entire operational-support layer. This is
   the single most likely way to get the pull wrong now that the edge table is gone.
2. **Inheritance must be handled, or accountability double-counts.** Because assignments inherit
   application to deployment, pulling TOM at *both* levels returns the same accountability twice. The
   plan must either read at application level and treat deployments as inheriting, or read at
   deployment level and dedupe on the `Inherited` mode. Do not pull both and union.
3. **Take `tom_roles` in full.** ~100 rows is a dimension table, and its Scope/Type columns are what
   makes clause 1 executable.
4. **`used_for` is an environment filter available at the deployment grain.** If only Production
   matters, it cuts the deployment set before anything else joins — and it is the concrete form of
   the environment concept C10's candidate #1 was parked on.

### 8.3 What it does to G35 — five clauses move

| Clause | What the API evidence shows |
|---|---|
| **§A enumeration** | The catalog holds **100+ role types**, so the "7 vs 9 vs 13" dispute is about what the SEAL extract surfaces, not about the register. The gate should say which it is ruling |
| **§B6** — "a role holding always names a person" | **Answered: no.** Scope is a declared attribute of the role type, `Individual` or `Group`. Both are legitimate, and the model must admit an Organization-typed agent (§B6c already noted `prov:agent` allows it) |
| **§A2 / §G5** — `technology_risk_controls`, "a concept with no source" | It is a **live role type with a live holder** in ServiceNow. The concept has a source after all; what it lacks is a crosswalk branch in the SEAL contact loader |
| **§A5 / §B1b** — the three Operate Manager classes | **Confirmed on live data**: all three appear as distinct assignments, held by the same person. The SME's 2026-08-05 ruling now has instance evidence behind it |
| **§G13 / §G14** — Deployment Owner, Deployment Information Owner | **These two are DIRECT on the deployment** while everything else inherits. That resolves §G0e's fork toward genuine deployment-grain attribution for these two specifically — not application-level roles that merely name a deployment concern |

**And one whole family DryDocs has no home for.** The group-scoped roles on a single deployment
include service ownership, change ownership, several distinct change-approval teams, an eCAB approval
team, five distinct incident-resolver tiers, and four problem-owner variants. That is the
**production-support ownership layer** — precisely what this project exists to answer — and none of
it is in the `tom_roles` scheme's seven concepts. Group names follow a parseable convention
(`<LOB>_<domain>_<function>_<app>: <TOM-function>`), and each group resolves to real members, so the
path from an application to the people who actually carry its incidents is available today.

**Recorded as scope, not as a proposal:** it is a large addition, it is exactly on-mission, and it
belongs to a gate rather than to this document.

### 8.4 Two things to reconcile before building

1. ~~**Inheritance was described at two different rungs.**~~ **CLOSED 2026-08-11 — see §8.5.** It is
   ONE mechanism ("copy from the nearest ancestor holding the role") applied repeatedly up an N-level
   CI parent chain, not two relations. G35 §E5 states only the area-product rung and should state the
   walk.
2. **A count field disagrees with the row count.** The CI's `u_operational_responsibilities_count`
   read 16 while the tool found 28 active assignments. Sixteen is exactly the number of *group-scoped*
   assignments, so the field most likely counts operational responsibilities only — but that is an
   inference, and a count field that means something narrower than its name is worth confirming
   before anything trusts it.

### 8.5 Inheritance, fully resolved (SME, 2026-08-11) — and §8.4's first item closes

**`Inheritance` is COMPUTED, not typed.** It is not a field anyone fills in. The TOM engine walks the
**CI parent chain upward** and copies each role's assignment down to child CIs, and every row records
where it came from through two lineage references:

| Field | Points at |
|---|---|
| `inherited_from_ci` | the ancestor **CI** that owns the original assignment |
| `inherited_from` | the ancestor's specific **TOM row** that was copied |

**Three states, and the blank one is real:**

| Value | Meaning | How to spot it |
|---|---|---|
| *(blank)* = **Direct** | Origin row — defined on this CI itself, or fed in by a feed (a `u_source` value names it, e.g. the SEAL deployment-contacts feed) | both lineage fields **empty** |
| **Inherited** | Copied down from the *nearest ancestor that has the role* | both lineage fields **populated** |
| **Overridden** | Was inherited, then **locally edited** — a different group or person — breaking the link to the parent | recorded on the CI where the edit was made |

**The rule that makes it non-trivial: a child always inherits the ancestor's CURRENT value — even
when that ancestor value is itself an Override.** Overrides therefore propagate downward, and the
effective holder at a deployment can differ from the definition at the top of the chain, with the
lineage fields recording exactly where the divergence was introduced.

**The chain is N-level, not two-level.** The sampled hierarchy runs an infrastructure/service CI at
the top, then the business application, then the deployment — each linked by `parent` / `u_parent`,
with the deployment additionally carrying `u_business_application`. Observed behaviours on one
deployment:

- most roles inherit from the **business application** one rung up;
- **Service Owner Team** inherits from the CI **above** the application, where it is Direct — it
  originates two rungs up and passes straight through;
- **Change Owner Team** inherits from an application-level row that is itself **Overridden**, so the
  deployment carries an overridden value rolled down;
- **Deployment Owner** and **Deployment Information Owner** are **Direct** on the deployment, fed
  from SEAL rather than inherited.

**This closes §8.4 item 1.** The two rungs described separately — area product → application, and
application → deployment — are **not two relations.** They are one mechanism, "copy from the nearest
ancestor holding the role", applied repeatedly up whatever chain exists. G35 §E5 states only the
area-product rung and should state the walk.

#### What it changes for the load

**1. Only two of the three states are assertions.** `Direct` and `Overridden` rows are *authored* —
somebody decided them. `Inherited` rows are *derived copies* that carry pointers to their origin.
So the honest load pulls the authored rows and treats inheritance as what it is: a computation. That
is both a large volume reduction and the semantically correct choice — storing a derived fact as if
it were asserted is how a graph starts disagreeing with its source.

**The caveat that decides the design:** reconstructing an inherited holder requires the ancestor
chain, and ancestors sit **above** our ~200 applications — including CIs owned by teams we do not
support (§7.4). So either the pull widens to include ancestor CIs for their TOM rows only, or
inherited rows are kept as materialized copies flagged derived. That is a real gate decision, and it
is the first place the ~200-application boundary and the inheritance model actually conflict.

**2. The PROV shape is now obvious.** An inherited assignment `prov:wasDerivedFrom` the ancestor
assignment. G35 §E3's option (i) — an `assertion_mode` property plus an inherited-from pointer — is
the right shape and needs **two** pointers, not one: the ancestor CI *and* the ancestor row.

**3. `u_source` may already be the §D3 discriminator.** G35 §D3 proposes adding a surface
discriminator so a roster disagreement is readable. Direct rows carry `u_source` naming the feed that
produced them. If SEAL-fed and hand-authored rows are distinguishable there, the ServiceNow side
already carries the fact §D3 wants to invent — and the gate should check before designing one.

**4. Part of §D2's roster puzzle is answered by structure rather than by a discriminator.** §D2 asks
how an operator can tell whether "five Operate Managers" is one roster with five people or two
rosters disagreeing. Where the difference is an inheritance artifact, the lineage fields say so
outright: the holder differs because an override was made at a named CI. That does not replace §D3,
but it means some disagreements have an explanation already sitting in the data.

#### A correction to this repo's own gate prompt

G35 §E1 lists three inheritance values — `Inherited` / `Overridden` / *(empty)*. On 2026-08-10 this
document's §E1b challenged the third, on the grounds that the evidence did not corroborate it, and
asked the walk to "confirm or drop it."

**The blank value is real, and it is the most important of the three** — blank *is* Direct, the
origin state that every inherited copy ultimately points back to. §E1 was right as drafted and §E1b
was wrong to question it. The gate prompt has been corrected so the walk is not asked to consider
dropping a legitimate state.

---

## 9. The company-side ServiceNow model the producer cannot see

**Recorded 2026-08-11 at the G35 walk, because this document is where a producer-side gate looks for
what ServiceNow means — and it was missing the fact that half the question is already answered.**

The company has **built and signed** a ServiceNow support model. Gate `snow-hpsm-queue-to-group`,
signed 2026-07-15:

| Layer | Artifact |
|---|---|
| Source data | a hand-verified Internal YAML crosswalk, keyed on SEAL id — gitignored, per-machine |
| Adapter | `snow_support_crosswalk.py` — flattens to one row per (app, tier, platform) |
| Graph write | `snow_support_crosswalk.cypher` — MERGEs `:ServiceNowGroup` / `:HpsmQueue`, links to `:BusinessApplication` |
| CLI | `load-snow-support-crosswalk` |

The shape it writes, with `:BusinessApplication.seal_id` as the pivot:

```
(:BusinessApplication {seal_id})-[:HAS_SUPPORT_QUEUE]->(:HpsmQueue)-[:RESOLVED_BY]->(:ServiceNowGroup)
```

`:ServiceNowGroup` carries the technician list, the group id, the tier and a certification status.
The crosswalk joins three things per application: the PAT side (product, tech partner and product
owner SIDs), the SEAL id as join key, and the ServiceNow side (group plus L2/L3 technicians), with
an HPSM queue as the routing anchor.

**None of this exists producer-side, and none of it ever has** — verified against the working tree
and against `git log --all` on every path. It is company-originated work, not a producer artifact
awaiting a port.

### 9.1 Why it is recorded here

Because a producer-side gate was about to invent a competing model. G35's walk on 2026-08-11 reached
the question "should the group-scoped TOM roles enter the model?" with no way to know that
`(:BusinessApplication)-[:HAS_SUPPORT_QUEUE]->(:HpsmQueue)-[:RESOLVED_BY]->(:ServiceNowGroup)`
already exists and is signed. It was stopped by the SME producing the screenshots, not by anything
in this repo.

**The port doctrine has no slot for this.** Guardrail 6 rules the company adopting a *producer*-signed
gate — Tier A when the company holds no position, Tier B when it does. There is no provision for the
reverse. And "company-only" elsewhere in the port-prompt means paths and config rows, which are
inert; a **modelling position is not inert**, because the producer can independently invent a
competing one against the same source. Filed as `RELAY-6` so every future port re-states it.

### 9.2 The two models are the same fact from different sources

This is the part with consequences beyond bookkeeping.

| | Company crosswalk | ServiceNow TOM (§8) |
|---|---|---|
| Origin | hand-verified YAML, per-machine, gitignored | the source system, via replica or API |
| Keyed on | SEAL id | CI, resolved to SEAL via `u_seal_application_id` |
| Groups | `snow_group` + technicians CSV, per tier | `sys_user_group`, per group-scoped role type |
| Tiers | explicit `l2` / `l3` | the incident-resolver role tiers |
| Trust | `verified`, `cert_status`, `cert_next_date` | none — it is whatever the source says |

The `l2`/`l3` tiers and TOM's incident-resolver tiers are **the same fact recorded twice**. That is
§D1's roster-disagreement problem again — for groups rather than people — and it is why G35's §D4
ruling had to place them in an order: **hand-verified > ServiceNow TOM > SEAL extract.**

**The upgrade path is real and is not this gate's to take.** A hand-verified, per-machine, gitignored
YAML is exactly the kind of artifact a sourced feed should eventually replace. But `verified` and
`cert_status` exist for a reason — somebody checked — and replacing human verification with a raw
source feed trades accuracy for currency. That decision belongs to `snow-hpsm-queue-to-group`, and
the producer should not pre-empt it. §D4's order deliberately lets both coexist so that the choice
stays open.

### 9.3 What G35 does about it

**Nothing structural, and that is the ruling.** G35 admits the group-scoped role *types* into the
vocabulary with `Scope: Group`, so the register is complete and honest, and **mints no
group→application graph shape**. The shape stays owned by the signed gate. A second shape for the
same fact would collide at the next port, and the collision would be the producer's fault.

---

## 10. The group naming convention — and why the label is not the identity

**SME, 2026-08-11.** ServiceNow ships four default technician groups; the team **reuses one** of
them. Whether an application has SRE cover is **not asserted** — it is **derived from the team
naming convention**, whose third segment is a function class:

```
<LOB>_<domain>_<function>[_<app>]        and, where the group serves a TOM role:
<LOB>_<domain>_<function>_<app>: <TOM-function>

function segment:
  ASUP   support
  SENG   development / software engineering
  SSRE   support SRE   — serves 1:many applications, roughly 20 to 60
```

So the group name carries the LOB, the domain, **the team's function class**, the application or
application-group it serves, and — after the colon — the TOM function it performs (Technician,
Change Owner, Change Approver, Problem Owner, Service Owner). It is the bridge §8.1(a) implied: an
abstract, estate-wide role catalog realized as concrete `sys_user_group` records.

### 10.1 The finding: the role label and the group's function segment disagree

In the sampled deployment, the TOM role **`Incident Resolver – SRE / DevOps Team`** resolves to a
group whose function segment is **`ASUP` — support, not `SSRE`.** That is the SME's "reusing one",
visible in the data: an SRE-named role slot filled by a support technician group.

**The consequence for any crosswalk: reading the ROLE NAME to decide whether SRE cover exists returns
the wrong answer.** Only the group name's function segment is reliable. Pattern-matching `%SRE%`
against role names is the obvious implementation and it is wrong here.

This is the third instance of one defect class in this document, and they are worth reading together
because the next one will look different again:

| Where | The label that isn't the identity |
|---|---|
| §3.3 | Two relationship types share `parent_descriptor`; the forward label does not identify the type |
| G35 §A3b | A role name the canonicalizer cannot match kills its own row |
| §10.1 | An SRE-named role resolves to a support-function group |

**The rule they share: identify by the key, classify by the structured field, and treat the
human-readable label as evidence rather than as identity.**

### 10.2 Why this changed a signed ruling

G35's register originally ruled **G16 Site Reliability Engineer REQUIRED**, inferring "accountable"
from required-ness. Amended the same day to **OPTIONAL and DERIVED**, for three compounding reasons
recorded in the gate-log:

- **the cardinality is inverted** — every other register line is a per-application holding, while an
  SRE team covers 20–60 applications: a shared function pointing at many, not an accountability held
  by one;
- **it is derivable, so asserting it is the wrong mechanism** — a required flag would demand a
  redundant assertion for a computable fact, and would put every application in breach until
  somebody made it;
- **§G16's own KIND question is answered** — it is a *staffing* fact about a shared team, which
  §G16 warned is "a different kind of fact" from accountability for an application.

**And G71's completeness report must exclude it.** A derived, many-to-one fact has no place in a
per-application required-contact check; including it would raise a finding on every application
whose SRE team merely was not asserted — the noisy check §C6 warns gets weakened rather than fixed.

### 10.3 What is NOT decided here

Whether DryDocs **parses** the convention. Deriving a team's function class from its name is a
capability, not a fact, and it belongs with the group-membership work under the company-signed
`snow-hpsm-queue-to-group` (§9), not to G35. Two things to settle there rather than here: whether
the segment vocabulary is closed (three function codes observed, more may exist), and whether a
group name that does not parse is a data-quality finding or simply out of scope.

### 10.4 The convention IS already parsed — partially, and not for the case that raised it

**§10.3 asked whether DryDocs parses the naming convention and said it was a capability question for
the group-membership work. It is already answered company-side, and the answer has a gap exactly
where §10 needed it.**

Evidence: a company-session code search, 2026-08-11. The tier derivation lives in the ServiceNow
row model as a computed field, and its implementation is two lines:

```
_SENG  ->  "L3"     # Software Engineering
_ASUP  ->  "L2"     # App Support
otherwise -> None   # unknown, never guessed
```

**What it drives.** The derived tier is not decorative — it reaches the graph as an edge property on
the support edges: the `:ServiceNowGroup.tier` property, a primary-resolver edge to the HPSM queue,
the support-queue edge from the application, and a membership edge. So the `*_ASUP` / `*_SENG`
suffix is a **load-bearing convention**: it sets the L2/L3 tier wherever support is modelled.

**What it does NOT parse, and this is deliberate.** The division prefix and the domain segment are
opaque. The function's own docstring says so: *"Derives ONLY the tier from the group name — the
group name itself is never derived (names are irregular and used as-fetched)."* The **full group
name string is the MERGE key**, used verbatim. There is no decomposition of division or domain.

### 10.5 Three things this changes

**(a) THE SRE CASE IS NOT COVERED.** The parser knows two tokens. The SME's third function code —
support-SRE — is **not among them**, so an SRE group derives `tier = None`. §10 recorded that "is
there SRE cover" is derivable from the convention; the derivation **exists for support and
development and not for SRE**. That is a concrete, named gap rather than an open question, and it
belongs to the company gate that owns the parser. G16's ruling (OPTIONAL and DERIVED) is unaffected
— the fact remains derivable in principle — but anything that *depends* on the derivation working
today would be depending on a branch that returns None.

**(b) THE MATCH IS UNDERSCORE-DELIMITED, which is a fragility worth recording.** The token matches
mid-name or trailing, but only in underscore form. A run-together name or a hyphenated variant does
not match and yields `tier = None`. Combined with (a), the failure mode is uniform and quiet:
**unknown tier is never guessed, it is null** — which is the right behaviour, and also means a
missing tier is indistinguishable from an unparseable one unless something says which.

**(c) THE `u_group` NAME IS THE JOIN, AND IT IS TAKEN AS-FETCHED.** Names being "irregular" is
recorded in the source, not inferred by us. Any DryDocs-side parsing beyond the tier token would be
re-deriving something the owning side deliberately declined to derive.

### 10.6 A correction to RELAY-6 and §9: signed is not finished

**§9 and RELAY-6 both say the company model is "built and signed". That overstates the build half,
and the correction matters for anyone planning against it.** The gate is signed (2026-07-15) and the
tier logic is implemented — but the **SNOW support loaders are marked DRAFT and the source entry
stays `confirmed: false`**, pending the final loader build.

So the accurate statement is: **the MODEL is signed and partially implemented; the LOAD is not
finished.** That changes nothing about G35's decision not to mint a competing shape — a signed
model is a position whether or not its loader is complete — but it does mean the company side is
mid-build, and a producer-side item that assumed a finished loader would be wrong.

**Also visible, and worth naming because it bears on a separate open question:** the company model
carries a **`:LogicalDeployment` node class** on the primary-resolver edge. DryDocs has no
deployment-grain node, and C10's gate-bound candidate #1 plus `Idea-101` are both about whether to
adopt one. **The company may already have.** Recorded as an observation, not a conclusion — the
screenshots show the label in an edge shape, not its definition — and it is now the sharpest
question for RELAY-6 to bring back, because two sides independently modelling a deployment concept
is exactly the collision RELAY-6 exists to prevent.

### 10.7 The catalog, exported (2026-08-11) — 83 rows, and it carries its own SEAL marker

**The count is 83, not "100+".** §8.1(a) recorded the SME's initial estimate; the export corrects it.
Columns: `name`, `scope`, `type`, `description`, plus audit fields.

**`scope`** is `Individual` or `Group`, as §8.1(b) recorded. Roughly a quarter are Individual and the
rest Group — so the catalog is mostly the **operational and approval layer**, not the accountable
one.

**`type`** takes `Accountable`, `Operational`, `Approval`, `Assignment`, `other` and NULL. **The
overwhelming majority are `other`** — only a couple carry `Accountable`, and NULL appears on several.
So `type` is present but weakly populated, and it is **not** a reliable classifier on its own. This
is §3.2's rule again: the column exists, and what it carries is thinner than its name suggests.

**THE USEFUL FINDING: the catalog says which roles come from SEAL, in its own description text.**
A substantial block of the Individual-scoped rows are described as "… from SEAL" — Application
Owner, the Information Risk Manager, CTO, Deployment Owner, Primary and Backup Information Owner,
Design Authority, the Operate Manager family, Chief Business Technologist, Backup Application Owner.
**That is the register mapping §A asked for, already written down by the source.** G70 does not have
to reconstruct which of the two registers a role belongs to — it can read it, then verify rather
than derive.

**Also visible: role families this project has never seen** — third-party-website ownership, an
RTM pair for external e-bonding, capacity planning, legal-entity approvals, a universal-request
fulfilment ladder, and several central management teams. None is in scope; they are recorded because
"the catalog is 83 roles, most of which are not ours" is the honest shape, and a vocabulary file
seeded from it should mark what is out of scope rather than silently drop it.

### 10.8 One thing to settle before G70 seeds the register: two different SREs

The export shows **two distinct role types**, and this document may have conflated them:

| Catalog row | `scope` | What it looks like |
|---|---|---|
| Site Reliability Engineer (SRE) | **Individual** | a named person, sitting among the other Individual accountable roles |
| Incident Resolver – SRE / DevOps Team | **Group** | an operational team, alongside the other incident-resolver tiers |

**G16's amendment (OPTIONAL and DERIVED) was argued from the GROUP one** — "an SRE team serves 20–60
applications", which is a many-to-one shared function and correctly not a per-application assertion.

**But the register line G16 came from the SME's thirteen-class list, which reads as the INDIVIDUAL
one.** If that is right, the amendment's *ruling* still holds — optional — while its *reasoning* was
about the other row, and an Individual-scoped SRE is a per-person holding like every other Individual
role, not something derived from a group name.

**This is flagged rather than ruled**, because it changes what G70 seeds. It does not reopen the
gate: G16 is OPTIONAL either way, and nothing else in the register moves. See the open question in
the gate-log amendment note.
