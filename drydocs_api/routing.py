"""Per-view database routing — the trust axis enforced server-side.

Which database a console view reads (``drydocs`` ground truth vs the
``ddall`` composite that includes uncertain ``ddcontext`` content)
is a ROUTING DECISION made here, never by whatever string reaches a client
session option (ADR 0005 force 2 / ADR 0002 D1). Every named query and the
raw-Cypher endpoint resolve their database through this map.
"""

from __future__ import annotations

# View id -> database. All current views read ground truth only; a view that
# deliberately surfaces uncertain context (e.g. a deepdoc findings panel)
# gets an explicit 'ddall' row HERE, through review — never a default.
VIEW_DATABASES: dict[str, str] = {
    "overview-counts": "drydocs",
    "folder-census": "drydocs",
    "dependency-chain": "drydocs",
    "c4-graph": "drydocs",
    "raw-cypher": "drydocs",
}


class UnknownViewError(KeyError):
    """Raised for a view id with no routing row — fail closed, never default."""


def database_for(view: str) -> str:
    try:
        return VIEW_DATABASES[view]
    except KeyError as exc:
        raise UnknownViewError(
            f"no database routing for view '{view}' — add an explicit VIEW_DATABASES row"
        ) from exc
