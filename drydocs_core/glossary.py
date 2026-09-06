"""The business glossary as a READ surface (R19, 2026-09-06).

Reads the ``drydocs.glossary.v1`` files — ``config/glossary/terms-public.yaml``
(publishable senses) and the Internal twin ``internal/glossary/terms.yaml`` when
the checkout carries it — and answers one question for the Q&A pipeline: what
senses does this acronym have, and at what confidence?

THE RULE THIS SERVES: a sense is APPROVED only at ``confidence: confirmed``
(or ``corrected``, which is a confirmation that overturned an earlier one). A
``candidate`` or ``likely`` sense is a decoding hint an SME has not ruled on,
so the pipeline may OFFER it as a choice but never silently resolve a term
onto it. Pure config read; no graph, no LLM, no write.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
PUBLIC_PATH = _REPO_ROOT / "config" / "glossary" / "terms-public.yaml"
INTERNAL_PATH = _REPO_ROOT / "internal" / "glossary" / "terms.yaml"
SCHEMA = "drydocs.glossary.v1"
#: The confidence values at which a sense counts as APPROVED — an SME ruled.
APPROVED_CONFIDENCE = frozenset({"confirmed", "corrected"})


@dataclass(frozen=True)
class GlossarySense:
    acronym: str
    term_id: str
    scope: str
    pref_label: str
    alt_labels: tuple[str, ...]
    definition: str
    confidence: str
    source: str  # the file the sense came from, repo-relative

    @property
    def approved(self) -> bool:
        return self.confidence in APPROVED_CONFIDENCE


def _read(path: Path) -> list[GlossarySense]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if doc.get("schema") != SCHEMA:
        raise ValueError(
            f"glossary {path.name}: expected schema {SCHEMA}, got {doc.get('schema')!r}"
        )
    try:
        source = str(path.relative_to(_REPO_ROOT)).replace("\\", "/")
    except ValueError:
        source = path.name
    out: list[GlossarySense] = []
    for entry in doc.get("terms") or []:
        acronym = str(entry.get("acronym", "")).strip()
        if not acronym:
            continue
        for sense in entry.get("senses") or []:
            out.append(
                GlossarySense(
                    acronym=acronym,
                    term_id=str(sense.get("term_id", "")),
                    scope=str(sense.get("scope", "")),
                    pref_label=" ".join(str(sense.get("pref_label", "")).split()),
                    alt_labels=tuple(str(a) for a in sense.get("alt_labels") or []),
                    definition=" ".join(str(sense.get("definition", "")).split()),
                    confidence=str(sense.get("confidence", "candidate")),
                    source=source,
                )
            )
    return out


@lru_cache(maxsize=4)
def load_glossary(paths: tuple[str, ...] | None = None) -> tuple[GlossarySense, ...]:
    """Every sense in the given files (default: the public file plus the
    Internal twin when present), in file order. A missing default file is
    skipped — the public file is the one the schema guard requires."""
    targets = (
        [Path(p) for p in paths]
        if paths is not None
        else [p for p in (PUBLIC_PATH, INTERNAL_PATH) if p.exists()]
    )
    senses: list[GlossarySense] = []
    for path in targets:
        senses.extend(_read(path))
    return tuple(senses)


def senses_for(
    acronym: str, senses: tuple[GlossarySense, ...] | None = None
) -> tuple[GlossarySense, ...]:
    """All senses of one acronym, case-insensitive on the key."""
    key = acronym.strip().lower()
    return tuple(
        s for s in (senses if senses is not None else load_glossary()) if s.acronym.lower() == key
    )
