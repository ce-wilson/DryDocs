"""R22 — Tower has a declared source contract that text2cypher cannot cross.

* (a) the declaration agrees with its TypeScript source in BOTH directions
  (cardinality and members vs TOWERS in web/src/data/towers.ts), names a source
  that exists, and carries a closed graph_binding;
* (b) "how many towers are there" resolves at Tier 0 from the declaration with
  its provenance — the real number, never a graph count;
* (c) a question naming a declared non-graph term NEVER produces Cypher: the
  pipeline answers before the router, no read runs, no LLM is called, and the
  schema prompt tells text2cypher the term is not a graph concept.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from graph_qa import pipeline as pl  # noqa: E402
from graph_qa.providers import LlmReply, LlmUsage  # noqa: E402
from graph_qa.schema_context import build_schema_prompt  # noqa: E402

from drydocs_core.ui_concepts import (  # noqa: E402
    GRAPH_BINDINGS,
    answer_for,
    load_ui_concepts,
    match,
    not_graph_concept_lines,
)

TOWERS_TS = REPO_ROOT / "web" / "src" / "data" / "towers.ts"


def _tower():
    (tower,) = (c for c in load_ui_concepts() if c.term == "Tower")
    return tower


# -- (a) the declaration -------------------------------------------------------------


def test_declaration_matches_the_typescript_source_both_ways() -> None:
    tower = _tower()
    assert (REPO_ROOT / tower.source).exists(), tower.source
    text = TOWERS_TS.read_text(encoding="utf-8")
    assert f"export const {tower.source_symbol}" in text
    keys = re.findall(r"^\s{2}(\w+): \{\s*$", text, re.M)  # top-level record keys
    titles = re.findall(r"^\s{4}title: '([^']+)',", text, re.M)
    assert keys == [k for k, _ in tower.members], (keys, tower.members)
    assert titles == [t for _, t in tower.members], (titles, tower.members)
    assert tower.cardinality == len(keys) == 4
    assert tower.graph_binding in GRAPH_BINDINGS and tower.graph_binding == "none"
    assert "TOMRole" in tower.relationship_to_graph  # the proxy is named and refused in words


# -- (b) the Tier-0 answer ------------------------------------------------------------


def test_count_question_resolves_from_the_declaration_with_provenance() -> None:
    concept = match("how many towers are there")
    assert concept is not None and concept.term == "Tower"
    answer = answer_for("how many towers are there", concept)
    assert answer.startswith(
        "There are 4 towers: Home Lending, Auto, Credit Cards, Shared Services."
    )
    assert "not from the graph" in answer
    assert "web/src/data/towers.ts" in answer
    assert "not a graph concept" in answer


def test_matching_is_whole_word_and_alias_aware() -> None:
    assert match("list the CTO towers") is not None
    assert match("which tower owns auto?") is not None
    assert match("is the watchtower job late?") is None  # substring, not the term
    assert match("how many folders does each application support?") is None


# -- (c) no Cypher for a declared term ---------------------------------------------------


@dataclass
class _Provider:
    provider: str = "fake"
    calls: list = field(default_factory=list)

    def complete(self, system, user, max_tokens=1200):
        self.calls.append((system, user))
        raise AssertionError("the LLM must not be called for a declared term")


def test_pipeline_answers_a_declared_term_before_routing_and_runs_no_cypher() -> None:
    reads: list[str] = []

    def _read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        reads.append(cypher)
        raise AssertionError("no read may run for a declared term")

    provider = _Provider()
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_read,
        graph_schema=lambda: {
            "labels": ["TOMRole"],
            "relationshipTypes": [],
            "propertyKeys": ["name"],
        },
        vocabulary_loader=lambda: [],
    )
    env = pipeline.answer("how many towers are there", run_id="qa-r22")
    assert env.tier == "declared"
    assert env.answer.startswith("There are 4 towers")
    assert reads == [] and provider.calls == []
    assert [s.kind for s in env.steps] == ["declared"]
    assert env.steps[0].cypher is None and env.steps[0].rows == 4
    assert env.sources[0].document.startswith("config/taxonomy/ui-concepts.yaml#Tower")
    assert env.metrics.llm_calls == 0 and env.metrics.response_ms["total"] >= 0


def test_schema_prompt_declares_the_term_not_a_graph_concept() -> None:
    prompt = build_schema_prompt(
        [], {"labels": ["TOMRole"], "relationshipTypes": [], "propertyKeys": []}, []
    )
    assert "## NOT graph concepts" in prompt
    assert "Tower" in prompt and "web/src/data/towers.ts" in prompt
    assert any("not :TOMRole" in line for line in not_graph_concept_lines())


def test_a_gate_bound_term_returns_to_the_graph_path() -> None:
    """Once the HITL gate binds a term (planned/confirmed), the declaration no
    longer short-circuits — the graph owns it."""
    from dataclasses import replace

    bound = replace(_tower(), graph_binding="planned")
    assert match("how many towers are there", (bound,)) is None


def test_llm_reply_shape_is_untouched() -> None:
    """Sanity: the declared path changed nothing about provider contracts."""
    reply = LlmReply(text="x", usage=LlmUsage(1, 1), model="m", ms=1)
    assert reply.text == "x"
