"""Reader for the declared TOM role vocabulary (G70, gate §F3).

``config/taxonomy/tom-role-vocabulary.yaml`` is the ONE surface the four
formerly-hardcoded role lists defer to (gate tom-roles-enumeration-and-
cardinality §A8: the SealRole enum, the _ROLE_CANONICAL alias map, the
loader's Cypher CASE and the supplement's scheme seed — three languages,
four lists, none agreeing, and the only YAML copy read by no code). This
module is how code reads it:

- :func:`load_vocabulary` — the validated declaration (cached; ``reload`` for
  tests). Validation refuses rather than guesses, the ``log_kinds`` idiom: a
  malformed declaration is a configuration error, never a silent fallback.
- :func:`concept_for` — source name -> TOMRole concept id, the resolution the
  contact model stamps into every row (``tom_role_id``); ``None`` means
  UNDECLARED, which loads flagged (``unmapped_role``) rather than being
  refused — §A3/§F4's admit-flagged ruling.

Pure config read, no graph write — the ``concept_scheme.py`` precedent.
Drift guards live in tests/unit/test_tom_role_vocabulary.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent.parent)
VOCABULARY_FILE = _REPO_ROOT / "config" / "taxonomy" / "tom-role-vocabulary.yaml"

SCOPES = ("Individual", "Group")


class TomRoleVocabularyError(RuntimeError):
    """A declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class TomRoleClass:
    """One declared role class, both registers on one row."""

    id: str
    pref_label: str
    scope: str
    required: bool
    active: bool
    derived: bool
    seal_extract_name: str | None
    source_names: tuple[str, ...]
    catalog_name: str | None
    abbrev: str | None = None
    type: str | None = None
    note: str = ""


@dataclass(frozen=True)
class TomRoleVocabulary:
    """The declaration: the classes plus the scheme-level facts."""

    cardinality: str
    classes: tuple[TomRoleClass, ...]
    catalog_total_rows: int
    out_of_scope_families: tuple[str, ...]

    def by_id(self, class_id: str) -> TomRoleClass:
        for cls in self.classes:
            if cls.id == class_id:
                return cls
        declared = sorted(c.id for c in self.classes)
        raise TomRoleVocabularyError(
            f"undeclared TOM role class {class_id!r} — declared: {declared}"
        )

    def required_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.classes if c.required)

    def concept_for(self, source_name: str | None) -> str | None:
        """Source spelling -> concept id for an ACTIVE class; None = undeclared.

        Casefold exact match over ``source_names`` — drift tolerance ('l2 ops
        manager', trailing abbreviation parentheticals) is the alias table's
        job (``drydocs_core.models.seal``), which resolves INTO these names.
        A retired class (``active: false``) does NOT resolve: its rows load
        flagged like any undeclared name, which is what makes retirement a
        state with behaviour rather than an annotation.
        """
        if not source_name:
            return None
        wanted = source_name.strip().casefold()
        for cls in self.classes:
            if cls.active and any(name.casefold() == wanted for name in cls.source_names):
                return cls.id
        return None


