"""Per-view database routing — the trust axis enforced server-side.

Which database a console view reads is a ROUTING DECISION made here, never by
whatever string reaches a client session option (ADR 0005 force 2 / ADR 0002
D1). Every named query and the raw-Cypher endpoint resolve their database
through this map. Since the G102 fold (2026-08-18) there is ONE content
database — the retired ``ddcontext``/``ddall`` split is gone, and the trust
axis rides the :Uncertain LABEL plus each spec's own ``uncertain`` declaration
(ADR 0011 §117), not a database name.
"""

from __future__ import annotations

# View id -> database. All views read the one content database; a view that
# deliberately surfaces uncertain content (e.g. a deepdoc findings panel)
# declares uncertain=True on its SPEC, through review — never a default.
# (Pre-fold this comment routed such views to the retired 'ddall' composite.)
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
