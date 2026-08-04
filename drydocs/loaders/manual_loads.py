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
    """Writes SME-authored seal_app_ref PINS at the folder grain
    (match_method 'manual', origin 'manual-pin'; rekeyed at K8 per gate
    seal-app-ref-edge-reshape §D2).

    After the write it reconciles edges-touched against rows loaded and
    stamps the shortfall on the :JobRun as dropped_in_graph — reported,
    never silent. Note a code-level row legitimately writes MORE edges than
    rows (the §B1 fan-out), so the reconciliation floor is rows with a
    folder pin, not raw row count.
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

    def extra_cypher_params(self) -> dict[str, Any]:
        # §G1 (K11): a manual pin confirms the mapping, so it authors the
        # same orchestrator USES_SOFTWARE edge as the automated loader.
        from .folder_attribution import orchestrator_product_ref

        return {"orchestrator_product_id": orchestrator_product_ref()}

    def load(self):
        summary = super().load()
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMFolder)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(:Port)
              WHERE r.last_run_id = $run_id AND r.match_method = 'manual'
            WITH run, count(r) AS edges_written
            OPTIONAL MATCH (n:BusinessApplication {manually_created: true})
              WHERE n.first_seen_at IS NOT NULL AND n.source = 'manual-csv'
            WITH run, edges_written, count(n) AS manually_created_total
            SET run.edges_written          = edges_written,
                run.rows_authored          = $rows,
                run.manually_created_total = manually_created_total
            RETURN edges_written
            """,
            run_id=self.run_id,
            rows=summary.rows_processed,
        )
        if result:
            written = result[0].get("edges_written", 0)
            if written == 0 and summary.rows_processed:
                LOGGER.warning(
                    "manual_seal_attribution: %d authored row(s) wrote no edges "
                    "— app code / folder / Port endpoints missing in the graph.",
                    summary.rows_processed,
                )
        return summary
