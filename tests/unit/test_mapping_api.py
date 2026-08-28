"""O13 mapping-endpoint guards (plan M2) — offline, framework-free.

Covers: the steward role gate (user < steward < admin), grid/options reads
over a real mapping-store build, changeset artifact generation (fail-closed
validation, REQUIRED rationale, template column order, zero server writes).
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import pytest

from drydocs_api.handlers import Forbidden
from drydocs_api.mappings import (
    APP_CODE_HEADER,
    DOMAINS,
    K2_SHAPE,
    OVERRIDE_HEADER,
    ChangesetValidationError,
    MappingStore,
    UnknownDomainError,
    app_code_migration_report,
    draft_app_code_mapping,
    draft_changeset,
    draft_override,
    list_domains,
    mapping_grid,
    mapping_options,
    pending_source_correction_report,
    promote_draft,
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
            [{"app_code": "PRA", "app_id": "S", "rationale": "r"}],
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
    assert ("BELONGS_TO_APPLICATION", "seal_app_ref") in rels
    # K8: the job-grain edge deprecated with the folder flip — active options
    # no longer offer it.
    assert ("WAS_ASSOCIATED_WITH", "seal_app_ref") not in rels


def test_changeset_artifact_shape(sessions, store):
    """K9: the changeset artifact carries the K7 RULED edge shape, keyed by
    app_code (§B1 — job identity retired for authoring at §A1)."""
    token = _token(sessions, "kchen2190")
    out = draft_changeset(
        [
            {
                "app_code": "PRA",
                "app_id": "APP-9876",
                "rationale": "support team confirmed owner",
            },
            {
                "app_code": "PRB",
                "app_id": "APP-9876",
                "rationale": "same platform team",
                "create_target_if_missing": True,
            },
        ],
        token,
        sessions,
        store,
    )
    rows = list(csv.DictReader(io.StringIO(out["csv"])))
    assert len(rows) == 2
    assert rows[0]["source_label"] == "ControlMFolder"
    assert rows[0]["source_key"] == "app_code=PRA"
    assert rows[0]["relationship"] == "BELONGS_TO_APPLICATION"
    assert rows[0]["rel_props"] == "role=seal_app_ref"
    assert rows[0]["target_label"] == "Port"
    assert rows[0]["target_key"] == "app_id=APP-9876"
    assert rows[0]["authored_by"] == "kchen2190"  # session persona, never client-supplied
    assert rows[1]["create_target_if_missing"] == "true"
    assert "pending-load" in out["manifest_snippet"]
    assert "replaces_with" in out["manifest_snippet"]
    assert "K8" in out["note"]  # honest: the folder-grain loader is the K8 build
    # The artifact's header matches the committed (rekeyed) template.
    template = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "manual-loads"
        / ("TEMPLATE-node-mapping.csv")
    )
    assert out["csv"].splitlines()[0] == template.read_text(encoding="utf-8").splitlines()[0]


def test_k2_shape_is_the_ruled_edge():
    """The constant follows gate seal-app-ref-edge-reshape §A1/§C1/§D1."""
    assert K2_SHAPE == {
        "source_label": "ControlMFolder",
        "relationship": "BELONGS_TO_APPLICATION",
        "role": "seal_app_ref",
        "target_label": "Port",
    }


@pytest.mark.parametrize(
    "bad,reason",
    [
        ([], "empty"),
        ([{"app_code": "PRA", "app_id": "S", "rationale": "  "}], "rationale"),
        ([{"app_code": "", "app_id": "S", "rationale": "r"}], "app_code required"),
        # the retired job-grain entry shape is refused, not silently remapped
        ([{"folder_id": "F", "job_id": "J", "app_id": "S", "rationale": "r"}], "job grain"),
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
    # The GRID emits app_id (S3 / gate §E1); the committed FILE below keeps
    # app_seal_id. That split is the contract, not an oversight.
    flags = [(r["app_id"], r["origin"], r["holder_sid"]) for r in out["rows"]]
    assert flags == [
        ("APP-1234", "source", "U111111"),
        ("APP-1234", "override", "U222222"),
        ("APP-5678", "override", "U333333"),
    ]
    assert all(r["origin"] in ("source", "override") for r in out["rows"])


_A_DRAFT = {
    "app_id": "APP-9012",
    "role_name": "l1 ops manager",
    "seal_holder_sid": "U444444",
    "override_holder_sid": "U555555",
    "override_holder_name": "Ada Admin",
    "rationale": "SEAL points at the retired rota owner",
}


def test_draft_override_writes_a_row_not_a_file(sessions, override_store):
    """S4: drafting persists ROWS to var/mapping.db and returns a receipt.

    It used to return the complete updated file (commit-by-replace), which one
    editor could hold in a browser download while a second editor built their
    own copy from the same base — whichever was committed last erased the
    other. The receipt names the draft instead; the diff comes from promotion.
    """
    token = _token(sessions, "asmith7734")
    out = draft_override([_A_DRAFT], token, sessions, override_store)

    assert "csv" not in out, "drafting must no longer hand back a whole replacement file"
    assert out["domain"] == "seal-contact-override"
    assert out["entries"] == 1 and out["pending"] == 1
    assert out["committed_rows"] == 2
    assert out["draft_id"].startswith("asmith7734-")  # readable in v_open_drafts

    stored = override_store.draft_payloads(out["draft_id"])
    assert len(stored) == 1
    row = stored[0]
    # The stored row is already in COMMITTED-FILE shape: app_seal_id (not the
    # wire's app_id), canonicalized role, server-stamped author.
    assert row["app_seal_id"] == "APP-9012"
    assert row["role_name"] == "L1 Operate Manager"
    assert row["authored_by"] == "asmith7734"  # session persona, never client-supplied
    assert row["status"] == "active"
    assert "NO committed file was written" in out["note"]


def test_concurrent_drafts_from_two_sessions_both_survive(sessions, override_store):
    """The property commit-by-replace could not offer.

    Two stewards drafting at the same time get two independent drafts; neither
    overwrites the other, and each promotes to its own diff.
    """
    alice = _token(sessions, "kchen2190")
    bob = _token(sessions, "asmith7734")

    a = draft_override(
        [{**_A_DRAFT, "override_holder_sid": "U555555"}], alice, sessions, override_store
    )
    b = draft_override(
        [{**_A_DRAFT, "app_id": "APP-3333", "override_holder_sid": "U666666"}],
        bob,
        sessions,
        override_store,
    )
    assert a["draft_id"] != b["draft_id"]

    pending = {d["draft_id"]: d for d in override_store.open_drafts()}
    assert set(pending) == {a["draft_id"], b["draft_id"]}
    assert pending[a["draft_id"]]["authored_by"] == "kchen2190"
    assert pending[b["draft_id"]]["authored_by"] == "asmith7734"

    # Each still holds exactly its own row — no cross-contamination.
    assert override_store.draft_payloads(a["draft_id"])[0]["override_holder_sid"] == "U555555"
    assert override_store.draft_payloads(b["draft_id"])[0]["override_holder_sid"] == "U666666"


def test_draft_survives_a_store_rebuild(sessions, override_store, tmp_path, monkeypatch):
    """A rebuild is routine — editing any source file makes the store stale —
    so it must not discard pending work. Everything else in the file is
    derived and IS discarded; the draft table is the deliberate exception."""
    from drydocs_core import mapping_store as core

    token = _token(sessions, "kchen2190")
    out = draft_override([_A_DRAFT], token, sessions, override_store)

    # Touch the committed source: the next read sees drift and rebuilds.
    fix = Path(core.SEAL_CONTACT_OVERRIDES_PATH)
    fix.write_text(
        fix.read_text(encoding="utf-8")
        + "APP-7777,L2 Operate Manager,,U888888,,added out of band,kchen2190,2026-07-22,active\n",
        encoding="utf-8",
    )
    assert not core.is_current(override_store._db_path), "fixture edit should make the store stale"

    # The rebuild happens inside this read; the draft must come through it.
    assert override_store.draft_payloads(out["draft_id"])[0]["app_seal_id"] == "APP-9012"
    assert [d["draft_id"] for d in override_store.open_drafts()] == [out["draft_id"]]


def test_promote_emits_an_additive_diff_that_round_trips(sessions, override_store):
    """The promote half of ADR 0009 rule 5.

    The diff must (a) apply cleanly to the committed file it was generated
    against and (b) produce a file that parses to the committed rows plus the
    drafted ones — no reformatting of untouched lines.
    """
    from drydocs_core import mapping_store as core

    token = _token(sessions, "kchen2190")
    drafted = draft_override([_A_DRAFT], token, sessions, override_store)
    out = promote_draft(drafted["draft_id"], token, sessions, override_store)

    assert out["entries"] == 1
    assert out["filename"].endswith(".patch")
    assert "wrote NOTHING" in out["note"]

    committed = Path(core.SEAL_CONTACT_OVERRIDES_PATH).read_text(encoding="utf-8")
    patched = _apply_unified_diff(committed, out["diff"])

    # (a) additive: every committed line survives byte-identically, in order.
    assert patched.startswith(committed)
    added = [
        ln for ln in out["diff"].splitlines() if ln.startswith("+") and not ln.startswith("+++")
    ]
    removed = [
        ln for ln in out["diff"].splitlines() if ln.startswith("-") and not ln.startswith("---")
    ]
    assert len(added) == 1 and removed == [], "a new override is an append, not a rewrite"

    # (b) round-trip: the patched file parses to old rows + the drafted one.
    rows = list(csv.DictReader(io.StringIO(patched)))
    assert [r["app_seal_id"] for r in rows] == ["APP-1234", "APP-5678", "APP-9012"]
    assert rows[-1]["role_name"] == "L1 Operate Manager"
    assert rows[-1]["authored_by"] == "kchen2190"
    # committed rows survive byte-faithfully
    assert rows[0]["override_holder_name"] == "Sam Steward"

    # Promotion closes the draft: the rows stay as the record of what was
    # proposed, but the draft is no longer pending.
    assert override_store.open_drafts() == []
    with pytest.raises(ChangesetValidationError):
        promote_draft(drafted["draft_id"], token, sessions, override_store)


def test_promote_diff_applies_with_real_git(sessions, override_store, tmp_path):
    """The same diff, validated by the tool that will actually apply it.

    _apply_unified_diff above is our reader of the patch; `git apply` is the
    one the user runs. Both must accept it, or the artifact is only
    theoretically correct.
    """
    import shutil
    import subprocess

    git = shutil.which("git")
    if git is None:
        pytest.skip("git not on PATH")

    from drydocs_core import mapping_store as core

    token = _token(sessions, "kchen2190")
    drafted = draft_override([_A_DRAFT], token, sessions, override_store)
    out = promote_draft(drafted["draft_id"], token, sessions, override_store)

    work = tmp_path / "apply"
    target = work / out["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        Path(core.SEAL_CONTACT_OVERRIDES_PATH).read_text(encoding="utf-8"), encoding="utf-8"
    )
    patch = work / "change.patch"
    patch.write_text(out["diff"], encoding="utf-8")

    subprocess.run([git, "init", "-q"], cwd=work, check=True)
    done = subprocess.run(
        [git, "apply", "--verbose", str(patch)], cwd=work, capture_output=True, text=True
    )
    assert done.returncode == 0, f"git refused the emitted diff:\n{done.stderr}"
    rows = list(csv.DictReader(io.StringIO(target.read_text(encoding="utf-8"))))
    assert [r["app_seal_id"] for r in rows] == ["APP-1234", "APP-5678", "APP-9012"]


def test_no_endpoint_writes_a_tracked_file():
    """ADR 0009 rule 1, enforced rather than asserted in prose: git is the only
    commit target.

    S4 gave this service its first durable write, and it goes to
    var/mapping.db — DERIVED and gitignored. The line that must not be crossed
    is a write to a file git tracks, which would put the source of truth
    somewhere the HITL gate never reviews and the cross-repo port cannot carry.

    Static and deliberately absolute: drydocs_api may not call a filesystem
    WRITE primitive at all. SQLite writes reach the draft buffer through the
    sqlite3 driver, not through these, so the rule costs nothing today and a
    future `write_text` has to argue with this test first.
    """
    import ast

    banned_funcs = {"write_text", "write_bytes", "unlink", "rmdir", "remove", "rename", "replace"}
    api_dir = Path(__file__).resolve().parents[2] / "drydocs_api"
    offenders: list[str] = []

    for path in sorted(api_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "open":
                mode = ""
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(ch in mode for ch in "wax+"):
                    offenders.append(f"{path.name}:{node.lineno}: open(..., {mode!r})")
            elif isinstance(fn, ast.Attribute) and fn.attr in banned_funcs:
                offenders.append(f"{path.name}:{node.lineno}: .{fn.attr}()")

    # O46 amendment (2026-08-06) — the one argued-for exception this test's
    # docstring anticipated: intake evidence (.msg/.json/.txt) lands WHOLE
    # under DRYDOCS_DATA_ROOT/context-intake/ via write_bytes. That is a
    # payload write to the gitignored data root, never to a file git tracks —
    # the rule this test defends is untouched (the root-outside-the-repo seam
    # is pinned by test_intake_api.py::test_records_reference_the_data_root_
    # seam). ONLY the landing write is exempt, and only in intake.py:
    # delete/rename/replace stay banned there too (evidence is never edited).
    offenders = [
        o for o in offenders if not (o.startswith("intake.py:") and o.endswith(".write_bytes()"))
    ]

    assert not offenders, (
        "drydocs_api must not write files — propose in the DB, land in git "
        "(ADR 0009 rule 5). Drafts belong in the mapping.db draft table; a "
        "committed file changes only through a promoted diff:\n" + "\n".join(offenders)
    )


def _apply_unified_diff(original: str, diff: str) -> str:
    """Minimal unified-diff applier — the test's own reader of the artifact.

    Deliberately independent of the code that produced the diff: reusing the
    promoter's new_text would prove only that it equals itself.
    """
    src = original.splitlines(keepends=True)
    out: list[str] = []
    pos = 0
    lines = diff.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("@@"):
            i += 1
            continue
        header = re.match(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", line)
        assert header, f"unparseable hunk header: {line}"
        start = int(header.group(1)) - 1
        out.extend(src[pos:start])
        pos = start
        i += 1
        while i < len(lines) and not lines[i].startswith("@@"):
            body = lines[i]
            if body.startswith("+"):
                out.append(body[1:] + "\n")
            elif body.startswith("-"):
                pos += 1
            elif body.startswith(" "):
                out.append(src[pos])
                pos += 1
            i += 1
    out.extend(src[pos:])
    return "".join(out)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [
            {
                "app_id": "A",
                "role_name": "Head Chef",
                "override_holder_sid": "U2",
                "rationale": "r",
            }
        ],  # unknown role
        [
            {
                "app_id": "A",
                "role_name": "L2 Operate Manager",
                "override_holder_sid": "U2",
                "rationale": " ",
            }
        ],  # rationale required
        [
            {
                "app_id": "A",
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
                    "app_id": "A",
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


# ---------------------------------------------------------------------------
# K9 — the K7 defined-mapping store (gate seal-app-ref-edge-reshape §E1/§E2).
# Synthetic values only (publish boundary).
# ---------------------------------------------------------------------------


@pytest.fixture()
def app_code_store(tmp_path, monkeypatch) -> MappingStore:
    """A store whose committed defined-mapping list is a fixture covering all
    three row kinds — the module constant is monkeypatched so the WHOLE read
    chain (is_current -> build) resolves to it."""
    fix = tmp_path / "app-code-mappings.csv"
    fix.write_text(
        ",".join(APP_CODE_HEADER) + "\n"
        # seal-born: code-level 1:1
        "PRA,,seal-born,APP-1234,,defined,,kchen2190,2026-08-03\n"
        # the shared platform code declares itself (K18: the declaration
        # carries the platform's OWN SEAL + rationale, and attributes nothing)...
        "PLT,,platform,APP-9900,,defined,shared SRE-dictated code,kchen2190,2026-08-03\n"
        # ...and resolves per folder
        "PLT,F0001,platform,APP-5678,,defined,,kchen2190,2026-08-03\n"
        # a per-folder override sits beside the defined row, origin-flagged
        "PLT,F0001,platform,APP-9012,,override,platform row predates the team split,"
        "kchen2190,2026-08-03\n"
        # dual-coded carries its DECLARED end state (§B2)
        "PRB,,dual-coded,APP-3456,all workload under PRB once the PLT folders drain,"
        "defined,,kchen2190,2026-08-03\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("drydocs_core.mapping_store.APP_CODE_MAPPINGS_PATH", fix)
    return MappingStore(tmp_path / "mapping.db")


def test_app_code_domain_registered():
    dom = next(d for d in DOMAINS if d["id"] == "app-code-mapping")
    assert dom["available"] and dom["kind"] == "defined"
    assert dom["source"] == "config/overrides/app-code-mappings.csv"


def test_app_code_grid_carries_row_kind_origin_and_end_state(sessions, app_code_store):
    """Every row is origin-flagged (§B3); code-level rows precede their
    per-folder resolutions; the dual-coded row's declared end state is on the
    surface (§B2). K18: the wire says row_kind, and the declaration row
    carries the platform's own app_id."""
    token = _token(sessions, "kchen2190")
    out = mapping_grid("app-code-mapping", token, sessions, app_code_store)
    assert {"app_code", "row_kind", "origin", "declared_end_state"} <= set(out["keys"])
    rows = [(r["app_code"], r["folder_id"], r["origin"], r["app_id"]) for r in out["rows"]]
    assert rows == [
        ("PLT", None, "defined", "APP-9900"),  # code-level (declaration) before per-folder
        ("PLT", "F0001", "defined", "APP-5678"),
        ("PLT", "F0001", "override", "APP-9012"),  # adjacent, origin-flagged
        ("PRA", None, "defined", "APP-1234"),
        ("PRB", None, "defined", "APP-3456"),
    ]
    dual = next(r for r in out["rows"] if r["row_kind"] == "dual-coded")
    assert "PLT folders drain" in dual["declared_end_state"]


