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

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ValidationError

# The comment/string-aware statement scanner lives in drydocs_core (D5) so the
# client's run_script and this module's dispatch share ONE implementation; the
# private alias is kept — it is part of this module's tested surface.
from drydocs_core.cypher_split import code_semicolons as _code_semicolons
from drydocs_core.run_log import LoaderRunLog

if TYPE_CHECKING:
    from drydocs_core.adapters import Adapter
    from drydocs_core.neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)


# ---- row checksum (doc 06 Phase 2 — provenance-edge diet) -------------------
#
# Fields excluded by default because they are volatile (change every run even
# when the underlying source record is unchanged) or are BaseLoader batch-level
# params rather than row content:
#   - capture_date: the ETL/replication pull timestamp, not a source-record
#     value; would make every row look "changed" on every run.
#   - run_id / loaded_at / loader / source_label: passed by BaseLoader._flush
#     as separate query params, never merged into a row dict today — excluded
#     defensively so a future refactor can't silently poison every hash.
#   - last_seen_at / last_run_id / row_checksum: cypher-side bookkeeping
#     properties, never legitimately part of a row's own domain content.
DEFAULT_CHECKSUM_EXCLUDE: frozenset[str] = frozenset(
    {
        "capture_date",
        "run_id",
        "loaded_at",
        "loader",
        "source_label",
        "last_seen_at",
        "last_run_id",
        "row_checksum",
        "removed_from_source_at",
        "removed_by_run_id",
    }
)


def compute_row_checksum(
    params: dict[str, Any],
    *,
    exclude: frozenset[str] | set[str] = DEFAULT_CHECKSUM_EXCLUDE,
) -> str:
    """Deterministic content hash of a loader row's domain fields.

    Used to gate ``WAS_GENERATED_BY`` (doc 06 Phase 2): the same row hashes
    identically on every run it is unchanged, so the Cypher template can skip
    the provenance edge for a full-refresh no-op and write it only on create
    or actual change.

    ``params`` is whatever :meth:`BaseLoader.to_params` produced for one row
    (i.e. what lands in ``$batch``) — dict key order is irrelevant (the
    canonical form sorts keys); pass a wider ``exclude`` set if a loader's
    row dict carries extra volatile fields beyond :data:`DEFAULT_CHECKSUM_EXCLUDE`.
    """
    filtered = {k: v for k, v in params.items() if k not in exclude}
    canonical = json.dumps(filtered, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class LoadSummary:
    """Result of a single loader run."""

    loader: str
    run_id: str
    started_at: str
    completed_at: str | None = None
    rows_processed: int = 0
    rows_rejected: int = 0
    rows_changed: int = 0
    nodes_marked_removed: int = 0
    nodes_reactivated: int = 0
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
            "rows_changed": self.rows_changed,
            "nodes_marked_removed": self.nodes_marked_removed,
            "nodes_reactivated": self.nodes_reactivated,
            "status": self.status,
        }


