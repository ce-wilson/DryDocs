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
    OVERRIDE_HEADER,
    ChangesetValidationError,
    MappingStore,
    UnknownDomainError,
    draft_changeset,
    draft_override,
    list_domains,
    mapping_grid,
    mapping_options,
    source_corrections_report,
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
            token,
            sessions,
            store,
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
        "id",
        "source_label",
        "relationship_type",
        "role",
        "target_label",
    ]
    by_id = {r["id"]: r for r in out["rows"]}
    seed = by_id["job-contains"]
    assert (seed["source_label"], seed["relationship_type"], seed["target_label"]) == (
        "ControlMFolder",
        "CONTAINS_JOB",
        "ControlMJob",
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
    rw.execute("UPDATE meta SET value = 'drifted' WHERE key = 'source:taxonomy-ontology-map.yaml'")
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
            {
                "folder_id": "F0001",
                "job_id": "J0002",
                "seal_id": "APP-9876",
                "rationale": "support team confirmed owner",
            },
            {
                "folder_id": "F0001",
                "job_id": "J0003",
                "seal_id": "APP-9876",
                "rationale": "same series as J0002",
                "create_target_if_missing": True,
            },
        ],
        token,
        sessions,
        store,
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
    template = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "manual-loads"
        / ("TEMPLATE-node-mapping.csv")
    )
    assert out["csv"].splitlines()[0] == template.read_text(encoding="utf-8").splitlines()[0]


@pytest.mark.parametrize(
    "bad,reason",
    [
        ([], "empty"),
        ([{"folder_id": "F", "job_id": "J", "seal_id": "S", "rationale": "  "}], "rationale"),
        ([{"folder_id": "", "job_id": "J", "seal_id": "S", "rationale": "r"}], "required"),
    ],
)
def test_changeset_fails_closed(sessions, store, bad, reason):
    token = _token(sessions, "kchen2190")
    with pytest.raises(ChangesetValidationError):
        draft_changeset(bad, token, sessions, store)


# ---------------------------------------------------------------------------
# O24 — SEAL-contact override domain (ui-write-surface gate SME-3, M2 tier).
# Synthetic values only (publish boundary).
# ---------------------------------------------------------------------------


@pytest.fixture()
def override_store(tmp_path, monkeypatch) -> MappingStore:
    """A store whose committed override list is a two-row fixture — the module
    constant is monkeypatched so the WHOLE read chain (is_current -> build)
    resolves to it, exactly how the endpoint would see a committed list."""
    fix = tmp_path / "seal-contact-overrides.csv"
    fix.write_text(
        ",".join(OVERRIDE_HEADER) + "\n"
        "APP-1234,L2 Operate Manager,U111111,U222222,Sam Steward,"
        "person left the team,kchen2190,2026-07-21,active\n"
        "APP-5678,L1 Operate Manager,,U333333,,role unassigned in SEAL,"
        "kchen2190,2026-07-21,active\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("drydocs_core.mapping_store.SEAL_CONTACT_OVERRIDES_PATH", fix)
    return MappingStore(tmp_path / "mapping.db")


def test_override_domain_registered():
    dom = next(d for d in DOMAINS if d["id"] == "seal-contact-override")
    assert dom["available"] and dom["kind"] == "override"
    assert dom["source"] == "config/overrides/seal-contact-overrides.csv"


def test_override_grid_carries_origin_flag(sessions, override_store):
    """Every grid row is origin-flagged; the SEAL source value and the user
    override arrive as adjacent rows (source first) — never merged, never
    silently replaced."""
    token = _token(sessions, "kchen2190")
    out = mapping_grid("seal-contact-override", token, sessions, override_store)
    assert "origin" in out["keys"]
    flags = [(r["app_seal_id"], r["origin"], r["holder_sid"]) for r in out["rows"]]
    assert flags == [
        ("APP-1234", "source", "U111111"),
        ("APP-1234", "override", "U222222"),
        ("APP-5678", "override", "U333333"),
    ]
    assert all(r["origin"] in ("source", "override") for r in out["rows"])


def test_draft_override_returns_full_updated_file(sessions, override_store):
    """The artifact is the COMPLETE updated committed file (existing rows +
    drafts) — commit-by-replace; authored_by is server-stamped; the server
    wrote nothing."""
    token = _token(sessions, "asmith7734")
    out = draft_override(
        [
            {
                "app_seal_id": "APP-9012",
                "role_name": "l1 ops manager",
                "seal_holder_sid": "U444444",
                "override_holder_sid": "U555555",
                "override_holder_name": "Ada Admin",
                "rationale": "SEAL points at the retired rota owner",
            }
        ],
        token,
        sessions,
        override_store,
    )
    rows = list(csv.DictReader(io.StringIO(out["csv"])))
    assert out["filename"] == "seal-contact-overrides.csv"
    assert out["entries"] == 1 and out["total_rows"] == 3
    assert [r["app_seal_id"] for r in rows] == ["APP-1234", "APP-5678", "APP-9012"]
    new = rows[-1]
    assert new["role_name"] == "L1 Operate Manager"  # canonicalized
    assert new["authored_by"] == "asmith7734"  # session persona, never client-supplied
    assert new["status"] == "active"
    # committed rows survive byte-faithfully through the store round-trip
    assert rows[0]["override_holder_name"] == "Sam Steward"
    assert "wrote NOTHING" in out["note"]


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [
            {
                "app_seal_id": "A",
                "role_name": "Head Chef",
                "override_holder_sid": "U2",
                "rationale": "r",
            }
        ],  # unknown role
        [
            {
                "app_seal_id": "A",
                "role_name": "L2 Operate Manager",
                "override_holder_sid": "U2",
                "rationale": " ",
            }
        ],  # rationale required
        [
            {
                "app_seal_id": "A",
                "role_name": "L2 Operate Manager",
                "seal_holder_sid": "U2",
                "override_holder_sid": "U2",
                "rationale": "r",
            }
        ],  # not a correction
    ],
)
def test_draft_override_fails_closed(sessions, override_store, bad):
    token = _token(sessions, "kchen2190")
    with pytest.raises(ChangesetValidationError):
        draft_override(bad, token, sessions, override_store)


def test_override_endpoints_refuse_user_role(sessions, override_store):
    token = _token(sessions, "jdoe4821")
    with pytest.raises(Forbidden):
        draft_override(
            [
                {
                    "app_seal_id": "A",
                    "role_name": "L2 Operate Manager",
                    "override_holder_sid": "U2",
                    "rationale": "r",
                }
            ],
            token,
            sessions,
            override_store,
        )
    with pytest.raises(Forbidden):
        source_corrections_report(token, sessions, override_store)


def test_source_corrections_report_content(sessions, override_store):
    """The report is the AO-facing artifact: SEAL current value, corrected
    value, author and rationale per outstanding override, with the AO-privilege
    framing spelled out."""
    token = _token(sessions, "kchen2190")
    out = source_corrections_report(token, sessions, override_store)
    assert out["count"] == 2
    md = out["markdown"]
    assert "AO privilege" in md and "does NOT write SEAL" in md
    assert "| APP-1234 | L2 Operate Manager | U111111 | U222222 (Sam Steward) |" in md
    assert "person left the team" in md
    assert "(nobody assigned)" in md  # the empty-SEAL-value row is explicit
    assert out["filename"].startswith("seal-contact-source-corrections-")
