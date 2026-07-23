"""Shared Neo4j access for the DryDocs ADK agents.

One module-level driver per process — drivers own a connection pool and are
thread-safe; creating one per call is both slow and the classic leak vector.
`execute_query()` opens and closes its session internally, so this module
holds no per-request state (memray/tracemalloc against the api_server process
should show a flat baseline under repeated tool calls).
"""

import os

import neo4j
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

_driver: neo4j.Driver | None = None

# Read-only guard for LLM-driven tools: graph writes go through the DryDocs
# loaders + HITL gate, never through a chat agent.
_WRITE_TOKENS = ("create ", "merge ", "delete ", "set ", "remove ", "drop ", "load csv")


def _get_driver() -> neo4j.Driver:
    global _driver
    if _driver is None:
        _driver = neo4j.GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
        )
    return _driver


def get_driver() -> neo4j.Driver:
    """Public accessor for the shared driver (graph_read.py; one pool per process)."""
    return _get_driver()


def read_cypher(query: str) -> dict:
    """Run a read-only Cypher query against the DryDocs knowledge graph.

    Args:
        query: A Cypher read query (MATCH/RETURN). Write clauses are rejected.

    Returns:
        dict with status, rowCount, keys and up to 100 result records.
    """
    normalized = " " + " ".join(query.lower().split()) + " "
    if any(tok in normalized for tok in _WRITE_TOKENS):
        return {"status": "error", "error": "write operations are not allowed from this tool"}
    try:
        result = _get_driver().execute_query(
            query,
            database_=os.getenv("NEO4J_DATABASE", "neo4j"),
            routing_=neo4j.RoutingControl.READ,
        )
        records = [r.data() for r in result.records]
        return {
            "status": "success",
            "rowCount": len(records),
            "keys": list(result.keys),
            "records": records[:100],
        }
    except Exception as exc:  # surface driver errors to the agent, don't crash the run
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def graph_schema() -> dict:
    """Return the node labels, relationship types and property keys present in the graph."""
    try:
        driver = _get_driver()
        db = os.getenv("NEO4J_DATABASE", "neo4j")
        labels = [r["label"] for r in driver.execute_query("CALL db.labels() YIELD label RETURN label", database_=db).records]
        rels = [r["relationshipType"] for r in driver.execute_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType", database_=db).records]
        props = [r["propertyKey"] for r in driver.execute_query("CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey", database_=db).records]
        return {"status": "success", "labels": labels, "relationshipTypes": rels, "propertyKeys": props}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def graph_schema_detailed() -> dict:
    """graph_schema() plus per-label property keys — text2cypher grounding needs to
    know WHICH label owns a property (the flat propertyKeys list made the model
    guess ControlMFolder.name where the real key is sched_table)."""
    base = graph_schema()
    try:
        records = _get_driver().execute_query(
            "CALL db.schema.nodeTypeProperties() "
            "YIELD nodeLabels, propertyName RETURN nodeLabels, propertyName",
            database_=os.getenv("NEO4J_DATABASE", "neo4j"),
        ).records
        by_label: dict[str, set] = {}
        for r in records:
            for label in r["nodeLabels"]:
                if r["propertyName"]:
                    by_label.setdefault(label, set()).add(r["propertyName"])
        base["propertiesByLabel"] = {k: sorted(v) for k, v in sorted(by_label.items())}
    except Exception:
        pass  # older servers without the procedure — flat propertyKeys still present
    return base
