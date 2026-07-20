"""O13 mapping-endpoint guards (plan M2) — offline, framework-free.

Covers: the steward role gate (user < steward < admin), grid/options reads
over a real mapping-store build, changeset artifact generation (fail-closed
validation, REQUIRED rationale, template column order, zero server writes).
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from drydocs_api.handlers import Forbidden
from drydocs_api.mappings import (
    DOMAINS,
    ChangesetValidationError,
    MappingStore,
    UnknownDomainError,
    draft_changeset,
    list_domains,
    mapping_grid,
    mapping_options,
)
from drydocs_api.personas import PERSONAS
from drydocs_api.sessions import InMemorySessionStore


@pytest.fixture(scope="module")
def store(tmp_path_factory) -> MappingStore:
    """One real materialization for the module — built from the committed
    repo sources, exactly what the endpoint serves."""
    db = tmp_path_factory.mktemp("mapping") / "mapping.db"
    return MappingStore(db)


@pytest.fixture()
def sessions() -> InMemorySessionStore:
    return InMemorySessionStore()


def _token(sessions: InMemorySessionStore, persona: str) -> str:
    return sessions.issue(persona).token


def test_steward_persona_exists():
    assert PERSONAS["kchen2190"].role == "steward"


def test_user_role_is_refused(sessions, store):
    token = _token(sessions, "jdoe4821")
    with pytest.raises(Forbidden):
        list_domains(token, sessions)
    with pytest.raises(Forbidden):
        mapping_grid("ontology-map", token, sessions, store)
    with pytest.raises(Forbidden):
        draft_changeset(
            [{"folder_id": "F", "job_id": "J", "seal_id": "S", "rationale": "r"}],
            token, sessions, store,
        )


@pytest.mark.parametrize("persona", ["kchen2190", "asmith7734"])
def test_steward_and_admin_see_domains(sessions, persona):
    out = list_domains(_token(sessions, persona), sessions)
    ids = [d["id"] for d in out["domains"]]
    assert ids == [d["id"] for d in DOMAINS]
    assert "ontology-map" in ids and "job-application" in ids


def test_grid_serves_the_quintuple(sessions, store):
    token = _token(sessions, "kchen2190")
    out = mapping_grid("ontology-map", token, sessions, store)
    assert out["keys"][:5] == [
        "id", "source_label", "relationship_type", "role", "target_label",
    ]
    by_id = {r["id"]: r for r in out["rows"]}
    seed = by_id["job-contains"]
    assert (seed["source_label"], seed["relationship_type"], seed["target_label"]) == (
        "ControlMFolder", "CONTAINS_JOB", "ControlMJob"
    )


def test_stale_store_rebuilds_on_read(sessions, tmp_path):
    """O14: a materialization whose meta hashes no longer match the committed
    sources is rebuilt transparently on the next read — a stale grid is never
    served (the pre-O14 behavior rebuilt only when the FILE was absent)."""
    import sqlite3

    from drydocs_core.mapping_store import source_hashes

    own = MappingStore(tmp_path / "mapping.db")
    token = _token(sessions, "kchen2190")
    mapping_grid("ontology-map", token, sessions, own)  # first read builds

    rw = sqlite3.connect(str(tmp_path / "mapping.db"))  # simulate source drift
    rw.execute(
        "UPDATE meta SET value = 'drifted' WHERE key = 'source:taxonomy-ontology-map.yaml'"
    )
    rw.commit()
    rw.close()

    out = mapping_grid("ontology-map", token, sessions, own)
    assert any(r["id"] == "job-contains" for r in out["rows"])  # served, not stale
    ro = sqlite3.connect(str(tmp_path / "mapping.db"))
    stored = dict(ro.execute("SELECT key, value FROM meta"))
    ro.close()
    assert stored == source_hashes()  # the rebuild restored current hashes


def test_unavailable_and_unknown_domains_404(sessions, store):
    token = _token(sessions, "kchen2190")
    with pytest.raises(UnknownDomainError):
        mapping_grid("fid-seal", token, sessions, store)  # registered but not available
    with pytest.raises(UnknownDomainError):
        mapping_grid("nope", token, sessions, store)


def test_options_feed_the_dropdowns(sessions, store):
    token = _token(sessions, "kchen2190")
    out = mapping_options(token, sessions, store)
    labels = {r["label"] for r in out["labels"]}
    assert {"ControlMJob", "ControlMFolder", "BusinessApplication"} <= labels
    rels = {(r["neo4j_label"], r["role"]) for r in out["relationships"]}
    assert ("WAS_ASSOCIATED_WITH", "seal_app_ref") in rels


def test_changeset_artifact_shape(sessions, store):
    token = _token(sessions, "kchen2190")
    out = draft_changeset(
        [
            {"folder_id": "F0001", "job_id": "J0002", "seal_id": "APP-9876",
             "rationale": "support team confirmed owner"},
            {"folder_id": "F0001", "job_id": "J0003", "seal_id": "APP-9876",
             "rationale": "same series as J0002", "create_target_if_missing": True},
        ],
        token, sessions, store,
    )
    rows = list(csv.DictReader(io.StringIO(out["csv"])))
    assert len(rows) == 2
    assert rows[0]["source_label"] == "ControlMJob"
    assert rows[0]["source_key"] == "folder_id=F0001;job_id=J0002"
    assert rows[0]["rel_props"] == "role=seal_app_ref"
    assert rows[0]["authored_by"] == "kchen2190"  # session persona, never client-supplied
    assert rows[1]["create_target_if_missing"] == "true"
    assert "pending-load" in out["manifest_snippet"]
    assert "replaces_with" in out["manifest_snippet"]
    # The artifact parses under the SAME validation chain the loader uses
    # once registered — assert the header matches the committed template.
    template = Path(__file__).resolve().parents[2] / "config" / "manual-loads" / (
        "TEMPLATE-node-mapping.csv"
    )
    assert out["csv"].splitlines()[0] == template.read_text(encoding="utf-8").splitlines()[0]


@pytest.mark.parametrize("bad,reason", [
    ([], "empty"),
    ([{"folder_id": "F", "job_id": "J", "seal_id": "S", "rationale": "  "}], "rationale"),
    ([{"folder_id": "", "job_id": "J", "seal_id": "S", "rationale": "r"}], "required"),
])
def test_changeset_fails_closed(sessions, store, bad, reason):
    token = _token(sessions, "kchen2190")
    with pytest.raises(ChangesetValidationError):
        draft_changeset(bad, token, sessions, store)
