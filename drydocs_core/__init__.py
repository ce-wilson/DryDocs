"""drydocs-core — shared transformation surface (ADR 0002-a Phase B, physical).

The core modules physically live HERE as of the Phase B relocate
([0002-a](../docs/decisions/0002-a-drydocs-core-extraction-plan.md), thin variant per
[0002-a-1](../docs/decisions/0002-a-1-phase-b-thin-relocate.md)): the shared models,
adapters, the orchestration parser surface (`orchestration`, with `orchestration.controlm`
beneath it — S2/ADR 0008), the Neo4j driver, the
config layer (`config` / `precedence` / `source_registry`), the ontology namespaces +
vocabulary, and the schema/ontology `.cypher` resources.

Core imports nothing from any component; components (the `drydocs` package: loaders /
cli / snapshots / review / plan / docgen) import only `drydocs_core.*` — enforced by
`tests/unit/test_module_boundary.py`. The load-cadence staging bundle builder lives
component-side as `drydocs.staging` (0002-a §6 borderline decision).

Usage::

    from drydocs_core import models, orchestration
    from drydocs_core.orchestration import controlm
    client = drydocs_core.Neo4jClient(uri, user, password, database="drydocs")

WHAT OF CORE IS PUBLIC IS NOT ``__all__`` (CORE12, 2026-09-10). ``__all__`` below
is the star-import surface and is correct as that; the IMPORT CONTRACT — which of
core's 39 modules a component may name — is
``drydocs_core.component_map.PUBLIC_MODULES``, enforced default-deny by
``tests/unit/test_module_boundary.py``. The two are deliberately different
objects: the seven names here are EAGERLY imported, so growing this list to the
whole contract would make ``import drydocs_core`` pull in yaml, neo4j and
pydantic-settings, and a contract must not be paid for at import time. The
reasoning, and the measurement behind it, sit with the registry.
"""

from . import adapters, config, models, ontology, orchestration, precedence, source_registry
from .neo4j_client import Neo4jClient

__all__ = [
    "adapters",
    "config",
    "orchestration",
    "models",
    "ontology",
    "precedence",
    "source_registry",
    "Neo4jClient",
]
