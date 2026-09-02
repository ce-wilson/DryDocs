"""drydocs-deepdoc — the corpus-driven investigator, seeded from the grounded graph (ADR 0002 D2 C3; G4; charter ruled at gate document-content-topology, G32, 2026-08-18).

THE CHARTER (G32 ruling, restated here at MM1 2026-08-21 — the earlier "reactive
on-failure deep dive" into a separate uncertain database is retired): deepdoc is a
**corpus-driven retriever seeded from the grounded graph**. It starts from a
subject that ALREADY EXISTS in ``drydocs`` (a job, a folder, an application, a
data flow), searches the document corpus and the SDLC surfaces for what is said
about it, and lands what it finds as **:Uncertain-labeled** findings with
``reliability`` / ``trust`` stamped on every node and edge. **It creates no
relationship whose subject is not already in the graph.** The parser-driven
command-line reading (``drydocs_core.orchestration.controlm``, the same parser
``drydocs_lineage`` runs) is an INPUT to an investigation, not a rival to it.

THE WRITE TARGET is ``drydocs`` — the one content database since the G102 fold
(2026-08-18) — and the boundary is the :Uncertain LABEL, not a database: deepdoc
never writes unlabeled ground truth, and promotion of a finding is a separate
HITL-gated write through the loader path (``status: proposed`` → confirmed),
never an in-place label strip. Linkage is the proxy-node pattern (ADR 0002 D1):
findings reference real subjects by their DryDocs business key
(``:ControlMJob {jobId}`` / ``:DataAsset {assetId}``), never by copying
ground-truth properties onto finding rows.

THE METHOD, from the first hand-run investigation (2026-08-20; synthesis in
docs/design/deepdoc-data-flow-overview.md; epic MM): a central question, a
mind map whose EMPTY slots direct the next search, identifier decomposition
(folder name → application / zone / cadence), the application chase across
sources, the producer/consumer split — graph-seeded retrieval in practice.
``investigate()`` v1 (MM10) is that skeleton; MM3-MM6 are its state file,
entity extractor, per-tool connectors and ontology proposals.

Invariants:

- **Every write carries :Uncertain**, and never without reliability/trust stamps
  (``tests/unit/test_uncertain_boundary.py``).
- **Imports only ``drydocs_core.*``** (boundary group ``deepdoc``); never
  ``drydocs_lineage`` or ``drydocs_docmeta`` — deepdoc CONSUMES the docmeta
  corpus through the graph, never in-process.
- **The parser is core's** — parse gaps become core changes, never local forks.

Scaffold status: interfaces + contracts (G4, 2026-07-10); the ``investigate``
and ``writer`` bodies raise ``NotImplementedError`` until MM10. ``mindmap`` and
``search_log`` (MM3) are real: the state file the loop reads, where a slot fills
only with evidence, and the per-search ledger whose every row names the slot it
was for and the ids it was the first to find.
"""

import logging

from . import investigate, mindmap, search_log, writer

#: G105/ADR 0014 clause 2 — a module logger per component. These components
#: had NONE, so anything they wanted to say had nowhere to go. A component
#: never calls basicConfig: configuring the root logger steals it from the
#: caller, which is why drydocs.cli owns the one dictConfig call.
LOGGER = logging.getLogger(__name__)

#: The write target. Name per the DEPLOYED topology (``drydocs`` / ``ddschema``,
#: created by ``drydocs_core/schema/provisioning/01_databases.cypher``;
#: ``ddlineage`` retired 2026-08-04, ADR 0002 X1 amendment; the separate
#: uncertain and union databases retired 2026-08-18 at the G32/G102 fold —
#: the retired names are pinned in tests/unit/test_database_names.py).
#: ADR 0002's original ``drydocs_context`` was superseded by the G6/G7 deploy and
#: that supersession is recorded in ADR 0006 §1 + the gate-log dd*-convention entry.
#: ``tests/unit/test_database_names.py`` pins this to what provisioning creates.
DATABASE = "drydocs"  # G102 (2026-08-18): the fold — uncertain writes land in ground truth CARRYING :Uncertain (writer contract); the pre-fold separate database is retired

__all__ = ["DATABASE", "investigate", "mindmap", "search_log", "writer"]
