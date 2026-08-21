# ADR 0010 — Internal source terms: identity takes a neutral name (`app_id`); evidence keeps the source's

```yaml
status: ACCEPTED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-07-25
accepted: 2026-08-01    # ruled at backlog S1 (chad.wilson) — ACCEPTED WITH AMENDMENTS,
                        # edited to the business-application-identity gate ruling (2026-07-27)
gate: business-application-identity   # config/gate-log.md — owns the property-term binding
deciders: [chad.wilson, ontology-mapper, SME-gate]
layer: 2-ontology
affects:
  - drydocs_core/schema/seal_ontology_supplement.cypher , ontology.cypher , constraints.cypher
  - drydocs/loaders/seal_*.py + drydocs/loaders/cypher/seal_*.cypher
  - drydocs_core/models/seal.py
  - drydocs_api/query_specs.py
  - web/src/data/mappingsDemo.ts , web/src/ownership/
  - config/taxonomy/business-application.yaml
  - docs/patterns/data-catalog/enterprise-data-catalog-ontology.md
extends: 0003-application-naming-disambiguation.md
```

> ## ACCEPTED WITH AMENDMENTS — 2026-08-01 (backlog S1)
>
> The amendment this ADR was waiting on has been **made**. The body below is now the ruled
> shape, not the v1 proposal; the `business-application-identity` gate (SIGNED OFF
> 2026-07-27, `config/gate-log.md`, 22/22 confirmed / 0 edits) is the authority for the
> property-term binding and this ADR now agrees with it. **Build from this document.**
>
> What the gate changed, recorded here so the reasoning is not lost:
>
> - **`id_authority` is WITHDRAWN** (§B0 → §B1(c)). The SME ruled that a second authority
>   issuing app ids will not happen, which removed the only justification for a qualified
>   reference — with one permanent registry it is a constant column on every node. The
>   authority is recorded **once**, in `config/taxonomy/business-application.yaml`
>   (`source_of_record: SEAL`), which is also strictly cheaper under the case that *can*
>   still happen: a registry rename. The Decision block, Option C and rules 2–3 below were
>   edited accordingly; the original analysis is kept under "Options considered" because the
>   dual-registry reasoning is what the ruling had to answer.
> - **`app_urn` is DEFERRED, not withdrawn**, with a named trigger (§B3).
> - **The rule is TWO-PART** (§B2 — the session's most consequential correction). Rule 1
>   alone was incomplete; see the Decision block.
> - **`SEALID` was never a source field name** (§B4/B5). It appears nowhere in code, SQL or
>   Cypher — only in prose. The seal-extract reads the SEAL Reports export, whose header is
>   `Application ID`, and the row model was already `app_id`. `seal_id` was a DryDocs-era
>   coinage over a value that was already neutral everywhere else.
>
> The build is backlog **S3**, which this ADR gates. This document authorizes the SHAPE;
> the gate authorized the graph write.

## Context

Two internal abbreviations run through DryDocs:

- **SEAL** — the internal registry of record for business applications; issues the
  application id. (Amended at S1: this line said "issues the `SEALID`". §B4/B5 established
  that no source ever used that name — the SEAL Reports export header is `Application ID`.)
- **PAT** — the internal product/area-product catalog; source of the product hierarchy and
  team roles.

The review question: *will these survive an internal port restructure — i.e. if the company
renames, replaces, or reorganizes SEAL or PAT, how much of DryDocs has to change?*

### The audit

The two are in **very different** shape, and the difference tells you what the fix is.

**PAT — already safe.** It appears in gate specs, `config/precedence.yaml` prose, and
comments. It appears essentially **nowhere** in graph labels, property names, module names,
or the API. Its concepts landed as `:Product`, `:AreaProduct`, `:ProductLine`, `:CatalogLOB`,
`:BusinessSegment`, `:Role`, `:ProductRole`. Renaming PAT tomorrow costs a documentation
sweep and nothing else.

**SEAL — not safe.** `seal_id` is the **canonical key** on `:BusinessApplication`:

| Token | Occurrences (schema + loader Cypher + API) |
|---|---|
| `seal_id` | 47 |
| `seal_app_ref` | 15 |
| `seal_ids` | 13 |
| `seal_sid` / `seal_holder_sid` | 8 |

It has already crossed the boundaries that make it expensive:

- **API** — `drydocs_api/query_specs.py` (the console's contract).
- **Console** — `web/src/data/mappingsDemo.ts` carries `seal_id` and `app_seal_id`;
  `match_method: 'seal_var'` is a displayed enum value.
- **Config** — `config/overrides/seal-contact-overrides.csv`, materialized as the
  `seal_contact_override` table in `mapping.db`.
- **Modules** — `seal_applications.py`, `seal_attribution.py`, `seal_contacts.py`,
  `seal_ontology_supplement.cypher`.

### This contradicts a rule the repo already made

ADR 0003 rule 1: *"source-system fields stay verbatim on **source-labeled** nodes."* The
whole point of the rule is that `:ControlMJob` may carry Control-M's own field names because
the label already declares the source. `:BusinessApplication` is the **canonical** node — the
one deliberately named for the concept rather than the registry — so a registry-named key on
it is exactly the case the rule excludes. The rule is right; it just was not applied here.

The taxonomy layer already got this right. `config/taxonomy/business-application.yaml`:

```yaml
concept: BusinessApplication           # generic node concept
source_of_record: SEAL                 # authoritative registry for BusinessApplication
identifier: "Application ID"           # the SOURCE's own field name for the unique id (= app_id)
```

with the comment *"The concept is deliberately decoupled from the vendor system — SEAL is one
source of record for it, not the concept itself."* The graph and API layers did not inherit
that separation.

**Amended at S1 — and this file is now the two-part rule in miniature.** When this ADR was
written the `identifier:` line read `SEALID`, which §B4/B5 found recorded *a name the source
does not use*; it was corrected at the gate sign-off to `"Application ID"`, the export's
actual header. Note it was NOT corrected to `app_id`: the taxonomy entry is **evidence**, so
it keeps the source's own term (rule 2), while the graph property is **identity**, so it is
neutral (rule 1). The same concept, named twice, on purpose.

### External precedent

`reference/research/databricks-unity-catalog.md` (2026-07-25) records why this matters beyond
tidiness. Unity Catalog's central design choice is that **the namespace is the governance
object** — the identifier that resolves a reference is the same object carrying permissions,
lineage, and definitions. What it replaced was one metastore per workspace: identity
fragmented every time an org unit changed. That is the same failure an internal registry
rename would cause here.

Its glossary/domain/governed-tag features land almost exactly on node types
`docs/patterns/data-catalog/enterprise-data-catalog-ontology.md` already defines
(`CatalogBusinessTerm`, `CatalogDataDomain`, `CatalogTag`, `CatalogClassifier`) — independent
convergence on the same four concepts. The note's takeaway 2, *"a controlled vocabulary needs
an enforcement point, or it rots"*, is the reason the migration below ends at a gate rather
than at a rename.

## Decision

**The naming rule is TWO-PART. Identity takes a neutral name; evidence keeps the source's
own term.** Ruled at gate §B2 — the half this ADR originally lacked, and the one that stops
the rename from becoming a lie about provenance.

```cypher
(:BusinessApplication {
   app_id: "70001"        // the canonical key; neutral name, no registry in it
})                        // the issuing registry is recorded ONCE, in
                          // config/taxonomy/business-application.yaml (source_of_record: SEAL)
```

Six rules:

1. **(i) IDENTITY — canonical nodes take neutral property names.**
   `:BusinessApplication.app_id`, not `seal_id`. Registry-named properties are permitted only
   on source-labeled nodes, per ADR 0003 rule 1.
2. **(ii) EVIDENCE — provenance and match vocabulary KEEPS the source's own term.**
   `ATTRIBUTION_TIERS 'SEAL'` and `match_method: 'seal'` **stay**. SEAL's portal calls the
   field `Application ID`, but the wider ecosystem — Control-M CMDLINEs, internal docs —
   says SEAL / SEAL_ID. Those strings record *what another system literally wrote*; renaming
   them would make the graph misdescribe its own source rather than tidy it. An application
   of rule 1 that sweeps these too is a misapplication.
3. **The issuing authority is declared once, not carried per node.** `id_authority` is
   WITHDRAWN (§B0/§B1(c)): one permanent registry makes it a constant column. The authority
   lives in `config/taxonomy/business-application.yaml`, and the source-field ledger in
   `config/source-mappings/seal-extract.yaml` — the mechanism `controlm-psgmgr.yaml` already
   uses, guarded by `test_source_mapping_drift.py`. **The honest limit (§B6):** that ledger
   is DECLARATIVE and guard-reconciled, **not** a runtime mapping — loaders still hardcode,
   and making it load-bearing is a real build, deliberately out of scope.
   `app_urn` is DEFERRED with a named trigger (§B3), not withdrawn: it returns if a second
   authority ever issues application identifiers.
4. **External surfaces expose the neutral name only.** `drydocs_api` and `web/` emit
   `app_id`. No `seal_id` in a route, a QuerySpec, a column header, or a demo fixture —
   subject to rule 2, which keeps `match_method` values as they are. This costs nothing today
   and is the entire reason for doing this before the console hardens.
5. **Abbreviations get defined, not encoded.** "SEAL", "PAT", "AIS" and their kin belong in a
   `CatalogBusinessTerm`-shaped glossary with a definition and a scope — not embedded in
   identifiers. (Amended at S1: this rule originally required an `id_authority` cross-link;
   with that property withdrawn, the glossary links to the `source_of_record` declared in
   `config/taxonomy/business-application.yaml`.) Same conclusion the reopened **Q6** acronym
   question is circling, and the gap the Unity Catalog note names (*"Agent metadata
   (synonyms, display names) — no analogue yet"*).
6. **PAT terminology is explicitly out of scope.** It never leaked into code. Touching it
   would be effort with no return.

### Migration — additive, reversible, gated

**Amended at S1 to the gate's C1–C4 cutover.** The inventory is **8 key-bearing sites**, not
7 — 4 MERGE (`seal_applications:19`, `manual_seal_attribution:32`, `pat_product_mapping:54`,
`software_registry:52`) and 4 MATCH (`batch_port_orchestrator:25`,
`manual_seal_attribution:41`, `seal_attribution:32`, `seal_contacts:27`). The key flips in
**ONE atomic change across all eight**: a Neo4j uniqueness constraint IGNORES NULLS, so a
partial cutover would *silently double* the canonical node rather than fail. `:Port` follows
NOW (§D1). Existing graphs are handled by **REBUILD, not migration** (wipe-and-rebuild
doctrine, 2026-07-23), which is why phase 4 below is a retirement rather than a backfill.

> **Trap recorded at §D1 for the implementing phase:** `CREATE CONSTRAINT <name> IF NOT
> EXISTS` matches on the NAME — redefining `port_unique` under the same name SUCCEEDS AND
> DOES NOTHING, leaving the old definition live. DROP first, or take a new name.

| Phase | Action | Reversible? |
|---|---|---|
| **1** | Loaders write `app_id` **alongside** `seal_id` from the same row value, across all 8 sites at once. Constraint added on `app_id`; existing `seal_id` constraint retained. | Yes — drop one property |
| **2** | `drydocs_api` + `web/` read and emit only `app_id`. QuerySpecs updated. Console fixtures renamed. Rule 2 keeps `match_method` values unchanged. | Yes — revert the readers |
| **3** | Loader Cypher, `graph-tests/`, and gate pages move to `app_id`. `seal_id` becomes a **deprecated alias**, still written. | Yes |
| **4** | Gate: retire `seal_id` writes; keep it on `:Document`-style source-labeled nodes where ADR 0003 rule 1 permits it. | Gate decision |

Module and file renames (`seal_applications.py` → `business_applications.py`,
`seal_ontology_supplement.cypher` → `business_application_supplement.cypher`) are **phase 3+
and lowest value** — they are cosmetic relative to the property key, and they collide hard
with the company port. Do them last, or not at all.

## Options considered

### Option A — Leave `seal_id` as the canonical key

**Pros:** zero work; `seal_id` is unambiguous today; SEAL may well never be renamed.
**Cons:** the console is being built *right now* against it, so the blast radius grows weekly;
it violates ADR 0003's own rule on the canonical node; and it hard-codes an org-chart artifact
into the graph's primary key. **Rejected** — the cost is lowest today and rises monotonically.

### Option B — Rename `seal_id` → `app_id`, nothing else ✅ TAKEN (as amended)

| Dimension | Assessment |
|---|---|
| Complexity | Low-medium |
| Cost | One mechanical sweep |
| Restructure-resilience | **Partial** |

**Pros:** removes the vendor name from the key; a small, well-understood diff (the
`ControlMFolder` rename playbook applies).
**Cons:** loses the information that the id came from SEAL. If a second registry ever issues
application ids — the plausible outcome of an internal restructure, e.g. a migration where
both old and new ids are live — there is no way to say which authority a bare `app_id` came
from, and the two id spaces silently collide. ~~**Rejected as insufficient**~~

**AMENDED — this option was TAKEN at gate §B0/§B1(c).** The SME ruled the dual-registry
premise false: SEAL remains the single issuing registry. The stated con is answered without
a per-node property — the authority is declared once in
`config/taxonomy/business-application.yaml` plus the `seal-extract.yaml` source-field ledger,
so nothing is lost except the ability to represent a case that will not arise. If it ever
does, §B3's named trigger reopens `app_urn`.

> **Amended at S1: the gate chose Option B, not Option C.** §B0 ruled the premise below
> false — a second issuing authority will not happen — which collapses the case-3 argument
> that made C worth its cost. What C got right and B as originally written did not is that
> the authority still has to be *recorded* somewhere; the ruling puts it in the taxonomy file
> and the source-field ledger instead of on every node. Both options are kept below because
> the ruling is only legible against the alternative it rejected.

### Option C — `app_id` + `id_authority` (+ optional URN) — NOT TAKEN (superseded at §B0)

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | Additive migration; no big-bang |
| Restructure-resilience | **Full** — a rename is a data change |
| Standards fit | Matches the catalog URN pattern and Unity Catalog's precedent |

**Pros:** survives a registry rename, a registry replacement, *and* a dual-registry
transition; the authority becomes queryable (`which apps are still keyed by the old
registry?` is a one-hop query); it is additive, so every phase is independently revertible;
it makes the canonical node genuinely canonical, finishing what the taxonomy layer started.
**Cons:** two properties instead of one; a transition window where both `seal_id` and
`app_id` exist and could drift (mitigated: same loader writes both, and a verify rule asserts
equality); wide but mechanical diff; must be port-sequenced.

### Option D — Full `CatalogBusinessTerm` glossary now, identity via glossary lookup

**Pros:** the most complete answer; directly implements the documented catalog pattern; would
also resolve Q6.
**Cons:** the glossary is not built, is not gated, and Q6 is explicitly still open and under
producer review. Making the console's identity contract depend on an unbuilt, ungated
subsystem is the wrong sequencing. **Rejected for now** — Option C is a strict subset and a
clean stepping stone; rule 5 keeps the glossary on the roadmap without blocking on it.

## Trade-off analysis

> **Amended at S1 — this whole section rested on a premise the gate ruled false.** The
> analysis below argues from three possible futures and concludes that case 3 justifies
> Option C's extra property. §B0 established that case 3 will not arise: SEAL remains the
> single issuing registry. Case 1 is the live risk, and Option B handles it. The section is
> kept unedited because it is the reasoning the SME was asked to rule on, and a decision
> record that deletes the argument it overruled is not a record. Read it as history.

The decision hinges on **what an "internal port restructure" would actually do.** Three cases:

1. **SEAL is renamed** — Option B and C both survive; A requires a 47-site sweep across
   schema, loaders, API, and UI.
2. **SEAL is replaced by another registry** — only C survives cleanly: `id_authority` changes
   value, the property name does not.
3. **Both registries live during a transition** — only C survives *at all*. B silently merges
   two id spaces under one key; A cannot represent the new one without a second property
   named after the second vendor, which is where this started.

Case 3 is the realistic shape of a corporate registry migration, and it is the one that
argues past the "B is cheaper" objection.

The counter-argument deserves stating plainly: **this may never happen, and B is materially
cheaper.** The reason to take C anyway is that the marginal cost over B is small — one extra
property written by the same loader — while the difference in outcome under case 3 is total.
And rule 4 (external surfaces emit the neutral pair) is free *today* and unaffordable later;
even if the graph migration is deferred, **the API and console should adopt the neutral
contract in the next commit that touches them.**

## Consequences

*(Amended at S1 to the ruled shape — one property, not two.)*

**Easier**
- A registry **rename** becomes a one-line taxonomy edit, not a refactor: the name lives in
  `business-application.yaml`, not on 47 sites.
- The canonical/source-labeled split from ADR 0003 becomes consistently true.
- The console's contract stops leaking an internal tool name to every viewer.
- Provenance stays honest: rule 2 means `match_method: 'seal'` keeps saying what the source
  actually said, so the rename cannot quietly rewrite history.

**Harder**
- A dual-write window during phases 1–3; a `graph-tests/` rule must assert
  `app_id = seal_id`.
- All 8 key-bearing sites must flip in ONE change — uniqueness constraints ignore nulls, so
  a partial cutover silently doubles the canonical node instead of failing.
- Every `seal_*` module, Cypher file, and QuerySpec is touched — mechanical but wide, and
  rule 2 makes it a *judged* sweep rather than a find-and-replace.
- The company port must sequence this; `seal_id` almost certainly appears in company-side
  code the producer cannot see.
- Existing loaded graphs are handled by **rebuild, not backfill** (wipe-and-rebuild doctrine,
  2026-07-23).

**To revisit**
- Whether `Employee.seal_sid` / `seal_holder_sid` follow the same treatment — they name a
  *person* identifier that happens to be sourced from SEAL, which may be a different call.
  Deliberately out of scope here.
- `app_urn` if §B3's named trigger fires (a second authority issuing application ids).
- The `CatalogBusinessTerm` glossary (Option D) once Q6 is ruled — the natural home for
  defining SEAL/PAT/AIS as terms, per Unity Catalog takeaway 2 ("the entry and its
  enforcement ship together").

## Action items

*(Amended at S1; items 2/3/9 closed by the **S3 build, 2026-08-01**. Items 1 and 4 were done
at the gate itself, 2026-07-27.)*

1. [x] Gate spec in `config/gate-prompts/` for the identity reshape; routed and recorded in `config/gate-log.md` — **SIGNED OFF 2026-07-27, 22/22 confirmed, 0 edits.**
2. [x] **Phase 1 — DONE (S3).** All 8 key-bearing sites flipped in one change: the MERGE key is `app_id` at `seal_applications:19`, `manual_seal_attribution:32`, `pat_product_mapping:64`, `software_registry:52`, and the four MATCHes (`batch_port_orchestrator`, `manual_seal_attribution:41`, `seal_attribution`, `seal_contacts`) read it. `seal_id` is dual-written from the same row value as a deprecated alias. New constraint `businessapplication_app_id`; `businessapplication_seal` retained. `:Port` NODE KEY → `port_app_key (parent_app_id, kind)`, with `port_unique` DROPped first. New suite `graph-tests/business-application-identity.yaml` (5 cases) asserts `app_id = seal_id` and the §C2 double.
3. [x] **Phase 2 — DONE (S3).** `query_specs.py` (6 specs) and `mappings.py` emit `app_id`; `web/src` (`mappingsDemo.ts`, `mappingsApi.ts`, `MappingsRoute.tsx`, `assetSearch.ts`) follows. `match_method` values UNCHANGED per rule 2 — the fixture's invented `'seal_var'` was corrected to the real `'seal'`, which is the opposite of renaming it.
4. [x] `config/taxonomy/business-application.yaml` corrected at sign-off: `identifier: SEALID` → `"Application ID"`, the export's real header.
5. [ ] ~~Add the URN form~~ — DEFERRED with §B3's named trigger, not an open item.
6. [ ] Phase 3–4: migrate the remaining loader Cypher prose and gate pages; gate the `seal_id` retirement (§G3). **Carries S3's named residual:** the committed FILE formats still say `seal_id` — the manual-load `target_key=seal_id=<value>` grammar (`manual_mappings.py` refuses a row without it) and the override CSV header `app_seal_id` (`OVERRIDE_HEADER`). S3 aliased at the wire and left the files alone deliberately; renaming them stops every already-committed CSV from parsing, so they belong to the retirement gate.
7. [ ] Feed the glossary rule into the **Q6** disposition and the domain-scoped acronym-catalog idea (`docs/restructure/IDEAS.md` L51/L74) — where SEAL/PAT/AIS get defined.
8. [ ] Port-sequence through `docs/port/port-prompt.md` before any other wide structural port.
9. [x] **DONE (S3):** `config/source-mappings/seal-extract.yaml` written — 87 + 5 column rows transcribed from `models/seal.py` and the two loaders, `census: pending`, the identity row recorded as `Application ID → BusinessApplication.app_id`. Registered at the dataset's `locator.mapping` and removed from `test_source_mapping_drift.py`'s `LEDGER_PENDING`. Still DECLARATIVE per §B6 — no loader reads it.
