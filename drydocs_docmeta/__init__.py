"""``drydocs-docmeta`` — the document-ingestion component (ADR 0006, backlog Q6).

Proactive corpus ingestion: it acquires documentation from a registered
source, cleans and hashes it, and hands the result to the load path. It is
deliberately NOT ``drydocs-deepdoc`` — that component is reactive, on-failure,
on-demand and writes uncertain findings; this one runs on a refresh cadence.
The Q4 gate (2026-07-18) ruled them separate, with deepdoc a CONSUMER of this
corpus. Both now write to ``drydocs``: the G32/G102 fold (2026-08-18)
retired ``ddcontext`` and superseded ``dddocs`` outright as a name nothing
ever provisioned, so the separation is carried by the ``:Uncertain`` LABEL
rather than by storage location -- keying trust on which database a row sat
in was the root cause the gate's section B named.

Boundary: imports ``drydocs_core`` only, never another component. CLI verbs
wire into ``drydocs/cli.py`` through the entrypoint exemption rather than
growing a second CLI package (the MODULE_MAP canonical resolution).

Layer discipline (CLAUDE.md §1): registering and fetching a doc source is
TAXONOMY. Extracting meaning from doc content is an ontology decision and goes
through ``relationship_vocabulary.yaml`` ``status: planned`` plus the HITL
gate. Nothing here invents a relationship type.
"""

from __future__ import annotations

import logging

#: G105/ADR 0014 clause 2 — a module logger per component. The components had
#: NONE, so anything they wanted to say had nowhere to go; the CLI's dictConfig
#: is what gives this a console and a file sink. A component never calls
#: basicConfig: configuring the root logger steals it from the caller.
LOGGER = logging.getLogger(__name__)

__all__ = ["__doc__"]
