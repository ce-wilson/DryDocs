"""The ontology layer: what the graph's connections MEAN (CLAUDE.md section 1, layer 2).

Holds the relationship-vocabulary registry and its per-domain fragments, the
standard-term namespaces, the domain registry, and the schema-graph reader. A
relationship type is registered here — through ``docs/RELATIONSHIP_GUIDE.md`` and
the HITL gate — before any loader may write it, which is what keeps taxonomy
imports reversible and meaning edges deliberate.
"""
