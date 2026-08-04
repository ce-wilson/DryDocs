"""Offline tests for the K8 folder-grain attribution loader.

Pins the K7 close-out exactly as SME-signed at gate seal-app-ref-edge-reshape
(config/gate-log.md, 2026-08-03, 24/24): folder grain with job inheritance
(§A1), one authoring mechanism per app code with loader fan-out (§B1), the
three tiers (§B2), the origin-disclosed K2 fallback demotion (§B3), the
BatchProcessing Port target (§C1), one shape everywhere (§D2), and the 1:1
OWNER-NOT-USER rule (a folder with two application candidates is a conflict,
never an auto-pick). Pure — synthetic fixtures only, no network/DB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from drydocs.graph_verify import Assertion, load_suite
from drydocs.loaders.folder_attribution import (
    AUTHORED_SOURCE,
    FALLBACK_SOURCE,
    FolderAttributionAdapter,
    FolderAttributionLoader,
    resolve_folder_attributions,
)
from drydocs.loaders.seal_attribution import TierReconcilers
from drydocs_core.adapters import CsvAdapter
from drydocs_core.models import FolderAttributionRow, SealAttributionRow

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CSV = REPO_ROOT / "tests" / "fixtures" / "attribution" / "stg_app_fact__synthetic.csv"
AUTOMATED_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "folder_attribution.cypher"
MANUAL_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "manual_seal_attribution.cypher"
VOCAB_FILE = REPO_ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"
SUITE_FILE = REPO_ROOT / "graph-tests" / "folder-attribution-coverage.yaml"


def _authored(
    app_code: str,
    app_id: str | None,
    *,
    folder_id: str | None = None,
    tier: str = "seal-born",
    origin: str = "defined",
) -> dict:
    return {
        "app_code": app_code,
        "folder_id": folder_id,
        "tier": tier,
        "app_id": app_id,
        "declared_end_state": None,
        "origin": origin,
        "rationale": None,
        "authored_by": "sid-test",
        "authored_on": "2026-08-04",
    }


def _decision(folder: str, job: str, app: str, method: str = "seal") -> SealAttributionRow:
    return SealAttributionRow(folder_id=folder, job_id=job, seal_id=app, match_method=method)


# --- §B1 fan-out + authored precedence ------------------------------------------


def test_code_level_row_fans_out_to_every_folder_under_the_code() -> None:
    rows, cov = resolve_folder_attributions(
        [_authored("ARA", "SL0001")],
        {"f1": "ARA", "f2": "ARA", "f3": "OTH"},
        [],
    )
    by_folder = {r.folder_id: r for r in rows}
    assert set(by_folder) == {"f1", "f2"}
    for r in by_folder.values():
        assert r.app_id == "SL0001"
        assert r.origin == "defined" and r.match_method == "defined"
        assert r.tier == "seal-born"
        assert r.source == AUTHORED_SOURCE
    assert cov.attributed == 2 and cov.unmatched == 1 and cov.reconciles()


def test_per_folder_row_narrows_to_one_folder() -> None:
    rows, cov = resolve_folder_attributions(
        [_authored("DPL", "SL0002", folder_id="f1", tier="platform")],
        {"f1": "DPL", "f2": "DPL"},
        [],
    )
    assert [r.folder_id for r in rows] == ["f1"]
    assert cov.attributed == 1 and cov.unmatched == 1 and cov.reconciles()


def test_origin_precedence_manual_pin_beats_override_beats_defined() -> None:
    rows, _ = resolve_folder_attributions(
        [
            _authored("ARA", "SL0001"),
            _authored("ARA", "SL0009", origin="override"),
        ],
        {"f1": "ARA"},
        [],
    )
    assert rows[0].app_id == "SL0009" and rows[0].origin == "override"

    rows, _ = resolve_folder_attributions(
        [
            _authored("ARA", "SL0009", origin="override"),
            _authored("ARA", "SL0005", folder_id="f1", origin="manual-pin"),
        ],
        {"f1": "ARA"},
        [],
    )
    assert rows[0].app_id == "SL0005"
    assert rows[0].origin == "manual-pin" and rows[0].match_method == "manual"


def test_authored_tie_is_a_conflict_never_an_auto_pick() -> None:
    """1:1 (OWNER-NOT-USER): two same-precedence candidates naming different
    applications surface to the steward; nothing is written."""
    rows, cov = resolve_folder_attributions(
        [
            _authored("ARA", "SL0001"),
            _authored("ARA", "SL0002", tier="dual-coded"),
        ],
        {"f1": "ARA"},
        [],
    )
    assert rows == []
    (conflict,) = cov.conflicts
    assert conflict.kind == "authored-tie"
    assert conflict.candidates == ("SL0001", "SL0002")
    assert cov.reconciles()


# --- §B2 platform declarations ---------------------------------------------------


def test_declared_platform_code_folders_surface_instead_of_falling_back() -> None:
    """A code-level platform DECLARATION (empty app_id) means the code HAS a
    defined row, so §B3's no-defined-row fallback does not apply — its
    unresolved folders queue for the steward."""
    rows, cov = resolve_folder_attributions(
        [
            _authored("DPL", None, tier="platform"),
            _authored("DPL", "SL0002", folder_id="f1", tier="platform"),
        ],
        {"f1": "DPL", "f2": "DPL"},
        [_decision("f2", "1", "SL0777")],  # would resolve f2 — must NOT be used
    )
    assert [r.folder_id for r in rows] == ["f1"]
    (conflict,) = cov.conflicts
    assert conflict.folder_id == "f2" and conflict.kind == "platform-unresolved"
    assert cov.reconciles()


# --- §B3 fallback demotion -------------------------------------------------------


def test_fallback_requires_unanimity_and_is_disclosed() -> None:
    rows, cov = resolve_folder_attributions(
        [],
        {"f1": "UNK", "f2": None},
        [
            _decision("f1", "1", "SL0003", "app_name"),
            _decision("f1", "2", "SL0003", "seal"),
            _decision("f2", "1", "SL0004", "alias"),
        ],
    )
    by_folder = {r.folder_id: r for r in rows}
    assert by_folder["f1"].origin == "matched-fallback"
    assert by_folder["f1"].match_method == "seal"  # best tier among agreeing facts
    assert by_folder["f1"].tier is None
    assert by_folder["f1"].source == FALLBACK_SOURCE
    assert by_folder["f2"].match_method == "alias"
    assert cov.attributed_by_origin == {"matched-fallback": 2}


def test_fallback_disagreement_is_a_conflict() -> None:
    rows, cov = resolve_folder_attributions(
        [],
        {"f1": "UNK"},
        [
            _decision("f1", "1", "SL0003"),
            _decision("f1", "2", "SL0004"),
        ],
    )
    assert rows == []
    (conflict,) = cov.conflicts
    assert conflict.kind == "fallback-disagreement"
    assert conflict.candidates == ("SL0003", "SL0004")


def test_authored_row_beats_fallback_for_its_code() -> None:
    rows, _ = resolve_folder_attributions(
        [_authored("ARA", "SL0001")],
        {"f1": "ARA"},
        [_decision("f1", "1", "SL0777")],
    )
    assert rows[0].app_id == "SL0001" and rows[0].origin == "defined"


# --- §F pins ---------------------------------------------------------------------


def test_pinned_folder_is_excluded_and_conflict_surfaced() -> None:
    rows, cov = resolve_folder_attributions(
        [_authored("ARA", "SL0002")],
        {"f1": "ARA", "f2": "ARA"},
        [],
        pinned={"f1": "SL0005"},
    )
    assert [r.folder_id for r in rows] == ["f2"]
    assert cov.pinned == 1
    (pin,) = cov.pin_conflicts
    assert pin.pinned_app_id == "SL0005" and pin.derived_app_id == "SL0002"
    assert pin.agrees is False
    assert cov.reconciles()


# --- 1:1 by construction ---------------------------------------------------------


def test_resolver_emits_at_most_one_row_per_folder() -> None:
    rows, _ = resolve_folder_attributions(
        [
            _authored("ARA", "SL0001"),
            _authored("ARA", "SL0001", folder_id="f1"),  # same app via both paths
        ],
        {"f1": "ARA", "f2": "ARA"},
        [],
    )
    folder_ids = [r.folder_id for r in rows]
    assert len(folder_ids) == len(set(folder_ids))


# --- adapter end-to-end (fixture fallback + authored rows) -----------------------


def test_adapter_combines_authored_rows_with_fixture_fallback() -> None:
    adapter = FolderAttributionAdapter(
        [_authored("ARA", "SL0100")],
        {
            "900001": "ARA",  # authored — fallback ignored for it
            "900002": "UNK",  # falls back on the fixture's job decisions
            "900005": None,  # no code, no facts -> unmatched
        },
        fact_source=CsvAdapter(FIXTURE_CSV),
        reconcilers=TierReconcilers(
            app_name={"SYNTHETIC PAYMENTS HUB": "SL0003", "OTHER APP": "SL0099"},
            alias={"PAYHUB": "SL0003"},
        ),
    )
    with adapter:
        rows = [FolderAttributionRow.model_validate(r) for r in adapter.rows()]
    by_folder = {r.folder_id: r for r in rows}
    assert by_folder["900001"].app_id == "SL0100"
    assert by_folder["900001"].origin == "defined"
    assert by_folder["900002"].app_id == "SL0003"
    assert by_folder["900002"].origin == "matched-fallback"
    cov = adapter.coverage
    assert cov is not None and cov.reconciles()
    assert cov.eligible_folders == 3
    assert cov.attributed == 2 and cov.unmatched == 1


def test_adapter_authored_only_run_needs_no_fact_source() -> None:
    adapter = FolderAttributionAdapter(
        [_authored("ARA", "SL0001")],
        {"f1": "ARA"},
    )
    rows = list(adapter.rows())
    assert len(rows) == 1
    assert adapter.coverage is not None and adapter.coverage.fact_rows_rejected == 0


# --- §D cypher shape pins --------------------------------------------------------


def test_automated_cypher_creates_no_nodes_and_targets_the_batch_port() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))
    merges = [line.strip() for line in code.splitlines() if "MERGE" in line]
    # §C1 + §G1 (K11): exactly two MERGEs, both EDGES — the attribution edge
    # and the orchestrator USES_SOFTWARE edge the confirmed mapping authors.
    # The automated path still creates NO nodes (every endpoint is MATCHed).
    assert merges == [
        "MERGE (f)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(p)",
        "MERGE (a)-[u:USES_SOFTWARE {source: 'app-code-mapping'}]->(sp)",
    ]
    assert "MATCH (f:ControlMFolder {folder_id: row.folder_id})" in code
    # §C1: the attribution target is the application's BatchProcessing Port,
    # key (parent_app_id, kind) — never :BusinessApplication. The app node
    # appears exactly once, as the §G1 orchestrator edge's MATCHed source.
    assert (
        "MATCH (p:Port:BatchProcessing {parent_app_id: row.app_id, kind: 'BatchProcessing'})"
        in code
    )
    assert code.count("BusinessApplication") == 1
    assert "MATCH (a:BusinessApplication {app_id: row.app_id})" in code


def test_automated_cypher_on_create_set_split_carries_the_origin_flag() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    on_create = text.split("ON CREATE SET", 1)[1].split("SET r.last_seen_at", 1)[0]
    for prop in ("r.first_seen_at", "r.source", "r.origin", "r.match_method", "r.tier"):
        assert prop in on_create
    every_run = text.split("SET r.last_seen_at", 1)[1]
    assert "r.last_run_id" in every_run


def test_automated_cypher_carries_the_pin_guard() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    assert "NOT EXISTS" in text and "m.match_method = 'manual'" in text


# --- K10 port activation cutover (§G4/§G5) ---------------------------------------

SEAL_APPS_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "seal_applications.cypher"


def _code_lines(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))


def test_ports_seed_declared_and_never_confirmed_at_the_seal_load() -> None:
    """K10 (§G4): seal_applications seeds active_state='declared' ON CREATE
    only — a SEAL reload never resets a confirmation — and the retired
    `active` boolean is gone. Confirmation is NEVER written here (§G5: it is
    derived from the edge landing, by the attribution loaders)."""
    code = _code_lines(SEAL_APPS_CYPHER)
    assert code.count("active_state  = 'declared'") == 2  # both ports
    assert "'confirmed'" not in code
    assert "active = false" not in code
    # declared stamps ride the seed (§G4)
    assert "declared_by" in code and "declared_at" in code


def test_attribution_cyphers_derive_confirmation_with_stable_first_stamps() -> None:
    """K10 (§G5): both edge writers stamp the port confirmed when the edge
    lands — no separate trigger — and the first-confirmation stamps are
    coalesce-stable so a re-run re-confirms without rewriting who or when
    confirmed first."""
    for path in (AUTOMATED_CYPHER, MANUAL_CYPHER):
        code = _code_lines(path)
        assert "p.active_state     = 'confirmed'" in code
        for stamp in ("p.confirmed_by", "p.confirmed_at", "p.confirmed_run_id"):
            assert f"coalesce({stamp}" in code, f"{path.name}: {stamp} must be coalesce-stable"


def test_authored_by_travels_to_the_row_for_the_confirmed_by_stamp() -> None:
    """K10: authored rows carry the steward's authored_by (the cypher's
    confirmed_by source); fallback rows carry None so the loader identity
    confirms instead."""
    rows, _ = resolve_folder_attributions([_authored("ARA", "SL0001")], {"f1": "ARA"}, [])
    assert rows[0].authored_by == "sid-test"
    rows, _ = resolve_folder_attributions([], {"f1": None}, [_decision("f1", "1", "SL0002")])
    assert rows[0].authored_by is None


def test_folder_applications_spec_surfaces_the_port_state() -> None:
    from drydocs_api.query_specs import QUERY_SPECS

    spec = QUERY_SPECS["explorer.folder-applications.v1"]
    assert "p.active_state AS port_state" in spec.cypher
    assert "port_state" in [c.name for c in spec.columns]


def test_manual_cypher_fans_out_per_app_code_and_stamps_manual_pin() -> None:
    text = MANUAL_CYPHER.read_text(encoding="utf-8")
    assert "MATCH (ca:ControlMApplication {name: row.app_code})-[:CONTAINS_FOLDER]->" in text
    assert "row.folder_id IS NULL OR f.folder_id = row.folder_id" in text
    assert "r.origin           = 'manual-pin'" in text
    assert "r.match_method     = 'manual'" in text
    assert "'manual-csv'" in text
    assert "r.manual_load_file" in text and "r.authored_by" in text
    # node creation only inside the SME-authorized FOREACH guards
    assert "FOREACH (_ IN CASE WHEN row.create_target_if_missing THEN [1] ELSE [] END |" in text
    assert "n.manually_created" in text
    merge_app_lines = [line for line in text.splitlines() if "MERGE (n:BusinessApplication" in line]
    assert len(merge_app_lines) == 1, "Application MERGE exists only in the FOREACH guard"


# --- activation pins (vocabulary + verify suite) ---------------------------------


def test_folder_vocab_entry_is_active_with_loader_and_supplement_recorded() -> None:
    vocab = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    entry = next(r for r in vocab["local_relationships"] if r["id"] == "m3_belongs_to_application")
    assert entry["status"] == "active"
    assert entry["loader"] == "folder_attribution.cypher"
    assert entry["supplement"] == "ontology_supplement.cypher"
    assert entry["neo4j_label"] == "BELONGS_TO_APPLICATION"
    assert entry["role"] == "seal_app_ref"
    assert entry["from_node"] == "ControlMFolder" and entry["to_node"] == "Port"


def test_coverage_suite_loads_and_asserts_empty_invariants() -> None:
    suite = load_suite(SUITE_FILE)
    assert suite.name == "folder-attribution-coverage"
    assert len(suite.cases) >= 8
    assert all(c.assertion is Assertion.EMPTY for c in suite.cases)
    text = SUITE_FILE.read_text(encoding="utf-8")
    assert "application_edges > 1" in text, "the 1:1 graph-test is the suite's reason to exist"


def test_loader_class_wiring() -> None:
    assert FolderAttributionLoader.name == "folder_attribution.v1"
    assert FolderAttributionLoader.row_model is FolderAttributionRow
    assert FolderAttributionLoader.cypher_path is not None
    assert FolderAttributionLoader.cypher_path.exists()


# --- K11 §G1/§G2 — the confirmed orchestrator edge --------------------------------

BATCH_PORT_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "batch_port_orchestrator.cypher"


def test_orchestrator_product_ref_resolves_from_the_platforms_taxonomy() -> None:
    """§G1: the domain orchestrator is a per-domain constant resolved from the
    C12-confirmed platforms taxonomy — never hardcoded in Cypher; an unknown
    platform id fails loudly at wiring time."""
    from drydocs.loaders.folder_attribution import orchestrator_product_ref

    assert orchestrator_product_ref() == "controlm"
    with pytest.raises(ValueError):
        orchestrator_product_ref("no-such-platform")


def test_attribution_cyphers_author_the_confirmed_orchestrator_edge() -> None:
    """§G1 (K11): BOTH edge writers author the app -> orchestrator
    USES_SOFTWARE edge when a folder edge lands — created BY the confirmed
    mapping, keyed {source: 'app-code-mapping'} so it coexists with the
    declared 'batch-port' edge, origin/confirmation stamps set ON CREATE
    only, FOREACH-guarded so an absent registry skips (reported by the
    loader) rather than erroring."""
    for path in (AUTOMATED_CYPHER, MANUAL_CYPHER):
        code = _code_lines(path)
        assert "MERGE (a)-[u:USES_SOFTWARE {source: 'app-code-mapping'}]->(sp)" in code, path.name
        assert "$orchestrator_product_id" in code, path.name
        on_create = code.split("MERGE (a)-[u:USES_SOFTWARE", 1)[1].split("SET u.last_seen_at", 1)[0]
        assert "u.origin        = 'confirmed'" in on_create, path.name
        assert "u.confirmed_by" in on_create and "u.confirmed_at" in on_create, path.name
        assert "FOREACH (_ IN CASE WHEN sp IS NOT NULL THEN [1] ELSE [] END |" in code, path.name


def test_batch_port_declared_edges_carry_the_g2_origin() -> None:
    """§G2: the SEAL-declared 'batch-port' edge is KEPT origin='declared'
    (prefill only) — coalesce so a re-run never overwrites, and this writer
    never writes 'confirmed'."""
    code = _code_lines(BATCH_PORT_CYPHER)
    assert "u.origin           = coalesce(u.origin, 'declared')" in code
    assert "'confirmed'" not in code


def test_attribution_loaders_supply_the_orchestrator_param() -> None:
    """Both attribution writers pass the §G1 domain constant into their
    templates via the extra_cypher_params hook (per-domain constant, not a
    row value)."""
    from drydocs.loaders.base import BaseLoader
    from drydocs.loaders.manual_loads import ManualSealAttributionLoader

    # The hook reads no instance state, so calling it unbound is safe here.
    expected = {"orchestrator_product_id": "controlm"}
    assert FolderAttributionLoader.extra_cypher_params(object()) == expected
    assert ManualSealAttributionLoader.extra_cypher_params(object()) == expected
    assert BaseLoader.extra_cypher_params(object()) == {}


def test_coverage_suite_pins_the_orchestrator_agreement() -> None:
    """TC-12: a {source: 'app-code-mapping'} edge exists only on apps with a
    confirmed Batch port, always origin=confirmed with its stamps."""
    text = SUITE_FILE.read_text(encoding="utf-8")
    assert "TC-12" in text and "app-code-mapping" in text


# --- K11 cascade specs (the steward screen's data frames) -------------------------


def test_cascade_specs_are_registered_with_the_ruled_semantics() -> None:
    """The four cascade specs carry the gate's rulings in their Cypher:
    unmapped-only folders (§G7), the catalog spine over HAS_APPLICATION
    (§G6 — the list picker's traversal), the orchestrator role filter (C12),
    and the per-app edge disclosure (source + origin, §G2/§G3)."""
    from drydocs_api.query_specs import QUERY_SPECS

    folders = QUERY_SPECS["mappings.unmapped-folders.v1"]
    assert "NOT EXISTS { MATCH (f)-[:BELONGS_TO_APPLICATION" in folders.cypher
    assert "run_as_users" in [c.name for c in folders.columns]  # SME sort addition

    cascade = QUERY_SPECS["mappings.catalog-cascade.v1"]
    assert "[:HAS_APPLICATION]->(a:BusinessApplication)" in cascade.cypher
    assert "[:HAS_PRODUCT]->(p:Product)" in cascade.cypher

    orchestrators = QUERY_SPECS["mappings.orchestrators.v1"]
    assert "{role: 'orchestrator'}" in orchestrators.cypher

    app_orch = QUERY_SPECS["mappings.app-orchestrators.v1"]
    cols = [c.name for c in app_orch.columns]
    assert "source" in cols and "origin" in cols
