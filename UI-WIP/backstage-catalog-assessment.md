# Backstage catalog model — what's useful for the DryDocs design

> **Scope (2026-07-22, supersedes the broad `backstage-deepdive-plan.md`):** the internal
> Backstage/Neo4j site could not be located, so the distribution question (WP-7) is
> dropped. This is the WP-2 dive only: **catalog structure & design**, read from the
> clone at `C:\coding\projects\backstage` (`packages/catalog-model/`,
> `docs/features/software-catalog/`), assessed against the DryDocs graph design.
> The ReUI stack decision is untouched.

## 1. How their catalog is shaped (30-second version)

- **Entity envelope** (Kubernetes-style): `apiVersion` + `kind` + `metadata` + `spec`.
  `apiVersion`+`kind` together identify the schema; `metadata` is cross-kind
  (name/namespace/title/description/labels/annotations/tags/links); `spec` is
  kind-specific.
- **Kinds are few and closed** (Component, API, Resource, System, Domain, Group, User,
  Location — recently + AiResource, McpServerApi). Variety lives in **`spec.type`**, a
  free string the org is told to govern as its own taxonomy ("great care to establish a
  proper taxonomy"; explicit advice *against* a catch-all `Other`). Adding a kind is
  documented as high-impact and discouraged; adding a type is cheap.
- **Relations are never authored — always derived.** Descriptor files carry only spec
  fields (`spec.owner`, `spec.dependsOn`); backend *processors* emit directed relations
  from them; a *stitching* step materializes both directions onto each entity.
  Materialized `relations` are declared **authoritative over the raw spec field**
  (consume `ownedBy`, not `spec.owner` — the relation may have come from CODEOWNERS
  instead of the YAML).
- **Fixed small relation vocabulary, always inverse pairs:** ownedBy/ownerOf,
  partOf/hasPart, dependsOn/dependencyOf, providesApi/apiProvidedBy,
  consumesApi/apiConsumedBy, parentOf/childOf, memberOf/hasMember. Custom types are
  allowed but must be org-prefixed (`myCompany-maintainerOf`).
- **Stable identity = string ref `kind:namespace/name`** (`group:default/dev.infra`).
  The DB `uid` is documented as explicitly UNSTABLE — never referenced externally.
  `namespace` exists solely to bound name-uniqueness when two sources collide.
- **Three metadata channels with naming governance:** `annotations` (non-identifying,
  mostly machine-written keys into external systems), `labels` (filterable key:value
  classification), `tags` (flat facets). Keys are domain-prefixed
  (`pagerduty.com/…`); the `backstage.io/` prefix is reserved; unprefixed = private to
  the instance.
- **`status.items`** = read-only, multi-source status envelope on every entity:
  namespaced `type` + level/message/error, deduced by processing (today mainly
  ingestion errors surfaced back to the user).
- Separately from semantic relations, the catalog tracks **emitter→emitted edges**
  (which source called which entity into existence) purely for orphan detection and
  cascading deletion — deliberately NOT exposed as relations.

## 2. Crosswalk — their model ↔ ours

| Backstage | DryDocs | Note |
|---|---|---|
| Domain (bounded context, nestable) | LOB → ProductLine/Product | same role: business grouping above systems |
| System ("hides its internals, exposes public APIs") | Application (SEAL) | strongest match; their encapsulation framing fits SEAL exactly |
| Component (unit of software; types incl. data pipelines) | Job/Folder, ETLProcess, Script | their `spec.type` ≈ our kind discriminators |
| API (first-class *boundary* artifact, machine-readable definition) | the dataset/feed handoff between jobs | see takeaway T6 |
| Resource (runtime infrastructure) | DataAsset, DB/schema, server | |
| Group/User + memberOf/childOf | Team/Person + HAS_MEMBERSHIP (PAT) | their single-ultimate-owner rule ≈ our SUPPORTS design |
| ownedBy ("display + accountability, NOT runtime authorization") | SUPPORTS edge | boundary statement worth copying verbatim into our edge docs |
| kind:namespace/name ref | FID/ALIAS join tiers, ctlm_id | T3 |
| status.items | layer-4 context graph / loader WARN stream | T5 |
| emitter→emitted edges (hidden, GC-only) | WAS_GENERATED_BY / JobRun provenance | supports the edge-diet plan: provenance ≠ domain relations |

Their ontology is much coarser than ours (8 kinds vs 17+ node types and a governed
relationship registry) — it is **not** a candidate replacement, and nothing here argues
for reshaping our node labels. The value is in their *governance mechanics*, which are
Spotify-scale-tested versions of rules DryDocs mostly already has.

## 3. Takeaways worth adopting (concrete, small)

- **T1 — Closed kinds / open governed `type`: direct prior art for the MAC kind-enum
  rider gate.** Their settled answer to exactly our pending question (extend enum vs
  utility, from G17): keep the label/kind set small and closed; absorb variety in a
  governed free-string discriminator; never add a catch-all `Other` (it kills
  contextual behavior — plugins/views key off specific types, same way our modules
  would). Cite this at the gate as external precedent; it argues for "utility +
  governed discriminator" over enum growth.
- **T2 — "Consume the derived edge, not the raw field" as a UI rule.** They materialize
  relations and declare them authoritative over the spec fields they came from. Our
  equivalent: module pages and QuerySpecs should read ontology edges, never re-derive
  meaning from raw staged columns (which may lose precedence resolution — same reason
  as their CODEOWNERS example). Worth one sentence in the QuerySpec conventions.
- **T3 — Stable string ref format + namespace-as-collision-bound.** `kind:namespace/name`
  with an explicitly-unstable internal uid mirrors lessons we already paid for
  (FID/ALIAS tiers). Two cheap borrows: (a) standardize a display/deep-link ref grammar
  (`job:P012/<name>`-style — data center as the namespace is a natural fit for the
  4-DC name-collision case) for inspector URLs and export manifests; (b) keep graph
  element ids out of every external surface, stated as a rule.
- **T4 — Inverse-pair *labels* in the relationship registry.** We store one directed
  edge; they name both directions. Borrow for presentation only: add an
  `inverse_label` (e.g. SUPPORTS → "supported by") per entry in
  `relationship_vocabulary.yaml`, so the node inspector can phrase edges correctly
  from either endpoint without per-module hardcoding.
- **T5 — `status.items` shape for per-node operational status.** A namespaced,
  multi-source, read-only list ({type, level, message, error}) is a clean landing shape
  for what layer 4 (context graph) and the loader WARN/reject stream want to show in
  the inspector sidebar: each source contributes its own typed items; nothing authors
  status by hand. Candidate shape for the future health glyphs on the radial hub too.
- **T6 — The boundary artifact as first-class.** They promote the *interface* (API,
  with a machine-readable definition) to its own entity rather than a mere edge —
  their claim: it's the primary unit of discovery between teams. Our analog is the
  dataset/feed contract between producer and consumer jobs. We already have DataAsset;
  the borrowable idea is attaching the *machine-readable definition* (schema) to it as
  the contract — which is literally the Lineage module's "Schema definition" frame.
  Confirms that frame deserves first-class data, not an afterthought.
- **T7 — Metadata-key governance for the Description-field plan.** Their
  annotation/label naming rules (reserved core prefix; third-party keys
  domain-prefixed; unprefixed = instance-local) drop straight into the pipe-delimited
  Description-field metadata standard: reserve a `drydocs` prefix, require a
  system prefix for keys owned by external systems (scim, jira, seal), leave
  unprefixed keys team-local. Cheap to add to the template phase.
- **T8 — One canonical entity across environments.** Their explicit anti-pattern:
  `mytool-dev`/`mytool-prod` as separate entities; the recommendation is one canonical
  entity with per-environment views. Confirms our env toggle design (Prod|UAT|Dev
  re-scopes data under one node identity) and warns against ever splitting node
  identity per environment.

## 4. Explicitly not useful — skip

- **Storage/pipeline machinery** (SQL tables, stitching, refresh loops) — we have Neo4j
  + loaders; their pipeline (providers → processors → stitcher) is just a convergent
  validation of our taxonomy-first → ontology-rules → load order, nothing to import.
- **YAML descriptor files in source repos** — our sources are DB extracts and
  registries, not per-entity files. (Their `catalog-info.yaml`-in-repo idea only
  becomes relevant if scripts-in-SCM ever self-describe; parked.)
- **`apiVersion` machinery** — our versioned loaders + source-registry + versioned
  QuerySpec ids (`explorer.jobs.v1`) already cover schema evolution.
- **Their UI layer** — Material-UI v4 legacy mid-migration to `@backstage/ui`; nothing
  transfers to ReUI/Tailwind.
- **Relations-as-pairs in storage** — Neo4j traverses both directions natively; only
  the *labeling* idea (T4) transfers.

## 5. Verdict

The Backstage catalog does not change the DryDocs model — it independently arrives at
the same core rules we already enforce (derived-not-authored edges, small governed
vocabulary, taxonomy discipline for discriminators), which is a useful confidence
signal. The adoptable value is eight small, mostly-presentational-or-governance items
(T1–T8), of which **T1 (kind-enum gate precedent), T4 (inverse labels), T5
(status.items shape), and T7 (metadata-key prefixes)** are the ones with an obvious
existing home. Each is inbox/groom material, not unplanned scope.
