"""Business segment refresh loader.

M0 ``ontology.cypher`` already seeded JPMC + 4 current + 1 retired segment.
This loader is a no-op refresh path used when the annual report changes
(e.g., another reorg) — it tweaks ``effective_to`` on existing edges and
adds new segments without disturbing the seeded set.

For phase 1 this is rarely needed; it lives here to keep the loader-set
exhaustive and to give the CLI a target to call when manually triggered.
"""
from __future__ import annotations

import logging

from ..neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)


def refresh_business_segments(client: Neo4jClient) -> dict:
    """Verify the M0-seeded segments are still present; return a count.

    A real refresh — adding a new segment, retiring one — should be done by
    editing ``ontology.cypher`` and re-running ``drydocs bootstrap`` with
    ``--skip-constraints``. Don't put corporate-org changes in CSV land.
    """
    rows = client.run(
        """
        MATCH (c:Company {name:'JPMC'})-[r:HAS_BUSINESS_SEGMENT]->(s:BusinessSegment)
        RETURN count(*) AS n_active,
               collect(s.code) AS codes
        """
    )
    n = rows[0]["n_active"] if rows else 0
    codes = rows[0]["codes"] if rows else []
    LOGGER.info("Business segments active: %s = %s", n, codes)
    return {"active_segments": n, "codes": codes}
