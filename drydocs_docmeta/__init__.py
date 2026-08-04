"""``drydocs-docmeta`` — the document-ingestion component (ADR 0006, backlog Q6).

Proactive corpus ingestion: it acquires documentation from a registered
source, cleans and hashes it, and hands the result to the load path. It is
deliberately NOT ``drydocs-deepdoc`` — that component is reactive, on-failure,
on-demand and writes uncertain findings to ``ddcontext``; this one runs on a
refresh cadence and feeds ``dddocs``. The Q4 gate (2026-07-18) ruled them
separate, with deepdoc a CONSUMER of this corpus.

Boundary: imports ``drydocs_core`` only, never another component. CLI verbs
wire into ``drydocs/cli.py`` through the entrypoint exemption rather than
growing a second CLI package (the MODULE_MAP canonical resolution).

Layer discipline (CLAUDE.md §1): registering and fetching a doc source is
TAXONOMY. Extracting meaning from doc content is an ontology decision and goes
through ``relationship_vocabulary.yaml`` ``status: planned`` plus the HITL
gate. Nothing here invents a relationship type.
"""

from __future__ import annotations

__all__ = ["__doc__"]
