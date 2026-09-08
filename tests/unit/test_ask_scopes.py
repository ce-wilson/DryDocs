"""AGENT1 — the /ask scope as a ROUTER HINT (fakes; no litellm, no driver, no ADK).

What this suite proves, clause by clause:

- (a) a scope filters ``specs_catalog.catalog_lines()`` BEFORE the join into the
  router system prompt, so a spec outside the scope is absent from that prompt
  and cannot be chosen — the acceptance's own sentence, measured;
- (b) the envelope carries the scope that RAN, and says when a requested one was
  not honoured;
- (c) readiness is per option: only ``knowledge-graph`` resolves, and the two
  unready scopes are declared with the reason they are not shipped;
- and the membership sets in ``scopes.py`` are DERIVED here from the labels the
  registered Cypher touches, so the constants and the registry cannot drift
  apart in silence.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common import scopes, specs_catalog  # noqa: E402
from graph_qa import pipeline as pl  # noqa: E402

from drydocs_api.query_specs import QUERY_SPECS  # noqa: E402

VOCAB = [
    {
        "neo4j_label": "WAS_INFORMED_BY",
        "from_node": "ControlMJob",
        "to_node": "ControlMJob",
        "role": None,
        "note": "job dependency",
        "status": "active",
    }
]
LIVE_SCHEMA = {"labels": ["ControlMJob"], "relationshipTypes": [], "propertyKeys": []}

#: A spec the knowledge-graph scope drops — it reads the ingested document
#: corpus and nothing else. Named rather than computed so the acceptance's
#: sentence ("a spec outside it is absent from the router prompt") is asserted
#: about a specific, real spec.
CORPUS_ONLY_EXAMPLE = "docs.search.v1"
GRAPH_EXAMPLE = "explorer.applications.v1"


class FakeProvider:
    provider = "anthropic"

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def complete(self, system, user, max_tokens=1200):
        from graph_qa.providers import LlmReply, LlmUsage

        self.calls.append((system, user))
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return LlmReply(text=text, usage=LlmUsage(100, 20), model="fake-model", ms=5)


class FakeResult:
    def __init__(self) -> None:
        self.records = [{"n": 1}]
        self.keys = ["n"]
        self.row_count = 1
        self.truncated = False
        self.ms = 3
        self.notifications: list = []


def _read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
    return FakeResult()


def _answer(scope=None, replies=None, question="how many applications?"):
    provider = FakeProvider(
        replies
        if replies is not None
        else [f'{{"spec_id": "{GRAPH_EXAMPLE}", "params": {{}}, "reason": "counts apps"}}', "One."]
    )
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
    )
    envelope = pipeline.answer(question, run_id="qa-scope", session_id="s", scope=scope)
    return envelope, provider


def _router_prompt(provider) -> str:
    """The router call is the first, and its USER part carries the catalog."""
    return provider.calls[0][1]


# ── the membership constants, derived from the registry ──────────────────────


def _corpus_classification() -> tuple[set[str], set[str]]:
    """(corpus-only, corpus-touching), derived from each spec's own Cypher.

    THE DERIVATION IS HERE AND THE CONSTANTS ARE IN THE MODULE, deliberately:
    a runtime filter that regex-scanned Cypher would be a string parse standing
    in for a declaration, and `QuerySpec` carries no scope field. So the code
    holds a set and this holds the evidence — the arrangement ColumnOut already
    has with COLUMN_TYPES.

    Node labels are CamelCase and relationship types are UPPER_SNAKE, so the
    `isupper()` filter is load-bearing rather than tidy: without it `:PART_OF`
    reads as a label named PART and two corpus-only specs classify as hybrids.
    """
    corpus_only: set[str] = set()
    touching: set[str] = set()
    for spec_id, spec in QUERY_SPECS.items():
        labels = {t for t in re.findall(r":([A-Z][A-Za-z]+)", spec.cypher) if not t.isupper()}
        subject = labels - scopes.META_LABELS
        if subject & scopes.CORPUS_LABELS:
            touching.add(spec_id)
            if not (subject - scopes.CORPUS_LABELS):
                corpus_only.add(spec_id)
    return corpus_only, touching


def test_the_membership_constants_match_what_the_registered_cypher_reads():
    corpus_only, touching = _corpus_classification()
    assert corpus_only, "the derivation must find something — an empty scan proves nothing"
    assert set(scopes.CORPUS_ONLY_SPECS) == corpus_only
    assert set(scopes.CORPUS_SPECS) == touching
    # the hybrids are the point of the two sets being different
    assert touching - corpus_only


def test_every_named_spec_is_registered():
    """A constant naming a spec that no longer exists would filter nothing and
    say nothing — the drift this pairs with the test above to catch."""
    assert set(scopes.CORPUS_SPECS) <= set(QUERY_SPECS)


# ── (a) the filter acts on the router prompt ─────────────────────────────────


def test_a_scoped_catalog_drops_the_specs_outside_it():
    every = specs_catalog.catalog_lines()
    scoped = specs_catalog.catalog_lines("knowledge-graph")
    assert len(scoped) < len(every)
    assert not any(line.startswith(f"- {CORPUS_ONLY_EXAMPLE} ") for line in scoped)
    assert any(line.startswith(f"- {GRAPH_EXAMPLE} ") for line in every)
    assert any(line.startswith(f"- {GRAPH_EXAMPLE} ") for line in scoped)


def test_an_out_of_scope_spec_is_not_offered_to_the_router():
    """The acceptance's own sentence. Not offered rather than discouraged: the
    router cannot choose from a menu it was never shown, where "prefer X" in the
    prompt would be advice it is free to ignore.

    Asserted on the CATALOG ENTRY and not on the raw prompt text, because a
    dropped spec's id legitimately survives inside a KEPT spec's description —
    docs.utility-lookup.v1 names docs.search.v1 as its own fallback. That is
    prose about a spec, not an offer of one, and the difference is exactly why
    the test below exists."""
    offered = f"- {CORPUS_ONLY_EXAMPLE} ["
    assert offered not in _router_prompt(_answer(scope="knowledge-graph")[1])
    assert f"- {GRAPH_EXAMPLE} [" in _router_prompt(_answer(scope="knowledge-graph")[1])
    assert offered in _router_prompt(_answer(scope=None)[1])


def test_an_out_of_scope_spec_named_anyway_is_dropped_rather_than_run():
    """The latch behind the filter, and it is not hypothetical: a surviving
    spec's description names a dropped one, so the router CAN read an id it was
    never offered. An out-of-scope id is a hallucinated id — same treatment,
    Tier 1 takes over — and the answer never comes from outside the scope the
    person picked."""
    envelope, provider = _answer(
        scope="knowledge-graph",
        replies=[
            f'{{"spec_id": "{CORPUS_ONLY_EXAMPLE}", "params": {{}}, "reason": "docs"}}',
            '{"cypher": "MATCH (a:BusinessApplication) RETURN a.app_id AS app_id"}',
            "One.",
        ],
    )
    assert envelope.tier == "text2cypher", "the corpus spec must not have answered"
    assert [s.spec_id for s in envelope.steps if s.kind == "spec"] == []
    router_step = next(s for s in envelope.steps if s.kind == "router")
    assert router_step.spec_id is None
    assert len(provider.calls) == 3, "router, text2cypher, answer — the spec never ran"


def test_an_unscoped_run_sends_exactly_the_prompt_it_always_did():
    """The R18 both-modes discipline applied here: a feature that changes the
    default run's prompt is a feature nobody can compare against."""
    _, before = _answer(scope=None)
    catalog = "\n".join(specs_catalog.catalog_lines())
    assert catalog in _router_prompt(before)


