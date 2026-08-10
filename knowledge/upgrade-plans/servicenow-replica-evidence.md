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