def test_app_code_migration_report_reads_the_declared_end_states(sessions, app_code_store):
    """K7 §B2's readback, lifted from wip/k9-laptop (bfb2f0b) at J30.

    Tier 3 was admitted ON THE CONDITION that the end state is declared. The
    shipped K9 built the view and the authoring UI but no reader, so
    v_dual_coded_migrations had exactly one consumer in the tree — a unit test.
    A declaration nothing reads back is a form field, not a condition.
    """
    token = _token(sessions, "kchen2190")
    out = app_code_migration_report(token, sessions, app_code_store)

    assert out["count"] == len(out["migrations"])
    assert out["count"] >= 1, "the fixture carries a dual-coded row"
    row = out["migrations"][0]
    assert set(row) == {"app_code", "app_id", "declared_end_state", "authored_by", "authored_on"}
    assert row["declared_end_state"], "a dual-coded row without an end state is the defect"
    # Dual-coded ONLY — seal-born and platform rows are not migrations.
    codes = {r["app_code"] for r in out["migrations"]}
    kinds = {r["app_code"]: r["row_kind"] for r in app_code_store.app_code_rows()}
    assert all(kinds[c] == "dual-coded" for c in codes)


def test_app_code_migration_report_refuses_user_role(sessions, app_code_store):
    with pytest.raises(Forbidden):
        app_code_migration_report(_token(sessions, "jdoe4821"), sessions, app_code_store)


