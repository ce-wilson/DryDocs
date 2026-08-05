"""BatchPortOrchestratorLoader — the declared batch-port orchestrator migration.

Backlog C14, executing the C12 platforms-taxonomy sign-off (config/gate-log.md
2026-07-21): the SEAL-declared batch-port orchestrator string becomes an
app-level edge on the ACTIVE registry relationship —

    (:BusinessApplication)-[:USES_SOFTWARE {source: 'batch-port'}]->
    (:SoftwareProduct {role: 'orchestrator'})

``source: 'batch-port'`` distinguishes these declared-orchestrator edges from
the DRYDOCS-SELF stack rows (``source: 'registry'``) and the future plan-07
'controlm-cmdline' detections on the same edge type. This replaces the retired
``REQUIRES_SCHEDULER -> :SchedulerKind`` design (seal_requires_scheduler,
deprecated at C12/C13).

Source of the strings: ``config/taxonomy/business-application.yaml`` (the
taxonomy capture of the SEAL extract; apps without a ``batch_orchestrator``
field simply have no declaration and are skipped). The string -> product
crosswalk comes from ``config/taxonomy/platforms.yaml`` seed rows
(id / scheduler_kind / label -> ``software_registry_ref``, all confirmed at
the C12 gate). An unmapped string yields ``product_id=None`` — the Cypher
flags the app node and the adapter reports it (the invocation-patterns
coverage-policy precedent: surfaced, never guessed).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import yaml

from drydocs_core.models.registry import BatchPortOrchestratorRow

from .base import BaseLoader, LoadSummary

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from drydocs_core.run_log import LoaderRunLog

LOGGER = logging.getLogger(__name__)

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APPS_PATH = REPO_ROOT / "config" / "taxonomy" / "business-application.yaml"
DEFAULT_PLATFORMS_PATH = REPO_ROOT / "config" / "taxonomy" / "platforms.yaml"


def build_orchestrator_crosswalk(
    platforms_path: Path | str = DEFAULT_PLATFORMS_PATH,
) -> dict[str, str]:
    """Orchestrator string -> registry product id, from the platforms seed rows.

    Each seed row contributes its ``id``, ``scheduler_kind``, and ``label``
    (casefolded) as keys to its ``software_registry_ref``. Rows without a ref
    contribute nothing — a string can only ever resolve to a gate-confirmed
    link, never to a guess.
    """
    doc = yaml.safe_load(Path(platforms_path).read_text(encoding="utf-8"))
    crosswalk: dict[str, str] = {}
    for row in doc.get("platforms", []):
        ref = row.get("software_registry_ref")
        if not ref:
            continue
        for key in (row.get("id"), row.get("scheduler_kind"), row.get("label")):
            if key:
                crosswalk[str(key).strip().casefold()] = str(ref)
    return crosswalk


class BatchOrchestratorYamlAdapter:
    """Yields one row per app that declares a batch orchestrator.

    Coverage bookkeeping (inspect after iterating):
    ``unmapped``                — rows whose string resolved to no product;
    ``apps_without_declaration`` — apps skipped for having no field at all.
    """

    def __init__(
        self,
        apps_path: Path | str = DEFAULT_APPS_PATH,
        platforms_path: Path | str = DEFAULT_PLATFORMS_PATH,
    ) -> None:
        self.apps_path = Path(apps_path)
        self.platforms_path = Path(platforms_path)
        self.unmapped: list[dict] = []
        self.apps_without_declaration = 0

    def __enter__(self) -> BatchOrchestratorYamlAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        self.unmapped = []
        self.apps_without_declaration = 0
        crosswalk = build_orchestrator_crosswalk(self.platforms_path)
        doc = yaml.safe_load(self.apps_path.read_text(encoding="utf-8"))
        apps = (doc.get("nodes") or {}).get("business_applications", [])
        for app in apps:
            raw = app.get("batch_orchestrator")
            if not raw:
                self.apps_without_declaration += 1
                continue
            row = {
                "seal_id": str(app["sealid"]),
                "orchestrator_raw": str(raw),
                "product_id": crosswalk.get(str(raw).strip().casefold()),
            }
            if row["product_id"] is None:
                self.unmapped.append(
                    {"seal_id": row["seal_id"], "orchestrator_raw": row["orchestrator_raw"]}
                )
            yield row


class BatchPortOrchestratorLoader(BaseLoader):
    """Writes the declared-orchestrator edge; refuses when its endpoints are absent.

    This pass is MATCH-only on BOTH endpoints, so it has TWO ways to succeed
    while doing nothing (the failure family Q8 closed in ``bmc_docs``):

    * the app registry absent — the hard ``MATCH (a:BusinessApplication ...)``
      fails per row, so the row writes nothing at all, not even the raw string;
    * the product registry absent — the ``OPTIONAL MATCH`` + FOREACH guard drops
      every USES_SOFTWARE edge.

    Both are whole-registry conditions and both are refused up front. Their
    per-ROW counterparts (this app is missing / this product is missing) stay
    tolerated — one bad row must not cost the other apps their edges — but are
    reported after the load, never silent.
    """

    name: ClassVar[str] = "batch_port_orchestrator.v1"
    # The declared orchestrator string comes out of the SEAL taxonomy capture
    # (business-application.yaml), so the seal-extract gate is the right gate.
    source_id: ClassVar[str | None] = "seal:app-extract"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "batch_port_orchestrator.cypher"
    row_model: ClassVar[type] = BatchPortOrchestratorRow
    source_label: ClassVar[str] = "taxonomy"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # seal_ids actually sent to the database this run (recorded in _flush).
        self.seal_ids_sent: set[str] = set()
        # Post-load coverage: rows whose app was not in the graph, and apps this
        # run stamped that ended up with no batch-port edge.
        self.apps_not_in_graph: list[str] = []
        self.apps_without_edge: list[dict] = []

    # ---- prereq enforcement -------------------------------------------------

    def _load(self, summary: LoadSummary, run_log: LoaderRunLog | None) -> LoadSummary:
        """Refuse absent endpoint registries, then report the per-row misses.

        The refusal runs BEFORE ``super()._load`` — which is what reaches
        ``_preflight_indexes`` and ``_open_run`` — so a refused load writes
        nothing at all, not even the :JobRun (the ``_preflight_indexes``
        convention).
        """
        self._assert_endpoint_registries_present()
        result = super()._load(summary, run_log)
        self._report_rows_that_wrote_nothing()
        return result

    def _flush(self, cypher: str, batch: list[dict]) -> None:
        """Record what was sent, then send it.

        A hard-MATCH miss leaves NO trace in the graph, so unlike the
        ``bmc_docs`` probe it cannot be found by asking what this run touched —
        the only way to name those apps is to remember what we asked for.
        ``_flush`` is the right place: it is already the "these rows go to the
        database" seam, so it stays honest bookkeeping rather than the stateful
        ``to_params`` that Q8 rejected.
        """
        self.seal_ids_sent.update(
            str(row["seal_id"]) for row in batch if row.get("seal_id") is not None
        )
        super()._flush(cypher, batch)

    def _count_real_nodes(self, label: str, key: str) -> int:
        """Count real nodes of ``label``, excluding the schema exemplars.

        ``schema_graph.cypher`` MERGEs ``:SchemaMeta:<Label> {name: '<Label>'}``
        exemplars that carry the REAL label with no key property, so a bare
        ``count()`` would count the exemplar and wave an empty registry straight
        through — the whole failure this check exists to catch. ``NOT n:SchemaMeta``
        is the rename-proof form; the key-not-null clause additionally rejects
        any other keyless stub. (``label``/``key`` are module-controlled
        literals, never row data — no injection surface.)
        """
        rows = self.client.run(
            f"MATCH (n:{label}) WHERE NOT n:SchemaMeta AND n.{key} IS NOT NULL "
            "RETURN count(n) AS found"
        )
        return rows[0].get("found", 0) if rows else 0

    def _assert_endpoint_registries_present(self) -> None:
        """Fail loudly when either MATCH-only endpoint registry is empty."""
        # Counts on the CANONICAL key (S3 re-key), not the deprecated seal_id
        # alias this line used through 2026-08-05. Both are written today, so the
        # counts agree — but the alias retires at §G3, and a presence probe that
        # retires with it would start reporting an empty registry against a
        # perfectly good graph. (Noticed at S10; the alias is why it still worked.)
        apps = self._count_real_nodes("BusinessApplication", "app_id")
        if not apps:
            raise RuntimeError(
                f"Loader {self.name}: refusing to load — no :BusinessApplication "
                "nodes are reachable in this database, so every row's MATCH would "
                "fail and the run would still report success with nothing written. "
                "Load the SEAL application chain against this database first "
                "(`drydocs load-seal-applications`)."
            )
        products = self._count_real_nodes("SoftwareProduct", "product_id")
        if not products:
            raise RuntimeError(
                f"Loader {self.name}: refusing to load — no :SoftwareProduct nodes "
                "are reachable in this database, so every USES_SOFTWARE edge would "
                "be silently dropped and the load would still report success. Run "
                "`drydocs load-software-registry` against this database first "
                "(a relationship cannot span databases — check you are pointed at "
                "the database that holds the registry)."
            )
        LOGGER.info(
            "Loader %s: endpoints present (%d :BusinessApplication, %d :SoftwareProduct)",
            self.name,
            apps,
            products,
        )

    def _report_rows_that_wrote_nothing(self) -> None:
        """Warn (never fail) about the per-row misses both endpoints can produce."""
        self._report_apps_not_in_graph()
        self._report_apps_without_edge()

    def _report_apps_not_in_graph(self) -> None:
        """Rows whose ``MATCH (a:BusinessApplication ...)`` found nothing.

        These write NOTHING — not the edge, not even ``batch_orchestrator_raw``
        — so they are invisible in the graph and in the CLI coverage report,
        which counts crosswalk hits on the SOURCE side and would happily read
        "3/3 mapped" while three rows landed nowhere.
        """
        if not self.seal_ids_sent:
            return
        rows = self.client.run(
            "UNWIND $seal_ids AS sid "
            "OPTIONAL MATCH (a:BusinessApplication {seal_id: sid}) "
            "WITH sid, a WHERE a IS NULL "
            "RETURN sid AS seal_id ORDER BY seal_id",
            seal_ids=sorted(self.seal_ids_sent),
        )
        self.apps_not_in_graph = [r["seal_id"] for r in rows]
        if not self.apps_not_in_graph:
            return
        LOGGER.warning(
            "Loader %s: %d of %d row(s) named a :BusinessApplication that is not in "
            "this database — nothing was written for them, not even the raw "
            "orchestrator string (seal_id(s): %s). The SEAL capture and the graph "
            "have drifted; re-run the SEAL application load.",
            self.name,
            len(self.apps_not_in_graph),
            len(self.seal_ids_sent),
            ", ".join(self.apps_not_in_graph),
        )

    def _report_apps_without_edge(self) -> None:
        """Apps this run stamped that ended up with no batch-port edge.

        Asks the graph what actually happened rather than re-deriving it from
        the rows. Two distinct causes, split apart because they need different
        actions: ``batch_orchestrator_unmapped`` means platforms.yaml has no
        ``software_registry_ref`` for the string (a CONFIG gap — extend the
        crosswalk, gate the new seed row); anything else means the crosswalk
        DID resolve but that product is missing from the registry (a LOAD gap —
        the registry is present but incomplete, which the whole-registry
        refusal above cannot see).
        """
        rows = self.client.run(
            "MATCH (a:BusinessApplication {batch_orchestrator_last_run_id: $run_id}) "
            "WHERE NOT (a)-[:USES_SOFTWARE {source: 'batch-port'}]->(:SoftwareProduct) "
            "RETURN a.seal_id AS seal_id, "
            "       a.batch_orchestrator_raw AS orchestrator_raw, "
            "       a.batch_orchestrator_unmapped AS unmapped "
            "ORDER BY seal_id",
            run_id=self.run_id,
        )
        self.apps_without_edge = [dict(r) for r in rows]
        if not self.apps_without_edge:
            return
        missing_product = [r for r in self.apps_without_edge if not r.get("unmapped")]
        LOGGER.warning(
            "Loader %s: %d app(s) stamped WITHOUT a USES_SOFTWARE {source:'batch-port'} "
            "edge (%d unmapped in platforms.yaml, %d resolved to a product that is not "
            "in the registry).",
            self.name,
            len(self.apps_without_edge),
            len(self.apps_without_edge) - len(missing_product),
            len(missing_product),
        )
        for row in missing_product:
            LOGGER.warning(
                "Loader %s: app %s declares '%s' — the platforms.yaml crosswalk "
                "resolved it, but no matching :SoftwareProduct is in this database. "
                "The registry is present but incomplete; re-run "
                "`drydocs load-software-registry`.",
                self.name,
                row.get("seal_id"),
                row.get("orchestrator_raw"),
            )