def test_the_filter_is_the_only_thing_a_scope_changes():
    """No new tier, no second backend — the acceptance's first line. Same
    router, same spec execution, same answer call."""
    scoped, scoped_provider = _answer(scope="knowledge-graph")
    unscoped, unscoped_provider = _answer(scope=None)
    assert [s.kind for s in scoped.steps] == [s.kind for s in unscoped.steps]
    assert scoped.answer == unscoped.answer
    assert scoped.tier == unscoped.tier == "spec"
    assert len(scoped_provider.calls) == len(unscoped_provider.calls)
    # the ONLY difference between the two router prompts is the catalog
    assert scoped_provider.calls[0][0] == unscoped_provider.calls[0][0]


# ── (b) the envelope reports which scope ran ─────────────────────────────────


def test_the_envelope_carries_the_scope_that_ran():
    assert _answer(scope="knowledge-graph")[0].scope == "knowledge-graph"
    assert _answer(scope=None)[0].scope is None


def test_an_unknown_scope_answers_unscoped_and_says_so():
    """Router noise never kills a question, and a degradation nobody is told
    about is one that reads as a routing judgement."""
    envelope, provider = _answer(scope="everything-please")
    assert envelope.scope is None
    assert "unknown scope" in envelope.scope_note
    assert "everything-please" in envelope.scope_note
    assert envelope.answer.endswith("One.")
    assert CORPUS_ONLY_EXAMPLE in _router_prompt(provider), "unscoped means the full catalog"


