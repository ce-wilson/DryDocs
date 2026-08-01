"""Manual mapping CSV loads — tier 5 of the K2 SEAL attribution policy.

Gate seal-attribution-match-policy §F (SME-confirmed 2026-07-14,
config/gate-log.md): when no fact tier resolves a job — or multi-hit triage
cannot — the SME may author a CSV row (template
config/manual-loads/TEMPLATE-node-mapping.csv) mapping a source node key to a
PRE-EXISTING relationship to a target node key.

The pure half (manifest gate, vocabulary check, supported shape, CSV parse)
lives in drydocs_core.manual_mappings since the mapping-store plan M2 — it is
shared with the store materialization drydocs-api serves, and components
never import each other. Re-exported here so this module stays the loader's
single import surface. THE RULES are documented there; the graph-writing
half (PIN semantics, :JobRun provenance) is HERE and only here.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from drydocs_core.manual_mappings import (  # noqa: F401 — re-exported surface
    DEFAULT_MANIFEST_PATH,
    LOADABLE_STATUSES,
    SUPPORTED_SHAPE,
    VOCABULARY_PATH,
    ManualLoadError,
    load_manifest,
    parse_mapping_csv,
    relationship_registered,
    require_registered,
)
from drydocs_core.models import ManualMappingRow

from .base import BaseLoader

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read seam (mapping-store plan M1/M3)
# ---------------------------------------------------------------------------


def mapping_rows(
    csv_path: str | Path,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    vocabulary_path: str | Path = VOCABULARY_PATH,
) -> list[ManualMappingRow]:
    """The loader-facing read entry point. Default (M3): rows come back
    across the SQL boundary of the mapping-store materialization
    (drydocs_core.mapping_store) — validation is the same chain either way.
    Set DRYDOCS_MAPPING_READ=yaml to force the legacy direct-CSV path
    (the M1 fallback; parity is test-guarded)."""
    import os

    if os.environ.get("DRYDOCS_MAPPING_READ", "db").lower() == "yaml":
        return parse_mapping_csv(
            csv_path, manifest_path=manifest_path, vocabulary_path=vocabulary_path
        )
    from drydocs_core.mapping_store import manual_mapping_rows_from_store

    return manual_mapping_rows_from_store(
        csv_path, manifest_path=manifest_path, vocabulary_path=vocabulary_path
    )


# ---------------------------------------------------------------------------
# Adapter + loader
# ---------------------------------------------------------------------------


class ManualMappingAdapter:
    """Yields pre-validated manual mapping rows to BaseLoader."""

    def __init__(self, rows: list[ManualMappingRow]) -> None:
        self._rows = rows

    def __enter__(self) -> ManualMappingAdapter:
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for row in self._rows:
            yield row.model_dump(mode="json")


class ManualSealAttributionLoader(BaseLoader):
    """Writes SME-authored seal_app_ref edges (match_method 'manual').

    After the write it reconciles edges-touched against rows loaded and
    stamps the shortfall (rows whose ControlMJob was absent) on the :JobRun
    as dropped_in_graph — reported, never silent.
    """

    name: ClassVar[str] = "manual_seal_attribution.v1"
    # Deliberately None: rows are SME-authored CSVs gated by
    # config/manual-loads/manifest.yaml, not a source-registry feed — the
    # named exemption lives in cli.SOURCELESS_LOADERS (N3).
    source_id: ClassVar[str | None] = None
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "manual_seal_attribution.cypher"
    )
    row_model: ClassVar[type] = ManualMappingRow
    source_label: ClassVar[str] = "human"

    def load(self):
        summary = super().load()
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMJob)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(:BusinessApplication)
              WHERE r.last_run_id = $run_id AND r.match_method = 'manual'
            WITH run, count(r) AS edges_written
            OPTIONAL MATCH (n:BusinessApplication {manually_created: true})
              WHERE n.first_seen_at IS NOT NULL AND n.source = 'manual-csv'
            WITH run, edges_written, count(n) AS manually_created_total
            SET run.edges_written          = edges_written,
                run.dropped_in_graph       = $rows - edges_written,
                run.manually_created_total = manually_created_total
            RETURN edges_written
            """,
            run_id=self.run_id,
            rows=summary.rows_processed,
        )
        if result:
            dropped = summary.rows_processed - result[0].get("edges_written", 0)
            if dropped:
                LOGGER.warning(
                    "manual_seal_attribution: %d row(s) found no ControlMJob "
                    "endpoint — surfaced as JobRun.dropped_in_graph.",
                    dropped,
                )
        return summary
