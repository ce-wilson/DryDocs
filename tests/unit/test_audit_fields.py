"""Drift gate for config/audit-fields.yaml (doc 06 — source audit envelope).

Per the doc-06 design (and port-prompt step 15): every confirmed source in
config/source-registry.yaml must have an audit-fields entry; confirmed entries
map ONLY the four frozen envelope property names; stub entries mark sources
whose envelope gate has not run. Company-side, a stub for a confirmed source
staying red-until-filled is the sync signal — producer-side stubs are legal.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_FILE = ROOT / "config" / "audit-fields.yaml"
REGISTRY_FILE = ROOT / "config" / "source-registry.yaml"
DOC_REGISTRY_FILE = ROOT / "config" / "doc-source-registry.yaml"
VOCAB_FILE = ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"

FROZEN_ENVELOPE = [
    "source_created_by",
    "source_created_at",
    "source_updated_by",
    "source_updated_at",
]


@pytest.fixture(scope="module")
def audit() -> dict:
    return yaml.safe_load(AUDIT_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> dict:
    """v2: the audit ledger keys on DATASET ids, plus the doc-ledger corpora
    the runtime registry unions in (their pipeline twins dropped at N9)."""
    reg = yaml.safe_load(REGISTRY_FILE.read_text(encoding="utf-8"))
    doc = yaml.safe_load(DOC_REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"sources": list(reg["datasets"]) + list(doc["sources"])}


def test_schema_and_classification(audit: dict) -> None:
    assert audit["schema"] == "drydocs.audit-fields.v1"
    assert audit["classification"] == "Internal-Public"


def test_envelope_property_names_are_frozen(audit: dict) -> None:
    assert audit["envelope"] == FROZEN_ENVELOPE


def test_every_confirmed_source_has_an_entry(audit: dict, registry: dict) -> None:
    confirmed = {s["id"] for s in registry["sources"] if s.get("confirmed") is True}
    covered = {s["id"] for s in audit["sources"]}
    assert (
        confirmed <= covered
    ), f"confirmed sources missing an audit-fields entry: {confirmed - covered}"


def test_entries_reference_registered_sources(audit: dict, registry: dict) -> None:
    registered = {s["id"] for s in registry["sources"]}
    for entry in audit["sources"]:
        assert entry["id"] in registered, f"audit-fields entry {entry['id']} not in source-registry"


def test_entry_status_vocabulary(audit: dict) -> None:
    for entry in audit["sources"]:
        assert entry["status"] in {"confirmed", "stub"}, entry["id"]


def test_confirmed_entries_are_gated_and_envelope_only(audit: dict) -> None:
    for entry in audit["sources"]:
        if entry["status"] != "confirmed":
            continue
        assert entry.get("decided_by"), f"{entry['id']}: confirmed without a gate id"
        for obj in entry["objects"]:
            keys = set(obj["mapping"].keys())
            assert keys <= set(
                FROZEN_ENVELOPE
            ), f"{entry['id']}/{obj['object']}: non-envelope keys {keys - set(FROZEN_ENVELOPE)}"
            assert keys, f"{entry['id']}/{obj['object']}: empty mapping"


def test_controlm_mapping_matches_the_gate(audit: dict) -> None:
    """The gate-confirmed Control-M envelope (controlm-q1q3-phase1):
    CREATION_* + CHANGE_* on jobs; VERSION_* excluded as duplicates."""
    entry = next(s for s in audit["sources"] if s["id"] == "controlm@[db].psgmgr.cm_def_vjob")
    vjob = next(o for o in entry["objects"] if o["object"] == "CM_DEF_VJOB")
    assert vjob["mapping"]["source_created_by"] == "CREATION_USER"
    assert vjob["mapping"]["source_updated_by"] == "CHANGE_USERID"
    excluded_cols = {e["column"] for e in vjob["excluded"]}
    assert {"VERSION_USER", "VERSION_TIMESTAMP"} <= excluded_cols


def test_loaders_set_exactly_the_confirmed_envelope(audit: dict) -> None:
    """Phase-1 wiring check: the Control-M cyphers SET each confirmed envelope
    property, and never one the mapping doesn't grant (folders have no
    creation columns, so no source_created_* there)."""
    cypher_dir = ROOT / "drydocs" / "loaders" / "cypher"
    jobs = (cypher_dir / "controlm_jobs.cypher").read_text(encoding="utf-8")
    folders = (cypher_dir / "controlm_folders.cypher").read_text(encoding="utf-8")
    for prop in FROZEN_ENVELOPE:
        assert f"j.{prop}" in jobs, f"jobs cypher missing {prop}"
    assert "f.source_updated_by" in folders
    assert "f.source_updated_at" in folders
    assert "f.source_created_by" not in folders  # no creation columns on CM_DEF_VTAB
    assert "f.source_created_at" not in folders


# ---- property-term bindings (M4, gate envelope-property-terms) --------------


@pytest.fixture(scope="module")
def property_terms() -> list[dict]:
    vocab = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    return vocab["property_terms"]


def test_every_envelope_property_carries_a_term_binding(
    audit: dict, property_terms: list[dict]
) -> None:
    """M4 drift guard: the frozen envelope names each have a registered
    property-term binding in the vocabulary's property_terms section."""
    bound = {e["property"] for e in property_terms}
    missing = set(audit["envelope"]) - bound
    assert not missing, f"envelope properties without a property_terms binding: {missing}"


def test_property_term_curies_expand_and_are_gated(property_terms: list[dict]) -> None:
    from drydocs_core.ontology.namespaces import expand

    for entry in property_terms:
        assert entry.get("decided_by"), f"{entry['property']}: binding without a gate id"
        iri = expand(entry["term"])
        assert iri.startswith("http"), f"{entry['property']}: {entry['term']} -> {iri}"


def test_the_ruled_envelope_bindings(property_terms: list[dict]) -> None:
    """The gate's rulings, pinned: the dct: trio plus the recorded-imprecision
    contributor row (gate envelope-property-terms §B1/§B2)."""
    by_prop = {e["property"]: e for e in property_terms}
    assert by_prop["source_created_by"]["term"] == "dct:creator"
    assert by_prop["source_created_at"]["term"] == "dct:created"
    assert by_prop["source_updated_by"]["term"] == "dct:contributor"
    assert by_prop["source_updated_at"]["term"] == "dct:modified"
