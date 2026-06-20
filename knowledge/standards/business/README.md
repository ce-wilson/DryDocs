# standards/business/ — org taxonomy standards (placeholder)

**Domain:** `business`. **Authority:** `lob-product-team` (config/precedence.yaml, tier 3).

Standards that govern the **Business** taxonomy: LOB → Product → Team naming, ownership
assignment rules, segment reconciliation conventions. These attach *context and ownership*;
they do not redefine orchestration objects.

No standards captured yet. When adding one, use a `taxonomy_path` like:
- `business/lob` — line-of-business code rules
- `business/lob/product` — product naming/registry rules
- `business/lob/product/team` — DevTeam / AreaProduct alignment rules

Follow the frontmatter format in [`../README.md`](../README.md). Candidate first standard:
the LOB-code registry that resolves position 2 of the folder-naming convention
(`R` = CCB Retail, `C` = …) — currently an open item in
[`../technology/folder-naming-convention.md`](../technology/folder-naming-convention.md).
