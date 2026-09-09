"""The integration suite: tests that need a live Neo4j (Docker/testcontainers).

Opt-in and deselected by default, so a machine with no container runtime still
runs the full unit suite. A package for the same reason ``tests.unit`` is — the
shared helpers at the tests root are importable from both.
"""