def test_draft_app_code_mapping_writes_a_row_and_promotes(sessions, app_code_store):
    """O24 mechanics verbatim, including the S4 move: drafting writes a ROW,
    promotion emits the additive diff, authored_by is server-stamped, and the
    server writes no committed file. Converted alongside the overrides so one
    module does not carry two different write models."""
    from drydocs_core import mapping_store as core

    token = _token(sessions, "asmith7734")
    out = draft_app_code_mapping(
        [
            {
                "app_code": "PRC",
                "row_kind": "seal-born",
                "app_id": "APP-7777",
            }
        ],
        token,
        sessions,
        app_code_store,
    )
    assert "csv" not in out
    assert out["domain"] == "app-code-mapping"
    assert out["entries"] == 1 and out["committed_rows"] == 5
    row = app_code_store.draft_payloads(out["draft_id"])[0]
    assert row["app_code"] == "PRC"
    assert row["origin"] == "defined"  # the default authoring origin
    assert row["authored_by"] == "asmith7734"  # session persona, never client-supplied

    promoted = promote_draft(out["draft_id"], token, sessions, app_code_store)
    committed = Path(core.APP_CODE_MAPPINGS_PATH).read_text(encoding="utf-8")
    patched = _apply_unified_diff(committed, promoted["diff"])
    assert patched.startswith(committed)  # additive, untouched lines untouched
    rows = list(csv.DictReader(io.StringIO(patched)))
    assert len(rows) == 6 and rows[-1]["app_code"] == "PRC"
    # committed rows survive byte-faithfully through the store round-trip
    assert rows[0]["app_code"] == "PRA" and rows[0]["app_id"] == "APP-1234"
    assert "wrote NOTHING" in promoted["note"]


