"""Offline tests for the K2 match policy (now the K8 fallback resolver).

Pins the match policy exactly as SME-confirmed at gate
seal-attribution-match-policy (config/gate-log.md, 2026-07-14): precedence
tiers (§A), coverage reconciliation (§B), deterministic multi-hit tie-break
(§C), and PIN semantics (§F). The policy was NOT re-opened at the K7
close-out (gate seal-app-ref-edge-reshape §B3) — it DEMOTED to the fallback
tier feeding the folder-grain loader, so these tests keep pinning it; the
edge-write and loader pins moved to test_folder_attribution.py with the
grain. Pure — synthetic fixtures only, no network/DB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from drydocs.loaders.seal_attribution import (
    ATTRIBUTION_TIERS,
    MATCH_METHOD_BY_TIER,
    TierReconcilers,
    resolve_attributions,
    validate_fact_rows,
)
from drydocs_core import yaml_fragments
from drydocs_core.models import StgAppFactRow

REPO_ROOT = Path(__file__).resolve().parents[2]
VOCAB_FILE = REPO_ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary"


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


# --- fact validation seam ------------------------------------------------------


def test_validate_fact_rows_counts_malformed_rows_as_rejects() -> None:
    facts, rejected, samples = validate_fact_rows(
        [
            {
                "run_id": "r",
                "folder_id": "f",
                "job_id": "",  # invalid
                "fact_type": "SEAL",
                "fact_value": "SL1",
            },
            {
                "run_id": "r",
                "folder_id": "f",
                "job_id": "1",
                "fact_type": "SEAL",
                "fact_value": "SL1",
            },
        ]
    )
    assert len(facts) == 1
    assert rejected == 1
    assert samples and samples[0]["row_index"] == 0


# --- K7 demotion pins -----------------------------------------------------------


def test_job_grain_vocab_entry_is_deprecated_with_no_loader() -> None:
    """The K8 flip (gate §A1): the job-grain edge is retired — the vocabulary
    entry records the supersession and names no loader or supplement. The
    K7 sign-off's 'stays active until the K7 build migrates it' clause is
    this downgrade's authority (recorded in the entry note)."""
    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    entry = next(r for r in vocab["local_relationships"] if r["id"] == "m3_seal_app_ref")
    assert entry["status"] == "deprecated"
    assert entry["loader"] is None
    assert entry["supplement"] is None
    assert "m3_belongs_to_application" in entry["note"]  # the K8-era note is history; G87 left it


def test_retired_job_grain_writer_files_are_gone() -> None:
    """§A1: no per-job application edge is authored — the module keeps only
    the resolver; the edge-writer cypher is deleted."""
    assert not (REPO_ROOT / "drydocs" / "loaders" / "cypher" / "seal_attribution.cypher").exists()
    module = (REPO_ROOT / "drydocs" / "loaders" / "seal_attribution.py").read_text(encoding="utf-8")
    assert "class SealAttributionLoader" not in module
    assert "BaseLoader" not in module
