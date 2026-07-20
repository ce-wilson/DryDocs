"""Source adapters — CSV today, Oracle from day one (BMC, HR), Oracle in
phase 2 (SEAL, PAT), Oracle in phase 3 (ServiceNow). The adapter abstraction
lets loaders stay source-agnostic; the phase-2 swap is configuration only.
"""

from .base import Adapter
from .csv_adapter import CsvAdapter
from .oracle_adapter import OracleAdapter

__all__ = ["Adapter", "CsvAdapter", "OracleAdapter"]
