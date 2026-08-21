"""Gate corporate-backbone-vocabulary §D — an edge's endpoints must be declared.

WHY THIS EXISTS. (:Company)-[:HAS_BUSINESS_SEGMENT]->(:BusinessSegment) was
MERGEd by ``drydocs_core/schema/ontology.cypher`` from M0, carried a live
uniqueness constraint, and was documented as THE corporate hierarchy across four
``.claude/skills/data-context-extractor/`` files — while ``:Company`` and both
segment edges were absent from the relationship vocabulary the whole time.
``git log -S "Company"`` over that directory returns nothing, so nothing retired
them; they were never declared.

Nothing caught it, and that is the reusable finding. ``test_taxonomy_ontology_map``
checks label UNIQUENESS; ``test_yaml_fragments`` checks fragment KEYS. Neither
compares an edge against the label registry, so ``RECONCILES_TO`` passed only
because its endpoint happened to be registered, and an entirely absent edge was
invisible to both.

§D3 ruled the guard reads BOTH directions, because the registry-only half could
not have caught this: while an edge is missing from the vocabulary altogether,
there is nothing for a registry-side check to look at. The seed-side check is the
one that fires.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs_core.yaml_fragments import load_yaml_source

REPO = Path(__file__).resolve().parents[2]
VOCAB_DIR = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
SCHEMA_DIR = REPO / "drydocs_core" / "schema"

#: Relationship types written by a schema .cypher that deliberately carry no
#: vocabulary entry. DECLARED, never inferred: an entry here is a ruling that a
#: type is infrastructure rather than ontology, and it must say why. Empty is the
#: honest default — add a row only with a reason, or the guard degrades into the
#: silence it was built to end.
SEED_EDGE_EXEMPTIONS: dict[str, str] = {
    "MAPS_TO": "ontology META: (:LocalClass|:LocalRelationship)->(:OntologyTerm), the "
    "standards mapping that DECLARES the vocabulary. Not an estate edge — registering it "
    "would make the registry describe itself.",
    "SUBCLASS_OF": "ontology META: rdfs:subClassOf between :OntologyTerm nodes in the "
    "supplements. Same reasoning as MAPS_TO.",
    "IN_SCHEME": "ontology META: skos:inScheme, binding a term to its concept scheme.",
}

#: Seeded relationship types that are REAL ontology edges with no vocabulary entry.
#: Kept separate from SEED_EDGE_EXEMPTIONS on purpose: that dict means "not
#: ontology", and filing debt there would misdescribe it as a ruling. Same debt
#: framing as KNOWN_UNREGISTERED_ENDPOINTS — the guard fails on anything new.
KNOWN_UNREGISTERED_SEED_EDGES: dict[str, str] = {
    "CAN_ACT_AS": "sosa_experimental_supplement.cypher:86,91 MERGEs it between "
    ":LocalClass and :FeatureOfInterest — a genuine gap, not infrastructure. The "
    "vocabulary header says SOSA terms 'use status: planned here until the SME "
    "confirms via the gate', and this one never got its entry. Belongs to the E1 "
    "SOSA gate (in_progress), not to G98 — registering it here would be a second "
    "gate's ruling made without its session.",
}

#: Endpoint labels named by a DECLARED edge that are not (yet) in
#: node_classifications. FOUND BY THIS GUARD ON ITS FIRST RUN, 2026-08-17 — every
#: one is the same defect class as :Company, which is the point: the guard was
#: built for one gap and immediately found eight more.
#:
#: THIS LIST IS DEBT, NOT A DISPOSITION. It exists so the guard can land without
#: either lying about the tree or blocking on ontology rulings nobody has made —
#: each label needs its own gate, exactly as :Company did (G98). The guard FAILS on
#: anything NEW, so the debt can only shrink. Deleting a row is the fix; adding one
#: needs a reason and should be rare.
KNOWN_UNREGISTERED_ENDPOINTS: dict[str, str] = {
    "QualityMeasurement": "DQV seed, C23 ruled DEFERRED as a reference catalog (no upstream)",
    "Dataset": "DQV/DCAT; also the live subject of gate snowflake-data-catalog clause A",
    "Metric": "DQV seed, C23-deferred",
    "Dimension": "DQV seed, C23-deferred",
    "OntologyTerm": "the META node the supplements declare terms as; docs_governed_by points at it",
    "SchedulerKind": "seal_requires_scheduler is deprecated (never built, retired at a gate)",
    "SwoClass": "arch_is_encoded_in — software-ontology class, status planned",
    "MediaType": "arch_has_media_type — dcat:mediaType, status planned",
}

#: Wildcard from_node is a rendering convenience (WILDCARD_EXEMPLARS), not a label.
_WILDCARD = "*"

_REL_IN_CYPHER = re.compile(r"[-<]\[\s*(?:\w+)?\s*:([A-Z][A-Z0-9_]*)\s*[\]{]")

#: A Cypher line comment, but NOT the `//` inside a URL — `(?<!:)` keeps
#: `https://drydocs.local/ontology#` intact. Stripping comments is required, not
#: tidiness: the first run of this guard reported :DEVELOPS and :CAN_ACT_AS as
#: unregistered seeded edges when both appear ONLY in prose explaining a past
#: reshape ("Was DevTeam-[:DEVELOPS]-> pre-K4"). A guard that reads commentary as
#: code manufactures findings, and a guard that cries wolf gets muted — which is
#: the Idea-111 failure this whole class of check exists to avoid.
_LINE_COMMENT = re.compile(r"(?<!:)//.*$", re.MULTILINE)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

#: String literals are stripped for the same reason comments are, and it is a
#: SEPARATE source of the same error: `n.notes = "Was DevTeam-[:DEVELOPS]-> pre-K4."`
#: is a property VALUE describing a reshape that already happened, and reading it as
#: a live edge reported :DEVELOPS as an unregistered seeded type. Prose about an
#: edge — in a comment or in a note property — is not an edge.
_STRING_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"' r"|'(?:[^'\\]|\\.)*'")


def _code_only(text: str) -> str:
    """Cypher with comments and string literals removed.

    Order matters: comments first (they may contain quotes that would otherwise
    open a bogus string), then literals.
    """
    stripped = _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))
    return _STRING_LITERAL.sub('""', stripped)


def _endpoint_labels(value: str) -> list[str]:
    """Split an endpoint cell into labels.

    ``from_node``/``to_node`` may name ALTERNATIVES — ``"Script | ETLProcess"``,
    ``"ETLProcess | ControlMJob"`` — the "one edge meaning, two endpoint classes"
    convention ruled at rua-load-shapes §B2, with the endpoint recorded on the
    edge. Each alternative is a real label and each must be registered; reading
    the cell as one opaque string reports every such entry as a defect.
    """
    return [part.strip() for part in value.split("|") if part.strip()]


def _vocabulary() -> dict:
    return load_yaml_source(VOCAB_DIR)


def _registered_labels() -> set[str]:
    return {e["label"] for e in _vocabulary()["node_classifications"]}


def _entries() -> list[dict]:
    return list(_vocabulary()["local_relationships"])


def test_every_declared_edge_endpoint_is_a_registered_label() -> None:
    """Direction 1 — the registry must be internally closed.

    An edge naming an unregistered endpoint is a half-declaration: the meaning
    edge exists in the vocabulary while the thing it connects does not, which is
    the ControlMApplication defect (closed 2026-07-09) and the reason the :Port
    contact-point edge shipped WITH its node class.
    """
    labels = _registered_labels()
    failures: list[str] = []
    for entry in _entries():
        for side in ("from_node", "to_node"):
            value = (entry.get(side) or "").strip()
            if not value or value == _WILDCARD:
                continue
            for label in _endpoint_labels(value):
                if label in labels or label in KNOWN_UNREGISTERED_ENDPOINTS:
                    continue
                failures.append(f"{entry['id']}.{side} -> {label!r}")

    assert not failures, (
        "relationship entries name endpoint labels that are not registered in "
        "node_classifications:\n  "
        + "\n  ".join(sorted(failures))
        + "\nDeclare the label (10-node-classifications.yaml) in the SAME change as "
        "the edge — an edge whose node class is unclassified is a gap, not a shortcut."
    )


def test_every_edge_the_schema_seeds_has_a_vocabulary_entry() -> None:
    """Direction 2 — the one that would actually have caught G98.

    Direction 1 sees nothing while an edge is absent from the vocabulary
    entirely, which is precisely the state the corporate backbone sat in for
    months. This reads the seeded Cypher instead and asks the inverse question:
    the graph is being written this edge — does the ontology know about it?
    """
    declared = {e["neo4j_label"] for e in _entries()}
    failures: list[str] = []
    for path in sorted(SCHEMA_DIR.glob("*.cypher"), key=lambda p: p.as_posix()):
        seeded = set(_REL_IN_CYPHER.findall(_code_only(path.read_text(encoding="utf-8"))))
        known = set(SEED_EDGE_EXEMPTIONS) | set(KNOWN_UNREGISTERED_SEED_EDGES)
        for rel_type in sorted(seeded - declared - known):
            failures.append(f"{path.name} writes :{rel_type}")

    assert not failures, (
        "schema Cypher seeds relationship type(s) with no vocabulary entry:\n  "
        + "\n  ".join(failures)
        + "\nRegister the type (status: planned) per docs/RELATIONSHIP_GUIDE.md, or add "
        "it to SEED_EDGE_EXEMPTIONS with the reason it is infrastructure rather than "
        "ontology. Do not silence it by deleting the seed."
    )


def test_the_corporate_backbone_is_registered_both_ways() -> None:
    """Pin the specific gap G98 closed, so a regression names itself.

    Written against the two edges and the label by name rather than trusting the
    two sweeps above to keep covering them — the sweeps are the general rule,
    this is the case that proved the rule was missing.
    """
    labels = _registered_labels()
    assert "Company" in labels, ":Company must stay registered (gate §A1)"
    assert "BusinessSegment" in labels

    by_label = {e["neo4j_label"]: e for e in _entries()}
    for rel_type in ("HAS_BUSINESS_SEGMENT", "HAS_BUSINESS_SEGMENT_HISTORICAL"):
        entry = by_label.get(rel_type)
        assert entry is not None, f"{rel_type} must stay registered (gate §B1/§B3)"
        assert entry["from_node"] == "Company"
        assert entry["to_node"] == "BusinessSegment"
        assert entry["domain"] == "corporate", "§B3 ruled the corporate domain"
        assert entry["status"] == "planned", "nothing activates without a loader"
