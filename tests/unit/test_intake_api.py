"""O46 intake guards — offline, framework-free, NO Neo4j.

Covers: the creation stamps (origin: sme-intake + classification: Internal,
no unlabeled default), context-type validation against the O45 vocabulary,
evidence landing (data-root staging, sha256 identity, relative keys only,
whole-file rule), the Copilot pair link, re-upload re-queue semantics,
parse-preview warnings-never-rejections, thread-identity detection + the
delta review payload + the SME's adds-value/no-new-value decision, the
status machine with its per-role legal-transitions map, and the absolute
load boundary (admin-accepted parks; 'loaded' is unreachable here).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_api.handlers import Forbidden
from drydocs_api.intake import (
    ALLOWED_EXTENSIONS,
    CLASSIFICATION,
    ORIGIN,
    TRANSITIONS,
    IllegalTransitionError,
    IntakeStore,
    IntakeValidationError,
    UnknownIntakeError,
    add_evidence,
    create_intake,
    get_intake,
    list_intakes,
    normalized_subject,
    thread_decision,
    transition,
)
from drydocs_api.sessions import InMemorySessionStore

REPO = Path(__file__).resolve().parent.parent.parent

# synthetic evidence only — the fixture rule (plan Demo script): reserved-block
# SEAL ids (70001-70099) + bundled sample names, never production values.
FIRST_MAIL = b"""Subject: PARAD0060_PEX_EXPLOANRQTDTL_AWS_RFND failed
From: sme.one@example.test
Date: Mon, 3 Aug 2026 07:12:00 -0500
Message-ID: <thread-70002-001@example.test>

The 6:40 run of PARAD0060_PEX_EXPLOANRQTDTL_AWS_RFND ended NOTOK.
Folder PRARAG-HLDM-70002-PEX-RFND-DLY, SEAL 70002.
Downstream refund detail feed is holding.
Log shows ORA-01555 on the extract step.
"""

REPLY_MAIL = b"""Subject: RE: PARAD0060_PEX_EXPLOANRQTDTL_AWS_RFND failed
From: sme.two@example.test
Date: Mon, 3 Aug 2026 09:30:00 -0500
Message-ID: <thread-70002-002@example.test>
In-Reply-To: <thread-70002-001@example.test>

Rerun completed clean at 09:10 after the undo retention bump.
No new value beyond that.

