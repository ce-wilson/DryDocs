"""Enforce the sensitivity-classification axis (no Neo4j required).

Every ingested source must carry a `classification` from the controlled vocabulary
in config/classification.yaml plus a `source`; External sources must additionally
cite `source_url` + `captured_at`. This is the publish-boundary safety net — it fails
CI if a source is registered without a sensitivity label.
"""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

CONFIG_DIR        = Path(__file__).resolve().parents[2] / "config"
CLASSIFICATION    = CONFIG_DIR / "classification.yaml"
SOURCE_REGISTRY   = CONFIG_DIR / "source-registry.yaml"
REFERENCE_REGISTRY = Path(__file__).resolve().parents[2] / "reference" / "REGISTRY.yaml"


def test_classification_file_exists() -> None:
    assert CLASSIFICATION.exists(), f"Missing controlled vocabulary: {CLASSIFICATION}"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_classification_vocabulary_shape() -> None:
    doc = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    ids = {lvl["id"] for lvl in doc.get("levels", [])}
    assert ids == {"External", "Internal-Public", "Internal", "Internal-Confidential"}, (
        f"classification levels drifted: {ids}"
    )
    # publishable must be a bool on every level
    for lvl in doc["levels"]:
        assert isinstance(lvl.get("publishable"), bool), f"{lvl['id']} missing publishable bool"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_every_source_is_classified() -> None:
    """Each source-registry entry has a valid classification + source; External
    entries additionally carry source_url + captured_at."""
    if not SOURCE_REGISTRY.exists():
        pytest.skip("source-registry.yaml not present")

    vocab = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    valid = {lvl["id"] for lvl in vocab["levels"]}

    reg = yaml.safe_load(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    failures: list[str] = []

    for src in reg.get("sources", []):
        sid = src.get("id", "<no-id>")
        cls = src.get("classification")
        if cls not in valid:
            failures.append(f"[{sid}] classification '{cls}' not in {sorted(valid)}")
            continue
        if not src.get("source"):
            failures.append(f"[{sid}] missing required field 'source'")
        if cls == "External":
            for field in ("source_url", "captured_at"):
                if not src.get(field):
                    failures.append(f"[{sid}] External source missing '{field}'")

    assert not failures, (
        f"{len(failures)} classification error(s):\n" + "\n".join(failures)
    )


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_reference_registry_is_external() -> None:
    """All Tier-1 reference material is External by definition — the registry must
    declare it, so the publish boundary can treat reference/ as publishable."""
    if not REFERENCE_REGISTRY.exists():
        pytest.skip("reference/REGISTRY.yaml not present")
    reg = yaml.safe_load(REFERENCE_REGISTRY.read_text(encoding="utf-8"))
    assert reg.get("classification") == "External", (
        "reference/REGISTRY.yaml must declare top-level `classification: External`"
    )
