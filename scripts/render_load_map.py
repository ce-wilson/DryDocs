"""Generate the N4 load map — ONE surface joining sources, loaders, commands,
order, column ledgers, taxonomy captures and ontology mappings.

Joins the N3 declarations (BaseLoader.source_id, cli.COMMAND_LOADERS,
cli.CANONICAL_LOAD_SEQUENCE) to config/source-registry.yaml, the
config/source-mappings/ column ledgers (via each entry's ``locator.mapping``
pointer), the config/taxonomy/ captures (their top-level ``source:`` key) and
config/taxonomy-ontology-map.yaml, and emits
``web/src/generated/load-map.json``. ``tests/unit/test_load_map_json.py`` is
the drift guard; a default-paths ``render_board.py`` run refreshes this file
alongside the board, gates.json and the enforcement matrix (J17/J20 — one
entry point, no stale renders).

Ledger coverage renders in the THREE states governance already defines (N2),
never omitted:
- ``ledger``      — the entry carries a ``locator.mapping`` column ledger;
- ``pending``     — confirmed but no ledger yet (the frozen shrink-only
                    LEDGER_PENDING set, enforced by test_source_mapping_drift);
- ``placeholder`` — not yet SME-confirmed.
A source silently absent from the render is a defect (guarded).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

REGISTRY = REPO / "config" / "source-registry.yaml"
TAXONOMY_DIR = REPO / "config" / "taxonomy"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map.yaml"
OUT = REPO / "web" / "src" / "generated" / "load-map.json"


def _ledger_state(entry: dict) -> dict:
    mapping = (entry.get("locator") or {}).get("mapping")
    if mapping:
        return {"state": "ledger", "path": mapping}
    if entry.get("confirmed"):
        return {"state": "pending", "path": None}
    return {"state": "placeholder", "path": None}


def build_load_map() -> dict:
    from drydocs import cli  # deferred: scripts/ runs outside the package

    registry_entries = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["sources"]
    map_entries = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))["mappings"]

    # taxonomy captures, joined by their own top-level `source:` declaration
    captures_by_source: dict[str, list[str]] = {}
    for path in sorted(TAXONOMY_DIR.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        source = doc.get("source") if isinstance(doc, dict) else None
        if source:
            captures_by_source.setdefault(source, []).append(
                path.relative_to(REPO).as_posix()
            )

    # loaders by source_id; cli names + commands reverse-joined
    cli_name_by_class = {cls: nm for nm, cls in cli.LOADER_REGISTRY.items()}
    commands_by_class: dict[type, list[str]] = {}
    for command, classes in sorted(cli.COMMAND_LOADERS.items()):
        for cls in classes:
            commands_by_class.setdefault(cls, []).append(command)

    all_classes = set(cli.LOADER_REGISTRY.values())
    for classes in cli.COMMAND_LOADERS.values():
        all_classes.update(classes)

    def _loader_row(cls: type) -> dict:
        return {
            "name": cls.name,
            "class": cls.__name__,
            "cli_name": cli_name_by_class.get(cls),
            "source_label": cls.source_label,
            "commands": sorted(commands_by_class.get(cls, [])),
        }

    loaders_by_source: dict[str, list[dict]] = {}
    for cls in all_classes:
        if cls.source_id is not None:
            loaders_by_source.setdefault(cls.source_id, []).append(_loader_row(cls))
    for rows in loaders_by_source.values():
        rows.sort(key=lambda r: r["name"])

    # ontology mappings by taxonomy.source
    mappings_by_source: dict[str, list[dict]] = {}
    unmatched_map_sources: list[dict] = []
    registry_ids = {e["id"] for e in registry_entries}
    for m in map_entries:
        source = (m.get("taxonomy") or {}).get("source")
        row = {
            "id": m.get("id"),
            "status": m.get("status"),
            "label": (m.get("ontology") or {}).get("neo4j_label"),
        }
        if source in registry_ids:
            mappings_by_source.setdefault(source, []).append(row)
        else:
            # never silently dropped — a map entry pointing at no registered
            # source is drift worth seeing on the one surface
            unmatched_map_sources.append({**row, "source": source})

    sources: list[dict] = []
    for entry in registry_entries:  # registry order — the file's own grouping
        sid = entry["id"]
        sources.append(
            {
                "id": sid,
                "kind": entry.get("kind"),
                "classification": entry.get("classification"),
                "confirmed": bool(entry.get("confirmed")),
                "ledger": _ledger_state(entry),
                "taxonomy_captures": captures_by_source.get(sid, []),
                "ontology_mappings": mappings_by_source.get(sid, []),
                "loaders": loaders_by_source.get(sid, []),
            }
        )

    sequence = [
        {
            "command": command,
            "mode": mode,
            "note": note,
            "loaders": [cls.name for cls in cli.COMMAND_LOADERS.get(command, ())],
        }
        for command, mode, note in cli.CANONICAL_LOAD_SEQUENCE
    ]

    sourceless = [
        {
            "name": cls.name,
            "class": cls.__name__,
            "reason": reason,
            "commands": sorted(commands_by_class.get(cls, [])),
        }
        for cls, reason in sorted(
            cli.SOURCELESS_LOADERS.items(), key=lambda kv: kv[0].__name__
        )
    ]

    return {
        "note": (
            "GENERATED by scripts/render_load_map.py -- never hand-edit. "
            "tests/unit/test_load_map_json.py fails when this drifts from the "
            "declarations it joins (N3) or the registries it reads. One surface "
            "answering taxonomy-by-source, ontology, extract and loads."
        ),
        "sequence": sequence,
        "ad_hoc_commands": sorted(cli.AD_HOC_COMMANDS),
        "sources": sources,
        "sourceless_loaders": sourceless,
        "map_entries_without_registry_source": unmatched_map_sources,
    }


def main() -> int:
    data = build_load_map()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_ledger = sum(1 for s in data["sources"] if s["ledger"]["state"] == "ledger")
    n_pending = sum(1 for s in data["sources"] if s["ledger"]["state"] == "pending")
    print(
        f"wrote {OUT} ({len(data['sources'])} sources: {n_ledger} with ledgers, "
        f"{n_pending} pending, "
        f"{len(data['sources']) - n_ledger - n_pending} placeholders; "
        f"{len(data['sequence'])} sequence steps)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
