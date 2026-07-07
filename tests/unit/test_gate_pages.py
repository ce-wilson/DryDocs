"""Unit tests for gate_pages (drydocs/gate_pages.py) — pure, no Neo4j."""
from __future__ import annotations

import pytest

from drydocs.gate_pages import (
    DEFAULT_GATE_PROMPTS_DIR,
    GateSpecError,
    load_gate_spec,
    render_gate_page,
    spec_from_dict,
)

_DOC = {
    "id": "demo",
    "title": "Demo gate",
    "step": "Step 1",
    "classification": "Internal-Public",
    "summary": "loads a thing",
    "sections": [
        {"title": "A. Scope", "confirmations": ["source is authoritative", "no PII in scope"]},
        {"title": "B. Sign-off", "confirmations": ["safe to confirm"]},
    ],
    "mapping": [{"n": 1, "element": "Folder", "target": ":ControlMFolder", "edge": "—"}],
}


def test_spec_counts_confirmations() -> None:
    spec = spec_from_dict(_DOC)
    assert spec.total_confirmations == 3
    assert spec.sections[0].title == "A. Scope"


def test_spec_requires_title() -> None:
    with pytest.raises(GateSpecError):
        spec_from_dict({"sections": []})


def test_render_has_checkbox_per_confirmation() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert out.count('type="checkbox"') == 3


def test_render_includes_gate_semantics() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert "No graph write" in out
    assert "localStorage" in out                    # persistence wired
    assert "CLASSIFICATION: Internal-Public" in out
    assert "0 / 3" in out                            # progress counter seeded
    assert ":ControlMFolder" in out                       # mapping table rendered


def test_render_is_self_contained() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert out.startswith("<!doctype html>")
    assert "<script>" in out and "<style>" in out


def test_committed_example_spec_loads_and_renders() -> None:
    spec = load_gate_spec(DEFAULT_GATE_PROMPTS_DIR / "vendor-bmc-example.yaml")
    assert spec.classification in {"External", "Internal-Public"}
    out = render_gate_page(spec)
    assert spec.title in out
    assert out.count('type="checkbox"') == spec.total_confirmations


_DOC_RICH = {
    **_DOC,
    "meta": {"Module": "drydocs-core", "Registry ref": "controlm-psgmgr — confirmed"},
    "provenance": [
        {
            "label": ":ControlMFolder",
            "source_object": "CM_DEF_VTAB",
            "key": "folder_id",
            "loader": "controlm_folders",
            "properties": [
                {"name": "folder_id", "origin": "source", "from": "TABLE_ID"},
                {"name": "app_code", "origin": "derived", "from": "name pos 3-5", "note": "platform caveat"},
            ],
        }
    ],
}


def test_render_meta_header_card() -> None:
    out = render_gate_page(spec_from_dict(_DOC_RICH))
    assert "controlm-psgmgr" in out and "drydocs-core" in out


def test_render_provenance_origin_badges() -> None:
    out = render_gate_page(spec_from_dict(_DOC_RICH))
    assert "origin-source" in out and "origin-derived" in out
    assert "CM_DEF_VTAB" in out and "platform caveat" in out


def test_provenance_rejects_bad_origin() -> None:
    bad = {**_DOC, "provenance": [{"label": "X", "properties": [{"name": "p", "origin": "guessed"}]}]}
    with pytest.raises(GateSpecError):
        spec_from_dict(bad)


def test_committed_q1q3_spec_loads_and_renders() -> None:
    spec = load_gate_spec(DEFAULT_GATE_PROMPTS_DIR / "controlm-q1q3-phase1.yaml")
    assert spec.classification == "Internal-Public"
    out = render_gate_page(spec)
    assert out.count('type="checkbox"') == spec.total_confirmations
    assert "origin-derived" in out                    # provenance split rendered
    assert "CONTAINS_FOLDER" in out                   # proposed edge visible
