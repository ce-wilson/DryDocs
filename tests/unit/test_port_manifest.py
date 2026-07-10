"""Guard for PORT-MANIFEST.yaml — the machine-readable port-disposition ledger
(docs/reviews/tech-debt-port-boundary.md Phase 1, 2026-07-09).

The manifest is the authority the consumer-side reconcile-port run reads
mechanically; these checks keep it well-formed and pin the rows whose loss
would be catastrophic (a blind checkout of drydocs/publishing/** destroys the
consumer's wired Confluence originals). Pure YAML — no git, no Neo4j.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "PORT-MANIFEST.yaml"

VALID_DISPOSITIONS = {
    "clean-add", "canonical-producer", "canonical-company",
    "union-append", "per-entry", "evaluate", "never-port",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_schema_and_header(manifest: dict) -> None:
    assert manifest["schema"] == "drydocs.port-manifest.v1"
    assert manifest["classification"] == "Internal-Public"
    assert manifest.get("default"), "the no-row default must be stated"


def test_paths_unique(manifest: dict) -> None:
    paths = [r["path"] for r in manifest["rows"]]
    dupes = [p for p, n in Counter(paths).items() if n > 1]
    assert not dupes, f"duplicate manifest paths: {dupes}"


def test_dispositions_valid(manifest: dict) -> None:
    bad = [(r["path"], r.get("disposition")) for r in manifest["rows"]
           if r.get("disposition") not in VALID_DISPOSITIONS]
    assert not bad, f"invalid dispositions: {bad}"


def test_per_entry_rows_carry_an_entry_rule(manifest: dict) -> None:
    missing = [r["path"] for r in manifest["rows"]
               if r["disposition"] == "per-entry" and not r.get("entry_rule")]
    assert not missing, f"per-entry rows without entry_rule: {missing}"


def test_protective_rows_carry_a_note(manifest: dict) -> None:
    """canonical-company and never-port rows exist to STOP someone — the note
    is the one-line why that stops them."""
    missing = [r["path"] for r in manifest["rows"]
               if r["disposition"] in ("canonical-company", "never-port")
               and not r.get("note")]
    assert not missing, f"protective rows without a note: {missing}"


def test_critical_rows_are_pinned(manifest: dict) -> None:
    """Regression pins for the rows whose loss caused (or nearly caused) real
    damage: the back-flow stream, the append-only audit log, the per-entry
    ontology files, and the port-frozen adapter."""
    by_path = {r["path"]: r["disposition"] for r in manifest["rows"]}
    expected = {
        "drydocs/publishing/**": "canonical-company",
        "config/gate-prompts/**": "canonical-company",
        "drydocs/adapters/oracle_adapter.py": "canonical-company",
        "config/gate-log.md": "union-append",
        "drydocs/ontology/relationship_vocabulary.yaml": "per-entry",
        "config/taxonomy-ontology-map.yaml": "per-entry",
        "drydocs/data/**": "never-port",
    }
    for path, disposition in expected.items():
        assert by_path.get(path) == disposition, (
            f"{path}: expected {disposition}, manifest says {by_path.get(path)}"
        )


def test_overrides_precede_their_broader_glob(manifest: dict) -> None:
    """First match wins — a specific override (config/gate-log.md) must appear
    BEFORE the broad glob that would otherwise swallow it (config/**)."""
    paths = [r["path"] for r in manifest["rows"]]

    def idx(p: str) -> int:
        return paths.index(p)

    broad = "config/**"
    for override in ("config/gate-log.md", "config/gate-prompts/**",
                     "config/review-labels.yaml", "config/taxonomy-ontology-map.yaml"):
        assert idx(override) < idx(broad), (
            f"{override} must precede {broad} (first match wins)"
        )
    # same shape for the drydocs/ tree: the frozen adapter + review modules are
    # file-specific rows, and no broad drydocs/** row may exist at all
    assert "drydocs/**" not in paths, "no blanket drydocs/** row — keep dispositions explicit"
