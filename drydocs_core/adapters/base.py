"""Adapter Protocol.

Every loader takes an Adapter; concrete adapters know how to yield raw row
dicts from a source. Validation happens downstream in the row model, so
adapters return strings as-is and let pydantic coerce.
"""
from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable


@runtime_checkable
class Adapter(Protocol):
    """Yield raw dict rows from a source.

    Implementations must be context managers so connection / file handles
    are released even on partial reads.
    """

    name: str  # short identifier used in log lines (e.g. 'csv:seal_apps', 'oracle:lobs')

    def __enter__(self) -> "Adapter":
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        ...

    def rows(self) -> Iterator[dict]:
        """Yield one dict per source row. Keys lowercased; values left as strings."""
        ...