@pytest.mark.parametrize(
    "bad",
    [
        [],
        # dual-coded without the §B2 declared end state
        [{"app_code": "PRD", "row_kind": "dual-coded", "app_id": "APP-1"}],
        # matched-fallback is derived at load, never authored
        [
            {
                "app_code": "PRD",
                "row_kind": "seal-born",
                "app_id": "APP-1",
                "origin": "matched-fallback",
            }
        ],
        # override without rationale (permanence makes the why load-bearing)
        [{"app_code": "PRD", "row_kind": "seal-born", "app_id": "APP-1", "origin": "override"}],
        # K18: a platform DECLARATION requires the platform's own app_id...
        [{"app_code": "PRD", "row_kind": "platform", "rationale": "shared code"}],
        # ...and its rationale
        [{"app_code": "PRD", "row_kind": "platform", "app_id": "APP-1"}],
        # duplicate of a COMMITTED row (1:1, OWNER-NOT-USER)
        [{"app_code": "PRA", "row_kind": "seal-born", "app_id": "APP-1"}],
    ],
)
def test_draft_app_code_mapping_fails_closed(sessions, app_code_store, bad):
    token = _token(sessions, "kchen2190")
    with pytest.raises(ChangesetValidationError):
        draft_app_code_mapping(bad, token, sessions, app_code_store)


