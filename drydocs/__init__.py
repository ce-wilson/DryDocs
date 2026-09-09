"""The drydocs-load component: the loaders, the CLI, and the load-cadence tooling.

What remains of the original single package after the ADR 0002-A-1 split moved the
pure parse/resolve/model/driver layer to ``drydocs_core``. Everything here either
WRITES the graph or owns a run cadence, which is the placement test that decides
what belongs on this side of the line. The name is kept until Phase C.
"""

__version__ = "0.3.0"
