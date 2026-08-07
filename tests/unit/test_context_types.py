"""O45 guards: the context-type vocabulary (config/taxonomy/context-types.yaml)
and its generated artifact (web/src/generated/context-types.json).

Pins: schema id, entry field completeness, id uniqueness, the status enum
(active|retired — values are never deleted, only retired), and artifact drift
(the gates.json pattern: the committed json must equal a fresh regeneration)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO / "config" / "taxonomy" / "context-types.yaml"
COMMITTED = REPO / "web" / "src" / "generated" / "context-types.json"

VALID_STATUSES = {"active", "retired"}


def _data() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_context_types", REPO / "scripts" / "render_context_types.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_schema_and_header():
    data = _data()
    assert data["schema"] == "drydocs.context-types.v1"
    assert data["classification"] == "Internal-Public"
    assert "context_types" in data and data["context_types"]


def test_entries_are_complete():
    for e in _data()["context_types"]:
        for field in ("id", "label", "description", "status"):
            assert e.get(field), f"context type {e.get('id', '?')} missing {field}"


def test_ids_are_unique():
    ids = [e["id"] for e in _data()["context_types"]]
    assert len(ids) == len(set(ids)), "duplicate context-type id"


def test_status_enum():
    for e in _data()["context_types"]:
        assert e["status"] in VALID_STATUSES, (
            f"context type {e['id']} has status {e['status']!r} — values are "
            "never deleted, only retired (active|retired)"
        )


def test_seed_values_present_and_active():
    """The four seed values from the intake plan §2 stay resolvable. They may
    be RETIRED later (that is the enum's job) but they may never vanish —
    historical intake records reference these ids."""
    by_id = {e["id"]: e for e in _data()["context_types"]}
    for seed in ("job-failure", "missed-data-load", "missed-file", "data-issue"):
        assert seed in by_id, f"seed context type {seed} was deleted — retire, never delete"


def test_committed_artifact_matches_regeneration():
    fresh = _generator().build_context_types()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "context-types.json drifted from config/taxonomy/context-types.yaml — "
        "run: python scripts/render_context_types.py and commit the result"
    )


def test_artifact_carries_only_active_entries_in_the_dropdown_list():
    fresh = _generator().build_context_types()
    source_active = {e["id"] for e in _data()["context_types"] if e["status"] == "active"}
    assert {e["id"] for e in fresh["context_types"]} == source_active
