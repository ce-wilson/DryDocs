"""AWS Glue base-table inventory ingest seam (G41) — the dataset POPULATION
feed, without the transformations.

The DPL zone model (runtime trace 2026-07-21) puts every dataset's physical
form in per-zone Glue databases + tables (one bucket, RAW / TRUSTED / REFINED
prefixes). The registry that catalogs those tables is exportable as a flat
sheet (user disclosure 2026-07-28; mechanism-only — real values stay
company-side). Three sheet variants were observed, all consumed here through
ONE header-synonym contract:

- **GUID-bearing inventory** — ``PlatformId, databaseName, tableName,
  tableDatasetId, tableDatasetIdSource, databaseFullPath``. The load-bearing
  observation: a ``*_RAW_TRUSTED`` table appears in BOTH the ``RAW__*`` and
  ``TRUSTED__*`` databases **with the same dataset GUID** — one dataset, two
  zone placements (the FILE→CONFORMED ≈ RAW→TRUSTED note, now measured).
  ``REFINED`` placements carry their own GUID.
- **Consumption inventory** — ``database`` (the platform, ``AWS-S3``),
  ``databasePlatformId, databaseName, tableName, databaseFullPath`` — NO GUID
  column at all: these rows can only key on the glue path.
- **Normalized load sheet** — ``databasePlatform, databasePlatformId,
  database, schema, table, tableType, appId, tableDatasetId,
  tableDatasetIdSource, fullPath`` — the curated merge, with the SEAL
  (``appId``) already lifted out of the table-name prefix.

ASSUMED FIELD CONTRACT (defined by the SYNTHETIC fixtures, adjust when a real
sample validates it — the dpl_mac discipline). Naming facts observed:

- ``databaseName`` = ``<ZONE>__<LOB>__<segment...>__<name>`` split on double
  underscore; segment 1 is the zone (RAW | TRUSTED | REFINED), segment 2 the
  LOB. Anything else: staged with ``zone=""`` and counted, never guessed.
- ``tableName`` MAY embed ``<appId>_<datasetFamily>_<logical>_<zoneSuffix>``
  (e.g. ``111331_300000011_*_RAW_TRUSTED``) — but a legacy family
  (``1_TM_PSWD*``) shows bare numeric prefixes that are NOT SEALs, so the
  name prefix is only ever a CROSS-CHECK against the ``appId`` column
  (disagreement counted), never an extraction source on its own.

IDENTITY (the G17/G22 seam, applied):

- A row whose ``tableDatasetId`` is a dataset GUID (``tableDatasetIdSource``
  = ``datasetGuid`` or blank) lands on the SAME ``dpl_dataset`` DataAsset the
  MAC seam stages (identity = GUID alone, G17): the glue placement becomes
  per-zone PROPERTIES (``glue_database_<zone>`` / ``glue_table_<zone>`` /
  ``glue_path_<zone>``) — exactly the "glue db/table can join later as more
  properties" slot reserved at the G17 build.
- A row with NO GUID keys on the canonical lowercase ``db.table`` path as a
  ``glue_table`` DataAsset — the PATH-keyed fallback, mirroring the
  Script GUID-vs-path boundary. Whether path-keyed assets later unify with a
  GUID is the G22 clause-f identity ruling; here a no-GUID row whose path
  matches an already-staged GUID placement joins it (counted), everything
  else stays separate.
- ``tableDatasetIdSource`` naming any OTHER id scheme routes the row to path
  identity (never join a non-GUID id into GUID space) — counted.

RELATIONSHIPS: **none are created here.** The GUID is the join key that makes
the G17 ``READS_FROM``/``WRITES_TO`` candidates land on these same nodes; the
SEAL (``appId``) is an attribution FACT stored as a property — attribution
edges are Epic K territory and every graph write stays behind G22.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from ..model import DataAssetNode, LineageGraph, asset_id
from .dpl_mac import MAC_DATASET_KIND

#: DataAsset kind for path-keyed rows (no GUID) — the clause-f fallback side
GLUE_TABLE_KIND = "glue_table"

#: the traced zone vocabulary (databaseName segment 1)
ZONES = ("raw", "trusted", "refined")

#: the only tableDatasetIdSource spelling that authorizes a GUID-identity join
_GUID_SOURCE = "datasetguid"


def _norm_header(raw: str) -> str:
    return "".join(c for c in raw.lower() if c.isalnum())


@dataclass(frozen=True)
class InventoryRow:
    """One normalized sheet row (header variants already resolved)."""

    database: str
    table: str
    guid: str = ""
    guid_source: str = ""
    seal: str = ""
    platform: str = ""
    platform_id: str = ""
    full_path: str = ""


@dataclass
class GlueInventoryCoverage:
    """Per-run accounting — every skip/mismatch counted BY REASON, never
    silent (the STG_PARSE_QUALITY / UNMATCHED house rule, candidate side)."""

    files_read: int = 0
    files_invalid: int = 0  # unreadable / no recognizable headers
    rows_read: int = 0
    rows_invalid: int = 0  # missing database or table — skipped
    guid_rows: int = 0  # GUID-identity rows
    path_rows: int = 0  # path-identity rows (no GUID)
    idsource_not_guid: int = 0  # tableDatasetIdSource names another scheme
    datasets_created: int = 0  # dpl_dataset nodes staged first BY this feed
    datasets_enriched: int = 0  # dpl_dataset nodes that already existed (MAC/flow)
    glue_created: int = 0  # path-keyed glue_table nodes staged
    path_joined_guid: int = 0  # no-GUID row whose path matched a GUID placement
    placements_added: int = 0  # per-zone glue placements stamped
    placement_conflicts: int = 0  # same GUID+zone, different path — first wins
    duplicate_rows: int = 0  # identical placement seen again
    zone_unknown: int = 0  # databaseName segment 1 not RAW/TRUSTED/REFINED
    seal_facts: int = 0  # appId captured as a property
    seal_disagreements: int = 0  # appId differs from an already-staged seal
    name_seal_disagreements: int = 0  # appId != the tableName numeric prefix

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"files={self.files_read} rows={self.rows_read} "
            f"guid_rows={self.guid_rows} path_rows={self.path_rows} | "
            f"datasets: created={self.datasets_created} "
            f"enriched={self.datasets_enriched} glue={self.glue_created} "
            f"path_joined={self.path_joined_guid} | "
            f"placements={self.placements_added} "
            f"conflicts={self.placement_conflicts} dupes={self.duplicate_rows} | "
            f"seal: facts={self.seal_facts} "
            f"disagree={self.seal_disagreements} "
            f"name_disagree={self.name_seal_disagreements} | "
            f"skipped: invalid_files={self.files_invalid} "
            f"invalid_rows={self.rows_invalid} "
            f"idsource={self.idsource_not_guid} zone_unknown={self.zone_unknown}"
        )


def parse_database_name(name: str) -> tuple[str, str]:
    """``<ZONE>__<LOB>__...`` → ``(zone, lob)`` lowercase; ``("", "")`` when
    the shape doesn't match — the caller counts, never guesses."""
    parts = name.split("__")
    if len(parts) >= 2 and parts[0].lower() in ZONES:
        return parts[0].lower(), parts[1].lower()
    return "", ""


