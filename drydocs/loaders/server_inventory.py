"""Server-inventory loader (Z3; gate server-location-ontology SIGNED OFF
12/12, 2026-08-19 — config/gate-log.md).

Source: ``infra:server-export`` — the infrastructure site's PER-BUSINESS-
APPLICATION server export (CSV; one file per application, both PROD and DR
rows — the prod filter selects applications at download, never rows here).
Produces :Server nodes (the inventory spine, keyed ``name`` — gate §A1),
:DataCenter nodes (PHYSICAL buildings, keyed ``name``, carrying the geography
properties + the Idea-90 ``location_grain`` declaration — §B1/§B2), the
LOCATED_IN placement edges (``infra_located_in``; rack rides the edge), and
the technology-port leg (§C2, the SME reshape): (:BusinessApplication)
-[:HAS_PORT]->(:Port:Technology {kind:'Technology'})-[:RUNS_ON {role:
'technology_port'}]->(:Server).

MATCH-ONLY on :BusinessApplication (the folder_attribution / load-batch-
orchestrators discipline): a row whose ``business_application`` is not in the
graph still loads its Server/DataCenter half, and the missing app is COUNTED
by the coverage query — reported, never guessed, never minted here.

DELIBERATELY NO ``sweep_label``: the extract is a PER-APPLICATION file, so a
full-extract sweep on one application's load would mark every OTHER
application's servers removed. Removal detection for a per-app snapshot is a
future per-scope sweep design, not a wrong flag here.

The ExecutionHost join is NOT this pass — it is the derived resolution pass
(:mod:`drydocs.loaders.server_resolution`), run after this loader and the
hosts pass (the runs_on_resolution precedent).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from drydocs_core.models import ServerInventoryRow

from .base import BaseLoader

#: Apps named by inventory rows but absent from the graph — the §C2 leg
#: skips them (MATCH-only) and this query makes the gap visible.
COVERAGE_QUERY = """
MATCH (s:Server) WHERE NOT s:SchemaMeta
WITH collect(DISTINCT s.owning_app_id) AS app_ids, count(s) AS servers
UNWIND app_ids AS app_id
WITH servers, app_id,
     EXISTS { MATCH (a:BusinessApplication {app_id: app_id}) WHERE NOT a:SchemaMeta } AS known
RETURN servers                                              AS servers,
       count(app_id)                                        AS distinct_apps,
       sum(CASE WHEN known THEN 0 ELSE 1 END)               AS apps_unmatched
"""


class ServerInventoryLoader(BaseLoader):
    name: ClassVar[str] = "server_inventory.v1"
    source_id: ClassVar[str | None] = "infra:server-export"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "server_inventory.cypher"
    )
    row_model: ClassVar[type] = ServerInventoryRow
    source_label: ClassVar[str] = "csv"
    sweep_label: ClassVar[str | None] = None  # per-app files — see the module docstring

    def to_params(self, model: ServerInventoryRow) -> dict[str, Any]:  # type: ignore[override]
        params = super().to_params(model)
        # The Idea-90 declaration (§B2) is computed HERE, not in Cypher: the
        # finest level the row actually supplied, never inferred.
        params["location_grain"] = model.location_grain
        return params
