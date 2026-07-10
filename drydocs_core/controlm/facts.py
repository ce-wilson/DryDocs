"""Route SEMANTIC_FACT variables to STG_APP_FACT / STG_NOTIFICATION (Phase C).

The Phase-A classifier already tags each fact-bearing variable with a
``fact_type`` (via FACT_REGISTRY). This module turns those into staging
rows: notification facts split on ``;`` into one STG_NOTIFICATION row per
address; everything else becomes one STG_APP_FACT row, carrying the env
tag when the variable was part of a _D/_Q/_P triplet.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .variables import ClassifiedVariable

_ADDR_SPLIT_RE = re.compile(r"[;,]")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class AppFact:
    fact_type: str
    fact_value: str
    environment: str | None
    source_var: str


@dataclass(frozen=True)
class Notification:
    channel: str
    address: str
    source_var: str


def route_fact(
    cv: ClassifiedVariable, resolved_value: str
) -> tuple[list[AppFact], list[Notification]]:
    """Split one classified SEMANTIC_FACT variable into app-fact and/or
    notification rows. Non-fact variables yield nothing."""
    if cv.fact_type is None:
        return [], []

    value = (resolved_value or cv.raw_value or "").strip()
    if not value:
        return [], []

    if cv.fact_type == "NOTIFICATION":
        notes: list[Notification] = []
        for part in _ADDR_SPLIT_RE.split(value):
            addr = part.strip()
            if not addr:
                continue
            channel = "EMAIL" if _EMAIL_RE.match(addr) else "OTHER"
            notes.append(Notification(channel=channel, address=addr[:320],
                                      source_var=cv.raw_name))
        return [], notes

    return [AppFact(
        fact_type=cv.fact_type,
        fact_value=value[:500],
        environment=cv.env_candidate if cv.env_tag else None,
        source_var=cv.raw_name,
    )], []
