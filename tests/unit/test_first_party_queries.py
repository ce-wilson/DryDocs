"""A first-party query may only name labels and relationship types the schema declares (O84).

THE DEFECT THIS CLOSES IS THE DETECTION GAP, not the two strings. The console's
depgraph preset and the graph-query agent's default query both named a code-FILE
label, a depends-on relationship and a camel-case path property, while the signed
``self-documentation-code-graph`` gate ruled a code-MODULE label — explicitly
rejecting the code-file option — and an imports relationship, and the loader
writes the snake_case property. Both call sites were corrected on 2026-08-29. The
reason nothing noticed is that a ruling which exists only in a gate document and
in two hand-copied strings has no enforcement point at all: the query was valid
Cypher, the database answered it, and the surface reported success with zero rows.

WHY A GUARD RATHER THAN A GENERATED ARTIFACT — O84 clause (b) required choosing
one and saying why the other was not chosen. The two call sites are in different
languages (a TypeScript preset map and a Python default), so a shared generated
artifact would need two consumers, a build step, and a drift test of its own,
which is three moving parts to enforce one sentence. The schema files are already
the source of truth, and the invariant is directly checkable against them. The
generated-artifact shape stays the right answer where a VALUE must be rendered
into a surface (gates.json, load-map.json); here nothing is rendered — a rule is
enforced.

SCOPE FENCE (clause d). First-party presets and the agent default only. This is
NOT a validator for user-typed Cypher: the bolt panel is a raw-Cypher bench by
design, and widening this into a general query checker is a product decision
nobody has made.

J66 COMPLIANCE IS LOAD-BEARING HERE, not ceremonial. Both source files NAME the
rejected label in a comment explaining the ruling — a bare substring scan would
read those comments, "find" the forbidden label, and fail on the explanation.
The Python side is read as an ABSTRACT SYNTAX TREE, where comments do not exist
at all — ``source_scan.code_only`` was the first choice and is wrong here for an
instructive reason: it strips comments *and string literals*, and the thing being
guarded IS a string literal, so it returned nothing. The TypeScript side gets a
local comment stripper, which is exactly the precedent ``source_scan``'s own
header sets for the Cypher stripper in ``test_vocabulary_endpoints.py`` — a
grammar Python cannot parse gets its own stripper rather than being folded in.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
CONSOLE = REPO / "web" / "src" / "components" / "CypherConsole.tsx"
AGENT = REPO / "agents" / "graph_query" / "agent.py"
SCHEMA_DIR = REPO / "drydocs_core" / "schema"
VOCAB_DIR = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"

#: `(a:Label)`, `(:Label)`, `(a:A:B)` — mirrors web/src/lib/cypher-labels.ts.
LABEL_RE = re.compile(r"\(\s*\w*\s*:\s*([A-Za-z_]\w*(?:\s*:\s*[A-Za-z_]\w*)*)\s*[){]")
#: `[:REL]`, `[r:REL]`, `[:A|B]`, `[:REL*1..3]`.
REL_RE = re.compile(r"\[\s*\w*\s*:\s*([A-Z_][A-Z0-9_]*(?:\s*\|\s*[A-Z_][A-Z0-9_]*)*)\s*[*\]]")

#: A Cypher query, recognised by the clause every first-party query opens with.
QUERY_RE = re.compile(r"MATCH\s*\(")


def _strip_ts_comments(source: str) -> str:
    """Remove `//` and `/* */` comments from TypeScript source.

    Local by the precedent source_scan's header sets: a grammar Python's
    tokenizer cannot parse gets its own stripper rather than being folded into
    the shared helper. Deliberately simple — it does not need to survive a `//`
    inside a string literal, because the queries it protects contain no URLs, and
    a stripper that silently mangles a query would be worse than none. The guard
    below asserts the strings it found still contain the queries it expects.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", source)


def _console_queries() -> list[str]:
    """The PRESETS map's query strings, comments removed first."""
    code = _strip_ts_comments(CONSOLE.read_text(encoding="utf-8"))
    block = re.search(r"const PRESETS[^=]*=\s*\{(.*?)\n\}", code, flags=re.DOTALL)
    assert block, "PRESETS map not found in CypherConsole.tsx — has it been renamed?"
    return [s for s in re.findall(r"'([^']*)'", block.group(1)) if QUERY_RE.search(s)]


def _agent_queries() -> list[str]:
    """Cypher string literals in the agent module, read STRUCTURALLY.

    Not via ``source_scan.code_only``: that helper strips comments AND string
    literals, and here the query IS a string literal — it returned nothing, which
    this module's own finds-nothing guard caught on the first run. An AST walk is
    the better answer anyway and is J66 in its purest form: comments do not exist
    in a parse tree, so the rejected label named in this file's own explanation
    cannot be read no matter how the prose is worded, and implicit concatenation
    is already joined by the parser rather than by a regex.
    """
    tree = ast.parse(AGENT.read_text(encoding="utf-8"))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and QUERY_RE.search(node.value)
    ]


