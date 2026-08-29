# Source-file map — where ingestion input lands, and which file feeds which loader

<!-- anchor: front-matter -->
- **Scope:** a reference map, deliberately **NOT a module runbook** — it operates nothing
  and claims coverage of no module. It answers one question the runbooks assume you have
  already answered: *where does the input file go, and what is already there?*
- **Status:** DESCRIPTIVE — documents the working convention. **Rev 1, 2026-08-27.**
- **Classification:** Internal-Public (mechanism only — zone names, environment-variable
  names, bundled synthetic samples; no credentials, no company values, no real hostnames)
- **Audience:** anyone about to drop a file for a loader to read, anyone wondering why a
  load produced nothing, and anyone reading the bundled samples and asking what they prove
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (the SYSTEM-level cold
  start — **it owns the load sequence, this document does not**),
  `docs/design/drydocs-load-runbook.md` (one loader at a time),
  `docs/design/drydocs-core-runbook.md` (environment roots, provisioning, run logs),
  `internal/server-inventory/README.md` (the one zone that already has its own README)

<!-- anchor: purpose-scope -->
## Purpose and scope

**The gap this fills.** The best explanation of the landing-zone convention in this repo is
a module docstring — `drydocs_core/landing_zones.py`. The declared zones themselves are
readable only as scattered `acquisition:` blocks inside `config/source-registry.yaml`, and
`drydocs landing-zones` is named in exactly one place, the port prompt, which nobody reads
as operator documentation. Nothing anywhere says which bundled sample feeds which loader.
That is what this page collects.

**What this page refuses to restate.** The load sequence. It is declared once in
`drydocs.cli.CANONICAL_LOAD_SEQUENCE` and profiled into
`docs/design/drydocs-startup-refresh-runbook.md` Appendix B, pinned by
`tests/unit/test_load_sequence_surfaces.py`. A third copy would be one more surface to keep
in step, and the load runbook already records an explicit ruling against one.

<!-- anchor: where-location-is-declared -->
## 1. Location is declared in one place, and it is not a filename

Every ingested dataset in `config/source-registry.yaml` carries an `acquisition:` block:

```yaml
acquisition:
  mode: manual                       # manual | automated | db
  format: csv                        # csv | ascii | json | archive
  drop_dir: internal/server-inventory/
  drop_dir_base: repo                # repo | data_root
```

**There is no filename field, and no glob field, anywhere in the registry.** The convention
pins the **directory** and the **format**; the loader then takes what it finds. For the
server export that is `sorted(export_path.glob("*.csv"))` (`drydocs/cli_ingest.py:686`), so
any CSV in the directory is picked up in name order.

What replaces a filename convention is a **grain contract** stated in prose on the registry
row. The infrastructure export is pulled per business application, one file per
application, never merged — and that is enforced by a fixture guard
(`test_one_application_per_file_is_the_download_grain`), not by a name pattern.

Practical consequence: **do not rename a file to make it match. Put it in the right
directory in the right format, and give it a name a human can still recognize in six
months.**

<!-- anchor: two-bases -->
## 2. Two bases, and the reason there are two

`drop_dir_base` selects how `drop_dir` resolves. The choice is about surviving `git clean`,
which is the failure this convention exists to prevent.

| Base | Resolves under | Why a zone would choose it |
|---|---|---|
| `data_root` | `DRYDOCS_DATA_ROOT`, default `~/data/DryDocs` | The directory sits **outside the working tree**, so no `git clean` at any strength can reach it. This is the default choice for real source payloads. |
| `repo` | the repository root | The zone holds **tracked** files. `git clean` removes untracked files, and a tracked file is not untracked, so it survives. Legitimate ONLY when the files are actually committed. |

An in-tree zone whose files are not tracked has the protection of neither, which is the
trap `drydocs_core/landing_zones.py` documents at length.

**On this desktop** `DRYDOCS_DATA_ROOT` is set to `C:\coding\projects\data\DryDocs`, not
the `~/data/DryDocs` default. `.env` cannot set it — it is read from the environment.

