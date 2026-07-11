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

Status (2026-07-10): G4 scaffold + the G9 re-home first slice (ADR 0002-C §4) —
``model`` (the depgraph lineage layer reconciled to DryDocs identity: the ControlMJob
NODE-KEY composite, the registered gate-bound rel vocabulary m3_invokes / m3_triggers /
m3_reads_from / m3_writes_to) and ``extractors.controlm_inventory`` (CSV projection →
ProcessNodes + INVOKES candidates, parsing via the SHARED core parser — the depgraph
fork is retired). STILL STUBS: ``curation.curate`` (phased cadence) and
``writer.write_curated`` (Fork-3 mechanics, next slice; rel vocabulary is gate-bound —
no live load before the HITL gate).
"""
from . import curation, extractors, model, writer

#: The write target — ground truth. The trust axis IS the DB boundary (ADR 0002 D1).
DATABASE = "drydocs"

__all__ = ["DATABASE", "curation", "extractors", "model", "writer"]
