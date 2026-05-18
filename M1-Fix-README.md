# DryDocs — M1 SEAL fix + schema upgrade

Two things in this pack:

1. **Fixes the `ModuleNotFoundError: No module named 'drydocs.models.seal'`** you hit when applying the M3 updates. That error is because `drydocs/models/seal.py` (and probably `catalog.py` too) didn't make it into your project — the M3 pack overwrote `models/__init__.py` but didn't include the M1 model files.

2. **Aligns SEAL to the real schema you uploaded** — the real `PSGMGR.DECO_SEAL_APP_INFO` column list, the SEAL framework role vocabulary, and the three contacts embedded directly on each app row (Application Owner, CTO, Primary Information Owner).

## Drop-in mapping

```
drydocs_m1_seal_fix/                                  C:\coding\projects\DryDocs\
├── drydocs/
│   ├── models/
│   │   ├── seal.py                                   drydocs/models/seal.py             (NEW — was missing)
│   │   ├── catalog.py                                drydocs/models/catalog.py          (NEW — was probably missing)
│   │   └── __init__.py                               drydocs/models/__init__.py         (overwrites)
│   ├── loaders/cypher/
│   │   ├── seal_applications.cypher                  drydocs/loaders/cypher/...         (overwrites)
│   │   └── seal_contacts.cypher                      drydocs/loaders/cypher/...         (overwrites)
│   └── schema/
│       └── m1_role_vocabulary_update.cypher          drydocs/schema/...                 (new)
├── data/samples/
│   ├── seal_application_data__sample.csv             data/samples/...                   (overwrites)
│   └── seal_contact_data__sample.csv                 data/samples/...                   (overwrites)
└── README.md
```

`models/__init__.py` is a superset — it exports SEAL + catalog + Control-M models, matching the M3 pack. Safe to overwrite the M3 version.

## Apply

```powershell
# 1. Copy files per the table above.

# 2. Apply the role-vocabulary upgrade against Neo4j.
poetry run drydocs apply-m3-supplement   # the existing M3 supplement script

# 3. Apply the role rename / additions specifically.
# Easiest: extend apply-m3-supplement to also run m1_role_vocabulary_update.cypher
# (see "CLI tweak" below). Or run it manually via cypher-shell:
#
#     Get-Content drydocs\schema\m1_role_vocabulary_update.cypher | cypher-shell

# 4. Run M0 verify + M1 sample load to confirm.
poetry run drydocs check
poetry run drydocs refresh-reference --samples-dir data/samples
poetry run drydocs m1-verify
```

### CLI tweak (optional but recommended)

Open `drydocs/cli.py` and find this block near the top of `apply-m3-supplement`:

```python
M3_SUPPLEMENT_FILE = SCHEMA_DIR / "m3_ontology_supplement.cypher"
M3_CONSTRAINTS_UPGRADE = SCHEMA_DIR / "m3_constraints_upgrade.cypher"
```

Add:

```python
M1_ROLE_VOCAB_UPGRADE = SCHEMA_DIR / "m1_role_vocabulary_update.cypher"
```

Then in the body of `apply_m3_supplement`, after the existing two `execute_file` calls, add:

```python
if M1_ROLE_VOCAB_UPGRADE.exists():
    cli.execute_file(M1_ROLE_VOCAB_UPGRADE)
    console.print("[green]Role vocabulary aligned to SEAL spec.[/]")
```

## What the new SEAL model captures

`SealApplicationRow` is now locked to the real `PSGMGR.DECO_SEAL_APP_INFO` column list — projects down from ~90 source columns to ~50 fields covering:

