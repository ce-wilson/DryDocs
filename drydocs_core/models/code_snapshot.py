"""Row model for the self-documentation code-snapshot load (G33 / Epic U).

One row per FILE node of the newest dependency-mode depgraph snapshot
(``knowledge/depgraph-snapshots/drydocs-*.json``, schema
depgraph-machine-first/v1, ``meta.tree == false``). The adapter denormalizes
the snapshot's ``meta`` block (capture time + git provenance) onto every row
so the Cypher can MERGE the single ``:Project`` root idempotently.

Gate ``self-documentation-code-graph`` SIGNED OFF 2026-07-27
(config/gate-prompts/self-documentation-code-graph.yaml, 36/36):
  * §B1(a) — ONE :Project root; the six scan roots are the ``project``
    PROPERTY here, never nodes.
  * §C1(a)/§C2 — key is ``file_id`` (repo-relative path, forward slashes);
    the only non-colliding key (``name`` collides 15 ways on '__init__.py',
    ``rel_path`` collides across scan roots).
  * §C3 — ``circular`` loads as a property (what the scanner concluded at
    capture time).
  * §E1(b) — ``language_iri`` is derived from ``extension`` by the adapter
    and targets the ALREADY-SEEDED SwoClass term; None means "no seeded term
    for this extension" and the Cypher skips the IS_ENCODED_IN edge.
  * §H4 — ``abs_path`` is DROPPED: it never reaches this model.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CodeModuleRow(BaseModel):
    """One :CodeModule node row + its outbound IMPORTS targets."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",  # abs_path (and anything future) is dropped, not rejected
    )

    # ---- node identity + properties (gate §C) -----------------------------
    file_id: str = Field(
        ...,
        min_length=1,
        description=":CodeModule key — repo-relative path, e.g. 'drydocs_core/models/seal.py'.",
    )
    project: str = Field(
        ...,
        min_length=1,
        description="Scan root this file belongs to (one of six) — a PROPERTY per §B1(a).",
    )
    rel_path: str = Field(..., description="Path relative to the scan root (collides across roots).")
    name: str = Field(..., description="Bare file name (collides 15 ways on '__init__.py').")
    extension: str = Field(..., description="File extension, '.py' for every dependency-mode node.")
    circular: bool = Field(
        default=False,
        description="Scanner's circular-import verdict AT CAPTURE TIME (§C3 — load it).",
    )

    # ---- outbound dependency edges (gate §D) -------------------------------
    imports: list[str] = Field(
        default_factory=list,
        description="file_ids this file imports (direction importer -> imported, §D1).",
    )

    # ---- SWO binding (gate §E1(b)) -----------------------------------------
    language_iri: str | None = Field(
        default=None,
        description="IRI of the seeded SwoClass language term derived from extension; "
        "None = no seeded term, IS_ENCODED_IN edge skipped for this row.",
    )

    # ---- :Project root + snapshot provenance (denormalized meta) -----------
    project_id: str = Field(
        ...,
        min_length=1,
        description="The single :Project root key (§B1(a)) — 'drydocs' for this repo.",
    )
    captured_at: str = Field(..., description="meta.captured_at ISO timestamp of the snapshot.")
    git_commit: str = Field(default="", description="meta.git.commit (short) the snapshot describes.")
    git_full: str = Field(default="", description="meta.git.full — full commit hash.")
    git_branch: str = Field(default="", description="meta.git.branch at capture.")
    git_dirty: bool = Field(default=False, description="meta.git.dirty — worktree had uncommitted changes.")
