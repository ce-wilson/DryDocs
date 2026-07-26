"""The ontology-supplement registry — the apply chain as DATA, not as verbs.

Every ``*_supplement.cypher`` beside this module seeds :OntologyTerm anchor
terms. Before G29 each one had its own hand-written CLI verb whose body was the
same four lines (exists? -> execute_file -> print), so the ORDER of the chain
lived only in prose (``internal/repo-README.md``, the runbook, this package's
file headers) and nothing verified that a supplement had actually landed.

This module makes the chain a list. :data:`SUPPLEMENTS` is the single ordered
declaration; ``drydocs apply-supplements`` walks it and the legacy verbs
delegate into it.

**Order is load-bearing, not cosmetic.** ``catalog`` reuses the
``:Attribution`` class and ``#hasAgent`` term that ``seal`` declares, so seal
must precede catalog. ``base`` precedes everything (it declares the anchors the
domain files ``:SUBCLASS_OF`` onto). The order here IS the documented order;
``tests/unit/test_supplements.py`` pins it.

**Declared terms are parsed, not counted by hand.** :func:`declared_terms`
reads the IRIs a file MERGEs so the post-apply assertion has a ground truth
that cannot drift out of step with the .cypher — a hand-maintained "expect N
terms" constant would silently rot the first time a term is added.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from drydocs_core.cypher_split import strip_comments

SCHEMA_DIR = Path(__file__).resolve().parent

#: Every supplement file uses one MERGE shape — ``MERGE (n:OntologyTerm:<Kind>
#: {iri: "..."})``. Anchored on ``MERGE`` so a MATCH or a comment mentioning an
#: IRI is not mistaken for a declaration.
_TERM_MERGE = re.compile(
    r'MERGE\s*\(\s*\w*\s*:OntologyTerm[\w:]*\s*\{\s*iri:\s*"([^"]+)"',
)


@dataclass(frozen=True)
class Supplement:
    """One ontology supplement file and how it is applied."""

    name: str          #: chain name — what ``--only`` takes
    filename: str      #: file beside this module
    legacy_verb: str   #: the pre-G29 CLI verb, kept as a delegating alias
    summary: str       #: one line for --help and the run log
    opt_in: bool = False  #: excluded from the default chain (SOSA is experimental)

    @property
    def path(self) -> Path:
        return SCHEMA_DIR / self.filename


#: The apply chain, in order. base -> seal -> catalog -> registry; SOSA is
#: opt-in (W3C standard, NOT a declared company standard — ADR-fenced, every
#: term it seeds carries ``adoption:"experimental"``).
SUPPLEMENTS: tuple[Supplement, ...] = (
    Supplement(
        name="base",
        filename="ontology_supplement.cypher",
        legacy_verb="apply-ontology-supplement",
        summary="Control-M anchor terms + docs-corpus/traceability classes",
    ),
    Supplement(
        name="seal",
        filename="seal_ontology_supplement.cypher",
        legacy_verb="apply-seal-supplement",
        summary="SEAL domain terms (BusinessApplication, Port, TOM attribution)",
    ),
    Supplement(
        name="catalog",
        filename="catalog_ontology_supplement.cypher",
        legacy_verb="apply-catalog-supplement",
        # MUST follow seal — reuses seal's :Attribution class + #hasAgent term.
        summary="Catalog/PAT terms + all canonical Role seeds (needs seal first)",
    ),
    Supplement(
        name="registry",
        filename="registry_ontology_supplement.cypher",
        legacy_verb="apply-registry-supplement",
        summary="software-registry terms (Vendor, SoftwareProduct, MADE_BY, USES_SOFTWARE)",
    ),
    Supplement(
        name="sosa",
        filename="sosa_experimental_supplement.cypher",
        legacy_verb="apply-sosa-supplement",
        summary="EXPERIMENTAL SOSA/SSN observation + temporal terms (opt-in)",
        opt_in=True,
    ),
)

BY_NAME: dict[str, Supplement] = {s.name: s for s in SUPPLEMENTS}


def default_chain() -> tuple[Supplement, ...]:
    """The supplements a plain ``apply-supplements`` applies, in order."""
    return tuple(s for s in SUPPLEMENTS if not s.opt_in)


@cache
def declared_terms(path: Path) -> frozenset[str]:
    """The distinct :OntologyTerm IRIs *path* MERGEs.

    This is the ground truth the post-apply assertion compares against: after
    the file runs, every IRI here must be present as an :OntologyTerm. Returns
    an empty set for a file that declares none — the caller decides whether
    that is a problem (it always is, for a supplement).

    Comments are stripped with the shared comment/string-aware scanner first,
    so a commented-out MERGE — the natural way to retire a term — does not
    become an IRI the graph is then required to hold forever.
    """
    return frozenset(
        _TERM_MERGE.findall(strip_comments(path.read_text(encoding="utf-8")))
    )