def test_app_code_draft_route_is_wired():
    """K11: the K9 pure handler is actually SERVED — /mappings/app-code/draft
    was built at K9 but never routed in app.py, which is exactly the gap the
    steward cascade pane found when it tried to submit."""
    pytest.importorskip("fastapi", reason="fastapi not installed")
    from drydocs_api.app import create_app

    app = create_app(runner=object(), store=InMemorySessionStore())
    assert "/mappings/app-code/draft" in {getattr(r, "path", None) for r in app.routes}


def test_app_code_endpoints_refuse_user_role(sessions, app_code_store):
    token = _token(sessions, "jdoe4821")
    with pytest.raises(Forbidden):
        draft_app_code_mapping(
            [{"app_code": "PRC", "row_kind": "seal-born", "app_id": "APP-7777"}],
            token,
            sessions,
            app_code_store,
        )


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


# ---------------------------------------------------------------------------
# N14 — the pending-source-correction UNION report (gate SIGNED 2026-08-18).
# One age-ordered list across domains; permanent-by-nature stores unreachable;
# never a gate, never styled as a defect. Synthetic values only.
# ---------------------------------------------------------------------------

from drydocs_core.mapping_store import STORE_NATURES  # noqa: E402
from drydocs_core.source_registry import Source, SourceRegistry  # noqa: E402


