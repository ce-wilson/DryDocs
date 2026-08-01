"""Named queries shaped for the console's views (ADR 0005 decision 2).

The first two non-trivial entries are the support queries proven live on the
internal graph 2026-07-14 (IDEAS capture, mechanism-only): the dependency-chain
finder and the folder-scoped dependency census. Parameters are declared and
validated here — unknown or missing params fail closed before any driver call.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParamSpec:
    name: str
    type: str  # 'string' | 'int'
    required: bool = True
    default: object | None = None


@dataclass(frozen=True)
class NamedQuery:
    id: str
    description: str
    cypher: str
    params: tuple[ParamSpec, ...] = field(default=())


NAMED_QUERIES: dict[str, NamedQuery] = {
    q.id: q
    for q in (
        NamedQuery(
            id="overview-counts",
            description="Node label counts — the console's overview/health strip.",
            cypher=("MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC"),
        ),
        NamedQuery(
            id="folder-census",
            description=(
                "Folder-scoped dependency census: edges, distinct successors, and "
                "cross-folder edge count for folders whose sched_table matches."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(s:ControlMJob)"
                "-[:WAS_INFORMED_BY]->(p:ControlMJob) "
                "WHERE f.sched_table CONTAINS $sched_table "
                "RETURN count(*) AS edges, count(DISTINCT s) AS successors, "
                "sum(CASE WHEN NOT (f)-[:CONTAINS_JOB]->(p) THEN 1 ELSE 0 END) "
                "AS cross_folder_edges"
            ),
            params=(ParamSpec("sched_table", "string"),),
        ),
        NamedQuery(
            id="dependency-chain",
            description=(
                "Undirected shortest dependency chain between two jobs — 'how are "
                "these two jobs connected?' with the via-condition per hop."
            ),
            cypher=(
                "MATCH (a:ControlMJob {job_name: $job_a}) "
                "MATCH (b:ControlMJob {job_name: $job_b}) "
                "MATCH p = shortestPath((a)-[:WAS_INFORMED_BY*..15]-(b)) "
                "RETURN [n IN nodes(p) | n.job_name] AS hop_names, "
                "[r IN relationships(p) | r.via_condition] AS via_conditions, "
                "length(p) AS hops"
            ),
            params=(ParamSpec("job_a", "string"), ParamSpec("job_b", "string")),
        ),
        NamedQuery(
            id="c4-graph",
            description=(
                "Graph payload for the console's C4/graph view: dependency edges as "
                "source/target/rel rows, capped."
            ),
            cypher=(
                "MATCH (s:ControlMJob)-[r:WAS_INFORMED_BY]->(t:ControlMJob) "
                "RETURN s.job_name AS source, t.job_name AS target, type(r) AS rel, "
                "r.via_condition AS via_condition LIMIT $limit"
            ),
            params=(ParamSpec("limit", "int", required=False, default=200),),
        ),
    )
}


class UnknownQueryError(KeyError):
    """Raised for a query id not in the registry."""


class ParamValidationError(ValueError):
    """Raised when supplied params don't match the query's declared specs."""


_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
}


def named_query(query_id: str) -> NamedQuery:
    try:
        return NAMED_QUERIES[query_id]
    except KeyError as exc:
        raise UnknownQueryError(query_id) from exc


def validate_params(query: NamedQuery, given: dict[str, object]) -> dict[str, object]:
    """Fail-closed validation: unknown keys rejected, required keys enforced,
    declared types checked, defaults applied. Returns the exact param dict the
    driver receives."""
    declared = {p.name: p for p in query.params}
    unknown = sorted(set(given) - set(declared))
    if unknown:
        raise ParamValidationError(f"unknown params for '{query.id}': {unknown}")
    out: dict[str, object] = {}
    for spec in query.params:
        if spec.name in given:
            value = given[spec.name]
            if not _TYPE_CHECKS[spec.type](value):
                raise ParamValidationError(
                    f"param '{spec.name}' of '{query.id}' must be {spec.type}"
                )
            out[spec.name] = value
        elif spec.required:
            raise ParamValidationError(f"missing required param '{spec.name}' for '{query.id}'")
        elif spec.default is not None:
            out[spec.name] = spec.default
    return out
