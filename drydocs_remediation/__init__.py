"""drydocs-remediation — failure-driven Control-M definition remediation (ADR 0002-B / G3).

The component runs **detect → transform → prove → Jira**: import the *legacy* Control-M
definition via a :class:`~drydocs_remediation.formats.DefinitionFormat` (XML today, BMC's
JSON Automation API later), detect standards findings against the rules registry, propose a
*greenfield* definition, prove offline equivalence (the greenfield re-derives the same
resolved behavior via ``drydocs_core.orchestration.controlm``), and hand off as a Jira — the dev team
holds deploy rights (separation of duties; we author, they implement).

Invariants (0002-B §0/§3 — each lands as a test with the real implementation):

- **Writes NO graph.** Neo4j (``database="drydocs"``) and the Oracle extract are read-only
  corroboration via ``drydocs_core`` adapters; the only durable outputs are the greenfield
  artifact and the Jira (the system of record).
- **Imports only ``drydocs_core.*``** — never another component
  (``tests/unit/test_module_boundary.py`` enforces, group ``remediation``).
- **Rules are gate-bound.** The rule source is the R1-R29 registry
  (``internal/remediation/standards-rules-registry.md``, Internal): only ✅-ratified rules
  may drive greenfield changes; 🟡/❓ rules surface as WARN-only findings.
- **Format-agnostic definitions.** No XML assumption outside the
  :class:`~drydocs_remediation.formats.XmlDefinitionFormat` implementation.

Status (2026-07-10): M0 slice + the Tier-1/handoff slice IMPLEMENTED — transcript load
(the gate-1 fallback format), the R1 dot-smuggling detector, the order-paired
equivalence proof, the ratified-only Tier-1 transform engine (FR-REM-3; first rule:
canonical variable rename), and the Jira handoff boundary (FR-REM-6; render is pure,
``JiraSubmitter`` is the only wire, REST impl is company-side), and read-only
corroboration (``corroborate`` — pure reconcile + the ``ReadOnlyGraph`` wrapper that
refuses write Cypher before the driver; live schema-specific queries are Track-2,
company-side). STILL STUBS — ``XmlDefinitionFormat`` (blocked on the vendor schema
acquisition, see ``formats.py``); Tier-2 (agentic) fixes are a future slice. The equivalence
verdict on the real M0 unit stays PENDING ground truth (info item A3 / the ``var.text``
rule B1) — see ``internal/remediation/m0/``. Contract:
``docs/design/drydocs-remediation-tdd.md`` wins on conflict.
"""

from . import corroborate, detect, equivalence, formats, jira, transform, xml_bridge

__all__ = [
    "corroborate",
    "detect",
    "equivalence",
    "formats",
    "jira",
    "transform",
    "xml_bridge",
]

import logging

#: G105/ADR 0014 clause 2 — a module logger per component.
LOGGER = logging.getLogger(__name__)
