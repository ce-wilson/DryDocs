"""drydocs-lineage — proactive, curated command-line lineage (ADR 0002 D2, C2; G4).

Deepens job lineage starting from the **job command line**: the shared parser in
``drydocs_core.orchestration.controlm`` (``parse_command`` / ``extract_container_command`` /
``build_file_ref``) turns CMD_LINE into invocations and file references; this component
derives dataset/file lineage candidates from them, runs them through **phased HITL
curation**, and writes ONLY the curated result to the **ground-truth** database
(``drydocs``) — that write is what distinguishes it from ``drydocs_deepdoc``
(reactive, uncertain — its writes carry the :Uncertain label since the G102
fold; pre-fold they landed in the retired ``ddcontext`` database). Per D2 the
two are deliberately separate
components: each owns only its trigger, write target, and trust handling, and they
never import each other (boundary test enforces).

Invariants:

- **Curated-only writes.** Nothing reaches ``drydocs`` without passing curation
  (``status: proposed`` → confirmed via the HITL gate flow) — an uncurated candidate
  is deepdoc/context material, not ground truth.
- **Imports only ``drydocs_core.*``** (boundary group ``lineage``).
- **The parser is core's.** Any parse gap found here becomes a core change, never a
  local fork (the G3/0002-B rule, same reasoning).

Status (2026-07-11): G9 re-home complete (ADR 0002-C §4) — ``model`` (the depgraph
lineage layer reconciled to DryDocs identity: the ControlMJob NODE-KEY composite, the
registered gate-bound rel vocabulary scheduler_invokes / scheduler_triggers / scheduler_reads_from /
scheduler_writes_to), ``extractors.controlm_inventory`` (CSV projection → ProcessNodes +
INVOKES candidates, parsing via the SHARED core parser — the depgraph fork is
retired), ``review`` (the self-contained SME review page), ``collect/`` (the RHEL
run-as-user collector, shell assets), and ``writer`` (Fork-3 curated-write mechanics —
GATE-BOUND per label: gate rua-load-shapes SIGNED OFF 2026-08-07 activated
scheduler_invokes / scheduler_uses_artifact / scheduler_reads_from / scheduler_writes_to (applied at G55), so
``write_curated`` executes for those and still refuses planned labels (scheduler_triggers);
``plan_curated`` is the review surface. G23 (2026-08-07) added the rua curated load
— ``plan_rua`` / ``write_rua``: :Script on the §D1 path key, :SourceOccurrence
records anchored OCCURRENCE_OF, directory DataAssets, §C3 IS_ENCODED_IN).
STILL A STUB: ``curation.curate`` (phased cadence — trigger wiring is later work).
"""

from . import curation, extractors, model, review, writer

#: The write target — ground truth. Defined AT the write boundary (writer.py);
#: the trust axis IS the DB boundary (ADR 0002 D1).
DATABASE = writer.DATABASE

__all__ = ["DATABASE", "curation", "extractors", "model", "review", "writer"]