<!-- anchor: declared-zones -->
## 3. The declared zones

Read them live with `drydocs landing-zones`, which prints every zone, its resolved absolute
path, and its state. `--check` exits 1 on a zone that is present but empty; `--json` gives
the machine-readable form.

| Source id | Format | Base | Directory |
|---|---|---|---|
| `controlm:deftable-xml-export` | ascii | data_root | `controlm-xml/` |
| `autosys:export` | ascii | data_root | `autosys/` |
| `airflow:dag-export` | ascii | data_root | `airflow/` |
| `seal:app-extract` | csv | data_root | `seal/` |
| `pat:product-catalog` | csv | data_root | `pat/` |
| `pat:people-report` | csv | data_root | `pat/` |
| `snow:cmdb-ci-classes` | csv | data_root | `snow/` |
| `exec-hosts:rua-bundle` | archive | data_root | `rua/` |
| `dpl:pipeline-registry` | json | data_root | `dpl/` |
| `dpl:dataset-registry` | json | data_root | `dpl/` |
| `bitbucket:repo-objects-manifest` | ascii | data_root | `bitbucket/` |
| `infra:server-export` | csv | **repo** | `internal/server-inventory/` |
| `repo:software-registry` | ascii | **repo** | `config/taxonomy/` |
| `repo:depgraph-snapshot` | json | **repo** | `knowledge/depgraph-snapshots/` |
| `repo:design-docs` | ascii | **repo** | `docs/design/` |

### Reading a zone's state

`absent` means the directory is not there. That is the healthy first state of a zone nobody
has dropped into yet, and it is also what `git clean -fd` leaves behind, so it is never
treated as a defect. `EMPTY` is the narrower and more suspicious signature — the directory
exists and holds nothing, which is what a selective delete or a half-finished restore looks
like. `--check` fails on `EMPTY`, never on `absent`.

<!-- anchor: undeclared-zones -->
## 4. Zones the code creates that the registry does not declare

`drydocs_core/data_root.py` exposes named helpers for directories with **no
`source-registry` row**, which means `drydocs landing-zones --check` cannot see them. They
are real zones with no governance, and knowing they exist is the point of listing them:

| Helper | Directory |
|---|---|
| `controlm_xml_dir()` | `controlm-xml/` (this one is also declared) |
| `email_extracts_dir()` | `email-extracts/` |
| `context_intake_dir()` | `context-intake/` |
| `vendor_docs_dir()` | `vendor-docs/<tree>/` |
| `catalog_dir()` | `catalog/` |
| `dpl_registry_dir()` | `dpl-registry/` |
| `rua_incoming_dir()` / `rua_extracted_dir()` | `rua/incoming/`, `rua/extracted/<bundle>/` |
| `remediation_incoming_dir()` and siblings | `remediation/incoming`, `outgoing`, `recommendations` |
| the cmdline staging database | `cmdline-staging/` |

Note the drift worth not tripping over: the registry says `dpl/` while the code helper says
`dpl-registry/`. Neither is wrong on its own; they simply do not agree, and nothing checks
that they do.

<!-- anchor: bundled-samples -->
## 5. The bundled samples, and which loader reads which file

The samples live at `drydocs/data/samples/` (`drydocs.cli.DEFAULT_SAMPLES_DIR`). They are
the only end-to-end demonstration available without company data.

**A tracking subtlety that has misled readers.** `.gitignore` line 33 ignores
`drydocs/data/`, and `internal/repo-README.md` describes the samples as git-ignored. Yet
thirteen files under `drydocs/data/samples/` are **tracked**, because a tracked file is
unaffected by a later ignore rule. So the samples DO arrive with a clone — but **a new file
dropped there is invisible to git by default**, and adding one takes `git add -f`.

