"""drydocs-core — shared transformation surface (TRANSITIONAL SHIM · ADR 0002-a Phase B, step 1).

Realizes the first, zero-risk step of the core extraction
([0002-a §6 step 1](../docs/decisions/0002-a-drydocs-core-extraction-plan.md)):
introduce the `drydocs_core` package and **re-export** the shared surface while the files
physically still live under `drydocs/`. Components import from `drydocs_core.*` instead of
`drydocs.*`; when the modules later relocate into this package (Phase B step 2+), only these
re-exports flip — no component import site changes.

Surface (per 0002-a §3): the shared models, adapters, the Control-M command-line/lineage
parser (`controlm`), the Neo4j driver, the config layer (`config` / `precedence` /
`source_registry`), and the ontology namespaces. It **never** re-exports loaders / cli /
snapshots — that is the component layer (enforced by `tests/unit/test_module_boundary.py`).

Usage during the shim::

    from drydocs_core import controlm, models
    client = drydocs_core.Neo4jClient(uri, user, password, database="drydocs_context")
"""
from drydocs import adapters, config, controlm, models, ontology, precedence, source_registry
from drydocs.neo4j_client import Neo4jClient

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
