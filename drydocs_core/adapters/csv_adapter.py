"""CSV adapter.

Phase-1 SEAL/PAT/ServiceNow extracts arrive as CSV (saved that way for clean
APOC ingestion). The adapter normalizes header casing and yields dicts.

The implementation uses Python's stdlib ``csv`` rather than pandas so we
don't pay the pandas import cost for every loader; pandas is still in
``pyproject.toml`` for analytical work but loaders don't need it.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterator

LOGGER = logging.getLogger(__name__)


class CsvAdapter:
    """Stream rows from a UTF-8 CSV file with a header row.

    Header keys are lowercased and stripped. Empty cells are kept as empty
    strings (not None) so downstream pydantic coercers see a consistent shape.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8-sig",  # tolerates BOM from Excel exports
        delimiter: str = ",",
    ) -> None:
        self.path = Path(path)
        self.encoding = encoding
        self.delimiter = delimiter
        self.name = f"csv:{self.path.name}"
        self._fh = None  # type: ignore[assignment]

    def __enter__(self) -> "CsvAdapter":
        if not self.path.exists():
            raise FileNotFoundError(f"CSV not found: {self.path}")
        self._fh = open(self.path, encoding=self.encoding, newline="")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def rows(self) -> Iterator[dict]:
        if self._fh is None:
            raise RuntimeError("CsvAdapter must be used as a context manager")
        reader = csv.DictReader(self._fh, delimiter=self.delimiter)
        if reader.fieldnames is None:
            LOGGER.warning("CSV %s has no header row", self.path)
            return
        # Lowercase + strip header keys, keep value strings as-is.
        norm_fields = [f.strip().lower() for f in reader.fieldnames]
        for raw in reader:
            yield {
                norm: ("" if raw.get(orig) is None else str(raw[orig]))
                for orig, norm in zip(reader.fieldnames, norm_fields)
            }
