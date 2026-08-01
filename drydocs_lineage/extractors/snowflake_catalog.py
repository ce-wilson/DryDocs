"""Snowflake data-catalog ingestion seam (G42) — the dataset/distribution
registration views, taxonomy-first.

The catalog is the company's dataset registration system, exposed as two
curated Snowflake views (``<CATALOG>_DATASETS_V`` — one row per logical
dataset; ``<CATALOG>_DISTRIBUTIONS_V`` — one row per physical materialization
on a platform). It is the FOURTH registry seam (beside G17 MAC / G25 DPL
registry / G41 Glue inventory) and the closest thing to the target inventory
already assembled: dataset + producing app id + contact + physical
coordinates. Full plan: ``docs/generic-snowflake-data-catalog-ingestion-plan.md``
(the mapping ledger for the ``snowflake-data-catalog`` source entry).

This module stages FLAT RECORDS ONLY — no graph parameter exists anywhere in
its API. Node/edge shape (one node or two, ``HAS_DISTRIBUTION``, attribution,
contact, publisher→org) is entirely the gate's to rule (plan §5); the
cross-check reports are G43's.

ASSUMED FIELD CONTRACT (defined by the SYNTHETIC fixtures, adjust when a real
sample validates it — the dpl_mac discipline):

- Exports are CSV, one file per view, header row = the view's column names
  (JSON exports wait for a real sample to pin their shape). A file is
  recognized by its header: ``DISTRIBUTION_IDENTIFIER`` present → the
  distributions view; else ``DATASET_IDENTIFIER`` present → the datasets
  view; neither → counted invalid.
- The datasets view is a ``UNION ALL`` over catalog + event tables (DDL
  observation), so the same GUID can appear more than once — staging keeps
  the LATEST row per GUID (by ``TIMESTAMP``; two formats observed, ISO-ish
  and ``DD-MON-YYYY HH:MM:SS``) and counts every duplicate; an unparseable
  timestamp is counted and loses to any parseable one. The same rule guards
  the distributions view (keyed by distribution GUID).
- Distributions carry a sparse union of three physical shapes — exactly one
  populated per row: **table** (Snowflake / Teradata / Glue external),
  **file** (HDFS), **s3**. Zero shapes → staged ``shape=""`` and counted;
  more than one → also ``""``, counted separately (contract violation, never
  guessed).
- The literal sentinel ``NOT INSTRUMENTED`` (observed in
  ``LOGICALDATABASE_NAME`` / ``FILE_SYSTEM_NAME``) is nulled AND counted
  wherever it appears — instrumentation coverage is itself a finding.

ORIGIN (identity routing, plan §3 — the G41 never-join rule applied):

- ``REGISTRATION_SOURCE_SYSTEMNAME = DPL`` → origin ``dpl``: the
  ``REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER`` is the DPL dataset GUID,
  so the row lands on the same ``dpl_dataset`` identity G17/G25/G41 stage.
- Any OTHER non-empty registration authority → origin ``authority2`` (the
  generic non-DPL bucket; the verbatim system name travels in
  ``registration_source`` for the census). Its ids NEVER join DPL GUID space.
- Empty/null → origin ``catalog``: the row keys on the catalog's own
  ``DATASET_IDENTIFIER``. Cross-authority unification is a gate ruling
  (plan §5b), never decided here.

``candidate_asset_urn`` is a FACT COLUMN, not an identity ruling:
``urn:drydocs:dataasset:{platform}:{namespace}:{name}`` lowercased —
platform from ``DATATECHNOLOGY_NAME``/shape, namespace from db(.schema) /
directory / bucket, name from table / file / s3 asset. Table-shape rows
without a schema yield the G41-style ``db`` namespace so Glue placements
join on the same canonical lowercase path (G43's join). Any missing part →
``""`` and counted.

Real exports are confidential (Internal, J23) and live in the G19 landing zone
(``catalog/``, resolver ``drydocs_core.data_root.catalog_dir``), never in
the repo; ``tests/unit/test_data_root.py`` sweeps the tree for strays.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

#: the instrumentation sentinel — nulled AND counted wherever it appears
NOT_INSTRUMENTED = "NOT INSTRUMENTED"

#: the staged origin vocabulary (plan §3)
ORIGINS = ("dpl", "authority2", "catalog")


def _norm_header(raw: str) -> str:
    return "".join(c for c in raw.lower() if c.isalnum())


def _parse_ts(raw: str) -> datetime | None:
    """The two observed timestamp formats (the view COALESCEs audit dates in
    both); anything else → None, which the caller counts."""
    s = raw.strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace(" ", "T", 1))
    except ValueError:
        try:
            dt = datetime.strptime(s, "%d-%b-%Y %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _origin(registration_source: str) -> str:
    norm = registration_source.strip().lower()
    if not norm:
        return "catalog"
    return "dpl" if norm == "dpl" else "authority2"


@dataclass(frozen=True)
class CatalogDatasetRecord:
    """One logical dataset, taxonomy-first: classification facts +
    provenance, no meaning."""

    guid: str  # DATASET_IDENTIFIER — the identity key
    name: str = ""
    business_name: str = ""
    description: str = ""
    publisher: str = ""  # org/product line — taxonomy fact (§5f)
    producedby_app_id: str = ""  # SEAL-shaped bridge key — fact, not edge (§5c)
    contact_email: str = ""  # routes to the email-dl-contact-point gate (§5d)
    registration_source: str = ""  # verbatim upstream authority name
    registration_source_ref: str = ""  # foreign key into that authority (DPL rows: the DPL GUID)
    origin: str = "catalog"  # dpl | authority2 | catalog (§3)
    timestamp: str = ""  # audit time, verbatim (latest-per-GUID already applied)
    source_file: str = ""  # provenance: which export staged this record


@dataclass(frozen=True)
class CatalogDistributionRecord:
    """One physical materialization of a dataset on a platform."""

    dataset_guid: str  # parent DATASET_IDENTIFIER ("" counted)
    distribution_guid: str  # DISTRIBUTION_IDENTIFIER — the identity key
    name: str = ""  # platform-prefixed — cross-check only, never extraction
    shape: str = ""  # "table" | "file" | "s3" | "" (unresolved/ambiguous — counted)
    platform: str = ""
    namespace: str = ""  # db(.schema) / directory / bucket, lowercase
    asset_name: str = ""  # table / file / s3 asset
    storage_uri: str = ""  # the shape's resource URI (jdbc:/hdfs:/s3a:)
    candidate_asset_urn: str = ""  # FACT column only — never an identity ruling
    consumable: str = ""  # CONSUMABLE_INDICATOR, verbatim (lifecycle is layer-4, §5e)
    publication_mode: str = ""
    registration_source: str = ""
    registration_source_ref: str = ""
    registration_source_parent_ref: str = ""
    description: str = ""
    timestamp: str = ""
    source_file: str = ""


@dataclass
class CatalogCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent."""

    files_read: int = 0
    files_invalid: int = 0  # unreadable / header names neither view
    rows_read: int = 0
    rows_no_guid: int = 0  # missing the view's identity column — skipped
    datasets_staged: int = 0  # unique dataset GUIDs after dedup
    distributions_staged: int = 0  # unique distribution GUIDs after dedup
    duplicate_datasets: int = 0  # union dupes — latest-per-GUID wins
    duplicate_distributions: int = 0
    distributions_no_dataset: int = 0  # distribution row without a parent GUID — staged, counted
    shape_unresolved: int = 0  # no physical shape populated — staged ""
    shape_ambiguous: int = 0  # >1 shape populated (contract violation) — staged ""
    sentinel_not_instrumented: int = 0  # NOT INSTRUMENTED occurrences nulled
    timestamp_unparsed: int = 0  # neither observed format — loses dedup ties
    urn_underived: int = 0  # distribution without a full urn triple
    origin_dpl: int = 0  # census over the staged (deduped) datasets
    origin_authority2: int = 0
    origin_catalog: int = 0

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"files={self.files_read} rows={self.rows_read} "
            f"datasets={self.datasets_staged} "
            f"distributions={self.distributions_staged} | origin: "
            f"dpl={self.origin_dpl} authority2={self.origin_authority2} "
            f"catalog={self.origin_catalog} | dupes: "
            f"datasets={self.duplicate_datasets} "
            f"distributions={self.duplicate_distributions} | "
            f"shape: unresolved={self.shape_unresolved} "
            f"ambiguous={self.shape_ambiguous} | "
            f"sentinel={self.sentinel_not_instrumented} "
            f"urn_underived={self.urn_underived} | skipped: "
            f"invalid_files={self.files_invalid} no_guid={self.rows_no_guid} "
            f"no_dataset={self.distributions_no_dataset} "
            f"ts_unparsed={self.timestamp_unparsed}"
        )


