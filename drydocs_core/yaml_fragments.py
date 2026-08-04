"""S5 — the deterministic concatenating reader for split config YAMLs.

``config/taxonomy-ontology-map.yaml`` and
``drydocs_core/ontology/relationship_vocabulary.yaml`` each grew past a
thousand lines while serving many domains, so two concurrent sessions (or a
cross-repo port) collided on one file even when they touched different
domains. Each is now a DIRECTORY of per-domain fragment files; this module is
the ONE reader everything goes through.

The contract is textual on purpose: ``merged_text`` concatenates the
fragments in sorted-filename order and the result IS the document — byte-for-
byte what the single file would contain. That keeps every downstream behavior
identical (comment-preserving line scans, content hashing for staleness
detection, YAML parsing) and makes the merge trivially deterministic. A
fragment is not required to parse standalone (a file may open a top-level key
whose list the NEXT files continue), which is why parsing happens once, on
the merged text, never per fragment.

Failure modes are loud (the L17 family):
- a source that is neither a file nor a directory, or a directory with no
  ``*.yaml`` fragments, raises — an empty registry must never read as "no
  entries, carry on";
- a duplicate mapping KEY anywhere in the merged document raises — plain
  ``yaml.safe_load`` silently keeps the last duplicate, which is exactly how
  two fragments both declaring ``mappings:`` would eat each other;
- duplicate entry ids inside the known registry sections raise via
  ``load_yaml_source(..., unique=...)``.

Single files remain first-class inputs: tests and tools that build a
one-off YAML in tmp_path keep working unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class FragmentSourceError(RuntimeError):
    """A fragment source is missing, empty, or holds a duplicate key/id."""


class _DuplicateKeySafeLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys instead of last-wins."""


def _construct_mapping(loader: _DuplicateKeySafeLoader, node: yaml.MappingNode, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        if isinstance(key, str | int | float | bool | tuple) and key in seen:
            raise FragmentSourceError(
                f"duplicate key {key!r} at line {key_node.start_mark.line + 1} — "
                "yaml.safe_load would silently keep the last value; with "
                "concatenated fragments that means one fragment eating another"
            )
        if isinstance(key, str | int | float | bool | tuple):
            seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_DuplicateKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def fragment_paths(source: Path) -> list[Path]:
    """The fragments of *source* in merge order (sorted by filename)."""
    return sorted(source.glob("*.yaml"), key=lambda p: p.name)


def merged_bytes(source: str | Path) -> bytes:
    """The document bytes: the file's, or the fragments' concatenated."""
    source = Path(source)
    if source.is_file():
        return source.read_bytes()
    if source.is_dir():
        fragments = fragment_paths(source)
        if not fragments:
            raise FragmentSourceError(
                f"fragment directory holds no *.yaml files: {source} — an empty "
                "registry must never read as 'no entries'"
            )
        return b"".join(p.read_bytes() for p in fragments)
    raise FragmentSourceError(f"YAML source not found: {source}")


def merged_text(source: str | Path) -> str:
    return merged_bytes(source).decode("utf-8")


def load_yaml_source(source: str | Path, *, unique: dict[str, str] | None = None) -> Any:
    """Parse the merged document, refusing duplicate keys — and, per *unique*
    (``{section: id_field}``), duplicate entry ids inside list sections."""
    doc = yaml.load(merged_text(source), Loader=_DuplicateKeySafeLoader)
    for section, field in (unique or {}).items():
        entries = (doc or {}).get(section) or []
        seen: dict[Any, int] = {}
        for entry in entries:
            key = entry.get(field) if isinstance(entry, dict) else None
            if key is None:
                continue
            seen[key] = seen.get(key, 0) + 1
        duplicates = sorted(str(k) for k, n in seen.items() if n > 1)
        if duplicates:
            raise FragmentSourceError(
                f"{Path(source).name}: duplicate {section}[].{field} across "
                f"fragments: {duplicates}"
            )
    return doc