| Sample file | Read by | Chain |
|---|---|---|
| `catalog_lobs__sample.csv` | `CatalogLOBsLoader` | `REFRESH_REFERENCE_CHAIN` |
| `product_lines__sample.csv` | `ProductLinesLoader` | `REFRESH_REFERENCE_CHAIN` |
| `products__sample.csv` | `ProductsLoader` | `REFRESH_REFERENCE_CHAIN` |
| `seal_application_data__sample.csv` | `SealApplicationsLoader` | `REFRESH_REFERENCE_CHAIN` — **file absent, see below** |
| `seal_contact_data__sample.csv` | `SealContactsLoader` | `REFRESH_REFERENCE_CHAIN` — **file absent, see below** |
| `dev_teams__sample.csv` | `DevTeamsLoader` | `REFRESH_REFERENCE_CHAIN` |
| `pat_product_mapping__sample.csv` | `PatProductMappingLoader` | `REFRESH_REFERENCE_CHAIN` |
| `controlm_folders__sample.csv` | `ControlMFoldersLoader` | `ingest-controlm`, node stages |
| `controlm_jobs__sample.csv` | `ControlMJobsLoader` | `ingest-controlm`, node stages |
| `controlm_hosts__sample.csv` | `ControlMHostsLoader` | `ingest-controlm`, node stages |
| `controlm_conditions_in__sample.csv` | conditions-in loader | `ingest-controlm` |
| `controlm_conditions_out__sample.csv` | conditions-out loader | `ingest-controlm` |
| `controlm_dependencies__sample.csv` | dependencies loader | `ingest-controlm`, relationship stages |
| `controlm_variables__sample.csv` | variable analysis and normalization | **file absent** |
| `email-extracts/*.json` | email-extract ingestion | two bundled files |

**The two SEAL samples are deliberately absent.** They were deleted in 2026-07 because they
carried real `seal_id` values. A missing sample makes the step **skip rather than fail**, so
a chain run looks clean while loading nothing — the single most operationally important
sample fact in the repo, documented in depth in the startup/refresh runbook. Regenerate
with `scripts/build_seal_samples.py` and expect `rows_rejected=5`.

Two sanitized files sit outside that directory because they belong to tests and config:

- `tests/fixtures/server_inventory/synthetic-server-export.csv` — the publishable twin of
  the real `infra:server-export` download.
- `config/taxonomy/location-gazetteer.yaml` — not a sample, but the table that turns the
  place NAMES those files carry into points on the map.

<!-- anchor: worked-example -->
## 6. Worked example: the infrastructure server export

The one zone with its own README (`internal/server-inventory/README.md`), and the clearest
illustration of every rule above.

- **Declared at** `infra:server-export` in `config/source-registry.yaml`.
- **Location** `internal/server-inventory/`, base `repo` — an in-tree zone, legitimate
  because the real exports are committed there. `internal/` is excluded from any public
  push by `PUBLISH-BOUNDARY.md`, which is what makes committing real hostnames acceptable.
- **Filename** unconstrained. The **grain** is the contract: one CSV per business
  application, carrying both that application's PROD and DR servers.
- **Loaded by** `drydocs load-server-inventory --export <file-or-directory>`, which globs
  the directory when given one, then runs the derived `server_resolution` join pass.
- **Synthetic twin** `tests/fixtures/server_inventory/synthetic-server-export.csv`.

<!-- anchor: known-gaps -->
## 7. Known gaps, recorded rather than smoothed over

1. **The bundled samples do not interlock.** Run together, the Control-M samples and the
   server-export fixture cannot join: the sample hosts and the export's server names share
   no value under the signed match tiers, the export names an application the graph does
   not carry, and its second synthetic city has no gazetteer row. The consequence is that
   the samples exercise the coverage-REPORTING path and never the success path. Recorded as
   `Idea-193` and item **Z7**.
2. **`drydocs landing-zones` is missing from the CLI reference** in
   `internal/repo-README.md`, which lists every other verb.
3. **`.env.example` documents neither `DRYDOCS_DATA_ROOT` nor `DRYDOCS_LOGDIR`**, so a new
   machine has to discover both from code or from this page.
4. **The undeclared zones in section 4 are invisible to `--check`.** Nothing is broken by
   that today; it means only that the guard's coverage is narrower than it appears.
