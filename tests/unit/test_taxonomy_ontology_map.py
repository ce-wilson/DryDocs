"""Guard for config/taxonomy-ontology-map.yaml — "THE central artifact of the
configuration layer", previously the only ledger with zero test coverage
(docs/reviews/tech-debt-taxonomy-ontology-map.md F1/F3, 2026-07-09).

Mirrors the test_backlog discipline: the summary block is a COMPUTED view that
must match the entries exactly; every vocab_id must resolve into
relationship_vocabulary.yaml; labels must agree between the two files so the
map and the vocabulary cannot silently diverge (the dual-source-of-truth debt).
Pure YAML checks — no Neo4j.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MAP_FILE = REPO / "config" / "taxonomy-ontology-map.yaml"
VOCAB_FILE = REPO / "drydocs" / "ontology" / "relationship_vocabulary.yaml"

VALID_STATUSES = {"proposed", "confirmed", "applied", "rejected"}


@pytest.fixture(scope="module")
def map_doc() -> dict:
    return yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def vocab_ids() -> dict:
    doc = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    return {rel["id"]: rel for rel in doc["local_relationships"]}


def test_schema_id(map_doc: dict) -> None:
    assert map_doc["schema"] == "drydocs.taxonomy-ontology-map.v1"


def test_mapping_ids_unique_and_present(map_doc: dict) -> None:
    ids = [m["id"] for m in map_doc["mappings"]]
    assert all(ids), "every mapping needs an id"
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    assert not dupes, f"duplicate mapping ids: {dupes}"


def test_status_lifecycle_enum(map_doc: dict) -> None:
    bad = [(m["id"], m.get("status")) for m in map_doc["mappings"]
           if m.get("status") not in VALID_STATUSES]
    assert not bad, f"invalid lifecycle status (proposed|confirmed|applied|rejected): {bad}"


def test_confirmed_and_applied_carry_sme_fields(map_doc: dict) -> None:
    """An SME decision is only auditable with who + when; applied additionally
    records when the loader first wrote it."""
    failures = []
    for m in map_doc["mappings"]:
        if m["status"] in ("confirmed", "applied"):
            if not m.get("confirmed_by") or not m.get("confirmed_on"):
                failures.append(f"{m['id']}: {m['status']} without confirmed_by/confirmed_on")
        if m["status"] == "applied" and not m.get("applied_on"):
            failures.append(f"{m['id']}: applied without applied_on")
    assert not failures, "\n".join(failures)


def test_summary_is_a_computed_view(map_doc: dict) -> None:
    """The exact failure that hit backlog.yaml in the 2026-07-09 merges: a
    hand-maintained roll-up drifting from the items. Recompute and compare."""
    actual = Counter(m["status"] for m in map_doc["mappings"])
    summary = map_doc["summary"]
    for status in VALID_STATUSES:
        assert summary.get(status, 0) == actual.get(status, 0), (
            f"summary says {status}={summary.get(status, 0)} but entries have "
            f"{actual.get(status, 0)} — recount the summary block"
        )


def test_vocab_id_resolves_into_the_vocabulary(map_doc: dict, vocab_ids: dict) -> None:
    """F3: the map must reference the vocabulary by id, and the id must exist —
    no more free-text '(active)' parentheticals that rot on status flips."""
    failures = []
    for m in map_doc["mappings"]:
        vid = m.get("vocab_id")
        if vid is None:
            continue
        for one in (vid if isinstance(vid, list) else [vid]):
            if one not in vocab_ids:
                failures.append(f"{m['id']}: vocab_id '{one}' not in relationship_vocabulary.yaml")
    assert not failures, "\n".join(failures)


def test_map_and_vocabulary_agree_on_the_label(map_doc: dict, vocab_ids: dict) -> None:
    """Dual-source-of-truth check: when a mapping points at one vocabulary
    entry and declares a neo4j_label, the two files must name the same label
    (the RUNS_ON reassignment precedent shows labels do get renamed)."""
    failures = []
    for m in map_doc["mappings"]:
        vid = m.get("vocab_id")
        if vid is None or isinstance(vid, list):
            continue
        map_label = (m.get("ontology") or {}).get("neo4j_label")
        vocab_label = vocab_ids[vid].get("neo4j_label")
        if map_label and vocab_label and map_label != vocab_label:
            failures.append(
                f"{m['id']}: map says {map_label}, vocabulary '{vid}' says {vocab_label}"
            )
    assert not failures, "\n".join(failures)


def test_updated_header_is_not_stale(map_doc: dict) -> None:
    """The header sat at 2026-06-20 while entries advanced to 2026-07-09."""
    import datetime as dt

    dates = [m["confirmed_on"] for m in map_doc["mappings"] if m.get("confirmed_on")]
    dates += [m["applied_on"] for m in map_doc["mappings"] if m.get("applied_on")]
    dates = [d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d)) for d in dates]
    updated = map_doc["updated"]
    updated = updated if isinstance(updated, dt.date) else dt.date.fromisoformat(str(updated))
    assert updated >= max(dates), (
        f"updated: {updated} is older than the newest entry date {max(dates)}"
    )


def test_no_duplicate_node_classification_labels() -> None:
    """F4 regression guard: two `- label: Document` entries once coexisted in
    node_classifications; a label must classify exactly once."""
    doc = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    labels = [n["label"] for n in doc["node_classifications"]]
    dupes = [l for l, n in Counter(labels).items() if n > 1]
    assert not dupes, f"duplicate node_classifications labels: {dupes}"
