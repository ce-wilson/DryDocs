# Internal — database inventory: the `{db}` slot of the source-registry id grammar (REAL values)

**classification: Internal** — excluded from any public push per [`PUBLISH-BOUNDARY.md`](../../../PUBLISH-BOUNDARY.md).

Home for the real database names that `config/source-registry.yaml` deliberately writes as
`[db]`. Created 2026-08-25, and the reason it did not exist before is worth stating: the
redaction has been in place since the N9 build on 2026-07-31 and **nothing recorded what was
being redacted**, so the placeholder had no key. Ten shipped ids carry `[db]` today. A
redaction whose real value lives only in somebody's shell profile is not a boundary control,
it is a gap that happens to look like one — the same defect
[`data-center-inventory.md`](data-center-inventory.md) was created to close for the `P`→`T`
environment-letter swap.

## The grammar, and where the placeholder is enforced

Gate `source-registry-v2` (N7, signed 2026-07-31) ruled the replica id shape at Q1:

```
{origin}@{db}.{schema}.{table}
```

The **database is redacted, the schema and table are published** — that is J13 class 3, ruled
2026-08-11: *"NO SWEEP OWED — already covered by the SIGNED N9 source-registry-v2 id grammar,
which redacts the database and publishes schema.table."* The literal `[db]` string is pinned in
[`tests/unit/test_source_registry.py`](../../../tests/unit/test_source_registry.py), so changing
it is a coordinated change across the registry, the retired-id `replaced_by` lists and that
guard — never an edit to one row.

## The values

| Placeholder in the registry | Real value | What it is |
|---|---|---|
| `[db]` in every `*@[db].psgmgr.*` id | **`SPIDERP`** | the Oracle database holding the `psgmgr` schema — the read-only `CM_`-prefixed Control-M replica, plus `hr_phone_exp` and `cm_escalation_db` |
| `[db]` in `controlm@[db].drydocs_stg.stg_app_fact` | **`SPIDERP`** | same database; `drydocs_stg` is the staging schema, not a separate instance |
| `[db]` / `[schema]` in the two `catalog@[db].[schema].*` rows | **not yet known** | Snowflake data-catalog placeholders; the gate prompt is undrafted, so these are unresolved rather than redacted |

`SPIDERP` is a **database name**, not a SID in the instance sense, and it resolves **only via
`tnsnames`** — a thin-mode driver connection will not find it. That fact is already recorded
publishably in the `reconcile-port` skill because it is a connection MECHANISM; the value's home
is here.

## The ten ids this table is the key to

All in the `psgmgr` schema: `cm_def_vtab`, `cm_def_vjob`, `cm_def_lnki_p_vw`,
`cm_def_lnko_p_vw`, `cm_def_setvar_vw`, `cm_hosts`, `cm_avg_run`, `cm_hist_vw` (all
`controlm@`), `hr_phone_exp` (`hr@`), and `cm_escalation_db` (`seal@` — origin under review,
see the row's own notes).

## OPEN — one inconsistency for the SME, not swept here

**The same token is published as an environment-variable prefix while being redacted as a
database name.** `SPIDERP_LOGDIR` appears in tracked, publishable files — `.env.example`,
[`docs/decisions/0014-runtime-substrate.md`](../../../docs/decisions/0014-runtime-substrate.md),
the `run-drydocs` skill — as the deprecated alias for `DRYDOCS_LOGDIR`, and the `reconcile-port`
skill names `SPIDERP` directly in its tnsnames caution. So the value the id grammar removes is
sitting in four other tracked files under a different job.

Either the redaction is doing less than it appears to, or the env prefix and the skill mention
should be swept the way the data-center codes were at J13 class 2. **This is the SME's ruling,
exactly as the four J13 value classes were**, and it is recorded rather than acted on because
the honest options differ in cost: ADR 0014 already deprecates `SPIDERP_*` on both log families
for one cycle, so the env prefix has a scheduled death and may need nothing; the skill mention is
a connection mechanism that loses its point if generalized.

Do not resolve this by editing the registry. The `[db]` placeholder is signed-gate output and
guard-pinned; whatever is ruled about the env prefix leaves the id grammar alone.