- **Identity**: `app_id`, `name`, `app_short_name`, `description`
- **Lifecycle**: `app_state`, planned/actual build/operate/decom/retirement dates, `replacement_app_type`, `retirement_type`
- **Org context**: `app_lob`, `reporting_cio_lob`, `reporting_cto_group`, `tech_group_owner` + `tech_group_owner_id`
- **Risk + compliance**: `overall_risk_rating`, `sox_reportable`, `glba_reportable`, `pci_reportable`, `soc1_reportable`, `info_classification`, `personal_info`, `sensitive_personal_info`, `phi`, `mnpi`, `strictest_rpo`, `strictest_rto`
- **Hosting + platform**: `hosting_vendor`, `overall_hosting_type`, `platforms`, `kapp`, `programming_languages`, `app_dev_responsibility`
- **Authentication + network**: `authentication_type`, `authorization_type`, network connectivity flags
- **Embedded contacts (3)**: `app_owner_sid`/`_name`, `chief_tech_officer_sid`/`_name`, `info_owner_sid`/`_name`
- **Audit**: `capture_date`, `certification_status`, `last_certified_*`, `data_integrity`

All fields except `app_id` and `name` are optional. Pydantic `extra="ignore"` means the model tolerates either direction of drift — missing optional columns are fine, extra source columns are silently dropped.

## What the new role vocabulary looks like

Per `seal-overview-with-roles.txt`. **Mandatory application-level roles** (from SEAL framework spec):

| Role | What changed |
|---|---|
| Application Owner | **Renamed** from `App Owner` to match SEAL spec |
| Primary Information Owner | **Renamed** from `Data Owner` to match SEAL spec |
| Backup Information Owner | **Added** |
| CTO | Unchanged |
| Design Authority | **Added** |
| Chief Business Technologist | **Added** |

**Optional operational roles** (set by production support teams):

| Role | What changed |
|---|---|
| L1 Operate Manager | **Added** |
| L2 Operate Manager | Unchanged (drives the §F.4 support-team derivation) |
| Backup Application Owner | **Added** (effective 2026-05-18) |
| Risk Manager | Kept — user-confirmed, not in published SEAL spec |

**PAT roles** (Agility Lead / Software Engineer / Product Contact) — unchanged.

The Cypher upgrade renames existing nodes in-place (preserving incoming `:OF_ROLE` edges) rather than creating new ones, so any pre-existing Memberships pointing at `App Owner` / `Data Owner` continue to resolve correctly after the rename.

## How the SEAL contact loading works now

DECO_SEAL_APP_INFO has three contacts embedded on each application row (App Owner, CTO, Information Owner). The `seal_applications.cypher` loader now **splays those three into Memberships directly** while loading the app — no separate file needed.

For the other roles (BIO, Design Authority, CBT, L1/L2 Operate Manager, BAO, Risk Manager), you'll still need a separate SEAL Contact extract — long format, one row per (app_id, role_name, employee_sid). The `seal_contacts.cypher` loader handles that.

Date columns from DECO (`9-Jan-26`, `24-Aug-12`) come through as strings on the row model — no Python-side date parsing, kept as-is on the graph node. Add a date-coercer at the model layer if a query needs `WHERE ad < date('2024-01-01')` semantics; for inventory dashboards, string compares against ISO equivalents work fine.

## What I still need from you to fully close M1

1. **Confirm `DECO_SEAL_APP_INFO` IS the SEAL Application Data extract** (column list matches in this pack). If your team is pulling from a different SEAL view, drop the DDL and I'll align.
2. **Confirm the SEAL Contact Data extract shape** — does it actually arrive as long format (one row per (app_id, role, employee))? If wide-format (one row per app with multiple role columns), I'll add a splayer to `seal_contacts.py` upstream of the Cypher.
3. **Risk Manager origin** — you originally listed it as a SEAL role. It's not in the published SEAL framework spec — is it set via a custom SEAL field, a ServiceNow attribute, or some other system? Knowing that lets me put a `source` property on the Membership.

## Why this file pack is "M1" not "M3"

These changes target the SEAL portion of the M1 pack — `seal_applications`, `seal_contacts`, the SEAL row models, and the SEAL roles seeded by the M0 ontology backbone. Everything in M3 (folders, jobs, conditions, dependencies) is untouched.
