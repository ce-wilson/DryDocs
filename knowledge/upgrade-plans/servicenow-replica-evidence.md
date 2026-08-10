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
> **The module half is a second finding, not an aside.** ServiceNow's Application Module is
> referenced by default on change records, so the field is *populated* and *not meaningful* — the
> reference exists because the form defaults it, not because someone asserted it. This is §3.2's
> lesson arriving on a field that would be far more tempting to trust than a null `u_hash`: a
> populated column can be emptier than an empty one. It bears directly on G35 §G15, which asks
> whether Application Module Owner's subject is a module DryDocs has no grain for — the honest
> answer from practice is that the module grain exists in the source and does not carry reliable
> meaning, so building a module grain to hold it would model the form default rather than the
> operating model.
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

### 1.4 Three reasons this is a report, not an ingestion contract

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
| **G35 §G15** — Application Module Owner: "a module owner plausibly owns a PART of an application, and DryDocs has no module grain to attribute to. Confirm the subject before required-ness" | SME 2026-08-09: modules are **referenced by default on changes and in practice not used as intended** | **ANSWERS THE SUBJECT QUESTION FROM PRACTICE** — the module grain exists in the source and does not carry reliable meaning. A DryDocs module grain built to hold this would model a form default. §G15 can be ruled without inventing one |

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

Ordered by how much they block. Q1–Q3 are SME questions; Q4–Q6 need one more look at the replica.

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
   alternative was considered and ruled out. **Residual:** what
   `tom_main.inheritance` / `inherited_from_ci` encode is still unexplained — if mapping is
   application-level, the inheritance those columns carry is inheritance *between CIs*, which is a
   different mechanism than role inheritance between application and deployment. §1.3(e) stands.
4. **Does the replica's `cmdb_rel_type` view carry `parent_descriptor`?** Not visible; decides §3.3.
5. **What does `delete_flag` mean operationally** — values, retention, interaction with
   `dwintel_dl_snapshot_trim`? Decides §3.4.
6. **What is `end_point` on `cmdb_rel_type`?** No public definition found. Instance or SME only.
7. **Is `u_seal_deployment_id` globally unique, or unique only within its application?** Raised by
   the 2026-08-09 confirmation that the identifier reads as `app_id(seal_id):deployment_id`. This is
   the one question that turns the SME's read into a business key: if it is scoped, any deployment
   node must be keyed on the **pair**, and a loader keying on `deployment_id` alone will MERGE
   distinct deployments from different applications into one node. Cheap to settle — a count of
   distinct `u_seal_deployment_id` against a count of distinct pairs answers it. **Blocks any
   deployment-grain modelling**, not just the gate.

Two smaller ones, recorded so they are not rediscovered: whether any table appears in more than one
`DW_*_DATA_VIEW` schema and which would be authoritative (§2.2), and whether `connection_strength` /
`percent_outage` are populated anywhere beyond the constant-and-null sample (§3.2) — the CMDB models
impact weight on the edge, and DryDocs has no equivalent, so it is worth knowing whether there is
anything there before deciding we do not need one.