-----Original Message-----
The 6:40 run of PARAD0060_PEX_EXPLOANRQTDTL_AWS_RFND ended NOTOK.
Folder PRARAG-HLDM-70002-PEX-RFND-DLY, SEAL 70002.
Downstream refund detail feed is holding.
Log shows ORA-01555 on the extract step.
"""


@pytest.fixture()
def store(tmp_path) -> IntakeStore:
    return IntakeStore(tmp_path / "context-intake")


@pytest.fixture()
def sessions() -> InMemorySessionStore:
    return InMemorySessionStore()


def _token(sessions, persona="mouse"):
    return sessions.issue(persona).token


def _intake(sessions, store, token=None, **kw):
    token = token or _token(sessions)
    kw.setdefault("context_type", "job-failure")
    kw.setdefault("area", {"seal": "70002"})
    kw.setdefault("note", "")
    return token, create_intake(kw["context_type"], kw["area"], kw["note"], token, sessions, store)


# ── creation stamps + vocabulary ─────────────────────────────────────────────


def test_creation_stamps_origin_and_classification(sessions, store):
    _, rec = _intake(sessions, store)
    assert rec["origin"] == ORIGIN == "sme-intake"
    assert rec["classification"] == CLASSIFICATION == "Internal"
    assert rec["status"] == "draft"
    assert rec["area"] == {"seal": "70002"}


def test_unknown_context_type_is_refused(sessions, store):
    token = _token(sessions)
    with pytest.raises(IntakeValidationError):
        create_intake("not-a-real-type", {}, "", token, sessions, store)


def test_other_requires_the_growth_note(sessions, store):
    token = _token(sessions)
    with pytest.raises(IntakeValidationError):
        create_intake("other", {}, "", token, sessions, store)
    rec = create_intake("other", {}, "capacity breach, not on the list", token, sessions, store)
    assert rec["context_type"] == "other"


def test_context_vocabulary_comes_from_the_o45_file(sessions, store):
    """The four seeds resolve; the handler reads the taxonomy file, not a
    hardcoded list."""
    token = _token(sessions)
    for ct in ("job-failure", "missed-data-load", "missed-file", "data-issue"):
        rec = create_intake(ct, {}, "", token, sessions, store)
        assert rec["context_type"] == ct


# ── evidence landing ─────────────────────────────────────────────────────────


def test_evidence_lands_whole_under_the_root_with_digest(sessions, store):
    token, rec = _intake(sessions, store)
    out = add_evidence(rec["intake_id"], "failure.msg", FIRST_MAIL, token, sessions, store)
    (ev,) = out["evidence"]
    assert ev["sha256"] and ev["size"] == len(FIRST_MAIL)
    # relative key only — no filesystem assumption above the seam
    assert ev["rel_key"] == f"{rec['intake_id']}/failure.msg"
    assert not Path(ev["rel_key"]).is_absolute()
    landed = store.evidence_path(ev["rel_key"])
    assert landed.read_bytes() == FIRST_MAIL  # whole, byte-for-byte
    assert store.root.name == "context-intake"


def test_disallowed_kind_is_refused_and_repo_tree_untouched(sessions, store):
    token, rec = _intake(sessions, store)
    with pytest.raises(IntakeValidationError):
        add_evidence(rec["intake_id"], "shot.png", b"\x89PNG", token, sessions, store)
    assert ALLOWED_EXTENSIONS == (".msg", ".json", ".txt")


def test_copilot_pair_links_by_basename(sessions, store):
    token, rec = _intake(sessions, store)
    add_evidence(rec["intake_id"], "failure.msg", FIRST_MAIL, token, sessions, store)
    out = add_evidence(
        rec["intake_id"], "failure.json", b'{"summary": "copilot"}', token, sessions, store
    )
    pairs = {e["filename"]: e["pair_key"] for e in out["evidence"]}
    assert pairs["failure.msg"] == pairs["failure.json"] == "failure"


def test_reupload_same_bytes_is_idempotent(sessions, store):
    token, rec = _intake(sessions, store)
    add_evidence(rec["intake_id"], "a.txt", b"line one\n", token, sessions, store)
    out = add_evidence(rec["intake_id"], "a.txt", b"line one\n", token, sessions, store)
    assert len(out["evidence"]) == 1


def test_reupload_changed_bytes_requeues_review(sessions, store):
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    add_evidence(iid, "a.txt", b"first version\n", token, sessions, store)
    transition(iid, "ontology-reviewed", "", token, sessions, store)
    out = add_evidence(iid, "a.txt", b"second version\n", token, sessions, store)
    # never silently replaced: old row superseded, review back to draft
    assert out["status"] == "draft"
    assert [e["filename"] for e in out["evidence"]] == ["a.txt"]
    all_rows = store.evidence_rows(iid, include_superseded=True)
    assert len(all_rows) == 2 and sum(r["superseded"] for r in all_rows) == 1


def test_upload_refused_once_accepted(sessions, store):
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    add_evidence(iid, "a.txt", b"x\n", token, sessions, store)
    for to in ("ontology-reviewed", "correlated", "sme-confirmed"):
        transition(iid, to, "", token, sessions, store)
    admin = _token(sessions, "morpheus")
    transition(iid, "admin-accepted", "", admin, sessions, store)
    with pytest.raises(IllegalTransitionError):
        add_evidence(iid, "late.txt", b"y\n", token, sessions, store)


# ── parse preview: display-only, warning never rejection ─────────────────────


def test_msg_preview_extracts_headers_best_effort(sessions, store):
    token, rec = _intake(sessions, store)
    out = add_evidence(rec["intake_id"], "m.msg", FIRST_MAIL, token, sessions, store)
    p = out["evidence"][0]["preview"]
    assert p["subject"].startswith("PARAD0060_PEX")
    assert p["from"] == "sme.one@example.test"


def test_unparseable_msg_lands_with_a_warning(sessions, store):
    token, rec = _intake(sessions, store)
    blob = bytes(range(256)) * 4  # no recoverable headers
    out = add_evidence(rec["intake_id"], "opaque.msg", blob, token, sessions, store)
    (ev,) = out["evidence"]
    assert ev["preview"]["warnings"]  # warned…
    assert store.evidence_path(ev["rel_key"]).read_bytes() == blob  # …but landed


def test_json_preview_lists_keys(sessions, store):
    token, rec = _intake(sessions, store)
    out = add_evidence(
        rec["intake_id"], "c.json", b'{"prompt": 1, "answer": 2}', token, sessions, store
    )
    assert out["evidence"][0]["preview"]["keys"] == ["answer", "prompt"]


def test_invalid_json_is_a_warning_not_a_rejection(sessions, store):
    token, rec = _intake(sessions, store)
    out = add_evidence(rec["intake_id"], "bad.json", b"{not json", token, sessions, store)
    assert out["evidence"][0]["preview"]["warnings"]


# ── thread reuse → ingest the diff ───────────────────────────────────────────


def test_normalized_subject_strips_reply_prefixes():
    assert normalized_subject("RE: RE: FW: Job failed") == normalized_subject("Job  failed")
    assert normalized_subject("Re[2]: Job failed") == "job failed"


def _thread_pair(sessions, store):
    token_a, first = _intake(sessions, store)
    add_evidence(first["intake_id"], "first.msg", FIRST_MAIL, token_a, sessions, store)
    token_b = _token(sessions, "trinity")
    second = create_intake("job-failure", {}, "", token_b, sessions, store)
    out = add_evidence(second["intake_id"], "reply.msg", REPLY_MAIL, token_b, sessions, store)
    return first, out, token_b


def test_thread_continuation_is_flagged_with_linkage_and_delta(sessions, store):
    first, out, _ = _thread_pair(sessions, store)
    assert out["thread_flagged"] is True
    assert out["thread_of"] == [first["intake_id"]]
    # the review payload is the DELTA — the new content above the quoted tail
    assert "undo retention bump" in out["review_payload"]
    assert "ORA-01555" not in out["review_payload"]
    # the original file still landed WHOLE (evidence is never edited)
    (ev,) = out["evidence"]
    assert store.evidence_path(ev["rel_key"]).read_bytes() == REPLY_MAIL


def test_flag_blocks_progress_until_the_sme_decides(sessions, store):
    _, out, token_b = _thread_pair(sessions, store)
    with pytest.raises(IllegalTransitionError):
        transition(out["intake_id"], "ontology-reviewed", "", token_b, sessions, store)
    lt = out["legal_transitions"]
    assert lt["thread_decision_required"] is True
    assert lt["thread_decisions"] == ["adds-value", "no-new-value"]


def test_adds_value_proceeds(sessions, store):
    _, out, token_b = _thread_pair(sessions, store)
    rec = thread_decision(out["intake_id"], "adds-value", token_b, sessions, store)
    assert rec["thread_decision"] == "adds-value" and rec["status"] == "draft"
    rec = transition(out["intake_id"], "ontology-reviewed", "", token_b, sessions, store)
    assert rec["status"] == "ontology-reviewed"


def test_no_new_value_stops_but_the_record_survives(sessions, store):
    first, out, token_b = _thread_pair(sessions, store)
    rec = thread_decision(out["intake_id"], "no-new-value", token_b, sessions, store)
    assert rec["status"] == "no-new-value"
    lt = rec["legal_transitions"]
    assert lt["terminal"] is True and lt["transitions"] == []
    # the record exists with linkage + decision — a third bounce can see it
    assert rec["thread_of"] == [first["intake_id"]]
    assert rec["thread_decision"] == "no-new-value"


def test_subject_match_alone_flags_without_content_overlap(sessions, store):
    token_a, first = _intake(sessions, store)
    add_evidence(
        first["intake_id"],
        "a.txt",
        b"Subject: nightly load missed\nbody A\n" * 2,
        token_a,
        sessions,
        store,
    )
    second = create_intake("missed-data-load", {}, "", token_a, sessions, store)
    out = add_evidence(
        second["intake_id"],
        "b.txt",
        b"Subject: RE: nightly load missed\ncompletely different body\n",
        token_a,
        sessions,
        store,
    )
    assert out["thread_flagged"] is True


def test_unrelated_upload_is_not_flagged(sessions, store):
    token_a, first = _intake(sessions, store)
    add_evidence(first["intake_id"], "a.msg", FIRST_MAIL, token_a, sessions, store)
    second = create_intake("data-issue", {}, "", token_a, sessions, store)
    out = add_evidence(
        second["intake_id"],
        "b.txt",
        b"Subject: reconciliation break in catalog feed\nrow counts differ\n",
        token_a,
        sessions,
        store,
    )
    assert out["thread_flagged"] is False


# ── the status machine + legal-transitions map ───────────────────────────────


def test_illegal_jump_is_refused(sessions, store):
    token, rec = _intake(sessions, store)
    with pytest.raises(IllegalTransitionError):
        transition(rec["intake_id"], "admin-accepted", "", token, sessions, store)


def test_accept_and_return_are_admin_only(sessions, store):
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    for to in ("ontology-reviewed", "correlated", "sme-confirmed"):
        transition(iid, to, "", token, sessions, store)
    with pytest.raises(Forbidden):
        transition(iid, "admin-accepted", "", token, sessions, store)
    admin = _token(sessions, "morpheus")
    rec = transition(iid, "admin-accepted", "", admin, sessions, store)
    assert rec["status"] == "admin-accepted"


def test_return_requires_a_note(sessions, store):
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    for to in ("ontology-reviewed", "correlated", "sme-confirmed"):
        transition(iid, to, "", token, sessions, store)
    admin = _token(sessions, "morpheus")
    with pytest.raises(IntakeValidationError):
        transition(iid, "admin-returned", "", admin, sessions, store)
    rec = transition(iid, "admin-returned", "bindings look wrong", admin, sessions, store)
    assert rec["status"] == "admin-returned"


def test_legal_transitions_map_is_role_scoped(sessions, store):
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    for to in ("ontology-reviewed", "correlated", "sme-confirmed"):
        transition(iid, to, "", token, sessions, store)
    sme_view = get_intake(iid, token, sessions, store)["legal_transitions"]
    assert sme_view["transitions"] == []  # accept/return are not the SME's buttons
    admin = _token(sessions, "morpheus")
    admin_view = get_intake(iid, admin, sessions, store)["legal_transitions"]
    assert {t["to"] for t in admin_view["transitions"]} == {"admin-accepted", "admin-returned"}


def test_admin_accepted_parks_waiting_on_gate(sessions, store):
    """The load boundary is absolute: no transition reaches 'loaded' from this
    API — admin acceptance parks the record and says why."""
    token, rec = _intake(sessions, store)
    iid = rec["intake_id"]
    for to in ("ontology-reviewed", "correlated", "sme-confirmed"):
        transition(iid, to, "", token, sessions, store)
    admin = _token(sessions, "morpheus")
    rec = transition(iid, "admin-accepted", "", admin, sessions, store)
    lt = rec["legal_transitions"]
    assert lt["waiting_on_gate"] is True and lt["transitions"] == []
    with pytest.raises(IllegalTransitionError):
        transition(iid, "loaded", "", admin, sessions, store)
    assert all("loaded" not in {t[0] for t in outs} for outs in TRANSITIONS.values())


# ── visibility + audit ───────────────────────────────────────────────────────


def test_users_see_own_intakes_only(sessions, store):
    token_a, rec = _intake(sessions, store)
    other_user = _token(sessions, "mouse")  # same persona, new session — still owner
    assert (
        get_intake(rec["intake_id"], other_user, sessions, store)["intake_id"] == rec["intake_id"]
    )
    steward = _token(sessions, "trinity")
    assert len(list_intakes(steward, sessions, store)["intakes"]) == 1  # queue sees all


def test_events_record_the_audit_trail(sessions, store):
    token, rec = _intake(sessions, store)
    add_evidence(rec["intake_id"], "a.txt", b"x\n", token, sessions, store)
    actions = [
        r["action"]
        for r in store.conn.execute(
            "SELECT action FROM event WHERE intake_id = ? ORDER BY rowid", (rec["intake_id"],)
        )
    ]
    assert actions[0] == "created" and "evidence-added" in actions


def test_unknown_intake_raises(sessions, store):
    token = _token(sessions)
    with pytest.raises(UnknownIntakeError):
        get_intake("nope", token, sessions, store)


# ── the boundaries, pinned in source ─────────────────────────────────────────


def test_no_graph_writes_no_neo4j_import():
    src = (REPO / "drydocs_api" / "intake.py").read_text(encoding="utf-8")
    assert "import neo4j" not in src and "GraphDatabase" not in src


def test_records_reference_the_data_root_seam():
    """The store root defaults to DRYDOCS_DATA_ROOT/context-intake (the one
    configured base path) — never a repo-tree path."""
    from drydocs_api.intake import default_intake_root
    from drydocs_core.data_root import context_intake_dir

    assert default_intake_root() == context_intake_dir()
    assert not str(default_intake_root()).startswith(str(REPO))
