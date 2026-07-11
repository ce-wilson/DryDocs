"""drydocs-lineage — proactive, curated command-line lineage (ADR 0002 D2, C2; G4).

Deepens job lineage starting from the **job command line**: the shared parser in
``drydocs_core.controlm`` (``parse_command`` / ``extract_container_command`` /
``build_file_ref``) turns CMD_LINE into invocations and file references; this component
derives dataset/file lineage candidates from them, runs them through **phased HITL
curation**, and writes ONLY the curated result to the **ground-truth** database
(``drydocs``) — that write is what distinguishes it from ``drydocs_deepdoc``
(reactive, uncertain, ``drydocs_context``). Per D2 the two are deliberately separate
components: each owns only its trigger, write target, and trust handling, and they
never import each other (boundary test enforces).

Invariants:

- **Curated-only writes.** Nothing reaches ``drydocs`` without passing curation
  (``status: proposed`` → confirmed via the HITL gate flow) — an uncurated candidate
  is deepdoc/context material, not ground truth.
- **Imports only ``drydocs_core.*``** (boundary group ``lineage``).
- **The parser is core's.** Any parse gap found here becomes a core change, never a
  local fork (the G3/0002-B rule, same reasoning).

Scaffold status (2026-07-10, G4): interfaces + contracts; bodies raise
``NotImplementedError``. The population path is the depgraph-prototype re-home —
see G9 + ADR 0002-C. Trigger wiring (phased curation cadence) is later work by design.
"""
from . import curation, extract, writer

#: The write target — ground truth. The trust axis IS the DB boundary (ADR 0002 D1).
DATABASE = "drydocs"

__all__ = ["DATABASE", "curation", "extract", "writer"]
