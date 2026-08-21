"""Declared UI-taxonomy concepts whose source is NOT the graph (R22, 2026-08-21).

Reads ``config/taxonomy/ui-concepts.yaml`` — the console terms (Tower is the
first) whose authority is an in-repo definition rather than a graph label —
and answers two questions for the Q&A pipeline without touching a database:

* :func:`match` — does this question name a declared non-graph term?
* :func:`answer_for` — the deterministic Tier-0 answer with its provenance.

THE RULE THIS ENFORCES: a term with a declared non-graph source is never
answered by a graph label chosen for lexical similarity. When the pipeline
cannot ground a term in the graph it says the term is not a graph concept and
names where it IS defined — instead of reporting a count of zero (the
2026-08-20 Tower → :TOMRole proxy). Pure config read; no graph write, no LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_PATH = _REPO_ROOT / "config" / "taxonomy" / "ui-concepts.yaml"
SCHEMA = "drydocs.ui-concepts.v1"
GRAPH_BINDINGS = ("none", "planned", "confirmed")

_COUNT_RE = re.compile(r"\b(how many|number of|count( of)?|total)\b", re.I)


@dataclass(frozen=True)
class UiConcept:
    term: str
    aliases: tuple[str, ...]
    source: str
    source_symbol: str
    authority: str
    cardinality: int
    members: tuple[tuple[str, str], ...]  # (key, title)
    graph_binding: str
    relationship_to_graph: str

    @property
    def provenance(self) -> str:
        return f"config/taxonomy/ui-concepts.yaml#{self.term} -> {self.source}#{self.source_symbol}"

    def names(self) -> tuple[str, ...]:
        return (self.term, *self.aliases)


@lru_cache(maxsize=2)
def load_ui_concepts(path: str | Path | None = None) -> tuple[UiConcept, ...]:
    doc = yaml.safe_load(Path(path or DEFAULT_PATH).read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"ui-concepts: expected schema {SCHEMA}, got {doc.get('schema')!r}")
    out = []
    for row in doc.get("concepts") or []:
        binding = row.get("graph_binding", "none")
        if binding not in GRAPH_BINDINGS:
            raise ValueError(
                f"ui-concepts: {row.get('term')}: graph_binding {binding!r} not in {GRAPH_BINDINGS}"
            )
        members = tuple((str(m["key"]), str(m["title"])) for m in row.get("members") or [])
        out.append(
            UiConcept(
                term=str(row["term"]),
                aliases=tuple(str(a) for a in row.get("aliases") or []),
                source=str(row["source"]),
                source_symbol=str(row.get("source_symbol", "")),
                authority=str(row.get("authority", "")),
                cardinality=int(row["cardinality"]),
                members=members,
                graph_binding=binding,
                relationship_to_graph=" ".join(str(row.get("relationship_to_graph", "")).split()),
            )
        )
    return tuple(out)


def match(question: str, concepts: tuple[UiConcept, ...] | None = None) -> UiConcept | None:
    """The first declared concept whose term or alias appears as a whole word
    in the question (case-insensitive). Only concepts with ``graph_binding:
    none`` short-circuit — a planned or confirmed binding means the gate has
    spoken and the graph path owns the term."""
    text = question.lower()
    for concept in concepts or load_ui_concepts():
        if concept.graph_binding != "none":
            continue
        for name in concept.names():
            if re.search(rf"(?<![a-z0-9]){re.escape(name.lower())}(?![a-z0-9])", text):
                return concept
    return None


def answer_for(question: str, concept: UiConcept) -> str:
    """Deterministic, provenance-bearing. A count question gets the number; any
    other question gets the members and where they are defined. Never a graph
    count, never a proxy label."""
    titles = ", ".join(title for _, title in concept.members)
    where = f"from {concept.authority} — not from the graph"
    if _COUNT_RE.search(question):
        return (
            f"There are {concept.cardinality} {concept.term.lower()}s: {titles}. "
            f"Source: {where}. {concept.term} is not a graph concept; "
            f"{concept.relationship_to_graph}"
        )
    return (
        f"{concept.term} is a console concept defined in {concept.source} "
        f"({concept.cardinality}: {titles}), {where}. It is not a graph concept; "
        f"{concept.relationship_to_graph}"
    )


def not_graph_concept_lines(concepts: tuple[UiConcept, ...] | None = None) -> list[str]:
    """Prompt lines for schema grounding: the terms text2cypher must refuse to
    proxy onto a label. Belt to the pipeline's braces — the declared-term step
    answers first, so the model normally never sees such a question."""
    return [
        f"- {c.term} (aliases: {', '.join(c.aliases) or '—'}): NOT a graph concept; "
        f"defined in {c.source}. Never map it to a label by word similarity "
        f"(it is not :TOMRole); answer that it is not in the graph and name the source."
        for c in (concepts or load_ui_concepts())
        if c.graph_binding == "none"
    ]
