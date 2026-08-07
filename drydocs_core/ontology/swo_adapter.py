"""Extension → SWO language-term adapter (G33 §E1(b); shared core seam).

Binds a file extension to the ALREADY-SEEDED SwoClass term (ontology.cypher)
its language realises — bind to a seeded term, derive from data the artifact
already carries, invent nothing. First consumer was the depgraph code-snapshot
loader (:CodeModule, G33); gate rua-load-shapes §C3 (SIGNED OFF 2026-08-07)
pointed the SAME adapter at :Script, which put it on both sides of the
drydocs / drydocs_lineage import boundary — so it lives in core (the house
rule: a shared mapping is a core change, never a local fork). The media-type
adapter (EXTENSION_MEDIA_TYPE_IRI) stays with the code-snapshot loader: only
the language binding was widened to :Script.
"""

from __future__ import annotations

#: extension -> seeded SwoClass iri. Extensions absent here stay unbound and
#: are reported by each consumer, never guessed.
EXTENSION_LANGUAGE_IRI: dict[str, str] = {
    ".py": "http://www.ebi.ac.uk/swo/SWO_0000118",  # Python
    ".sh": "http://www.ebi.ac.uk/swo/SWO_0000124",  # Shell
    # .ksh binds to the SAME Shell term as .sh — SME ruling 2026-08-06 (gate
    # rua-load-shapes §C3). ksh IS a shell, so this binds a seeded term rather
    # than inventing one, and it is not a cosmetic addition: the signed
    # m3_triggers note names the .ksh wrapper as the COMMON case in this estate
    # ("one .ksh wrapper script that launches the Informatica / Ab Initio / DPL
    # workload"), so leaving it out left the most frequent extension unbound and
    # merely CLI-reported.
    ".ksh": "http://www.ebi.ac.uk/swo/SWO_0000124",  # Shell (ksh)
    ".sql": "http://www.ebi.ac.uk/swo/SWO_0000126",  # SQL
}
