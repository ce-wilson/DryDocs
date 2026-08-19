"""drydocs-deepdoc — reactive, on-demand deep documentation (ADR 0002 D2, C3; G4).

The same dependency analysis as ``drydocs_lineage`` — the shared parser in
``drydocs_core.orchestration.controlm`` — run **reactively when a failure needs context**, writing
its findings as **:Uncertain-labeled** rows with ``reliability`` / ``trust``
stamped on every node and edge. Per D2 deepdoc is the SINGLE uncertain write
boundary; since the G102 fold (2026-08-18) the trust axis is the :Uncertain
LABEL in the one content database (pre-fold it was the retired ``ddcontext``
database boundary). Deepdoc never writes unlabeled ground truth; promotion of
an uncertain finding is a separate HITL-gated write through the loader path
(``status: proposed`` → confirmed), never an in-place label strip.

Linkage is the **proxy-node pattern** (ADR 0002 D1): findings reference real
jobs/assets by the shared DryDocs URN business key (``:ControlMJob {jobId}`` /
``:DataAsset {assetId}``) rather than copying ground-truth properties onto
finding rows.

Invariants:

- **Every write carries :Uncertain**, and never without reliability/trust stamps.
- **Imports only ``drydocs_core.*``** (boundary group ``deepdoc``); never
  ``drydocs_lineage`` — the two integrate through the graph, not in-process calls.
- **The parser is core's** — parse gaps become core changes, never local forks.

Scaffold status (2026-07-10, G4): interfaces + contracts; bodies raise
``NotImplementedError``. Trigger wiring (on-failure) is later work by design.
"""

from . import investigate, writer

#: The write target. Name per the DEPLOYED topology (``drydocs`` / ``ddschema``,
#: created by ``drydocs_core/schema/provisioning/01_databases.cypher``;
#: ``ddlineage`` retired 2026-08-04, ADR 0002 X1 amendment; ``ddcontext`` and
#: ``ddall`` retired 2026-08-18 at the G32/G102 fold).
#: ADR 0002's original ``drydocs_context`` was superseded by the G6/G7 deploy and
#: that supersession is recorded in ADR 0006 §1 + the gate-log dd*-convention entry.
#: ``tests/unit/test_database_names.py`` pins this to what provisioning creates.
DATABASE = "drydocs"  # G102 (2026-08-18): the fold — uncertain writes land in ground truth CARRYING :Uncertain (writer contract); was the retired `ddcontext`

__all__ = ["DATABASE", "investigate", "writer"]
