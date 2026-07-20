"""Guards for the C9 PAT reconcile (gate 2026-07-18 — no Neo4j required).

The loader semantics live in Cypher, which unit tests don't execute — so these
are DRIFT GUARDS on the row model and the cypher text: the ladder the SME
confirmed (apps via arch_develops + fallback-only home product) must not
quietly regress to the pre-C9 shape the 2026-06-21 gate deprecated.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from drydocs.loaders.catalog import PatProductMappingRow


def _cypher() -> str:
    path = Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher" / "pat_product_mapping.cypher"
    return path.read_text(encoding="utf-8")


def test_row_model_accepts_sponsored_area_product() -> None:
    row = PatProductMappingRow(
        team_id="T1",
        product_id="P1",
        team_type="Dedicated",          # normalizes to lowercase
        sponsored_area_product_id="AP9",
    )
    assert row.team_type == "dedicated"
    assert row.sponsored_area_product_id == "AP9"
    assert row.sponsored is False


def test_row_model_normalizes_semicolon_seal_ids() -> None:
    """The real PAT team report delimits SEAL ids with ';' (internal/pat-evidence);
    the loader cypher splits on ','. The row model normalizes at the boundary —
    without this, a real team-report extract silently produces zero app edges."""
    row = PatProductMappingRow(
        team_id="T1",
        product_id="P1",
        team_type="aligned",
        seal_ids="104358; 112534",
    )
    assert row.seal_ids == "104358, 112534"


def test_row_model_rejects_unknown_team_type() -> None:
    with pytest.raises(ValueError):
        PatProductMappingRow(team_id="T1", product_id="P1", team_type="embedded")


def test_cypher_feeds_arch_develops_not_has_application() -> None:
    """C9: team-scoped seal_ids feed the ACTIVE arch_develops edge; the
    Product->HAS_APPLICATION write (entry still status: planned) is gone."""
    text = _cypher()
    assert "WAS_ATTRIBUTED_TO {role: 'developed_by'}" in text
    assert "HAS_APPLICATION]->" not in text


def test_cypher_home_product_is_fallback_only() -> None:
    """The home-product SUPPORTS write only fires when the row has no area
    product (the C5 sole-assertion fallback) — never unconditionally."""
    text = _cypher()
    assert "WHEN NOT has_area" in text
    # the pre-C9 unconditional form (bare MATCH product + MERGE SUPPORTS) is gone
    assert "MATCH (p:Product  {product_id: row.product_id})" not in text


def test_cypher_sweeps_stale_alignment() -> None:
    """Alignment is volatile: each load deletes the team's pat-sourced edges
    not refreshed by this run (tracked, never frozen)."""
    text = _cypher()
    assert "stale.last_run_id <> $run_id" in text
    assert "stale_dev.last_run_id <> $run_id" in text


def test_migration_file_exists_and_targets_pat_edges_only() -> None:
    path = Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher" / "migrate_pat_alignment_c9.cypher"
    text = path.read_text(encoding="utf-8")
    # both cleanups are scoped to pat-sourced edges — never other writers' edges
    assert text.count("r.source = 'pat'") == 2
