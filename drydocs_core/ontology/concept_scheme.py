"""The lob-product-team skos:ConceptScheme as a Python object (G77, 2026-08-21).

ONE VOCABULARY, TWO CORPORA. ``config/taxonomy/lob-product-team.yaml`` declares
its LOB > ProductLine > Product tree a ``skos:ConceptScheme`` (C34 (a), taxonomy,
layer 1, no gate). This module reads that declaration so BOTH corpora can
classify against it — the structured estate through the folder-scope ``THEME``
description token (:mod:`drydocs_core.orchestration.controlm.description_tokens`)
and the unstructured one through the docmeta capture envelope
(:mod:`drydocs_docmeta.manifest`). Neither side carries its own copy of the
vocabulary; both resolve to the same concept IRIs here.

THE JOIN IS AT THE CLASSIFICATION, NEVER THE CONTENT. A document and a folder
sharing a theme are both ABOUT that subject. That is not an assertion that the
document describes the folder, and no edge may imply it; trust tiers do not
merge because two things share a subject. This module therefore resolves
VALUES to IRIs and nothing more — no edge, no graph write, no ratification
(the dcat:theme edge is the ``dcat-theme-subject-scheme`` gate's).

JOINED BY CONCEPT IRI, NEVER BY LABEL. The IRI form is the one the gate prompt
confirms as the join key (§A2): ``<scheme uri>#<notation>``, notation being the
row's ``code`` where present, else its ``id``. Labels are display text and can
drift between corpora; a label is never accepted as a theme value, so label
drift cannot fork the join, and the scheme works unchanged under one database
or two.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent.parent)
DEFAULT_SCHEME_PATH = _REPO_ROOT / "config" / "taxonomy" / "lob-product-team.yaml"

#: The one scheme declared today. Kept as a constant so the two corpora name
#: the same thing by the same string.
LOB_PRODUCT_TEAM_SCHEME = "urn:drydocs:scheme:lob-product-team"


class ThemeStatus(str, Enum):
    """C34 (c): unclassified is FIRST-CLASS, and out-of-scope is a DIFFERENT
    value from not-yet-classified. Collapsing them makes coverage unmeasurable,
    because the number stops distinguishing backlog from scope."""

    #: carries at least one resolved concept IRI
    CLASSIFIED = "classified"
    #: in scope, not yet classified — PENDING work, counted as backlog
    UNCLASSIFIED = "unclassified"
    #: permanently outside the scheme (external-vendor, unrelated pages) —
    #: never pending, never counted as backlog
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class Concept:
    iri: str
    notation: str
    tier: str
    pref_label: str
    #: skos:broader — the parent_* link the taxonomy row already carries,
    #: read as a SKOS relation; ``None`` for a top concept
    broader: str | None


@dataclass(frozen=True)
class ThemeResolution:
    """What a set of raw theme values resolved to. ``unrecognised`` is
    RETURNED, never raised — the standing aliases-suggest / values-decide
    discipline: an unknown value is a finding for the reader, not an
    exception for the caller."""

    iris: tuple[str, ...]
    unrecognised: tuple[str, ...]

    @property
    def status(self) -> ThemeStatus:
        return ThemeStatus.CLASSIFIED if self.iris else ThemeStatus.UNCLASSIFIED


@dataclass(frozen=True)
class ConceptScheme:
    uri: str
    pref_label: str
    concepts: dict[str, Concept]  # keyed by IRI
    _by_notation: dict[str, str]  # notation -> IRI

    def iri_for(self, notation: str) -> str | None:
        return self._by_notation.get(notation)

    def __contains__(self, iri: object) -> bool:
        return iri in self.concepts

    def resolve(self, value: str | None) -> str | None:
        """A full concept IRI or a bare notation → the IRI; anything else
        (including a label) → ``None``. Case-sensitive on purpose: notations
        are identifiers, not prose."""
        if not value:
            return None
        value = value.strip()
        if value in self.concepts:
            return value
        return self._by_notation.get(value)

    def resolve_all(self, values: list[str] | tuple[str, ...]) -> ThemeResolution:
        iris: list[str] = []
        bad: list[str] = []
        for value in values:
            iri = self.resolve(value)
            if iri is None:
                bad.append(value)
            elif iri not in iris:
                iris.append(iri)
        return ThemeResolution(iris=tuple(iris), unrecognised=tuple(bad))

    def broader_closure(self, iri: str) -> tuple[str, ...]:
        """The IRI and every skos:broader ancestor — what annotation at one
        tier yields for free at the tiers above (gate §C annotation depth).
        Resolution only; no edge is written here."""
        out: list[str] = []
        cur: str | None = iri
        while cur is not None and cur in self.concepts and cur not in out:
            out.append(cur)
            cur = self.concepts[cur].broader
        return tuple(out)


def _notation(row: dict, notation_from: str) -> str:
    value = row.get(notation_from)
    return str(value) if value not in (None, "") else str(row["id"])


@lru_cache(maxsize=4)
def load_concept_scheme(path: str | Path | None = None) -> ConceptScheme:
    """Read the ``concept_scheme`` block and materialise every candidate
    concept from the tiers it names. Whether a Product IS the concept or HAS
    one is the gate's question; this reader only mints the IRIs the join
    needs either way."""
    source = Path(path) if path else DEFAULT_SCHEME_PATH
    doc = yaml.safe_load(source.read_text(encoding="utf-8"))
    decl = doc["concept_scheme"]
    uri = decl["uri"]
    notation_from = decl.get("notation_from", "id")
    nodes = doc["nodes"]
    concepts: dict[str, Concept] = {}
    by_notation: dict[str, str] = {}
    id_to_iri: dict[str, str] = {}
    for tier_decl in decl["concept_tiers"]:
        tier = tier_decl["tier"]
        broader_key = tier_decl.get("broader")
        for row in nodes.get(tier, []):
            notation = _notation(row, notation_from)
            iri = f"{uri}#{notation}"
            broader = None
            if broader_key and row.get(broader_key):
                broader = id_to_iri.get(str(row[broader_key]))
            concepts[iri] = Concept(
                iri=iri,
                notation=notation,
                tier=tier,
                pref_label=str(row.get("name", notation)),
                broader=broader,
            )
            by_notation[notation] = iri
            id_to_iri[str(row["id"])] = iri
    return ConceptScheme(
        uri=uri,
        pref_label=str(decl.get("pref_label", uri)),
        concepts=concepts,
        _by_notation=by_notation,
    )


def theme_status(classification: str | None, resolution: ThemeResolution | None) -> ThemeStatus:
    """The three-way split, decided once so the scraper side and the coverage
    report cannot disagree. An External (vendor / public) source is out of
    scope PERMANENTLY — it is never pending, whatever its theme field says;
    everything else is classified when it resolved to at least one IRI and
    unclassified otherwise."""
    if (classification or "").strip().lower() == "external":
        return ThemeStatus.OUT_OF_SCOPE
    if resolution is not None and resolution.iris:
        return ThemeStatus.CLASSIFIED
    return ThemeStatus.UNCLASSIFIED
