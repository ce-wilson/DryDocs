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

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Iterator

import yaml

from drydocs_core.models.registry import BatchPortOrchestratorRow
from .base import BaseLoader

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

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

    def __enter__(self) -> "BatchOrchestratorYamlAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: "TracebackType | None",
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
    name: ClassVar[str] = "batch_port_orchestrator.v1"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "batch_port_orchestrator.cypher"
    row_model: ClassVar[type] = BatchPortOrchestratorRow
    source_label: ClassVar[str] = "taxonomy"
