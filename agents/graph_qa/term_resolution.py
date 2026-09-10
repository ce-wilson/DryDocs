"""Term resolution and the clarification request (R19, 2026-09-06).

The Tower → :TOMRole mismatch (R18) was the router choosing a near match for a
term it did not know. R22 answered the part that has a DECLARED non-graph
source; this module answers the rest: a question that names an acronym or a
label-shaped term the pipeline cannot resolve is not routed at all. It is
returned as a STRUCTURED CLARIFICATION REQUEST — the unresolved term, the
candidate senses and labels the pipeline can see, and concise choices — and
the console asks the person before any Cypher runs.

What counts as RESOLVED (the acceptance's four sources, nothing more):

* a registered QuerySpec — its id (whole and by dotted segment), its param
  names, and the words of its description;
* an ACTIVE vocabulary row — label, endpoints, role, and their CamelCase /
  snake_case parts;
* the LIVE schema of the routed database — labels, relationship types,
  property keys, and their parts;
* an APPROVED glossary sense (``confidence: confirmed`` / ``corrected``) or a
  declared UI concept (``config/taxonomy/ui-concepts.yaml``).

Everything else the pipeline can see — an unconfirmed glossary sense, a label
that merely resembles the term — becomes a CHOICE, never a resolution. This
is a disambiguation contract, not permission to invent ontology: a term the
person cannot resolve either stays unresolved (the answer says so) or goes to
the SME through the HITL gate, exactly as before.

Detection is deterministic and conservative on purpose: acronym-shaped tokens
(two to eight capitals/digits) outside a small stop set, and label-shaped
tokens (mixed case with an internal capital, or an explicit ``:Label``). A
lower-case question detects nothing and the pipeline is byte-for-byte the
single pass it was — the regression path the acceptance names.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field

from drydocs_core.glossary import GlossarySense, load_glossary
from drydocs_core.ui_concepts import load_ui_concepts

#: The two choice ids every term carries besides its candidates. The console
#: renders them as the free-text box and the "answer anyway" action; the agent
#: reads the RESULT of either through the ``clarifications`` control field.
FREE_TEXT_CHOICE = "__free_text__"
PROCEED_CHOICE = "__proceed__"

#: Capitalised words that are English, not acronyms — a question written with
#: emphasis ("show ALL jobs") must not be asked what ALL means. Kept short and
#: obviously non-domain; the resolution sources below are what decide the rest.
ACRONYM_STOP_WORDS = frozenset(
    """
    A AN AND ARE AS AT BE BY DO DOES FOR FROM HAS HAVE HOW I IF IN IS IT ITS
    MANY ME MY NO NOT OF ON OR OUR SHOW THE THEIR THERE THIS TO US WAS WE WHAT
    WHEN WHERE WHICH WHO WHY WILL WITH YES YOU ALL ANY EACH EVERY LIST GIVE
    TELL FIND COUNT TOP LAST FIRST NEW OLD
    """.split()
)

#: House and platform names that are not graph terms and need no glossary.
HOUSE_TERMS = frozenset(
    t.lower()
    for t in (
        "DryDocs",
        "Neo4j",
        "Cypher",
        "QuerySpec",
        "QuerySpecs",
        "Explorer",
        "Control-M",
        "ControlM",
        "SQL",
        "JSON",
        "CSV",
        "YAML",
        "XML",
        "HTML",
        "PDF",
        "API",
        "URL",
        "URI",
        "URN",
        "UI",
        "ID",
        "IDS",
        "DB",
        "LLM",
        "ADK",
        "ADR",
        "HITL",
        "SME",
        "OK",
        "AM",
        "PM",
        "UTC",
        "EST",
        "GMT",
    )
)

_ACRONYM_RE = re.compile(r"(?<![A-Za-z0-9_:])[A-Z][A-Z0-9]{1,7}(?![A-Za-z0-9_])")
# mixed case with at least one lower-case letter and two capitals: ControlMJob,
# TOMRole, BusinessApplication — the shape of a Neo4j label written as one word.
_LABEL_RE = re.compile(
    r"(?<![A-Za-z0-9_:])(?=[A-Za-z0-9]*[a-z])(?=(?:[A-Za-z0-9]*[A-Z]){2})[A-Z][A-Za-z0-9]{2,}(?![A-Za-z0-9_])"
)
_EXPLICIT_LABEL_RE = re.compile(r"(?<![A-Za-z0-9_]):([A-Z][A-Za-z0-9_]{1,})(?![A-Za-z0-9_])")
_CAMEL_SPLIT_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9]+")


@dataclass(frozen=True)
class DetectedTerm:
    term: str
    kind: str  # 'acronym' | 'label'


@dataclass
class Candidate:
    id: str
    label: str
    detail: str
    source: str  # 'glossary' | 'label' | 'relationship' | 'property' | 'spec' | 'declared'


@dataclass
class UnresolvedTerm:
    term: str
    kind: str
    candidates: list[Candidate] = field(default_factory=list)
    choices: list[dict] = field(default_factory=list)


@dataclass
class ClarificationRequest:
    terms: list[UnresolvedTerm]
    prompt: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Clarification:
    """One answer from the person asking, as carried by the control part.
    ``resolution`` is their free text or the label of the choice they took;
    ``declined`` is the "answer anyway" path — no resolution, and the answer
    must say so."""

    term: str
    resolution: str | None = None
    declined: bool = False


def parse_clarifications(raw: object) -> list[Clarification]:
    """The ``clarifications`` control field as sent by the console: a list of
    ``{term, resolution, declined}``. Anything malformed is dropped — a bad
    clarification degrades to "not clarified", never to an error."""
    out: list[Clarification] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or "").strip()
        if not term:
            continue
        resolution = item.get("resolution")
        resolution = " ".join(str(resolution).split()) if resolution not in (None, "") else None
        declined = bool(item.get("declined")) or resolution is None
        out.append(Clarification(term=term, resolution=resolution, declined=declined))
    return out


# -- detection ---------------------------------------------------------------
def detect_terms(question: str) -> list[DetectedTerm]:
    """Acronym- and label-shaped tokens, in order of appearance, deduplicated
    case-insensitively. A question written entirely in capitals is emphasis,
    not a string of acronyms, and detects nothing."""
    words = _WORD_RE.findall(question)
    alpha = [w for w in words if any(c.isalpha() for c in w)]
    if alpha and all(w.upper() == w for w in alpha):
        return []
    seen: set[str] = set()
    found: list[DetectedTerm] = []

    def add(term: str, kind: str) -> None:
        key = term.lower()
        if key in seen or key in HOUSE_TERMS:
            return
        seen.add(key)
        found.append(DetectedTerm(term=term, kind=kind))

    for match in _EXPLICIT_LABEL_RE.finditer(question):
        add(match.group(1), "label")
    for match in _ACRONYM_RE.finditer(question):
        token = match.group(0)
        if token in ACRONYM_STOP_WORDS:
            continue
        add(token, "acronym")
    for match in _LABEL_RE.finditer(question):
        add(match.group(0), "label")
    # keep question order, whatever the pass that found each one
    found.sort(key=lambda t: question.lower().find(t.term.lower()))
    return found


def _parts(name: str) -> set[str]:
    """CamelCase / snake_case parts, two or more characters, lower-cased —
    ``seal_id`` → {seal, id}; ``ControlMJob`` → {control, m, job} minus ``m``."""
    out: set[str] = set()
    for piece in re.split(r"[_\-\s.]+", name):
        for part in _CAMEL_SPLIT_RE.findall(piece):
            if len(part) >= 2:
                out.add(part.lower())
    return out


# -- the resolution index ----------------------------------------------------
class ResolutionIndex:
    """What the pipeline can resolve a term against, built once per question
    that needs it, from the same four sources the acceptance names."""

    def __init__(
        self,
        *,
        specs: Iterable,
        vocab_rows: Iterable[dict],
        live_schema: dict,
        glossary: Iterable[GlossarySense],
        ui_concepts: Iterable | None = None,
    ) -> None:
        self.known: set[str] = set(HOUSE_TERMS)
        self.labels: list[str] = []
        self.relationships: list[str] = []
        self.properties: list[str] = []
        self.spec_ids: list[str] = []
        self.glossary: list[GlossarySense] = list(glossary)
        for spec in specs:
            self.spec_ids.append(spec.id)
            self._know(spec.id)
            for segment in spec.id.split("."):
                self._know(segment)
            for param in getattr(spec, "params", ()) or ():
                self._know(param.name)
            for word in _WORD_RE.findall(getattr(spec, "description", "") or ""):
                self._know(word)
        for row in vocab_rows:
            for key in ("neo4j_label", "from_node", "to_node", "role"):
                value = row.get(key)
                if value:
                    self._know(str(value))
                    if key == "neo4j_label":
                        self.relationships.append(str(value))
                    elif key in ("from_node", "to_node"):
                        self.labels.append(str(value))
        for label in live_schema.get("labels") or []:
            self.labels.append(str(label))
            self._know(str(label))
        for rel in live_schema.get("relationshipTypes") or []:
            self.relationships.append(str(rel))
            self._know(str(rel))
        for prop in live_schema.get("propertyKeys") or []:
            self.properties.append(str(prop))
            self._know(str(prop))
        for sense in self.glossary:
            if sense.approved:
                self._know(sense.acronym)
                self._know(sense.pref_label)
        for concept in ui_concepts if ui_concepts is not None else load_ui_concepts():
            for name in concept.names():
                self._know(name)
        self.labels = sorted(set(self.labels))
        self.relationships = sorted(set(self.relationships))
        self.properties = sorted(set(self.properties))

    def _know(self, name: str) -> None:
        self.known.add(name.lower())
        self.known.update(_parts(name))

    def resolves(self, term: str) -> bool:
        key = term.lower()
        return key in self.known or (key.endswith("s") and key[:-1] in self.known)

    # -- candidates -----------------------------------------------------------
    def candidates(self, term: str) -> list[Candidate]:
        key = term.lower()
        out: list[Candidate] = []
        for sense in self.glossary:
            if sense.acronym.lower() == key:
                detail = sense.definition[:160] + ("…" if len(sense.definition) > 160 else "")
                out.append(
                    Candidate(
                        id=sense.term_id or f"glossary:{sense.acronym}:{sense.pref_label}",
                        label=sense.pref_label,
                        detail=f"{sense.confidence} glossary sense ({sense.scope}); {detail}",
                        source="glossary",
                    )
                )
        for source, names in (
            ("label", self.labels),
            ("relationship", self.relationships),
            ("property", self.properties),
            ("spec", self.spec_ids),
        ):
            for name in names:
                if _near(key, name):
                    out.append(
                        Candidate(
                            id=f"{source}:{name}",
                            label=name,
                            detail=f"live graph {source}"
                            if source != "spec"
                            else "registered QuerySpec",
                            source=source,
                        )
                    )
        return out[:8]


def _initials(name: str) -> str:
    return "".join(p[0] for p in _CAMEL_SPLIT_RE.findall(name.replace("_", " ")) if p).lower()


def _near(key: str, name: str) -> bool:
    lowered = name.lower()
    compact = lowered.replace("_", "")
    if key == lowered or key == compact:
        return True
    if len(key) >= 3 and (key in compact or compact in key):
        return True
    if len(key) >= 2 and _initials(name) == key:
        return True
    return len(key) >= 4 and difflib.SequenceMatcher(None, key, compact).ratio() >= 0.75


# -- the request ---------------------------------------------------------------
def _choices(term: UnresolvedTerm) -> list[dict]:
    choices = [
        {"id": c.id, "label": c.label, "detail": c.detail, "source": c.source}
        for c in term.candidates
    ]
    choices.append(
        {
            "id": FREE_TEXT_CHOICE,
            "label": "Something else — say what it means",
            "detail": "your words are carried into the query as the meaning of this term",
            "source": "you",
        }
    )
    choices.append(
        {
            "id": PROCEED_CHOICE,
            "label": "Answer anyway",
            "detail": "the term stays unresolved and the answer will say so",
            "source": "you",
        }
    )
    return choices


def _prompt(terms: list[UnresolvedTerm]) -> str:
    names = ", ".join(f"'{t.term}'" for t in terms)
    plural = len(terms) > 1
    return (
        f"Before querying the graph: {names} {'do' if plural else 'does'} not resolve to a "
        "registered QuerySpec, an active vocabulary term, a live label or property, or an "
        f"approved glossary sense. Which meaning did you intend? Choosing nothing keeps "
        f"{'them' if plural else 'it'} unresolved and the answer will say so."
    )


def build_clarification(
    question: str,
    index: ResolutionIndex,
    clarifications: Iterable[Clarification] = (),
) -> ClarificationRequest | None:
    """None when every detected term resolves or was already clarified (or
    declined) for this question; otherwise the request the console renders."""
    settled = {c.term.lower() for c in clarifications}
    unresolved: list[UnresolvedTerm] = []
    for detected in detect_terms(question):
        if detected.term.lower() in settled or index.resolves(detected.term):
            continue
        term = UnresolvedTerm(term=detected.term, kind=detected.kind)
        term.candidates = index.candidates(detected.term)
        term.choices = _choices(term)
        unresolved.append(term)
    if not unresolved:
        return None
    return ClarificationRequest(terms=unresolved, prompt=_prompt(unresolved))


def clarification_clause(clarifications: Iterable[Clarification]) -> str:
    """The prompt text that carries confirmed clarifications into the router
    and text2cypher calls — the ONE place a control field reaches the LLM, and
    it is the person's own words about their own question."""
    lines = []
    for c in clarifications:
        if c.declined or not c.resolution:
            lines.append(
                f"- {c.term}: no clarification given; treat it as unresolved and do not substitute a near match"
            )
        else:
            lines.append(f"- {c.term} means: {c.resolution}")
    if not lines:
        return ""
    return (
        "\n\nTerm clarifications from the person asking (authoritative for this question):\n"
        + "\n".join(lines)
    )


def declined_note(clarifications: Iterable[Clarification]) -> str:
    """The sentence prefixed to an answer whose question carried a DECLINED
    term: the ambiguity is stated, and a zero-row result is not a finding."""
    declined = [c.term for c in clarifications if c.declined]
    if not declined:
        return ""
    names = ", ".join(f"'{t}'" for t in declined)
    plural = len(declined) > 1
    return (
        f"Note: {names} {'were' if plural else 'was'} not resolved to a known term, so this answer "
        "may not address what you meant; a result with no rows is not evidence that nothing exists. "
        "If the term is real, it belongs with an SME through the HITL gate.\n\n"
    )


def load_glossary_senses() -> tuple[GlossarySense, ...]:
    """The default glossary loader — a seam the pipeline injects for tests."""
    return load_glossary()
