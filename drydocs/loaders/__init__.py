"""Loaders — one per source. Each loader is the canonical bridge between
a row stream (via an Adapter) and Cypher MERGE statements.
"""

from .base import BaseLoader, LoadSummary

__all__ = ["BaseLoader", "LoadSummary"]
