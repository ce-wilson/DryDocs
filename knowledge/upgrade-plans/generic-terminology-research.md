# Generic terminology research — replacing SEAL/PAT with industry-standard, SaaS-configurable naming

**Classification:** Internal-Public (SYNTHESIZED — industry terminology research with public
citations; no company data. "SEAL"/"PAT" appear as system names only, the repo-wide norm.)
**Captured:** 2026-07-20 (user request, in-session; web research same day).
**Status:** RESEARCH — decision-support for a future ADR. Nothing here renames anything.

## The ask

DryDocs today names two company source systems throughout its config, vocabulary domains,
and prose: **SEAL** (the business-application registry) and **PAT** (the product catalog /
product-team hierarchy). For the standalone/SaaS generalization goal ("pick your
orchestrator, get a scaffolded support graph" — the 2026-07-17 scaffold research), those
names must become **industry-standard concepts** with the company names demoted to
**tenant-configurable display/source labels**.

## What the industry calls these two things

### 1. The SEAL side — the business-application registry

| Term | Who standardizes it | Notes for DryDocs |
|---|---|---|
| **Business Application** | ServiceNow CSDM (`cmdb_ci_business_app`) — "software used by business users to perform a business function or support a business capability"; the foundation table of APM | **Already our node label** (:BusinessApplication, K4 2026-07-15) — independently validated; keep |
| **Application Portfolio** / **Application Portfolio Management (APM)** | ServiceNow APM; LeanIX; Gartner discipline name | The natural name for the *registry/collection* — "Application Portfolio" for the source-system concept |
| Application inventory / registry | generic EA usage | plainer synonym; weaker brand recognition than APM |
| **Business Capability** (taxonomy) | TOGAF / LeanIX — "an ordered hierarchy of business capabilities" | adjacent concept CSDM ties apps to; a future modeling candidate, not a SEAL rename |

**Candidate:** concept = *Business Application*; registry concept = **Application
Portfolio** (registry/APM sense). "SEAL" becomes the tenant's configured name for their
Application Portfolio source.

### 2. The PAT side — the product catalog / hierarchy

| Term | Who standardizes it | Notes for DryDocs |
|---|---|---|
| **Product Taxonomy** | product-operating-model literature (IT Revolution: "define your product taxonomy first" — the hierarchy of products and capabilities in a business area) | closest match for what PAT *is*: LOB ▸ ProductLine ▸ Product ▸ AreaProduct ▸ DevTeam |
| **Product Portfolio** | SAFe Lean Portfolio Management; Deloitte/Planview product operating model | the top-of-hierarchy collection sense |
| **Product Operating Model** | Deloitte, Planview, Marty Cagan lineage | the org philosophy, not the catalog artifact — context term, not a rename target |
| SAFe hierarchy (Portfolio → Solution/Value Stream → ART → Team) | Scaled Agile | maps loosely (AreaProduct ≈ ART/"team of teams"); framework-specific — avoid baking SAFe words into the schema |
| ITIL Service/Product Catalog | ITIL 4 / CSDM service layer | "catalog" collides with our existing `catalog` vocab domain (which is generic already) — usable but check the collision |

**Candidate:** concept = **Product Taxonomy** (the hierarchy) inside a **Product
Portfolio** (the collection). "PAT" becomes the tenant's configured name for their
Product Taxonomy source. Our existing generic labels (Product, AreaProduct, DevTeam,
CatalogLOB, ProductLine) already fit; AreaProduct is the least standard term (PAT-ism —
industry says "team of teams" / ART; candidate for a display-name override rather than a
label rename).

### 3. The SaaS-configurability pattern

The canonical precedent is **Salesforce "Rename Tabs and Labels"**: standard objects keep
stable internal API names; tenants rename the *labels* to their own vocabulary ("you may
say customer or client"). The pattern for DryDocs:

- **Canonical concept ids never change** — node labels, vocab ids, anchors stay the
  industry-standard generic terms (the schema is the "API name" layer).
- **Display names + source-system names are config** — a per-tenant/per-deployment
  mapping in `config/` (the source-registry already names sources; extend with
  `display_name` / `system_of_record_name` fields), rendered wherever prose/UI says
  "SEAL"/"PAT" today. The web console (Epic O — O12 admin config page, O13 stewardship)
  is the natural rendering surface.
- **The K4 precedent proves the hard half is done once**: :Application →
  :BusinessApplication was a one-time schema rename through a gate; after this item,
  future tenants never need one — they configure a label instead.

## Known SEAL/PAT-specific surfaces (first inventory = step 1 of the eventual item)

Vocabulary domain `seal` + `seal_*` vocab ids; the `SEALID` identity property; source ids
`seal-extract` / `catalog-pat`; precedence authorities (`seal-pat`, `lob-product-team`);
`pat_product_mapping` loader naming; TOMRole prose ("SEAL Technical Operating Model");
docs/skills prose throughout. A full grep inventory with a keep/rename/config-label
disposition per surface is the first acceptance-testable step.

## Decision surface (why this parks, not promotes, today)

1. **Scope:** display-label config only (Salesforce pattern, cheap) vs also renaming
   vocab ids/domains (`seal_*` → `app_portfolio_*`?, churn + port impact) — an ADR-scale
   terminology decision (the ADR 0004 software-registry precedent).
2. **Placement:** productization/generalization has no epic or phase — promoting this is
   a **plan change** (new epic proposal), which the groom rule routes to the user.
3. **Identity property:** `SEALID` → generic (`app_id`? CSDM has no portable id name) —
   touches loaders + constraints; needs the same gate discipline as any identity change.

## Sources

- ServiceNow CSDM Business Application definition: https://www.servicenow.com/community/common-service-data-model-forum/what-is-the-correct-definition-of-quot-business-application-quot/td-p/2845942
- ServiceNow APM ↔ CSDM tables: https://www.servicenow.com/docs/r/washingtondc/application-portfolio-management/apm-use-case.html
- CSDM explained (business apps vs technical services): https://plat4mation.com/blog/the-common-service-data-model-explained-aligning-it-to-business-strategy/
- LeanIX EA glossary (application portfolio, business capability taxonomy): https://www.leanix.net/en/blog/enterprise-architecture-terms-to-know-glossary
- LeanIX on TOGAF application architecture: https://www.leanix.net/en/wiki/ea/togaf
- IT Revolution — Product Taxonomy (seven domains of transformation): https://itrevolution.com/articles/product-taxonomy-the-seven-domains-of-transformation/
- SAFe hierarchy levels: https://www.enov8.com/blog/the-hierarchy-of-safe-scaled-agile-framework-explained/
- Deloitte product operating model framework: https://www.deloitte.com/us/en/services/consulting/articles/product-operating-model-framework.html
- Salesforce Rename Standard Objects (the tenant-label pattern): https://help.salesforce.com/s/articleView?id=sf.cg_task_rename_standard_object_labels.htm&language=en_US&type=5
- Salesforce rename considerations: https://help.salesforce.com/s/articleView?id=platform.customize_rename_considerations.htm&language=en_US&type=5