def test_a_declared_but_unready_scope_is_refused_with_its_reason():
    envelope, _ = _answer(scope="vendor-corpus")
    assert envelope.scope is None
    assert "not ready" in envelope.scope_note
    assert "chunk text" in envelope.scope_note


def test_a_scope_never_empties_the_catalog():
    """The worst of the three outcomes: the router silently has nothing to
    choose from and the run looks like it decided."""
    for asked in (None, "knowledge-graph", "vendor-corpus", "nonsense", "", "   "):
        resolved, _ = scopes.resolve(asked)
        assert specs_catalog.catalog_lines(resolved), f"empty catalog for {asked!r}"


# ── (c) readiness is per option ──────────────────────────────────────────────


def test_only_the_knowledge_graph_scope_is_ready():
    assert scopes.READY_SCOPES == ("knowledge-graph",)
    assert set(scopes.SCOPES) == {"knowledge-graph", "vendor-corpus", "general-knowledge"}


def test_every_unready_scope_states_why():
    """A disabled option that does not say why is indistinguishable from a
    broken one — and these two are disabled for different reasons."""
    for scope in scopes.SCOPES.values():
        assert bool(scope.reason) is not scope.ready
    assert "API4" in scopes.SCOPES["vendor-corpus"].reason
    assert scopes.SCOPES["vendor-corpus"].reason != scopes.SCOPES["general-knowledge"].reason


def test_the_vendor_corpus_scope_is_declared_but_unreachable():
    """Declared so the filter is testable and API4 has something to switch on;
    unreachable so no answer can be produced under a label that would claim the
    documents were searched when only their titles were."""
    assert scopes.in_scope("docs.search.v1", "vendor-corpus") is True
    assert scopes.resolve("vendor-corpus")[0] is None


def test_the_general_knowledge_finding_is_recorded_not_assumed():
    """Clause (c) asks R19 to be checked FIRST and the item to record what it
    found. R19 asks when an unresolved acronym or label names the subject; it
    does not fire on plain prose, and the answer contract forbids answering
    without rows — so this is a ruling, not a badge."""
    finding = scopes.GENERAL_KNOWLEDGE_FINDING
    assert "R19" in finding and "plain prose" in finding
    assert "contract" in finding


def test_the_hybrids_stay_in_the_knowledge_graph_scope():
    """ "Which utility does this document describe" is a graph question whose
    answer cites a document. Dropping it would make the scope mean "specs that
    never mention a document", which is not what picking it asks for."""
    for spec_id in set(scopes.CORPUS_SPECS) - set(scopes.CORPUS_ONLY_SPECS):
        assert scopes.in_scope(spec_id, "knowledge-graph") is True
