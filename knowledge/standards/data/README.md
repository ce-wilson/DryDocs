# standards/data/ — data-platform standards (placeholder)

**Domain:** `data`. **Authority:** `internal-standards` (config/precedence.yaml, tier 2).

Standards that govern the **Data** taxonomy: Oracle/Snowflake schema, table, and dataset
naming; data-product conventions; source-of-record designation rules. These refine how data
assets are classified and named here.

No standards captured yet. When adding one, use a `taxonomy_path` like:
- `data/oracle/schema` — schema/owner naming rules
- `data/oracle/schema/table` — table naming + dataset mapping rules
- `data/dataset` — DataAsset URN / namespace conventions

Follow the frontmatter format in [`../README.md`](../README.md). This domain feeds the
Oracle-schema taxonomy capture (backlog **B4**) and the `DataAsset` model in the
[internal-import upgrade plan](../../upgrade-plans/internal-import.md).

> Real schema/table/object names are **confidential** — they live in `internal/schemas/`,
> referenced here by stable id, never inlined.