@dataclass
class CatalogExtract:
    """The staged catalog: flat records + the run's coverage."""

    datasets: list[CatalogDatasetRecord] = field(default_factory=list)
    distributions: list[CatalogDistributionRecord] = field(default_factory=list)
    coverage: CatalogCoverage = field(default_factory=CatalogCoverage)

    def dataset_guids(self) -> set[str]:
        return {r.guid for r in self.datasets}

    def dpl_refs(self) -> set[str]:
        """The DPL-GUID join keys (origin ``dpl`` rows' upstream refs) —
        what G43's registry cross-check consumes."""
        return {
            r.registration_source_ref
            for r in self.datasets
            if r.origin == "dpl" and r.registration_source_ref
        }


class SnowflakeCatalogExtractor:
    """View exports → taxonomy-first staging records (no graph, no edges —
    the snowflake-data-catalog gate owns everything the facts could mean)."""

    name = "snowflake-data-catalog"

    def extract(self, source: str | Path) -> CatalogExtract:
        """``source`` is the catalog landing zone (``catalog/``) or a single
        export file. Returns the staged :class:`CatalogExtract`; callers
        report its coverage."""
        root = Path(source)
        files = sorted(root.glob("*.csv")) if root.is_dir() else [root]
        result = CatalogExtract()
        datasets: dict[str, tuple[datetime | None, CatalogDatasetRecord]] = {}
        dists: dict[str, tuple[datetime | None, CatalogDistributionRecord]] = {}
        for path in files:
            self._read_file(path, result.coverage, datasets, dists)
        result.datasets = [rec for _, rec in datasets.values()]
        result.distributions = [rec for _, rec in dists.values()]
        coverage = result.coverage
        coverage.datasets_staged = len(result.datasets)
        coverage.distributions_staged = len(result.distributions)
        for rec in result.datasets:
            if rec.origin == "dpl":
                coverage.origin_dpl += 1
            elif rec.origin == "authority2":
                coverage.origin_authority2 += 1
            else:
                coverage.origin_catalog += 1
        return result

    # -- one export file -----------------------------------------------------
    def _read_file(
        self,
        path: Path,
        coverage: CatalogCoverage,
        datasets: dict[str, tuple[datetime | None, CatalogDatasetRecord]],
        dists: dict[str, tuple[datetime | None, CatalogDistributionRecord]],
    ) -> None:
        try:
            with path.open(encoding="utf-8-sig", newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                if header is None:
                    coverage.files_invalid += 1
                    return
                cols = {_norm_header(h): i for i, h in enumerate(header) if h.strip()}
                # header decides the view — DISTRIBUTION_IDENTIFIER wins
                # because the distributions view ALSO carries the parent
                # DATASET_IDENTIFIER column
                if "distributionidentifier" in cols:
                    stage = self._stage_distribution_row
                    staged = dists
                elif "datasetidentifier" in cols:
                    stage = self._stage_dataset_row
                    staged = datasets
                else:
                    coverage.files_invalid += 1
                    return
                coverage.files_read += 1
                for raw in reader:
                    if not any(cell.strip() for cell in raw):
                        continue
                    coverage.rows_read += 1
                    stage(raw, cols, path, coverage, staged)
        except OSError:
            coverage.files_invalid += 1

    @staticmethod
    def _cell_reader(raw: list[str], cols: dict[str, int], coverage: CatalogCoverage):
        """Returns a cell getter that NULLS the sentinel; counting happens
        once per row in :meth:`_count_sentinels` (eager, whole row) so an
        occurrence in a column the shape branch never reads still counts —
        instrumentation coverage is itself a finding."""

        def cell(key: str) -> str:
            idx = cols.get(key)
            if idx is None or idx >= len(raw):
                return ""
            value = raw[idx].strip()
            return "" if value.upper() == NOT_INSTRUMENTED else value

        return cell

    @staticmethod
    def _count_sentinels(raw: list[str], coverage: CatalogCoverage) -> None:
        coverage.sentinel_not_instrumented += sum(
            1 for value in raw if value.strip().upper() == NOT_INSTRUMENTED
        )

    def _timestamp(self, raw_ts: str, coverage: CatalogCoverage) -> datetime | None:
        ts = _parse_ts(raw_ts)
        if raw_ts.strip() and ts is None:
            coverage.timestamp_unparsed += 1
        return ts

    @staticmethod
    def _keep_latest(staged, key, ts, record, dupe_bump) -> None:
        prev = staged.get(key)
        if prev is None:
            staged[key] = (ts, record)
            return
        dupe_bump()
        prev_ts = prev[0]
        if ts is not None and (prev_ts is None or ts > prev_ts):
            staged[key] = (ts, record)

    # -- datasets view ---------------------------------------------------------
    def _stage_dataset_row(
        self,
        raw: list[str],
        cols: dict[str, int],
        path: Path,
        coverage: CatalogCoverage,
        staged: dict[str, tuple[datetime | None, CatalogDatasetRecord]],
    ) -> None:
        self._count_sentinels(raw, coverage)
        cell = self._cell_reader(raw, cols, coverage)
        guid = cell("datasetidentifier")
        if not guid:
            coverage.rows_no_guid += 1
            return
        registration_source = cell("registrationsourcesystemname")
        raw_ts = cell("timestamp")
        record = CatalogDatasetRecord(
            guid=guid,
            name=cell("datasetname"),
            business_name=cell("datasetbusinessname"),
            description=cell("businessdescriptiontext"),
            publisher=cell("publishercompanyname"),
            producedby_app_id=cell("producedbyapplicationidentifier"),
            contact_email=cell("emailaddresstext"),
            registration_source=registration_source,
            registration_source_ref=cell("registrationsourcesystemdataassetidentifier"),
            origin=_origin(registration_source),
            timestamp=raw_ts,
            source_file=path.as_posix(),
        )
        ts = self._timestamp(raw_ts, coverage)

        def bump() -> None:
            coverage.duplicate_datasets += 1

        self._keep_latest(staged, guid, ts, record, bump)

    # -- distributions view ------------------------------------------------------
    #: shape → (platform resolver key, namespace parts, asset key, uri key)
    def _stage_distribution_row(
        self,
        raw: list[str],
        cols: dict[str, int],
        path: Path,
        coverage: CatalogCoverage,
        staged: dict[str, tuple[datetime | None, CatalogDistributionRecord]],
    ) -> None:
        self._count_sentinels(raw, coverage)
        cell = self._cell_reader(raw, cols, coverage)
        dist_guid = cell("distributionidentifier")
        if not dist_guid:
            coverage.rows_no_guid += 1
            return
        dataset_guid = cell("datasetidentifier")
        if not dataset_guid:
            coverage.distributions_no_dataset += 1

        shape, platform, namespace, asset, uri = self._resolve_shape(cell, coverage)
        if platform and namespace and asset:
            urn = f"urn:drydocs:dataasset:{platform}:{namespace}:{asset}".lower()
        else:
            urn = ""
            coverage.urn_underived += 1

        raw_ts = cell("timestamp") or cell("updatedate")
        record = CatalogDistributionRecord(
            dataset_guid=dataset_guid,
            distribution_guid=dist_guid,
            name=cell("distributionname"),
            shape=shape,
            platform=platform,
            namespace=namespace,
            asset_name=asset,
            storage_uri=uri,
            candidate_asset_urn=urn,
            consumable=cell("consumableindicator"),
            publication_mode=cell("publicationmodetext"),
            registration_source=cell("registrationsourcesystemname"),
            registration_source_ref=cell("registrationsourcesystemdataassetidentifier"),
            registration_source_parent_ref=cell("registrationsourceparentdataassetidentifier"),
            description=cell("tabledescriptiontext"),
            timestamp=raw_ts,
            source_file=path.as_posix(),
        )
        ts = self._timestamp(raw_ts, coverage)

        def bump() -> None:
            coverage.duplicate_distributions += 1

        self._keep_latest(staged, dist_guid, ts, record, bump)

    @staticmethod
    def _resolve_shape(cell, coverage: CatalogCoverage):
        """The sparse three-shape union: exactly one populated per row, or
        the row is counted (unresolved / ambiguous) and staged shapeless —
        never guessed."""
        table_name = cell("tablename")
        file_name = cell("filename")
        s3_bucket = cell("s3bucketname")
        s3_asset = cell("s3dataassetname")

        populated = [
            name
            for name, hit in (
                ("table", bool(table_name)),
                ("file", bool(file_name)),
                ("s3", bool(s3_bucket or s3_asset)),
            )
            if hit
        ]
        if len(populated) != 1:
            if populated:
                coverage.shape_ambiguous += 1
            else:
                coverage.shape_unresolved += 1
            return "", "", "", "", ""

        shape = populated[0]
        if shape == "table":
            db = cell("logicaldatabasename") or cell("databasename")
            schema = cell("databaseschemaname")
            # no schema → the G41 canonical db namespace, so Glue external
            # tables join the placements G41 already staged on db.table
            namespace = f"{db}.{schema}".lower() if db and schema else db.lower()
            return (
                shape,
                cell("datatechnologyname").lower(),
                namespace,
                table_name.lower(),
                cell("databasestorageresourceuritext"),
            )
        if shape == "file":
            return (
                shape,
                cell("filesystemtypetext").lower() or "file",
                cell("directoryname").lower(),
                file_name.lower(),
                cell("filestorageresourceuritext"),
            )
        return (
            shape,
            "s3",
            s3_bucket.lower(),
            s3_asset.lower(),
            cell("storageresourceuritext"),
        )
