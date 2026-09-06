"""The log-estate read surface (O68).

One handler, framework-free, in its own module — the same shape as
``handlers.py``: a function over injectable inputs that ``app.py`` wires to a
route in four lines. That keeps the API slice of this item small on purpose, so
the route table gains one entry and the logic is testable with no server.

IT COMPUTES NOTHING. ``drydocs_core.log_estate`` walks the directories and
``drydocs_core.data_zones`` inventories the zones; this shapes what they return
for the wire. O68 clause (b) is explicit that the byte sum belongs in core, and
the reason is not tidiness: a size computed here would be a second answer, free
to disagree with the count standing beside it.

THE DEBUG TIER IS REPORTED, NEVER RENDERED (clause c). ADR 0014 clause 6 splits
the lean API log from a verbose short-retention debug log that carries Cypher
text and request detail. CAPTURING that is ruled; SURFACING it is not, and they
are different risks — a short-lived file on an operator's disk versus a rendered
page anyone with the console can read. So this returns a kind's SIZE, RETENTION
and AGE like any other kind's, and there is no route, field or parameter here
through which a log's contents can be requested. That is a property of the
module, not a promise in a comment: nothing below opens a file.
"""

from __future__ import annotations

from typing import Any

from drydocs_core.data_zones import inventory
from drydocs_core.log_estate import estate


def log_estate() -> dict[str, Any]:
    """The admin panel's payload: every declared kind, and every declared zone.

    Both halves are here because the SME's question spans them — "where do my
    logs live and how much is there" is the same question as "where did my
    extracts go", and G109's zone inventory already answered the second.
    """
    kinds = [
        {
            "id": e.kind.id,
            "level": e.kind.level,
            "retention_days": e.kind.retention_days,
            "rotation": e.kind.rotation,
            "format": e.kind.format,
            "status": e.kind.status,
            "dir": e.kind.dir,
            "path": str(e.path),
            "exists": e.exists,
            "file_count": e.file_count,
            "total_bytes": e.total_bytes,
            "oldest_days": e.oldest_days,
            "over_retention": e.over_retention,
        }
        for e in estate()
    ]
    zones = [
        {
            "id": s.zone.id,
            "path": str(s.zone.path),
            "mode": s.zone.mode,
            "exists": s.exists,
            "file_count": s.file_count,
            "total_bytes": s.total_bytes,
            "empty": s.empty,
        }
        for s in inventory()
    ]
    return {"kinds": kinds, "zones": zones}
