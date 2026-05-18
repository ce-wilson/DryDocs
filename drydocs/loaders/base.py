"""BaseLoader — the canonical loader pattern every M1+ loader inherits from.

Lifecycle:

1. Open a :JobRun (PROV Activity, kind='load') with a fresh UUID.
2. Stream rows from the Adapter.
3. Validate each row through the loader's pydantic model; rejects go to a
   side log with the row index + error.
4. Batch validated rows; UNWIND each batch into the loader's Cypher.
5. Close the :JobRun with row counts and a final status.

Loaders inherit from BaseLoader and implement three things:
- ``name``         : str, e.g. 'seal_applications.v1'
- ``cypher_path``  : Path to the .cypher file (UNWIND $batch AS row)
- ``row_model``    : pydantic model class

The Cypher template is responsible for MERGE idempotency, port creation
where applicable, and provenance attribution (`:WAS_GENERATED_BY` to the
loader's :JobRun).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from ..adapters import Adapter
    from ..neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)


@dataclass
class LoadSummary:
    """Result of a single loader run."""

    loader: str
    run_id: str
    started_at: str
    completed_at: str | None = None
    rows_processed: int = 0
    rows_rejected: int = 0
    rejects: list[dict] = field(default_factory=list)
    status: str = "STARTED"

    def as_dict(self) -> dict:
        return {
            "loader": self.loader,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "rows_processed": self.rows_processed,
            "rows_rejected": self.rows_rejected,
            "status": self.status,
        }


class BaseLoader:
    """Abstract loader. Concrete loaders set the three class attributes below."""

    name: ClassVar[str] = "base"
    cypher_path: ClassVar[Path | None] = None
    row_model: ClassVar[type[BaseModel] | None] = None
    source_label: ClassVar[str] = "csv"  # 'csv' | 'oracle' | 'agent' | 'human'

    def __init__(
        self,
        client: "Neo4jClient",
        adapter: "Adapter",
        *,
        batch_size: int = 1000,
        max_rejects_kept: int = 100,
    ) -> None:
        if not self.cypher_path:
            raise NotImplementedError(f"{type(self).__name__} must set cypher_path")
        if not self.row_model:
            raise NotImplementedError(f"{type(self).__name__} must set row_model")
        self.client = client
        self.adapter = adapter
        self.batch_size = batch_size
        self.max_rejects_kept = max_rejects_kept
        self.run_id = str(uuid.uuid4())
        self.loaded_at = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )

    # ---- entrypoint ------------------------------------------------------

    def load(self) -> LoadSummary:
        summary = LoadSummary(
            loader=self.name,
            run_id=self.run_id,
            started_at=self.loaded_at,
        )

        self._open_run()
        cypher = self._read_cypher()

        batch: list[dict] = []
        try:
            with self.adapter as adapter:
                for idx, raw in enumerate(adapter.rows()):
                    try:
                        model = self.row_model.model_validate(raw)  # type: ignore[union-attr]
                    except ValidationError as exc:
                        summary.rows_rejected += 1
                        if len(summary.rejects) < self.max_rejects_kept:
                            summary.rejects.append(
                                {"row_index": idx, "errors": exc.errors(), "raw": raw}
                            )
                        continue
                    batch.append(self.to_params(model))
                    if len(batch) >= self.batch_size:
                        self._flush(cypher, batch)
                        summary.rows_processed += len(batch)
                        batch.clear()
                if batch:
                    self._flush(cypher, batch)
                    summary.rows_processed += len(batch)
        except Exception as exc:
            LOGGER.exception("Loader %s failed: %s", self.name, exc)
            self._close_run(status="FAILED", summary=summary)
            summary.status = "FAILED"
            summary.completed_at = (
                datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            )
            raise

        summary.status = "OK"
        summary.completed_at = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        self._close_run(status="OK", summary=summary)
        LOGGER.info("Loader %s done: %s", self.name, summary.as_dict())
        return summary

    # ---- hooks loaders may override -------------------------------------

    def to_params(self, model: BaseModel) -> dict:
        """Serialize a validated row model to a flat dict the Cypher expects."""
        return model.model_dump(mode="json")

    # ---- internals -------------------------------------------------------

    def _read_cypher(self) -> str:
        path = self.cypher_path
        assert path is not None  # narrowed in __init__
        return path.read_text(encoding="utf-8")

    def _flush(self, cypher: str, batch: list[dict]) -> None:
        params: dict[str, Any] = {
            "batch": batch,
            "run_id": self.run_id,
            "loaded_at": self.loaded_at,
            "loader": self.name,
            "source_label": self.source_label,
        }
        # Use APOC runMany for multi-statement scripts; a single UNWIND
        # template runs faster via plain run() — try plain first, fall
        # back to runMany if the script has multiple statements.
        if cypher.count(";") > 1:
            self.client.run_script(cypher, params=params)
        else:
            self.client.run(cypher, **params)

    def _open_run(self) -> None:
        self.client.run(
            """
            MERGE (run:JobRun {run_id: $run_id})
              ON CREATE SET run.kind        = 'load',
                            run.loader      = $loader,
                            run.source      = $source_label,
                            run.started_at  = datetime($loaded_at),
                            run.status      = 'STARTED'
            """,
            run_id=self.run_id,
            loader=self.name,
            source_label=self.source_label,
            loaded_at=self.loaded_at,
        )

    def _close_run(self, *, status: str, summary: LoadSummary) -> None:
        self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            SET run.status         = $status,
                run.completed_at   = datetime(),
                run.rows_processed = $rows_processed,
                run.rows_rejected  = $rows_rejected
            """,
            run_id=self.run_id,
            status=status,
            rows_processed=summary.rows_processed,
            rows_rejected=summary.rows_rejected,
        )