def _declared_labels() -> set[str]:
    """Every label a constraint or index declares, across the schema files."""
    labels: set[str] = set()
    for path in SCHEMA_DIR.glob("*.cypher"):
        text = path.read_text(encoding="utf-8")
        labels |= set(re.findall(r"FOR\s*\(\s*\w+\s*:\s*(\w+)\s*\)", text))
    return labels


def _declared_rel_types() -> set[str]:
    """Every relationship type the vocabulary registry binds to a Neo4j label."""
    types: set[str] = set()
    for path in VOCAB_DIR.glob("*.yaml"):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        types |= _neo4j_labels(doc)
    return types


def _neo4j_labels(node: object) -> set[str]:
    """Every `neo4j_label` value anywhere in a loaded fragment."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "neo4j_label" and isinstance(value, str):
                found.add(value.strip())
            else:
                found |= _neo4j_labels(value)
    elif isinstance(node, list):
        for item in node:
            found |= _neo4j_labels(item)
    return found


# --------------------------------------------------------------------------- #
# the guard
# --------------------------------------------------------------------------- #
def test_the_queries_are_actually_found() -> None:
    """A guard that silently finds nothing passes forever.

    Both extractors are pattern-based over source, so the first thing to assert
    is that they still see a query at all — a rename of PRESETS or of the agent's
    default would otherwise turn this whole module into a no-op that reports
    success, which is the same failure mode O84 is about.
    """
    assert _console_queries(), "no first-party queries found in CypherConsole.tsx"
    assert _agent_queries(), "no first-party queries found in agents/graph_query/agent.py"


def test_the_comment_naming_the_rejected_label_is_not_read() -> None:
    """J66, asserted rather than assumed.

    Both files explain the ruling by NAMING the rejected label in a comment. If
    the strippers ever stop working, this guard would fail on the explanation and
    teach the next author to delete it. So the property is tested directly: the
    rejected name appears in the raw source and must not appear in what the
    extractors return.
    """
    rejected = "Code" + "File"  # split so this line is not itself a match
    assert rejected in CONSOLE.read_text(encoding="utf-8"), (
        "the comment recording the rejected option is gone — if that was "
        "deliberate, delete this guard with it"
    )
    assert rejected in AGENT.read_text(encoding="utf-8")
    for query in _console_queries() + _agent_queries():
        assert rejected not in query


def test_every_label_a_first_party_query_names_is_declared() -> None:
    declared = _declared_labels()
    assert declared, "no labels found in the schema files — the guard has no basis"
    offenders: list[tuple[str, str]] = []
    for query in _console_queries() + _agent_queries():
        for group in LABEL_RE.findall(query):
            for label in (p.strip() for p in group.split(":")):
                if label and label not in declared:
                    offenders.append((label, query[:70]))
    assert not offenders, (
        "first-party quer(ies) name labels no schema declares: "
        f"{offenders}. A label that exists only in a hand-copied string returns "
        "success with zero rows and nothing notices."
    )


def test_every_relationship_type_a_first_party_query_names_is_declared() -> None:
    declared = _declared_rel_types()
    assert declared, "no relationship types found in the vocabulary registry"
    offenders: list[tuple[str, str]] = []
    for query in _console_queries() + _agent_queries():
        for group in REL_RE.findall(query):
            for rel in (p.strip() for p in group.split("|")):
                if rel and rel not in declared:
                    offenders.append((rel, query[:70]))
    assert (
        not offenders
    ), f"first-party quer(ies) name relationship types the vocabulary does not bind: {offenders}"


def test_the_guard_catches_the_drift_it_exists_for() -> None:
    """Proving the mechanism, not the current strings.

    Every other assertion here passes because the two call sites are correct
    today, which is exactly the state that would also be reported by a guard
    checking nothing. So the rejected shape is run through the same extraction
    and the same declared sets: the label the gate rejected must be absent from
    the schema, and the depends-on edge absent from the vocabulary, or this guard
    would have had nothing to catch on 2026-08-29 either.
    """
    drifted = "MATCH (a:CodeFile)-[:DEPENDS_ON]->(b:CodeFile) RETURN a.relPath LIMIT 25"

    named_labels = {p.strip() for g in LABEL_RE.findall(drifted) for p in g.split(":")}
    named_rels = {p.strip() for g in REL_RE.findall(drifted) for p in g.split("|")}
    assert named_labels == {"CodeFile"}, "the extractor no longer sees the label"
    assert named_rels == {"DEPENDS_ON"}, "the extractor no longer sees the relationship"

    assert not named_labels & _declared_labels(), (
        "the rejected label is now declared in the schema — if that is a real "
        "ruling change, this guard and the gate record need updating together"
    )
    assert not named_rels & _declared_rel_types()