def _tiny_registry() -> SourceRegistry:
    """Two manual rows (one dated via acquisition.since, one undated) and one
    automated row that must never appear — built directly so the test owns
    every value (no shipped-file coupling)."""
    rows = {
        "infra@x.y.zzz": Source(
            id="infra@x.y.zzz",
            confirmed=True,
            data={
                "system": "infra",
                "artifact": "zzz",
                "acquisition": {
                    "mode": "manual",
                    "format": "csv",
                    "drop_dir": "server-inventory/",
                    "since": "2026-01-05",
                },
            },
        ),
        "seal@a.b.ccc": Source(
            id="seal@a.b.ccc",
            confirmed=False,
            data={
                "system": "seal",
                "artifact": "ccc",
                "acquisition": {"mode": "manual", "format": "csv", "drop_dir": "seal/"},
            },
        ),
        "controlm@d.e.fff": Source(
            id="controlm@d.e.fff",
            confirmed=True,
            data={
                "system": "psgmgr",
                "artifact": "fff",
                "acquisition": {"mode": "automated", "via": "db"},
            },
        ),
    }
    return SourceRegistry(sources=rows)


@pytest.fixture()
def empty_override_store(tmp_path, monkeypatch) -> MappingStore:
    fix = tmp_path / "seal-contact-overrides.csv"
    fix.write_text(",".join(OVERRIDE_HEADER) + "\n", encoding="utf-8")
    monkeypatch.setattr("drydocs_core.mapping_store.SEAL_CONTACT_OVERRIDES_PATH", fix)
    return MappingStore(tmp_path / "mapping.db")


