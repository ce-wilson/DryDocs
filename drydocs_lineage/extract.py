"""Derive lineage candidates from job command lines (the shared-parser seam).

All parsing is ``drydocs_core.controlm`` — this module only interprets the parsed
``Invocation`` / ``FileOp`` stream into dataset/file lineage *candidates*. A candidate
is uncertain by construction; it becomes ground truth only through curation.
"""
from __future__ import annotations

from dataclasses import dataclass

from drydocs_core.controlm import FileOp, Invocation, parse_command  # noqa: F401  (the shared parser surface)

from .curation import CurationStatus


@dataclass(frozen=True)
class LineageCandidate:
    """One derived lineage edge candidate: a job touching a file/dataset."""

    job_name: str
    direction: str                 # reads | writes (from the FileOp role)
    file_ref: str                  # canonicalized file reference (core's build_file_ref)
    evidence: str                  # the invocation fragment it was derived from
    status: CurationStatus = CurationStatus.PROPOSED


def extract_candidates(job_name: str, cmd_line: str) -> list[LineageCandidate]:
    """Parse ``cmd_line`` via the core parser and derive lineage candidates."""
    raise NotImplementedError(
        "populated by the depgraph-prototype re-home — see G9 + ADR 0002-C"
    )
