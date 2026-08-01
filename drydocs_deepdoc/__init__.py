"""drydocs-deepdoc — reactive, on-demand deep documentation (ADR 0002 D2, C3; G4).

The same dependency analysis as ``drydocs_lineage`` — the shared parser in
``drydocs_core.controlm`` — run **reactively when a failure needs context**, writing
its findings to the **isolated uncertain** database (``ddcontext``) with
``reliability`` / ``trust`` stamped on every node and edge. Per D2 the trust axis IS
the DB boundary: deepdoc never writes ground truth; promotion of an uncertain finding
into ``drydocs`` is a separate HITL-gated write through the loader path
(``status: proposed`` → confirmed), never an in-place cross-DB edit.

Cross-DB linkage is the **proxy-node pattern** (ADR 0002 D1): findings reference real
jobs/assets by the shared DryDocs URN business key (``:ControlMJob {jobId}`` /
``:DataAsset {assetId}``) so the composite joins without copying ground truth.

Invariants:

- **Writes ONLY ``ddcontext``**, and never without reliability/trust stamps.
- **Imports only ``drydocs_core.*``** (boundary group ``deepdoc``); never
  ``drydocs_lineage`` — the two integrate through the graph, not in-process calls.
- **The parser is core's** — parse gaps become core changes, never local forks.

Scaffold status (2026-07-10, G4): interfaces + contracts; bodies raise
``NotImplementedError``. Trigger wiring (on-failure) is later work by design.
"""

from . import investigate, writer

#: The write target — the isolated uncertain context graph (ADR 0002 D1).
#: Name per the DEPLOYED topology (``drydocs`` / ``ddlineage`` / ``ddcontext`` /
#: ``ddall``, created by ``drydocs_core/schema/provisioning/01_databases.cypher``).
#: ADR 0002's original ``drydocs_context`` was superseded by the G6/G7 deploy and
#: that supersession is recorded in ADR 0006 §1 + the gate-log dd*-convention entry.
#: ``tests/unit/test_database_names.py`` pins this to what provisioning creates.
DATABASE = "ddcontext"

__all__ = ["DATABASE", "investigate", "writer"]