def test_pending_report_unions_both_domains(sessions, override_store):
    """(a) ONE report, both gate-joined domains, plus the Q21 email rider —
    and (d) nothing worded as a defect."""
    token = _token(sessions, "kchen2190")
    out = pending_source_correction_report(
        token, sessions, override_store, registry=_tiny_registry(), email_unassigned=3
    )
    md = out["markdown"]
    assert out["counts"] == {"overrides": 2, "manual_sources": 2, "email_unassigned": 3}
    assert out["count"] == 4
    assert "APP-1234 / L2 Operate Manager" in md  # override domain present
    assert "infra@x.y.zzz" in md and "seal@a.b.ccc" in md  # manual domain present
    assert "controlm@d.e.fff" not in md  # automated rows are not placeholders
    assert "3 unassigned email(s)" in md
    low = md.lower()
    assert "defect" not in low and "violation" not in low and "overdue" not in low
    assert "expected first state" in md  # N12 clause (f) framing, verbatim intent
    assert out["filename"].startswith("pending-source-corrections-")


def test_pending_report_age_order_and_undated_bucket(sessions, override_store):
    """(b) oldest first across BOTH domains on one list; rows with no
    determinable age land in the explicit bucket, never silently."""
    token = _token(sessions, "kchen2190")
    out = pending_source_correction_report(
        token, sessions, override_store, registry=_tiny_registry(), email_unassigned=None
    )
    md = out["markdown"]
    assert md.index("| 2026-01-05 |") < md.index("| 2026-07-21 |")
    undated = md.split("## Undated")[1]
    assert "seal@a.b.ccc" in undated
    # graph unavailable degrades to the named read path, never an error
    assert "docs.email-unassigned.v1" in md


def test_pending_report_reads_declared_natures_not_a_hardcoded_exemption():
    """(e) §D2: the fetch map covers EXACTLY the stores declared pending, so a
    permanent-by-nature store (app_code_mapping, K7 §E2) is structurally
    unreachable and a new pending store must register a fetcher or fail here."""
    from drydocs_api.mappings import _PENDING_STORE_FETCHERS

    assert STORE_NATURES["app_code_mapping"] == "permanent"
    assert set(_PENDING_STORE_FETCHERS) == {
        table for table, nature in STORE_NATURES.items() if nature == "pending"
    }


def test_store_natures_cover_every_table(empty_override_store):
    """The declaration happens AT creation: a table added to the DDL without a
    declared nature fails here, not at the first report that guesses."""
    rows = empty_override_store._select(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).rows
    assert {r["name"] for r in rows} == set(STORE_NATURES)


def test_pending_report_empty_case(sessions, empty_override_store):
    token = _token(sessions, "kchen2190")
    out = pending_source_correction_report(
        token,
        sessions,
        empty_override_store,
        registry=SourceRegistry(sources={}),
        email_unassigned=0,
    )
    assert out["count"] == 0
    assert "(no dated placeholders)" in out["markdown"]
    assert "nothing pending" in out["markdown"]


def test_pending_report_refuses_user_role(sessions, override_store):
    token = _token(sessions, "jdoe4821")
    with pytest.raises(Forbidden):
        pending_source_correction_report(
            token, sessions, override_store, registry=SourceRegistry(sources={})
        )