class BaseLoader:
    """Abstract loader. Concrete loaders set the three class attributes below."""

    name: ClassVar[str] = "base"
    cypher_path: ClassVar[Path | None] = None
    row_model: ClassVar[type[BaseModel] | None] = None
    source_label: ClassVar[str] = "csv"  # 'csv' | 'oracle' | 'agent' | 'human'

    # ---- N3: the loader -> source join ----------------------------------
    # The config/source-registry.yaml id this loader draws from. Declared on
    # every concrete loader so loader -> source -> column-ledger is a
    # traversal, not tribal knowledge; the D3 confirmed-gate and the load-map
    # render both read it. None is legal ONLY for abstract bases and for
    # loaders named in cli.SOURCELESS_LOADERS with a written reason
    # (guarded by tests/unit/test_load_map_declarations.py).
    source_id: ClassVar[str | None] = None

    # ---- D7: incremental-delete (soft-delete mark) opt-in ----------------
    # sweep_label names the node label whose population this loader's extract
    # DECLARES within scope — after a successful load, in-scope nodes the run
    # did NOT touch are marked removed-from-source (property + timestamp;
    # never deleted here — `drydocs sweep-removed` hard-deletes later).
    # sweep_scope_property names a row param whose distinct values bound the
    # declaration (e.g. folder_id for jobs: a folder-filtered extract only
    # declares the folders it actually carried, so out-of-scope nodes are
    # untouched). Without a scope property the mark pass runs only when the
    # caller passes full_extract=True — only the caller knows the extract
    # was unfiltered. Property-only mechanism; no edge meaning involved.
    sweep_label: ClassVar[str | None] = None
    sweep_scope_property: ClassVar[str | None] = None

    def __init__(
        self,
        client: Neo4jClient,
        adapter: Adapter,
        *,
        batch_size: int = 1000,
        max_rejects_kept: int = 100,
        index_wait_seconds: int = 300,
        full_extract: bool = False,
        run_log: bool = True,
    ) -> None:
        if not self.cypher_path:
            raise NotImplementedError(f"{type(self).__name__} must set cypher_path")
        if not self.row_model:
            raise NotImplementedError(f"{type(self).__name__} must set row_model")
        self.client = client
        self.adapter = adapter
        self.batch_size = batch_size
        self.max_rejects_kept = max_rejects_kept
        self.index_wait_seconds = index_wait_seconds
        self.run_id = str(uuid.uuid4())
        self.loaded_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        self.full_extract = full_extract
        self.run_log = run_log
        self._scope_values: set = set()  # distinct sweep_scope_property values seen

    # ---- entrypoint ------------------------------------------------------

    def load(self) -> LoadSummary:
        summary = LoadSummary(
            loader=self.name,
            run_id=self.run_id,
            started_at=self.loaded_at,
        )
        run_log = self._open_run_log()
        error: BaseException | None = None
        try:
            return self._load(summary, run_log)
        except BaseException as exc:
            error = exc
            raise
        finally:
            if run_log is not None:
                run_log.close(summary.as_dict(), error=error)

    def _load(self, summary: LoadSummary, run_log: LoaderRunLog | None) -> LoadSummary:
        self._preflight_indexes()
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
                        if run_log is not None:
                            run_log.reject(idx, exc.errors())
                        if len(summary.rejects) < self.max_rejects_kept:
                            summary.rejects.append(
                                {"row_index": idx, "errors": exc.errors(), "raw": raw}
                            )
                        continue
                    batch.append(self.to_params(model))
                    if self.sweep_label and self.sweep_scope_property:
                        scope_val = batch[-1].get(self.sweep_scope_property)
                        if scope_val is not None:
                            self._scope_values.add(scope_val)
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
            summary.completed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
            raise

        self._mark_removed(summary)

        summary.status = "OK"
        summary.completed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        self._close_run(status="OK", summary=summary)
        LOGGER.info("Loader %s done: %s", self.name, summary.as_dict())
        return summary

    def _open_run_log(self) -> LoaderRunLog | None:
        """Open the per-run log (header/meta + WARN-stream capture + rejects).

        Best-effort by contract: an unwritable log directory downgrades to a
        WARNING and the load proceeds without a log — the audit trail is never
        the reason a load fails.
        """
        if not self.run_log:
            return None
        source_detail = getattr(self.adapter, "path", None)
        source = f"{self.source_label} ({source_detail or type(self.adapter).__name__})"
        uri = getattr(self.client, "_uri", "") or ""
        database = getattr(self.client, "_database", "") or ""
        log = LoaderRunLog(
            self.name,
            self.run_id,
            source=source,
            target=f"{uri} db={database}".strip(),
            meta={"batch size": self.batch_size, "full extract": self.full_extract},
        )
        try:
            path = log.open()
        except OSError as exc:
            LOGGER.warning(
                "Loader %s: run log unavailable (%s) — continuing without",
                self.name,
                exc,
            )
            return None
        log.attach()
        LOGGER.info("[run-log] %s", path)
        return log

    # ---- hooks loaders may override -------------------------------------

    def to_params(self, model: BaseModel) -> dict:
        """Serialize a validated row model to a flat dict the Cypher expects."""
        return model.model_dump(mode="json")

    # ---- internals -------------------------------------------------------

    def _preflight_indexes(self) -> None:
        """Refuse to load against a broken index; wait out a populating one.

        MERGE against a POPULATING index succeeds but degrades 10-100x (the
        planner can't use it), and a FAILED index silently breaks the NODE KEY
        guarantees every loader's identity model depends on. Runs before
        :meth:`_open_run` so a refused load writes nothing — not even the
        :JobRun. (neo4j-advisor-confirmation-2026-07-17 §2c.)
        """
        rows = self.client.run(
            "SHOW INDEXES YIELD name, state, labelsOrTypes "
            "WHERE state <> 'ONLINE' "
            "RETURN name, state, labelsOrTypes"
        )
        if not rows:
            return
        failed = [r for r in rows if r.get("state") == "FAILED"]
        if failed:
            detail = ", ".join(f"{r.get('name')} ({r.get('labelsOrTypes')})" for r in failed)
            raise RuntimeError(
                f"Loader {self.name}: refusing to load — FAILED index(es): {detail}. "
                "Drop and recreate them (see constraints.cypher) before loading."
            )
        # Remaining states (POPULATING) resolve on their own — block until they
        # do rather than racing the population. Raises on timeout.
        LOGGER.info(
            "Loader %s: waiting up to %ss for %d index(es) to come ONLINE",
            self.name,
            self.index_wait_seconds,
            len(rows),
        )
        self.client.run("CALL db.awaitIndexes($seconds)", seconds=self.index_wait_seconds)

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
        # template runs faster via plain run() — and runMany SPLITS on
        # semicolons wherever they appear, so a ';' inside a // comment
        # must not route us there (it would shear the statement mid-comment;
        # found by the J9 e2e test on controlm_folders.cypher's audit-envelope
        # comment). Count code semicolons only.
        if _code_semicolons(cypher) > 1:
            self.client.run_script(cypher, params=params)
        else:
            self.client.run(cypher, **params)

    def _mark_removed(self, summary: LoadSummary) -> None:
        """D7 — the incremental-delete mark pass (soft delete, property-only).

        The full-diff ID set falls out of the run bookkeeping: every row this
        run touched carries ``last_run_id = $run_id`` (every loader template
        sets it), so within the extract's declared scope any node still on an
        older run id was REMOVED FROM SOURCE. Mark it (timestamp + run id) —
        never delete; the retention sweep (:func:`sweep_removed`, CLI
        ``drydocs sweep-removed``) hard-deletes later. Re-appeared nodes get
        their mark cleared. Counts are always reported — never silent (the
        STG_PARSE_QUALITY house rule).
        """
        label = self.sweep_label
        if not label:
            return
        scope_clause = ""
        params: dict[str, Any] = {"run_id": self.run_id, "loaded_at": self.loaded_at}
        if self.sweep_scope_property:
            if not self._scope_values:
                LOGGER.info(
                    "Loader %s: mark pass skipped — empty extract declares nothing",
                    self.name,
                )
                return
            scope_clause = f"AND n.{self.sweep_scope_property} IN $scope_values "
            params["scope_values"] = sorted(self._scope_values)
        elif not self.full_extract:
            LOGGER.info(
                "Loader %s: mark pass skipped — no scope property and the run did "
                "not declare full_extract (a filtered extract must not mark)",
                self.name,
            )
            return
        rows = self.client.run(
            f"MATCH (n:{label}) "
            "WHERE (n.last_run_id IS NULL OR n.last_run_id <> $run_id) "
            "AND n.removed_from_source_at IS NULL "
            f"{scope_clause}"
            "SET n.removed_from_source_at = datetime($loaded_at), "
            "    n.removed_by_run_id     = $run_id "
            "RETURN count(n) AS marked",
            **params,
        )
        summary.nodes_marked_removed = rows[0].get("marked", 0) if rows else 0
        rows = self.client.run(
            f"MATCH (n:{label}) "
            "WHERE n.last_run_id = $run_id AND n.removed_from_source_at IS NOT NULL "
            "SET n.removed_from_source_at = null, "
            "    n.removed_by_run_id     = null "
            "RETURN count(n) AS reactivated",
            run_id=self.run_id,
        )
        summary.nodes_reactivated = rows[0].get("reactivated", 0) if rows else 0
        LOGGER.info(
            "Loader %s: incremental-delete mark — %d marked removed-from-source, "
            "%d reactivated (scope=%s)",
            self.name,
            summary.nodes_marked_removed,
            summary.nodes_reactivated,
            "full"
            if not self.sweep_scope_property
            else f"{self.sweep_scope_property} x{len(self._scope_values)}",
        )

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
        # rows_changed is derived from the graph itself rather than tracked in
        # Python: since Cypher templates now write :WAS_GENERATED_BY only on
        # create/change (doc 06 Phase 2), every edge pointing at THIS run was,
        # by construction, written because a row was new or actually differed
        # — counting them gives the full-refresh "what changed" total without
        # any per-row bookkeeping on the Python side.
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (run)<-[gen:WAS_GENERATED_BY]-()
            WITH run, count(gen) AS rows_changed
            SET run.status               = $status,
                run.completed_at         = datetime(),
                run.rows_processed       = $rows_processed,
                run.rows_rejected        = $rows_rejected,
                run.rows_changed         = rows_changed,
                run.nodes_marked_removed = $nodes_marked_removed,
                run.nodes_reactivated    = $nodes_reactivated
            RETURN rows_changed
            """,
            run_id=self.run_id,
            status=status,
            rows_processed=summary.rows_processed,
            rows_rejected=summary.rows_rejected,
            nodes_marked_removed=summary.nodes_marked_removed,
            nodes_reactivated=summary.nodes_reactivated,
        )
        if result:
            summary.rows_changed = result[0].get("rows_changed", 0)


def sweep_removed(
    client: Neo4jClient,
    label: str,
    *,
    older_than_days: int,
    dry_run: bool = False,
) -> dict[str, int]:
    """D7 — the retention sweep: hard-delete nodes whose removed-from-source
    mark is older than the window (the mark pass in :meth:`BaseLoader.load`
    only ever marks). ``dry_run`` counts without deleting. Returns
    ``{"swept": n, "retained": m}`` — retained = marks inside the window that
    survive this sweep. Counts always reported, never silent."""
    match = (
        f"MATCH (n:{label}) "
        "WHERE n.removed_from_source_at IS NOT NULL "
        "AND n.removed_from_source_at < datetime() - duration({days: $days}) "
    )
    if dry_run:
        rows = client.run(match + "RETURN count(n) AS swept", days=older_than_days)
    else:
        rows = client.run(match + "DETACH DELETE n RETURN count(n) AS swept", days=older_than_days)
    swept = rows[0].get("swept", 0) if rows else 0
    rows = client.run(
        f"MATCH (n:{label}) WHERE n.removed_from_source_at IS NOT NULL "
        "RETURN count(n) AS retained"
    )
    retained = rows[0].get("retained", 0) if rows else 0
    return {"swept": swept, "retained": retained}
