"""At/above-Application snapshot writer (v3 §I).

5-year rolling retention; runs at the end of every ``refresh-reference``.
"""
from .writer import SnapshotWriter

__all__ = ["SnapshotWriter"]
