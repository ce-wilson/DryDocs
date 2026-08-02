"""Offline tests for the K2 SEAL attribution loader.

Pins the match policy exactly as SME-confirmed at gate
seal-attribution-match-policy (config/gate-log.md, 2026-07-14): precedence
tiers (§A), coverage reconciliation (§B), deterministic multi-hit tie-break
(§C), the edge write shape (§D), and PIN semantics (§F). Pure — synthetic
fixtures only, no network/DB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from drydocs.graph_verify import Assertion, load_suite
from drydocs.loaders.seal_attribution import (
    ATTRIBUTION_TIERS,
    MATCH_METHOD_BY_TIER,
    SealAttributionAdapter,
    SealAttributionLoader,
    TierReconcilers,
    resolve_attributions,
)
from drydocs_core.adapters import CsvAdapter
from drydocs_core.models import SealAttributionRow, StgAppFactRow

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CSV = REPO_ROOT / "tests" / "fixtures" / "attribution" / "stg_app_fact__synthetic.csv"
AUTOMATED_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "seal_attribution.cypher"
MANUAL_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "manual_seal_attribution.cypher"
VOCAB_FILE = REPO_ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"
SUITE_FILE = REPO_ROOT / "graph-tests" / "seal-attribution-coverage.yaml"


def _fact(
    folder: str, job: str, ftype: str, value: str, sk: int | None = None, run: str = "run-x"
) -> StgAppFactRow:
    return StgAppFactRow(
        run_id=run,
        folder_id=folder,
        job_id=job,
        fact_type=ftype,
        fact_value=value,
        app_fact_sk=sk,
    )


# --- §A precedence -----------------------------------------------------------


def test_tier_order_is_the_gate_confirmed_precedence() -> None:
    assert ATTRIBUTION_TIERS == ("SEAL", "FID", "APP_NAME", "ALIAS")
    assert MATCH_METHOD_BY_TIER == {
        "SEAL": "seal",
        "FID": "fid",
        "APP_NAME": "app_name",
        "ALIAS": "alias",
    }


def test_seal_tier_one_to_one_accepts_without_review() -> None:
    decisions, cov = resolve_attributions([_fact("f1", "j1", "SEAL", "SL0001", sk=1)])
    assert [d.model_dump() for d in decisions] == [
        {"folder_id": "f1", "job_id": "j1", "seal_id": "SL0001", "match_method": "seal"}
    ]
    assert cov.matched == 1 and cov.eligible_jobs == 1 and cov.reconciles()
    assert not cov.multi_hits


def test_seal_hit_attributes_alone_lower_tiers_are_corroboration_only() -> None:
    recon = TierReconcilers(app_name={"AGREES": "SL0001", "DISAGREES": "SL0099"})
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "SEAL", "SL0001", sk=1),
            _fact("f1", "j1", "APP_NAME", "agrees", sk=2),
            _fact("f1", "j1", "APP_NAME", "disagrees", sk=3),
        ],
        reconcilers=recon,
    )
    assert len(decisions) == 1
    assert decisions[0].match_method == "seal"  # never overridden
    assert decisions[0].seal_id == "SL0001"
    assert cov.corroboration_agree == 1
    assert cov.corroboration_disagree == 1


def test_tier_walk_falls_back_in_precedence_order() -> None:
    recon = TierReconcilers(fid={"F-1": "SL0002"}, alias={"AL-1": "SL0003"})
    decisions, _ = resolve_attributions(
        [
            _fact("f1", "j1", "FID", "F-1", sk=1),
            _fact("f1", "j1", "ALIAS", "AL-1", sk=2),
        ],
        reconcilers=recon,
    )
    assert decisions[0].match_method == "fid"  # FID outranks ALIAS
    assert decisions[0].seal_id == "SL0002"


# --- §B coverage / unmatched -------------------------------------------------


def test_unmatched_job_is_surfaced_never_dropped() -> None:
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "DS_ID", "DS-1", sk=1),  # not an attribution tier
        ]
    )
    assert decisions == []
    assert cov.unmatched == 1 and cov.ignored_fact_rows == 1
    assert cov.reconciles()


def test_unresolvable_reconciler_values_are_counted() -> None:
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "APP_NAME", "no such app", sk=1),
        ]
    )
    assert decisions == [] and cov.unmatched == 1
    assert cov.unresolved_facts_by_tier == {"APP_NAME": 1}


# --- §C multi-hit triage -----------------------------------------------------


def test_multi_hit_tie_break_prefers_most_recent_feed_row() -> None:
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "SEAL", "SL0009", sk=1, run="run-a"),
            _fact("f1", "j1", "SEAL", "SL0002", sk=2, run="run-b"),
        ]
    )
    assert decisions[0].seal_id == "SL0002"
    (hit,) = cov.multi_hits
    assert hit.tie_break == "run_recency"
    assert hit.candidates == ("SL0002", "SL0009")
    assert hit.accepted == "SL0002"


def test_multi_hit_tie_break_last_resort_is_lowest_seal_id() -> None:
    # Equal recency keys — only the lexicographic rule can decide.
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "SEAL", "SL0007", sk=5),
            _fact("f1", "j1", "SEAL", "SL0003", sk=5),
        ]
    )
    assert decisions[0].seal_id == "SL0003"
    assert cov.multi_hits[0].tie_break == "lowest_seal_id"


def test_multi_hit_only_counts_same_tier_conflicts() -> None:
    # SEAL resolves alone; a conflicting FID is corroboration, not a multi-hit.
    recon = TierReconcilers(fid={"F-1": "SL0099"})
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "SEAL", "SL0001", sk=1),
            _fact("f1", "j1", "FID", "F-1", sk=2),
        ],
        reconcilers=recon,
    )
    assert decisions[0].seal_id == "SL0001"
    assert not cov.multi_hits
    assert cov.corroboration_disagree == 1


def test_resolution_is_deterministic_under_input_reordering() -> None:
    rows = [
        _fact("f1", "j1", "SEAL", "SL0009", sk=1),
        _fact("f1", "j1", "SEAL", "SL0002", sk=2),
        _fact("f2", "j2", "SEAL", "SL0005", sk=3),
    ]
    forward, _ = resolve_attributions(rows)
    backward, _ = resolve_attributions(list(reversed(rows)))

    def by_job(ds):
        return {(d.folder_id, d.job_id): (d.seal_id, d.match_method) for d in ds}

    assert by_job(forward) == by_job(backward)


# --- §F pins -----------------------------------------------------------------


def test_pinned_job_produces_no_decision_and_surfaces_the_conflict() -> None:
    pinned = {("f1", "j1"): "SL0001", ("f1", "j2"): "SL0777"}
    decisions, cov = resolve_attributions(
        [
            _fact("f1", "j1", "SEAL", "SL0001", sk=1),  # agrees with the pin
            _fact("f1", "j2", "SEAL", "SL0002", sk=2),  # disagrees with the pin
        ],
        pinned=pinned,
    )
    assert decisions == []  # automation never touches pins
    assert cov.pinned == 2 and cov.reconciles()
    agrees = {(c.folder_id, c.job_id): c.agrees for c in cov.pin_conflicts}
    assert agrees == {("f1", "j1"): True, ("f1", "j2"): False}


def test_pinned_job_with_no_derivation_holds_without_conflict() -> None:
    decisions, cov = resolve_attributions(
        [_fact("f1", "j1", "DS_ID", "DS-1", sk=1)],
        pinned={("f1", "j1"): "SL0001"},
    )
    assert decisions == [] and cov.pinned == 1
    (conflict,) = cov.pin_conflicts
    assert conflict.derived_seal_id is None and conflict.agrees is None


# --- fixture batch end-to-end (adapter) ---------------------------------------


def _fixture_adapter() -> SealAttributionAdapter:
    return SealAttributionAdapter(
        CsvAdapter(FIXTURE_CSV),
        reconcilers=TierReconcilers(
            fid={"FID-ALPHA": "SL0002"},
            app_name={"SYNTHETIC PAYMENTS HUB": "SL0003", "OTHER APP": "SL0099"},
            alias={"PAYHUB": "SL0004"},
        ),
        pinned={("900004", "6"): "SL0005", ("900004", "8"): "SL0777"},
    )


def test_fixture_batch_counts_pin_exactly() -> None:
    adapter = _fixture_adapter()
    with adapter:
        decisions = list(adapter.rows())
    cov = adapter.coverage
    assert cov is not None and cov.reconciles()
    assert cov.eligible_jobs == 10
    assert cov.matched == 6 and cov.unmatched == 2 and cov.pinned == 2
    assert cov.matched_by_method == {"seal": 3, "fid": 1, "app_name": 1, "alias": 1}
    assert len(cov.multi_hits) == 2
    assert sum(1 for c in cov.pin_conflicts if c.agrees is not None) == 2
    assert cov.corroboration_disagree == 1
    assert cov.ignored_fact_rows == 1
    assert cov.unresolved_facts_by_tier == {"APP_NAME": 1}
    assert cov.fact_rows_rejected == 0

    by_job = {(d["folder_id"], d["job_id"]): (d["seal_id"], d["match_method"]) for d in decisions}
    assert by_job == {
        ("900001", "3"): ("SL0001", "seal"),
        ("900001", "7"): ("SL0002", "fid"),
        ("900002", "2"): ("SL0003", "app_name"),
        ("900002", "4"): ("SL0004", "alias"),
        ("900003", "1"): ("SL0003", "seal"),  # run_recency tie-break
        ("900003", "5"): ("SL0004", "seal"),  # run_recency tie-break
    }
    # every emitted decision re-validates against the loader's row model
    for d in decisions:
        SealAttributionRow.model_validate(d)


def test_adapter_counts_malformed_fact_rows_as_rejects() -> None:
    class _Inner:
        def rows(self):
            yield {
                "run_id": "r",
                "folder_id": "f",
                "job_id": "",  # invalid
                "fact_type": "SEAL",
                "fact_value": "SL1",
            }
            yield {
                "run_id": "r",
                "folder_id": "f",
                "job_id": "1",
                "fact_type": "SEAL",
                "fact_value": "SL1",
            }

    adapter = SealAttributionAdapter(_Inner())
    decisions = list(adapter.rows())
    assert len(decisions) == 1
    assert adapter.coverage is not None
    assert adapter.coverage.fact_rows_rejected == 1
    assert adapter.fact_rejects and adapter.fact_rejects[0]["row_index"] == 0


# --- §D cypher shape pins ------------------------------------------------------


def test_automated_cypher_creates_no_nodes() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))
    merges = [line for line in code.splitlines() if "MERGE" in line]
    assert len(merges) == 1, "the automated path MERGEs exactly one thing: the edge"
    assert "MERGE (j)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(a)" in code
    assert "MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})" in code
    # S3 / gate business-application-identity §C1: the canonical node is keyed on the
    # neutral app_id. `row.seal_id` keeps its name on purpose — it is the value a
    # Control-M CMDLINE carried, i.e. evidence, which §B2(ii) rules stays in the
    # source's own terms. The two halves of the two-part rule, on one line.
    assert "MATCH (a:BusinessApplication {app_id: row.seal_id})" in code


def test_automated_cypher_on_create_set_split_matches_the_gate() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    on_create = text.split("ON CREATE SET", 1)[1].split("SET r.last_seen_at", 1)[0]
    assert "r.first_seen_at" in on_create
    assert "r.source" in on_create and "'controlm-variable-normalization'" in on_create
    assert "r.match_method" in on_create
    every_run = text.split("SET r.last_seen_at", 1)[1]
    assert "r.last_run_id" in every_run


def test_automated_cypher_carries_the_pin_guard() -> None:
    text = AUTOMATED_CYPHER.read_text(encoding="utf-8")
    assert "NOT EXISTS" in text and "m.match_method = 'manual'" in text


def test_manual_cypher_stamps_manual_provenance_and_guards_node_creation() -> None:
    text = MANUAL_CYPHER.read_text(encoding="utf-8")
    assert "r.match_method     = 'manual'" in text
    assert "'manual-csv'" in text
    assert "r.manual_load_file" in text and "r.authored_by" in text
    # node creation only inside the SME-authorized FOREACH guard
    assert "FOREACH (_ IN CASE WHEN row.create_target_if_missing THEN [1] ELSE [] END |" in text
    assert "n.manually_created" in text
    merge_app_lines = [line for line in text.splitlines() if "MERGE (n:BusinessApplication" in line]
    assert len(merge_app_lines) == 1, "Application MERGE exists only in the FOREACH guard"


# --- activation pins (vocabulary + verify suite) --------------------------------


def test_vocab_entry_is_active_with_loader_and_supplement_recorded() -> None:
    vocab = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    entry = next(r for r in vocab["local_relationships"] if r["id"] == "m3_seal_app_ref")
    assert entry["status"] == "active"
    assert entry["loader"] == "seal_attribution.cypher"
    assert entry["supplement"] == "ontology_supplement.cypher"
    assert entry["neo4j_label"] == "WAS_ASSOCIATED_WITH"
    assert entry["role"] == "seal_app_ref"


def test_coverage_suite_loads_and_asserts_empty_invariants() -> None:
    suite = load_suite(SUITE_FILE)
    assert suite.name == "seal-attribution-coverage"
    assert len(suite.cases) >= 6
    assert all(c.assertion is Assertion.EMPTY for c in suite.cases)


def test_loader_class_wiring() -> None:
    assert SealAttributionLoader.name == "seal_attribution.v1"
    assert SealAttributionLoader.row_model is SealAttributionRow
    assert SealAttributionLoader.cypher_path is not None
    assert SealAttributionLoader.cypher_path.exists()
