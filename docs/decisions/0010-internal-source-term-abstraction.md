# ADR 0010 — Internal source terms: identity carries its authority (`app_id` + `id_authority`), not the registry's name

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-07-25
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

## Context

Two internal abbreviations run through DryDocs:

- **SEAL** — the internal registry of record for business applications; issues the `SEALID`.
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
concept: BusinessApplication      # generic node concept
source_of_record: SEAL            # authoritative registry for BusinessApplication
identifier: SEALID                # the unique id (= app_id)
```

with the comment *"The concept is deliberately decoupled from the vendor system — SEAL is one
source of record for it, not the concept itself."* The graph and API layers did not inherit
that separation.

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

**Carry identity as a qualified reference — the value plus the authority that issued it —
never as a scalar named after the registry.**

```cypher
(:BusinessApplication {
   app_id:       "82507",                                  // the value; neutral name
   id_authority: "SEAL",                                   // WHICH registry issued it
   app_urn:      "urn:dd:businessapplication:seal:82507"   // optional canonical form
})
```

Six rules:

1. **Canonical nodes take neutral property names.** `:BusinessApplication.app_id`, not
   `seal_id`. Registry-named properties are permitted only on source-labeled nodes, per
   ADR 0003 rule 1.
2. **The registry name becomes data, not a name.** `id_authority: "SEAL"` is a value in a
   controlled vocabulary. A registry rename becomes a data migration over one property —
   which is a gate, not a refactor.
3. **The URN form follows the catalog pattern already documented.**
   `urn:dd:<concept>:<authority>:<value>`, aligned with the URN section of
   `enterprise-data-catalog-ontology.md`. Optional in phase 1; it is the join key if a second
   authority ever issues application identifiers.
4. **External surfaces expose the neutral pair only.** `drydocs_api` and `web/` emit `app_id`
   and `id_authority`. No `seal_id` in a route, a QuerySpec, a column header, or a demo
   fixture. This costs nothing today and is the entire reason for doing this before the
   console hardens.
5. **Abbreviations get defined, not encoded.** "SEAL", "PAT", "AIS" and their kin belong in a
   `CatalogBusinessTerm`-shaped glossary with a definition, a scope, and an
   `id_authority` cross-link — not embedded in identifiers. This is the same conclusion the
   reopened **Q6** acronym question is circling and the gap the Unity Catalog note names
   (*"Agent metadata (synonyms, display names) — no analogue yet"*).
6. **PAT terminology is explicitly out of scope.** It never leaked into code. Touching it
   would be effort with no return.

### Migration — additive, reversible, gated

| Phase | Action | Reversible? |
|---|---|---|
| **1** | Loaders write `app_id` + `id_authority` **alongside** `seal_id`. Constraint added on `app_id`; existing `seal_id` constraint retained. | Yes — drop two properties |
| **2** | `drydocs_api` + `web/` read and emit only `app_id`/`id_authority`. QuerySpecs updated. Console fixtures renamed. | Yes — revert the readers |
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

### Option B — Rename `seal_id` → `app_id`, nothing else

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
from, and the two id spaces silently collide. **Rejected as insufficient**, though it is
strictly better than Option A and is a valid fallback if capacity is tight.

### Option C — `app_id` + `id_authority` (+ optional URN) ✅

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

**Easier**
- A registry rename or replacement becomes a gated data migration, not a refactor.
- `id_authority` is queryable — dual-registry transition state is visible in the graph.
- The canonical/source-labeled split from ADR 0003 becomes consistently true.
- The console's contract stops leaking an internal tool name to every viewer.

**Harder**
- Two properties during the transition; a verify rule must assert they agree.
- Every `seal_*` module, Cypher file, and QuerySpec is touched — mechanical but wide.
- The company port must sequence this; `seal_id` almost certainly appears in company-side
  code the producer cannot see.
- Existing loaded graphs need a backfill (one `SET` statement, plus the new constraint).

**To revisit**
- Whether `Employee.seal_sid` / `seal_holder_sid` follow the same treatment — they name a
  *person* identifier that happens to be sourced from SEAL, which may be a different call.
  Deliberately out of scope here.
- The `CatalogBusinessTerm` glossary (Option D) once Q6 is ruled — at which point
  `id_authority` values should become glossary-backed rather than free strings, per Unity
  Catalog takeaway 2 ("the entry and its enforcement ship together").

## Action items

1. [ ] Gate spec in `config/gate-prompts/` for the identity reshape; route through `ontology-mapper` and record in `config/gate-log.md`.
2. [ ] Phase 1: loaders write `app_id` + `id_authority` alongside `seal_id`; add the `app_id` constraint; add a `graph-tests/` rule asserting `app_id = seal_id` during the transition.
3. [ ] Phase 2 (**do this before more console routes land**): `drydocs_api/query_specs.py` and `web/src/**` emit `app_id` + `id_authority` only; rename `app_seal_id` in `mappingsDemo.ts`; reword `match_method: 'seal_var'`.
4. [ ] Update `config/taxonomy/business-application.yaml` to state the property contract explicitly (`identifier: SEALID` → `app_id` carried with `id_authority: SEAL`).
5. [ ] Add the `urn:dd:businessapplication:<authority>:<value>` form to `docs/patterns/data-catalog/` URN reference.
6. [ ] Phase 3–4: migrate loader Cypher and gate pages; gate the `seal_id` retirement.
7. [ ] Feed rule 5 into the **Q6** disposition and the domain-scoped acronym-catalog idea (`docs/restructure/IDEAS.md` L51/L74) — the glossary is where SEAL/PAT/AIS get defined.
8. [ ] Port-sequence through `docs/port-prompt.md` before any other wide structural port.
