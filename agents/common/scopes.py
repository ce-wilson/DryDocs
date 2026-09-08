"""Ask SCOPES — a router hint, not a retrieval path (AGENT1, from Idea-279 D1).

The dropdown in front of "Ask the knowledge graph" CONSTRAINS the spec catalog
the LLM router already sees: ``specs_catalog.catalog_lines(scope)`` drops the
specs a scope excludes before the join into ``pipeline.ROUTER_SYSTEM``. There is
no new tier, no second backend, and no separate index — a scope changes what the
router may CHOOSE, and nothing else about how an answer is produced.

READINESS IS PER OPTION, and that is the finding this module exists to carry
rather than a caveat on it. Shipping the control does not ship the options:

- ``knowledge-graph`` — READY. Registered specs plus text2cypher, which is what
  /ask has always done; this scope is today's behaviour with the corpus-only
  specs removed from the catalog.
- ``vendor-corpus`` — NOT READY, gated on API4. No registered spec searches
  ``Chunk.text``: ``docs.search.v1`` searches a Document's title and abstract
  and says so, and ``pipeline`` reports ``chunks: 0`` because no tier reads
  chunk text at all. A control LABELLED "vendor corpus" over a
  title-and-abstract search would turn O62's illusion — a full listing read as a
  search hit by title similarity — into a feature. The scope is DECLARED here so
  the filter is testable and API4 has something to switch on; ``ready`` is False,
  and ``resolve`` refuses it.
- ``general-knowledge`` — NOT READY, and see ``GENERAL_KNOWLEDGE_FINDING`` below
  for what checking it actually turned up.

WHY MEMBERSHIP IS A CONSTANT HERE AND A DERIVATION IN THE TEST. The evidence for
which specs read only the document corpus is each spec's own Cypher, but a
runtime filter that regex-scanned Cypher text would be a string parse standing in
for a declaration — and `QuerySpec` carries no scope field, because 47 spec
definitions are the wrong layer to edit for a router hint. So the sets below are
constants, and ``tests/unit/test_ask_scopes.py`` DERIVES them from the labels the
registered Cypher touches and asserts the two agree. That is the arrangement
``ColumnOut`` already has with ``query_specs.COLUMN_TYPES``: a second copy is
allowed exactly when a test makes it impossible for the copies to disagree. A
spec added, retired or re-pointed at the corpus fails that test with the name of
the spec that moved.

WHAT IS NOT DECLARED, and is the handback: no governed file maps a node LABEL to
a scope. `config/taxonomy/domains.yaml` partitions the relationship VOCABULARY
(edges) rather than specs, and several corpus specs traverse no edge at all
(``docs.search.v1`` matches a bare ``:Document``), so it cannot answer this
question as it stands.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The node labels that ARE the ingested document corpus. Used by the test's
#: derivation, not by any runtime filter.
CORPUS_LABELS = frozenset({"Document", "Chunk", "DocSection"})

#: Labels every spec carries for provenance and trust rather than for subject
#: matter — they say nothing about what a spec is ABOUT and are excluded before
#: a spec is classified.
META_LABELS = frozenset({"SchemaMeta", "Uncertain"})

#: Specs that read the document corpus and NOTHING else. These are the ones the
#: knowledge-graph scope drops: a question routed to one of them is answered out
#: of the ingested documents, which is the scope a person did not pick.
CORPUS_ONLY_SPECS = frozenset(
    {
        # API4: the first spec that searches chunk BODY TEXT. Corpus-only by
        # construction, and the reason vendor-corpus was gated on API4 in the
        # first place — this is the spec whose absence made that scope a label
        # over a title search. Whether the scope now FLIPS to ready is AGENT1's
        # re-evaluation, not this addition's.
        "docs.chunk-search.v1",
        "docs.chunks.v1",
        "docs.documents.v1",
        "docs.email-unassigned.v1",
        "docs.search.v1",
        "docs.section-browse.v1",
        "docs.trust-provenance.v1",
    }
)

#: Every spec that touches the corpus at all — the six above plus three that
#: JOIN a document to something in the graph. The hybrids stay in the
#: knowledge-graph scope on purpose: "which utility does this document
#: describe" is a graph question whose answer happens to cite a document, and
#: dropping it would make the scope mean "specs that never mention a document",
#: which is not what anybody picking it wants.
CORPUS_SPECS = CORPUS_ONLY_SPECS | frozenset(
    {
        "docs.role-siblings.v1",
        "docs.utility-lookup.v1",
        "software.doc-coverage.v1",
    }
)

#: What checking clause (c)'s R19 question actually found, recorded here because
#: the item says the cheapest outcome is that the option should not exist.
#:
#: R19 covers HALF of it, and the half it covers it covers well: a term that
#: resolves to none of the four sources (a registered spec, the relationship
#: vocabulary, a live label or property, an approved glossary sense) becomes a
#: clarification request at Tier 0, before anything routes — which IS "the
#: person does not know the subject", asked back instead of guessed at.
#:
#: It does NOT cover the other half, and this is the part worth keeping: R19
#: fires on ACRONYM- and LABEL-SHAPED tokens (`term_resolution.detect_terms`),
#: so a plain-prose general question detects no term and is never asked about.
#: But shipping general-knowledge would take more than an epistemic label:
#: `pipeline.ANSWER_SYSTEM` answers "from query results ONLY ... never invent
#: data", so the option needs a DIFFERENT ANSWER CONTRACT, not just a different
#: badge on the same one. That is a bigger decision than a dropdown entry, and
#: it is a gate question rather than a build.
GENERAL_KNOWLEDGE_FINDING = (
    "R19 already asks when an unrecognized acronym or label names the subject, "
    "but not when a general question is plain prose; and the answer contract "
    "forbids answering without rows, so this scope needs a new contract and a "
    "ruling, not an epistemic label"
)


@dataclass(frozen=True)
class Scope:
    """One dropdown option. ``ready`` is what a control renders live, and
    ``reason`` is what it renders instead — a disabled option that does not say
    why is indistinguishable from a broken one."""

    id: str
    label: str
    ready: bool
    reason: str = ""


#: The CLOSED vocabulary. A scope that is not here does not exist, and
#: ``resolve`` refuses it rather than inventing an empty catalog from it.
SCOPES: dict[str, Scope] = {
    s.id: s
    for s in (
        Scope("knowledge-graph", "Knowledge graph", ready=True),
        Scope(
            "vendor-corpus",
            "Vendor corpus",
            ready=False,
            reason=(
                "no registered spec searches chunk text yet (API4) — a search over "
                "titles and abstracts would answer as if it had searched the documents"
            ),
        ),
        Scope(
            "general-knowledge",
            "General knowledge",
            ready=False,
            reason=(
                "answers here come from query results only; answering without rows "
                "is a different contract and a ruling, not a label"
            ),
        ),
    )
}

#: The scopes a caller may actually select today.
READY_SCOPES = tuple(s.id for s in SCOPES.values() if s.ready)


def resolve(scope: str | None) -> tuple[str | None, str | None]:
    """``(scope, refusal)`` — the scope to filter by, and why a request was not
    honoured when it was not.

    A scope that is unknown, or known but not ready, degrades to UNSCOPED and
    says so; it never becomes an error and never becomes an empty catalog. That
    is ``_route``'s existing rule for a hallucinated ``spec_id``, applied one
    level up: router noise never kills a question. An empty catalog would be the
    worst of the three outcomes — the router would silently have nothing to
    choose from, and the run would look like a routing judgement.
    """
    if not scope:
        return None, None
    scope = scope.strip()
    declared = SCOPES.get(scope)
    if declared is None:
        return None, f"unknown scope {scope!r}; answered unscoped (declared: {sorted(SCOPES)})"
    if not declared.ready:
        return None, f"scope {scope!r} is not ready: {declared.reason}; answered unscoped"
    return declared.id, None


def in_scope(spec_id: str, scope: str | None) -> bool:
    """Whether a registered spec belongs to a resolved scope. ``None`` is
    UNSCOPED and admits everything, which is what every run does today —
    keeping the no-scope prompt byte-identical to the pre-AGENT1 one."""
    if scope is None:
        return True
    if scope == "knowledge-graph":
        return spec_id not in CORPUS_ONLY_SPECS
    if scope == "vendor-corpus":  # declared, refused by resolve() until API4
        return spec_id in CORPUS_SPECS
    return False
