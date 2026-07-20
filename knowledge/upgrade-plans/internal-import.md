# Upgrade plan — internal import (v1)

**Status:** planned (to follow the v1 restructure).
**Owner agents:** `taxonomy-importer` → `ontology-mapper` → `pipeline-config` (+ loaders).
**Scope:** bring the **internal** data sources into the graph through the v1 four-layer flow,
with confidential data isolated in `internal/`. Companion to the producer→company port guide
([`../../git-readme.md`](../../git-readme.md)) and the backlog
([`../../docs/restructure/02-backlog.md`](../../docs/restructure/02-backlog.md), epics B/C).

> "Internal import" = the sources whose provenance is internal: **SEAL** (applications,
> ports, ownership), the **LOB → Product → Team** org taxonomy (Catalog/PAT), and **Oracle
> schemas/scripts**. Orchestration (BMC Control-M) is *external* and already lives — this
> plan is the internal counterpart, and it is where the publish boundary matters most.

---

## 1. Why a dedicated plan

Internal import is not just "more loaders." Three things make it different from the
already-live Control-M (external) ingestion:

1. **Confidentiality.** Real rosters, people, SIDs, and schema object names are confidential.
   They must land in the graph but **never** be committed outside `internal/`
   (see [`../../PUBLISH-BOUNDARY.md`](../../PUBLISH-BOUNDARY.md)).
2. **Precedence.** Internal sources sit at authority tiers 2–3 in
   [`../../config/precedence.yaml`](../../config/precedence.yaml) (internal standards, then
   LOB→Product→Team). They *refine and attach context to* the BMC baseline; they never
   redefine orchestration objects.
3. **Taxonomy/ontology discipline.** This is exactly where the POC drifted. Every internal
   hierarchy is imported as **taxonomy first**, then mapped to ontology through the
   **HITL gate** ([`../../docs/restructure/03-hitl-sme-flow.md`](../../docs/restructure/03-hitl-sme-flow.md))
   before any edge is written.

## 2. The flow (per source)

```
source extract  →  config/taxonomy/<source>.yaml      (taxonomy-importer; classification only)
                       │  real values → internal/, referenced by stable id
                       ▼
              taxonomy-ontology-map.yaml (status: proposed)   (ontology-mapper; PROV/ORG/DPROD)
                       │
                       ▼  guided per-decision gate
              status: confirmed                                (SME)
                       │
                       ▼
              loader applies edges → Neo4j                     (existing loaders, config-gated)
```

A source loads only when its `source-registry.yaml` entry is `confirmed: true` **and** every
mapping it needs is `confirmed`.

## 3. Sources, in order

### 3a. SEAL (applications, ports, ownership) — tier: lob-product-team / internal
- **Taxonomy** (`config/taxonomy/seal.yaml`): `Application ▸ Port(kind)`;
  `Membership ▸ Role ▸ Employee` as classification. (Backlog **B2**.)
- **Ontology** (gate): `HAS_PORT` → DPROD pattern; `HAS_MEMBERSHIP`/`OF_ROLE`/`HELD_BY` →
  W3C ORG n-ary membership. (Backlog **C2**.) These map types already exist in
  `relationship_vocabulary.yaml` (active) — reconcile, don't reinvent.
- **Confidential:** employee identities, real SEAL ids → `internal/org/`; taxonomy holds
  shape + stable ids only.
- **Loader:** existing `seal_applications` / `seal_contacts` — gate activation on
  `source-registry.yaml#seal-extract.confirmed`.

### 3b. LOB → Product → Team (Catalog / PAT) — tier: lob-product-team
- **Taxonomy** (`config/taxonomy/lob-product-team.yaml`):
  `LOB ▸ ProductLine ▸ Product ▸ AreaProduct ▸ DevTeam`. Shape only. (Backlog **B3**.)
- **Ontology** (gate): `CatalogLOB`/`DevTeam` → `org:OrganizationalUnit`,
  `BusinessSegment` → `org:FormalOrganization`; resolve the existing `SUPPORTS`
  Product-vs-AreaProduct range ambiguity (split or union notation). (Backlog **C3**.)
- **Confidential:** real team names, members, the PAT roster → `internal/org/`.
- **Precedence note:** this is the **lowest** authority for object *meaning* but the **sole**
  authority for *ownership* — it attaches context, it does not redefine baseline objects.

### 3c. Oracle schemas / scripts — tier: internal-standards
- **Taxonomy** (`config/taxonomy/oracle-schemas.yaml`): `Schema ▸ Table`; `Script`. Shape
  with placeholder ids; real object names → `internal/schemas/`. (Backlog **B4**.)
- **Ontology** (gate): `Schema`/`Table` → `DataAsset` (`dcat:Dataset` / `prov:Entity`);
  `Script`→`DataAsset` via `USED`/`GENERATED` from the consuming `ControlMJob`. This is the
  `oracle-schema-asset` proposed mapping already stubbed in
  [`../../config/taxonomy-ontology-map.yaml`](../../config/taxonomy-ontology-map.yaml).
- **Reference:** Oracle `db:` skill for extract SQL; never commit real schema names outside
  `internal/`.
- **Loader:** new `DataAsset` loader (see consolidated-plan Stream C.4) — depends on the
  `:Script`/`:File` constraints (Stream B.7) landing first.

## 4. Phases

| Phase | Work | Backlog | Gate / acceptance |
|-------|------|---------|-------------------|
| I0 | Stand up `internal/{org,schemas}/` with stable-id reference files (no real values in tracked public paths) | — | `PUBLISH-BOUNDARY.md` grep clean |
| I1 | Taxonomy capture: SEAL, LOB→Product→Team, Oracle-schema shape | B2, B3, B4 | counts match source; zero meaning edges |
| I2 | Ontology mapping + HITL for each | C2, C3, (oracle-schema-asset) | drift guard green; map summary == vocab active |
| I3 | Config-gate loader activation (`confirmed:` flag enforced) | D3 | unconfirmed source fails fast |
| I4 | DataAsset loader for Oracle (after `:Script`/`:File` constraints) | C.4 / B.7 | lineage query returns asset paths on sample |

## 5. Invariants (carried from the restructure)

1. No internal taxonomy becomes graph edges while any of its mappings is `proposed`/`rejected`.
2. No real SID / schema name / roster value is committed outside `internal/`; `config/` and
   `config/taxonomy/` reference them by stable id.
3. Precedence is applied via `config/precedence.yaml`, never hardcoded in a loader.
4. Reuse existing `relationship_vocabulary.yaml` active terms; new terms go through the gate
   with `status: planned` first (per [`../../docs/RELATIONSHIP_GUIDE.md`](../../docs/RELATIONSHIP_GUIDE.md)).

## 6. Definition of done

- SEAL, LOB→Product→Team, and Oracle-schema taxonomies captured, mapped, confirmed, and loaded
  through the config-gated flow.
- The repo can still be published by excluding `internal/` with zero confidential leakage.
- Every internal graph edge traces to a `confirmed` entry in `config/taxonomy-ontology-map.yaml`.
