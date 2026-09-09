"""The unit suite: everything that runs with no database and no network.

A package rather than a bare directory so modules here can import each other and
the shared helpers at the tests root (``tests.source_scan``, ``tests.env_drift``).
This is the suite CI blocks on.
"""
