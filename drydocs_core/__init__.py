"""drydocs-core — shared transformation surface (ADR 0002-a Phase B, physical).

The core modules physically live HERE as of the Phase B relocate
([0002-a](../docs/decisions/0002-a-drydocs-core-extraction-plan.md), thin variant per
[0002-a-1](../docs/decisions/0002-a-1-phase-b-thin-relocate.md)): the shared models,
adapters, the Control-M command-line/lineage parser (`controlm`), the Neo4j driver, the
config layer (`config` / `precedence` / `source_registry`), the ontology namespaces +
vocabulary, and the schema/ontology `.cypher` resources.

Core imports nothing from any component; components (the `drydocs` package: loaders /
cli / snapshots / review / plan / docgen) import only `drydocs_core.*` — enforced by
`tests/unit/test_module_boundary.py`. The load-cadence staging bundle builder lives
component-side as `drydocs.staging` (0002-a §6 borderline decision).

Usage::

    from drydocs_core import controlm, models
    client = drydocs_core.Neo4jClient(uri, user, password, database="drydocs_context")
"""
from . import adapters, config, controlm, models, ontology, precedence, source_registry
from .neo4j_client import Neo4jClient

__all__ = [
    "adapters",
    "config",
    "controlm",
    "models",
    "ontology",
    "precedence",
    "source_registry",
    "Neo4jClient",
]