def _load(path: Path) -> TomRoleVocabulary:
    import yaml

    if not path.is_file():
        raise TomRoleVocabularyError(
            f"the declared TOM role vocabulary is missing: {path}. The loaders, "
            "the supplement seed and the alias table all defer to it (G70 §A8), "
            "so a missing file is a configuration error, not a reason to fall "
            "back to a hardcoded list — that is the state G70 removed."
        )
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_classes = doc.get("classes") or []
    if not raw_classes:
        raise TomRoleVocabularyError(
            f"{path} declares no classes — an empty vocabulary is never what was meant"
        )

    cardinality = str(doc.get("cardinality") or "")
    if cardinality != "one-or-more":
        # §B3: the rule is a property of the MODEL, recorded once on the scheme.
        raise TomRoleVocabularyError(
            f"cardinality must be declared 'one-or-more' at file level (§B3), got {cardinality!r}"
        )

    seen_ids: set[str] = set()
    seen_names: dict[str, str] = {}
    classes: list[TomRoleClass] = []
    for raw in raw_classes:
        cls_id = str(raw.get("id") or "").strip()
        if not cls_id:
            raise TomRoleVocabularyError("a class with no id — the id IS the TOMRole graph key")
        if cls_id in seen_ids:
            raise TomRoleVocabularyError(f"duplicate class id {cls_id!r}")
        seen_ids.add(cls_id)

        scope = str(raw.get("scope") or "")
        if scope not in SCOPES:
            raise TomRoleVocabularyError(f"{cls_id}: unknown scope {scope!r} — declared: {SCOPES}")
        for flag in ("required", "active"):
            if not isinstance(raw.get(flag), bool):
                raise TomRoleVocabularyError(f"{cls_id}: {flag} must be an explicit boolean")
        required = bool(raw["required"])
        active = bool(raw["active"])
        derived = bool(raw.get("derived") or False)
        if required and not active:
            raise TomRoleVocabularyError(
                f"{cls_id}: a REQUIRED class cannot be retired — re-rule the register first"
            )
        if required and derived:
            # the G16 amendment's whole point: a derived fact has no place in
            # the required-contact register.
            raise TomRoleVocabularyError(
                f"{cls_id}: derived and required are mutually exclusive (G16 amendment)"
            )

        source_names = tuple(
            str(n).strip() for n in (raw.get("source_names") or []) if str(n).strip()
        )
        if not source_names:
            raise TomRoleVocabularyError(
                f"{cls_id}: no source_names — an unspellable class admits nothing"
            )
        seal_name = raw.get("seal_extract_name")
        seal_name = str(seal_name).strip() if seal_name else None
        if seal_name and seal_name not in source_names:
            raise TomRoleVocabularyError(
                f"{cls_id}: seal_extract_name {seal_name!r} must appear in source_names — "
                "it is the canonical spelling, not a separate register"
            )
        for name in source_names:
            key = name.casefold()
            if key in seen_names:
                raise TomRoleVocabularyError(
                    f"source name {name!r} declared on both {seen_names[key]!r} and {cls_id!r} — "
                    "one spelling cannot admit into two classes"
                )
            seen_names[key] = cls_id

        catalog_name = raw.get("catalog_name")
        classes.append(
            TomRoleClass(
                id=cls_id,
                pref_label=str(raw.get("pref_label") or "").strip(),
                scope=scope,
                required=required,
                active=active,
                derived=derived,
                seal_extract_name=seal_name,
                source_names=source_names,
                catalog_name=str(catalog_name).strip() if catalog_name else None,
                abbrev=(str(raw["abbrev"]).strip() if raw.get("abbrev") else None),
                type=(str(raw["type"]).strip() if raw.get("type") else None),
                note=str(raw.get("note") or "").strip(),
            )
        )

    catalog = doc.get("catalog") or {}
    return TomRoleVocabulary(
        cardinality=cardinality,
        classes=tuple(classes),
        catalog_total_rows=int(catalog.get("total_rows") or 0),
        out_of_scope_families=tuple(str(f) for f in (catalog.get("out_of_scope_families") or [])),
    )


_CACHE: dict[Path, TomRoleVocabulary] = {}


def load_vocabulary(path: Path | None = None, *, reload: bool = False) -> TomRoleVocabulary:
    """The validated declaration, cached per path (it is read on every contact
    row's validation, and the file changes only with a commit)."""
    target = path or VOCABULARY_FILE
    if reload or target not in _CACHE:
        _CACHE[target] = _load(target)
    return _CACHE[target]


def concept_for(source_name: str | None, path: Path | None = None) -> str | None:
    """Module-level convenience over :meth:`TomRoleVocabulary.concept_for`."""
    return load_vocabulary(path).concept_for(source_name)