def _name_prefix_digits(table: str) -> str:
    """The leading ``<digits>_`` of a table name, if any (cross-check only)."""
    head, sep, _ = table.partition("_")
    return head if sep and head.isdigit() else ""


class GlueTableInventoryExtractor:
    """Glue base-table sheets → DataAsset population + per-zone placement
    properties. Nodes only — the GUID/SEAL are join keys for edges OTHER
    seams (G17 flow) and future gates (Epic K, G22) own."""

    name = "glue-tables"

    def extract(self, source: str | Path, into: LineageGraph) -> GlueInventoryCoverage:
        """``source`` is one CSV export or a directory of them. Returns the
        run's :class:`GlueInventoryCoverage`; callers report it — nothing
        drops silently."""
        root = Path(source)
        files = sorted(root.glob("*.csv")) if root.is_dir() else [root]
        coverage = GlueInventoryCoverage()

        rows: list[InventoryRow] = []
        for path in files:
            rows.extend(self._read_file(path, coverage))

        # pass 1 — GUID-identity rows stage/enrich dpl_dataset nodes and build
        # the path→node index pass 2 joins against
        path_index: dict[str, str] = {}
        guid_rows, path_rows = [], []
        for row in rows:
            (guid_rows if self._guid_identity(row, coverage) else path_rows).append(row)
        for row in guid_rows:
            coverage.guid_rows += 1
            self._stage_guid_row(row, into, coverage, path_index)

        # pass 2 — path-identity rows join a known placement or stand alone
        for row in path_rows:
            coverage.path_rows += 1
            self._stage_path_row(row, into, coverage, path_index)
        return coverage

    # -- input --------------------------------------------------------------
    def _read_file(self, path: Path, coverage: GlueInventoryCoverage) -> list[InventoryRow]:
        try:
            with path.open(encoding="utf-8-sig", newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                if header is None:
                    coverage.files_invalid += 1
                    return []
                cols = self._map_headers(header)
                if "database" not in cols or "table" not in cols:
                    coverage.files_invalid += 1
                    return []
                coverage.files_read += 1
                out: list[InventoryRow] = []
                for raw in reader:
                    if not any(cell.strip() for cell in raw):
                        continue
                    coverage.rows_read += 1
                    row = self._build_row(raw, cols)
                    if row is None:
                        coverage.rows_invalid += 1
                    else:
                        out.append(row)
                return out
        except OSError:
            coverage.files_invalid += 1
            return []

    @staticmethod
    def _map_headers(header: list[str]) -> dict[str, int]:
        """Resolve the three observed header variants to one column map.

        ``database`` is the ambiguous header: it is the DB NAME on the
        normalized sheet but the PLATFORM on the consumption sheet (where the
        DB name travels as ``databaseName``) — presence of ``databaseName``
        decides which.
        """
        norm = {_norm_header(h): i for i, h in enumerate(header) if h.strip()}
        cols: dict[str, int] = {}
        if "databasename" in norm:
            cols["database"] = norm["databasename"]
            if "database" in norm:
                cols["platform"] = norm["database"]
        elif "database" in norm:
            cols["database"] = norm["database"]
        for want, keys in (
            ("table", ("tablename", "table")),
            ("guid", ("tabledatasetid",)),
            ("guid_source", ("tabledatasetidsource",)),
            ("seal", ("appid",)),
            ("platform", ("databaseplatform",)),
            ("platform_id", ("databaseplatformid", "platformid")),
        ):
            for key in keys:
                if key in norm and want not in cols:
                    cols[want] = norm[key]
        # the normalized sheet's header carries an annotation
        # ("fullPath *formula except for AWS") — match by prefix
        for key, idx in norm.items():
            if key.startswith(("fullpath", "databasefullpath")):
                cols.setdefault("full_path", idx)
        return cols

    @staticmethod
    def _build_row(raw: list[str], cols: dict[str, int]) -> InventoryRow | None:
        def cell(name: str) -> str:
            idx = cols.get(name)
            return raw[idx].strip() if idx is not None and idx < len(raw) else ""

        database, table = cell("database"), cell("table")
        if not database or not table:
            return None
        return InventoryRow(
            database=database,
            table=table,
            guid=cell("guid"),
            guid_source=cell("guid_source"),
            seal=cell("seal"),
            platform=cell("platform"),
            platform_id=cell("platform_id"),
            full_path=cell("full_path"),
        )

    # -- identity routing -----------------------------------------------------
    @staticmethod
    def _guid_identity(row: InventoryRow, coverage: GlueInventoryCoverage) -> bool:
        if not row.guid:
            return False
        source = _norm_header(row.guid_source)
        if source and source != _GUID_SOURCE:
            coverage.idsource_not_guid += 1
            return False
        return True

    # -- staging --------------------------------------------------------------
    @staticmethod
    def _canonical_path(row: InventoryRow) -> str:
        return (row.full_path or f"{row.database}.{row.table}").lower()

    def _stage_guid_row(
        self,
        row: InventoryRow,
        graph: LineageGraph,
        coverage: GlueInventoryCoverage,
        path_index: dict[str, str],
    ) -> None:
        aid = asset_id(MAC_DATASET_KIND, row.guid)
        node = graph.data_assets.get(aid)
        if node is None:
            node = DataAssetNode(
                node_id=aid,
                kind=MAC_DATASET_KIND,
                location=row.guid,
                properties={"glue_only": "true"},
            )
            graph.add_data_asset(node)
            coverage.datasets_created += 1
        else:
            coverage.datasets_enriched += 1
        self._stamp_placement(node, row, coverage)
        self._stamp_seal(node, row, coverage)
        path_index.setdefault(self._canonical_path(row), aid)

    def _stage_path_row(
        self,
        row: InventoryRow,
        graph: LineageGraph,
        coverage: GlueInventoryCoverage,
        path_index: dict[str, str],
    ) -> None:
        canonical = self._canonical_path(row)
        joined = path_index.get(canonical)
        if joined is not None:
            # the same physical table already staged under a GUID — enrich it,
            # never mint a second node for one table (clause-f friendly)
            coverage.path_joined_guid += 1
            node = graph.data_assets[joined]
            self._stamp_seal(node, row, coverage)
            return
        aid = asset_id(GLUE_TABLE_KIND, canonical)
        node = graph.data_assets.get(aid)
        if node is None:
            node = DataAssetNode(
                node_id=aid,
                kind=GLUE_TABLE_KIND,
                location=canonical,
                properties={},
            )
            graph.add_data_asset(node)
            coverage.glue_created += 1
        self._stamp_placement(node, row, coverage)
        self._stamp_seal(node, row, coverage)
        path_index.setdefault(canonical, aid)

    def _stamp_placement(
        self,
        node: DataAssetNode,
        row: InventoryRow,
        coverage: GlueInventoryCoverage,
    ) -> None:
        zone, lob = parse_database_name(row.database)
        if not zone:
            coverage.zone_unknown += 1
        suffix = zone or "unzoned"
        path = self._canonical_path(row)
        existing = node.properties.get(f"glue_path_{suffix}")
        if existing is not None:
            if existing == path:
                coverage.duplicate_rows += 1
            else:
                # first-seen wins (setdefault semantics); a second path for
                # the same GUID+zone is curation material, not a new node
                coverage.placement_conflicts += 1
            return
        node.properties[f"glue_path_{suffix}"] = path
        node.properties[f"glue_database_{suffix}"] = row.database
        node.properties[f"glue_table_{suffix}"] = row.table
        coverage.placements_added += 1
        if lob:
            node.properties.setdefault("lob", lob)
        if row.platform:
            node.properties.setdefault("platform", row.platform)
        if row.platform_id:
            node.properties.setdefault("platform_id", row.platform_id)

    @staticmethod
    def _stamp_seal(
        node: DataAssetNode,
        row: InventoryRow,
        coverage: GlueInventoryCoverage,
    ) -> None:
        if not row.seal:
            return
        existing = node.properties.get("seal", "")
        if existing and existing != row.seal:
            coverage.seal_disagreements += 1
            return
        if not existing:
            node.properties["seal"] = row.seal
            coverage.seal_facts += 1
        prefix = _name_prefix_digits(row.table)
        if prefix and prefix != row.seal:
            coverage.name_seal_disagreements += 1
