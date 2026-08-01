"""Phased HITL curation — the gate between candidates and ground truth.

The component is *proactive/curated* (ADR 0002 D2): candidates arrive in phases
(estate slices), a human confirms or rejects, and only confirmed candidates may be
written. The cadence/trigger wiring is later work; the state model is the contract.
"""

from __future__ import annotations

from enum import Enum


class CurationStatus(str, Enum):
    PROPOSED = "proposed"  # derived, unreviewed — never written to ground truth
    CONFIRMED = "confirmed"  # human-accepted — eligible for the drydocs write
    REJECTED = "rejected"  # human-declined — kept for audit, never written


def curate(candidates: list, decisions: dict[str, CurationStatus]) -> list:
    """Apply human curation decisions to candidates (phased batches)."""
    raise NotImplementedError("curation cadence lands with the phased trigger wiring")
