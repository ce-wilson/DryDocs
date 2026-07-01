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
    "mapping": [{"n": 1, "element": "Folder", "target": ":JobFolder", "edge": "—"}],
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
    assert ":JobFolder" in out                       # mapping table rendered


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
