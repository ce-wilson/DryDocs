"""Namespace prefixes used across the knowledge graph.

Keep this in sync with ``drydocs/schema/ontology.cypher``. When the corporate
DPROD namespace is published internally, swap the ``dprod`` value here.
"""
from __future__ import annotations

NAMESPACES: dict[str, str] = {
    # W3C standards
    "dcat": "http://www.w3.org/ns/dcat#",
    "prov": "http://www.w3.org/ns/prov#",
    "dqv":  "http://www.w3.org/ns/dqv#",
    "org":  "http://www.w3.org/ns/org#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd":  "http://www.w3.org/2001/XMLSchema#",

    # Data product ontology — using the SEMIC / EKGF DPROD namespace as the
    # working default; replace with the corporate-blessed IRI once published.
    "dprod": "https://ekgf.github.io/dprod#",

    # Software ontology (EBI SWO) and OBI for data transformation.
    "swo":  "http://www.ebi.ac.uk/swo/",
    "obi":  "http://purl.obolibrary.org/obo/",
    "iao":  "http://purl.obolibrary.org/obo/",

    # OpenLineage doesn't publish an OWL ontology; we treat it as a label
    # vocabulary inside the graph (see :OlClass nodes in ontology.cypher).
    "ol":   "https://openlineage.io/spec/",

    # Local namespace for DryDocs-specific concepts.
    "dd":   "https://drydocs.local/ontology#",
}


def expand(curie: str) -> str:
    """Expand ``prefix:local`` to a full IRI; raise on unknown prefix."""
    if ":" not in curie:
        raise ValueError(f"Not a CURIE: {curie!r}")
    prefix, local = curie.split(":", 1)
    if prefix not in NAMESPACES:
        raise KeyError(f"Unknown prefix: {prefix!r}")
    return NAMESPACES[prefix] + local